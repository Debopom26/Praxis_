from pydantic import AwareDatetime, Field

from .base import Contract, Identifier, RiskScore, Version
from .risk import EvidenceSummary
from .status import ModuleStatus, PolicyAction


class AuditEvent(Contract):
    tenant_id: Identifier
    session_id: Identifier
    event_id: Identifier
    event_type: Identifier
    call_id: Identifier | None = None
    window_id: Identifier | None = None
    timestamp: AwareDatetime
    model_versions: dict[str, Version] = Field(default_factory=dict)
    calibration_versions: dict[str, Version] = Field(default_factory=dict)
    risk_model_version: Version | None = None
    policy_version: Version | None = None
    profile_version: Version | None = None
    threshold_version: Version | None = None
    context_config_version: Version | None = None
    retention_config_version: Version | None = None
    evidence_summary: list[EvidenceSummary] = Field(default_factory=list)
    final_risk: RiskScore | None = None
    action: PolicyAction | None = None
    status: ModuleStatus
    quality: dict[str, float | None] = Field(default_factory=dict)
    reason_codes: list[str] = Field(default_factory=list)
