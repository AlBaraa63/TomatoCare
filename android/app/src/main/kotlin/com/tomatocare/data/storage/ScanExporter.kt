package com.tomatocare.data.storage

import android.content.Context
import android.net.Uri
import com.tomatocare.data.model.ScanHistory
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

sealed class ExportResult {
    data class Success(val recordCount: Int) : ExportResult()
    data class Failure(val message: String) : ExportResult()
}

/**
 * Exports the current scan history to a user-chosen URI obtained via
 * `Intent(ACTION_CREATE_DOCUMENT)`. Output is pretty-printed for human
 * readability (the on-disk copy stays compact).
 */
class ScanExporter(
    private val context: Context,
    private val storage: ScanStorageManager,
) {
    @OptIn(ExperimentalSerializationApi::class)
    private val prettyJson = Json {
        prettyPrint = true
        prettyPrintIndent = "  "
        encodeDefaults = true
    }

    suspend fun export(targetUri: Uri): ExportResult = withContext(Dispatchers.IO) {
        try {
            val records = storage.loadAll()
            val payload = prettyJson.encodeToString(ScanHistory(records))
            context.contentResolver.openOutputStream(targetUri, "w")?.use { os ->
                os.write(payload.toByteArray(Charsets.UTF_8))
                os.flush()
            } ?: return@withContext ExportResult.Failure(
                "Could not open output stream — pick a writable location."
            )
            ExportResult.Success(records.size)
        } catch (e: Exception) {
            ExportResult.Failure(e.message ?: "Unknown export error")
        }
    }
}
