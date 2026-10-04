"""Disposable real PostgreSQL/Caddy/WSS/V2 voice-path smoke; never prints credentials."""

import argparse
import asyncio
import base64
import json
import os
import secrets
import ssl
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
import numpy as np
import websockets

ROOT = Path(__file__).resolve().parents[1]
DOCKER = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/DockerDesktop/resources/bin/docker.exe"
CA = ROOT / "integrations/android/Praxis-Local-CA.crt"
ORIGIN = "https://localhost"

CREATE = """
import json,os,secrets
from uuid import uuid4
from praxis.config import Settings
from praxis.db.models import Organization,User,Membership
from praxis.db.repository import Repository
from praxis.security import hash_password
t=os.environ['PRAXIS_TEST_TENANT']; password=secrets.token_urlsafe(24)
names=[t+'-a',t+'-b']; ids=[str(uuid4()),str(uuid4())]
r=Repository.from_url(Settings().database_url.get_secret_value())
with r.sessions.begin() as d:
 d.add(Organization(id=t,name='Disposable VoIP verification'))
 for uid,name in zip(ids,names):
  d.add(User(id=uid,username=name,password_hash=hash_password(password),active=True)); d.flush()
  d.add(Membership(tenant_id=t,user_id=uid,role='host'))
r.engine.dispose()
print(json.dumps({'names':names,'password':password}))
"""

CLEAN = """
import os
from sqlalchemy import delete,select
from praxis.config import Settings
from praxis.db.models import (AuditRecord,EvidenceRecord,RiskRecord,RetainedPayload,
 SessionRecord,SpeakerProfile,Configuration,Membership,User,Organization)
from praxis.db.repository import Repository
t=os.environ['PRAXIS_TEST_TENANT']; r=Repository.from_url(Settings().database_url.get_secret_value())
with r.sessions.begin() as d:
 ids=list(d.scalars(select(User.id).join(Membership,Membership.user_id==User.id).where(Membership.tenant_id==t)))
 for table in (AuditRecord,EvidenceRecord,RiskRecord,RetainedPayload,SessionRecord,
               SpeakerProfile,Configuration,Membership):
  d.execute(delete(table).where(table.tenant_id==t))
 for uid in ids: d.execute(delete(User).where(User.id==uid))
 d.execute(delete(Organization).where(Organization.id==t))
r.engine.dispose()
"""


def docker_python(code: str, tenant: str) -> str:
    result = subprocess.run([str(DOCKER), "exec", "-e", f"PRAXIS_TEST_TENANT={tenant}",
                             "praxis-backend-1", "python", "-c", code],
                            capture_output=True, text=True, timeout=45, check=True)
    return result.stdout.strip()


async def relay_test(tokens: list[str], frame_data: bytes, duration_seconds: int = 4) -> tuple[bytes, bytes]:
    context = ssl.create_default_context(cafile=str(CA))
    async with websockets.connect("wss://localhost/api/v1/voip", ssl=context,
                                  additional_headers={"Authorization": "Bearer " + tokens[0]}) as caller:
        assert json.loads(await caller.recv())["type"] == "ready"
        async with websockets.connect("wss://localhost/api/v1/voip", ssl=context,
                                      additional_headers={"Authorization": "Bearer " + tokens[1]}) as callee:
            ready = json.loads(await callee.recv())
            await caller.send(json.dumps({"type": "dial", "to": ready["username"]}))
            ring = json.loads(await callee.recv())
            assert ring["type"] == "ring"
            assert json.loads(await caller.recv())["type"] == "dialing"
            await callee.send(json.dumps({"type": "accept", "call_id": ring["call_id"]}))
            assert json.loads(await caller.recv())["type"] == "active"
            assert json.loads(await callee.recv())["type"] == "active"

            async def receive_audio(socket) -> bytes:
                chunks = []
                for index in range(duration_seconds * 50):
                    frame = await asyncio.wait_for(socket.recv(), timeout=3)
                    assert isinstance(frame, bytes) and len(frame) == 640
                    if index < 200:
                        chunks.append(frame)
                return b"".join(chunks)

            async def send_audio(socket) -> None:
                for index in range(duration_seconds * 50):
                    offset = (index % 200) * 640
                    await socket.send(frame_data[offset:offset + 640])
                    await asyncio.sleep(0.02)

            heard_a, heard_b, _, _ = await asyncio.gather(
                receive_audio(caller), receive_audio(callee),
                send_audio(caller), send_audio(callee))
            assert heard_a == frame_data and heard_b == frame_data
            await caller.send('{"type":"hangup"}')
            assert json.loads(await caller.recv())["type"] == "ended"
            assert json.loads(await callee.recv())["type"] == "ended"
            return heard_a, heard_b


