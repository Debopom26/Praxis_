# Phase 4 - SDK integration

Implemented actual SDK adapter, validated configuration, session lifecycle, Closeable subscription ownership, callback-based connection/error state and explicit manual reconnection by creating a new client. No invented original SDK APIs. Locally added stopStreaming is documented in SDK_RUNTIME_PATCHES.md and implemented in sdk-runtime. Original supplied source integrity passes.

SDK/runtime mapping: SdkPort constructor -> PraxisClient(PraxisConfig); listen -> onEvent; start -> startSession; audio -> streamAudio with actual contracts.AudioFormat; stop -> runtime stopStreaming; end -> endSession; close -> close. No public ACK count is invented.

Supplied five contract tests pass in phase4-supplied-sdk. Runtime derivative's eight tests pass in final-runtime-sdk-repair. Real app adapter/SDK loopback path and six adapter tests pass in final-regression-render-fix. Production network remains BLOCKED by absent configuration. Gate: PASS for defined compile/API/test acceptance; no live server claim.
