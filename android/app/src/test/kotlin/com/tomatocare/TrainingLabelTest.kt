package com.tomatocare

import com.tomatocare.data.storage.TrainingDataExporter
import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * The feedback-flywheel export labels each image with its TRUE class. Verifies
 * label resolution: confirmed prediction when correct, user correction when
 * wrong, and a safe fallback when neither id is usable.
 */
class TrainingLabelTest {

    @Test
    fun correctDiagnosis_usesModelPrediction() {
        assertEquals(
            "early_blight",
            TrainingDataExporter.resolveLabel(
                wasCorrect = true,
                predictedConditionId = "early_blight",
                correctedConditionId = null,
            )
        )
    }

    @Test
    fun incorrectDiagnosis_usesUserCorrection() {
        assertEquals(
            "late_blight",
            TrainingDataExporter.resolveLabel(
                wasCorrect = false,
                predictedConditionId = "early_blight",
                correctedConditionId = "late_blight",
            )
        )
    }

    @Test
    fun missingPrediction_fallsBackToUnknown() {
        assertEquals(
            TrainingDataExporter.UNKNOWN_LABEL,
            TrainingDataExporter.resolveLabel(true, predictedConditionId = null, correctedConditionId = null)
        )
    }

    @Test
    fun blankCorrection_fallsBackToUnknown() {
        assertEquals(
            TrainingDataExporter.UNKNOWN_LABEL,
            TrainingDataExporter.resolveLabel(false, predictedConditionId = "early_blight", correctedConditionId = "   ")
        )
    }
}
