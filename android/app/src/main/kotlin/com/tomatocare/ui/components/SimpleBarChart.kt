package com.tomatocare.ui.components

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

/**
 * A lightweight horizontal bar chart drawn with standard Compose layout
 * primitives. No external charting library needed. Each item gets an
 * animated bar proportional to its count relative to the max.
 */
@Composable
fun SimpleBarChart(
    items: List<BarChartItem>,
    modifier: Modifier = Modifier,
) {
    if (items.isEmpty()) return
    val maxCount = items.maxOf { it.count }.coerceAtLeast(1)

    Column(
        modifier = modifier.fillMaxWidth(),
    ) {
        items.forEach { item ->
            BarRow(
                label = item.label,
                count = item.count,
                maxCount = maxCount,
                color = item.color,
            )
        }
    }
}

@Composable
private fun BarRow(
    label: String,
    count: Int,
    maxCount: Int,
    color: Color,
) {
    var target by remember { mutableFloatStateOf(0f) }
    LaunchedEffect(count, maxCount) {
        target = count.toFloat() / maxCount.toFloat()
    }
    val animatedFraction by animateFloatAsState(
        targetValue = target,
        animationSpec = tween(durationMillis = 600),
        label = "bar_$label",
    )

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 3.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.width(100.dp),
            maxLines = 1,
        )
        Box(
            modifier = Modifier
                .weight(1f)
                .height(14.dp)
                .clip(RoundedCornerShape(7.dp))
                .background(MaterialTheme.colorScheme.surfaceVariant),
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth(animatedFraction.coerceIn(0.02f, 1f))
                    .height(14.dp)
                    .clip(RoundedCornerShape(7.dp))
                    .background(color),
            )
        }
        Spacer(Modifier.width(8.dp))
        Text(
            text = count.toString(),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurface,
        )
    }
}

data class BarChartItem(
    val label: String,
    val count: Int,
    val color: Color,
)
