# Current known issues - 2026-09-29

## Physical-call finding - 2026-10-02
On the connected Samsung test phone, Android's audio service reported `src:MIC silenced pack:com.praxis.caller` throughout an active cellular call, despite the app holding the default dialer role, the speaker route being selected, and a separate speaker playing test audio beside the phone. Praxis received all-zero microphone windows and cannot produce a valid live score from them. Restarting `AudioRecord` every few seconds did not restore audio. The app now keeps the microphone-unavailable explanation visible instead of alternating it with generic audio-event text. A different permitted audio source/device or a controlled non-cellular capture path is required for a live-audio demonstration; no score should be fabricated.

## External blockers
- KI-004: production origin/tenant/hostAppId/auth contract/client registration/credentials absent. Generic PKCE adapter is disabled until actual backend agreement/configuration; no auth success claimed.
- KI-005: SDK remote-only input intent versus V1 acoustic mixed input remains unresolved with backend/model owner. Capture is implemented but disabled by acousticInputApproved=false. No claim of model quality or remote isolation.
- KI-011: actual successful Android Studio sync remains unobserved. CLI/model/build results cannot close it.
- KI-016: every physical phone/SIM/OEM/Keystore/microphone/Bluetooth/sound test remains unperformed. Device recording may be silenced or unavailable during a SIM call.
- KI-009: canonical contract generator/schema sources absent. Do not regenerate supplied contracts from guesses.

## Nonblocking limitations
- Debug-signed APK only; no store/release signing credentials configured.
- Backend token refresh contract absent; expired credentials require login again. Sign-out/session end does not invent a server revocation endpoint.
- Server session cleanup is best effort with bounded timeout; process/network failure can require backend expiry/retention handling.
- Call history shows newest100 records; contacts query loads phone entries on IO. Notification/full-screen permissions and Android/OEM policy govern incoming UI behavior.
- Sound and real UX/large-font/device-size accessibility require hardware review; host screenshots are synthetic.
- Lint31 warnings (largely dependency/resource/style advisories), SDK XML/analytics and debug-native-stripping warnings remain visible. No lint errors or suppressed failing tests.

## Resolved implementation findings
KI-006/007 SDK stream/protocol/lifecycle findings are fixed for app use in sdk-runtime, documented in SDK_RUNTIME_PATCHES.md and retested (8 SDK tests). Original source intentionally remains unchanged. App enforces call/epoch/time filtering and bounded dedup.
KI-017/018 Phase3 code gaps are resolved: real endpoint/mute callbacks, API34 routes/legacy fallback, bounded DTMF, SIM selection, contacts/photos/recents/duration. Host gate passes; physical queue remains.
Capture uses serialized recorder ownership, per-service epoch/live guards and finally cleanup; five lifecycle tests pass. UI contrast and host render capture defects repaired.

Prior full issue history is under docs/history/pre-final-2026-09-29/KNOWN_ISSUES.md. Current results: docs/FINAL_ACCEPTANCE.md.

## User phone observation - 2026-09-29
User reports that starting a call from Praxis opens the normal phone app and calls there. This is an unresolved device observation, not a successful in-app call test. Phone model, Android version, installed APK version, default Phone role, and InCallService binding/crash logs are not yet available. Current source requires the role before Telecom.placeCall and implements its own call UI; cause is not established. Track as KI-019. No physical score/auth/audio success was reported.


KI-019 clarification: user confirms Praxis Caller IS the default Phone app. Its keypad stays open until call placement, then the stock ongoing-call UI takes over. Default-role misconfiguration is not an established cause. ADB devices inspection found no connected device. Need phone model/Android version, installed APK identity and scoped Telecom/app crash evidence before attributing cause or marking fixed.


KI-019 device update: user supplied About phone image identifying Samsung Galaxy A37 5G, model SM-A376E/DS, and reports Android 16. Do not copy phone number, serial, or IMEI from the image into diagnostic records. Stock ongoing-call UI takeover remains unresolved; default Phone role confirmed by user.


KI-019 diagnosis: ADB confirms com.praxis.caller holds ROLE_DIALER. Device crash buffer shows repeated IllegalArgumentException at CallNotifications.update: CallStyle notifications require foreground service/user-initiated job/fullScreenIntent. Outgoing notifications lacked these, crashing onCallAdded. Patch uses standard actionable ongoing-call notifications, reserves CallStyle for eligible incoming full-screen notifications, and contains notification rejection. Regression/build pending; physical retest remains REQUIRED.


## KI-019 repair checkpoint - 2026-09-29
ADB verified default dialer role and repeated fatal CallStyle notification rejection in CallNotifications.update. Replaced unsupported ongoing CallStyle with standard ongoing category-CALL notification and End action; incoming CallStyle requires allowed full-screen intent. Notification rejection is contained with plain fallback. Clean ki019-notification-fix build/test/lint PASS, 37 tests, signature verified. Updated artifacts/Praxis-Caller-debug.apk SHA256 e6896624d194462782331526d90eedb694dbec9e9c79a096267ab62d64b00e84. ADB install -r SUCCESS on user phone. Physical call retest PENDING; do not mark issue resolved until user reports result. Previous 36-test/checksum records describe the prior build. Live Praxis backend/input blockers unchanged.
