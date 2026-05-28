package com.tomatocare.ui.theme

import androidx.compose.ui.graphics.Color

// ── Clinical Blue (Primary) ────────────────────────────────────────────
val ClinicalBlue = Color(0xFF1565C0)
val ClinicalBlueLight = Color(0xFF64B5F6)
val ClinicalBlueSurface = Color(0xFFE3F2FD)
val ClinicalBlueDarkSurface = Color(0xFF1A3A5C)

// ── Healthy Green (Secondary) ──────────────────────────────────────────
val HealthyGreen = Color(0xFF2E7D32)
val HealthyGreenLight = Color(0xFF81C784)
val HealthyGreenSurface = Color(0xFFE8F5E9)
val HealthyGreenDarkSurface = Color(0xFF1B3D1F)

// ── Alert Amber (Tertiary) ─────────────────────────────────────────────
val AlertAmber = Color(0xFFE65100)
val AlertAmberLight = Color(0xFFFFB74D)

// ── Error / Critical ───────────────────────────────────────────────────
val CriticalRed = Color(0xFFC62828)
val CriticalRedLight = Color(0xFFEF5350)

// ── Neutral tones ──────────────────────────────────────────────────────
val BackgroundLight = Color(0xFFFAFBFD)
val BackgroundDark = Color(0xFF0F1419)
val SurfaceLight = Color(0xFFFFFFFF)
val SurfaceDark = Color(0xFF1A1F25)
val SurfaceVariantLight = Color(0xFFF0F4F8)
val SurfaceVariantDark = Color(0xFF252B33)
val OutlineLight = Color(0xFFD0D7DE)
val OutlineDark = Color(0xFF3A424D)
val OnSurfaceLight = Color(0xFF1A1F25)
val OnSurfaceDark = Color(0xFFE6EDF3)
val OnSurfaceVariantLight = Color(0xFF57606A)
val OnSurfaceVariantDark = Color(0xFF8B949E)

// ── Severity palette ───────────────────────────────────────────────────
val SeverityLowColor = Color(0xFF43A047)
val SeverityMediumColor = Color(0xFFFB8C00)
val SeverityHighColor = Color(0xFFE53935)
val SeverityCriticalColor = Color(0xFFB71C1C)

// ── Treatment type colours ─────────────────────────────────────────────
val TreatmentChemicalColor = Color(0xFF1565C0)
val TreatmentCulturalColor = Color(0xFF2E7D32)
val TreatmentBiologicalColor = Color(0xFF7B1FA2)

// ── Confidence interpolation ───────────────────────────────────────────
/** Maps a 0.0–1.0 confidence to a colour (red→amber→green). */
fun confidenceColor(confidence: Float): Color = when {
    confidence >= 0.85f -> SeverityLowColor        // strong green
    confidence >= 0.60f -> SeverityMediumColor      // amber
    else -> SeverityHighColor                       // red
}
