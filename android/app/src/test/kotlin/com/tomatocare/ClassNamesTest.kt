package com.tomatocare

import com.tomatocare.inference.TomatoClasses
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
    fun classCount_isEleven() {
        assertEquals(11, TomatoClasses.CLASS_NAMES.size)
    }

    /**
     * 10 disease classes (indices 0-9) plus the OOD reject class
     * Tomato_NotALeaf at index 10. Order matches train.csv from
     * prepare_plantvillage.py; NotALeaf is appended after the
     * alphabetical disease list in prepare_negatives.py.
     */
    @Test
    fun classNames_matchAuthoritativeOrder() {
        val expected = listOf(
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
            "Tomato_NotALeaf",
        )
        assertEquals("CLASS_NAMES must match the authoritative training order from train.csv",
            expected, TomatoClasses.CLASS_NAMES)
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
            "Tomato_NotALeaf",
        )
        for (name in required) {
            assertTrue("Missing required class: $name",
                TomatoClasses.CLASS_NAMES.contains(name))
        }
    }

    @Test
    fun oodClass_isAtIndexTen() {
        assertEquals("Tomato_NotALeaf", TomatoClasses.CLASS_NAMES[10])
        assertEquals(10, TomatoClasses.OOD_CLASS_INDEX)
    }

    @Test
    fun healthyClass_isAtIndex2() {
        assertEquals("Tomato_healthy", TomatoClasses.CLASS_NAMES[2])
    }

    @Test
    fun allClassNames_startWithTomato() {
        for (name in TomatoClasses.CLASS_NAMES) {
            assertTrue("Class '$name' must start with 'Tomato'", name.startsWith("Tomato"))
        }
    }
}
