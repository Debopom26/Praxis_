import base64
from datetime import timedelta

import pytest
from cryptography.exceptions import InvalidTag
from fastapi.testclient import TestClient
from praxis.contracts import SessionStart
from praxis.db.models import SessionRecord
from praxis.db.repository import utcnow
from praxis.main import create_app
from praxis.security import AccessDenied, Encryption, Tokens, hash_password, verify_password
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from starlette.websockets import WebSocketDisconnect


def login(client, uid="admin-a", tenant="a"):
    response = client.post(
        "/api/v1/auth/login",
        json=dict(username=uid, password="test-password-only", tenant_id=tenant),
    )
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def session_payload(tenant="a", call="call"):
    return dict(tenant_id=tenant, call_id=call, host_app_id="host", created_at=utcnow().isoformat())


def test_auth_tenant_rbac_and_atomic_audit(repo, settings):
    with TestClient(create_app(settings, repo)) as client:
        a = login(client)
        b = login(client, "admin-b", "b")
        analyst = login(client, "analyst-a")
        assert client.post("/api/v1/sessions", json=session_payload()).status_code == 401
        assert (
            client.post("/api/v1/sessions", json=session_payload("b"), headers=a).status_code == 403
        )
        assert (
            client.post("/api/v1/sessions", json=session_payload(), headers=analyst).status_code
            == 403
        )
        response = client.post("/api/v1/sessions", json=session_payload(), headers=a)
        assert response.status_code == 201
        sid = response.json()["session_id"]
        assert client.get("/api/v1/sessions/" + sid, headers=b).status_code == 404
        assert (
            client.patch(
                f"/api/v1/sessions/{sid}/context", json={"known_contact": True}, headers=b
            ).status_code
            == 404
        )
        assert client.get("/api/v1/audit/" + sid, headers=b).status_code == 404
        assert len(client.get("/api/v1/audit/" + sid, headers=a).json()) == 1
        assert client.post(f"/api/v1/sessions/{sid}/end", headers=a).status_code == 200
        assert (
            client.patch(f"/api/v1/sessions/{sid}/context", json={}, headers=a).status_code == 409
        )


def test_dashboard_directory_tenant_owner_labels_and_live_presence(repo, settings):
    with TestClient(create_app(settings, repo)) as client:
        admin = login(client)
        host = login(client, "host-a")
        other = login(client, "admin-b", "b")
        sid = client.post("/api/v1/sessions", json=session_payload(), headers=host).json()["session_id"]
        assert client.get("/api/v1/dashboard/sessions", headers=other).json()["total"] == 0
        assert client.get(f"/api/v1/dashboard/sessions/{sid}", headers=other).status_code == 404
        assert client.put(f"/api/v1/sessions/{sid}/display", headers=other,
                          json={"remote_name": "Someone"}).status_code == 404
        assert client.put(f"/api/v1/sessions/{sid}/display", headers=host,
                          json={"remote_name": "Saved contact", "remote_number": "+123"}).status_code == 200
        rows = client.get("/api/v1/dashboard/sessions?q=Saved", headers=admin).json()
        assert rows["total"] == 1
        assert rows["sessions"][0]["remote_name"] == "Saved contact"
        assert rows["sessions"][0]["owner_username"] == "host-a"
        assert rows["sessions"][0]["connected"] is False
        assert client.get("/api/v1/dashboard/sessions?active=true", headers=admin).json()["total"] == 0
        with client.websocket_connect("/api/v1/stream/" + sid, headers=host) as ws:
            assert ws.receive_json()["type"] == "connection"
            live = client.get("/api/v1/dashboard/sessions?active=true", headers=admin).json()
            assert live["total"] == 1 and live["sessions"][0]["connected"] is True
        assert client.get("/api/v1/dashboard/sessions?active=true", headers=admin).json()["total"] == 0


def test_audit_failure_rolls_back(repo, monkeypatch):
    p = repo.principal("admin-a", "a")

    def fail(*args):
        raise OperationalError("audit unavailable", {}, Exception())

    monkeypatch.setattr(repo, "_audit", fail)
    with pytest.raises(OperationalError):
        repo.start(p, SessionStart.model_validate(session_payload()))
    with repo.sessions() as db:
        assert db.scalar(select(SessionRecord)) is None


