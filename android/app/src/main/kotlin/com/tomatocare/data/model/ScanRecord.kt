package com.tomatocare.data.model

import kotlinx.serialization.Serializable

@Serializable
data class ScanRecord(
    val scanId: Int,
    val imagePath: String,
    val timestamp: String,             // ISO-8601, UTC
    val growingMethod: GrowingMethod,
    val modelVersion: String,
    val results: List<DiagnosisResult>,
    // User feedback on this diagnosis (data-flywheel). Null until the user
    // answers "was this correct?". New field defaults null so existing
    // history files remain valid (ignoreUnknownKeys + encodeDefaults).
    val feedback: ScanFeedback? = null,
) {
    val primary: DiagnosisResult?
        get() = results.firstOrNull { it.isPrimary } ?: results.firstOrNull()
}

/**
 * User-supplied ground truth for a scan, used to grow a real-world (UAE)
 * labelled dataset for retraining. [correctedConditionId] is the true
 * class key (matches Stage-3 class names / ConditionInfo.conditionId) and
 * is only set when [wasCorrect] is false.
 */
@Serializable
data class ScanFeedback(
    val wasCorrect: Boolean,
    val correctedConditionId: String? = null,
    val timestamp: String,             // ISO-8601, UTC — when feedback was given
)

/** Top-level JSON envelope used for export, import, and on-disk storage. */
@Serializable
data class ScanHistory(
    val scans: List<ScanRecord>,
)
