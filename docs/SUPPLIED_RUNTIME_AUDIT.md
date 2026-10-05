# Supplied runtime integration audit — 2026-09-29

## Preserved baseline and architecture

The fresh local run in docs/import-2026-09-29/final-e2e-local.json passed all baseline
comparisons (54 windows; peak 0.9998408555984497; risk 97.4643709518332; HOLD).
Qwen's accepted CPU numerical difference does not change its capped fusion input.
Context with unknown metadata is truthfully unavailable. ECAPA requires trusted enrollment.
The historical result remains unchanged; the new user-requested guidance is separate.
No model was trained, no artifact architecture changed, and no supplied weights overwritten.

New opt-in praxis.supplied runtime uses the canonical local model paths and separate verified
Python 3.10/Fairseq worker. Models are persistent. Wave A precedes transcript-dependent Wave B;
all evidence completes before fusion, risk and guidance. Requests are bounded to 120 seconds
and one concurrent analysis per process. Personal CLI capture queue holds one pending block.
V1 contracts, validated-risk gates and default configuration remain unchanged. Disable V1
model loading explicitly when running V2 to avoid duplicate heavyweight model sets.
Imported runtimes and reproduction/w2v2_runtime remain required local dependencies; this is
not yet a self-contained Docker distribution of the new runtime.

## Security and privacy

V2 uses existing authentication, tenant/owner session access, roles and rate limits.
It validates finite PCM and bounded bodies. Enrolled ECAPA reference lookup is tenant-scoped,
version-checked and decrypted with existing authenticated encryption. No calibrated ECAPA
threshold is invented. The result is delivered only after its metadata audit transaction commits.
Unit tests inject audit failure and verify no result delivery; these are explicitly SQLite unit
fixtures, not new real-PostgreSQL deployment evidence. Historical P10 deployment evidence remains.
No default credentials, secret changes, raw-audio writes, transcript or embedding outputs added.
CORS is explicit opt-in; client requires HTTPS and stores tokens in memory only.
The local model manifest/import tree is operator-trusted and must not be writable by API callers.
Legacy Fairseq/joblib artifacts are trusted local imports, never user-uploaded checkpoints.
MiniLM explicitly uses torch.load(weights_only=True); its trained tensor architecture is unchanged.
Bandit subprocess findings are reviewed with targeted annotations: fixed internal worker,
absolute Windows launcher, separate arguments, no shell or request-controlled command input.

## Guidance limits and manual testing

Synthetic speech alone never causes scam guidance/HOLD. Explicit harmful requests or
corroborating trained MiniLM labels trigger secondary verification. Negated safety advice is
handled without masking a later harmful request. No numeric thresholds were invented.
English directive rules and trained multilingual labels are not a validated scam classifier.
No detected indicators does not establish safety; missing transcript/evidence reports pending.
The original bootstrap numerical score remains diagnostic, not a scam probability.

The 8-second file test exercises actual persistent models; device enumeration and format checks
exercise no microphone capture. The operator must perform their own microphone test. CPU
inference is slower than capture; latest queued blocks are prioritized and drops are reported.
The webapp is not supplied, connected or deployed. integrations/webapp contains the connection
interface and requirements. New V2 Docker/PostgreSQL/HTTPS deployment has not been verified.
