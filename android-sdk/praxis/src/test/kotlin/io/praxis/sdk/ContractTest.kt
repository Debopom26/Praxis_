package io.praxis.sdk

import io.praxis.sdk.contracts.*
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.*
import kotlinx.serialization.json.*
import okhttp3.*
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.*
import org.junit.Test
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

class ContractTest {
    private val json = PraxisWire.json
    private fun fixture(name: String) = javaClass.classLoader!!.getResourceAsStream("$name.json")!!.bufferedReader().use { it.readText() }

    @Test fun canonicalFixturesRoundTrip() {
        val session = json.decodeFromString<SessionStart>(fixture("SessionStart"))
        assertEquals("test-tenant", session.tenantId)
        assertEquals(0L, json.decodeFromString<AudioFrame>(fixture("AudioFrame")).sequenceId)
        assertEquals("test-0", json.decodeFromString<AudioWindow>(fixture("AudioWindow")).windowId)
        assertEquals(SpeakerState.UNAVAILABLE, json.decodeFromString<SpeakerEvidence>(fixture("SpeakerEvidence")).speakerState)
        assertEquals("en", json.decodeFromString<TranscriptEvent>(fixture("TranscriptEvent")).language)
        assertNull(json.decodeFromString<ContextEvidence>(fixture("ContextEvidence")).contextScore)
        val risk = json.decodeFromString<RiskEvent>(fixture("RiskEvent"))
        assertEquals(60.0, risk.riskDisplay0100, 0.0)
        assertEquals(risk, json.decodeFromString<RiskEvent>(json.encodeToString(risk)))
        assertEquals(PolicyAction.SECONDARY_VERIFICATION, json.decodeFromString<PolicyEvent>(fixture("PolicyEvent")).action)
        assertEquals("UNAVAILABLE", json.decodeFromString<UnavailableEvent>(fixture("UnavailableEvent")).status)
        assertEquals("test-event", json.decodeFromString<AuditEvent>(fixture("AuditEvent")).eventId)
    }

    @Test fun riskAndUnavailableRemainSeparate() {
        assertTrue(PraxisWire.decode(fixture("RiskEvent")) is PraxisEvent.Risk)
        val unavailable = PraxisWire.decode(fixture("UnavailableEvent")) as PraxisEvent.Unavailable
        assertEquals(ArtifactState.UNVALIDATED, unavailable.value.artifactState)
        val invalid = fixture("RiskEvent").replace("60.0", "101.0")
        assertThrows(IllegalArgumentException::class.java) { PraxisWire.decode(invalid) }
    }

    @Test fun tlsAndAudioValidation() {
        assertThrows(IllegalArgumentException::class.java) { PraxisClient(PraxisConfig("http://example.com/", "t", "h", { "token" })) }
        PraxisClient(PraxisConfig("https://example.com/", "t", "h", { "token" })).use { client ->
            assertThrows(IllegalArgumentException::class.java) { client.streamAudio("s", byteArrayOf(1), 0, AudioFormat(sampleRate=16000, channels=1)) }
        }
    }

