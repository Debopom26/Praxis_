# API contract

All protected REST/WSS requests use `Authorization: Bearer <token>`. Credentials and tokens never appear in URLs. Login takes username, password and tenant_id; membership determines access. Hosts can operate their own sessions; administrators can operate tenant sessions; analysts can inspect tenant history but cannot stream, enroll or change configuration. Errors omit request inputs and secrets.

| Route | Purpose / access |
| --- | --- |
| POST /api/v1/auth/login | Local identity login; JWT TTL at most 30 minutes |
| POST /api/v1/sessions | Admin/host; create with authorized call ID/context |
| GET /api/v1/sessions/{id} | Authorized tenant/session summary |
| PATCH /api/v1/sessions/{id}/context | Admin/host; omitted facts unchanged, explicit null clears |
| POST /api/v1/sessions/{id}/end | Admin/host; idempotent end |
| WS /api/v1/stream/{id} | Admin/host; authorized PCM and asynchronous typed events |
| POST /api/v1/speaker-enrollments | Admin; controlled approved enrollment |
| DELETE /api/v1/speaker-enrollments/{identity}?session_id=... | Admin; delete tenant profile and retained enrollment audio, with audit |
| GET /api/v1/config/{context,policy,retention} | Admin/analyst; effective tenant configuration |
| PUT /api/v1/config/{context,policy,retention}?session_id=... | Admin; append immutable configuration version and audit |
| GET /api/v1/audit/{id} | Admin/analyst; limit 1–500, offset >=0 |
| GET /api/v1/sessions/{id}/retained | Admin/analyst; unexpired retained-object metadata |
| GET /api/v1/sessions/{id}/retained/{payload_id} | Admin/analyst; explicitly retained data; access audited |
| GET /api/v1/health | Operational components, model versions and separate artifact readiness |

Enrollment JSON contains `session_id`, `identity`, `approved: true`, and `clips_base64` with 3–10 WAV/FLAC clips. Each encoded clip is at most 8 MiB and the whole request at most 32 MiB. Each clip must pass quality/VAD checks; at least 15 total voiced seconds are required. This is an administrator's controlled genuine-audio workflow, not automatic enrollment from live callers. No validated match/mismatch thresholds are present; real cosine similarity remains distinct from identity decisions. Raw clips are discarded unless the tenant explicitly enables encrypted retention.

WSS accepts JSON AudioFrame: type=audio, increasing sequence_id/timestamp_ms, pcm_s16le sample rate/channels and base64 PCM (at most one second). Server connection event includes last_sequence_id and last_timestamp_ms. Clients discard already accepted frames after reconnect, including when an acknowledgment was lost. New connections explicitly reset transient buffers. One stream per session; at most 16 per process. Use exactly one API worker.

Events: connection, ack, pong, analysis_gap, audio_window, evidence, transcript, context, risk, policy and unavailable. Evidence module identifies speaker/prosody/linguistic/AI-text variants. JSON schemas are canonical in contracts/schemas; OpenAPI covers REST in contracts/openapi/openapi.json. `{ "type": "ping" }` heartbeat is whitespace-independent and should arrive within 30 seconds. Malformed frames close 1007, unauthorized/conflicting state 1008, oversized frames 1009, and persistence/timeout failures 1013.

Two pending windows and 64 output events bound each session. Slow inference drops queued windows with an explicit analysis gap. Native-model calls finish within bounded worker pools; Qwen uses a separate low-priority worker. Core results are delivered before ASR/AI-text completion. Whisper accumulates novel speech without double-counting overlaps; unsupported or low-quality transcript-dependent evidence is unavailable. Events are persisted with audit metadata before delivery; audit failure closes the stream.

Raw live audio is never stored. Full transcript and approved enrollment-audio retention are separately opt-in and encrypted with AES-256-GCM; default metadata retention is 30 days. Retained objects expire, cannot be read after expiry, and are purged at startup/hourly. Completed session context/history also expires. Policy defaults are versioned SIH thresholds, not learned fraud truth. Risk remains UNAVAILABLE without an externally approved, hash-matched validated artifact.
