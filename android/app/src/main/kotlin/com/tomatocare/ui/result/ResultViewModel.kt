package com.tomatocare.ui.result

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.tomatocare.data.model.ConditionInfo
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.model.Language
import com.tomatocare.data.model.ScanFeedback
import com.tomatocare.data.model.ScanRecord
import com.tomatocare.data.model.Treatment
import com.tomatocare.di.AppContainer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.format.DateTimeFormatter

data class ResultUiState(
    val isLoading: Boolean = true,
    val record: ScanRecord? = null,
    val selectedMethod: GrowingMethod = GrowingMethod.OPEN_FIELD,
    val treatments: List<Treatment> = emptyList(),
    val language: Language = Language.ENGLISH,
    val conditions: List<ConditionInfo> = emptyList(),
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
                conditions = container.treatmentRepository.allConditions()
                    .sortedBy { it.conditionId },
                errorMessage = null,
            )
        }
    }

    /**
     * Record the user's verdict on this diagnosis (data-flywheel). Pass
     * [correctedConditionId] only when the user marks it wrong and picks the
     * true condition. Persists to history and refreshes state in place.
     */
    fun submitFeedback(wasCorrect: Boolean, correctedConditionId: String? = null) {
        val record = _uiState.value.record ?: return
        viewModelScope.launch {
            val feedback = ScanFeedback(
                wasCorrect = wasCorrect,
                correctedConditionId = if (wasCorrect) null else correctedConditionId,
                timestamp = DateTimeFormatter.ISO_INSTANT.format(Instant.now()),
            )
            container.scanStorageManager.setFeedback(record.scanId, feedback)
            _uiState.value = _uiState.value.copy(
                record = record.copy(feedback = feedback),
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
