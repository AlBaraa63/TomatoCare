package com.tomatocare

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.tomatocare.data.model.Language
import com.tomatocare.ui.navigation.TomatoCareNavHost
import com.tomatocare.ui.theme.TomatoCareTheme
import com.tomatocare.utils.LocaleHelper
import kotlinx.coroutines.runBlocking

class MainActivity : ComponentActivity() {

    override fun attachBaseContext(newBase: Context) {
        // Load persisted language *synchronously* before Compose reads
        // resources, so the first frame is already in the right locale.
        // The settings store is a tiny file (single enum) — runBlocking
        // is acceptable here and avoids a "first-frame English flash".
        val app = newBase.applicationContext as? TomatoCareApp
        val lang: Language = runBlocking {
            app?.container?.settingsStore?.read()?.language ?: Language.ENGLISH
        }
        super.attachBaseContext(LocaleHelper.applyLocale(newBase, lang))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            TomatoCareTheme {
                TomatoCareNavHost(
                    container = (application as TomatoCareApp).container,
                )
            }
        }
    }
}
