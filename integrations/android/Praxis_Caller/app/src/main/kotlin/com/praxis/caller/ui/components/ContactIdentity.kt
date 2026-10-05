package com.praxis.caller.ui.components

import android.graphics.BitmapFactory
import android.net.Uri
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.material3.MaterialTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.ui.Alignment
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.praxis.caller.data.PhoneDataRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

@Composable
fun ContactPhoto(uri: String?) {
    val context = LocalContext.current
    val bitmap by produceState<android.graphics.Bitmap?>(null, uri) {
        value = withContext(Dispatchers.IO) {
            if (uri == null || Uri.parse(uri).scheme != "content") null else try {
                val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                context.contentResolver.openInputStream(Uri.parse(uri))?.use { BitmapFactory.decodeStream(it, null, bounds) }
                val options = BitmapFactory.Options().apply {
                    inSampleSize = 1
                    while (bounds.outWidth / inSampleSize > 256 || bounds.outHeight / inSampleSize > 256) inSampleSize *= 2
                }
                context.contentResolver.openInputStream(Uri.parse(uri))?.use { BitmapFactory.decodeStream(it, null, options) }
            } catch (_: Exception) { null }
        }
    }
    bitmap?.let { Image(it.asImageBitmap(), "Contact photo", Modifier.size(72.dp).clip(CircleShape)) }
}
@Composable
fun ContactIdentity(number: String) {
    val context = LocalContext.current
    val entry by produceState<com.praxis.caller.data.PhoneEntry?>(null, number) {
        value = PhoneDataRepository(context).lookup(number)
    }
    if (entry?.photo == null) Box(Modifier.size(88.dp).clip(CircleShape).background(Color(0xFF303C38)), contentAlignment = Alignment.Center) {
        Text(entry?.name?.firstOrNull()?.toString() ?: "?", style = MaterialTheme.typography.headlineLarge)
    } else ContactPhoto(entry?.photo)
    entry?.name?.takeIf(String::isNotBlank)?.let { Text(it, style = MaterialTheme.typography.headlineSmall) }
    Text(number.ifEmpty { "Unknown or private number" })
}
