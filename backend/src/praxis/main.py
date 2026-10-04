import asyncio
import base64
import json
import logging
from contextlib import asynccontextmanager, suppress
from datetime import timedelta
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import AwareDatetime, Field, ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from praxis import __version__
from praxis.audio.decode import decode_clip
from praxis.config import Settings
from praxis.contracts import (
    CONTRACT_VERSION,
    ArtifactState,
    AudioFrame,
    ComponentHealth,
    ConnectionEvent,
    ContextConfig,
    ContextInput,
    Contract,
    HealthStatus,
    ModelArtifactStatus,
    ModuleStatus,
    PolicyConfig,
    RetentionConfig,
    SessionStart,
)
from praxis.contracts.enrollment import EnrollmentRequest
from praxis.db.repository import Conflict, MissingResource, Repository, utcnow
from praxis.http_limits import BodyLimit
from praxis.logging_utils import configure_logging
from praxis.orchestration import ModelProcessor
from praxis.privacy import Privacy
from praxis.runtime import Runtime
from praxis.security import AccessDenied, Encryption, RateLimiter, Tokens, require_role
from praxis.speaker import SpeakerService
from praxis.streaming import StreamCapacity, StreamRegistry, UnavailableProcessor
from praxis.voip import Peer, VoipHub

logger = logging.getLogger("praxis")


class Login(Contract):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=1024, repr=False)
    tenant_id: str = Field(min_length=1, max_length=128)


class SessionDisplay(Contract):
    remote_name: str | None = Field(default=None, max_length=128)
    remote_number: str | None = Field(default=None, max_length=64)
    call_connected_at: AwareDatetime | None = None


