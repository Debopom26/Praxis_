"""Opt-in live Compose verification. Uses disposable tenants; never prints credentials.

Run from the project root after startup. Requires the project Python environment,
Docker CLI access, and localhost Caddy. The local CA is trusted only by this client.
This is deployment verification, not model/identity accuracy validation.
"""

import base64
import hashlib
import json
import os
import secrets
import shutil
import ssl
import subprocess
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
import jwt
from dotenv import dotenv_values
from websockets.exceptions import ConnectionClosed, InvalidStatus
from websockets.sync.client import connect

ROOT = Path(__file__).resolve().parents[1]
DOCKER = shutil.which("docker") or str(
    Path(os.environ["LOCALAPPDATA"]) / "Programs/DockerDesktop/resources/bin/docker.exe"
)
COMPOSE = [
    DOCKER,
    "compose",
    "--env-file",
    str(ROOT / ".env"),
    "-f",
    str(ROOT / "deployment/compose.yaml"),
]
REPORT = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "checks": {},
    "scope": "Real PostgreSQL and deployed HTTPS/WSS; synthetic fixtures only; local CA trust",
}
SENSITIVE = []


def command(args, data=None, timeout=120):
    result = subprocess.run(
        args,
        input=data,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        cwd=ROOT,
        check=False,
    )
    if result.returncode:
        # Never forward unfiltered Docker/DB exceptions or subprocess arguments.
        raise RuntimeError(
            "Deployment verification subprocess failed (exit %s)" % result.returncode
        )
    return result.stdout


def remote(code, data=None):
    source = "import json,sys\nx=json.load(sys.stdin)\n" + code
    return command(COMPOSE + ["exec", "-T", "backend", "python", "-c", source], json.dumps(data))


def sql(statement):
    return command(
        COMPOSE
        + [
            "exec",
            "-T",
            "database",
            "psql",
            "-U",
            "praxis_owner",
            "-d",
            "praxis",
            "-v",
            "ON_ERROR_STOP=1",
            "-At",
        ],
        statement,
    )


def record(name, detail=True):
    REPORT["checks"][name] = detail
    (ROOT / "docs/DEPLOYMENT_VERIFICATION.json").write_text(
        json.dumps(REPORT, indent=2) + "\n", encoding="utf-8"
    )
    print("PASS:", name, flush=True)
    if name in {
        "migrations_0001_0002_schema",
        "runtime_least_privilege",
        "https_health_models_and_unvalidated_artifacts",
        "trusted_wss_auth_ping_ack_reconnect_duplicate_sequence_gap",
        "postgres_trigger_audit_failure_rolls_back_deployed_mutations",
        "environment_keys_unchanged",
    }:
        milestone = (
            "## Live verification milestone - "
            + datetime.now(timezone.utc).isoformat()
            + "\n\nLatest completed check: `"
            + name
            + "`. Exact observed checks: "
            "docs/DEPLOYMENT_VERIFICATION.json. The run is still in progress unless its "
            "result says PASSED. Existing .env preserved; temporary verification tenants "
            "are cleaned in the runner's finally block. Historical checkpoints below "
            "must not override newer observed results.\n\n"
        )
        for filename in ["MEMORY.md", "CONTEXT_SHIFT.md"]:
            path = ROOT / filename
            heading, rest = path.read_text(encoding="utf-8").split("\n", 1)
            path.write_text(heading + "\n\n" + milestone + rest.lstrip(), encoding="utf-8")


def admin(tenant, username, password):
    # Exercise the documented script in a real Linux PTY, including getpass's
    # non-echo password prompt. Credentials travel through stdin, never argv.
    remote(
        """
import os,pty,select,time
pid,fd=pty.fork()
if pid==0:
    os.execvp('python',['python','/app/scripts/create_admin.py'])
prompts=[b'Organization ID: ',b'Organization name: ',b'Administrator username: ',b'New password (at least 12 characters): ']
answers=[x['tenant'], 'P10 disposable verification', x['username'],x['password']]
pending=b''; transcript=b''; deadline=time.monotonic()+45
for prompt,answer in zip(prompts,answers):
    while prompt not in pending:
        if time.monotonic()>deadline: raise RuntimeError('Interactive prompt timeout')
        if select.select([fd],[],[],1)[0]:
            chunk=os.read(fd,4096); pending+=chunk; transcript+=chunk
    pending=b''
    os.write(fd,(answer+'\\n').encode())
while time.monotonic()<deadline:
    if select.select([fd],[],[],1)[0]:
        try: chunk=os.read(fd,4096)
        except OSError: break
        if not chunk: break
        transcript+=chunk
_,status=os.waitpid(pid,0)
os.close(fd)
assert os.waitstatus_to_exitcode(status)==0
assert b'Organization administrator created' in transcript
assert x['password'].encode() not in transcript
""",
        {"tenant": tenant, "username": username, "password": password},
    )


