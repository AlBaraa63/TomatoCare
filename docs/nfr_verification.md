# TomatoCare — NFR Verification Report

Numeric placeholders live in [ml/results/nfr_verification.json](../ml/results/nfr_verification.json). This document is the
human-readable companion: how to run each test, what counts as pass, and where
to look up the result.

## NFR-01 — Zero network calls
**Method:** Put the test device in airplane mode for the entire FR-01..FR-20 run.
**Pass:** Every functional test passes without any "no internet" prompts or
failures. The app never makes a connection attempt because the `INTERNET`
permission is not declared in the manifest.

## NFR-02 — Inference ≤ 3 s
**Method:** Snapdragon 660-class device (Pixel 3a or similar mid-range Android phone). Time 10 fresh scans; report the average.
**Field source:** `TFLiteEngine.classify` measures `inferenceTimeMs`; surface it via Logcat or the result UI's debug overlay during testing.
**Pass:** mean ≤ 3000 ms.

## NFR-03 — Accuracy ≥ 90 %
**Method:** Read `overall_accuracy` from `ml/results/eval_report.json`. This is produced by `ml/scripts/eval_model.py` on the held-out test split; if accuracy < 0.90 the script exits non-zero and the build cannot ship.
**Pass:** field present and ≥ 0.90.

## NFR-04 — APK ≤ 50 MB, model ≤ 15 MB
**Method:** Build the release APK (`gradlew :app:assembleRelease` from `android/`). Open the resulting `app-release.apk` in Android Studio → "Analyze APK". Read total APK size and the `assets/tomatocare_model_float16.tflite` entry size.
**Pass:** APK ≤ 50 MB AND .tflite ≤ 15 MB. The export script (`ml/scripts/export_tflite.py`) refuses to write a .tflite > 15 MB.

## NFR-05 — Two-tap reach
**Method:** Starting on Home, count taps to reach each core function: Scan (1), History (1), Settings (1), Open a saved result from History (2). The Home screen lists the "Last scan" card that opens Result in a single tap.
**Pass:** every core function reachable in ≤ 2 taps.

## NFR-06 — 50 consecutive scans, zero crashes
**Method:** Either automate with an Espresso UI test that loops 50 times, or scan 50 leaves manually back-to-back without killing the app. Watch Logcat for crashes.
**Pass:** 50 scans complete, app survives, history shows 50 records (or 50 minus any explicit deletions).

## NFR-07 — API 26 AND API 34
**Method:** Install release APK on both an API 26 (Android 8.0) emulator and an API 34 (Android 14) emulator. Complete the full scan flow on each.
**Pass:** both emulators render correctly and inference returns without crash.

## NFR-08 — Zero outbound traffic
**Method:** Configure the device's Wi-Fi proxy to a `mitmproxy` instance on the host. Install the mitmproxy CA cert so HTTPS is intercepted. Perform 10 scans, 1 export, 1 import. Inspect the mitmproxy flow window.
**Pass:** zero outbound requests to non-localhost destinations. Localhost requests from Android system services unrelated to TomatoCare are excluded.

## Sign-off

| NFR    | Verified by | Date       | Pass? |
|--------|-------------|------------|-------|
| NFR-01 |             |            |       |
| NFR-02 |             |            |       |
| NFR-03 |             |            |       |
| NFR-04 |             |            |       |
| NFR-05 |             |            |       |
| NFR-06 |             |            |       |
| NFR-07 |             |            |       |
| NFR-08 |             |            |       |
