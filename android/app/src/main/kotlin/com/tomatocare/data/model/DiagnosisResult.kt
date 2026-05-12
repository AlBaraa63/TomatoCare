package com.tomatocare.data.model

import kotlinx.serialization.Serializable

@Serializable
data class DiagnosisResult(
    val resultId: Int = 0,
    val conditionId: String,           // stable key for repository lookup
    val conditionNameEn: String,
    val conditionNameAr: String,
    val confidence: Double,            // 0.0..1.0
    val isPrimary: Boolean = false,
    val stressType: StressType,
    val severityLevel: SeverityLevel,
    val treatments: List<Treatment> = emptyList(),
)
