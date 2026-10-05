from collections import Counter
from pathlib import Path
from time import perf_counter

import numpy as np

from praxis.artifacts import verified_model
from praxis.contracts import AIWrittenEvidence, ArtifactState, ModuleStatus, Provenance
from praxis.db.repository import utcnow


class QwenStatistics:
    """Sequential observer/performer forward passes; no text generation or policy access."""

    def __init__(self, artifacts: Path):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        base, self.version = verified_model(artifacts, "qwen_base")
        performer, self.performer_version = verified_model(artifacts, "qwen_performer")
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(base), revision=self.version, local_files_only=True, trust_remote_code=False
        )
        second = AutoTokenizer.from_pretrained(
            str(performer),
            revision=self.performer_version,
            local_files_only=True,
            trust_remote_code=False,
        )
        if self.tokenizer.get_vocab() != second.get_vocab():
            raise ValueError("Qwen tokenizers incompatible")
        self.tokenizer.truncation_side = "left"
        self.base = AutoModelForCausalLM.from_pretrained(
            str(base), revision=self.version, local_files_only=True, trust_remote_code=False
        ).eval()
        self.performer = AutoModelForCausalLM.from_pretrained(
            str(performer),
            revision=self.performer_version,
            local_files_only=True,
            trust_remote_code=False,
        ).eval()

    def analyze(self, call_id, text, previous_mean=None, low_probability_threshold=None):
        started = perf_counter()
        if len(text) > 32000:
            raise ValueError("AI-text input exceeds rolling text limit")
        if previous_mean is not None and not np.isfinite(previous_mean):
            raise ValueError("Previous log probability must be finite")
        if low_probability_threshold is not None and not 0 < low_probability_threshold < 1:
            raise ValueError("Probability threshold outside range")
        text = " ".join(text.split())
        ids = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512, add_special_tokens=False
        )["input_ids"]
        count = ids.shape[1]
        features = {}
        reasons = ["CLASSIFIERS_AND_FUSION_UNVALIDATED"]
        if count < 64:
            status = ModuleStatus.UNAVAILABLE
            reasons = ["INSUFFICIENT_NORMALIZED_TOKENS"]
        else:
            with self.torch.inference_mode():
                observed = self.base(input_ids=ids, use_cache=False).logits.float()
                logp = observed.log_softmax(-1)
                prob = logp.exp()
                targets = ids[:, 1:]
                actual = logp[:, :-1].gather(-1, targets.unsqueeze(-1)).squeeze(-1)
                entropy = -(prob[:, :-1] * logp[:, :-1]).sum(-1)
                # Observer distribution is needed only for cross entropy. Performer runs second.
                performer = (
                    self.performer(input_ids=ids, use_cache=False).logits.float().log_softmax(-1)
                )
                performer_nll = -performer[:, :-1].gather(-1, targets.unsqueeze(-1)).mean()
                # Cross entropy uses all unpadded positions, as in the reference metrics.
                cross_entropy = -(prob * performer).sum(-1).mean()
                mean = float(actual.mean())
                tokens = ids[0].tolist()
                grams = list(zip(tokens, tokens[1:], tokens[2:]))
                counts = Counter(grams)
                features = {
                    "mean_token_logprob": mean,
                    "perplexity": float(np.exp(min(-mean, 80))),
                    "mean_entropy": float(entropy.mean()),
                    "logprob_variance": float(actual.var(unbiased=False)),
                    "low_probability_ratio": float(
                        (actual.exp() < low_probability_threshold).float().mean()
                    )
                    if low_probability_threshold is not None
                    else None,
                    "repeated_trigram_ratio": sum(v - 1 for v in counts.values())
                    / max(1, len(grams)),
                    "high_probability_ratio": float((actual.exp() > 0.9).float().mean()),
                    "rolling_drift": mean - previous_mean if previous_mean is not None else None,
                    "binoculars_raw_ratio": float(performer_nll / cross_entropy)
                    if float(cross_entropy) > 0
                    else None,
                }
            status = ModuleStatus.AVAILABLE
            if low_probability_threshold is None:
                reasons.append("LOW_PROBABILITY_THRESHOLD_UNVALIDATED")
        return AIWrittenEvidence(
            call_id=call_id,
            module="ai_text",
            model_version=self.version + ":" + self.performer_version,
            status=status,
            features=features,
            latency_ms=(perf_counter() - started) * 1000,
            reason_codes=reasons,
            provenance=Provenance(
                model_version=self.version + ":" + self.performer_version,
                artifact_state=ArtifactState.UNVALIDATED,
            ),
            timestamp=utcnow(),
            normalized_token_count=count,
        )
