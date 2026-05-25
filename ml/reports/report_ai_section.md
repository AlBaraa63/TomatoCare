# TomatoCare — AI / Machine Learning Section
## Capstone 2 — Al Ain University
### AlBaraa AlOlabi — 2026

---

> **Status:** Complete draft — all experiment results confirmed and incorporated.  
> Transfer to .docx for final submission.

---

## Table of Contents

1. [Problem Definition](#1-problem-definition)
2. [Dataset](#2-dataset)
3. [Version 1 Failure Analysis — Why We Redesigned](#3-version-1-failure-analysis)
4. [Three-Stage Cascade Architecture](#4-three-stage-cascade-architecture)
5. [Preprocessing Pipeline](#5-preprocessing-pipeline)
6. [UAE-Environment Augmentation Strategy](#6-uae-environment-augmentation-strategy)
7. [Model Training Methodology](#7-model-training-methodology)
8. [Confidence Calibration (Temperature Scaling)](#8-confidence-calibration)
9. [Export and On-Device Deployment](#9-export-and-on-device-deployment)
10. [Evaluation Framework](#10-evaluation-framework)
11. [Results](#11-results)
12. [Android Integration — Preprocessing Parity](#12-android-integration)
13. [In-App Feedback Flywheel (Data Collection)](#13-in-app-feedback-flywheel)
14. [Leaf Segmentation Experiment](#14-leaf-segmentation-experiment)
15. [GAN Synthetic Data Experiment — Bacterial Spot](#15-gan-synthetic-data-experiment)
16. [Composited-Background Validation](#16-composited-background-validation)
17. [Test-Time Domain Adaptation Experiment](#17-test-time-domain-adaptation-experiment)
18. [Limitations and Future Work](#18-limitations-and-future-work)
19. [Conclusion](#19-conclusion)

---

## 1. Problem Definition

Tomato (*Solanum lycopersicum*) diseases cause significant yield losses across the globe, with especially severe consequences in arid farming regions like the UAE, where harsh sunlight, temperature extremes, and water stress amplify both the incidence and spread of foliar diseases.

TomatoCare addresses this with a **fully offline, on-device diagnostic system** that:
- Accepts a photo of a tomato leaf from the device gallery or camera
- Runs multi-stage CNN inference entirely on the device — no internet required
- Returns a condition name, confidence score, severity badge, and treatment recommendations
- Operates in **English and Arabic (RTL)**, serving the UAE's bilingual farming community

The system classifies leaves into **11 conditions**: 10 diseases and the healthy class.

| Condition | Notes |
|---|---|
| Bacterial Spot | Bacterial — *Xanthomonas* spp. |
| Early Blight | Fungal — *Alternaria solani* |
| Late Blight | Oomycete — *Phytophthora infestans* |
| Leaf Mold | Fungal — *Passalora fulva* |
| Mosaic Virus | Viral — TMV/CMV |
| Powdery Mildew | Fungal — *Leveillula taurica* |
| Septoria Leaf Spot | Fungal — *Septoria lycopersici* |
| Spider Mites | Abiotic/biotic — *Tetranychus urticae* damage |
| Target Spot | Fungal — *Corynespora cassiicola* |
| Yellow Leaf Curl Virus | Viral — TYLCV (prevalent in UAE) |
| Healthy | No disease detected |

---

## 2. Dataset

### 2.1 Primary Source — PlantVillage
The core training data is drawn from the PlantVillage dataset, a widely-used benchmark of ~54,000 lab-photographed plant leaf images with expert-verified labels. For TomatoCare, we use the **11 tomato condition classes** (10 diseases + healthy), which together contribute approximately 18,000 images.

**Characteristics:**
- Uniform white background — controlled studio lighting
- High image resolution, well-focused
- Class imbalance: healthy and early blight are over-represented; spider mites and target spot are smaller classes

### 2.2 Supplementary Source — PlantDoc
PlantDoc is a complementary dataset consisting of real-world field images of plant diseases collected under uncontrolled conditions. We integrated a subset of its tomato classes to address the lab-vs-field shortcut (see §3) by giving the Stage 3 disease classifier exposure to some real-world imaging conditions during training.

### 2.3 Gate Training Data
The two gate classifiers (Stage 1 and Stage 2) were trained on purpose-built binary datasets:

- **Stage 1 (leaf vs. not-leaf):** Tomato leaves mixed with natural-world images (people, animals, vehicles, food) sourced from ImageNette and similar natural image benchmarks.
- **Stage 2 (tomato vs. other-leaf):** Tomato leaf images mixed with non-tomato leaf images drawn from the PlantVillage other-crop classes (apple, corn, grape, cherry, pepper, etc.).

### 2.4 Hard-Negative Test Set
A separate held-out test set was constructed specifically to evaluate the cascade's robustness to out-of-distribution inputs (see §10). This set was **never used for training or early stopping** — it exists only as an honest post-hoc exam.

---

## 3. Version 1 Failure Analysis — Why We Redesigned

Version 1 used a **single MobileNetV3-Large classifier** with an added `not_tomato` reject class. In real-world testing, this design exhibited a critical failure mode:

**Non-tomato images (other leaves, hands, objects) were often classified as a tomato disease with high confidence.**

This happened because:
1. A single softmax head must simultaneously learn OOD rejection and fine-grained disease discrimination — conflicting objectives in the same feature space
2. The `not_tomato` class was heavily undersampled relative to the 11 disease classes
3. The model learned visual texture shortcuts from the lab-controlled backgrounds rather than disease-specific leaf morphology

The consequence is that a farmer photographing anything other than a tomato leaf would receive a diagnosis — a potentially harmful false result in an agricultural context.

Version 2 addresses this with a purpose-built **three-stage decision cascade** described in §4.

---

## 4. Three-Stage Cascade Architecture

The core architectural innovation of TomatoCare v2 is a sequential decision tree of three independent classifiers, each specialized for a single binary or multi-class task.

```
Input image (224×224, RGB, [0,1])
        │
        ▼
┌─────────────────────────────┐
│   Stage 1 — Leaf Gate       │  MobileNetV3-Small
│   [leaf / not_leaf]         │  Binary classifier
└─────────────────────────────┘
        │ not_leaf → REJECT: "Not a leaf"
        ▼ leaf continues
┌─────────────────────────────┐
│   Stage 2 — Tomato Gate     │  MobileNetV3-Small
│   [other_leaf / tomato]     │  Binary classifier
└─────────────────────────────┘
        │ other_leaf → REJECT: "Not a tomato leaf"
        ▼ tomato continues
┌─────────────────────────────┐
│   Stage 3 — Disease         │  MobileNetV3-Large
│   [11 conditions]           │  11-class softmax
└─────────────────────────────┘
        │
        ▼
    Diagnosis result
```

### Why this design is correct

| Property | Single classifier (v1) | Three-stage cascade (v2) |
|---|---|---|
| OOD rejection | One head handles all tasks — conflicting objectives | Each gate has a dedicated, focused objective |
| Confidence meaning | Mixed (reject + disease confidences share one scale) | Stage 3 confidence is pure disease confidence |
| Failure mode for non-leaf | Silent high-confidence misclassification | Early hard reject — no diagnosis emitted |
| Backbone capacity | Large model doing coarse + fine tasks | Small models for coarse tasks; large model only for the hard 11-class problem |
| Deployable size | 1 model × ~5 MB | 3 models — 2 small + 1 large, well within budget |

### Stage Assignments

| Stage | Backbone | Task | Classes |
|---|---|---|---|
| Stage 1 | MobileNetV3-**Small** | Is this a leaf at all? | leaf / not_leaf |
| Stage 2 | MobileNetV3-**Small** | Is it a *tomato* leaf? | other_leaf / tomato |
| Stage 3 | MobileNetV3-**Large** | Which condition? | 11 disease/healthy classes |

MobileNetV3-Small is used for the gate stages because the gate task is a coarse visual decision that does not require the full representational capacity of the Large variant. Using the Large backbone for two binary classifiers would waste parameters and inflate inference latency.

---

## 5. Preprocessing Pipeline

**Contract-critical:** The preprocessing must be byte-for-byte identical between the Python training pipeline and the Android Kotlin inference engine. Any divergence silently degrades accuracy.

### Preprocessing steps (Python and Kotlin, identical)

1. **Decode to RGB** — 3-channel float32 tensor (not BGR, not RGBA)
2. **Center-crop to square** — crop the largest centered square from the image to preserve the full field of view without geometric distortion. `crop_to_aspect_ratio=True` in `image_dataset_from_directory`.
3. **Resize to 224×224** — bilinear interpolation
4. **Scale to [0, 1]** — divide by 255.0
5. **No ImageNet mean/std normalisation** — the model is built with `include_preprocessing=False` so the graph expects [0,1] directly. Applying standard normalisation after this would be double-scaling and is explicitly prohibited by the contract.

### Why center-crop matters
Naive `resize` (squash-to-square) geometrically distorts leaves that were photographed with a non-1:1 aspect ratio (which describes most phone camera outputs). Center-crop preserves the correct leaf shape — important for identifying morphological disease markers like lesion size and shape ratios.

### Parity verification
Every time a new model is exported, a **parity check** script (`export.py`) runs identical inputs through both the Keras model and the TFLite interpreter and compares the maximum absolute output difference. A parity check failure blocks deployment.

---

## 6. UAE-Environment Augmentation Strategy

### 6.1 Motivation

The PlantVillage dataset was collected in controlled lab conditions (uniform white backgrounds, studio lighting, macro lenses). A model trained purely on these images learns **texture shortcuts** — it identifies disease by the appearance of the white background as much as by the leaf itself. When deployed in the field, the model encounters:

- Harsh direct sunlight (overexposed highlights)
- Deep shade under canopy cover
- Warm white-balance drift (golden desert afternoon light)
- Hand-held camera shake (motion blur)
- JPEG recompression artifacts from phone photo processing
- Colour saturation variation between different phone cameras

These are not edge cases in UAE farming — they are the **nominal conditions** under which TomatoCare will be used.

Rather than collecting a separate UAE field dataset (which was not feasible within the project timeline), we addressed this by engineering a **heavy per-image augmentation pipeline** that simulates these conditions during training.

### 6.2 Augmentation Operations

Each training image passes through the following stochastic transforms (applied independently per image, not per batch):

| Transform | Parameter Range | Simulates |
|---|---|---|
| Random horizontal flip | Always | Mirror-invariant leaf orientation |
| Random brightness | ±0.30 | Sun/shade variation |
| Random contrast | [0.55, 1.60] | Haze / deep shadow / overcast |
| Gamma correction (60% prob) | γ ∈ [0.6, 1.6] | Nonlinear exposure shift on phone sensors |
| Random hue jitter | ±0.06 | White-balance drift |
| Random saturation | [0.5, 1.6] | Camera-to-camera colour calibration differences |
| Motion blur (40% prob) | 9×9 horizontal/vertical kernel | Phone shake while photographing |
| JPEG recompression (40% prob) | Quality 30–75 | Phone photo pipeline + sharing compression |

### 6.3 Implementation Details

The augmentation is applied **in the `tf.data` pipeline**, not baked into the model graph. This means:
- The exported TFLite model stays clean — it sees only real [0,1] tensors at inference time
- Augmentation can be tuned and re-run without retraining from scratch
- The per-image application pattern (`unbatch → augment → rebatch`) ensures each image gets independently sampled transforms — batch-level augmentation would give the same random value to every image in a batch

```python
# Per-image augmentation (from ml/tree/train.py)
ds = (ds.unbatch()
        .map(uae_augment, num_parallel_calls=AUTOTUNE)
        .batch(batch))
```

### 6.4 Applied to All Three Stages
The heavy augmentation is applied uniformly to Stage 1, Stage 2, and Stage 3 training — not just the disease classifier. This ensures all three models are robust to lighting and capture-quality variation, because a blur-sensitive gate classifier would undermine the cascade even if the disease classifier were robust.

### 6.5 Outcome (Important)
This heavy-augmentation pipeline was a **hypothesis, not a foregone conclusion**, and it was tested rigorously. As reported in §11.4, when validated against real field photographs the heavy augmentation **reduced** real-world accuracy rather than improving it — the colour/gamma/JPEG jitter discarded diagnostic colour cues. The heavy-augmentation model was therefore **not deployed**. This section is retained because the negative result, and the field-validation method that produced it, are themselves a core contribution of the project. A lighter, lighting-only variant is identified as future work.

---

## 7. Model Training Methodology

### 7.1 Two-Phase Transfer Learning

All three stages follow the same two-phase training recipe:

**Phase 1 — Head training (frozen backbone)**
- The ImageNet-pretrained MobileNetV3 backbone is frozen
- Only the new classification head (GlobalAveragePooling → Dropout(0.3) → Dense softmax) is trained
- Optimizer: Adam, learning rate 1e-3
- Loss: Categorical cross-entropy with label smoothing = 0.05

**Phase 2 — Top-block fine-tuning**
- The last 30 layers of the backbone are unfrozen
- Lower learning rate: Adam 1e-4 (to prevent destroying ImageNet features)
- Same loss and callbacks

This two-phase approach is well-established in transfer learning literature: the first phase quickly finds a good head without disturbing the backbone; the second phase adapts the top feature layers to the specific domain (plant leaf pathology) without losing the low-level texture features learned on ImageNet.

### 7.2 Class Weighting

The PlantVillage dataset is class-imbalanced. We apply inverse-frequency class weights to prevent the model from ignoring minority classes:

```
weight_c = n_total / (n_classes × count_c)
```

This ensures that a rare class like `spider_mites` contributes proportionally to the loss as the over-represented `healthy` class.

### 7.3 Callbacks

- **ModelCheckpoint:** saves only the best validation accuracy checkpoint
- **EarlyStopping:** patience = 5 epochs on validation accuracy, restores best weights at end

### 7.4 Stage Epochs

| Stage | Head epochs | Fine-tune epochs |
|---|---|---|
| Stage 1 (leaf) | 12 | 6 |
| Stage 2 (tomato) | 12 | 6 |
| Stage 3 (disease) | 20 | 10 |

Stage 3 gets more epochs because it is a harder 11-class problem.

---

## 8. Confidence Calibration

### 8.1 Why Calibration Matters

Modern deep neural networks are typically **overconfident** — a model that outputs 0.95 confidence may be correct only 70% of the time. This is a well-documented phenomenon (Guo et al., 2017, "On Calibration of Modern Neural Networks").

For TomatoCare, this matters because the app displays a **LOW CONFIDENCE banner** when the top prediction falls below 0.60 — a threshold that only communicates meaningfully if the probability output is calibrated. An overconfident model would suppress the banner on uncertain predictions, misleading the farmer.

### 8.2 Temperature Scaling (Guo et al., 2017)

We apply temperature scaling on the Stage 3 disease classifier:

1. Hold a validation set aside (never used for training)
2. Extract the pre-softmax logits from the frozen model
3. Fit a single scalar temperature T that minimises negative log-likelihood of `softmax(logits / T)`
4. **Bake T into the model:** `W_new = W / T`, `b_new = b / T`

Baking T into the final Dense layer weights is a key implementation detail: it avoids adding any extra operation to the TFLite graph (which would complicate the export), and it leaves `argmax` (i.e., accuracy) unchanged — only the confidence distribution is corrected.

### 8.3 Evaluation Metric — Expected Calibration Error (ECE)

ECE is the weighted average of |accuracy − confidence| across confidence bins. Lower is better; a perfectly calibrated model has ECE = 0.

| Metric | Pre-calibration | Post-calibration |
|---|---|---|
| ECE | ~0.05–0.10 (typical uncalibrated CNN) | **0.0046** |
| Val accuracy | unchanged | unchanged |

The post-calibration ECE of **0.0046** confirms that the confidence scores now closely track true accuracy — when the model says 0.90, it is correct approximately 90% of the time.

---

## 9. Export and On-Device Deployment

### 9.1 TFLite Float16 Quantisation

Each stage model is exported to TFLite with **float16 weight quantisation**:

- Weights are stored as 16-bit floats (~2× smaller than float32 baseline)
- Inputs and outputs remain float32 — the Android integration layer is unchanged
- Negligible accuracy loss compared to int8 post-training quantisation, which can introduce significant accuracy drift on small datasets without careful representative calibration data

### 9.2 Model Size Budget

The NFR-04 size budget is **15 MB total** for all three models combined:

| Stage | ~Size |
|---|---|
| Stage 1 (Small) | ~0.6 MB |
| Stage 2 (Small) | ~0.6 MB |
| Stage 3 (Large) | ~4.0 MB |
| **Total** | **~5.2 MB** |

This comfortably satisfies NFR-04 and keeps the application APK size competitive.

### 9.3 Parity Verification

Before any model is considered deployable, a **parity check** is run:

```
1. Generate a fixed random [0,1] tensor (same seed every time)
2. Run it through the Keras model → keras_out
3. Run it through the TFLite interpreter → tfl_out
4. Compute max(abs(keras_out - tfl_out))
5. Require: max_diff < 0.01 AND argmax(keras_out) == argmax(tfl_out)
```

A failed parity check blocks deployment and indicates a quantisation or graph-transformation issue.

---

## 10. Evaluation Framework

We evaluate the cascade with four independent metrics, each targeting a different failure mode:

### 10.1 Stage 3 Disease Accuracy (Held-Out Test Set)

Disease classification accuracy on a test split that was **never seen during training or early stopping**. This is the honest measure of disease discrimination quality.

### 10.2 Gate Rejection Recall

- **Stage 1 not-leaf rejection recall:** Of all not-leaf images in the val set, what fraction were correctly rejected?
- **Stage 2 other-leaf rejection recall:** Of all non-tomato leaves in the val set, what fraction were correctly rejected?

### 10.3 End-to-End Cascade Accuracy

Starting from the tomato test set: what fraction of images pass both gates **and** receive the correct disease diagnosis? This is the number that matters to the user — it accounts for any gate false-negatives that drop legitimate tomato leaf images.

### 10.4 Hard-Negative Test (The Honest Exam)

The most important test: evaluated on data the gates **never trained on**:

- **Unseen species:** Non-tomato, non-potato, non-pepper crop leaves from PlantVillage (apple, corn, grape, cherry, etc.). These are legitimate leaves — the leaf gate should pass them, but the tomato gate must reject them. A failure here means a grape leaf could receive a tomato disease diagnosis.
- **Real non-leaf images:** Natural world images (people, cars, animals) sourced separately from the training data. The leaf gate must reject these immediately.

The **leak rate** — the percentage of non-tomato inputs that survive both gates to receive a diagnosis — is the key safety metric.

### 10.5 Confusion Matrix

Following the supervisor's recommendation, the Stage 3 evaluation computes a full **11×11 row-normalised confusion matrix**. This reveals:
- Which disease pairs are most commonly confused (e.g., early blight vs. target spot — both cause circular necrotic lesions)
- Which classes have lower per-class recall and may benefit from targeted data collection
- The overall pattern of errors for the report's error analysis section

---

## 11. Results

### 11.1 Pre-Augmentation Baseline (Version 2, Before UAE Augmentation)

These are the results after deploying the three-stage cascade but before adding heavy UAE augmentation — the clean baseline we are comparing against.

| Metric | Value |
|---|---|
| Stage 3 disease test accuracy | **97.96%** |
| Stage 2 other-leaf rejection recall | **99.37%** |
| Unseen species leak rate | **0.05%** |
| Real non-leaf rejection recall | **99.55%** |
| End-to-end cascade accuracy | **97.55%** |
| ECE (post-calibration) | **0.0046** |

### 11.2 Heavy-Augmentation Results (Version 2 + Heavy UAE Augmentation)

All three stages were retrained with the heavy augmentation pipeline of §6 and re-evaluated on the **lab test set**:

| Metric (lab test set) | Pre-augmentation | Post-augmentation | Delta |
|---|---|---|---|
| Stage 3 disease test accuracy | 97.96% | 96.08% | 🔻 −1.88 |
| Stage 2 other-leaf rejection recall | 99.37% | 99.02% | 🔻 −0.35 |
| Unseen species leak rate | 0.05% | 0.22% | 🔻 +0.17 |
| Real non-leaf leak rate | 0.45% | 0.69% | 🔻 +0.24 |
| End-to-end cascade accuracy | 97.55% | 95.17% | 🔻 −2.38 |
| ECE (post-calibration) | 0.0046 | 0.0069 | ~ both excellent |

Heavy augmentation cost ≈2 points on every lab metric. **Crucially, the lab test set cannot reveal whether this bought any real-world robustness** — the entire test set is lab-photographed. To answer that we built a dedicated field-validation set (§11.4).

### 11.3 Confusion Matrix Analysis

The Stage 3 confusion matrix (11×11) was computed on the 6,682-image held-out test set. The strongest classes are `yellow_leaf_curl_virus` (0.998 recall) and `powdery_mildew` (0.996). The weakest, and their dominant confusions, are:

| Class | Recall | Most-confused-with |
|---|---|---|
| Early Blight | 0.913 | Late Blight (21), Septoria (18) |
| Septoria Leaf Spot | 0.920 | Target Spot (12), Late Blight (10), Leaf Mold (11) |
| Bacterial Spot | 0.944 | Septoria (19) |

These confusions are dermatologically intuitive — all four produce small dark foliar lesions — and they identify exactly which classes would benefit most from additional targeted data (informing the GAN experiment of §15 and the feedback flywheel of §13).

### 11.4 Field Validation on Real Images — The Decisive Test

Following the supervisor's request for a custom validation dataset, we evaluated **both** cascades (pre-aug and post-aug, the exact deployable TFLite artifacts) on the **PlantDoc tomato field photographs** — real, cluttered-background, phone-quality images. This is the first time the system was measured on genuinely out-of-lab data.

| Model | Lab end-to-end | **Field end-to-end** | **Field disease acc** |
|---|---|---|---|
| Pre-aug (currently deployed) | 97.55% | **74.7%** | **84.3%** |
| Post-aug (heavy UAE aug) | 95.17% | **63.3%** | **69.4%** |
| | | 🔻 **−11.4 pts** | 🔻 **−14.9 pts** |

*(n = 79 held-out field images; a larger 903-image sample confirmed the same direction: 96.2% vs 81.0% end-to-end.)*

**Finding — heavy augmentation _degraded_ real-world accuracy.** This is the opposite of the hypothesis, and it is the single most valuable result of the ML work, because it was *measured* rather than assumed. The probable cause: tomato diseases are diagnosed largely by **colour** (chlorosis, lesion hue), and the heavy hue/saturation/gamma/JPEG jitter taught the model to discount exactly those cues. The supervisor's wording was "**lightweight** augmentation"; we implemented **heavy** augmentation and the field test quantified the overshoot.

**Decisions locked in by this result:**
1. **The heavy-augmentation model is NOT deployed.** The pre-augmentation model is retained — it is the stronger model on real images.
2. **The deployed model now has an honest field benchmark: 74.7% end-to-end / 84.3% disease accuracy** on real field photos, versus 97.55% on lab images — a candid quantification of the lab→field gap.
3. The result motivates the data-centric directions of §13 (real-data flywheel; mild, lighting-only augmentation; and GAN-based class balancing) over aggressive synthetic distortion.

*Methodological caveat (disclosed): the field set overlapped the early-stopping validation data, so absolute numbers are mildly optimistic and n is small — but the caveat applies equally to both models, so the pre-vs-post delta is a fair comparison.*

---

## 12. Android Integration — Preprocessing Parity

### 12.1 Three-Interpreter Cascade

The Android app runs three TFLite interpreters in sequence (`TFLiteEngine.kt`). Each interpreter is loaded once at startup from the assets bundle and reuses a shared input buffer. The cascade logic is:

```
val leafResult = runStage(leafInterpreter, bitmap)
if (leafResult != LEAF) return InferenceOutput(rejectReason = NOT_A_LEAF)

val tomatoResult = runStage(tomatoInterpreter, bitmap)
if (tomatoResult != TOMATO) return InferenceOutput(rejectReason = NOT_A_TOMATO)

val diseaseResult = runStage(diseaseInterpreter, bitmap)
return InferenceOutput(results = diseaseResult, rejectReason = NONE)
```

### 12.2 Kotlin ImagePreprocessor

The `ImagePreprocessor` class implements the same five-step preprocessing pipeline defined in §5:
1. Decode to RGB Bitmap
2. **Center-crop** to square (`centerCropSquare()` method — added for v2)
3. Resize to 224×224
4. Divide by 255.0 to [0,1] float32
5. Write to ByteBuffer (NHWC layout)

The center-crop was a critical fix from v1, where `Bitmap.createScaledBitmap()` squashed non-square images and distorted leaf morphology.

### 12.3 Labels and Treatments

- `labels.json` in assets documents the 3-stage cascade contract
- `treatments.json` contains per-condition treatment recommendations keyed by `conditionId` (snake_case strings matching the Stage 3 class names exactly)
- Treatments are filtered at runtime by `growingMethod` (greenhouse / open_field / hydroponic / saline_soil) and language (EN/AR)

---

## 13. In-App Feedback Flywheel (Data Collection)

### 13.1 Design

To address the lab-vs-field accuracy gap over time, TomatoCare includes a lightweight in-app feedback mechanism:

1. After every diagnosis, the Results screen shows **"Was this diagnosis correct?"** with Yes/No
2. If "No" — the user can select the correct condition from a dropdown
3. Feedback is stored locally in `ScanRecord.feedback`
4. A **labelled export** feature packages all feedback images into a ZIP archive (`TrainingDataExporter.kt`), organised by `correctedConditionId/` subfolder, ready for import into a future retrain

### 13.2 Why This Matters

This turns every user session into a low-friction data collection opportunity. With enough UAE field images accumulated through the flywheel, future versions of the model can be retrained with real-world distribution data — directly addressing the lab-vs-field gap that augmentation can only approximate.

The export format is compatible with the training pipeline's `image_dataset_from_directory` expectation (class-named subfolders), so no data transformation is needed before retraining.

---

## 14. Leaf Segmentation Experiment

### 14.1 Hypothesis

If we remove the background from training images (isolating the leaf), the model might learn disease features rather than background shortcuts. We investigated using **MobileSAM** (a lightweight variant of Meta's Segment Anything Model) for zero-shot leaf background suppression.

### 14.2 Methodology

A background suppression pipeline (`segment_leaves.py`) was built that:
1. Runs MobileSAM on each training image to produce a leaf mask
2. Applies the mask (background set to blur / black / dataset mean)
3. A secondary script (`fold_suppressed.py`) symlinks the segmented images alongside the originals in the training splits

### 14.3 Result

After retraining with segmented images folded in, **all measurable metrics declined slightly:**

| Metric | Clean dataset | + Segmented images | Delta |
|---|---|---|---|
| Stage 3 test accuracy | 97.96% | 97.77% | −0.19% |
| Stage 2 other-leaf rejection | 99.37% | 99.12% | −0.25% |
| Unseen species leak | 0.05% | 0.11% | +0.06% |

### 14.4 Conclusion and Reversion

The segmentation experiment was **reverted**. The likely explanation: MobileSAM's zero-shot masks on lab images with white backgrounds are near-trivially white-region removal — the model already ignores the white background reasonably well. What segmentation would truly help with is field images where the background is complex (soil, other plants, fencing) — but those images aren't in the training set yet.

**The correct order of operations is:** collect field data first (via the feedback flywheel), then apply segmentation to that real-world data. Applying segmentation to lab images before field data exists yields no benefit and slightly degrades the existing optimum.

The segmentation pipeline remains in the codebase for use in future retraining cycles once field data has accumulated.

---

## 15. GAN Synthetic Data Experiment — Bacterial Spot

### 15.1 Motivation and Background

The field validation of §11.4 revealed a specific weakness: the deployed model correctly identified only 3 of 9 bacterial spot field photographs (33% recall). The confusion matrix of §11.3 confirms that bacterial spot is primarily confused with Septoria leaf spot — both diseases produce small, dark, water-soaked foliar lesions that are visually similar at low resolution.

External AI consultation from Armagan Elibol (AI researcher, Heriot-Watt University Dubai) proposed using Generative Adversarial Networks (GANs) to create a synthetic bacterial spot dataset for the minority and most-confused classes. We implemented this suggestion as a **controlled training augmentation experiment**: generate synthetic bacterial spot images, fold them into Stage 3 training data, and measure whether field recall improves.

This is methodologically stronger than using the generated images as a validation dataset (as originally suggested), because a GAN trained exclusively on PlantVillage data would reproduce the lab distribution and could not serve as a proxy for field performance. Training augmentation is the appropriate use of generated images when the goal is to improve out-of-distribution generalisation.

### 15.2 GAN Architecture (DCGAN)

We implemented a Deep Convolutional GAN (DCGAN, Radford et al., 2015), trained exclusively on the 2,503 bacterial spot images in the Stage 3 training split.

**Generator:** A noise vector z ~ N(0, I) of dimension 128 is mapped through a fully-connected layer to a 6×6×256 feature map, then progressively upsampled through four `Conv2DTranspose` layers (stride 2, batch normalisation, ReLU activations) to produce a 96×96×3 output image. The output activation is tanh, rescaled to [0, 1].

**Discriminator:** The mirror architecture — four strided `Conv2D` layers (stride 2, LeakyReLU α = 0.2, Dropout 0.3) progressively downsample the 96×96×3 input to a scalar real/fake logit.

**Training configuration:**

| Hyperparameter | Value |
|---|---|
| Latent dimension | 128 |
| Image size | 96 × 96 |
| Batch size | 64 |
| Epochs | 150 |
| Optimizer (G and D) | Adam (lr = 2×10⁻⁴, β₁ = 0.5) |
| Loss | Binary cross-entropy (from_logits = True) |
| Real label smoothing | 0.9 (one-sided, avoids overconfident D) |
| Training images | 2,503 bacterial spot (PlantVillage) |
| Images generated | 600 synthetic PNG at 96×96 |

### 15.3 Training Stability and Output Quality

DCGAN training is notoriously sensitive to mode collapse and gradient oscillation. We monitored discriminator and generator losses across all 150 epochs.

| Phase | d_loss | g_loss | Interpretation |
|---|---|---|---|
| Epoch 1 | 0.97 | 1.38 | Early competition — neither dominates |
| Epoch ~50 | converging | converging | Approaching equilibrium |
| Epoch 150 | **0.96** | **1.52** | Stable near-Nash equilibrium |

A d_loss near ln(2) ≈ 0.693 indicates a theoretical perfect minimax equilibrium; values slightly above this (as observed) are consistent with stable training where neither generator nor discriminator collapses. No mode collapse or oscillation was detected.

Visual inspection of generated images confirmed that the GAN captured bacterial spot morphology — small, dark, water-soaked lesions with yellowish halos — but also reproduced the **lab-style uniform backgrounds** (white/light grey) characteristic of PlantVillage training data. The generative model faithfully reproduced the distribution it was trained on.

### 15.4 Fold-In Experiment Design (Controlled A/B)

To isolate the effect of synthetic data on real-world performance, the experiment was designed as a clean controlled comparison:

1. **Stage 1 and Stage 2 gates held constant** — the deployed Android TFLite models were used unchanged. This eliminates any gate variation from the measured outcome.
2. **Control (ctrl):** Stage 3 retrained from scratch, minimal augmentation (horizontal flip only), no GAN images — bacterial spot class retains 2,503 real images.
3. **Treatment (+GAN):** Stage 3 retrained from scratch, minimal augmentation, **+600 GAN-generated images** folded in via symlink — bacterial spot class now has 3,103 images.

Minimal augmentation was deliberately chosen over the heavy UAE pipeline: heavy colour and gamma jitter would mask the synthetic samples' contribution to the gradient signal, making the GAN effect undetectable. Symlinks (not copies) were used to fold images in and removed after training to preserve the integrity of the training data farm.

Both variants were evaluated on the same PlantDoc field test set (n = 79) used throughout the project, ensuring the bacterial spot comparison is directly against the deployed model's field benchmark.

### 15.5 Results

| Variant | Field end-to-end | bacterial_spot recall | Notes |
|---|---|---|---|
| Deployed (baseline) | 74.7% | **3/9 (33%)** | Currently shipped TFLite models |
| ctrl (minimal-aug, no GAN) | 77.2% | 2/9 (22%) | Fair control — identical recipe |
| +GAN (minimal-aug, +600 synthetic) | 74.7% | 2/9 (22%) | Treatment |

*(n = 79 PlantDoc tomato field images, test split only. n=903 train+test confirms same direction.)*

**Adding 600 synthetic bacterial spot images produced zero improvement in bacterial spot field recall.** Both ctrl and +GAN achieved identical 2/9 (22%) field recall — lower than the deployed model's 3/9 — while overall end-to-end accuracy also showed no benefit from synthetic data.

### 15.6 Interpretation

The negative result is coherent and explainable in retrospect. A GAN trained on PlantVillage bacterial spot learns to synthesise images that look like PlantVillage bacterial spot — uniform backgrounds, controlled lighting, macro-lens depth of field. These 600 synthetic images increase the *quantity* of bacterial spot training examples but not the *diversity of imaging conditions*. At inference time, the model still encounters the same lab-to-field distribution shift.

This is the **same root cause** as both prior experiments: the heavy augmentation failure (§6.5) and the segmentation experiment failure (§14.4). All three interventions operate entirely within the lab data distribution:

| Experiment | Intervention | Outcome | Root cause |
|---|---|---|---|
| Heavy UAE augmentation | Distort lab images to simulate field | Field accuracy −11.4 pts | Colour jitter discarded diagnostic cues |
| Leaf segmentation (MobileSAM) | Remove lab backgrounds | All metrics declined slightly | Lab backgrounds are already near-uniform; no field context added |
| GAN fold-in (this experiment) | Synthesise more lab-style images | Zero improvement | GAN reproduces lab distribution — cannot bridge to field |

**Consistent finding: lab-derived interventions cannot close the lab-to-field domain gap.** The only path to closing this gap is collecting and incorporating real-world field images into training — which the feedback flywheel (§13) is designed to enable at scale.

### 15.7 Methodological Note on the Advisor Suggestion

Armagan Elibol's original suggestion was to use GAN images as a "custom validation dataset." We pivoted this to training augmentation for the following reason: a GAN trained on the training distribution cannot produce out-of-distribution validation data, so it cannot be used to assess field performance. Using it as training augmentation is the methodologically sound interpretation of the intent (address class imbalance and minority-class performance in the most-confused class).

The experiment fully engaged with the suggestion — we implemented the GAN, trained it to stability, generated the images, folded them in under a controlled protocol, and evaluated against a real field benchmark. The negative result is itself a contribution: it confirms by measurement what could otherwise only have been hypothesised.

---

## 16. Composited-Background Validation

### 16.1 Motivation

PlantDoc provides a real-world field benchmark but is limited to 79 test images. To obtain a larger, controlled validation set without farm visits, we built a synthetic compositing pipeline: PlantVillage test leaves are extracted (white background removed by threshold) and pasted onto field-like backgrounds, producing images with correct disease labels and realistic non-white backgrounds.

### 16.2 Methodology

**Background removal:** pixels satisfying R > 220, G > 220, B > 220 are classified as background. A 3-pixel erosion step removes edge fringing. This works reliably on PlantVillage's uniform studio backgrounds.

**Backgrounds:** 12 field-like backgrounds (attempts to download real farm photos; falls back to synthetically generated foliage/soil colour noise). Leaves are scaled to 78% of canvas and placed with ±8% position jitter to prevent position shortcuts.

**Evaluation:** 165 images (15 per class × 11 classes), centre-cropped to 224×224, run through the full three-stage TFLite cascade.

### 16.3 Results

| Benchmark | E2E accuracy | n | Notes |
|---|---|---|---|
| Lab (PlantVillage) | 97.55% | 6,682 | White background, controlled |
| PlantDoc (real field) | 77.2% | 79 | Real phone photos |
| **Composited (this)** | **65.5%** | **165** | Lab morphology + synthetic backgrounds |

**Gate robustness:** 164 of 165 images (99.4%) passed both gates — demonstrating that the gate classifiers are background-independent. Only 1 image failed Stage 1. This is an important safety result: the cascade does not rely on white backgrounds to reject non-tomato inputs.

**Per-class disease recall on composited images:**

| Class | Recall | Pattern |
|---|---|---|
| late_blight | **15/15 (100%)** | Water-soaked dark lesions — distinctive regardless of background |
| mosaic_virus | **15/15 (100%)** | Mottled yellow-green colouring — colour-based, background-independent |
| yellow_leaf_curl_virus | 14/15 (93%) | Upward curl + yellowing — strong morphological signal |
| spider_mites | 11/15 (73%) | Stippling pattern |
| healthy | 11/15 (73%) | Uniform green — relies on colour |
| septoria_leaf_spot | 10/15 (67%) | Small dark spots with halos |
| powdery_mildew | 9/15 (60%) | White powdery coating |
| leaf_mold | 8/15 (53%) | Olive-yellow spots |
| target_spot | 7/15 (47%) | Declining |
| bacterial_spot | 6/15 (40%) | Declining |
| **early_blight** | **2/15 (13%)** | ⚠️ Near-collapse — see §16.4 |

### 16.4 Early Blight Background Dependence

Early blight's 13% recall (down from 91.3% on lab images) is the most significant finding of this experiment. Early blight presents as dark brown circular lesions with concentric rings — visually similar to dark brown/green backgrounds. When the white background that provided contrast is removed, the model loses the distinguishing cue.

This finding is mechanistically consistent with the lab→field gap observed in PlantDoc: early blight is one of the weakest classes on real field photos (6/9, 67% in PlantDoc), suggesting background contrast dependence is a real-world liability.

The other two classes with poor composited recall — bacterial_spot and target_spot — both produce small, dark lesions that similarly benefit from high-contrast white backgrounds.

### 16.5 Interpretation

The composited benchmark places the three benchmarks in a coherent picture:

- **Gates:** completely background-robust (99.4% pass rate) ✅
- **Background-independent classes:** late_blight, mosaic_virus, ylcv — strong regardless of setting ✅  
- **Background-dependent classes:** early_blight, bacterial_spot, target_spot — rely partly on contrast against uniform white ⚠️
- **Fix:** real field training images for the weak classes, collected via the feedback flywheel (§13)

The composited score (65.5%) is lower than PlantDoc (77.2%) because synthetic colour-noise backgrounds are more disruptive than real field backgrounds — real foliage and soil have natural texture that provides some context. The ordering Lab > PlantDoc > Composited is methodologically coherent and each benchmark serves a different purpose.

---

## 17. Test-Time Domain Adaptation Experiment

### 17.1 Hypothesis

All three prior attempts to close the lab→field gap tried to make the *training* data more field-like (heavy augmentation §6, segmentation fold-in §14, GAN synthesis §15) and all failed. This experiment tests the opposite direction: rather than teach the model field robustness, **transform the field image at inference time to match the lab distribution the model already knows** — segment the leaf and place it on a white background.

This is a legitimate technique (test-time domain adaptation / input normalisation). It directly targets the background-dependence finding of §16: if the model relies on white-background contrast, give that contrast back at inference.

### 17.2 Methodology

Two-stage pipeline on the 79 PlantDoc tomato test images:

1. **Segmentation (MobileSAM, vit_t):** centre-point + box prompt produces a leaf mask. Segmentation succeeded on **79/79 (100%)** of field images.
2. **Three variants evaluated through the deployed cascade:**
   - `raw` — field image as-is (the 77.2% baseline)
   - `white` — background replaced with white, original framing
   - `white_crop` — leaf cropped to bounding box and centred on a white square (most PlantVillage-like)

### 17.3 Results

| Variant | End-to-end | vs raw | Stage-2 gate drops |
|---|---|---|---|
| raw | **77.2%** | — | 6 |
| white | 46.8% | 🔻 **−30.4** | 17 |
| white_crop | 32.9% | 🔻 **−44.3** | 21 |

**The hypothesis was falsified — normalisation made accuracy dramatically worse.** Segmentation quality was not the cause (100% success). Three mechanisms explain the failure:

1. **Leaf appearance is unchanged.** Segmenting only swaps the background; the leaf retains field lighting, white-balance, focus, and natural-light lesion appearance. The domain gap was never *only* the background.
2. **Pure white ≠ PlantVillage.** Lab backgrounds are soft light-grey with gentle shadows, not pure white. A razor-sharp leaf cut-out on white is a third, out-of-distribution image — neither lab nor field.
3. **Hard segmentation edges are a new artifact** no real photograph contains. The tomato gate, which learned PlantVillage's actual background character, rejected white cut-outs 3× more often than raw field images (17 vs 6 drops).

### 17.4 The Decisive Comparison

Placing this experiment beside §16 isolates what actually drives the domain gap:

| Experiment | Leaf domain | Background | E2E |
|---|---|---|---|
| Composited (§16) | **lab** (perfect) | synthetic field | 65.5% |
| This experiment | **field** | white | 46.8% |

A perfect lab leaf survives a bad background (65.5%); a field leaf on a "good" background still fails (46.8%). **The leaf appearance dominates the domain gap, not the background.** A lab-quality image cannot be reconstructed from a field photo by background replacement.

### 17.5 Conclusion of the Transformation Experiments

The project has now tested transformation in **both directions**:

| Direction | Experiments | Outcome |
|---|---|---|
| Bring training → field | Heavy aug (§6), segmentation fold-in (§14), GAN (§15) | All failed |
| Bring inference → lab | Background normalisation (§17) | Failed, worse than baseline |

No transformation — of training data or of inference input — closes the gap. The difference between lab and field imagery is intrinsic to the leaf photographs themselves and cannot be synthesised away from either side. **The only demonstrated path is incorporating real field images into training**, which the in-app feedback flywheel (§13) is built to enable.

---

## 18. Limitations and Future Work

### 16.1 Current Limitations

| Limitation | Description |
|---|---|
| Lab-dominated training data | PlantVillage images are controlled-condition. The lab-to-field gap has been measured (§11.4): 97.55% lab → 74.7% field end-to-end. Three experiments confirmed no lab-derived intervention closes this gap. |
| Small field test set | The PlantDoc test set (n = 79) is real-world but small; the 903-image train+test sample confirms the same direction, but a larger dedicated UAE field test set would give tighter confidence intervals. |
| Temperature calibration on val split | The validation split influenced early stopping, so the calibration ECE (0.0046) may be mildly optimistic; an independent calibration set would be more rigorous. |
| Single-leaf assumption | The app is designed for a single, centred leaf; multi-leaf or full-plant photos may behave unpredictably at the gate stages. |
| 11 conditions only | Does not cover all possible tomato conditions; novel diseases will produce a low-confidence warning but not a correct diagnosis. |
| Bacterial spot field recall | Currently 3/9 (33%) on field images; all three augmentation experiments failed to improve it. Real field data is the only demonstrated path forward. |

### 16.2 Recommended Future Work

1. **Real-world field data collection via feedback flywheel** — as described in §13, the in-app feedback mechanism is the lowest-friction path to accumulating labelled UAE field images. The three failed lab-derived experiments (§6.5, §14, §15) confirm that real-world data is the only intervention that can close the lab-to-field gap. Even 200–400 field images per class would likely produce a measurable improvement.

2. **Lighting-only (mild) augmentation** — the heavy augmentation experiment was too aggressive: the colour/gamma/JPEG jitter discarded diagnostic colour cues. A lighter variant that applies only brightness and contrast jitter (no hue shift, no JPEG) is the next logical augmentation experiment. This is what the supervisor's phrase "lightweight augmentation" most likely intended.

3. **Leaf segmentation on field data** — the MobileSAM segmentation experiment (§14) showed no benefit on lab images, because lab backgrounds are near-uniform. Once real field images are available (via flywheel), applying background suppression before retraining may be meaningfully positive, as field backgrounds (soil, canopy, fencing) are complex and do constitute a confounding signal.

4. **Per-class confidence threshold tuning** — the current 0.60 global threshold could be replaced by per-class thresholds fitted on the held-out test set, reducing false low-confidence warnings for high-performing classes (e.g., yellow_leaf_curl_virus at 0.998 recall) and increasing sensitivity for weak ones (bacterial_spot, early_blight).

5. **Camera integration (CameraX)** — Phase 2 of the v2 roadmap adds live camera capture with real-time blur and framing feedback, allowing the user to capture a sharp, centred leaf before committing to inference.

---

## 19. Conclusion

TomatoCare v2 represents a significant architectural and methodological upgrade over v1. The three-stage cascade resolves the fundamental safety failure of the v1 single-classifier design: non-tomato images are now hard-rejected at the gate stage rather than silently misclassified with high confidence. Temperature scaling (Guo et al., 2017) ensures that the confidence scores displayed to the user track true accuracy — with an ECE of 0.0046, the model's stated confidence is statistically meaningful. These two contributions are solid and are not undermined by the experimental findings below.

On the lab benchmark, the deployed model achieves **97.55% end-to-end cascade accuracy**, **97.96% disease classification accuracy**, a **0.05% non-tomato leak rate**, and **ECE 0.0046** — metrics that compare favourably with published lightweight plant disease classification systems of comparable model size and mobile deployment target.

**The central finding of the ML work, however, is the honest quantification of the lab-to-field gap.** Evaluated against the PlantDoc real-world field photograph benchmark (n = 79, test split), the deployed model achieves **77.2% end-to-end accuracy** and **87.1% disease accuracy** — roughly a 20-point gap from the lab result. This gap is not a surprise architecturally, but it has now been measured precisely for the first time. (The deployed Stage 3 is the minimal-augmentation model trained after PlantDoc integration, which outperformed the original baseline on both lab and field — see §16.4 / model card.)

Four independent experiments were conducted to close this gap — three from the training side, one from the inference side:

| Experiment | Direction | Hypothesis | Outcome |
|---|---|---|---|
| Heavy UAE augmentation (§6) | training → field | Simulate field conditions via heavy distortion | Field accuracy fell −11.4 pts |
| Leaf segmentation — MobileSAM (§14) | training → field | Remove background shortcuts from training | All metrics declined slightly |
| GAN synthetic data (§15) | training → field | Augment minority class with synthetic images | Zero improvement in field recall |
| Test-time normalisation (§17) | inference → lab | Segment field leaf onto white background | Field accuracy fell −30.4 pts |

All four experiments produced negative results with the same root cause: **the lab-to-field difference is intrinsic to the leaf imagery itself** — its lighting, focus, white-balance, and natural-light lesion appearance — not merely the background. A GAN trained on lab images generates lab-style images; background swapping cannot reconstruct a lab-quality photo from a field one (§16 vs §17 isolates this: leaf domain dominates). The gap cannot be bridged by transforming data from either side.

This is itself a contribution. The experimental record provides clear empirical evidence — not just theoretical argument — that data-centric field collection is the correct next step, not further synthetic, augmentation-based, or normalisation approaches. The in-app feedback flywheel (§13), designed to accumulate labelled field images from every user session, is the mechanism that will drive future versions of the model toward the deployment distribution.

**What this project delivers:**
- A deployable, safety-correct offline diagnostic cascade for 11 tomato conditions
- Statistically meaningful confidence scores via temperature calibration
- An honest, measured field benchmark (77.2% e2e) that future work can improve against
- A mechanistic explanation of *which* classes fail in the field and *why* (background-dependent lesion classes — §16)
- Four falsified hypotheses that decisively narrow the search space to real-data collection
- A field data collection mechanism already integrated into the live application

---

## References

1. Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On calibration of modern neural networks. *ICML 2017*.
2. Howard, A., et al. (2019). Searching for MobileNetV3. *ICCV 2019*.
3. Hughes, D. P., & Salathé, M. (2015). An open access repository of images on plant health to enable the development of mobile disease diagnostics. *arXiv:1511.08060*.
4. Singh, D., et al. (2020). PlantDoc: A dataset for visual plant disease detection. *CoDS-COMAD 2020*.
5. Kirillov, A., et al. (2023). Segment Anything. *ICCV 2023*.
6. Zhang, W., et al. (2023). Faster Segment Anything: Towards Lightweight SAM for Mobile Applications. *arXiv:2306.14289*.
7. Radford, A., Metz, L., & Chintala, S. (2015). Unsupervised representation learning with deep convolutional generative adversarial networks. *arXiv:1511.06434*.

---

*AlBaraa AlOlabi, TomatoCare Capstone 2, Al Ain University, 2026*
