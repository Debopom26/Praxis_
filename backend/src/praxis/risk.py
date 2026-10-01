"""Inference-only regularized logistic artifact path; no training or fallback coefficients."""

import hashlib
import math
from pathlib import Path

import numpy as np
from pydantic import Field, model_validator
from sklearn.linear_model import LogisticRegression

from praxis.contracts import (
    ArtifactState,
    Contract,
    EvidenceSummary,
    LinguisticLabel,
    ModuleStatus,
    RiskEvent,
    UnavailableEvent,
)
from praxis.contracts.context import CONTEXT_RULES
from praxis.db.repository import utcnow

FEATURES = (
    "acoustic",
    "prosody",
    "speaker_cosine",
    "speaker_match",
    "speaker_uncertain",
    "speaker_mismatch",
    *tuple(label.value for label in LinguisticLabel),
    "linguistic_aggregate",
    "ai_text",
    "context",
    *tuple("context_" + rule for rule in CONTEXT_RULES),
    "audio_clipping",
    "audio_silence",
    "audio_completeness",
    "asr_quality",
)
FEATURE_VERSION = "1.1.0"


class RiskArtifact(Contract):
    version: str
    feature_version: str
    features: list[str]
    validation_report: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    split_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_version: str = Field(min_length=1)
    regularization_c: float = Field(gt=0)
    means: list[float]
    scales: list[float]
    coefficients: list[float]
    intercept: float

    @model_validator(mode="after")
    def check(self):
        n = len(FEATURES)
        if self.feature_version != FEATURE_VERSION or tuple(self.features) != FEATURES:
            raise ValueError("Risk feature schema mismatch")
        if (
            len(self.means) != n
            or len(self.scales) != n
            or len(self.coefficients) != 2 * n
            or any(v <= 0 for v in self.scales)
        ):
            raise ValueError("Risk preprocessing dimensions invalid")
        return self


class EMA:
    def __init__(self, alpha: float = 0.35):
        if not 0 < alpha <= 1:
            raise ValueError("EMA alpha outside range")
        self.alpha = alpha
        self.value: float | None = None

    def update(self, value: float) -> float:
        if not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError("Invalid risk")
        self.value = (
            value if self.value is None else self.alpha * value + (1 - self.alpha) * self.value
        )
        return self.value


def feature_vector(values: dict[str, float | None]) -> np.ndarray:
    if set(values) - set(FEATURES):
        raise ValueError("Unknown risk feature")
    output = np.array(
        [np.nan if values.get(k) is None else values[k] for k in FEATURES], dtype=float
    )
    if np.isinf(output).any():
        raise ValueError("Infinite risk feature")
    return output


class RiskEngine:
    def __init__(self):
        self.artifact: RiskArtifact | None = None
        self.model = None
        self.ema = EMA()

    def load(self, path: Path, approved_sha256: str) -> None:
        if not approved_sha256 or path.stat().st_size > 1024 * 1024:
            raise ValueError("Artifact approval/size invalid")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != approved_sha256:
            raise ValueError("Unapproved artifact hash")
        artifact = RiskArtifact.model_validate_json(raw)
        model = LogisticRegression(C=artifact.regularization_c)
        model.classes_ = np.array([0, 1])
        model.coef_ = np.array([artifact.coefficients])
        model.intercept_ = np.array([artifact.intercept])
        model.n_features_in_ = 2 * len(FEATURES)
        self.artifact = artifact
        self.model = model
        self.ema = EMA()

    def preprocess(self, values: dict[str, float | None]) -> tuple[np.ndarray, dict[str, bool]]:
        if self.artifact is None:
            raise ValueError("UNVALIDATED")
        raw = feature_vector(values)
        missing = np.isnan(raw)
        filled = np.where(missing, np.array(self.artifact.means), raw)
        scaled = (filled - np.array(self.artifact.means)) / np.array(self.artifact.scales)
        return np.concatenate((scaled, missing.astype(float))).reshape(1, -1), dict(
            zip(FEATURES, missing.tolist(), strict=True)
        )

    def evaluate(
        self,
        call_id: str,
        window_id: str,
        values: dict[str, float | None],
        evidence: list[EvidenceSummary],
        quality: dict[str, float | None],
    ):
        if self.artifact is None or self.model is None:
            return UnavailableEvent(
                call_id=call_id,
                module="risk",
                status=ModuleStatus.UNAVAILABLE,
                artifact_state=ArtifactState.UNVALIDATED,
                reason_codes=["NO_VALIDATED_ARTIFACT"],
                timestamp=utcnow(),
            )
        features, missing = self.preprocess(values)
        raw = float(self.model.predict_proba(features)[0, 1]) * 100
        return RiskEvent(
            call_id=call_id,
            window_id=window_id,
            risk_raw_0_100=raw,
            risk_display_0_100=self.ema.update(raw),
            evidence_summary=evidence,
            quality=quality,
            missingness=missing,
            risk_model_version=self.artifact.version,
            timestamp=utcnow(),
        )
