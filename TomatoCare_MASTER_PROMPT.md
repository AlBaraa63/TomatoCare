# TomatoCare — Capstone 2 Master Implementation Prompt
### For Claude Opus 4 · Full Agentic Build

---

## HOW TO USE THIS PROMPT

Paste this entire document as your first message to Claude Opus 4.
Do not summarise it. Do not paraphrase it. Send it verbatim.
After sending it, Claude will confirm it understood and ask you one
clarifying question before starting. Answer that question, then let
it work. Do not interrupt unless it asks you something directly.

---

## YOUR ROLE AND MISSION

You are a senior full-stack engineer and machine learning engineer
implementing **TomatoCare** — a fully offline, bilingual Android application
that diagnoses tomato leaf diseases using an on-device MobileNetV3-Large CNN
model. This is a real Capstone 2 university project and your code will be
submitted, tested, and graded.

You are not planning, summarising, or advising.
**You are building.** You write real, runnable code. You create real files.
You follow the protocol in this document exactly. You do not skip steps.
You do not ask unnecessary questions. When you are uncertain about a minor
detail, you make the most sensible engineering decision, document it with a
comment, and continue.

When you finish every micro-process, you explicitly say:
```
✅ [A1] COMPLETE — <one sentence summary of what was produced>
```
Then you immediately start the next one without waiting for permission.

---

## FULL PROJECT KNOWLEDGE

Everything you need to know about TomatoCare is embedded below.
You do not need the original report. You do not need to search the web.

### What TomatoCare Is

A native Android application (Kotlin + Jetpack Compose) that:
- Takes a photo of a tomato leaf (camera or gallery)
- Runs on-device inference using a TFLite model (MobileNetV3-Large, float16)
- Classifies it into 1 of 10 classes (1 healthy + 9 diseases)
- Shows the diagnosis with: condition name in English AND Arabic,
  confidence %, a biotic/abiotic stress badge, a severity level (Low /
  Medium / High / Critical), and localised treatment recommendations
- If confidence < 60%, shows a Low Confidence Warning instead
- Stores every scan locally as JSON (no cloud, no internet, ever)
- Supports full English/Arabic bilingual UI with RTL layout
- Allows export and import of scan history via Android Storage Access Framework
- Runs on Android API 26 (Android 8.0) and above, min 2 GB RAM

### The 10 Classification Classes (exact names)
```
Tomato_healthy
Tomato_Early_blight
Tomato_Late_blight
Tomato_Bacterial_spot
Tomato_Septoria_leaf_spot
Tomato_Spider_mites_Two_spotted_spider_mite
Tomato_Target_Spot
Tomato_Yellow_Leaf_Curl_Virus
Tomato_mosaic_virus
Tomato_Leaf_Mold
```

### Biotic vs Abiotic Mapping
```
BIOTIC  → Early Blight, Late Blight, Bacterial Spot, Septoria Leaf Spot,
           Spider Mites, Target Spot, Yellow Leaf Curl Virus,
           Mosaic Virus, Leaf Mold
ABIOTIC → Healthy (no stress), Sunscald, Heat Stress, Salinity Chlorosis
           (abiotic labels appear when confidence is ambiguous or
            when a healthy leaf shows environmental stress markers)
```

### Architecture — Three Layers
```
Layer 1 — Presentation (Jetpack Compose, CameraX)
Layer 2 — Application Logic (ImagePreprocessor, TFLiteEngine, ViewModel)
Layer 3 — Data (ScanStorageManager JSON, TreatmentRepository, SAF)
```

### Data Model (JSON schema — must match exactly for export/import compatibility)
```json
{
  "scans": [
    {
      "scanId": 1,
      "imagePath": "string",
      "timestamp": "ISO-8601",
      "growingMethod": "GREENHOUSE | OPEN_FIELD | HYDROPONIC | SALINE_SOIL",
      "modelVersion": "1.0.0",
      "results": [
        {
          "resultId": 1,
          "conditionNameEn": "string",
          "conditionNameAr": "string",
          "confidence": 0.94,
          "isPrimary": true,
          "stressType": "BIOTIC | ABIOTIC",
          "severityLevel": "LOW | MEDIUM | HIGH | CRITICAL",
          "treatments": [
            {
              "treatmentId": 1,
              "growingMethod": "GREENHOUSE",
              "treatmentType": "CHEMICAL | CULTURAL | BIOLOGICAL",
              "urgencyLevel": "LOW | MEDIUM | HIGH | CRITICAL",
              "recommendationEn": "string",
              "recommendationAr": "string"
            }
          ]
        }
      ]
    }
  ]
}
```

