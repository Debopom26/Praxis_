package com.praxis.caller.audio

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.AudioManager
import android.media.MediaRecorder
import android.os.SystemClock
import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

internal interface MicRecorder {
    fun start()
    fun read(buffer: ByteArray, offset: Int, count: Int): Int
    fun stop()
    fun release()
}
private class AndroidMicRecorder(private val context: Context) : MicRecorder {
    private var recorder: AudioRecord
    private var source: Int
    private val bufferSize: Int
    private fun create(source: Int): AudioRecord {
        check(context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED)
        return AudioRecord(source, 16000, AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT, bufferSize)
    }
    init {
        check(context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED)
        val min = AudioRecord.getMinBufferSize(16000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
        check(min > 0) { "AUDIO_FORMAT_UNAVAILABLE" }
        bufferSize = maxOf(min, 3200)
        val supported = context.getSystemService(AudioManager::class.java)
            ?.getProperty(AudioManager.PROPERTY_SUPPORT_AUDIO_SOURCE_UNPROCESSED) == "true"
        val preferred = if (supported) MediaRecorder.AudioSource.UNPROCESSED else MediaRecorder.AudioSource.MIC
        val attempt = runCatching { create(preferred) }.getOrNull()
        if (attempt?.state == AudioRecord.STATE_INITIALIZED) {
            recorder = attempt; source = preferred
        } else {
            attempt?.release()
            recorder = create(MediaRecorder.AudioSource.MIC); source = MediaRecorder.AudioSource.MIC
        }
        Log.i("PraxisCapture", "Microphone source: ${if (source == MediaRecorder.AudioSource.UNPROCESSED) "UNPROCESSED" else "MIC"}")
    }
    override fun start() {
        check(recorder.state == AudioRecord.STATE_INITIALIZED) { "AUDIO_INITIALIZATION_FAILED" }
        try { recorder.startRecording() }
        catch (e: RuntimeException) {
            if (source != MediaRecorder.AudioSource.UNPROCESSED) throw e
            recorder.release()
            recorder = create(MediaRecorder.AudioSource.MIC)
            source = MediaRecorder.AudioSource.MIC
            Log.i("PraxisCapture", "Unprocessed input unavailable during call; using MIC")
            recorder.startRecording()
        }
        check(recorder.recordingState == AudioRecord.RECORDSTATE_RECORDING) { "MICROPHONE_UNAVAILABLE" }
    }
    override fun read(buffer: ByteArray, offset: Int, count: Int) = recorder.read(buffer, offset, count, AudioRecord.READ_NON_BLOCKING)
    override fun stop() { recorder.stop() }
    override fun release() { recorder.release() }
}
/** Acoustic microphone only; no downlink access, audio files or accumulating queues. */
class SpeakerMicAudioSource internal constructor(
    private val factory: () -> MicRecorder,
    private val permission: () -> Boolean,
    private val clock: () -> Long,
    private val retryDelayMillis: Long = 1000,
) : CallAudioSource {
    companion object { private val ownership = Mutex() }
    constructor(context: Context) : this({
        // Check again next to construction for revocation races and Android lint.
        check(context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED)
        AndroidMicRecorder(context)
    }, { context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED }, SystemClock::elapsedRealtime)
    override suspend fun capture(allowed: () -> Boolean, send: (ByteArray, Long, Float) -> Boolean) = withContext(Dispatchers.IO) { ownership.withLock {
        check(permission()) { "MICROPHONE_PERMISSION_REQUIRED" }
        if (!allowed()) return@withContext
        var recorder: MicRecorder? = factory()
        val frame = ByteArray(640)
        try {
            if (!allowed()) return@withContext
            recorder!!.start()
            var offset = 0; var last = -1L; var silentFrames = 0
            while (currentCoroutineContext().isActive && permission() && allowed()) {
                val count = recorder!!.read(frame, offset, frame.size - offset)
                if (count !in 0..(frame.size - offset)) Log.w("PraxisCapture", "Microphone read interrupted; retrying")
                if (count !in 0..(frame.size - offset) || silentFrames >= 200) {
                    runCatching { recorder?.stop() }; recorder?.release(); recorder = null
                    frame.fill(0); offset = 0; silentFrames = 0
                    while (currentCoroutineContext().isActive && permission() && allowed() && recorder == null) {
                        delay(retryDelayMillis)
                        val next = runCatching { factory() }.getOrNull() ?: continue
                        if (runCatching { next.start() }.isSuccess) recorder = next
                        else next.release()
                    }
                    if (recorder == null) break
                    continue
                }
                offset += count
                if (offset == frame.size) {
                    if (!allowed() || !permission()) break
                    silentFrames = if (frame.all { it == 0.toByte() }) silentFrames + 1 else 0
                    var sum = 0.0
                    for (i in frame.indices step 2) {
                        val sample = ((frame[i].toInt() and 255) or (frame[i + 1].toInt() shl 8)).toShort().toDouble() / 32768.0
                        sum += sample * sample
                    }
                    val timestamp = maxOf(last + 1, clock())
                    if (!send(frame, timestamp, kotlin.math.sqrt(sum / 320).toFloat())) break
                    last = timestamp; offset = 0
                } else delay(5)
            }
        } finally {
            frame.fill(0)
            runCatching { recorder?.stop() }
            recorder?.release()
        }
    }
    }
}
