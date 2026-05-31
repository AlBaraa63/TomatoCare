package com.tomatocare

import androidx.activity.ComponentActivity
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import com.tomatocare.data.model.SeverityLevel
import com.tomatocare.data.model.StressType
import com.tomatocare.ui.components.SeverityChip
import com.tomatocare.ui.components.StressBadge
import com.tomatocare.ui.theme.TomatoCareTheme
import org.junit.Rule
import org.junit.Test

/**
 * Compose UI tests for the status badges. Resolves expected labels through the
 * activity's resources (so the assertions stay correct if the wording changes)
 * and renders each component inside the real app theme.
 */
class BadgeUiTest {

    @get:Rule
    val composeRule = createAndroidComposeRule<ComponentActivity>()

    private fun string(resId: Int) = composeRule.activity.getString(resId)

    @Test
    fun severityChip_rendersCriticalLabel() {
        composeRule.setContent {
            TomatoCareTheme { SeverityChip(SeverityLevel.CRITICAL) }
        }
        composeRule.onNodeWithText(string(R.string.severity_critical)).assertIsDisplayed()
    }

    @Test
    fun severityChip_rendersLowLabel() {
        composeRule.setContent {
            TomatoCareTheme { SeverityChip(SeverityLevel.LOW) }
        }
        composeRule.onNodeWithText(string(R.string.severity_low)).assertIsDisplayed()
    }

    @Test
    fun stressBadge_rendersBioticLabel() {
        composeRule.setContent {
            TomatoCareTheme { StressBadge(StressType.BIOTIC) }
        }
        composeRule.onNodeWithText(string(R.string.badge_biotic)).assertIsDisplayed()
    }
}
