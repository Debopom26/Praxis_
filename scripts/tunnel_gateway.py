"""Loopback-only demo gateway: wake existing Praxis on login; never store audio."""
import asyncio
import contextlib
import ssl
import subprocess
import time
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import uvicorn
import websockets
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 32 * 1024 * 1024
WAKE_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register"}
HOP_HEADERS = {"host", "connection", "upgrade", "transfer-encoding", "content-length",
               "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer"}


class Starter:
    def __init__(self):
        self.task = None
        self.retry_at = 0.0

    async def run(self):
        # Fixed command only. No request data, credentials, or shell text is passed.
        try:
            with (ROOT / "runtime" / "tunnel-startup.log").open("ab") as log:
                await asyncio.to_thread(
                    subprocess.run,
                    ["powershell.exe", "-NoProfile", "-NonInteractive", "-File",
                     str(ROOT / "scripts" / "start.ps1")], cwd=str(ROOT),
                    stdout=log, stderr=log, creationflags=0x08000000, timeout=600,
                    check=False,
                )
        except (OSError, subprocess.TimeoutExpired):
            pass
        finally:
            self.retry_at = time.monotonic() + 60

    def wake(self):
        if (self.task is None or self.task.done()) and time.monotonic() >= self.retry_at:
            self.task = asyncio.create_task(self.run())


starter = Starter()


@asynccontextmanager
async def lifespan(app):
    (ROOT / "runtime").mkdir(exist_ok=True)
    # Trust the existing local CA and verify localhost; never disable TLS checks.
    app.state.tls = ssl.create_default_context()
    app.state.tls.load_verify_locations(str(ROOT / "integrations/android/Praxis-Local-CA.crt"))
    values = dict(line.split("=", 1) for line in (ROOT / ".env").read_text().splitlines()
                  if "=" in line and not line.startswith("#"))
    app.state.worker_required = values.get("PRAXIS_SUPPLIED_MODELS_ENABLED") == "true"
    app.state.worker_token = values.get("PRAXIS_SUPPLIED_WORKER_TOKEN", "")
    async with httpx.AsyncClient(verify=app.state.tls, trust_env=False,
                                 timeout=150, follow_redirects=False) as client:
        app.state.client = client
        yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


async def available():
    try:
        response = await app.state.client.get("https://localhost/api/v1/health", timeout=3)
        if response.status_code != 200:
            return False
        if app.state.worker_required:
            if not app.state.worker_token:
                return False
            worker = await app.state.client.get("http://127.0.0.1:8765/health", timeout=3,
                headers={"Authorization": "Bearer " + app.state.worker_token})
            return worker.status_code == 200 and worker.json().get("status") == "AVAILABLE"
        return True
    except (httpx.HTTPError, ValueError):
        return False


@app.api_route("/api/{path:path}", methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy(request: Request, path: str):
    if request.method == "POST" and request.url.path in WAKE_PATHS and not await available():
        starter.wake()
        return JSONResponse({"code": "PRAXIS_STARTING", "message": "Praxis is starting. Please wait."},
                            status_code=503, headers={"Retry-After": "5", "Cache-Control": "no-store"})
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > LIMIT:
            return Response(status_code=413)
    headers = {key: value for key, value in request.headers.items() if key.lower() not in HOP_HEADERS}
    try:
        response = await app.state.client.request(request.method, "https://localhost/api/" + path,
                                                 params=request.query_params, headers=headers, content=bytes(body))
    except httpx.HTTPError:
        return JSONResponse({"code": "BACKEND_UNAVAILABLE", "message": "Praxis backend is unavailable."},
                            status_code=503, headers={"Cache-Control": "no-store"})
    outgoing = {key: value for key, value in response.headers.items()
                if key.lower() not in HOP_HEADERS | {"content-encoding"}}
    outgoing["cache-control"] = "no-store"
    return Response(response.content, status_code=response.status_code, headers=outgoing)


@app.websocket("/api/{path:path}")
async def socket(websocket: WebSocket, path: str):
    query = websocket.scope.get("query_string", b"").decode("ascii")
    url = "wss://localhost/api/" + path + ("?" + query if query else "")
    headers = {key: value for key, value in websocket.headers.items()
               if key.lower() not in HOP_HEADERS and not key.lower().startswith("sec-websocket-")}
    try:
        async with websockets.connect(url, ssl=app.state.tls, proxy=None,
                                      additional_headers=headers, max_size=LIMIT,
                                      ping_interval=60, ping_timeout=60) as upstream:
            await websocket.accept()

            async def inbound():
                while True:
                    message = await websocket.receive()
                    if message["type"] == "websocket.disconnect":
                        return
                    await upstream.send(message.get("bytes") if message.get("bytes") is not None else message["text"])

            async def outbound():
                async for message in upstream:
                    if isinstance(message, bytes):
                        await websocket.send_bytes(message)
                    else:
                        await websocket.send_text(message)

            tasks = [asyncio.create_task(inbound()), asyncio.create_task(outbound())]
            try:
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
    except (OSError, websockets.exceptions.WebSocketException, RuntimeError):
        pass
    finally:
        with contextlib.suppress(RuntimeError, WebSocketDisconnect):
            await websocket.close()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8787, access_log=False, log_level="warning")
