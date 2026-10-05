# Praxis Caller — Decision Log

## D-012 — Continued phases authorized; actual JVM evidence required
**Date:** 2026-09-28
**Status:** Current; supersedes D-010/D-011 statements that later phases are unauthorized.
User explicitly authorized completing phases sequentially with the deadline constraint. Preserve all acceptance criteria and external blockers. Remove Studio-generated Java25 daemon criteria and verify actual daemon/test JVM17 rather than relying on JAVA_HOME metadata. Repair validation is pending due to shell sandbox startup failure (KI-015). No successful Studio sync or physical-device functionality is inferred.

Use one entry per architectural/product decision.

## D-001 — Real cellular dialer
**Status:** Locked  
**Decision:** Use Android Telecom and SIM/eSIM cellular calling. Praxis Caller is not a VoIP/WebRTC dialer.  
**Reason:** Product requirement.

## D-002 — Praxis is optional
**Status:** Locked  
**Decision:** Telephony is independent of Praxis cloud/SDK availability.  
**Reason:** Calling must remain reliable when security analysis is unavailable.

## D-003 — V1 audio acquisition
**Status:** Locked for V1  
**Decision:** Use speakerphone -> microphone -> AudioRecord as the practical V1 audio source, behind `CallAudioSource`.  
**Reason:** Normal third-party Android applications face restrictions on direct cellular downlink capture. The abstraction preserves a future legitimate direct source.

## D-004 — Server-side analysis windowing
**Status:** Locked  
**Decision:** Send small continuous PCM frames through the SDK; keep 4 s / 2 s analysis windowing on the Praxis server.  
**Reason:** Avoid duplicated ML preprocessing and keep model behavior authoritative server-side.

## D-005 — Two-orb interaction
**Status:** Locked  
**Decision:** Maintain separate voice/audio-flow and analysis/decision orb concepts.  
**Reason:** User-approved UI flow.

## D-006 — Risk color semantics
**Status:** Locked  
**Decision:** Low risk = green; increasing AI/suspicion risk moves continuously through yellow/amber/orange to red.  
**Reason:** User-approved UI semantics.

## New decision template
### D-XXX — Title
**Date:**  
**Status:** Proposed / Locked / Superseded  
**Decision:**  
**Evidence/source:**  
**Reason:**  
**Consequences:**  
**Supersedes:**

## D-007 — Preserve supplied SDK and separate build workspace
**Date:** 2026-09-23  
**Status:** Adopted for Phase 0  
**Decision:** Keep the complete extraction under vendor/android-sdk and a byte-identical source-only build copy under sdk. Restore missing test resources from the supplied generated copies with SHA-256 provenance; use workspace-local JDK 17/Gradle/Android tooling. Do not rewrite SDK runtime in this truth-establishment phase.  
**Evidence:** evidence/input-verification.json; scripts/inspect_pack.py.  
**Reason:** Enables fresh independent checks without confusing old caches/results with new evidence. Supplied source risks remain explicit dependencies before affected integration phases.

## D-008 — Distinguish product intent, SDK source and server evidence
**Date:** 2026-09-23  
**Status:** Adopted  
**Decision:** D-004 specifies desired server windowing, not a verified server implementation. README login path is not an established browser-auth contract. SDK remote-only intent is not proof V1 mixed acoustic input has appropriate model behavior. Proposed host classes remain distinct from SDK types.  
**Evidence:** PraxisClient.kt, Contracts.kt, SDK README; docs/PRAXIS_INTEGRATION.md.  
**Consequences:** Keep production auth, input semantics and physical acoustic/model validation explicit. No requirements are weakened.

## D-009 — Scope stop at Phase 0
**Date:** 2026-09-23  
**Status:** Locked by current user request  
**Decision:** Complete Phase 0 audit/checkpoint only. Do not auto-advance to Phase 1, even if Phase 0 passes.  
**Evidence:** User request; MASTER_PROMPT.md Phase 0 gate. The supplied UI file was explicitly located by the user and is preserved under references/.

## D-010 — Phase 1 authorized
**Date:** 2026-09-24
**Status:** Current; supersedes D-009's stop boundary for this task.
**Decision:** User explicitly requested Phase 1. Implement Android skeleton only, audit/checkpoint, then stop before Phase 2. Phase 0 remains complete.

## D-011 — Phase 1 app toolchain and test boundary (2026-09-24)
Root :app uses AGP9.1.1, Gradle9.3.1, built-in Kotlin/Compose compiler2.2.10, JDK17 and stable API37/BuildTools37.0.0, min29. The supplied sdk/ independent build remains unchanged and is not yet linked. Source/platform compatibility evidence is in docs/PHASE_1_AUDIT.md. UI state is StateFlow/SavedStateHandle with lifecycle-aware Compose observation; it is not telephony state.

The MASTER gate requiring an Android Studio opening remains literal. Tooling API model validation is supporting evidence only; absent observed Studio opening must remain BLOCKED. Physical phone testing remains separate. Phase 2 is not authorized by the current request.

## D-013 — Continue with isolated external Studio blocker
2026-09-28: Follow MASTER_PROMPT section2 after verified repair/re-audit. Keep Phase1 gate BLOCKED on KI-011 and continue sequential implementation; no invented sync result. Prior stricter continuation interpretation is superseded.

## D-014 - Finish code before hardware (2026-09-29)
User explicitly requests all finishable work through Phase10 today, before phone connection. Continue phases in order after each code gate; queue physical-only tests per MASTER_PROMPT. SDK source remains authoritative; missing production configuration cannot become fabricated success.

## D-015 - User-directed implementation-first order (2026-09-29)
User explicitly requests remaining tests/audits at the end and app implementation first. This supersedes per-phase test timing, not acceptance standards. Implement remaining phases sequentially, compile as needed, then run all available tests/audits. No unverified phase marked PASS. External dependencies stay blocked.
