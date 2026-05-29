package com.tomatocare.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.tomatocare.data.model.Language
import com.tomatocare.data.model.ScanRecord
import com.tomatocare.di.AppContainer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class HomeUiState(
    val isLoading: Boolean = true,
    val lastScan: ScanRecord? = null,
    val totalScans: Int = 0,
    val showOnboarding: Boolean = false,
    val distinctConditions: Int = 0,
    val healthRate: Int = 0,
    val topConditions: List<Pair<String, Int>> = emptyList(),
    val language: Language = Language.ENGLISH,
)

class HomeViewModel(private val container: AppContainer) : ViewModel() {
    private val _uiState = MutableStateFlow(HomeUiState())
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    init { refresh() }

    fun refresh() {
        viewModelScope.launch {
            val all = container.scanStorageManager.loadAll()
            val settings = container.settingsStore.read()

            val stats = HomeStats.compute(all, settings.language == Language.ARABIC)

            _uiState.value = HomeUiState(
                isLoading = false,
                lastScan = all.firstOrNull(),
                totalScans = stats.totalScans,
                showOnboarding = !settings.hasSeenOnboarding,
                distinctConditions = stats.distinctConditions,
                healthRate = stats.healthRate,
                topConditions = stats.topConditions,
                language = settings.language,
            )
        }
    }

    /** Persist that onboarding was shown; the dialog never appears again. */
    fun dismissOnboarding() {
        viewModelScope.launch {
            val settings = container.settingsStore.read()
            container.settingsStore.write(settings.copy(hasSeenOnboarding = true))
            _uiState.value = _uiState.value.copy(showOnboarding = false)
        }
    }

    companion object {
        fun factory(container: AppContainer): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T =
                    HomeViewModel(container) as T
            }
    }
}
