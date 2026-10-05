## Current implementation - 2026-09-29

Current architecture: CallerApplication owns CallManager, PraxisManager, auth, capture status and application scope. InCallService alone owns Telecom Call references. CaptureService owns lifecycle-bound microphone source on IO, sharing CapturePolicy; it calls PraxisManager via SdkPort. Auth owns encrypted storage and exact callback exchange. UI observes StateFlows. No cloud/audio component issues a Telecom disconnect. See PHASE_4_AUDIT through PHASE_8_AUDIT. Historical skeleton notes below are not current state.

---

# Architecture

## Top-level separation
1. Telephony domain — Android Telecom and real SIM/eSIM calling.
2. Praxis domain — optional cloud analysis through supplied SDK.
3. Audio domain — authorized audio source abstraction feeding Praxis.
4. Data domain — contacts and call logs.
5. UI domain — phone UI plus Praxis status/analysis visualization.

## Suggested packages
`com.praxis.caller.telecom`
`com.praxis.caller.audio`
`com.praxis.caller.praxis`
`com.praxis.caller.data`
`com.praxis.caller.ui`

## Critical dependency direction
UI -> application managers/state
PraxisManager -> supplied Praxis SDK
PraxisManager -> CallAudioSource abstraction
Telephony must not depend on successful Praxis operation.

Update this document with concrete classes and diagrams after implementation.

## Phase 0 historical repository
Only the supplied standalone SDK exists: `sdk/:praxis`, namespace `io.praxis.sdk`; no `com.praxis.caller` app yet. Names above are planned host packages/classes, not existing implementation or SDK APIs. `vendor/android-sdk` is an immutable supplied snapshot; `sdk` is the independent build copy; `contracts/examples` contains recovered test resources. `PraxisClient` owns HTTP/WebSocket and bounded pending audio, not phone/capture/auth UI. App adapter must enforce lifecycle/consent, map callbacks to app state, discard stale events and protect Telecom from exceptions.

## Phase 1 implemented skeleton
Root Gradle project owns `:app`, applicationId/namespace `com.praxis.caller`. The independent `sdk/` build remains separate and unchanged; it is not a runtime dependency until Phase 4.

`MainActivity` hosts Compose `CallerApp`. `CallerViewModel` owns immutable `CallerUiState` through StateFlow; `SavedStateHandle` persists destination, phone tab and bounded draft number. Compose observes with `collectAsStateWithLifecycle`. Navigation is a small enum-based destination switch; Android Back returns from Call/Praxis to Phone. No fictitious call or connection objects exist.

`ui/phone` renders empty Recents/Contacts and a draft-only keypad. `ui/call` and `ui/praxis` render unavailable controls. All actual call/end/connect actions are disabled. Domain directories telecom/audio/praxis/auth/data contain explicit reservation notes, not implemented services. Future domain state must derive from actual Telecom/SDK callbacks rather than reusing navigation state as operational state.

Host tests cover navigation, draft bounds, restored state and Activity recreation. This does not establish physical calls, full process-death recovery or API 37 device behavior.

## Phase2 update
CallerApplication owns main-thread CallManager. PraxisInCallService owns the Android Call identity map and subscriptions. AndroidCallPort isolates Android command/callback plumbing; test ports exist only in host tests. UI collects immutable call snapshots with lifecycle-aware Flow. MainActivity holds role/permission launchers and handles safe draft-only ACTION_DIAL. No telephony state is saved as a fake live call after process recreation.
