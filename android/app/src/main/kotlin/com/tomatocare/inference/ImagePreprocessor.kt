package com.tomatocare.inference

import android.graphics.Bitmap
import androidx.exifinterface.media.ExifInterface
import java.io.InputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Centre-crops a camera/gallery bitmap to its largest square, resizes to
 * 224x224, normalises pixels to [0,1], and packs them into a direct float32
 * ByteBuffer suitable for TFLite.
 *
 * CENTRE-CROP, not squash: training uses crop_to_aspect_ratio=True (see
 * ml/tree/train.py and predict.py), so the on-device pipeline MUST match
 * byte-for-byte per Contract 5.1. The previous build used
 * Bitmap.createScaledBitmap which stretches non-square photos and distorts
 * leaf shape — a train/serve mismatch that hurt real-world accuracy.
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
        val square = centerCropSquare(bitmap)
        val resized = if (square.width != imgSize || square.height != imgSize) {
            Bitmap.createScaledBitmap(square, imgSize, imgSize, true)
        } else {
            square
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
        // Recycle only intermediates we created — never the caller's bitmap.
        if (resized !== square && resized !== bitmap) resized.recycle()
        if (square !== bitmap) square.recycle()
        return buf
    }

    /**
     * Crops [bitmap] to the largest centred square. Equivalent to
     * tf.image.resize_with_crop_or_pad to min(h,w) in the training pipeline
     * and the PIL centre-crop in predict.py. Returns the original bitmap
     * untouched when it is already square.
     */
    private fun centerCropSquare(bitmap: Bitmap): Bitmap {
        val w = bitmap.width
        val h = bitmap.height
        if (w == h) return bitmap
        val side = minOf(w, h)
        val left = (w - side) / 2
        val top = (h - side) / 2
        return Bitmap.createBitmap(bitmap, left, top, side, side)
    }

    companion object {
        /**
         * Reapply EXIF rotation if present. CameraX preview frames are usually
         * correct already, but gallery imports from other apps frequently carry
         * portrait EXIF tags on landscape pixel data — failing to rotate makes
         * the leaf appear sideways to the model and tanks accuracy.
         *
         * Static so `ImageValidation.decodeBitmap` can reach it without
         * instantiating a preprocessor just to read EXIF.
         *
         * On API >= 28 the framework's `ImageDecoder` already applies EXIF
         * orientation — callers on that path MUST NOT call this, or the
         * bitmap will be rotated twice.
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
}
