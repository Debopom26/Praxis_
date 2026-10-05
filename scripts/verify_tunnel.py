"""Opt-in live tunnel smoke; disposable tenant, no audio or credential output."""
import argparse
import json
import secrets
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from verify_deployment import admin, cleanup
from websockets.sync.client import connect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("origin")
    parser.add_argument("--dashboard")
    args = parser.parse_args()
    tenant = "p10-verify-tunnel-" + uuid4().hex[:12]
    username = "tunnel-smoke"
    password = secrets.token_urlsafe(24)
    try:
        admin(tenant, username, password)
        with httpx.Client(base_url=args.origin, trust_env=False, timeout=30) as client:
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
        print("PASS: public HTTPS login/session, authenticated WSS ping/pong, dashboard login proxy")
    finally:
        cleanup([tenant])
        print("Disposable verification records removed")


if __name__ == "__main__":
    main()
