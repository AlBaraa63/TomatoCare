package com.tomatocare.data.storage

import android.content.Context
import com.tomatocare.data.model.UserSettings
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File

/**
 * Minimal settings persistence — flat JSON, same atomic-write discipline
 * as [ScanStorageManager]. Not DataStore because the codebase already
 * standardises on kotlinx.serialization JSON and the settings file is
 * a single object, no migrations needed.
 */
class SettingsStore(private val context: Context) {

    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }
    private val mutex = Mutex()

    private val file: File get() = File(context.filesDir, FILE_NAME)
    private val temp: File get() = File(context.filesDir, TEMP_NAME)

    suspend fun read(): UserSettings = withContext(Dispatchers.IO) {
        mutex.withLock {
            if (!file.exists()) UserSettings()
            else try {
                json.decodeFromString(file.readText(Charsets.UTF_8))
            } catch (_: Exception) {
                UserSettings()
            }
        }
    }

    suspend fun write(settings: UserSettings) = withContext(Dispatchers.IO) {
        mutex.withLock {
            temp.writeText(json.encodeToString(settings), Charsets.UTF_8)
            if (file.exists()) file.delete()
            temp.renameTo(file)
        }
    }

    companion object {
        private const val FILE_NAME = "settings.json"
        private const val TEMP_NAME = "settings.tmp"
    }
}
