package com.tomatocare

import com.tomatocare.ui.format.formatConfidence
import com.tomatocare.ui.format.formatTimestamp
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class FormatTest {

    @Test
    fun formatConfidence_roundsDown() {
        assertEquals("95%", formatConfidence(0.9588))
    }

    @Test
    fun formatConfidence_zero() {
        assertEquals("0%", formatConfidence(0.0))
    }

    @Test
    fun formatConfidence_full() {
        assertEquals("100%", formatConfidence(1.0))
    }

    @Test
    fun formatConfidence_partialPercent() {
        assertEquals("84%", formatConfidence(0.849))
    }

    @Test
    fun formatTimestamp_validIso_doesNotReturnRaw() {
        val iso = "2026-05-12T10:00:00Z"
        val result = formatTimestamp(iso)
        // Should be locale-formatted, not the raw ISO string
        assertFalse("Expected locale format, got raw ISO", result == iso)
        assertTrue("Formatted string must not be blank", result.isNotBlank())
    }

    @Test
    fun formatTimestamp_invalidString_returnsRaw() {
        val bad = "not-a-date"
        assertEquals(bad, formatTimestamp(bad))
    }

    @Test
    fun formatTimestamp_emptyString_returnsRaw() {
        assertEquals("", formatTimestamp(""))
    }
}
