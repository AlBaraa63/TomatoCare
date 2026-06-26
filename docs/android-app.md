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
   - [EncyclopediaScreen](#encyclopediascreen)
   - [HistoryScreen](#historyscreen)
   - [SettingsScreen](#settingsscreen)
5. [The feedback flywheel](#the-feedback-flywheel)
6. [Navigation](#navigation)
7. [Inference pipeline](#inference-pipeline)
   - [TFLiteEngine](#tfliteengine)
   - [ImagePreprocessor](#imagepreprocessor)
   - [TomatoClasses](#tomatoclasses)
8. [Data layer](#data-layer)
   - [Data models](#data-models)
   - [ScanStorageManager](#scanstoragemanager)
   - [TreatmentRepository](#treatmentrepository)
   - [ConditionRepository](#conditionrepository)
   - [SettingsStore](#settingsstore)
   - [ScanExporter and ScanImporter](#scanexporter-and-scanimporter)
   - [TrainingDataExporter](#trainingdataexporter)
9. [Theming and dark mode](#theming-and-dark-mode)
10. [UI components](#ui-components)
11. [Bilingual system](#bilingual-system)
12. [Unit tests](#unit-tests)
13. [Build commands](#build-commands)

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

The `noCompress` directive is critical: if the `.tflite` files are compressed
inside the APK the OS cannot memory-map them, forcing full heap allocations
(~9.87 MB across the three cascade models) at load time.

---

## Dependency injection

`AppContainer` (in `di/AppContainer.kt`) is the single dependency container.
It is instantiated once in `TomatoCareApp.onCreate()` and accessed by
ViewModels through the `Application` reference.

```kotlin
class AppContainer(context: Context) {
    val settingsStore        = SettingsStore(context)
    val scanStorageManager   = ScanStorageManager(context)
    val scanExporter         = ScanExporter(context, scanStorageManager)
    val scanImporter         = ScanImporter(context, scanStorageManager)
    val trainingDataExporter = TrainingDataExporter(context, scanStorageManager)
    val treatmentRepository  = TreatmentRepository(context)
    val conditionRepository  = ConditionRepository(context)   // Encyclopedia + feedback
    val imagePreprocessor    = ImagePreprocessor()
    val tfliteEngine         = TFLiteEngine(context, imagePreprocessor, treatmentRepository)

    init {
        // Warm-up: fire one inference on a blank bitmap so the first real scan
        // doesn't pay the JIT + native library loading cost.
        scope.launch(SupervisorJob()) {
            tfliteEngine.classify(Bitmap.createBitmap(224, 224, Bitmap.Config.ARGB_8888),
                                  GrowingMethod.GREENHOUSE)
        }
    }
}
```

`conditionRepository` and `trainingDataExporter` were added alongside the
Encyclopedia screen and the [feedback flywheel](#the-feedback-flywheel).

The warm-up uses `SupervisorJob` so a warm-up failure (extremely unlikely)
does not crash the app.

---

## Screens and ViewModels

### HomeScreen

**File:** `ui/home/HomeScreen.kt`, `ui/home/HomeViewModel.kt`

The landing screen — a **dashboard** that summarises the user's scan history at
a glance. Shown immediately after launch (and is the bottom-nav start
destination).

**What it displays:**
- **Hero card** — a gradient banner with the app title, tagline, and a "Scan a
  leaf" call-to-action. Tapping anywhere on it opens the camera.
- **Stats row** — three `StatCard`s: total scans, **health rate** (% of scans
  whose primary diagnosis is `healthy`), and number of distinct conditions seen.
- **Last scan card** (if any scan exists): thumbnail, primary condition name
  (in the active language), a `ConfidenceBar`, severity chip, and timestamp.
  Tapping it opens that scan's result.
- **Disease distribution** — a `SimpleBarChart` of the user's three most
  frequent conditions (labels localised to the active language).
- **Onboarding dialog** — a one-time how-to-use dialog shown on first launch
  (gated by `UserSettings.hasSeenOnboarding`).

**ViewModel state:**
```kotlin
data class HomeUiState(
    val isLoading: Boolean = true,
    val lastScan: ScanRecord? = null,
    val totalScans: Int = 0,
    val showOnboarding: Boolean = false,
    val distinctConditions: Int = 0,
    val healthRate: Int = 0,                       // % primary == "healthy"
    val topConditions: List<Pair<String, Int>> = emptyList(),
    val language: Language = Language.ENGLISH,
)
```

`HomeViewModel.refresh()` is called every time the screen is entered
(`LaunchedEffect`), so the dashboard updates after a new scan or deletion.

> The health-rate metric keys on the canonical `conditionId` `"healthy"` (the
> Stage-3 class key), not a display name — the value must match
> `assets/treatments.json`.

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
- Header card: thumbnail, primary condition name in the active language,
  timestamp, the on-device inference time ("Diagnosed on-device in *N* ms" —
  NFR-02 evidence), stress badge, severity chip, and a circular
  **`ConfidenceGauge`** showing the top confidence.
- **Growing method selector:** chips (Greenhouse / Open Field / Hydroponic /
  Saline Soil). Changing the method re-filters treatments via
  `ResultViewModel.onMethodSelected(method)`.
- **Treatment cards:** one per treatment for the selected method. Each card
  shows treatment type (Chemical/Cultural/Biological), urgency level, and
  expandable full recommendation text in the active language.
- **Feedback card:** the [feedback flywheel](#the-feedback-flywheel) prompt —
  "Was this correct?". Captured once per scan, then becomes a thank-you summary.
- **Other possibilities:** the 2nd and 3rd ranked diagnoses with `ConfidenceBar`
  and percentage, names localised to the active language.

---

### EncyclopediaScreen

**File:** `ui/encyclopedia/EncyclopediaScreen.kt`, `ui/encyclopedia/EncyclopediaViewModel.kt`

A browsable, **searchable reference** of all conditions the app knows about —
independent of whether the user has scanned them. Backed by
[`ConditionRepository`](#conditionrepository) (which reads `treatments.json`).

**What it displays:**
- A search field that filters conditions by English **or** Arabic name.
- A `LazyColumn` of expandable cards. Collapsed: condition name + the other
  language as a subtitle. Expanded: stress badge, default severity chip, and
  the full set of `TreatmentCard`s for that condition.

**ViewModel state:**
```kotlin
data class EncyclopediaUiState(
    val allConditions: List<ConditionInfo> = emptyList(),
    val filteredConditions: List<ConditionInfo> = emptyList(),
    val searchQuery: String = "",
    val language: Language = Language.ENGLISH,
)
```

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

**Appearance — language:**
Chips for English / العربية. Changing language writes `UserSettings.language`,
which `MainActivity` observes via the reactive `SettingsStore.settings` flow and
applies by recreating the Activity (so resources reload in the new locale and
layout direction). See [Bilingual system](#bilingual-system).

**Appearance — theme mode:**
Chips for Light / Dark / System. Writes `UserSettings.themeMode`; the theme
switches **live** (no restart) because `MainActivity` drives `TomatoCareTheme`
from the same reactive flow. See [Theming and dark mode](#theming-and-dark-mode).

**Default growing method:**
A `GrowingMethodSelector` (Greenhouse / Open Field / Hydroponic / Saline Soil).
Saved to `SettingsStore`. Used as the default in `ScanViewModel` for new scans.

**Data management:**

| Action | Implementation |
|---|---|
| Export history | `ActivityResultContracts.CreateDocument("application/json")` → `ScanExporter.export(uri)` |
| Import history | `ActivityResultContracts.OpenDocument(["application/json"])` → `ScanImporter.import(uri)` with confirmation dialog |
| **Export training data** | `CreateDocument("application/zip")` → [`TrainingDataExporter.export(uri)`](#trainingdataexporter) — the feedback-flywheel ZIP |
| Delete all history | Confirmation dialog → `ScanStorageManager.deleteAll()` |

Events emitted to show Snackbar feedback: `ExportFinished`, `ImportFinished`,
`HistoryDeleted`, `LanguageChanged`.

---

## The feedback flywheel

> **This is the app's strategic feature.** The ML evaluation measures a lab→field
> accuracy gap (97.19% lab end-to-end vs 77.2% field on PlantDoc, per
> `ml/reports/eval_deployed.json`). The report's plan to close that gap is a
> **real-world data flywheel**: collect genuine field images with verified
> labels, then retrain. That flywheel is **implemented in the app**, fully
> offline — nothing is uploaded; the user owns and exports the data.

**The loop:**

1. **Capture** — every scan is saved as a `ScanRecord` (image + prediction).
2. **Confirm** — on the result screen, the `FeedbackCard` asks *"Was this
   correct?"*. The user taps **Yes** (the prediction becomes the verified label)
   or **No** and picks the true condition from a dropdown of all 11 classes.
   The answer is stored as `ScanRecord.feedback: ScanFeedback?` and is captured
   **once per scan** (the card then shows a read-only thank-you).
3. **Export** — Settings → *Export training data* runs
   [`TrainingDataExporter`](#trainingdataexporter), which bundles every
   feedback-labelled scan into a ZIP, **grouped by true label**, with a
   `manifest.json`. The folder layout is the exact shape the ML training farm
   ingests (`integrate_plantdoc.py`).
4. **Retrain** — the exported ZIP drops into the ML pipeline as new field data.

```kotlin
@Serializable
data class ScanFeedback(
    val wasCorrect: Boolean,
    val correctedConditionId: String? = null,  // true class when wasCorrect == false
    val timestamp: String,                      // ISO-8601 UTC
)
```

The true label written to the export is the user's correction when they marked
the diagnosis wrong, otherwise the model's own primary prediction (a confirmed
label). Feedback is submitted via `ResultViewModel.submitFeedback(wasCorrect, conditionId?)`.

---

## Navigation

**File:** `ui/navigation/TomatoCareNavHost.kt`, `ui/navigation/Routes.kt`

A single `NavController` with six destinations, five of which are reachable from
a **bottom navigation bar** (`BottomNavItem`):

```
Routes.HOME          → HomeScreen        ┐
Routes.SCAN          → ScanScreen        │
Routes.ENCYCLOPEDIA  → EncyclopediaScreen ├─ bottom-nav tabs
Routes.HISTORY       → HistoryScreen     │
Routes.SETTINGS      → SettingsScreen    ┘
Routes.RESULT        → ResultScreen  (detail; requires Int arg: scanId)
```

The bottom bar is **hidden on `ResultScreen`** (a detail screen pushed on top,
with its own back arrow). Tab switching uses `saveState`/`restoreState` +
`launchSingleTop` so each tab keeps its scroll position.

After a successful scan, the back-stack pops up to `HomeScreen` before pushing
`ResultScreen`, so Back from the result goes home — not back to the camera.

```kotlin
navController.navigate(Routes.result(scanId)) {
    popUpTo(Routes.HOME)
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
- Memory-maps three TFLite models from the APK's `assets/` directory:
  `stage1_leaf_float16.tflite` (1.92 MB), `stage2_tomato_float16.tflite`
  (1.92 MB), and `stage3_disease_float16.tflite` (6.03 MB). No heap allocation.
- Sets `numThreads = 4` for each TFLite interpreter.

**Classification steps:**
1. Delegate to `ImagePreprocessor.preprocess(bitmap)` → `ByteBuffer`.
2. **Stage 1 — leaf gate:** run leaf model; reject if not a leaf.
3. **Stage 2 — tomato gate:** run tomato model; reject if not a tomato leaf.
4. **Stage 3 — disease classifier:** run disease model.
5. Read output tensor: `FloatArray` of size 11 (10 diseases + healthy).
6. Map each index to class name (alphabetical order).
7. Sort descending → take top 3.
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

The deployed cascade uses three model assets and an 11-class disease label set
(10 diseases + healthy). OOD rejection is handled by the gate models, not by a
reject class in the disease classifier.

```kotlin
// Cascade model assets
const val STAGE1_ASSET = "stage1_leaf_float16.tflite"     // 1.92 MB — leaf gate
const val STAGE2_ASSET = "stage2_tomato_float16.tflite"   // 1.92 MB — tomato gate
const val STAGE3_ASSET = "stage3_disease_float16.tflite"  // 6.03 MB — disease classifier

// Disease classifier class names (Stage 3 output, alphabetical)
val CLASS_NAMES: List<String> = listOf(
    "bacterial_spot",             // 0
    "early_blight",               // 1
    "healthy",                    // 2
    "late_blight",                // 3
    "leaf_mold",                  // 4
    "mosaic_virus",               // 5
    "powdery_mildew",             // 6
    "septoria_leaf_spot",         // 7
    "spider_mites",               // 8
    "target_spot",                // 9
    "yellow_leaf_curl_virus",     // 10
)
```

This list is the **contract** between the ML pipeline and the Android app:
index 0 in the Stage 3 output tensor must map to `bacterial_spot`, and so on.
The order is alphabetical — matching `ml/reports/eval_deployed.json`.
`ClassNamesTest` verifies this at build time.

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
    val feedback: ScanFeedback? = null,   // flywheel; null until the user answers
    val inferenceTimeMs: Long? = null,    // total cascade time; NFR-02 evidence, shown on Result
) {
    val primary: DiagnosisResult?
        get() = results.firstOrNull { it.isPrimary } ?: results.firstOrNull()
}

@Serializable
data class ScanFeedback(             // see "The feedback flywheel"
    val wasCorrect: Boolean,
    val correctedConditionId: String? = null,
    val timestamp: String,
)
```

The `feedback` field defaults to `null`, so adding it did not break existing
on-disk history (the JSON config uses `ignoreUnknownKeys` + `encodeDefaults`).

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
StressType:    BIOTIC | ABIOTIC  (static metadata — NOT a learned prediction)
SeverityLevel: LOW | MEDIUM | HIGH | CRITICAL
GrowingMethod: GREENHOUSE | OPEN_FIELD | HYDROPONIC | SALINE_SOIL
Language:      ENGLISH | ARABIC
ThemeMode:     LIGHT | DARK | SYSTEM
TreatmentType: CHEMICAL | CULTURAL | BIOLOGICAL
UrgencyLevel:  LOW | MEDIUM | HIGH | CRITICAL
```

**`UserSettings`** — persisted app preferences (see [SettingsStore](#settingsstore)):
```kotlin
@Serializable
data class UserSettings(
    val language: Language = Language.ENGLISH,
    val defaultGrowingMethod: GrowingMethod = GrowingMethod.OPEN_FIELD,
    val confidenceThreshold: Float = 0.60f,
    val hasSeenOnboarding: Boolean = false,   // gates the one-time Home dialog
    val themeMode: ThemeMode = ThemeMode.SYSTEM,
)
```

**`ConditionInfo` / `TreatmentsCatalog`** — the parsed shape of
`assets/treatments.json` (used by [TreatmentRepository](#treatmentrepository)
and [ConditionRepository](#conditionrepository)): a `conditionId`, `classLabel`,
bilingual names, `stressType`, `severityDefault`, and a `treatments` list.

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

### ConditionRepository

**File:** `data/repository/ConditionRepository.kt`

Loads `assets/treatments.json` once and exposes its conditions for the
[Encyclopedia](#encyclopediascreen) and the [feedback](#the-feedback-flywheel)
dropdown. Distinct from `TreatmentRepository` (which is lookup-by-id for
inference); this one serves whole-catalog browsing.

```kotlin
fun getAllConditions(): List<ConditionInfo>          // sorted by English name
fun getCondition(conditionId: String): ConditionInfo?
```

### SettingsStore

**File:** `data/storage/SettingsStore.kt`

A flat-JSON store (`filesDir/settings.json`), **not** DataStore — the codebase
standardises on kotlinx.serialization and settings is a single object with no
migrations. It uses the same atomic temp-file-then-rename write discipline as
`ScanStorageManager`.

```kotlin
val settings: StateFlow<UserSettings>     // reactive — seeded by read(), updated by write()

suspend fun read(): UserSettings          // loads from disk, seeds the flow
suspend fun write(settings: UserSettings) // atomic write, updates the flow
```

> **Why the `StateFlow` matters.** `MainActivity` collects `settings` to drive
> the theme and locale. Without a reactive stream, the in-app theme/language
> toggle would only take effect after an app restart (this was a real bug —
> the store originally exposed only a one-shot `read()`). Theme now switches
> live; a language change triggers `Activity.recreate()` to reload resources.

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

### TrainingDataExporter

**File:** `data/storage/TrainingDataExporter.kt`

The export half of the [feedback flywheel](#the-feedback-flywheel). Bundles
every scan that carries `feedback` into a single ZIP at a SAF-chosen URI:

```
<true_label>/scan_<id>.jpg     ← images grouped by their verified label
manifest.json                  ← per-image record (label, predicted, confidence, …)
```

```kotlin
suspend fun export(targetUri: Uri): TrainingExportResult
//   Success(imageCount, labelCount) | Empty (no feedback yet) | Failure(message)
```

The true label is the user's correction when they marked the diagnosis wrong,
otherwise the model's confirmed prediction. Labels are canonical `conditionId`
keys, so the folder layout drops straight into the ML training farm (the same
shape `integrate_plantdoc.py` expects). Fully offline — writes only to the
user-selected document.

---

## Theming and dark mode

**Files:** `ui/theme/Theme.kt`, `ui/theme/Color.kt`, `ui/theme/Type.kt`

`TomatoCareTheme` is a Material 3 theme with explicit light and dark color
schemes (a clinical-blue / healthy-green palette), shared shapes, and a custom
typography scale. It takes a `ThemeMode`:

```kotlin
@Composable
fun TomatoCareTheme(themeMode: ThemeMode = ThemeMode.SYSTEM, content: @Composable () -> Unit) {
    val darkTheme = when (themeMode) {
        ThemeMode.LIGHT  -> false
        ThemeMode.DARK   -> true
        ThemeMode.SYSTEM -> isSystemInDarkTheme()
    }
    val colorScheme = if (darkTheme) DarkColors else LightColors
    MaterialTheme(colorScheme, TomatoCareTypography, TomatoCareShapes, content)
}
```

`MainActivity` reads `themeMode` from the reactive
[`SettingsStore.settings`](#settingsstore) flow, so changing it in Settings
recomposes the theme **live** — no restart. Screens use
`MaterialTheme.colorScheme.*` tokens (never hard-coded colors, apart from the
hero gradient), so both schemes render correctly.

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

A small colored chip indicating the condition's stress type. The `stressType`
field is **static descriptive metadata** carried from the condition record — it
is NOT a learned prediction. The system does not detect or classify abiotic
stress; all 10 disease classes are biotic, and "healthy" is neither.

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

### Other components

| Component | File | Role |
|---|---|---|
| `ConfidenceBar` | `ConfidenceBar.kt` | Thin horizontal confidence bar (Home last-scan, Result secondary list) |
| `ConfidenceGauge` | `ConfidenceGauge.kt` | Circular gauge for the primary confidence on Result |
| `StatCard` | `StatCard.kt` | Icon + value + label tile in the Home stats row |
| `SimpleBarChart` | `SimpleBarChart.kt` | Disease-distribution bar chart on Home (`BarChartItem` data) |
| `ScanAnimationOverlay` | `ScanAnimationOverlay.kt` | Animated "analysing" overlay during inference |
| `GateRejectWarning` | `GateRejectWarning.kt` | Shown when a cascade gate rejects the image (not a leaf / not a tomato) with a Retake action |
| `OnboardingDialog` | `OnboardingDialog.kt` | One-time how-to-use dialog on first launch |
| `GrowingMethodSelector` | `GrowingMethodSelector.kt` | Shared chip selector for the four growing methods (Result + Settings) |
| `FeedbackCard` | `FeedbackCard.kt` | The [flywheel](#the-feedback-flywheel) "Was this correct?" prompt |
| `FullScreenImageViewer` | `FullScreenImageViewer.kt` | Tap a scan thumbnail (History/Result) to open the full image with pinch-to-zoom, pan, and double-tap reset |

---

## Bilingual system

### String resources

All user-visible strings are in two resource files:

- `res/values/strings.xml` — English (default locale)
- `res/values-ar/strings.xml` — Arabic

Android's resource system selects the correct file based on the active locale.
Compose accesses them via `stringResource(R.string.key)`.

### Locale switching

Changing the language in Settings writes `UserSettings.language` to
`SettingsStore`. `MainActivity` collects the reactive `settings` flow; when the
language differs from the one the current Activity context was built with, it
calls `recreate()`. On recreation, `attachBaseContext` applies the new locale
via `LocaleHelper.applyLocale(base, language)` before the first frame, so all
`stringResource()` calls return the right language and Compose mirrors RTL for
Arabic automatically — with no visible English flash.

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

48 JVM unit tests (no device needed) live in
`android/app/src/test/kotlin/com/tomatocare/`, plus Compose UI tests in
`src/androidTest/`. They run on every push/PR via
[GitHub Actions CI](../.github/workflows/android-ci.yml), which also runs Android
Lint and a JaCoCo coverage report.

| Test file | What it guards |
|---|---|
| `ClassNamesTest` | `TomatoClasses.CLASS_NAMES` stays alphabetical and matches `training_config.yaml` — a mismatch would silently mislabel every output tensor index |
| `ScanHistorySerializationTest` | Scan-history JSON round-trips; unknown keys ignored |
| `ScanRecordTest` | `ScanRecord.primary` selection logic |
| `FormatTest` | Timestamp formatting |
| `FeedbackSerializationTest` | `ScanFeedback` round-trips **and legacy records without the field still decode** (flywheel backward-compat) |
| `HomeStatsTest` | Dashboard stats incl. the health-rate metric (regression test for the `"healthy"` conditionId fix) |
| `HistoryFilterTest` | History search (EN/AR) + severity filter logic |
| `BadgeUiTest` (androidTest) | Compose UI test: severity / stress badges render correct labels |
| `SeverityHeuristicTest` | Confidence → severity boundary mapping |
| `TrainingLabelTest` | Flywheel export label resolution (prediction vs correction vs fallback) |

The pure logic these test (`HomeStats`, `SeverityHeuristic`,
`TrainingDataExporter.resolveLabel`) was deliberately extracted from
Android-coupled classes so it is unit-testable without Robolectric or a device.

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
