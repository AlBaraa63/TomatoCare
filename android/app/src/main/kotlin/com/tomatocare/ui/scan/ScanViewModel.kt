package com.tomatocare.ui.scan

import android.app.Application
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageDecoder
import android.net.Uri
import android.os.Build
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
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
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

    fun onImageCaptured(uri: Uri) {
        viewModelScope.launch {
            _uiState.value = ScanUiState.Processing
            try {
                // Decode here (not in the Composable) so both camera (file://)
                // and gallery (content://) URIs work. decodeFile(uri.path) only
                // handled file:// and returned null for gallery picks → crash.
                val bitmap = decodeBitmap(uri)
                if (bitmap == null) {
                    _uiState.value = ScanUiState.Error(
                        getApplication<Application>().getString(
                            R.string.error_image_decode_failed)
                    )
                    return@launch
                }

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

                val record = buildRecord(output.results, savedPath, method,
                                         output.inferenceTimeMs)
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

    /**
     * Decode a bitmap from any URI (camera file:// or gallery content://) on
     * the IO dispatcher. Returns null on any failure instead of throwing.
     * On API 28+ ImageDecoder applies EXIF orientation automatically; the
     * SOFTWARE allocator is required because TFLite preprocessing reads pixels
     * (a hardware bitmap would fail getPixels).
     */
    private suspend fun decodeBitmap(uri: Uri): Bitmap? = withContext(Dispatchers.IO) {
        val resolver = getApplication<Application>().contentResolver
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                val source = ImageDecoder.createSource(resolver, uri)
                ImageDecoder.decodeBitmap(source) { decoder, _, _ ->
                    decoder.allocator = ImageDecoder.ALLOCATOR_SOFTWARE
                }
            } else {
                resolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it) }
            }
        } catch (t: Throwable) {
            null
        }
    }

    private fun buildRecord(
        results: List<DiagnosisResult>,
        imagePath: String,
        method: GrowingMethod,
        inferenceTimeMs: Long,
    ): ScanRecord = ScanRecord(
        scanId = 0,                       // assigned by ScanStorageManager
        imagePath = imagePath,
        timestamp = DateTimeFormatter.ISO_INSTANT.format(Instant.now()),
        growingMethod = method,
        modelVersion = "2.0.0",
        results = results,
        inferenceTimeMs = inferenceTimeMs,
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
