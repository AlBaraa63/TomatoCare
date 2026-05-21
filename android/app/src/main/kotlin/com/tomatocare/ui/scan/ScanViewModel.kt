package com.tomatocare.ui.scan

import android.app.Application
import android.graphics.Bitmap
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.tomatocare.R
import com.tomatocare.TomatoCareApp
import com.tomatocare.data.model.DiagnosisResult
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.model.InferenceOutput
import com.tomatocare.data.model.RejectReason
import com.tomatocare.data.model.ScanRecord
import com.tomatocare.di.AppContainer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.format.DateTimeFormatter

sealed interface ScanUiState {
    data object Idle : ScanUiState
    data object Processing : ScanUiState
    data class LowConfidence(val output: InferenceOutput,
                             val savedScanId: Int) : ScanUiState
    data class Success(val output: InferenceOutput,
                       val savedScanId: Int) : ScanUiState
    /**
     * A cascade gate rejected the image before any diagnosis was made
     * (not a leaf, or not a tomato leaf). No scan record is saved — the
     * user is asked to retake. See [RejectReason].
     */
    data class Rejected(val reason: RejectReason) : ScanUiState
    data class Error(val message: String) : ScanUiState
}

class ScanViewModel(
    application: Application,
    private val container: AppContainer,
) : AndroidViewModel(application) {

    private val _uiState = MutableStateFlow<ScanUiState>(ScanUiState.Idle)
    val uiState: StateFlow<ScanUiState> = _uiState.asStateFlow()

    fun onImageCaptured(bitmap: Bitmap) {
        viewModelScope.launch {
            _uiState.value = ScanUiState.Processing
            try {
                val settings = container.settingsStore.read()
                val method = settings.defaultGrowingMethod
                val threshold = settings.confidenceThreshold

                val output: InferenceOutput = container.tfliteEngine.classify(
                    bitmap = bitmap,
                    growingMethod = method,
                    confidenceThreshold = threshold,
                )

                // A gate rejected the image (not a leaf / not a tomato leaf):
                // there is no diagnosis to persist, so skip saving entirely
                // and route straight to the retake prompt.
                if (output.isRejected) {
                    _uiState.value = ScanUiState.Rejected(output.rejectReason)
                    return@launch
                }

                val savedPath = ScanImageSaver.save(
                    getApplication<Application>().applicationContext,
                    bitmap,
                )

                val record = buildRecord(output.results, savedPath, method)
                container.scanStorageManager.saveRecord(record)
                val savedId = container.scanStorageManager.loadAll()
                    .firstOrNull()?.scanId ?: 0

                _uiState.value = if (output.isLowConfidence) {
                    ScanUiState.LowConfidence(output.copy(savedImagePath = savedPath),
                                              savedScanId = savedId)
                } else {
                    ScanUiState.Success(output.copy(savedImagePath = savedPath),
                                        savedScanId = savedId)
                }
            } catch (t: Throwable) {
                _uiState.value = ScanUiState.Error(
                    t.message ?: getApplication<Application>().getString(
                        R.string.error_inference_failed)
                )
            }
        }
    }

    fun reset() { _uiState.value = ScanUiState.Idle }

    private fun buildRecord(
        results: List<DiagnosisResult>,
        imagePath: String,
        method: GrowingMethod,
    ): ScanRecord = ScanRecord(
        scanId = 0,                       // assigned by ScanStorageManager
        imagePath = imagePath,
        timestamp = DateTimeFormatter.ISO_INSTANT.format(Instant.now()),
        growingMethod = method,
        modelVersion = "2.0.0",
        results = results,
    )

    companion object {
        fun factory(app: TomatoCareApp): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T =
                    ScanViewModel(app, app.container) as T
            }
    }
}