def cleanup(tenants):
    remote(
        """
from sqlalchemy import delete,select
from praxis.config import Settings
from praxis.db.repository import Repository
from praxis.db.models import AuditRecord,EvidenceRecord,RiskRecord,RetainedPayload,SessionRecord,SpeakerProfile,Configuration,Membership,Organization,User
r=Repository.from_url(Settings().database_url.get_secret_value())
assert all(t.startswith('p10-verify-') for t in x)
with r.sessions.begin() as db:
    users=list(db.scalars(select(Membership.user_id).where(Membership.tenant_id.in_(x))))
    for model in [RetainedPayload,EvidenceRecord,RiskRecord,AuditRecord,SpeakerProfile,SessionRecord,Configuration,Membership]:
        db.execute(delete(model).where(model.tenant_id.in_(x)))
    db.execute(delete(Organization).where(Organization.id.in_(x)))
    db.execute(delete(User).where(User.id.in_(users),~User.id.in_(select(Membership.user_id))))
r.engine.dispose()
""",
        tenants,
    )


def run():
    env = dotenv_values(ROOT / ".env")
    if env.get("PRAXIS_HOST", "localhost") != "localhost":
        raise RuntimeError("This disruptive verification runner is for local development only")
    required = [
        "PRAXIS_OWNER_PASSWORD",
        "PRAXIS_RUNTIME_PASSWORD",
        "PRAXIS_JWT_SECRET",
        "PRAXIS_EMBEDDING_KEY_BASE64",
    ]
    assert all(env.get(k) for k in required)
    SENSITIVE.extend(env[k] for k in required)
    before_env = hashlib.sha256((ROOT / ".env").read_bytes()).hexdigest()
    assert env["PRAXIS_OWNER_PASSWORD"] != env["PRAXIS_RUNTIME_PASSWORD"]
    record("distinct_existing_credentials_preserved")
    states = [
        json.loads(line)
        for line in command(COMPOSE + ["ps", "--all", "--format", "json"]).splitlines()
        if line.strip()
    ]
    assert any(s["Service"] == "database" and s["Health"] == "healthy" for s in states)
    assert any(s["Service"] == "migrate" and s["ExitCode"] == 0 for s in states)
    record("postgres_healthy_and_migration_exit_zero")
    assert sql("SELECT version_num FROM alembic_version;").strip() == "0002"
    tables = sql(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"
    ).splitlines()
    assert "retained_payloads" in tables and "sessions" in tables and "audit_events" in tables
    record("migrations_0001_0002_schema", tables)
    record("postgres_version", sql("SHOW server_version;").strip())
    # A fresh deployment has no pre-seeded account. On later runs, report counts
    # without treating legitimately operator-created users as defaults.
    record("pre_verification_user_count", int(sql("SELECT count(*) FROM users;").strip()))
    privileges = json.loads(
        remote("""
from praxis.config import Settings
from sqlalchemy import create_engine,text
e=create_engine(Settings().database_url.get_secret_value(),hide_parameters=True)
with e.connect() as c:
    role=c.execute(text("SELECT current_user,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=current_user")).one()
    assert role[0]=='praxis_runtime' and not any(role[1:])
    assert c.execute(text("SELECT count(*) FROM pg_tables WHERE schemaname='public' AND tableowner=current_user")).scalar()==0
    for statement in ['CREATE TABLE public.p10_forbidden(id integer)','ALTER TABLE sessions ADD COLUMN p10_forbidden integer','SELECT * FROM alembic_version','CREATE ROLE p10_forbidden','CREATE TEMP TABLE p10_forbidden(id integer)']:
        c.rollback()
        try:
            c.execute(text(statement))
        except Exception as exc:
            assert getattr(exc.orig,'sqlstate',None)=='42501'
        else:
            c.rollback(); raise AssertionError('Runtime has unnecessary administrative privileges')
    c.rollback()
print(json.dumps({'role':role[0],'superuser':role[1],'owns_tables':False,'ddl_role_migration_temp_denied':True}))
""")
    )
    record("runtime_least_privilege", privileges)
    ca = ROOT / ".cache/p10-caddy-root.crt"
    ca.write_text(
        command(
            COMPOSE
            + [
                "exec",
                "-T",
                "caddy",
                "cat",
                "/data/caddy/pki/authorities/local/root.crt",
            ]
        ),
        encoding="ascii",
    )
    trust = ssl.create_default_context(cafile=str(ca))
    assert trust.verify_mode == ssl.CERT_REQUIRED and trust.check_hostname
    try:
        with httpx.Client(trust_env=False) as untrusted:
            untrusted.get("https://localhost/api/v1/health")
    except httpx.ConnectError:
        record("untrusted_local_ca_rejected")
    else:
        raise AssertionError("Local CA unexpectedly globally trusted; review trust test")
    with httpx.Client(
        base_url="https://localhost", verify=trust, trust_env=False, timeout=120
    ) as client:
        for _ in range(90):
            try:
                health = client.get("/api/v1/health")
                if health.status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(2)
        else:
            raise AssertionError("Deployed models/service not healthy")
        h = health.json()
        assert h["components"]["database"]["status"] == "AVAILABLE"
        assert all(a["state"] == "UNVALIDATED" for a in h["artifacts"])
        assert all(
            h["components"][m]["status"] == "AVAILABLE"
            for m in ["audio", "whisper", "ecapa", "prosody", "minilm", "ai_text"]
        )
        record("https_health_models_and_unvalidated_artifacts", h)
        assert health.headers["strict-transport-security"] == "max-age=31536000"
        record("caddy_https_security_headers")
        assert client.post("/api/v1/auth/login", content=b"x" * 65537).status_code == 413
        record("deployed_request_body_limit")
        suffix = uuid4().hex[:12]
        tenants = ["p10-verify-" + suffix + "-a", "p10-verify-" + suffix + "-b"]
        identities = [(t, t + "-admin", secrets.token_urlsafe(36)) for t in tenants]
        for _, _, p in identities:
            SENSITIVE.append(p)
        try:
            for identity in identities:
                admin(*identity)
            record("documented_interactive_admin_creation_no_password_echo")
            headers = []
            for t, u, p in identities:
                response = client.post(
                    "/api/v1/auth/login", json=dict(tenant_id=t, username=u, password=p)
                )
                assert response.status_code == 200
                token = response.json()["access_token"]
                SENSITIVE.append(token)
                headers.append({"Authorization": "Bearer " + token})
            a, b = headers
            t1, t2 = tenants
            payload = dict(
                tenant_id=t1,
                call_id="p10-call-" + suffix,
                host_app_id="p10-verification",
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            assert client.post("/api/v1/sessions", json=payload).status_code == 401
            assert client.post("/api/v1/sessions", json=payload, headers=b).status_code == 403
            for changes in [{"exp": 1}, {"iss": "wrong"}, {"aud": "wrong"}]:
                claims = jwt.decode(
                    a["Authorization"][7:],
                    env["PRAXIS_JWT_SECRET"],
                    algorithms=["HS256"],
                    audience="praxis-sdk",
                    issuer="praxis",
                )
                forged = jwt.encode(claims | changes, env["PRAXIS_JWT_SECRET"], algorithm="HS256")
                SENSITIVE.append(forged)
                assert (
                    client.post(
                        "/api/v1/sessions",
                        json=payload,
                        headers={"Authorization": "Bearer " + forged},
                    ).status_code
                    == 401
                )
            assert (
                client.post(
                    "/api/v1/sessions",
                    json=payload,
                    headers={"Authorization": a["Authorization"] + "bad"},
                ).status_code
                == 401
            )
            response = client.post("/api/v1/sessions", json=payload, headers=a)
            assert response.status_code == 201
            sid = response.json()["session_id"]
            route = "/api/v1/sessions/" + sid
            assert (
                client.patch(
                    route + "/context", json={"known_contact": True}, headers=a
                ).status_code
                == 200
            )
            assert client.get(route, headers=a).json()["permitted_context"]["known_contact"] is True
            assert client.get(route, headers=b).status_code == 404
            assert (
                client.patch(
                    route + "/context", json={"known_contact": False}, headers=b
                ).status_code
                == 404
            )
            assert client.get("/api/v1/audit/" + sid, headers=b).status_code == 404
            record("auth_jwt_expiry_issuer_audience_tenant_and_session_context")
            # Role changes in the real DB must take effect for an already-issued JWT.
            remote(
                "from praxis.config import Settings\nfrom sqlalchemy import create_engine,text\ne=create_engine(Settings().database_url.get_secret_value(),hide_parameters=True)\nwith e.begin() as c:c.execute(text(\"UPDATE memberships SET role='analyst' WHERE tenant_id=:t\"),{'t':x})",
                t1,
            )
            assert (
                client.post(
                    "/api/v1/sessions",
                    json=payload | {"call_id": "analyst-denied"},
                    headers=a,
                ).status_code
                == 403
            )
            assert client.patch(route + "/context", json={}, headers=a).status_code == 403
            assert client.get("/api/v1/audit/" + sid, headers=a).status_code == 200
            remote(
                "from praxis.config import Settings\nfrom sqlalchemy import create_engine,text\ne=create_engine(Settings().database_url.get_secret_value(),hide_parameters=True)\nwith e.begin() as c:c.execute(text(\"UPDATE memberships SET role='admin' WHERE tenant_id=:t\"),{'t':x})",
                t1,
            )
            record("live_membership_rbac_rechecked")
            for kind, versionkey in [
                ("context", "version"),
                ("policy", "policy_version"),
                ("retention", "version"),
            ]:
                own = client.get("/api/v1/config/" + kind, headers=a).json()
                other = client.get("/api/v1/config/" + kind, headers=b).json()
                assert own["tenant_id"] == t1 and other["tenant_id"] == t2
                own[versionkey] = "p10-" + suffix
                assert (
                    client.put(
                        "/api/v1/config/" + kind,
                        params={"session_id": sid},
                        json=own,
                        headers=b,
                    ).status_code
                    == 403
                )
                assert (
                    client.put(
                        "/api/v1/config/" + kind,
                        params={"session_id": sid},
                        json=own,
                        headers=a,
                    ).status_code
                    == 200
                )
                assert (
                    client.get("/api/v1/config/" + kind, headers=b).json()[versionkey]
                    != "p10-" + suffix
                )
            record("tenant_configuration_policy_isolation")
            verify_wss(sid, a, b, trust)
            # Fault injection is a real PostgreSQL trigger scoped only to this
            # disposable tenant. No mock DB or bypass of deployed authentication.
            trigger = "p10_" + suffix
            sql(
                f"CREATE FUNCTION {trigger}() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.tenant_id='{t1}' THEN RAISE EXCEPTION 'P10 controlled audit failure'; END IF; RETURN NEW; END $$; CREATE TRIGGER {trigger} BEFORE INSERT ON audit_events FOR EACH ROW EXECUTE FUNCTION {trigger}();"
            )
            try:
                assert (
                    client.patch(
                        route + "/context", json={"known_contact": False}, headers=a
                    ).status_code
                    == 503
                )
                assert (
                    client.get(route, headers=a).json()["permitted_context"]["known_contact"]
                    is True
                )
                assert (
                    client.post(
                        "/api/v1/sessions",
                        json=payload | {"call_id": "p10-rollback-" + suffix},
                        headers=a,
                    ).status_code
                    == 503
                )
                assert (
                    sql(
                        f"SELECT count(*) FROM sessions WHERE call_id='p10-rollback-{suffix}';"
                    ).strip()
                    == "0"
                )
                with connect(
                    "wss://localhost/api/v1/stream/" + sid,
                    ssl=trust,
                    additional_headers=a,
                    proxy=None,
                ) as ws:
                    assert json.loads(ws.recv())["last_sequence_id"] == 3
                    ws.send(
                        json.dumps(
                            dict(
                                sequence_id=6,
                                timestamp_ms=600,
                                format=dict(sample_rate=16000, channels=1),
                                audio_base64=base64.b64encode(bytes(320)).decode(),
                            )
                        )
                    )
                    try:
                        ws.recv()
                    except ConnectionClosed as exc:
                        assert exc.rcvd.code == 1013
                    else:
                        raise AssertionError("Audit failure was acknowledged over WSS")
                record("real_wss_audit_failure_closes_without_ack")
            finally:
                sql(
                    f"DROP TRIGGER IF EXISTS {trigger} ON audit_events; DROP FUNCTION IF EXISTS {trigger}();"
                )
            record("postgres_trigger_audit_failure_rolls_back_deployed_mutations")
            verify_privacy(sid, tenants, payload["call_id"])
            # A real synthetic-speech approved enrollment exercises actual ECAPA,
            # quality gates, AES storage and the deployed API; no identity claim.
            wave = (ROOT / ".cache/synthetic-speech.wav").read_bytes()
            encoded = base64.b64encode(wave).decode()
            SENSITIVE.append(encoded)
            enr = client.post(
                "/api/v1/speaker-enrollments",
                json=dict(
                    session_id=sid,
                    identity="p10-synthetic",
                    approved=True,
                    clips_base64=[encoded] * 3,
                ),
                headers=a,
            )
            assert enr.status_code == 201, "Synthetic enrollment workflow failed"
            assert enr.json()["threshold_state"] == "UNVALIDATED"
            remote(
                """
import json
from praxis.config import Settings
from praxis.db.repository import Repository
from praxis.db.models import SpeakerProfile,RetainedPayload
from praxis.security import Encryption
from sqlalchemy import select,func
s=Settings();r=Repository.from_url(s.database_url.get_secret_value())
with r.sessions() as db:
    row=db.get(SpeakerProfile,(x,'p10-synthetic'));assert row and row.model_version and row.version
    plain=Encryption(s.embedding_key_base64.get_secret_value()).decrypt(row.encrypted_centroid,x,row.identity,row.version)
    assert len(json.loads(plain))==192 and plain not in row.encrypted_centroid
    assert db.scalar(select(func.count()).select_from(RetainedPayload).where(RetainedPayload.tenant_id==x,RetainedPayload.kind=='enrollment'))==0
""",
                t1,
            )
            assert (
                client.delete(
                    "/api/v1/speaker-enrollments/p10-synthetic",
                    params={"session_id": sid},
                    headers=b,
                ).status_code
                == 404
            )
            assert (
                client.delete(
                    "/api/v1/speaker-enrollments/p10-synthetic",
                    params={"session_id": sid},
                    headers=a,
                ).json()["deleted"]
                is True
            )
            record(
                "actual_ecapa_synthetic_profile_encrypted_tenant_scoped_deleted_audio_default_off"
            )
            remote(
                "from pathlib import Path\nassert not any(p.suffix.lower() in {'.wav','.flac','.pcm','.raw'} for root in ['/tmp','/app/.cache'] for p in Path(root).rglob('*') if p.is_file())"
            )
            record("no_live_audio_files_in_writable_container_paths")
            command(COMPOSE + ["stop", "database"])
            try:
                unavailable = client.get("/api/v1/health")
                assert unavailable.status_code == 503
                assert unavailable.json()["components"]["database"]["status"] == "UNAVAILABLE"
            finally:
                command(COMPOSE + ["start", "database"])
            record("deployed_health_reports_real_database_outage")
            # Persisted context/sequence survive actual database/backend restarts.
            command(COMPOSE + ["restart", "database", "backend"], timeout=180)
            for _ in range(90):
                try:
                    if client.get("/api/v1/health").status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(2)
            else:
                raise AssertionError("Restart health timeout")
            assert client.get(route, headers=a).json()["permitted_context"]["known_contact"] is True
            with connect(
                "wss://localhost/api/v1/stream/" + sid,
                ssl=trust,
                additional_headers=a,
                proxy=None,
            ) as ws:
                assert json.loads(ws.recv())["last_sequence_id"] == 3
            assert client.post(route + "/end", headers=a).json()["ended_at"]
            assert client.patch(route + "/context", json={}, headers=a).status_code == 409
            record("postgres_volume_backend_restart_session_context_sequence_and_completion")
            audits = client.get("/api/v1/audit/" + sid, headers=a).json()
            assert all(e.get("call_id") == payload["call_id"] for e in audits)
            record("audit_call_provenance", len(audits))
        finally:
            cleanup(tenants)
            record("disposable_tenants_users_profiles_and_credentials_removed")
    logs = command(COMPOSE + ["logs", "--no-color"])
    assert not any(s and s in logs for s in SENSITIVE), "Sensitive content found in logs"
    assert not any(
        marker in logs
        for marker in [
            "encrypted_centroid",
            "audio_base64",
            "clips_base64",
            "Bearer eyJ",
        ]
    )
    record("container_log_secret_token_audio_embedding_marker_scan")
    assert hashlib.sha256((ROOT / ".env").read_bytes()).hexdigest() == before_env
    record("environment_keys_unchanged")


def verify_wss(sid, a, b, trust):
    url = "wss://localhost/api/v1/stream/" + sid
    for headers in [{}, b]:
        try:
            with connect(url, ssl=trust, additional_headers=headers, proxy=None):
                pass
        except InvalidStatus:
            pass
        else:
            raise AssertionError("Unauthorized WSS accepted")
    frame = dict(
        sequence_id=0,
        timestamp_ms=0,
        format=dict(sample_rate=16000, channels=1),
        audio_base64=base64.b64encode(bytes(320)).decode(),
    )
    with connect(url, ssl=trust, additional_headers=a, proxy=None) as ws:
        assert json.loads(ws.recv())["last_sequence_id"] == -1
        ws.send(json.dumps({"type": "ping"}))
        assert json.loads(ws.recv())["type"] == "pong"
        ws.send(json.dumps(frame))
        while json.loads(ws.recv())["type"] != "ack":
            pass
    time.sleep(0.5)
    with connect(url, ssl=trust, additional_headers=a, proxy=None) as ws:
        assert json.loads(ws.recv())["last_sequence_id"] == 0
        ws.send(json.dumps(frame))
        try:
            ws.recv()
        except ConnectionClosed as exc:
            assert exc.rcvd.code == 1008
        else:
            raise AssertionError("Duplicate accepted")
    time.sleep(0.5)
    with connect(url, ssl=trust, additional_headers=a, proxy=None) as ws:
        assert json.loads(ws.recv())["last_sequence_id"] == 0
        ws.send(json.dumps(frame | dict(sequence_id=3, timestamp_ms=300)))
        gap = False
        while True:
            event = json.loads(ws.recv())
            if event["type"] == "analysis_gap":
                gap = True
            if event["type"] == "ack":
                break
        assert gap
    record("trusted_wss_auth_ping_ack_reconnect_duplicate_sequence_gap")
    time.sleep(0.5)
    with connect(url, ssl=trust, additional_headers=a, proxy=None) as ws:
        assert json.loads(ws.recv())["last_sequence_id"] == 3
        ws.send("x" * 262145)
        try:
            ws.recv()
        except ConnectionClosed as exc:
            assert exc.rcvd.code == 1009
        else:
            raise AssertionError("Oversized WSS message accepted")
    record("deployed_wss_message_size_bound")


def verify_privacy(sid, tenants, call):
    source = (ROOT / "scripts/verify_postgres_privacy.py").read_text(encoding="utf-8")
    remote(source + "\nverify(x)\n", dict(sid=sid, tenants=tenants, call=call))
    record("postgres_retention_default_off_opt_in_encryption_expiry_and_completed_context_purge")


if __name__ == "__main__":
    os.chdir(ROOT)
    try:
        run()
    except Exception as exc:
        REPORT["result"] = "FAILED"
        REPORT["failure_type"] = type(exc).__name__
        REPORT["failure_locations"] = [
            {"file": Path(f.filename).name, "line": f.lineno}
            for f in traceback.extract_tb(exc.__traceback__)
        ]
        print(REPORT["failure_locations"], flush=True)
        (ROOT / "docs/DEPLOYMENT_VERIFICATION.json").write_text(
            json.dumps(REPORT, indent=2) + "\n", encoding="utf-8"
        )
        # Deliberately omit exception text: it may carry request/DB input.
        print(
            "FAILED:",
            type(exc).__name__,
            "after",
            list(REPORT["checks"])[-1:],
            flush=True,
        )
        raise SystemExit(1)
    REPORT["result"] = "PASSED"
    (ROOT / "docs/DEPLOYMENT_VERIFICATION.json").write_text(
        json.dumps(REPORT, indent=2) + "\n", encoding="utf-8"
    )
