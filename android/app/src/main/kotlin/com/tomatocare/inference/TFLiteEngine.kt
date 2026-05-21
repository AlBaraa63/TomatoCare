package com.tomatocare.inference

import android.content.Context
import android.content.res.AssetFileDescriptor
import android.graphics.Bitmap
import com.tomatocare.data.model.DiagnosisResult
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.model.InferenceOutput
import com.tomatocare.data.repository.TreatmentRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.tensorflow.lite.Interpreter
import java.io.FileInputStream
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel
import kotlin.math.max

/**
 * On-device classifier. Loads the .tflite once at construction; all
 * subsequent calls reuse the same Interpreter.
 *
 * Class index order MUST match Track A's training (alphabetical by folder
 * name = TF Keras default class_indices). The [CLASS_NAMES] array below is
 * the single source of truth on the Android side — if Track A ever changes
 * the class order, this list changes too. Treatments are looked up via the
 * stable [classLabel] field in ConditionInfo, not via index, so renaming
 * a display name in treatments.json is safe.
 */
class TFLiteEngine(
    context: Context,
    private val preprocessor: ImagePreprocessor,
    private val treatmentRepository: TreatmentRepository,
    private val numThreads: Int = 4,
) {

    private val interpreter: Interpreter

    init {
        val modelBuffer = loadModelFile(context, MODEL_ASSET)
        val opts = Interpreter.Options().apply {
            setNumThreads(numThreads)
            // No NNAPI / GPU delegate: NNAPI on API 26 is unreliable and
            // float16 CPU comfortably hits the 3 s NFR-02 budget.
        }
        interpreter = Interpreter(modelBuffer, opts)
    }

    /**
     * Run inference on [bitmap], returning the top-3 results sorted by
     * confidence. If the top class is below [confidenceThreshold], the
     * result is flagged via [InferenceOutput.isLowConfidence] and the
     * UI shows the Low Confidence Warning instead of the normal screen.
     */
    suspend fun classify(
        bitmap: Bitmap,
        growingMethod: GrowingMethod,
        confidenceThreshold: Float = 0.60f,
    ): InferenceOutput = withContext(Dispatchers.IO) {
        val input = preprocessor.process(bitmap)
        val output = Array(1) { FloatArray(CLASS_NAMES.size) }
        val t0 = System.currentTimeMillis()
        interpreter.run(input, output)
        val elapsed = System.currentTimeMillis() - t0

        val probs = output[0]

        // Full ranked list first, so we can detect the OOD reject class
        // (Tomato_NotALeaf) before slicing to top-3. If the model's top
        // pick is NotALeaf the image probably isn't a tomato leaf at all
        // — we flag low confidence so the UI shows the warning screen,
        // and we strip NotALeaf out of the diagnosis list either way so
        // users never see "Tomato_NotALeaf" as a treatable condition.
        val rankedAll = probs.mapIndexed { idx, p -> idx to p }
            .sortedByDescending { it.second }
        val isOod = rankedAll.first().first == TomatoClasses.OOD_CLASS_INDEX
        val ranked = rankedAll
            .filter { it.first != TomatoClasses.OOD_CLASS_INDEX }
            .take(3)

        val topProb = ranked.first().second
        val isLowConfidence = isOod || topProb < confidenceThreshold

        val results = ranked.mapIndexed { rank, (idx, prob) ->
            val classLabel = CLASS_NAMES[idx]
            val condition = treatmentRepository.getConditionByClassLabel(classLabel)
            val severity = severityFor(prob, isPrimary = rank == 0,
                                       baseSeverity = condition?.severityDefault)
            val treatments = if (condition != null) {
                treatmentRepository.getTreatments(condition.conditionId, growingMethod)
            } else emptyList()

            DiagnosisResult(
                resultId = rank + 1,
                conditionId = condition?.conditionId ?: classLabel.lowercase(),
                conditionNameEn = condition?.nameEn ?: classLabel,
                conditionNameAr = condition?.nameAr ?: classLabel,
                confidence = prob.toDouble(),
                isPrimary = rank == 0,
                stressType = condition?.stressType
                    ?: com.tomatocare.data.model.StressType.BIOTIC,
                severityLevel = severity,
                treatments = treatments,
            )
        }

        InferenceOutput(
            results = results,
            isLowConfidence = isLowConfidence,
            inferenceTimeMs = max(elapsed, 1L),
        )
    }

    fun close() {
        interpreter.close()
    }

    private fun loadModelFile(context: Context, assetName: String): MappedByteBuffer {
        // Memory-map the .tflite directly out of the APK. This is why
        // build.gradle.kts sets noCompress += "tflite" — compressed assets
        // can't be mmapped and would force a 15 MB heap allocation.
        val afd: AssetFileDescriptor = context.assets.openFd(assetName)
        FileInputStream(afd.fileDescriptor).use { fis ->
            return fis.channel.map(
                FileChannel.MapMode.READ_ONLY,
                afd.startOffset,
                afd.declaredLength,
            )
        }
    }

    /**
     * Severity heuristic: scale the condition's default severity up or down
     * based on how confident the model is. A high-confidence detection of
     * Late Blight stays CRITICAL; a marginal one drops to HIGH so the UI
     * doesn't over-alarm the user.
     */
    private fun severityFor(
        confidence: Float,
        isPrimary: Boolean,
        baseSeverity: com.tomatocare.data.model.SeverityLevel?,
    ): com.tomatocare.data.model.SeverityLevel {
        val base = baseSeverity
            ?: com.tomatocare.data.model.SeverityLevel.MEDIUM
        if (!isPrimary) return com.tomatocare.data.model.SeverityLevel.LOW
        return when {
            confidence >= 0.90f -> base
            confidence >= 0.75f -> bumpDown(base, 1)
            confidence >= 0.60f -> bumpDown(base, 2)
            else -> com.tomatocare.data.model.SeverityLevel.LOW
        }
    }

    private fun bumpDown(
        s: com.tomatocare.data.model.SeverityLevel,
        steps: Int,
    ): com.tomatocare.data.model.SeverityLevel {
        val ordered = com.tomatocare.data.model.SeverityLevel.values()
        val idx = (s.ordinal - steps).coerceAtLeast(0)
        return ordered[idx]
    }

    companion object {
        val MODEL_ASSET get() = TomatoClasses.MODEL_ASSET
        val CLASS_NAMES  get() = TomatoClasses.CLASS_NAMES
    }
}
