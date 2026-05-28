package com.tomatocare.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.tomatocare.data.model.ThemeMode

private val LightColors = lightColorScheme(
    primary = ClinicalBlue,
    onPrimary = Color.White,
    primaryContainer = ClinicalBlueSurface,
    onPrimaryContainer = ClinicalBlue,
    secondary = HealthyGreen,
    onSecondary = Color.White,
    secondaryContainer = HealthyGreenSurface,
    onSecondaryContainer = HealthyGreen,
    tertiary = AlertAmber,
    onTertiary = Color.White,
    error = CriticalRed,
    onError = Color.White,
    background = BackgroundLight,
    onBackground = OnSurfaceLight,
    surface = SurfaceLight,
    onSurface = OnSurfaceLight,
    surfaceVariant = SurfaceVariantLight,
    onSurfaceVariant = OnSurfaceVariantLight,
    outline = OutlineLight,
)

private val DarkColors = darkColorScheme(
    primary = ClinicalBlueLight,
    onPrimary = Color(0xFF00315C),
    primaryContainer = ClinicalBlueDarkSurface,
    onPrimaryContainer = ClinicalBlueLight,
    secondary = HealthyGreenLight,
    onSecondary = Color(0xFF003910),
    secondaryContainer = HealthyGreenDarkSurface,
    onSecondaryContainer = HealthyGreenLight,
    tertiary = AlertAmberLight,
    onTertiary = Color(0xFF4A2800),
    error = CriticalRedLight,
    onError = Color(0xFF600004),
    background = BackgroundDark,
    onBackground = OnSurfaceDark,
    surface = SurfaceDark,
    onSurface = OnSurfaceDark,
    surfaceVariant = SurfaceVariantDark,
    onSurfaceVariant = OnSurfaceVariantDark,
    outline = OutlineDark,
)

private val TomatoCareShapes = Shapes(
    small = RoundedCornerShape(8.dp),
    medium = RoundedCornerShape(12.dp),
    large = RoundedCornerShape(16.dp),
    extraLarge = RoundedCornerShape(24.dp),
)

@Composable
fun TomatoCareTheme(
    themeMode: ThemeMode = ThemeMode.SYSTEM,
    content: @Composable () -> Unit,
) {
    val darkTheme = when (themeMode) {
        ThemeMode.LIGHT -> false
        ThemeMode.DARK -> true
        ThemeMode.SYSTEM -> isSystemInDarkTheme()
    }
    val colorScheme = if (darkTheme) DarkColors else LightColors
    MaterialTheme(
        colorScheme = colorScheme,
        typography = TomatoCareTypography,
        shapes = TomatoCareShapes,
        content = content,
    )
}
