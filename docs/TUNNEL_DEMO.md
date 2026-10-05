# Free local tunnel demo

Cloudflare hosts the dashboard; the PC runs the unchanged Praxis models and database.
No GPU cloud, paid plan, credit purchase, or automatic billing is enabled by this setup.

Keep Windows awake, Docker Desktop unpaused, and the connector/launcher running.
Run `scripts/start-tunnel.ps1` from the Praxis project. Its temporary HTTPS address
changes whenever the connector restarts. Quick Tunnels are a demo service, not a
guaranteed production endpoint.

Set Cloudflare Worker `praxisdashboard` runtime variable `PRAXIS_BACKEND_ORIGIN`
to that HTTPS origin, then use the same origin as the Android server address.
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
Cold startup remains unit-tested, not demonstrated by stopping the live backend.
The runtime origin is stored in Cloudflare settings, never hardcoded in source;
keep_vars preserves that setting on dashboard redeployment.
