# TomatoCare

A fully offline, bilingual (English / Arabic) Android app that diagnoses
tomato leaf diseases on-device using a MobileNetV3-Large TFLite model.

## What It Does

- Takes a photo of a tomato leaf (CameraX) or imports one from the gallery.
- Runs **on-device** TFLite inference (no network calls, ever).
- Classifies it into one of 10 conditions: 1 healthy + 9 diseases.
- Shows English and Arabic names, confidence, a biotic/abiotic stress badge,
  a Low/Medium/High/Critical severity chip, and localised treatment advice
  tailored to one of four growing methods (greenhouse, open field, hydroponic,
  saline soil — the latter two are UAE-specific concerns).
- If confidence < 60 %, shows a Low Confidence Warning instead of a guess.
- Stores every scan locally in `filesDir/scan_history.json` (atomic write).
- Supports SAF export/import for portable history files.
- Bilingual UI with full RTL support.

## Architecture

Three layers, hand-rolled DI:

| Layer | Components |
|---|---|
| Presentation | Jetpack Compose + CameraX; one Activity, five screens (Home / Scan / Result / History / Settings) |
| Application | `ScanViewModel`, `ResultViewModel`, `HistoryViewModel`, `SettingsViewModel`, `HomeViewModel`; `TFLiteEngine`; `ImagePreprocessor` |
| Data | `ScanStorageManager` (JSON, atomic write), `TreatmentRepository` (assets/treatments.json), `ScanExporter` / `ScanImporter` (SAF), `SettingsStore` |

The TFLite model is float16-quantised, mmap'd directly from `assets/` so no
heap allocation is needed at load time. Class index order is alphabetical
(TF Keras' `image_dataset_from_directory` default with `class_names=` pinned
explicitly in `dataset_loader.py`) and is the single source of truth in
`TFLiteEngine.CLASS_NAMES`.

## Repository Structure

```
tomatocare/
├── ml/                              # Track A — Python ML pipeline
│   ├── configs/training_config.yaml
│   ├── dataset/{raw,augmented,splits}/
│   ├── models/{checkpoints,tflite}/
│   ├── results/                     # eval_report.json, etc
│   └── scripts/                     # A2..A8 + utils/
├── android/                         # Track B — Android app
│   ├── app/src/main/
│   │   ├── assets/                  # tomatocare_model_float16.tflite + treatments.json
│   │   ├── kotlin/com/tomatocare/   # screens, VMs, inference, storage, repo
│   │   └── res/values{,-ar}/        # bilingual strings
│   └── build.gradle.kts
└── docs/                            # functional_tests.md, nfr_verification.md
```

## ML Pipeline — How to Reproduce

Requires Python 3.10–3.12 with TensorFlow 2.13–2.15. GPU strongly recommended.

```bash
pip install -r ml/requirements.txt

# Data: A2 has two modes, selected automatically from training_config.yaml.
#
# Mode A — pre-split (preferred): set pre_split_root in training_config.yaml
#   to a folder that already contains train/val/test subfolders with one
#   class folder each. Source folder names are remapped to canonical names
#   via the class_aliases map. This project ships pre_split_root pointing at
#   the cleaned, deduplicated dataset inherited from a prior TomatoCare
#   attempt (32,653 images, 91.17% PyTorch CNN baseline). Sources merged
#   into that dataset:
#     - Kaggle: abdallahalidev/plantvillage-dataset
#     - Kaggle: nirmalsankalana/plantdoc-dataset
#     - Kaggle: mamtag/tomato-village
#     - Kaggle: kaustubhb999/tomatoleaf
#
# Mode B — multi-root stratified split (fallback): set pre_split_root to null
# and drop raw datasets into ml/dataset/raw/. Recommended sources:
#     - Kaggle: arjuntejaswi/plant-village → ml/dataset/raw/plantvillage/
#     - Mendeley DOI 10.17632/tywbtsjrjv.1 → ml/dataset/raw/mendeley/

python -m ml.scripts.prepare_plantvillage   # A2 — inventory + split (pre-split or stratified)
python -m ml.scripts.augment_uae            # A3 — UAE-domain augmentation (4x)
python -m ml.scripts.train_stage1           # A5 — head only, EarlyStop patience 5
python -m ml.scripts.train_stage2           # A6 — unfreeze last 30 layers, LR 1e-4
python -m ml.scripts.eval_model             # A7 — must hit 90 % or exits 1
python -m ml.scripts.export_tflite          # A8 — float16, <= 15 MB

# Copy the produced .tflite into the Android app:
cp ml/models/tflite/tomatocare_model_float16.tflite \
   android/app/src/main/assets/
```

