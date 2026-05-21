package com.tomatocare.ui.result

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.tomatocare.R
import com.tomatocare.di.AppContainer
import com.tomatocare.ui.components.GrowingMethodSelector
import com.tomatocare.ui.components.SeverityChip
import com.tomatocare.ui.components.StressBadge
import com.tomatocare.ui.components.TreatmentCard
import com.tomatocare.ui.format.formatConfidence
import com.tomatocare.ui.format.formatTimestamp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResultScreen(
    container: AppContainer,
    scanId: Int,
    onBack: () -> Unit,
) {
    val viewModel: ResultViewModel = viewModel(
        factory = ResultViewModel.factory(container, scanId)
    )
    val state by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.screen_result_title)) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = stringResource(R.string.action_back),
                        )
                    }
                },
            )
        }
    ) { inner ->
        val record = state.record
        if (record == null) {
            Column(
                modifier = Modifier.fillMaxSize().padding(inner).padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Text(
                    state.errorMessage ?: stringResource(R.string.error_scan_not_found),
                )
            }
            return@Scaffold
        }

        val primary = record.primary
        if (primary == null) {
            // Record exists but has no results — defensive guard against an
            // import file with a malformed scan. Show the same error UX as
            // a missing-record state and let the user back out.
            Column(
                modifier = Modifier.fillMaxSize().padding(inner).padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Text(stringResource(R.string.error_scan_not_found))
                TextButton(
                    onClick = onBack,
                    modifier = Modifier.padding(top = 16.dp),
                ) {
                    Text(stringResource(R.string.action_back))
                }
            }
            return@Scaffold
        }
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(inner)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = primary.conditionNameEn,
                        style = MaterialTheme.typography.headlineSmall,
                    )
                    Text(
                        text = primary.conditionNameAr,
                        style = MaterialTheme.typography.headlineSmall,
                    )
                    Spacer(Modifier.height(8.dp))
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        StressBadge(primary.stressType)
                        SeverityChip(primary.severityLevel)
                        Text(
                            text = formatConfidence(primary.confidence),
                            style = MaterialTheme.typography.titleMedium,
                        )
                    }
                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = formatTimestamp(record.timestamp),
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }

            Text(
                text = stringResource(R.string.result_select_growing_method),
                style = MaterialTheme.typography.titleSmall,
            )
            GrowingMethodSelector(
                selected = state.selectedMethod,
                onSelected = viewModel::onMethodSelected,
            )

            Text(
                text = stringResource(R.string.result_treatments_title),
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(top = 8.dp),
            )

            if (state.treatments.isEmpty()) {
                Text(stringResource(R.string.result_no_treatments_for_method))
            } else {
                state.treatments.forEach { treatment ->
                    TreatmentCard(
                        treatment = treatment,
                        language = state.language,
                    )
                }
            }

            if (record.results.size > 1) {
                Spacer(Modifier.height(16.dp))
                Text(
                    text = stringResource(R.string.result_other_possibilities),
                    style = MaterialTheme.typography.titleSmall,
                )
                record.results.drop(1).forEach { other ->
                    Card(
                        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                    ) {
                        Row(modifier = Modifier.padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = other.conditionNameEn,
                                modifier = Modifier.weight(1f),
                            )
                            Text(formatConfidence(other.confidence))
                        }
                    }
                }
            }
        }
    }
}
