package com.praxis.caller.ui.call

import android.telecom.Call
import androidx.compose.foundation.layout.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.unit.dp
import androidx.compose.ui.graphics.Color
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.foundation.shape.CircleShape
import com.praxis.caller.ui.praxis.PraxisPanel
import androidx.compose.material3.TextButton
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.RadioButton
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableLongStateOf
import kotlinx.coroutines.delay
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import com.praxis.caller.telecom.CallManager
import com.praxis.caller.telecom.CallState
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.compose.runtime.DisposableEffect
import com.praxis.caller.ui.components.ContactIdentity

@Composable
fun CallScreen(calls: List<CallState>, manager: CallManager) {
    val audio by manager.audio.collectAsStateWithLifecycle()
    Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) {
        if (calls.isEmpty()) {
            Text("No current call")
            Button(onClick = {}, enabled = false, modifier = Modifier.testTag("end-call")) { Text("End call") }
        }
        calls.forEach { call ->
            var keypad by remember(call.id) { mutableStateOf(false) }
            var routes by remember(call.id) { mutableStateOf(false) }
            var now by remember(call.id) { mutableLongStateOf(System.currentTimeMillis()) }
            LaunchedEffect(call.id, call.connectTimeMillis, call.ended) {
                while (!call.ended) { now = System.currentTimeMillis(); delay(1000) }
            }
            DisposableEffect(call.id) { onDispose { manager.stopDtmf(call.id) } }
            ContactIdentity(call.number)
            Text(when (call.state) {
                Call.STATE_RINGING -> "Incoming call"
                Call.STATE_DIALING -> "Dialing"
                Call.STATE_CONNECTING -> "Connecting"
                Call.STATE_SELECT_PHONE_ACCOUNT -> "Choose a SIM account"
                Call.STATE_ACTIVE -> "Active call"
                Call.STATE_HOLDING -> "On hold"
                Call.STATE_DISCONNECTING -> "Ending call"
                Call.STATE_DISCONNECTED -> "Call ended"
                else -> "Call status pending"
            })
            if (call.connectTimeMillis > 0L && !call.ended) {
                val seconds = call.durationSeconds(now)
                Text("Duration %02d:%02d".format(seconds / 60, seconds % 60))
            }
            if (call.accountLabel.isNotEmpty()) Text("Account: ${call.accountLabel}")
            if (call.state == Call.STATE_SELECT_PHONE_ACCOUNT) {
                call.accounts.forEachIndexed { index, account ->
                    Button(onClick = { manager.selectAccount(call.id, account) }) { Text("SIM account ${index + 1}") }
                }
                if (call.accounts.isEmpty()) Text("No SIM accounts available. End this request and check SIM settings.")
            }
            PraxisPanel(call.id, call.state == Call.STATE_ACTIVE)
            if (call.state == Call.STATE_ACTIVE || call.state == Call.STATE_HOLDING) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                    OutlinedButton(onClick = { routes = true }, shape = CircleShape) { Text("Audio") }
                    OutlinedButton(onClick = { manager.setMuted(call.id, audio.muted != true) }, enabled = audio.muted != null, shape = CircleShape) {
                        Text(if (audio.muted == true) "Unmute" else "Mute")
                    }
                    OutlinedButton(onClick = { keypad = !keypad }, shape = CircleShape) { Text("Keypad") }
                }
                audio.routes.firstOrNull { it.id == audio.selected }?.let { Text(it.label, style = MaterialTheme.typography.bodySmall) }
                audio.error?.let { Text(it) }
                if (keypad) listOf("123", "456", "789", "*0#").forEach { row ->
                    Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) { row.forEach { digit ->
                        OutlinedButton(onClick = { manager.playDtmf(call.id, digit) }, enabled = call.state == Call.STATE_ACTIVE,
                            modifier = Modifier.testTag("dtmf-$digit").size(64.dp), shape = CircleShape) { Text(digit.toString()) }
                    } }
                }
                if (call.canHold) TextButton(onClick = { manager.toggleHold(call.id) }) { Text(if (call.state == Call.STATE_HOLDING) "Resume call" else "Hold call") }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                if (call.ringing) Button(onClick = { manager.answer(call.id) }, shape = CircleShape,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF3BC575)), modifier = Modifier.heightIn(min = 64.dp)) { Text("Answer") }
                Button(onClick = { if (call.ringing) manager.reject(call.id) else manager.disconnect(call.id) }, enabled = !call.ended,
                    shape = CircleShape, colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFF44750), contentColor = Color.White),
                    modifier = Modifier.testTag("end-call").heightIn(min = 64.dp)) { Text(if (call.ringing) "Decline" else "End call") }
            }
            if (routes) AlertDialog(onDismissRequest = { routes = false }, title = { Text("Call audio") },
                text = { Column { audio.routes.forEach { route ->
                    TextButton(onClick = { manager.selectRoute(route.id); routes = false }) { Text((if (route.id == audio.selected) "✓ " else "") + route.label) }
                }; if (audio.routes.isEmpty()) Text("No available audio outputs reported by Android.") } },
                confirmButton = { TextButton(onClick = { routes = false }) { Text("Close") } })
        }
    }
}
