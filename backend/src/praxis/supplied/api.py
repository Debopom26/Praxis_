"""Authenticated opt-in V2 integration; V1 contracts remain unchanged."""
import asyncio
import base64
import json
import math
from typing import Literal

import numpy as np
from fastapi import Header, HTTPException
from pydantic import Field

from praxis.contracts import Contract
from praxis.contracts.base import Identifier
from praxis.db.models import SpeakerProfile
from praxis.db.repository import utcnow
from praxis.security import Encryption, require_role


class AnalysisRequest(Contract):
    session_id: Identifier
    pcm_f32le_base64: str = Field(min_length=1, max_length=10240000, repr=False)
    sample_rate: Literal[16000] = 16000
    channels: Literal[1] = 1


def install_routes(app, runtime, repo, settings, authenticate, limiter):
    @app.get("/api/v2/health")
    def health(authorization: str | None = Header(default=None)):
        authenticate(authorization)
        if runtime.supplied is None:
            raise HTTPException(503, runtime.supplied_error or "SUPPLIED_MODELS_NOT_ENABLED")
        result = runtime.supplied.health()
        if result["status"] != "AVAILABLE":
            raise HTTPException(503, "SUPPLIED_WORKER_UNAVAILABLE")
        return result

    @app.post("/api/v2/analysis")
    async def analyze(value: AnalysisRequest, authorization: str | None = Header(default=None)):
        principal = await asyncio.to_thread(authenticate, authorization)
        require_role(principal, "admin", "host")
        session = await asyncio.to_thread(repo.get, principal, value.session_id)
        if session.ended_at:
            raise HTTPException(409, "SESSION_ENDED")
        if runtime.supplied is None:
            raise HTTPException(503, "SUPPLIED_MODELS_NOT_ENABLED")
        if not limiter.allow("supplied:" + principal.tenant_id, 30, 60):
            raise HTTPException(429, "RATE_LIMITED")
        raw = base64.b64decode(value.pcm_f32le_base64, validate=True)
        if len(raw) % 4 or not 64000 <= len(raw) <= 7680000:
            raise ValueError("Invalid PCM length")
        audio = np.frombuffer(raw, dtype="<f4").copy()
        if not np.isfinite(audio).all():
            raise ValueError("Non-finite PCM")
        reference = None
        profile_reason = None
        # Profile lookup remains tenant-scoped and uses existing encryption/AAD.
        if session.claimed_identity:
            with repo.sessions() as db:
                row = db.get(SpeakerProfile, (principal.tenant_id, session.claimed_identity))
                if row:
                    revisions = runtime.supplied.config["models"]["ecapa"].get("archive_metadata_revisions", [])
                    if row.model_version in revisions:
                        reference = json.loads(Encryption(settings.embedding_key_base64.get_secret_value()).decrypt(
                            row.encrypted_centroid, principal.tenant_id, row.identity, row.version))
                    else:
                        profile_reason = "MODEL_VERSION_MISMATCH"
        host_context = {"caller_in_contacts": session.permitted_context.known_contact}
        try:
            result = await asyncio.to_thread(runtime.supplied.analyze, audio, host_context, reference)
        except RuntimeError as exc:
            raise HTTPException(429 if str(exc) == "ANALYSIS_BUSY" else 503,
                                "ANALYSIS_BUSY" if str(exc) == "ANALYSIS_BUSY" else "ANALYSIS_UNAVAILABLE") from None
        if profile_reason:
            result["ecapa"] = {"status": "UNAVAILABLE", "available": False, "reason": profile_reason}
        # Commit allowlisted metadata before delivering a result; never persist PCM,
        # transcript, biometric vectors, or untrained output as validated final risk.
        def record():
            with repo.sessions.begin() as db:
                owned = repo._owned(db, principal, value.session_id)
                if owned.ended:
                    raise HTTPException(409, "SESSION_ENDED")
                score = result.get("experimental_score_0_100")
                if isinstance(score, (int, float)) and math.isfinite(score) and 0 <= score <= 100:
                    advice = result.get("guidance", {})
                    owned.latest_analysis = {
                        "experimental_score_0_100": float(score),
                        "regressor_status": str(result.get("regressor_status", ""))[:128],
                        "action": str(advice.get("action", ""))[:128],
                        "message": str(advice.get("message", ""))[:2000],
                    }
                    owned.latest_analysis_at = utcnow()
                repo._audit(db, principal, value.session_id, "supplied_analysis",
                            ["BOOTSTRAP_UNTRAINED", result["guidance"]["assessment"]],
                            policy_version="benign-ai-guidance-1")
        await asyncio.to_thread(record)
        return result
