package com.praxis.caller

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.praxis.caller.praxis.PraxisSettings
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class NativeConnectionTest {
    @Test fun acceptsHttpsRootAndValidTenantOnly() {
        val settings = PraxisSettings.passwordSettings(" https://192.168.1.10 ", " team-1 ")
        assertEquals("https://192.168.1.10/", settings.baseUrl)
        assertEquals("team-1", settings.tenantId)
        assertTrue(settings.passwordLogin)
        assertTrue(settings.acousticInputApproved)
        for (url in listOf("http://192.168.1.10", "https://user:pass@example.com", "https://example.com/path",
            "https://example.com?token=x", "https://example.com#fragment")) {
            assertTrue(url, runCatching { PraxisSettings.passwordSettings(url, "team") }.isFailure)
        }
        assertTrue(runCatching { PraxisSettings.passwordSettings("https://example.com", "bad tenant") }.isFailure)
    }
    @Test fun savesOnlyNonSecretConfigurationAndRestoresIt() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val prefs = context.getSharedPreferences("praxis-connection", Context.MODE_PRIVATE)
        prefs.edit().clear().commit()
        val settings = PraxisSettings.passwordSettings("https://praxis.example", "tenant-a")
        PraxisSettings.saveConnection(context, settings)
        assertEquals(settings, PraxisSettings.load(context))
        val raw = prefs.getString("configuration", "")!!
        assertFalse(raw.contains("password"))
        assertFalse(raw.contains("token"))
        prefs.edit().clear().commit()
    }
}
