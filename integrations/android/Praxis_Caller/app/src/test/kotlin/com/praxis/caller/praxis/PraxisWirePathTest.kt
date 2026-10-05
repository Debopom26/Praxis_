package com.praxis.caller.praxis

import io.praxis.sdk.*
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.first
import okhttp3.*
import okhttp3.mockwebserver.*
import org.junit.Assert.*
import org.junit.Test
import java.util.concurrent.TimeUnit

/** Synthetic audio and local loopback server: verifies the real adapter/SDK path, not production analysis. */
class PraxisWirePathTest {
    @Test fun realSdkCarriesFramesAndEventsWithoutOwningTelephony() = runBlocking {
        val risk = javaClass.classLoader!!.getResourceAsStream("RiskEvent.json")!!.bufferedReader().use { it.readText() }
        val callId = (PraxisWire.decode(risk) as PraxisEvent.Risk).value.callId
        MockWebServer().use { server ->
            server.enqueue(MockResponse().setBody("""{"tenant_id":"t","call_id":"$callId","host_app_id":"h","created_at":"2026-09-20T00:00:00Z","session_id":"s"}"""))
            server.enqueue(MockResponse().withWebSocketUpgrade(object : WebSocketListener() {
                override fun onOpen(ws: WebSocket, response: Response) { ws.send("""{"type":"connection","status":"AVAILABLE","session_id":"s","contract_version":"1.0.0","last_sequence_id":-1,"last_timestamp_ms":-1,"reason_codes":[]}""") }
                override fun onMessage(ws: WebSocket, text: String) {
                    assertTrue(text.contains("audio_base64")); ws.send("""{"type":"ack","sequence_id":0}"""); ws.send(risk)
                }
                override fun onClosing(ws: WebSocket, code: Int, reason: String) { ws.close(code, null) }
            }))
            server.enqueue(MockResponse().setBody("{}")); server.start()
            val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
            val m = PraxisManager({ _, _ -> SdkPort(PraxisClient(PraxisConfig(server.url("/").toString(), "t", "h", { "TEST_ONLY" }, allowCleartextForTests = true))) }, scope)
            try {
                m.connect(callId, PraxisSettings("https://example.com/", "t", "h")) { "TEST_ONLY" }
                withTimeout(5000) { m.state.first { it.status == PraxisStatus.CONNECTED && it.sessionId != null } }
                assertTrue(m.sendAudio(callId, ByteArray(640), 20))
                val result = withTimeout(5000) { m.state.first { it.risk != null } }
                assertEquals(60.0, result.risk!!, 0.0)
                assertEquals(1L, result.framesSent)
                m.disconnect()
                assertFalse(m.sendAudio(callId, ByteArray(640), 40))
                val requests = (1..3).map { server.takeRequest(5, TimeUnit.SECONDS)!! }
                assertTrue(requests.any { it.path == "/api/v1/sessions/s/end" })
                assertTrue(requests.all { it.getHeader("Authorization") == "Bearer TEST_ONLY" })
            } finally { m.disconnect(); scope.coroutineContext[Job]?.children?.toList()?.forEach { it.join() }; scope.cancel() }
        }
    }
}
