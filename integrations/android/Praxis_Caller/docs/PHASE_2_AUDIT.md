# Phase 2 acceptance — defined before implementation

1. RoleManager requests the actual default dialer role; denial/unavailability is visible and never counted as success.
2. Manifest exposes ACTION_DIAL (empty and tel URI) and a BIND_INCALL_SERVICE-protected InCallService with UI metadata.
3. Explicit user call action validates input/role/CALL_PHONE then uses TelecomManager.placeCall; external dial intents only fill a draft.
4. UI observes actual Call callbacks; callback removal, service destruction and stale action handling clear references. No invented dialing/active states.
5. Minimal active-call screen and disconnect work through Call; basic incoming answer/reject and notifications needed for a coherent role implementation are included. Comprehensive telephony is Phase3.
6. Host tests verify permission/role failures, draft intent safety, callback lifecycle/state and command dispatch. They do not certify SIM calls.
7. Build/test/lint, audit, repair, rebuild/retest/re-audit must finish. Physical role/call/notification tests queued explicitly.

Inherited external blocker: Phase1 Studio open/sync unverified (KI-011). Continued under MASTER_PROMPT section2 after completed Phase1 audit, not a waived gate.

Source: https://developer.android.com/reference/android/telecom/InCallService
Status: IMPLEMENTING; no Phase2 pass claimed.

Initial phase2-build compiled/assembled but failed 2 of 13 tests. Invalid characters were stripped to a different number (fixed by raw allowlist before formatting); unavailable-role test tried removing a role absent from its shadow (removed invalid setup). Added separate notification permission entry and gated incoming full-screen notification plus lock-screen visibility. Rebuild pending. Initial evidence is under evidence/phase1/phase2-build* because the verifier originally fixed the folder; subsequent runs use --phase 2.

## Final re-audit
## Phase2 checkpoint — 2026-09-28
Phase2 IMPLEMENT/BUILD/TEST/AUDIT/FIX/REBUILD/RETEST/RE-AUDIT complete. phase2-final clean assembleDebug/test/lint exits0 on actual JDK17; 13 tests pass without skipped tests; final lint0 errors/1 KTX suggestion (the prior rebuild also reported dependency advisories). Initial invalid-number bug and test setup failure fixed without weakening assertions. APK artifacts/praxis-caller-phase2-debug.apk has Telecom foundation, role/permission flows, basic incoming controls and call notification entry. No device installation/SIM tests performed. Phase2 gate PASS under its explicit physical-test queue; inherited Phase1 Studio gate still BLOCKED (KI-011), carried under MASTER_PROMPT section2. Phase3 is next, not implemented at this checkpoint. Praxis integration still unavailable.

Source audit: one placeCall path guarded by role/permission/raw validation; no call state synthesized from commands; private immutable notification actions reject stale IDs; callback/service cleanup drops references. No network/audio capture dependency exists. Compiled APK signature v2 verified during repaired run; final APK checksum in phase2-summary.json. Phase2-final removes unused resources and preserves portable wrapper.
