package com.praxis.caller.auth

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import com.praxis.caller.CallerApplication
import com.praxis.caller.MainActivity
import kotlinx.coroutines.launch

class AuthCallbackActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val uri = intent.data
        if (intent.action == Intent.ACTION_VIEW && uri != null) {
            val app = application as CallerApplication
            app.applicationScope.launch { app.auth.complete(uri) }
        }
        startActivity(Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP))
        finish()
    }
}
