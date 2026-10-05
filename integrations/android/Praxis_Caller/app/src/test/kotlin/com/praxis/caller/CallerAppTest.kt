package com.praxis.caller

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/** Host-side Android/Compose simulation; not physical-device verification. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class CallerAppTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    @Test fun destinationsShowUnavailableActionsWithoutFakeResults() {
        compose.onNodeWithTag("place-call").assertIsNotEnabled()
        compose.onNodeWithTag("nav-CALL").performClick()
        compose.onNodeWithTag("end-call").assertIsNotEnabled()
        compose.onNodeWithTag("nav-PRAXIS").performClick()
        compose.onNodeWithText("Not connected to Praxis").assertIsDisplayed()
        compose.onNodeWithTag("connect-praxis").assertIsNotEnabled()
        compose.runOnUiThread { compose.activity.onBackPressedDispatcher.onBackPressed() }
        compose.onNodeWithTag("place-call").assertIsNotEnabled()
    }

    @Test fun draftSurvivesTabSwitchAndActivityRecreation() {
        compose.onNodeWithTag("digit-1").performClick()
        compose.onNodeWithTag("digit-2").performClick()
        compose.onNodeWithTag("tab-CONTACTS").performClick()
        compose.onNodeWithText("No entries to display. Check permissions or search again.").performScrollTo().assertIsDisplayed()
        compose.activityRule.scenario.recreate()
        compose.onNodeWithTag("tab-KEYPAD").performScrollTo().performClick()
        compose.onNodeWithTag("number").performScrollTo().assertTextEquals("12")
        compose.onNodeWithTag("tab-RECENTS").performClick()
        compose.onNodeWithText("No entries to display. Check permissions or search again.").performScrollTo().assertIsDisplayed()
    }
}

