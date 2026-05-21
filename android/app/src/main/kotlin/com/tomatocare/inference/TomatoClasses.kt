package com.tomatocare.inference

/**
 * Canonical class metadata for the THREE-STAGE cascade (Capstone 2).
 *
 * The model is no longer a single classifier with an OOD reject class.
 * It is a decision tree of three TFLite models, each run in sequence:
 *
 *   Stage 1  leaf gate    : is this a leaf at all?      [leaf, not_leaf]
 *   Stage 2  tomato gate  : is it a TOMATO leaf?         [other_leaf, tomato]
 *   Stage 3  disease      : which of 11 conditions?      (10 diseases + healthy)
 *
 * Each list MUST match the order Keras assigned during training
 * (alphabetical by folder name = image_dataset_from_directory default).
 * The orders below are copied verbatim from the exported
 * {stage}.meta.json "class_names" arrays. A wrong order silently
 * misclassifies every inference.
 *
 * Kept dependency-free so JVM unit tests can validate the order without
 * pulling in the TFLite native library.
 */
object TomatoClasses {

    // ---- TFLite asset file names (bundled uncompressed; see build.gradle) ----
    const val LEAF_MODEL_ASSET = "stage1_leaf_float16.tflite"
    const val TOMATO_MODEL_ASSET = "stage2_tomato_float16.tflite"
    const val DISEASE_MODEL_ASSET = "stage3_disease_float16.tflite"

    // ---- Stage 1: leaf gate ----
    val LEAF_CLASS_NAMES: List<String> = listOf(
        "leaf",        // 0
        "not_leaf",    // 1
    )
    val LEAF_INDEX: Int = LEAF_CLASS_NAMES.indexOf("leaf")

    // ---- Stage 2: tomato gate ----
    val TOMATO_CLASS_NAMES: List<String> = listOf(
        "other_leaf",  // 0
        "tomato",      // 1
    )
    val TOMATO_INDEX: Int = TOMATO_CLASS_NAMES.indexOf("tomato")

    // ---- Stage 3: disease classifier ----
    // These are the canonical lowercase_snake_case condition keys; they map
    // 1:1 to ConditionInfo.conditionId in treatments.json, so the engine
    // looks conditions up by this key directly (no Tomato_* alias needed).
    val DISEASE_CLASS_NAMES: List<String> = listOf(
        "bacterial_spot",          // 0
        "early_blight",            // 1
        "healthy",                 // 2
        "late_blight",             // 3
        "leaf_mold",               // 4
        "mosaic_virus",            // 5
        "powdery_mildew",          // 6
        "septoria_leaf_spot",      // 7
        "spider_mites",            // 8
        "target_spot",             // 9
        "yellow_leaf_curl_virus",  // 10
    )
}
