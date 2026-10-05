package com.praxis.caller

import android.Manifest
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.content.pm.PackageManager
import androidx.lifecycle.lifecycleScope
import com.praxis.caller.data.PhoneDataRepository
import kotlinx.coroutines.launch
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModelProvider
import com.praxis.caller.telecom.DialerRoleManager
import com.praxis.caller.telecom.DialResult
import com.praxis.caller.ui.CallerApp
import com.praxis.caller.ui.CallerViewModel
import com.praxis.caller.ui.Destination
import com.praxis.caller.ui.theme.PraxisCallerTheme

class MainActivity : ComponentActivity() {
    private lateinit var model: CallerViewModel
    private val role by lazy { DialerRoleManager(this) }
    private var accounts by mutableStateOf<List<android.telecom.PhoneAccountHandle>>(emptyList())
    private var accountPermissionAsked = false
    private val accountPermissionRequest = registerForActivityResult(ActivityResultContracts.RequestPermission()) {
        message = if (it) "Phone access granted. Tap Call again." else "SIM selection unavailable; Android will select the account."
    }
    private var roleHeld by mutableStateOf(false)
    private var message by mutableStateOf("")
    private var notificationsAllowed by mutableStateOf(false)
    private var contacts by mutableStateOf<List<com.praxis.caller.data.PhoneEntry>>(emptyList())
    private var recents by mutableStateOf<List<com.praxis.caller.data.PhoneEntry>>(emptyList())
    private val phoneDataRequest = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { loadPhoneData() }
    private val notificationRequest = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        notificationsAllowed = granted
        message = if (granted) "Call notifications enabled." else "Call notifications are disabled. Enable them in app settings for incoming alerts."
    }
    private val roleRequest = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {
        refreshRole()
        message = if (roleHeld) "Default phone app selected. Tap Call to place a call." else "Default phone app was not changed."
    }
    private val permissionRequest = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {
        message = if (role.callPermission()) "Permission granted. Tap Call again to place the call." else "Phone permission is required to place a call."
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        model = ViewModelProvider(this)[CallerViewModel::class.java]
        if (savedInstanceState == null) acceptDialIntent(intent)
        enableEdgeToEdge()
        setContent { PraxisCallerTheme {
            if (accounts.isNotEmpty()) androidx.compose.material3.AlertDialog(
                onDismissRequest = { accounts = emptyList() }, title = { androidx.compose.material3.Text("Choose SIM") },
                text = { androidx.compose.foundation.layout.Column {
                    accounts.forEachIndexed { index, account -> androidx.compose.material3.TextButton(onClick = {
                        accounts = emptyList(); sendCall(account)
                    }) { androidx.compose.material3.Text(role.accountLabel(account, index)) } }
                } }, confirmButton = {}, dismissButton = { androidx.compose.material3.TextButton(onClick = { accounts = emptyList() }) { androidx.compose.material3.Text("Cancel") } })
            CallerApp(model, (application as CallerApplication).calls, roleHeld, message,
                onRequestRole = ::requestRole, onPlaceCall = ::placeCall,
                notificationsAllowed = notificationsAllowed,
                onRequestNotifications = {
                    if (Build.VERSION.SDK_INT >= 33) notificationRequest.launch(Manifest.permission.POST_NOTIFICATIONS)
                },
                onCallVisibility = { hasCall, ringing ->
                    setShowWhenLocked(hasCall)
                    setTurnScreenOn(ringing)
                }, contacts = contacts, recents = recents, onRequestPhoneData = ::requestPhoneData)
        } }
    }
    override fun onResume() { super.onResume(); refreshRole() }
    private fun requestPhoneData() = phoneDataRequest.launch(arrayOf(Manifest.permission.READ_CONTACTS, Manifest.permission.READ_CALL_LOG))
    private fun loadPhoneData() { lifecycleScope.launch { PhoneDataRepository(this@MainActivity).load().let { contacts = it.contacts; recents = it.recents; it.error?.let { error -> message = error } } } }
    override fun onNewIntent(intent: Intent) { super.onNewIntent(intent); setIntent(intent); acceptDialIntent(intent) }
    private fun acceptDialIntent(intent: Intent) {
        if (intent.action == Intent.ACTION_DIAL) {
            model.setDraft(DialerRoleManager.draftFrom(intent).orEmpty())
            model.navigate(Destination.PHONE)
        }
    }
    private fun refreshRole() {
        roleHeld = role.held()
        notificationsAllowed = Build.VERSION.SDK_INT < 33 ||
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == android.content.pm.PackageManager.PERMISSION_GRANTED
        loadPhoneData()
    }
    private fun requestRole() {
        val request = role.request()
        if (request == null) message = "Default phone role is unavailable on this device."
        else try { roleRequest.launch(request) } catch (_: android.content.ActivityNotFoundException) {
            message = "Default phone selection is unavailable."
        }
    }
    private fun placeCall() {
        if (role.held() && role.callPermission()) {
            if (!accountPermissionAsked && checkSelfPermission(Manifest.permission.READ_PHONE_STATE) != PackageManager.PERMISSION_GRANTED) {
                accountPermissionAsked = true
                accountPermissionRequest.launch(Manifest.permission.READ_PHONE_STATE)
                return
            }
            val options = role.phoneAccounts()
            if (options.size > 1) { accounts = options; return }
            sendCall(options.singleOrNull())
        } else sendCall(null)
    }
    private fun sendCall(account: android.telecom.PhoneAccountHandle?) {
        when (role.placeCall(model.state.value.number, account)) {
            DialResult.ROLE_REQUIRED -> requestRole()
            DialResult.PERMISSION_REQUIRED -> {
                val permissions = mutableListOf(Manifest.permission.CALL_PHONE)
                if (Build.VERSION.SDK_INT >= 33) permissions += Manifest.permission.POST_NOTIFICATIONS
                permissionRequest.launch(permissions.toTypedArray())
            }
            DialResult.INVALID_NUMBER -> message = "Enter a valid phone number."
            DialResult.UNAVAILABLE -> message = "Calling is unavailable. Check your SIM and phone service."
            DialResult.REQUESTED -> message = "Call request sent to Android. Waiting for call status."
        }
    }
}
