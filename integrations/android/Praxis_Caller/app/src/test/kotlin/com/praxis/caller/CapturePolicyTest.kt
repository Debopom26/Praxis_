package com.praxis.caller

import android.telecom.Call
import com.praxis.caller.audio.CapturePolicy
import com.praxis.caller.telecom.*
import com.praxis.caller.praxis.*
import org.junit.Assert.*
import org.junit.Test

class CapturePolicyTest {
    private val call = CallState("c", "", Call.STATE_ACTIVE)
    private val audio = AudioState(false, listOf(AudioRoute("speaker", "Speaker", true)), "speaker")
    private val praxis = PraxisState(PraxisStatus.CONNECTED, "c", "s")
    @Test fun onlyExplicitAuthorizedActiveSpeakerPathIsEligible() {
        assertTrue(CapturePolicy.allowed("c", listOf(call), audio, praxis, true, true))
        assertFalse(CapturePolicy.allowed("c", listOf(call), audio, praxis, false, true))
        assertFalse(CapturePolicy.allowed("c", listOf(call), audio, praxis, true, false))
        assertFalse(CapturePolicy.allowed("c", listOf(call), audio.copy(muted = true), praxis, true, true))
        assertFalse(CapturePolicy.allowed("c", listOf(call), audio.copy(selected = "bluetooth"), praxis, true, true))
        assertFalse(CapturePolicy.allowed("c", listOf(call), audio, praxis.copy(status = PraxisStatus.ERROR), true, true))
        assertFalse(CapturePolicy.allowed("c", listOf(call), audio, praxis.copy(sessionId = null), true, true))
    }
    @Test fun endHoldAndMultipleCallsInvalidateCapture() {
        for (status in listOf(Call.STATE_HOLDING, Call.STATE_DISCONNECTED, Call.STATE_RINGING, Call.STATE_CONNECTING))
            assertFalse(CapturePolicy.allowed("c", listOf(call.copy(state = status)), audio, praxis, true, true))
        assertFalse(CapturePolicy.allowed("c", emptyList(), audio, praxis, true, true))
        assertFalse(CapturePolicy.allowed("c", listOf(call, call.copy(id = "other")), audio, praxis, true, true))
    }
    @Test fun durationHandlesUnconnectedAndClockSkew() {
        assertEquals(0L, call.durationSeconds(1000))
        assertEquals(0L, call.copy(connectTimeMillis = 2000).durationSeconds(1000))
        assertEquals(3L, call.copy(connectTimeMillis = 1000).durationSeconds(4500))
    }
}
