# P10 container and architecture security audit

2026-09-21. Local deployment verification passed with unresolved image vulnerabilities. This is not a production-readiness or vulnerability-free result.

## Actual image scans

Trivy 0.74.0 ran successfully against all four final deployed images using the Docker Linux engine. Full unfiltered reports are `backend-patched-image-scan.json`, `migrate-patched-image-scan.json`, `postgres-patched-image-scan.json` and `caddy-patched-image-scan.json`. `CONTAINER_SCAN_SUMMARY.json` binds report hashes and image IDs; `DEPLOYMENT_IMAGES.json` records exact resolved digests, versions, settings and 104 Linux Python packages. Counts below are package/advisory entries, not unique CVEs or proven exploitable paths.

| Final image | Critical | High | Medium | Low | Unknown | Scope |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Backend | 11 | 241 | 364 | 226 | 35 | Debian 12.15 packages; zero Python findings |
| Migration | 11 | 241 | 364 | 226 | 35 | Same filesystem layers as backend; separately scanned |
| PostgreSQL | 1 | 61 | 89 | 119 | 6 | Debian 13.7 packages; zero gosu findings |
| Caddy | 0 | 0 | 2 | 4 | 1 | Go dependencies; zero Alpine 3.23.6 findings |

The scanner lists no fixed version for any remaining Debian entry. This does not prove that every finding is exploitable, inapplicable, or impossible to remediate. Preserve the reports and reassess vendor patches before any production release. No finding was suppressed and no base distribution/architecture was replaced merely to reduce scanner counts.

Docker Scout 1.24.0 refused to scan without Docker login. No successful Scout scan is claimed. Trivy was the functioning alternative; its official Windows archive SHA256 is `94c40e0696e4b907a74b7b2e1438d5d72ebaca83115817407f568a002d520842`. Its actual downloaded database metadata is in the summary JSON. Original pre-fix scans are retained as `backend-image-scan.json`, `postgres-image-scan.json`, and `caddy-image-scan.json`.

## Remediation and residuals

- The real database test found inherited PUBLIC TEMP permission. `migrate_and_grant.py` now revokes PUBLIC database privileges and explicitly grants runtime CONNECT. The runtime remains a distinct DML role, owns no tables, is not superuser/createdb/createrole/replication/bypassrls, and actually fails table creation/alteration, role creation, Alembic-table access and temporary-table creation with PostgreSQL 42501. Application DML, tenant isolation and concurrent sequence locking pass.
- PostgreSQL 17.11 and its official entrypoint remain intact. Rebuilding its gosu 1.19 helper with Go 1.26.8 and x/sys 0.44.0 removed all 46 helper findings. Database health, migrations and persistent-volume restart passed afterward.
- Caddy remains module v2.11.4, rebuilt with Go 1.26.8 and compatible crypto/net/text/gRPC dependency fixes. All 17 high findings in the original Caddy scan are removed. Existing gRPC libraries are Caddy dependencies; no Praxis gRPC service or transport was introduced.
- Caddy residuals: GHSA-gcjh-h69q-9w9g (CEL, medium), CVE-2026-81871 (OTLP log gRPC, medium), four CVE-2026-81870 package entries (OTLP trace/SDK, low), and GO-2026-5932 (x/crypto, unknown, no fixed version listed). CEL 0.29.0 and OpenTelemetry 0.21.0/1.45.0 upgrades were attempted but failed compilation against the current Caddy APIs. Those incompatible edits were removed. These findings require compatible upstream updates; they are not dismissed as false positives. Current Caddyfile does not configure CEL expressions or telemetry exporters, which limits configured exposure but does not establish non-exploitability.
- Backend setuptools 79.0.1 and vulnerable vendored components were replaced with 84.0.0, already used by the tested Windows environment. The unused pip installer and its bundled components/SBOM were removed after successful build-time `pip check`. Final backend/migration scans report zero Python findings; operational scripts and model loading still pass. No runtime dependency was removed merely to conceal a finding.
- Interrupted package downloads originally produced a Silero wheel hash mismatch and then a read timeout. Expected hash was checked against PyPI. Build-only pip 26.2.1, bounded resumption/retries and cached CPU/app layers repaired download resilience without bypassing hashes or TLS.

