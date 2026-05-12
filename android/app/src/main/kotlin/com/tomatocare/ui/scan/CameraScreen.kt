package com.tomatocare.ui.scan

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PhotoLibrary
import androidx.compose.material3.Button
import androidx.compose.material3.FilledIconButton
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.tomatocare.R
import kotlinx.coroutines.launch

/**
 * Live camera preview + capture button + gallery picker.
 *
 * The composable owns only the camera plumbing. The captured bitmap is
 * handed up via [onBitmapReady] and processed by [ScanViewModel] —
 * keeping inference out of any Composable per the rules.
 */
@Composable
fun CameraScreen(
    onBitmapReady: (Bitmap) -> Unit,
    onShowSnackbar: (String) -> Unit,
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val scope = rememberCoroutineScope()
    val controller = remember { CameraController(context) }

    var hasCameraPermission by remember {
        mutableStateOf(
            context.checkSelfPermission(Manifest.permission.CAMERA)
                == PackageManager.PERMISSION_GRANTED
        )
    }
    val cameraPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted -> hasCameraPermission = granted }

    val galleryLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri ->
        if (uri == null) return@rememberLauncherForActivityResult
        val failure = ImageValidation.validateUri(context, uri)
        if (failure != null) {
            onShowSnackbar(context.getString(failure.reasonResId))
            return@rememberLauncherForActivityResult
        }
        scope.launch {
            try {
                val bmp = ImageValidation.decodeBitmap(context, uri)
                onBitmapReady(bmp)
            } catch (e: Exception) {
                onShowSnackbar(
                    context.getString(R.string.error_image_decode_failed)
                )
            }
        }
    }

    if (!hasCameraPermission) {
        Column(
            modifier = Modifier.fillMaxSize().padding(24.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(stringResource(R.string.camera_permission_rationale))
            Spacer(Modifier.height(16.dp))
            Button(onClick = {
                cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
            }) {
                Text(stringResource(R.string.action_grant_permission))
            }
        }
        return
    }

    Box(modifier = Modifier.fillMaxSize()) {
        AndroidView(
            modifier = Modifier.fillMaxSize(),
            factory = { ctx ->
                PreviewView(ctx).also { pv ->
                    scope.launch {
                        try {
                            controller.bind(pv, lifecycleOwner)
                        } catch (e: Exception) {
                            onShowSnackbar(
                                context.getString(R.string.error_camera_bind_failed)
                            )
                        }
                    }
                }
            },
        )

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .align(Alignment.BottomCenter)
                .padding(bottom = 32.dp, start = 24.dp, end = 24.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            FilledIconButton(onClick = {
                galleryLauncher.launch("image/*")
            }) {
                Icon(
                    imageVector = Icons.Default.PhotoLibrary,
                    contentDescription = stringResource(R.string.action_pick_from_gallery),
                )
            }

            Button(onClick = {
                scope.launch {
                    try {
                        val bmp = controller.captureBitmap()
                        onBitmapReady(bmp)
                    } catch (e: Exception) {
                        onShowSnackbar(
                            context.getString(R.string.error_capture_failed)
                        )
                    }
                }
            }) {
                Text(stringResource(R.string.action_capture))
            }
        }
    }
}
