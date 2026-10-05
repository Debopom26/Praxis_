package com.praxis.caller.data

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.CallLog
import android.provider.ContactsContract
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

data class PhoneEntry(val name: String, val number: String, val photo: String? = null, val detail: String = "")
data class PhoneData(val contacts: List<PhoneEntry> = emptyList(), val recents: List<PhoneEntry> = emptyList(), val error: String? = null)

class PhoneDataRepository(private val context: Context) {
    private fun allowed(permission: String) = context.checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED
    suspend fun lookup(number: String): PhoneEntry? = withContext(Dispatchers.IO) {
        if (number.isBlank() || !allowed(Manifest.permission.READ_CONTACTS)) return@withContext null
        try {
            context.contentResolver.query(Uri.withAppendedPath(ContactsContract.PhoneLookup.CONTENT_FILTER_URI, Uri.encode(number)),
                arrayOf(ContactsContract.PhoneLookup.DISPLAY_NAME, ContactsContract.PhoneLookup.PHOTO_THUMBNAIL_URI), null, null, null)?.use {
                if (it.moveToFirst()) PhoneEntry(it.getString(0).orEmpty(), number, it.getString(1)) else null
            }
        } catch (_: RuntimeException) { null }
    }
    suspend fun load(): PhoneData = withContext(Dispatchers.IO) {
        var error: String? = null
        val contacts = try {
            if (!allowed(Manifest.permission.READ_CONTACTS)) emptyList() else
                context.contentResolver.query(ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                    arrayOf(ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME, ContactsContract.CommonDataKinds.Phone.NUMBER,
                        ContactsContract.CommonDataKinds.Phone.PHOTO_THUMBNAIL_URI), null, null, "display_name COLLATE NOCASE ASC")?.use { c ->
                    buildList { while (c.moveToNext()) add(PhoneEntry(c.getString(0).orEmpty(), c.getString(1).orEmpty(), c.getString(2))) }
                }.orEmpty()
        } catch (_: RuntimeException) { error = "Contacts are unavailable. Check permissions and retry."; emptyList() }
        val recents = try {
            if (!allowed(Manifest.permission.READ_CALL_LOG)) emptyList() else
                context.contentResolver.query(CallLog.Calls.CONTENT_URI,
                    arrayOf(CallLog.Calls.NUMBER, CallLog.Calls.TYPE, CallLog.Calls.DATE, CallLog.Calls.CACHED_NAME, CallLog.Calls.NUMBER_PRESENTATION),
                    null, null, CallLog.Calls.DATE + " DESC")?.use { c -> buildList {
                        while (c.moveToNext() && size < 100) {
                            val visible = c.getInt(4) == android.telecom.TelecomManager.PRESENTATION_ALLOWED
                            val kind = when (c.getInt(1)) { CallLog.Calls.INCOMING_TYPE -> "Incoming"; CallLog.Calls.OUTGOING_TYPE -> "Outgoing"; CallLog.Calls.MISSED_TYPE -> "Missed"; else -> "Call" }
                            add(PhoneEntry(if (visible) c.getString(3).orEmpty() else "Private number", if (visible) c.getString(0).orEmpty() else "",
                                detail = "$kind - ${java.text.DateFormat.getDateTimeInstance().format(java.util.Date(c.getLong(2)))}"))
                        }
                    } }.orEmpty()
        } catch (_: RuntimeException) { error = "Call history is unavailable. Check permissions and retry."; emptyList() }
        PhoneData(contacts, recents, error)
    }
}
