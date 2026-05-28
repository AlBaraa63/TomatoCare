# Getting Started

This guide walks a new team member from zero to a working development environment
for both tracks of the project. Follow only the section(s) relevant to your role.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
   - [Everyone](#everyone)
   - [ML track](#ml-track-prerequisites)
   - [Android track](#android-track-prerequisites)
2. [Clone the repository](#clone-the-repository)
3. [ML track setup](#ml-track-setup)
4. [Android track setup](#android-track-setup)
5. [Verify your setup](#verify-your-setup)
6. [Common issues](#common-issues)

---

## Prerequisites

### Everyone

- **Git** 2.30+
- **Docker Desktop** (optional but recommended — lets you skip the track-specific
  toolchain entirely). See [docker.md](docker.md) once you have Docker installed.

### ML track prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.10 | 3.11 works; 3.12 is untested. Do **not** use 3.9 or below. |
| pip | latest | `python -m pip install --upgrade pip` |
| CUDA (optional) | 12.x | Required for GPU training. CPU works but is 10–20× slower. |
| OS | Linux / WSL2 | **macOS and native Windows are unsupported** for GPU. CPU-only is fine on both. |

> **Windows users:** install WSL2 (Ubuntu 22.04 recommended) and work from inside it.
> `tensorflow[and-cuda]` only works on Linux — the pip package for Windows is CPU-only
> and the CUDA toolkit is not bundled. See
> [the TF install guide](https://www.tensorflow.org/install/pip) for details.

### Android track prerequisites

| Tool | Version | Notes |
|---|---|---|
| JDK | 17 or 21 | JDK 26+ triggers foojay auto-provisioning; it downloads JDK 17 automatically, but this adds time to the first build. Prefer JDK 17 directly. |
| Android Studio | Iguana (2023.2) or newer | Bundles everything else. Alternatively, install the Android SDK command-line tools and use VS Code or IntelliJ. |
| Android SDK | API 34 | Install via SDK Manager → SDK Platforms → Android 14 |
| Build Tools | 34.0.0 | Install via SDK Manager → SDK Tools → Android SDK Build-Tools |

---

## Clone the repository

```bash
git clone <repo-url>
cd TomatoCare
```

The repo uses `.gitattributes` to enforce LF line endings on shell scripts. On
Windows, make sure `core.autocrlf` is not set to `true`:

```bash
git config --global core.autocrlf input
```

---

## ML track setup

### 1. Create a virtual environment

```bash
cd TomatoCare

# Create and activate venv
python3.10 -m venv .venv
source .venv/bin/activate       # Linux / macOS / WSL2
# .venv\Scripts\activate        # native Windows

# Upgrade pip
pip install --upgrade pip
```

### 2. Install dependencies

```bash
pip install -r ml/requirements.txt
```

On Linux this installs `tensorflow[and-cuda]==2.15.1` which bundles CUDA 12.2
and cuDNN 8.9 as wheels — no separate CUDA installation needed. On Windows it
installs the CPU-only build.

### 3. Verify TensorFlow

```bash
python -c "import tensorflow as tf; print(tf.__version__); print(tf.config.list_physical_devices('GPU'))"
```

Expected output (GPU machine):
```
2.15.1
[PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')]
```

Expected output (CPU-only):
```
2.15.1
[]
```

### 4. Obtain the dataset

The training scripts support two dataset modes — choose the one that fits your situation:

**Mode A — pre-split (preferred):**

If you have access to the team's pre-split dataset (11 classes: 10 diseases + healthy):

1. Copy or symlink the folder so it has this structure:
   ```
   <your-path>/
   ├── train/
   │   ├── Tomato_Bacterial_spot/
   │   ├── Tomato_Early_blight/
   │   └── ... (11 class folders — 10 diseases + healthy)
   ├── val/
   └── test/
   ```
2. Edit `ml/configs/training_config.yaml` and set:
   ```yaml
   pre_split_root: "/path/to/your/dataset"
   ```

**Mode B — raw sources (fallback):**

Download from Kaggle and place under `ml/dataset/raw/`:

```
ml/dataset/raw/
├── plantvillage/    ← Kaggle: arjuntejaswi/plant-village
└── mendeley/        ← Mendeley DOI 10.17632/tywbtsjrjv.1
```

Then set `pre_split_root: null` in `ml/configs/training_config.yaml`.

### 5. Run the pipeline

Scripts must be run as modules from the repo root (not from inside `ml/`):

```bash
# From repo root with venv active:
python -m ml.scripts.prepare_plantvillage   # A2 — inventory + CSV split
python -m ml.scripts.train_stage1           # A5 — head-only training (per cascade stage)
python -m ml.scripts.train_stage2           # A6 — fine-tune top 30 layers
python -m ml.scripts.calibrate_temperature  # A6.5 — temperature scaling (T=0.5889)
python -m ml.scripts.eval_model             # A7 — evaluation (exits 1 if gates fail)
python -m ml.scripts.export_tflite          # A8 — float16 TFLite export (3 models)
```

Each script is **cached**: if the output artifact already exists it skips work
and loads the cached result. Delete the artifact to force a re-run:

| Script | Artifact to delete for re-run |
|---|---|
| prepare_plantvillage | `ml/dataset/splits/*.csv` |
| train_stage1 | `ml/models/checkpoints/stage1_best.keras` |
| train_stage2 | `ml/models/checkpoints/stage2_best.keras` |
| calibrate_temperature | `ml/models/checkpoints/stage2_calibrated.keras` |
| eval_model | `ml/results/eval_report.json` |
| export_tflite | `ml/models/tflite/stage{1,2,3}_*_float16.tflite` |

### 6. Copy the models to the Android app

The deployed system is a 3-stage cascade (leaf gate, tomato gate, disease
classifier). Copy all three TFLite files:

```bash
cp ml/models/tflite/stage1_leaf_float16.tflite \
   ml/models/tflite/stage2_tomato_float16.tflite \
   ml/models/tflite/stage3_disease_float16.tflite \
   android/app/src/main/assets/
```

---

## Android track setup

### 1. Open the project in Android Studio

1. Open Android Studio.
2. **File → Open** → select the `android/` subfolder (not the repo root).
3. Wait for Gradle sync to complete. It downloads all dependencies automatically.

> If you see "JDK 26 is not supported", Gradle's foojay-resolver is downloading
> JDK 17. Let it finish — it only happens once.

### 2. Verify the model asset is present

Check that the three TFLite cascade models exist before building:

```bash
ls android/app/src/main/assets/stage1_leaf_float16.tflite \
   android/app/src/main/assets/stage2_tomato_float16.tflite \
   android/app/src/main/assets/stage3_disease_float16.tflite
```

If any are missing, copy them from `ml/models/tflite/` (after running the ML
pipeline) or ask a team member who has the trained models.

### 3. Build from command line

```bash
cd android

# Debug APK (no signing required)
./gradlew :app:assembleDebug

# Install directly on a connected device
./gradlew :app:installDebug

# Release APK (requires a keystore — ask the team lead)
./gradlew :app:assembleRelease
```

APKs land in `android/app/build/outputs/apk/`.

### 4. Run unit tests

```bash
cd android
./gradlew :app:test
```

The test suite includes `ClassNamesTest` which verifies that
`TomatoClasses.CLASS_NAMES` stays in alphabetical order and matches the
training config's class list — this is a critical invariant for correct
inference.

---

## Verify your setup

### ML track

```bash
# Quick smoke-test: load the exported model and run one inference
python - <<'EOF'
import numpy as np, tensorflow as tf
interp = tf.lite.Interpreter("ml/models/tflite/stage3_disease_float16.tflite")
interp.allocate_tensors()
inp = interp.get_input_details()[0]
out = interp.get_output_details()[0]
interp.set_tensor(inp["index"], np.zeros((1,224,224,3), dtype=np.float32))
interp.invoke()
probs = interp.get_tensor(out["index"])[0]
print("Output shape:", probs.shape)   # (11,)
print("Sum of probs:", probs.sum())   # ≈ 1.0
EOF
```

### Android track

```bash
cd android
./gradlew :app:assembleDebug && echo "BUILD OK"
./gradlew :app:test && echo "TESTS OK"
```

---

## Common issues

### ML: `ModuleNotFoundError: No module named 'ml'`

You ran the script directly (`python ml/scripts/train_stage1.py`) instead of as
a module from the repo root. Always use:
```bash
# from TomatoCare/
python -m ml.scripts.train_stage1
```

### ML: GPU not detected after installing `tensorflow[and-cuda]`

Check that your NVIDIA driver supports CUDA 12.x:
```bash
nvidia-smi
```
The driver version shown must be ≥ 525. If it's older, update the driver.
TF 2.15 bundles CUDA 12.2 and cuDNN 8.9 as wheels — the toolkit itself does
not need to be installed separately.

### ML: `pre_split_root` path error on first run

`training_config.yaml` ships with `pre_split_root` pointing to the original
developer's local path. Edit it to point to your own dataset location, or set
it to `null` to use Mode B (raw multi-root).

### Android: Gradle fails with `SDK location not found`

Set the `ANDROID_HOME` environment variable, or create
`android/local.properties` with:
```
sdk.dir=/path/to/your/Android/Sdk
```

### Android: `org.gradle.java.home` path not found

The `android/gradle.properties` file has a hardcoded path to Android Studio's
JBR (JDK 21). If you installed Android Studio to a non-default location,
override this line locally by creating `android/local.properties` and adding:
```
org.gradle.java.home=/path/to/your/jbr
```
Or delete the line from `gradle.properties` entirely — Gradle will fall back
to your system `JAVA_HOME`.

### Android: TFLite model files missing at build time

The three TFLite cascade models (`stage1_leaf_float16.tflite`,
`stage2_tomato_float16.tflite`, `stage3_disease_float16.tflite`) are not
committed to git (binary artifacts). Copy them from `ml/models/tflite/` after
running the ML pipeline, or ask a team member for the files.
