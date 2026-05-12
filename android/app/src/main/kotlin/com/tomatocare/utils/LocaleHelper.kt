package com.tomatocare.utils

import android.content.Context
import android.content.res.Configuration
import com.tomatocare.data.model.Language
import java.util.Locale

/**
 * Returns a context wrapped with the user's chosen locale. Compose reads
 * resources from this wrapped context, so switching language at runtime
 * just needs an Activity.recreate() after writing to settings.
 *
 * Arabic is an RTL locale natively in Android — flipping the locale here
 * automatically triggers the framework's layout mirroring, no manual
 * layoutDirection swaps required (provided every layout uses
 * start/end padding rather than left/right).
 */
object LocaleHelper {

    fun applyLocale(context: Context, language: Language): Context {
        val locale = when (language) {
            Language.ARABIC -> Locale("ar")
            Language.ENGLISH -> Locale("en")
        }
        Locale.setDefault(locale)
        val config = Configuration(context.resources.configuration)
        config.setLocale(locale)
        config.setLayoutDirection(locale)
        return context.createConfigurationContext(config)
    }
}
