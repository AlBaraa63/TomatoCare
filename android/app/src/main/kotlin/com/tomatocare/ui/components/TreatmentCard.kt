package com.tomatocare.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
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
import com.tomatocare.data.model.Language
import com.tomatocare.data.model.Treatment
import com.tomatocare.data.model.UrgencyLevel

@Composable
fun TreatmentCard(
    treatment: Treatment,
    language: Language,
    modifier: Modifier = Modifier,
) {
    var expanded by remember { mutableStateOf(false) }
    val recommendation = if (language == Language.ARABIC) {
        treatment.recommendationAr
    } else {
        treatment.recommendationEn
    }

    Card(
        modifier = modifier.fillMaxWidth().clickable { expanded = !expanded },
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = stringResource(
                        labelForType(treatment.treatmentType),
                    ),
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.weight(1f),
                )
                UrgencyTag(treatment.urgencyLevel)
                Icon(
                    imageVector = if (expanded)
                        Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                    contentDescription = stringResource(R.string.action_toggle_details),
                )
            }
            AnimatedVisibility(visible = expanded) {
                Text(
                    text = recommendation,
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(top = 8.dp),
                )
            }
        }
    }
}

private fun labelForType(t: com.tomatocare.data.model.TreatmentType): Int =
    when (t) {
        com.tomatocare.data.model.TreatmentType.CHEMICAL -> R.string.treatment_type_chemical
        com.tomatocare.data.model.TreatmentType.CULTURAL -> R.string.treatment_type_cultural
        com.tomatocare.data.model.TreatmentType.BIOLOGICAL -> R.string.treatment_type_biological
    }

@Composable
private fun UrgencyTag(urgency: UrgencyLevel) {
    val labelRes = when (urgency) {
        UrgencyLevel.LOW -> R.string.urgency_low
        UrgencyLevel.MEDIUM -> R.string.urgency_medium
        UrgencyLevel.HIGH -> R.string.urgency_high
        UrgencyLevel.CRITICAL -> R.string.urgency_critical
    }
    Text(
        text = stringResource(labelRes),
        style = MaterialTheme.typography.labelSmall,
        modifier = Modifier.padding(end = 8.dp),
    )
}
