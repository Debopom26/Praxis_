# Runtime SDK patch provenance

Original sdk/ and vendor/android-sdk/ remain unchanged. sdk-runtime/ is an explicit derivative for app use; public contracts remain byte-identical. Patches address source-evidenced KI-006/007 and must pass final regression before delivery.

- Require pcm_s16le encoding and a connected stream for enqueuing audio.
- Validate AVAILABLE hello status and bounded resume/ACK sequence and timestamp values.
- Fail closed on malformed stream input.
- Cancel outstanding retry/heartbeat on manual reconnect.
- Add actual, documented `PraxisClient.stopStreaming()` to immediately stop transport, clear buffers and cancel peers without blocking the phone thread. App calls this before asynchronous best-effort `endSession`.
- End-session also stops transport before HTTP. A two-second app watchdog closes the client if server cleanup blocks.
- Reject URL fragments as well as credentials/query/non-root paths.

The added stopStreaming method is implemented here, not attributed to the supplied public API. Production app links artifacts/praxis-runtime-release.aar, rebuilt from sdk-runtime. Original artifacts/praxis-release.aar is retained for comparison. No new server API or authentication contract is introduced.
