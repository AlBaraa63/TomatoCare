package com.tomatocare.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BugReport
import androidx.compose.material.icons.filled.WbSunny
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.tomatocare.R
import com.tomatocare.data.model.StressType

@Composable
fun StressBadge(stressType: StressType, modifier: Modifier = Modifier) {
    val color = when (stressType) {
        StressType.BIOTIC -> Color(0xFFC62828)
        StressType.ABIOTIC -> Color(0xFFF57C00)
    }
    val icon = when (stressType) {
        StressType.BIOTIC -> Icons.Default.BugReport
        StressType.ABIOTIC -> Icons.Default.WbSunny
    }
    val labelRes = when (stressType) {
        StressType.BIOTIC -> R.string.badge_biotic
        StressType.ABIOTIC -> R.string.badge_abiotic
    }

    Surface(
        modifier = modifier,
        color = color.copy(alpha = 0.1f),
        shape = MaterialTheme.shapes.small,
        border = BorderStroke(1.dp, color.copy(alpha = 0.3f)),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = color,
                modifier = Modifier.size(14.dp),
            )
            Spacer(Modifier.width(4.dp))
            Text(
                text = stringResource(labelRes),
                color = color,
                style = MaterialTheme.typography.labelMedium,
            )
        }
    }
}
