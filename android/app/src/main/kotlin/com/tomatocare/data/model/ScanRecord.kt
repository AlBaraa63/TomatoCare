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
) {
    val primary: DiagnosisResult?
        get() = results.firstOrNull { it.isPrimary } ?: results.firstOrNull()
}

/** Top-level JSON envelope used for export, import, and on-disk storage. */
@Serializable
data class ScanHistory(
    val scans: List<ScanRecord>,
)
