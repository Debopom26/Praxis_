package com.praxis.caller.praxis

import com.praxis.caller.telecom.CallState
import com.praxis.caller.data.PhoneEntry
import java.time.Instant
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

/** Optional host-supplied contact label; no audio, transcript or credential is persisted here. */
internal class SessionDisplayClient {
    private val http = OkHttpClient.Builder().followRedirects(false).followSslRedirects(false).build()

    suspend fun update(settings: PraxisSettings, token: String, sessionId: String,
                       call: CallState, contact: PhoneEntry?) = withContext(Dispatchers.IO) {
        if (token.isBlank()) return@withContext
        val body = JSONObject()
            .put("remote_name", contact?.name?.take(128))
            .put("remote_number", call.number.takeIf { it.isNotBlank() }?.take(64))
            .put("call_connected_at", call.connectTimeMillis.takeIf { it > 0 }
                ?.let { Instant.ofEpochMilli(it).toString() })
            .toString().toRequestBody("application/json; charset=utf-8".toMediaType())
        http.newCall(Request.Builder()
            .url(settings.baseUrl + "api/v1/sessions/$sessionId/display")
            .header("Authorization", "Bearer $token")
            .put(body).build()).execute().use { if (!it.isSuccessful) throw java.io.IOException("HTTP_${it.code}") }
    }
}
