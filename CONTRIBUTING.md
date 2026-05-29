# Contributing to TomatoCare

Thanks for your interest in TomatoCare — a fully offline, bilingual
(English / Arabic) Android app that diagnoses tomato leaf diseases on-device
with a 3-stage MobileNetV3 TFLite cascade. This guide gets you from a fresh
clone to a running build and a green test suite.

The project has two independent tracks; pick the one you want to work on:

- **Track A — ML / model** (`ml/`, `reports/`): Python pipeline, training,
  calibration, evaluation, TFLite export.
- **Track B — Android app** (`android/`): Kotlin + Jetpack Compose, CameraX,
  on-device inference, storage.

---

## 1. Prerequisites

| Track | Tools |
|---|---|
| ML | Python 3.10 (3.11 ok), pip; Linux/WSL2 for GPU (CPU works) |
| Android | JDK 17 or 21, Android Studio Iguana (2023.2)+ / Android SDK API 34 |
| Both (optional) | Docker Desktop — skip the toolchain entirely (`docker-compose.yml`) |

Full step-by-step setup is in [docs/getting-started.md](docs/getting-started.md).

---

## 2. Get the TFLite models (required to run the app)

The three `.tflite` cascade models are **not committed** to git (binary
artifacts — see `.gitignore`). The app compiles without them, but every scan
fails until they are present in `android/app/src/main/assets/`:

```
stage1_leaf_float16.tflite      # 1.92 MB — leaf gate
stage2_tomato_float16.tflite    # 1.92 MB — tomato gate
stage3_disease_float16.tflite   # 6.03 MB — 11-class disease classifier
```

Obtain them by either:

1. **Downloading** them from the
   [Releases](https://github.com/AlBaraa63/TomatoCare/releases) page, or
2. **Producing** them with the ML pipeline (`docs/getting-started.md` → ML
   track), which writes them to `ml/models/tflite/`.

Then copy all three into `android/app/src/main/assets/`.

---

## 3. Build and test

**Android:**

```bash
cd android
./gradlew :app:assembleDebug     # build the debug APK
./gradlew :app:test              # run the 42 JVM unit tests (no device needed)
./gradlew :app:installDebug      # install on a connected device/emulator
```

**ML:**

```bash
pip install -r ml/requirements.txt
python -m ml.scripts.eval_model
```

Continuous integration ([.github/workflows/android-ci.yml](.github/workflows/android-ci.yml))
runs the unit tests and assembles the APK on every push and pull request. **Your
change must keep CI green.**

---

## 4. Coding conventions

**Kotlin / Android**

- Material 3 + Jetpack Compose. Use `MaterialTheme.colorScheme.*` tokens — do not
  hard-code colors (semantic status colors live in `ui/theme/Color.kt`).
- Keep business logic out of Composables and Android-coupled classes where it can
  be a pure function/object (see `HomeStats`, `SeverityHeuristic`,
  `TrainingDataExporter.resolveLabel`) so it can be unit-tested without a device.
- Every user-facing string goes in **both** `res/values/strings.xml` (English)
  and `res/values-ar/strings.xml` (Arabic). No hard-coded UI text.
- Icons that convey meaning need a localised `contentDescription`.
- The ML↔app class-name contract (`TomatoClasses.CLASS_NAMES`) is enforced by
  `ClassNamesTest` — keep it alphabetical and in sync with `training_config.yaml`.

**Python / ML**

- Never hand-edit metric numbers. The single source of truth is
  `ml/reports/eval_deployed.json`; every reported figure must trace back to it.
- Pipeline scripts are single-responsibility and cached by output artifact.

---

## 5. Tests

- Add or update unit tests for any logic change. Tests live in
  `android/app/src/test/kotlin/com/tomatocare/`.
- For new app features, add a row to the FR matrix in
  [docs/functional_tests.md](docs/functional_tests.md).
- Keep documentation in sync: app internals in [docs/android-app.md](docs/android-app.md),
  system design in [docs/architecture.md](docs/architecture.md).

---

## 6. Pull requests

1. Branch off `main`.
2. Make focused commits with clear messages.
3. Ensure `./gradlew :app:test` and `:app:assembleDebug` pass locally (CI will
   re-check).
4. Update the relevant docs and, if user-facing, the FR matrix.
5. Open a PR against `main` describing **what** changed and **why**.

---

## 7. License

By contributing you agree that your contributions are licensed under the
project's [MIT License](LICENSE).
