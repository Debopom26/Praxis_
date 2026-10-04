package com.praxis.caller.praxis

import io.praxis.sdk.PraxisClient
import io.praxis.sdk.PraxisConfig
import io.praxis.sdk.PraxisEvent
import io.praxis.sdk.contracts.AudioFormat
import java.io.Closeable
import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

// This seam is owned by the app; every production method delegates to the supplied SDK.
internal interface PraxisPort : Closeable {
    fun listen(callback: (PraxisEvent) -> Unit): Closeable
    suspend fun start(callId: String): String
    suspend fun end(sessionId: String)
    fun stopStreaming()
    fun audio(sessionId: String, bytes: ByteArray, timestamp: Long)
}
internal class SdkPort(private val client: PraxisClient) : PraxisPort {
    constructor(settings: PraxisSettings, token: () -> String) : this(PraxisClient(PraxisConfig(settings.baseUrl, settings.tenantId, settings.hostAppId, token,
        maxBufferedFrames = 25, maxBufferedAudioBytes = 96000)))
    override fun listen(callback: (PraxisEvent) -> Unit) = client.onEvent(callback)
    override suspend fun start(callId: String) = client.startSession(callId)
    override suspend fun end(sessionId: String) = client.endSession(sessionId)
    override fun audio(sessionId: String, bytes: ByteArray, timestamp: Long) =
        client.streamAudio(sessionId, bytes, timestamp, AudioFormat("pcm_s16le", 16000, 1))
    override fun stopStreaming() = client.stopStreaming()
    override fun close() = client.close()
}
enum class PraxisStatus { NOT_CONNECTED, CONFIGURATION_REQUIRED, AUTH_REQUIRED, CONNECTING, CONNECTED, RECONNECTING, ERROR }
data class PraxisState(val status: PraxisStatus = PraxisStatus.NOT_CONNECTED,
    val callId: String? = null, val sessionId: String? = null, val framesSent: Long = 0,
    val lastEvent: String? = null, val risk: Double? = null, val decision: String? = null,
    val decisionId: String? = null, val detail: String? = null, val error: String? = null,
    val experimentalScore: Double? = null, val syntheticScore: Double? = null,
    val regressorStatus: String? = null, val inputSilent: Boolean = false)

