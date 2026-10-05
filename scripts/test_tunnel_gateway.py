import asyncio
import importlib.util
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

spec = importlib.util.spec_from_file_location("tunnel_gateway", Path(__file__).with_name("tunnel_gateway.py"))
gateway = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)


def test_only_login_starts_and_never_forwards_credentials_while_starting(monkeypatch):
    starts = []
    monkeypatch.setattr(gateway.starter, "wake", lambda: starts.append(True))
    with TestClient(gateway.app) as client:
        gateway.app.state.client = httpx.AsyncClient(transport=httpx.MockTransport(
            lambda request: httpx.Response(503)))
        assert client.get("/api/v1/sessions").status_code == 503
        assert not starts
        result = client.post("/api/v1/auth/login", json={"password": "never-forward"})
        assert result.status_code == 503
        assert result.json()["code"] == "PRAXIS_STARTING"
        assert len(starts) == 1
        assert client.post("/api/v1/auth/refresh", json={"refresh_token": "never-forward"}).json()["code"] == "PRAXIS_STARTING"
        assert len(starts) == 2


def test_ready_backend_keeps_auth_failure_and_headers(monkeypatch):
    monkeypatch.setattr(gateway.starter, "wake", lambda: (_ for _ in ()).throw(AssertionError("unexpected wake")))
    seen = []

    def backend(request):
        if request.url.path.endswith("health"):
            return httpx.Response(200, json={"status": "AVAILABLE"})
        seen.append(request)
        return httpx.Response(401, json={"detail": "INVALID_CREDENTIALS"})

    with TestClient(gateway.app) as client:
        gateway.app.state.client = httpx.AsyncClient(transport=httpx.MockTransport(backend))
        result = client.post("/api/v1/auth/login", json={"username": "not-real"})
        assert result.status_code == 401
        assert seen[0].url.host == "localhost"
        assert result.headers["cache-control"] == "no-store"
        assert gateway.app.state.tls.check_hostname
        assert gateway.app.state.tls.verify_mode == 2


def test_start_single_flight_and_retry_cooldown():
    async def scenario():
        starter = gateway.Starter()
        calls = []

        async def run():
            calls.append(True)
            await asyncio.sleep(0.01)

        starter.run = run
        for _ in range(20):
            starter.wake()
        await starter.task
        assert len(calls) == 1
        starter.retry_at = gateway.time.monotonic() + 60
        starter.wake()
        assert len(calls) == 1

    asyncio.run(scenario())


def test_backend_up_worker_down_triggers_startup(monkeypatch):
    starts = []
    monkeypatch.setattr(gateway.starter, "wake", lambda: starts.append(True))
    with TestClient(gateway.app) as client:
        gateway.app.state.worker_token = "test-only-token"
        gateway.app.state.worker_required = True
        gateway.app.state.client = httpx.AsyncClient(transport=httpx.MockTransport(
            lambda request: httpx.Response(503) if request.url.port == 8765 else httpx.Response(200)))
        result = client.post("/api/v1/auth/login", json={"username": "not-real"})
        assert result.json()["code"] == "PRAXIS_STARTING"
        assert len(starts) == 1
