package com.praxis.caller.telecom

import android.os.Handler
import android.os.Looper
import android.telecom.Call
import android.telecom.TelecomManager
import android.telecom.VideoProfile
import android.telecom.InCallService
import android.telecom.PhoneAccountHandle
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.UUID

/** Only actual Telecom callbacks populate this state. No call state is persisted. */
data class CallState(
    val id: String, val number: String, val state: Int,
    val connectTimeMillis: Long = 0L,
    val accountLabel: String = "",
    val muted: Boolean = false,
    val audioRoute: Int = android.telecom.CallAudioState.ROUTE_EARPIECE,
    val canHold: Boolean = false,
    val accounts: List<PhoneAccountHandle> = emptyList(),
) {
    fun durationSeconds(now: Long): Long = if (connectTimeMillis <= 0L) 0L else ((now - connectTimeMillis).coerceAtLeast(0L) / 1000L)
    val ringing get() = state == Call.STATE_RINGING
    val ended get() = state == Call.STATE_DISCONNECTED || state == Call.STATE_DISCONNECTING
}

internal interface CallPort {
    fun snapshot(id: String): CallState
    fun observe(changed: () -> Unit)
    fun release()
    fun answer()
    fun reject()
    fun disconnect()
    fun playDtmf(digit: Char)
    fun stopDtmf()
    fun hold()
    fun unhold()
    fun setMuted(value: Boolean)
    fun setAudioRoute(route: Int)
    fun selectAccount(account: PhoneAccountHandle) {}
}

internal class AndroidCallPort(private val call: Call, private val service: PraxisInCallService) : CallPort {
    private var callback: Call.Callback? = null
    @Suppress("DEPRECATION")
    override fun snapshot(id: String): CallState {
        val details = call.details
        val number = if (details?.handlePresentation == TelecomManager.PRESENTATION_ALLOWED)
            details.handle?.schemeSpecificPart.orEmpty() else ""
        val account = details.accountHandle?.let { service.accountLabel(it) }.orEmpty()
        return CallState(id, number, call.state, details.connectTimeMillis, account,
            service.latestAudioState?.isMuted == true,
            service.latestAudioState?.route ?: android.telecom.CallAudioState.ROUTE_EARPIECE,
            details.can(Call.Details.CAPABILITY_HOLD),
            details.intentExtras?.getParcelableArrayList<PhoneAccountHandle>(Call.AVAILABLE_PHONE_ACCOUNTS).orEmpty())
    }
    override fun observe(changed: () -> Unit) {
        val listener = object : Call.Callback() {
            override fun onStateChanged(call: Call, state: Int) = changed()
            override fun onDetailsChanged(call: Call, details: Call.Details) = changed()
        }
        callback = listener
        call.registerCallback(listener, Handler(Looper.getMainLooper()))
    }
    override fun release() { runCatching { call.stopDtmfTone() }; callback?.let(call::unregisterCallback); callback = null }
    override fun answer() = call.answer(VideoProfile.STATE_AUDIO_ONLY)
    @Suppress("DEPRECATION")
    override fun reject() = call.reject(false, null)
    override fun disconnect() = call.disconnect()
    override fun playDtmf(digit: Char) = call.playDtmfTone(digit)
    override fun stopDtmf() = call.stopDtmfTone()
    override fun hold() = call.hold()
    override fun unhold() = call.unhold()
    override fun setMuted(value: Boolean) = service.setMuted(value)
    override fun setAudioRoute(route: Int) = service.setAudioRoute(route)
    override fun selectAccount(account: PhoneAccountHandle) = call.phoneAccountSelected(account, false)
}

/** Main-thread confined; service and UI both use Android's main thread. */
class CallManager {
    private val ports = linkedMapOf<String, CallPort>()
    private val mutable = MutableStateFlow<List<CallState>>(emptyList())
    val calls = mutable.asStateFlow()
    internal val mutableAudio = MutableStateFlow(AudioState())
    val audio = mutableAudio.asStateFlow()
    internal var routeRequest: ((String) -> Unit)? = null
    fun selectRoute(id: String) { routeRequest?.invoke(id) }
    private val toneStops = mutableMapOf<String, Runnable>()
    private val handler = Handler(Looper.getMainLooper())
    internal fun add(port: CallPort): String {
        val id = UUID.randomUUID().toString()
        ports[id] = port
        port.observe { if (ports[id] === port) publish() }
        publish()
        return id
    }
    internal fun remove(id: String) { stopDtmf(id); ports.remove(id)?.release(); publish() }
    internal fun clear() { ports.keys.toList().forEach(::remove) }
    private fun publish() { mutable.value = ports.map { (id, port) -> port.snapshot(id) } }
    fun answer(id: String): Boolean = act(id, true) { answer() }
    fun reject(id: String): Boolean = act(id, true) { reject() }
    fun disconnect(id: String): Boolean = act(id, false) { disconnect() }
    fun playDtmf(id: String, digit: Char): Boolean {
        if (digit !in "0123456789*#" || ports[id]?.snapshot(id)?.state != Call.STATE_ACTIVE) return false
        stopDtmf(id)
        if (!act(id, false) { playDtmf(digit) }) return false
        val stop = Runnable { stopDtmf(id) }
        toneStops[id] = stop
        handler.postDelayed(stop, 180)
        return true
    }
    fun stopDtmf(id: String): Boolean {
        toneStops.remove(id)?.let(handler::removeCallbacks)
        val port = ports[id] ?: return false
        return runCatching { port.stopDtmf() }.isSuccess
    }
    fun selectAccount(id: String, account: PhoneAccountHandle): Boolean {
        val call = ports[id]?.snapshot(id) ?: return false
        if (call.state != Call.STATE_SELECT_PHONE_ACCOUNT || account !in call.accounts) return false
        return act(id, false) { selectAccount(account) }
    }
    fun toggleHold(id: String): Boolean {
        val port = ports[id] ?: return false; val c = port.snapshot(id)
        if (!c.canHold || c.state !in listOf(Call.STATE_ACTIVE, Call.STATE_HOLDING)) return false
        return try { if (c.state == Call.STATE_HOLDING) port.unhold() else port.hold(); true }
        catch (_: SecurityException) { false } catch (_: IllegalStateException) { false }
    }
    fun setMuted(id: String, value: Boolean): Boolean = act(id, false) { setMuted(value) }
    fun setAudioRoute(id: String, route: Int): Boolean = act(id, false) { setAudioRoute(route) }
    internal fun refresh(id: String) { if (ports.containsKey(id)) publish() }
    private fun act(id: String, ringingOnly: Boolean, command: CallPort.() -> Unit): Boolean {
        val port = ports[id] ?: return false
        val current = port.snapshot(id)
        if (current.ended || (ringingOnly && !current.ringing)) return false
        return try { port.command(); true } catch (_: SecurityException) { false }
            catch (_: IllegalStateException) { false }
    }
}
