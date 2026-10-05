from datetime import datetime, timezone

from praxis.contracts import ModuleStatus, PolicyAction, PolicyConfig, PolicyEvent, RiskEvent


def evaluate_policy(risk: RiskEvent, config: PolicyConfig, supports_hold: bool) -> PolicyEvent:
    if not any(
        e.status in (ModuleStatus.AVAILABLE, ModuleStatus.LOW_QUALITY) and e.module != "ai_text"
        for e in risk.evidence_summary
    ):
        raise ValueError("POLICY_ERROR_NO_INDEPENDENT_EVIDENCE")
    score = risk.risk_display_0_100
    action = PolicyAction.ALLOW
    rule = "risk < warn_at"
    for threshold, decision in [
        (config.warn_at, PolicyAction.WARN),
        (config.verify_at, PolicyAction.SECONDARY_VERIFICATION),
        (config.escalate_at, PolicyAction.ESCALATE),
        (config.hold_at, PolicyAction.HOLD),
    ]:
        if score >= threshold:
            action = decision
            rule = f"risk >= {threshold:g}"
    if action == PolicyAction.HOLD and not supports_hold:
        action = PolicyAction.ESCALATE
        rule += "; HOST_HOLD_UNSUPPORTED"
    workflow = (
        config.verification_workflow
        if action in (PolicyAction.SECONDARY_VERIFICATION, PolicyAction.ESCALATE, PolicyAction.HOLD)
        else None
    )
    return PolicyEvent(
        call_id=risk.call_id,
        window_id=risk.window_id,
        policy_version=config.policy_version,
        action=action,
        triggering_threshold_or_rule=rule,
        verification_workflow=workflow,
        timestamp=datetime.now(timezone.utc),
    )