### ML Hyperparameters (authoritative — do not change without noting it)
```yaml
seed: 42
img_size: 224
batch_size: 32
stage1_epochs: 30
stage1_lr: 0.001
stage1_patience: 5
stage2_epochs: 10
stage2_lr: 0.0001
fine_tune_from_layer: -30
dropout_rate: 0.4
confidence_threshold: 0.60
target_accuracy: 0.90
tflite_max_size_mb: 15
apk_max_size_mb: 50
```

### Non-Functional Requirements (these are pass/fail acceptance criteria)
```
NFR-01  Zero network calls during any operation
NFR-02  Inference ≤ 3 seconds on API 26 / Snapdragon 660-class device
NFR-03  Model accuracy ≥ 90% on UAE-specific held-out test set
NFR-04  APK ≤ 50 MB total, .tflite ≤ 15 MB
NFR-05  Core functions reachable within 2 taps from Home
NFR-06  Zero crashes across 50 consecutive scan operations
NFR-07  Runs on both API 26 and API 34 emulators
NFR-08  Zero outbound data transmission (verifiable via network analyser)
```

---

## CODING PROTOCOL — FOLLOW WITHOUT EXCEPTION

### Console Banner System (3 levels, strictly typed)

Level 1 — Script Header (once per script):
```
##############################################################
  TomatoCare — [Script Purpose]
  Device : cuda / cpu
  Seed   : 42
##############################################################
```

Level 2 — Phase Header (per major phase):
```
==============================================================
  PHASE: [Name of phase]
==============================================================
```

Level 3 — Step Header (per individual step):
```
--------------------------------------------------------------
  [step_id] Description
  Param A: value  |  Param B: value
--------------------------------------------------------------
```

Result Block (end of any timed step):
```
  >> Metric A : value
  >> Metric B : value
  >> Saved to : path/to/output
```

❌ Never mix `#`, `=`, `-` across banner levels.
❌ Never use `*` or custom characters.

### Python Rules
- Import order: stdlib → third-party → project imports
- All paths: `pathlib.Path` only, never bare strings
- Every output file saved automatically — never rely on copy-paste
- Every script that produces a file: check if output exists → skip with message → return cached
- Comments explain WHY, not WHAT
- `set_seed(42)` called at the very start of every training script
- Model architecture never defined inside training scripts

### Kotlin / Android Rules
- No hardcoded strings in any Kotlin or XML file — all strings go in `strings.xml`
- All coroutines dispatched to `Dispatchers.IO` for file/inference work
- No business logic inside Composable functions — all logic in ViewModels
- Atomic write pattern mandatory for any JSON file write (write temp → rename)
- No Room, no SQLite — JSON flat file only via `kotlinx.serialization`
- Zero WRITE_EXTERNAL_STORAGE permission on API 29+ — use SAF only
- Model loaded once at init, not per classification request

### Caching Rule (Python)
```python
if output_path.exists():
    print(f"  >> SKIP: {output_path} already exists. Delete to re-run.")
    with open(output_path) as f:
        return json.load(f)
```

### Atomic Write Rule (Kotlin)
```kotlin
val tempFile = File(context.filesDir, "scan_history.tmp")
tempFile.writeText(Json.encodeToString(records))
tempFile.renameTo(File(context.filesDir, "scan_history.json"))
```

---

## REPOSITORY STRUCTURE (create this exactly)

