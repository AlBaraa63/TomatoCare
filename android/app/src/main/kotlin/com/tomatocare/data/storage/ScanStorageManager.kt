package com.tomatocare.data.storage

import android.content.Context
import com.tomatocare.data.model.ScanHistory
import com.tomatocare.data.model.ScanRecord
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File

/**
 * Source of truth for on-device scan history.
 *
 * Single flat file at filesDir/scan_history.json.
 * Atomic write: serialise to scan_history.tmp first, then rename — a crash
 * mid-write therefore can never leave a corrupt main file (the rename is
 * a single filesystem operation).
 *
 * All public methods are suspend + dispatch to IO. A [Mutex] serialises
 * writes so concurrent saves don't race the temp file.
 */
class ScanStorageManager(private val context: Context) {

    private val json = Json {
        prettyPrint = false              // compact on disk; pretty only for export
        ignoreUnknownKeys = true         // forward-compat: tolerate new fields
        encodeDefaults = true
    }

    private val mutex = Mutex()

    private val storageFile: File
        get() = File(context.filesDir, FILE_NAME)
    private val tempFile: File
        get() = File(context.filesDir, TEMP_NAME)

    suspend fun saveRecord(record: ScanRecord): Unit = withContext(Dispatchers.IO) {
        mutex.withLock {
            val current = loadAllInternal()
            val nextId = (current.maxOfOrNull { it.scanId } ?: 0) + 1
            val recordToSave = if (record.scanId == 0) {
                record.copy(scanId = nextId)
            } else record
            // Prepend to keep "newest first" consistent without re-sorting on read.
            val updated = listOf(recordToSave) + current
            writeAtomic(updated)
        }
    }

    suspend fun loadAll(): List<ScanRecord> = withContext(Dispatchers.IO) {
        mutex.withLock { loadAllInternal() }
    }

    suspend fun getById(scanId: Int): ScanRecord? = withContext(Dispatchers.IO) {
        mutex.withLock { loadAllInternal().firstOrNull { it.scanId == scanId } }
    }

    suspend fun deleteAll(): Unit = withContext(Dispatchers.IO) {
        mutex.withLock {
            if (storageFile.exists()) storageFile.delete()
            if (tempFile.exists()) tempFile.delete()
        }
    }

    suspend fun deleteById(scanId: Int): Boolean = withContext(Dispatchers.IO) {
        mutex.withLock {
            val current = loadAllInternal()
            val updated = current.filterNot { it.scanId == scanId }
            if (updated.size == current.size) return@withLock false
            writeAtomic(updated)
            true
        }
    }

    /** Replace entire history (used by [ScanImporter]). */
    suspend fun replaceAll(records: List<ScanRecord>): Unit =
        withContext(Dispatchers.IO) {
            mutex.withLock { writeAtomic(records) }
        }

    /**
     * Attach (or replace) user feedback on a single scan. Returns false if no
     * scan with [scanId] exists. Used by the data-flywheel feedback prompt.
     */
    suspend fun setFeedback(
        scanId: Int,
        feedback: com.tomatocare.data.model.ScanFeedback,
    ): Boolean = withContext(Dispatchers.IO) {
        mutex.withLock {
            val current = loadAllInternal()
            var found = false
            val updated = current.map {
                if (it.scanId == scanId) { found = true; it.copy(feedback = feedback) }
                else it
            }
            if (found) writeAtomic(updated)
            found
        }
    }

    // --- internals (must be called while holding [mutex]) ---

    private fun loadAllInternal(): List<ScanRecord> {
        if (!storageFile.exists()) return emptyList()
        return try {
            val text = storageFile.readText(Charsets.UTF_8)
            if (text.isBlank()) emptyList()
            else json.decodeFromString<ScanHistory>(text).scans
        } catch (e: Exception) {
            // Corrupted file: do not throw to the UI. Rename to .bad so
            // the user can recover manually via SAF export of the .bad file.
            storageFile.renameTo(File(context.filesDir, "scan_history.bad"))
            emptyList()
        }
    }

    private fun writeAtomic(records: List<ScanRecord>) {
        val payload = json.encodeToString(ScanHistory(records))
        tempFile.writeText(payload, Charsets.UTF_8)
        // File.renameTo is atomic on the same filesystem on Android.
        // We delete the existing target first because Java rename semantics
        // disallow overwrite on some Android API levels.
        if (storageFile.exists()) storageFile.delete()
        tempFile.renameTo(storageFile)
    }

    companion object {
        private const val FILE_NAME = "scan_history.json"
        private const val TEMP_NAME = "scan_history.tmp"
    }
}
