package com.praxis.caller.ui.praxis

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.*
import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.praxis.caller.CallerApplication
import com.praxis.caller.auth.AuthStatus
import com.praxis.caller.audio.CaptureService
import com.praxis.caller.praxis.PraxisStatus
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.first
import kotlin.math.*

fun riskColor(score: Double?): Color {
    if (score == null || !score.isFinite()) return Color(0xFF89939B)
    val stops = listOf(Color(0xFF49CF88), Color(0xFF9BCB51), Color(0xFFE3B63F), Color(0xFFF29739), Color(0xFFEC693D), Color(0xFFE9434B))
    val value = score.coerceIn(0.0, 100.0) / 20.0
    val index = value.toInt().coerceAtMost(4)
    return androidx.compose.ui.graphics.lerp(stops[index], stops[index + 1], (value - index).toFloat())
}
@Composable
fun PraxisPanel(callId: String?, active: Boolean) {
    val context = LocalContext.current
    val app = context.applicationContext as CallerApplication
    val state by app.praxis.state.collectAsStateWithLifecycle()
    val auth by app.auth.state.collectAsStateWithLifecycle()
    val capture by app.capture.collectAsStateWithLifecycle()
    val scope = rememberCoroutineScope()
    var loginDialog by remember { mutableStateOf(false) }
    var consent by remember { mutableStateOf(false) }
    var feedback by remember { mutableStateOf<String?>(null) }
    var contactsAllowed by remember { mutableStateOf(context.checkSelfPermission(Manifest.permission.READ_CONTACTS) == PackageManager.PERMISSION_GRANTED) }
    val contactsPermission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        contactsAllowed = granted
        if (granted) callId?.let(app::refreshSessionDisplay)
        else feedback = "Saved contact names need Contacts permission. A phone number may still appear."
    }
    fun startCapture() {
        if (callId == null) return
        val speaker = app.calls.audio.value.routes.firstOrNull { it.speaker }
        if (speaker == null) { feedback = "Speaker output is unavailable. Select Speaker from Audio and retry."; return }
        scope.launch {
            if (app.calls.audio.value.selected != speaker.id) {
                feedback = "Switching call audio to Speaker…"
                app.calls.selectRoute(speaker.id)
                val selected = withTimeoutOrNull(4000) {
                    app.calls.audio.first { it.selected == speaker.id && it.muted == false }
                }
                if (selected == null) { feedback = "Select Speaker from Audio and unmute the call, then retry."; return@launch }
            }
            if (app.calls.audio.value.muted != false) { feedback = "Unmute the call, then retry."; return@launch }
            try { context.startForegroundService(Intent(context, CaptureService::class.java).putExtra("callId", callId)); feedback = null }
            catch (_: RuntimeException) { feedback = "Microphone could not start. Keep the app open and retry." }
        }
    }
    val microphone = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) startCapture() else feedback = "Microphone permission was declined. The call continues."
    }
    val belongs = callId != null && state.callId == callId
    val connected = belongs && state.status in setOf(PraxisStatus.CONNECTED, PraxisStatus.RECONNECTING)
    val color by animateColorAsState(riskColor(if (belongs) state.risk else null), label = "risk")
    LaunchedEffect(state.decisionId, belongs) {
        if (belongs && active) state.decisionId?.let { if (app.praxis.consumeDecisionSound(it)) playDecisionChime() }
    }
    Column(Modifier.fillMaxWidth().background(Color(0xFF171B1B), RoundedCornerShape(24.dp)).padding(16.dp).animateContentSize(),
        horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        if (belongs && state.status == PraxisStatus.CONNECTING) {
            val transition = rememberInfiniteTransition(label = "connecting")
            val pulse by transition.animateFloat(0.3f, 1f, infiniteRepeatable(tween(600), RepeatMode.Reverse), label = "dots")
            Text("• • •  Connecting to Praxis", color = Color.White.copy(alpha = pulse))
        } else if (!connected) {
            Text("Not connected to Praxis")
            Button(onClick = {
                if (app.auth.state.value.status == com.praxis.caller.auth.AuthStatus.SIGNED_IN && app.auth.token().isBlank())
                    feedback = com.praxis.caller.auth.PraxisAuthManager.OFFLINE_MESSAGE
                else if (app.settings == null || app.auth.token().isBlank()) loginDialog = true
                else callId?.let(app::connectPraxis)
            }, enabled = active && callId != null, modifier = Modifier.testTag("connect-praxis")) { Text("Connect to Praxis") }
        }
        if (connected) {
            Text(if (state.status == PraxisStatus.RECONNECTING) "Praxis reconnecting" else "Praxis connected")
            if (!contactsAllowed) TextButton(onClick = { contactsPermission.launch(Manifest.permission.READ_CONTACTS) }) {
                Text("Show saved contact names")
            }
            if (capture.running && capture.callId == callId && state.framesSent > 0) {
                VoiceOrb(capture.energy)
                Text(when {
                    state.status == PraxisStatus.RECONNECTING -> "Reconnecting; audio send paused"
                    state.inputSilent -> "Microphone audio unavailable; retrying"
                    else -> "Sending microphone audio to Praxis"
                })
            } else {
                Text(if (capture.running && capture.callId == callId) "Starting microphone" else "Microphone is off")
                Button(onClick = { consent = true }, enabled = active) { Text("Enable speaker microphone") }
            }
            if (state.framesSent > 0 || state.lastEvent in listOf("Risk update", "Policy decision", "Analysis unavailable")) {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.animateContentSize()) {
                    AnalysisOrb(color, state.decision != null)
                    if (state.decision != null) Column(Modifier.weight(1f).padding(start = 12.dp)) {
                        Text(state.decision.orEmpty(), color = color, style = MaterialTheme.typography.titleMedium)
                        (state.experimentalScore ?: state.risk)?.let {
                            Text("${if (state.regressorStatus == "BOOTSTRAP_UNTRAINED") "Provisional score" else "Risk score"} ${"%.1f".format(java.util.Locale.US, it)} / 100")
                        }
                        state.detail?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
                    }
                }
                if (state.decision == null) {
                    Text(when {
                        state.inputSilent -> "Microphone audio unavailable; analysis paused"
                        state.lastEvent == "Analysis unavailable" -> "Analysis unavailable"
                        else -> "Waiting for Praxis analysis"
                    })
                    if (state.inputSilent || state.lastEvent == "Analysis unavailable") state.detail?.let { Text(it) }
                }
            }
            TextButton(onClick = {
                context.stopService(Intent(context, CaptureService::class.java)); app.praxis.disconnect()
            }) { Text("Disconnect Praxis") }
        }
        state.error?.let { Text(it) }
        capture.error?.let { Text(it) }
        feedback?.let { Text(it) }
        if (auth.status == AuthStatus.SIGNING_IN) TextButton(onClick = { scope.launch { app.auth.cancel() } }) { Text("Cancel sign-in") }
        auth.message?.let { Text(it) }
    }
    if (loginDialog && (app.settings?.auth == null || app.settings?.passwordLogin == true)) {
        ConnectionDialog(app, onDismiss = { loginDialog = false }, onConnected = {
            loginDialog = false
            callId?.let(app::connectPraxis)
        })
    }
    if (loginDialog && app.settings?.auth != null && app.settings?.passwordLogin != true) AlertDialog(onDismissRequest = { loginDialog = false }, title = { Text("Sign in to Praxis") },
        text = { Text(if (app.settings?.auth == null) "The production sign-in contract and endpoints have not been configured." else "Continue in your browser to sign in. Return here and tap Connect to Praxis.") },
        confirmButton = { TextButton(enabled = app.settings?.auth != null, onClick = {
            loginDialog = false
            scope.launch {
                app.auth.begin()?.let { uri -> try { context.startActivity(Intent(Intent.ACTION_VIEW, uri)) }
                    catch (_: RuntimeException) { app.auth.cancel(); feedback = "No browser is available." } }
            }
        }) { Text("Open sign-in") } }, dismissButton = { TextButton(onClick = { loginDialog = false }) { Text("Cancel") } })
    if (consent) AlertDialog(onDismissRequest = { consent = false }, title = { Text("Speaker microphone analysis") },
        text = { Text(if (app.settings?.acousticInputApproved != true) "Microphone analysis is unavailable for this connection."
            else "Controlled demo: switch to Speaker and keep the other phone muted so only the remote voice reaches this microphone. Nearby audio can still be captured. Audio is analyzed and not retained. Stop anytime.") },
        confirmButton = { TextButton(enabled = app.settings?.acousticInputApproved == true, onClick = {
            consent = false
            if (context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) startCapture()
            else microphone.launch(Manifest.permission.RECORD_AUDIO)
        }) { Text("Start microphone") } }, dismissButton = { TextButton(onClick = { consent = false }) { Text("Cancel") } })
}

