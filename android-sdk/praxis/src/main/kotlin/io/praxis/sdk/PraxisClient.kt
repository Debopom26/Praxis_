package io.praxis.sdk

import io.praxis.sdk.contracts.*
import java.io.Closeable
import java.io.IOException
import java.time.Instant
import java.util.Base64
import java.util.TreeMap
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.*
import kotlinx.serialization.json.*
import okhttp3.*
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody

data class PraxisConfig(
    val baseUrl: String,
    val tenantId: String,
    val hostAppId: String,
    val tokenProvider: () -> String,
    val maxBufferedAudioBytes: Int = 384000,
    val maxBufferedFrames: Int = 100,
    val allowCleartextForTests: Boolean = false,
)

sealed interface PraxisEvent {
    data class Evidence(val value: ModuleEvidence) : PraxisEvent
    data class Speaker(val value: SpeakerEvidence) : PraxisEvent
    data class Linguistic(val value: LinguisticEvidence) : PraxisEvent
    data class AiText(val value: AIWrittenEvidence) : PraxisEvent
    data class Transcript(val value: TranscriptEvent) : PraxisEvent
    data class Context(val value: ContextEvidence) : PraxisEvent
    data class Audio(val value: AudioWindow) : PraxisEvent
    data class Risk(val value: RiskEvent) : PraxisEvent
    data class Policy(val value: PolicyEvent) : PraxisEvent
    data class Unavailable(val value: UnavailableEvent) : PraxisEvent
    data class Connection(val connected: Boolean, val reasons: List<String>) : PraxisEvent
    data class Gap(val reasons: List<String>) : PraxisEvent
    data class Error(val code: String) : PraxisEvent
}

object PraxisWire {
    val json = Json { ignoreUnknownKeys = true; encodeDefaults = false; explicitNulls = false }
    fun decode(message: String): PraxisEvent? {
        require(message.length <= 1048576) { "EVENT_TOO_LARGE" }
        val value = json.parseToJsonElement(message).jsonObject
        return when (value["type"]?.jsonPrimitive?.content) {
            "evidence" -> when (value["module"]?.jsonPrimitive?.content) {
                "speaker" -> PraxisEvent.Speaker(json.decodeFromJsonElement(value))
                "linguistic_rules", "linguistic" -> PraxisEvent.Linguistic(json.decodeFromJsonElement(value))
                "ai_text" -> PraxisEvent.AiText(json.decodeFromJsonElement(value))
                else -> PraxisEvent.Evidence(json.decodeFromJsonElement(value))
            }
            "transcript" -> PraxisEvent.Transcript(json.decodeFromJsonElement(value))
            "context" -> PraxisEvent.Context(json.decodeFromJsonElement(value))
            "audio_window" -> PraxisEvent.Audio(json.decodeFromJsonElement(value))
            "risk" -> {
                val event = json.decodeFromJsonElement<RiskEvent>(value)
                require(event.riskRaw0100 in 0.0..100.0 && event.riskDisplay0100 in 0.0..100.0)
                PraxisEvent.Risk(event)
            }
            "policy" -> PraxisEvent.Policy(json.decodeFromJsonElement(value))
            "unavailable" -> PraxisEvent.Unavailable(json.decodeFromJsonElement(value))
            "analysis_gap" -> PraxisEvent.Gap(json.decodeFromJsonElement<AnalysisGapEvent>(value).reasonCodes)
            "ack", "pong", "connection" -> null
            else -> throw SerializationException("UNKNOWN_EVENT_TYPE")
        }
    }
}

