package com.tomatocare.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.tomatocare.R
import com.tomatocare.data.model.Language
import com.tomatocare.data.model.Treatment
import com.tomatocare.data.model.TreatmentType
import com.tomatocare.data.model.UrgencyLevel
import com.tomatocare.ui.theme.TreatmentBiologicalColor
import com.tomatocare.ui.theme.TreatmentChemicalColor
import com.tomatocare.ui.theme.TreatmentCulturalColor

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

    val typeColor = when (treatment.treatmentType) {
        TreatmentType.CHEMICAL -> TreatmentChemicalColor
        TreatmentType.CULTURAL -> TreatmentCulturalColor
        TreatmentType.BIOLOGICAL -> TreatmentBiologicalColor
    }

    val rotation by animateFloatAsState(
        targetValue = if (expanded) 180f else 0f,
        label = "expand_arrow",
    )

    Card(
        modifier = modifier
            .fillMaxWidth()
            .clickable { expanded = !expanded },
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
        shape = MaterialTheme.shapes.medium,
    ) {
        Row(modifier = Modifier.fillMaxWidth()) {
            // Left colour bar
            Box(
                modifier = Modifier
                    .width(4.dp)
                    .fillMaxHeight()
                    .background(typeColor)
                    .align(Alignment.CenterVertically),
            )
            // Content
            Column(modifier = Modifier.padding(16.dp).weight(1f)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = stringResource(labelForType(treatment.treatmentType)),
                        style = MaterialTheme.typography.titleMedium,
                        color = typeColor,
                        modifier = Modifier.weight(1f),
                    )
                    UrgencyPill(treatment.urgencyLevel)
                    Spacer(Modifier.width(8.dp))
                    Icon(
                        imageVector = Icons.Default.ExpandMore,
                        contentDescription = stringResource(R.string.action_toggle_details),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.rotate(rotation),
                    )
                }
                AnimatedVisibility(visible = expanded) {
                    Text(
                        text = recommendation,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurface,
                        modifier = Modifier.padding(top = 12.dp),
                    )
                }
            }
        }
    }
}

private fun labelForType(t: TreatmentType): Int = when (t) {
    TreatmentType.CHEMICAL -> R.string.treatment_type_chemical
    TreatmentType.CULTURAL -> R.string.treatment_type_cultural
    TreatmentType.BIOLOGICAL -> R.string.treatment_type_biological
}

@Composable
private fun UrgencyPill(urgency: UrgencyLevel) {
    val color = when (urgency) {
        UrgencyLevel.LOW -> Color(0xFF43A047)
        UrgencyLevel.MEDIUM -> Color(0xFFFB8C00)
        UrgencyLevel.HIGH -> Color(0xFFE53935)
        UrgencyLevel.CRITICAL -> Color(0xFFB71C1C)
    }
    val labelRes = when (urgency) {
        UrgencyLevel.LOW -> R.string.urgency_low
        UrgencyLevel.MEDIUM -> R.string.urgency_medium
        UrgencyLevel.HIGH -> R.string.urgency_high
        UrgencyLevel.CRITICAL -> R.string.urgency_critical
    }
    Surface(
        color = color.copy(alpha = 0.12f),
        shape = MaterialTheme.shapes.small,
    ) {
        Text(
            text = stringResource(labelRes),
            style = MaterialTheme.typography.labelSmall,
            color = color,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
        )
    }
}
