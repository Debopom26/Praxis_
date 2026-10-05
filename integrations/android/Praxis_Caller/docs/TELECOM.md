## Current implementation - 2026-09-29

Current Phase3 code is complete and host-verified: endpoint/mute callbacks, API34 routing plus legacy fallback, bounded DTMF, canHold capability, outgoing/in-call account selection, contacts/photos/search, private-aware recents and duration. Physical checks remain queued. See PHASE_3_AUDIT.md. Historical phase notes follow.

---

# Telecom Implementation Notes

Required:
- request default dialer role
- implement `InCallService`
- use `TelecomManager` for real calls
- observe real `Call` states
- support incoming/outgoing lifecycle
- support call controls
- handle available `PhoneAccountHandle`s for dual SIM

Do not fake call state.

Document manifest declarations, role flow, permissions, call-state mapping, audio-route behavior and device-specific limitations as they are implemented.

## Phase2 implementation
Manifest declares CALL_PHONE, POST_NOTIFICATIONS and USE_FULL_SCREEN_INTENT, ACTION_DIAL filters (without data and with tel), and an exported InCallService protected by system BIND_INCALL_SERVICE. IN_CALL_SERVICE_UI=true; platform ringtone is retained. A private action receiver handles immutable notification actions.

Dial intents only set a validated draft. An explicit Call tap checks current role and permission before TelecomManager.placeCall; success means request submitted, never active call. CallManager state is populated only by Call snapshots/callbacks. No number is placed in notification text or diagnostic logs. Number presentation restrictions hide private handles. Answer/reject/end commands reject removed/ended calls; callback subscriptions are removed on service cleanup. Multiple Call objects remain distinct.

Incoming notifications use CallStyle from API31, actions below31, full-screen intent only when allowed on34+, and lock-screen visibility only for actual calls. Notification denial has a user-visible permission entry. Physical incoming foreground/background/locked behavior remains untested.

Source: https://developer.android.com/reference/android/telecom/InCallService
Comprehensive audio routing, DTMF, contacts, recents and dual-SIM UI remain Phase3.
