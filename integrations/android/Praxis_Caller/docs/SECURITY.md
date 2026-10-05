## Current implementation - 2026-09-29

Current security review is docs/SECURITY_AUDIT.md. The app now declares Internet/Phone/Contacts/CallLog/microphone/foreground permissions; all optional paths are gated. Older Phase0/1 comments below are historical.

---

# Security Requirements

- Praxis optional; telephony independent.
- No exported audio-sharing service.
- No public call-audio files.
- No broadcast of audio payloads.
- No access-token logging.
- Secure token storage.
- Auth callback validation.
- Encrypted transport according to real SDK/server.
- Bounded audio buffers.
- Release capture immediately when no longer authorized/needed.
- Do not interpret missing analysis as zero risk.
- Do not bypass Android platform restrictions.

Phase 9 must create/update a detailed `docs/SECURITY_AUDIT.md`.

Phase 0 source inspection is not a completed Phase 9 security audit. SDK uses bearer headers, default TLS and disabled redirects; no credential persistence or audio capture exists in supplied code. Source validation/lifecycle limitations are tracked in KNOWN_ISSUES.md and PRAXIS_INTEGRATION.md. Synthetic fixtures and historical test reports do not establish backend trust, token validity, consent or model accuracy.

Phase 1 app has no Internet/call/microphone permissions or operational SDK dependency. Packaged manifest disables backup and cleartext traffic. AndroidX adds a signature-only dynamic-receiver permission, nonexported startup provider and DUMP-protected profile receiver; debug tooling adds an exported PreviewActivity. MainActivity is exported for launcher entry only. No audio/token interfaces, logging or files are implemented. Draft number is held in lifecycle saved state, not a contacts database. This narrow skeleton review does not replace Phase 9 or certify future sensitive-state handling. Detailed APK evidence: evidence/phase1/apk-manifest.txt.
