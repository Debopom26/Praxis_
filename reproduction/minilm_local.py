
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer


class MiniLMEncoder(nn.Module):
    """
    Wrapper name intentionally preserves checkpoint keys:
        transformer.model.*
    """

    def __init__(self, model_id, revision):
        super().__init__()

        self.model = AutoModel.from_pretrained(
            model_id,
            revision=revision
        )

    def forward(self, input_ids, attention_mask):

        out = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )

        # SentenceTransformer-compatible masked mean pooling
        token_embeddings = out.last_hidden_state

        mask = (
            attention_mask
            .unsqueeze(-1)
            .expand(token_embeddings.size())
            .float()
        )

        pooled = (
            (token_embeddings * mask).sum(1)
            / mask.sum(1).clamp(min=1e-9)
        )

        return pooled


class PraxisMiniLMClassifier(nn.Module):

    def __init__(
        self,
        model_id,
        revision,
        num_labels=8
    ):
        super().__init__()

        self.transformer = MiniLMEncoder(
            model_id,
            revision
        )

        hidden = self.transformer.model.config.hidden_size

        if hidden != 384:
            raise RuntimeError(
                f"Expected hidden size 384, got {hidden}"
            )

        self.classifier = nn.Linear(
            hidden,
            num_labels
        )

    def forward(
        self,
        input_ids,
        attention_mask
    ):

        pooled = self.transformer(
            input_ids,
            attention_mask
        )

        return self.classifier(pooled)


class PraxisMiniLMInference:

    VERSION = "1.0.0"

    def __init__(
        self,
        artifact_dir="/content/drive/MyDrive/Praxis_MiniLM_Handoff",
        device=None,
        local_model_path=None
    ):

        self.artifact_dir = Path(artifact_dir)

        self.device = (
            device
            or ("cuda" if torch.cuda.is_available() else "cpu")
        )

        config = json.loads(
            (self.artifact_dir / "training_config.json")
            .read_text()
        )

        self.model_id = str(local_model_path) if local_model_path else config["base_model"]
        self.revision = config["revision"]
        self.max_length = config["max_length"]

        self.labels = config["labels"]

        self.thresholds = json.loads(
            (self.artifact_dir / "thresholds.json")
            .read_text()
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            revision=self.revision
        )

        self.model = PraxisMiniLMClassifier(
            self.model_id,
            self.revision,
            len(self.labels)
        )

        checkpoint = torch.load(
            self.artifact_dir / "BEST_MODEL.pt",
            map_location="cpu"
        )

        state = checkpoint["model_state_dict"]

        # STRICT means every one of the 201 tensors must match.
        result = self.model.load_state_dict(
            state,
            strict=True
        )

        if result.missing_keys or result.unexpected_keys:
            raise RuntimeError(
                f"Checkpoint mismatch: {result}"
            )

        self.model.to(self.device)
        self.model.eval()

        self.checkpoint_epoch = checkpoint.get("epoch")
        self.checkpoint_model_id = checkpoint.get("model_id")
        self.checkpoint_revision = checkpoint.get(
            "model_revision"
        )

    @torch.inference_mode()
    def analyze(self, text):

        start = time.perf_counter()

        if not isinstance(text, str) or not text.strip():

            return {
                "available": False,
                "status": "UNAVAILABLE",
                "model": "minilm",
                "probabilities": None,
                "triggered_labels": [],
                "max_probability": None,
                "error": "EMPTY_TRANSCRIPT"
            }

        encoded = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
            padding=True
        )

        encoded = {
            k: v.to(self.device)
            for k, v in encoded.items()
        }

        logits = self.model(
            input_ids=encoded["input_ids"],
            attention_mask=encoded["attention_mask"]
        )

        probs = torch.sigmoid(
            logits
        )[0].detach().cpu().tolist()

        probabilities = {
            label: float(prob)
            for label, prob in zip(
                self.labels,
                probs
            )
        }

        triggered = [
            label
            for label in self.labels
            if probabilities[label]
            >= float(self.thresholds[label])
        ]

        latency_ms = (
            time.perf_counter() - start
        ) * 1000

        return {
            "available": True,
            "status": "AVAILABLE",
            "model": "minilm",
            "model_id": self.model_id,
            "version": self.VERSION,

            # Exact schema required by PraxisRiskEngine._minilm()
            "probabilities": probabilities,

            "thresholds": {
                k: float(v)
                for k, v in self.thresholds.items()
            },

            "triggered_labels": triggered,
            "max_probability": max(
                probabilities.values()
            ),

            "latency_ms": round(
                latency_ms,
                2
            ),

            "error": None
        }


_instance = None


def get_detector():

    global _instance

    if _instance is None:
        _instance = PraxisMiniLMInference()

    return _instance


def analyze_transcript(text):

    return get_detector().analyze(text)
