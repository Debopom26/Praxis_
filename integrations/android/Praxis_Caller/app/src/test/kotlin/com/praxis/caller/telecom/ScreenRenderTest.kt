package com.praxis.caller.telecom

import android.graphics.Bitmap
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.praxis.caller.ui.praxis.*
import com.praxis.caller.ui.theme.PraxisCallerTheme
import android.telecom.Call
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.graphics.asAndroidBitmap
import com.praxis.caller.MainActivity
import com.praxis.caller.CallerApplication
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode
import java.io.File

/** Host-rendered images with explicitly synthetic test calls. These are NOT phone screenshots. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], qualifiers = "w411dp-h891dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class ScreenRenderTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private fun save(name: String) {
        val dir = File(checkNotNull(System.getProperty("praxis.render.dir"))); dir.mkdirs()
        compose.runOnUiThread {
            val view = compose.activity.window.decorView
            val bitmap = Bitmap.createBitmap(view.width, view.height, Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
            File(dir, name).outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
            bitmap.recycle()
        }
    }
    @Test fun phoneAndCallRemainVisibleWithPraxisUnconfigured() {
        compose.onNodeWithTag("digit-5").performClick()
        compose.onNodeWithTag("place-call").assertIsEnabled()
        save("phone-host.png")
        val app = compose.activity.application as CallerApplication
        var id = ""
        compose.runOnUiThread { id = app.calls.add(RenderCall()) }
        compose.waitForIdle()
        compose.onNodeWithTag("connect-praxis").assertIsEnabled()
        compose.onNodeWithTag("end-call").performScrollTo().assertIsDisplayed().assertIsEnabled()
        save("call-host.png")
        compose.runOnUiThread { app.calls.remove(id) }
    }
    @Test fun renderDistinctOrbsWithExplicitSyntheticFixtureLabel() {
        compose.runOnUiThread {
            compose.activity.setContent { PraxisCallerTheme {
                Column(Modifier.fillMaxSize().padding(24.dp)) {
                    Text("HOST TEST FIXTURE - not a Praxis result", color = androidx.compose.ui.graphics.Color.White)
                    Text("Voice / audio", color = androidx.compose.ui.graphics.Color.White)
                    VoiceOrb(0.1f)
                    Text("Analysis / decision", color = androidx.compose.ui.graphics.Color.White)
                    AnalysisOrb(riskColor(null), false)
                    Row { AnalysisOrb(riskColor(60.0), true); Text("Synthetic test score 60 / 100", color = androidx.compose.ui.graphics.Color.White) }
                }
            } }
        }
        compose.waitForIdle()
        save("orbs-host-fixture.png")
    }
    private class RenderCall : CallPort {
        override fun snapshot(id: String) = CallState(id, "5550100", Call.STATE_ACTIVE, System.currentTimeMillis() - 12000)
        override fun observe(changed: () -> Unit) {}
        override fun release() {}
        override fun answer() {}
        override fun reject() {}
        override fun disconnect() {}
        override fun playDtmf(digit: Char) {}
        override fun stopDtmf() {}
        override fun hold() {}
        override fun unhold() {}
        override fun setMuted(value: Boolean) {}
        override fun setAudioRoute(route: Int) {}
    }
}
