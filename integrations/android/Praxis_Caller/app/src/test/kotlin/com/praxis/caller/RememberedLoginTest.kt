package com.praxis.caller

import com.praxis.caller.auth.*
import com.praxis.caller.praxis.PraxisSettings
import kotlinx.coroutines.runBlocking
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class RememberedLoginTest {
    private class MemoryStore : CredentialStore {
        val values = mutableMapOf<String, String>()
        override fun put(name: String, value: String) { values[name] = value }
        override fun get(name: String) = values[name]
        override fun clearSecrets() { values.clear() }
        override fun remove(name: String) { values.remove(name) }
    }
    private val settings = PraxisSettings.passwordSettings(PraxisSettings.PUBLIC_SERVER, "team")
    private fun saved() = MemoryStore().apply {
        put("token", JSONObject().put("token", "expired-access").put("expires", 1L)
            .put("binding", "praxis-password|${settings.baseUrl}|team")
            .put("refresh_token", "r".repeat(64)).toString())
    }
    private fun client(code: Int, body: String) = OkHttpClient.Builder().addInterceptor {
        Response.Builder().request(it.request()).protocol(Protocol.HTTP_1_1).code(code)
            .message("test").body(body.toResponseBody("application/json".toMediaType())).build()
    }.build()
    @Test fun expiredAccessSurvivesRestartAndOutageWithoutLogout() = runBlocking {
        val store = saved()
        val http = OkHttpClient.Builder().addInterceptor { throw java.io.IOException("offline") }.build()
        val auth = PraxisAuthManager(null, store, { settings }, http)
        auth.restore()
        assertEquals(AuthStatus.SIGNED_IN, auth.state.value.status)
        assertFalse(auth.ensureFresh())
        assertEquals(AuthStatus.SIGNED_IN, auth.state.value.status)
        assertEquals(PraxisAuthManager.OFFLINE_MESSAGE, auth.state.value.message)
        assertNotNull(store.get("token"))
        assertEquals("", auth.token())
    }
    @Test fun refreshRestoresAccessAndDeliberateLogoutClearsRememberedLogin() = runBlocking {
        val store = saved()
        val auth = PraxisAuthManager(null, store, { settings }, client(200,
            """{"access_token":"fresh-access","expires_in":900,"token_type":"bearer"}"""))
        auth.restore()
        assertTrue(auth.ensureFresh())
        assertEquals("fresh-access", auth.token())
        assertEquals(AuthStatus.SIGNED_IN, auth.state.value.status)
        auth.signOut()
        assertNull(store.get("token"))
        assertEquals(AuthStatus.SIGNED_OUT, auth.state.value.status)
        assertFalse(auth.ensureFresh())
    }
    @Test fun RevokedAccountDoesNotBecomeAnOfflineSession() = runBlocking {
        val store = saved()
        val auth = PraxisAuthManager(null, store, { settings }, client(401, "{}"))
        auth.restore()
        assertFalse(auth.ensureFresh())
        assertEquals(AuthStatus.SIGNED_OUT, auth.state.value.status)
        assertNull(store.get("token"))
    }
}
