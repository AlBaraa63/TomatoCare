package com.tomatocare

import com.tomatocare.data.model.DiagnosisResult
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.model.ScanHistory
import com.tomatocare.data.model.ScanRecord
import com.tomatocare.data.model.SeverityLevel
import com.tomatocare.data.model.StressType
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ScanHistorySerializationTest {

    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
    }

    private fun sampleRecord(id: Int) = ScanRecord(
        scanId = id,
        imagePath = "/data/user/0/com.tomatocare/files/img_$id.jpg",
        timestamp = "2026-05-12T10:00:00Z",
        growingMethod = GrowingMethod.GREENHOUSE,
        modelVersion = "1.0.0",
        results = listOf(
            DiagnosisResult(
                resultId = 1,
                conditionId = "tomato_bacterial_spot",
                conditionNameEn = "Bacterial Spot",
                conditionNameAr = "التبقع البكتيري",
                confidence = 0.956,
                isPrimary = true,
                stressType = StressType.BIOTIC,
                severityLevel = SeverityLevel.HIGH,
            )
        ),
    )

    @Test
    fun roundTrip_preservesAllFields() {
        val original = ScanHistory(listOf(sampleRecord(1), sampleRecord(2)))
        val encoded = json.encodeToString(original)
        val decoded = json.decodeFromString<ScanHistory>(encoded)

        assertEquals(2, decoded.scans.size)
        assertEquals(1, decoded.scans[0].scanId)
        assertEquals(2, decoded.scans[1].scanId)
        assertEquals("Bacterial Spot", decoded.scans[0].results[0].conditionNameEn)
        assertEquals(0.956, decoded.scans[0].results[0].confidence, 0.0001)
        assertEquals(GrowingMethod.GREENHOUSE, decoded.scans[0].growingMethod)
        assertEquals(SeverityLevel.HIGH, decoded.scans[0].results[0].severityLevel)
    }

    @Test
    fun emptyHistory_roundTrips() {
        val original = ScanHistory(emptyList())
        val encoded = json.encodeToString(original)
        val decoded = json.decodeFromString<ScanHistory>(encoded)
        assertTrue(decoded.scans.isEmpty())
    }

    @Test
    fun unknownKeys_areIgnored() {
        val json2 = Json { ignoreUnknownKeys = true }
        val withExtra = """{"scans":[],"unknownField":"value","version":99}"""
        val decoded = json2.decodeFromString<ScanHistory>(withExtra)
        assertTrue(decoded.scans.isEmpty())
    }

    @Test
    fun encodedJson_containsExpectedKeys() {
        val encoded = json.encodeToString(ScanHistory(listOf(sampleRecord(1))))
        assertTrue(encoded.contains("\"scanId\""))
        assertTrue(encoded.contains("\"timestamp\""))
        assertTrue(encoded.contains("\"growingMethod\""))
        assertTrue(encoded.contains("\"results\""))
        assertTrue(encoded.contains("\"confidence\""))
    }
}
