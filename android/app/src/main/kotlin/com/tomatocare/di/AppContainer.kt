package com.tomatocare.di

import android.content.Context
import com.tomatocare.data.repository.TreatmentRepository
import com.tomatocare.data.storage.ScanExporter
import com.tomatocare.data.storage.ScanImporter
import com.tomatocare.data.storage.ScanStorageManager
import com.tomatocare.data.storage.SettingsStore
import com.tomatocare.inference.ImagePreprocessor
import com.tomatocare.inference.TFLiteEngine

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
 */
class AppContainer(context: Context) {
    private val appContext = context.applicationContext

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
}
