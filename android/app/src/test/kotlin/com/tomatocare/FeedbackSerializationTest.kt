package com.tomatocare

import com.tomatocare.data.model.DiagnosisResult
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.model.ScanFeedback
import com.tomatocare.data.model.ScanRecord
import com.tomatocare.data.model.SeverityLevel
import com.tomatocare.data.model.StressType
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * The feedback flywheel adds a nullable `feedback` field to ScanRecord.
 * Verifies it round-trips and — critically — that history files written
 * before the flywheel existed (no "feedback" key) still decode, with
 * feedback defaulting to null. Backward compatibility is the whole point of
 * the default + ignoreUnknownKeys config.
 */
class FeedbackSerializationTest {

    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
    }

    private fun sampleRecord(id: Int) = ScanRecord(
        scanId = id,
        imagePath = "/data/files/img_$id.jpg",
        timestamp = "2026-05-12T10:00:00Z",
        growingMethod = GrowingMethod.GREENHOUSE,
        modelVersion = "2.0.0",
        results = listOf(
            DiagnosisResult(
                conditionId = "early_blight",
                conditionNameEn = "Early Blight",
                conditionNameAr = "اللفحة المبكرة",
                confidence = 0.91,
                isPrimary = true,
                stressType = StressType.BIOTIC,
                severityLevel = SeverityLevel.HIGH,
            )
        ),
    )

    @Test
    fun feedbackDefaultsToNull() {
        assertNull(sampleRecord(1).feedback)
    }

    @Test
    fun feedback_roundTrips() {
        val rec = sampleRecord(1).copy(
            feedback = ScanFeedback(
                wasCorrect = false,
                correctedConditionId = "late_blight",
                timestamp = "2026-05-12T11:00:00Z",
            ),
            inferenceTimeMs = 420L,
        )
        val decoded = json.decodeFromString<ScanRecord>(json.encodeToString(rec))
        assertEquals(false, decoded.feedback?.wasCorrect)
        assertEquals("late_blight", decoded.feedback?.correctedConditionId)
        assertEquals("2026-05-12T11:00:00Z", decoded.feedback?.timestamp)
        assertEquals(420L, decoded.inferenceTimeMs)
    }

    @Test
    fun legacyRecordWithoutFeedbackKey_decodesWithNull() {
        // A history record written before the flywheel feature shipped.
        val legacy = """
            {"scanId":7,"imagePath":"/x.jpg","timestamp":"2026-01-01T00:00:00Z",
             "growingMethod":"OPEN_FIELD","modelVersion":"1.0.0","results":[]}
        """.trimIndent()
        val decoded = json.decodeFromString<ScanRecord>(legacy)
        assertEquals(7, decoded.scanId)
        assertNull(decoded.feedback)
        assertNull(decoded.inferenceTimeMs)
    }
}
