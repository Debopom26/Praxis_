# Phase 6 - Audio pipeline

CallAudioSource -> SpeakerMicAudioSource implements MIC AudioRecord at 16kHz mono PCM16, 640-byte frames. IO coroutine owns creation/read/release. Nonblocking reads allow cancellation; stop/release runs in finally. A shared ownership mutex prevents overlapping recorders. Private non-sticky microphone foreground service displays a stop action; explicit visible-Activity consent/permission is required. Service epoch/live guard blocks stale capture workers. No audio files, full-call buffers or public audio component exist.

CapturePolicy requires exactly one active target call, selected speaker route, known unmuted state, valid credential, connected matching session and explicit backend acoustic-input approval. Source rechecks permission/eligibility before sends. Stops on hold/end/route/auth/disconnect/error/cancel; never resumes consent after process death.

Five recorder-ownership tests and three eligibility/duration tests pass in final-regression-render-fix. These are injected host recorder tests, not actual AudioRecord hardware. Physical acoustic path can fail/silence on OEM devices. Mixed input versus remote-only SDK intent remains BLOCKED and defaults disabled.

Gate: host implementation/lifecycle checks pass; physical/source compatibility remains explicitly pending.
