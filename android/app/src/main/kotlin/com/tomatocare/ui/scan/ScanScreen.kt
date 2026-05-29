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
        when (val s = state) {
            is ScanUiState.Success -> onResultReady(s.savedScanId)
            is ScanUiState.LowConfidence -> onResultReady(s.savedScanId)
            is ScanUiState.Error -> {
                // Decode or inference failed — tell the user and return to camera
                // instead of leaving a silent blank screen (or crashing).
                android.widget.Toast.makeText(
                    context, s.message, android.widget.Toast.LENGTH_LONG).show()
                viewModel.reset()
            }
            else -> Unit
        }
    }

    val isProcessing = state is ScanUiState.Processing
    val rejectReason = (state as? ScanUiState.Rejected)?.reason

    Box(
        modifier = Modifier.fillMaxSize(),
    ) {
        CameraScreen(
            onCapture = { uri -> viewModel.onImageCaptured(uri) },
            onBack = onBack,
            showOverlay = !isProcessing && rejectReason == null,
            onShowSnackbar = { msg ->
                android.widget.Toast.makeText(
                    context, msg, android.widget.Toast.LENGTH_SHORT).show()
            },
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
