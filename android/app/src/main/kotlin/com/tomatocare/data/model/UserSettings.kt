package com.tomatocare.data.model

import kotlinx.serialization.Serializable

@Serializable
data class UserSettings(
    val language: Language = Language.ENGLISH,
    val defaultGrowingMethod: GrowingMethod = GrowingMethod.OPEN_FIELD,
    val confidenceThreshold: Float = 0.60f,
)
