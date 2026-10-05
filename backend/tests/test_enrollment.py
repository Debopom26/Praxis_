import numpy as np
import pytest
from praxis.contracts import SessionStart
from praxis.db.models import SpeakerProfile
from praxis.db.repository import utcnow
from praxis.security import AccessDenied, Encryption
from praxis.speaker import SpeakerService
from sqlalchemy import select


class TestOnlyEmbedder:
    version = "TEST_ONLY_NOT_A_MODEL"

    def embed(self, samples, rate):
        return np.ones(192, np.float32)


def test_controlled_enrollment_guards_and_encrypted_profile(repo, settings, monkeypatch):
    monkeypatch.setattr("praxis.speaker.voiced_clip", lambda samples, rate: samples)
    principal = repo.principal("admin-a", "a")
    session = repo.start(
        principal,
        SessionStart(
            tenant_id="a",
            call_id="c",
            host_app_id="test",
            created_at=utcnow(),
            claimed_identity="test-id",
        ),
    )
    service = SpeakerService(
        repo, TestOnlyEmbedder(), Encryption(settings.embedding_key_base64.get_secret_value())
    )
    clean = [(np.full(5 * 16000, 0.1, np.float32), 16000) for _ in range(3)]
    with pytest.raises(AccessDenied):
        service.enroll(repo.principal("host-a", "a"), session.session_id, "test-id", clean, True)
    for clips, approved in [
        (clean[:2], True),
        (clean, False),
        ([(x[:16000], rate) for x, rate in clean], True),
    ]:
        with pytest.raises(ValueError):
            service.enroll(principal, session.session_id, "test-id", clips, approved)
    result = service.enroll(principal, session.session_id, "test-id", clean, True)
    assert result["threshold_state"] == "UNVALIDATED"
    with repo.sessions() as db:
        profile = db.scalar(select(SpeakerProfile))
        assert profile.tenant_id == "a" and profile.model_version == "TEST_ONLY_NOT_A_MODEL"
        assert b"[1.0" not in profile.encrypted_centroid
    assert len(repo.audit(principal, session.session_id)) == 2
    with pytest.raises(AccessDenied):
        repo.delete_profile(repo.principal("host-a", "a"), session.session_id, "test-id")
    assert repo.delete_profile(principal, session.session_id, "test-id") == {"deleted": True}
    with repo.sessions() as db:
        assert db.scalar(select(SpeakerProfile)) is None
