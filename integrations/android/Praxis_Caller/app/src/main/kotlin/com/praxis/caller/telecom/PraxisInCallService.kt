package com.praxis.caller.telecom

import android.content.Intent
import android.telecom.Call
import android.telecom.InCallService
import android.os.Build
import android.os.OutcomeReceiver
import android.telecom.CallEndpoint
import android.telecom.CallEndpointException
import android.telecom.CallAudioState
import android.telecom.PhoneAccountHandle
import android.telecom.TelecomManager
import androidx.annotation.RequiresApi
import com.praxis.caller.CallerApplication
import com.praxis.caller.MainActivity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

class PraxisInCallService : InCallService() {
    @Volatile var latestAudioState: android.telecom.CallAudioState? = null
        private set
    private val manager get() = (application as CallerApplication).calls
    private val ids = mutableMapOf<Call, String>()
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private lateinit var notifications: CallNotifications
    private var endpoints: List<CallEndpoint> = emptyList()
    private var live = false
    fun accountLabel(handle: PhoneAccountHandle): String = try {
        getSystemService(TelecomManager::class.java)?.getPhoneAccount(handle)?.label?.toString() ?: "SIM account"
    } catch (_: SecurityException) { "SIM account" }
    override fun onCreate() {
        super.onCreate()
        notifications = CallNotifications(this)
        live = true
        manager.routeRequest = ::selectRoute
        scope.launch { manager.calls.collect { notifications.update(it) } }
    }
    override fun onCallAdded(call: Call) {
        super.onCallAdded(call)
        if (call !in ids) ids[call] = manager.add(AndroidCallPort(call, this))
        showCallUi()
    }
    @Suppress("DEPRECATION")
    override fun onCallAudioStateChanged(audioState: android.telecom.CallAudioState) {
        latestAudioState = audioState
        super.onCallAudioStateChanged(audioState)
        manager.calls.value.forEach { manager.refresh(it.id) }
        if (Build.VERSION.SDK_INT < 34) {
            val choices = listOf(CallAudioState.ROUTE_EARPIECE to "Earpiece", CallAudioState.ROUTE_SPEAKER to "Speaker",
                CallAudioState.ROUTE_WIRED_HEADSET to "Wired headset", CallAudioState.ROUTE_BLUETOOTH to "Bluetooth")
            manager.mutableAudio.value = AudioState(audioState.isMuted,
                choices.filter { (route, _) -> audioState.supportedRouteMask and route != 0 }
                    .map { (route, name) -> AudioRoute(route.toString(), name, route == CallAudioState.ROUTE_SPEAKER) }, audioState.route.toString())
        }
    }
    @RequiresApi(34)
    override fun onAvailableCallEndpointsChanged(availableEndpoints: MutableList<CallEndpoint>) {
        endpoints = availableEndpoints.toList()
        manager.mutableAudio.value = manager.audio.value.copy(routes = endpoints.map {
            AudioRoute(it.identifier.toString(), it.endpointName.toString(), it.endpointType == CallEndpoint.TYPE_SPEAKER)
        })
    }
    @RequiresApi(34)
    override fun onCallEndpointChanged(callEndpoint: CallEndpoint) {
        manager.mutableAudio.value = manager.audio.value.copy(selected = callEndpoint.identifier.toString(), error = null)
    }
    override fun onMuteStateChanged(isMuted: Boolean) {
        manager.mutableAudio.value = manager.audio.value.copy(muted = isMuted)
    }
    @Suppress("DEPRECATION")
    private fun selectRoute(id: String) {
        if (!live || ids.isEmpty()) return
        try {
            if (Build.VERSION.SDK_INT >= 34) {
                val endpoint = endpoints.find { it.identifier.toString() == id } ?: return
                requestCallEndpointChange(endpoint, mainExecutor, object : OutcomeReceiver<Void, CallEndpointException> {
                    override fun onResult(result: Void?) { /* Actual route is set by the endpoint callback. */ }
                    override fun onError(error: CallEndpointException) {
                        if (live) manager.mutableAudio.value = manager.audio.value.copy(error = "Audio route change failed. Try another output.")
                    }
                })
            } else if (manager.audio.value.routes.any { it.id == id }) setAudioRoute(id.toInt())
        } catch (_: RuntimeException) {
            manager.mutableAudio.value = manager.audio.value.copy(error = "Audio route is unavailable.")
        }
    }
    override fun onCallRemoved(call: Call) {
        ids.remove(call)?.let(manager::remove)
        super.onCallRemoved(call)
    }
    override fun onBringToForeground(showDialpad: Boolean) = showCallUi()
    private fun showCallUi() {
        try {
            startActivity(Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP))
        } catch (_: SecurityException) { /* The call notification remains the user entry point. */ }
    }
    override fun onDestroy() {
        live = false
        manager.routeRequest = null
        manager.mutableAudio.value = AudioState()
        endpoints = emptyList()
        scope.cancel()
        ids.values.toList().forEach(manager::remove)
        ids.clear()
        notifications.update(emptyList())
        super.onDestroy()
    }
}
