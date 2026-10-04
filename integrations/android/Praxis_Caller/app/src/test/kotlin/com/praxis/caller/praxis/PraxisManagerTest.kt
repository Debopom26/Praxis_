package com.praxis.caller.praxis

import io.praxis.sdk.*
import kotlinx.coroutines.*
import org.junit.Assert.*
import org.junit.Test
import java.io.Closeable

class PraxisManagerTest {
    private val settings = PraxisSettings("https://example.com/", "test", "host")
    private class Port : PraxisPort {
        var callback: ((PraxisEvent) -> Unit)? = null
        @Volatile var closed = false; @Volatile var stopped = false; @Volatile var ended = false
        var frames = 0; var failStart = false
        override fun listen(callback: (PraxisEvent) -> Unit): Closeable { this.callback = callback; return Closeable {} }
        override suspend fun start(callId: String): String { if (failStart) error("TEST_FAILURE"); return "s" }
        override suspend fun end(sessionId: String) { ended = true }
        override fun stopStreaming() { stopped = true }
        override fun audio(sessionId: String, bytes: ByteArray, timestamp: Long) { frames++ }
        override fun close() { closed = true }
    }
    private fun manager(port: Port, analyzer: SuppliedAnalyzerPort = SuppliedAnalysisClient()) =
        PraxisManager({ _, _ -> port }, CoroutineScope(SupervisorJob() + Dispatchers.Unconfined), analyzer)
    @Test fun missingConfigurationAndTokenNeverConstructClient() = runBlocking {
        var built = 0
        val m = PraxisManager({ _, _ -> built++; Port() }, this)
        m.connect("c", null) { "test" }; assertEquals(PraxisStatus.CONFIGURATION_REQUIRED, m.state.value.status)
        m.connect("c", settings) { "" }; assertEquals(PraxisStatus.AUTH_REQUIRED, m.state.value.status)
        assertEquals(0, built)
    }
    @Test fun sessionIdDoesNotInventConnectionAndFramesAreGated() = runBlocking {
        val p = Port(); val m = manager(p); m.connect("c", settings) { "test" }
        assertEquals(PraxisStatus.CONNECTING, m.state.value.status)
        assertFalse(m.sendAudio("c", ByteArray(640), 1))
        p.callback!!(PraxisEvent.Connection(true, emptyList()))
        assertFalse(m.sendAudio("wrong", ByteArray(640), 1)); assertFalse(m.sendAudio("c", ByteArray(2), 1))
        assertTrue(m.sendAudio("c", ByteArray(640), 1)); assertFalse(m.sendAudio("c", ByteArray(640), 1))
        m.disconnect(); withTimeout(3000) { while (!p.closed || !p.ended) delay(10) }
        assertTrue(p.stopped)
        assertFalse(m.sendAudio("c", ByteArray(640), 2)); assertEquals(1, p.frames)
    }
    @Test fun staleCallbacksAndDisconnectCannotResurrectResults() = runBlocking {
        val p = Port(); val m = manager(p); m.connect("c", settings) { "test" }; val old = p.callback!!
        old(PraxisEvent.Connection(true, emptyList())); old(PraxisEvent.Connection(false, emptyList()))
        assertEquals(PraxisStatus.RECONNECTING, m.state.value.status)
        assertTrue(m.sendAudio("c", ByteArray(640), 1))
        assertEquals(0, p.frames)
        old(PraxisEvent.Connection(true, emptyList()))
        assertEquals(PraxisStatus.CONNECTED, m.state.value.status)
        assertTrue(m.sendAudio("c", ByteArray(640), 2))
        assertEquals(1, p.frames)
        m.disconnect()
        withTimeout(3000) { while (!p.closed) delay(10) }
        old(PraxisEvent.Connection(true, emptyList()))
        assertEquals(PraxisStatus.NOT_CONNECTED, m.state.value.status)
        assertTrue(p.stopped)
    }
    @Test fun failedStartClosesClientAndDoesNotThrowIntoPhone() = runBlocking {
        val p = Port().apply { failStart = true }; val m = manager(p); m.connect("c", settings) { "test" }
        withTimeout(3000) { while (!p.closed) delay(10) }
        assertEquals(PraxisStatus.ERROR, m.state.value.status)
    }
    @Test fun foreignStaleAndDuplicateDecisionsAreFiltered() = runBlocking {
        val p = Port(); val m = manager(p); m.connect("test-call", settings) { "test" }
        p.callback!!(PraxisEvent.Connection(true, emptyList()))
        val raw = javaClass.classLoader!!.getResourceAsStream("PolicyEvent.json")!!.bufferedReader().use { it.readText() }
        val event = PraxisWire.decode(raw) as PraxisEvent.Policy
        val matching = event.copy(value = event.value.copy(callId = "test-call"))
        p.callback!!(event.copy(value = event.value.copy(callId = "other")))
        assertNull(m.state.value.decision)
        p.callback!!(matching); val decision = m.state.value.decisionId!!
        assertTrue(m.consumeDecisionSound(decision)); assertFalse(m.consumeDecisionSound(decision))
        p.callback!!(matching); assertEquals(decision, m.state.value.decisionId)
        p.callback!!(matching.copy(value = matching.value.copy(timestamp = "2000-01-01T00:00:00Z", windowId = "old")))
        assertEquals(decision, m.state.value.decisionId)
        m.disconnect()
    }
    @Test fun configurationRejectsInsecureAndAmbiguousOrigins() {
        for (url in listOf("http://example.com/", "https://u:p@example.com/", "https://example.com/path", "https://example.com/?token=x", "https://example.com/#x")) {
            assertFalse(PraxisSettings.secureUrl(url, true))
        }
        assertTrue(PraxisSettings.secureUrl("https://example.com/", true))
    }
    @Test fun oneSecondVoipBlocksUseExistingSdkContract() = runBlocking {
        val p = Port(); val m = manager(p); m.connect("c", settings) { "test" }
        p.callback!!(PraxisEvent.Connection(true, emptyList()))
        assertTrue(m.sendAudio("c", ByteArray(32000), 1000))
        assertTrue(m.sendAudio("c", ByteArray(32000), 2000))
        assertFalse(m.sendAudio("c", ByteArray(32001), 3000))
        assertEquals(2, p.frames)
        m.disconnect()
    }
    @Test fun twoSecondBlocksProduceBoundedOverlappingV2Window() = runBlocking {
        val analyzer = object : SuppliedAnalyzerPort {
            var calls = 0
            override suspend fun analyze(settings: PraxisSettings, token: String, sessionId: String,
                pcmS16le: ByteArray): SuppliedResult {
                calls++; assertEquals(128000, pcmS16le.size)
                return SuppliedResult(42.0, 75.0, "AI_NOTICE", "No scam indicators.", "BOOTSTRAP_UNTRAINED")
            }
        }
        val p = Port(); val m = manager(p, analyzer)
        m.connect("c", PraxisSettings.passwordSettings("https://example.com", "test")) { "test" }
        p.callback!!(PraxisEvent.Connection(true, emptyList()))
        repeat(200) { assertTrue(m.sendAudio("c", ByteArray(640) { 1 }, it.toLong())) }
        assertEquals(1, analyzer.calls)
        assertEquals(42.0, m.state.value.experimentalScore!!, 0.0)
        assertEquals("BOOTSTRAP_UNTRAINED", m.state.value.regressorStatus)
        p.callback!!(PraxisEvent.Gap(listOf("SEQUENCE_GAP")))
        assertEquals(42.0, m.state.value.experimentalScore!!, 0.0)
        assertEquals("AI NOTICE", m.state.value.decision)
        val decisionId = m.state.value.decisionId!!
        assertTrue(m.consumeDecisionSound(decisionId))
        repeat(100) { assertTrue(m.sendAudio("c", ByteArray(640) { 1 }, (it + 200).toLong())) }
        assertEquals(decisionId, m.state.value.decisionId)
        assertFalse(m.consumeDecisionSound(decisionId))
        m.disconnect()
    }
    @Test fun silentMicrophoneDoesNotProduceOrRetainScoreAndRecoveryResumes() = runBlocking {
        val analyzer = object : SuppliedAnalyzerPort {
            var calls = 0
            override suspend fun analyze(settings: PraxisSettings, token: String, sessionId: String,
                pcmS16le: ByteArray): SuppliedResult {
                calls++
                return SuppliedResult(42.0, 75.0, "AI_NOTICE", "No scam indicators.", "BOOTSTRAP_UNTRAINED")
            }
        }
        val p = Port(); val m = manager(p, analyzer)
        m.connect("c", PraxisSettings.passwordSettings("https://example.com", "test")) { "test" }
        p.callback!!(PraxisEvent.Connection(true, emptyList()))
        repeat(200) { assertTrue(m.sendAudio("c", ByteArray(640), it.toLong())) }
        assertEquals(0, analyzer.calls)
        assertNull(m.state.value.experimentalScore)
        assertTrue(m.state.value.inputSilent)
        assertEquals("Analysis unavailable", m.state.value.lastEvent)
        repeat(100) { assertTrue(m.sendAudio("c", ByteArray(640) { 1 }, (it + 200).toLong())) }
        assertEquals(1, analyzer.calls)
        assertEquals(42.0, m.state.value.experimentalScore!!, 0.0)
        assertFalse(m.state.value.inputSilent)
        repeat(200) { assertTrue(m.sendAudio("c", ByteArray(640), (it + 300).toLong())) }
        assertNull(m.state.value.experimentalScore)
        assertTrue(m.state.value.inputSilent)
        assertNull(m.state.value.decision)
        m.disconnect()
    }
}
