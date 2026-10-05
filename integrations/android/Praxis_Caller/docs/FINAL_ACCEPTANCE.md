# Final acceptance and delivery - 2026-09-29

Installable test APK: `artifacts/Praxis-Caller-debug.apk` (29,539,845 bytes). SHA256 `0ac4d47d15a844a46afb2cb0eec04fb7509ae3c5c4c76e87496f885824e03658`. Debug signature verifies (v2); package com.praxis.caller, min29, target37. This APK supersedes earlier phase APKs.

**All locally runnable final checks PASS. Overall product acceptance remains BLOCKED by external prerequisites.** No live backend, real login, physical SIM call, hardware AudioRecord path, actual phone sound/routing or Android Studio successful sync is claimed. Work through Phase10 has been implemented and audited to the extent possible with those dependencies isolated. D-015 defers phase tests to this combined final regression at the user's request.

## Final evidence

- `phase10/final-delivery`: clean assembleDebug/test/lintDebug, exit0, actual JDK17; 36 tests, zero failures/errors/skips; lint0 errors/31 warnings.
- `final-runtime-sdk-repair`: eight tests (five supplied plus three adversarial), clean release AAR/lint PASS. A test-peer close-handshake teardown failure was repaired; no assertion disabled.
- `phase4-supplied-sdk`: pristine five tests/build/lint PASS.
- `input-verification.json`: full archive/vendor/source/fixture integrity PASS.
- `apk-signature.txt` and `apk-badging.txt`: package/platform/signature evidence. Merged manifest audit is separate.
- `evidence/ui-host`: phone/call images and explicitly synthetic orb fixture image. Host rendering only. Caption contrast was corrected in test harness with a targeted render rerun; no production source changed after final-delivery.

## Phase gates

| Phase | State at handoff |
| --- | --- |
| 0 | PASS - original SDK truth/provenance verified |
| 1 | CLI/skeleton checks PASS; Studio sync remains externally BLOCKED (KI-011) |
| 2 | PASS with physical Telecom checks queued |
| 3 | PASS with physical phone/SIM/OEM checks queued |
| 4 | PASS - actual SDK integration/API/host tests |
| 5 | Architecture implemented and host/static checks pass; live auth BLOCKED on actual backend contract/config |
| 6 | Capture/cleanup code and host checks pass; input agreement and physical acoustic path BLOCKED |
| 7 | Real SDK loopback path and failure-isolation checks pass; production end-to-end path BLOCKED by phases5/6 inputs |
| 8 | Host visual/state/gradient/sound-dedup checks PASS; real sound/device UX queued |
| 9 | Locally fixable findings repaired/retested; external restrictions explicitly retained |
| 10 | Available final regression, audits and handoff complete; overall gate BLOCKED by external acceptance items below |

## Acceptance matrix

| # | Requirement | Host/code evidence | Remaining real-world validation |
| --- | --- | --- | --- |
| 1 | Install/default dialer | Signed APK; RoleManager tests | PHYSICAL TEST REQUIRED |
| 2 | Outgoing SIM call | Telecom request/permission/account tests | PHYSICAL TEST REQUIRED |
| 3 | Incoming SIM call | InCallService state/notification code | PHYSICAL TEST REQUIRED |
| 4 | Answer/end | Callback and stale-action guards tested | PHYSICAL TEST REQUIRED |
| 5 | Speaker/mute/DTMF | Endpoint state callback test; tone bounds/cleanup test | PHYSICAL TEST REQUIRED |
| 6 | Dual SIM | Available-account picker and membership guards | PHYSICAL TEST REQUIRED |
| 7 | Contacts/photos | Provider IO, denied access test, bounded photo decode | PHYSICAL TEST REQUIRED |
| 8 | Recents | Provider query, presentation filtering, draft selection | PHYSICAL TEST REQUIRED |
| 9 | Calls without Praxis | No cloud dependency in Telecom; unavailable UI render | PHYSICAL TEST REQUIRED |
| 10 | Praxis connect/auth | Real client path; PKCE/callback/storage architecture | BLOCKED - backend contract/config + device Keystore |
| 11 | Praxis failure isolation | Adapter failure tests; no cloud code invokes Call.disconnect | PHYSICAL TEST REQUIRED |
| 12 | Capture authorized active call only | CapturePolicy negative-path matrix | PHYSICAL TEST REQUIRED; input approval absent |
| 13 | PCM reaches actual SDK | Real SDK loopback wire test with synthetic PCM | Physical microphone path pending |
| 14 | Real SDK events update UI state | Actual wire decode into manager; call/epoch filtering | Live production results BLOCKED |
| 15 | Risk gradient | Continuous endpoint/interpolation test; host render | Device visual check pending |
| 16 | Decision sound once | Bounded dedup test; generated chime/release source | Physical sound delivery pending |
| 17 | Orb shift/text reveal | Separate composables, animated size/reveal, host fixture | Device animation check pending |
| 18 | End releases resources/session | Capture lifecycle tests; stop-before-end SDK test; actual end REST in loopback | Device/network failure validation pending |
| 19 | Reopen/lifecycle recovery | Activity draft recreation; service references cleaned; no fake calls restored | Process kill/rebind PHYSICAL TEST REQUIRED |
| 20 | No orphaned mic | Finally release, mutex ownership, epoch/nonsticky service; cancellation tests | Device background/task-removal checks pending |

## Required external inputs

Production HTTPS base URL, tenantId, hostAppId; verified browser authentication contract/endpoints/public client registration and callback; backend owner agreement for acoustic mixed input. The optional OAuth2-PKCE adapter is an implementation option, not an assertion of backend support. Do not enable acousticInputApproved without that agreement.

The user must perform physical tests and report results. No emergency call is part of the test plan; use an ordinary consenting test contact. Hardware features unavailable on a given phone must be recorded rather than assumed to work.

## KI-019 repair checkpoint - 2026-09-29
ADB verified default dialer role and repeated fatal CallStyle notification rejection in CallNotifications.update. Replaced unsupported ongoing CallStyle with standard ongoing category-CALL notification and End action; incoming CallStyle requires allowed full-screen intent. Notification rejection is contained with plain fallback. Clean ki019-notification-fix build/test/lint PASS, 37 tests, signature verified. Updated artifacts/Praxis-Caller-debug.apk SHA256 e6896624d194462782331526d90eedb694dbec9e9c79a096267ab62d64b00e84. ADB install -r SUCCESS on user phone. Physical call retest PENDING; do not mark issue resolved until user reports result. Previous 36-test/checksum records describe the prior build. Live Praxis backend/input blockers unchanged.
