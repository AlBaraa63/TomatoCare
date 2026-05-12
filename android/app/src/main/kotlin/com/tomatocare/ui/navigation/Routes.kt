package com.tomatocare.ui.navigation

object Routes {
    const val HOME = "home"
    const val SCAN = "scan"
    const val RESULT = "result/{scanId}"
    const val HISTORY = "history"
    const val SETTINGS = "settings"

    fun result(scanId: Int) = "result/$scanId"
}
