# TomatoCare — Model Card

## Deployed cascade (current)

| File | Stage | Backbone | Lab acc | Field acc (PlantDoc) |
|---|---|---|---|---|
| stage1_leaf_float16.tflite | Leaf gate | MobileNetV3-Small | 99.55% not-leaf recall | — |
| stage2_tomato_float16.tflite | Tomato gate | MobileNetV3-Small | 99.37% other-leaf recall | — |
| **stage3_disease_float16.tflite** | Disease classifier | MobileNetV3-Large | **98.5% disease acc** | **77.2% e2e** |

**TFLite format:** float16 weight quantisation  
**Input contract:** float32[1, 224, 224, 3], RGB, values in [0.0, 1.0] (divide by 255, no ImageNet normalisation)  
**Total size:** ~6.0 MB (all three models combined)  
**NFR-04 budget:** 15 MB ✓

---

## Stage 3 model history

| Version | Training recipe | Lab e2e | Field e2e | Status |
|---|---|---|---|---|
| v1 (original) | Single classifier, heavy aug, pre-PlantDoc | ~97.5% | 74.7% | Replaced |
| ctrl (current) | Minimal aug (flip only), post-PlantDoc integration | 96.5% | **77.2%** | ✅ Deployed |
| heavy-aug | Full UAE augmentation | 95.17% | 63.3% | Rejected — field degradation |
| +GAN | Minimal aug + 600 synthetic bacterial_spot | 96.5% | 74.7% | Rejected — no improvement |
| lighting-aug | Brightness/contrast/gamma only | 97.9% | 73.4% | Rejected — marginal degradation |

**Decision rationale:** The ctrl model (minimal augmentation, trained after PlantDoc field data
integration) achieves the best field performance across all evaluated variants. Three augmentation
approaches (heavy UAE, GAN synthetic data, lighting-only) all failed to improve or degraded
real-world accuracy — see ml/reports/report_ai_section.md §§6, 14, 15 for full analysis.

---

## Confidence calibration

Temperature scaling applied to Stage 3 (Guo et al., 2017).  
Temperature T = 0.5889, baked into final Dense layer weights.  
ECE pre-calibration: ~0.07 | ECE post-calibration: **0.0046**

---

## Classes (Stage 3)

Index order matches `labels.json`:

| Index | Class key | Recall (lab) |
|---|---|---|
| 0 | bacterial_spot | 0.944 |
| 1 | early_blight | 0.913 |
| 2 | healthy | ~0.98 |
| 3 | late_blight | ~0.97 |
| 4 | leaf_mold | ~0.97 |
| 5 | mosaic_virus | ~0.99 |
| 6 | powdery_mildew | 0.996 |
| 7 | septoria_leaf_spot | 0.920 |
| 8 | spider_mites | ~0.96 |
| 9 | target_spot | ~0.96 |
| 10 | yellow_leaf_curl_virus | 0.998 |

---

## Known limitations

- **Lab-to-field gap:** 97.55% lab → 77.2% field end-to-end. Measured on PlantDoc (n=79 test).
- **Bacterial spot field recall:** 2/9 (22%) on field images — weakest class.
- **Gap closure path:** In-app feedback flywheel collects real UAE field images for future retraining.

*Last updated: May 2026 — AlBaraa AlOlabi, TomatoCare Capstone 2, Al Ain University*
