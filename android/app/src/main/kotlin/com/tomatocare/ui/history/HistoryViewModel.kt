package com.tomatocare.ui.history

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.tomatocare.data.model.ScanRecord
import com.tomatocare.di.AppContainer
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class HistoryUiState(
    val isLoading: Boolean = true,
    val records: List<ScanRecord> = emptyList(),
    val language: com.tomatocare.data.model.Language = com.tomatocare.data.model.Language.ENGLISH,
)

sealed interface HistoryEvent {
    data class RecordDeleted(val record: ScanRecord) : HistoryEvent
}

class HistoryViewModel(private val container: AppContainer) : ViewModel() {

    private val _uiState = MutableStateFlow(HistoryUiState())
    val uiState: StateFlow<HistoryUiState> = _uiState.asStateFlow()

    private val _events = MutableSharedFlow<HistoryEvent>(extraBufferCapacity = 4)
    val events: SharedFlow<HistoryEvent> = _events.asSharedFlow()

    init { refresh() }

    fun refresh() {
        viewModelScope.launch {
            val all = container.scanStorageManager.loadAll()
            val settings = container.settingsStore.read()
            _uiState.value = HistoryUiState(
                isLoading = false,
                records = all,
                language = settings.language,
            )
        }
    }

    fun delete(record: ScanRecord) {
        viewModelScope.launch {
            container.scanStorageManager.deleteById(record.scanId)
            _events.emit(HistoryEvent.RecordDeleted(record))
            refresh()
        }
    }

    /** Re-insert a record that was just removed (undo from Snackbar). */
    fun undoDelete(record: ScanRecord) {
        viewModelScope.launch {
            container.scanStorageManager.saveRecord(record)
            refresh()
        }
    }

    companion object {
        fun factory(container: AppContainer): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T =
                    HistoryViewModel(container) as T
            }
    }
}
