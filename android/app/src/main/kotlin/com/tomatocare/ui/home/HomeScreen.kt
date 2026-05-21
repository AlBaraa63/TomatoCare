package com.tomatocare.ui.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.tomatocare.R
import com.tomatocare.data.model.DiagnosisResult
import com.tomatocare.data.model.ScanRecord
import com.tomatocare.data.model.SeverityLevel
import com.tomatocare.data.model.StressType
import com.tomatocare.di.AppContainer
import com.tomatocare.ui.components.StressBadge
import com.tomatocare.ui.format.formatTimestamp
import com.tomatocare.ui.theme.TomatoCareTheme

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeContent(
    state: HomeUiState,
    onScanClick: () -> Unit,
    onHistoryClick: () -> Unit,
    onSettingsClick: () -> Unit,
    onLastScanClick: (Int) -> Unit,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.app_name)) },
            )
        }
    ) { inner ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(inner)
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                text = stringResource(R.string.home_tagline),
                style = MaterialTheme.typography.bodyLarge,
            )
            Spacer(Modifier.height(16.dp))

            Button(
                modifier = Modifier.fillMaxWidth().height(56.dp),
                onClick = onScanClick,
            ) {
                Icon(Icons.Default.CameraAlt, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text(
                    text = stringResource(R.string.action_scan_leaf),
                    style = MaterialTheme.typography.titleMedium,
                )
            }

            OutlinedButton(
                modifier = Modifier.fillMaxWidth().height(48.dp),
                onClick = onHistoryClick,
            ) {
                Icon(Icons.Default.History, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text(
                    text = stringResource(R.string.action_view_history),
                )
            }

            OutlinedButton(
                modifier = Modifier.fillMaxWidth().height(48.dp),
                onClick = onSettingsClick,
            ) {
                Icon(Icons.Default.Settings, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text(
                    text = stringResource(R.string.action_settings),
                )
            }

            val last = state.lastScan
            if (last != null) {
                Spacer(Modifier.height(16.dp))
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 8.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                    onClick = { onLastScanClick(last.scanId) },
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            text = stringResource(R.string.home_last_scan_title),
                            style = MaterialTheme.typography.labelLarge,
                        )
                        Spacer(Modifier.height(8.dp))
                        val primary = last.primary
                        if (primary != null) {
                            Text(
                                text = primary.conditionNameEn,
                                style = MaterialTheme.typography.titleMedium,
                            )
                            Spacer(Modifier.height(4.dp))
                            StressBadge(primary.stressType)
                        }
                        Spacer(Modifier.height(8.dp))
                        Text(
                            text = formatTimestamp(last.timestamp),
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun HomeScreen(
    container: AppContainer,
    onScanClick: () -> Unit,
    onHistoryClick: () -> Unit,
    onSettingsClick: () -> Unit,
    onLastScanClick: (Int) -> Unit,
) {
    val viewModel: HomeViewModel = viewModel(
        factory = HomeViewModel.factory(container)
    )
    val state by viewModel.uiState.collectAsState()

    LaunchedEffect(Unit) { viewModel.refresh() }

    HomeContent(
        state = state,
        onScanClick = onScanClick,
        onHistoryClick = onHistoryClick,
        onSettingsClick = onSettingsClick,
        onLastScanClick = onLastScanClick
    )
}

@Preview(showBackground = true)
@Composable
fun HomePreview() {
    TomatoCareTheme {
        HomeContent(
            state = HomeUiState(
                isLoading = false,
                lastScan = ScanRecord(
                    scanId = 1,
                    imagePath = "",
                    timestamp = "2024-05-13T10:00:00Z",
                    growingMethod = com.tomatocare.data.model.GrowingMethod.GREENHOUSE,
                    modelVersion = "1.0.0",
                    results = listOf(
                        DiagnosisResult(
                            resultId = 1,
                            conditionId = "tomato_early_blight",
                            conditionNameEn = "Early Blight",
                            conditionNameAr = "لفحة مبكرة",
                            confidence = 0.95,
                            isPrimary = true,
                            stressType = StressType.BIOTIC,
                            severityLevel = SeverityLevel.MEDIUM,
                            treatments = emptyList()
                        )
                    )
                ),
                totalScans = 1
            ),
            onScanClick = {},
            onHistoryClick = {},
            onSettingsClick = {},
            onLastScanClick = {}
        )
    }
}

@Preview(showBackground = true)
@Composable
fun HomeEmptyPreview() {
    TomatoCareTheme {
        HomeContent(
            state = HomeUiState(
                isLoading = false,
                lastScan = null,
                totalScans = 0
            ),
            onScanClick = {},
            onHistoryClick = {},
            onSettingsClick = {},
            onLastScanClick = {}
        )
    }
}
