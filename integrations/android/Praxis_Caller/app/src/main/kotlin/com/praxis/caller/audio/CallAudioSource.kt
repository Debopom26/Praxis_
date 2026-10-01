package com.praxis.caller.audio

interface CallAudioSource {
    suspend fun capture(allowed: () -> Boolean, send: (ByteArray, Long, Float) -> Boolean)
}
data class CaptureState(val running: Boolean = false, val callId: String? = null, val energy: Float = 0f, val error: String? = null)
