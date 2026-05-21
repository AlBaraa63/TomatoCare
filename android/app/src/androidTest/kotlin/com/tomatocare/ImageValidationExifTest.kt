package com.tomatocare

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.net.Uri
import androidx.exifinterface.media.ExifInterface
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.tomatocare.ui.scan.ImageValidation
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.io.FileOutputStream

/**
 * Guards the gallery decode path against the most common real-world failure:
 * a portrait-EXIF JPG from Google Photos arrives sideways, the model sees
 * a 90-rotated leaf, and accuracy tanks for that user.
 *
 * On API >= 28 the test verifies that the ImageDecoder path applies EXIF
 * automatically. On API 26-27 (legacy path) it verifies our explicit
 * ImagePreprocessor.rotateByExif call.
 */
@RunWith(AndroidJUnit4::class)
class ImageValidationExifTest {

    private lateinit var context: Context
    private lateinit var jpegFile: File

    @Before
    fun setUp() {
        context = InstrumentationRegistry.getInstrumentation().targetContext

        // 100 wide x 50 tall: red top-left quadrant, blue elsewhere.
        // Asymmetric size is deliberate — a square would mask rotation bugs.
        val source = Bitmap.createBitmap(100, 50, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(source)
        canvas.drawColor(Color.BLUE)
        canvas.drawRect(0f, 0f, 50f, 25f, Paint().apply { color = Color.RED })

        jpegFile = File(context.cacheDir, "exif_${System.currentTimeMillis()}.jpg")
        FileOutputStream(jpegFile).use { os ->
            source.compress(Bitmap.CompressFormat.JPEG, 95, os)
        }
        source.recycle()

        // Tag the file with "rotate 90 CW" — the on-disk pixels are still
        // landscape; a correct decoder must rotate them on the way out.
        val exif = ExifInterface(jpegFile.absolutePath)
        exif.setAttribute(
            ExifInterface.TAG_ORIENTATION,
            ExifInterface.ORIENTATION_ROTATE_90.toString(),
        )
        exif.saveAttributes()
    }

    @After
    fun tearDown() {
        if (this::jpegFile.isInitialized) jpegFile.delete()
    }

    @Test
    fun decodeBitmap_appliesExifRotation_dimensionsSwap() {
        val decoded = ImageValidation.decodeBitmap(context, Uri.fromFile(jpegFile))
        // Source was 100x50; after CW-90 the bitmap should be 50x100.
        assertEquals("Width should be source height after CW-90 rotation",
            50, decoded.width)
        assertEquals("Height should be source width after CW-90 rotation",
            100, decoded.height)
    }

    @Test
    fun decodeBitmap_appliesExifRotation_redQuadrantEndsTopRight() {
        val decoded = ImageValidation.decodeBitmap(context, Uri.fromFile(jpegFile))
        // Red was in the top-left quadrant of the source. After CW-90 it
        // ends up in the top-right quadrant of the rotated bitmap.
        val sampleX = decoded.width - 5
        val sampleY = 5
        val pixel = decoded.getPixel(sampleX, sampleY)
        val isReddish = Color.red(pixel) > 200 &&
            Color.green(pixel) < 100 &&
            Color.blue(pixel) < 100
        assertTrue(
            "Expected red near (${sampleX},${sampleY}) after CW-90 rotation, " +
                "got #${Integer.toHexString(pixel)}",
            isReddish,
        )
    }
}
