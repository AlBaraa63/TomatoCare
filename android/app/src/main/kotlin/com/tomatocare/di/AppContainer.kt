package com.tomatocare.di

import android.content.Context
import android.graphics.Bitmap
import android.util.Log
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.repository.TreatmentRepository
import com.tomatocare.data.storage.ScanExporter
import com.tomatocare.data.storage.ScanImporter
import com.tomatocare.data.storage.ScanStorageManager
import com.tomatocare.data.storage.SettingsStore
import com.tomatocare.inference.ImagePreprocessor
import com.tomatocare.inference.TFLiteEngine
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/**
 * Manual DI graph. One instance per process, created in
 * [com.tomatocare.TomatoCareApp.onCreate].
 *
 * Lifecycle contracts:
 *  - [tfliteEngine] loads the .tflite model exactly once at app start.
 *    Per-classification reloads would add ~200 ms to every scan and
 *    blow the 3 s NFR-02 budget.
 *  - [treatmentRepository] parses treatments.json exactly once and
 *    caches it in an immutable in-memory map.
 *  - A background warm-up runs one inference on a blank bitmap so the
 *    first user-visible scan does not pay JIT + native-load latency.
 */
class AppContainer(context: Context) {
    private val appContext = context.applicationContext

    // Owned by the container so warm-up never escapes the app process.
    // SupervisorJob: a failed warm-up must NOT cancel anything else
    // the container might launch later.
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    val settingsStore: SettingsStore = SettingsStore(appContext)
    val scanStorageManager: ScanStorageManager = ScanStorageManager(appContext)
    val scanExporter: ScanExporter = ScanExporter(appContext, scanStorageManager)
    val scanImporter: ScanImporter = ScanImporter(appContext, scanStorageManager)

    val treatmentRepository: TreatmentRepository = TreatmentRepository(appContext)
    val imagePreprocessor: ImagePreprocessor = ImagePreprocessor()
    val tfliteEngine: TFLiteEngine = TFLiteEngine(
        context = appContext,
        preprocessor = imagePreprocessor,
        treatmentRepository = treatmentRepository,
    )

    init {
        scope.launch {
            try {
                val t0 = System.currentTimeMillis()
                val blank = Bitmap.createBitmap(224, 224, Bitmap.Config.ARGB_8888)
                tfliteEngine.classify(
                    bitmap = blank,
                    growingMethod = GrowingMethod.GREENHOUSE,
                )
                blank.recycle()
                Log.d(TAG, "TFLite warm-up took ${System.currentTimeMillis() - t0}ms")
            } catch (t: Throwable) {
                // Warm-up failure must not crash the app — the first real
                // scan will pay the cold-start cost, but the app still works.
                Log.w(TAG, "TFLite warm-up failed", t)
            }
        }
    }

    companion object {
        private const val TAG = "TomatoCare"
    }
}
