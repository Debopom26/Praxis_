from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from .base import Contract, Identifier, RiskScore, Version
from .status import PolicyAction


class PolicyConfig(Contract):
    tenant_id: Identifier
    policy_version: Version
    warn_at: RiskScore = 40
    verify_at: RiskScore = 60
    escalate_at: RiskScore = 80
    hold_at: RiskScore = 90
    verification_workflow: str = Field(
        default="registered-number callback or MFA", min_length=1, max_length=512
    )

    @model_validator(mode="after")
    def check(self):
        if not 0 < self.warn_at < self.verify_at < self.escalate_at < self.hold_at <= 100:
            raise ValueError("Strictly ordered thresholds required")
        return self


class PolicyEvent(Contract):
    type: Literal["policy"] = "policy"
    call_id: Identifier
    window_id: Identifier
    policy_version: Version
    action: PolicyAction
    triggering_threshold_or_rule: str
    verification_workflow: str | None
    timestamp: AwareDatetime
