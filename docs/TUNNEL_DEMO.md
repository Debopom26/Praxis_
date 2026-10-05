# Free local tunnel demo

Cloudflare hosts the dashboard; the PC runs the unchanged Praxis models and database.
No GPU cloud, paid plan, credit purchase, or automatic billing is enabled by this setup.

Keep Windows awake, Docker Desktop unpaused, and the connector/launcher running.
Run `scripts/start-tunnel.ps1` from the Praxis project. Its temporary HTTPS address
changes whenever the connector restarts. Quick Tunnels are a demo service, not a
guaranteed production endpoint.

Set Cloudflare Worker `praxisdashboard` runtime variable `PRAXIS_BACKEND_ORIGIN`
to that HTTPS origin. In Android, use the fixed dashboard address instead:
`https://praxisdashboard.debopomrc2602.workers.dev/`.
After each tunnel restart, update only PRAXIS_BACKEND_ORIGIN in Cloudflare;
the phone server address stays unchanged. This update is manual, not automatic.
Do not put a password, tunnel token, or local IP into the repository.

The loopback gateway starts the existing `scripts/start.ps1` only when a POST to
the login or registration endpoint arrives while the backend is unavailable.
It returns `PRAXIS_STARTING` without forwarding credentials during startup.
The dashboard retries for up to ten minutes and shows “Starting Praxis…”.
Concurrent attempts share one startup, with a one-minute retry cooldown.
The backend stays running after login; no automatic shutdown is implemented.

HTTP and WebSocket forwarding to local Caddy verify TLS against the existing
Praxis CA and localhost hostname. Existing backend authentication/RBAC remain
mandatory. No raw audio or login bodies are saved by the gateway. Startup logs
are local under ignored runtime/. The gateway binds only to 127.0.0.1:8787.

Status: four gateway tests, Ruff and dashboard build passed. Docker is now
unpaused (29.8.0); backend/database healthy. The running loopback gateway reaches
the real backend over verified TLS and preserves invalid-login HTTP 401.
With explicit user approval, the free temporary tunnel is running. Real public
HTTPS login/session creation, authenticated WSS ping/pong, and hosted dashboard
login proxy passed; disposable verification records were removed. No phone-call
test or model-scoring run is claimed by this transport smoke.
Real login-triggered backend restart passed after confirming no recent call
activity. The persistent model worker's process and existing .env hash were
unchanged. The backend image was updated from existing tested source to include
the previously undeployed signup endpoint; backend regression suite: 93 passed.
The runtime origin is stored in Cloudflare settings, never hardcoded in source;
keep_vars preserves that setting on dashboard redeployment.

## 2026-10-05 expired tunnel recovery and stable Android origin
The historical wishing-strength-ethical-extreme Quick Tunnel expired. Dashboard 530 was caused by its stale backend origin. Production PRAXIS_BACKEND_ORIGIN now points to https://turns-sequences-est-eddie.trycloudflare.com; the active connector remains running. Future start-tunnel.ps1 launches force HTTP/2 over IPv4 after observed QUIC connection failures, without disabling TLS. Dashboard handles 530 with a tunnel recovery message. Commit 953b5f5 preserves the upstream 101 Response and WebSocket metadata in the Workers proxy; deployed successfully (288f1d49).
Verified through https://praxisdashboard.debopomrc2602.workers.dev: fresh signup persisted in real PostgreSQL, login, session lifecycle, authenticated analysis WSS ping/pong, and two-party VoIP signaling plus exact bidirectional synthetic PCM relay. Disposable records removed. Login-triggered existing model startup initially returned PRAXIS_STARTING; verification waited until readiness and then passed. No physical phone/model-score test claimed. Gateway tests 4 passed; Ruff passed; dashboard build passed. No model, secrets, TLS bypass, or APK changes.
Android can now use the fixed dashboard origin above; tunnel restart requires changing only Cloudflare runtime PRAXIS_BACKEND_ORIGIN. No automatic origin synchronization implemented. Keep PC awake, Docker unpaused, gateway and connector running. Older checkpoint URLs/instructions remain historical and are superseded here. No paid services used.