import json
from pathlib import Path

import numpy as np
import pytest
from praxis.context import evaluate_context
from praxis.contracts import ContextConfig, ContextInput, PolicyConfig, RiskEvent
from praxis.policy import evaluate_policy
from praxis.risk import EMA, FEATURES, RiskEngine, feature_vector


def test_context_missing_partial_and_complete():
    config = ContextConfig(tenant_id="a", version="sih-v1")
    empty = evaluate_context("c", ContextInput(), config)
    assert empty.status == "UNAVAILABLE" and empty.context_score is None
    partial = evaluate_context("c", ContextInput(known_contact=False), config)
    assert partial.context_score == 100
    partial = evaluate_context(
        "c", ContextInput(known_contact=True, beneficiary_known=False), config
    )
    assert partial.context_score == pytest.approx(200 / 3)
    assert partial.flags["unusual_amount"] == "UNKNOWN"
    full = ContextInput(
        known_contact=False,
        claimed_role="CEO",
        expected_role="clerk",
        beneficiary_known=False,
        amount=20,
        allowed_amount=10,
        workflow_permitted=False,
        historical_risk=True,
    )
    assert evaluate_context("c", full, config).context_score == 100


@pytest.mark.parametrize(
    "score,expected",
    [
        (0, "ALLOW"),
        (39, "ALLOW"),
        (39.9, "ALLOW"),
        (40, "WARN"),
        (59, "WARN"),
        (60, "SECONDARY_VERIFICATION"),
        (79, "SECONDARY_VERIFICATION"),
        (80, "ESCALATE"),
        (89, "ESCALATE"),
        (90, "HOLD"),
        (100, "HOLD"),
    ],
)
def test_policy_boundaries(score, expected):
    value = json.loads(
        (Path(__file__).parents[2] / "contracts/examples/RiskEvent.json").read_text()
    )
    value["risk_display_0_100"] = score
    event = evaluate_policy(
        RiskEvent.model_validate(value), PolicyConfig(tenant_id="a", policy_version="sih-v1"), True
    )
    assert event.action == expected
    if score >= 90:
        assert (
            evaluate_policy(
                RiskEvent.model_validate(value),
                PolicyConfig(tenant_id="a", policy_version="v"),
                False,
            ).action
            == "ESCALATE"
        )


def test_no_ai_only_policy():
    value = json.loads(
        (Path(__file__).parents[2] / "contracts/examples/RiskEvent.json").read_text()
    )
    value["evidence_summary"][0]["module"] = "ai_text"
    with pytest.raises(ValueError):
        evaluate_policy(
            RiskEvent.model_validate(value), PolicyConfig(tenant_id="a", policy_version="v"), True
        )


def test_ema_and_missingness():
    ema = EMA()
    assert ema.update(10) == 10
    assert ema.update(90) == 38
    with pytest.raises(ValueError):
        ema.update(float("nan"))
    values = feature_vector({"context": 20})
    assert np.isnan(values).sum() == len(FEATURES) - 1
    result = RiskEngine().evaluate("c", "w", {}, [], {})
    assert result.status == "UNAVAILABLE" and result.artifact_state == "UNVALIDATED"
    assert "risk_raw_0_100" not in result.model_dump()


def test_risk_artifact_hash_schema_and_preprocessing(tmp_path):
    import hashlib

    from praxis.risk import FEATURE_VERSION, RiskArtifact

    n = len(FEATURES)
    # TEST ONLY coefficients, never installed as a runtime artifact.
    value = dict(
        version="TEST_ONLY",
        feature_version=FEATURE_VERSION,
        features=list(FEATURES),
        validation_report="TEST_ONLY",
        dataset_version="TEST_ONLY",
        split_hash="0" * 64,
        code_version="TEST_ONLY",
        regularization_c=1,
        means=[2.0] * n,
        scales=[2.0] * n,
        coefficients=[0.0] * (n * 2),
        intercept=0,
    )
    path = tmp_path / "test-only.json"
    path.write_text(RiskArtifact(**value).model_dump_json())
    engine = RiskEngine()
    with pytest.raises(ValueError):
        engine.load(path, "0" * 64)
    engine.load(path, hashlib.sha256(path.read_bytes()).hexdigest())
    processed, missing = engine.preprocess({"context": 4})
    assert processed[0, FEATURES.index("context")] == 1
    assert missing["acoustic"] and not missing["context"]
    assert processed[0, 0] == 0 and processed[0, n] == 1
    value["feature_version"] = "obsolete"
    with pytest.raises(ValueError):
        RiskArtifact(**value)