```
tomatocare/
├── ml/
│   ├── configs/
│   │   └── training_config.yaml
│   ├── dataset/
│   │   ├── raw/plantvillage/        # downloaded manually
│   │   ├── augmented/
│   │   └── splits/
│   ├── models/
│   │   ├── checkpoints/
│   │   └── tflite/
│   ├── results/
│   └── scripts/
│       ├── prepare_plantvillage.py
│       ├── augment_uae.py
│       ├── train_stage1.py
│       ├── train_stage2.py
│       ├── eval_model.py
│       └── export_tflite.py
└── android/
    └── app/
        ├── src/main/
        │   ├── assets/
        │   │   ├── tomatocare_model_float16.tflite
        │   │   └── treatments.json
        │   ├── kotlin/com/tomatocare/
        │   │   ├── ui/
        │   │   │   ├── home/
        │   │   │   ├── scan/
        │   │   │   ├── result/
        │   │   │   ├── history/
        │   │   │   ├── settings/
        │   │   │   └── components/
        │   │   ├── inference/
        │   │   │   ├── TFLiteEngine.kt
        │   │   │   └── ImagePreprocessor.kt
        │   │   ├── data/
        │   │   │   ├── model/
        │   │   │   ├── storage/
        │   │   │   └── repository/
        │   │   ├── domain/usecase/
        │   │   └── utils/
        │   └── res/
        │       ├── values/strings.xml
        │       └── values-ar/strings.xml
        └── build.gradle.kts
```

---

## THE EXECUTION SEQUENCE

You will complete these micro-processes in this exact order.
**Track A (ML) must complete A1–A8 before B3 (Android) can embed the model.
B1, B2, B6 can start in parallel with Track A from the beginning.**

```
TRACK A (Python / ML):
A1 → A2 → A3 → A4 → A5 → A6 → A7 → A8
                                       ↘
TRACK B (Kotlin / Android):             B3 → B4 → B5 → B7 → B8 → B9
B1 ——————→ B2 ————————————————————————↗
B6 (parallel, can start after B2)

TRACK C (Testing + Release):
C1 → C2 → C3 → C4   (after all B tasks complete)
```

---

## MICRO-PROCESS SPECIFICATIONS

For each micro-process:
- Write every file completely — no `# TODO` stubs, no `pass`, no placeholders
- At the end, output a summary block with all files created
- Immediately move to the next task

---

### A1 · Environment Setup

**Produce:**
- `ml/requirements.txt`
- `ml/configs/training_config.yaml` (all hyperparameters from the YAML block above)
- `ml/scripts/utils/seed.py` (the `set_seed` utility used by all training scripts)

`requirements.txt` must pin:
`tensorflow>=2.13,<3.0`, `numpy`, `pillow`, `scikit-learn`, `matplotlib`,
`seaborn`, `tqdm`, `pyyaml`, `pandas`

`training_config.yaml` must contain every value from the hyperparameter block above.
Do not add any values that are not in that block.

`seed.py` must implement:
```python
def set_seed(seed: int = 42):
    # Sets seed for Python random, NumPy, and TensorFlow.
    # Called at the very start of every training script to ensure
    # that all weight initialisations and data shuffles are reproducible.
```

---

### A2 · Dataset Inventory

**Produce:** `ml/scripts/prepare_plantvillage.py`

This script must:
1. Print a Level 1 banner.
2. Walk `ml/dataset/raw/plantvillage/` and count images per class.
3. Print a Level 2 banner `PHASE: Dataset Inventory`.
4. For each of the 10 expected classes, print a Level 3 banner with
   class name and count. If a class is missing, raise `FileNotFoundError`
   with a message listing which class is absent.
5. Print a Level 2 banner `PHASE: Stratified Split`.
6. Apply stratified split: 70% train / 15% val / 15% test using
   `sklearn.model_selection.train_test_split` with `random_state=42`
   and `stratify=labels`.
7. Save three CSVs to `ml/dataset/splits/`: `train.csv`, `val.csv`,
   `test.csv`. Columns: `filepath`, `label`, `class_index`.
8. Auto-save `ml/results/dataset_report.json` with per-class counts and
   per-split totals.
9. Implement caching — if all three CSVs exist, skip and print the
   skip message.

---

### A3 · UAE Augmentation Pipeline

**Produce:** `ml/scripts/augment_uae.py`

This script augments only the training split.

UAE-specific augmentations (these are the ones that matter for the domain gap —
standard flips/rotations are table stakes, but these mimic Gulf conditions):
- **Brightness jitter** [0.6, 1.4] — UAE peak solar irradiance bleaches highlights
- **Contrast jitter** [0.7, 1.3]
- **Red-channel shift** +10 to +25 — dust haze in UAE adds a warm orange cast
  to images; shifting R up simulates this without destroying lesion hue contrast
- **Gaussian blur** σ ∈ [0, 1.5] — heat shimmer causes soft focus at distance
- **Random rotation** ±30°
- **Horizontal/Vertical flip** (50% / 20% probability)
- **Random zoom** up to 20%

