"""Opt-in live tunnel smoke; disposable tenant, no audio or credential output."""
import argparse
import json
import secrets
import time
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from verify_deployment import cleanup, remote
from websockets.sync.client import connect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("origin")
    parser.add_argument("--dashboard")
    parser.add_argument("--username")
    parser.add_argument("--voip", action="store_true")
    args = parser.parse_args()
    tenant = "p10-verify-tunnel-" + uuid4().hex[:12]
    username = args.username or "trial-" + uuid4().hex[:8]
    password = secrets.token_urlsafe(24)
    try:
        with httpx.Client(base_url=args.origin, trust_env=False, timeout=30) as client:
            signup = {
                "tenant_id": tenant, "organization_name": "Disposable tunnel verification",
                "username": username, "password": password}
            registered = client.post("/api/v1/auth/register", json=signup)
            if registered.status_code == 503 and registered.json().get("code") == "PRAXIS_STARTING":
                print("Waiting for existing login-triggered model startup...", flush=True)
                deadline = time.monotonic() + 600
                while time.monotonic() < deadline:
                    time.sleep(5)
                    registered = client.post("/api/v1/auth/register", json=signup)
                    if registered.status_code != 503:
                        break
            assert registered.status_code == 201, f"Signup HTTP {registered.status_code}"
            remote("""
from sqlalchemy import select
from praxis.config import Settings
from praxis.db.models import Membership, Organization, User
from praxis.db.repository import Repository
r=Repository.from_url(Settings().database_url.get_secret_value())
with r.sessions() as db:
    assert db.get(Organization,x['tenant']) is not None
    user=db.scalar(select(User).join(Membership,Membership.user_id==User.id).where(
        Membership.tenant_id==x['tenant'],User.username==x['username']))
    assert user is not None
""", {"tenant": tenant, "username": username})
            print("PASS: new account exists in real PostgreSQL")
            assert client.get("/api/v1/health").status_code == 200
            login = client.post("/api/v1/auth/login", json={
                "tenant_id": tenant, "username": username, "password": password})
            assert login.status_code == 200
            headers = {"Authorization": "Bearer " + login.json()["access_token"]}
            created = client.post("/api/v1/sessions", headers=headers, json={
                "tenant_id": tenant, "call_id": "tunnel-smoke", "host_app_id": "tunnel-verification",
                "created_at": datetime.now(timezone.utc).isoformat()})
            assert created.status_code == 201
            sid = created.json()["session_id"]
            with connect(args.origin.replace("https://", "wss://") + "/api/v1/stream/" + sid,
                         additional_headers=headers, proxy=None) as socket:
                socket.send(json.dumps({"type": "ping"}))
                for _ in range(5):
                    if json.loads(socket.recv(timeout=10)) == {"type": "pong"}:
                        break
                else:
                    raise AssertionError("No WSS pong received")
            assert client.post("/api/v1/sessions/" + sid + "/end", headers=headers).status_code == 200
            if args.dashboard:
                result = client.post(args.dashboard + "/api/v1/auth/login", json={
                    "tenant_id": tenant, "username": username, "password": password})
                assert result.status_code == 200
            if args.voip:
                peer_name = username + "-peer"
                assert client.post("/api/v1/admin/hosts", headers=headers, json={
                    "username": peer_name, "password": password}).status_code == 201
                peer_login = client.post("/api/v1/auth/login", json={
                    "tenant_id": tenant, "username": peer_name, "password": password})
                assert peer_login.status_code == 200
                peer_headers = {"Authorization": "Bearer " + peer_login.json()["access_token"]}
                ws_url = args.origin.replace("https://", "wss://") + "/api/v1/voip"
                with connect(ws_url, additional_headers=headers, proxy=None) as caller:
                    assert json.loads(caller.recv(timeout=10))["type"] == "ready"
                    with connect(ws_url, additional_headers=peer_headers, proxy=None) as callee:
                        assert json.loads(callee.recv(timeout=10))["type"] == "ready"
                        caller.send(json.dumps({"type": "dial", "to": peer_name}))
                        ring = json.loads(callee.recv(timeout=10))
                        assert ring["type"] == "ring"
                        assert json.loads(caller.recv(timeout=10))["type"] == "dialing"
                        callee.send(json.dumps({"type": "accept", "call_id": ring["call_id"]}))
                        assert json.loads(caller.recv(timeout=10))["type"] == "active"
                        assert json.loads(callee.recv(timeout=10))["type"] == "active"
                        for _ in range(10):
                            caller.send(bytes(640))
                            assert callee.recv(timeout=10) == bytes(640)
                            callee.send(bytes([1]) * 640)
                            assert caller.recv(timeout=10) == bytes([1]) * 640
                        caller.send(json.dumps({"type": "hangup"}))
                        assert json.loads(caller.recv(timeout=10))["type"] == "ended"
                        assert json.loads(callee.recv(timeout=10))["type"] == "ended"
                print("PASS: two-party VoIP signaling and exact bidirectional synthetic PCM relay")
        print("PASS: public HTTPS signup/login/session, authenticated WSS ping/pong, dashboard login proxy")
    finally:
        cleanup([tenant])
        print("Disposable verification records removed")


if __name__ == "__main__":
    main()
