package com.praxis.caller.ui.phone

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedButton
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.praxis.caller.R
import com.praxis.caller.ui.CallerUiState
import com.praxis.caller.ui.PhoneTab
import com.praxis.caller.ui.components.EmptyState

@Composable
fun PhoneScreen(
    state: CallerUiState,
    onTab: (PhoneTab) -> Unit,
    onDigit: (Char) -> Unit,
    onDelete: () -> Unit,
    onClear: () -> Unit,
    onPlaceCall: () -> Unit,
    contacts: List<com.praxis.caller.data.PhoneEntry>,
    recents: List<com.praxis.caller.data.PhoneEntry>,
    onRequestPhoneData: () -> Unit,
    onSelectNumber: (String) -> Unit,
) {
    var query by androidx.compose.runtime.remember { androidx.compose.runtime.mutableStateOf("") }
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(Modifier.fillMaxWidth().selectableGroup()) {
            PhoneTab.entries.forEach { tab ->
                Tab(selected = state.phoneTab == tab, onClick = { onTab(tab) },
                    modifier = Modifier.weight(1f).testTag("tab-" + tab.name),
                    text = { Text(stringResource(when (tab) {
                        PhoneTab.RECENTS -> R.string.recents
                        PhoneTab.CONTACTS -> R.string.contacts
            PhoneTab.KEYPAD -> R.string.keypad
                    })) })
            }
        }
        when (state.phoneTab) {
            PhoneTab.RECENTS, PhoneTab.CONTACTS -> {
                TextButton(onClick = onRequestPhoneData) { Text("Allow / refresh contacts and history") }
                androidx.compose.material3.OutlinedTextField(query, { query = it }, label = { Text("Search") }, singleLine = true)
                val entries = if (state.phoneTab == PhoneTab.CONTACTS) contacts else recents
                val matches = entries.filter { query.isBlank() || it.name.contains(query, true) || it.number.contains(query) }
                if (matches.isEmpty()) Text("No entries to display. Check permissions or search again.")
                androidx.compose.foundation.lazy.LazyColumn(Modifier.heightIn(max = 440.dp)) {
                    items(matches.size) { index ->
                        val entry = matches[index]
                        TextButton(onClick = { onSelectNumber(entry.number) }, enabled = entry.number.isNotBlank()) {
                            com.praxis.caller.ui.components.ContactPhoto(entry.photo)
                            Column { Text(entry.name.ifEmpty { entry.number.ifEmpty { "Unknown number" } }); Text(entry.number); if (entry.detail.isNotBlank()) Text(entry.detail) }
                        }
                    }
                }
            }
            PhoneTab.KEYPAD -> {
                Text(state.number.ifEmpty { stringResource(R.string.number_hint) },
                    Modifier.fillMaxWidth().padding(vertical = 12.dp).testTag("number"),
                    style = MaterialTheme.typography.headlineMedium)
                listOf("123", "456", "789", "*0#").forEach { keys ->
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        keys.forEach { digit ->
                            OutlinedButton(onClick = { onDigit(digit) },
                                modifier = Modifier.weight(1f).heightIn(min = 56.dp).testTag("digit-" + digit)) {
                                Text(digit.toString(), style = MaterialTheme.typography.titleLarge)
                            }
                        }
                    }
                }
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    TextButton(onClick = { onDigit('+') }, enabled = state.number.isEmpty(), modifier = Modifier.weight(1f)) { Text("+") }
                    TextButton(onClick = onDelete, enabled = state.number.isNotEmpty(), modifier = Modifier.weight(1f)) { Text(stringResource(R.string.delete_digit)) }
                    TextButton(onClick = onClear, enabled = state.number.isNotEmpty(), modifier = Modifier.weight(1f)) { Text(stringResource(R.string.clear_number)) }
                }
                Button(onClick = onPlaceCall, enabled = state.number.isNotEmpty(), modifier = Modifier.fillMaxWidth().testTag("place-call")) {
                    Text(stringResource(R.string.call))
                }

            }
        }
    }
}
