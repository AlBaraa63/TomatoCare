plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "com.tomatocare"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.tomatocare"
        minSdk = 26              // NFR: app runs on Android 8.0 and above
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        // Lock app to LTR/RTL based on locale only (we use values-ar).
        vectorDrawables.useSupportLibrary = true
    }

    buildTypes {
        release {
            // Minify is critical to hit the 50 MB APK budget alongside the
            // ~15 MB .tflite asset. Treatments.json is ~80 KB so it doesn't
            // need shrinking.
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }

    // The Gradle toolchain delegates to foojay-resolver in settings.gradle.kts
    // to fetch JDK 17 if the host JDK is too new (e.g. JDK 26).
    kotlin {
        jvmToolchain(17)
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.14"
    }

    // .tflite is already float16-compressed; further APK compression hurts
    // load time without saving meaningful bytes. Keep it uncompressed so
    // it can be memory-mapped directly into the TFLite interpreter.
    androidResources {
        noCompress += listOf("tflite")
    }

    sourceSets {
        getByName("main") {
            java.srcDirs("src/main/kotlin")
        }
    }

    lint {
        // Mirror lint.xml: fail the build on hardcoded strings in layouts.
        abortOnError = true
        warningsAsErrors = false
    }

    packaging {
        resources {
            excludes += listOf(
                "META-INF/AL2.0", "META-INF/LGPL2.1",
                "META-INF/{AL2.0,LGPL2.1}",
                "META-INF/licenses/**",
            )
        }
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.activity.compose)

    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.material.icons.extended)
    debugImplementation(libs.androidx.compose.ui.tooling)
    debugImplementation(libs.androidx.compose.ui.test.manifest)

    implementation(libs.androidx.navigation.compose)

    implementation(libs.androidx.camera.core)
    implementation(libs.androidx.camera.camera2)
    implementation(libs.androidx.camera.lifecycle)
    implementation(libs.androidx.camera.view)
    implementation(libs.androidx.exifinterface)

    implementation(libs.tensorflow.lite)
    implementation(libs.tensorflow.lite.support)

    implementation(libs.kotlinx.serialization.json)
    implementation(libs.kotlinx.coroutines.android)

    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
}
