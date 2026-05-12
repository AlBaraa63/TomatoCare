package com.tomatocare.data.model

import kotlinx.serialization.Serializable

/**
 * All enums are serialised as their name string (default kotlinx behaviour),
 * so JSON export/import is human-readable and forward-compatible: adding a
 * new enum value only breaks old apps reading the new file, not vice-versa.
 */
@Serializable
enum class StressType { BIOTIC, ABIOTIC }

@Serializable
enum class SeverityLevel { LOW, MEDIUM, HIGH, CRITICAL }

@Serializable
enum class GrowingMethod { GREENHOUSE, OPEN_FIELD, HYDROPONIC, SALINE_SOIL }

@Serializable
enum class Language { ENGLISH, ARABIC }

@Serializable
enum class TreatmentType { CHEMICAL, CULTURAL, BIOLOGICAL }

@Serializable
enum class UrgencyLevel { LOW, MEDIUM, HIGH, CRITICAL }
