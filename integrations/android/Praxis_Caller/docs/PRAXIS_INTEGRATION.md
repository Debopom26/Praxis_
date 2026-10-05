## Current implementation - 2026-09-29

Current app integration: SdkPort/PraxisManager use artifacts/praxis-runtime-release.aar. sdk-runtime is a documented safety derivative (SDK_RUNTIME_PATCHES.md); it adds implemented stopStreaming and tightens protocol validation. This file continues to map ORIGINAL supplied APIs. Do not attribute stopStreaming to the pristine archive.

---

# Praxis SDK integration — Phase 0 source truth

Verified 2026-09-23. `sdk/` is the standalone build copy; its ten supplied source/config/test files are byte-identical to `android-sdk.zip`. `vendor/android-sdk/` preserves the complete original extraction including historical outputs. `evidence/archive-inventory.csv` hashes every archived file. This document describes client source behavior, not verified production server behavior.

Source references: **C** = `sdk/praxis/src/main/kotlin/io/praxis/sdk/PraxisClient.kt`; **T** = `sdk/praxis/src/main/kotlin/io/praxis/sdk/contracts/Contracts.kt`; **U** = `sdk/praxis/src/test/kotlin/io/praxis/sdk/ContractTest.kt`. Line numbers refer to unchanged supplied source.

## Structure and dependencies

Root `PraxisSdk`, one Android library module `:praxis`; no app/APK. Namespace/package `io.praxis.sdk`; contract package `io.praxis.sdk.contracts`. AGP 8.9.2, Kotlin Android/serialization plugins 2.1.20, compileSdk 35, minSdk 26, Java/Kotlin target 17. Caller minSdk 29 remains a separate requirement. SDK compileSdk 35 does not decide the future app's current stable target.

Dependencies: serialization-json 1.8.1 (`api`), coroutines-core 1.10.2 and OkHttp 4.12.0 (`implementation`), JUnit 4.13.2 and MockWebServer 4.12.0 (tests). Repositories: Google, Maven Central, Gradle Plugin Portal. Manifest declares INTERNET only. Consumer rules contain a comment, no custom rules. Tests enable `isReturnDefaultValues`; resource directory `../../contracts/examples` is relative to the praxis module.

Original README names Gradle 8.11.1 but archive lacks a wrapper, bootstrap scripts, schemas and generator. Phase 0 supplies build tooling separately and recovers ten JSON fixtures plus README byte-for-byte from generated test resources. See `evidence/input-verification.json`. Old build/test/lint reports are historical, not fresh verification.

## Exact public API

| Interface | Meaning/limits | Source |
|---|---|---|
| `PraxisConfig(baseUrl: String, tenantId: String, hostAppId: String, tokenProvider: () -> String, maxBufferedAudioBytes: Int = 384000, maxBufferedFrames: Int = 100, allowCleartextForTests: Boolean = false)` | Config, no login/refresh/persistence. | C:22–30 |
| `PraxisClient(config: PraxisConfig) : Closeable` | Constructs HTTP/IO callback state; does not authenticate or create a session. | C:78–108 |
| `onEvent(callback: (PraxisEvent) -> Unit): Closeable` | Close returned handle to unsubscribe. | C:110–113 |
| `onRiskUpdate(callback: (RiskEvent) -> Unit): Closeable` | Filtered registration. | C:114 |
| `onPolicyAction(callback: (PolicyEvent) -> Unit): Closeable` | Filtered registration; does not execute phone actions. | C:115 |
| `suspend startSession(callId: String, context: ContextInput = ContextInput(), claimedIdentity: String? = null, supportsHold: Boolean = false): String` | One active session/client; POST then asynchronous socket connect. Returned ID does not prove streaming. | C:146–158 |
| `streamAudio(sessionId: String, audioFrame: ByteArray, timestamp: Long, format: AudioFormat): Unit` | Validates/enqueues JSON/base64 PCM. Return is not remote ACK or inference success. | C:160–185 |
| `reconnect(): Unit` | Replaces socket/reset retry counter for active session. | C:268 |
| `suspend updateContext(sessionId: String, contextPatch: ContextInput): Unit` | Typed PATCH; null/default properties omitted. | C:269–271 |
| `suspend updateContext(sessionId: String, contextPatch: JsonObject): Unit` | Explicit JSON null can clear facts. | C:272–275 |
| `suspend endSession(sessionId: String): Unit` | POST end; clears matching local session in finally even if request fails. | C:276–283 |
| `close(): Unit` | Cancels/clears sockets, jobs, listeners and buffers; no server end request. | C:284–293 |
| `PraxisWire.json: Json`, `PraxisWire.decode(message: String): PraxisEvent?` | Public decoder; ignores unknown keys, omits defaults/nulls. Unknown event types throw. | C:48–75 |

