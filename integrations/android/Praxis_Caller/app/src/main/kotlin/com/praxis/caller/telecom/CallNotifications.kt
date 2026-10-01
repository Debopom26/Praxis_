package com.praxis.caller.telecom

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Person
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import com.praxis.caller.CallerApplication
import com.praxis.caller.MainActivity
import com.praxis.caller.R

internal class CallNotifications(private val context: Context) {
    private val notifications = context.getSystemService(NotificationManager::class.java)
    fun update(calls: List<CallState>) {
        val current = calls.firstOrNull { it.ringing } ?: calls.firstOrNull { !it.ended }
        if (current == null) { notifications.cancel(31); return }
        val channel = NotificationChannel("calls", "Phone calls", NotificationManager.IMPORTANCE_HIGH)
        // Telecom supplies ringtone: this notification must not play a second ringtone.
        channel.setSound(null, null)
        notifications.createNotificationChannel(channel)
        val open = PendingIntent.getActivity(context, 0, Intent(context, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        fun action(name: String) = PendingIntent.getBroadcast(context, 0,
            Intent(context, CallActionReceiver::class.java).setAction(name).setData(android.net.Uri.parse("praxis-call:" + current.id)),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val end = action(if (current.ringing) "reject" else "end")
        val builder = Notification.Builder(context, "calls").setSmallIcon(R.drawable.ic_launcher)
            .setContentTitle(if (current.ringing) "Incoming call" else "Phone call")
            .setContentText("Tap to view call controls").setContentIntent(open)
            .setCategory(Notification.CATEGORY_CALL).setVisibility(Notification.VISIBILITY_PRIVATE)
            .setOngoing(true).setOnlyAlertOnce(true)
        val fullScreen = current.ringing && (Build.VERSION.SDK_INT < 34 || notifications.canUseFullScreenIntent())
        if (fullScreen) {
            builder.setFullScreenIntent(open, true)
        }
        // This is a bound InCallService, not a foreground service. CallStyle
        // requires an FGS/job or a full-screen intent; outgoing calls have none.
        if (Build.VERSION.SDK_INT >= 31 && fullScreen) {
            val person = Person.Builder().setName("Phone call").build()
            builder.setStyle(if (current.ringing) Notification.CallStyle.forIncomingCall(person, end, action("answer"))
                else Notification.CallStyle.forOngoingCall(person, end))
        } else {
            if (current.ringing) builder.addAction(Notification.Action.Builder(null, "Answer", action("answer")).build())
            builder.addAction(Notification.Action.Builder(null, if (current.ringing) "Decline" else "End", end).build())
        }
        try { notifications.notify(31, builder.build()) }
        catch (_: SecurityException) { /* Permission can be revoked. */ }
        catch (_: IllegalArgumentException) {
            // A policy/permission change must not crash the call service.
            builder.setStyle(null).setFullScreenIntent(null, false)
            if (fullScreen && Build.VERSION.SDK_INT >= 31) {
                builder.addAction(Notification.Action.Builder(null, "Answer", action("answer")).build())
                builder.addAction(Notification.Action.Builder(null, "Decline", end).build())
            }
            try { notifications.notify(31, builder.build()) }
            catch (_: SecurityException) { /* Calling remains available without notification permission. */ }
            catch (_: IllegalArgumentException) { /* OEM rejected the fallback; preserve the live call UI. */ }
        }
    }
}

/** Private receiver; immutable pending intents carry an opaque, live call ID only. */
class CallActionReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val id = intent.data?.takeIf { it.scheme == "praxis-call" }?.schemeSpecificPart ?: return
        val manager = (context.applicationContext as CallerApplication).calls
        when (intent.action) {
            "answer" -> manager.answer(id)
            "reject" -> manager.reject(id)
            "end" -> manager.disconnect(id)
        }
    }
}
