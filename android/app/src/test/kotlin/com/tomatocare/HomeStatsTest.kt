package com.tomatocare

import com.tomatocare.data.model.DiagnosisResult
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.model.ScanRecord
import com.tomatocare.data.model.SeverityLevel
import com.tomatocare.data.model.StressType
import com.tomatocare.ui.home.HomeStats
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Tests the Home dashboard statistics. Notably guards the health-rate metric,
 * which keys on the canonical conditionId "healthy" — a regression test for a
 * bug where it checked "tomato_healthy" and was permanently 0%.
 */
class HomeStatsTest {

    private fun record(
        id: Int,
        conditionId: String,
        en: String = conditionId,
        ar: String = conditionId,
    ) = ScanRecord(
        scanId = id,
        imagePath = "/data/files/img_$id.jpg",
        timestamp = "2026-05-12T10:00:00Z",
        growingMethod = GrowingMethod.OPEN_FIELD,
        modelVersion = "2.0.0",
        results = listOf(
            DiagnosisResult(
                conditionId = conditionId,
                conditionNameEn = en,
                conditionNameAr = ar,
                confidence = 0.9,
                isPrimary = true,
                stressType = StressType.BIOTIC,
                severityLevel = SeverityLevel.MEDIUM,
            )
        ),
    )

    @Test
    fun emptyScans_areAllZero() {
        val r = HomeStats.compute(emptyList(), isArabic = false)
        assertEquals(0, r.totalScans)
        assertEquals(0, r.healthRate)
        assertEquals(0, r.distinctConditions)
        assertTrue(r.topConditions.isEmpty())
    }

    @Test
    fun healthRate_countsHealthyConditionId() {
        val scans = listOf(
            record(1, "healthy"),
            record(2, "healthy"),
            record(3, "early_blight"),
            record(4, "late_blight"),
        )
        val r = HomeStats.compute(scans, isArabic = false)
        assertEquals(4, r.totalScans)
        assertEquals(50, r.healthRate)            // 2 healthy of 4
        assertEquals(3, r.distinctConditions)
    }

    @Test
    fun healthRate_isZeroWithNoHealthyScans() {
        val scans = listOf(record(1, "early_blight"), record(2, "late_blight"))
        assertEquals(0, HomeStats.compute(scans, isArabic = false).healthRate)
    }

    @Test
    fun topConditions_sortedByFrequency_andLocalised() {
        val scans = listOf(
            record(1, "early_blight", en = "Early Blight", ar = "اللفحة المبكرة"),
            record(2, "early_blight", en = "Early Blight", ar = "اللفحة المبكرة"),
            record(3, "late_blight", en = "Late Blight", ar = "اللفحة المتأخرة"),
        )
        val en = HomeStats.compute(scans, isArabic = false)
        assertEquals("Early Blight" to 2, en.topConditions.first())

        val ar = HomeStats.compute(scans, isArabic = true)
        assertEquals("اللفحة المبكرة", ar.topConditions.first().first)
    }

    @Test
    fun recordsWithoutPrimary_countInTotalButNotInValidStats() {
        val noPrimary = ScanRecord(
            scanId = 99,
            imagePath = "/x.jpg",
            timestamp = "2026-05-12T10:00:00Z",
            growingMethod = GrowingMethod.OPEN_FIELD,
            modelVersion = "2.0.0",
            results = emptyList(),
        )
        val r = HomeStats.compute(listOf(record(1, "healthy"), noPrimary), isArabic = false)
        assertEquals(2, r.totalScans)
        assertEquals(100, r.healthRate)           // 1 healthy of 1 valid scan
        assertEquals(1, r.distinctConditions)
    }
}
