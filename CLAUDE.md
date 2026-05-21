# CLAUDE.md — TomatoCare Capstone 2

> **Read this file completely before writing a single line of code.**
> This is the source of truth for how you work on this project.
> It overrides any assumption you bring from general knowledge.

---

## 1. What this project is

**TomatoCare** is an offline-first bilingual Android application that:
- Captures or selects a tomato leaf photo
- Runs on-device CNN inference (MobileNetV3-Large, TFLite float16)
- Classifies the leaf into one of 10 conditions (9 diseases + healthy)
- Distinguishes **biotic** (fungal/bacterial/viral) from **abiotic** (sunscald, salinity chlorosis, heat injury) stress — critical for UAE farming context
- Returns a result with condition name, confidence, severity badge, and treatment recommendations
- Works in **English and Arabic (RTL)**, fully offline, no internet permission

**Capstone 1 is the design baseline.** All architectural decisions there inherit into this build unless explicitly overridden by a Decisions Log entry.

---

## 2. Your role as an agent

You are a **Claude Code implementation agent**. You are not the planner — the plan already exists in Notion. Your job is to:

1. **Read** the assigned task from Notion before starting.
2. **Implement** exactly what the task specifies — no more, no less.
3. **Follow** the interface contracts without deviation.
4. **Update** Notion when done (status → Done, note any discoveries).
5. **Log** any meaningful decision you made during implementation.
6. **Never** touch files outside your task's `Files Touched` list.

If a task is ambiguous or the contracts don't cover a case you've hit: **stop, write a note in the task card, and surface the question**. Do not invent a solution and proceed silently.

---

## 3. Notion workspace — all links

This is your command centre. Use it constantly.

| Page | URL | Purpose |
|---|---|---|
| **Hub** | https://www.notion.so/36527e2675a681de837bdb8a38c10f39 | Project overview and navigation |
| **Roadmap** | https://www.notion.so/36527e2675a68185b55eeb874829aa6c | Five phases, exit criteria per phase |
| **Contracts** | https://www.notion.so/36527e2675a681efbc57e10f1ea291c5 | **Read first. Frozen interfaces. Non-negotiable.** |
| **Tasks DB** | https://www.notion.so/b1f3204ff96d4e34b370fc9d0db861a5 | Your task queue |
| **Decisions Log** | https://www.notion.so/c7c9a292bf3d4394ac1c62474a08f8cc 
 | Log every meaningful choice you make |
| **Edge Cases** | https://www.notion.so/656ab543e3c94943b526888bcaf99319 | Non-happy-path scenarios — read before writing any handler |
| **Model Spec** | https://www.notion.so/36527e2675a681219c24fabeec552ad1 | Architecture, training, export, evaluation |
| **App Spec** | https://www.notion.so/36527e2675a681deb15ae8632d74621f | Screens, navigation, stack, permissions |
| **Risks** | https://www.notion.so/36527e2675a681d5a841e849fde10563 | Known risks and mitigations |
| **References** | https://www.notion.so/36527e2675a6818fb5f7e2606013faf6 | Papers, docs, datasets |

---

## 4. Task protocol — do this every time

### Before writing any code

```
1. Open your assigned task card in the Tasks DB.
2. Read: Task title, Why, Where, Done When, Files Touched, Dependencies.
3. Open Contracts and read the relevant section for your workstream.
4. Check that all Dependencies are marked Done. If not — stop and report.
5. Set task Status → "In progress".
6. Create your git branch: phase{N}/{workstream}/{slug}
   Example: phase1/model/synthetic-augmentation
            phase1/app/results-screen
            phase0/integration/lock-contracts
```

### While implementing

```
- Touch ONLY the files listed in "Files Touched" on the task card.
- If you need to touch an unlisted file, stop and check with AlBaraa first.
- If you make a non-trivial design choice (library selection, data structure,
  algorithm, deviation from Capstone 1 spec), add a row to the Decisions Log
  immediately — do not leave it for later.
- Commit small and often. Message format:
  [TC-{id}] Short description of what this commit does
  Example: [TC-03] Add Laplacian blur pre-check before inference
```

### When done

```
1. Verify your "Done When" criteria — every single one, not just the easy ones.
2. Run on real hardware if the task is app-side (S10+ is the minimum bar).
3. Set task Status → "Done".
4. Add a note to the task card: what you built, any caveats, anything the next
   task in the chain should know.
5. If you discovered a new edge case not in the Edge Cases DB, add it.
6. Open a PR to main. Squash merge only.
```

