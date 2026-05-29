package com.tomatocare.ui.home

import com.tomatocare.data.model.ScanRecord

/**
 * Pure computation of the Home dashboard statistics, extracted from
 * [HomeViewModel] so the logic — including the health-rate metric — is
 * unit-testable without an Android context.
 */
object HomeStats {

    /** conditionId of the healthy class. Must match assets/treatments.json. */
    const val HEALTHY_ID = "healthy"

    data class Result(
        val totalScans: Int,
        val distinctConditions: Int,
        val healthRate: Int,                          // % of valid scans whose primary is healthy
        val topConditions: List<Pair<String, Int>>,   // up to 3, by frequency (localised label)
    )

    fun compute(scans: List<ScanRecord>, isArabic: Boolean): Result {
        val validScans = scans.mapNotNull { it.primary }
        val distinct = validScans.map { it.conditionId }.distinct().count()
        val healthyCount = validScans.count { it.conditionId == HEALTHY_ID }
        val healthRate = if (validScans.isNotEmpty()) {
            (healthyCount * 100f / validScans.size).toInt()
        } else 0
        val topConditions = validScans
            .groupingBy { if (isArabic) it.conditionNameAr else it.conditionNameEn }
            .eachCount()
            .entries
            .sortedByDescending { it.value }
            .take(3)
            .map { it.key to it.value }
        return Result(
            totalScans = scans.size,
            distinctConditions = distinct,
            healthRate = healthRate,
            topConditions = topConditions,
        )
    }
}
