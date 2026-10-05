package com.praxis.caller.telecom

import android.os.ParcelUuid
import android.telecom.CallEndpoint
import com.praxis.caller.CallerApplication
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import java.util.UUID

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class AudioStateTest {
    @Test fun endpointAndMuteStateAreCallbackDrivenAndClearedOnDestroy() {
        val controller = Robolectric.buildService(PraxisInCallService::class.java).create()
        val service = controller.get()
        val manager = (service.application as CallerApplication).calls
        val endpoint = CallEndpoint("Speaker", CallEndpoint.TYPE_SPEAKER, ParcelUuid(UUID.randomUUID()))
        service.onAvailableCallEndpointsChanged(mutableListOf(endpoint))
        assertNull(manager.audio.value.selected)
        service.onCallEndpointChanged(endpoint); service.onMuteStateChanged(true)
        assertEquals(endpoint.identifier.toString(), manager.audio.value.selected)
        assertEquals(true, manager.audio.value.muted)
        assertTrue(manager.audio.value.routes.single().speaker)
        controller.destroy()
        assertTrue(manager.audio.value.routes.isEmpty()); assertNull(manager.audio.value.muted)
    }
}