    @Test fun sessionStreamAckAndEnd() = runBlocking {
        val server = MockWebServer()
        val received = CountDownLatch(1)
        val connected = CountDownLatch(1)
        server.enqueue(MockResponse().setBody("""{"tenant_id":"t","call_id":"c","host_app_id":"h","created_at":"2026-09-20T00:00:00Z","session_id":"s"}"""))
        server.enqueue(MockResponse().withWebSocketUpgrade(object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                webSocket.send("""{"type":"connection","status":"AVAILABLE","session_id":"s","contract_version":"1.0.0","last_sequence_id":-1,"last_timestamp_ms":-1,"reason_codes":[]}""")
            }
            override fun onMessage(webSocket: WebSocket, text: String) {
                val frame = json.decodeFromString<AudioFrame>(text)
                assertEquals(0L, frame.sequenceId)
                webSocket.send("""{"type":"ack","sequence_id":0}""")
                received.countDown()
            }
            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(code, null)
            }
        }))
        server.enqueue(MockResponse().setBody("{}"))
        server.start()
        PraxisClient(PraxisConfig(server.url("/").toString(), "t", "h", { "TEST_ONLY" }, allowCleartextForTests=true)).use { client ->
            client.onEvent { if (it is PraxisEvent.Connection && it.connected) connected.countDown() }
            assertEquals("s", client.startSession("c"))
            assertTrue(connected.await(5, TimeUnit.SECONDS))
            client.streamAudio("s", ByteArray(640), 0, AudioFormat(sampleRate=16000, channels=1))
            assertTrue(received.await(5, TimeUnit.SECONDS))
            client.stopStreaming()
            assertThrows(IllegalStateException::class.java) {
                client.streamAudio("s", ByteArray(640), 20, AudioFormat(sampleRate=16000, channels=1))
            }
            client.endSession("s")
            assertEquals("Bearer TEST_ONLY", server.takeRequest().getHeader("Authorization"))
        }
        server.shutdown()
    }

    @Test fun reconnectDoesNotReplayAcceptedFrameAfterLostAck() = runBlocking {
        val server = MockWebServer()
        val firstOpen = CountDownLatch(1)
        val resumed = CountDownLatch(1)
        val nextFrame = CountDownLatch(1)
        server.enqueue(MockResponse().setBody("""{"tenant_id":"t","call_id":"c","host_app_id":"h","created_at":"2026-09-20T00:00:00Z","session_id":"s"}"""))
        fun hello(last: Long) = """{"type":"connection","status":"AVAILABLE","session_id":"s","contract_version":"1.0.0","last_sequence_id":$last,"last_timestamp_ms":$last,"reason_codes":[]}"""
        server.enqueue(MockResponse().withWebSocketUpgrade(object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) { webSocket.send(hello(-1)) }
            override fun onMessage(webSocket: WebSocket, text: String) {
                assertEquals(0L, json.decodeFromString<AudioFrame>(text).sequenceId)
                webSocket.close(1013, "Test reconnect before ACK")
            }
            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) { webSocket.close(code, null) }
        }))
        server.enqueue(MockResponse().withWebSocketUpgrade(object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) { webSocket.send(hello(0)) }
            override fun onMessage(webSocket: WebSocket, text: String) {
                assertEquals(1L, json.decodeFromString<AudioFrame>(text).sequenceId)
                nextFrame.countDown()
            }
            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) { webSocket.close(code, null) }
        }))
        server.start()
        PraxisClient(PraxisConfig(server.url("/").toString(), "t", "h", { "TEST_ONLY" }, allowCleartextForTests=true)).use { client ->
            var connections = 0
            client.onEvent { if (it is PraxisEvent.Connection && it.connected) { if (++connections == 1) firstOpen.countDown() else resumed.countDown() } }
            client.startSession("c")
            assertTrue(firstOpen.await(5, TimeUnit.SECONDS))
            client.streamAudio("s", ByteArray(640), 0, AudioFormat(sampleRate=16000, channels=1))
            assertTrue(resumed.await(10, TimeUnit.SECONDS))
            client.streamAudio("s", ByteArray(640), 20, AudioFormat(sampleRate=16000, channels=1))
            assertTrue(nextFrame.await(5, TimeUnit.SECONDS))
        }
        server.shutdown()
    }

    @Test fun transientForbiddenUpgradeRetriesWithinBoundedReconnects() = runBlocking {
        val server = MockWebServer()
        val connected = CountDownLatch(1)
        val rejected = CountDownLatch(1)
        server.enqueue(MockResponse().setBody("""{"tenant_id":"t","call_id":"c","host_app_id":"h","created_at":"2026-09-20T00:00:00Z","session_id":"s"}"""))
        server.enqueue(MockResponse().setResponseCode(403))
        server.enqueue(MockResponse().withWebSocketUpgrade(object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                webSocket.send("""{"type":"connection","status":"AVAILABLE","session_id":"s","contract_version":"1.0.0","last_sequence_id":-1,"last_timestamp_ms":-1,"reason_codes":[]}""")
            }
        }))
        server.start()
        PraxisClient(PraxisConfig(server.url("/").toString(), "t", "h", { "TEST_ONLY" }, allowCleartextForTests=true)).use { client ->
            client.onEvent {
                if (it is PraxisEvent.Connection && !it.connected) rejected.countDown()
                if (it is PraxisEvent.Connection && it.connected) connected.countDown()
            }
            client.startSession("c")
            assertTrue(rejected.await(5, TimeUnit.SECONDS))
            assertTrue(connected.await(10, TimeUnit.SECONDS))
        }
        server.shutdown()
    }
}
