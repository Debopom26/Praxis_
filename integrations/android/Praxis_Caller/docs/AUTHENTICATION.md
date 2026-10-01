## Current implementation - 2026-09-29

Current implementation: app auth/PraxisAuthManager.kt, SecureStore.kt and AuthCallbackActivity.kt. See PHASE_5_AUDIT.md. A generic, explicitly configured OAuth2-PKCE option exists; production Praxis compatibility/config remains unknown and disabled. Older source findings below describe the unchanged supplied SDK, which still provides no login.

---

# Praxis Authentication

Desired UX:
Connect to Praxis
-> check existing valid credentials/session
-> if valid: connect
-> if invalid: show auth dialog
-> open Praxis web app
-> authenticate
-> deep-link/App-Link callback
-> securely store credential/token
-> SDK token provider
-> connect

Do not fake success if server endpoints/client IDs/callback configuration are unavailable.

Document actual auth endpoints and callback scheme only when supplied/verified.

## Phase 0 source findings
`PraxisConfig.tokenProvider: () -> String` is synchronous and supplies bearer tokens to REST and WebSocket requests. SDK has no login, browser callback, refresh, expiry validation or credential storage. `/api/v1/auth/login` is a README assertion only; no server/login implementation or production configuration was supplied. Neither construction nor `startSession` return proves streaming/auth completeness. Socket HTTP 401/403 stops automatic retry; refresh belongs to the future host and `reconnect()` is the public recovery hook. Detailed source references are in PRAXIS_INTEGRATION.md.
