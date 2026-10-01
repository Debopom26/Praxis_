# Praxis dashboard

React, TypeScript and Vite dashboard for the **live Praxis backend** in the parent `Praxis_` folder. It displays authenticated, tenant-scoped sessions and actual persisted analysis. No demo account, fabricated score or browser audio capture is used.

Double-click `start.cmd` to build the current dashboard, start the existing Praxis services, and open their HTTPS dashboard. Docker Desktop must be running. For a launcher check without opening a browser, run `start.cmd -NoOpen`.

The launcher opens `https://localhost/` on this computer. On every backend start, the terminal also prints the current HTTPS LAN address for a phone on the same network. After switching networks, restart Praxis and update the phone's saved server address; no LAN IP is baked into the dashboard or Android app.

## Local development

Start Praxis using its own `scripts/start.ps1`. Then run `npm ci` and `npm run dev` here. The Vite proxy sends `/api` to `PRAXIS_DEV_BACKEND` from `.env.local`; the default is `http://127.0.0.1:8000`. Use the real organization ID, username and password created in Praxis. Do not commit `.env.local`.

For a local HTTPS deployment, run `../scripts/deploy-dashboard.ps1`, then `../scripts/start.ps1`. Caddy serves the built dashboard at the existing Praxis HTTPS address and forwards `/api/*` to the backend. Trust the existing local Praxis CA on the device; do not disable TLS verification.

## Cloudflare Pages, after uploading to GitHub

Set the Cloudflare Pages project root directory to `praxis-dashboard` in this combined repository.

Connect this repository to Cloudflare Pages. Set the build command to `npm run build` and output directory to `dist`. Add a **server-side Pages environment variable** `PRAXIS_BACKEND_ORIGIN=https://your-public-praxis-api.example` (an HTTPS origin with no path). `functions/api/[[path]].ts` forwards same-origin `/api/*` requests. The URL must reach the actual Praxis Caddy service from Cloudflare; a private Wi-Fi IP such as `10.x.x.x` will not work. Use a public domain or a correctly secured Cloudflare Tunnel and a valid certificate. Never put passwords, JWTs, model keys or database credentials in Pages variables or GitHub.

The dashboard polls actual session results every three seconds. An active audio connection with no fresh analysis displays “Awaiting analysis”; it does not claim a score. The current Android cellular-call microphone restriction can still prevent usable audio, even while a call appears connected. A contact name appears only when the Android app has permission and supplies it. Browser WebSocket observation is not used because the Praxis WSS endpoint is an exclusive audio source, not an observer endpoint.

The authoritative backend lives in the parent Praxis folder; this dashboard package contains only the web client.
