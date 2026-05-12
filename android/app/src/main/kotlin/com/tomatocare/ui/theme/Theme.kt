package com.tomatocare.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val TomatoRed = Color(0xFFD32F2F)
private val LeafGreen = Color(0xFF388E3C)
private val SoilBrown = Color(0xFF5D4037)
private val SandBeige = Color(0xFFFFF8E1)

private val LightColors = lightColorScheme(
    primary = TomatoRed,
    onPrimary = Color.White,
    secondary = LeafGreen,
    onSecondary = Color.White,
    tertiary = SoilBrown,
    background = SandBeige,
    surface = Color.White,
)

private val DarkColors = darkColorScheme(
    primary = TomatoRed,
    onPrimary = Color.White,
    secondary = LeafGreen,
    onSecondary = Color.White,
    tertiary = SoilBrown,
)

@Composable
fun TomatoCareTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val colorScheme = if (darkTheme) DarkColors else LightColors
    MaterialTheme(
        colorScheme = colorScheme,
        typography = MaterialTheme.typography,
        content = content,
    )
}
