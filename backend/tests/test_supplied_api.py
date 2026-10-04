"""API boundary tests with an explicit model double, not deployment evidence."""
import base64

import numpy as np
from fastapi.testclient import TestClient
from praxis.main import create_app
from sqlalchemy.exc import OperationalError
from test_backend import login, session_payload


class EngineDouble:
    calls = 0
    alive = True

    def health(self):
        return {"status": "AVAILABLE" if self.alive else "ERROR"}

    def analyze(self, *args):
        self.calls += 1
        return {"guidance": {"assessment": "NO_SCAM_INDICATORS_DETECTED"},
                "raw_audio_retained": False, "regressor_status": "BOOTSTRAP_UNTRAINED"}

    def close(self):
        pass


def payload(sid, audio=None):
    if audio is None:
        audio = np.zeros(16000, dtype="<f4")
    return {"session_id": sid, "pcm_f32le_base64": base64.b64encode(audio.tobytes()).decode()}


def test_supplied_auth_ownership_end_and_health(repo, settings):
    app = create_app(settings, repo)
    with TestClient(app) as client:
        engine = EngineDouble()
        app.state.runtime.supplied = engine
        admin = login(client)
        other = login(client, "admin-b", "b")
        analyst = login(client, "analyst-a")
        host = login(client, "host-a")
        sid = client.post("/api/v1/sessions", json=session_payload(), headers=admin).json()["session_id"]
        body = payload(sid)
        assert client.post("/api/v2/analysis", json=body).status_code == 401
        assert client.post("/api/v2/analysis", json=body, headers=analyst).status_code == 403
        for headers in (other, host):
            assert client.post("/api/v2/analysis", json=body, headers=headers).status_code == 404
        assert engine.calls == 0
        assert client.get("/api/v2/health").status_code == 401
        assert client.get("/api/v2/health", headers=admin).status_code == 200
        engine.alive = False
        assert client.get("/api/v2/health", headers=admin).status_code == 503
        engine.alive = True
        response = client.post("/api/v2/analysis", json=body, headers=admin)
        assert response.status_code == 200
        assert engine.calls == 1
        audit = client.get(f"/api/v1/audit/{sid}", headers=admin).json()
        assert len(audit) == 2
        assert "pcm_f32le_base64" not in str(audit)
        client.post(f"/api/v1/sessions/{sid}/end", headers=admin)
        assert client.post("/api/v2/analysis", json=body, headers=admin).status_code == 409
        assert engine.calls == 1


def test_supplied_invalid_input_and_audit_failure(repo, settings, monkeypatch):
    app = create_app(settings, repo)
    with TestClient(app) as client:
        admin = login(client)
        sid = client.post("/api/v1/sessions", json=session_payload(), headers=admin).json()["session_id"]
        assert client.post("/api/v2/analysis", json=payload(sid), headers=admin).status_code == 503
        engine = EngineDouble()
        app.state.runtime.supplied = engine
        bad = payload(sid)
        bad["pcm_f32le_base64"] = "!invalid!"
        assert client.post("/api/v2/analysis", json=bad, headers=admin).status_code == 422
        for audio in (np.zeros(2, dtype="<f4"), np.full(16000, np.nan, dtype="<f4")):
            assert client.post("/api/v2/analysis", json=payload(sid, audio), headers=admin).status_code == 422
        assert engine.calls == 0
        def fail(*args, **kwargs):
            raise OperationalError("unit-test injected failure", {}, Exception())
        monkeypatch.setattr(repo, "_audit", fail)
        response = client.post("/api/v2/analysis", json=payload(sid), headers=admin)
        assert response.status_code == 503
        assert "guidance" not in response.json()
        assert len(client.get(f"/api/v1/audit/{sid}", headers=admin).json()) == 1


def test_dashboard_persists_only_allowlisted_analysis_metadata(repo, settings):
    class ResultDouble(EngineDouble):
        def analyze(self, *args):
            return {"experimental_score_0_100": 42.5,
                    "regressor_status": "BOOTSTRAP_UNTRAINED",
                    "guidance": {"assessment": "NO_SCAM_INDICATORS_DETECTED",
                                 "action": "NO_ALERT", "message": "No scam indicators detected."},
                    "transcript": "must not persist", "embedding": [123.0]}

    app = create_app(settings, repo)
    with TestClient(app) as client:
        app.state.runtime.supplied = ResultDouble()
        admin = login(client)
        sid = client.post("/api/v1/sessions", json=session_payload(), headers=admin).json()["session_id"]
        assert client.post("/api/v2/analysis", json=payload(sid), headers=admin).status_code == 200
        view = client.get(f"/api/v1/dashboard/sessions/{sid}", headers=admin).json()
        assert view["latest_analysis"]["experimental_score_0_100"] == 42.5
        assert view["latest_analysis"]["action"] == "NO_ALERT"
        assert "transcript" not in str(view) and "embedding" not in str(view)
        history_url = f"/api/v1/dashboard/sessions/{sid}/analysis"
        history = client.get(history_url, headers=admin).json()
        assert history["total"] == 1
        assert history["results"][0]["experimental_score_0_100"] == 42.5
        assert "transcript" not in str(history) and "embedding" not in str(history)
        assert client.post(f"/api/v1/sessions/{sid}/end", headers=admin).status_code == 200
        assert client.get(history_url, headers=admin).json()["total"] == 1
        other = login(client, "admin-b", "b")
        assert client.get(history_url, headers=other).status_code == 404
