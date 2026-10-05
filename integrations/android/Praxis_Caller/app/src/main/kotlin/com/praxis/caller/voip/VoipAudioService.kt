package com.praxis.caller.voip

import android.app.*
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.media.*
import android.media.audiofx.AcousticEchoCanceler
import android.os.IBinder
import android.util.Log
import com.praxis.caller.CallerApplication
import com.praxis.caller.MainActivity
import com.praxis.caller.R
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.collectLatest

/** Owns both call directions. No SIM call is active and no speaker loopback is used. */
class VoipAudioService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private val app get() = application as CallerApplication
    private var audioJob: Job? = null
    override fun onBind(intent: Intent?): IBinder? = null
    override fun onCreate() {
        super.onCreate()
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel("voip", "Praxis internet calls", NotificationManager.IMPORTANCE_LOW))
        val open = PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
        val stop = PendingIntent.getService(this, 1, Intent(this, VoipAudioService::class.java).setAction("hangup"), PendingIntent.FLAG_IMMUTABLE)
        val notification = Notification.Builder(this, "voip").setSmallIcon(R.drawable.ic_launcher)
            .setContentTitle("Praxis internet call").setContentText("Call audio active")
            .setContentIntent(open).setOngoing(true)
            .addAction(Notification.Action.Builder(null, "End call", stop).build()).build()
        try { startForeground(43, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE) }
        catch (error: RuntimeException) { Log.e("PraxisVoip", "Audio service start failed", error); app.voip.hangup(); stopSelf() }
    }
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == "hangup") { app.voip.hangup(); stopSelf(); return START_NOT_STICKY }
        if (app.voip.state.value.phase != VoipPhase.ACTIVE) { stopSelf(); return START_NOT_STICKY }
        if (audioJob?.isActive == true) return START_NOT_STICKY
        audioJob = scope.launch {
            val monitor = launch {
                app.voip.state.collectLatest { if (it.phase != VoipPhase.ACTIVE) stopSelf() }
            }
            try { runAudio() }
            finally { monitor.cancel(); app.voip.audioRunning(false); stopSelf() }
        }
        return START_NOT_STICKY
    }
    private suspend fun runAudio() = withContext(Dispatchers.IO) {
        val rate = 16000
        val format = AudioFormat.Builder().setEncoding(AudioFormat.ENCODING_PCM_16BIT)
            .setSampleRate(rate).setChannelMask(AudioFormat.CHANNEL_IN_MONO).build()
        val outputFormat = AudioFormat.Builder().setEncoding(AudioFormat.ENCODING_PCM_16BIT)
            .setSampleRate(rate).setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build()
        val audioManager = getSystemService(AudioManager::class.java)
        val oldMode = audioManager.mode
        var recorder: AudioRecord? = null
        var player: AudioTrack? = null
        var echo: AcousticEchoCanceler? = null
        try {
            check(checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                "Microphone permission was revoked"
            }
            audioManager.mode = AudioManager.MODE_IN_COMMUNICATION
            recorder = AudioRecord.Builder().setAudioSource(MediaRecorder.AudioSource.VOICE_COMMUNICATION)
                .setAudioFormat(format).setBufferSizeInBytes(maxOf(6400, AudioRecord.getMinBufferSize(
                    rate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT))).build()
            player = AudioTrack.Builder().setAudioAttributes(AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_VOICE_COMMUNICATION).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
                .setAudioFormat(outputFormat).setBufferSizeInBytes(maxOf(6400, AudioTrack.getMinBufferSize(
                    rate, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT)))
                .setTransferMode(AudioTrack.MODE_STREAM).build()
            check(recorder.state == AudioRecord.STATE_INITIALIZED && player.state == AudioTrack.STATE_INITIALIZED)
            if (AcousticEchoCanceler.isAvailable()) echo = AcousticEchoCanceler.create(recorder.audioSessionId)?.also { it.enabled = true }
            recorder.startRecording(); player.play()
            app.voip.audioRunning(true)
            val playback = launch {
                while (isActive && app.voip.state.value.phase == VoipPhase.ACTIVE) {
                    val frame = app.voip.takeFrame() ?: continue
                    player.write(frame, 0, frame.size, AudioTrack.WRITE_BLOCKING)
                }
            }
            try {
                val frame = ByteArray(640)
                var framesLogged = 0
                var power = 0.0
                var peak = 0
                while (isActive && app.voip.state.value.phase == VoipPhase.ACTIVE) {
                    var read = 0
                    while (read < frame.size && isActive) {
                        val count = recorder.read(frame, read, frame.size - read, AudioRecord.READ_BLOCKING)
                        if (count <= 0) throw IllegalStateException("Microphone read failed")
                        read += count
                    }
                    for (sampleIndex in frame.indices step 2) {
                        val sample = ((frame[sampleIndex].toInt() and 255) or
                            (frame[sampleIndex + 1].toInt() shl 8)).toShort().toInt()
                        power += sample.toDouble() * sample
                        peak = maxOf(peak, kotlin.math.abs(sample))
                    }
                    framesLogged++
                    if (framesLogged == 200) {
                        Log.i("PraxisVoip", "microphone rms=%.6f peak=%.4f".format(
                            java.util.Locale.US, kotlin.math.sqrt(power / 64000) / 32768.0,
                            peak / 32768.0))
                        framesLogged = 0; power = 0.0; peak = 0
                    }
                    if (!app.voip.send(frame)) throw IllegalStateException("Call transport stopped")
                }
            } finally { playback.cancelAndJoin() }
        } catch (error: Exception) {
            val reason = when (error) {
                is SecurityException -> "Audio permission denied"
                is IllegalStateException -> error.message?.takeIf {
                    it == "Microphone read failed" || it == "Call transport stopped" ||
                        it == "Microphone permission was revoked"
                } ?: "Audio state invalid"
                else -> error.javaClass.simpleName
            }
            Log.w("PraxisVoip", "Call audio stopped: $reason")
            app.voip.hangup()
        } finally {
            runCatching { recorder?.stop() }; recorder?.release()
            runCatching { player?.stop() }; player?.release(); echo?.release()
            audioManager.mode = oldMode
        }
    }
    override fun onDestroy() { audioJob?.cancel(); scope.cancel(); app.voip.audioRunning(false); super.onDestroy() }
}
