# Requirement traceability

The Master SRS remains authoritative. IMPLEMENTED describes code in this partial phase; VALIDATED refers only to the stated checks, not detection accuracy, a complete SRS demo, or a production deployment.

| Requirement | Current implementation | Verification / remaining work |
| --- | --- | --- |
| FR-01 ingestion | Authenticated WSS, controlled enrollment clip input, synthetic test tooling | API/WSS unit tests, actual Caddy WSS authentication/PCM ACK/reconnect/gap/size checks and real model orchestration; general evaluation UI excluded |
| FR-02 preprocessing | PCM/decode, native-rate mono, real Silero, 4 s/2 s windows, source spans/quality | Sample-rate, silence, gap, overlap and reconnect-ID regressions; real synthetic-speech pipeline |
| FR-05 prosody | openSMILE eGeMAPSv02 + Parselmouth features | Real feature checks; XGBoost and calibration artifacts unavailable/deferred |
| FR-06 speaker | ECAPA embeddings/cosine; approved multi-clip enrollment; encrypted profile; deletion | Real ECAPA synthetic enrollment through HTTPS; 192-value encrypted centroid persisted/decrypted on PostgreSQL, tenant deletion/default-off audio verified; unit quality guards. No validated threshold or genuine identity accuracy claim |
| FR-07 ASR | Whisper Small Multilingual; source-timeline mapping; English analysis view | Actual synthetic speech transcription and quality/span regressions; multilingual WER/CER deferred |
| FR-08 linguistic | Eight deterministic English rule categories; multilingual MiniLM encoder/interface | Rules/quality gates and real 384-value embedding; trained Praxis head unavailable |
| FR-09 AI-written | Sequential Qwen observer/performer statistics, 64-token gate, low-priority runtime | Actual 83-token forward-pass smoke; classifier/fusion thresholds unavailable |
| FR-10 context | Seven supplied-fact flags, UNKNOWN missingness, versioned SIH weights | Complete/partial/empty context tests; real tenant config isolation, context persistence across PostgreSQL/backend restart and atomic rollback |
| FR-12/13 risk/EMA | Approved-hash logistic artifact loader, feature schema 1.1.0, preprocessing/missingness, EMA .35 | Artifact rejection/preprocessing/EMA tests; no trained runtime artifact or live risk value |
| FR-14 policy | Versioned thresholds 40/60/80/90, HOLD capability fallback, AI-only restriction | Boundary/fractional-risk/fallback tests; requires genuine validated risk |
| FR-15 SDK | Kotlin AAR, generated contracts, bounded PCM/reconnect/callbacks | Five JVM tests, shared fixtures, lost-ACK reconnect, Android lint and release build; device integration pending |
| FR-16 permitted integration | HTTPS/WSS interfaces and Caddy/Compose definitions | Real Docker/PostgreSQL migrations 0001/0002, trusted local HTTPS/WSS routing, authentication and bounds pass. Public TLS/device tests pending; calling app/WebRTC excluded; external webhooks not claimed |
| FR-18 audit | Atomic lifecycle/configuration/evidence audit, event/model/profile/config/risk/policy provenance | Real PostgreSQL trigger-induced failure gives REST 503 and WSS 1013/no ACK with rollback; provenance checked. Historical synthetic pipeline 57 events + 58 audit records used isolated SQLite |
| FR-19 privacy | No raw live audio storage; encrypted opt-in retained payloads; expiry/purge; encrypted profiles | Real PostgreSQL ciphertext/default-off/opt-in/expiry/off-purge/completed-context cleanup; no live audio files in writable runtime paths; key rotation remains an operational responsibility |
| FR-20 tenant isolation | JWT membership, RBAC, tenant/session ownership, composite FKs, tenant configs/profiles | Live HTTPS/WSS cross-tenant and RBAC denials, PostgreSQL composite FKs and concurrent sequence locking pass; separate least-privilege DML role denies DDL/TEMP |
| FR-24 failure transparency | Four operational statuses, separate artifact state; no substitute numeric evidence | Contract/failure-isolation checks; deployed six permitted components AVAILABLE/five trained artifacts UNVALIDATED; real database outage returns 503/UNAVAILABLE |
| NFR-01/02/04/08 | Bounded workers/queues, isolated model errors, sanitized errors/logs, health/provenance/latency | Unit checks, synthetic model execution, actual deployed size bounds/health/log checks; residual image advisories documented; no target-hardware real-time SLA claim |
| FR-03/04/11/17/21/22/23 and excluded FR-16 portions | Deferred by explicit phase scope | No anti-spoof, datasets, training/calibration, dashboard or calling-app implementation |

