package com.tomatocare

import com.tomatocare.inference.TomatoClasses
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Guards the THREE-STAGE cascade class lists against accidental reordering
 * or edits. Each list MUST match the order Keras assigned during training
 * (alphabetical by folder name), copied verbatim from the exported
 * {stage}.meta.json. A mismatch silently misclassifies every inference.
 */
class ClassNamesTest {

    // ---- Stage 1: leaf gate ----
    @Test
    fun leafGate_hasTwoClassesInOrder() {
        assertEquals(listOf("leaf", "not_leaf"), TomatoClasses.LEAF_CLASS_NAMES)
        assertEquals(0, TomatoClasses.LEAF_INDEX)
    }

    // ---- Stage 2: tomato gate ----
    @Test
    fun tomatoGate_hasTwoClassesInOrder() {
        assertEquals(listOf("other_leaf", "tomato"), TomatoClasses.TOMATO_CLASS_NAMES)
        assertEquals(1, TomatoClasses.TOMATO_INDEX)
    }

    // ---- Stage 3: disease classifier ----
    @Test
    fun diseaseNet_hasElevenClasses() {
        assertEquals(11, TomatoClasses.DISEASE_CLASS_NAMES.size)
    }

    /**
     * Authoritative order from stage3_disease.meta.json. 10 disease classes
     * plus "healthy" — no OOD class anymore (the two binary gates handle
     * rejection upstream).
     */
    @Test
    fun diseaseNet_matchesAuthoritativeOrder() {
        val expected = listOf(
            "bacterial_spot",
            "early_blight",
            "healthy",
            "late_blight",
            "leaf_mold",
            "mosaic_virus",
            "powdery_mildew",
            "septoria_leaf_spot",
            "spider_mites",
            "target_spot",
            "yellow_leaf_curl_virus",
        )
        assertEquals("DISEASE_CLASS_NAMES must match the training order from stage3_disease.meta.json",
            expected, TomatoClasses.DISEASE_CLASS_NAMES)
    }

    @Test
    fun diseaseNet_isAlphabetical() {
        // Keras orders class folders alphabetically; this catches reordering.
        assertEquals(TomatoClasses.DISEASE_CLASS_NAMES.sorted(),
            TomatoClasses.DISEASE_CLASS_NAMES)
    }

    @Test
    fun healthyClass_isAtIndexTwo() {
        assertEquals("healthy", TomatoClasses.DISEASE_CLASS_NAMES[2])
    }

    @Test
    fun diseaseClasses_areSnakeCaseKeys() {
        // conditionId keys in treatments.json are lowercase_snake_case; the
        // engine looks conditions up by these directly, so they must match.
        val pattern = Regex("^[a-z]+(_[a-z]+)*$")
        for (name in TomatoClasses.DISEASE_CLASS_NAMES) {
            assertTrue("Class '$name' must be lowercase_snake_case",
                pattern.matches(name))
        }
    }

    @Test
    fun modelAssets_areDeclared() {
        assertEquals("stage1_leaf_float16.tflite", TomatoClasses.LEAF_MODEL_ASSET)
        assertEquals("stage2_tomato_float16.tflite", TomatoClasses.TOMATO_MODEL_ASSET)
        assertEquals("stage3_disease_float16.tflite", TomatoClasses.DISEASE_MODEL_ASSET)
    }
}