There is **no public `connect()`**, disconnect, login, ACK listener, connection getter, frame counter, Flow or recorder. `PraxisManager`, `PraxisAuthManager`, app `PraxisState`/`PraxisResult`, `CallAudioSource` and `SpeakerMicAudioSource` are future host types, not SDK APIs.

## Auth and wire paths

Synchronous `tokenProvider` is invoked for every REST request and socket connection. SDK requires nonblank token and sets `Authorization: Bearer <token>` (C:130–143,207–214). It does not parse expiry, validate JWTs, refresh tokens, implement browser auth or persist credentials. Provider exceptions are not normalized into auth events.

| Transport | Source-constructed path | Operation |
|---|---|---|
| POST HTTPS | `/api/v1/sessions` | SessionStart -> SessionView/sessionId |
| HTTPS WebSocket upgrade / WSS | `/api/v1/stream/{sessionId}` | Audio/events |
| PATCH HTTPS | `/api/v1/sessions/{sessionId}/context` | Context patch |
| POST HTTPS | `/api/v1/sessions/{sessionId}/end` | `{}` body |

Source: C:126–157,214,269–278. `/api/v1/auth/login` exists only in supplied README; backend implementation, request/response, browser flow, refresh and callback are unverified. Production host, tenant, hostAppId and credentials are absent.

HTTPS required except test flag with localhost/127.0.0.1. Root path must be `/`, with no credentials/query; redirects disabled, normal TLS verification. Connect/read timeouts 10/30 seconds; REST response maximum 1,048,576 buffered bytes. Exceptions include CLIENT_CLOSED, ACCESS_TOKEN_REQUIRED, PRAXIS_HTTP_<status>, EMPTY_RESPONSE, RESPONSE_TOO_LARGE, network/serialization errors. Construction or session ID alone never means auth succeeded.

## Audio contract

`AudioFormat(encoding: String = "pcm_s16le", sampleRate: Long, channels: Long)` and `AudioFrame(type="audio", sequenceId: Long, timestampMs: Long, format: AudioFormat, audioBase64: String)` (T:48–61).

Intent: authorized remote-caller signed PCM16 little-endian. Source accepts 8000/16000/24000/32000/44100/48000 Hz, 1–2 channels, nonempty bytes aligned to `2 * channels`, length <= `sampleRate * channels * 2` (one second). Timestamps strictly increase within 0..9,007,199,254,740,991; sequences start at zero with the same upper bound (C:161–170). No continuity/overlap or actual PCM-content validation. **Encoding is a free String and is not validated**; host must use pcm_s16le.

16 kHz mono 20 ms = 640 bytes fits the checks; this is a suggested later framing choice, not an implemented device setting. No capture/resampling/channel selection/voice separation/ML windowing is implemented. Four-second/two-second server windowing is locked product intent, not verified server behavior. One synthetic fixture depicts a four-second window only.

V1 speaker/microphone may mix local voice and ambient sound. It is not established as remote-only PCM, despite the SDK's stated intended input. Preserve this Phase 6/backend-quality validation dependency; do not silently equate the two.

## Buffer, ACK and reconnect

Pending TreeMap uses sequence keys, default 100 frames / 384000 **raw audio bytes**. Config permits 1..200 frames and 1920..1048576 bytes (C:85–106,170–204). Heap also includes JSON/base64, events and socket queues. Oversized frame consumes sequence/timestamp, emits Gap(FRAME_EXCEEDS_BUFFER), then returns. Overflow evicts oldest pending frames and emits Gap(SDK_BUFFER_OVERFLOW).

Active disconnected sessions still accept/buffer audio; flush resumes on hello. SDK does not enforce opt-in/call state. Flush checks approximately 1 MiB socket queue limit; successful send means queued, not accepted by server (C:188–195). Future adapter must stop capture/enqueue on disconnect and explicitly handle retained audio policy.