/** An authorized remote-PCM integration layer. It never captures a microphone or owns a call. */
class PraxisClient(private val config: PraxisConfig) : Closeable {
    private val root = config.baseUrl.toHttpUrl()
    private val json = PraxisWire.json
    private val http = OkHttpClient.Builder().connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS).pingInterval(60, TimeUnit.SECONDS)
        .followRedirects(false).followSslRedirects(false).build()
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val eventQueue = Channel<PraxisEvent>(64)
    private val listeners = CopyOnWriteArrayList<(PraxisEvent) -> Unit>()
    private val lock = Any()
    private val lifecycle = Mutex()
    private val pending = TreeMap<Long, Pair<String, Int>>()
    private var bufferedBytes = 0
    private var nextSequence = 0L
    private var lastSent = -1L
    private var lastTimestamp = -1L
    private var session: String? = null
    private var socket: WebSocket? = null
    private val ownedSockets = mutableSetOf<WebSocket>()
    private var connected = false
    private var streamingStopped = false
    private var closed = false
    private var reconnectAttempt = 0
    private var reconnectJob: Job? = null
    private var heartbeat: Job? = null

    init {
        require(root.isHttps || (config.allowCleartextForTests && root.host in setOf("localhost", "127.0.0.1"))) { "HTTPS_REQUIRED" }
        require(root.username.isEmpty() && root.password.isEmpty() && root.query == null && root.encodedPath == "/")
        require(config.maxBufferedAudioBytes in 1920..1048576 && config.maxBufferedFrames in 1..200)
        scope.launch { for (event in eventQueue) listeners.forEach { callback -> runCatching { callback(event) } } }
    }

    fun onEvent(callback: (PraxisEvent) -> Unit): Closeable {
        listeners.add(callback)
        return Closeable { listeners.remove(callback) }
    }
    fun onRiskUpdate(callback: (RiskEvent) -> Unit) = onEvent { if (it is PraxisEvent.Risk) callback(it.value) }
    fun onPolicyAction(callback: (PolicyEvent) -> Unit) = onEvent { if (it is PraxisEvent.Policy) callback(it.value) }

    private fun emit(event: PraxisEvent) {
        if (eventQueue.trySend(event).isFailure && !closed) {
            // Stop consuming when the host cannot keep up; no unbounded callback backlog.
            synchronized(lock) { socket?.cancel(); connected = false }
            eventQueue.tryReceive()
            eventQueue.trySend(PraxisEvent.Error("CALLBACK_BACKPRESSURE"))
        }
    }

    private fun url(vararg segments: String): HttpUrl = root.newBuilder().apply {
        addPathSegment("api"); addPathSegment("v1"); segments.forEach { addPathSegment(it) }
    }.build()

    private suspend fun request(method: String, path: List<String>, body: String? = null): String = withContext(Dispatchers.IO) {
        check(!closed) { "CLIENT_CLOSED" }
        val token = config.tokenProvider()
        require(token.isNotBlank()) { "ACCESS_TOKEN_REQUIRED" }
        val request = Request.Builder().url(url(*path.toTypedArray())).header("Authorization", "Bearer $token")
            .method(method, body?.toRequestBody("application/json".toMediaType())).build()
        http.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw IOException("PRAXIS_HTTP_${response.code}")
            val responseBody = response.body ?: throw IOException("EMPTY_RESPONSE")
            val source = responseBody.source()
            source.request(1048577)
            if (source.buffer.size > 1048576) throw IOException("RESPONSE_TOO_LARGE")
            source.readUtf8()
        }
    }

    suspend fun startSession(callId: String, context: ContextInput = ContextInput(), claimedIdentity: String? = null, supportsHold: Boolean = false): String = lifecycle.withLock {
        synchronized(lock) { check(session == null) { "SESSION_ALREADY_ACTIVE" } }
        val value = SessionStart(tenantId=config.tenantId, callId=callId, hostAppId=config.hostAppId,
            claimedIdentity=claimedIdentity, permittedContext=context, createdAt=Instant.now().toString(), supportsHold=supportsHold)
        val response = json.decodeFromString<SessionView>(request("POST", listOf("sessions"), json.encodeToString(value)))
        synchronized(lock) {
            check(!closed && session == null)
            session = response.sessionId
            streamingStopped = false
            nextSequence = 0; lastTimestamp = -1; lastSent = -1
        }
        connect()
        response.sessionId
    }

    /** PCM must be the authorized remote caller stream; timestamps use one monotonic call timeline. */
    fun streamAudio(sessionId: String, audioFrame: ByteArray, timestamp: Long, format: AudioFormat) {
        require(format.sampleRate in setOf(8000L,16000L,24000L,32000L,44100L,48000L) && format.channels in 1L..2L)
        require(audioFrame.isNotEmpty() && audioFrame.size % (2 * format.channels).toInt() == 0)
        require(audioFrame.size <= format.sampleRate * format.channels * 2 && timestamp in 0..9007199254740991L)
        synchronized(lock) {
            check(!closed && session == sessionId) { "SESSION_NOT_ACTIVE" }
            check(!streamingStopped) { "SESSION_NOT_STREAMING" }
            require(timestamp > lastTimestamp && nextSequence <= 9007199254740991L)
            val sequence = nextSequence++
            lastTimestamp = timestamp
            val payload = json.encodeToString(AudioFrame(sequenceId=sequence, timestampMs=timestamp, format=format,
                audioBase64=Base64.getEncoder().encodeToString(audioFrame)))
            if (audioFrame.size > config.maxBufferedAudioBytes) {
                emit(PraxisEvent.Gap(listOf("FRAME_EXCEEDS_BUFFER")))
                return
            }
            var gap = false
            while (pending.size >= config.maxBufferedFrames || bufferedBytes + audioFrame.size > config.maxBufferedAudioBytes) {
                bufferedBytes -= checkNotNull(pending.pollFirstEntry()).value.second
                gap = true
            }
            pending[sequence] = payload to audioFrame.size
            bufferedBytes += audioFrame.size
            if (gap) emit(PraxisEvent.Gap(listOf("SDK_BUFFER_OVERFLOW")))
            flush()
        }
    }

    private fun flush() {
        val ws = socket ?: return
        if (!connected) return
        for ((sequence, frame) in pending.tailMap(lastSent + 1)) {
            if (ws.queueSize() + frame.first.length > 1048576 || !ws.send(frame.first)) return
            lastSent = sequence
        }
    }

    private fun acknowledge(sequence: Long) {
        val iterator = pending.entries.iterator()
        while (iterator.hasNext()) {
            val entry = iterator.next()
            if (entry.key > sequence) break
            bufferedBytes -= entry.value.second
            iterator.remove()
        }
    }

    private fun connect() {
        synchronized(lock) {
            val id = session ?: return
            if (closed) return
            connected = false
            val token = config.tokenProvider()
            if (token.isBlank()) { emit(PraxisEvent.Error("ACCESS_TOKEN_REQUIRED")); return }
            socket = http.newWebSocket(Request.Builder().url(url("stream", id)).header("Authorization", "Bearer $token").build(), object : WebSocketListener() {
                override fun onMessage(webSocket: WebSocket, text: String) {
                    synchronized(lock) {
                        if (socket !== webSocket) return
                        try {
                            require(text.length <= 1048576)
                            val data = json.parseToJsonElement(text).jsonObject
                            when (data["type"]?.jsonPrimitive?.content) {
                                "connection" -> {
                                    val hello = json.decodeFromJsonElement<ConnectionEvent>(data)
                                    require(hello.contractVersion.substringBefore('.') == "1" && hello.sessionId == session)
                                    acknowledge(hello.lastSequenceId)
                                    nextSequence = maxOf(nextSequence, hello.lastSequenceId + 1)
                                    lastTimestamp = maxOf(lastTimestamp, hello.lastTimestampMs)
                                    lastSent = hello.lastSequenceId
                                    connected = true
                                    reconnectAttempt = 0
                                    emit(PraxisEvent.Connection(true, hello.reasonCodes))
                                    heartbeat?.cancel()
                                    heartbeat = scope.launch { while (isActive) { delay(10000); webSocket.send("{\"type\":\"ping\"}") } }
                                    flush()
                                }
                                "ack" -> { acknowledge(json.decodeFromJsonElement<AckEvent>(data).sequenceId); flush() }
                                else -> PraxisWire.decode(text)?.let(::emit)
                            }
                        } catch (_: Exception) {
                            emit(PraxisEvent.Error("INVALID_SERVER_EVENT"))
                            webSocket.close(1002, "Invalid contract")
                        }
                    }
                }
                override fun onClosing(webSocket: WebSocket, code: Int, reason: String) { webSocket.close(code, null) }
                override fun onClosed(webSocket: WebSocket, code: Int, reason: String) = disconnected(webSocket, code)
                // A pre-upgrade 403 can mean the previous socket still owns this session.
                // Keep bounded reconnects for that transient overlap; a 401 remains terminal.
                override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) =
                    disconnected(webSocket, if (response?.code == 401) 1008 else 1013)
            })
            socket?.let(ownedSockets::add)
        }
    }

    private fun disconnected(ws: WebSocket, code: Int) {
        synchronized(lock) {
            ownedSockets.remove(ws)
            if (socket !== ws || closed || session == null) return
            connected = false
            heartbeat?.cancel()
            emit(PraxisEvent.Connection(false, listOf("STREAM_DISCONNECTED")))
            if (code in listOf(1000,1002,1007,1008,1009)) { emit(PraxisEvent.Error("STREAM_REJECTED_$code")); return }
            if (reconnectAttempt >= 8) { emit(PraxisEvent.Error("RECONNECT_LIMIT")); return }
            reconnectJob?.cancel()
            val delayMs = minOf(30000L, 1000L shl reconnectAttempt++)
            reconnectJob = scope.launch { delay(delayMs); connect() }
        }
    }

    fun reconnect() { synchronized(lock) { socket?.cancel(); socket = null; reconnectAttempt = 0 }; connect() }
    suspend fun updateContext(sessionId: String, contextPatch: ContextInput) {
        request("PATCH", listOf("sessions", sessionId, "context"), json.encodeToString(contextPatch))
    }
    /** JsonObject permits an explicit JSON null when clearing a previously supplied fact. */
    suspend fun updateContext(sessionId: String, contextPatch: JsonObject) {
        request("PATCH", listOf("sessions", sessionId, "context"), contextPatch.toString())
    }
    suspend fun endSession(sessionId: String) {
        try { request("POST", listOf("sessions", sessionId, "end"), "{}") }
        finally { synchronized(lock) { if (session == sessionId) { session = null; clearStream() } } }
    }
    fun stopStreaming() {
        synchronized(lock) {
            streamingStopped = true
            clearStream()
        }
    }
    private fun clearStream() {
        heartbeat?.cancel(); reconnectJob?.cancel(); socket?.close(1000, "Session ended")
        socket = null; connected = false; pending.clear(); bufferedBytes = 0
    }
    override fun close() {
        synchronized(lock) {
            closed = true; session = null; clearStream()
            // Also terminate peers that never completed an earlier graceful close.
            ownedSockets.forEach { it.cancel() }
            ownedSockets.clear()
        }
        eventQueue.close(); scope.cancel(); listeners.clear()
        http.dispatcher.cancelAll(); http.dispatcher.executorService.shutdown(); http.connectionPool.evictAll()
    }
}
