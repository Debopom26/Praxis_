package com.praxis.caller.audio

import android.app.*
import android.content.Intent
import android.os.IBinder
import android.util.Log
import android.content.pm.ServiceInfo
import android.telecom.Call
import com.praxis.caller.CallerApplication
import com.praxis.caller.MainActivity
import com.praxis.caller.R
import com.praxis.caller.praxis.PraxisStatus
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.combine

/** Start only from the visible Activity after explicit consent and RECORD_AUDIO grant. */
class CaptureService : Service() {
    private companion object { const val TAG = "PraxisCapture" }
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private val app get() = application as CallerApplication
    private var job: Job? = null
    private var generation = -1L
    @Volatile private var live = false
    private var promoted = false
    override fun onBind(intent: Intent?): IBinder? = null
    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "CaptureService created")
        // Promote before any call, authentication, network, or audio checks.
        try {
            val nm = getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(NotificationChannel("protection", "Praxis microphone", NotificationManager.IMPORTANCE_LOW))
            val stop = PendingIntent.getService(this, 10, Intent(this, CaptureService::class.java).setAction("stop"), PendingIntent.FLAG_IMMUTABLE)
            val open = PendingIntent.getActivity(this, 11, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
            val notification = Notification.Builder(this, "protection").setSmallIcon(R.drawable.ic_launcher)
                .setContentTitle("Praxis_").setContentText("Call analysis active")
                .setContentIntent(open).setOngoing(true).addAction(Notification.Action.Builder(null, "Stop microphone", stop).build()).build()
            startForeground(42, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE)
            promoted = true
            Log.i(TAG, "Foreground promotion successful")
        } catch (e: RuntimeException) {
            Log.e(TAG, "Foreground promotion failed", e)
            app.capture.value = CaptureState(error = "Microphone service could not start. Keep the app visible and retry.")
            stopSelf()
        }
    }
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (!promoted) { stopSelf(startId); return START_NOT_STICKY }
        if (intent?.action == "stop") { Log.i(TAG, "Capture stopping by request"); live = false; stopSelf(startId); return START_NOT_STICKY }
        val id = intent?.getStringExtra("callId")
        if (id == null || !allowed(id)) {
            Log.w(TAG, "Capture start rejected: ${policySnapshot(id)}")
            app.capture.value = CaptureState(error = "Speaker, active call, Praxis connection and microphone consent are required.")
            stopSelf(startId)
            return START_NOT_STICKY
        }
        if (job?.isActive == true) return START_NOT_STICKY
        live = true
        generation = app.captureEpoch.incrementAndGet()
        job = scope.launch {
            val monitor = launch {
                combine(app.calls.calls, app.calls.audio, app.praxis.state) { _, _, _ -> allowed(id) }
                    .collect { if (!it) { Log.i(TAG, "Capture policy ended"); job?.cancel(); stopSelf() } }
            }
            try {
                app.capture.value = CaptureState(true, id)
                Log.i(TAG, "Audio capture starting")
                var firstFrame = true
                SpeakerMicAudioSource(this@CaptureService).capture({ allowed(id) }) { bytes, timestamp, energy ->
                    if (!allowed(id)) false else app.praxis.sendAudio(id, bytes, timestamp).also { sent ->
                        if (sent && app.praxis.state.value.status == PraxisStatus.CONNECTED) {
                            if (firstFrame) { Log.i(TAG, "Audio capture active; first frame queued for backend"); firstFrame = false }
                            app.capture.value = CaptureState(true, id, energy)
                        }
                    }
                }
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) {
                Log.e(TAG, "Audio capture failed", e)
                app.capture.value = CaptureState(error = "Microphone unavailable or interrupted. The phone call continues.")
            }
            finally {
                monitor.cancel()
                if (generation == app.captureEpoch.get()) app.capture.value = app.capture.value.copy(running = false, energy = 0f)
                Log.i(TAG, "Capture stopping")
                stopForeground(STOP_FOREGROUND_REMOVE); stopSelf()
            }
        }
        return START_NOT_STICKY
    }
    private fun allowed(id: String): Boolean {
        if (generation != -1L && (!live || generation != app.captureEpoch.get())) return false
        return CapturePolicy.allowed(id, app.calls.calls.value, app.calls.audio.value, app.praxis.state.value,
            app.settings?.acousticInputApproved == true, app.auth.token().isNotBlank())
    }
    private fun policySnapshot(id: String?): String {
        val calls = app.calls.calls.value
        val audio = app.calls.audio.value
        val state = app.praxis.state.value
        return "activeCall=${calls.any { it.id == id && it.state == Call.STATE_ACTIVE }} " +
            "speaker=${audio.routes.any { it.id == audio.selected && it.speaker }} muted=${audio.muted} " +
            "connected=${state.status in setOf(PraxisStatus.CONNECTED, PraxisStatus.RECONNECTING)} matchingCall=${state.callId == id} " +
            "session=${state.sessionId != null} consent=${app.settings?.acousticInputApproved == true} " +
            "authenticated=${app.auth.token().isNotBlank()}"
    }
    override fun onDestroy() {
        Log.i(TAG, "CaptureService destroyed")
        live = false
        job?.cancel(); scope.cancel()
        if (generation == app.captureEpoch.get()) app.capture.value = app.capture.value.copy(running = false, energy = 0f)
        super.onDestroy()
    }
}
