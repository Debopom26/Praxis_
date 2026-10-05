package com.praxis.caller.audio

import kotlinx.coroutines.*
import org.junit.Assert.*
import org.junit.Test

class AudioLifecycleTest {
    private class Recorder : MicRecorder {
        var starts = 0; var stops = 0; var releases = 0; var count = 640; var failStart = false
        val started = CompletableDeferred<Unit>()
        override fun start() { starts++; started.complete(Unit); if (failStart) error("unavailable") }
        override fun read(buffer: ByteArray, offset: Int, count: Int): Int = minOf(this.count, count)
        override fun stop() { stops++ }
        override fun release() { releases++ }
    }
    @Test fun everyRepeatedRunReleasesAndFramesStaySmall() = runBlocking {
        repeat(3) {
            val r = Recorder(); var frames = 0
            SpeakerMicAudioSource({ r }, { true }, { 10 }).capture({ true }) { bytes, _, _ ->
                assertEquals(640, bytes.size); frames++; frames < 2
            }
            assertEquals(2, frames); assertEquals(1, r.starts); assertEquals(1, r.stops); assertEquals(1, r.releases)
        }
    }
    @Test fun deniedPermissionDoesNotCreateRecorder() = runBlocking {
        var created = false
        try { SpeakerMicAudioSource({ created = true; Recorder() }, { false }, { 0 }).capture({ true }) { _, _, _ -> true }; fail() }
        catch (_: IllegalStateException) { }
        assertFalse(created)
    }
    @Test fun startFailureStillReleasesRecorder() = runBlocking {
        val r = Recorder().apply { failStart = true }
        try { SpeakerMicAudioSource({ r }, { true }, { 0 }).capture({ true }) { _, _, _ -> true }; fail() }
        catch (_: IllegalStateException) { }
        assertEquals(1, r.releases)
    }
    @Test fun cancellationDuringEmptyReadReleasesWithoutSending() = runBlocking {
        val r = Recorder().apply { count = 0 }; var frames = 0
        val job = launch { SpeakerMicAudioSource({ r }, { true }, { 0 }).capture({ true }) { _, _, _ -> frames++; true } }
        r.started.await(); job.cancelAndJoin()
        assertEquals(0, frames); assertEquals(1, r.releases)
    }
    @Test fun authorizationLossStopsBeforeNextSend() = runBlocking {
        val r = Recorder(); var eligible = true; var sent = 0
        SpeakerMicAudioSource({ r }, { true }, { 0 }).capture({ eligible }) { _, _, _ -> sent++; eligible = false; true }
        assertEquals(1, sent); assertEquals(1, r.releases)
    }
    @Test fun silentRecorderRestartsAndResumesRealAudio() = runBlocking {
        var created = 0; var released = 0; var realFrames = 0
        val source = SpeakerMicAudioSource({
            created++
            val live = created > 1
            object : MicRecorder {
                override fun start() = Unit
                override fun read(buffer: ByteArray, offset: Int, count: Int): Int {
                    java.util.Arrays.fill(buffer, offset, offset + count, if (live) 1.toByte() else 0.toByte())
                    return count
                }
                override fun stop() = Unit
                override fun release() { released++ }
            }
        }, { true }, { 10 }, 0)
        withTimeout(1000) {
            source.capture({ true }) { bytes, _, _ ->
                if (bytes.any { it != 0.toByte() }) { realFrames++; false } else true
            }
        }
        assertEquals(2, created)
        assertEquals(2, released)
        assertEquals(1, realFrames)
    }
}
