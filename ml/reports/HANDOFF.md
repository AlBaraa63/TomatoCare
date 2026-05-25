# TomatoCare — Session Handoff / Context Brief

> **Purpose:** paste this (or point the new chat at this file) to transfer full
> context. Written 2026-05-25 after the ML experimentation phase.
> Author: AlBaraa AlOlabi (solo capstone, Al Ain University).

---

## 1. What TomatoCare is

Offline-first, bilingual (EN / Arabic RTL) **Android app** that diagnoses tomato
leaf diseases on-device. No internet permission. Capstone 2 project (v2 is a
redesign of a v1 that had a critical safety flaw).

**Core ML = a 3-stage TFLite cascade** (all MobileNetV3, float16, ~6 MB total):

| Stage | Model | Task | Classes |
|---|---|---|---|
| 1 | MobileNetV3-Small | leaf / not-leaf gate | binary |
| 2 | MobileNetV3-Small | tomato / other-leaf gate | binary |
| 3 | MobileNetV3-Large | disease classifier | 11 (10 diseases + healthy) |

Why a cascade: v1 was a single classifier with a `not_tomato` reject class —
it silently misclassified non-tomato images as diseases with high confidence.
The cascade hard-rejects non-tomato inputs at the gates. This is the headline
architectural contribution.

The 11 classes: bacterial_spot, early_blight, healthy, late_blight, leaf_mold,
mosaic_virus, powdery_mildew, septoria_leaf_spot, spider_mites, target_spot,
yellow_leaf_curl_virus.

---

## 2. Hard rules (from CLAUDE.md — do not violate)

- **Preprocessing contract:** float32[1,224,224,3], RGB, center-crop to square,
  resize 224, divide by 255 → [0,1]. **NO ImageNet mean/std normalisation.**
  Must be byte-identical in Python training and Kotlin inference.
- No INTERNET permission. No Room/SQLite (JSON flat file only). kotlinx.serialization
  (not Gson/Moshi). Min SDK 26.
- Don't commit trained weights or datasets to git (`.gitignore` enforces it;
  android assets `*.tflite` are intentionally untracked — a `model_card.md`
  records what's deployed instead).
- All strings through resources (EN + AR), never hardcoded.

---

## 3. The central scientific story (most important section)

**The lab→field domain gap, measured and explained.**

- Training data is **PlantVillage** (lab photos: uniform light backgrounds, studio
  lighting, macro lens). Real use is **field photos** (cluttered backgrounds,
  natural light, phone cameras).
- Deployed model: **97.55% lab end-to-end** → **77.2% field end-to-end**
  (measured on PlantDoc real field photos, n=79 test). ~20-point gap.

**Four experiments tried to close the gap. ALL failed. This is the contribution.**

| # | Experiment | Direction | Result |
|---|---|---|---|
| 1 | Heavy UAE augmentation (brightness/contrast/gamma/hue/sat/JPEG/blur) | train→field | field −11.4 pts, NOT deployed |
| 2 | MobileSAM leaf segmentation fold-in | train→field | slight decline, reverted |
| 3 | DCGAN synthetic bacterial_spot (+600 imgs) | train→field | zero improvement |
| 4 | Test-time normalization (segment field leaf → white bg) | inference→lab | field −30.4 pts |
| (extra) | Lighting-only augmentation (brightness/contrast/gamma, no colour jitter) | train→field | field −1.3 pts (97.9% lab) |

**The decisive insight (§16 vs §17 of the report):**
- Perfect **lab leaf** + bad (field-noise) background → 65.5%
- Field leaf + perfect **white background** → 46.8%
- ⇒ **The leaf appearance dominates the domain gap, not the background.**
  You cannot transform your way across the gap from either side.

**Mechanistic per-class finding (composited eval, §16):** gates are 99.4%
background-robust. But lesion-based classes depend on white-background contrast:
- Background-INDEPENDENT (strong): late_blight, mosaic_virus, yellow_leaf_curl_virus
- Background-DEPENDENT (weak): early_blight (collapses to 13% on non-white!),
  bacterial_spot, target_spot — these have dark spots that need white contrast.

**Conclusion: only real field data closes the gap.** The app has an in-app
feedback flywheel (collects + labels real field photos from users) built for
exactly this.

---

## 4. What's deployed RIGHT NOW

- **Stage 3 = "ctrl" model**: minimal augmentation (flip only), trained AFTER
  PlantDoc integration. It beats the original baseline on BOTH lab (96.5%) and
  field (77.2%). Deployed to `android/app/src/main/assets/stage3_disease_float16.tflite`.
