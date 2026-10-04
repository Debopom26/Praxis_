"""Authenticated client for the persistent host-side supplied-model worker."""

import base64
import json
import threading
import urllib.error
import urllib.request

import numpy as np


class RemoteSuppliedEngine:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip("/")
        self.token = token
        self.analysis_lock = threading.Lock()
        self.config: dict = {"models": {"ecapa": {"archive_metadata_revisions": []}}}

    def _request(self, path: str, payload=None):
        body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
        request = urllib.request.Request(
            self.url + path,
            data=body,
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"},
            method="GET" if body is None else "POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                if response.status != 200:
                    raise RuntimeError("SUPPLIED_WORKER_UNAVAILABLE")
                return json.loads(response.read(16 * 1024 * 1024))
        except (OSError, ValueError, urllib.error.HTTPError) as exc:
            raise RuntimeError("SUPPLIED_WORKER_UNAVAILABLE") from exc

    def health(self):
        try:
            return self._request("/health")
        except RuntimeError:
            return {"status": "ERROR", "reason": "SUPPLIED_WORKER_UNAVAILABLE"}

    def analyze(self, audio, host_context=None, trusted_embedding=None):
        samples = np.asarray(audio, dtype="<f4").reshape(-1)
        with self.analysis_lock:
            return self._request("/analysis", {
                "pcm_f32le_base64": base64.b64encode(samples.tobytes()).decode(),
                "host_context": host_context or {},
                "trusted_embedding": trusted_embedding,
            })

    def close(self):
        return None
