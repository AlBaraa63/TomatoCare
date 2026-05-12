package com.tomatocare.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.tomatocare.di.AppContainer
import com.tomatocare.ui.history.HistoryScreen
import com.tomatocare.ui.home.HomeScreen
import com.tomatocare.ui.result.ResultScreen
import com.tomatocare.ui.scan.ScanScreen
import com.tomatocare.ui.settings.SettingsScreen

@Composable
fun TomatoCareNavHost(container: AppContainer) {
    val navController = rememberNavController()
    NavHost(navController = navController, startDestination = Routes.HOME) {
        composable(Routes.HOME) {
            HomeScreen(
                container = container,
                onScanClick = { navController.navigate(Routes.SCAN) },
                onHistoryClick = { navController.navigate(Routes.HISTORY) },
                onSettingsClick = { navController.navigate(Routes.SETTINGS) },
                onLastScanClick = { id ->
                    navController.navigate(Routes.result(id))
                },
            )
        }
        composable(Routes.SCAN) {
            ScanScreen(
                container = container,
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
        composable(Routes.HISTORY) {
            HistoryScreen(
                container = container,
                onItemClick = { id -> navController.navigate(Routes.result(id)) },
                onBack = { navController.popBackStack() },
            )
        }
        composable(Routes.SETTINGS) {
            SettingsScreen(
                container = container,
                onBack = { navController.popBackStack() },
            )
        }
    }
}
