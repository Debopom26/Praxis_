package com.praxis.caller.audio

import android.telecom.Call
import com.praxis.caller.telecom.CallState
import com.praxis.caller.telecom.AudioState
import com.praxis.caller.praxis.PraxisState
import com.praxis.caller.praxis.PraxisStatus

object CapturePolicy {
    fun allowed(id: String, calls: List<CallState>, audio: AudioState, praxis: PraxisState,
        inputApproved: Boolean, authenticated: Boolean): Boolean {
        val active = calls.filter { it.state == Call.STATE_ACTIVE }
        return inputApproved && authenticated && active.size == 1 && active.single().id == id &&
            praxis.callId == id && praxis.status in setOf(PraxisStatus.CONNECTED, PraxisStatus.RECONNECTING) && praxis.sessionId != null &&
            audio.routes.any { it.id == audio.selected && it.speaker } && audio.muted == false
    }
}
