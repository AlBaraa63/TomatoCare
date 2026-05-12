package com.tomatocare

import android.app.Application
import com.tomatocare.di.AppContainer

/**
 * Single Application subclass. Holds the manual-DI [AppContainer] so all
 * ViewModels and screens reach singleton dependencies (storage, repo,
 * inference engine) through one well-known graph.
 *
 * No Hilt: a 10-screen capstone doesn't need a DI framework, and a manual
 * container is trivial to audit for the "loaded once" contracts that the
 * inference engine and treatment repository depend on.
 */
class TomatoCareApp : Application() {

    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
    }
}
