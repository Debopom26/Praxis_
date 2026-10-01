from pydantic import AwareDatetime, Field, StrictBool

from .base import Contract, Identifier
from .context import ContextInput


class SessionStart(Contract):
    tenant_id: Identifier
    call_id: Identifier
    host_app_id: Identifier
    claimed_identity: Identifier | None = None
    permitted_context: ContextInput = Field(default_factory=ContextInput)
    created_at: AwareDatetime
    supports_hold: StrictBool = False


class SessionView(SessionStart):
    session_id: Identifier
    ended_at: AwareDatetime | None = None


class RetentionConfig(Contract):
    tenant_id: Identifier
    version: str
    retain_transcript: StrictBool = False
    retain_enrollment_audio: StrictBool = False
    metadata_days: int = Field(default=30, ge=1, le=3650)
