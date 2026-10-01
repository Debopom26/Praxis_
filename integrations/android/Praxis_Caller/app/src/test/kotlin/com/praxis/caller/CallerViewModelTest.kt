package com.praxis.caller

import androidx.lifecycle.SavedStateHandle
import com.praxis.caller.ui.*
import org.junit.Assert.*
import org.junit.Test

class CallerViewModelTest {
    @Test fun draftRejectsUnsupportedCharactersAndCapsLength() {
        assertEquals("+12*#3", CallerViewModel.normalizeNumber("+1a2+*#3"))
        assertEquals(64, CallerViewModel.normalizeNumber("7".repeat(200)).length)
        assertEquals("", CallerViewModel.normalizeNumber("abc"))
    }

    @Test fun navigationPreservesDraftAndBackReturnsToPhone() {
        val model = CallerViewModel(SavedStateHandle())
        model.appendDigit('4')
        model.appendDigit('2')
        model.selectPhoneTab(PhoneTab.CONTACTS)
        model.navigate(Destination.PRAXIS)
        model.backToPhone()
        assertEquals(CallerUiState(Destination.PHONE, PhoneTab.CONTACTS, "42"), model.state.value)
        model.deleteDigit()
        assertEquals("4", model.state.value.number)
        model.clearNumber()
        model.deleteDigit()
        assertEquals("", model.state.value.number)
    }

    @Test fun restoredStateRecoversNavigationAndSanitizesDraft() {
        val model = CallerViewModel(SavedStateHandle(mapOf(
            "destination" to "CALL", "phoneTab" to "RECENTS", "number" to "+12wrong3",
        )))
        assertEquals(CallerUiState(Destination.CALL, PhoneTab.RECENTS, "+123"), model.state.value)
    }

    @Test fun unknownRestoredRoutesFallBackSafely() {
        val model = CallerViewModel(SavedStateHandle(mapOf("destination" to "gone", "phoneTab" to "gone")))
        assertEquals(CallerUiState(), model.state.value)
    }
}

