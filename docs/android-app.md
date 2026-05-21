# Android App

This document is the complete reference for the TomatoCare Android app (Track B).
It covers every screen, component, inference pipeline, storage system, and
bilingual mechanism.

---

## Table of Contents

1. [Tech stack](#tech-stack)
2. [Build configuration](#build-configuration)
3. [Dependency injection](#dependency-injection)
4. [Screens and ViewModels](#screens-and-viewmodels)
   - [HomeScreen](#homescreen)
   - [ScanScreen](#scanscreen)
   - [ResultScreen](#resultscreen)
   - [HistoryScreen](#historyscreen)
   - [SettingsScreen](#settingsscreen)
5. [Navigation](#navigation)
6. [Inference pipeline](#inference-pipeline)
   - [TFLiteEngine](#tfliteengine)
   - [ImagePreprocessor](#imagepreprocessor)
   - [TomatoClasses](#tomatoclasses)
7. [Data layer](#data-layer)
   - [Data models](#data-models)
   - [ScanStorageManager](#scanstoragemanager)
   - [TreatmentRepository](#treatmentrepository)
   - [SettingsStore](#settingsstore)
   - [ScanExporter and ScanImporter](#scanexporter-and-scanimporter)
8. [UI components](#ui-components)
9. [Bilingual system](#bilingual-system)
10. [Unit tests](#unit-tests)
11. [Build commands](#build-commands)

---

## Tech stack

| Component | Library | Version |
|---|---|---|
| UI framework | Jetpack Compose + Material 3 | Compose 1.5.14 |
| Camera | CameraX | androidx.camera |
| Navigation | Navigation Compose | — |
| On-device ML | TensorFlow Lite | — |
| Serialization | kotlinx.serialization | — |
| Coroutines | kotlinx.coroutines | — |
| Image metadata | ExifInterface | androidx.exifinterface |
| Preferences | DataStore | — |
| DI | Hand-rolled (AppContainer) | — |
| Language | Kotlin | — |
| Min SDK | API 26 (Android 8.0) | — |
| Target SDK | API 34 (Android 14) | — |

---

## Build configuration

Key settings in `android/app/build.gradle.kts`:

```kotlin
android {
    compileSdk = 34
    defaultConfig {
        minSdk = 26
        targetSdk = 34
    }
    buildTypes {
        release {
            isMinifyEnabled = true   // ProGuard — critical for keeping APK ≤ 50 MB
            isShrinkResources = true
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    androidResources {
        noCompress += listOf("tflite")  // model is mmap'd — must not be compressed
    }
}
```

The `noCompress` directive is critical: if the `.tflite` is compressed inside
the APK the OS cannot memory-map it, forcing a full heap allocation (~6 MB) at
model load time.

---

## Dependency injection

`AppContainer` (in `di/AppContainer.kt`) is the single dependency container.
It is instantiated once in `TomatoCareApp.onCreate()` and accessed by
ViewModels through the `Application` reference.

```kotlin
class AppContainer(context: Context) {
    val settingsStore       = SettingsStore(context)
    val scanStorageManager  = ScanStorageManager(context)
    val scanExporter        = ScanExporter(context, scanStorageManager)
    val scanImporter        = ScanImporter(context, scanStorageManager)
    val treatmentRepository = TreatmentRepository(context)
    val imagePreprocessor   = ImagePreprocessor()
    val tfliteEngine        = TFLiteEngine(context, imagePreprocessor)

    init {
        // Warm-up: fire one inference on a blank bitmap so the first real scan
        // doesn't pay the JIT + native library loading cost.
        scope.launch(SupervisorJob()) {
            tfliteEngine.classify(Bitmap.createBitmap(224, 224, Bitmap.Config.ARGB_8888),
                                  GrowingMethod.OPEN_FIELD)
        }
    }
}
```

The warm-up uses `SupervisorJob` so a warm-up failure (extremely unlikely)
does not crash the app.

---

## Screens and ViewModels

### HomeScreen

**File:** `ui/home/HomeScreen.kt`, `ui/home/HomeViewModel.kt`

The landing screen. Shown immediately after launch.

**What it displays:**
- App logo and tagline ("Identify tomato leaf diseases — fully offline.")
- Three navigation buttons: Scan a leaf, View history, Settings
- **Last scan card** (if any scan exists): shows the primary condition name,
  stress badge, and timestamp. Tapping it navigates to that scan's result.

**ViewModel state:**
```kotlin
data class HomeUiState(
    val lastScan: ScanRecord? = null,
)
```

`HomeViewModel.refresh()` is called every time the screen is (re)composed —
this ensures the last scan card updates after a new scan or deletion.

---

### ScanScreen

**File:** `ui/scan/ScanScreen.kt`, `ui/scan/ScanViewModel.kt`

Manages the full capture-to-diagnosis flow.

**UI states:**

```kotlin
sealed interface ScanUiState {
    data object Idle : ScanUiState                      // camera preview
    data object Processing : ScanUiState                // spinner while inferring
    data class LowConfidence(                           // confidence < threshold
        val output: InferenceOutput,
        val savedScanId: Int,
    ) : ScanUiState
    data class Success(                                 // confidence ≥ threshold
        val output: InferenceOutput,
        val savedScanId: Int,
    ) : ScanUiState
    data class Error(val message: String) : ScanUiState
}
```

**Flow on capture:**

1. CameraX `ImageCapture.takePicture()` returns a `Bitmap`.
2. `ScanViewModel.onImageCaptured(bitmap)` runs on a background coroutine:
   - Reads `growingMethod` and `confidenceThreshold` from `SettingsStore`.
   - Calls `TFLiteEngine.classify(bitmap, growingMethod, threshold)`.
   - Saves the bitmap thumbnail to `filesDir/images/<scanId>.jpg`.
   - Looks up treatments from `TreatmentRepository`.
   - Builds and saves a `ScanRecord` via `ScanStorageManager`.
   - Emits `LowConfidence` or `Success` state depending on the top result's confidence.
3. If `LowConfidence`: shows `LowConfidenceWarning` component with Retake / Show Anyway.
4. If `Success` or "Show Anyway" chosen: navigates to `ResultScreen(scanId)`.

**Gallery import:**

Users can also pick an image from gallery via `ActivityResultContracts.PickVisualMedia`.
The picked image goes through the same `onImageCaptured()` flow.

---

### ResultScreen

**File:** `ui/result/ResultScreen.kt`, `ui/result/ResultViewModel.kt`

Displays the full diagnosis for a given `scanId`.

**ViewModel state:**
```kotlin
data class ResultUiState(
    val isLoading: Boolean = true,
    val record: ScanRecord? = null,
    val selectedMethod: GrowingMethod = GrowingMethod.OPEN_FIELD,
    val treatments: List<Treatment> = emptyList(),
    val language: Language = Language.ENGLISH,
    val errorMessage: String? = null,
)
```

**What it displays:**
- Primary condition: English name + Arabic name (bilingual)
- Stress badge (BIOTIC / ABIOTIC)
- Severity chip (LOW / MEDIUM / HIGH / CRITICAL)
- Confidence percentage (e.g. "87.3%")
- **Growing method selector:** radio buttons (Greenhouse / Open Field /
  Hydroponic / Saline Soil). Changing the method re-filters treatments
  via `ResultViewModel.onMethodSelected(method)`.
- **Treatment cards:** one per treatment for the selected method. Each card
  shows treatment type (Chemical/Cultural/Biological), urgency level, and
  expandable full recommendation text in the active language.
- **Other possibilities:** collapsible section showing the 2nd and 3rd
  ranked diagnoses with their confidence percentages.

---

### HistoryScreen

**File:** `ui/history/HistoryScreen.kt`, `ui/history/HistoryViewModel.kt`

A scrollable list of all past scans, newest first.

**Each row shows:**
- Thumbnail image (loaded asynchronously; falls back to leaf icon if image
  file is missing — handles orphaned records gracefully)
- Primary condition name (in the active language)
- Stress badge
- Timestamp (formatted as "May 19, 2025 · 14:30")
- Delete button (trash icon)

**Delete with undo:**

Tapping the trash icon removes the record and its image file from disk, then
shows a Snackbar with "Undo". If the user taps Undo within 5 seconds,
`HistoryViewModel.undoDelete(record)` restores the record.

---

### SettingsScreen

**File:** `ui/settings/SettingsScreen.kt`, `ui/settings/SettingsViewModel.kt`

**Sections:**

**Language:**
Radio buttons for English / Arabic. Changing language calls
`LocaleHelper.setLocale(context, language)` and then recreates the Activity
so the entire UI re-renders in the new language and layout direction.

**Default growing method:**
Radio buttons for Greenhouse / Open Field / Hydroponic / Saline Soil.
Saved to `SettingsStore` (DataStore). Used as the default in `ScanViewModel`
when processing a new scan.

**Data management:**

| Action | Implementation |
|---|---|
| Export history | `ActivityResultContracts.CreateDocument("application/json")` → `ScanExporter.export(uri)` |
| Import history | `ActivityResultContracts.OpenDocument(["application/json"])` → `ScanImporter.import(uri)` with confirmation dialog |
| Delete all history | Confirmation dialog → `ScanStorageManager.deleteAll()` |

Events emitted to show Snackbar feedback: `ExportFinished(count)`,
`ImportFinished(count)`, `HistoryDeleted`, `LanguageChanged`.

---

## Navigation

**File:** `ui/navigation/TomatoCareNavHost.kt`

Single `NavController` with five destinations:

```
Routes.HOME         → HomeScreen
Routes.SCAN         → ScanScreen
Routes.RESULT       → ResultScreen  (requires Int arg: scanId)
Routes.HISTORY      → HistoryScreen
Routes.SETTINGS     → SettingsScreen
```

After a successful scan, the back-stack is cleared up to (and including)
`HomeScreen` before pushing `ResultScreen`. This means pressing Back from
the result goes home — not back to the camera, which would be disorienting.

```kotlin
navController.navigate(Routes.result(scanId)) {
    popUpTo(Routes.HOME) { inclusive = false }
}
```

---

## Inference pipeline

### TFLiteEngine

**File:** `inference/TFLiteEngine.kt`

```kotlin
suspend fun classify(
    bitmap: Bitmap,
    growingMethod: GrowingMethod,
    confidenceThreshold: Float = 0.60f,
): InferenceOutput
```

**Initialization:**
- Memory-maps `tomatocare_model_float16.tflite` from the APK's `assets/`
  directory using `MappedByteBuffer`. No heap allocation.
- Sets `numThreads = 4` for the TFLite interpreter.

**Classification steps:**
1. Delegate to `ImagePreprocessor.preprocess(bitmap)` → `ByteBuffer`.
2. Set input tensor from `ByteBuffer`.
3. Call `interpreter.run()`.
4. Read output tensor: `FloatArray` of size 11 (one probability per class, including Tomato_NotALeaf).
5. Map each index to `TomatoClasses.CLASS_NAMES[i]`.
6. Sort descending → take top 3.
7. Apply severity heuristic based on the top result's confidence:

   | Confidence | Severity adjustment |
   |---|---|
   | ≥ 90% | Use the class's base severity |
   | 75–90% | One level lower than base |
   | 60–75% | Two levels lower than base |
   | < 60% | Always LOW (also sets `isLowConfidence = true`) |

8. Return `InferenceOutput(topResults, inferenceTimeMs, isLowConfidence)`.

### ImagePreprocessor

**File:** `inference/ImagePreprocessor.kt`

```kotlin
fun preprocess(bitmap: Bitmap): ByteBuffer
```

1. **EXIF rotation (API < 28 only):** On API 28+, `ImageDecoder` applies EXIF
   rotation automatically. On older APIs this must be done manually with
   `ExifInterface`.
2. **Resize:** Scale bitmap to 224 × 224 if needed (uses `Bitmap.createScaledBitmap`).
3. **Normalize:** Extract each pixel's R, G, B channels as integers [0, 255]
   and write as float32 [0.0, 1.0] into a direct `ByteBuffer`.
   - Buffer size: `224 × 224 × 3 × 4 bytes = 602,112 bytes` (~590 KB)
   - Direct buffer (not heap-backed) for zero-copy transfer to the TFLite
     interpreter's native memory.

### TomatoClasses

**File:** `inference/TomatoClasses.kt`

```kotlin
const val MODEL_ASSET = "tomatocare_model_float16.tflite"

val CLASS_NAMES: List<String> = listOf(
    "Tomato_Bacterial_spot",                        // 0
    "Tomato_Early_blight",                          // 1
    "Tomato_healthy",                               // 2
    "Tomato_Late_blight",                           // 3
    "Tomato_Leaf_Mold",                             // 4
    "Tomato_Septoria_leaf_spot",                    // 5
    "Tomato_Spider_mites_Two_spotted_spider_mite",  // 6
    "Tomato_Target_Spot",                           // 7
    "Tomato_Yellow_Leaf_Curl_Virus",                // 8
    "Tomato_mosaic_virus",                          // 9
    "Tomato_NotALeaf",                              // 10 (OOD reject)
)
```

This list is the **contract** between the ML pipeline and the Android app:
index 0 in the model's output tensor must map to `Tomato_Bacterial_spot`, and
so on. The order is alphabetical — matching the order TF Keras assigns when
using `image_dataset_from_directory`. `ClassNamesTest` verifies this at build
time.

---

## Data layer

### Data models

All models are `@Serializable` Kotlin data classes (kotlinx.serialization).
They are stored as human-readable JSON with enum values as name strings.

**`ScanRecord`** — one scan session:
```kotlin
@Serializable
data class ScanRecord(
    val scanId: Int,
    val imagePath: String,        // absolute path in filesDir
    val timestamp: String,        // ISO-8601 UTC
    val growingMethod: GrowingMethod,
    val modelVersion: String,     // "2.0.0"
    val results: List<DiagnosisResult>,
) {
    val primary: DiagnosisResult?
        get() = results.firstOrNull { it.isPrimary } ?: results.firstOrNull()
}
```

**`DiagnosisResult`** — one ranked result within a scan:
```kotlin
@Serializable
data class DiagnosisResult(
    val resultId: Int,
    val conditionId: String,      // stable key for TreatmentRepository lookup
    val conditionNameEn: String,
    val conditionNameAr: String,
    val confidence: Double,       // 0.0–1.0
    val isPrimary: Boolean,
    val stressType: StressType,
    val severityLevel: SeverityLevel,
    val treatments: List<Treatment>,
)
```

**`Treatment`** — one treatment recommendation:
```kotlin
@Serializable
data class Treatment(
    val treatmentId: Int,
    val growingMethod: GrowingMethod,
    val treatmentType: TreatmentType,   // CHEMICAL | CULTURAL | BIOLOGICAL
    val urgencyLevel: UrgencyLevel,
    val recommendationEn: String,
    val recommendationAr: String,
)
```

**Enums:**
```
StressType:    BIOTIC | ABIOTIC
SeverityLevel: LOW | MEDIUM | HIGH | CRITICAL
GrowingMethod: GREENHOUSE | OPEN_FIELD | HYDROPONIC | SALINE_SOIL
Language:      ENGLISH | ARABIC
TreatmentType: CHEMICAL | CULTURAL | BIOLOGICAL
UrgencyLevel:  LOW | MEDIUM | HIGH | CRITICAL
```

### ScanStorageManager

**File:** `data/storage/ScanStorageManager.kt`

Reads and writes `filesDir/scan_history.json`. All operations are on
`Dispatchers.IO`.

```kotlin
suspend fun save(record: ScanRecord)    // append-or-update
suspend fun loadAll(): List<ScanRecord> // newest first
suspend fun delete(scanId: Int)         // removes record + image file
suspend fun deleteAll()
```

**Atomic write strategy:**
1. Load all existing records.
2. Append/replace the new record.
3. Encode the updated list to JSON.
4. Write to a temp file: `scan_history.json.tmp`
5. Rename temp → `scan_history.json` (atomic on Android's ext4 filesystem).

A crash mid-write leaves the `.tmp` file behind but the canonical file intact.

### TreatmentRepository

**File:** `data/repository/TreatmentRepository.kt`

Loads `assets/treatments.json` once at construction time and keeps the result
as an immutable map keyed by `conditionId`. All subsequent lookups are
in-memory.

```kotlin
fun getTreatments(conditionId: String, method: GrowingMethod): List<Treatment>
```

The `treatments.json` file is a 32 KB JSON array of treatment objects. It is
the source of all treatment recommendations and is bundled inside the APK.

### SettingsStore

**File:** `data/repository/SettingsStore.kt`

A DataStore-backed preferences wrapper.

```kotlin
val growingMethod: Flow<GrowingMethod>    // default: OPEN_FIELD
val language: Flow<Language>              // default: ENGLISH
val confidenceThreshold: Flow<Float>      // default: 0.60

suspend fun setGrowingMethod(method: GrowingMethod)
suspend fun setLanguage(language: Language)
```

### ScanExporter and ScanImporter

**Files:** `data/storage/ScanExporter.kt`, `data/storage/ScanImporter.kt`

Both use Android's Storage Access Framework (SAF). The app never sees raw
filesystem paths — only a `Uri` provided by the system file picker.

**Export:**
```kotlin
suspend fun export(targetUri: Uri): ExportResult
// Loads all records, encodes to pretty-printed JSON (2-space indent),
// writes to the SAF Uri.
// Returns ExportResult.Success(recordCount) or ExportResult.Failure(message).
```

**Import:**
```kotlin
suspend fun import(sourceUri: Uri): ImportResult
// Reads JSON from the SAF Uri, decodes to ScanHistory, merges with existing
// records (deduplication by scanId).
// Returns ImportResult.Success(importedCount) or ImportResult.Failure(message).
```

---

## UI components

### TreatmentCard

**File:** `ui/components/TreatmentCard.kt`

An expandable card for a single treatment recommendation.

- Collapsed: shows treatment type chip (CHEMICAL / CULTURAL / BIOLOGICAL),
  urgency tag, and expand/collapse arrow.
- Expanded: shows full recommendation text in the active language.
- Uses `AnimatedVisibility` for a smooth expand/collapse animation.

### StressBadge

**File:** `ui/components/StressBadge.kt`

A small colored chip:
- `BIOTIC` → green background
- `ABIOTIC` → amber/orange background

Displayed on the HomeScreen last-scan card, HistoryScreen rows, and
ResultScreen.

### LowConfidenceWarning

**File:** `ui/components/LowConfidenceWarning.kt`

Shown when `TFLiteEngine` returns `isLowConfidence = true` (confidence below
the configured threshold, default 0.60).

- Orange-tinted card with warning icon
- Explanation: the leaf may be out of focus, too dark, or not a leaf at all
- Two buttons:
  - **Retake** — resets `ScanViewModel` state back to `Idle` (camera)
  - **Show Anyway** — proceeds to `ResultScreen` with the low-confidence result

### SeverityChip

**File:** `ui/components/SeverityChip.kt`

Color-coded chip for the four severity levels:
- `LOW` → grey
- `MEDIUM` → yellow
- `HIGH` → orange
- `CRITICAL` → red

---

## Bilingual system

### String resources

All user-visible strings are in two resource files:

- `res/values/strings.xml` — English (default locale)
- `res/values-ar/strings.xml` — Arabic

Android's resource system selects the correct file based on the active locale.
Compose accesses them via `stringResource(R.string.key)`.

### Locale switching

`LocaleHelper.setLocale(context, Language.ARABIC)` updates the app's
configuration to use the `ar` locale and triggers an Activity restart. After
restart, all `stringResource()` calls return Arabic strings, and the layout
system automatically mirrors RTL (right-to-left) for all standard Compose
layouts.

### Bilingual data

Condition names and treatment recommendations are stored in both languages
inside `treatments.json` and in every `DiagnosisResult` object:
- `conditionNameEn` / `conditionNameAr`
- `recommendationEn` / `recommendationAr`

The active language determines which field `ResultScreen` and `HistoryScreen`
display.

> **Note:** Arabic treatment text was AI-generated and is flagged for review
> by a native-speaking agronomist before production deployment.

---

## Unit tests

**File:** `android/app/src/test/kotlin/com/tomatocare/ClassNamesTest.kt`

```kotlin
@Test fun classNamesAreAlphabeticallySorted()
@Test fun classNameCountMatchesConfig()
@Test fun classNamesMatchTrainingConfig()
```

These tests verify that `TomatoClasses.CLASS_NAMES` stays in alphabetical
order and contains exactly the classes defined in `training_config.yaml`. A
mismatch would cause silent misclassification (wrong label for every output
tensor index) — this is caught at build time, not at runtime.

Run:
```bash
cd android
./gradlew :app:test
```

---

## Build commands

```bash
cd android

# Debug build (signed with debug key, installs on any device)
./gradlew :app:assembleDebug

# Install debug APK on connected device
./gradlew :app:installDebug

# Release build (requires keystore configuration in build.gradle.kts)
./gradlew :app:assembleRelease

# Unit tests only (no device needed)
./gradlew :app:test

# Full check: tests + lint + build
./gradlew :app:check :app:assembleDebug
```

APK output locations:
```
android/app/build/outputs/apk/debug/app-debug.apk
android/app/build/outputs/apk/release/app-release.apk
```
