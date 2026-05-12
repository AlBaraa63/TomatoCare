package com.tomatocare.ui.result

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.model.Language
import com.tomatocare.data.model.ScanRecord
import com.tomatocare.data.model.Treatment
import com.tomatocare.di.AppContainer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ResultUiState(
    val isLoading: Boolean = true,
    val record: ScanRecord? = null,
    val selectedMethod: GrowingMethod = GrowingMethod.OPEN_FIELD,
    val treatments: List<Treatment> = emptyList(),
    val language: Language = Language.ENGLISH,
    val errorMessage: String? = null,
)

class ResultViewModel(
    private val container: AppContainer,
    private val scanId: Int,
) : ViewModel() {

    private val _uiState = MutableStateFlow(ResultUiState())
    val uiState: StateFlow<ResultUiState> = _uiState.asStateFlow()

    init { load() }

    fun load() {
        viewModelScope.launch {
            val settings = container.settingsStore.read()
            val record = container.scanStorageManager.getById(scanId)
            val method = record?.growingMethod ?: settings.defaultGrowingMethod
            val primary = record?.primary
            val treatments = if (primary != null) {
                container.treatmentRepository.getTreatments(
                    primary.conditionId, method)
            } else emptyList()
            _uiState.value = ResultUiState(
                isLoading = false,
                record = record,
                selectedMethod = method,
                treatments = treatments,
                language = settings.language,
                errorMessage = if (record == null) "Scan not found" else null,
            )
        }
    }

    fun onMethodSelected(method: GrowingMethod) {
        val record = _uiState.value.record ?: return
        val primary = record.primary ?: return
        val treatments = container.treatmentRepository.getTreatments(
            primary.conditionId, method)
        _uiState.value = _uiState.value.copy(
            selectedMethod = method,
            treatments = treatments,
        )
    }

    companion object {
        fun factory(container: AppContainer, scanId: Int):
                ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T =
                    ResultViewModel(container, scanId) as T
            }
    }
}
