package com.praxis.caller

import android.app.Application
import android.telecom.Call
import com.praxis.caller.telecom.CallManager
import com.praxis.caller.praxis.*
import com.praxis.caller.auth.*
import com.praxis.caller.audio.CaptureState
import com.praxis.caller.data.PhoneDataRepository
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow

class CallerApplication : Application() {
    val calls = CallManager()
    val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    val settings get() = PraxisSettings.load(this)
    val auth by lazy { PraxisAuthManager(settings?.auth, SecureStore(this), { settings }) }
    val praxis = PraxisManager()
    val captureEpoch = java.util.concurrent.atomic.AtomicLong()
    val capture = MutableStateFlow(CaptureState())
    override fun onCreate() {
        super.onCreate()
        applicationScope.launch { auth.restore() }
        applicationScope.launch {
            calls.calls.collect { current ->
                val id = praxis.state.value.callId
                if (id != null && current.none { it.id == id && !it.ended }) praxis.disconnect()
            }
        }
        applicationScope.launch {
            while (isActive) {
                delay(1000)
                if (praxis.state.value.callId != null && auth.token().isBlank()) praxis.disconnect()
            }
        }
    }
    fun connectPraxis(callId: String) {
        val call = calls.calls.value.firstOrNull { it.id == callId && it.state == Call.STATE_ACTIVE } ?: return
        applicationScope.launch {
            val connection = settings ?: return@launch
            praxis.connect(callId, connection, auth::token)
            val sessionId = praxis.state.value.sessionId ?: return@launch
            val contact = PhoneDataRepository(this@CallerApplication).lookup(call.number)
            runCatching { SessionDisplayClient().update(connection, auth.token(), sessionId, call, contact) }
        }
    }
}
