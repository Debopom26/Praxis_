"""Per-session bounded speech processing. No model trains or invents missing evidence."""

import asyncio
import logging
from contextlib import suppress
from time import perf_counter

import numpy as np

from praxis.audio.pipeline import AudioPipeline
from praxis.context import evaluate_context
from praxis.contracts import (
    ArtifactState,
    ContextConfig,
    EvidenceSummary,
    ModuleStatus,
    PolicyConfig,
    RiskEvent,
    RuleFlag,
    SpeakerEvidence,
    TranscriptEvent,
    UnavailableEvent,
)
from praxis.db.repository import utcnow
from praxis.linguistic import analyze_rules
from praxis.policy import evaluate_policy
from praxis.risk import RiskEngine
from praxis.security import Encryption
from praxis.speaker import SpeakerService


def unavailable(call_id, module, reason, error=False):
    return UnavailableEvent(
        call_id=call_id,
        module=module,
        status=ModuleStatus.ERROR if error else ModuleStatus.UNAVAILABLE,
        artifact_state=ArtifactState.UNVALIDATED,
        reason_codes=[reason],
        timestamp=utcnow(),
    )


class SpeechBuffer:
    """Accumulate novel speech only, omitting overlap by source timestamps."""

    def __init__(self):
        self.parts = []
        self.spans = []
        self.last_end = -1.0
        self.count = 0

    def add(self, window):
        rate = window.contract.analysis_sample_rate
        offset = 0
        for span in window.contract.speech_spans:
            length = round((span.end_ms - span.start_ms) * rate / 1000)
            skip = max(0, min(length, round((self.last_end - span.start_ms) * rate / 1000)))
            if skip < length:
                self.parts.append(window.samples[offset + skip : offset + length].copy())
                self.spans.append((span.start_ms + skip * 1000 / rate, span.end_ms))
                self.count += length - skip
            offset += length
        self.last_end = window.contract.end_ms
        if self.count < 8 * rate:
            return None
        result = (np.concatenate(self.parts), rate, self.spans)
        self.parts, self.spans, self.count = [], [], 0
        return result

    def clear(self):
        self.parts, self.spans, self.count = [], [], 0
        self.last_end = -1.0


