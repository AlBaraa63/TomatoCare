package com.tomatocare.ui.components

import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.tomatocare.R
import com.tomatocare.data.model.SeverityLevel
import com.tomatocare.ui.theme.SeverityCriticalColor
import com.tomatocare.ui.theme.SeverityHighColor
import com.tomatocare.ui.theme.SeverityLowColor
import com.tomatocare.ui.theme.SeverityMediumColor

@Composable
fun SeverityChip(severity: SeverityLevel, modifier: Modifier = Modifier) {
    val bg = when (severity) {
        SeverityLevel.LOW -> SeverityLowColor
        SeverityLevel.MEDIUM -> SeverityMediumColor
        SeverityLevel.HIGH -> SeverityHighColor
        SeverityLevel.CRITICAL -> SeverityCriticalColor
    }
    val labelRes = when (severity) {
        SeverityLevel.LOW -> R.string.severity_low
        SeverityLevel.MEDIUM -> R.string.severity_medium
        SeverityLevel.HIGH -> R.string.severity_high
        SeverityLevel.CRITICAL -> R.string.severity_critical
    }
    Surface(
        modifier = modifier,
        color = bg.copy(alpha = 0.15f),
        shape = MaterialTheme.shapes.small,
        tonalElevation = 0.dp,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                imageVector = Icons.Default.Shield,
                contentDescription = null,
                tint = bg,
                modifier = Modifier.size(14.dp),
            )
            Spacer(Modifier.width(4.dp))
            Text(
                text = stringResource(labelRes),
                color = bg,
                style = MaterialTheme.typography.labelMedium,
            )
        }
    }
}
