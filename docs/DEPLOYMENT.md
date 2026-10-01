# Windows deployment

Use the existing `C:\Users\KIIT\Downloads\Praxis_` project. P10 local deployment passed on 2026-09-21. PostgreSQL/backend are healthy, migrations 0001/0002 are applied, and Caddy serves HTTPS/WSS. Remaining image vulnerabilities prevent a production-readiness claim; read `CONTAINER_SECURITY_AUDIT.md` before release. Exact images/packages: `DEPLOYMENT_IMAGES.json`. Actual execution: `DEPLOYMENT_VERIFICATION.json`.

## Start or resume

Use PowerShell from the project root. Docker Desktop must be running Linux containers. If the current terminal lacks Docker on PATH, add `%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin` to that process PATH; the credential helper also needs that directory. No system PATH edit is required.

```powershell
cd C:\Users\KIIT\Downloads\Praxis_
$env:PATH = "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin;" + $env:PATH
docker version
docker compose version
docker compose --env-file .env -f deployment/compose.yaml ps --all
```

Inspect existing state first. The canonical file is `deployment/compose.yaml`; configuration is root `.env`. Do not reset volumes or regenerate valid keys. For an intentional startup/build use the existing entry point:

```powershell
.\scripts\start.ps1
```

`init-env.ps1` creates keys only if absent and refuses to overwrite an existing file. Preserve the embedding key securely: losing it makes encrypted retained data unreadable. The initial start created `.env` once when absent; all subsequent checks preserved its hash. No default/demo administrator is seeded. Create an operator-controlled organization administrator interactively:

```powershell
docker compose --env-file .env -f deployment/compose.yaml exec backend python scripts/create_admin.py
```

The command asks for organization ID/name, username and a non-echoed password. Never place passwords in command arguments. This exact script was exercised in a Linux PTY; temporary verification accounts were removed. No lasting operator account has been selected on your behalf.

The Windows developer environment uses Python 3.11 in `.venv`; declarations are in `backend/pyproject.toml`, and exact tested Windows packages are in `backend/requirements-dev.lock`. Permitted model assets are fetched/reused with `.\.venv\Scripts\python.exe scripts/fetch_models.py`, using committed revisions and hashes in `model-assets.json`. Do not replace existing matching assets. No dataset/training download occurs.

## TLS and health

Readiness is `https://localhost/api/v1/health`. Caddy uses its local CA for localhost. The verified client explicitly trusted the public root certificate exported from the Caddy volume to `.cache/p10-caddy-root.crt`; no system trust store was modified. For a local command-line check, export only the public CA certificate and pass it as the trust anchor:

```powershell
docker compose --env-file .env -f deployment/compose.yaml exec -T caddy cat /data/caddy/pki/authorities/local/root.crt | Set-Content -Encoding ascii .cache/p10-caddy-root.crt
curl.exe --cacert .cache/p10-caddy-root.crt https://localhost/api/v1/health
```

Do not use `-k`, `verify=False`, permissive trust managers or hostname-verification bypasses. Configure a separately authorized owned DNS name via `PRAXIS_HOST` and reachable ports 80/443 for public issuance; that path and Android-device CA configuration were not tested in P10. A client without the local CA failed validation as expected. Final TLS protocol/cipher/fingerprint are recorded in the live report.

Observed health: six permitted model components AVAILABLE; five absent trained artifacts UNVALIDATED. Database outage actually returned 503/database UNAVAILABLE; restart restored readiness. This is infrastructure readiness, not model accuracy or complete SRS readiness.

## Deployment security and reproducibility

PostgreSQL has no host port and is on an internal network. Caddy alone exposes 80/443. Migration credentials belong to the owner; backend credentials belong to the distinct runtime role with application DML, no table ownership, no schema/role creation, no Alembic access and no TEMP. PostgreSQL's default PUBLIC TEMP access was removed after the live negative test found it.

