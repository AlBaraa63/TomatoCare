package com.tomatocare.data.model

/**
 * Internal-only — never persisted or exported, so deliberately NOT
 * @Serializable. Used as the result type of [com.tomatocare.inference.TFLiteEngine.classify].
 */
data class InferenceOutput(
    val results: List<DiagnosisResult>,
    val isLowConfidence: Boolean,
    val inferenceTimeMs: Long,
    val savedImagePath: String? = null,
)
