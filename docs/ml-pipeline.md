# ML Pipeline

This document is the complete reference for the TomatoCare ML pipeline (Track A).
It covers every stage from raw images to a production-ready TFLite model.

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration](#configuration)
3. [Stage A2 — Data preparation](#stage-a2--data-preparation)
4. [Stage A3 — UAE-domain augmentation](#stage-a3--uae-domain-augmentation)
5. [Stage A5 — Stage-1 training (head only)](#stage-a5--stage-1-training-head-only)
6. [Stage A6 — Stage-2 training (fine-tune)](#stage-a6--stage-2-training-fine-tune)
7. [Stage A7 — Evaluation](#stage-a7--evaluation)
8. [Stage A8 — TFLite export](#stage-a8--tflite-export)
9. [Model architecture](#model-architecture)
10. [Class list](#class-list)
11. [Results summary](#results-summary)
12. [Utilities reference](#utilities-reference)
13. [Re-running specific stages](#re-running-specific-stages)

---

## Overview

The pipeline is a linear sequence of six Python scripts. Each script reads
hyperparameters exclusively from `ml/configs/training_config.yaml` — values
are never duplicated into script files. Every script caches its output: if the
output artifact already exists it skips processing and loads the cached result.

```
A2 → A3 → A5 → A6 → A6.5 → A7 → A8
```

Run all stages in order from the **repo root** (not from inside `ml/`):

```bash
python -m ml.scripts.prepare_plantvillage
python -m ml.scripts.augment_uae
python -m ml.scripts.train_stage1
python -m ml.scripts.train_stage2
python -m ml.scripts.calibrate_temperature
python -m ml.scripts.eval_model
python -m ml.scripts.export_tflite
```

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

`balanced` computes `n_samples / (n_classes × count_c)` per class. Without
this the `Tomato_NotALeaf` class (~8,000 samples) would dominate the loss over
smaller tomato disease classes (~2,500 samples each).

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

## Stage A3 — UAE-domain augmentation

**Script:** `ml/scripts/augment_uae.py`
**Input:** `ml/dataset/splits/train.csv` + raw images
**Output:** `ml/dataset/augmented/train/`, `val/`, `test/`
**Cached by:** existence of the `augmented/train/` directory

### Why augment offline?

Applying augmentation offline (before training) rather than on-the-fly means:
- Augmented images are saved to disk — the training loop reads them as regular images
- The augmentation pipeline is decoupled from the TF graph
- `augmentations_per_image: 3` multiplies the training set ~4× (100k+ images)

### Two augmentation stacks

**Stack 1 — UAE-domain (tomato classes only):**

Mimics conditions in UAE agricultural fields: intense sunlight, dust haze, heat
shimmer.

| Parameter | Range |
|---|---|
| Brightness | 0.6–1.4× |
| Contrast | 0.7–1.3× |
| Red-channel shift | +10..+25 (simulates warm dust haze) |
| Gaussian blur σ | 0.0–1.5 (heat shimmer) |

Applied **only to tomato classes** — adding orange haze to a photo of a dog
(Tomato_NotALeaf class) would be incorrect.

**Stack 2 — real-world phone-shot (all classes):**

PlantVillage images are lab photos with uniform backgrounds. This stack makes
the model robust to how farmers actually take photos: shaky hands, JPEG
compression, exposure variation.

| Parameter | Value |
|---|---|
| Rotation | ±30° |
| Horizontal flip | 50% probability |
| Vertical flip | 20% probability |
| Zoom | ±20% |
| JPEG quality | 30–80 (compression artifacts) |
| Motion blur kernel | up to 7×7 |
| Gamma | 0.7–1.4 |
| Gaussian noise std | 0–6 |
| Perspective warp | 40% probability, strength 0.06 |
| Random crop offset | up to 15% of image size |
| Cutout | 30% probability, up to 56×56 px patch |

**Val/test light augmentation:**

Val and test sets receive a much lighter version (JPEG quality 50–90 + mild
gamma only) so that evaluation numbers reflect realistic inference conditions
without inflating them with clean lab images.

---

## Stage A5 — Stage-1 training (head only)

**Script:** `ml/scripts/train_stage1.py`
**Input:** `ml/dataset/augmented/train/` + `splits/val.csv`
**Output:** `ml/models/checkpoints/stage1_best.keras`
**Cached by:** existence of `stage1_best.keras`

### What happens

1. Load augmented training data using `dataset_loader.build_train_dataset()`.
2. Compute per-class weights using `sklearn.utils.class_weight.compute_class_weight('balanced')`.
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
6. Save `results/results_stage1.json` with training history and best metrics.

---

## Stage A6 — Stage-2 training (fine-tune)

**Script:** `ml/scripts/train_stage2.py`
**Input:** `stage1_best.keras` + `augmented/train/` + `splits/val.csv`
**Output:** `ml/models/checkpoints/stage2_best.keras`
**Cached by:** existence of `stage2_best.keras`

### What happens

1. Load `stage1_best.keras`.
2. Call `model_factory.unfreeze_top_layers(model, fine_tune_from_layer=-30)`:
   - Sets `base.trainable = True`
   - Re-freezes all layers **except** the last 30
   - Keeps BatchNorm layers in inference mode for the frozen portion
3. Recompile at lower learning rate:
   ```python
   optimizer = Adam(learning_rate=config['stage2_lr'])  # 0.0001
   ```
4. Train with:
   - `EarlyStopping(patience=3)` — tighter than Stage 1
   - `ModelCheckpoint` → `stage2_best.keras`
5. Save `results/results_stage2.json`.

### Why two stages?

Fine-tuning the whole network from the start destroys ImageNet pretrained
features (catastrophic forgetting) if the learning rate is not carefully tuned.
Stage 1 first trains a good classification head. Stage 2 then nudges the top
of the base with a much lower LR, adapting high-level features to tomato leaf
textures while preserving low-level edge detectors.

---

## Stage A7 — Evaluation

**Script:** `ml/scripts/eval_model.py`
**Input:** `stage2_best.keras` + `splits/test.csv`
**Output:** `ml/results/eval_report.json`, `ml/results/confusion_matrix.png`
**Cached by:** existence of `eval_report.json`

### Metrics computed

**Classification:**
- Overall accuracy
- Per-class precision, recall, F1 (classification report)
- Macro-averaged F1
- 10×10 confusion matrix (saved as PNG heatmap via seaborn)

**Calibration:**
- ECE (Expected Calibration Error)
- Brier score
- The calibrated model (`stage2_calibrated.keras`) is saved after temperature
  scaling if the calibration step runs before evaluation.

**OOD (Out-of-Distribution / Tomato_NotALeaf):**
- NotALeaf recall — fraction of non-tomato images correctly rejected
- False-reject rate — fraction of real tomato leaves incorrectly rejected
- AUROC on the NotALeaf vs. rest binary problem
- FPR @ 95% TPR
- 20 hardest failures dumped to `ml/results/ood_failures/`

### Hard gates

The script exits with code 1 if any of these fail:

```
overall_accuracy    >= target_accuracy      (0.90)
notaleaf_recall     >= notaleaf_min_recall  (0.80)
false_reject_rate   <= max_false_reject_rate (0.15)
```

This means `export_tflite` (A8) will never run on a model that doesn't meet
the minimum bar.

---

## Stage A8 — TFLite export

**Script:** `ml/scripts/export_tflite.py`
**Input:** `stage2_best.keras` (or `stage2_calibrated.keras` if present)
**Output:** `ml/models/tflite/tomatocare_model_float16.tflite`
**Cached by:** existence of the `.tflite` file

### Conversion process

```python
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.float16]
tflite_model = converter.convert()
```

Float16 is chosen over INT8 because:
- INT8 drops 2–4% per-class accuracy on this dataset
- Float16 drops < 0.5%
- Both achieve the ≤ 15 MB size target (float16: 5.75 MB vs float32: ~13 MB)

### Post-export verification

1. **Size gate:** file size ≤ `tflite_max_size_mb` (15 MB)
2. **Shape gate:** input `[1, 224, 224, 3]` float32, output `[1, 11]` float32
3. **Accuracy gate:** re-run test set with the TFLite interpreter; warn if drop > 1%
   compared to the Keras model accuracy

### Deploying to Android

```bash
cp ml/models/tflite/tomatocare_model_float16.tflite \
   android/app/src/main/assets/
```

---

## Model architecture

```
Input: (224, 224, 3) float32, values in [0.0, 1.0]
    │
    ▼
Rescaling(scale=2.0, offset=-1.0)    → values in [-1.0, 1.0]  (matches ImageNet normalization)
    │
    ▼
MobileNetV3-Large (ImageNet pretrained, include_preprocessing=False)
    ├── ~280 layers
    ├── Stage 1: all frozen
    └── Stage 2: last 30 layers unfrozen
    │
    ▼
GlobalAveragePooling2D
    │
    ▼
Dropout(0.4)
    │
    ▼
Dense(11, activation='softmax')
    │
    ▼
Output: (11,) float32 — probability distribution over 11 classes (10 diseases + 1 OOD reject class)
```

**Parameter count (approximate):**
- MobileNetV3-Large base: ~4.2 M parameters
- Classification head: ~14,000 parameters
- Total: ~4.2 M parameters

**Quantized model:** 5.75 MB float16 (half precision, ~2.1 M effective 16-bit values)

---

## Class list

Class indices are fixed. The order is **alphabetical** — this is the order
TF Keras assigns when using `image_dataset_from_directory` with `class_names`
pinned. New classes must always be **appended** (never inserted) to avoid
breaking existing model weights.

| Index | Class name | Stress type |
|---|---|---|
| 0 | Tomato_Bacterial_spot | Biotic |
| 1 | Tomato_Early_blight | Biotic |
| 2 | Tomato_healthy | — |
| 3 | Tomato_Late_blight | Biotic |
| 4 | Tomato_Leaf_Mold | Biotic |
| 5 | Tomato_Septoria_leaf_spot | Biotic |
| 6 | Tomato_Spider_mites_Two_spotted_spider_mite | Biotic |
| 7 | Tomato_Target_Spot | Biotic |
| 8 | Tomato_Yellow_Leaf_Curl_Virus | Biotic |
| 9 | Tomato_mosaic_virus | Biotic |
| 10 | Tomato_NotALeaf | OOD (out-of-distribution) |

> **Note:** `Tomato_NotALeaf` (index 10) is the OOD reject class. It is included in `TomatoClasses.CLASS_NAMES` on the Android side as index 10. When the top-1 probability lands on index 10, the inference engine treats it as out-of-distribution, routing the result through the low-confidence warning UI.

---

## Results summary

Achieved on the held-out test set (3,565 images, never seen during training or
validation):

| Metric | Value |
|---|---|
| Overall accuracy | **95.60%** |
| Macro F1 | **0.9541** |
| Confidence threshold (app) | 0.60 |
| Model file size | 5.75 MB (float16 TFLite) |
| Training baseline (PyTorch CNN) | 91.17% |

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
rm ml/results/eval_report.json
python -m ml.scripts.eval_model

# Re-run training from scratch
rm ml/models/checkpoints/stage1_best.keras
rm ml/models/checkpoints/stage2_best.keras
rm ml/models/checkpoints/stage2_calibrated.keras
rm ml/results/eval_report.json
rm ml/models/tflite/tomatocare_model_float16.tflite
python -m ml.scripts.train_stage1
python -m ml.scripts.train_stage2
python -m ml.scripts.calibrate_temperature
python -m ml.scripts.eval_model
python -m ml.scripts.export_tflite

# Re-run augmentation (e.g. after changing augmentation parameters)
rm -rf ml/dataset/augmented/
python -m ml.scripts.augment_uae
# Then re-run training and everything downstream.
```
