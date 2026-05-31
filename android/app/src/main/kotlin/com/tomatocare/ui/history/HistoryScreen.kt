package com.tomatocare.ui.history

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Eco
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.SwipeToDismissBox
import androidx.compose.material3.SwipeToDismissBoxValue
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.rememberSwipeToDismissBoxState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.tomatocare.R
import com.tomatocare.data.model.ScanRecord
import com.tomatocare.data.model.SeverityLevel
import com.tomatocare.di.AppContainer
import com.tomatocare.ui.components.ConfidenceBar
import com.tomatocare.ui.components.FullScreenImageViewer
import com.tomatocare.ui.components.SeverityChip
import com.tomatocare.ui.format.formatTimestamp
import com.tomatocare.ui.util.ThumbnailLoader

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistoryScreen(
    container: AppContainer,
    onItemClick: (Int) -> Unit,
) {
    val viewModel: HistoryViewModel = viewModel(
        factory = HistoryViewModel.factory(container)
    )
    val state by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    val context = LocalContext.current

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is HistoryEvent.RecordDeleted -> {
                    val deletedRecord = event.record
                    val message = context.getString(R.string.snackbar_scan_deleted)
                    val action = context.getString(R.string.snackbar_undo)
                    val result = snackbarHostState.showSnackbar(
                        message = message,
                        actionLabel = action,
                        duration = androidx.compose.material3.SnackbarDuration.Short,
                    )
                    if (result == SnackbarResult.ActionPerformed) {
                        viewModel.undoDelete(deletedRecord)
                    }
                }
            }
        }
    }

    LaunchedEffect(Unit) { viewModel.refresh() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.screen_history_title)) },
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
    ) { inner ->
        Column(modifier = Modifier.fillMaxSize().padding(inner)) {
            // Search + severity filter — only once there is history to filter.
            if (state.allRecords.isNotEmpty()) {
                OutlinedTextField(
                    value = state.query,
                    onValueChange = viewModel::onQueryChanged,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    placeholder = { Text(stringResource(R.string.history_search_hint)) },
                    leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
                    singleLine = true,
                    shape = MaterialTheme.shapes.medium,
                )
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState())
                        .padding(horizontal = 16.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    FilterChip(
                        selected = state.severityFilter == null,
                        onClick = { viewModel.onSeverityFilterChanged(null) },
                        label = { Text(stringResource(R.string.filter_all)) },
                    )
                    SeverityLevel.values().forEach { sev ->
                        FilterChip(
                            selected = state.severityFilter == sev,
                            onClick = { viewModel.onSeverityFilterChanged(sev) },
                            label = { Text(stringResource(severityLabelRes(sev))) },
                        )
                    }
                }
                Spacer(Modifier.height(8.dp))
            }

            when {
                state.allRecords.isEmpty() && !state.isLoading ->
                    CenteredMessage(stringResource(R.string.history_empty))

                state.records.isEmpty() && !state.isLoading ->
                    CenteredMessage(stringResource(R.string.history_no_matches))

                else -> LazyColumn(modifier = Modifier.fillMaxSize()) {
                    items(items = state.records, key = { it.scanId }) { record ->
                        SwipeableHistoryItem(
                            record = record,
                            language = state.language,
                            onClick = { onItemClick(record.scanId) },
                            onDelete = { viewModel.delete(record) },
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun CenteredMessage(text: String) {
    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text(
            text = text,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(32.dp),
        )
    }
}

private fun severityLabelRes(s: SeverityLevel): Int = when (s) {
    SeverityLevel.LOW -> R.string.severity_low
    SeverityLevel.MEDIUM -> R.string.severity_medium
    SeverityLevel.HIGH -> R.string.severity_high
    SeverityLevel.CRITICAL -> R.string.severity_critical
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SwipeableHistoryItem(
    record: ScanRecord,
    language: com.tomatocare.data.model.Language,
    onClick: () -> Unit,
    onDelete: () -> Unit,
) {
    val dismissState = rememberSwipeToDismissBoxState(
        confirmValueChange = { value ->
            if (value == SwipeToDismissBoxValue.EndToStart) {
                onDelete()
                true
            } else false
        }
    )

    SwipeToDismissBox(
        state = dismissState,
        backgroundContent = {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp, vertical = 8.dp)
                    .clip(MaterialTheme.shapes.medium)
                    .background(MaterialTheme.colorScheme.error)
                    .padding(horizontal = 24.dp),
                contentAlignment = Alignment.CenterEnd,
            ) {
                Icon(
                    imageVector = Icons.Default.Delete,
                    contentDescription = stringResource(R.string.action_delete),
                    tint = Color.White,
                )
            }
        },
        enableDismissFromStartToEnd = false,
    ) {
        HistoryItemCard(record, language, onClick)
    }
}

@Composable
private fun HistoryItemCard(
    record: ScanRecord,
    language: com.tomatocare.data.model.Language,
    onClick: () -> Unit,
) {
    var showFullImage by remember { mutableStateOf(false) }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .clickable(onClick = onClick),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
        shape = MaterialTheme.shapes.medium,
    ) {
        Row(
            modifier = Modifier.padding(16.dp).fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            val density = LocalDensity.current
            val sizePx = with(density) { 64.dp.roundToPx() }
            val thumb by produceState<android.graphics.Bitmap?>(null, record.imagePath) {
                value = ThumbnailLoader.load(record.imagePath, sizePx)
            }

            if (thumb != null) {
                Image(
                    bitmap = thumb!!.asImageBitmap(),
                    contentDescription = stringResource(R.string.cd_view_full_image),
                    contentScale = ContentScale.Crop,
                    modifier = Modifier
                        .size(64.dp)
                        .clip(MaterialTheme.shapes.small)
                        .clickable { showFullImage = true },  // tap thumb = view image; row = details
                )
            } else {
                Box(
                    modifier = Modifier
                        .size(64.dp)
                        .background(MaterialTheme.colorScheme.surfaceVariant, MaterialTheme.shapes.small),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(Icons.Default.Eco, null, tint = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }

            Spacer(Modifier.width(16.dp))

            Column(modifier = Modifier.weight(1f)) {
                val primary = record.primary
                if (primary != null) {
                    val name = if (language == com.tomatocare.data.model.Language.ARABIC) {
                        primary.conditionNameAr
                    } else {
                        primary.conditionNameEn
                    }
                    Text(
                        text = name,
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSurface,
                    )
                    Spacer(Modifier.height(4.dp))
                    ConfidenceBar(confidence = primary.confidence.toFloat())
                    Spacer(Modifier.height(6.dp))
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        SeverityChip(primary.severityLevel)
                        Spacer(Modifier.weight(1f))
                        Column(horizontalAlignment = androidx.compose.ui.Alignment.End) {
                            Text(
                                text = formatTimestamp(record.timestamp),
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                            record.inferenceTimeMs?.let { ms ->
                                Text(
                                    text = stringResource(R.string.latency_ms, ms),
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                        }
                    }
                }
            }
        }
    }

    if (showFullImage) {
        FullScreenImageViewer(imagePath = record.imagePath, onDismiss = { showFullImage = false })
    }
}
