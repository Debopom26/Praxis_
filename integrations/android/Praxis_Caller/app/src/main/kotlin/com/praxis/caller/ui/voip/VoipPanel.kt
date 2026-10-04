package com.praxis.caller.ui.voip

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.praxis.caller.CallerApplication
import com.praxis.caller.ui.praxis.ConnectionDialog
import com.praxis.caller.voip.VoipAudioService
import com.praxis.caller.voip.VoipPhase

@Composable
fun VoipPanel() {
    val context = LocalContext.current
    val app = context.applicationContext as CallerApplication
    val state by app.voip.state.collectAsStateWithLifecycle()
    val analysis by app.praxis.state.collectAsStateWithLifecycle()
    var recipient by remember { mutableStateOf("") }
    var login by remember { mutableStateOf(false) }
    var permissionGranted by remember { mutableStateOf(context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) }
    var pendingDial by remember { mutableStateOf<String?>(null) }
    var pendingAnswer by remember { mutableStateOf(false) }
    var permissionError by remember { mutableStateOf(false) }
    val micPermission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        permissionGranted = granted
        permissionError = !granted
        if (granted) {
            pendingDial?.let(app.voip::dial)
            if (pendingAnswer) app.voip.answer()
        }
        pendingDial = null; pendingAnswer = false
    }
    LaunchedEffect(state.phase, permissionGranted) {
        if (state.phase == VoipPhase.ACTIVE && permissionGranted && !state.audioRunning)
            runCatching { context.startForegroundService(Intent(context, VoipAudioService::class.java)) }
                .onFailure { app.voip.hangup() }
        if (state.phase != VoipPhase.ACTIVE) context.stopService(Intent(context, VoipAudioService::class.java))
    }
    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Praxis internet call", style = MaterialTheme.typography.titleMedium)
        Text("Calls connect only to signed-in Praxis users in your organization.")
        if (state.phase == VoipPhase.OFFLINE) {
            Text("Internet calling offline")
            Button(onClick = { if (app.auth.token().isBlank()) login = true else app.voip.connect() }) { Text("Connect internet calling") }
        } else {
            if (state.username.isNotBlank()) Text("Your Praxis name: ${state.username}")
            when (state.phase) {
                VoipPhase.READY -> {
                    OutlinedTextField(recipient, { recipient = it.trim().take(128) }, label = { Text("Other person's Praxis username") }, singleLine = true)
                    Button(onClick = {
                        if (!permissionGranted) { pendingDial = recipient; micPermission.launch(Manifest.permission.RECORD_AUDIO) }
                        else app.voip.dial(recipient)
                    }, enabled = recipient.isNotBlank()) { Text("Internet call") }
                }
                VoipPhase.DIALING -> Text("Calling ${state.peer}…")
                VoipPhase.RINGING -> {
                    Text("Incoming internet call from ${state.peer}")
                    Button(onClick = {
                        if (!permissionGranted) { pendingAnswer = true; micPermission.launch(Manifest.permission.RECORD_AUDIO) }
                        else app.voip.answer()
                    }) { Text("Answer") }
                }
                VoipPhase.ACTIVE -> {
                    Text("Connected to ${state.peer}")
                    Text(if (state.audioRunning) "Call audio active" else "Starting call audio…")
                    if (!permissionGranted) Button(onClick = { micPermission.launch(Manifest.permission.RECORD_AUDIO) }) { Text("Allow microphone") }
                    if (analysis.sessionId != null) {
                        val score = analysis.experimentalScore ?: analysis.risk
                        if (score != null) Text("${if (analysis.regressorStatus == "BOOTSTRAP_UNTRAINED") "Provisional score" else "Risk score"} ${"%.1f".format(java.util.Locale.US, score)} / 100")
                        Text(analysis.detail ?: "Waiting for Praxis analysis of incoming voice")
                    } else Text("Connecting call analysis…")
                }
                else -> Unit
            }
            if (state.phase in setOf(VoipPhase.DIALING, VoipPhase.RINGING, VoipPhase.ACTIVE))
                OutlinedButton(onClick = { app.voip.hangup() }) { Text(if (state.phase == VoipPhase.RINGING) "Decline" else "End internet call") }
        }
        state.error?.let { Text(it) }
        if (permissionError) Text("Microphone permission is required for an internet call.")
    }
    if (login) ConnectionDialog(app, onDismiss = { login = false }, onConnected = { login = false; app.voip.connect() })
}
