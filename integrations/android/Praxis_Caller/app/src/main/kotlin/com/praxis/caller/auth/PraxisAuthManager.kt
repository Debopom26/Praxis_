package com.praxis.caller.auth

import android.net.Uri
import com.praxis.caller.praxis.PraxisSettings
import com.praxis.caller.praxis.AuthSettings
import java.security.SecureRandom
import java.security.MessageDigest
import java.util.Base64
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import okhttp3.*
import org.json.JSONObject
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody

enum class AuthStatus { CONFIGURATION_REQUIRED, SIGNED_OUT, SIGNING_IN, SIGNED_IN, ERROR }
data class AuthState(val status: AuthStatus = AuthStatus.SIGNED_OUT, val message: String? = null)

/** Configurable OAuth2-PKCE adapter, not a claim that the Praxis backend implements OAuth2. */
class PraxisAuthManager(private val config: AuthSettings?, private val store: SecureStore,
    private val settingsProvider: () -> PraxisSettings? = { null }) {
    private var nativeBinding: String? = settingsProvider()?.takeIf { it.passwordLogin }?.let(::passwordBinding)
    private val mutex = Mutex()
    private val mutable = MutableStateFlow(AuthState(if (config == null) AuthStatus.CONFIGURATION_REQUIRED else AuthStatus.SIGNED_OUT))
    val state = mutable.asStateFlow()
    @Volatile private var credential: Pair<String, Long>? = null
    private var attempt = 0L
    private val http = OkHttpClient.Builder().followRedirects(false).followSslRedirects(false)
        .callTimeout(20, TimeUnit.SECONDS).build()
    private val binding get() = nativeBinding ?: config?.let { "${it.authorizeUrl}|${it.tokenUrl}|${it.clientId}" }.orEmpty()
    fun token(): String = credential?.takeIf { it.second > System.currentTimeMillis() + 30000 }?.first.orEmpty()
    suspend fun restore() = withContext(Dispatchers.IO) { mutex.withLock {
        if (config == null && nativeBinding == null) return@withLock
        try {
            store.get("token")?.let { raw ->
                val json = JSONObject(raw)
                if (json.optString("binding") == binding) credential = json.getString("token") to json.getLong("expires")
            }
            if (token().isNotBlank()) mutable.value = AuthState(AuthStatus.SIGNED_IN)
            else { credential = null; store.remove("token"); mutable.value = AuthState(AuthStatus.SIGNED_OUT) }
        } catch (_: Exception) { credential = null; mutable.value = AuthState(AuthStatus.ERROR, "Secure sign-in storage is unavailable.") }
    } }
    /** Existing Praxis JSON login; password exists only for this request. */
    suspend fun signInWithPassword(settings: PraxisSettings, username: String, password: String,
        persistConnection: () -> Unit): Boolean =
        withContext(Dispatchers.IO) {
            val generation = mutex.withLock {
                nativeBinding = passwordBinding(settings)
                credential = null
                attempt++
                mutable.value = AuthState(AuthStatus.SIGNING_IN)
                attempt
            }
            try {
                require(settings.passwordLogin && username.isNotBlank() && password.isNotEmpty())
                mutex.withLock { if (generation == attempt) store.remove("token") }
                val body = JSONObject().put("username", username).put("password", password)
                    .put("tenant_id", settings.tenantId).toString()
                    .toRequestBody("application/json; charset=utf-8".toMediaType())
                val response = http.newCall(Request.Builder()
                    .url(settings.baseUrl + "api/v1/auth/login").post(body).build()).execute().use {
                    require(it.isSuccessful)
                    val source = checkNotNull(it.body).source()
                    source.request(65537); require(source.buffer.size <= 65536)
                    JSONObject(source.readUtf8())
                }
                val token = response.getString("access_token")
                require(token.length in 1..16384 && token.none { it.isWhitespace() || it.code < 32 })
                require(response.getString("token_type").equals("Bearer", true))
                val seconds = response.getLong("expires_in"); require(seconds in 31..1800)
                val expires = System.currentTimeMillis() + seconds * 1000
                mutex.withLock {
                    if (generation != attempt) return@withLock false
                    store.put("token", JSONObject().put("token", token).put("expires", expires)
                        .put("binding", passwordBinding(settings)).toString())
                    persistConnection()
                    credential = token to expires
                    mutable.value = AuthState(AuthStatus.SIGNED_IN)
                    true
                }
            } catch (e: CancellationException) {
                mutex.withLock { if (generation == attempt) { credential = null; store.remove("token"); mutable.value = AuthState(AuthStatus.SIGNED_OUT) } }
                throw e
            } catch (_: Exception) {
                mutex.withLock {
                    if (generation == attempt) mutable.value = AuthState(AuthStatus.ERROR,
                        "Sign-in failed. Check the server address, trusted certificate, organization and account.")
                }
                false
            }
        }
    private fun random(): String = ByteArray(32).also { SecureRandom().nextBytes(it) }.let { Base64.getUrlEncoder().withoutPadding().encodeToString(it) }
    suspend fun begin(): Uri? = withContext(Dispatchers.IO) { mutex.withLock {
        val cfg = config ?: return@withLock null
        try {
            attempt++
            val verifier = random(); val nonce = random()
            val challenge = Base64.getUrlEncoder().withoutPadding().encodeToString(MessageDigest.getInstance("SHA-256").digest(verifier.toByteArray(Charsets.US_ASCII)))
            store.put("pending", JSONObject().put("state", nonce).put("verifier", verifier)
                .put("expires", System.currentTimeMillis() + 600000).put("binding", binding).toString())
            mutable.value = AuthState(AuthStatus.SIGNING_IN)
            Uri.parse(cfg.authorizeUrl).buildUpon().appendQueryParameter("response_type", "code")
                .appendQueryParameter("client_id", cfg.clientId).appendQueryParameter("redirect_uri", cfg.redirectUri)
                .appendQueryParameter("scope", cfg.scope).appendQueryParameter("state", nonce)
                .appendQueryParameter("code_challenge", challenge).appendQueryParameter("code_challenge_method", "S256").build()
        } catch (_: Exception) { mutable.value = AuthState(AuthStatus.ERROR, "Unable to prepare secure sign-in."); null }
    } }
    suspend fun cancel() = withContext(Dispatchers.IO) { mutex.withLock {
        attempt++; store.remove("pending"); mutable.value = AuthState(if (token().isBlank()) AuthStatus.SIGNED_OUT else AuthStatus.SIGNED_IN)
    } }
    suspend fun signOut() = withContext(Dispatchers.IO) { mutex.withLock {
        attempt++; credential = null
        try { store.clearSecrets(); mutable.value = AuthState(AuthStatus.SIGNED_OUT) }
        catch (_: Exception) { mutable.value = AuthState(AuthStatus.ERROR, "Could not clear secure storage. Clear app data in Android settings.") }
    } }
    suspend fun complete(uri: Uri) = withContext(Dispatchers.IO) {
        val cfg = config ?: return@withContext
        var generation = 0L
        val body = mutex.withLock {
            try {
                require(validCallback(uri, cfg.redirectUri))
                val pending = store.get("pending")?.let(::JSONObject) ?: return@withLock null
                require(pending.getString("binding") == binding && pending.getLong("expires") > System.currentTimeMillis())
                require(MessageDigest.isEqual(pending.getString("state").toByteArray(), uri.getQueryParameter("state").orEmpty().toByteArray()))
                val code = uri.getQueryParameter("code")?.takeIf { it.isNotBlank() && it.length <= 4096 } ?: throw IllegalArgumentException()
                store.remove("pending") // single-use callback
                generation = ++attempt
                FormBody.Builder().add("grant_type", "authorization_code").add("code", code)
                    .add("client_id", cfg.clientId).add("redirect_uri", cfg.redirectUri)
                    .add("code_verifier", pending.getString("verifier")).build()
            } catch (_: Exception) { mutable.value = AuthState(AuthStatus.ERROR, "Sign-in callback was rejected. Start sign-in again."); null }
        } ?: return@withContext
        try {
            val response = http.newCall(Request.Builder().url(cfg.tokenUrl).post(body).build()).execute().use {
                require(it.isSuccessful)
                val source = checkNotNull(it.body).source(); source.request(65537); require(source.buffer.size <= 65536)
                JSONObject(source.readUtf8())
            }
            val token = response.getString("access_token")
            require(token.length in 1..16384 && token.none { it.isWhitespace() || it.code < 32 })
            require(response.getString("token_type").equals("Bearer", true))
            val seconds = response.getLong("expires_in"); require(seconds in 31..2592000)
            val expires = System.currentTimeMillis() + seconds * 1000
            mutex.withLock {
                if (generation != attempt) return@withLock
                store.put("token", JSONObject().put("token", token).put("expires", expires).put("binding", binding).toString())
                credential = token to expires; mutable.value = AuthState(AuthStatus.SIGNED_IN)
            }
        } catch (_: Exception) { mutex.withLock { if (generation == attempt) mutable.value = AuthState(AuthStatus.ERROR, "Sign-in failed. Please try again.") } }
    }
    companion object {
        private fun passwordBinding(value: PraxisSettings) = "praxis-password|${value.baseUrl}|${value.tenantId}"
        fun validCallback(uri: Uri, redirect: String): Boolean {
            val expected = Uri.parse(redirect)
            return uri.toString().length <= 8192 && uri.scheme == expected.scheme && uri.encodedAuthority == expected.encodedAuthority &&
                uri.encodedPath == expected.encodedPath && uri.fragment == null &&
                uri.queryParameterNames.all { it in setOf("state", "code", "error", "error_description") } &&
                uri.queryParameterNames.all { uri.getQueryParameters(it).size == 1 } && uri.getQueryParameter("error") == null &&
                uri.getQueryParameter("state")?.isNotBlank() == true && uri.getQueryParameter("code")?.isNotBlank() == true
        }
    }
}