class PraxisManager internal constructor(
    private val factory: (PraxisSettings, () -> String) -> PraxisPort,
    private val scope: CoroutineScope,
    private val analyzer: SuppliedAnalyzerPort = SuppliedAnalysisClient(),
) {
    constructor() : this({ settings, token -> SdkPort(settings, token) }, CoroutineScope(SupervisorJob() + Dispatchers.IO))
    private val lock = Any()
    private val lifecycle = Mutex()
    private val mutable = MutableStateFlow(PraxisState())
    val state = mutable.asStateFlow()
    private var epoch = 0L
    private var client: PraxisPort? = null
    private var listener: Closeable? = null
    private var cleanup: Job? = null
    private var analysisJob: Job? = null
    private var analysisRevision = 0L
    private var analysisSettings: PraxisSettings? = null
    private var analysisToken: (() -> String)? = null
    private var previousBlock: ByteArray? = null
    private val currentBlock = java.io.ByteArrayOutputStream(64000)
    private var lastTimestamp = -1L
    private var lastResultTime = java.time.Instant.MIN
    private val seen = linkedSetOf<String>()
    private val sounded = linkedSetOf<String>()
    fun consumeDecisionSound(id: String): Boolean = synchronized(lock) {
        if (!sounded.add(id)) return false
        if (sounded.size > 128) sounded.remove(sounded.first())
        true
    }

    suspend fun connect(callId: String, settings: PraxisSettings?, token: () -> String) = lifecycle.withLock {
        cleanup?.join()
        val generation = synchronized(lock) {
            if (client != null) return@withLock
            if (settings == null) { mutable.value = PraxisState(PraxisStatus.CONFIGURATION_REQUIRED, error = "Praxis configuration is required."); return@withLock }
            if (runCatching { token() }.getOrDefault("").isBlank()) { mutable.value = PraxisState(PraxisStatus.AUTH_REQUIRED); return@withLock }
            epoch++; lastTimestamp = -1; lastResultTime = java.time.Instant.MIN; seen.clear()
            mutable.value = PraxisState(PraxisStatus.CONNECTING, callId)
            epoch
        }
        try {
            val port = factory(checkNotNull(settings), token)
            synchronized(lock) {
                if (generation != epoch) { port.close(); return@withLock }
                client = port
                analysisSettings = settings
                analysisToken = token
                listener = port.listen { event -> receive(generation, callId, event) }
            }
            val id = withContext(Dispatchers.IO) { port.start(callId) }
            synchronized(lock) { if (generation == epoch) mutable.value = mutable.value.copy(sessionId = id) }
        } catch (e: CancellationException) { disconnect(); throw e }
        catch (e: Exception) {
            runCatching { Log.e("PraxisTransport", "Session connect failed", e) }
            val message = if (e.message == "PRAXIS_HTTP_409")
                "This call already has a Praxis session. Start a new call to reconnect."
            else "Praxis connection failed. Check configuration and sign in again."
            fail(generation, message)
        }
    }
    private fun receive(generation: Long, callId: String, event: PraxisEvent) {
        synchronized(lock) {
            if (generation != epoch || client == null) return
            val current = mutable.value
            when (event) {
                is PraxisEvent.Connection -> {
                    if (!event.connected) {
                        runCatching { Log.w("PraxisTransport", "WSS disconnected; SDK reconnecting: ${event.reasons.joinToString()}") }
                        mutable.value = current.copy(status = PraxisStatus.RECONNECTING, lastEvent = "Reconnecting", error = "Praxis stream reconnecting.")
                        return
                    }
                    runCatching { Log.i("PraxisTransport", "WSS connected") }
                    mutable.value = current.copy(status = PraxisStatus.CONNECTED, lastEvent = "Connected", error = null)
                }
                is PraxisEvent.Error -> {
                    runCatching { Log.w("PraxisTransport", "SDK error: ${event.code}") }
                    fail(generation, "Praxis reported an error. Reconnect or sign in again.")
                    return
                }
                is PraxisEvent.Gap -> mutable.value = if (current.experimentalScore != null)
                    current.copy(lastEvent = "Audio gap")
                else current.copy(lastEvent = "Audio gap", risk = null, decision = null,
                    decisionId = null, detail = "Some audio was not analyzed.")
                is PraxisEvent.Risk -> {
                    val value = event.value
                    if (value.callId != callId || value.riskDisplay0100 !in 0.0..100.0) return
                    if (!accept("risk:${value.windowId}:${value.timestamp}", value.timestamp)) return
                    mutable.value = current.copy(risk = value.riskDisplay0100, lastEvent = "Risk update",
                        detail = value.evidenceSummary.joinToString("; ") { it.module + ": " + it.status.name }.take(2000))
                }
                is PraxisEvent.Policy -> {
                    val value = event.value
                    if (value.callId != callId || !accept("policy:${value.windowId}:${value.action}:${value.timestamp}", value.timestamp)) return
                    val key = "$callId:${value.windowId}:${value.action}:${value.policyVersion}"
                    mutable.value = current.copy(decision = value.action.name.replace('_', ' '), decisionId = key,
                        detail = value.triggeringThresholdOrRule.take(2000), lastEvent = "Policy decision")
                }
                is PraxisEvent.Unavailable -> if (event.value.callId == callId) {
                    mutable.value = if (current.experimentalScore != null || current.inputSilent) current else current.copy(
                        risk = null, decision = null, decisionId = null,
                        lastEvent = "Analysis unavailable",
                        detail = "Analysis unavailable: " + event.value.module.take(100))
                }
                else -> {
                    val eventCall = when (event) {
                        is PraxisEvent.Evidence -> event.value.callId; is PraxisEvent.Speaker -> event.value.callId
                        is PraxisEvent.Linguistic -> event.value.callId; is PraxisEvent.AiText -> event.value.callId
                        is PraxisEvent.Transcript -> event.value.callId; is PraxisEvent.Context -> event.value.callId
                        is PraxisEvent.Audio -> event.value.callId; else -> null
                    }
                    if (eventCall == callId && !(current.inputSilent && event is PraxisEvent.Audio))
                        mutable.value = current.copy(lastEvent = event.javaClass.simpleName)
                }
            }
        }
    }
    private fun accept(key: String, timestamp: String): Boolean {
        val time = runCatching { java.time.Instant.parse(timestamp) }.getOrNull() ?: return false
        if (time < lastResultTime || key in seen) return false
        lastResultTime = time; seen.add(key)
        if (seen.size > 128) seen.remove(seen.first())
        return true
    }
    fun sendAudio(callId: String, bytes: ByteArray, timestamp: Long): Boolean = synchronized(lock) {
        val s = mutable.value
        if (s.status !in setOf(PraxisStatus.CONNECTED, PraxisStatus.RECONNECTING) || s.callId != callId || s.sessionId == null ||
            bytes.size !in setOf(640, 32000) || timestamp <= lastTimestamp || timestamp < 0) return false
        if (s.status == PraxisStatus.RECONNECTING) {
            // The supplied SDK rejects frames while its WSS is down. Do not retain raw audio;
            // keep the consented capture service alive and resume on the next connection event.
            lastTimestamp = timestamp
            return true
        }
        try {
            client?.audio(s.sessionId, bytes, timestamp) ?: return false
            lastTimestamp = timestamp
            mutable.value = s.copy(framesSent = s.framesSent + 1)
            queueSuppliedAnalysis(bytes)
            true // Enqueued in real SDK, not a server ACK.
        } catch (e: Exception) {
            runCatching { Log.e("PraxisTransport", "Audio transmission failed", e) }
            fail(epoch, "Audio transmission stopped.")
            false
        }
    }
    private fun queueSuppliedAnalysis(bytes: ByteArray) {
        val settings = analysisSettings ?: return
        if (!settings.acousticInputApproved || !settings.passwordLogin) return
        currentBlock.write(bytes)
        if (currentBlock.size() < 64000) return
        val block = currentBlock.toByteArray(); currentBlock.reset()
        val previous = previousBlock; previousBlock = block
        val session = mutable.value.sessionId ?: return
        if (previous == null) return
        val generation = epoch
        val window = previous + block
        if (window.all { it == 0.toByte() }) {
            analysisRevision++
            analysisJob?.cancel(); analysisJob = null
            mutable.value = mutable.value.copy(risk = null, experimentalScore = null,
                syntheticScore = null, regressorStatus = null, decision = null, decisionId = null,
                inputSilent = true, lastEvent = "Analysis unavailable",
                detail = "No microphone audio reached Praxis during this call. Check the phone's microphone access.")
            return
        }
        if (analysisJob?.isActive == true) return
        val revision = ++analysisRevision
        val token = analysisToken ?: return
        analysisJob = scope.launch {
            try {
                val result = analyzer.analyze(settings, token(), session, window)
                synchronized(lock) {
                    if (generation == epoch && revision == analysisRevision && mutable.value.sessionId == session) {
                        mutable.value = mutable.value.copy(risk = null,
                            experimentalScore = result.experimentalScore,
                            syntheticScore = result.syntheticScore,
                            regressorStatus = result.regressorStatus,
                            inputSilent = false,
                            decision = result.action.replace('_', ' '),
                            decisionId = "v2:$session:${result.action}",
                            detail = result.message, lastEvent = "Experimental analysis")
                        runCatching { Log.i("PraxisTransport", "V2 analysis result displayed") }
                    }
                }
            } catch (error: Exception) {
                Log.w("PraxisTransport", "V2 request failed type=${error.javaClass.simpleName}")
                synchronized(lock) {
                    if (generation == epoch) mutable.value = mutable.value.copy(
                        lastEvent = "Analysis unavailable", detail = "V2 analysis unavailable.")
                }
            }
        }
    }
    private fun fail(generation: Long, message: String) {
        synchronized(lock) { if (generation != epoch) return; disconnect(); mutable.value = PraxisState(PraxisStatus.ERROR, error = message) }
    }
    fun disconnect() {
        synchronized(lock) {
            epoch++
            val port = client; val session = mutable.value.sessionId
            client = null; listener?.close(); listener = null
            analysisJob?.cancel(); analysisJob = null
            analysisSettings = null; analysisToken = null
            previousBlock = null; currentBlock.reset()
            mutable.value = PraxisState()
            seen.clear()
            if (port != null) cleanup = scope.launch(Dispatchers.IO) {
                val watchdog = launch { delay(2000); runCatching { port.close() } }
                try {
                    port.stopStreaming()
                    if (session != null) port.end(session)
                } catch (_: Exception) { /* Call cleanup never blocks the phone UI. */ }
                finally { watchdog.cancel(); runCatching { port.close() } }
            }
        }
    }
}
