package com.tomatocare.ui.util

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.collection.LruCache
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

/**
 * Downsampled-JPEG loader for the history list. BitmapFactory + inSampleSize
 * with an in-memory LruCache.
 *
 * Deliberately no Coil/Glide dependency: Coil pulls OkHttp into the classpath
 * and weakens the "no network" NFR-08 argument we make at defence. BitmapFactory
 * is native to Android, costs zero APK bytes, and is plenty fast for 40 dp thumbs.
 */
object ThumbnailLoader {

    // 64 entries comfortably fits under a few MB of decoded thumbs.
    private val cache = LruCache<String, Bitmap>(64)

    suspend fun load(path: String, sizePx: Int): Bitmap? =
        withContext(Dispatchers.IO) {
            val key = "$path@$sizePx"
            cache.get(key)?.let { return@withContext it }

            val file = File(path)
            if (!file.exists()) return@withContext null

            // First decode pass: bounds only, no allocation. Cheap.
            val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
            BitmapFactory.decodeFile(path, bounds)
            if (bounds.outWidth <= 0 || bounds.outHeight <= 0) {
                return@withContext null
            }

            val options = BitmapFactory.Options().apply {
                inSampleSize = calculateSampleSize(
                    bounds.outWidth, bounds.outHeight, sizePx,
                )
                inPreferredConfig = Bitmap.Config.ARGB_8888
            }
            val bitmap = BitmapFactory.decodeFile(path, options)
                ?: return@withContext null
            cache.put(key, bitmap)
            bitmap
        }

    /**
     * Largest power-of-two inSampleSize that keeps the short side >= target.
     * BitmapFactory only honours power-of-two values, so requesting a
     * non-power-of-two yields the next lower power anyway — compute it
     * explicitly to avoid surprise oversizing.
     */
    private fun calculateSampleSize(width: Int, height: Int, target: Int): Int {
        if (target <= 0) return 1
        var sample = 1
        val shortSide = minOf(width, height)
        while (shortSide / (sample * 2) >= target) sample *= 2
        return sample
    }
}
