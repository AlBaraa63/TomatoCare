package com.tomatocare.data.model

import kotlinx.serialization.Serializable

/**
 * Repository-side metadata loaded from assets/treatments.json. This is
 * what [com.tomatocare.data.repository.TreatmentRepository] returns when
 * mapping a model class index to user-facing condition info.
 */
@Serializable
data class ConditionInfo(
    val conditionId: String,           // e.g. "early_blight"
    val classLabel: String,            // e.g. "Tomato_Early_blight" — matches TF class name
    val nameEn: String,
    val nameAr: String,
    val stressType: StressType,
    val severityDefault: SeverityLevel,
    val treatments: List<Treatment>,
)

@Serializable
data class TreatmentsCatalog(
    val _review_note: String = "",
    val modelVersion: String = "1.0.0",
    val conditions: List<ConditionInfo>,
)
