from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from praxis.contracts import ContextConfig, ContextEvidence, ContextInput, ModuleStatus, RuleFlag
from praxis.contracts.context import CONTEXT_RULES


def evaluate_context(call_id: str, value: ContextInput, config: ContextConfig) -> ContextEvidence:
    flags = dict.fromkeys(CONTEXT_RULES, RuleFlag.UNKNOWN)

    def set_flag(name, condition):
        flags[name] = RuleFlag.TRUE if condition else RuleFlag.FALSE

    if value.known_contact is not None:
        set_flag("unknown_contact", not value.known_contact)
    if value.claimed_role is not None and value.expected_role is not None:
        set_flag(
            "claimed_role_mismatch", value.claimed_role.casefold() != value.expected_role.casefold()
        )
    if value.beneficiary_known is not None:
        set_flag("new_beneficiary", not value.beneficiary_known)
    if value.amount is not None and value.allowed_amount is not None:
        set_flag("unusual_amount", value.amount > value.allowed_amount)
    if value.workflow_permitted is not None:
        set_flag("workflow_violation", not value.workflow_permitted)
    if value.historical_risk is not None:
        set_flag("historical_risk_indicator", value.historical_risk)
    if (
        value.time is not None
        and config.operating_start is not None
        and config.operating_end is not None
        and config.timezone is not None
    ):
        local = value.time.astimezone(ZoneInfo(config.timezone)).time()
        if config.operating_start < config.operating_end:
            normal = config.operating_start <= local < config.operating_end
        elif config.operating_start > config.operating_end:
            normal = local >= config.operating_start or local < config.operating_end
        else:
            normal = True  # equal endpoints explicitly mean 24-hour operation
        set_flag("unusual_time", not normal)
    denominator = sum(config.weights[k] for k, v in flags.items() if v != RuleFlag.UNKNOWN)
    numerator = sum(config.weights[k] for k, v in flags.items() if v == RuleFlag.TRUE)
    score = 100 * numerator / denominator if denominator else None
    return ContextEvidence(
        call_id=call_id,
        config_version=config.version,
        status=ModuleStatus.AVAILABLE if score is not None else ModuleStatus.UNAVAILABLE,
        flags=flags,
        context_score=score,
        reason_codes=[k.upper() for k, v in flags.items() if v == RuleFlag.TRUE]
        or ([] if score is not None else ["NO_APPLICABLE_CONTEXT"]),
        timestamp=datetime.now(timezone.utc),
    )
