package com.tomatocare.ui.navigation

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.tomatocare.di.AppContainer
import com.tomatocare.ui.encyclopedia.EncyclopediaScreen
import com.tomatocare.ui.history.HistoryScreen
import com.tomatocare.ui.home.HomeScreen
import com.tomatocare.ui.result.ResultScreen
import com.tomatocare.ui.scan.ScanScreen
import com.tomatocare.ui.settings.SettingsScreen

@Composable
fun TomatoCareNavHost(container: AppContainer) {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    // Hide bottom bar on detail screens (ResultScreen)
    val showBottomBar = currentRoute != null &&
        currentRoute != Routes.RESULT

    Scaffold(
        bottomBar = {
            AnimatedVisibility(
                visible = showBottomBar,
                enter = slideInVertically(initialOffsetY = { it }),
                exit = slideOutVertically(targetOffsetY = { it }),
            ) {
                NavigationBar(
                    containerColor = MaterialTheme.colorScheme.surface,
                    tonalElevation = 2.dp,
                ) {
                    BottomNavItem.values().forEach { item ->
                        val selected = navBackStackEntry?.destination?.hierarchy
                            ?.any { it.route == item.route } == true
                        NavigationBarItem(
                            selected = selected,
                            onClick = {
                                navController.navigate(item.route) {
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = {
                                Icon(
                                    imageVector = if (selected) item.selectedIcon
                                    else item.unselectedIcon,
                                    contentDescription = stringResource(item.labelRes),
                                )
                            },
                            label = {
                                Text(
                                    text = stringResource(item.labelRes),
                                    style = MaterialTheme.typography.labelSmall,
                                )
                            },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = MaterialTheme.colorScheme.primary,
                                selectedTextColor = MaterialTheme.colorScheme.primary,
                                unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                indicatorColor = MaterialTheme.colorScheme.primaryContainer,
                            ),
                        )
                    }
                }
            }
        },
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Routes.HOME,
            modifier = Modifier.padding(innerPadding),
        ) {
            composable(Routes.HOME) {
                HomeScreen(
                    container = container,
                    onScanClick = {
                        navController.navigate(Routes.SCAN) {
                            launchSingleTop = true
                        }
                    },
                    onLastScanClick = { id ->
                        navController.navigate(Routes.result(id))
                    },
                )
            }
            composable(Routes.SCAN) {
                ScanScreen(
                    onResultReady = { scanId ->
                        navController.navigate(Routes.result(scanId)) {
                            popUpTo(Routes.HOME)
                        }
                    },
                    onBack = { navController.popBackStack() },
                )
            }
            composable(
                route = Routes.RESULT,
                arguments = listOf(navArgument("scanId") { type = NavType.IntType }),
            ) { backStackEntry ->
                val scanId = backStackEntry.arguments?.getInt("scanId") ?: -1
                ResultScreen(
                    container = container,
                    scanId = scanId,
                    onBack = { navController.popBackStack() },
                )
            }
            composable(Routes.ENCYCLOPEDIA) {
                EncyclopediaScreen(container = container)
            }
            composable(Routes.HISTORY) {
                HistoryScreen(
                    container = container,
                    onItemClick = { id -> navController.navigate(Routes.result(id)) },
                )
            }
            composable(Routes.SETTINGS) {
                SettingsScreen(container = container)
            }
        }
    }
}
