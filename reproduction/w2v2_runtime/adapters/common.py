
import re
import time
import torch
import numpy as np
import torch.nn as nn


CANONICAL_SAMPLES = 64000


def canonical_audio(audio):
    x = np.asarray(audio, dtype=np.float32).reshape(-1)

    if len(x) != CANONICAL_SAMPLES:
        raise ValueError(
            f"Expected {CANONICAL_SAMPLES} samples, got {len(x)}"
        )

    if not np.isfinite(x).all():
        raise ValueError("Audio contains NaN/Inf")

    return x


def extract_state(artifact, keys):
    for key in keys:
        if key in artifact:
            return artifact[key]

    if all(torch.is_tensor(v) for v in artifact.values()):
        return artifact

    raise KeyError(f"Could not find state dict. Tried: {keys}")


def load_state_flexible(model, state):
    """
    Load a state dict even if training wrapper added prefixes such as
    model., wavlm., backbone., module., etc.
    """

    target = model.state_dict()
    mapped = {}

    for target_key in target:

        if target_key in state:
            mapped[target_key] = state[target_key]
            continue

        matches = [
            k for k in state
            if k.endswith("." + target_key)
        ]

        if len(matches) == 1:
            mapped[target_key] = state[matches[0]]

    missing = [
        k for k in target
        if k not in mapped
    ]

    if missing:
        preview = missing[:10]
        raise RuntimeError(
            f"Checkpoint mismatch. Missing {len(missing)} keys. "
            f"First missing keys: {preview}"
        )

    model.load_state_dict(mapped, strict=True)


def logits_to_evidence(logits):

    if isinstance(logits, (tuple, list)):
        logits = logits[-1]

    if logits.ndim == 1:
        logits = logits.unsqueeze(0)

    if logits.shape[-1] != 2:
        raise RuntimeError(
            f"Expected 2 logits, got shape {tuple(logits.shape)}"
        )

    logits = logits.float()

    probs = torch.softmax(
        logits,
        dim=-1
    )[0]

    # Praxis convention:
    # spoof = 0
    # bonafide = 1

    return {
        "raw_spoof_logit":
            float(logits[0, 0].detach().cpu()),

        "raw_bonafide_logit":
            float(logits[0, 1].detach().cpu()),

        "spoof_softmax":
            float(probs[0].detach().cpu()),

        "bonafide_softmax":
            float(probs[1].detach().cpu()),

        "predicted_class":
            "spoof"
            if probs[0] >= probs[1]
            else "bonafide"
    }


class BaseAdapter:

    name = "base"

    def __init__(self, paths, device="cpu"):
        self.paths = paths

        if device == "auto":
            device = (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )

        self.device = torch.device(device)
        self.loaded = False
        self.model = None


    def load(self):
        if not self.loaded:
            self._load()
            self.loaded = True


    def analyze(self, audio):

        started = time.perf_counter()

        try:
            x = canonical_audio(audio)

            self.load()

            with torch.inference_mode():
                evidence = self._predict(x)

            evidence.update({
                "model": self.name,
                "available": True,
                "device": str(self.device),
                "latency_ms": round(
                    (time.perf_counter() - started) * 1000,
                    2
                ),
                "error": None
            })

            return evidence

        except Exception as e:

            return {
                "model": self.name,
                "available": False,
                "raw_spoof_logit": None,
                "raw_bonafide_logit": None,
                "spoof_softmax": None,
                "bonafide_softmax": None,
                "predicted_class": None,
                "device": str(self.device),
                "latency_ms": round(
                    (time.perf_counter() - started) * 1000,
                    2
                ),
                "error":
                    f"{type(e).__name__}: {e}"
            }


class StateDictMLP(nn.Module):
    """
    Reconstruct the frozen Praxis WavLM classifier from the actual
    Linear weight tensors in classifier_state_dict.

    Expected Praxis dimensions:
        768 -> 256 -> 64 -> 2
    """

    def __init__(self, state):
        super().__init__()

        def natural_key(s):
            return [
                int(x) if x.isdigit() else x
                for x in re.split(r"(\d+)", s)
            ]

        weights = sorted(
            [
                (k, v)
                for k, v in state.items()
                if torch.is_tensor(v)
                and v.ndim == 2
                and k.endswith("weight")
            ],
            key=lambda x: natural_key(x[0])
        )

        if len(weights) != 3:
            raise RuntimeError(
                "Expected 3 classifier Linear layers, "
                f"found {len(weights)}: "
                f"{[k for k, _ in weights]}"
            )

        dims = [
            (
                int(w.shape[1]),
                int(w.shape[0])
            )
            for _, w in weights
        ]

        expected = [
            (768, 256),
            (256, 64),
            (64, 2)
        ]

        if dims != expected:
            raise RuntimeError(
                f"Unexpected WavLM classifier dimensions: {dims}; "
                f"expected {expected}"
            )

        self.layers = nn.ModuleList([
            nn.Linear(768, 256),
            nn.Linear(256, 64),
            nn.Linear(64, 2)
        ])

        # Copy trained parameters independent of their original key names.
        for layer, (weight_key, weight) in zip(
            self.layers,
            weights
        ):
            layer.weight.data.copy_(weight)

            base = weight_key[:-len("weight")]
            bias_key = base + "bias"

            if bias_key not in state:
                raise RuntimeError(
                    f"Missing classifier bias: {bias_key}"
                )

            layer.bias.data.copy_(
                state[bias_key]
            )


    def forward(self, x):
        # Dropout is irrelevant in eval mode.
        # Praxis training classifier:
        # 768 -> 256 -> 64 -> 2

        x = torch.relu(
            self.layers[0](x)
        )

        x = torch.relu(
            self.layers[1](x)
        )

        return self.layers[2](x)
