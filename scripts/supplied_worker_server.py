"""Private persistent supplied-model worker used by the Docker backend."""

import argparse
import base64
import hmac
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

from praxis.supplied.engine import SuppliedEngine


def serve(model_paths: Path, token: str, port: int):
    engine = SuppliedEngine(model_paths)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            return

        def authorized(self):
            expected = "Bearer " + token
            return hmac.compare_digest(self.headers.get("Authorization", ""), expected)

        def send_value(self, status, value):
            body = json.dumps(value, separators=(",", ":")).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if not self.authorized():
                return self.send_value(401, {"detail": "AUTHENTICATION_REQUIRED"})
            if self.path != "/health":
                return self.send_value(404, {"detail": "NOT_FOUND"})
            self.send_value(200, engine.health())

        def do_POST(self):
            if not self.authorized():
                return self.send_value(401, {"detail": "AUTHENTICATION_REQUIRED"})
            if self.path != "/analysis":
                return self.send_value(404, {"detail": "NOT_FOUND"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 1 <= length <= 16 * 1024 * 1024:
                    raise ValueError("Invalid request size")
                value = json.loads(self.rfile.read(length))
                raw = base64.b64decode(value["pcm_f32le_base64"], validate=True)
                if len(raw) % 4 or not 64000 <= len(raw) <= 7680000:
                    raise ValueError("Invalid audio")
                audio = np.frombuffer(raw, dtype="<f4").copy()
                result = engine.analyze(audio, value.get("host_context"), value.get("trusted_embedding"))
                self.send_value(200, result)
            except RuntimeError as exc:
                self.send_value(429 if str(exc) == "ANALYSIS_BUSY" else 503,
                                {"detail": "ANALYSIS_BUSY" if str(exc) == "ANALYSIS_BUSY" else "ANALYSIS_UNAVAILABLE"})
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                self.send_value(422, {"detail": "INVALID_REQUEST"})

    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        engine.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-paths", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    values = {}
    for line in args.env_file.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    token = values.get("PRAXIS_SUPPLIED_WORKER_TOKEN", "")
    if len(token) < 32:
        raise ValueError("Missing supplied worker token")
    serve(args.model_paths, token, args.port)
