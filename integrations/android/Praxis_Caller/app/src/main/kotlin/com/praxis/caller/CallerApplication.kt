package com.praxis.caller

import android.app.Application
import android.telecom.Call
import android.util.Log
import com.praxis.caller.telecom.CallManager
import com.praxis.caller.praxis.*
import com.praxis.caller.auth.*
import com.praxis.caller.audio.CaptureState
import com.praxis.caller.data.PhoneDataRepository
import com.praxis.caller.voip.VoipManager
import com.praxis.caller.voip.VoipPhase
import com.praxis.caller.auth.AuthStatus
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow

class CallerApplication : Application() {
    val calls = CallManager()
    val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    val settings get() = PraxisSettings.load(this)
    val auth by lazy { PraxisAuthManager(settings?.auth, SecureStore(this), { settings }) }
    val praxis = PraxisManager()
    val voip by lazy { VoipManager(this) }
    val captureEpoch = java.util.concurrent.atomic.AtomicLong()
    val capture = MutableStateFlow(CaptureState())
    override fun onCreate() {
        super.onCreate()
        applicationScope.launch { auth.restore() }
        applicationScope.launch {
            while (isActive) {
                if (auth.state.value.status == AuthStatus.SIGNED_IN) {
                    if (auth.ensureFresh()) voip.connect()
                }
                delay(10_000)
            }
        }
        applicationScope.launch {
            calls.calls.collect { current ->
                val id = praxis.state.value.callId
                if (id != null && !voip.ownsAnalysis(id) && current.none { it.id == id && !it.ended }) praxis.disconnect()
            }
        }
        applicationScope.launch {
            auth.state.collect { state ->
                if (state.status == AuthStatus.SIGNED_IN) voip.connect() else voip.disconnect()
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
            if (praxis.state.value.sessionId != null) refreshSessionDisplay(callId)
        }
    }
    fun refreshSessionDisplay(callId: String) {
        applicationScope.launch {
            val call = calls.calls.value.firstOrNull { it.id == callId && !it.ended } ?: return@launch
            val sessionId = praxis.state.value.sessionId ?: return@launch
            val connection = settings ?: return@launch
            val contact = PhoneDataRepository(this@CallerApplication).lookup(call.number)
            Log.i("PraxisDisplay", "Sending call details: savedName=${contact != null} number=${call.number.isNotBlank()} time=${call.connectTimeMillis > 0}")
            repeat(3) { attempt ->
                try {
                    SessionDisplayClient().update(connection, auth.token(), sessionId, call, contact)
                    Log.i("PraxisDisplay", "Call details updated")
                    return@launch
                } catch (error: Exception) {
                    val code = error.message?.takeIf { it.matches(Regex("HTTP_[0-9]{3}")) }
                    Log.w("PraxisDisplay", "Call details update failed: ${code ?: error.javaClass.simpleName}")
                    if (attempt < 2) delay(1000)
                }
            }
        }
    }
}
