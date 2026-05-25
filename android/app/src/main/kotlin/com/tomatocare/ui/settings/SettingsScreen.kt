package com.tomatocare.ui.settings

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.tomatocare.R
import com.tomatocare.TomatoCareApp
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.model.Language
import com.tomatocare.di.AppContainer

// RTL Checklist (verify on Arabic emulator before submission):
//   [ ] Navigation back arrow points RIGHT (auto-flipped via AutoMirrored icon)
//   [ ] List items: icon on the visually-leading edge (start, not left)
//   [ ] StressBadge/SeverityChip: padding uses horizontal symmetry so text mirrors
//   [ ] All padding asymmetry uses start/end, never left/right
//   [ ] App bar title and dialog buttons sit at the appropriate edge

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    container: AppContainer,
    onBack: () -> Unit,
) {
    val context = LocalContext.current
    val app = context.applicationContext as TomatoCareApp
    val viewModel: SettingsViewModel = viewModel(
        factory = SettingsViewModel.factory(app, container)
    )
    val state by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    var showDeleteDialog by remember { mutableStateOf(false) }
    var showImportDialog by remember { mutableStateOf<android.net.Uri?>(null) }

    val exportLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/json")
    ) { uri ->
        if (uri != null) viewModel.onExportSelected(uri)
    }

    val importLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) showImportDialog = uri
    }

    val trainingExportLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/zip")
    ) { uri ->
        if (uri != null) viewModel.onExportTrainingDataSelected(uri)
    }

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is SettingsEvent.ExportFinished ->
                    snackbarHostState.showSnackbar(event.message)
                is SettingsEvent.ImportFinished ->
                    snackbarHostState.showSnackbar(event.message)
                SettingsEvent.HistoryDeleted ->
                    snackbarHostState.showSnackbar(
                        context.getString(R.string.toast_history_deleted))
                SettingsEvent.LanguageChanged -> {
                    // Force activity recreate so resources re-resolve under the new locale.
                    (context as? androidx.activity.ComponentActivity)?.recreate()
                }
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.screen_settings_title)) },
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
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(inner)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            // Language section
            Text(stringResource(R.string.settings_language),
                 style = MaterialTheme.typography.titleMedium)
            Language.values().forEach { lang ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .selectable(
                            selected = state.settings.language == lang,
                            onClick = { viewModel.onLanguageChanged(lang) },
                        )
                        .padding(vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    RadioButton(
                        selected = state.settings.language == lang,
                        onClick = { viewModel.onLanguageChanged(lang) },
                    )
                    Text(
                        text = stringResource(
                            if (lang == Language.ENGLISH)
                                R.string.language_english
                            else R.string.language_arabic
                        ),
                        modifier = Modifier.padding(start = 8.dp),
                    )
                }
            }

            HorizontalDivider()

            // Default growing method
            Text(stringResource(R.string.settings_default_growing_method),
                 style = MaterialTheme.typography.titleMedium)
            GrowingMethod.values().forEach { method ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .selectable(
                            selected = state.settings.defaultGrowingMethod == method,
                            onClick = { viewModel.onDefaultMethodChanged(method) },
                        )
                        .padding(vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    RadioButton(
                        selected = state.settings.defaultGrowingMethod == method,
                        onClick = { viewModel.onDefaultMethodChanged(method) },
                    )
                    Text(
                        text = stringResource(labelResFor(method)),
                        modifier = Modifier.padding(start = 8.dp),
                    )
                }
            }

            HorizontalDivider()

            // Data management
            Text(stringResource(R.string.settings_data_management),
                 style = MaterialTheme.typography.titleMedium)
            Button(
                onClick = { exportLauncher.launch("tomatocare_history.json") },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(stringResource(R.string.action_export_history))
            }
            OutlinedButton(
                onClick = { importLauncher.launch(arrayOf("application/json", "text/*")) },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(stringResource(R.string.action_import_history))
            }
            OutlinedButton(
                onClick = { trainingExportLauncher.launch("tomatocare_training_data.zip") },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(stringResource(R.string.action_export_training_data))
            }
            Text(
                text = stringResource(R.string.export_training_data_hint),
                style = MaterialTheme.typography.bodySmall,
            )
            Button(
                onClick = { showDeleteDialog = true },
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFB71C1C)),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(stringResource(R.string.action_delete_all_history))
            }

            Spacer(Modifier.height(24.dp))
            Text(
                text = stringResource(R.string.settings_about_blurb),
                style = MaterialTheme.typography.bodySmall,
            )
        }
    }

    if (showDeleteDialog) {
        AlertDialog(
            onDismissRequest = { showDeleteDialog = false },
            title = { Text(stringResource(R.string.dialog_delete_all_title)) },
            text = { Text(stringResource(R.string.dialog_delete_all_message)) },
            confirmButton = {
                Button(onClick = {
                    showDeleteDialog = false
                    viewModel.onDeleteAllConfirmed()
                }) { Text(stringResource(R.string.action_confirm_delete)) }
            },
            dismissButton = {
                OutlinedButton(onClick = { showDeleteDialog = false }) {
                    Text(stringResource(R.string.action_cancel))
                }
            },
        )
    }

    val pendingImportUri = showImportDialog
    if (pendingImportUri != null) {
        AlertDialog(
            onDismissRequest = { showImportDialog = null },
            title = { Text(stringResource(R.string.dialog_import_confirm_title)) },
            text = { Text(stringResource(R.string.dialog_import_confirm_message)) },
            confirmButton = {
                Button(onClick = {
                    viewModel.onImportSelected(pendingImportUri)
                    showImportDialog = null
                }) { Text(stringResource(R.string.action_confirm_import)) }
            },
            dismissButton = {
                OutlinedButton(onClick = { showImportDialog = null }) {
                    Text(stringResource(R.string.action_cancel))
                }
            },
        )
    }
}

private fun labelResFor(method: GrowingMethod): Int = when (method) {
    GrowingMethod.GREENHOUSE -> R.string.method_greenhouse
    GrowingMethod.OPEN_FIELD -> R.string.method_open_field
    GrowingMethod.HYDROPONIC -> R.string.method_hydroponic
    GrowingMethod.SALINE_SOIL -> R.string.method_saline_soil
}
