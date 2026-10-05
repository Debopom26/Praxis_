package com.praxis.caller.praxis

import android.util.Base64
import android.util.Log
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.Locale
import java.util.concurrent.TimeUnit
import kotlin.math.abs
import kotlin.math.sqrt
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

data class SuppliedResult(val experimentalScore: Double, val syntheticScore: Double,
    val action: String, val message: String, val regressorStatus: String)

internal interface SuppliedAnalyzerPort {
    suspend fun analyze(settings: PraxisSettings, token: String, sessionId: String,
        pcmS16le: ByteArray): SuppliedResult
}

internal class SuppliedAnalysisClient : SuppliedAnalyzerPort {
    private val http = OkHttpClient.Builder().followRedirects(false).followSslRedirects(false)
        .readTimeout(120, TimeUnit.SECONDS).callTimeout(120, TimeUnit.SECONDS).build()

    override suspend fun analyze(settings: PraxisSettings, token: String, sessionId: String,
        pcmS16le: ByteArray): SuppliedResult = withContext(Dispatchers.IO) {
        require(pcmS16le.size == 128000 && token.isNotBlank())
        val input = ByteBuffer.wrap(pcmS16le).order(ByteOrder.LITTLE_ENDIAN)
        val output = ByteBuffer.allocate(pcmS16le.size * 2).order(ByteOrder.LITTLE_ENDIAN)
        var power = 0.0; var peak = 0.0
        while (input.remaining() >= 2) {
            val sample = input.short / 32768f
            power += sample.toDouble() * sample
            peak = maxOf(peak, abs(sample.toDouble()))
            output.putFloat(sample)
        }
        val body = JSONObject().put("session_id", sessionId)
            .put("sample_rate", 16000).put("channels", 1)
            .put("pcm_f32le_base64", Base64.encodeToString(output.array(), Base64.NO_WRAP))
            .toString().toRequestBody("application/json; charset=utf-8".toMediaType())
        val started = android.os.SystemClock.elapsedRealtime()
        Log.i("PraxisTransport", String.format(Locale.US,
            "V2 request started rms=%.6f peak=%.4f", sqrt(power / (pcmS16le.size / 2)), peak))
        val value = http.newCall(Request.Builder().url(settings.baseUrl + "api/v2/analysis")
            .header("Authorization", "Bearer $token").post(body).build()).execute().use {
            if (!it.isSuccessful) Log.w("PraxisTransport", "V2 HTTP status=${it.code}")
            require(it.isSuccessful)
            val source = checkNotNull(it.body).source(); source.request(1048577)
            require(source.buffer.size <= 1048576)
            JSONObject(source.readUtf8())
        }
        require(value.getString("status") == "AVAILABLE")
        val guidance = value.getJSONObject("guidance")
        val score = value.getDouble("experimental_score_0_100")
        val synthetic = value.getJSONObject("synthetic_voice").getDouble("score_0_100")
        require(score in 0.0..100.0 && synthetic in 0.0..100.0)
        Log.i("PraxisTransport", String.format(Locale.US,
            "V2 window rms=%.6f peak=%.4f score=%.3f ai=%.3f action=%s latency_ms=%d",
            sqrt(power / (pcmS16le.size / 2)), peak, score, synthetic, guidance.getString("action"),
            android.os.SystemClock.elapsedRealtime() - started))
        SuppliedResult(score, synthetic, guidance.getString("action").take(128),
            guidance.getString("message").take(2000), value.getString("regressor_status").take(128))
    }
}
