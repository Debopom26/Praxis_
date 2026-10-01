package com.praxis.caller.telecom

import android.Manifest
import android.app.Application
import android.app.role.RoleManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.telecom.Call
import android.telecom.TelecomManager
import androidx.test.core.app.ApplicationProvider
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config

/** Android services below are host shadows: none of these assertions proves a SIM call. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class TelecomTest {
    private val context get() = ApplicationProvider.getApplicationContext<Application>()
    @Test fun dialIntentOnlyProvidesValidatedDraft() {
        assertEquals("+12345", DialerRoleManager.draftFrom(Intent(Intent.ACTION_DIAL, Uri.parse("tel:+12345"))))
        assertNull(DialerRoleManager.draftFrom(Intent(Intent.ACTION_CALL, Uri.parse("tel:12345"))))
        assertNull(DialerRoleManager.draftFrom(Intent(Intent.ACTION_DIAL, Uri.parse("https://example.com"))))
        assertNull(DialerRoleManager.validateNumber("+"))
        assertNull(DialerRoleManager.validateNumber("123@evil"))
        assertNull(DialerRoleManager.validateNumber("1".repeat(65)))
    }
    @Test fun noPermissionOrRoleNeverSendsCall() {
        val dialer = DialerRoleManager(context)
        val telecom = shadowOf(context.getSystemService(TelecomManager::class.java))
        assertEquals(DialResult.ROLE_REQUIRED, dialer.placeCall("12345"))
        val role = shadowOf(context.getSystemService(RoleManager::class.java))
        role.addHeldRole(RoleManager.ROLE_DIALER)
        shadowOf(context).denyPermissions(Manifest.permission.CALL_PHONE)
        assertEquals(DialResult.PERMISSION_REQUIRED, dialer.placeCall("12345"))
        assertTrue(telecom.allOutgoingCalls.isEmpty())
    }
    @Test fun explicitAuthorizedRequestReachesTelecomWithoutInventingCallState() {
        val role = shadowOf(context.getSystemService(RoleManager::class.java))
        role.addAvailableRole(RoleManager.ROLE_DIALER)
        role.addHeldRole(RoleManager.ROLE_DIALER)
        shadowOf(context).grantPermissions(Manifest.permission.CALL_PHONE)
        val telecom = shadowOf(context.getSystemService(TelecomManager::class.java))
        telecom.setCallPhonePermission(true)
        assertEquals(DialResult.REQUESTED, DialerRoleManager(context).placeCall("12345"))
        assertEquals(1, telecom.allOutgoingCalls.size)
        assertTrue((context as com.praxis.caller.CallerApplication).calls.calls.value.isEmpty())
    }
    @Test fun unavailableRoleHasNoRequestAndIsNotHeld() {
        val role = shadowOf(context.getSystemService(RoleManager::class.java))
        assertNull(DialerRoleManager(context).request())
        assertFalse(DialerRoleManager(context).held())
    }
    @Test fun callbacksAreAuthoritativeAndRemovalDropsReferences() {
        val manager = CallManager()
        val port = FakeCall()
        val id = manager.add(port)
        assertTrue(manager.calls.value.single().ringing)
        assertTrue(manager.answer(id))
        assertEquals(1, port.answers)
        assertTrue(manager.calls.value.single().ringing) // command itself must not synthesize ACTIVE
        port.status = Call.STATE_ACTIVE; port.changed!!()
        assertEquals(Call.STATE_ACTIVE, manager.calls.value.single().state)
        assertFalse(manager.answer(id))
        assertTrue(manager.disconnect(id))
        val lateCallback = port.changed!!
        manager.remove(id)
        assertTrue(port.released)
        assertFalse(manager.disconnect(id))
        lateCallback()
        assertTrue(manager.calls.value.isEmpty())
    }
    @Test fun independentCallsAndClearReleaseEveryPort() {
        val manager = CallManager(); val one = FakeCall(); val two = FakeCall()
        val a = manager.add(one); val b = manager.add(two)
        manager.remove(a)
        assertEquals(b, manager.calls.value.single().id)
        assertTrue(manager.reject(b)); assertEquals(1, two.rejects)
        manager.clear()
        assertTrue(one.released && two.released)
        assertTrue(manager.calls.value.isEmpty())
    }
    @Test fun finishedCallsAndPlatformErrorsAreNotSuccess() {
        val manager = CallManager(); val port = FakeCall(); val id = manager.add(port)
        port.status = Call.STATE_DISCONNECTED
        assertFalse(manager.disconnect(id))
        port.status = Call.STATE_RINGING; port.throwOnAnswer = true
        assertFalse(manager.answer(id))
        assertEquals(Call.STATE_RINGING, manager.calls.value.single().state)
    }
    @Test fun dtmfIsActiveOnlyBoundedAndStopsOnRemoval() {
        val manager = CallManager(); val port = FakeCall(); val id = manager.add(port)
        assertFalse(manager.playDtmf(id, '1'))
        port.status = Call.STATE_ACTIVE
        assertFalse(manager.playDtmf(id, 'X'))
        assertTrue(manager.playDtmf(id, '5'))
        val before = port.stops
        shadowOf(android.os.Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(200))
        assertTrue(port.stops > before)
        assertTrue(manager.playDtmf(id, '6'))
        manager.remove(id)
        assertTrue(port.released)
        assertFalse(manager.playDtmf(id, '7'))
    }
    @Test fun unlistedPhoneAccountNeverReachesTelecom() {
        shadowOf(context.getSystemService(RoleManager::class.java)).addHeldRole(RoleManager.ROLE_DIALER)
        shadowOf(context).grantPermissions(Manifest.permission.CALL_PHONE)
        val account = android.telecom.PhoneAccountHandle(android.content.ComponentName("test", "Phone"), "unknown")
        assertEquals(DialResult.UNAVAILABLE, DialerRoleManager(context).placeCall("12345", account))
    }
    @Test fun deniedProvidersReturnNoPersonalData() = kotlinx.coroutines.runBlocking {
        shadowOf(context).denyPermissions(Manifest.permission.READ_CONTACTS, Manifest.permission.READ_CALL_LOG)
        val data = com.praxis.caller.data.PhoneDataRepository(context).load()
        assertTrue(data.contacts.isEmpty()); assertTrue(data.recents.isEmpty())
    }
    private class FakeCall : CallPort {
        var tones = 0; var stops = 0
        var status = Call.STATE_RINGING; var changed: (() -> Unit)? = null
        var released = false; var answers = 0; var rejects = 0; var throwOnAnswer = false
        override fun snapshot(id: String) = CallState(id, "", status)
        override fun observe(changed: () -> Unit) { this.changed = changed }
        override fun release() { released = true; changed = null }
        override fun answer() { if (throwOnAnswer) throw SecurityException(); answers++ }
        override fun reject() { rejects++ }
        override fun disconnect() {}
        override fun playDtmf(digit: Char) { tones++ }
        override fun stopDtmf() { stops++ }
        override fun hold() { status = Call.STATE_HOLDING; changed?.invoke() }
        override fun unhold() { status = Call.STATE_ACTIVE; changed?.invoke() }
        override fun setMuted(value: Boolean) {}
        override fun setAudioRoute(route: Int) {}
    }
}
