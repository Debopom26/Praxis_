import base64
import json
from pathlib import Path

import pytest
from praxis import contracts
from praxis.contracts import AudioFrame, ModuleEvidence, PolicyConfig, SessionStart, SpeakerEvidence
from pydantic import ValidationError

NOW = "2026-09-20T00:00:00Z"


def test_session_requires_aware_time_and_known_fields():
    value = dict(tenant_id="t", call_id="c", host_app_id="h", created_at=NOW)
    assert SessionStart.model_validate_json(SessionStart(**value).model_dump_json()).call_id == "c"
    for patch in ({"created_at": "2026-09-20T00:00:00"}, {"unexpected": True}, {"tenant_id": ""}):
        with pytest.raises(ValidationError):
            SessionStart(**(value | patch))


@pytest.mark.parametrize(
    "payload",
    ["!!!=", "", base64.b64encode(b"x").decode(), base64.b64encode(b"xx" * 16001).decode()],
    ids=["invalid-base64", "empty", "unaligned", "oversized"],
)
def test_bad_audio(payload):
    with pytest.raises(ValidationError):
        AudioFrame(
            sequence_id=0,
            timestamp_ms=0,
            format={"sample_rate": 16000, "channels": 1},
            audio_base64=payload,
        )


def test_unavailable_scores_forbidden():
    value = dict(
        call_id="c",
        module="risk",
        model_version=None,
        status="UNAVAILABLE",
        latency_ms=0,
        reason_codes=["MISSING"],
        timestamp=NOW,
    )
    assert ModuleEvidence(**value).raw_score is None
    for patch in ({"raw_score": 0.5}, {"calibrated_score": 0}, {"features": {"score": 1}}):
        with pytest.raises(ValidationError):
            ModuleEvidence(**(value | patch))


def test_identity_requires_thresholds():
    with pytest.raises(ValidationError):
        SpeakerEvidence(
            call_id="c",
            module="speaker",
            model_version=None,
            status="AVAILABLE",
            latency_ms=0,
            reason_codes=[],
            timestamp=NOW,
            speaker_state="MATCH",
        )


@pytest.mark.parametrize("patch", [{"warn_at": 60}, {"hold_at": 101}, {"warn_at": float("nan")}])
def test_policy_invalid(patch):
    with pytest.raises(ValidationError):
        PolicyConfig(tenant_id="t", policy_version="v1", **patch)


def test_all_fixture_json_roundtrips_and_schemas():
    import jsonschema

    root = Path(__file__).parents[2] / "contracts"
    fixtures = list((root / "examples").glob("*.json"))
    assert len(fixtures) >= 9
    for path in fixtures:
        cls = getattr(contracts, path.stem)
        value = json.loads(path.read_text())
        model = cls.model_validate(value)
        assert cls.model_validate_json(model.model_dump_json()) == model
        jsonschema.validate(
            value, json.loads((root / "schemas" / (path.stem + ".json")).read_text())
        )


def test_contract_exports_do_not_import_business_logic():
    import subprocess
    import sys

    code = "import praxis.contracts, sys; assert not any(n.startswith(('praxis.api', 'praxis.db', 'praxis.speaker')) for n in sys.modules)"
    subprocess.run([sys.executable, "-I", "-c", code], check=True, timeout=10)
