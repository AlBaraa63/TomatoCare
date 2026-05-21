package com.tomatocare.ui.settings

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import com.tomatocare.R
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.model.Language
import com.tomatocare.data.model.UserSettings
import com.tomatocare.data.storage.ExportResult
import com.tomatocare.data.storage.ImportResult
import com.tomatocare.di.AppContainer
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class SettingsUiState(
    val settings: UserSettings = UserSettings(),
    val isLoading: Boolean = true,
)

sealed interface SettingsEvent {
    data class ExportFinished(val success: Boolean, val message: String) : SettingsEvent
    data class ImportFinished(val success: Boolean, val message: String) : SettingsEvent
    data object HistoryDeleted : SettingsEvent
    data object LanguageChanged : SettingsEvent
}

class SettingsViewModel(
    application: Application,
    private val container: AppContainer,
) : AndroidViewModel(application) {

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    private val _events = MutableSharedFlow<SettingsEvent>(extraBufferCapacity = 4)
    val events: SharedFlow<SettingsEvent> = _events.asSharedFlow()

    init {
        viewModelScope.launch {
            _uiState.value = SettingsUiState(
                isLoading = false,
                settings = container.settingsStore.read(),
            )
        }
    }

    fun onLanguageChanged(language: Language) {
        viewModelScope.launch {
            val updated = _uiState.value.settings.copy(language = language)
            container.settingsStore.write(updated)
            _uiState.value = _uiState.value.copy(settings = updated)
            _events.emit(SettingsEvent.LanguageChanged)
        }
    }

    fun onDefaultMethodChanged(method: GrowingMethod) {
        viewModelScope.launch {
            val updated = _uiState.value.settings.copy(defaultGrowingMethod = method)
            container.settingsStore.write(updated)
            _uiState.value = _uiState.value.copy(settings = updated)
        }
    }

    fun onExportSelected(uri: Uri) {
        viewModelScope.launch {
            when (val r = container.scanExporter.export(uri)) {
                is ExportResult.Success -> _events.emit(
                    SettingsEvent.ExportFinished(true,
                        getApplication<Application>().getString(
                            R.string.snackbar_exported_n_scans, r.recordCount))
                )
                is ExportResult.Failure -> _events.emit(
                    SettingsEvent.ExportFinished(false,
                        getApplication<Application>().getString(
                            R.string.snackbar_export_failed, r.message))
                )
            }
        }
    }

    fun onImportSelected(uri: Uri) {
        viewModelScope.launch {
            when (val r = container.scanImporter.import(uri)) {
                is ImportResult.Success -> _events.emit(
                    SettingsEvent.ImportFinished(true,
                        getApplication<Application>().getString(
                            R.string.snackbar_imported_n_scans, r.recordCount))
                )
                is ImportResult.Failure -> _events.emit(
                    SettingsEvent.ImportFinished(false,
                        getApplication<Application>().getString(
                            R.string.snackbar_import_failed, r.message))
                )
            }
        }
    }

    fun onDeleteAllConfirmed() {
        viewModelScope.launch {
            container.scanStorageManager.deleteAll()
            _events.emit(SettingsEvent.HistoryDeleted)
        }
    }

    companion object {
        fun factory(app: Application, container: AppContainer):
                ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : androidx.lifecycle.ViewModel> create(
                    modelClass: Class<T>,
                ): T = SettingsViewModel(app, container) as T
            }
    }
}
