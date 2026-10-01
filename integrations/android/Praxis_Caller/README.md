# Praxis Caller

Android cellular dialer with an optional Praxis analysis layer. Package: `com.praxis.caller`; Android 10/API29 or newer. Calls use Android Telecom and the device SIM/eSIM. The recipient does not need this app.

## Delivery status

The app implements phone, contacts, recents, call controls, SIM selection, and the optional Praxis SDK/auth/audio/UI pipeline. Final automated results and APK checksum are recorded in `docs/FINAL_ACCEPTANCE.md` and `evidence/phase10/`. No physical phone/SIM/acoustic test has been performed. Successful Android Studio sync remains unobserved. Production Praxis/auth configuration and approval for mixed speaker/microphone audio are missing, so live cloud protection is unavailable in the supplied build.

## Install and run

Use `artifacts/Praxis-Caller-debug.apk` after the final verification checkpoint. This is a debug-signed test build, not a Play Store release.

1. Copy the APK to an Android phone and open it. Allow installation from that source if Android asks. Alternatively use `adb install -r artifacts/Praxis-Caller-debug.apk` with USB debugging enabled.
2. Open Praxis Caller and select **Set as default phone app**. Accept Android's role prompt.
3. Allow Phone and Notifications. Use **Allow / refresh contacts and history** for Contacts and Call logs. Grant phone-state access for the SIM picker; if declined, a subsequent Call tap delegates account selection to Android.
4. Enter a number and tap Call. With multiple enabled accounts, choose the SIM. Contacts and recents fill the keypad draft; confirm by tapping Call.
5. During a call, use Audio to choose an Android-reported output, Mute, Keypad for DTMF, Hold when supported, and End call. Incoming calls expose Answer/Decline.

Actual OEM permission screens, default-dialer behavior, lock-screen incoming calls and SIM controls require the user's phone test. Restore the previous default dialer through Android Settings if needed.

## Build requirements

Android Studio compatible with AGP9.1.1; JDK17; Gradle9.3.1; Android SDK37 and Build Tools37.0.0. Minimum SDK29. The project has a standard Gradle wrapper. Set your SDK directory in ignored `local.properties` and select JDK17 in Studio. Do not generate a `gradle/gradle-daemon-jvm.properties` override selecting another Java version.

```
./gradlew clean assembleDebug test lintDebug
```

For this Windows workspace, run from the repository root:

```powershell
python scripts/verify_app.py --java-home ../../work/tools/jdk17/jdk-17.0.20.1+1 --android-sdk ../../work/android-sdk --gradle-home ../../work/tools/phase1-gradle/gradle-9.3.1 --work-dir ../../work --run-name local-final --phase 10
```

The verifier uses workspace caches and checks the actual daemon/test Java17 runtime. It records logs and JUnit/lint reports. Direct Gradle invocation must also set `GRADLE_USER_HOME` to the workspace cache to avoid the earlier Windows native DLL launcher failure. Cold builds need Internet dependency access.

## SDK integration and provenance

`sdk/` and `vendor/android-sdk/` preserve supplied sources. `sdk-runtime/` is the explicit safety derivative, documented in `docs/SDK_RUNTIME_PATCHES.md`. The app links `artifacts/praxis-runtime-release.aar` with the SDK's real serialization/coroutine/OkHttp dependencies. `PraxisManager` calls actual startSession/onEvent/streamAudio/endSession/close APIs; `stopStreaming` is a documented locally implemented runtime extension. ACK counts are not exposed by the supplied SDK and are shown as unavailable.

Rebuild and test the derivative:

```powershell
python scripts/verify_sdk.py --runtime --java-home ../../work/tools/jdk17/jdk-17.0.20.1+1 --android-sdk ../../work/android-sdk --gradle-home ../../work/tools/gradle/gradle-8.11.1 --work-dir ../../work --run-name runtime-sdk
```

Then copy `sdk-runtime/praxis/build/outputs/aar/praxis-release.aar` to `artifacts/praxis-runtime-release.aar` and rebuild the app. `python scripts/inspect_pack.py` checks original archive/source integrity.

## Praxis configuration

Copy `config/praxis-config.example.json` to `app/src/main/assets/praxis-config.json` and populate only verified values. The actual file is git-ignored. Do not put tokens or client secrets in it. The unconfigured build still permits normal phone calls.

Required: HTTPS root `baseUrl`, `tenantId`, `hostAppId`. None has been supplied. The SDK creates sessions; a session ID alone does not mean a connected stream or successful analysis.

The optional auth adapter implements standard OAuth2 Authorization Code + PKCE. Enable `auth.protocol` as `oauth2-pkce` ONLY after the backend confirms support, and supply its exact HTTPS `authorizeUrl`, `tokenUrl`, public `clientId`, and `scope`. Register `praxis-caller://auth/callback` with that provider. No production auth URL, callback registration or token contract is known. If Praxis uses another contract, its adapter must be implemented from the provided specification before login can work. No secret-based/public-client workaround is present.

Authentication uses random single-use state, S256 PKCE, exact callback matching, bounded token responses, expiry checks, Android Keystore AES-GCM storage and disabled backup. Refresh is not invented: expired credentials require another login. Sign-out stops Praxis and clears credentials. A browser cancellation can be completed using Cancel sign-in in the app.

## Audio and protection

Connect to Praxis during an active call. With a configured backend and valid sign-in, the app waits for an actual SDK connection callback. Microphone streaming requires a separate explicit confirmation and permission; choose Speaker and unmute first. It runs in a private microphone foreground service with a Stop action.

V1 is acoustic speakerphone -> microphone -> AudioRecord -> 16kHz mono PCM16, 20ms/640-byte frames -> actual Praxis SDK. It does not access protected cellular downlink or create audio files. Android/OEM restrictions can deny or silence recording during calls; physical validation is mandatory. The SDK describes remote-only input, while this source may mix both people and background sounds. `acousticInputApproved` defaults false and must remain false until the backend/model owner confirms suitability. This is an unresolved input contract, not a software bypass.

Capture stops on call end/hold, conflicting active calls, route change away from speaker, mute, permission loss, expired credentials, SDK disconnect/error, or explicit stop. Re-enabling is explicit. SDK transport is stopped immediately before best-effort HTTP session cleanup, with bounded buffers and a two-second shutdown watchdog. Normal Telecom calls have no dependency on Praxis success.

## UI and results

Dark phone-first Compose UI based on the supplied reference. Separate voice and analysis visuals reflect actual streaming/events. Missing analysis is neutral/unavailable, never zero risk. Real SDK policy decisions reveal text and request a short original sound once. Sound delivery, Bluetooth/OEM routing and visual behavior on devices remain untested. Local test fixtures and host-rendered images are synthetic verification only.

## Audits and handoff

Read MASTER_PROMPT.md, AI_CONTEXT.md, AI_MEMORY.md, PROJECT_STATUS.md, DECISIONS.md, KNOWN_ISSUES.md, HANDOFF.md, then docs/. D-015 records the user's instruction to defer the remaining audits/tests until after implementation. See `docs/SECURITY_AUDIT.md`, `docs/FINAL_ACCEPTANCE.md` and TEST_LOG.md for actual results and external blockers. Physical tests must not be marked PASS until the user performs them and supplies results.
