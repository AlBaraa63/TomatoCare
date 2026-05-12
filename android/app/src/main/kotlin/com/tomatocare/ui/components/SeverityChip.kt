package com.tomatocare.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.tomatocare.R
import com.tomatocare.data.model.SeverityLevel

@Composable
fun SeverityChip(severity: SeverityLevel, modifier: Modifier = Modifier) {
    val bg = when (severity) {
        SeverityLevel.LOW -> Color(0xFF43A047)
        SeverityLevel.MEDIUM -> Color(0xFFFB8C00)
        SeverityLevel.HIGH -> Color(0xFFE53935)
        SeverityLevel.CRITICAL -> Color(0xFFB71C1C)
    }
    val labelRes = when (severity) {
        SeverityLevel.LOW -> R.string.severity_low
        SeverityLevel.MEDIUM -> R.string.severity_medium
        SeverityLevel.HIGH -> R.string.severity_high
        SeverityLevel.CRITICAL -> R.string.severity_critical
    }
    Text(
        text = stringResource(labelRes),
        color = Color.White,
        style = MaterialTheme.typography.labelMedium,
        modifier = modifier
            .background(bg, shape = RoundedCornerShape(8.dp))
            .padding(horizontal = 12.dp, vertical = 6.dp),
    )
}
