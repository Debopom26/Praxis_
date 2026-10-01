## Current implementation - 2026-09-29

Current implementation: app audio/CallAudioSource.kt, SpeakerMicAudioSource.kt, CaptureService.kt and CapturePolicy.kt. See PHASE_6_AUDIT.md. The runtime SDK derivative enforces connected-only frames and immediate stop; production input approval remains absent so capture is gated off. Original Phase0 observations below are historical and remain accurate for the pristine supplied SDK.

---

# Audio Pipeline

## V1
Active call + Praxis enabled
-> speakerphone
-> microphone
-> AudioRecord
-> `SpeakerMicAudioSource`
-> PCM frames
-> `PraxisManager`
-> supplied Praxis SDK
-> Praxis cloud

## Requirements
- abstract behind `CallAudioSource`
- no full-call storage
- no transmission when Praxis disconnected
- stop/release on call end
- bounded buffering
- avoid main-thread audio/network work
- server owns ML analysis windows

Document actual AudioRecord source/configuration and device behavior after implementation and physical testing.

## Phase 0 findings, not implemented capture
Actual method: `PraxisClient.streamAudio(sessionId: String, audioFrame: ByteArray, timestamp: Long, format: io.praxis.sdk.contracts.AudioFormat)`. Source accepts 16 kHz mono PCM-sized frames; 20 ms is 640 bytes. Encoding defaults to pcm_s16le but must be enforced by the host because SDK does not validate the string. Full supported rates and constraints: PRAXIS_INTEGRATION.md.

SDK buffers during disconnect and may send retained audio after reconnect. Future adapter must gate capture and enqueue on consent, active call and connection, and make retained-audio behavior explicit. SDK endSession awaits network before cleanup, so capture must stop first. No application audio code exists yet.

SDK source/README describe remote-only input, while speaker/microphone can mix both voices/environment. Compatibility/model quality on that acoustic path is unverified and requires backend agreement and human physical tests. Server 4 s/2 s windowing is a locked design requirement, not a verified runtime result.
