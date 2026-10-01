from datetime import datetime, timezone
from typing import TYPE_CHECKING, cast
from uuid import uuid4

from sqlalchemy import create_engine, delete, func, or_, select, text, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from praxis.contracts import (
    AudioWindow,
    AuditEvent,
    ContextEvidence,
    ContextInput,
    EvidenceSummary,
    ModuleEvidence,
    ModuleStatus,
    PolicyEvent,
    RiskEvent,
    SessionStart,
    SessionView,
    TranscriptEvent,
    UnavailableEvent,
)
from praxis.security import PASSWORD_HASHER, AccessDenied, Principal, verify_password

from .models import (
    AuditRecord,
    Configuration,
    EvidenceRecord,
    Membership,
    RetainedPayload,
    RiskRecord,
    SessionRecord,
    SpeakerProfile,
    User,
)

if TYPE_CHECKING:
    from praxis.privacy import Privacy


class MissingResource(Exception):
    pass


class Conflict(Exception):
    pass


def utcnow():
    return datetime.now(timezone.utc)


class Repository:
    def __init__(self, engine):
        self.engine = engine
        self.sessions = sessionmaker(engine, expire_on_commit=False)
        self.dummy_hash = PASSWORD_HASHER.hash(str(uuid4()))
        self.privacy: "Privacy | None" = None

    @classmethod
    def from_url(cls, url: str):
        return cls(
            create_engine(
                url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=5,
                hide_parameters=True,
                connect_args={"connect_timeout": 5},
            )
        )

    def healthy(self) -> bool:
        try:
            with self.sessions() as db:
                db.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def principal(self, user_id: str, tenant_id: str) -> Principal:
        with self.sessions() as db:
            role = db.scalar(
                select(Membership.role)
                .join(User, User.id == Membership.user_id)
                .where(
                    Membership.user_id == user_id,
                    Membership.tenant_id == tenant_id,
                    User.active.is_(True),
                )
            )
            if role is None:
                raise AccessDenied()
            return Principal(user_id, tenant_id, role)

    def login(self, username: str, password: str, tenant_id: str) -> Principal:
        with self.sessions() as db:
            user = db.scalar(select(User).where(User.username == username, User.active.is_(True)))
            valid = verify_password(user.password_hash if user else self.dummy_hash, password)
            if not user or not valid:
                raise AccessDenied()
            return self.principal(user.id, tenant_id)

    @staticmethod
    def _owned(db, principal: Principal, session_id: str):
        query = select(SessionRecord).where(
            SessionRecord.id == session_id, SessionRecord.tenant_id == principal.tenant_id
        )
        if principal.role == "host":
            query = query.where(SessionRecord.owner_id == principal.user_id)
        row = db.scalar(query.with_for_update())
        if row is None:
            raise MissingResource()
        return row

    @staticmethod
    def _audit(
        db, principal: Principal, session_id: str, event_type: str, reasons: list[str], **metadata
    ):
        session = Repository._owned(db, principal, session_id)
        event = AuditEvent(
            tenant_id=principal.tenant_id,
            session_id=session_id,
            event_id=str(uuid4()),
            event_type=event_type,
            call_id=session.call_id,
            timestamp=utcnow(),
            status=ModuleStatus.AVAILABLE,
            reason_codes=reasons,
            **metadata,
        )
        db.add(
            AuditRecord(
                id=event.event_id,
                tenant_id=event.tenant_id,
                session_id=session_id,
                timestamp=event.timestamp,
                payload=event.model_dump(mode="json"),
            )
        )
        db.flush()  # failure aborts the enclosing state change transaction

    def start(self, p: Principal, value: SessionStart) -> SessionView:
        if p.tenant_id != value.tenant_id:
            raise AccessDenied()
        view = SessionView(**value.model_dump(), session_id=str(uuid4()))
        with self.sessions.begin() as db:
            db.add(
                SessionRecord(
                    id=view.session_id,
                    tenant_id=p.tenant_id,
                    owner_id=p.user_id,
                    call_id=value.call_id,
                    payload=view.model_dump(mode="json"),
                    created_at=view.created_at,
                )
            )
            db.flush()
            self._audit(db, p, view.session_id, "session_started", [])
        return view

    def get(self, p: Principal, session_id: str) -> SessionView:
        with self.sessions() as db:
            return SessionView.model_validate(self._owned(db, p, session_id).payload)

    def dashboard_session(self, p: Principal, session_id: str, connected: bool) -> dict:
        with self.sessions() as db:
            row = self._owned(db, p, session_id)
            return self._dashboard_view(db, row, connected)

    def dashboard_sessions(
        self, p: Principal, connected_ids: set[str], q: str, offset: int, limit: int,
        active: bool | None,
    ) -> dict:
        with self.sessions() as db:
            stmt = select(SessionRecord).where(SessionRecord.tenant_id == p.tenant_id)
            if p.role == "host":
                stmt = stmt.where(SessionRecord.owner_id == p.user_id)
            if q:
                pattern = f"%{q}%"
                stmt = stmt.where(or_(SessionRecord.remote_name.ilike(pattern),
                                      SessionRecord.remote_number.ilike(pattern)))
            if active is True:
                stmt = stmt.where(SessionRecord.ended.is_(False), SessionRecord.id.in_(connected_ids))
            elif active is False:
                stmt = stmt.where(or_(SessionRecord.ended.is_(True), SessionRecord.id.not_in(connected_ids)))
            total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
            rows = db.scalars(stmt.order_by(SessionRecord.created_at.desc(), SessionRecord.id.desc())
                              .offset(offset).limit(limit)).all()
            return {"sessions": [self._dashboard_view(db, row, row.id in connected_ids) for row in rows],
                    "total": total}

    @staticmethod
    def _dashboard_view(db, row: SessionRecord, connected: bool) -> dict:
        view = SessionView.model_validate(row.payload)
        owner = db.get(User, row.owner_id)
        risk = db.scalar(select(RiskRecord).where(
            RiskRecord.tenant_id == row.tenant_id, RiskRecord.session_id == row.id
        ).order_by(RiskRecord.timestamp.desc(), RiskRecord.id.desc()).limit(1))
        policy = db.scalar(select(EvidenceRecord).where(
            EvidenceRecord.tenant_id == row.tenant_id, EvidenceRecord.session_id == row.id,
            EvidenceRecord.payload["type"].as_string() == "policy",
        ).order_by(EvidenceRecord.timestamp.desc(), EvidenceRecord.id.desc()).limit(1))
        return {
            "session_id": row.id, "tenant_id": row.tenant_id, "call_id": row.call_id,
            "owner_username": owner.username if owner else None,
            "remote_name": row.remote_name, "remote_number": row.remote_number,
            "created_at": view.created_at.isoformat(),
            "call_connected_at": row.call_connected_at.isoformat() if row.call_connected_at else None,
            "ended_at": view.ended_at.isoformat() if view.ended_at else None,
            "connected": connected and not row.ended,
            "latest_analysis": row.latest_analysis,
            "latest_analysis_at": row.latest_analysis_at.isoformat() if row.latest_analysis_at else None,
            "latest_risk": risk.payload if risk else None,
            "latest_policy": policy.payload if policy else None,
        }

    def set_display(self, p: Principal, session_id: str, remote_name: str | None,
                    remote_number: str | None, call_connected_at) -> None:
        with self.sessions.begin() as db:
            row = self._owned(db, p, session_id)
            if row.ended:
                raise Conflict()
            row.remote_name = remote_name
            row.remote_number = remote_number
            row.call_connected_at = call_connected_at
            self._audit(db, p, session_id, "session_display_updated", [])

    def sequence_state(self, p: Principal, session_id: str):
        with self.sessions() as db:
            row = self._owned(db, p, session_id)
            return row.last_sequence, row.last_timestamp_ms

    def delete_profile(self, p: Principal, session_id: str, identity: str):
        from praxis.security import require_role

        require_role(p, "admin")
        with self.sessions.begin() as db:
            self._owned(db, p, session_id)
            row = db.get(SpeakerProfile, (p.tenant_id, identity))
            deleted = row is not None
            if row is not None:
                db.delete(row)
            db.execute(
                delete(RetainedPayload).where(
                    RetainedPayload.tenant_id == p.tenant_id,
                    RetainedPayload.kind == "enrollment",
                    RetainedPayload.identity == identity,
                )
            )
            self._audit(
                db,
                p,
                session_id,
                "speaker_profile_deleted",
                ["PROFILE_AND_RETAINED_ENROLLMENT_PURGED"],
            )
            return {"deleted": deleted}

    def context(self, p: Principal, session_id: str, patch: ContextInput) -> SessionView:
        with self.sessions.begin() as db:
            row = self._owned(db, p, session_id)
            if row.ended:
                raise Conflict()
            view = SessionView.model_validate(row.payload)
            value = view.permitted_context.model_dump() | patch.model_dump(exclude_unset=True)
            view.permitted_context = ContextInput.model_validate(value)
            row.payload = view.model_dump(mode="json")
            self._audit(db, p, session_id, "context_updated", [])
            return view

    def end(self, p: Principal, session_id: str) -> SessionView:
        with self.sessions.begin() as db:
            row = self._owned(db, p, session_id)
            view = SessionView.model_validate(row.payload)
            if not row.ended:
                view.ended_at = utcnow()
                row.ended = True
                row.payload = view.model_dump(mode="json")
                self._audit(db, p, session_id, "session_ended", [])
            return view

    def accept_sequence(
        self, p: Principal, session_id: str, sequence: int, timestamp_ms: int
    ) -> bool:
        with self.sessions.begin() as db:
            row = self._owned(db, p, session_id)
            if row.ended:
                raise Conflict()
            if sequence <= row.last_sequence or timestamp_ms <= row.last_timestamp_ms:
                raise Conflict()
            old = row.last_sequence
            result = db.execute(
                update(SessionRecord)
                .where(
                    SessionRecord.id == session_id,
                    SessionRecord.tenant_id == p.tenant_id,
                    SessionRecord.last_sequence == old,
                    SessionRecord.ended.is_(False),
                )
                .values(last_sequence=sequence, last_timestamp_ms=timestamp_ms)
            )
            if cast(CursorResult, result).rowcount != 1:
                raise Conflict()
            gap = sequence != old + 1
            if gap:
                self._audit(db, p, session_id, "analysis_gap", ["SEQUENCE_GAP"])
            return gap

    def audit(
        self, p: Principal, session_id: str, limit: int = 100, offset: int = 0
    ) -> list[AuditEvent]:
        with self.sessions() as db:
            self._owned(db, p, session_id)
            rows = db.scalars(
                select(AuditRecord)
                .where(AuditRecord.tenant_id == p.tenant_id, AuditRecord.session_id == session_id)
                .order_by(AuditRecord.timestamp, AuditRecord.id)
                .limit(limit)
                .offset(offset)
            )
            return [AuditEvent.model_validate(r.payload) for r in rows]

    def config(self, p: Principal, kind: str):
        with self.sessions() as db:
            row = db.scalar(
                select(Configuration)
                .where(Configuration.tenant_id == p.tenant_id, Configuration.kind == kind)
                .order_by(Configuration.created_at.desc())
                .limit(1)
            )
            return row.payload if row else None

    def save_config(self, p: Principal, session_id: str, kind: str, value):
        from praxis.security import require_role

        require_role(p, "admin")
        if value.tenant_id != p.tenant_id or kind not in {"context", "policy", "retention"}:
            raise AccessDenied()
        version = getattr(value, "version", None) or getattr(value, "policy_version", None)
        with self.sessions.begin() as db:
            self._owned(db, p, session_id)
            db.add(
                Configuration(
                    tenant_id=p.tenant_id,
                    kind=kind,
                    version=version,
                    payload=value.model_dump(mode="json"),
                    created_at=utcnow(),
                )
            )
            self._audit(
                db,
                p,
                session_id,
                kind + "_configuration_updated",
                ["VERSIONED_CONFIGURATION"],
                **{
                    {
                        "policy": "policy_version",
                        "context": "context_config_version",
                        "retention": "retention_config_version",
                    }[kind]: version
                },
            )
        return value

    def record_event(self, p: Principal, session_id: str, event):
        """Persist typed allowlisted metadata and provenance atomically before delivery."""
        if not isinstance(
            event,
            (
                AudioWindow,
                ContextEvidence,
                ModuleEvidence,
                RiskEvent,
                PolicyEvent,
                TranscriptEvent,
                UnavailableEvent,
            ),
        ):
            raise ValueError("Unsupported persisted event")
        payload = event.model_dump(mode="json")
        module = getattr(event, "module", event.type)
        status = getattr(event, "status", ModuleStatus.AVAILABLE)
        reasons = getattr(event, "reason_codes", [])
        model_version = getattr(event, "model_version", None)
        if isinstance(event, AudioWindow):
            model_version = event.vad_model_version
        quality = getattr(event, "quality", {})
        if not isinstance(quality, dict):
            quality = (
                {"asr_quality": event.quality}
                if isinstance(event, TranscriptEvent)
                else event.quality.model_dump(exclude={"reason_codes"})
                if isinstance(event, AudioWindow)
                else {}
            )
        if isinstance(event, TranscriptEvent):
            payload = {
                k: v
                for k, v in payload.items()
                if k not in {"text", "segments", "analysis_english"}
            }
        audit = AuditEvent(
            tenant_id=p.tenant_id,
            session_id=session_id,
            event_id=str(uuid4()),
            event_type=event.type,
            call_id=event.call_id,
            window_id=getattr(event, "window_id", None),
            timestamp=utcnow(),
            status=status,
            reason_codes=reasons,
            model_versions={module: model_version} if model_version else {},
            quality=quality,
            calibration_versions={module: event.provenance.calibration_version}
            if isinstance(event, ModuleEvidence) and event.provenance.calibration_version
            else {},
            risk_model_version=event.risk_model_version if isinstance(event, RiskEvent) else None,
            policy_version=event.policy_version if isinstance(event, PolicyEvent) else None,
            profile_version=getattr(event, "profile_version", None),
            threshold_version=getattr(event, "threshold_version", None),
            context_config_version=event.config_version
            if isinstance(event, ContextEvidence)
            else None,
            final_risk=event.risk_display_0_100 if isinstance(event, RiskEvent) else None,
            action=event.action if isinstance(event, PolicyEvent) else None,
            evidence_summary=event.evidence_summary
            if isinstance(event, RiskEvent)
            else [
                EvidenceSummary(
                    module=module, status=status, reason_codes=reasons, model_version=model_version
                )
            ],
        )
        with self.sessions.begin() as db:
            row = self._owned(db, p, session_id)
            if row.ended:
                raise Conflict()
            if event.call_id != row.call_id:
                raise ValueError("Event call mismatch")
            record = RiskRecord if isinstance(event, RiskEvent) else EvidenceRecord
            if isinstance(event, TranscriptEvent) and self.privacy is not None:
                self.privacy.retain(
                    db, p, session_id, "transcript", event.model_dump_json().encode()
                )
            db.add(
                record(
                    id=str(uuid4()),
                    tenant_id=p.tenant_id,
                    session_id=session_id,
                    timestamp=audit.timestamp,
                    payload=payload,
                )
            )
            db.add(
                AuditRecord(
                    id=audit.event_id,
                    tenant_id=p.tenant_id,
                    session_id=session_id,
                    timestamp=audit.timestamp,
                    payload=audit.model_dump(mode="json"),
                )
            )
            db.flush()