Read augmentation parameters from `training_config.yaml`, not hardcoded.

Write augmented images to `ml/dataset/augmented/train/<class_name>/`.
Save `ml/results/augmentation_log.json` with before/after image counts per class.
Implement caching — if `augmented/train/` already contains images, skip.

---

### A4 · Data Pipeline (TF Dataset Builders)

**Produce:** `ml/scripts/utils/dataset_loader.py`

Implement:
```python
def build_dataset(split_csv: Path, config: dict,
                  augment: bool = False) -> tf.data.Dataset:
    # Returns a batched, prefetched tf.data.Dataset.
    # augment=True applies the UAE augmentation pipeline on-the-fly
    # (used for training); False applies only resize + normalise
    # (used for val and test).
```

The preprocessing must:
- Resize to 224×224
- Normalise pixel values to [0.0, 1.0]
- One-hot encode labels to 10 classes

The output dataset must be batched to `batch_size` from config and prefetched
with `tf.data.AUTOTUNE`.

---

### A5 · Stage 1 Training — Classification Head Only

**Produce:** `ml/scripts/train_stage1.py`

1. Print Level 1 banner (script name, device, seed).
2. Load config from `training_config.yaml`.
3. Call `set_seed(config['seed'])`.
4. Build the model:
   - `MobileNetV3Large(include_top=False, weights='imagenet', input_shape=(224,224,3))`
   - Freeze the entire base model.
   - Add: `GlobalAveragePooling2D()` → `Dropout(config['dropout_rate'])` →
     `Dense(10, activation='softmax')`
5. Compile with Adam lr=`stage1_lr`, loss=`categorical_crossentropy`,
   metrics=`['accuracy']`.
6. Print Level 2 banner `PHASE: Stage 1 Training — Head Only`.
7. Use callbacks:
   - `EarlyStopping(monitor='val_accuracy', patience=config['stage1_patience'],
     restore_best_weights=True)`
   - `ModelCheckpoint('ml/models/checkpoints/stage1_best.keras', save_best_only=True)`
8. Print a Level 3 banner every 5 epochs:
   `Epoch N | Train Loss: X | Val Accuracy: Y% | Time: Zs`
9. After training, auto-save `ml/results/results_stage1.json`:
   ```json
   {
     "best_val_accuracy": 0.0,
     "best_epoch": 0,
     "total_epochs_run": 0,
     "stage1_lr": 0.001,
     "history": []
   }
   ```
10. Implement caching — if `stage1_best.keras` exists, skip training
    and load the checkpoint.

---

### A6 · Stage 2 Training — Fine-Tuning

**Produce:** `ml/scripts/train_stage2.py`

1. Load Stage 1 checkpoint from `ml/models/checkpoints/stage1_best.keras`.
2. Print Level 1 banner, Level 2 banner `PHASE: Stage 2 Training — Fine-Tune`.
3. Unfreeze `base_model.layers[config['fine_tune_from_layer']:]`.
   The config value `-30` means the last 30 layers — explain this in a comment.
4. Re-compile: Adam lr=`stage2_lr` (0.0001).
   Lower LR is critical: fine-tuning with the Stage 1 LR would destroy
   the ImageNet feature representations we need in the lower layers.
5. Train for up to `stage2_epochs` (10) with same callback pattern.
   Save to `ml/models/checkpoints/stage2_best.keras`.
6. Auto-save `ml/results/results_stage2.json` with same schema as Stage 1
   plus `"fine_tuned_from_layer": -30`.
7. Implement caching — if `stage2_best.keras` exists, skip.

---

### A7 · Evaluation

**Produce:** `ml/scripts/eval_model.py`

1. Load `stage2_best.keras`.
2. Load the **test split only** (`ml/dataset/splits/test.csv`).
3. Run inference on every test image.
4. Compute:
   - Overall accuracy (float)
   - Per-class precision, recall, F1 (use `sklearn.metrics.classification_report`)
   - Macro-averaged F1
   - 10×10 confusion matrix
5. Save `ml/results/eval_report.json`:
   ```json
   {
     "overall_accuracy": 0.0,
     "macro_f1": 0.0,
     "per_class": {},
     "confusion_matrix": [[]]
   }
   ```
