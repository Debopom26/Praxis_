"""Length-framed, memory-only, persistent Python 3.10 W2V2 worker."""
import contextlib
import importlib
import json
import struct
import sys
from pathlib import Path

import numpy as np
import torch

root = Path(sys.argv[1]).resolve()
config = json.loads((root / "model_paths.json").read_text())
sys.path.insert(0, str(root / "reproduction/w2v2_runtime"))
W2V2AASISTAdapter = importlib.import_module("adapters.w2v2_adapter").W2V2AASISTAdapter

protocol = sys.stdout.buffer

def send(value):
    raw = json.dumps(value).encode()
    protocol.write(struct.pack("<I", len(raw)) + raw)
    protocol.flush()

def read_exact(count):
    result = bytearray()
    while len(result) < count:
        block = sys.stdin.buffer.read(count - len(result))
        if not block:
            raise EOFError
        result.extend(block)
    return bytes(result)

try:
    with contextlib.redirect_stdout(sys.stderr):
        torch.set_num_threads(2)
        def asset(name):
            return str(root / config["models"][name]["path"])
        adapter = W2V2AASISTAdapter({"checkpoint": asset("w2v2_checkpoint"),
            "xlsr_checkpoint": asset("xlsr_fairseq0122"), "repo": asset("w2v2_source")}, device="cpu")
        adapter.load()
    send({"status": "READY"})
    while True:
        size = struct.unpack("<I", read_exact(4))[0]
        if not 16000 <= size <= 16000 * 120 * 4 or size % 4:
            raise ValueError("Invalid PCM frame")
        audio = np.frombuffer(read_exact(size), dtype="<f4")
        if not np.isfinite(audio).all():
            raise ValueError("Non-finite audio")
        results = []
        with contextlib.redirect_stdout(sys.stderr), torch.inference_mode():
            start = 0
            while start < len(audio):
                chunk = audio[start:start + 64000]
                if len(chunk) < 64000:
                    chunk = np.tile(chunk, int(np.ceil(64000 / len(chunk))))[:64000]
                results.append(adapter.analyze(chunk))
                if start + 64000 >= len(audio):
                    break
                start += 32000
        if not all(r.get("available") for r in results):
            send({"status": "ERROR", "available": False, "reason": "W2V2_INFERENCE_FAILED"})
        else:
            send(dict(max(results, key=lambda r: r["spoof_softmax"]),
                      status="AVAILABLE", window_count=len(results)))
except EOFError:
    pass
except Exception as exc:
    send({"status": "ERROR", "available": False, "reason": type(exc).__name__})
