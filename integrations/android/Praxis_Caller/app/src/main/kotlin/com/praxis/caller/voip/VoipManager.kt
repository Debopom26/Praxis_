package com.praxis.caller.voip

import android.os.SystemClock
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.media.AudioAttributes
import android.media.Ringtone
import android.media.RingtoneManager
import android.util.Log
import com.praxis.caller.CallerApplication
import com.praxis.caller.MainActivity
import com.praxis.caller.R
import com.praxis.caller.auth.AuthStatus
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import okhttp3.*
import okio.ByteString
import okio.ByteString.Companion.toByteString
import org.json.JSONObject
import java.util.UUID
import java.util.concurrent.LinkedBlockingQueue
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicLong

enum class VoipPhase { OFFLINE, READY, DIALING, RINGING, ACTIVE }
data class VoipState(
    val phase: VoipPhase = VoipPhase.OFFLINE,
    val username: String = "",
    val peer: String = "",
    val callId: String? = null,
    val error: String? = null,
    val audioRunning: Boolean = false,
)

/** One authenticated, tenant-scoped WSS connection. Audio is never stored on disk. */
class VoipManager(private val app: CallerApplication) {
    // Two simultaneous model analyses can briefly delay WebSocket pong delivery.
    private val client = OkHttpClient.Builder().pingInterval(60, TimeUnit.SECONDS)
        .connectTimeout(10, TimeUnit.SECONDS).build()
    private val mutable = MutableStateFlow(VoipState())
    val state = mutable.asStateFlow()
    private val queue = LinkedBlockingQueue<ByteArray>(20)
    private data class AnalysisFrame(val callId: String, val audio: ByteArray, val timestamp: Long)
    // At most four seconds of received PCM in memory; evict oldest audio on overload.
    private val analysisQueue = LinkedBlockingQueue<AnalysisFrame>(200)
    private var analysisPump: Job? = null
    private val droppedAnalysisFrames = AtomicLong()
    private val receivedFrames = AtomicLong()
    private val forwardedAnalysisFrames = AtomicLong()
    private val rejectedAnalysisFrames = AtomicLong()
    private val timestamp = AtomicLong()
    private var socket: WebSocket? = null
    private var generation = 0L
    private var reconnectJob: Job? = null
    private var reconnectDelayMs = 1_000L
    @Volatile private var analysisId: String? = null
    private var ringtone: Ringtone? = null
    private fun startRinging() {
        stopRinging()
        runCatching {
            RingtoneManager.getRingtone(app, RingtoneManager.getDefaultUri(RingtoneManager.TYPE_RINGTONE))?.also {
                it.setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_NOTIFICATION_RINGTONE).build())
                it.setLooping(true)
                it.play()
                ringtone = it
            }
        }.onFailure { Log.w("PraxisVoip", "Ringtone unavailable: ${it.javaClass.simpleName}") }
    }
    private fun stopRinging() { runCatching { ringtone?.stop() }; ringtone = null }
    private fun incomingNotification() {
        if (Build.VERSION.SDK_INT >= 33 && app.checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return
        val manager = app.getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel("voip-incoming", "Incoming Praxis calls", NotificationManager.IMPORTANCE_HIGH))
        val open = PendingIntent.getActivity(app, 2, Intent(app, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
        manager.notify(44, Notification.Builder(app, "voip-incoming").setSmallIcon(R.drawable.ic_launcher)
            .setContentTitle("Incoming Praxis internet call").setContentText("Tap to answer in Praxis Caller")
            .setContentIntent(open).setAutoCancel(true).build())
    }
    private fun clearNotification() = app.getSystemService(NotificationManager::class.java).cancel(44)
    fun ownsAnalysis(id: String): Boolean = analysisId == id && state.value.phase == VoipPhase.ACTIVE

    private fun scheduleReconnect(epoch: Long) {
        synchronized(this) {
            if (reconnectJob?.isActive == true || epoch != generation ||
                app.auth.state.value.status != AuthStatus.SIGNED_IN) return
            val delayMs = reconnectDelayMs
            reconnectDelayMs = (reconnectDelayMs * 2).coerceAtMost(30_000L)
            reconnectJob = app.applicationScope.launch {
                delay(delayMs)
                synchronized(this@VoipManager) { reconnectJob = null }
                if (epoch == generation && socket == null && app.auth.token().isNotBlank()) connect()
            }
        }
    }

    @Synchronized fun connect() {
        if (socket != null || app.auth.token().isBlank()) return
        val settings = app.settings ?: return
        val epoch = ++generation
        val url = settings.baseUrl.replaceFirst("https://", "wss://") + "api/v1/voip"
        val request = Request.Builder().url(url).header("Authorization", "Bearer ${app.auth.token()}").build()
        socket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                if (epoch != generation) return
                val value = runCatching { JSONObject(text) }.getOrNull() ?: return
                val call = value.optString("call_id")
                Log.i("PraxisVoip", "signal=${value.optString("type")}")
                when (value.optString("type")) {
                    "ready" -> {
                        reconnectDelayMs = 1_000L
                        mutable.value = VoipState(VoipPhase.READY, username = value.optString("username"))
                    }
                    "dialing" -> mutable.value = mutable.value.copy(phase = VoipPhase.DIALING, callId = call, error = null)
                    "ring" -> if (mutable.value.phase == VoipPhase.READY && app.calls.calls.value.none { !it.ended }) {
                        mutable.value = mutable.value.copy(
                            phase = VoipPhase.RINGING, callId = call, peer = value.optString("from"), error = null)
                        startRinging()
                        runCatching { incomingNotification() }
                    } else if (mutable.value.phase != VoipPhase.READY || app.calls.calls.value.any { !it.ended }) hangup()
                    "active" -> if (mutable.value.callId == call) {
                        stopRinging()
                        clearNotification()
                        mutable.value = mutable.value.copy(phase = VoipPhase.ACTIVE)
                        val id = "$call-${UUID.randomUUID()}"
                        analysisId = id
                        timestamp.set(SystemClock.elapsedRealtime())
                        receivedFrames.set(0); forwardedAnalysisFrames.set(0)
                        rejectedAnalysisFrames.set(0); droppedAnalysisFrames.set(0)
                        val peerName = mutable.value.peer
                        app.applicationScope.launch {
                            val settings = app.settings
                            app.praxis.connect(id, settings, app.auth::token)
                            val sessionId = app.praxis.state.value.sessionId
                            if (generation == epoch && mutable.value.callId == call &&
                                mutable.value.phase == VoipPhase.ACTIVE && settings != null &&
                                sessionId != null) {
                                try {
                                    com.praxis.caller.praxis.SessionDisplayClient().updateVoip(
                                        settings, app.auth.token(), sessionId, peerName)
                                } catch (error: Exception) {
                                    Log.w("PraxisVoip", "Call display update failed: ${error.javaClass.simpleName}")
                                }
                            }
                        }
                        analysisPump?.cancel()
                        analysisPump = app.applicationScope.launch(Dispatchers.IO) {
                            val block = java.io.ByteArrayOutputStream(32000)
                            var blockTimestamp = -1L
                            var expectedTimestamp = -1L
                            while (isActive && analysisId == id) {
                                val item = analysisQueue.poll(100, TimeUnit.MILLISECONDS) ?: continue
                                if (analysisId == item.callId) {
                                    if (expectedTimestamp != -1L && item.timestamp != expectedTimestamp) block.reset()
                                    if (block.size() == 0) blockTimestamp = item.timestamp
                                    block.write(item.audio)
                                    expectedTimestamp = item.timestamp + 20
                                    if (block.size() == 32000) {
                                        val accepted = app.praxis.sendAudio(id, block.toByteArray(), blockTimestamp)
                                        val count = if (accepted) forwardedAnalysisFrames.addAndGet(50)
                                            else rejectedAnalysisFrames.addAndGet(50)
                                        if (count % 250L == 0L || (!accepted && count == 50L))
                                            Log.i("PraxisVoip", "analysis progress received=${receivedFrames.get()} accepted=${forwardedAnalysisFrames.get()} rejected=${rejectedAnalysisFrames.get()} dropped=${droppedAnalysisFrames.get()}")
                                        block.reset()
                                    }
                                }
                            }
                        }
                    }
                    "ended" -> if (mutable.value.callId == call) finish()
                    "unavailable" -> mutable.value = mutable.value.copy(phase = VoipPhase.READY,
                        callId = null, peer = "", error = "That Praxis user is offline or busy.")
                }
            }
            override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
                if (epoch != generation || mutable.value.phase != VoipPhase.ACTIVE || bytes.size != 640) return
                val frame = bytes.toByteArray()
                val received = receivedFrames.incrementAndGet()
                if (received % 250L == 0L)
                    Log.i("PraxisVoip", "media progress received=$received accepted=${forwardedAnalysisFrames.get()} rejected=${rejectedAnalysisFrames.get()} dropped=${droppedAnalysisFrames.get()}")
                if (!queue.offer(frame)) { queue.poll(); queue.offer(frame) }
                val id = analysisId ?: return
                val next = timestamp.getAndAdd(20)
                val item = AnalysisFrame(id, frame, next)
                if (!analysisQueue.offer(item)) {
                    analysisQueue.poll()
                    analysisQueue.offer(item)
                    val dropped = droppedAnalysisFrames.incrementAndGet()
                    if (dropped % 100L == 1L) Log.w("PraxisVoip", "analysis queue dropped late frames count=$dropped")
                }
            }
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                if (epoch == generation) {
                    Log.w("PraxisVoip", "Call connection failed: ${response?.code ?: t.javaClass.simpleName}")
                    if (response?.code == 401 || response?.code == 403)
                        app.applicationScope.launch { app.auth.invalidateAccess() }
                    socket = null; finish()
                    mutable.value = VoipState(error = com.praxis.caller.auth.PraxisAuthManager.OFFLINE_MESSAGE)
                    scheduleReconnect(epoch)
                }
            }
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                if (epoch == generation) {
                    socket = null; finish(); mutable.value = VoipState(error = com.praxis.caller.auth.PraxisAuthManager.OFFLINE_MESSAGE)
                    scheduleReconnect(epoch)
                }
            }
        })
    }

    @Synchronized fun disconnect() {
        generation++
        reconnectJob?.cancel(); reconnectJob = null
        reconnectDelayMs = 1_000L
        socket?.close(1000, "closed"); socket = null
        finish(); mutable.value = VoipState()
    }
    fun dial(username: String) {
        if (mutable.value.phase != VoipPhase.READY || app.calls.calls.value.any { !it.ended } ||
            !username.matches(Regex("[A-Za-z0-9_.:@-]{1,128}"))) return
        mutable.value = mutable.value.copy(phase = VoipPhase.DIALING, peer = username, error = null)
        if (socket?.send(JSONObject().put("type", "dial").put("to", username).toString()) != true)
            mutable.value = mutable.value.copy(phase = VoipPhase.OFFLINE, error = "Call connection unavailable.")
    }
    fun answer() {
        val current = mutable.value
        if (current.phase == VoipPhase.RINGING && current.callId != null) {
            stopRinging()
            socket?.send(JSONObject().put("type", "accept").put("call_id", current.callId).toString())
        }
    }
    fun hangup() {
        socket?.send("{\"type\":\"hangup\"}")
        finish()
    }
    fun send(frame: ByteArray): Boolean {
        val queued = socket?.queueSize() ?: Long.MAX_VALUE
        val sent = mutable.value.phase == VoipPhase.ACTIVE && frame.size == 640 &&
            queued < 128_000 && socket?.send(frame.toByteString()) == true
        if (!sent) Log.w("PraxisVoip", "outgoing audio rejected phase=${mutable.value.phase} queueBytes=$queued")
        return sent
    }
    fun takeFrame(): ByteArray? = queue.poll(100, TimeUnit.MILLISECONDS)
    fun audioRunning(value: Boolean) { mutable.value = mutable.value.copy(audioRunning = value) }

    private fun finish() {
        stopRinging()
        clearNotification()
        queue.clear()
        analysisPump?.cancel(); analysisPump = null
        analysisQueue.clear()
        analysisId?.let { if (app.praxis.state.value.callId == it) app.praxis.disconnect() }
        analysisId = null
        mutable.value = mutable.value.copy(phase = if (socket == null) VoipPhase.OFFLINE else VoipPhase.READY,
            peer = "", callId = null, audioRunning = false)
    }
}
