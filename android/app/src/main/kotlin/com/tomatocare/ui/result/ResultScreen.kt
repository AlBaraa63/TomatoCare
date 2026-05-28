package com.tomatocare.ui.result

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.produceState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.tomatocare.R
import com.tomatocare.di.AppContainer
import com.tomatocare.ui.components.ConfidenceBar
import com.tomatocare.ui.components.ConfidenceGauge
import com.tomatocare.ui.components.FeedbackCard
import com.tomatocare.ui.components.GrowingMethodSelector
import com.tomatocare.ui.components.LowConfidenceWarning
import com.tomatocare.ui.components.SeverityChip
import com.tomatocare.ui.components.StressBadge
import com.tomatocare.ui.components.TreatmentCard
import com.tomatocare.ui.format.formatTimestamp
import com.tomatocare.ui.util.ThumbnailLoader

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
                        Icon(Icons.Default.ArrowBack, contentDescription = stringResource(R.string.action_back))
                    }
                }
            )
        }
    ) { inner ->
        val record = state.record
        if (record != null) {
            val primary = record.primary
            if (primary != null) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(inner)
                        .verticalScroll(rememberScrollState())
                        .padding(16.dp),
                ) {
                    // Header Card
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                        shape = MaterialTheme.shapes.large,
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Row(verticalAlignment = Alignment.Top) {
                                // Image
                                val density = LocalDensity.current
                                val sizePx = with(density) { 100.dp.roundToPx() }
                                val thumb by produceState<android.graphics.Bitmap?>(null, record.imagePath) {
                                    value = ThumbnailLoader.load(record.imagePath, sizePx)
                                }
                                if (thumb != null) {
                                    Image(
                                        bitmap = thumb!!.asImageBitmap(),
                                        contentDescription = null,
                                        contentScale = ContentScale.Crop,
                                        modifier = Modifier
                                            .size(100.dp)
                                            .clip(MaterialTheme.shapes.medium),
                                    )
                                } else {
                                    Box(
                                        modifier = Modifier
                                            .size(100.dp)
                                            .background(MaterialTheme.colorScheme.surfaceVariant, MaterialTheme.shapes.medium)
                                    )
                                }

                                Spacer(Modifier.width(16.dp))

                                // Disease info
                                Column(modifier = Modifier.weight(1f)) {
                                    val name = if (state.language == com.tomatocare.data.model.Language.ARABIC) {
                                        primary.conditionNameAr
                                    } else {
                                        primary.conditionNameEn
                                    }
                                    Text(
                                        text = name,
                                        style = MaterialTheme.typography.titleLarge,
                                        color = MaterialTheme.colorScheme.onSurface,
                                    )
                                    Text(
                                        text = formatTimestamp(record.timestamp),
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                        modifier = Modifier.padding(top = 4.dp),
                                    )
                                    Spacer(Modifier.height(8.dp))
                                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                        StressBadge(primary.stressType)
                                        SeverityChip(primary.severityLevel)
                                    }
                                }
                            }
                            
                            Spacer(Modifier.height(24.dp))
                            
                            // Gauge
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.Center,
                            ) {
                                ConfidenceGauge(confidence = primary.confidence.toFloat())
                            }
                        }
                    }

                    Spacer(Modifier.height(24.dp))

                    // Growing Method
                    Text(
                        text = stringResource(R.string.result_select_growing_method),
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.padding(start = 4.dp, end = 4.dp, bottom = 8.dp),
                    )
                    GrowingMethodSelector(
                        selected = state.selectedMethod,
                        onSelected = viewModel::onMethodSelected,
                        modifier = Modifier.fillMaxWidth(),
                    )

                    Spacer(Modifier.height(24.dp))

                    // Treatments
                    Text(
                        text = stringResource(R.string.result_treatments_title),
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.padding(start = 4.dp, end = 4.dp, bottom = 12.dp),
                    )
                    
                    if (state.treatments.isEmpty()) {
                        Text(
                            text = stringResource(R.string.result_no_treatments_for_method),
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.padding(horizontal = 4.dp),
                        )
                    } else {
                        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            state.treatments.forEach { t ->
                                TreatmentCard(treatment = t, language = state.language)
                            }
                        }
                    }

                    Spacer(Modifier.height(32.dp))

                    // Feedback Card
                    FeedbackCard(
                        feedback = record.feedback,
                        conditions = state.conditions,
                        language = state.language,
                        onCorrect = { viewModel.submitFeedback(true) },
                        onIncorrect = { id -> viewModel.submitFeedback(false, id) },
                    )

                    // Other possibilities
                    val secondary = record.results.filter { it != primary }
                    if (secondary.isNotEmpty()) {
                        Spacer(Modifier.height(32.dp))
                        Text(
                            text = stringResource(R.string.result_other_possibilities),
                            style = MaterialTheme.typography.titleMedium,
                            modifier = Modifier.padding(start = 4.dp, end = 4.dp, bottom = 12.dp),
                        )
                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            secondary.forEach { sec ->
                                val secName = if (state.language == com.tomatocare.data.model.Language.ARABIC) {
                                    sec.conditionNameAr
                                } else {
                                    sec.conditionNameEn
                                }
                                Row(
                                    modifier = Modifier.fillMaxWidth().padding(horizontal = 4.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                ) {
                                    Text(
                                        text = secName,
                                        style = MaterialTheme.typography.bodyMedium,
                                        modifier = Modifier.weight(1f),
                                    )
                                    Box(modifier = Modifier.width(80.dp).padding(horizontal = 8.dp)) {
                                        ConfidenceBar(confidence = sec.confidence.toFloat())
                                    }
                                    Text(
                                        text = "${(sec.confidence * 100).toInt()}%",
                                        style = MaterialTheme.typography.bodySmall,
                                    )
                                }
                            }
                        }
                    }
                    
                    Spacer(Modifier.height(32.dp))
                }
            }
        }
    }
}
