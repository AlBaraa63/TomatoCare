package com.tomatocare.inference

import android.content.Context
import android.content.res.AssetFileDescriptor
import android.graphics.Bitmap
import com.tomatocare.data.model.DiagnosisResult
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.model.InferenceOutput
import com.tomatocare.data.model.RejectReason
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.tensorflow.lite.Interpreter
import java.io.FileInputStream
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel
import kotlin.math.max

/**
 * On-device THREE-STAGE cascade (Capstone 2). Loads three .tflite models
 * once at construction; every scan runs them in sequence:
 *
 *   Stage 1  leaf gate    -> reject NOT_A_LEAF   if the image isn't a leaf
 *   Stage 2  tomato gate  -> reject NOT_A_TOMATO if it's a non-tomato leaf
 *   Stage 3  disease      -> diagnose 1 of 11 conditions (10 diseases + healthy)
 *
 * This replaces the old single-model + OOD-class design. The two binary
 * gates are what make the app reject "not a tomato leaf" photos instead of
 * confidently mislabelling them (the v1 failure mode). Each stage uses the
 * SAME preprocessed input buffer (all three models take float32[1,224,224,3]),
 * rewound between runs so we preprocess the bitmap only once.
 *
 * Stage-3 class indices map 1:1 to ConditionInfo.conditionId in
 * treatments.json, so conditions are looked up by that key directly.
 */
class TFLiteEngine(
    context: Context,
    private val preprocessor: ImagePreprocessor,
    private val treatmentRepository: com.tomatocare.data.repository.TreatmentRepository,
    private val numThreads: Int = 4,
) {

    private val leafGate: Interpreter
    private val tomatoGate: Interpreter
    private val diseaseNet: Interpreter

    init {
        val opts = Interpreter.Options().apply {
            setNumThreads(numThreads)
            // No NNAPI / GPU delegate: NNAPI on API 26 is unreliable and
            // float16 CPU comfortably hits the 3 s NFR-02 budget even with
            // three models — the two gates are MobileNetV3-Small (~1.8 MB).
        }
        leafGate = Interpreter(loadModelFile(context, TomatoClasses.LEAF_MODEL_ASSET), opts)
        tomatoGate = Interpreter(loadModelFile(context, TomatoClasses.TOMATO_MODEL_ASSET), opts)
        diseaseNet = Interpreter(loadModelFile(context, TomatoClasses.DISEASE_MODEL_ASSET), opts)
    }

    /**
     * Run the cascade on [bitmap].
     *
     * If a gate rejects, returns immediately with the matching
     * [RejectReason] and an empty result list. Otherwise returns the top-3
     * diagnoses sorted by confidence; if the top class is below
     * [confidenceThreshold] the result is flagged via
     * [InferenceOutput.isLowConfidence] so the UI shows the warning.
     */
    suspend fun classify(
        bitmap: Bitmap,
        growingMethod: GrowingMethod,
        confidenceThreshold: Float = 0.60f,
    ): InferenceOutput = withContext(Dispatchers.IO) {
        val input = preprocessor.process(bitmap)
        val t0 = System.currentTimeMillis()

        // ---- Stage 1: leaf gate ----
        val leafProbs = runStage(leafGate, input, TomatoClasses.LEAF_CLASS_NAMES.size)
        if (leafProbs.argmax() != TomatoClasses.LEAF_INDEX) {
            return@withContext InferenceOutput(
                results = emptyList(),
                isLowConfidence = false,
                inferenceTimeMs = max(System.currentTimeMillis() - t0, 1L),
                rejectReason = RejectReason.NOT_A_LEAF,
            )
        }

        // ---- Stage 2: tomato gate ----
        val tomatoProbs = runStage(tomatoGate, input, TomatoClasses.TOMATO_CLASS_NAMES.size)
        if (tomatoProbs.argmax() != TomatoClasses.TOMATO_INDEX) {
            return@withContext InferenceOutput(
                results = emptyList(),
                isLowConfidence = false,
                inferenceTimeMs = max(System.currentTimeMillis() - t0, 1L),
                rejectReason = RejectReason.NOT_A_TOMATO,
            )
        }

        // ---- Stage 3: disease classifier ----
        val diseaseProbs = runStage(diseaseNet, input, TomatoClasses.DISEASE_CLASS_NAMES.size)
        val elapsed = System.currentTimeMillis() - t0

        val ranked = diseaseProbs.mapIndexed { idx, p -> idx to p }
            .sortedByDescending { it.second }
            .take(3)

        val topProb = ranked.first().second
        val isLowConfidence = topProb < confidenceThreshold

        val results = ranked.mapIndexed { rank, (idx, prob) ->
            val conditionId = TomatoClasses.DISEASE_CLASS_NAMES[idx]
            val condition = treatmentRepository.getCondition(conditionId)
            val severity = severityFor(prob, isPrimary = rank == 0,
                                       baseSeverity = condition?.severityDefault)
            val treatments = if (condition != null) {
                treatmentRepository.getTreatments(condition.conditionId, growingMethod)
            } else emptyList()

            DiagnosisResult(
                resultId = rank + 1,
                conditionId = condition?.conditionId ?: conditionId,
                conditionNameEn = condition?.nameEn ?: conditionId,
                conditionNameAr = condition?.nameAr ?: conditionId,
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
            rejectReason = RejectReason.NONE,
        )
    }

    fun close() {
        leafGate.close()
        tomatoGate.close()
        diseaseNet.close()
    }

    /**
     * Runs one stage. The input buffer is shared across all three models, so
     * rewind it first — TFLite advances the buffer position as it reads.
     */
    private fun runStage(
        interpreter: Interpreter,
        input: java.nio.ByteBuffer,
        numClasses: Int,
    ): FloatArray {
        input.rewind()
        val output = Array(1) { FloatArray(numClasses) }
        interpreter.run(input, output)
        return output[0]
    }

    private fun FloatArray.argmax(): Int {
        var best = 0
        for (i in 1 until size) if (this[i] > this[best]) best = i
        return best
    }

    private fun loadModelFile(context: Context, assetName: String): MappedByteBuffer {
        // Memory-map the .tflite directly out of the APK. This is why
        // build.gradle.kts sets noCompress += "tflite" — compressed assets
        // can't be mmapped and would force a heap allocation per model.
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
}
