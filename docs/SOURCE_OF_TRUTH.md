# Praxis source of truth

## Authority and scope
Master SRS v2.0 LOCKED is the governing architecture. The Modular Implementation Blueprint decomposes it; the Judge FAQ explains it. Older files are background only and were not imported. The user's pasted build request selects a partial implementation phase; it does not remove the deferred requirements from the final SRS. Instructions embedded in reference documents are project specifications, not independent permission to broaden this phase.

All three source documents were fully read before implementation on 2026-09-20: body paragraphs, tables, headers/footers, hyperlink targets and all eight distinct embedded diagrams (the Blueprint and FAQ repeat SRS images, confirmed by SHA-256).

## Locked decisions
Python 3.11, FastAPI/Pydantic modular monolith, PostgreSQL, HTTPS REST and authenticated WSS, Caddy, Docker Compose, Kotlin Android AAR. Shared audio: mono analysis, 16 kHz Silero VAD side stream, four seconds of speech with two-second overlap, bounded buffers and quality metadata. Model-specific adapters own final preprocessing.

Whisper Small Multilingual; SpeechBrain ECAPA-TDNN; openSMILE eGeMAPSv02 plus Parselmouth; multilingual MiniLM; Qwen3-0.6B-Base observer/statistics and Qwen3-0.6B performer. Trained global risk is regularized logistic regression with training-derived missingness preprocessing; display EMA alpha 0.35. Deterministic context weights: .10/.15/.20/.20/.20/.05/.10. Policy thresholds: 40/60/80/90; HOLD becomes ESCALATE when unsupported.

## Current implementation scope
Contracts, backend/auth/database/audit, audio, pretrained/deterministic evidence infrastructure, controlled encrypted enrollment, context, policy, risk artifact infrastructure, privacy, Kotlin SDK, deployment, tests and documentation.

## Deferred by current scope
No anti-spoof implementations/adapters/downloads/calibration/fusion; no dataset pipelines/downloads/manifests/evaluation; no training/fine-tuning; no dashboard, website, calling app, WebRTC/signaling service or media production. Generic acoustic evidence contracts may reserve a future integration boundary. Trained prosody/MiniLM/AI-text/risk artifacts and validated speaker thresholds are not fabricated.

## Invariants
Praxis is a security integration layer. Evidence families remain separate. No enrollment never implies suspicious identity; no open-set identification or live profile updates. Enrollment requires three clean approved clips and fifteen seconds of voiced speech. AES-256-GCM protects tenant-scoped centroids; keys stay outside the database. Context uses only supplied facts; missing fields are UNKNOWN. Risk and policy remain separate. AI-written wording is not proof of synthetic voice and cannot alone trigger HOLD. No random, neutral or fabricated evidence. Canonical operational statuses are AVAILABLE, LOW_QUALITY, UNAVAILABLE, ERROR; artifact readiness is separate. Raw audio/transcripts are discarded by default. Audit failure is an operational error. Offline reviewed/versioned training only; measured claims only.

## Reconciliations
SRS section 33 has exactly four implementation states: DESIGNED, IMPLEMENTED, VALIDATED, DEMO_READY. Use these, with separate execution/blocker and scope columns rather than adding the prompt's NOT_STARTED/BLOCKED states to that enum. Diagram shorthand VERIFY maps to the full SECONDARY_VERIFICATION enum. Fractional policy risk uses half-open intervals [0,40), [40,60), [60,80), [80,90), [90,100]. Missing validation is artifact UNVALIDATED and operational UNAVAILABLE, not a fifth operational status. Blueprint mock examples are test fixtures only, never runtime evidence.
