package com.tomatocare

import com.tomatocare.data.model.DiagnosisResult
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.model.Language
import com.tomatocare.data.model.ScanRecord
import com.tomatocare.data.model.SeverityLevel
import com.tomatocare.data.model.StressType
import com.tomatocare.ui.history.HistoryUiState
import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * Tests the History search + severity filtering (the pure `HistoryUiState.records`
 * derivation) without a device. Covers query matching in both languages, the
 * severity filter, their combination, and case-insensitive/trimmed queries.
 */
class HistoryFilterTest {

    private fun rec(id: Int, en: String, ar: String, sev: SeverityLevel) = ScanRecord(
        scanId = id,
        imagePath = "/img_$id.jpg",
        timestamp = "2026-05-29T10:00:00Z",
        growingMethod = GrowingMethod.OPEN_FIELD,
        modelVersion = "2.0.0",
        results = listOf(
            DiagnosisResult(
                conditionId = en,
                conditionNameEn = en,
                conditionNameAr = ar,
                confidence = 0.9,
                isPrimary = true,
                stressType = StressType.BIOTIC,
                severityLevel = sev,
            )
        ),
    )

    private val records = listOf(
        rec(1, "Early Blight", "اللفحة المبكرة", SeverityLevel.HIGH),
        rec(2, "Late Blight", "اللفحة المتأخرة", SeverityLevel.CRITICAL),
        rec(3, "Healthy", "سليمة", SeverityLevel.LOW),
    )

    @Test
    fun noFilters_returnsAll() {
        assertEquals(3, HistoryUiState(allRecords = records).records.size)
    }

    @Test
    fun query_filtersByEnglishName() {
        val s = HistoryUiState(allRecords = records, query = "blight")
        assertEquals(2, s.records.size)
    }

    @Test
    fun query_filtersByArabicName_whenArabic() {
        val s = HistoryUiState(allRecords = records, query = "سليمة", language = Language.ARABIC)
        assertEquals(1, s.records.size)
        assertEquals(3, s.records.first().scanId)
    }

    @Test
    fun severityFilter_narrowsResults() {
        val s = HistoryUiState(allRecords = records, severityFilter = SeverityLevel.CRITICAL)
        assertEquals(1, s.records.size)
        assertEquals(2, s.records.first().scanId)
    }

    @Test
    fun queryAndSeverity_combine() {
        val s = HistoryUiState(
            allRecords = records,
            query = "blight",
            severityFilter = SeverityLevel.HIGH,
        )
        assertEquals(1, s.records.size)
        assertEquals(1, s.records.first().scanId)
    }

    @Test
    fun query_isCaseInsensitiveAndTrimmed() {
        val s = HistoryUiState(allRecords = records, query = "  EARLY  ")
        assertEquals(1, s.records.size)
        assertEquals(1, s.records.first().scanId)
    }
}
