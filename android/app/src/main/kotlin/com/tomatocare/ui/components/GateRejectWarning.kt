package com.tomatocare.ui.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Info
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.tomatocare.R
import com.tomatocare.data.model.RejectReason

/**
 * Shown when a cascade gate rejected the image before any diagnosis: the
 * photo is not a leaf, or it is a leaf but not a tomato. There is no
 * "show anyway" escape hatch (unlike LowConfidenceWarning) — a rejected
 * image has no diagnosis to show, so the only action is to retake.
 */
@Composable
fun GateRejectWarning(
    reason: RejectReason,
    onRetake: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val titleRes = when (reason) {
        RejectReason.NOT_A_LEAF -> R.string.reject_not_leaf_title
        RejectReason.NOT_A_TOMATO -> R.string.reject_not_tomato_title
        RejectReason.NONE -> R.string.reject_not_leaf_title
    }
    val bodyRes = when (reason) {
        RejectReason.NOT_A_LEAF -> R.string.reject_not_leaf_body
        RejectReason.NOT_A_TOMATO -> R.string.reject_not_tomato_body
        RejectReason.NONE -> R.string.reject_not_leaf_body
    }

    Card(
        modifier = modifier.fillMaxWidth().padding(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFE3F2FD)),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Default.Info,
                    tint = Color(0xFF1565C0),
                    contentDescription = null,
                )
                Text(
                    text = stringResource(titleRes),
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(start = 8.dp),
                )
            }
            Spacer(Modifier.height(12.dp))
            Text(
                text = stringResource(bodyRes),
                style = MaterialTheme.typography.bodyMedium,
            )
            Spacer(Modifier.height(16.dp))
            Button(onClick = onRetake) {
                Text(stringResource(R.string.action_retake))
            }
        }
    }
}
