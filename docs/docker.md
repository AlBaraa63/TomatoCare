# Docker

This document covers how to use the TomatoCare Docker setup for both the ML
pipeline and the Android build. Docker lets every team member work with identical
environments without installing Python, TensorFlow, JDK, or the Android SDK locally.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Services overview](#services-overview)
3. [ML pipeline (CPU)](#ml-pipeline-cpu)
4. [ML pipeline (GPU)](#ml-pipeline-gpu)
5. [Android build](#android-build)
6. [Dataset and volume mounts](#dataset-and-volume-mounts)
7. [Rebuilding images](#rebuilding-images)
8. [Common commands reference](#common-commands-reference)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Docker Desktop** 4.x or later (Windows / macOS) or **Docker Engine** 24.x+
  (Linux)
- **Docker Compose** v2 (bundled with Docker Desktop; on Linux install the
  `docker-compose-plugin` package)

GPU training additionally requires:
- NVIDIA GPU with driver ≥ 525
- [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
  installed on the host

Verify your installation:
```bash
docker --version          # Docker version 24.x or higher
docker compose version    # Docker Compose version v2.x
```

---

## Services overview

| Service | Profile | Image | Purpose |
|---|---|---|---|
| `ml` | (default) | `tensorflow/tensorflow:2.15.0` | ML pipeline, CPU |
| `ml-gpu` | `gpu` | `tensorflow/tensorflow:2.15.0-gpu` | ML pipeline, GPU |
| `android-build` | `android` | `eclipse-temurin:17-jdk-jammy` + Android SDK 34 | Build APK |

Services tagged with a profile are **not started by default**. Pass
`--profile <name>` to activate them.

---

## ML pipeline (CPU)

### Build the image (first time only)

```bash
docker compose build ml
```

This downloads `tensorflow/tensorflow:2.15.0` (~500 MB) and installs the
additional Python dependencies (scikit-learn, matplotlib, pandas, etc.).
Subsequent builds reuse the layer cache.

### Run a single script

```bash
# Evaluate the pre-trained model
docker compose run --rm ml python -m ml.scripts.eval_model

# Export the TFLite model
docker compose run --rm ml python -m ml.scripts.export_tflite

# Run the full pipeline in sequence
docker compose run --rm ml bash -c "
  python -m ml.scripts.prepare_plantvillage &&
  python -m ml.scripts.train_stage1 &&
  python -m ml.scripts.train_stage2 &&
  python -m ml.scripts.calibrate_temperature &&
  python -m ml.scripts.eval_model &&
  python -m ml.scripts.export_tflite
"
```

### Interactive shell

```bash
docker compose run --rm ml bash
# Inside the container:
python -m ml.scripts.eval_model
```

---

## ML pipeline (GPU)

### Requirements

The host must have an NVIDIA GPU and the `nvidia-container-toolkit` installed.
Verify the toolkit is working:

```bash
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

### Build the GPU image

```bash
docker compose --profile gpu build ml-gpu
```

This builds the same Dockerfile as the CPU service but uses
`tensorflow/tensorflow:2.15.0-gpu` as the base (~2 GB with CUDA libraries).

### Run training

```bash
# Stage 1 training (GPU)
docker compose --profile gpu run --rm ml-gpu python -m ml.scripts.train_stage1

# Stage 2 fine-tuning (GPU)
docker compose --profile gpu run --rm ml-gpu python -m ml.scripts.train_stage2

# Interactive GPU shell
docker compose --profile gpu run --rm ml-gpu bash
```

Inside the container, verify TensorFlow sees the GPU:

```python
import tensorflow as tf
print(tf.config.list_physical_devices('GPU'))
# [PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')]
```

---

## Android build

### Build the image (first time only)

```bash
docker compose --profile android build android-build
```

This downloads JDK 17, the Android command-line tools (~200 MB), installs the
Android 34 SDK and build tools, and pre-fetches all Gradle dependencies. The
first build takes 10–20 minutes but is fully cached afterwards.

### Build a debug APK

```bash
docker compose --profile android run --rm android-build
```

The default command builds a debug APK. Output is written to the host via
volume mount:

```
android/app/build/outputs/apk/debug/app-debug.apk   # on your host
```

### Build a release APK

```bash
docker compose --profile android run --rm android-build \
  bash -c "cd android && ./gradlew :app:assembleRelease --no-daemon"
```

> Release builds require a keystore. Configure signing in
> `android/app/build.gradle.kts` before running this command.

### Run unit tests inside Docker

```bash
docker compose --profile android run --rm android-build \
  bash -c "cd android && ./gradlew :app:test --no-daemon"
```

---

## Dataset and volume mounts

The `docker-compose.yml` mounts four directories from your host into the `ml`
container:

| Host path | Container path | Purpose |
|---|---|---|
| `./ml/dataset` | `/app/ml/dataset` | Raw and augmented images |
| `./ml/models` | `/app/ml/models` | Checkpoint and TFLite files |
| `./ml/results` | `/app/ml/results` | Evaluation reports |
| `./ml/configs` | `/app/ml/configs` | `training_config.yaml` |

Mounting `configs/` means you can edit `training_config.yaml` on the host
and the change takes effect immediately without rebuilding the image.

### Providing the pre-split dataset

The `training_config.yaml` ships with `pre_split_root` pointing to a local
Windows path. Before running training inside Docker:

1. Copy or symlink your pre-split dataset onto the host machine.
2. Edit `ml/configs/training_config.yaml`:
   ```yaml
   pre_split_root: /app/ml/dataset/processed
   ```
3. Add a bind mount for the dataset directory. For example, if your dataset
   is at `D:/datasets/tomato-processed/` on Windows:
   ```yaml
   # In docker-compose.yml, under ml.volumes:
   - D:/datasets/tomato-processed:/app/ml/dataset/processed:ro
   ```
   Or set `pre_split_root: null` to use the fallback mode (raw images under
   `ml/dataset/raw/`).

---

## Rebuilding images

Rebuild a specific image after code changes:

```bash
docker compose build ml                           # CPU image
docker compose --profile gpu build ml-gpu         # GPU image
docker compose --profile android build android-build
```

Force a complete rebuild (no cache):

```bash
docker compose build --no-cache ml
```

---

## Common commands reference

```bash
# ── ML (CPU) ──────────────────────────────────────────────────────────────────
docker compose build ml
docker compose run --rm ml python -m ml.scripts.eval_model
docker compose run --rm ml python -m ml.scripts.export_tflite
docker compose run --rm ml bash                         # interactive shell

# ── ML (GPU) ──────────────────────────────────────────────────────────────────
docker compose --profile gpu build ml-gpu
docker compose --profile gpu run --rm ml-gpu python -m ml.scripts.train_stage1
docker compose --profile gpu run --rm ml-gpu python -m ml.scripts.train_stage2
docker compose --profile gpu run --rm ml-gpu bash

# ── Android build ─────────────────────────────────────────────────────────────
docker compose --profile android build android-build
docker compose --profile android run --rm android-build              # debug APK
docker compose --profile android run --rm android-build \
  bash -c "cd android && ./gradlew :app:assembleRelease --no-daemon" # release APK
docker compose --profile android run --rm android-build \
  bash -c "cd android && ./gradlew :app:test --no-daemon"            # unit tests

# ── Maintenance ───────────────────────────────────────────────────────────────
docker compose down                 # stop all services
docker volume rm tomatocare_gradle-cache   # clear Gradle cache volume
docker system prune                 # remove all stopped containers + dangling images
```

---

## Troubleshooting

### `docker compose` not found

Use `docker compose` (with a space, Compose v2), not `docker-compose` (v1 hyphen form).
If you only have v1, install the plugin: `sudo apt install docker-compose-plugin`.

### ML: `no space left on device` during augmentation

The augmented dataset is ~15–20 GB. Make sure Docker has enough disk space
allocated. In Docker Desktop: Settings → Resources → Disk image size → increase
to at least 60 GB.

### ML: Out of memory during training

Reduce `batch_size` in `ml/configs/training_config.yaml` (try 16 or 8).
Or increase Docker's memory limit: Docker Desktop → Settings → Resources → Memory.

### GPU: `could not select device driver "nvidia"`

The `nvidia-container-toolkit` is not installed or not configured. Follow the
[official guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
then restart the Docker daemon:
```bash
sudo systemctl restart docker
```

### Android: First build is very slow

The first build downloads ~500 MB of Gradle dependencies. These are cached in
the `gradle-cache` named volume — subsequent builds reuse the cache and are
much faster (typically 2–3 minutes).

### Android: `SDK location not found`

The Android SDK is pre-installed inside the container at `/opt/android-sdk`.
This error should not occur inside Docker. If it does, check that the
`ANDROID_HOME` environment variable is set:
```bash
docker compose --profile android run --rm android-build env | grep ANDROID
```

### Android cmdline-tools URL is stale

If the `Dockerfile.android` build fails on the `wget` step with a 404, the
cmdline-tools version number in the URL is outdated. Get the latest URL from
[developer.android.com/studio#command-line-tools-only](https://developer.android.com/studio#command-line-tools-only)
and update the URL in `Dockerfile.android`.
