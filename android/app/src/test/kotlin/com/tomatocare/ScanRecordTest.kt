package com.tomatocare

import com.tomatocare.data.model.DiagnosisResult
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.model.ScanRecord
import com.tomatocare.data.model.SeverityLevel
import com.tomatocare.data.model.StressType
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class ScanRecordTest {

    private fun makeResult(id: Int, isPrimary: Boolean, confidence: Double = 0.9) =
        DiagnosisResult(
            resultId = id,
            conditionId = "tomato_late_blight",
            conditionNameEn = "Late Blight",
            conditionNameAr = "اللفحة المتأخرة",
            confidence = confidence,
            isPrimary = isPrimary,
            stressType = StressType.BIOTIC,
            severityLevel = SeverityLevel.HIGH,
        )

    private fun makeRecord(results: List<DiagnosisResult>) = ScanRecord(
        scanId = 1,
        imagePath = "/data/user/0/com.tomatocare/files/img_1.jpg",
        timestamp = "2026-05-12T10:00:00Z",
        growingMethod = GrowingMethod.OPEN_FIELD,
        modelVersion = "1.0.0",
        results = results,
    )

    @Test
    fun primary_returnsPrimaryResult() {
        val primary = makeResult(1, isPrimary = true, confidence = 0.95)
        val alt = makeResult(2, isPrimary = false, confidence = 0.03)
        val record = makeRecord(listOf(primary, alt))
        assertEquals(primary, record.primary)
    }

    @Test
    fun primary_fallsBackToFirst_whenNoneMarkedPrimary() {
        val first = makeResult(1, isPrimary = false, confidence = 0.7)
        val second = makeResult(2, isPrimary = false, confidence = 0.2)
        val record = makeRecord(listOf(first, second))
        assertEquals(first, record.primary)
    }

    @Test
    fun primary_isNull_whenResultsEmpty() {
        val record = makeRecord(emptyList())
        assertNull(record.primary)
    }

    @Test
    fun primary_singleResult_isAlwaysPrimary() {
        val only = makeResult(1, isPrimary = false)
        val record = makeRecord(listOf(only))
        assertNotNull(record.primary)
        assertEquals(only, record.primary)
    }
}
