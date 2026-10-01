from pydantic import AwareDatetime, Field, model_validator

from .base import Contract, Identifier, NonNegative, UnitScore, Version
from .status import ArtifactState, LinguisticLabel, ModuleStatus, SpeakerState


class Provenance(Contract):
    model_version: Version | None = None
    artifact_version: Version | None = None
    calibration_version: Version | None = None
    artifact_state: ArtifactState = ArtifactState.NOT_LOADED
    checksum_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class ModuleEvidence(Contract):
    type: str = "evidence"
    call_id: Identifier
    window_id: Identifier | None = None
    module: Identifier
    model_version: Version | None
    status: ModuleStatus
    raw_score: float | None = None
    features: dict[str, float | None] = Field(default_factory=dict)
    calibrated_score: UnitScore | None = None
    quality: dict[str, float | None] = Field(default_factory=dict)
    latency_ms: NonNegative
    reason_codes: list[str]
    provenance: Provenance = Field(default_factory=Provenance)
    timestamp: AwareDatetime

    @model_validator(mode="after")
    def check(self):
        if self.status in (ModuleStatus.UNAVAILABLE, ModuleStatus.ERROR):
            if (
                self.raw_score is not None
                or self.calibrated_score is not None
                or any(v is not None for v in self.features.values())
            ):
                raise ValueError("Unavailable/error evidence cannot contain semantic scores")
        if self.calibrated_score is not None and not self.provenance.calibration_version:
            raise ValueError("Calibrated scores require calibration provenance")
        if self.provenance.model_version != self.model_version:
            raise ValueError("Model provenance must agree")
        return self


class SpeakerEvidence(ModuleEvidence):
    speaker_state: SpeakerState = SpeakerState.UNAVAILABLE
    cosine_similarity: float | None = Field(default=None, ge=-1, le=1)
    profile_version: Version | None = None
    threshold_version: Version | None = None
    threshold_state: ArtifactState = ArtifactState.NOT_LOADED

    @model_validator(mode="after")
    def speaker_check(self):
        if self.cosine_similarity is not None:
            if (
                self.status not in (ModuleStatus.AVAILABLE, ModuleStatus.LOW_QUALITY)
                or not self.profile_version
            ):
                raise ValueError("Similarity requires real available profile evidence")
        if self.speaker_state != SpeakerState.UNAVAILABLE:
            if (
                self.threshold_state != ArtifactState.VALIDATED
                or not self.threshold_version
                or self.cosine_similarity is None
            ):
                raise ValueError("Identity decision requires validated thresholds and similarity")
        return self


class LinguisticEvidence(ModuleEvidence):
    rule_labels: list[LinguisticLabel] = Field(default_factory=list)
    classifier_scores: dict[LinguisticLabel, UnitScore] | None = None
    classifier_state: ArtifactState = ArtifactState.NOT_LOADED


class AIWrittenEvidence(ModuleEvidence):
    normalized_token_count: int = Field(ge=0)
    supporting_only: bool = True

    @model_validator(mode="after")
    def ai_check(self):
        if not self.supporting_only:
            raise ValueError("AI-written evidence is supporting only")
        if self.normalized_token_count < 64 and self.status != ModuleStatus.UNAVAILABLE:
            raise ValueError("AI-written evidence requires at least 64 normalized tokens")
        return self
