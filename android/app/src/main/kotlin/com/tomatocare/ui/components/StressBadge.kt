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
import com.tomatocare.data.model.StressType

@Composable
fun StressBadge(stressType: StressType, modifier: Modifier = Modifier) {
    val bg = when (stressType) {
        StressType.BIOTIC -> Color(0xFFC62828)
        StressType.ABIOTIC -> Color(0xFFF57C00)
    }
    val labelRes = when (stressType) {
        StressType.BIOTIC -> R.string.badge_biotic
        StressType.ABIOTIC -> R.string.badge_abiotic
    }
    Text(
        text = stringResource(labelRes),
        color = Color.White,
        style = MaterialTheme.typography.labelMedium,
        modifier = modifier
            .background(bg, shape = RoundedCornerShape(50))
            .padding(horizontal = 12.dp, vertical = 6.dp),
    )
}
