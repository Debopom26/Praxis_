# Phase 7 - Traceable end-to-end path

Real Telecom state -> explicit consent + CapturePolicy -> CaptureService/AudioRecord -> PraxisManager.sendAudio -> SdkPort -> actual runtime PraxisClient.streamAudio -> network -> typed SDK events -> epoch/call/timestamp/dedup filters -> StateFlow -> Compose. Phone calls have no dependency on any Praxis result. All errors are optional-layer state only. The status page reports connection, session existence, frames enqueued and last event; server ACK explicitly unavailable.

Real SDK loopback test passes: synthetic frame to MockWebServer WebSocket, actual SDK risk decoding back to adapter state, followed by immediate stop and real session-end HTTP request. This proves host wiring, not live analysis. Tests also reject disconnected/foreign frames, stale callbacks, duplicate/delayed decisions, missing credentials and failed session start. SDK invalid-event tests fail closed. Missing analysis stays null/neutral.

Gate: host traceability/failure isolation passes. Production auth/network/model and physical microphone/SIM coexistence are BLOCKED/PHYSICAL TEST REQUIRED.
