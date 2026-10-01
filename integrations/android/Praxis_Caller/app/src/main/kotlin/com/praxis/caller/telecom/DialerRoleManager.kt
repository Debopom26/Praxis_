package com.praxis.caller.telecom

import android.Manifest
import android.app.role.RoleManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.telecom.TelecomManager
import android.telecom.PhoneAccountHandle
import android.telephony.PhoneNumberUtils

class DialerRoleManager(private val context: Context) {
    private val roles get() = context.getSystemService(RoleManager::class.java)
    fun available() = roles?.isRoleAvailable(RoleManager.ROLE_DIALER) == true
    fun held() = roles?.isRoleHeld(RoleManager.ROLE_DIALER) == true
    fun request(): Intent? = if (available()) roles?.createRequestRoleIntent(RoleManager.ROLE_DIALER) else null
    fun callPermission() = context.checkSelfPermission(Manifest.permission.CALL_PHONE) == PackageManager.PERMISSION_GRANTED
    fun phoneAccounts(): List<PhoneAccountHandle> {
        if (context.checkSelfPermission(Manifest.permission.READ_PHONE_STATE) != PackageManager.PERMISSION_GRANTED) return emptyList()
        return try {
        context.getSystemService(TelecomManager::class.java)?.callCapablePhoneAccounts.orEmpty()
        } catch (_: SecurityException) { emptyList() }
    }
    fun accountLabel(account: PhoneAccountHandle, index: Int): String = try {
        context.getSystemService(TelecomManager::class.java)?.getPhoneAccount(account)?.label?.toString() ?: "SIM ${index + 1}"
    } catch (_: SecurityException) { "SIM ${index + 1}" }
    fun placeCall(number: String, account: PhoneAccountHandle? = null): DialResult {
        val validated = validateNumber(number) ?: return DialResult.INVALID_NUMBER
        if (!held()) return DialResult.ROLE_REQUIRED
        if (!callPermission()) return DialResult.PERMISSION_REQUIRED
        if (account != null && account !in phoneAccounts()) return DialResult.UNAVAILABLE
        val telecom = context.getSystemService(TelecomManager::class.java) ?: return DialResult.UNAVAILABLE
        return try {
            val extras = Bundle().apply {
                if (account != null) putParcelable(TelecomManager.EXTRA_PHONE_ACCOUNT_HANDLE, account)
            }
            telecom.placeCall(Uri.fromParts("tel", validated, null), extras)
            DialResult.REQUESTED // A request is not proof of a dialing/active call.
        } catch (_: SecurityException) { DialResult.PERMISSION_REQUIRED }
          catch (_: IllegalArgumentException) { DialResult.INVALID_NUMBER }
          catch (_: IllegalStateException) { DialResult.UNAVAILABLE }
    }
    companion object {
        fun validateNumber(raw: String): String? {
            if (raw.length > 128 || raw.any { it !in "0123456789+*#()- ." }) return null
            val number = PhoneNumberUtils.stripSeparators(raw)
            return number.takeIf { it.length in 1..64 && it.any { c -> c in '0'..'9' } &&
                it.withIndex().all { (i, c) -> c in '0'..'9' || c == '*' || c == '#' || (i == 0 && c == '+') } }
        }
        fun draftFrom(intent: Intent): String? = if (intent.action == Intent.ACTION_DIAL && intent.data?.scheme == "tel")
            validateNumber(intent.data?.schemeSpecificPart.orEmpty()) else null
    }
}
enum class DialResult { REQUESTED, INVALID_NUMBER, ROLE_REQUIRED, PERMISSION_REQUIRED, UNAVAILABLE }
