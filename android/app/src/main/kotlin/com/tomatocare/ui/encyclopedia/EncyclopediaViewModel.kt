package com.tomatocare.ui.encyclopedia

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.tomatocare.data.model.ConditionInfo
import com.tomatocare.data.model.Language
import com.tomatocare.di.AppContainer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class EncyclopediaUiState(
    val allConditions: List<ConditionInfo> = emptyList(),
    val filteredConditions: List<ConditionInfo> = emptyList(),
    val searchQuery: String = "",
    val language: Language = Language.ENGLISH,
)

class EncyclopediaViewModel(private val container: AppContainer) : ViewModel() {

    private val _uiState = MutableStateFlow(EncyclopediaUiState())
    val uiState: StateFlow<EncyclopediaUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            val all = container.conditionRepository.getAllConditions()
            val settings = container.settingsStore.read()
            _uiState.value = EncyclopediaUiState(
                allConditions = all,
                filteredConditions = all,
                language = settings.language,
            )
        }
    }

    fun onSearchQueryChanged(query: String) {
        val state = _uiState.value
        val filtered = if (query.isBlank()) {
            state.allConditions
        } else {
            state.allConditions.filter {
                it.nameEn.contains(query, ignoreCase = true) ||
                    it.nameAr.contains(query, ignoreCase = true)
            }
        }
        _uiState.value = state.copy(
            searchQuery = query,
            filteredConditions = filtered,
        )
    }

    companion object {
        fun factory(container: AppContainer): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T =
                    EncyclopediaViewModel(container) as T
            }
    }
}