---

## 5. Interface contracts — memorise these

These are frozen. You cannot change them without a Decisions Log entry and AlBaraa's sign-off.

### 5.1 Model input

```
Tensor shape:  float32[1, 224, 224, 3]   (NHWC, RGB)
Preprocessing:
  1. Decode image to RGB (not BGR, not RGBA).
  2. Centre-crop to square, resize to 224×224 — bilinear interpolation.
  3. Divide by 255.0 → values in [0.0, 1.0].
  4. DO NOT apply ImageNet mean/std normalisation.

This preprocessing must be byte-for-byte equivalent in:
  - Python training pipeline  (model/src/augment/preprocess.py)
  - Python sanity check       (model/scripts/sanity_check.py)
  - Kotlin inference engine   (android/.../InferenceEngine.kt)
```

### 5.2 Model output

```
Tensor shape: float32[1, 10]   (softmax probabilities)
Class mapping: defined in android/app/src/main/assets/model/labels.json
               and model/src/data/class_map.py
               — both files must use identical index → key ordering.
```

### 5.3 Model artefact location

```
android/app/src/main/assets/model/tomatocare_v{MAJOR}.{MINOR}.tflite
android/app/src/main/assets/model/labels.json
android/app/src/main/assets/model/model_card.md
```

### 5.4 Scan record JSON schema (v1)

```json
{
  "schema_version": 1,
  "scan_id": "uuid-v4",
  "timestamp": "ISO-8601",
  "image_path": "file://...",
  "growing_method": "greenhouse|open_field|hydroponic|saline_soil",
  "model_version": "1.0",
  "top_prediction": {
    "class_key": "early_blight",
    "confidence": 0.92,
    "is_primary": true,
    "severity": "low|medium|high|critical",
    "stress_type": "biotic|abiotic"
  },
  "alternatives": [
    { "class_key": "late_blight", "confidence": 0.06 }
  ],
  "low_confidence": false
}
```

### 5.5 Repository layout — do not deviate

```
/
├── README.md
├── .gitignore
├── CLAUDE.md                          ← this file
├── /model
│   ├── requirements.txt               ← pinned, no version ranges
│   ├── /scripts
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   ├── export_tflite.py
│   │   └── sanity_check.py            ← parity test Python vs Kotlin
│   ├── /src
│   │   ├── /data                      ← dataset loading, class_map.py
│   │   ├── /augment                   ← standard + UAE synthetic transforms
│   │   ├── /model                     ← model definition, head
│   │   └── /eval                      ← metrics, confusion matrix
│   ├── /data                          ← gitignored
│   ├── /models                        ← gitignored
│   ├── /notebooks                     ← exploration only, not production
│   └── /reports
└── /android
    └── (standard Android Studio project structure)
```

### 5.6 Naming conventions

```
Class keys:       lowercase_snake_case   e.g. early_blight
Growing methods:  lowercase_snake_case   e.g. saline_soil
Severity values:  lowercase              e.g. critical
Branch names:     phase{N}/{workstream}/{slug}
Commit prefix:    [TC-{task_id}]
```

---

## 6. Tech stack

### Model side

```
Language:     Python 3.11+
Framework:    TensorFlow 2.x (use tf.keras)
Base model:   MobileNetV3-Large, ImageNet weights
Export:       TFLite with float16 quantisation
GPU:          Local machine — verify CUDA before starting any training task
Dataset:      PlantVillage tomato subset (10 classes)
Augmentation: torchvision or tf.keras.layers (standard) +
              custom UAE synthetic transforms (brightness, dust, heat-glare)
```

### App side

```
Language:      Kotlin
UI:            Jetpack Compose
Camera:        CameraX  (Phase 2+; gallery picker in Phase 1)
Inference:     TensorFlow Lite (LiteRT) — lock version in build.gradle
Serialisation: kotlinx.serialization (NOT Gson, NOT Moshi)
Navigation:    Compose Navigation
Concurrency:   Kotlin Coroutines + Flow
Storage:       App-private JSON file  (NOT Room, NOT SQLite — CR-04)
File I/O:      Storage Access Framework for export/import
Min SDK:       26 (Android 8.0 Oreo)
No INTERNET permission — the app is offline-only (CR-01)
```

---

## 7. Edge cases — read before building any handler

