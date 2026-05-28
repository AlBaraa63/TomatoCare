package com.tomatocare.ui.scan

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.ExperimentalAnimationApi
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import com.tomatocare.ui.components.ScanAnimationOverlay

@OptIn(ExperimentalAnimationApi::class)
@Composable
fun ScanScreen(
    onResultReady: (scanId: Int) -> Unit,
    onBack: () -> Unit,
) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val viewModel: ScanViewModel = viewModel(
        factory = ScanViewModel.factory(context.applicationContext as com.tomatocare.TomatoCareApp)
    )
    val state by viewModel.uiState.collectAsState()

    LaunchedEffect(state) {
        if (state is ScanUiState.Success) {
            onResultReady((state as ScanUiState.Success).savedScanId)
        } else if (state is ScanUiState.LowConfidence) {
            onResultReady((state as ScanUiState.LowConfidence).savedScanId)
        }
    }
    
    val isProcessing = state is ScanUiState.Processing
    val rejectReason = (state as? ScanUiState.Rejected)?.reason

    Box(
        modifier = Modifier.fillMaxSize(),
    ) {
        CameraScreen(
            onCapture = { uri -> viewModel.onImageCaptured(android.graphics.BitmapFactory.decodeFile(uri.path)) },
            onBack = onBack,
            showOverlay = !isProcessing && rejectReason == null,
        )

        if (isProcessing) {
            // New animated overlay
            ScanAnimationOverlay()
        }

        if (rejectReason != null) {
            com.tomatocare.ui.components.GateRejectWarning(
                reason = rejectReason,
                onRetake = viewModel::reset,
            )
        }
    }
}
