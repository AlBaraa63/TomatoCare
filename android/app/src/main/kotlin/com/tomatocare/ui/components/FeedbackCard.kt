package com.tomatocare.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Done
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.tomatocare.R
import com.tomatocare.data.model.ConditionInfo
import com.tomatocare.data.model.Language
import com.tomatocare.data.model.ScanFeedback

/**
 * Data-flywheel feedback prompt on the result screen. Asks the user whether
 * the diagnosis was correct; if not, lets them pick the true condition. The
 * answer is stored on the ScanRecord so real-world (UAE) labelled data
 * accumulates for later retraining export.
 *
 * Once feedback exists it becomes a read-only thank-you summary — feedback
 * is captured once per scan.
 */
@Composable
fun FeedbackCard(
    feedback: ScanFeedback?,
    conditions: List<ConditionInfo>,
    language: Language,
    onCorrect: () -> Unit,
    onIncorrect: (conditionId: String) -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            if (feedback != null) {
                ThanksSummary(feedback, conditions, language)
            } else {
                Prompt(conditions, language, onCorrect, onIncorrect)
            }
        }
    }
}

@Composable
private fun Prompt(
    conditions: List<ConditionInfo>,
    language: Language,
    onCorrect: () -> Unit,
    onIncorrect: (conditionId: String) -> Unit,
) {
    var picking by remember { mutableStateOf(false) }

    Text(
        text = stringResource(R.string.feedback_question),
        style = MaterialTheme.typography.titleSmall,
    )
    Spacer(Modifier.height(12.dp))
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Button(onClick = onCorrect, modifier = Modifier.weight(1f)) {
            Icon(Icons.Default.Done, contentDescription = null)
            Spacer(Modifier.width(8.dp))
            Text(stringResource(R.string.feedback_yes))
        }
        OutlinedButton(onClick = { picking = true }, modifier = Modifier.weight(1f)) {
            Icon(Icons.Default.Close, contentDescription = null)
            Spacer(Modifier.width(8.dp))
            Text(stringResource(R.string.feedback_no))
        }
    }

    if (picking) {
        Spacer(Modifier.height(8.dp))
        Text(
            text = stringResource(R.string.feedback_pick_correct),
            style = MaterialTheme.typography.bodyMedium,
        )
        Box {
            var expanded by remember { mutableStateOf(true) }
            OutlinedButton(
                onClick = { expanded = true },
                modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
            ) {
                Text(stringResource(R.string.feedback_select_condition))
            }
            DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                conditions.forEach { c ->
                    DropdownMenuItem(
                        text = { Text(displayName(c, language)) },
                        onClick = {
                            expanded = false
                            picking = false
                            onIncorrect(c.conditionId)
                        },
                    )
                }
            }
        }
    }
}

@Composable
private fun ThanksSummary(
    feedback: ScanFeedback,
    conditions: List<ConditionInfo>,
    language: Language,
) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(
            imageVector = Icons.Default.CheckCircle,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.primary,
        )
        Spacer(Modifier.width(8.dp))
        Column {
            Text(
                text = stringResource(R.string.feedback_thanks),
                style = MaterialTheme.typography.titleSmall,
            )
            val detail = if (feedback.wasCorrect) {
                stringResource(R.string.feedback_marked_correct)
            } else {
                val name = conditions
                    .firstOrNull { it.conditionId == feedback.correctedConditionId }
                    ?.let { displayName(it, language) }
                    ?: (feedback.correctedConditionId ?: "")
                stringResource(R.string.feedback_corrected_to, name)
            }
            Text(text = detail, style = MaterialTheme.typography.bodySmall)
        }
    }
}

private fun displayName(c: ConditionInfo, language: Language): String =
    if (language == Language.ARABIC) c.nameAr else c.nameEn
