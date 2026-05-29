# Changelog

All notable changes to TomatoCare are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/). The model/metrics single source
of truth is `reports/eval_deployed.json`; this log covers application and
documentation changes.

## [Unreleased]

### Fixed
- **Gallery picks crashed the app.** Captured images were decoded with
  `BitmapFactory.decodeFile(uri.path)`, which returns `null` for gallery
  `content://` URIs → NPE (broke FR-05). Decoding now happens in `ScanViewModel`
  from the content resolver, off the main thread, with EXIF-correct `ImageDecoder`
  on API 28+; a failed decode shows a message instead of crashing.
- **Home "Health Rate" was permanently 0%.** It counted `conditionId ==
  "tomato_healthy"`; the canonical id is `"healthy"` (matches
  `assets/treatments.json`).
- **Theme and language changes did not apply until app restart.** `SettingsStore`
  exposed only a one-shot `read()`. It now exposes a reactive
  `StateFlow<UserSettings>`; `MainActivity` collects it so the theme switches
  live and a language change re-applies the locale via `recreate()`.
- **Home last-scan card** showed the English condition name even in Arabic mode.
- **ResultScreen** rendered a blank screen for a missing/loading scan; it now has
  explicit loading, not-found, no-diagnosis, and error states.

### Added
- **Dark mode** (Light / Dark / System) with full light & dark Material 3 color
  schemes; selectable in Settings.
- **Disease Encyclopedia** tab — searchable, bilingual browser of all conditions
  and their treatments.
- **Home dashboard** — total scans, health rate, distinct conditions, and a
  disease-distribution chart.
- **In-app feedback flywheel** — "Was this correct?" capture on results plus a
  `TrainingDataExporter` that bundles verified images (grouped by true label +
  `manifest.json`) for retraining, fully offline.
- **Unit-test suite expanded 23 → 42 tests:** `SeverityHeuristicTest`,
  `HomeStatsTest` (incl. a health-rate regression test), `TrainingLabelTest`,
  and `FeedbackSerializationTest` (round-trip + backward compatibility).
- **GitHub Actions CI** (`.github/workflows/android-ci.yml`) — runs the unit
  tests and assembles the debug APK on every push/PR; README build badge.
- **Inference-latency measurement (NFR-02 evidence).** Total cascade time is now
  persisted on the `ScanRecord` and shown on the results screen ("Diagnosed
  on-device in *N* ms"); per-stage timing (leaf / tomato / disease) is logged
  under the `TomatoCarePerf` logcat tag. **Measured on a physical device (n = 10):
  12–20 ms (median 13.5), ~150× under the 3 s NFR-02 budget** — written up in
  report §7.9, Table 7.6.
- **`CONTRIBUTING.md`** and documented model-acquisition path so a fresh clone is
  runnable (models are released/produced separately, not committed).

### Changed
- Extracted pure, testable logic out of Android-coupled classes:
  `SeverityHeuristic` (from `TFLiteEngine`), `HomeStats` (from `HomeViewModel`),
  and `TrainingDataExporter.resolveLabel`.
- Localised the camera screen's icon content descriptions (Arabic accessibility).
- Removed a dead `groupBy` in the Encyclopedia treatment list.
- Documentation refreshed to match the shipped app: `docs/android-app.md`,
  `docs/architecture.md`, `docs/functional_tests.md` (now FR-01..FR-28), and the
  top-level `README.md` (badges + Engineering Practices section).

### Notes
- The CI build badge shows "no status" until the workflow runs once on GitHub.
- CI builds an APK **without** the TFLite models (gitignored); the
  compile/unit-test signal is unaffected because models load by name at runtime.
- `reports/FINAL_REPORT_REVISED.md` is mirrored by a hand-built `.docx`; report
  edits must be applied to the Word file manually.
