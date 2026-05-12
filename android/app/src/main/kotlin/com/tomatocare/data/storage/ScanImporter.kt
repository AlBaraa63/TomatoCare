package com.tomatocare.data.storage

import android.content.Context
import android.net.Uri
import com.tomatocare.data.model.ScanHistory
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json

sealed class ImportResult {
    data class Success(val recordCount: Int) : ImportResult()
    data class Failure(val message: String) : ImportResult()
}

/**
 * Imports a previously exported scan_history.json from a SAF URI.
 *
 * Validation order matters: we parse the payload *before* touching the
 * live storage file. A malformed import file therefore can never destroy
 * existing scan history — failure leaves on-device data untouched.
 */
class ScanImporter(
    private val context: Context,
    private val storage: ScanStorageManager,
) {
    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }

    suspend fun import(sourceUri: Uri): ImportResult = withContext(Dispatchers.IO) {
        val text: String = try {
            context.contentResolver.openInputStream(sourceUri)?.use { input ->
                input.bufferedReader(Charsets.UTF_8).readText()
            } ?: return@withContext ImportResult.Failure(
                "Could not open the selected file."
            )
        } catch (e: SecurityException) {
            return@withContext ImportResult.Failure(
                "Permission denied for the selected file."
            )
        } catch (e: Exception) {
            return@withContext ImportResult.Failure(
                "Read failed: ${e.message ?: "unknown"}"
            )
        }

        val parsed: ScanHistory = try {
            json.decodeFromString(text)
        } catch (e: Exception) {
            return@withContext ImportResult.Failure(
                "Invalid file format: not a TomatoCare scan history JSON."
            )
        }

        // Only after successful parse: replace storage.
        storage.replaceAll(parsed.scans)
        ImportResult.Success(parsed.scans.size)
    }
}
