import re
from pathlib import Path
from time import perf_counter

import numpy as np

from praxis.artifacts import verified_model
from praxis.contracts import (
    ArtifactState,
    LinguisticEvidence,
    LinguisticLabel,
    ModuleStatus,
    Provenance,
)
from praxis.db.repository import utcnow

PATTERNS = {
    "urgency": r"\b(?:act now|immediately|right now|within (?:five|5|ten|10) minutes)\b",
    "secrecy": r"\b(?:do not tell|don't tell|keep (?:this|it) (?:secret|between us))\b",
    "authority_pressure": r"\b(?:i am|this is|speaking from) (?:your |the )?(?:ceo|bank manager|police|government|technical support)\b",
    "financial_request": r"\b(?:send|transfer|pay|wire) (?:the |me |this |your )?(?:money|funds|payment|amount|rupees)\b",
    "credential_request": r"\b(?:share|send|give|tell|read) (?:me |us )?(?:your |the )?(?:otp|password|pin|verification code)\b",
    "verification_bypass": r"\b(?:skip|bypass|ignore|disable) (?:the |your )?(?:verification|approval|security check|mfa)\b",
    "coercion": r"\b(?:you will be arrested|legal action against you|your account will be (?:closed|blocked)|we will arrest)\b",
    "emotional_pressure": r"\b(?:please help me|my life depends on|your (?:son|daughter|child) is in (?:danger|hospital)|you have won)\b",
}
PROTECTIVE = re.compile(
    r"\b(?:never|do not|don't)\s+(?:share|send|give|tell|read|transfer|pay|wire|skip|bypass|ignore|disable)\b",
    re.I,
)


def analyze_rules(transcript):
    started = perf_counter()
    labels = []
    reasons = []
    valid = transcript.status == ModuleStatus.AVAILABLE and transcript.language == "en"
    if valid:
        for sentence in re.split(r"[.!?;]", transcript.text.casefold()):
            for name, pattern in PATTERNS.items():
                if re.search(pattern, sentence) and not (
                    name in {"credential_request", "financial_request", "verification_bypass"}
                    and PROTECTIVE.search(sentence)
                ):
                    labels.append(LinguisticLabel(name))
                    reasons.append("RULE_" + name.upper())
    else:
        reasons.append("ASR_OR_RULE_LANGUAGE_UNAVAILABLE")
    return LinguisticEvidence(
        call_id=transcript.call_id,
        module="linguistic_rules",
        model_version="rules-en-1.0.0",
        status=ModuleStatus.AVAILABLE if valid else ModuleStatus.UNAVAILABLE,
        latency_ms=(perf_counter() - started) * 1000,
        reason_codes=sorted(set(reasons)),
        provenance=Provenance(
            model_version="rules-en-1.0.0", artifact_state=ArtifactState.UNVALIDATED
        ),
        timestamp=utcnow(),
        rule_labels=sorted(set(labels)),
        classifier_state=ArtifactState.UNVALIDATED,
    )


class MiniLM:
    def __init__(self, artifacts: Path):
        from sentence_transformers import SentenceTransformer

        directory, self.version = verified_model(artifacts, "minilm")
        self.encoder = SentenceTransformer(
            str(directory), device="cpu", local_files_only=True, trust_remote_code=False
        )

    def embed(self, text: str) -> np.ndarray:
        if not text.strip() or len(text) > 32000:
            raise ValueError("Invalid MiniLM text length")
        return self.encoder.encode(text, convert_to_numpy=True, normalize_embeddings=True)

    @property
    def classifier_state(self):
        return ArtifactState.UNVALIDATED
