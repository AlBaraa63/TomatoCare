# ML Pipeline

This document is the complete reference for the TomatoCare ML pipeline (Track A).
It covers every stage from raw images to the production-ready 3-stage TFLite
cascade.

> **Updated 2026-05-28** to reflect the **deployed cascade** architecture.
> Metrics are sourced from `ml/reports/eval_deployed.json` (single source of truth).

---

## Table of Contents

1. [Overview](#overview)
2. [Deployed architecture — 3-stage cascade](#deployed-architecture--3-stage-cascade)
3. [Configuration](#configuration)
4. [Stage A2 — Data preparation](#stage-a2--data-preparation)
5. [Augmentation — deployed vs experimental](#augmentation--deployed-vs-experimental)
6. [Training — two-phase per model](#training--two-phase-per-model)
7. [Temperature calibration](#temperature-calibration)
8. [Stage A7 — Evaluation](#stage-a7--evaluation)
9. [Stage A8 — TFLite export](#stage-a8--tflite-export)
10. [Class list (deployed)](#class-list-deployed)
11. [Results summary](#results-summary)
12. [Utilities reference](#utilities-reference)
13. [Re-running specific stages](#re-running-specific-stages)

---

## Overview

The pipeline produces a **3-stage TFLite cascade** (leaf gate → tomato gate →
11-class disease classifier). Each script reads hyperparameters from
`ml/configs/training_config.yaml` and caches its output — if the artifact
already exists it skips processing.

```
A2 → Train (×3 stages) → A6.5 → A7 → A8
```

Run all stages in order from the **repo root** (not from inside `ml/`):

```bash
python -m ml.scripts.prepare_plantvillage
python -m ml.scripts.train_stage1
python -m ml.scripts.train_stage2
python -m ml.scripts.calibrate_temperature
python -m ml.scripts.eval_model
python -m ml.scripts.export_tflite
```

---

## Deployed architecture — 3-stage cascade

The deployed model is NOT a single classifier. It is a three-stage cascade
where each stage is a separate MobileNetV3 model:

| Stage | Model | Purpose | Size |
|-------|-------|---------|------|
| 1 — Leaf gate | MobileNetV3-Small | Reject non-leaf images (e.g. sky, hand, table) | 1.92 MB |
| 2 — Tomato gate | MobileNetV3-Small | Reject non-tomato leaves (e.g. rose, basil) | 1.92 MB |
| 3 — Disease classifier | MobileNetV3-Large | Classify into 11 classes (10 diseases + healthy) | 6.03 MB |
| **Total** | | | **9.87 MB** |

**Why a cascade?** The earlier v1 prototype used a single MobileNetV3-Large with
a `not_tomato` reject class. This failed: non-tomato inputs were silently
labeled as diseases with high confidence. The cascade solves this — each gate
has a dedicated rejection objective, and hard-rejects before the disease
classifier ever runs. See the master report (`presentation_prep/reports/FINAL_REPORT_REVISED.md`,
§1.4 and §3.8.3) for the full evolution story.

**Gate safety metrics:**
- Non-leaf rejection: 99.55%
- Non-tomato-leaf rejection: 99.37%
- Cross-species leak: 0.05%

---

## Configuration

**`ml/configs/training_config.yaml`** — single source of truth.

### Reproducibility

```yaml
seed: 42
```

All random operations (splits, shuffles, augmentation seeds, Keras weight init)
use this seed for reproducibility.

### Input dimensions and batching

```yaml
img_size: 224        # pixels — must match MobileNetV3-Large input
batch_size: 32
```

### Training stages

```yaml
stage1_epochs: 30        # max epochs; EarlyStopping will stop earlier
stage1_lr: 0.001         # Adam LR for head-only training
stage1_patience: 5       # EarlyStopping: stop if val_loss doesn't improve for 5 epochs

stage2_epochs: 10
stage2_lr: 0.0001        # 10× lower to avoid catastrophic forgetting
stage2_patience: 3       # tighter patience — fine-tuning overfits faster
fine_tune_from_layer: -30  # unfreeze the last 30 layers of MobileNetV3-Large
```

### Architecture

```yaml
dropout_rate: 0.4
```

### Loss

```yaml
loss:
  label_smoothing: 0.05
```

Label smoothing slightly reduces raw accuracy but produces much better
calibrated softmax probabilities. This matters because the Android app uses a
0.60 confidence threshold — that threshold is only meaningful if the model is
well-calibrated.

### Class weights

```yaml
class_weights:
  mode: balanced
```

`balanced` computes `n_samples / (n_classes × count_c)` per class. This
prevents larger classes from dominating the loss over smaller disease classes.

### Inference gates

```yaml
confidence_threshold: 0.60    # below this → Low Confidence Warning on Android
target_accuracy: 0.90         # A7 exits 1 if overall accuracy is below this
notaleaf_min_recall: 0.80     # A7 exits 1 if OOD recall is below this
max_false_reject_rate: 0.15   # A7 exits 1 if too many real leaves are rejected
tflite_max_size_mb: 15        # A8 exits 1 if .tflite exceeds this
```

### Dataset paths (relative to `ml/`)

```yaml
pre_split_root: "C:/Users/POTATO/Desktop/Code/tomato-care/data/processed"
# Set to null for fallback multi-root mode.
# Docker users: set to /app/ml/dataset/processed (see docker.md)
```

---

## Stage A2 — Data preparation

**Script:** `ml/scripts/prepare_plantvillage.py`
**Output:** `ml/dataset/splits/train.csv`, `val.csv`, `test.csv`
**Cached by:** existence of all three CSV files

### Two modes

**Mode A (preferred) — pre-split dataset:**

If `pre_split_root` in the config points to a valid directory that already
contains `train/`, `val/`, and `test/` subfolders (each with one folder per
class), the script skips any splitting and simply walks the folders to emit
the three CSVs. Folder names are remapped to canonical class names via the
`class_aliases` map in the config.

Example alias mapping:
```yaml
class_aliases:
  Bacterial_spot: Tomato_Bacterial_spot
  Healthy: Tomato_healthy
  # ...
```

**Mode B (fallback) — raw multi-root stratified split:**

Set `pre_split_root: null`. The script walks all directories listed under
`dataset_roots`, merges the images, applies `class_aliases`, and performs a
stratified 70/15/15 split with `random_state=seed`.

### Dataset used in this project

The pre-split dataset (Mode A) contains 32,653 images merged and deduplicated
from four Kaggle sources:

| Source | Kaggle slug |
|---|---|
| PlantVillage | `abdallahalidev/plantvillage-dataset` |
| PlantDoc | `nirmalsankalana/plantdoc-dataset` |
| Tomato Village | `mamtag/tomato-village` |
| Tomatoleaf | `kaustubhb999/tomatoleaf` |

Split sizes: **train 25,100 / val 3,988 / test 3,565** (stratified, seed=42).

---

## Augmentation — deployed vs experimental

### Deployed model: minimal (flip-only)

The **deployed** cascade uses horizontal-flip-only augmentation. This is the
`ctrl` (control) configuration that produced the authoritative evaluation
numbers in `ml/reports/eval_deployed.json`.

### Experimental: heavy field-simulation augmentation (REJECTED)

A heavy augmentation stack (rotation, zoom, JPEG compression, motion blur,
perspective warp, cutout, brightness/contrast variation) was tested as
Experiment 1 in the master report (Ch 7). It was designed to simulate
real-world phone-camera conditions.

**Result: field accuracy dropped by 11.4 percentage points** (77.2% → 65.8%).
The heavy augmentation was rejected. The finding — together with three other
negative experiments — triangulated that **leaf appearance, not background,
dominates the lab-to-field domain gap**. Synthetic transforms cannot close it;
real field data (via the in-app feedback flywheel) is the planned path forward.

A separate lighting-only augmentation (brightness/contrast variation) was also
tested: it maintained lab accuracy (~97.9%) but reduced field accuracy by 3.8
percentage points (77.2% → 73.4%). Also rejected for the deployed model.

> **Note:** the `augment_uae.py` script still exists in `ml/scripts/` as a
> historical artifact. It is NOT part of the deployed training pipeline.

---

## Training — two-phase per model

Each of the three cascade models is trained using the same two-phase strategy.
The disease classifier (Stage 3, MobileNetV3-Large) is documented here; the
two gates (MobileNetV3-Small) follow the same approach with their own datasets.

### Phase 1 — head-only (A5)

**Script:** `ml/scripts/train_stage1.py`
**Output:** `ml/models/checkpoints/stage1_best.keras`

1. Load training data using `dataset_loader.build_train_dataset()`.
2. Compute per-class weights (`balanced` mode).
3. Build the model via `model_factory.build_model()` — base frozen, head trainable.
4. Compile:
   ```python
   optimizer = Adam(learning_rate=config['stage1_lr'])  # 0.001
   loss = CategoricalCrossentropy(label_smoothing=0.05)
   metrics = ['accuracy']
   ```
5. Train with callbacks:
   - `EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)`
   - `ModelCheckpoint(save_best_only=True)` → `stage1_best.keras`

### Phase 2 — fine-tune (A6)

**Script:** `ml/scripts/train_stage2.py`
**Output:** `ml/models/checkpoints/stage2_best.keras`

1. Load `stage1_best.keras`.
2. Call `model_factory.unfreeze_top_layers(model, fine_tune_from_layer=-30)`:
   - Sets `base.trainable = True`
   - Re-freezes all layers **except** the last 30
   - Keeps BatchNorm layers in inference mode for the frozen portion
3. Recompile at lower learning rate (LR=1e-4).
4. Train with `EarlyStopping(patience=3)`.

### Why two phases?

Fine-tuning the whole network from the start destroys ImageNet pretrained
features (catastrophic forgetting). Phase 1 first trains a good classification
head. Phase 2 then nudges the top of the base with a much lower LR, adapting
high-level features to tomato leaf textures while preserving low-level edge
detectors.

---

## Temperature calibration

**Script:** `ml/scripts/calibrate_temperature.py`
**Input:** `stage2_best.keras` + val split
**Output:** `stage2_calibrated.keras` (temperature-scaled Stage 3 only)

Temperature scaling (Guo et al. 2017) learns a single scalar T that divides the
logits before softmax. This does not change the argmax (accuracy is preserved)
but compresses overconfident predictions, making the 60% confidence threshold
statistically meaningful.

| Parameter | Value |
|---|---|
| Temperature T | **0.5889** |
| ECE (in-sample val split) | 0.0046 |
| ECE (held-out test, n=6,683) | **0.061** |

The held-out test ECE (0.061) is the honest deployed figure. The in-sample
0.0046 is on the same data used to fit T and is NOT reported as the model's
calibration quality.

---

## Stage A7 — Evaluation

**Script:** `ml/scripts/eval_model.py` (pipeline); `ml/tree/eval_deployed_tflite.py` (deployed cascade)
**Input:** 3 TFLite models + held-out test set (n=6,683)
**Output:** `ml/ml/reports/eval_deployed.json`, `ml/reports/confusion_matrix_deployed.png`

### Metrics computed

**Classification (disease classifier, Stage 3):**
- Disease accuracy (97.59%)
- Per-class recall (11 classes)
- 11×11 confusion matrix (saved as PNG heatmap)

**End-to-end (full cascade):**
- Passed leaf gate: 100.0%
- Passed both gates: 99.42%
- Correct diagnosis given passed both gates: **97.19%** (end-to-end)

**Calibration:**
- ECE (Expected Calibration Error, 15-bin): 0.061 held-out test
- Temperature T: 0.5889

**Field evaluation (PlantDoc, n=79):**
- Field end-to-end: **77.2%**
- Field disease accuracy: 87.1%
- Laboratory-to-field gap: ~20 percentage points

### Hard gates

The script exits with code 1 if any of these fail:

```
overall_accuracy    >= target_accuracy      (0.90)
```

This means `export_tflite` (A8) will never run on a model that doesn't meet
the minimum bar.

---

## Stage A8 — TFLite export

**Script:** `ml/scripts/export_tflite.py`
**Input:** calibrated Keras models (×3)
**Output:** 3 float16 TFLite files
**Cached by:** existence of the `.tflite` files

### Conversion process (per model)

```python
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.float16]
tflite_model = converter.convert()
```

Float16 is chosen over INT8 because:
- INT8 drops 2–4% per-class accuracy on this dataset
- Float16 drops < 0.5%
- The 3-model cascade totals **9.87 MB** in float16 — well under the 15 MB budget

### Exported files

| File | Model | Size |
|------|-------|------|
| `stage1_leaf_float16.tflite` | MobileNetV3-Small leaf gate | 1.92 MB |
| `stage2_tomato_float16.tflite` | MobileNetV3-Small tomato gate | 1.92 MB |
| `stage3_disease_float16.tflite` | MobileNetV3-Large disease classifier | 6.03 MB |
| **Total** | | **9.87 MB** |

### Post-export verification

1. **Size gate:** total ≤ `tflite_max_size_mb` (15 MB)
2. **Shape gate:** input `[1, 224, 224, 3]` float32; Stage 3 output `[1, 11]` float32
3. **Accuracy gate:** re-run test set with the TFLite interpreter; warn if drop > 1%

### Deploying to Android

```bash
cp ml/models/tflite/stage1_leaf_float16.tflite \
   ml/models/tflite/stage2_tomato_float16.tflite \
   ml/models/tflite/stage3_disease_float16.tflite \
   android/app/src/main/assets/
```

---

## Model architecture (Stage 3 — disease classifier)

The gates (Stages 1–2) use MobileNetV3-Small with the same head pattern but
only 2 output classes each (leaf/not-leaf, tomato/not-tomato).

```
Input: (224, 224, 3) float32, values in [0.0, 1.0]
    │
    ▼
Rescaling(scale=2.0, offset=-1.0)    → values in [-1.0, 1.0]  (ImageNet normalization)
    │
    ▼
MobileNetV3-Large (ImageNet pretrained, include_preprocessing=False)
    ├── ~280 layers
    ├── Phase 1: all frozen
    └── Phase 2: last 30 layers unfrozen
    │
    ▼
GlobalAveragePooling2D
    │
    ▼
Dropout(0.4)
    │
    ▼
Dense(11, activation='softmax')   ← temperature-scaled (T=0.5889)
    │
    ▼
Output: (11,) float32 — probability distribution over 11 classes (10 diseases + healthy)
```

**Quantized:** 6.03 MB float16 (Stage 3). Total cascade: 9.87 MB.

---

## Class list (deployed)

The **deployed** disease classifier (Stage 3) has **11 classes** — 10 tomato
diseases + healthy. Class indices are alphabetical (the order TF Keras assigns
via `image_dataset_from_directory`). This matches `ml/reports/eval_deployed.json`.

| Index | Class name | Note |
|---|---|---|
| 0 | bacterial_spot | |
| 1 | early_blight | weakest: recall 0.943 |
| 2 | healthy | |
| 3 | late_blight | |
| 4 | leaf_mold | |
| 5 | mosaic_virus | |
| 6 | powdery_mildew | perfect: recall 1.000 |
| 7 | septoria_leaf_spot | second weakest: recall 0.957 |
| 8 | spider_mites | |
| 9 | target_spot | |
| 10 | yellow_leaf_curl_virus | |

> **Note:** OOD rejection is handled by the cascade gates (Stages 1–2), not by
> a reject class in Stage 3. The old `Tomato_NotALeaf` class from the v1
> prototype is no longer part of the deployed model.

---

## Results summary

All numbers sourced from `ml/reports/eval_deployed.json` — the single source of truth.

| Metric | Value |
|---|---|
| Disease accuracy (lab, n=6,683) | **97.59%** |
| End-to-end accuracy (lab) | **97.19%** |
| Field accuracy (PlantDoc, n=79) | **77.2%** |
| ECE (held-out test, 15-bin) | **0.061** |
| Temperature T | 0.5889 |
| Model size (cascade total) | **9.87 MB** (1.92 + 1.92 + 6.03) |
| Weakest recalls | early_blight 0.943, septoria 0.957 |
| Gate safety (non-leaf reject) | 99.55% |
| Confidence threshold (app) | 0.60 |
| Training baseline (from-scratch TomatoCareNet) | 91.17% |

---

## Utilities reference

### `ml/utils/model_factory.py`

```python
build_model(num_classes, img_size=224, dropout_rate=0.4) → keras.Model
    # Builds MobileNetV3-Large + head. Base frozen by default (Stage 1 mode).

unfreeze_top_layers(model, fine_tune_from_layer=-30)
    # Unfreezes the last N layers of the base for Stage 2.
    # BatchNorm in frozen layers stays in inference mode.
```

### `ml/utils/dataset_loader.py`

```python
build_train_dataset(augmented_train_dir, config) → tf.data.Dataset
    # Reads pre-augmented images from disk.
    # class_names pinned to config['classes'] — alphabetical order enforced.
    # Normalizes uint8 [0,255] → float32 [0,1]. Batched + prefetched.

build_split_dataset(split_csv, config, shuffle=False) → tf.data.Dataset
    # Reads val or test split from CSV.
    # Same normalization and batching as train.
```

### `ml/utils/seed.py`

```python
set_global_seed(seed)
    # Sets Python random, NumPy, TensorFlow, and OS env seeds.
    # Called at the top of every training script.
```

---

## Re-running specific stages

Delete the cached artifact for the stage you want to re-run. Downstream stages
will also need their artifacts deleted if their inputs have changed.

```bash
# Re-run only evaluation (useful for checking a new model without retraining)
rm ml/ml/reports/eval_deployed.json
python -m ml.scripts.eval_model

# Re-run training from scratch (disease classifier)
rm ml/models/checkpoints/stage1_best.keras
rm ml/models/checkpoints/stage2_best.keras
rm ml/models/checkpoints/stage2_calibrated.keras
rm ml/ml/reports/eval_deployed.json
python -m ml.scripts.train_stage1
python -m ml.scripts.train_stage2
python -m ml.scripts.calibrate_temperature
python -m ml.scripts.eval_model
python -m ml.scripts.export_tflite
```