- Stages 1 & 2 unchanged.
- Temperature scaling applied to Stage 3 (Guo et al. 2017): T baked into weights,
  ECE 0.07 → 0.0046. Accuracy unchanged, confidence now calibrated.
- The 60% low-confidence banner threshold relies on this calibration.

---

## 5. Repo + environment

- **Main repo (git):** `C:\Users\POTATO\Desktop\TomatoCare`
  - Remote: https://github.com/AlBaraa63/TomatoCare
  - Active branch: `sprintA/app/onboarding` (pushed; PR to main not yet opened)
  - NOTE: `C:\Users\POTATO\Desktop\TomatoCare-v2` is a separate planning folder
    (CLAUDE.md + Notion links live there). The CODE and report live in
    `TomatoCare`. Everything was consolidated into `TomatoCare` per the user.
- **ML code:** `ml/tree/` (train.py, export.py, predict.py, evaluate_tree.py,
  gan_dcgan.py, gan_field_eval.py, segment_leaves.py, composite_eval.py,
  da_segment.py, da_eval.py, ...)
- **Report:** `ml/reports/report_ai_section.md` (19 sections, complete).
- **Android:** `android/` (Kotlin, Jetpack Compose, TFLite cascade).

**WSL environment (training runs in WSL, NOT git-bash):**
- TF venv: `/home/albaraa/.venvs/tomatocare-wsl/bin/python` (TensorFlow + CUDA)
- Seg venv: `/home/albaraa/.venvs/seg-wsl/bin/python` (torch + MobileSAM)
- Data root: `/home/albaraa/tc_data/` (stage{1,2,3}_*, tflite_*, gan/, _img/plantdoc/)
- MobileSAM weights: `/mnt/c/Users/POTATO/Desktop/F-UNet/.../MobileSAM/weights/mobile_sam.pt`
- **Invoke WSL from git-bash like this** (avoids path mangling):
  `MSYS_NO_PATHCONV=1 wsl.exe -- bash -c '/home/albaraa/.venvs/tomatocare-wsl/bin/python ...'`
- For long training, use the harness background-run, not nohup (WSL kills detached children).

**train.py `--aug` modes:** heavy (full UAE, degrades field), lighting
(brightness/contrast/gamma only — colour-safe), minimal (flip only — what ctrl
uses), none.

---

## 6. External advisors (context for emails)

- **Dr. Yazeed** — suggested "lightweight augmentation" + motion blur emphasis.
  (We over-did it with "heavy" aug; lighting-only is the lightweight version.)
- **Armagan Elibol** (Heriot-Watt Dubai) — suggested GAN for a custom validation
  set. We pivoted GAN to training augmentation (sounder), ran controlled A/B,
  got zero improvement. Email sent 2026-05-25 explaining this honestly; awaiting reply.

---

## 7. Recent git history (sprintA/app/onboarding)

```
[TC-26] docs: test-time domain adaptation §17, update conclusion
[TC-25] ml: test-time domain adaptation experiment (field→lab)
[TC-24] docs: composited-background validation §16
[TC-23] ml: composited-background field validation
[TC-22] ml+docs: lighting aug experiment, deploy ctrl stage3, model card
[TC-21] ml: add lighting-only augmentation mode
[TC-20] docs: complete AI/ML report (was 17 sections, now 19)
[TC-19] ml: aug flag, segmentation, DCGAN, field eval experiments
[TC-18] android: in-app feedback flywheel, onboarding, training export
```

---

## 8. What's LEFT to do (open tasks)

1. **Open the PR** `sprintA/app/onboarding` → main (branch pushed; GitHub CLI not
   installed, so create it via the web UI).
2. **Export report to .docx** for submission (`ml/reports/report_ai_section.md`).
3. **Notion** task cards / Decisions Log updates were SKIPPED at user's request —
   may need doing for the capstone process.
4. Optional app work: Phase 2 CameraX (live capture), per-class confidence thresholds.
5. The ML investigation is **complete** — no more experiments needed. The story
   is clean: 4 falsified hypotheses → real-data flywheel is the answer.

---

## 9. User context

Solo capstone student, was feeling overwhelmed at one point — values honest
assessment, clear next steps, and not being over-helped. Prefers committing work
in clean logical chunks with `[TC-NN]` commit prefixes. Switched to Opus for the
domain-adaptation reasoning. Goal throughout: make the app **actually valid in a
real-world environment**, not just look good on lab numbers.