The Edge Cases DB is the canonical list. Before building any input validation,
error handler, or fallback UI, check there first. Do not invent behaviour that
contradicts what's already designed.

**Critical cases to handle by Phase:**

### Phase 1 (vertical slice minimum)
- `EC` — No image selected → show "please select an image" state, no crash
- `EC` — Inference returns null or throws → show "analysis failed, try again"

### Phase 2 (expand)
- Image blur detected (Laplacian variance < threshold) → warn user, allow override
- Image too dark or too bright (mean luminance check) → warn user
- Image too small (< 224×224 before crop) → reject with message
- Camera permission denied → graceful permission rationale screen
- Storage full → catch IOException, show storage full message
- Model .tflite fails to load → show "model unavailable" and log
- Empty history (first launch) → empty state illustration, not blank screen

### Phase 4 (quality hardening)
- Top-1 vs top-2 confidence margin < 0.15 → show "two possible conditions" UI
- JSON history file corrupted → catch parse exception, offer to reset history
- SAF export to read-only location → catch SecurityException, show message

**The 60% Low Confidence Warning (all phases from 1 onward):**
```
if (topConfidence < 0.60) → show LOW CONFIDENCE banner on Results screen
```

---

## 8. Parallel agent rules

Multiple agents may run simultaneously. To avoid collisions:

1. **Check `Files Touched` on your task card.** If another task in progress
   shares even one file with yours — coordinate before starting.

2. **Each task gets its own branch.** Never commit to main directly.
   Never commit to another task's branch.

3. **The Contracts page is read-only for agents.** If you think a contract
   needs changing, write a note and surface it. Do not edit Contracts.

4. **Natural safe split:** `/model` and `/android` are almost always parallel-safe.
   Within a workstream, check `Parallel-Safe With` on the task card.

5. **Integration tasks are never parallel-safe with each other.**
   Only one integration task runs at a time.

---

## 9. Decisions log — what to log

Log a Decision entry whenever you:
- Choose between two or more libraries/approaches
- Deviate from the Capstone 1 spec for any reason
- Pick a threshold, constant, or magic number (e.g. the 60% confidence threshold,
  the Laplacian blur threshold value, the top-2 margin value)
- Defer something explicitly (with a reason)
- Discover that a contract needs updating

**Decision entry format (add a row to the Decisions Log DB):**
```
Decision:          Short title of what was decided
Status:            Accepted
Date:              Today
Area:              AI / Model | Android / App | Architecture | Scope | Process
Context:           What problem prompted this
Options Considered: What alternatives you considered
Choice:            What you chose
Rationale:         Why — be specific
Consequences:      What this means in practice, what is traded off
```

---

## 10. What NOT to do

```
✗ Do not add internet permission or any network call anywhere.
✗ Do not use Room or SQLite — JSON flat file only per CR-04.
✗ Do not apply ImageNet mean/std normalisation in preprocessing.
✗ Do not use Gson or Moshi — kotlinx.serialization only.
✗ Do not commit trained model weights or datasets to git.
✗ Do not use CameraX in Phase 1 — gallery picker only.
✗ Do not edit the Contracts page without AlBaraa sign-off.
✗ Do not touch files outside your task's "Files Touched" list.
✗ Do not merge to main without a PR — squash merge only.
✗ Do not skip the sanity_check.py parity test before Phase 1 closes.
✗ Do not hardcode Arabic strings — all strings go through string resources.
✗ Do not assume the training preprocessing matches the Kotlin preprocessing
  — verify with sanity_check.py every time the model is retrained.
```

---

## 11. Quick-start for a new task

```bash
# 1. Pull latest main
git checkout main && git pull

# 2. Create your branch
git checkout -b phase1/app/results-screen

# 3. Open your task card, read everything
# https://www.notion.so/b1f3204ff96d4e34b370fc9d0db861a5

# 4. Open Contracts, read your workstream section
# https://www.notion.so/36527e2675a681efbc57e10f1ea291c5

# 5. Set task status → In Progress in Notion

# 6. Build. Commit often: git commit -m "[TC-05] Add results screen scaffold"

# 7. Verify Done When criteria on the task card

# 8. Set task status → Done. Add implementation note to the card.

# 9. Open PR to main. Squash merge.
```

---

*Last updated: May 2026 — AlBaraa AlOlabi, Capstone 2, Al Ain University*
*Notion hub: https://www.notion.so/36527e2675a681de837bdb8a38c10f39*
