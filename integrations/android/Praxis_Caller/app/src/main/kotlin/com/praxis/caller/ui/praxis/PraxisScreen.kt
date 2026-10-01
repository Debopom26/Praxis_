package com.praxis.caller.ui.praxis

import androidx.compose.foundation.layout.Column
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.praxis.caller.CallerApplication
import android.telecom.Call
import kotlinx.coroutines.launch

@Composable
fun PraxisScreen() {
    val app = LocalContext.current.applicationContext as CallerApplication
    val calls by app.calls.calls.collectAsStateWithLifecycle()
    val state by app.praxis.state.collectAsStateWithLifecycle()
    val scope = rememberCoroutineScope()
    val active = calls.firstOrNull { it.state == Call.STATE_ACTIVE }
    Column {
        PraxisPanel(active?.id, active != null)
        Text("Praxis status: ${state.status.name.replace('_', ' ')}")
        Text("Session: ${if (state.sessionId == null) "None" else "Created"}")
        Text("Frames enqueued: ${state.framesSent}")
        Text("Server ACK: not exposed by supplied SDK")
        Text("Last event: ${state.lastEvent ?: "None"}")
        if (app.settings == null) Text("Service configuration required. Phone calls remain independent.")
        TextButton(onClick = { app.praxis.disconnect(); scope.launch { app.auth.signOut() } }) { Text("Sign out") }
    }
}
