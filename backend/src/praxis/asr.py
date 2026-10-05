from math import gcd
from pathlib import Path
from threading import Lock
from time import perf_counter

import numpy as np
from scipy.signal import resample_poly

from praxis.artifacts import verified_model
from praxis.contracts import ModuleStatus, TranscriptEvent, TranscriptSegment
from praxis.db.repository import utcnow


class WhisperSmall:
    def __init__(self, artifacts: Path):
        import whisper

        directory, self.version = verified_model(artifacts, "whisper")
        self.model = whisper.load_model(str(directory / "small.pt"), device="cpu")
        self.lock = Lock()

    def transcribe(
        self,
        call_id: str,
        samples: np.ndarray,
        sample_rate: int,
        source_spans: list[tuple[float, float]],
    ) -> TranscriptEvent:
        started = perf_counter()
        if sample_rate <= 0 or samples.ndim != 1 or not np.isfinite(samples).all():
            raise ValueError("Finite mono audio and positive sample rate required")
        if (
            not source_spans
            or any(
                not np.isfinite([start, end]).all() or start < 0 or end <= start
                for start, end in source_spans
            )
            or any(left[1] > right[0] for left, right in zip(source_spans, source_spans[1:]))
        ):
            raise ValueError("Ordered nonempty source spans required")
        if (
            abs(sum(end - start for start, end in source_spans) - len(samples) * 1000 / sample_rate)
            > 2
        ):
            raise ValueError("Source spans do not match speech duration")
        factor = gcd(sample_rate, 16000)
        audio = resample_poly(samples, 16000 // factor, sample_rate // factor).astype(np.float32)
        if not 1 <= len(audio) / 16000 <= 30:
            raise ValueError("ASR buffer duration out of bounds")
        with self.lock:
            result = self.model.transcribe(
                audio,
                task="transcribe",
                fp16=False,
                temperature=0,
                condition_on_previous_text=False,
            )
            translation_result = (
                self.model.transcribe(
                    audio,
                    task="translate",
                    fp16=False,
                    temperature=0,
                    condition_on_previous_text=False,
                )
                if result["language"] != "en"
                else result
            )

        def source_time(seconds):
            remaining = max(0, seconds * 1000)
            for start, end in source_spans:
                if remaining <= end - start:
                    return start + remaining
                remaining -= end - start
            return source_spans[-1][1]

        segments = [
            TranscriptSegment(
                start_ms=source_time(s["start"]), end_ms=source_time(s["end"]), text=s["text"]
            )
            for s in result["segments"]
        ]
        poor = not segments or any(
            s.get("avg_logprob", 0) < -1
            or s.get("no_speech_prob", 0) > 0.6
            or s.get("compression_ratio", 0) > 2.4
            for s in result["segments"] + translation_result["segments"]
        )
        return TranscriptEvent(
            call_id=call_id,
            text=result["text"].strip(),
            language=result["language"],
            segments=segments,
            quality=None,
            status=ModuleStatus.LOW_QUALITY if poor else ModuleStatus.AVAILABLE,
            model_version=self.version,
            latency_ms=(perf_counter() - started) * 1000,
            timestamp=utcnow(),
            analysis_english=translation_result["text"].strip() if not poor else None,
            reason_codes=["ASR_HEURISTIC_LOW_QUALITY"] if poor else [],
        )
