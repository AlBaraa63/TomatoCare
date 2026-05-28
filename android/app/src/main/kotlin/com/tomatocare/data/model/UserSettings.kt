package com.tomatocare.data.model

import kotlinx.serialization.Serializable

@Serializable
data class UserSettings(
    val language: Language = Language.ENGLISH,
    val defaultGrowingMethod: GrowingMethod = GrowingMethod.OPEN_FIELD,
    val confidenceThreshold: Float = 0.60f,
    // First-launch onboarding: false until the user dismisses the how-to-use
    // dialog once, then never shown again. New field defaults false so existing
    // installs (whose settings.json lacks it) also see it once after update.
    val hasSeenOnboarding: Boolean = false,
    // UI appearance: LIGHT / DARK / SYSTEM. Defaults to SYSTEM so existing
    // installs inherit the previous behaviour.
    val themeMode: ThemeMode = ThemeMode.SYSTEM,
)
