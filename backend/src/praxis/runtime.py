"""Bounded model lifetime and separate core/experimental execution lanes."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from importlib import import_module

from praxis.contracts import ArtifactState, ComponentHealth, ModuleStatus


class Runtime:
    def __init__(self, settings):
        self.settings = settings
        self.models = {}
        self.supplied = None
        self.supplied_error = None
        self.health = {}
        self.core = ThreadPoolExecutor(
            max_workers=settings.inference_workers, thread_name_prefix="praxis-core"
        )
        self.experimental = ThreadPoolExecutor(max_workers=1, thread_name_prefix="praxis-ai-text")
        self.audio = ThreadPoolExecutor(max_workers=2, thread_name_prefix="praxis-audio")
        self.ai_lock = asyncio.Lock()
        self.risk_state = ArtifactState.UNVALIDATED
        self.risk_version = None

    def load(self):
        if self.settings.risk_artifact:
            from praxis.risk import RiskEngine

            try:
                risk = RiskEngine()
                risk.load(self.settings.risk_artifact, self.settings.risk_artifact_sha256 or "")
                self.risk_state = ArtifactState.VALIDATED
                self.risk_version = risk.artifact.version if risk.artifact else None
                self.health["risk"] = ComponentHealth(
                    status=ModuleStatus.AVAILABLE, version=self.risk_version
                )
            except (ValueError, OSError):
                self.health["risk"] = ComponentHealth(
                    status=ModuleStatus.ERROR, reason_codes=["RISK_ARTIFACT_REJECTED"]
                )
        if self.settings.supplied_models_enabled:
            try:
                if self.settings.supplied_worker_url:
                    from praxis.supplied.remote import RemoteSuppliedEngine

                    self.supplied = RemoteSuppliedEngine(
                        self.settings.supplied_worker_url,
                        self.settings.supplied_worker_token.get_secret_value(),
                    )
                else:
                    from praxis.supplied.engine import SuppliedEngine

                    self.supplied = SuppliedEngine(self.settings.model_paths_file)
            except Exception:
                self.supplied_error = "SUPPLIED_MODELS_INITIALIZATION_FAILED"
        if not self.settings.models_enabled:
            return
        import torch

        torch.set_num_threads(self.settings.torch_threads)
        adapters = {
            "audio": ("praxis.audio.pipeline", "SileroVad", ()),
            "whisper": ("praxis.asr", "WhisperSmall", (self.settings.artifacts_dir,)),
            "ecapa": ("praxis.speaker", "ECAPA", (self.settings.artifacts_dir,)),
            "prosody": ("praxis.prosody", "Prosody", ()),
            "minilm": ("praxis.linguistic", "MiniLM", (self.settings.artifacts_dir,)),
            "ai_text": ("praxis.ai_text", "QwenStatistics", (self.settings.artifacts_dir,)),
        }
        for name, (module, constructor, arguments) in adapters.items():
            try:
                model = getattr(import_module(module), constructor)(*arguments)
                if name != "audio":
                    self.models[name] = model
                self.health[name] = ComponentHealth(
                    status=ModuleStatus.AVAILABLE, version=getattr(model, "version", None)
                )
            except Exception:
                # No third-party exception strings: they can contain paths or input data.
                self.health[name] = ComponentHealth(
                    status=ModuleStatus.ERROR, reason_codes=["MODEL_INITIALIZATION_FAILED"]
                )

    async def run(self, function, *args, experimental=False, audio=False):
        future = asyncio.get_running_loop().run_in_executor(
            self.audio if audio else self.experimental if experimental else self.core,
            partial(function, *args),
        )
        try:
            return await asyncio.shield(future)
        except asyncio.CancelledError:
            # A running native model cannot be cancelled; retain its bounded slot until it exits.
            try:
                await future
            finally:
                raise

    async def close(self):
        await asyncio.to_thread(self.core.shutdown, wait=True, cancel_futures=True)
        await asyncio.to_thread(self.experimental.shutdown, wait=True, cancel_futures=True)
        await asyncio.to_thread(self.audio.shutdown, wait=True, cancel_futures=True)
        self.models.clear()
        if self.supplied is not None:
            await asyncio.to_thread(self.supplied.close)
