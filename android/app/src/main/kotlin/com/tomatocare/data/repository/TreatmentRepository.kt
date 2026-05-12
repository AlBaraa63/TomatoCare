package com.tomatocare.data.repository

import android.content.Context
import com.tomatocare.data.model.ConditionInfo
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.model.Treatment
import com.tomatocare.data.model.TreatmentsCatalog
import kotlinx.serialization.json.Json

/**
 * Loads treatments.json from assets once at construction and caches it in
 * an immutable map keyed by both conditionId and classLabel. All lookups
 * are O(1). Per-condition filter by GrowingMethod returns a (possibly
 * empty) list of treatments — empty results are valid input to the UI,
 * which shows a "no advice for this growing method yet" placeholder.
 */
class TreatmentRepository(context: Context) {

    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }

    private val byConditionId: Map<String, ConditionInfo>
    private val byClassLabel: Map<String, ConditionInfo>

    init {
        val text = context.assets.open(ASSET_NAME).bufferedReader(Charsets.UTF_8)
            .use { it.readText() }
        val catalog: TreatmentsCatalog = json.decodeFromString(text)
        byConditionId = catalog.conditions.associateBy { it.conditionId }
        byClassLabel = catalog.conditions.associateBy { it.classLabel }
    }

    fun getCondition(conditionId: String): ConditionInfo? =
        byConditionId[conditionId]

    fun getConditionByClassLabel(classLabel: String): ConditionInfo? =
        byClassLabel[classLabel]

    fun getTreatments(conditionId: String, method: GrowingMethod): List<Treatment> {
        val condition = byConditionId[conditionId] ?: return emptyList()
        return condition.treatments.filter { it.growingMethod == method }
    }

    fun allConditions(): List<ConditionInfo> = byConditionId.values.toList()

    companion object {
        private const val ASSET_NAME = "treatments.json"
    }
}