6. Save `ml/results/confusion_matrix.png` (seaborn heatmap, class names on axes).
7. Print Level 2 banner `PHASE: Evaluation Results` and display all metrics.
8. **Enforce pass/fail:** if accuracy < 0.90, print:
   ```
   ❌ TARGET NOT MET: accuracy=X.XX < 0.90 required
      Check augmentation quality and retrain.
   ```
   and `sys.exit(1)`.

---

### A8 · TFLite Export

**Produce:** `ml/scripts/export_tflite.py`

1. Load `stage2_best.keras`.
2. Convert with float16 quantisation:
   ```python
   converter = tf.lite.TFLiteConverter.from_keras_model(model)
   converter.optimizations = [tf.lite.Optimize.DEFAULT]
   converter.target_spec.supported_types = [tf.float16]
   tflite_model = converter.convert()
   ```
   Float16 (not int8) because int8 can introduce per-class accuracy drops
   of 2–4% on fine-grained classification — unacceptable at our 90% target.
3. Save to `ml/models/tflite/tomatocare_model_float16.tflite`.
4. Measure file size — if > 15 MB, print a warning and `sys.exit(1)`.
5. **Post-export accuracy check:** reload the `.tflite` with the TFLite
   Interpreter, run the full test split through it, compare accuracy to the
   Keras model's reported accuracy from `eval_report.json`.
   If the drop > 1%, print a warning (do not fail — float16 drops are usually < 0.5%).
6. Save `ml/results/tflite_export_report.json`:
   ```json
   {
     "keras_accuracy": 0.0,
     "tflite_accuracy": 0.0,
     "accuracy_drop": 0.0,
     "model_size_mb": 0.0,
     "quantisation": "float16"
   }
   ```
7. Print the path to the `.tflite` file prominently — the Android team
   copies this file into `android/app/src/main/assets/`.

---

### B1 · Android Project Scaffold

**Produce:** All Gradle and configuration files for the Android project.

Write the full contents of:
- `android/app/build.gradle.kts` — min SDK 26, compile SDK 34,
  Kotlin serialization plugin, all dependencies below:
  ```
  tensorflow-lite:2.14.0
  tensorflow-lite-support:0.4.4
  camera-core, camera-camera2, camera-lifecycle, camera-view (CameraX BOM)
  kotlinx-serialization-json:1.6.3
  navigation-compose:2.7.7
  compose BOM:2024.02.00
  hilt-android (optional — only if you choose Hilt over manual DI)
  ```
- `android/settings.gradle.kts`
- `android/gradle.libs.versions.toml` (version catalog)
- `android/app/src/main/AndroidManifest.xml` — declare:
  `CAMERA`, `READ_EXTERNAL_STORAGE` (maxSdkVersion 28 only)
  No INTERNET permission declared at all.
- `android/lint.xml` — rule to fail if hardcoded text found in layouts.

---

### B2 · Data Model Layer

**Produce:** All data classes and enums.

Write complete files:

`data/model/Enums.kt`:
```kotlin
enum class StressType { BIOTIC, ABIOTIC }
enum class SeverityLevel { LOW, MEDIUM, HIGH, CRITICAL }
enum class GrowingMethod { GREENHOUSE, OPEN_FIELD, HYDROPONIC, SALINE_SOIL }
enum class Language { ENGLISH, ARABIC }
enum class TreatmentType { CHEMICAL, CULTURAL, BIOLOGICAL }
```

`data/model/ScanRecord.kt` — `@Serializable` data class matching the JSON schema exactly.
`data/model/DiagnosisResult.kt` — `@Serializable`.
`data/model/Treatment.kt` — `@Serializable`.
`data/model/UserSettings.kt` — `@Serializable`.
`data/model/InferenceOutput.kt` — internal-only (not serialised):
```kotlin
data class InferenceOutput(
    val results: List<DiagnosisResult>,
    val isLowConfidence: Boolean,
    val inferenceTimeMs: Long
)
```

All field names must match the JSON schema field-for-field.
Do not add convenience fields that would break import/export compatibility.

---

### B3 · TFLite Inference Engine

**Produce:**
- `inference/ImagePreprocessor.kt`
- `inference/TFLiteEngine.kt`

`ImagePreprocessor.kt`:
```kotlin
class ImagePreprocessor {
    fun process(bitmap: Bitmap): ByteBuffer {
        // Resize to 224×224, normalise pixels to [0.0, 1.0],
        // pack into a direct ByteBuffer with FLOAT32 type.
        // The ByteBuffer must be direct (allocateDirect) for zero-copy
        // access from native TFLite code.
    }
}
```

