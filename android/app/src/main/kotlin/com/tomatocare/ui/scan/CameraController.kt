package com.tomatocare.ui.scan

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageDecoder
import android.net.Uri
import android.os.Build
import android.provider.MediaStore
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import androidx.lifecycle.LifecycleOwner
import com.google.common.util.concurrent.ListenableFuture
import com.tomatocare.inference.ImagePreprocessor
import kotlinx.coroutines.suspendCancellableCoroutine
import java.io.ByteArrayOutputStream
import java.io.File
import java.util.concurrent.Executor
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

/**
 * Thin wrapper around CameraX that the ScanScreen uses to bind preview +
 * image capture to a lifecycle. Kept separate from the composable so the
 * camera plumbing can be unit-tested with a fake [ImageCapture].
 */
class CameraController(
    private val context: Context,
    private val executor: Executor =
        ContextCompat.getMainExecutor(context),
) {

    private var imageCapture: ImageCapture? = null

    suspend fun bind(
        previewView: PreviewView,
        lifecycleOwner: LifecycleOwner,
    ): Boolean = suspendCancellableCoroutine { cont ->
        val future: ListenableFuture<ProcessCameraProvider> =
            ProcessCameraProvider.getInstance(context)
        future.addListener({
            try {
                val provider = future.get()
                val preview = Preview.Builder().build().also {
                    it.setSurfaceProvider(previewView.surfaceProvider)
                }
                val capture = ImageCapture.Builder()
                    .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                    .build()
                imageCapture = capture
                provider.unbindAll()
                provider.bindToLifecycle(
                    lifecycleOwner,
                    androidx.camera.core.CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                    capture,
                )
                cont.resume(true)
            } catch (e: Exception) {
                cont.resumeWithException(e)
            }
        }, executor)
    }

    suspend fun captureBitmap(): Bitmap = suspendCancellableCoroutine { cont ->
        val capture = imageCapture ?: run {
            cont.resumeWithException(IllegalStateException("Camera not bound."))
            return@suspendCancellableCoroutine
        }
        capture.takePicture(executor, object : ImageCapture.OnImageCapturedCallback() {
            override fun onCaptureSuccess(image: androidx.camera.core.ImageProxy) {
                try {
                    val bitmap = imageProxyToBitmap(image)
                    image.close()
                    cont.resume(bitmap)
                } catch (e: Exception) {
                    image.close()
                    cont.resumeWithException(e)
                }
            }
            override fun onError(exception: ImageCaptureException) {
                cont.resumeWithException(exception)
            }
        })
    }

    /** Convert a JPEG ImageProxy to a portrait-oriented Bitmap. */
    private fun imageProxyToBitmap(image: androidx.camera.core.ImageProxy): Bitmap {
        val planes = image.planes
        val buffer = planes[0].buffer
        val bytes = ByteArray(buffer.remaining())
        buffer.get(bytes)
        val raw = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
        val rotation = image.imageInfo.rotationDegrees.toFloat()
        if (rotation == 0f) return raw
        val matrix = android.graphics.Matrix().apply { postRotate(rotation) }
        return Bitmap.createBitmap(raw, 0, 0, raw.width, raw.height, matrix, true)
    }
}

/** Image validation — file size and decodable format checks. */
object ImageValidation {
    private const val MAX_BYTES = 10 * 1024 * 1024  // 10 MB
    private val ALLOWED_MIMES = setOf("image/jpeg", "image/png", "image/jpg")

    data class ValidationFailure(val reasonResId: Int)

    fun validateUri(context: Context, uri: Uri): ValidationFailure? {
        val resolver = context.contentResolver
        val mime = resolver.getType(uri)?.lowercase()
        if (mime != null && mime !in ALLOWED_MIMES) {
            return ValidationFailure(
                com.tomatocare.R.string.error_unsupported_image_format
            )
        }
        val size = resolver.openFileDescriptor(uri, "r")?.use {
            it.statSize
        } ?: 0L
        if (size > MAX_BYTES) {
            return ValidationFailure(
                com.tomatocare.R.string.error_image_too_large
            )
        }
        return null
    }

    fun decodeBitmap(context: Context, uri: Uri): Bitmap {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            // ImageDecoder applies EXIF orientation automatically since API 28,
            // so the bitmap is already upright when it comes back.
            val source = ImageDecoder.createSource(context.contentResolver, uri)
            ImageDecoder.decodeBitmap(source) { decoder, _, _ ->
                decoder.allocator = ImageDecoder.ALLOCATOR_SOFTWARE
                decoder.isMutableRequired = true
            }
        } else {
            // Legacy path: getBitmap does NOT honour EXIF orientation, so a
            // portrait-EXIF JPG from Photos arrives sideways and tanks the
            // model. Open a second stream for ExifInterface (the first was
            // consumed by the decoder) and rotate explicitly.
            @Suppress("DEPRECATION")
            val raw = MediaStore.Images.Media.getBitmap(context.contentResolver, uri)
            context.contentResolver.openInputStream(uri)?.use { exifStream ->
                ImagePreprocessor.rotateByExif(raw, exifStream)
            } ?: raw
        }
    }
}

/** Save a captured bitmap to filesDir/scans/ — returns the absolute path. */
object ScanImageSaver {
    fun save(context: Context, bitmap: Bitmap): String {
        val dir = File(context.filesDir, "scans").apply { mkdirs() }
        val file = File(dir, "scan_${System.currentTimeMillis()}.jpg")
        ByteArrayOutputStream().use { baos ->
            bitmap.compress(Bitmap.CompressFormat.JPEG, 88, baos)
            file.writeBytes(baos.toByteArray())
        }
        return file.absolutePath
    }
}
