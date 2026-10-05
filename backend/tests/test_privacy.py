from datetime import timedelta

import pytest
from praxis.contracts import RetentionConfig, SessionStart, TranscriptEvent
from praxis.db.models import RetainedPayload
from praxis.db.repository import MissingResource, utcnow
from praxis.privacy import Privacy
from praxis.security import Encryption
from sqlalchemy import select, update


def test_retention_opt_in_encryption_tenant_and_expiry(repo, settings):
    privacy = Privacy(repo, Encryption(settings.embedding_key_base64.get_secret_value()))
    repo.privacy = privacy
    p = repo.principal("admin-a", "a")
    other = repo.principal("admin-b", "b")
    session = repo.start(
        p, SessionStart(tenant_id="a", call_id="c", host_app_id="test", created_at=utcnow())
    )
    transcript = TranscriptEvent(
        call_id="c",
        text="PRIVATE TRANSCRIPT",
        language="en",
        segments=[],
        quality=None,
        status="AVAILABLE",
        model_version="TEST_ONLY",
        latency_ms=0,
        timestamp=utcnow(),
    )
    repo.record_event(p, session.session_id, transcript)
    assert privacy.list(p, session.session_id) == []
    repo.save_config(
        p,
        session.session_id,
        "retention",
        RetentionConfig(tenant_id="a", version="v1", retain_transcript=True),
    )
    repo.record_event(p, session.session_id, transcript)
    rows = privacy.list(p, session.session_id)
    assert len(rows) == 1
    assert privacy.read(p, session.session_id, rows[0]["id"])["text"] == "PRIVATE TRANSCRIPT"
    with repo.sessions() as db:
        assert b"PRIVATE TRANSCRIPT" not in db.scalar(select(RetainedPayload)).ciphertext
    with pytest.raises(MissingResource):
        privacy.read(other, session.session_id, rows[0]["id"])
    with repo.sessions.begin() as db:
        db.execute(update(RetainedPayload).values(expires_at=utcnow() - timedelta(seconds=1)))
    with pytest.raises(MissingResource):
        privacy.read(p, session.session_id, rows[0]["id"])
    privacy.purge()
    assert privacy.list(p, session.session_id) == []