Hello validates session ID and contract major `1`, cumulatively discards IDs <= server lastSequenceId, advances local sequence/timestamp, resets retry count and emits Connection(true, reasons). **Hello status is decoded but ignored**. ACK cumulatively discards IDs and flushes; no public ACK getter/event and no bounds check against sent sequence (C:222–236).

Disconnect emits Connection(false,[STREAM_DISCONNECTED]). Codes 1000/1002/1007/1008/1009 stop retries with STREAM_REJECTED_<code>; HTTP 401/403 on socket handshake maps to 1008. Other failures back off 1,2,4,8,16,30,30,30 seconds then RECONNECT_LIMIT. Hello resets count; no jitter (C:245–268). Manual reconnect does not explicitly cancel a scheduled retry/heartbeat before replacing socket. JSON ping and OkHttp protocol ping each use 10 seconds; no app-level pong deadline.

endSession performs HTTP before local cleanup; host must stop capture immediately before awaiting it. close alone does not finalize server state. SDK does not filter analysis by current call/window or deduplicate risk/policy. Host must isolate lifecycle failures, reject stale events and implement decision sound once.

## Events and types

| PraxisEvent | Payload |
|---|---|
| Evidence | ModuleEvidence |
| Speaker | SpeakerEvidence (`module=speaker`) |
| Linguistic | LinguisticEvidence (`linguistic_rules` or `linguistic`) |
| AiText | AIWrittenEvidence (`ai_text`) |
| Transcript | TranscriptEvent |
| Context | ContextEvidence |
| Audio | AudioWindow metadata, not microphone samples |
| Risk | RiskEvent, raw/display 0..100 checked on decode |
| Policy | PolicyEvent |
| Unavailable | UnavailableEvent, separate from numeric risk |
| Connection | Boolean connected, List<String> reasons |
| Gap | List<String> reasons |
| Error | String code |

C:32–75; [all 37 DTO/enum definitions](SDK_CONTRACT_TYPES.md). Risk fields include call/window IDs, scores, evidenceSummary, quality, missingness, model version, artifactState and timestamp. Policy enum: ALLOW/WARN/SECONDARY_VERIFICATION/ESCALATE/HOLD; source executes none. DTO defaults such as risk artifactState VALIDATED are not evidence of validated models. Missing analysis must never become zero risk.

Callbacks run sequentially on IO, must return promptly; listener exceptions are swallowed. Channel capacity 64. Overflow cancels socket, sets disconnected, drops one queued item and attempts CALLBACK_BACKPRESSURE error. Delivery of every event/error is not guaranteed; socket cancellation can enter retry logic (C:84–122).

Wire input <=1,048,576 characters. Malformed socket events emit INVALID_SERVER_EVENT and close 1002. Standalone decoder returns null for ack/pong/connection; live socket processes ACK/hello internally. Most DTO semantics have no additional validation beyond serialization; risk ranges are explicitly checked. There is no SDK-provided deduplication/quality guarantee.

## Supplied tests and limitations

Exactly five tests (U): canonicalFixturesRoundTrip, riskAndUnavailableRemainSeparate, tlsAndAudioValidation, sessionStreamAckAndEnd, reconnectDoesNotReplayAcceptedFrameAfterLostAck. First two require recovered fixtures. Network tests use loopback MockWebServer, TEST_ONLY token and synthetic PCM; they are not live Praxis tests. ACK/end test checks sending and auth header, not every internal ACK transition/end-body detail.

Missing coverage includes slow callbacks, buffer overflow, provider exceptions, hello status/ACK bounds, manual reconnect races, stale/duplicate analysis, production TLS/auth, hardware capture and SIM calls. These are recorded source risks; Phase 0 establishes truth, not production readiness. The supplied SDK implementation remains unchanged. Fresh results: TEST_LOG.md and evidence/.

## Official build-tool references

[AGP 8.9 compatibility](https://developer.android.com/build/releases/agp-8-9-0-release-notes), [Gradle distributions](https://services.gradle.org/distributions/), [Android CLI downloads](https://developer.android.com/studio). These support build-tool sourcing; supplied Praxis source is the API authority.
