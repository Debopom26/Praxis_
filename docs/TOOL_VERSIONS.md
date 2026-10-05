# Verified toolchain

Python 3.11.16 in project .venv/.tools; complete tested Windows package pins in backend/requirements-dev.lock. Primary runtime declarations are in backend/pyproject.toml. Dependency vulnerability scan: docs/DEPENDENCY_AUDIT.json (138 packages, no known vulnerabilities at scan time).

Kotlin 2.1.20, Android Gradle Plugin 8.9.2, Gradle 8.11.1, compile SDK 35, build-tools 35.0.0, min SDK 26, Java bytecode target 17; build executed with existing JDK 22. Android platform-tools 37.0.1 were installed automatically by AGP inside the project-local SDK. Download inventory: docs/android-toolchain.json. No global SDK/JDK/Gradle changes.

References checked: https://developer.android.com/build/releases/agp-8-9-0-release-notes and https://docs.gradle.org/8.11.1/userguide/compatibility.html .

Docker Desktop 4.91.0 (239619), Linux Engine 29.8.0, Compose 5.5.1, containerd 2.3.4, runc 1.4.3 are verified. Runtime Python 3.11.16; PostgreSQL 17.11 (Debian 17.11-1.pgdg13+2); Caddy module v2.11.4; gosu 1.19; Go security builder 1.26.8; FFmpeg 5.1.9-0+deb12u1. Caddy's display version is unknown in the custom module build; embedded `CADDY_BUILD_INFO.txt` records the actual module and dependency versions. Native clip input remains bounded WAV/FLAC through soundfile.

Exact deployed image IDs, resolved base digests, selected security settings and 104 Linux Python package versions: `DEPLOYMENT_IMAGES.json`. Python/PostgreSQL/Caddy runtime bases are digest-pinned; the Go builder's exact resolved digest is recorded. The Windows lock is not asserted to be the Linux inventory. Backend build uses pip 26.2.1, removes it after successful pip check, and retains setuptools 84.0.0 for runtime dependencies.

Trivy 0.74.0 executed on all four final image digests. Raw reports, database timestamps and report checksums: `CONTAINER_SCAN_SUMMARY.json`; remediation and outstanding findings: `CONTAINER_SECURITY_AUDIT.md`. Scout 1.24.0 was present but refused without login; it did not scan. Critical/high Debian findings and lower-severity Caddy findings remain. Docker availability is no longer a blocker.
