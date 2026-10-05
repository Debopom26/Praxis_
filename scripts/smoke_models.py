"""Actual pretrained inference on synthetic fixtures; not accuracy or enrollment validation."""
import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import torch

parser = argparse.ArgumentParser()
parser.add_argument("model", choices=["whisper", "ecapa", "minilm", "qwen"])
args = parser.parse_args()
torch.set_num_threads(2)
root = Path(__file__).resolve().parents[1]
start = perf_counter()
result = {"model": args.model, "fixture": "SYNTHETIC_TEST_ONLY", "accuracy_validated": False}
wave = (0.1 * np.sin(2 * np.pi * 120 * np.arange(64000) / 16000)).astype(np.float32)
if args.model == "whisper":
    from praxis.asr import WhisperSmall
    model = WhisperSmall(root / "artifacts")
    event = model.transcribe("test-smoke", np.zeros(64000, np.float32), 16000, [(0, 4000)])
    result.update(version=model.version, status=event.status, segments=len(event.segments))
elif args.model == "ecapa":
    from praxis.speaker import ECAPA
    model = ECAPA(root / "artifacts")
    vector = model.embed(wave, 16000)
    if vector.size != 192 or not np.isfinite(vector).all():
        raise RuntimeError("Invalid ECAPA embedding")
    result.update(version=model.version, dimensions=vector.size, norm=float(np.linalg.norm(vector)))
elif args.model == "minilm":
    from praxis.linguistic import MiniLM
    model = MiniLM(root / "artifacts")
    vector = model.embed("Synthetic software verification text. No classifier validation.")
    if vector.size != 384 or not np.isfinite(vector).all():
        raise RuntimeError("Invalid MiniLM embedding")
    result.update(version=model.version, dimensions=vector.size, classifier_state=model.classifier_state)
else:
    from praxis.ai_text import QwenStatistics
    model = QwenStatistics(root / "artifacts")
    short = model.analyze("test-smoke", "short text")
    if short.status != "UNAVAILABLE":
        raise RuntimeError("Token gate failed")
    event = model.analyze("test-smoke", "This paragraph is synthetic software verification text. It only tests numerical execution of language model statistics and cannot establish whether a person or a machine wrote a real message. We will inspect the actual returned probabilities, entropy, and model compatibility. No threshold or calibrated classification is supplied by this test. The result is not a fraud decision or an identity claim. All generated values are measured forward pass outputs on an explicitly artificial test input.")
    if event.status != "AVAILABLE" or event.calibrated_score is not None:
        raise RuntimeError("Unexpected AI-text status")
    result.update(version=event.model_version, status=event.status, tokens=event.normalized_token_count, features=event.features)
result["elapsed_seconds"] = round(perf_counter() - start, 3)
out = root / ".cache" / ("smoke-" + args.model + ".json")
out.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result), flush=True)
