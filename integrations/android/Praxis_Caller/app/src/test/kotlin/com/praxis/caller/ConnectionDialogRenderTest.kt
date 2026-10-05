package com.praxis.caller

import androidx.activity.compose.setContent
import android.graphics.Bitmap
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import com.praxis.caller.ui.praxis.ConnectionDialog
import com.praxis.caller.ui.theme.PraxisCallerTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], qualifiers = "w411dp-h891dp-mdpi")
class ConnectionDialogRenderTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    @Test fun connectionDialogRendersWithoutCrash() {
        compose.mainClock.autoAdvance = false
        compose.runOnUiThread {
            compose.activity.setContent {
                PraxisCallerTheme {
                    ConnectionDialog(compose.activity.application as CallerApplication, {}, {})
                }
            }
        }
        compose.mainClock.advanceTimeBy(500)
        compose.runOnUiThread {
            val view = compose.activity.window.decorView
            val bitmap = Bitmap.createBitmap(view.width, view.height, Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
            bitmap.recycle()
        }
    }
}
