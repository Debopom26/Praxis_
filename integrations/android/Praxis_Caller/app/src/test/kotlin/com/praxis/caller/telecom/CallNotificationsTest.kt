package com.praxis.caller.telecom

import android.app.Notification
import android.app.NotificationManager
import android.telecom.Call
import androidx.test.core.app.ApplicationProvider
import android.content.Context
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class CallNotificationsTest {
    @Test fun outgoingAndActiveCallsHaveActionableNotificationsWithoutRestrictedCallStyle() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val manager = context.getSystemService(NotificationManager::class.java)
        val notifications = CallNotifications(context)
        for (state in listOf(Call.STATE_DIALING, Call.STATE_ACTIVE, Call.STATE_HOLDING)) {
            notifications.update(listOf(CallState("fixture", "", state)))
            val posted = shadowOf(manager).getNotification(31)
            assertNotNull(posted)
            assertNull(posted.fullScreenIntent)
            assertNotEquals(Notification.CallStyle::class.java.name, posted.extras.getString("android.template"))
            assertEquals("End", posted.actions.single().title.toString())
            assertNotNull(posted.contentIntent)
        }
        notifications.update(emptyList())
        assertNull(shadowOf(manager).getNotification(31))
    }
}