class ModelProcessor:
    def __init__(self, runtime, repo, principal):
        self.runtime, self.repo, self.principal = runtime, repo, principal
        self.pipeline = None
        self.windows: asyncio.Queue = asyncio.Queue(maxsize=2)
        self.events: asyncio.Queue = asyncio.Queue(maxsize=64)
        self.speech = SpeechBuffer()
        self.text = ""
        self.previous_mean = None
        self.linguistic_values = {}
        self.linguistic_at = -1.0
        self.linguistic_summary = None
        self.asr_quality_reasons = set()
        self.ai_task = None
        self.closed = False
        self.audio_failed = False
        self.audio_unavailable_reported = False
        self.risk = RiskEngine()
        self.risk_error = False
        if runtime.settings.risk_artifact:
            try:
                self.risk.load(
                    runtime.settings.risk_artifact, runtime.settings.risk_artifact_sha256 or ""
                )
            except (ValueError, OSError):
                self.risk_error = True
        self.worker = asyncio.create_task(self._work())

    async def process(self, session, frame):
        if self.closed:
            raise RuntimeError("Processor closed")
        if self.audio_failed:
            return []
        if self.pipeline is None:
            if (
                "audio" not in self.runtime.health
                or self.runtime.health["audio"].status != ModuleStatus.AVAILABLE
            ):
                if self.audio_unavailable_reported:
                    return []
                self.audio_unavailable_reported = True
                return [unavailable(session.call_id, "audio", "AUDIO_MODEL_UNAVAILABLE")]
            try:
                self.pipeline = await self.runtime.run(AudioPipeline, session.call_id, audio=True)
            except Exception:
                self.audio_failed = True
                return [
                    unavailable(session.call_id, "audio", "AUDIO_INITIALIZATION_FAILED", error=True)
                ]
        try:
            windows = await self.runtime.run(self.pipeline.push, frame, audio=True)
        except ValueError:
            self.pipeline.close()
            self.pipeline = None
            self.speech.clear()
            return [unavailable(session.call_id, "audio", "AUDIO_GAP_BUFFER_RESET")]
        except Exception:
            self.pipeline.close()
            self.audio_failed = True
            return [unavailable(session.call_id, "audio", "AUDIO_PROCESSING_FAILED", error=True)]
        for window in windows:
            if self.windows.full():
                # Drop oldest queued window; never block the receive loop on slow inference.
                self.windows.get_nowait()
                self.windows.task_done()
                await self.events.put(
                    unavailable(session.call_id, "audio", "ANALYSIS_BACKPRESSURE_GAP")
                )
            self.windows.put_nowait((session, window))
        return []

    async def next_event(self):
        return await self.events.get()

    async def _model(self, session, name, method, *args):
        model = self.runtime.models.get(name)
        if model is None:
            return unavailable(session.call_id, name, "MODEL_UNAVAILABLE")
        try:
            return await self.runtime.run(getattr(model, method), *args)
        except Exception:
            return unavailable(session.call_id, name, "MODEL_INFERENCE_FAILED", error=True)

    async def _work(self):
        while True:
            session, window = await self.windows.get()
            try:
                await self._analyze(session, window)
            except Exception:
                await self.events.put(
                    unavailable(session.call_id, "orchestrator", "ANALYSIS_FAILED", error=True)
                )
            finally:
                self.windows.task_done()

    async def _analyze(self, session, window):
        started = perf_counter()
        outputs = [window.contract, unavailable(session.call_id, "acoustic", "DEFERRED_SCOPE")]
        prosody = await self._model(session, "prosody", "analyze", window)
        outputs.append(prosody)
        if "ecapa" in self.runtime.models:
            service = SpeakerService(
                self.repo,
                self.runtime.models["ecapa"],
                Encryption(self.runtime.settings.embedding_key_base64.get_secret_value()),
            )
            try:
                speaker = await self.runtime.run(service.verify, self.principal, session, window)
            except Exception:
                speaker = unavailable(
                    session.call_id, "speaker", "SPEAKER_INFERENCE_FAILED", error=True
                )
        else:
            speaker = unavailable(session.call_id, "speaker", "MODEL_UNAVAILABLE")
        outputs.append(speaker)
        config_raw = await asyncio.to_thread(self.repo.config, self.principal, "context")
        config = (
            ContextConfig.model_validate(config_raw)
            if config_raw
            else ContextConfig(tenant_id=session.tenant_id, version="sih-context-v1")
        )
        context = evaluate_context(session.call_id, session.permitted_context, config)
        outputs.append(context)
        values = {
            "context": context.context_score,
            "prosody": getattr(prosody, "calibrated_score", None),
            "audio_clipping": window.contract.quality.clipping_ratio,
            "audio_silence": window.contract.quality.silence_ratio,
            "audio_completeness": window.contract.quality.completeness,
        }
        values.update(
            {
                "context_" + key: None if flag == RuleFlag.UNKNOWN else float(flag == RuleFlag.TRUE)
                for key, flag in context.flags.items()
            }
        )
        if window.contract.end_ms - self.linguistic_at <= 30000:
            values.update(self.linguistic_values)
        if isinstance(speaker, SpeakerEvidence):
            values["speaker_cosine"] = speaker.cosine_similarity
            if speaker.speaker_state != "UNAVAILABLE":
                values.update(
                    {
                        "speaker_" + name.lower(): float(speaker.speaker_state == name)
                        for name in ["MATCH", "UNCERTAIN", "MISMATCH"]
                    }
                )
        summaries = [
            EvidenceSummary(
                module=getattr(e, "module", "context"),
                status=e.status,
                reason_codes=e.reason_codes,
                model_version=getattr(e, "model_version", None),
            )
            for e in outputs[1:]
        ]
        if (
            self.linguistic_summary is not None
            and window.contract.end_ms - self.linguistic_at <= 30000
        ):
            summaries.append(self.linguistic_summary)
        risk = self.risk.evaluate(
            session.call_id,
            window.contract.window_id,
            values,
            summaries,
            {"audio_completeness": window.contract.quality.completeness},
        )
        outputs.append(
            risk
            if not self.risk_error
            else unavailable(session.call_id, "risk", "RISK_ARTIFACT_REJECTED", error=True)
        )
        if isinstance(risk, RiskEvent):
            policy_raw = await asyncio.to_thread(self.repo.config, self.principal, "policy")
            policy = (
                PolicyConfig.model_validate(policy_raw)
                if policy_raw
                else PolicyConfig(tenant_id=session.tenant_id, policy_version="sih-policy-v1")
            )
            try:
                outputs.append(evaluate_policy(risk, policy, session.supports_hold))
            except ValueError:
                outputs.append(
                    unavailable(session.call_id, "policy", "INSUFFICIENT_INDEPENDENT_EVIDENCE")
                )
        else:
            outputs.append(unavailable(session.call_id, "policy", "RISK_UNAVAILABLE"))
        # Deliver core updates before transcript and experimental model execution.
        for output in outputs:
            await self.events.put(output)
        logging.getLogger("praxis").info(
            "core_analysis_complete",
            extra={
                "session_id": session.session_id,
                "window_id": window.contract.window_id,
                "latency_ms": (perf_counter() - started) * 1000,
            },
        )
        self.asr_quality_reasons.update(window.contract.quality.reason_codes)
        speech = self.speech.add(window)
        if speech is None:
            return
        transcript = await self._model(session, "whisper", "transcribe", session.call_id, *speech)
        if (
            isinstance(transcript, TranscriptEvent)
            and self.asr_quality_reasons
            and transcript.status == ModuleStatus.AVAILABLE
        ):
            transcript.status = ModuleStatus.LOW_QUALITY
            transcript.analysis_english = None
            transcript.reason_codes.append("UPSTREAM_AUDIO_LOW_QUALITY")
        self.asr_quality_reasons.clear()
        await self.events.put(transcript)
        if not isinstance(transcript, TranscriptEvent):
            self.linguistic_values = {}
            self.linguistic_summary = None
            self.text = ""
            await self.events.put(unavailable(session.call_id, "linguistic", "ASR_UNAVAILABLE"))
            return
        rules = analyze_rules(transcript)
        await self.events.put(rules)
        self.linguistic_values = {}
        self.linguistic_summary = None
        if rules.status == ModuleStatus.AVAILABLE:
            from praxis.contracts import LinguisticLabel

            self.linguistic_values = {
                label.value: float(label in rules.rule_labels) for label in LinguisticLabel
            }
            self.linguistic_at = window.contract.end_ms
            self.linguistic_summary = EvidenceSummary(
                module=rules.module,
                status=rules.status,
                reason_codes=rules.reason_codes,
                model_version=rules.model_version,
            )
        await self.events.put(unavailable(session.call_id, "minilm", "CLASSIFIER_HEAD_UNVALIDATED"))
        if transcript.status != ModuleStatus.AVAILABLE or not transcript.analysis_english:
            self.text = ""
            await self.events.put(unavailable(session.call_id, "ai_text", "ASR_LOW_QUALITY"))
            return
        self.text = (self.text + " " + transcript.analysis_english)[-32000:]
        if self.ai_task is None or self.ai_task.done():
            self.ai_task = asyncio.create_task(self._ai(session, self.text))

    async def _ai(self, session, text):
        if self.runtime.ai_lock.locked():
            await self.events.put(unavailable(session.call_id, "ai_text", "LOW_PRIORITY_CAPACITY"))
            return
        async with self.runtime.ai_lock:
            model = self.runtime.models.get("ai_text")
            if model is None:
                result = unavailable(session.call_id, "ai_text", "MODEL_UNAVAILABLE")
            else:
                try:
                    result = await self.runtime.run(
                        model.analyze, session.call_id, text, self.previous_mean, experimental=True
                    )
                    self.previous_mean = result.features.get("mean_token_logprob")
                except Exception:
                    result = unavailable(
                        session.call_id, "ai_text", "MODEL_INFERENCE_FAILED", error=True
                    )
            await self.events.put(result)

    async def close(self):
        self.closed = True
        tasks = [self.worker] + ([self.ai_task] if self.ai_task else [])
        for task in tasks:
            task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError):
                await task
        while not self.windows.empty():
            self.windows.get_nowait()
            self.windows.task_done()
        while not self.events.empty():
            self.events.get_nowait()
        if self.pipeline is not None:
            self.pipeline.close()
        self.speech.clear()
        self.text = ""
