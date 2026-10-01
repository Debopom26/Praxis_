"""Deployment-test payload executed inside backend by verify_deployment.py.

The caller supplies x through stdin. All rows belong to disposable test tenants.
No database replacement, mocks or private content is printed.
"""

from datetime import timedelta
from uuid import uuid4

from praxis.config import Settings
from praxis.contracts import RetentionConfig, SessionStart, TranscriptEvent
from praxis.db.models import (
    EvidenceRecord,
    Membership,
    RetainedPayload,
    SessionRecord,
)
from praxis.db.repository import MissingResource, Repository, utcnow
from praxis.privacy import Privacy
from praxis.security import Encryption
from sqlalchemy import func, select, update


def verify(x):
    s = Settings()
    r = Repository.from_url(s.database_url.get_secret_value())
    privacy = Privacy(r, Encryption(s.embedding_key_base64.get_secret_value()))
    r.privacy = privacy
    t1, t2 = x["tenants"]
    sid = x["sid"]
    with r.sessions() as db:
        u1 = db.scalar(select(Membership.user_id).where(Membership.tenant_id == t1))
        u2 = db.scalar(select(Membership.user_id).where(Membership.tenant_id == t2))
    p, other = r.principal(u1, t1), r.principal(u2, t2)
    marker = "P10_PRIVATE_FIXTURE_" + uuid4().hex
    event = TranscriptEvent(
        call_id=x["call"],
        text=marker,
        language="en",
        segments=[],
        quality=None,
        status="AVAILABLE",
        model_version="P10_FIXTURE_ONLY",
        latency_ms=0,
        timestamp=utcnow(),
    )
    r.record_event(p, sid, event)
    assert privacy.list(p, sid) == []
    with r.sessions() as db:
        for payload in db.scalars(
            select(EvidenceRecord.payload).where(EvidenceRecord.tenant_id == t1)
        ):
            assert marker not in str(payload)
    r.save_config(
        p,
        sid,
        "retention",
        RetentionConfig(tenant_id=t1, version="p10-opt-in", retain_transcript=True),
    )
    r.record_event(p, sid, event)
    row = privacy.list(p, sid)[0]
    assert privacy.read(p, sid, row["id"])["text"] == marker
    with r.sessions() as db:
        cipher = db.get(RetainedPayload, row["id"]).ciphertext
        assert marker.encode() not in cipher
    try:
        privacy.read(other, sid, row["id"])
    except MissingResource:
        pass
    else:
        raise AssertionError("Cross-tenant retained read succeeded")
    with r.sessions.begin() as db:
        db.execute(
            update(RetainedPayload)
            .where(RetainedPayload.id == row["id"])
            .values(expires_at=utcnow() - timedelta(seconds=1))
        )
    try:
        privacy.read(p, sid, row["id"])
    except MissingResource:
        pass
    else:
        raise AssertionError("Expired payload readable")
    privacy.purge()
    with r.sessions() as db:
        assert db.get(RetainedPayload, row["id"]) is None
    r.record_event(p, sid, event)
    assert privacy.list(p, sid)
    r.save_config(p, sid, "retention", RetentionConfig(tenant_id=t1, version="p10-off"))
    privacy.purge()
    assert privacy.list(p, sid) == []
    old = r.start(
        p,
        SessionStart(
            tenant_id=t1,
            call_id="p10-expiry-" + uuid4().hex,
            host_app_id="p10-test",
            created_at=utcnow(),
        ),
    )
    r.end(p, old.session_id)
    with r.sessions.begin() as db:
        row = db.get(SessionRecord, old.session_id)
        row.payload = row.payload | {"ended_at": (utcnow() - timedelta(days=31)).isoformat()}
    privacy.purge()
    with r.sessions() as db:
        assert db.get(SessionRecord, old.session_id) is None
        assert db.get(SessionRecord, sid) is not None
        assert (
            db.scalar(
                select(func.count())
                .select_from(RetainedPayload)
                .where(RetainedPayload.tenant_id == t1)
            )
            == 0
        )
    # PostgreSQL enforces the composite tenant/session FK, even for direct DML.
    from praxis.db.models import AuditRecord
    from sqlalchemy.exc import IntegrityError

    try:
        with r.sessions.begin() as db:
            db.add(
                AuditRecord(
                    id=str(uuid4()), tenant_id=t2, session_id=sid, timestamp=utcnow(), payload={}
                )
            )
    except IntegrityError as exc:
        assert exc.orig.sqlstate == "23503"
    else:
        raise AssertionError("Cross-tenant composite FK not enforced")
    # Two actual concurrent PostgreSQL transactions may accept a sequence once.
    from concurrent.futures import ThreadPoolExecutor

    from praxis.db.repository import Conflict

    race = r.start(
        p,
        SessionStart(
            tenant_id=t1,
            call_id="p10-lock-" + uuid4().hex,
            host_app_id="p10-test",
            created_at=utcnow(),
        ),
    )

    def accept():
        try:
            r.accept_sequence(p, race.session_id, 0, 0)
            return "accepted"
        except Conflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: accept(), range(2)))
    assert sorted(outcomes) == ["accepted", "conflict"]
    r.end(p, race.session_id)
    r.engine.dispose()
