# TomatoCare

A fully offline, bilingual (English / Arabic) Android app that diagnoses
tomato leaf diseases on-device using a MobileNetV3-Large TFLite model.

**Model accuracy: 95.60% — Model size: 5.75 MB — Min Android: API 26 — Zero network calls**

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Key Metrics](#key-metrics)
3. [Repository Structure](#repository-structure)
4. [Quick Start](#quick-start)
5. [Documentation](#documentation)
6. [Team](#team)
7. [License](#license)

---

## What It Does

TomatoCare helps farmers and agronomists identify tomato leaf diseases instantly
without requiring internet access. It runs entirely on the device:

- **Captures** a photo via CameraX or imports from gallery
- **Classifies** it into 1 of 10 conditions (9 diseases + healthy)
- **Displays** English and Arabic names, confidence score, biotic/abiotic stress
  badge, Low/Medium/High/Critical severity, and treatment advice
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
| Test-set accuracy | **95.60%** | ≥ 90% |
| Model file size | **5.75 MB** (float16) | ≤ 15 MB |
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
│   │   └── tflite/                 # tomatocare_model_float16.tflite (deployment artifact)
│   ├── results/                    # eval_report.json, confusion_matrix.png, etc.
│   ├── scripts/                    # A2..A8 pipeline scripts
│   └── utils/                      # dataset_loader.py, model_factory.py, seed.py
│
├── android/                        # Track B — Android app (Kotlin / Jetpack Compose)
│   ├── app/src/main/
│   │   ├── assets/
│   │   │   ├── tomatocare_model_float16.tflite   # 5.75 MB, mmap'd at runtime
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
│   ├── getting-started.md          # new member onboarding
│   ├── architecture.md             # system design and data flow
│   ├── ml-pipeline.md              # ML pipeline reference
│   ├── android-app.md              # Android app reference
│   ├── docker.md                   # Docker usage guide
│   ├── functional_tests.md         # FR-01..FR-20 test matrix
│   └── nfr_verification.md         # NFR sign-off procedure
│
├── Dockerfile.ml                   # ML pipeline container
├── Dockerfile.android              # Android build container
├── docker-compose.yml              # orchestration
└── .dockerignore
```

---

## Quick Start

### Option A — Docker (recommended for new members)

No local toolchain setup required.

```bash
# Clone
git clone <repo-url>
cd TomatoCare

# Run ML evaluation against the pre-trained model
docker compose run --rm ml python -m ml.scripts.eval_model

# Build an Android debug APK
docker compose --profile android run --rm android-build
# APK lands in: android/app/build/outputs/apk/debug/
```

See [docs/docker.md](docs/docker.md) for GPU training and full workflow.

### Option B — Native setup

See [docs/getting-started.md](docs/getting-started.md) for step-by-step
instructions for both the ML and Android tracks.

**ML (Python 3.10, TF 2.15.1, Linux/WSL2 recommended):**

```bash
pip install -r ml/requirements.txt
python -m ml.scripts.eval_model
```

**Android (JDK 17 or 21, Android Studio Iguana+):**

```bash
cd android
./gradlew :app:assembleDebug
```

---

## Documentation

| Document | Audience | What it covers |
|---|---|---|
| [docs/getting-started.md](docs/getting-started.md) | Everyone | Prerequisites, clone, first build for both tracks |
| [docs/architecture.md](docs/architecture.md) | Everyone | System design, data flow, component diagram, key decisions |
| [docs/ml-pipeline.md](docs/ml-pipeline.md) | ML / QA | Stages A2–A8, config reference, training, evaluation, export |
| [docs/android-app.md](docs/android-app.md) | Android / QA | Screens, ViewModels, inference engine, storage, bilingual system |
| [docs/docker.md](docs/docker.md) | Everyone | Docker services, volumes, GPU support, CI usage |
| [docs/functional_tests.md](docs/functional_tests.md) | QA | FR-01..FR-20 test matrix with steps and expected results |
| [docs/nfr_verification.md](docs/nfr_verification.md) | QA / Architect | NFR sign-off procedure and current status |

---

## Team

| Name | Student ID | Role |
|---|---|---|
| AlBaraa AlOlabi | 202210405 | CV Engineer — dataset prep, MobileNetV3-Large training, evaluation, TFLite export |
| Ahmed Saeed Ahmed Mohamed | 202211615 | Android Developer (UI/UX) — Compose screens, RTL layout, bilingual toggle |
| Kazi Mahir Al Wafi | 202211829 | Android Developer (Backend) — CameraX, preprocessing, TFLite engine, JSON storage |
| Iyad El Boussi | 202111261 | System Architect & Docs — requirements, UML, design, report |
| Fares Muaatasem Awda | 202211410 | QA & Integration — functional testing, device compatibility |

---

## License

[MIT](LICENSE)
