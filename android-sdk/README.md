# Praxis Kotlin SDK

This Android library receives authorized remote-caller PCM from its host. It does not capture a microphone, establish calls, signal WebRTC, present a UI, or implement fraud decisions.

Build on Windows from the project root:

```powershell
.\.venv\Scripts\python.exe scripts/bootstrap_android.py
.\.venv\Scripts\python.exe scripts/export_contracts.py
.\.venv\Scripts\python.exe scripts/generate_kotlin_contracts.py
.\scripts\build-sdk.ps1 -JavaHome 'C:\path\to\compatible-jdk'
```

The checks run JVM unit tests, Android lint and release AAR assembly. Build files pin Android Gradle Plugin 8.9.2, Gradle 8.11.1, Kotlin 2.1.20 and compile SDK 35. JDK 17–23 can run this Gradle release; the current build uses the existing JDK 22. Tool downloads/cache remain under this project. APKs and calling applications are outside scope.

```kotlin
val client = PraxisClient(PraxisConfig(
    baseUrl = "https://your-authorized-praxis-host/",
    tenantId = organizationId,
    hostAppId = authorizedHostAppId,
    tokenProvider = { secureTokenStore.currentAccessToken() }
))
client.onRiskUpdate { event -> /* host presents real validated risk when available */ }
client.onPolicyAction { event -> /* host implements its approved action workflow */ }
client.onEvent { event -> /* handle evidence, unavailable states, gaps and errors */ }
val sessionId = client.startSession(callId, suppliedContext)
client.streamAudio(sessionId, authorizedRemotePcm, monotonicCallTimestampMs,
    AudioFormat(sampleRate = 16000, channels = 1))
client.updateContext(sessionId, contextPatch)
client.endSession(sessionId)
client.close()
```

`startSession`, `updateContext` and `endSession` are suspend functions. The host obtains the JWT from `/api/v1/auth/login`, stores it securely, and supplies refreshed tokens through `tokenProvider`; the SDK never persists credentials. Authentication rejection stops automatic reconnect. Refresh the token and call `reconnect()` explicitly when appropriate.

The host supplies only authorized decoded remote audio. Frames are little-endian signed 16-bit PCM, at most one second, in one/two channels and a supported native sample rate. Timestamps use a single increasing call timeline. SDK sequence IDs survive reconnects; the server reports its last accepted ID so accepted audio is not replayed after lost acknowledgments. Audio is kept only in bounded memory (100 frames/384 KB defaults), with explicit gap events on overflow. Reconnect backs off to 30 seconds and stops after eight failed attempts. Call `endSession` before `close` to finalize server state.

Callbacks are dispatched sequentially and must return promptly. The SDK bounds callback backlog and closes the stream with an explicit error when the host cannot keep up. It never maps unavailable evidence to zero risk or chooses a policy action itself. Unknown/invalid event contracts produce an error. TLS verification is mandatory; the cleartext test option is restricted to loopback hosts.

Canonical types are generated from `contracts/schemas`; shared examples are consumed by JVM tests. Use the `JsonObject` context overload when explicitly clearing a previously supplied fact with JSON null. Device integration and real two-party calling validation are not claimed by these JVM/AAR checks.
