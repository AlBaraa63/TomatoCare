package com.tomatocare

import com.tomatocare.data.model.SeverityLevel
import com.tomatocare.inference.SeverityHeuristic
import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * Verifies the confidence → severity mapping used by [com.tomatocare.inference.TFLiteEngine].
 * Boundaries: ≥0.90 keeps base, ≥0.75 drops one level, ≥0.60 drops two, else LOW.
 */
class SeverityHeuristicTest {

    @Test
    fun highConfidence_keepsBaseSeverity() {
        assertEquals(SeverityLevel.CRITICAL,
            SeverityHeuristic.severityFor(0.95f, isPrimary = true, baseSeverity = SeverityLevel.CRITICAL))
        assertEquals(SeverityLevel.HIGH,
            SeverityHeuristic.severityFor(0.90f, isPrimary = true, baseSeverity = SeverityLevel.HIGH))
    }

    @Test
    fun mediumConfidence_dropsOneLevel() {
        assertEquals(SeverityLevel.HIGH,
            SeverityHeuristic.severityFor(0.80f, isPrimary = true, baseSeverity = SeverityLevel.CRITICAL))
        assertEquals(SeverityLevel.LOW,
            SeverityHeuristic.severityFor(0.75f, isPrimary = true, baseSeverity = SeverityLevel.MEDIUM))
    }

    @Test
    fun lowerConfidence_dropsTwoLevels() {
        assertEquals(SeverityLevel.MEDIUM,
            SeverityHeuristic.severityFor(0.65f, isPrimary = true, baseSeverity = SeverityLevel.CRITICAL))
        assertEquals(SeverityLevel.LOW,
            SeverityHeuristic.severityFor(0.60f, isPrimary = true, baseSeverity = SeverityLevel.MEDIUM))
    }

    @Test
    fun belowThreshold_isAlwaysLow() {
        assertEquals(SeverityLevel.LOW,
            SeverityHeuristic.severityFor(0.59f, isPrimary = true, baseSeverity = SeverityLevel.CRITICAL))
    }

    @Test
    fun nonPrimaryResult_isAlwaysLow() {
        assertEquals(SeverityLevel.LOW,
            SeverityHeuristic.severityFor(0.99f, isPrimary = false, baseSeverity = SeverityLevel.CRITICAL))
    }

    @Test
    fun nullBaseSeverity_defaultsToMedium() {
        assertEquals(SeverityLevel.MEDIUM,
            SeverityHeuristic.severityFor(0.95f, isPrimary = true, baseSeverity = null))
    }

    @Test
    fun bumpDown_clampsAtLow() {
        assertEquals(SeverityLevel.LOW,
            SeverityHeuristic.severityFor(0.65f, isPrimary = true, baseSeverity = SeverityLevel.LOW))
    }
}
