package com.tomatocare.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.outlined.CameraAlt
import androidx.compose.material.icons.outlined.History
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.MenuBook
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.ui.graphics.vector.ImageVector
import com.tomatocare.R

object Routes {
    const val HOME = "home"
    const val SCAN = "scan"
    const val RESULT = "result/{scanId}"
    const val HISTORY = "history"
    const val SETTINGS = "settings"
    const val ENCYCLOPEDIA = "encyclopedia"

    fun result(scanId: Int) = "result/$scanId"
}

/**
 * Bottom navigation destinations. ResultScreen is NOT included — it is a
 * detail screen pushed on top, with back navigation.
 */
enum class BottomNavItem(
    val route: String,
    val labelRes: Int,
    val selectedIcon: ImageVector,
    val unselectedIcon: ImageVector,
) {
    HOME(
        route = Routes.HOME,
        labelRes = R.string.nav_home,
        selectedIcon = Icons.Filled.Home,
        unselectedIcon = Icons.Outlined.Home,
    ),
    SCAN(
        route = Routes.SCAN,
        labelRes = R.string.nav_scan,
        selectedIcon = Icons.Filled.CameraAlt,
        unselectedIcon = Icons.Outlined.CameraAlt,
    ),
    ENCYCLOPEDIA(
        route = Routes.ENCYCLOPEDIA,
        labelRes = R.string.nav_encyclopedia,
        selectedIcon = Icons.Filled.MenuBook,
        unselectedIcon = Icons.Outlined.MenuBook,
    ),
    HISTORY(
        route = Routes.HISTORY,
        labelRes = R.string.nav_history,
        selectedIcon = Icons.Filled.History,
        unselectedIcon = Icons.Outlined.History,
    ),
    SETTINGS(
        route = Routes.SETTINGS,
        labelRes = R.string.nav_settings,
        selectedIcon = Icons.Filled.Settings,
        unselectedIcon = Icons.Outlined.Settings,
    ),
}
