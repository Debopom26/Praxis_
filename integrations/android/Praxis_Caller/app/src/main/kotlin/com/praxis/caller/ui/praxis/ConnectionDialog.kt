package com.praxis.caller.ui.praxis

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import com.praxis.caller.CallerApplication
import com.praxis.caller.praxis.PraxisSettings
import kotlinx.coroutines.launch

/** Only connection settings are persisted; passwords never enter saved state or preferences. */
@Composable
fun ConnectionDialog(app: CallerApplication, onDismiss: () -> Unit, onConnected: () -> Unit) {
    var server by remember { mutableStateOf(app.settings?.baseUrl ?: app.getString(com.praxis.caller.R.string.praxis_default_server)) }
    var tenant by remember { mutableStateOf(app.settings?.tenantId.orEmpty()) }
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
    AlertDialog(onDismissRequest = { if (!busy) { password = ""; onDismiss() } },
        title = { Text("Sign in to Praxis") },
        text = { Column(Modifier.width(280.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Use the HTTPS address printed when Praxis starts, plus your organization account.")
            OutlinedTextField(server, { server = it.take(2048) }, enabled = !busy,
                label = { Text("HTTPS server address") }, singleLine = true)
            OutlinedTextField(tenant, { tenant = it.take(128) }, enabled = !busy,
                label = { Text("Organization ID") }, singleLine = true)
            OutlinedTextField(username, { username = it.take(128) }, enabled = !busy,
                label = { Text("Username") }, singleLine = true)
            OutlinedTextField(password, { password = it.take(1024) }, enabled = !busy,
                label = { Text("Password") }, singleLine = true,
                visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                trailingIcon = {
                    TextButton(onClick = { passwordVisible = !passwordVisible }) {
                        Text(if (passwordVisible) "Hide" else "Show")
                    }
                })
            error?.let { Text(it) }
        } },
        confirmButton = { TextButton(enabled = !busy && username.isNotBlank() && password.isNotEmpty(),
            onClick = {
                val settings = runCatching { PraxisSettings.passwordSettings(server, tenant) }.getOrNull()
                if (settings == null) { error = "Enter a valid HTTPS server address and organization ID." }
                else {
                    busy = true; error = null
                    val secret = password; password = ""
                    scope.launch {
                        try {
                            if (app.auth.signInWithPassword(settings, username.trim(), secret) {
                                PraxisSettings.saveConnection(app, settings)
                            }) onConnected()
                            else error = app.auth.state.value.message
                        } finally { busy = false }
                    }
                }
            }) { Text(if (busy) "Signing in..." else "Sign in and connect") } },
        dismissButton = { TextButton(enabled = !busy, onClick = { password = ""; onDismiss() }) { Text("Cancel") } })
}