Every script implements caching: re-running a finished stage skips work and
reloads the cached output. Delete the relevant artifact under
`ml/models/checkpoints/`, `ml/dataset/`, or `ml/results/` to force re-run.

## Android App — How to Build

Requires Android Studio (Iguana or newer) and **JDK 17 or 21** on PATH. JDK 26
will trigger Gradle's foojay-resolver to download JDK 17 automatically per the
toolchain pin in `settings.gradle.kts`.

```bash
cd android
./gradlew :app:assembleDebug      # debug APK
./gradlew :app:assembleRelease    # release APK (minified, ~ 30 MB with model)
./gradlew :app:installDebug       # install on connected device
```

Before the first build:
1. Copy `tomatocare_model_float16.tflite` into `app/src/main/assets/` (see ML
   step above).
2. Delete the `tomatocare_model_float16.tflite.PLACEHOLDER.md` companion file
   in that directory.

## Model Card

| Field | Value |
|---|---|
| Base model | MobileNetV3-Large (ImageNet pretrained, `include_preprocessing=False`) |
| Head | GlobalAveragePooling2D → Dropout(0.4) → Dense(10, softmax) |
| Input | 224×224 RGB, normalised to [0, 1] |
| Output | Softmax probability vector of length 10 |
| Quantisation | float16 (post-training, dynamic range) |
| Training data | 32,653 images merged from PlantVillage + PlantDoc + TomatoVillage + Tomatoleaf (4 Kaggle sources, deduplicated and split by the previous TomatoCare attempt) + offline UAE-domain augmentation |
| Baseline (carried over) | 91.17 % from a custom PyTorch CNN (TomatoCareNet) trained on the same data. Transfer-learning MobileNetV3-Large in this project targets ≥ 90 % with a smaller, mobile-friendly footprint. |
| UAE augmentation | brightness × contrast × red-channel shift × Gaussian blur × rotation × flip × zoom (3 variants per source image) |
| Splits | 70 % train / 15 % val / 15 % test, stratified, random_state 42 |
| Stage 1 | head only, LR 1e-3, up to 30 epochs, EarlyStopping patience 5 |
| Stage 2 | unfreeze last 30 layers, LR 1e-4, up to 10 epochs |
| Accuracy target | ≥ 90 % on held-out test set (build fails below) |
| Confidence threshold | 0.60 (below → Low Confidence Warning) |
| Size budget | .tflite ≤ 15 MB; release APK ≤ 50 MB |
| Classes | Tomato_Bacterial_spot · Tomato_Early_blight · Tomato_healthy · Tomato_Late_blight · Tomato_Leaf_Mold · Tomato_Septoria_leaf_spot · Tomato_Spider_mites_Two_spotted_spider_mite · Tomato_Target_Spot · Tomato_Yellow_Leaf_Curl_Virus · Tomato_mosaic_virus |
| Known limitations | Training data is laboratory-style; UAE abiotic-stress augmentation is synthetic, not from field photos. Arabic treatment text was AI-generated and flagged for native-speaker agronomist review. |

## Requirements

- **Min Android API:** 26 (Android 8.0)
- **Target Android API:** 34 (Android 14)
- **Minimum RAM:** 2 GB
- **Storage:** ~30 MB APK + scan history grows ~1 KB per scan (+ image file)
- **Permissions:** CAMERA (required); READ_EXTERNAL_STORAGE only on API ≤ 28

The app **never** declares the INTERNET permission. NFR-01 and NFR-08 are
hard guarantees.

## Verification

See [docs/functional_tests.md](docs/functional_tests.md) for FR-01..FR-20
test matrix and [docs/nfr_verification.md](docs/nfr_verification.md) for the
NFR sign-off procedure. Machine-readable NFR results live at
[ml/results/nfr_verification.json](ml/results/nfr_verification.json).

## Team

Capstone 2 student project. Fill in team names before submission.

## License

[MIT](LICENSE).