def main(audio_path: Path, start_seconds: float = 0.0, duration_seconds: int = 4) -> None:
    tenant = "voip-check-" + uuid4().hex[:12]
    created = False
    try:
        details = json.loads(docker_python(CREATE, tenant))
        created = True
        extra_name = tenant + "-created-by-operator-command"
        account = subprocess.run([str(DOCKER), "exec", "-i", "praxis-backend-1", "python",
                                  "/app/scripts/create_host.py"],
                                 input=f"{tenant}\n{extra_name}\n{details['password']}\n",
                                 capture_output=True, text=True, check=True, timeout=45)
        assert "account created" in account.stdout
        with httpx.Client(verify=str(CA), timeout=20) as http:
            health = http.get(ORIGIN + "/api/v1/health")
            health.raise_for_status()
            tokens = []
            for name in details["names"]:
                response = http.post(ORIGIN + "/api/v1/auth/login", json={
                    "tenant_id": tenant, "username": name, "password": details["password"]})
                response.raise_for_status()
                tokens.append(response.json()["access_token"])
            extra = http.post(ORIGIN + "/api/v1/auth/login", json={
                "tenant_id": tenant, "username": extra_name, "password": details["password"]})
            extra.raise_for_status()
            replacement = secrets.token_urlsafe(24)
            reset = subprocess.run([str(DOCKER), "exec", "-i", "praxis-backend-1", "python",
                                    "/app/scripts/reset_account_password.py"],
                                   input=f"{tenant}\n{extra_name}\n{replacement}\n{replacement}\n",
                                   capture_output=True, text=True, check=True, timeout=45)
            assert "Password reset completed" in reset.stdout
            changed = http.post(ORIGIN + "/api/v1/auth/login", json={
                "tenant_id": tenant, "username": extra_name, "password": replacement})
            changed.raise_for_status()
            session_ids = []
            for token in tokens:
                session = http.post(ORIGIN + "/api/v1/sessions", headers={"Authorization": "Bearer " + token},
                                    json={"tenant_id": tenant, "call_id": str(uuid4()), "host_app_id": "praxis-caller",
                                          "created_at": datetime.now(timezone.utc).isoformat()})
                session.raise_for_status()
                session_ids.append(session.json()["session_id"])
        pcm = subprocess.run([str(DOCKER), "run", "--rm", "--network", "none", "--read-only",
                              "--mount", f"type=bind,source={audio_path.resolve()},target=/input.m4a,readonly",
                              "--entrypoint", "ffmpeg", "praxis-backend:latest", "-loglevel", "error",
                              "-ss", str(start_seconds), "-i", "/input.m4a", "-ac", "1", "-ar", "16000", "-f", "s16le", "pipe:1"],
                             capture_output=True, check=True, timeout=45).stdout[:128000]
        assert len(pcm) == 128000 and any(pcm), "No usable four-second audio input"
        heard = asyncio.run(relay_test(tokens, pcm, duration_seconds))
        def analyze_one(inputs):
            token, session_id, audio = inputs
            with httpx.Client(verify=str(CA), timeout=120) as http:
                floating = (np.frombuffer(audio, dtype="<i2").astype("<f4") / 32768.0).tobytes()
                result = http.post(ORIGIN + "/api/v2/analysis", headers={"Authorization": "Bearer " + token},
                                   json={"session_id": session_id, "sample_rate": 16000, "channels": 1,
                                         "pcm_f32le_base64": base64.b64encode(floating).decode()})
                result.raise_for_status()
                outcome = result.json()
                assert outcome["status"] == "AVAILABLE"
                assert 0 <= outcome["experimental_score_0_100"] <= 100
                return outcome
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(analyze_one, zip(tokens, session_ids, heard)))
        with httpx.Client(verify=str(CA), timeout=20) as http:
            for token, session_id, outcome in zip(tokens, session_ids, outcomes):
                history = http.get(
                    ORIGIN + f"/api/v1/dashboard/sessions/{session_id}/analysis",
                    headers={"Authorization": "Bearer " + token},
                )
                history.raise_for_status()
                saved = history.json()
                assert saved["total"] == 1
                assert abs(saved["results"][0]["experimental_score_0_100"]
                           - outcome["experimental_score_0_100"]) < 1e-6
        for outcome in outcomes:
            print("V2 action:", outcome["guidance"]["action"], "score:", round(outcome["experimental_score_0_100"], 2))
        print(f"PASS: trusted HTTPS, PostgreSQL/operator account creation and reset, tenant WSS call, {duration_seconds * 50} frames in each direction, concurrent V2 analysis for both users")
    finally:
        if created:
            docker_python(CLEAN, tenant)
            print("Disposable organization, users, session and audit removed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", type=Path)
    parser.add_argument("--start-seconds", type=float, default=0.0)
    parser.add_argument("--duration-seconds", type=int, choices=range(4, 121), default=4)
    args = parser.parse_args()
    main(args.audio, args.start_seconds, args.duration_seconds)
