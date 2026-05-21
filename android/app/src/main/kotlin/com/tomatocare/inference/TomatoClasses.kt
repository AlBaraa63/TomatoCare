package com.tomatocare.inference

/**
 * Canonical class label list, alphabetical (matches TF Keras
 * image_dataset_from_directory's default class_names ordering).
 *
 * Kept in a dependency-free file so JVM unit tests can validate the
 * order without pulling in the TFLite native library.
 */
object TomatoClasses {

    const val MODEL_ASSET = "tomatocare_model_float16.tflite"

    /**
     * MUST match the order Keras assigned during training.
     * Wrong order → silent misclassification on every inference.
     *
     * Index 10 (Tomato_NotALeaf) is the OOD reject class: when the
     * top-1 probability lands on it, the image isn't a tomato leaf
     * and the engine routes the result through the low-confidence
     * UI instead of returning a bogus diagnosis. See [OOD_CLASS_INDEX].
     */
    val CLASS_NAMES: List<String> = listOf(
        "Tomato_Bacterial_spot",                        // 0
        "Tomato_Early_blight",                          // 1
        "Tomato_healthy",                               // 2
        "Tomato_Late_blight",                           // 3
        "Tomato_Leaf_Mold",                             // 4
        "Tomato_Septoria_leaf_spot",                    // 5
        "Tomato_Spider_mites_Two_spotted_spider_mite",  // 6
        "Tomato_Target_Spot",                           // 7
        "Tomato_Yellow_Leaf_Curl_Virus",                // 8
        "Tomato_mosaic_virus",                          // 9
        "Tomato_NotALeaf",                              // 10 (OOD reject)
    )

    const val OOD_CLASS_NAME: String = "Tomato_NotALeaf"

    /** -1 if the OOD class is missing — engine then degrades to no-OOD. */
    val OOD_CLASS_INDEX: Int = CLASS_NAMES.indexOf(OOD_CLASS_NAME)
}
