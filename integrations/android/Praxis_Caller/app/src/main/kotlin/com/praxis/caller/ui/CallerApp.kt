package com.praxis.caller.ui

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Phone
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.material3.Button
import com.praxis.caller.telecom.CallManager
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.praxis.caller.R
import com.praxis.caller.ui.call.CallScreen
import com.praxis.caller.ui.phone.PhoneScreen
import com.praxis.caller.ui.praxis.PraxisScreen

@Composable
fun CallerApp(model: CallerViewModel = viewModel(), calls: CallManager,
    roleHeld: Boolean, message: String, onRequestRole: () -> Unit, onPlaceCall: () -> Unit,
    notificationsAllowed: Boolean, onRequestNotifications: () -> Unit,
    onCallVisibility: (Boolean, Boolean) -> Unit,
    contacts: List<com.praxis.caller.data.PhoneEntry>, recents: List<com.praxis.caller.data.PhoneEntry>, onRequestPhoneData: () -> Unit) {
    val activeCalls by calls.calls.collectAsStateWithLifecycle()
    LaunchedEffect(activeCalls) {
        onCallVisibility(activeCalls.any { !it.ended }, activeCalls.any { it.ringing })
    }
    LaunchedEffect(activeCalls.firstOrNull()?.id) {
        if (activeCalls.isNotEmpty()) model.navigate(Destination.CALL)
    }
    val state by model.state.collectAsStateWithLifecycle()
    BackHandler(enabled = state.destination != Destination.PHONE) { model.backToPhone() }
    Scaffold(bottomBar = {
        NavigationBar {
            Destination.entries.forEach { destination ->
                NavigationBarItem(
                    selected = state.destination == destination,
                    onClick = { model.navigate(destination) },
                    modifier = Modifier.testTag("nav-" + destination.name),
                    icon = { Icon(when (destination) {
                        Destination.PHONE -> Icons.Default.Home
                        Destination.CALL -> Icons.Default.Phone
                        Destination.PRAXIS -> Icons.Default.Info
                    }, contentDescription = null) },
                    label = { Text(stringResource(when (destination) {
                        Destination.PHONE -> R.string.phone
                        Destination.CALL -> R.string.call
                        Destination.PRAXIS -> R.string.praxis
                    })) },
                )
            }
        }
    }) { padding ->
        Column(Modifier.fillMaxSize().padding(padding).padding(horizontal = 20.dp)
            .verticalScroll(rememberScrollState())) {
            Text(if (state.destination == Destination.PHONE) "Phone" else if (state.destination == Destination.CALL) "Call" else "Praxis", Modifier.padding(vertical = 16.dp),
                style = MaterialTheme.typography.headlineMedium)
            if (!roleHeld) Button(onClick = onRequestRole) { Text("Set as default phone app") }
            if (!notificationsAllowed) Button(onClick = onRequestNotifications) { Text("Enable call notifications") }
            if (message.isNotEmpty()) Text(message)
            when (state.destination) {
                Destination.PHONE -> PhoneScreen(state, model::selectPhoneTab, model::appendDigit, model::deleteDigit, model::clearNumber, onPlaceCall, contacts, recents, onRequestPhoneData, { number -> model.setDraft(number); model.selectPhoneTab(PhoneTab.KEYPAD) })
                Destination.CALL -> CallScreen(activeCalls, calls)
                Destination.PRAXIS -> PraxisScreen()
            }
        }
    }
}
