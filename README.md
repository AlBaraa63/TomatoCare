# TomatoCare

A fully offline, bilingual (English / Arabic) Android app that diagnoses
tomato leaf diseases on-device using a 3-stage MobileNetV3 TFLite cascade
(leaf gate → tomato gate → 11-class disease classifier).

**Disease accuracy: 97.59% (lab) · 77.2% (field) — Model size: 9.87 MB — Min Android: API 26 — Zero network calls**

[![Android CI](https://github.com/AlBaraa63/TomatoCare/actions/workflows/android-ci.yml/badge.svg)](https://github.com/AlBaraa63/TomatoCare/actions/workflows/android-ci.yml)
![Min API 26](https://img.shields.io/badge/Android-API%2026%2B-3DDC84?logo=android&logoColor=white)
![Kotlin](https://img.shields.io/badge/Kotlin-Compose-7F52FF?logo=kotlin&logoColor=white)
![Network: none](https://img.shields.io/badge/network-none-success)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Key Metrics](#key-metrics)
3. [Repository Structure](#repository-structure)
4. [Quick Start](#quick-start)
5. [Documentation](#documentation)
6. [Engineering Practices](#engineering-practices)
7. [Team](#team)
8. [License](#license)

---

## What It Does

TomatoCare helps farmers and agronomists identify tomato leaf diseases instantly
without requiring internet access. It runs entirely on the device:

- **Captures** a photo via CameraX or imports from gallery
- **Gates** the image through a leaf check and a tomato check, rejecting
  non-leaf and non-tomato inputs before any diagnosis
- **Classifies** it into 1 of 11 conditions (10 diseases + healthy)
- **Displays** English and Arabic names, confidence score,
  Low/Medium/High/Critical severity badge, and treatment advice
- **Filters** treatments by growing method: Greenhouse, Open Field, Hydroponic,
  or Saline Soil (UAE-specific growing contexts)
- **Warns** when confidence < 60% instead of showing a low-quality guess
- **Stores** every scan locally with atomic JSON writes
- **Exports/imports** scan history via Android's Storage Access Framework

The app never declares the `INTERNET` permission — privacy and offline
operation are hard guarantees, not configuration options.

---

## Key Metrics

| Metric | Value | Target |
|---|---|---|
| Disease accuracy (held-out lab test, n=6,683) | **97.59%** | ≥ 90% |
| End-to-end accuracy (lab) | **97.19%** | — |
| Field accuracy (PlantDoc, n=79) | **77.2%** | — |
| Model size (3-stage cascade, float16) | **9.87 MB** (1.92 + 1.92 + 6.03) | ≤ 15 MB |
| Release APK size | **38.51 MB** | ≤ 50 MB |
| Confidence threshold | **0.60** | — |
| Min Android API | **26** (Android 8.0) | — |
| Target Android API | **34** (Android 14) | — |
| Network permission | **None** | None |

---

## Repository Structure

```
TomatoCare/
├── ml/                              # Track A — Python ML pipeline
│   ├── configs/
│   │   └── training_config.yaml    # single source of truth for all hyperparameters
│   ├── dataset/
│   │   ├── raw/                    # raw source images (gitignored, mount as Docker volume)
│   │   ├── augmented/              # offline-augmented training images (gitignored)
│   │   └── splits/                 # train.csv / val.csv / test.csv
│   ├── models/
│   │   ├── checkpoints/            # stage1_best.keras, stage2_best.keras (gitignored)
│   │   └── tflite/                 # stage1/stage2/stage3 float16 TFLite (3-stage cascade)
│   ├── results/                    # eval_report.json, confusion_matrix.png, etc.
│   ├── scripts/                    # A2..A8 pipeline scripts
│   └── utils/                      # dataset_loader.py, model_factory.py, seed.py
│
├── android/                        # Track B — Android app (Kotlin / Jetpack Compose)
│   ├── app/src/main/
│   │   ├── assets/
│   │   │   ├── stage1_leaf_float16.tflite        # 1.92 MB — leaf gate
│   │   │   ├── stage2_tomato_float16.tflite      # 1.92 MB — tomato gate
│   │   │   ├── stage3_disease_float16.tflite     # 6.03 MB — 11-class classifier
│   │   │   └── treatments.json                   # 32 KB treatment database
│   │   ├── kotlin/com/tomatocare/
│   │   │   ├── data/               # models, enums, storage, repository
│   │   │   ├── di/                 # AppContainer (hand-rolled DI)
│   │   │   ├── inference/          # TFLiteEngine, ImagePreprocessor, TomatoClasses
│   │   │   └── ui/                 # screens, ViewModels, components, navigation
│   │   └── res/
│   │       ├── values/strings.xml  # English strings
│   │       └── values-ar/strings.xml  # Arabic strings (RTL)
│   └── build.gradle.kts
│
├── docs/
│   ├── architecture.md             # system design and data flow
│   ├── ml-pipeline.md              # ML pipeline reference
│   ├── android-app.md              # Android app reference
│   ├── functional_tests.md         # FR-01..FR-28 test matrix
│   └── nfr_verification.md         # NFR sign-off procedure
```

---

## Quick Start

**ML (Python 3.12, TF 2.15.1):**

```bash
pip install -r ml/requirements.txt
python -m ml.scripts.eval_model
```

**Android (JDK 17 or 21, Android Studio Iguana+):**

```bash
cd android
./gradlew :app:assembleDebug
```

> **You need the 3 TFLite models first** — see below. The app **compiles and runs
> without them**, but every scan will fail until the models are in
> `android/app/src/main/assets/`.

### Getting the models

The three `.tflite` cascade models are **not committed** to git (binary
artifacts — see `.gitignore`). Obtain them one of two ways:

1. **Download a release (fastest).** Grab `stage1_leaf_float16.tflite`,
   `stage2_tomato_float16.tflite`, and `stage3_disease_float16.tflite` from the
   repository's [Releases](https://github.com/AlBaraa63/TomatoCare/releases)
   page and drop them into `android/app/src/main/assets/`.
2. **Produce them from the pipeline.** Run the ML pipeline scripts in `ml/scripts/` 
   which write the three files to `ml/models/tflite/`; then copy them into the assets folder.

Verify all three are present:

```bash
ls android/app/src/main/assets/stage{1_leaf,2_tomato,3_disease}_float16.tflite
```

---

## Documentation

| Document | Audience | What it covers |
|---|---|---|
| [docs/architecture.md](docs/architecture.md) | Everyone | System design, data flow, component diagram, key decisions |
| [docs/ml-pipeline.md](docs/ml-pipeline.md) | ML / QA | Stages A2–A8, config reference, training, evaluation, export |
| [docs/android-app.md](docs/android-app.md) | Android / QA | Screens, ViewModels, inference engine, storage, bilingual system |
| [docs/functional_tests.md](docs/functional_tests.md) | QA | FR-01..FR-28 test matrix with steps and expected results |
| [docs/nfr_verification.md](docs/nfr_verification.md) | QA / Architect | NFR sign-off procedure and current status |

---

## Engineering Practices

TomatoCare is engineered to production standards, not just to demo:

- **Unit-tested core logic** — 48 JVM unit tests (plus Compose UI tests) cover the ML↔app class-name
  contract, JSON serialization **and backward compatibility**, the severity
  heuristic, the Home dashboard statistics, and the feedback-flywheel label
  resolution. Run: `cd android && ./gradlew :app:test`.
- **Offline by construction** — the `INTERNET` permission is absent from the
  manifest; there is no network code to audit. All inference runs on-device.
- **Crash-safe storage** — scan history and settings use atomic
  temp-file-then-rename writes, so an interrupted write never corrupts data.
- **Robust input handling** — camera (`file://`) and gallery (`content://`)
  images both decode safely off the main thread; a failed decode shows a
  message instead of crashing, and result loading/empty/error states are
  handled explicitly.
- **Reactive settings** — theme switches apply live and a language change
  re-applies the locale, both driven by a single reactive settings flow.
- **On-device feedback flywheel** — users verify each diagnosis; verified images
  export (grouped by true label + manifest) as a retraining set to close the
  lab→field gap — entirely offline, user-owned data.
- **Bilingual + RTL + accessibility** — every user-facing string ships in
  English and Arabic; icons carry localised content descriptions.

---

## Team

| Name | Student ID | Role |
|---|---|---|
| AlBaraa AlOlabi | 202210405 | CV Engineer — dataset prep, 3-stage MobileNetV3 cascade training, calibration, evaluation, TFLite export |
| Ahmed Saeed Ahmed Mohamed | 202211615 | Android Developer (UI/UX) — Compose screens, RTL layout, bilingual toggle |
| Kazi Mahir Al Wafi | 202211829 | Android Developer (Backend) — CameraX, preprocessing, TFLite engine, JSON storage |
| Iyad El Boussi | 202111261 | System Architect & Docs — requirements, UML, design, report |
| Fares Muaatasem Awda | 202211410 | QA & Integration — functional testing, device compatibility |

---

## License

[MIT](LICENSE)
