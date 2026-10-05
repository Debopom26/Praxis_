"""Persistent local models with two inference waves and an evidence barrier."""
import copy
import hashlib
import importlib.util
import json
import os
import struct

# Fixed internal worker with shell disabled.
import subprocess  # nosec B404
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from praxis.supplied.guidance import guidance
from praxis.supplied.minilm import PraxisMiniLMInference
from praxis.supplied.whisper_execution import reuse_encoder


def load_source(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    if spec is None or spec.loader is None:
        raise ValueError("Invalid local module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class W2V2Worker:
    def __init__(self, root, config):
        env = config["w2v2_environment"]
        worker = root / "backend/src/praxis/supplied/worker.py"
        if os.name == "nt":
            linux_root = "/mnt/" + root.drive[0].lower() + root.as_posix()[2:]
            command = [str(Path(os.environ["SystemRoot"]) / "System32/wsl.exe"), "-d", env["distribution"], "--", env["python"], "-u", "-B",
                       linux_root + "/backend/src/praxis/supplied/worker.py", linux_root]
        else:
            command = [env["python"], "-u", "-B", str(worker), str(root)]
        # Operator-owned configuration; no request arguments or shell.
        self.process = subprocess.Popen(  # nosec B603
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL)
        self.lock = threading.Lock()
        try:
            if self.receive().get("status") != "READY":
                raise RuntimeError("W2V2 initialization failed")
        except Exception:
            self.close()
            raise

    def receive(self):
        def read(count):
            value = bytearray()
            while len(value) < count:
                output = self.process.stdout
                if output is None:
                    raise RuntimeError("Missing worker output pipe")
                block = output.read(count - len(value))
                if not block:
                    raise RuntimeError("W2V2 worker disconnected")
                value.extend(block)
            return bytes(value)
        if self.process.stdout is None:
            raise RuntimeError("Missing worker output pipe")
        size = struct.unpack("<I", read(4))[0]
        if size > 1024 * 1024:
            raise RuntimeError("Invalid worker response size")
        return json.loads(read(size))

    def analyze(self, audio):
        with self.lock:
            raw = np.asarray(audio, dtype="<f4").tobytes()
            if self.process.stdin is None:
                raise RuntimeError("Missing worker input pipe")
            self.process.stdin.write(struct.pack("<I", len(raw)) + raw)
            self.process.stdin.flush()
            return self.receive()

    def close(self):
        if self.process.stdin:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        if self.process.stdout:
            self.process.stdout.close()


class SuppliedEngine:
    def __init__(self, model_paths):
        self.root = Path(model_paths).resolve().parent
        self.config = json.loads(Path(model_paths).read_text(encoding="utf-8"))
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        import torch
        from transformers import pipeline
        # Warm thread sweep on this 16-logical-CPU host: 8 beats 2 and 4.
        torch.set_num_threads(min(8, os.cpu_count() or 2))
        self.request_lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix="praxis-v2")
        self.w2v2 = None
        self.ecapa = None
        try:
            runtime = self.asset("imported_runtime")
            self.whisper = pipeline("automatic-speech-recognition", model=str(self.asset("whisper")),
                                    device=-1, chunk_length_s=30)
            self.whisper.model.eval()
            reuse_encoder(self.whisper)
            self.minilm = PraxisMiniLMInference(self.asset("minilm_trained"), device="cpu",
                                                local_model_path=self.asset("minilm_base"))
            if self.minilm.labels != self.config["locked_labels"]:
                raise ValueError("MiniLM label order mismatch")
            qwen = load_source("praxis_supplied_qwen", runtime.parent / "models/qwen_ai_detector/inference.py")
            qwen.MODEL_ID = str(self.asset("qwen_base"))
            self.qwen = qwen.QwenAIScriptDetector(device="cpu")
            self.rules = load_source("praxis_supplied_rules", runtime / "rules_engine.py").PraxisRulesEngine()
            self.context = load_source("praxis_supplied_context", runtime / "context_engine.py").PraxisContextEngine()
            self.prosody = load_source("praxis_supplied_prosody", runtime / "adapters/prosody_feature_adapter.py").PraxisProsodyFeatureAdapter(self.asset("prosody"))
            self.prosody.load()
            self.fusion = load_source("praxis_supplied_fusion", runtime / "fusion_features_v2.py").PraxisFusionFeaturesV2()
            self.risk = load_source("praxis_supplied_risk", runtime / "risk_engine_v2.py").PraxisRiskEngineV2()
            self.w2v2 = W2V2Worker(self.root, self.config)
        except Exception:
            self.close()
            raise

    def asset(self, name):
        result = (self.root / self.config["models"][name]["path"]).resolve()
        if not result.is_relative_to(self.root) or not result.exists():
            raise ValueError("Missing or invalid local model path")
        return result

    def speaker(self, audio, reference):
        if reference is None:
            return {"status": "UNAVAILABLE", "available": False,
                    "reason": "NO_ENROLLED_TRUSTED_SPEAKER"}
        import torch
        from speechbrain.inference.speaker import SpeakerRecognition
        from speechbrain.utils.fetching import LocalStrategy
        if self.ecapa is None:
            source = self.asset("ecapa")
            self.ecapa = SpeakerRecognition.from_hparams(source=str(source),
                savedir=str(self.root / ".cache/supplied-ecapa"),
                overrides={"pretrained_path": str(source)}, local_strategy=LocalStrategy.COPY,
                run_opts={"device": "cpu"})
        with torch.inference_mode():
            vector = self.ecapa.encode_batch(torch.from_numpy(audio).unsqueeze(0)).numpy().reshape(-1)
        reference = np.asarray(reference, dtype=np.float32).reshape(-1)
        if reference.shape != (192,) or not np.isfinite(reference).all() or not np.linalg.norm(reference):
            raise ValueError("Invalid enrollment")
        similarity = float(np.dot(vector, reference) / (np.linalg.norm(vector) * np.linalg.norm(reference)))
        return {"status": "AVAILABLE", "available": True, "cosine_similarity": similarity,
                "threshold_state": "UNVALIDATED", "identity_risk": None}

    def analyze(self, samples, host_context=None, trusted_embedding=None, *, transcript_samples=None, text_cache=None):
        audio = np.asarray(samples, dtype=np.float32).reshape(-1)
        if not 16000 <= len(audio) <= 120 * 16000 or not np.isfinite(audio).all():
            raise ValueError("Expected 1-120 seconds of finite mono 16kHz PCM")
        speech = audio if transcript_samples is None else np.asarray(transcript_samples, dtype=np.float32).reshape(-1)
        if not 16000 <= len(speech) <= len(audio) or not np.isfinite(speech).all():
            raise ValueError("Invalid new speech samples")
        if not self.request_lock.acquire(blocking=False):
            raise RuntimeError("ANALYSIS_BUSY")
        audit = {}
        def timed(name, fn, *args):
            start = datetime.now(timezone.utc).isoformat()
            tick = time.perf_counter()
            try:
                import torch
                with torch.inference_mode():
                    result = fn(*args)
                status = result.get("status", "SUCCESS") if isinstance(result, dict) else "SUCCESS"
                return result
            except Exception:
                status = "ERROR"
                return {"available": False, "status": "ERROR", "reason": "INFERENCE_FAILED"}
            finally:
                audit[name] = {"started_at": start,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "latency_ms": round((time.perf_counter() - tick) * 1000, 2),
                    "status": status, "worker_id": threading.current_thread().name}
        def cached(name, fn, text):
            if text_cache is None:
                return fn(text)
            key = hashlib.sha256(text.encode()).hexdigest()
            previous = text_cache.get(name)
            if previous is not None and previous[0] == key:
                return copy.deepcopy(previous[1])
            result = fn(text)
            if result.get("status") != "ERROR":
                text_cache[name] = (key, copy.deepcopy(result))
            return result
        def submit(name, fn, *args):
            return self.pool.submit(timed, name, fn, *args)
        try:
            if self.w2v2 is None:
                raise RuntimeError("ACOUSTIC_EVIDENCE_UNAVAILABLE")
            wave_a = {"w2v2": submit("w2v2", self.w2v2.analyze, audio),
                "prosody": submit("prosody", self.prosody.analyze, audio),
                "whisper": submit("whisper", self.whisper, {"array": speech, "sampling_rate": 16000}),
                "context": submit("context", lambda: self.context.analyze(**(host_context or {}))),
                "ecapa": submit("ecapa", self.speaker, audio, trusted_embedding)}
            transcript = str(wave_a["whisper"].result().get("text", "")).strip()
            wave_b = {"minilm": submit("minilm", cached, "minilm", self.minilm.analyze, transcript),
                      "rules": submit("rules", self.rules.analyze, transcript),
                      "qwen": submit("qwen", cached, "qwen", self.qwen.predict, transcript)}
            evidence = {name: job.result() for name, job in {**wave_a, **wave_b}.items()}
            qwen = evidence["qwen"]
            qwen = dict(qwen, probability=qwen.get("ai_script_probability"),
                        available=qwen.get("status") == "OK")
            context = evidence["context"]
            context = dict(context.get("features", {}),
                           available=context.get("available_features", 0) > 0,
                           status=context.get("status", "ERROR"))
            if not evidence["w2v2"].get("available"):
                raise RuntimeError("ACOUSTIC_EVIDENCE_UNAVAILABLE")
            fusion = timed("fusion", lambda: self.fusion.build(w2v2=evidence["w2v2"],
                prosody=evidence["prosody"], minilm=evidence["minilm"], rules=evidence["rules"],
                qwen=qwen, context=context, ecapa=evidence["ecapa"]))
            risk = timed("risk", self.risk.score, fusion)
            if "risk_score" not in risk:
                raise RuntimeError("RISK_ENGINE_UNAVAILABLE")
            advice = timed("policy", guidance, transcript, evidence["w2v2"], evidence["minilm"])
            return {"schema_version": "praxis-supplied-2.1", "status": "AVAILABLE",
                "synthetic_voice": {"detected": evidence["w2v2"]["predicted_class"] == "spoof",
                    "score_0_100": evidence["w2v2"]["spoof_softmax"] * 100,
                    "score_semantics": "uncalibrated_model_output"},
                "experimental_score_0_100": risk["risk_score"],
                "regressor_status": risk["regressor_status"], "scam_probability": None,
                "guidance": advice, "audit": audit, "ecapa": evidence["ecapa"],
                "transcript_available": bool(transcript),
                "module_status": {k: v.get("status", "AVAILABLE") for k, v in evidence.items()},
                "raw_audio_retained": False}
        finally:
            self.request_lock.release()

    def health(self):
        alive = self.w2v2 is not None and self.w2v2.process.poll() is None
        return {"status": "AVAILABLE" if alive else "ERROR",
                "components": {"w2v2": "AVAILABLE" if alive else "ERROR",
                    "whisper": "AVAILABLE", "minilm": "AVAILABLE", "qwen": "AVAILABLE",
                    "prosody": "AVAILABLE", "rules": "AVAILABLE", "context": "AVAILABLE",
                    "ecapa": "AVAILABLE" if self.ecapa is not None else "NOT_LOADED_NO_ENROLLMENT"},
                "regressor_status": "BOOTSTRAP_UNTRAINED", "scam_probability_available": False,
                "raw_audio_retained": False}

    def close(self):
        if hasattr(self, "pool"):
            self.pool.shutdown(wait=True, cancel_futures=True)
        if self.w2v2:
            self.w2v2.close()
            self.w2v2 = None
