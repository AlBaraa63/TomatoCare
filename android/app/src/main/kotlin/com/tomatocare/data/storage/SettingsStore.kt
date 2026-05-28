package com.tomatocare.data.storage

import android.content.Context
import com.tomatocare.data.model.UserSettings
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
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
 *
 * Exposes [settings] as a [StateFlow] so UI (theme, language) reacts to
 * changes live: [read] seeds it from disk and [write] updates it. Without
 * this, the in-app theme/language toggle would not apply until app restart.
 */
class SettingsStore(private val context: Context) {

    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }
    private val mutex = Mutex()

    private val _settings = MutableStateFlow(UserSettings())
    /** Latest persisted settings. Seeded by [read], updated by [write]. */
    val settings: StateFlow<UserSettings> = _settings.asStateFlow()

    private val file: File get() = File(context.filesDir, FILE_NAME)
    private val temp: File get() = File(context.filesDir, TEMP_NAME)

    suspend fun read(): UserSettings = withContext(Dispatchers.IO) {
        mutex.withLock {
            val loaded = if (!file.exists()) UserSettings()
            else try {
                json.decodeFromString(file.readText(Charsets.UTF_8))
            } catch (_: Exception) {
                UserSettings()
            }
            _settings.value = loaded
            loaded
        }
    }

    suspend fun write(settings: UserSettings) = withContext(Dispatchers.IO) {
        mutex.withLock {
            temp.writeText(json.encodeToString(settings), Charsets.UTF_8)
            if (file.exists()) file.delete()
            temp.renameTo(file)
            _settings.value = settings
        }
    }

    companion object {
        private const val FILE_NAME = "settings.json"
        private const val TEMP_NAME = "settings.tmp"
    }
}
