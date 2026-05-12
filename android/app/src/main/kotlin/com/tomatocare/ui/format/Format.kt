package com.tomatocare.ui.format

import java.text.DateFormat
import java.time.Instant
import java.util.Date

/**
 * Render a stored ISO-8601 UTC timestamp in the user's locale.
 * Falls back to the raw string if parsing fails — the UI prefers showing
 * something readable over crashing on a malformed history entry.
 */
fun formatTimestamp(iso: String): String = try {
    val date = Date.from(Instant.parse(iso))
    DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.SHORT)
        .format(date)
} catch (_: Exception) {
    iso
}

fun formatConfidence(value: Double): String =
    "${(value * 100).toInt()}%"
