# Remaining acceptance, defined before implementation (2026-09-29)

Follow MASTER_PROMPT phases 3 through 10 in order. This document adds checks, not exemptions. Every phase receives a build/test/audit and repair/rebuild/retest/re-audit checkpoint before advancement. User explicitly requests finishing all possible code before phone testing.

| Phase | Acceptance evidence required |
| --- | --- |
| 3 | Authoritative Telecom state, valid account membership, API34 endpoints plus legacy routes, bounded/stopped DTMF, guarded permissions/providers, photos/search/dialable recents, lifecycle cleanup; host tests and clean lint/build. Physical SIM/OEM checks queued. |
| 4 | Actual supplied SDK binary/source provenance, initialization/configuration, serialized session lifecycle, subscription cleanup, honest connection/error state, stale callback rejection; adapter tests and supplied SDK tests. |
| 5 | Explicit external configuration, secure token persistence, expiry/cancel/invalid callback handling, no token logging, no invented backend exchange. Missing production auth contract is BLOCKED, with usable phone independent. |
| 6 | AudioRecord ownership off main, bounded PCM frames, stop/release under cancellation/call end/disconnect/permission failure, no public audio storage; acoustic input contract conflict remains external and capture must not pretend compatibility. |
| 7 | Real call -> capture -> actual SDK -> actual events with epoch/call filtering and bounded deduplication; missing/malformed/late events and network failure do not become safe scores or affect calls. |
| 8 | Inspected reference, distinct audio/analysis orbs, real-state-only transitions, continuous risk gradient, once-per-new-decision sound, persistent result reveal, usable phone controls. |
| 9 | Adversarial audit table with severity/evidence/fix/retest. Fix every locally resolvable critical/high issue; name remaining external constraints. |
| 10 | Fresh clean build/tests/lint, SDK tests, static architecture/security/UI checks, APK hash, truthful acceptance matrix, complete README/control files and exact configuration/install steps. |

No network credentials, backend success, phone behavior, or analysis quality may be inferred from mock tests. Physical device tests are unperformed until the user supplies results. Phase1 Studio sync remains an inherited external check.
