package com.tomatocare.ui.scan

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.viewmodel.compose.viewModel
import com.tomatocare.R
import com.tomatocare.TomatoCareApp
import com.tomatocare.di.AppContainer
import com.tomatocare.ui.components.LowConfidenceWarning
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ScanScreen(
    container: AppContainer,
    onResultReady: (Int) -> Unit,
    onBack: () -> Unit,
) {
    val context = LocalContext.current
    val app = context.applicationContext as TomatoCareApp
    val viewModel: ScanViewModel = viewModel(
        factory = ScanViewModel.factory(app)
    )
    val state by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.screen_scan_title)) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = stringResource(R.string.action_back),
                        )
                    }
                },
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
    ) { inner ->
        Box(modifier = Modifier.fillMaxSize().padding(inner)) {
            when (val s = state) {
                ScanUiState.Idle -> CameraScreen(
                    onBitmapReady = viewModel::onImageCaptured,
                    onShowSnackbar = { msg ->
                        scope.launch { snackbarHostState.showSnackbar(msg) }
                    },
                )

                ScanUiState.Processing -> Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center,
                ) {
                    CircularProgressIndicator()
                }

                is ScanUiState.LowConfidence -> LowConfidenceWarning(
                    onRetake = { viewModel.reset() },
                    onProceed = { onResultReady(s.savedScanId) },
                )

                is ScanUiState.Success -> {
                    LaunchedEffect(s.savedScanId) {
                        onResultReady(s.savedScanId)
                    }
                }

                is ScanUiState.Error -> {
                    LaunchedEffect(s.message) {
                        snackbarHostState.showSnackbar(s.message)
                        viewModel.reset()
                    }
                }
            }
        }
    }
}
