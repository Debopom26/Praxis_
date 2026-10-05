# Live Praxis dashboard contract

The authoritative backend is in the parent `Praxis_` folder. The locked SRS remains the source for model and security behavior. These dashboard routes are authenticated integration extensions implemented in the current Praxis backend.

| Route | Current use |
| --- | --- |
| `POST /api/v1/auth/login` | Username, password and `tenant_id`; returns JWT, expiry, role and account name. |
| `GET /api/v1/health` | Actual backend, database, component and artifact states. |
| `GET /api/v1/dashboard/sessions` | Tenant-scoped list with `q`, `offset`, `limit`, optional `active`; host role sees owned sessions only. |
| `GET /api/v1/dashboard/sessions/{id}` | One tenant-scoped session including actual connection presence, optional contact label, duration timestamps and persisted latest analysis. |
| `PUT /api/v1/sessions/{id}/display` | Android host/admin sends optional contact name, number and connected time. |
| `GET /api/v1/audit/{id}` | Recorded events for admin/analyst roles. |
| `POST /api/v2/analysis` | Android submits consented audio; the dashboard never sends audio. |

The dashboard uses same-origin `/api` and polls session records every three seconds. It never opens the exclusive Praxis audio WebSocket or puts a JWT in a URL. The latest V2 score is a provisional bootstrap result, not a calibrated scam probability. The UI shows it only for an active connection when the persisted result is at most 30 seconds old, and displays the backend's action/message without deriving a decision from the number. An active connection can still have no usable audio, particularly when Android silences a third-party microphone during a cellular call. No score appears then.

For Cloudflare Pages, the server-side `PRAXIS_BACKEND_ORIGIN` variable must identify a publicly reachable HTTPS Praxis backend; the Pages Function forwards `/api` with the Authorization header. No browser CORS relaxation or disabled certificate validation is required.