P10 local deployment evidence: `DEPLOYMENT_VERIFICATION.json`; exact image/digest inventory: `DEPLOYMENT_IMAGES.json`; real scans and remaining vulnerabilities: `CONTAINER_SECURITY_AUDIT.md`. Historical offline results remain preserved. The full SRS success conditions require later validated artifacts and real-device/public-deployment checks. No module is marked DEMO_READY; current images are not claimed production-ready.


## Fresh E2E baseline PASSED — 2026-09-29
All 54 W2V2 windows succeeded. Peak 0.9998408555984497 exactly matches the supplied baseline. Fresh Whisper transcript matches exactly (302 words); trained MiniLM strict 8-label output succeeds; Prosody has 98/98 finite features. Fresh fusion/risk reproduces 97.4643709518332/HOLD, BOOTSTRAP_UNTRAINED. Qwen CPU variation was accepted by the user and leaves its existing cap unchanged. Context execution succeeds but unknown evidence remains unavailable (historical runner forced AVAILABLE). ECAPA has no trusted enrollment; separate public-sample embedding test passes. Proof: docs/import-2026-09-29/final-e2e-local.json. W2V2 environment exactly matches every supplied pinned dependency, imports successfully, and pip check passes. Active interpreter: /home/kiit/.local/share/praxis/w2v2-py310/bin/python in Ubuntu-24.04.

Latest user scope: preserve this baseline; now integrate persistent dependency-aware inference, connect a previously built webapp (path requested), provide a microphone CLI, and distinguish synthetic speech from harmful scam indicators. Do not convert bootstrap score into calibrated scam probability. No microphone recording has been started by the agent.


## Latest checkpoint — supplied E2E and personal tester ready (2026-09-29)
Fresh full baseline remains PASSED: 54/54 windows, peak 0.9998408555984497,
97.4643709518332/HOLD, BOOTSTRAP_UNTRAINED; see final-e2e-local.json. No retraining.
Opt-in persistent backend runtime and authenticated V2 routes now implemented. Actual final
8-second file run passes: concurrent Wave A, Whisper-dependent Wave B, evidence barrier,
fusion/risk/policy ordering. AI-only clip yields AI_NOTICE rather than scam guidance.
Final inference ~21.84 seconds for 8 seconds of audio, excluding startup; not real-time throughput.
Proof: docs/import-2026-09-29/manual-cli-final-result.json and integration-verification.json.
Regression: 81 backend tests passed; final affected 9 tests passed; mypy 46 files, Ruff,
Bandit (reviewed internal subprocess annotations), pip check and JS client boundary checks pass.
Existing weights/secrets/V1 validated-risk contracts preserved. Unknown context/no enrollment
and short-text Qwen remain unavailable honestly. Bootstrap score is never a scam probability.
Disposable independent tester: manual-tests/microphone-cli/start.ps1. Default Realtek device
supports mono16k float32; only device/format checks performed, no microphone capture started.
User can manually run tester and delete that folder later. It drops stale queued audio on CPU lag.
Webapp files are not yet available from user. integrations/webapp provides HTTPS client and
configuration notes; actual webapp connection and new V2 Docker/PostgreSQL/Caddy deployment
are NOT complete or claimed. Existing historical P10 deployment evidence remains separate.
Do not rerun/rebuild baseline or train models just to continue. Next: user's manual microphone
testing; integrate actual webapp once supplied, then verify its target deployment/runtime access.

## Android V2 demo bridge — 2026-09-30

Authenticated `/api/v2/analysis` now reaches one persistent host-side supplied-model worker; the consent-gated Android caller sends 16 kHz mono 4-second windows with 2-second overlap and displays experimental score/guidance. Real model smoke passed; backend 85 tests and Android 41 tests/lint/build passed. Docker activation and physical-phone E2E await a Windows restart to clear Docker's locked stale socket.
Architecture/security/redundancy review: docs/SUPPLIED_RUNTIME_AUDIT.md.

