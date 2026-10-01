package com.praxis.caller.praxis

import android.content.Context
import org.json.JSONObject
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull

data class PraxisSettings(val baseUrl: String, val tenantId: String, val hostAppId: String,
    val auth: AuthSettings? = null, val acousticInputApproved: Boolean = false,
    val passwordLogin: Boolean = false) {
    init {
        require(secureUrl(baseUrl, true) && tenantId.isNotBlank() && hostAppId.isNotBlank())
    }
    companion object {
        fun secureUrl(value: String, rootOnly: Boolean = false): Boolean {
            val url = value.toHttpUrlOrNull() ?: return false
            return url.isHttps && url.username.isEmpty() && url.password.isEmpty() && url.fragment == null &&
                url.query == null && (!rootOnly || url.encodedPath == "/")
        }
        fun saveConnection(context: Context, value: PraxisSettings) {
            require(value.passwordLogin)
            check(context.getSharedPreferences("praxis-connection", Context.MODE_PRIVATE).edit()
                .putString("configuration", JSONObject().put("baseUrl", value.baseUrl)
                    .put("tenantId", value.tenantId).put("hostAppId", value.hostAppId).toString()).commit())
        }
        fun passwordSettings(base: String, tenant: String) = PraxisSettings(
            base.trim().trimEnd('/') + "/", tenant.trim(), "praxis-caller",
            acousticInputApproved = true, passwordLogin = true).also {
                require(it.tenantId.matches(Regex("[A-Za-z0-9_.:@-]{1,128}")))
            }
        fun load(context: Context): PraxisSettings? { return try {
            val saved = context.getSharedPreferences("praxis-connection", Context.MODE_PRIVATE)
                .getString("configuration", null)
            if (saved != null) {
                val value = JSONObject(saved)
                return passwordSettings(value.getString("baseUrl"), value.getString("tenantId"))
            }
            val json = context.assets.open("praxis-config.json").bufferedReader().use { JSONObject(it.readText()) }
            val base = json.getString("baseUrl"); val tenant = json.getString("tenantId"); val app = json.getString("hostAppId")
            require(secureUrl(base, true) && tenant.isNotBlank() && app.isNotBlank())
            val authJson = json.optJSONObject("auth")
            val auth = authJson?.takeIf { it.optString("protocol") == "oauth2-pkce" }?.let {
                AuthSettings(it.getString("authorizeUrl"), it.getString("tokenUrl"), it.getString("clientId"), it.optString("scope"))
            }?.takeIf { secureUrl(it.authorizeUrl) && secureUrl(it.tokenUrl) && it.clientId.isNotBlank() }
            PraxisSettings(base, tenant, app, auth, json.optBoolean("acousticInputApproved", false))
        } catch (_: Exception) { null } }
    }
}
data class AuthSettings(val authorizeUrl: String, val tokenUrl: String, val clientId: String, val scope: String) {
    val redirectUri: String get() = "praxis-caller://auth/callback"
}
