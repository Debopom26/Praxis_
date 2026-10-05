package com.praxis.caller

import android.net.Uri
import com.praxis.caller.auth.PraxisAuthManager
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class AuthBoundaryTest {
    private val redirect = "praxis-caller://auth/callback"
    @Test fun callbackRequiresExactTargetSingleStateAndCode() {
        assertTrue(PraxisAuthManager.validCallback(Uri.parse("$redirect?state=nonce&code=one"), redirect))
        for (url in listOf("https://auth/callback?state=x&code=y", "$redirect/extra?state=x&code=y", "$redirect?state=x&state=y&code=z",
            "$redirect?state=x&code=y&access_token=secret", "$redirect?state=x&code=y#fragment", "$redirect?code=y", "$redirect?state=x&error=denied")) {
            assertFalse(url, PraxisAuthManager.validCallback(Uri.parse(url), redirect))
        }
    }
}
