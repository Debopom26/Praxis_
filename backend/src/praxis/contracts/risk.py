from typing import Literal

from pydantic import AwareDatetime, Field

from .base import Contract, Identifier, RiskScore, Version
from .status import ArtifactState, ModuleStatus


class EvidenceSummary(Contract):
    module: Identifier
    status: ModuleStatus
    reason_codes: list[str]
    model_version: Version | None = None


class RiskEvent(Contract):
    type: Literal["risk"] = "risk"
    call_id: Identifier
    window_id: Identifier
    risk_raw_0_100: RiskScore
    risk_display_0_100: RiskScore
    evidence_summary: list[EvidenceSummary] = Field(min_length=1)
    quality: dict[str, float | None]
    missingness: dict[str, bool]
    risk_model_version: Version
    artifact_state: Literal[ArtifactState.VALIDATED] = ArtifactState.VALIDATED
    timestamp: AwareDatetime


class UnavailableEvent(Contract):
    type: Literal["unavailable"] = "unavailable"
    call_id: Identifier
    module: Identifier
    status: Literal[ModuleStatus.UNAVAILABLE, ModuleStatus.ERROR]
    artifact_state: ArtifactState
    reason_codes: list[str] = Field(min_length=1)
    timestamp: AwareDatetime
