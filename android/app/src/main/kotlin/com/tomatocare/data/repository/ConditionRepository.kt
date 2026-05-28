package com.tomatocare.data.repository

import android.content.Context
import com.tomatocare.data.model.ConditionInfo
import com.tomatocare.data.model.TreatmentsCatalog
import kotlinx.serialization.json.Json

/**
 * Loads conditions from the treatments.json catalog for use in the
 * Disease Encyclopedia screen and Feedback card.
 */
class ConditionRepository(context: Context) {

    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }
    private val byConditionId: Map<String, ConditionInfo>

    init {
        val text = context.assets.open(ASSET_NAME).bufferedReader(Charsets.UTF_8)
            .use { it.readText() }
        val catalog: TreatmentsCatalog = json.decodeFromString(text)
        byConditionId = catalog.conditions.associateBy { it.conditionId }
    }

    fun getAllConditions(): List<ConditionInfo> =
        byConditionId.values.toList().sortedBy { it.nameEn }

    fun getCondition(conditionId: String): ConditionInfo? =
        byConditionId[conditionId]

    companion object {
        private const val ASSET_NAME = "treatments.json"
    }
}
