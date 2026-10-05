# Start the local Praxis server online

Double-click **Start-Praxis-Online.bat** in the project root. It opens Docker Desktop if needed, waits for the engine, runs the existing start.ps1 without rebuilding models, starts the loopback gateway and a free temporary tunnel, verifies public HTTPS health, and publishes the new address to Cloudflare KV. Keep the launcher window open and the laptop awake/online. If Docker is paused, unpause it and retry. Ctrl+C stops this launcher/tunnel; saved accounts, history and models remain on disk.

Dashboard and Android server address (unchanged after restarts):
https://praxisdashboard.debopomrc2602.workers.dev/

No dashboard redeployment or manual Cloudflare setting update is needed on subsequent starts. Address propagation can take about a minute. Model loading after a cold start can take several minutes. The laptop being off/asleep makes the backend unavailable; the launcher cannot wake it remotely.

One-time setup is complete on this PC: official Wrangler 4.137.0 OAuth authorization, KV namespace PRAXIS_TUNNEL, production worker binding and deployment. The launcher uses cached Wrangler, and its existing authorization refreshes normally. Credentials stay in Wrangler's local ignored configuration; none are exported to this repository. If access is revoked or login expires, run `npx wrangler@4.137.0 login` inside praxis-dashboard and approve once in the browser. If npm's cache was deleted, run `npx --yes wrangler@4.137.0 --version` once to restore it. This is authorization/package recovery, not a dashboard deployment.

KV stores only backend-origin, not credentials, audio or analysis. The Worker reads it on API requests with a 60-second cache TTL; lookup failures or a missing value fail closed (503), rather than forwarding credentials to a stale fallback. HTTPS validation, backend authentication and upstream WebSocket upgrade metadata are preserved. No public address-update endpoint exists: only the authorized local Cloudflare CLI writes KV. The database, gateway and model-worker ports stay private. The single launcher locks against duplicate startup.

No paid plan, payment details, GPU cloud or automatic top-up was enabled. Cloudflare's existing Free-plan quotas still apply; Quick Tunnels provide no uptime guarantee. This is a local demo setup.

## Verified 2026-10-05
The real launcher reused persistent worker PID 16644, confirmed PostgreSQL/backend/Caddy, created a different tunnel and automatically wrote its verified HTTPS origin to remote KV. Removed only the previous manual connector, then passed fresh real PostgreSQL signup/login/session, authenticated analysis WSS ping/pong, and two-party VoIP signaling plus exact bidirectional synthetic PCM relay through the unchanged dashboard URL. Disposable test records were removed. Four gateway tests, Ruff, PowerShell syntax, dynamic proxy/security tests, and dashboard build passed; duplicate launcher correctly rejected. Initial CLI output decoding error was fixed with explicit UTF-8 decoding. No physical phone call/scoring run claimed. Production deployment c83c7340-818b-428d-aa71-b82b0de1a91b enabled dynamic lookup; later repository builds retain the binding. Models, APKs, secrets and API contracts unchanged.

Prior manual tunnel instructions in historical checkpoint files are superseded by this guide.