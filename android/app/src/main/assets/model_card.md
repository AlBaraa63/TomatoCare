# TomatoCare — Model Card

> All laboratory metrics below were recomputed by evaluating the **deployed TFLite
> artifacts** in this folder against the held-out `tomato20k/valid` test set
> (6,683 images). Source of truth: `ml/reports/eval_deployed.json`.

## Deployed cascade (current)

| File | Stage | Backbone | Size | Lab metric | Field (PlantDoc) |
|---|---|---|---|---|---|
| stage1_leaf_float16.tflite | Leaf gate | MobileNetV3-Small | 1.92 MB | 99.55% not-leaf rejection recall† | — |
| stage2_tomato_float16.tflite | Tomato gate | MobileNetV3-Small | 1.92 MB | 99.37% other-leaf rejection recall† | — |
| **stage3_disease_float16.tflite** | Disease classifier | MobileNetV3-Large | 6.03 MB | **97.59% disease acc** | **77.2% e2e** |

**Cascade end-to-end (lab):** 97.19%  |  **Cascade end-to-end (field, PlantDoc n=79):** 77.2%
**Total size:** 9.87 MB (1.92 + 1.92 + 6.03) — within the 15 MB NFR-04 budget ✓
**Input contract:** float32[1, 224, 224, 3], RGB, [0,1] (divide by 255, no ImageNet normalisation), center-crop to square.

† Gate rejection-recall and leak rate are gate-model properties carried from the prior
evaluation (the gate models are unchanged); they were not regenerated in the latest pass and
should be re-verified on a held-out hard-negative set.

---

## Stage 3 model history

| Version | Training recipe | Lab e2e | Field e2e | Status |
|---|---|---|---|---|
| v1 (original) | Single classifier, pre-PlantDoc | ~97.5% | 74.7% | Replaced |
| **ctrl (current)** | Minimal aug (flip only), post-PlantDoc | **97.19%** | **77.2%** | ✅ Deployed |
| heavy-aug | Full UAE augmentation | 95.17% | 63.3% | Rejected — field degradation |
| +GAN | Minimal aug + 600 synthetic bacterial_spot | ~96.5% | 74.7% | Rejected — no improvement |
| lighting-aug | Brightness/contrast/gamma only | ~97.9% | 73.4% | Rejected — no field gain |

**Decision rationale:** the ctrl model (minimal augmentation, trained after PlantDoc field
integration) was selected on **field** performance, not lab score. Three augmentation
approaches all failed to improve real-world accuracy — see `ml/reports/report_ai_section.md`
§§6, 14, 15 and `FINAL_REPORT.md` Ch 7.

---

## Confidence calibration

Temperature scaling applied to Stage 3 (Guo et al., 2017); T = 0.5889 baked into the final
dense layer (accuracy unchanged).
**ECE on held-out test set (deployed model): 0.061** (15-bin).
The earlier 0.0046 figure was measured in-sample on the temperature-fitting (validation)
split and does not hold out-of-sample. A dedicated held-out calibration set and re-fit on
the deployed model is required to substantiate a tighter ECE (future work).

---

## Classes (Stage 3) — recall on held-out lab test

Index order matches `labels.json`:

| Index | Class key | Recall | n |
|---|---|---|---|
| 0 | bacterial_spot | 0.980 | 732 |
| 1 | early_blight | 0.943 | 643 |
| 2 | healthy | 0.988 | 805 |
| 3 | late_blight | 0.976 | 792 |
| 4 | leaf_mold | 0.972 | 739 |
| 5 | mosaic_virus | 0.986 | 584 |
| 6 | powdery_mildew | 1.000 | 252 |
| 7 | septoria_leaf_spot | 0.957 | 746 |
| 8 | spider_mites | 0.975 | 435 |
| 9 | target_spot | 0.991 | 457 |
| 10 | yellow_leaf_curl_virus | 0.992 | 498 |

Overall Stage 3 accuracy: 97.59% (n = 6,683). Weakest classes early_blight (0.943) and
septoria_leaf_spot (0.957) — the small-dark-lesion cluster.

---

## Known limitations

- **Lab-to-field gap:** 97.19% lab → 77.2% field end-to-end. Measured on PlantDoc (n=79).
- **Bacterial spot field recall:** weakest on field images; not improved by any augmentation
  experiment (heavy aug, GAN, lighting).
- **Calibration not verified out-of-sample:** test-set ECE is 0.061; tighter calibration is
  future work.
- **Gap closure path:** in-app feedback flywheel collects real field images for retraining.

## Data provenance

- **Disease classes (Stage 3):** `tomato20k` — a PlantVillage-derived tomato collection
  (10 classes) plus a **powdery_mildew** class not present in the original PlantVillage
  tomato subset. 25,851 train / 6,683 test. The exact public source of tomato20k (and of the
  powdery_mildew class) must be cited in the final report.
- **Tomato-gate negatives:** PlantVillage non-tomato crops (pepper, potato — 4,627 images) +
  PlantDoc non-tomato field leaves.
- **Field data:** PlantDoc tomato (824 train folded in; 79 held out as field benchmark).

*Last updated: 2026-05-26 — recomputed against deployed TFLite. AlBaraa AlOlabi, Capstone 2.*
