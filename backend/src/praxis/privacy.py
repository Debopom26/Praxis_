import json
from datetime import timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, select

from praxis.contracts import RetentionConfig
from praxis.db.models import (
    AuditRecord,
    Configuration,
    EvidenceRecord,
    Organization,
    RetainedPayload,
    RiskRecord,
    SessionRecord,
)
from praxis.db.repository import utcnow
from praxis.security import require_role


class Privacy:
    def __init__(self, repo, cipher):
        self.repo, self.cipher = repo, cipher

    @staticmethod
    def config(db, tenant):
        row = db.scalar(
            select(Configuration)
            .where(Configuration.tenant_id == tenant, Configuration.kind == "retention")
            .order_by(Configuration.created_at.desc())
            .limit(1)
        )
        return (
            RetentionConfig.model_validate(row.payload)
            if row
            else RetentionConfig(tenant_id=tenant, version="privacy-default-v1")
        )

    def retain(self, db, principal, session_id, kind, data, identity=None):
        config = self.config(db, principal.tenant_id)
        if not (
            config.retain_transcript if kind == "transcript" else config.retain_enrollment_audio
        ):
            return
        key = str(uuid4())
        db.add(
            RetainedPayload(
                id=key,
                tenant_id=principal.tenant_id,
                session_id=session_id,
                kind=kind,
                identity=identity,
                ciphertext=self.cipher.encrypt(
                    data, principal.tenant_id, session_id + ":" + kind, key
                ),
                expires_at=utcnow() + timedelta(days=config.metadata_days),
            )
        )

    def list(self, principal, session_id, limit=100):
        require_role(principal, "admin", "analyst")
        with self.repo.sessions() as db:
            self.repo._owned(db, principal, session_id)
            rows = db.scalars(
                select(RetainedPayload)
                .where(
                    RetainedPayload.tenant_id == principal.tenant_id,
                    RetainedPayload.session_id == session_id,
                    RetainedPayload.expires_at > utcnow(),
                )
                .order_by(RetainedPayload.expires_at)
                .limit(limit)
            )
            return [{"id": row.id, "kind": row.kind, "expires_at": row.expires_at} for row in rows]

    def read(self, principal, session_id, payload_id):
        require_role(principal, "admin", "analyst")
        from praxis.db.repository import MissingResource

        with self.repo.sessions.begin() as db:
            self.repo._owned(db, principal, session_id)
            row = db.scalar(
                select(RetainedPayload).where(
                    RetainedPayload.id == payload_id,
                    RetainedPayload.tenant_id == principal.tenant_id,
                    RetainedPayload.session_id == session_id,
                    RetainedPayload.expires_at > utcnow(),
                )
            )
            if row is None:
                raise MissingResource()
            result = json.loads(
                self.cipher.decrypt(
                    row.ciphertext, principal.tenant_id, session_id + ":" + row.kind, row.id
                )
            )
            self.repo._audit(db, principal, session_id, "retained_payload_read", [row.kind.upper()])
            return result

    def purge(self):
        now = utcnow()
        with self.repo.sessions.begin() as db:
            db.execute(delete(RetainedPayload).where(RetainedPayload.expires_at <= now))
            for tenant in db.scalars(select(Organization.id)):
                config = self.config(db, tenant)
                for kind, keep in [
                    ("transcript", config.retain_transcript),
                    ("enrollment", config.retain_enrollment_audio),
                ]:
                    if not keep:
                        db.execute(
                            delete(RetainedPayload).where(
                                RetainedPayload.tenant_id == tenant, RetainedPayload.kind == kind
                            )
                        )
                cutoff = now - timedelta(days=config.metadata_days)
                tables: list[Any] = [EvidenceRecord, RiskRecord, AuditRecord]
                for model in tables:
                    db.execute(
                        delete(model).where(model.tenant_id == tenant, model.timestamp < cutoff)
                    )
                stale_sessions = select(SessionRecord.id).where(
                    SessionRecord.tenant_id == tenant,
                    SessionRecord.ended.is_(True),
                    SessionRecord.payload["ended_at"].as_string() < cutoff.isoformat(),
                )
                children: list[Any] = [RetainedPayload, EvidenceRecord, RiskRecord, AuditRecord]
                for model in children:
                    db.execute(
                        delete(model).where(
                            model.tenant_id == tenant, model.session_id.in_(stale_sessions)
                        )
                    )
                db.execute(delete(SessionRecord).where(SessionRecord.id.in_(stale_sessions)))
