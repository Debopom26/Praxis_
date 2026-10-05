# Phase 1 — Android skeleton audit

## Current checkpoint — 2026-09-28, JDK17 repair verified
Phase1 implementation/build/test/re-audit PASS after removal of Java25 criteria. phase1-jdk17-repair exits0: actual daemon17.0.20.1, six tests with zero failures/errors/skips, lint completes; original SDK/archive/fixtures integrity PASS. Shell execution works again (KI-015 no longer reproduced). Studio GUI/sync remains BLOCKED: native launch returned no targetable window and stopping the identified stalled process was denied. No physical tests performed.

MASTER_PROMPT section2 explicitly permits continuing with an isolated external blocker. Earlier blanket statements forbidding any further work until Studio sync were overly restrictive. Phase1 audit is complete with gate BLOCKED on that external requirement; it is NOT relabeled PASS. User authorized all phases. Proceed to Phase2 in order while carrying KI-011 and the incomplete IDE check in every checkpoint. No missing requirement is waived.


## Current re-audit — 2026-09-28
**Gate BLOCKED; repair validation NOT RUN.** Removed a Studio-generated Java25 daemon override and strengthened verify_app.py to assert actual daemon/test JVM17. Earlier passing logs remain historical; JAVA_HOME metadata alone does not certify the daemon. APK/signature/integrity checks are separate from verify_app.py, contrary to some earlier prose.

exec_command now refuses the granted split-writable-root sandbox profile, including read-only git status. Native sky currently returns no Studio window after launch. No successful sync is inferred. See PHASE_1_RECOVERY.md. Older privacy/setup descriptions and authorization boundaries below are historical and superseded by current HANDOFF.

Latest follow-up 2026-09-27: Studio installation and native automation availability resolved. Official archive checksum matches; a real Studio window now shows the first-run usage-statistics privacy choice. The user must choose their preference before project opening/sync can be observed. Gate remains BLOCKED, not PASS. evidence/phase1/studio-visible-setup.json and latest HANDOFF record the exact resume point. No automated build evidence has been substituted for observed sync.

Authorized by user 2026-09-24. Phase 0 remains PASS at d6925ea. Current scope stops before Phase 2. Acceptance was recorded in PROJECT_STATUS before application code.

## Acceptance
- Root Gradle Android application: com.praxis.caller, Kotlin/Compose, JDK17, minSdk29, stable supported compile/target SDK.
- Minimal navigation, lifecycle-aware state, honest unavailable Phone/Call/Praxis placeholders; no simulated Telecom/auth/results or later-phase integration.
- clean / assembleDebug / test succeed with no missing resources/manifest compile errors; lint and APK metadata inspected.
- Meaningful executable state/navigation/restoration tests; distinguish host simulation from physical testing. Validate actual IDE-facing model and disclose GUI import coverage.
- IMPLEMENT → BUILD → TEST → AUDIT → FIX → REBUILD → RETEST → RE-AUDIT, preserve failures, update controls/checkpoint.

## Initial implementation
Root :app is separate from original sdk/:praxis. AGP9.1.1 with built-in Kotlin2.2.10, Compose compiler2.2.10, Gradle9.3.1, JDK17. SDK platform android-37.0 revision2 reports PreviewSdkInt=0/no codename; compile/target37, min29; BuildTools37.0.0. Compose BOM2025.08.01, Activity1.10.1 and Lifecycle2.9.1 are pinned stable dependencies compatible with this Kotlin baseline; using the current Android platform does not require upgrading every library to the newest release.