`TFLiteEngine.kt`:
```kotlin
class TFLiteEngine(context: Context) {
    private val interpreter: Interpreter

    init {
        // Load model from assets once at init.
        // Loading per-request would add ~200 ms latency to every scan.
    }

    suspend fun classify(bitmap: Bitmap,
                         growingMethod: GrowingMethod,
                         treatmentRepository: TreatmentRepository,
                         confidenceThreshold: Float = 0.60f): InferenceOutput {
        // Runs on Dispatchers.IO.
        // Returns InferenceOutput with isLowConfidence=true if
        // top class probability < confidenceThreshold.
    }

    fun close() { interpreter.close() }
}
```

The output array from the interpreter is a float array of length 10.
Map index → class name using the exact class list from this document
(in the same order as PlantVillage class indices: alphabetical by class folder name).

---

### B4 · JSON Storage Manager

**Produce:** `data/storage/ScanStorageManager.kt`

```kotlin
class ScanStorageManager(private val context: Context) {

    private val storageFile get() = File(context.filesDir, "scan_history.json")

    suspend fun saveRecord(record: ScanRecord)
    suspend fun loadAll(): List<ScanRecord>        // newest first
    suspend fun deleteAll()
    suspend fun getById(scanId: Int): ScanRecord?
}
```

Rules:
- `saveRecord` must use the atomic write pattern (write .tmp → rename).
- `loadAll` returns empty list if the file does not exist — never throws.
- All operations use `withContext(Dispatchers.IO)`.
- Uses `kotlinx.serialization.json.Json { prettyPrint = false }` for storage
  (compact for disk efficiency; pretty is only for export display).

---

### B5 · SAF Export / Import

**Produce:**
- `data/storage/ScanExporter.kt`
- `data/storage/ScanImporter.kt`

`ScanExporter`:
- Takes a `Uri` from `ACTION_CREATE_DOCUMENT`.
- Reads `scan_history.json` from `filesDir`.
- Writes it to the user-chosen URI via `contentResolver.openOutputStream`.
- Pretty-prints the JSON on export for human readability.

`ScanImporter`:
- Takes a `Uri` from `ACTION_OPEN_DOCUMENT`.
- Reads the file content from the URI.
- Attempts `Json.decodeFromString<Map<String, List<ScanRecord>>>(content)`.
- If decoding fails, return `ImportResult.Failure("Invalid file format")`.
- If decoding succeeds, call `ScanStorageManager.deleteAll()` then
  write each record with `saveRecord`.
- Return `ImportResult.Success(count)`.
- **Never touch existing storage if import validation fails.**

---

### B6 · Treatment Knowledge Base

**Produce:**
- `android/app/src/main/assets/treatments.json`
- `data/repository/TreatmentRepository.kt`

`treatments.json` must cover all 10 conditions × 4 growing methods.
Structure per condition:
```json
{
  "conditionId": "early_blight",
  "nameEn": "Early Blight",
  "nameAr": "اللفحة المبكرة",
  "stressType": "BIOTIC",
  "severityDefault": "HIGH",
  "treatments": [
    {
      "growingMethod": "GREENHOUSE",
      "treatmentType": "CHEMICAL",
      "urgencyLevel": "HIGH",
      "recommendationEn": "Apply copper-based fungicide (e.g. copper hydroxide 77% WP) at 2.5 g/L every 7 days. Remove and dispose of infected leaves outside the greenhouse.",
      "recommendationAr": "ضع مبيد فطري نحاسي (مثل هيدروكسيد النحاس 77%) بمعدل 2.5 جم/لتر كل 7 أيام. أزل الأوراق المصابة وتخلص منها خارج الدفيئة."
    }
  ]
}
```

Write all 40 treatment entries (10 conditions × 4 growing methods).
Arabic text must use formal agricultural botanical terminology.
Use UA-specific advice: reference UAE growing temperatures (45°C+),
hydroponic system constraints, and saline-soil considerations where relevant.

`TreatmentRepository.kt`:
```kotlin
class TreatmentRepository(context: Context) {
    // Loads treatments.json from assets once at init and caches it in memory.
    // Expensive file I/O on first load is acceptable; every subsequent
    // lookup is O(1) from the in-memory map.

    fun getTreatments(conditionId: String,
                      method: GrowingMethod): List<Treatment>

    fun getCondition(conditionId: String): ConditionInfo?
}
```

