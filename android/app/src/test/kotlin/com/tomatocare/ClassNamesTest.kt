package com.tomatocare

import com.tomatocare.inference.TFLiteEngine
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Guards the class label list against accidental reordering or edits.
 * The order MUST match what TF Keras assigned during training (alphabetical
 * by folder name). A mismatch silently misclassifies every inference.
 */
class ClassNamesTest {

    @Test
    fun classCount_isTen() {
        assertEquals(10, TFLiteEngine.CLASS_NAMES.size)
    }

    @Test
    fun classNames_areAlphabeticallySorted() {
        val sorted = TFLiteEngine.CLASS_NAMES.sorted()
        assertEquals("CLASS_NAMES must be in alphabetical order to match Keras index",
            sorted, TFLiteEngine.CLASS_NAMES)
    }

    @Test
    fun classNames_containsAllRequiredConditions() {
        val required = listOf(
            "Tomato_Bacterial_spot",
            "Tomato_Early_blight",
            "Tomato_healthy",
            "Tomato_Late_blight",
            "Tomato_Leaf_Mold",
            "Tomato_Septoria_leaf_spot",
            "Tomato_Spider_mites_Two_spotted_spider_mite",
            "Tomato_Target_Spot",
            "Tomato_Yellow_Leaf_Curl_Virus",
            "Tomato_mosaic_virus",
        )
        for (name in required) {
            assertTrue("Missing required class: $name",
                TFLiteEngine.CLASS_NAMES.contains(name))
        }
    }

    @Test
    fun healthyClass_isAtIndex2() {
        // Healthy is a sentinel — wrong index makes the app report disease on clean leaves
        assertEquals("Tomato_healthy", TFLiteEngine.CLASS_NAMES[2])
    }

    @Test
    fun allClassNames_startWithTomato() {
        for (name in TFLiteEngine.CLASS_NAMES) {
            assertTrue("Class '$name' must start with 'Tomato'", name.startsWith("Tomato"))
        }
    }
}
