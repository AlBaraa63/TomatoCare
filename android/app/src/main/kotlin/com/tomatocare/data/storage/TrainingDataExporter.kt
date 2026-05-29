package com.tomatocare.data.storage

import android.content.Context
import android.net.Uri
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File
import java.time.Instant
import java.time.format.DateTimeFormatter
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

sealed class TrainingExportResult {
    data class Success(val imageCount: Int, val labelCount: Int) : TrainingExportResult()
    /** No scans carry feedback yet — nothing labelled to export. */
    data object Empty : TrainingExportResult()
    data class Failure(val message: String) : TrainingExportResult()
}

/**
 * Data-flywheel export. Bundles every scan the user gave feedback on into a
 * single ZIP at a SAF-chosen URI:
 *
 *   <label>/scan_<id>.jpg     images grouped by their TRUE label
 *   manifest.json             per-image record (label, predicted, etc.)
 *
 * The true label is the user's correction when they marked the diagnosis
 * wrong, otherwise the model's own primary prediction (a confirmed label).
 * Labels are the canonical conditionId keys, so the folder layout drops
 * straight into the training farm (same shape integrate_plantdoc.py expects).
 * Fully offline — writes only to the user-selected document.
 */
class TrainingDataExporter(
    private val context: Context,
    private val storage: ScanStorageManager,
) {
    private val prettyJson = Json { prettyPrint = true; encodeDefaults = true }

    @Serializable
    private data class ManifestEntry(
        val scanId: Int,
        val label: String,
        val predicted: String?,
        val wasCorrect: Boolean,
        val confidence: Double?,
        val growingMethod: String,
        val modelVersion: String,
        val scanTimestamp: String,
        val feedbackTimestamp: String,
    )

    @Serializable
    private data class Manifest(
        val app: String = "TomatoCare",
        val schemaVersion: Int = 1,
        val exportedAt: String,
        val imageCount: Int,
        val labels: List<String>,
        val entries: List<ManifestEntry>,
    )

    suspend fun export(targetUri: Uri): TrainingExportResult = withContext(Dispatchers.IO) {
        try {
            val labelled = storage.loadAll().filter { it.feedback != null }
            if (labelled.isEmpty()) return@withContext TrainingExportResult.Empty

            val entries = mutableListOf<ManifestEntry>()
            val labels = linkedSetOf<String>()

            val os = context.contentResolver.openOutputStream(targetUri, "w")
                ?: return@withContext TrainingExportResult.Failure(
                    "Could not open output stream — pick a writable location.")

            ZipOutputStream(os).use { zip ->
                for (r in labelled) {
                    val fb = r.feedback ?: continue
                    val label = resolveLabel(
                        wasCorrect = fb.wasCorrect,
                        predictedConditionId = r.primary?.conditionId,
                        correctedConditionId = fb.correctedConditionId,
                    )
                    val img = File(r.imagePath)
                    if (!img.exists()) continue

                    labels += label
                    zip.putNextEntry(ZipEntry("$label/scan_${r.scanId}.jpg"))
                    img.inputStream().use { it.copyTo(zip) }
                    zip.closeEntry()

                    entries += ManifestEntry(
                        scanId = r.scanId,
                        label = label,
                        predicted = r.primary?.conditionId,
                        wasCorrect = fb.wasCorrect,
                        confidence = r.primary?.confidence,
                        growingMethod = r.growingMethod.name,
                        modelVersion = r.modelVersion,
                        scanTimestamp = r.timestamp,
                        feedbackTimestamp = fb.timestamp,
                    )
                }

                if (entries.isEmpty()) {
                    // All labelled records had missing image files.
                    return@withContext TrainingExportResult.Empty
                }

                val manifest = Manifest(
                    exportedAt = DateTimeFormatter.ISO_INSTANT.format(Instant.now()),
                    imageCount = entries.size,
                    labels = labels.toList(),
                    entries = entries,
                )
                zip.putNextEntry(ZipEntry("manifest.json"))
                zip.write(prettyJson.encodeToString(manifest).toByteArray(Charsets.UTF_8))
                zip.closeEntry()
            }

            TrainingExportResult.Success(imageCount = entries.size, labelCount = labels.size)
        } catch (e: Exception) {
            TrainingExportResult.Failure(e.message ?: "Unknown export error")
        }
    }

    companion object {
        const val UNKNOWN_LABEL = "unknown"

        /**
         * The true training label for an exported scan: the user's correction
         * when they marked the diagnosis wrong, otherwise the model's own
         * primary prediction (a user-confirmed label). Falls back to
         * [UNKNOWN_LABEL] if neither yields a usable id. Pure → unit-tested.
         */
        fun resolveLabel(
            wasCorrect: Boolean,
            predictedConditionId: String?,
            correctedConditionId: String?,
        ): String =
            (if (wasCorrect) predictedConditionId else correctedConditionId)
                ?.takeIf { it.isNotBlank() } ?: UNKNOWN_LABEL
    }
}