Sources for compatibility: [AGP9.1.1](https://developer.android.com/build/releases/agp-9-1-0-release-notes), [API37 minimum tooling](https://developer.android.com/build/releases/about-agp), [Android17 setup](https://developer.android.com/about/versions/17/setup-sdk), [built-in Kotlin](https://developer.android.com/build/migrate-to-built-in-kotlin), [lifecycle-aware Compose state](https://developer.android.com/develop/ui/compose/state). Installed source.properties/package.xml provide final stable SDK package evidence rather than assuming from a filename.

Single launcher Activity; Material3 dark base with scrollable content/insets. CallerViewModel owns navigation/draft via StateFlow and SavedStateHandle; UI observes with collectAsStateWithLifecycle. Navigation returns to Phone on Back from auxiliary tabs. Keypad edits a bounded draft only. Calling/connect/end actions disabled; no contacts/recents queried. No SDK dependency, call service, permission requests, network or audio functionality added. Domain package README markers reserve later implementation; they are not working managers.

## Run log
- First SDK install requested nonexistent platforms;android-37. Correct package platforms;android-37.0 installed with stable metadata. Evidence: sdk-install.log and sdk-install-retry.log.
- Official Gradle9.3.1 download SHA-256 verified; evidence/phase1/gradle-download.json.
- build-first failed Kotlin compilation: experimental SecondaryTabRow usage without opt-in. Replaced with stable selectable Row/Tab navigation; no diagnostic suppressed.
- build-second compiled but failed signing: manually overridden debug-keystore location was not auto-created by AGP. Removed override; standard AGP debug signing uses configured ANDROID_USER_HOME. No private signing key is packaged.
- build-third assembled debug APK and ran four state tests successfully. Robolectric class initialization failed before UI tests because it could not create artifact staging directories under machine Temp. Test JVM temporary directory now explicitly uses workspace .local/test-temp, created before tests; tests and assertions unchanged.
- Packaged APK inspected: com.praxis.caller, min29/target37, launcher MainActivity; no INTERNET/CALL_PHONE/RECORD_AUDIO permission. AndroidX contributes a signature-only dynamic receiver permission, nonexported startup provider and exported profile receiver protected by android.permission.DUMP. Debug tooling contributes exported PreviewActivity. These are dependency components, not Telecom/audio services. Standard debug APK v2 signature verifies.

## IDE gate boundary
The original MASTER_PROMPT gate requires the project to open as a coherent Android Studio project. Actual AGP Tooling API model checks provide partial evidence, not a substitute for an observed IDE opening. No Studio executable exists in the three usual installation/Toolbox paths inspected (studio-availability.json); this session's native-app automation surface is disabled. Therefore the actual Studio opening must remain BLOCKED unless independently verified. Do not relabel that check PASS based only on CLI compilation/model retrieval.

## Repair and re-audit completion
- build-fourth reproduced Maven staging failure even in workspace temp. Build-fifth used the exact API35 instrumented runtime resolved through Gradle and Robolectric offline resolver; all six tests passed. This resolves dependency acquisition, not by faking Android APIs or changing assertions.
- build-fifth lint found an unescaped drive colon in ignored local.properties and a backup-rules warning. Escaped the property; added explicit cloud/device-transfer exclusions for all nine documented storage domains, fullBackupContent=false and dataExtractionRules. Primary reference: [Android Auto Backup](https://developer.android.com/identity/data/autobackup).
- Final phase1-rebuild ran root wrapper clean/assembleDebug/test/lintDebug, no build cache, exit0. Six tests, no failures/errors/skips. Lint0 errors/9 unsuppressed version advisories. Full logs/XML retained. AGP9 executed debug unit tests only; no release-test run claimed.
- Source re-audit: UI holds only navigation/draft, no call/auth/result fabrication, bounded64-character keypad draft, lifecycle state restoration, no SDK/network/audio/Telecom runtime code. Stable tab layout and weighted controls remain minimal; final visual polish deferred.
- APK re-inspection and signature check, actual IDE model check, supplied archive/source/fixture integrity all pass. Documentation now describes current Phase1 state and preserves historical Phase0 evidence.

## Final gate
**Automated implementation/build/test/re-audit: PASS. Overall Phase 1 gate: BLOCKED.**

The remaining exact requirement is an observed coherent Android Studio open/sync. Neither native GUI access nor a Studio installation at checked common paths is available here; IDE models validate successfully but the requirement is not replaced. KI-011 defines the next verification. No further known code-level failure remains in this phase's automated checks. Do not begin Phase2. No physical-device, live auth, inference or real calling test performed.


## Studio verification follow-up — 2026-09-24
User requested completing the remaining IDE gate. A separate deferred node_repl/@oai/sky Windows automation runtime is available and successfully listed native apps; earlier conclusions based only on the browser CUA surface were incomplete. No Studio installation was found. Official Quail4 Patch1 ZIP acquisition and actual UI opening/sync are in progress; no gate PASS is inferred yet. The local Gradle JDK selection uses ignored .gradle/config.properties with JDK17.

## Verification follow-up — 2026-09-27
A fresh clean verifier run passed with exit code 0 (7m12s): assembleDebug, six unit tests, lintDebug, APK/package checks and reports. Evidence: `evidence/phase1/phase1-followup.json`, `.log`, and `phase1-followup-reports/`. Direct shell Gradle startup produced a native-platform.dll error and is recorded separately; it does not override the passing reproducible verifier. The observed Android Studio sync criterion remains unmet; gate stays BLOCKED.
