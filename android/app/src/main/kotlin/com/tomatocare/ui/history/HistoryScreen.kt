package com.tomatocare.ui.history

import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Eco
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
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
import com.tomatocare.data.model.ScanRecord
import com.tomatocare.di.AppContainer
import com.tomatocare.ui.components.StressBadge
import com.tomatocare.ui.format.formatTimestamp
import com.tomatocare.ui.util.ThumbnailLoader

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistoryScreen(
    container: AppContainer,
    onItemClick: (Int) -> Unit,
    onBack: () -> Unit,
) {
    val viewModel: HistoryViewModel = viewModel(
        factory = HistoryViewModel.factory(container)
    )
    val state by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    val deletedMsg = stringResource(R.string.snackbar_scan_deleted)
    val undoLabel = stringResource(R.string.snackbar_undo)

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is HistoryEvent.RecordDeleted -> {
                    val result = snackbarHostState.showSnackbar(
                        message = deletedMsg,
                        actionLabel = undoLabel,
                        duration = SnackbarDuration.Short,
                    )
                    if (result == SnackbarResult.ActionPerformed) {
                        viewModel.undoDelete(event.record)
                    }
                }
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.screen_history_title)) },
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
        if (state.records.isEmpty()) {
            Box(
                modifier = Modifier.fillMaxSize().padding(inner),
                contentAlignment = Alignment.Center,
            ) {
                Text(stringResource(R.string.history_empty))
            }
            return@Scaffold
        }

        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(inner).padding(8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            items(state.records, key = { it.scanId }) { record ->
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onItemClick(record.scanId) },
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp).fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        HistoryThumbnail(record)
                        Column(modifier = Modifier.weight(1f).padding(start = 12.dp)) {
                            val primary = record.primary
                            if (primary != null) {
                                Text(
                                    text = primary.conditionNameEn,
                                    style = MaterialTheme.typography.titleMedium,
                                )
                                StressBadge(
                                    stressType = primary.stressType,
                                    modifier = Modifier.padding(top = 4.dp),
                                )
                            }
                            Text(
                                text = formatTimestamp(record.timestamp),
                                style = MaterialTheme.typography.bodySmall,
                                modifier = Modifier.padding(top = 6.dp),
                            )
                        }
                        IconButton(onClick = { viewModel.delete(record) }) {
                            Icon(
                                imageVector = Icons.Default.Delete,
                                contentDescription = stringResource(R.string.action_delete),
                            )
                        }
                    }
                }
            }
        }
    }
}

/**
 * Loads the scan's saved JPEG asynchronously via [ThumbnailLoader].
 * Falls back to the Eco icon while loading or if the file is gone
 * (legitimately possible after history import or external file deletion).
 */
@Composable
private fun HistoryThumbnail(record: ScanRecord) {
    val density = LocalDensity.current
    val sizePx = with(density) { 40.dp.roundToPx() }
    val thumb by produceState<Bitmap?>(initialValue = null, record.imagePath, sizePx) {
        value = ThumbnailLoader.load(record.imagePath, sizePx)
    }
    val bmp = thumb
    if (bmp != null) {
        Image(
            bitmap = bmp.asImageBitmap(),
            contentDescription = null,
            contentScale = ContentScale.Crop,
            modifier = Modifier
                .size(40.dp)
                .clip(RoundedCornerShape(6.dp)),
        )
    } else {
        Icon(
            imageVector = Icons.Default.Eco,
            contentDescription = null,
            modifier = Modifier.size(40.dp),
        )
    }
}
