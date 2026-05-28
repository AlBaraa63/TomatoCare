package com.tomatocare.ui.components

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.tomatocare.ui.theme.confidenceColor

/**
 * Horizontal animated confidence bar. A thin track with a filled portion
 * that animates from 0 to the target width. Used in history rows and
 * "other possibilities" cards.
 */
@Composable
fun ConfidenceBar(
    confidence: Float,     // 0.0–1.0
    height: Dp = 6.dp,
    modifier: Modifier = Modifier,
) {
    var target by remember { mutableFloatStateOf(0f) }
    LaunchedEffect(confidence) { target = confidence }

    val animatedFraction by animateFloatAsState(
        targetValue = target,
        animationSpec = tween(durationMillis = 700),
        label = "confidence_bar",
    )

    val trackColor = MaterialTheme.colorScheme.surfaceVariant
    val fillColor = confidenceColor(confidence)
    val shape = RoundedCornerShape(height / 2)

    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(height)
            .clip(shape)
            .background(trackColor),
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth(animatedFraction)
                .height(height)
                .clip(shape)
                .background(fillColor),
        )
    }
}
