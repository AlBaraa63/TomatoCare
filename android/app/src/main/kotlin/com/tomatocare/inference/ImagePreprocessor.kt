package com.tomatocare.inference

import android.graphics.Bitmap
import androidx.exifinterface.media.ExifInterface
import java.io.InputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Resizes a camera/gallery bitmap to 224x224, normalises pixels to [0,1],
 * and packs them into a direct float32 ByteBuffer suitable for TFLite.
 *
 * Direct ByteBuffer is mandatory — heap-allocated buffers force a copy
 * across the JNI boundary every inference call, costing ~10-20 ms per
 * scan on mid-range Snapdragon hardware.
 */
class ImagePreprocessor(
    private val imgSize: Int = 224,
) {

    /** Allocates a fresh buffer per call so it's safe to use from coroutines. */
    fun process(bitmap: Bitmap): ByteBuffer {
        val resized = if (bitmap.width != imgSize || bitmap.height != imgSize) {
            Bitmap.createScaledBitmap(bitmap, imgSize, imgSize, true)
        } else {
            bitmap
        }

        // float32 = 4 bytes, 3 channels (RGB), 224*224 pixels.
        val buf = ByteBuffer.allocateDirect(4 * imgSize * imgSize * 3)
        buf.order(ByteOrder.nativeOrder())

        val pixels = IntArray(imgSize * imgSize)
        resized.getPixels(pixels, 0, imgSize, 0, 0, imgSize, imgSize)
        for (p in pixels) {
            val r = ((p shr 16) and 0xFF) / 255.0f
            val g = ((p shr 8) and 0xFF) / 255.0f
            val b = (p and 0xFF) / 255.0f
            buf.putFloat(r)
            buf.putFloat(g)
            buf.putFloat(b)
        }
        buf.rewind()
        if (resized !== bitmap) resized.recycle()
        return buf
    }

    /**
     * Reapply EXIF rotation if present. CameraX preview frames are usually
     * correct already, but gallery imports from other apps frequently carry
     * portrait EXIF tags on landscape pixel data — failing to rotate makes
     * the leaf appear sideways to the model and tanks accuracy.
     */
    fun rotateByExif(bitmap: Bitmap, exifInput: InputStream): Bitmap {
        val exif = ExifInterface(exifInput)
        val orientation = exif.getAttributeInt(
            ExifInterface.TAG_ORIENTATION,
            ExifInterface.ORIENTATION_NORMAL,
        )
        val matrix = android.graphics.Matrix()
        when (orientation) {
            ExifInterface.ORIENTATION_ROTATE_90 -> matrix.postRotate(90f)
            ExifInterface.ORIENTATION_ROTATE_180 -> matrix.postRotate(180f)
            ExifInterface.ORIENTATION_ROTATE_270 -> matrix.postRotate(270f)
            else -> return bitmap
        }
        return Bitmap.createBitmap(
            bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true,
        )
    }
}
