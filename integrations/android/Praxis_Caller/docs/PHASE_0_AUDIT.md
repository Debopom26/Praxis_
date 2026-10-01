# Phase 0 audit

Scope: repository and SDK truth establishment only. Acceptance criteria were written in PROJECT_STATUS.md before build implementation. A Phase 0 truth gate is not certification that SDK runtime is production-ready. Phase 1 is not authorized in this task.

## Inputs and complete inspection

- Outer ZIP: 16 files, SHA-256 `685b4ae2cc2f353289cfde4a733a8be6ff7e9f58eef7146910e6e464a0fa4296`.
- Nested SDK ZIP: 646 files, SHA-256 `d129129d66dfee33eca7ddc19f478f112706d5e42359616d6adc4b70915dfd2c`.
- Complete ZIP CRC checks, per-file hash inventory and pristine vendor/source comparisons: scripts/inspect_pack.py, evidence/input-verification.json, archive-inventory.csv.
- Read MASTER_PROMPT, AI_CONTEXT, AI_MEMORY, PROJECT_STATUS, DECISIONS, KNOWN_ISSUES, HANDOFF, every original docs file, then SDK source/config/tests; also read TEST_LOG. MASTER_PROMPT is authoritative because the user explicitly designated it; SDK README commands are inspected as source material, not permission to expand task scope.
- Read all ten non-generated SDK files: root/settings/module Gradle, properties, manifest, consumer rules, README, client, generated contract source and test class. All 37 DTO/enums inspected. Read all ten recovered JSON fixtures and their README; generated Kotlin metadata is not a fixture.
- Historical JUnit XML records five passes on another host at 2026-09-20T19:45:16; historical lint says no issues. These are labeled historical and not counted as current passes. Public API of supplied classes.jar inspected with javap. Remaining generated classes, caches, HTML/CSS/JS reports and intermediates are indexed/hash-checked, not mistaken for source or hand-authored implementation. No claim is made that each cache binary was semantically reverse-engineered.
- User-identified UI JPEG visually inspected, preserved at references/finalized-praxis-caller-ui.jpeg; SHA-256 `7eb9ba057522a05c9c48de7a7bbbe8b2e8700d6dc6adc2ca87b0ec47342991fb`. Eight-panel flow documented in UI_UX.md. No application UI implemented.

## Documentation-to-source audit

| Claim group | Source comparison | Audit/fix |
|---|---|---|
| Modules/packages/dependencies | All Gradle files, manifest, package declarations | Exact map added, SDK minSdk26 distinguished from app minSdk29 |
| Public methods/config | PraxisClient.kt:22–30,78,110–115,146,161,268–293 | Signatures mapped; public connect/login/ACK methods explicitly absent |
| Auth | C:130–143,207–214 vs SDK README | Login URL only README-level, no backend/browser/refresh success claimed |
| Session lifecycle | C:146–158,276–293 | ID != connected; end request precedes local cleanup; close != server end |
| Audio format | C:161–185, T:48–61 | Rates/channels/alignment/frame limits/timestamps documented; encoding-validation omission disclosed |
| Events/contracts | C:32–75, full Contracts.kt | 13 event variants, 37 contracts indexed; missing evidence not zero risk |
| Buffer/ACK/reconnect | C:85–123,170–268 | Raw byte cap vs heap distinguished; ACK internal; reconnect/backpressure caveats disclosed |
| 4s/2s windowing | Source has no processing engine | AI_CONTEXT/AI_MEMORY corrected to label locked design intent, not verified server fact |
| Remote-only vs speaker/mic | C:77,160 and SDK README vs V1 requirement | Mixed acoustic compatibility kept unresolved, not silently treated as remote-only |
| Host class names | SDK source package/type scan | Planned PraxisManager/auth/audio types labeled future host types |
| Visual risk/authenticity examples | UI image vs contract fields | Scores/verdicts in image and fixtures never treated as production results |
| Historical reports | Supplied XML timestamps vs current log paths | Fresh and inherited evidence separated |

## Audit/fix iterations

1. IMPLEMENT: pristine extraction, source map, build copy and acceptance tests. BUILD/TEST attempt: absent tools/resources identified; compatible tools downloaded/hash-verified and fixtures recovered exactly. Initial Gradle fails on unwritable default .android. AUDIT: no test execution claimed; setup paths corrected.
2. FIX: local Android/Gradle homes, platform download retry; wrapper generated after real ZIP checksum validation, failed URL HEAD preflight recorded. REBUILD/RETEST: build-second.log. AUDIT: Kotlin daemon file lock/fallback requires a clean repeat using in-process non-incremental compilation; source untouched.
3. FIX/REBUILD/RETEST/RE-AUDIT: current outcome is recorded in TEST_LOG.md and final section below after verification completes. No acceptance test is removed/skipped to force a pass.

## Known boundaries carried forward

KI-004 production backend/auth unavailable; KI-005 remote-input acoustic suitability; KI-006 validation omissions; KI-007 lifecycle/backpressure risks. Canonical generator/schema sources absent. These do not prevent documenting the Phase 0 integration surface, but affected later phase gates cannot ignore them. No physical, live auth or inference tests were performed. Phase 0 makes no promise that the existing SDK is defect-free.

## Final result

**Audit PASS; Phase 0 gate PASS.** All Phase 0 acceptance criteria met without changing the gate. First full build succeeded in 7m54s with fallback; corrected clean rebuild succeeded in 1m18s. Both ran all five supplied tests with zero failures/errors/skips and lint with no issues. Wrapper smoke succeeded; final pristine source/fixture checks passed; rebuilt public API matches supplied binary. Evidence: TEST_LOG.md, evidence/phase0-rebuild.json, phase0-rebuild-reports, integrity-final.txt and both javap outputs.

Current source claims were searched across every root control/doc file and SDK README and compared with C/T/U and Gradle inputs. README-only auth/server assertions remain explicitly unverified; proposed host types, synthetic data, old reports and physical tests are labeled. Documentation defects fixed; original MASTER_PROMPT remains unchanged. No current-phase implementation defect or external input prevents the source-truth gate. SDK runtime findings remain open for their affected phases, not relabeled as fixed. Nonfatal tool analytics warning recorded as KI-010.

Phase 1 is NOT STARTED. Current task stops at this checkpoint.
