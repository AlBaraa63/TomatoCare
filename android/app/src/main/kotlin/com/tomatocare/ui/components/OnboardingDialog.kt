package com.tomatocare.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.CloudOff
import androidx.compose.material.icons.filled.Eco
import androidx.compose.material.icons.filled.WbSunny
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.tomatocare.R

/**
 * First-launch how-to-use dialog. Shown once (gated by
 * UserSettings.hasSeenOnboarding); dismissing it persists the flag so it
 * never appears again. Content mirrors what the cascade needs from a good
 * photo, so users don't fight the leaf/tomato gates.
 */
@Composable
fun OnboardingDialog(
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.onboarding_title)) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
                OnboardingStep(Icons.Default.CameraAlt, R.string.onboarding_step_photo)
                OnboardingStep(Icons.Default.WbSunny, R.string.onboarding_step_light)
                OnboardingStep(Icons.Default.Eco, R.string.onboarding_step_tomato)
                OnboardingStep(Icons.Default.CloudOff, R.string.onboarding_step_offline)
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text(stringResource(R.string.onboarding_got_it))
            }
        },
    )
}

@Composable
private fun OnboardingStep(icon: ImageVector, textRes: Int) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.primary,
            modifier = androidx.compose.ui.Modifier.size(24.dp),
        )
        Spacer(androidx.compose.ui.Modifier.width(12.dp))
        Text(
            text = stringResource(textRes),
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}
