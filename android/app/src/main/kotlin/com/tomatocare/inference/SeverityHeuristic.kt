package com.tomatocare.inference

import com.tomatocare.data.model.SeverityLevel

/**
 * Confidence → severity mapping, extracted from [TFLiteEngine] so it can be
 * unit-tested without loading the TFLite interpreters.
 *
 * A condition's default severity is scaled down as confidence drops, so a
 * marginal detection of a CRITICAL disease doesn't over-alarm the user.
 * Secondary (non-primary) results are always reported as LOW.
 */
object SeverityHeuristic {

    fun severityFor(
        confidence: Float,
        isPrimary: Boolean,
        baseSeverity: SeverityLevel?,
    ): SeverityLevel {
        val base = baseSeverity ?: SeverityLevel.MEDIUM
        if (!isPrimary) return SeverityLevel.LOW
        return when {
            confidence >= 0.90f -> base
            confidence >= 0.75f -> bumpDown(base, 1)
            confidence >= 0.60f -> bumpDown(base, 2)
            else -> SeverityLevel.LOW
        }
    }

    private fun bumpDown(s: SeverityLevel, steps: Int): SeverityLevel {
        val ordered = SeverityLevel.values()
        val idx = (s.ordinal - steps).coerceAtLeast(0)
        return ordered[idx]
    }
}