---

### B7 · CameraX Integration

**Produce:**
- `ui/scan/CameraScreen.kt`
- `ui/scan/ScanViewModel.kt`

`CameraScreen.kt` must:
- Embed a live camera preview using `PreviewView` inside `AndroidView`.
- Show a shutter button and a gallery picker button.
- Handle `CAMERA` permission: if denied, show a rationale screen with
  a "Grant Permission" button that re-triggers the request.
- On capture or gallery selection, validate the image:
  - Format must be JPEG or PNG — reject others with a Snackbar.
  - File size must be ≤ 10 MB — reject larger with a Snackbar.
- On valid image, call `ScanViewModel.onImageCaptured(bitmap)`.

`ScanViewModel.kt` must:
- Expose `uiState: StateFlow<ScanUiState>` with states:
  `Idle`, `Processing`, `Success(InferenceOutput)`, `LowConfidence`, `Error(String)`
- `fun onImageCaptured(bitmap: Bitmap)` → triggers inference on IO dispatcher.

---

### B8 · UI Screens

**Produce:** Five complete Composable screen files with their ViewModels.

#### B8.1 · HomeScreen.kt + HomeViewModel.kt
- Buttons: "Scan a Leaf", "View History", "Settings"
- Show last scan summary if `loadAll()` returns a non-empty list
- All text via `stringResource`

#### B8.2 · ScanScreen.kt (uses B7 CameraScreen as sub-composable)
- Loading overlay during inference (CircularProgressIndicator)
- Navigates to ResultScreen on `ScanUiState.Success`
- Shows inline LowConfidenceWarning on `ScanUiState.LowConfidence`
  with two buttons: "Retake" and "Show Anyway"

#### B8.3 · ResultScreen.kt + ResultViewModel.kt
`LowConfidenceWarning` composable (standalone, reusable):
```kotlin
@Composable
fun LowConfidenceWarning(onRetake: () -> Unit, onProceed: () -> Unit)
```

Full result layout (when confidence ≥ 60%):
- Condition name in English AND Arabic (both visible simultaneously)
- Confidence percentage
- StressBadge composable: red background for BIOTIC, amber for ABIOTIC
- SeverityChip composable: colour-coded LOW/MEDIUM/HIGH/CRITICAL
- GrowingMethodSelector: chip row for the 4 methods — selecting one
  re-filters the treatment list instantly
- TreatmentCard list: expandable cards per treatment

#### B8.4 · HistoryScreen.kt + HistoryViewModel.kt
- LazyColumn of scan records, newest first
- Each item: thumbnail (or placeholder icon), condition name,
  date/time formatted, stress badge
- Swipe-to-delete with undo Snackbar
- Tap → navigate to ResultScreen in read-only mode

#### B8.5 · SettingsScreen.kt + SettingsViewModel.kt
- Language selector (English / Arabic) → immediately applies locale
- Default growing method selector (4 options, radio buttons)
- "Export Scan History" button → launches `ACTION_CREATE_DOCUMENT`
- "Import Scan History" button → launches `ACTION_OPEN_DOCUMENT` with
  a confirmation dialog warning that import replaces current history
- "Delete All History" button → confirmation AlertDialog →
  `ScanStorageManager.deleteAll()` → show success Snackbar

---

### B9 · Bilingual Support + RTL Layout

**Produce:**
- `res/values/strings.xml` (English — complete, every UI string)
- `res/values-ar/strings.xml` (Arabic — complete, mirrors English exactly)
- `utils/LocaleHelper.kt`

`LocaleHelper.kt`:
```kotlin
object LocaleHelper {
    fun applyLocale(context: Context, language: Language): Context {
        // Wraps context with the selected locale.
        // Compose re-reads resources from the wrapped context,
        // which triggers RTL layout automatically when Arabic is selected
        // because Arabic is an RTL locale natively in Android.
    }
}
```

`strings.xml` must cover every label, button, error message, dialog title,
and status text in the app. Minimum 60 string entries.

`values-ar/strings.xml` must be a complete translation — no English fallbacks.

