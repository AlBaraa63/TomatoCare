# Architecture

This document describes the overall system design of TomatoCare, the data flow
from camera to diagnosis, and the key design decisions that shaped both tracks.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Track A — ML Pipeline](#track-a--ml-pipeline)
3. [Track B — Android App](#track-b--android-app)
   - [Layer diagram](#layer-diagram)
   - [Dependency graph](#dependency-graph)
   - [Screen flow](#screen-flow)
   - [Inference data flow](#inference-data-flow)
4. [Data models](#data-models)
5. [Key design decisions](#key-design-decisions)
6. [File layout reference](#file-layout-reference)

---

## System Overview

TomatoCare has two independent tracks that share a single artifact: the TFLite
model file.

```
┌─────────────────────────────────────────────────┐
│              Track A — ML Pipeline               │
│                                                  │
│  Raw images → Augmentation → Train → Eval        │
│                                     │            │
│                              Export .tflite      │
└─────────────────────────────────────┬────────────┘
                                      │ copy
                                      ▼
                          android/app/src/main/assets/
                          tomatocare_model_float16.tflite

┌─────────────────────────────────────────────────┐
│            Track B — Android App                │
│                                                  │
│  Camera/Gallery → Preprocess → TFLite infer     │
│                                      │           │
│                              ScanRecord → JSON   │
│                              + Treatment advice  │
└─────────────────────────────────────────────────┘
```

The Android app is fully self-contained: the model is bundled inside the APK
as an uncompressed asset that is memory-mapped at runtime. No server, no API,
no internet connection of any kind.

---

## Track A — ML Pipeline

The ML pipeline is a sequence of numbered stages. Each stage reads a config
value from `ml/configs/training_config.yaml` and writes a cached artifact. If
the artifact already exists the stage is skipped.

```
training_config.yaml  (single source of truth for all hyperparameters)
         │
         ▼
┌─────────────────┐
│  A2             │  prepare_plantvillage.py
│  Data prep      │  Input:  pre-split dataset OR raw images
│                 │  Output: ml/dataset/splits/{train,val,test}.csv
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  A3             │  augment_uae.py
│  Augmentation   │  Input:  train.csv + raw images
│                 │  Output: ml/dataset/augmented/train/ (4x)
└────────┬────────┘         ml/dataset/augmented/val/
         │                  ml/dataset/augmented/test/
         ▼
┌─────────────────┐
│  A5             │  train_stage1.py
│  Stage-1 train  │  Input:  augmented/train/ + val.csv
│  (head only)    │  Output: models/checkpoints/stage1_best.keras
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  A6             │  train_stage2.py
│  Stage-2 train  │  Input:  stage1_best.keras + augmented/train/ + val.csv
│  (fine-tune)    │  Output: models/checkpoints/stage2_best.keras
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  A6.5           │  calibrate_temperature.py
│  Calibration    │  Input:  stage2_best.keras + val.csv
│                 │  Output: models/checkpoints/stage2_calibrated.keras
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  A7             │  eval_model.py
│  Evaluation     │  Input:  stage2_calibrated.keras + test.csv
│                 │  Output: results/eval_report.json
│  Gate: ≥ 90%   │          results/confusion_matrix.png
└────────┬────────┘  Exits with code 1 if accuracy/OOD gates fail.
         │
         ▼
┌─────────────────┐
│  A8             │  export_tflite.py
│  TFLite export  │  Input:  stage2_calibrated.keras
│                 │  Output: models/tflite/tomatocare_model_float16.tflite
│  Gate: ≤ 15 MB  │  Exits with code 1 if size gate fails.
└─────────────────┘
```

See [ml-pipeline.md](ml-pipeline.md) for detailed documentation of each stage.

---

## Track B — Android App

### Layer diagram

The app uses a hand-rolled dependency injection container (`AppContainer`) instead
of Hilt, keeping the dependency graph explicit and the build fast.

```
┌──────────────────────────────────────────────────────────────────┐
│                     Presentation Layer                           │
│                                                                  │
│  HomeScreen   ScanScreen   ResultScreen   HistoryScreen   Settings│
│      │             │            │              │               │  │
│  HomeVM     ScanVM        ResultVM       HistoryVM     SettingsVM │
└──────────────────────────┬──────────────────────────────────────┘
                           │  (via AppContainer)
┌──────────────────────────▼──────────────────────────────────────┐
│                    Application Layer                             │
│                                                                  │
│  TFLiteEngine          ImagePreprocessor                         │
│  (classify bitmap)     (resize 224×224, normalize [0,1])         │
└──────────┬──────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────┐
│                       Data Layer                                 │
│                                                                  │
│  ScanStorageManager     TreatmentRepository    SettingsStore     │
│  (filesDir/scan_history.json, atomic write)    (DataStore)       │
│                                                                  │
│  ScanExporter / ScanImporter  (SAF — no raw storage permission)  │
└─────────────────────────────────────────────────────────────────┘
```

### Dependency graph

`AppContainer` is created once in `TomatoCareApp.onCreate()` and passed down to
each screen's ViewModel. There is no static singleton — the container is
accessed through the `Application` reference.

```
TomatoCareApp
└── AppContainer
    ├── SettingsStore
    ├── ScanStorageManager
    ├── ScanExporter(ScanStorageManager)
    ├── ScanImporter(ScanStorageManager)
    ├── TreatmentRepository          ← reads assets/treatments.json once, then immutable
    ├── ImagePreprocessor
    └── TFLiteEngine(ImagePreprocessor)
        └── warm-up coroutine         ← one blank inference on a background thread at startup
```

### Screen flow

```
App launch
    │
    ▼
HomeScreen ──── [Scan a leaf] ──────► ScanScreen
    │                                     │
    │           [View history]             │ capture / import
    │                │                    ▼
    │           HistoryScreen        (Processing)
    │                │                    │
    │           [tap record]         (LowConfidence?) ── [Retake] ──► ScanScreen
    │                │                    │
    │                └──────────────► ResultScreen
    │                                     │
    │           [Settings]                │ [Back]
    └────────► SettingsScreen             ▼
                                      HomeScreen
```

Navigation is handled by Compose Navigation with a single `NavController`.
After a successful scan the back-stack is cleared to `HomeScreen` so pressing
Back from `ResultScreen` goes home, not back to the camera.

### Inference data flow

```
User taps Capture
    │
    ▼
CameraX ImageCapture.takePicture()
    │ Bitmap (full resolution JPEG → decoded to Bitmap)
    ▼
ImagePreprocessor.preprocess(bitmap)
    ├── Rotate by EXIF tag (if API < 28)
    ├── Scale to 224 × 224
    └── Normalize pixels: uint8 [0,255] → float32 [0.0, 1.0]
        → DirectByteBuffer (4 bytes × 224 × 224 × 3 = ~590 KB)
    │
    ▼
TFLiteEngine.classify(bitmap, growingMethod, threshold)
    ├── Set input tensor ← ByteBuffer from ImagePreprocessor
    ├── Interpreter.run()
    │       (MobileNetV3-Large float16, mmap'd, 4 threads)
    ├── Read output tensor [1 × 11] softmax probabilities
    ├── Map index → class name (TomatoClasses.CLASS_NAMES, alphabetical)
    ├── Sort descending → top-3 results
    ├── Apply severity heuristic (confidence → severity level)
    │       ≥ 90% → base severity
    │       75–90% → one level lower
    │       60–75% → two levels lower
    │       < 60%  → LOW
    └── Return InferenceOutput(topResults, inferenceTimeMs, isLowConfidence)
    │
    ▼
ScanViewModel.onImageCaptured()
    ├── Save thumbnail to filesDir/images/<scanId>.jpg
    ├── Lookup treatments from TreatmentRepository (by conditionId + growingMethod)
    ├── Build ScanRecord(scanId, imagePath, timestamp, growingMethod, results)
    └── ScanStorageManager.save(record) → atomic write to scan_history.json
    │
    ▼
Navigate to ResultScreen(scanId)
```

---

## Data models

All models are Kotlin `@Serializable` data classes stored as human-readable JSON.

```
ScanHistory
└── List<ScanRecord>
    ├── scanId: Int                  unique per device, increments from 0
    ├── imagePath: String            absolute path inside filesDir
    ├── timestamp: String            ISO-8601 UTC ("2025-05-19T14:30:00Z")
    ├── growingMethod: GrowingMethod  GREENHOUSE | OPEN_FIELD | HYDROPONIC | SALINE_SOIL
    ├── modelVersion: String         "2.0.0"
    └── results: List<DiagnosisResult>
        ├── resultId: Int
        ├── conditionId: String       stable key for TreatmentRepository lookup
        ├── conditionNameEn: String
        ├── conditionNameAr: String
        ├── confidence: Double        0.0–1.0
        ├── isPrimary: Boolean        true for the top result only
        ├── stressType: StressType    BIOTIC | ABIOTIC
        ├── severityLevel: SeverityLevel  LOW | MEDIUM | HIGH | CRITICAL
        └── treatments: List<Treatment>
            ├── treatmentId: Int
            ├── growingMethod: GrowingMethod
            ├── treatmentType: TreatmentType   CHEMICAL | CULTURAL | BIOLOGICAL
            ├── urgencyLevel: UrgencyLevel     LOW | MEDIUM | HIGH | CRITICAL
            ├── recommendationEn: String
            └── recommendationAr: String
```

Enum values are serialized as their name strings (`"BIOTIC"`, `"MEDIUM"`, etc.)
for human-readable, forward-compatible JSON — adding new enum variants never
breaks existing history files.

---

## Key design decisions

### 1. No internet permission

The `INTERNET` permission is deliberately absent from the manifest. This is an
explicit hard guarantee to the user: TomatoCare never transmits data. It also
makes security reviews trivial — there is no network code to audit.

### 2. Float16 quantization over INT8

Post-training INT8 quantization typically drops 2–4% per-class accuracy on this
dataset. Float16 drops less than 0.5% while cutting model size from ~13 MB
(float32) to 5.75 MB. The 15 MB size budget is easily met while keeping
accuracy at 95.60%.

### 3. Memory-mapped TFLite model

The `.tflite` asset is stored uncompressed in the APK (`noCompress += "tflite"`
in `build.gradle.kts`). The Android linker can then `mmap()` it directly from
the APK without heap allocation. This means the model never occupies heap memory
and the OS can evict its pages under memory pressure and reload them as needed.

### 4. Alphabetical class order as the contract

TF Keras' `image_dataset_from_directory` sorts class names alphabetically when
loading training data. `TomatoClasses.CLASS_NAMES` replicates this exact order
and is the single source of truth used by both the training pipeline and the
Android app. Any mismatch causes silent misclassification — `ClassNamesTest`
enforces this contract in CI.

### 5. Hand-rolled DI instead of Hilt

Hilt adds annotation processing to every build, slowing down incremental
compilation. With only five screens and a handful of dependencies, a plain
`AppContainer` class (instantiated once in `Application.onCreate`) is clearer,
faster to build, and easier to understand for a team learning the codebase.

### 6. TFLite warm-up at startup

The first TFLite inference includes JIT compilation and native library loading
overhead (~500–1000 ms extra on some devices). `AppContainer` fires a
background warm-up inference on a blank bitmap immediately at startup so the
first real scan feels instant.

### 7. Two-stage training

- **Stage 1 (A5):** MobileNetV3-Large base is frozen; only the classification
  head (GAP → Dropout → Dense) is trained. This converges quickly and avoids
  destroying ImageNet weights with a high learning rate.
- **Stage 2 (A6):** The last 30 layers of the base are unfrozen and fine-tuned
  at LR=1e-4. This adapts higher-level features to tomato leaf textures without
  catastrophic forgetting of the lower-level edge/texture detectors.

### 8. Atomic JSON writes for scan history

`ScanStorageManager` writes to a temp file then renames it over the target. On
Linux/Android the rename is atomic at the filesystem level, so a crash mid-write
never corrupts the history file.

### 9. Storage Access Framework for export/import

Using SAF (`ActivityResultContracts.CreateDocument` / `OpenDocument`) means the
app never needs `READ_EXTERNAL_STORAGE` on API 29+. The user controls where the
export file lives and the app only ever sees a `Uri` — not raw paths.

---

## File layout reference

```
com.tomatocare/
├── TomatoCareApp.kt          Application class — creates AppContainer
├── MainActivity.kt           Single Activity — hosts NavController
│
├── di/
│   └── AppContainer.kt       All dependencies wired here; no framework DI
│
├── inference/
│   ├── TFLiteEngine.kt       loads model, runs inference, applies severity heuristic
│   ├── ImagePreprocessor.kt  EXIF rotation, 224×224 resize, float32 normalization
│   └── TomatoClasses.kt      CLASS_NAMES list + MODEL_ASSET constant
│
├── data/
│   ├── model/
│   │   ├── ScanRecord.kt
│   │   ├── DiagnosisResult.kt
│   │   ├── Treatment.kt
│   │   ├── UserSettings.kt
│   │   └── Enums.kt          StressType, SeverityLevel, GrowingMethod, Language, …
│   ├── storage/
│   │   ├── ScanStorageManager.kt   read/write/delete scan_history.json
│   │   ├── ScanExporter.kt         SAF write
│   │   └── ScanImporter.kt         SAF read + merge
│   └── repository/
│       ├── TreatmentRepository.kt  loads treatments.json asset once → immutable map
│       └── SettingsStore.kt        DataStore<Preferences> wrapper
│
└── ui/
    ├── navigation/
    │   └── TomatoCareNavHost.kt    NavGraph with five destinations
    ├── home/
    │   ├── HomeScreen.kt
    │   └── HomeViewModel.kt
    ├── scan/
    │   ├── ScanScreen.kt
    │   ├── ScanViewModel.kt
    │   └── CameraController.kt     CameraX setup
    ├── result/
    │   ├── ResultScreen.kt
    │   └── ResultViewModel.kt
    ├── history/
    │   ├── HistoryScreen.kt
    │   └── HistoryViewModel.kt
    ├── settings/
    │   ├── SettingsScreen.kt
    │   └── SettingsViewModel.kt
    └── components/
        ├── TreatmentCard.kt        expandable treatment row
        ├── StressBadge.kt          BIOTIC / ABIOTIC colored chip
        ├── LowConfidenceWarning.kt orange warning with Retake / Show Anyway
        └── SeverityChip.kt         LOW / MEDIUM / HIGH / CRITICAL chip
```
