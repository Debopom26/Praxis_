package com.praxis.caller.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Colors = darkColorScheme(
    primary = Color(0xFF4CCD87),
    onPrimary = Color(0xFF062517),
    secondary = Color(0xFFB4D9C5),
    secondaryContainer = Color(0xFF263F34),
    onSecondaryContainer = Color(0xFFD6F4E4),
    surfaceContainer = Color(0xFF191E1B),
    background = Color(0xFF101313),
    surface = Color(0xFF101313),
)

@Composable
fun PraxisCallerTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = Colors, content = content)
}

