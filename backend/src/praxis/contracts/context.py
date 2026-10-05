from datetime import time
from typing import Literal

from pydantic import AwareDatetime, Field, StrictBool, model_validator

from .base import Contract, Identifier, NonNegative, RiskScore, Version
from .status import ModuleStatus, RuleFlag

CONTEXT_RULES = (
    "unknown_contact",
    "claimed_role_mismatch",
    "new_beneficiary",
    "unusual_amount",
    "workflow_violation",
    "unusual_time",
    "historical_risk_indicator",
)


class ContextInput(Contract):
    known_contact: StrictBool | None = None
    claimed_role: str | None = Field(default=None, max_length=128)
    expected_role: str | None = Field(default=None, max_length=128)
    department: str | None = Field(default=None, max_length=128)
    transaction_type: str | None = Field(default=None, max_length=128)
    amount: NonNegative | None = None
    allowed_amount: NonNegative | None = None
    beneficiary: str | None = Field(default=None, max_length=128)
    beneficiary_known: StrictBool | None = None
    workflow_state: str | None = Field(default=None, max_length=128)
    workflow_permitted: StrictBool | None = None
    time: AwareDatetime | None = None
    historical_risk: StrictBool | None = None


class ContextConfig(Contract):
    tenant_id: Identifier
    version: Version
    weights: dict[str, NonNegative] = Field(
        default_factory=lambda: dict(
            zip(CONTEXT_RULES, (0.1, 0.15, 0.2, 0.2, 0.2, 0.05, 0.1), strict=True)
        )
    )
    operating_start: time | None = None
    operating_end: time | None = None
    timezone: str | None = None

    @model_validator(mode="after")
    def check(self):
        if set(self.weights) != set(CONTEXT_RULES) or sum(self.weights.values()) <= 0:
            raise ValueError("Exact context rule set and positive total weight required")
        if any(v is not None for v in (self.operating_start, self.operating_end, self.timezone)):
            if any(v is None for v in (self.operating_start, self.operating_end, self.timezone)):
                raise ValueError("Operating hours require start, end and explicit timezone")
            from zoneinfo import ZoneInfo

            ZoneInfo(str(self.timezone))
        return self


class ContextEvidence(Contract):
    type: Literal["context"] = "context"
    call_id: Identifier
    config_version: Version
    status: ModuleStatus
    flags: dict[str, RuleFlag]
    context_score: RiskScore | None
    reason_codes: list[str]
    timestamp: AwareDatetime

    @model_validator(mode="after")
    def check(self):
        if set(self.flags) != set(CONTEXT_RULES):
            raise ValueError("All context flags including UNKNOWN are required")
        usable = self.status in (ModuleStatus.AVAILABLE, ModuleStatus.LOW_QUALITY)
        if usable != (self.context_score is not None):
            raise ValueError("Context score must agree with availability")
        return self