**RTL verification checklist** (write these as comments in `SettingsScreen.kt`):
```kotlin
// RTL Checklist — verify on Arabic emulator before submitting:
// [ ] Navigation back arrow points RIGHT (← becomes →)
// [ ] List items: icon on RIGHT, text on LEFT
// [ ] Buttons: primary action on LEFT (RTL convention)
// [ ] StressBadge: text reads right-to-left
// [ ] All padding/margin asymmetry uses start/end not left/right
```

---

### C1 · Functional Test Matrix

**Produce:** `docs/functional_tests.md`

A Markdown table covering FR-01 through FR-20 with columns:
`FR-ID | Precondition | Steps | Expected Result | Actual Result | Pass/Fail`

Fill in Expected Result for every FR. Leave Actual Result and Pass/Fail
as `TBD` — the team fills those in on a physical device.

---

### C2 · NFR Verification Report Template

**Produce:** `docs/nfr_verification.md` and `ml/results/nfr_verification.json`

The JSON must have this schema (fill numeric fields with 0 as placeholder):
```json
{
  "NFR-01": { "method": "Airplane mode test", "result": null, "pass": null },
  "NFR-02": { "method": "Stopwatch on Snapdragon 660 device",
               "measured_seconds": 0.0, "threshold_seconds": 3.0, "pass": null },
  "NFR-03": { "method": "eval_report.json test accuracy",
               "measured_accuracy": 0.0, "threshold": 0.90, "pass": null },
  "NFR-04": { "method": "Android Studio Analyze APK",
               "apk_size_mb": 0.0, "model_size_mb": 0.0,
               "apk_threshold_mb": 50, "model_threshold_mb": 15, "pass": null },
  "NFR-05": { "method": "Tap count from Home screen", "max_taps": 2, "pass": null },
  "NFR-06": { "method": "50 consecutive scan operations", "crashes": 0, "pass": null },
  "NFR-07": { "method": "Install on API 26 and API 34 emulators", "pass": null },
  "NFR-08": { "method": "mitmproxy traffic capture", "outbound_requests": 0, "pass": null }
}
```

---

### C3 · GitHub Repository Setup

**Produce:**
- `README.md` (complete, professional)
- `LICENSE` (MIT)
- `.gitignore`
- `.github/ISSUE_TEMPLATE/bug_report.md`

`README.md` structure:
```
# TomatoCare

[one-line description]

## What It Does
## Architecture
## Repository Structure
## ML Pipeline — How to Reproduce
## Android App — How to Build
## Model Card
## Requirements
## Team
## License
```

Model card section must include:
- Base model: MobileNetV3-Large (ImageNet pre-trained)
- Training data: PlantVillage tomato subset + UAE-specific augmentation
- Classes: [list all 10]
- Accuracy: ≥90% on UAE-specific held-out test set (exact figure from eval_report.json)
- Quantisation: float16
- Input: 224×224 RGB image, normalised to [0, 1]
- Output: softmax probability vector, length 10
- Known limitations: laboratory training data, UAE abiotic augmentation is synthetic

`.gitignore` must exclude: `build/`, `__pycache__/`, `*.pyc`, `venv/`,
`*.h5`, `*.keras` (checkpoints are large; only the `.tflite` is committed).

---

## HOW TO HANDLE BLOCKERS

If you encounter a situation not covered by this prompt:
1. Make the most sensible engineering decision.
2. Add a `// DECISION:` comment explaining your reasoning.
3. Continue without stopping to ask.

The only time you should stop and ask is if you are missing a piece of
information that is **impossible to infer** — for example, if the user's
local PlantVillage dataset path differs from what this prompt assumes.

---

## YOUR FIRST ACTION

Before writing any code, output the following and nothing else:

```
##############################################################
  TomatoCare — Capstone 2 Build Session Started
  Plan    : 15 micro-processes across 3 tracks
  Protocol: TomatoCare Coding Protocol v1.0
  Order   : A1 → A2 → A3 → A4 → A5 → A6 → A7 → A8
             B1 → B2 → B3 → B4 → B5 → B6 → B7 → B8 → B9
             C1 → C2 → C3
##############################################################

Understood. One clarifying question before I start:

Where is the PlantVillage tomato dataset located on your system?
(Expected: a folder with 10 subdirectories named after each disease class)
If you have already downloaded it, provide the path.
If not, I will write the download instructions as part of A2.
```

After the user answers, immediately begin A1 and work through every
micro-process to completion without stopping.
```
