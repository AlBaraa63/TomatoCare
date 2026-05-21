package com.tomatocare.data.model

/**
 * Why a scan produced no diagnosis. Set by the cascade engine when an
 * earlier gate rejects the image before Stage 3 ever runs.
 *
 *  - NONE          : image passed both gates; [InferenceOutput.results] is real.
 *  - NOT_A_LEAF    : Stage 1 leaf gate rejected — probably not a leaf at all.
 *  - NOT_A_TOMATO  : Stage 2 tomato gate rejected — a leaf, but not tomato.
 *
 * Internal-only (mirrors [InferenceOutput]); never persisted or exported.
 */
enum class RejectReason { NONE, NOT_A_LEAF, NOT_A_TOMATO }

/**
 * Internal-only — never persisted or exported, so deliberately NOT
 * @Serializable. Used as the result type of [com.tomatocare.inference.TFLiteEngine.classify].
 *
 * When [rejectReason] is not [RejectReason.NONE], the cascade stopped at a
 * gate and [results] is empty — the UI shows a "retake" prompt instead of a
 * diagnosis, and no scan record is saved.
 */
data class InferenceOutput(
    val results: List<DiagnosisResult>,
    val isLowConfidence: Boolean,
    val inferenceTimeMs: Long,
    val savedImagePath: String? = null,
    val rejectReason: RejectReason = RejectReason.NONE,
) {
    val isRejected: Boolean get() = rejectReason != RejectReason.NONE
}