@Composable
internal fun VoiceOrb(energy: Float) {
    Canvas(Modifier.size(104.dp)) {
        val radius = size.minDimension * (0.3f + energy.coerceIn(0f, 0.3f))
        val points = (0 until 16).map { n ->
            val angle = n * 2 * PI / 16
            Offset(center.x + cos(angle).toFloat() * radius, center.y + sin(angle).toFloat() * radius)
        }
        points.forEachIndexed { i, point ->
            drawCircle(Color(0xFFCFDDD7), 2.5f, point)
            drawLine(Color(0xFF668378).copy(alpha = 0.5f), point, points[(i + 5) % points.size], 1f)
        }
    }
}
@Composable
internal fun AnalysisOrb(color: Color, compact: Boolean) {
    val diameter by animateDpAsState(if (compact) 90.dp else 148.dp, tween(450), label = "analysis-reveal")
    Canvas(Modifier.size(diameter)) {
        val radius = size.minDimension * 0.42f
        for (row in -7..7) {
            val y = row / 8f
            val ring = sqrt(1 - y * y) * radius
            for (n in 0 until 22) {
                val angle = n * 2 * PI / 22
                drawCircle(color.copy(alpha = (0.35 + 0.6 * (sin(angle) + 1) / 2).toFloat()), 1.6f,
                    Offset(center.x + cos(angle).toFloat() * ring, center.y + y * radius + sin(angle).toFloat() * 4))
            }
        }
    }
}
private suspend fun playDecisionChime() = withContext(Dispatchers.IO) {
    val rate = 16000; val samples = ShortArray(4800) { index ->
        val t = index.toDouble() / rate
        val envelope = sin(PI * index / 4800).pow(2)
        (sin(2 * PI * (if (index < 2400) 740 else 988) * t) * envelope * 6000).toInt().toShort()
    }
    var track: android.media.AudioTrack? = null
    try {
        track = android.media.AudioTrack.Builder().setAudioAttributes(android.media.AudioAttributes.Builder()
            .setUsage(android.media.AudioAttributes.USAGE_NOTIFICATION_EVENT).setContentType(android.media.AudioAttributes.CONTENT_TYPE_SONIFICATION).build())
            .setAudioFormat(android.media.AudioFormat.Builder().setSampleRate(rate).setChannelMask(android.media.AudioFormat.CHANNEL_OUT_MONO)
                .setEncoding(android.media.AudioFormat.ENCODING_PCM_16BIT).build()).setBufferSizeInBytes(samples.size * 2)
            .setTransferMode(android.media.AudioTrack.MODE_STATIC).build()
        track.write(samples, 0, samples.size); track.play(); delay(350)
    } catch (_: Exception) { /* A missing sound never changes calls or results. */ }
    finally { track?.release(); samples.fill(0) }
}
