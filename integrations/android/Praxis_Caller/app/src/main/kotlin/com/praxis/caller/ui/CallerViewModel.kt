package com.praxis.caller.ui

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

enum class Destination { PHONE, CALL, PRAXIS, VOIP }
enum class PhoneTab { RECENTS, CONTACTS, KEYPAD }

data class CallerUiState(
    val destination: Destination = Destination.PHONE,
    val phoneTab: PhoneTab = PhoneTab.KEYPAD,
    val number: String = "",
)

/** UI navigation/draft only. No call, auth or SDK states are synthesized. */
class CallerViewModel(private val savedState: SavedStateHandle) : ViewModel() {
    private val mutableState = MutableStateFlow(
        CallerUiState(
            destination = Destination.entries.firstOrNull { it.name == savedState.get<String>("destination") }
                ?: Destination.PHONE,
            phoneTab = PhoneTab.entries.firstOrNull { it.name == savedState.get<String>("phoneTab") }
                ?: PhoneTab.KEYPAD,
            number = normalizeNumber(savedState.get<String>("number").orEmpty()),
        ),
    )
    val state = mutableState.asStateFlow()

    fun navigate(destination: Destination) = update(state.value.copy(destination = destination))
    fun selectPhoneTab(tab: PhoneTab) = update(state.value.copy(phoneTab = tab))
    fun appendDigit(digit: Char) = update(state.value.copy(number = normalizeNumber(state.value.number + digit)))
    fun deleteDigit() = update(state.value.copy(number = state.value.number.dropLast(1)))
    fun setDraft(number: String) = update(state.value.copy(number = normalizeNumber(number), phoneTab = PhoneTab.KEYPAD))
    fun clearNumber() = update(state.value.copy(number = ""))
    fun backToPhone() = navigate(Destination.PHONE)

    private fun update(next: CallerUiState) {
        savedState["destination"] = next.destination.name
        savedState["phoneTab"] = next.phoneTab.name
        savedState["number"] = next.number
        mutableState.value = next
    }

    companion object {
        const val MAX_NUMBER_LENGTH = 64
        fun normalizeNumber(input: String): String = buildString {
            for (char in input) {
                if (length >= MAX_NUMBER_LENGTH) break
                if (char in '0'..'9' || char == '*' || char == '#' || (char == '+' && isEmpty())) append(char)
            }
        }
    }
}
