package com.tomatocare

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import com.tomatocare.data.model.Language
import com.tomatocare.ui.navigation.TomatoCareNavHost
import com.tomatocare.ui.theme.TomatoCareTheme
import com.tomatocare.utils.LocaleHelper
import kotlinx.coroutines.runBlocking

class MainActivity : ComponentActivity() {

    // The language the current Activity context was built with (in
    // attachBaseContext). A live change to a different language requires
    // recreate() so the new locale is applied to resources.
    private var appliedLanguage: Language = Language.ENGLISH

    override fun attachBaseContext(newBase: Context) {
        // Load persisted language *synchronously* before Compose reads
        // resources, so the first frame is already in the right locale.
        // The settings store is a tiny file (single enum) — runBlocking
        // is acceptable here and avoids a "first-frame English flash".
        // read() also seeds SettingsStore.settings so onCreate's collector
        // starts with the correct on-disk values (no default-English flash).
        val app = newBase.applicationContext as? TomatoCareApp
        val settings = runBlocking {
            app?.container?.settingsStore?.read() ?: com.tomatocare.data.model.UserSettings()
        }
        appliedLanguage = settings.language
        super.attachBaseContext(LocaleHelper.applyLocale(newBase, settings.language))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val app = application as TomatoCareApp
        setContent {
            // Collect the reactive settings flow. attachBaseContext already
            // seeded it from disk, so the initial value is correct.
            val settings by app.container.settingsStore.settings.collectAsState()

            // Theme switches live via recomposition. Language needs a full
            // recreate() because the locale is applied in attachBaseContext.
            LaunchedEffect(settings.language) {
                if (settings.language != appliedLanguage) {
                    recreate()
                }
            }

            TomatoCareTheme(themeMode = settings.themeMode) {
                TomatoCareNavHost(container = app.container)
            }
        }
    }
}