def create_app(
    settings: Settings | None = None, repository: Repository | None = None, processor_factory=None
) -> FastAPI:
    configure_logging()
    settings = settings or Settings()  # type: ignore[call-arg]  # BaseSettings reads environment
    repo = repository or Repository.from_url(settings.database_url.get_secret_value())
    tokens = Tokens(settings)
    limiter = RateLimiter()
    registry = StreamRegistry(settings.max_connections)
    voip = VoipHub()
    runtime = Runtime(settings)
    privacy = Privacy(repo, Encryption(settings.embedding_key_base64.get_secret_value()))
    repo.privacy = privacy

    def new_processor(principal):
        if processor_factory:
            return processor_factory()
        return (
            ModelProcessor(runtime, repo, principal)
            if settings.models_enabled
            else UnavailableProcessor()
        )

    @asynccontextmanager
    async def lifespan(app):
        await asyncio.to_thread(runtime.load)

        async def retention_loop():
            while True:
                await asyncio.sleep(3600)
                try:
                    await asyncio.to_thread(privacy.purge)
                except SQLAlchemyError:
                    logger.error("retention_cleanup_failed")

        try:
            await asyncio.to_thread(privacy.purge)
        except SQLAlchemyError:
            logger.error("retention_cleanup_failed")
        cleanup = asyncio.create_task(retention_loop())
        try:
            yield
        finally:
            cleanup.cancel()
            with suppress(asyncio.CancelledError):
                await cleanup
            await runtime.close()
            if repository is None:
                await asyncio.to_thread(repo.engine.dispose)

    app = FastAPI(title="Praxis", version=__version__, lifespan=lifespan)
    app.state.repository = repo
    app.state.runtime = runtime
    app.state.voip = voip
    app.add_middleware(BodyLimit)
    if settings.webapp_origins:
        app.add_middleware(CORSMiddleware, allow_origins=settings.webapp_origins,
                          allow_methods=["GET", "POST"],
                          allow_headers=["Authorization", "Content-Type"])

    @app.middleware("http")
    async def request_metadata(request: Request, call_next):
        request_id = str(uuid4())
        # Headers carry no credentials in logs. Validation errors never echo request inputs.
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["Cache-Control"] = "no-store"
        logger.info(
            "request_complete", extra={"request_id": request_id, "status": response.status_code}
        )
        return response

    @app.exception_handler(RequestValidationError)
    @app.exception_handler(ValueError)
    async def invalid_request(request, exc):
        return JSONResponse(status_code=422, content={"detail": "INVALID_REQUEST"})

    @app.exception_handler(AccessDenied)
    async def denied(request, exc):
        return JSONResponse(status_code=403, content={"detail": "ACCESS_DENIED"})

    @app.exception_handler(MissingResource)
    async def missing(request, exc):
        return JSONResponse(status_code=404, content={"detail": "RESOURCE_NOT_FOUND"})

    @app.exception_handler(Conflict)
    @app.exception_handler(IntegrityError)
    async def conflict(request, exc):
        return JSONResponse(status_code=409, content={"detail": "STATE_CONFLICT"})

    @app.exception_handler(SQLAlchemyError)
    async def unavailable(request, exc):
        return JSONResponse(status_code=503, content={"detail": "PERSISTENCE_UNAVAILABLE"})

    def authenticate(header: str | None):
        if not header or not header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="AUTHENTICATION_REQUIRED")
        try:
            user, tenant = tokens.decode(header[7:])
            return repo.principal(user, tenant)
        except AccessDenied:
            raise HTTPException(status_code=401, detail="INVALID_ACCESS_TOKEN") from None

    from praxis.supplied.api import install_routes

    install_routes(app, runtime, repo, settings, authenticate, limiter)

    @app.post("/api/v1/auth/login")
    def login(value: Login, request: Request):
        ip = request.client.host if request.client else "unknown"
        if not limiter.allow("login:" + ip, 10, 60):
            raise HTTPException(status_code=429, detail="RATE_LIMITED")
        try:
            p = repo.login(value.username, value.password, value.tenant_id)
        except AccessDenied:
            raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS") from None
        return {
            "access_token": tokens.issue(p.user_id, p.tenant_id),
            "token_type": "bearer",  # nosec B105
            "expires_in": settings.token_ttl_minutes * 60,
            "expires_at": (utcnow() + timedelta(minutes=settings.token_ttl_minutes)).isoformat(),
            "tenant_id": p.tenant_id,
            "role": p.role,
            "username": value.username,
        }

    @app.websocket("/api/v1/voip")
    async def voip_socket(ws: WebSocket):
        peer = None
        async def close_safely(code: int) -> None:
            # A concurrent peer failure may already have closed this socket.
            with suppress(Exception):
                await ws.close(code=code)
        try:
            principal = await asyncio.to_thread(authenticate, ws.headers.get("authorization"))
            require_role(principal, "admin", "host")
            peer = Peer(principal, ws)
            if not await voip.register(peer):
                await close_safely(1008)
                return
            await ws.accept()
            await peer.send({"type": "ready", "username": await asyncio.to_thread(repo.voip_identity, principal)})
            while True:
                message = await ws.receive()
                if message["type"] == "websocket.disconnect":
                    break
                current = await asyncio.to_thread(authenticate, ws.headers.get("authorization"))
                if current.user_id != principal.user_id or current.tenant_id != principal.tenant_id:
                    await close_safely(1008)
                    break
                if message.get("bytes") is not None:
                    if not limiter.allow("voip-audio:" + principal.user_id, 65, 1):
                        await close_safely(1008)
                        break
                    if not await voip.relay(peer, message["bytes"]):
                        await close_safely(1008)
                        break
                    continue
                raw = message.get("text")
                if raw is None or len(raw) > 256 or not limiter.allow("voip-control:" + principal.user_id, 20, 1):
                    await close_safely(1008)
                    break
                data = json.loads(raw)
                if not isinstance(data, dict):
                    await close_safely(1007)
                    break
                action = data.get("type")
                if action == "ping":
                    await peer.send({"type": "pong"})
                elif action == "dial":
                    target = data.get("to")
                    if not isinstance(target, str) or not 1 <= len(target) <= 128:
                        await close_safely(1007)
                        break
                    recipient = await asyncio.to_thread(repo.voip_recipient, principal, target)
                    name = await asyncio.to_thread(repo.voip_identity, principal)
                    await voip.invite(peer, recipient or "", name)
                elif action == "accept":
                    await voip.accept(peer, str(data.get("call_id", "")))
                elif action == "hangup":
                    await voip.hangup(peer)
                else:
                    await close_safely(1007)
                    break
        except WebSocketDisconnect:
            pass
        except (HTTPException, AccessDenied):
            await close_safely(1008)
        except (ValueError, TypeError, json.JSONDecodeError):
            await close_safely(1007)
        except SQLAlchemyError:
            await close_safely(1013)
        finally:
            if peer:
                await voip.unregister(peer)

    @app.get("/api/v1/dashboard/sessions")
    async def dashboard_sessions(
        q: str = Query(default="", max_length=128),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
        active: bool | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ):
        p = await asyncio.to_thread(authenticate, authorization)
        connected = await registry.snapshot()
        active_voip = await voip.active_refs()
        return await asyncio.to_thread(repo.dashboard_sessions, p, connected, q, offset, limit, active, active_voip)

    @app.get("/api/v1/dashboard/sessions/{session_id}")
    async def dashboard_session(session_id: str, authorization: str | None = Header(default=None)):
        p = await asyncio.to_thread(authenticate, authorization)
        connected = await registry.snapshot()
        active_voip = await voip.active_refs()
        return await asyncio.to_thread(repo.dashboard_session, p, session_id, session_id in connected, active_voip)

    @app.get("/api/v1/dashboard/sessions/{session_id}/analysis")
    async def dashboard_analysis_history(
        session_id: str,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        authorization: str | None = Header(default=None),
    ):
        p = await asyncio.to_thread(authenticate, authorization)
        return await asyncio.to_thread(repo.analysis_history, p, session_id, limit, offset)

    @app.post("/api/v1/sessions", status_code=201)
    def start(value: SessionStart, authorization: str | None = Header(default=None)):
        p = authenticate(authorization)
        require_role(p, "admin", "host")
        return repo.start(p, value)

    @app.get("/api/v1/sessions/{session_id}")
    def get_session(session_id: str, authorization: str | None = Header(default=None)):
        return repo.get(authenticate(authorization), session_id)

    @app.put("/api/v1/sessions/{session_id}/display")
    def set_session_display(session_id: str, value: SessionDisplay,
                            authorization: str | None = Header(default=None)):
        p = authenticate(authorization)
        require_role(p, "admin", "host")
        repo.set_display(p, session_id, value.remote_name, value.remote_number,
                         value.call_connected_at)
        return {"status": "AVAILABLE"}

    @app.post("/api/v1/sessions/{session_id}/end")
    def end_session(session_id: str, authorization: str | None = Header(default=None)):
        p = authenticate(authorization)
        require_role(p, "admin", "host")
        return repo.end(p, session_id)

    @app.patch("/api/v1/sessions/{session_id}/context")
    def update_context(
        session_id: str, value: ContextInput, authorization: str | None = Header(default=None)
    ):
        p = authenticate(authorization)
        require_role(p, "admin", "host")
        return repo.context(p, session_id, value)

    @app.get("/api/v1/audit/{session_id}")
    def audit(
        session_id: str,
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
        authorization: str | None = Header(default=None),
    ):
        p = authenticate(authorization)
        require_role(p, "admin", "analyst")
        return repo.audit(p, session_id, limit, offset)

    @app.get("/api/v1/health")
    def health():
        ready = repo.healthy()
        status = ModuleStatus.AVAILABLE if ready else ModuleStatus.UNAVAILABLE
        components = {
            "backend": ComponentHealth(status=ModuleStatus.AVAILABLE, version=__version__),
            "database": ComponentHealth(
                status=status, reason_codes=[] if ready else ["DATABASE_UNAVAILABLE"]
            ),
        }
        for module in ["audio", "whisper", "ecapa", "prosody", "minilm", "ai_text"]:
            components[module] = runtime.health.get(
                module,
                ComponentHealth(status=ModuleStatus.UNAVAILABLE, reason_codes=["NOT_CONNECTED"]),
            )
        components["linguistic_rules"] = ComponentHealth(
            status=ModuleStatus.AVAILABLE, version="rules-en-1.0.0"
        )
        components["policy"] = ComponentHealth(
            status=ModuleStatus.AVAILABLE,
            version="sih-policy-v1",
            reason_codes=["REQUIRES_VALID_RISK"],
        )
        if "risk" in runtime.health:
            components["risk"] = runtime.health["risk"]
        if any(v.status == ModuleStatus.ERROR for v in components.values()):
            status = ModuleStatus.ERROR
        value = HealthStatus(
            service_version=__version__,
            contract_version=CONTRACT_VERSION,
            status=status,
            components=components,
            artifacts=[
                ModelArtifactStatus(
                    module=n,
                    state=runtime.risk_state if n == "risk" else ArtifactState.UNVALIDATED,
                    version=runtime.risk_version if n == "risk" else None,
                    reason_codes=[]
                    if n == "risk" and runtime.risk_state == ArtifactState.VALIDATED
                    else ["NO_VALIDATED_ARTIFACT"],
                )
                for n in ["minilm", "ai_text", "risk", "speaker_thresholds", "prosody_classifier"]
            ],
            timestamp=utcnow(),
        )
        return JSONResponse(
            value.model_dump(mode="json"),
            status_code=200 if status == ModuleStatus.AVAILABLE else 503,
        )

    @app.post("/api/v1/speaker-enrollments", status_code=201)
    async def enroll(value: EnrollmentRequest, authorization: str | None = Header(default=None)):
        p = await asyncio.to_thread(authenticate, authorization)
        require_role(p, "admin")
        if "ecapa" not in runtime.models:
            raise HTTPException(status_code=503, detail="SPEAKER_MODEL_UNAVAILABLE")
        if not limiter.allow("enroll:" + p.tenant_id, 3, 60):
            raise HTTPException(status_code=429, detail="RATE_LIMITED")
        clips = [
            await asyncio.to_thread(decode_clip, base64.b64decode(v, validate=True))
            for v in value.clips_base64
        ]
        service = SpeakerService(
            repo,
            runtime.models["ecapa"],
            Encryption(settings.embedding_key_base64.get_secret_value()),
        )
        return await runtime.run(
            service.enroll,
            p,
            value.session_id,
            value.identity,
            clips,
            value.approved,
            value.clips_base64,
        )

    @app.put("/api/v1/config/context")
    def context_config(
        value: ContextConfig, session_id: str, authorization: str | None = Header(default=None)
    ):
        return repo.save_config(authenticate(authorization), session_id, "context", value)

    @app.delete("/api/v1/speaker-enrollments/{identity}")
    def delete_enrollment(identity: str, session_id: str, authorization: str | None = Header(default=None)):
        return repo.delete_profile(authenticate(authorization), session_id, identity)

    @app.get("/api/v1/config/{kind}")
    def get_config(kind: str, authorization: str | None = Header(default=None)):
        p = authenticate(authorization)
        require_role(p, "admin", "analyst")
        defaults = {"context": ContextConfig(tenant_id=p.tenant_id, version="sih-context-v1"),
                    "policy": PolicyConfig(tenant_id=p.tenant_id, policy_version="sih-policy-v1"),
                    "retention": RetentionConfig(tenant_id=p.tenant_id, version="privacy-default-v1")}
        if kind not in defaults:
            raise MissingResource()
        return repo.config(p, kind) or defaults[kind]

    @app.put("/api/v1/config/policy")
    def policy_config(
        value: PolicyConfig, session_id: str, authorization: str | None = Header(default=None)
    ):
        return repo.save_config(authenticate(authorization), session_id, "policy", value)

    @app.put("/api/v1/config/retention")
    def retention_config(
        value: RetentionConfig, session_id: str, authorization: str | None = Header(default=None)
    ):
        result = repo.save_config(authenticate(authorization), session_id, "retention", value)
        privacy.purge()
        return result

    @app.get("/api/v1/sessions/{session_id}/retained")
    def retained(
        session_id: str,
        limit: int = Query(default=100, ge=1, le=100),
        authorization: str | None = Header(default=None),
    ):
        return privacy.list(authenticate(authorization), session_id, limit)

    @app.get("/api/v1/sessions/{session_id}/retained/{payload_id}")
    def retained_payload(
        session_id: str, payload_id: str, authorization: str | None = Header(default=None)
    ):
        return privacy.read(authenticate(authorization), session_id, payload_id)

    @app.websocket("/api/v1/stream/{session_id}")
    async def stream(ws: WebSocket, session_id: str):
        processor = None
        sender = None
        receive_task = None
        send_lock = asyncio.Lock()

        async def send(value):
            async with send_lock:
                await ws.send_json(value)

        async def deliver(event):
            current = await asyncio.to_thread(authenticate, ws.headers.get("authorization"))
            require_role(current, "admin", "host")
            await asyncio.to_thread(repo.record_event, current, session_id, event)
            await send(event.model_dump(mode="json"))

        async def send_events(active_processor):
            while True:
                event = await active_processor.next_event()
                await asyncio.to_thread(authenticate, ws.headers.get("authorization"))
                await deliver(event)

        try:
            p = await asyncio.to_thread(authenticate, ws.headers.get("authorization"))
            require_role(p, "admin", "host")
            session = await asyncio.to_thread(repo.get, p, session_id)
            if session.ended_at:
                raise Conflict()
            async with registry.acquire(session_id):
                processor = new_processor(p)
                await ws.accept()
                last_sequence, last_timestamp = await asyncio.to_thread(
                    repo.sequence_state, p, session_id
                )
                await send(
                    ConnectionEvent(
                        session_id=session_id,
                        contract_version=CONTRACT_VERSION,
                        last_sequence_id=last_sequence,
                        last_timestamp_ms=last_timestamp,
                        reason_codes=["NEW_CONNECTION_BUFFER_RESET"],
                    ).model_dump(mode="json")
                )
                if hasattr(processor, "next_event"):
                    sender = asyncio.create_task(send_events(processor))
                while True:
                    receive_task = asyncio.create_task(ws.receive_text())
                    waiters = [receive_task] + ([sender] if sender else [])
                    done, _ = await asyncio.wait(
                        waiters,
                        timeout=settings.stream_timeout_seconds,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    if not done:
                        raise asyncio.TimeoutError()
                    if sender is not None and sender in done:
                        await sender  # Surface persistence/sender failure; never silently continue.
                    message = await receive_task
                    p = await asyncio.to_thread(authenticate, ws.headers.get("authorization"))
                    require_role(p, "admin", "host")
                    if len(message.encode()) > settings.max_message_bytes:
                        await ws.close(code=1009)
                        return
                    if not limiter.allow("stream:" + session_id, settings.max_frames_per_second, 1):
                        await ws.close(code=1008)
                        return
                    parsed = json.loads(message)
                    if parsed == {"type": "ping"}:
                        await send({"type": "pong"})
                        continue
                    frame = AudioFrame.model_validate_json(message)
                    gap = await asyncio.to_thread(
                        repo.accept_sequence, p, session_id, frame.sequence_id, frame.timestamp_ms
                    )
                    if gap:
                        if sender:
                            sender.cancel()
                            with suppress(asyncio.CancelledError):
                                await sender
                        await processor.close()
                        processor = new_processor(p)
                        sender = (
                            asyncio.create_task(send_events(processor))
                            if hasattr(processor, "next_event")
                            else None
                        )
                        await send({"type": "analysis_gap", "reason_codes": ["SEQUENCE_GAP"]})
                    session = await asyncio.to_thread(repo.get, p, session_id)
                    for event in await processor.process(session, frame):
                        await deliver(event)
                    await send({"type": "ack", "sequence_id": frame.sequence_id})
        except WebSocketDisconnect:
            return
        except (HTTPException, AccessDenied, MissingResource):
            await ws.close(code=1008)
        except (ValidationError, ValueError):
            await ws.close(code=1007)
        except (Conflict, StreamCapacity):
            await ws.close(code=1008)
        except (SQLAlchemyError, asyncio.TimeoutError):
            await ws.close(code=1013)
        finally:
            for task in [sender, receive_task]:
                if task is not None:
                    task.cancel()
                    with suppress(asyncio.CancelledError, Exception):
                        await task
            if processor is not None:
                await processor.close()

    return app