## 2026-10-01 phone deployment and score checkpoint
Actual HTTPS sign-in, PostgreSQL session/WSS audio upload and authenticated V2 results were observed on the USB phone at the current LAN IP `10.21.23.117`; Caddy CA and hostname validation passed. The first UI score vanished after V1 gaps; the gap fix was phone-verified. A later WSS reconnect received HTTP 403; bounded SDK retry is tested but not yet phone-verified. One provisional score and backend guidance replace duplicate numeric scores; repeated action chime was deduplicated. Direct real-worker 4s analysis of `spoof1.m4a` returned score 7.604/AI 0.209 at 0s and score 97.037/AI 99.981 at 20s, disproving a constant model output. The phone's 7-point AI-voice result remains unresolved pending acoustic capture testing. Latest APK prefers supported UNPROCESSED microphone input with MIC fallback and logs RMS/peak and output scores only; physical-call verification remains pending. SDK 6 tests and caller 41 tests, lint and builds pass. No model weights, artifact thresholds, risk coefficients, secrets or backend contract were changed; no raw audio is retained.
2026-10-01 LAN address repair: DHCP moved the Praxis host from 10.21.23.117 to 10.20.51.112 while the Android app retained the old server URL. Updated only PRAXIS_HOST and PRAXIS_DEFAULT_SNI in the existing .env, preserving secrets, and recreated Caddy without rebuilding images. Docker backend and PostgreSQL remain healthy; Caddy serves https://10.20.51.112/api/v1/health with HTTP 200 under normal CA/hostname validation. The Caddy local CA SHA-256 matches the Android-bundled Praxis-Local-CA.crt: 7A1A1A7C357BB55D17146B5A927533226AE29C6FF3912AEFF97720167B057487. User should set the Android saved server URL to https://10.20.51.112/ and use the existing account. User deferred phone retest; do not claim sign-in or call streaming now verified at the new address. The prior AI-voice capture/score diagnostic call is also pending.

2026-10-01 Android silent-capture repair: USB phone logs showed repeated V2 rms=0.000000/peak=0.0000, score=7.516 and Android AudioService recorded com.praxis.caller src=MIC silenced during the active cellular call. This explains the apparently fixed 7.5 score; it was a response to zero audio, not a frozen model. Caller now retries AudioRecord after 4 seconds of consecutive all-zero frames or read interruption, keeps the session/capture service alive while permitted, and resumes sending when nonzero audio becomes available. All-zero 4-second V2 windows are not scored; previous score/action is cleared and the UI reports microphone audio unavailable/retrying. On valid audio, analysis can resume with the existing model/API. Password sign-in also has a default-hidden Show/Hide toggle without persisting the password. Android app: 43/43 JVM tests, lintDebug and assembleDebug passed; APK integrations/android/Praxis-Caller-Connected.apk SHA-256 F7EF92A7D2E4FF2AA8586C11E7369CB4EC3A5DE64E771B3346FC30A553BE97CC. New APK installed on USB phone after removing the old differently signed debug build; app sign-in/settings were cleared and must be entered again. No audio, model, thresholds, backend API or secrets changed. User deferred live call; automatic recovery and continuous scoring remain phone-unverified. Android may continue silencing third-party capture for the entire cellular call, which no app retry can override.

2026-10-01 live retest at 12:14-12:15 IST: USB phone is in active cellular call (mCallState=2). Android dumpsys audio repeatedly reports com.praxis.caller src:MIC silenced for every recorder instance. The new APK restarted MIC capture about every 5 seconds, but Android silenced each new instance; no nonzero V2 windows/results appeared. WSS briefly disconnected and reconnected, so network recovery is not the cause of microphone unavailability. The UI correctly says microphone audio unavailable. A continuous score cannot be produced from this phone during this call while Android enforces capture silencing. Recovery after Android releases the microphone remains unverified; retry cannot override OS audio policy. Do not claim this APK delivers live scores in a normal cellular call on this device. Demo needs an independent capture device or a calling architecture that owns the audio stream.

2026-10-01 dashboard implementation: UI `praxis-dashboard/src/components/CurrentSessions.tsx` + `pages/LivePage.tsx` -> authenticated `GET /api/v1/dashboard/sessions` and detail endpoint -> PostgreSQL `sessions`/audit/risk records; active presence from actual WSS registry. Login uses tenant ID and backend JWT/RBAC. Android `SessionDisplayClient.kt` -> optional contact name/number/call time, with READ_CONTACTS lookup. V2 `/api/v2/analysis` persists only allowlisted score/status/guidance after successful audit transaction. Caddy serves built dashboard and reverse proxies `/api/*`; Cloudflare Pages Function uses public HTTPS origin. Verified migration 0003, TLS static/API, DB privileges, health and auth; live phone call remains pending because phone disconnected and Android MIC silencing persists.