Backend and migration run as UID 10001 with read-only roots, dropped capabilities and no-new-privileges; model assets mount read-only. Backend uses one worker because stream ownership and rate limiting are process-local. Runtime transcript/enrollment retention is opt-in and encrypted; metadata defaults to 30 days. Expired payloads cannot be read; cleanup runs at startup and hourly. Completed context/history expires with metadata retention. Live audio is not written to disk. Key rotation, backups and genuine enrollment validation need operational procedures before production.

Python/PostgreSQL/Caddy runtime bases are digest-pinned in Dockerfiles. The Go builder is version-tagged 1.26.8-alpine; its resolved digest is recorded with the runtime digests. Rebuilt PostgreSQL gosu and Caddy dependencies remove actionable Go findings without changing services. Caddy's `version` command prints `unknown` for this custom Go module build; `caddy build-info` proves module v2.11.4 and the full dependency graph, preserved in `CADDY_BUILD_INFO.txt`.

The backend build uses pinned pip 26.2.1 with bounded retries/resumption, separate CPU Torch/app layers, setuptools 84.0.0, and build-time pip check. The unused pip installer is removed from the final image; run package checks during the build or in the developer environment, not with runtime `pip`. `DEPLOYMENT_IMAGES.json` captures all 104 installed Linux Python distributions. Local build digests identify this exact execution; the images have not been published to a registry. Transitive/OS resolution on a future rebuild can change, so compare inventories and rescan before promotion.

All four final images were actually scanned with project-local Trivy 0.74.0. For an intentional rescan, with Docker's directory on process PATH:

```powershell
.\.tools\trivy-0.74.0\trivy.exe image --docker-host npipe:////./pipe/dockerDesktopLinuxEngine --image-src docker --cache-dir .cache/trivy --scanners vuln --format json --output docs/backend-patched-image-scan.json praxis-backend:latest
```

Repeat for the migration, PostgreSQL and Caddy image tags in the inventory, preserving prior reports if comparing changes. An exit code of zero means the scan ran; it does not mean zero findings. Scout required login and did not scan. Critical/high Debian advisories and seven Caddy dependency entries remain explicitly documented; no suppression or clean-image claim.

## Verification commands and scope

Run `.\scripts\test.ps1` for backend regression/type/lint/Bandit/pip checks. Final result: 72 tests and mypy 40 files pass. Android was unchanged; the prior five JVM tests, lint and AAR build remain valid with checksum rechecked. Historical model smoke/pipeline files remain synthetic execution evidence; the original pipeline used isolated SQLite. New PostgreSQL reports are separate.

The following is an opt-in, disruptive LOCAL DEVELOPMENT verification command. It creates disposable tenants, invokes the real interactive admin command, tests authentication and negative permissions, installs a tenant-scoped audit-failure trigger, exercises retention cleanup, and stops/restarts database/backend. Use only on this authorized local test deployment, with `.cache/synthetic-speech.wav` available. Do not use it on a customer deployment. It rejects a non-localhost PRAXIS_HOST.

```powershell
.\.venv\Scripts\python.exe scripts/verify_deployment.py
```

The runner trusts Caddy's CA per client; it never bypasses TLS, uses SQLite, writes credentials to argv, or creates mock application endpoints. It cleans its own tenants/users/profiles and fault trigger in finally blocks. If the process is forcibly terminated, inspect its uniquely named `p10-verify-*` resources before a controlled cleanup; never delete arbitrary application rows. Normal final cleanup confirmed zero users, test organizations, triggers and functions. Tests include actual ECAPA execution on synthetic speech, not an identity/accuracy claim.

P10 verified session/context persistence, real PostgreSQL transaction rollback, composite tenant FKs, concurrent sequence acceptance, retained ciphertext/default-off/expiry, speaker-profile encryption/deletion, trusted WSS reconnect/duplicate/gap and payload bounds, honest outage health, logs and key preservation. No emulator/device/two-party call, public TLS issuance, target-hardware SLA, trained risk value or DEMO_READY claim is made. Stop at the authorized P10 milestone; excluded product/training scope remains deferred.
