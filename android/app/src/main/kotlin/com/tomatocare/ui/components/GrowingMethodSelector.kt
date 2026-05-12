package com.tomatocare.ui.components

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.tomatocare.R
import com.tomatocare.data.model.GrowingMethod

@Composable
fun GrowingMethodSelector(
    selected: GrowingMethod,
    onSelected: (GrowingMethod) -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier
            .horizontalScroll(rememberScrollState())
            .padding(horizontal = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        GrowingMethod.values().forEach { method ->
            val labelRes = labelResFor(method)
            FilterChip(
                selected = method == selected,
                onClick = { onSelected(method) },
                label = { Text(stringResource(labelRes)) },
                colors = FilterChipDefaults.filterChipColors(),
            )
        }
    }
}

private fun labelResFor(method: GrowingMethod): Int = when (method) {
    GrowingMethod.GREENHOUSE -> R.string.method_greenhouse
    GrowingMethod.OPEN_FIELD -> R.string.method_open_field
    GrowingMethod.HYDROPONIC -> R.string.method_hydroponic
    GrowingMethod.SALINE_SOIL -> R.string.method_saline_soil
}
