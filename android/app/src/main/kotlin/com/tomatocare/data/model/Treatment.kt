package com.tomatocare.data.model

import kotlinx.serialization.Serializable

@Serializable
data class Treatment(
    val treatmentId: Int = 0,
    val growingMethod: GrowingMethod,
    val treatmentType: TreatmentType,
    val urgencyLevel: UrgencyLevel,
    val recommendationEn: String,
    val recommendationAr: String,
)
