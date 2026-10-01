# Existing-webapp connection interface

The webapp has not yet been supplied. This client is prepared for its eventual integration;
it is not evidence of a connected or deployed webapp. The disposable microphone CLI is separate.

Import `PraxisClient` from `praxis-client.mjs`. Instantiate with the trusted HTTPS backend origin,
login with an existing organization account, start a session, and submit mono 16 kHz Float32 PCM.
The client does not capture or resample audio. The future webapp must convert its actual sample
rate correctly, keep one request in flight, and stop/end its session when capture stops.
Tokens stay only in the client instance's memory; call logout when leaving the account.
No default account is created. Existing interactive administrator setup is in docs/DEPLOYMENT.md.

## Opt-in backend configuration

Existing secrets and PostgreSQL configuration must be preserved. For the supplied-model local
backend set PRAXIS_SUPPLIED_MODELS_ENABLED=true, PRAXIS_MODELS_ENABLED=false, and
PRAXIS_MODEL_PATHS_FILE to the absolute root model_paths.json. This avoids loading duplicate
V1 model sets; V1 authentication/session APIs remain, while V1 model inference is disabled.
Set PRAXIS_WEBAPP_ORIGINS to a JSON array of exact trusted HTTPS webapp origins when known.
The default empty list authorizes no cross-origin browser access. Do not use wildcard origins.
Run only one backend process/worker: each owns its persistent model set and bounded inference slot.

The verified supplied runtime currently uses Windows Python 3.11 plus its separate WSL Python
3.10/Fairseq worker. The existing Docker image does not yet package this worker/imported model
runtime; do not claim the new V2 routes are deployed through Caddy. Before browser hookup, verify
that deployment has local asset access and the correct worker environment, then test authenticated
HTTPS routing, body limits, request timeouts and CORS with the actual webapp origin. Never disable TLS.

## Response semantics

GET /api/v2/health and POST /api/v2/analysis require an organization bearer token.
Analysis requires admin/host access to the owned active session. It accepts 1-120 seconds;
use short blocks and expect CPU latency. It rejects concurrent analysis with 429.
Results use schema_version praxis-supplied-2.1. Display guidance.message prominently.
synthetic_voice.score_0_100 is an uncalibrated model output; experimental_score_0_100 is
BOOTSTRAP_UNTRAINED, not a calibrated scam probability. scam_probability is null.
An AI voice alone yields AI_NOTICE; harmful indicators yield SECONDARY_VERIFICATION.
No detected indicators is not proof of safety. Missing linguistic evidence yields assessment pending.
Audit entries contain timing/status/worker fields; responses exclude transcript, PCM and embeddings.
Only allowlisted audit metadata is committed before delivering the result. Raw audio is not retained.
Context with unknown metadata and ECAPA without compatible enrollment remain unavailable.
