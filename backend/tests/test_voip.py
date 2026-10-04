"""Real WebSocket control/media path with authenticated, tenant-scoped users."""

import asyncio
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from praxis.db.repository import utcnow
from praxis.main import create_app
from praxis.security import Principal
from praxis.voip import Call, Peer, VoipHub
from starlette.websockets import WebSocketDisconnect


def headers(client, username, tenant="a"):
    result = client.post("/api/v1/auth/login", json={
        "username": username, "password": "test-password-only", "tenant_id": tenant,
    })
    assert result.status_code == 200
    return {"Authorization": "Bearer " + result.json()["access_token"]}


def test_voip_two_party_audio_and_hangup(repo, settings):
    with TestClient(create_app(settings, repo)) as client:
        a = headers(client, "admin-a")
        b = headers(client, "host-a")
        with client.websocket_connect("/api/v1/voip", headers=a) as caller:
            assert caller.receive_json() == {"type": "ready", "username": "admin-a"}
            with client.websocket_connect("/api/v1/voip", headers=b) as callee:
                assert callee.receive_json()["username"] == "host-a"
                caller.send_json({"type": "dial", "to": "host-a"})
                ring = callee.receive_json()
                assert ring["type"] == "ring" and ring["from"] == "admin-a"
                assert caller.receive_json() == {"type": "dialing", "call_id": ring["call_id"]}
                callee.send_json({"type": "accept", "call_id": ring["call_id"]})
                assert caller.receive_json()["type"] == "active"
                assert callee.receive_json()["type"] == "active"
                for auth in (a, b):
                    started = client.post("/api/v1/sessions", headers=auth, json={
                        "tenant_id": "a", "call_id": ring["call_id"] + "-" + str(uuid4()),
                        "host_app_id": "caller", "created_at": utcnow().isoformat(),
                    })
                    assert started.status_code == 201
                live = client.get("/api/v1/dashboard/sessions?active=true", headers=a).json()
                assert live["total"] == 2 and all(row["connected"] for row in live["sessions"])
                assert {row["remote_name"] for row in live["sessions"]} == {"admin-a", "host-a"}
                caller.send_bytes(bytes(640))
                assert callee.receive_bytes() == bytes(640)
                callee.send_bytes(bytes([1]) * 640)
                assert caller.receive_bytes() == bytes([1]) * 640
                caller.send_json({"type": "hangup"})
                assert caller.receive_json()["type"] == "ended"
                assert callee.receive_json()["type"] == "ended"
                assert client.get("/api/v1/dashboard/sessions?active=true", headers=a).json()["total"] == 0


def test_voip_rejects_cross_tenant_analyst_and_bad_media(repo, settings):
    with TestClient(create_app(settings, repo)) as client:
        a = headers(client, "admin-a")
        b = headers(client, "admin-b", "b")
        analyst = headers(client, "analyst-a")
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/api/v1/voip", headers=analyst):
                pass
        with client.websocket_connect("/api/v1/voip", headers=a) as caller:
            caller.receive_json()
            with client.websocket_connect("/api/v1/voip", headers=b) as other_tenant:
                other_tenant.receive_json()
                caller.send_json({"type": "dial", "to": "admin-b"})
                assert caller.receive_json()["type"] == "unavailable"
            caller.send_bytes(bytes(640))
            with pytest.raises(WebSocketDisconnect):
                caller.receive_json()


@pytest.mark.asyncio
async def test_voip_drops_brief_send_stall_but_ends_unresponsive_peer():
    class Socket:
        def __init__(self, failures=0):
            self.failures = failures
            self.frames = []

        async def send_bytes(self, value):
            if self.failures:
                self.failures -= 1
                raise asyncio.TimeoutError
            self.frames.append(value)

        async def send_json(self, value):
            self.frames.append(value)

    caller = Peer(Principal("a", "tenant", "host"), Socket())
    recipient_socket = Socket(failures=1)
    callee = Peer(Principal("b", "tenant", "host"), recipient_socket)
    hub = VoipHub()
    call = Call("test-call", caller, callee, active=True)
    caller.call_id = callee.call_id = call.id
    hub.calls[call.id] = call
    assert await hub.relay(caller, bytes(640))
    assert call.id in hub.calls and callee.send_timeouts == 1
    assert await hub.relay(caller, bytes(640))
    assert callee.send_timeouts == 0 and recipient_socket.frames == [bytes(640)]
    recipient_socket.failures = 3
    assert await hub.relay(caller, bytes(640))
    assert await hub.relay(caller, bytes(640))
    assert not await hub.relay(caller, bytes(640))
    assert call.id not in hub.calls