def test_wss_and_duplicate_sequence(repo, settings):
    with TestClient(create_app(settings, repo)) as client:
        a = login(client)
        sid = client.post("/api/v1/sessions", json=session_payload(), headers=a).json()[
            "session_id"
        ]
        frame = dict(
            sequence_id=0,
            timestamp_ms=0,
            format=dict(sample_rate=16000, channels=1),
            audio_base64=base64.b64encode(bytes(320)).decode(),
        )
        with client.websocket_connect("/api/v1/stream/" + sid, headers=a) as ws:
            assert ws.receive_json()["type"] == "connection"
            ws.send_json(frame)
            assert ws.receive_json()["status"] == "UNAVAILABLE"
            assert ws.receive_json()["type"] == "ack"
            ws.send_json(frame)
            with pytest.raises(WebSocketDisconnect):
                ws.receive_json()
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/api/v1/stream/" + sid):
                pass


def test_token_wrong_key_and_expiry(settings):
    import jwt

    tokens = Tokens(settings)
    token = tokens.issue("u", "t")
    assert tokens.decode(token) == ("u", "t")
    with pytest.raises(AccessDenied):
        tokens.decode(token + "bad")
    claims = jwt.decode(token, options={"verify_signature": False})
    claims["exp"] = int((utcnow() - timedelta(seconds=1)).timestamp())
    expired = jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    with pytest.raises(AccessDenied):
        tokens.decode(expired)


def test_encryption_authenticates_tenant_and_version(settings):
    cipher = Encryption(settings.embedding_key_base64.get_secret_value())
    data = cipher.encrypt(b"biometric-test", "a", "id", "v1")
    assert cipher.decrypt(data, "a", "id", "v1") == b"biometric-test"
    assert b"biometric-test" not in data
    for tenant, identity, version in [("b", "id", "v1"), ("a", "other", "v1"), ("a", "id", "v2")]:
        with pytest.raises(InvalidTag):
            cipher.decrypt(data, tenant, identity, version)


def test_password_and_no_validation_leak(repo, settings):
    hashed = hash_password("long-test-password")
    assert hashed.startswith("$argon2id$") and verify_password(hashed, "long-test-password")
    assert not verify_password(hashed, "wrong")
    with TestClient(create_app(settings, repo)) as client:
        result = client.post("/api/v1/auth/login", json={"password": "SENSITIVE"})
        assert "SENSITIVE" not in result.text
        assert client.get("/api/v1/health").json()["artifacts"][2]["state"] == "UNVALIDATED"


def test_body_limit_and_versioned_config_tenant_boundary(repo, settings):
    with TestClient(create_app(settings, repo)) as client:
        assert client.post("/api/v1/auth/login", content="x" * 65537).status_code == 413
        a, b = login(client), login(client, "admin-b", "b")
        sid = client.post("/api/v1/sessions", json=session_payload(), headers=a).json()[
            "session_id"
        ]
        route = f"/api/v1/config/policy?session_id={sid}"
        config = {"tenant_id": "a", "policy_version": "test-v1"}
        assert client.put(route, json=config, headers=b).status_code == 403
        assert client.put(route, json=config, headers=a).status_code == 200
        assert client.put(route, json=config, headers=a).status_code == 409


def test_stream_does_not_deliver_when_audit_fails(repo, settings, monkeypatch):
    with TestClient(create_app(settings, repo)) as client:
        a = login(client)
        sid = client.post("/api/v1/sessions", json=session_payload(), headers=a).json()[
            "session_id"
        ]

        def fail(*args):
            raise OperationalError("test only", {}, Exception())

        monkeypatch.setattr(repo, "record_event", fail)
        with client.websocket_connect("/api/v1/stream/" + sid, headers=a) as ws:
            assert ws.receive_json()["type"] == "connection"
            ws.send_json({"type": "ping"})
            assert ws.receive_json()["type"] == "pong"
            ws.send_json(
                dict(
                    sequence_id=0,
                    timestamp_ms=0,
                    format=dict(sample_rate=16000, channels=1),
                    audio_base64=base64.b64encode(bytes(320)).decode(),
                )
            )
            with pytest.raises(WebSocketDisconnect) as exc:
                ws.receive_json()
            assert exc.value.code == 1013