## Architecture and redundancy review

The implementation remains the locked Python 3.11 FastAPI/Pydantic modular monolith, PostgreSQL, Caddy HTTPS/WSS and Kotlin AAR. No additional service, queue, database, application transport or excluded model scope was added. The only runtime permission change removes unnecessary TEMP access. Secrets remain in the existing ignored root `.env`; init-env overwrite refusal and unchanged file hash were tested.

Observed backend and migration containers run as `praxis` (UID 10001), with read-only roots, all capabilities dropped, no-new-privileges and temporary /tmp. Backend model assets are read-only. PostgreSQL has no host port and is reachable only on the internal network; Caddy alone exposes 80/443. Official PostgreSQL entrypoint privileges remain for initialization and its server drops to postgres. Caddy retains the upstream container user configuration; no claim that every service is non-root is made. Owner credentials exist only in database/migration service configuration; the backend receives only runtime credentials. One backend worker preserves process-local stream ownership and rate limiting.

Only the two operational admin/migration scripts are copied into the backend image. New live-test helpers stay outside the production image and reuse existing application interfaces instead of adding test endpoints, authentication bypasses or alternate persistence. Incompatible dependency candidates were removed; no duplicate production secret loader, database layer or fake health path was introduced. Repository review found no TLS verification bypass in backend, deployment or Android production source. No source/contracts/SDK behavior changed during these deployment repairs.

## Executed checks and limits

`DEPLOYMENT_VERIFICATION.json` records the final live run against the exact deployed images: real migrations 0001/0002 and 12 tables, zero preseeded users, interactive admin creation through getpass in a Linux PTY with no password echo, authentication/JWT negatives, live RBAC changes, tenant isolation, PostgreSQL composite FKs and concurrent sequence acceptance, encrypted retention/expiry/default-off, real ECAPA encrypted persistence/deletion, HTTPS/WSS authentication/reconnect/duplicate/gap behavior and request limits.

A tenant-scoped PostgreSQL trigger forced mandatory audit inserts to fail. REST returned 503 without committing session/context changes; WSS closed 1013 without ACK and the persisted sequence stayed unchanged. Oversized WSS messages closed 1009; oversized HTTP bodies returned 413. A real database outage returned 503/database UNAVAILABLE. Database/backend restart preserved sessions, context and sequence. Six permitted model components reported AVAILABLE, while five missing trained artifacts remained UNVALIDATED.

TLS certificate and hostname validation were enabled. A client without the local CA failed; a client explicitly trusting only the exported Caddy CA completed HTTPS and WSS. Final negotiated protocol/cipher/certificate fingerprint are recorded. No system trust store was modified. Public-CA issuance, remote/device clients, throughput and accuracy were not tested.

No live audio files were found in writable backend /tmp or model-cache paths; default enrollment retained no audio. Container logs were checked for exact environment secrets, ephemeral passwords/tokens/audio values and sensitive field markers, with no matches. Saved reports were checked for actual environment secret values. These checks apply to the exercised flows and inspected logs, not an absolute proof about all future inputs. Cleanup confirmed zero users, verification organizations, fault triggers or fault functions. Existing keys and volumes were preserved.

The full backend suite passed: 72 tests, mypy 40 source files, Ruff, Bandit and pip check. Existing Windows pip-audit result (138 packages) is historical and distinct from Linux image scans. The unchanged SDK retains its prior five JVM tests, lint and release build; AAR checksum was rechecked. No Android device/two-party E2E, genuine enrollment, model accuracy, trained risk or DEMO_READY claim is made.
