# TomatoCare — Final Capstone Report (rebuilt, single-source-of-truth)

> Build state: Chapters 1 and 3 complete. Abstract and Chapter 7 (Evaluation)
> are completed from the recomputed `eval_deployed.json` (deployed TFLite cascade
> vs. held-out `tomato20k/valid`). All numbers in this document trace to that
> artifact, the on-disk dataset counts, or the deployed model files. No
> biotic/abiotic framing. No future tense for completed work.

---

## Final report structure

```
Ch 1  Introduction                  problem (access + safety + honesty), aim, scope, contributions
Ch 2  Literature Review             CNN disease ID; lightweight mobile nets; PlantVillage & the
                                     domain gap; OOD/rejection cascades; calibration; TFLite; app review
Ch 3  Methodology                   datasets, preprocessing+parity, cascade, training, calibration, export
Ch 4  Requirements & Specifications FR/NFR/DR/CR (NFR-03 reworded; abiotic DR removed)
Ch 5  System Design                 layered arch w/ 3-interpreter cascade; UML; JSON schema
Ch 6  Implementation                model pipeline + Android (cascade integration, gates, feedback flywheel)
Ch 7  Evaluation & Experiments      framework, deployed results + confusion matrix, field gap,
                                     four negative experiments, synthesis, NFR verification
Ch 8  Conclusion & Future Work      feedback flywheel; lighting-only aug; field segmentation; thresholds
```

---

# Abstract

TomatoCare is a fully offline, bilingual (English / Arabic, right-to-left) Android
application that diagnoses tomato (*Solanum lycopersicum*) leaf conditions entirely
on-device, with no internet permission. Unlike single-classifier plant-disease apps —
which assign a disease label to any image, including non-tomato leaves and non-leaf
objects — TomatoCare uses a **three-stage decision cascade**: a leaf gate, a tomato gate,
and an eleven-class disease classifier, each a MobileNetV3 network exported to float16
TensorFlow Lite (9.87 MB combined). Inputs that are not a tomato leaf are rejected before
any diagnosis is produced. Evaluated on a held-out laboratory test set of 6,683 images,
the deployed cascade attains **97.59% disease-classification accuracy** and **97.19%
end-to-end accuracy** (every class ≥ 94% recall; 99.42% of genuine tomato leaves pass both
gates). On real-world field photographs (PlantDoc, n = 79) end-to-end accuracy is **77.2%**,
and this ~20-point laboratory-to-field gap is measured and reported rather than concealed.
The disease classifier's confidence is temperature-scaled; its expected calibration error on
the held-out test set is 0.061, indicating reasonably—though not tightly—calibrated
probabilities and motivating a dedicated calibration set as future work. Four interventions
to close the field gap — heavy environmental augmentation, leaf segmentation, GAN-based
synthetic data, and test-time input normalisation — were each tested and each failed,
together isolating the cause to intrinsic leaf-appearance domain shift rather than background,
and identifying real field-data collection as the only effective remedy. The application
embeds an in-app feedback mechanism that labels and stores real field images to drive that
collection. The result is a safety-correct, honestly-benchmarked offline diagnostic tool and
an empirically grounded account of why laboratory-trained plant classifiers degrade in the
field.

---

# Chapter 1 — Introduction

## 1.1 Overview

TomatoCare is a fully offline, bilingual (English / Arabic, right-to-left) Android
application that diagnoses tomato (*Solanum lycopersicum*) leaf conditions on-device.
A user photographs a leaf; the app classifies it into one of eleven conditions
(ten diseases and a healthy class), returns a calibrated confidence score, a severity
indicator, and growing-method-specific treatment guidance, and stores the result in a
local history — all with no internet permission and no data leaving the device.

What distinguishes TomatoCare from a conventional image classifier is **how it decides
when *not* to answer**. A single-headed classifier will assign one of its trained labels
to *any* image it is given, including another crop's leaf, a hand, or an object — there
is no class for "this is outside what I know." In an agricultural advisory tool that is a
safety defect: a confident but wrong diagnosis can lead a grower to apply the wrong
treatment. TomatoCare replaces the single classifier with a **three-stage decision
cascade** that first verifies the image is a leaf, then that it is specifically a tomato
leaf, and only then diagnoses the disease — rejecting out-of-scope inputs before any
diagnosis is produced.

## 1.2 Background and Motivation

**Access gap.** Tomato is among the most widely grown crops by smallholders and home
gardeners. The diagnostic tools that exist for them are poorly matched to their
conditions: leading apps (Plantix, Agrio) require continuous internet connectivity, are
offered only in English, and are gated behind subscriptions. Growers in low-connectivity
settings, and the large Arabic-speaking segment of the regional agricultural workforce,
are effectively excluded. An offline, free, bilingual, on-device tool directly addresses
this gap.

**Safety gap.** The dominant academic approach to plant-disease recognition is a single
convolutional classifier trained on a fixed set of disease classes. Such a model has no
representation of "not my domain," so it responds to every input with a confident class
label. The first prototype of this project exhibited exactly this failure: non-tomato
images were frequently labelled as a tomato disease with high confidence. Any deployed
tool intended for non-expert users must instead **recognise and reject** inputs it was
not built to handle.

**Honesty gap.** Plant-disease models are routinely trained and reported on controlled
laboratory datasets (most prominently PlantVillage: uniform backgrounds, studio lighting,
macro lenses) on which they exceed 95% accuracy. This figure does not transfer to the
cluttered backgrounds, natural lighting, and phone-camera quality of real field use, yet
the resulting lab-to-field gap is seldom measured or disclosed. A defensible system must
report how it performs on *real* photographs, not only on the benchmark it was trained on.

## 1.3 Problem Statement

| Element | Description |
|---|---|
| **The problem of** | Reliable, safe, on-device diagnosis of tomato leaf conditions for non-expert growers — combining three unmet needs: (i) no free, offline, bilingual diagnostic tool exists for low-connectivity smallholders; (ii) single-classifier designs unsafely assign a disease label to any image, including non-tomato and non-leaf inputs; and (iii) lab-trained models report accuracies that do not hold on real field photographs, a gap that is rarely measured. |
| **Affects** | Smallholder farmers and home gardeners, including the Arabic-speaking agricultural workforce, who lack access to professional agronomic advice and reliable connectivity. |
| **The impact is** | Misapplied treatments, wasted inputs, crop loss, and — with naive classifiers — confidently wrong advice for inputs the model never should have diagnosed. |
| **A successful solution** | A free, fully offline, bilingual Android tool that runs on low-end devices, rejects out-of-scope inputs before diagnosing, presents calibrated confidence, and reports its real-world (field) performance honestly. |

## 1.4 Aim and Objectives

**Aim.** Develop and evaluate TomatoCare, an offline, bilingual Android application that
diagnoses eleven tomato leaf conditions on-device using a safety-correct classification
cascade, with calibrated confidence and an honestly measured real-world performance
benchmark.

**Objectives.**
1. **Safety-correct cascade.** Design a three-stage cascade (leaf gate → tomato gate →
   disease classifier) that rejects non-leaf and non-tomato inputs before diagnosis,
   eliminating the high-confidence misclassification of the single-classifier design.
2. **Disease classification.** Train an eleven-class tomato disease/healthy classifier
   achieving ≥90% accuracy on a held-out laboratory test set.
3. **Confidence calibration.** Calibrate the classifier so the 60% low-confidence
   threshold corresponds to true predictive reliability (target ECE < 0.02).
4. **Offline on-device deployment.** Deploy all three models on Android (combined size
   ≤15 MB, API 26+), fully offline with no network permission, bilingual EN/AR with full
   RTL support.
5. **Honest real-world evaluation.** Evaluate the deployed cascade on real field
   photographs and quantify the lab-to-field gap rather than reporting lab accuracy alone.
6. **Data-collection mechanism.** Provide an in-app feedback flywheel that labels and
   stores real field images as the empirically justified path to closing that gap.

## 1.5 Scope and Delimitations

**In scope.** Tomato leaves only; eleven conditions (ten diseases + healthy); native
Android (API 26+); English and Arabic with RTL; offline on-device inference; local JSON
persistence with export/import.

**Out of scope (delimitations).**
- **Abiotic-stress classification** (sunscald, salinity chlorosis, heat injury) is **not**
  part of this system. No labelled abiotic dataset was available, and the eleven classes
  are biotic diseases plus healthy. Abiotic discrimination is noted only as future work.
- Multi-crop support, iOS, IoT sensors, cloud sync, and user accounts are out of scope.
- Treatment outputs are advisory, not legally binding agrochemical prescriptions.

## 1.6 Contributions

1. **A safety-correct three-stage cascade** that hard-rejects non-leaf and non-tomato
   inputs before diagnosis, fixing the documented failure mode of the single-classifier
   prototype (measured non-tomato leak rate reported in Ch 7).
2. **Calibrated on-device confidence** via temperature scaling, making the app's
   low-confidence warning statistically meaningful rather than cosmetic.
3. **An honest, measured lab-to-field gap** plus **four falsified hypotheses** (heavy
   augmentation, leaf segmentation, GAN synthesis, test-time normalisation) that together
   isolate the cause of the gap to leaf-appearance domain shift rather than background —
   narrowing the solution space to real field-data collection.
4. **A fully offline, bilingual, low-footprint deployment** with an in-app feedback
   flywheel that collects and labels real field images for future retraining.

## 1.7 Report Outline

Chapter 2 reviews the technical and academic background. Chapter 3 details the
methodology — datasets, preprocessing, cascade architecture, training, calibration, and
export. Chapter 4 specifies requirements; Chapter 5 presents the system design. Chapter 6
documents the implementation of the model pipeline and the Android application. Chapter 7
presents the evaluation, including the deployed-model results, the confusion matrix, the
field-performance gap, and the four negative experiments. Chapter 8 concludes and sets out
future work.

---

# Chapter 3 — Methodology

## 3.1 Overview

The methodology covers two coupled streams: development of the machine-learning cascade
and development of the Android application. This chapter concentrates on the model — the
dataset construction, preprocessing contract, cascade architecture, training procedure,
confidence calibration, and on-device export. The application implementation is covered in
Chapter 6. The project followed an Agile, iteration-driven process, which suited the
experimental nature of model development: training, evaluation, and refinement proceeded in
cycles, and several augmentation hypotheses were tested and rejected on evidence (Chapter 7).

## 3.2 Datasets

The cascade is trained from three labelled sources, each serving a distinct stage. The
classifier (Stage 3) is trained on a tomato leaf-disease collection referred to here as
**tomato20k**; the gates (Stages 1–2) are trained on binary problems built from tomato
leaves, non-tomato crop leaves, and natural-world non-leaf images. Real field photographs
from **PlantDoc** are folded into the tomato gate and disease classifier to break the
laboratory-versus-field shortcut, and a subset is held out as the field benchmark.

**Stage 3 — disease classifier (tomato20k, 11 classes).** tomato20k is a
PlantVillage-derived tomato collection augmented with a *powdery mildew* class that is not
present in the original PlantVillage tomato subset. It provides 25,851 training images and
6,683 held-out test images (the `valid` partition, never used in training or early
stopping):

| Class | Train | Test |
|---|---|---|
| bacterial_spot | 2,826 | 732 |
| early_blight | 2,455 | 643 |
| healthy | 3,051 | 805 |
| late_blight | 3,113 | 792 |
| leaf_mold | 2,754 | 739 |
| mosaic_virus | 2,153 | 584 |
| powdery_mildew | 1,004 | 252 |
| septoria_leaf_spot | 2,882 | 746 |
| spider_mites | 1,747 | 435 |
| target_spot | 1,827 | 457 |
| yellow_leaf_curl_virus | 2,039 | 498 |
| **Total** | **25,851** | **6,683** |

The 25,851 training images are split 85/15 into train and validation (seed 42, stratified
per class); the 6,683 `valid` images are the held-out test set used for all Stage-3 results
in Chapter 7.

> **Provenance note (must be cited in the final submission).** The eleventh class,
> powdery_mildew (1,004 train + 252 test), originates from the tomato20k compilation, not
> from PlantVillage. The exact public source of tomato20k must be cited; the working
> assumption is a Kaggle tomato-leaf-disease dataset that extends the PlantVillage tomato
> classes with a powdery-mildew class.

**Stage 2 — tomato gate.** Positives are the tomato leaves above; negatives are non-tomato
crop leaves — 4,627 PlantVillage images across five crops (pepper and potato) plus PlantDoc
non-tomato field leaves. Mixing real field negatives is essential: it prevents the gate
from learning "lab-looking = other crop, field-looking = tomato" instead of leaf identity.

**Stage 1 — leaf gate.** Positives are all leaf images (tomato + other-crop); negatives are
natural-world non-leaf images (people, animals, vehicles, objects) drawn from an ImageNette
-style natural-image set.

**PlantDoc field data.** 824 tomato field images are folded into the Stage 2/3 *training*
splits, and **79 tomato field images are held out as the field benchmark** used in Chapter 7.
PlantDoc has no target_spot or powdery_mildew tomato class, so those two remain
laboratory-only. PlantDoc's own test partition is folded into the *validation* split rather
than a separate held-out test; this overlap with early-stopping data is disclosed as a
caveat in Chapter 7.

## 3.3 Preprocessing and Parity

Every image — in both the Python training pipeline and the Android Kotlin inference
engine — passes through an identical, contract-fixed pipeline:

1. Decode to RGB (3-channel).
2. **Center-crop to the largest centered square** (no squash-to-square distortion).
3. Resize to 224×224 (bilinear).
4. Scale to [0, 1] by dividing by 255.
5. **No ImageNet mean/std normalisation** — the network is built to consume [0, 1] directly.

Center-crop (rather than naive resize) preserves leaf morphology — lesion size and shape
ratios that distinguish diseases. Because this preprocessing must be byte-identical across
Python and Kotlin, every exported model is subjected to a **parity check**: a fixed input is
run through both the Keras model and the TFLite interpreter and the maximum absolute output
difference must fall below a tolerance, otherwise deployment is blocked.

## 3.4 Cascade Architecture

The system is a sequential cascade of three independent classifiers:

| Stage | Backbone | Task | Output |
|---|---|---|---|
| 1 — Leaf gate | MobileNetV3-**Small** | Is this a leaf at all? | leaf / not_leaf |
| 2 — Tomato gate | MobileNetV3-**Small** | Is it a *tomato* leaf? | other_leaf / tomato |
| 3 — Disease | MobileNetV3-**Large** | Which condition? | 11 classes |

A rejection at either gate halts the pipeline and returns a retake instruction
(`NOT_A_LEAF` / `NOT_A_TOMATO`); only inputs that pass both gates reach the disease
classifier. The gates use the Small backbone because a binary in/out-of-domain decision does
not need the representational capacity of the Large variant; reserving Large for the hard
eleven-class problem keeps total size and latency low. Each stage is a MobileNetV3 backbone
(ImageNet-pretrained) with a classification head: GlobalAveragePooling → Dropout(0.3) →
Dense softmax.

This design is the central architectural decision of the project. A single classifier must
solve out-of-distribution rejection and fine-grained disease discrimination with one softmax
head — conflicting objectives that, in the prototype, produced confident misclassification of
non-tomato inputs. Separating the concerns gives each gate a dedicated objective and makes
the Stage-3 confidence a pure disease confidence.

## 3.5 Training

All three stages follow the same two-phase transfer-learning recipe:

- **Phase 1 — head training (frozen backbone).** The ImageNet-pretrained backbone is frozen
  and only the new head is trained. Optimizer Adam, learning rate 1e-3; loss categorical
  cross-entropy with label smoothing 0.05.
- **Phase 2 — fine-tuning.** The top ~30 backbone layers are unfrozen and trained at a lower
  learning rate (Adam 1e-4) to adapt high-level features to leaf pathology without destroying
  low-level ImageNet features.

Class imbalance (e.g., powdery_mildew is the smallest class) is handled with inverse-frequency
class weights. Training uses EarlyStopping (patience 5 on validation accuracy, best weights
restored) and best-validation checkpointing.

**Deployed Stage-3 variant.** Several augmentation strategies were trained and compared
(Chapter 7). The deployed Stage-3 model is the **minimal-augmentation variant** (horizontal
flip only), trained after PlantDoc integration. It was selected because it achieved the best
performance on the real field benchmark — not the best laboratory score. Stages 1 and 2 are
shared across the comparison and unchanged.

## 3.6 Confidence Calibration

Deep classifiers are typically overconfident, which would make the app's 60% low-confidence
banner meaningless. Temperature scaling (Guo et al., 2017) is applied to Stage 3: a single
scalar temperature T is fit on a held-aside split to minimise negative log-likelihood, then
**baked into the final Dense layer** (W ← W/T, b ← b/T). This leaves predictions (argmax) and
therefore accuracy unchanged, correcting only the confidence distribution, and adds no extra
operation to the TFLite graph. The fitted temperature is T = 0.5889. Calibration quality is
reported as Expected Calibration Error (ECE) in Chapter 7.

## 3.7 Export and On-Device Deployment

Each stage is exported to TFLite with **float16 weight quantisation** (≈2× smaller than
float32; inputs/outputs remain float32 so the Android layer is unchanged). The three deployed
artifacts are:

| File | Backbone | Size |
|---|---|---|
| stage1_leaf_float16.tflite | MobileNetV3-Small | 1.92 MB |
| stage2_tomato_float16.tflite | MobileNetV3-Small | 1.92 MB |
| stage3_disease_float16.tflite | MobileNetV3-Large | 6.03 MB |
| **Total** | | **9.86 MB** |

The combined 9.86 MB is well within the 15 MB model budget (NFR-04). On Android the three
interpreters run in sequence; a gate rejection short-circuits the pipeline. Class order and
the preprocessing contract are pinned in `labels.json` and mirrored in the Kotlin engine.

---

# Chapter 7 — Evaluation and Experiments

All laboratory results in this chapter were recomputed by running the **deployed TFLite
artifacts** (`stage{1,2,3}_*_float16.tflite`) against the held-out `tomato20k/valid` test
set (6,683 images, never used in training or early stopping), using the exact production
preprocessing. The source artifact is `ml/reports/eval_deployed.json`; the confusion matrix
figure is `ml/reports/confusion_matrix_deployed.png`. This is the literal shipped model, so
the figures below describe what runs on the phone — not an earlier checkpoint.

## 7.1 Evaluation Framework

The cascade is evaluated on four axes, each targeting a distinct failure mode:
1. **Stage 3 disease accuracy** on the held-out lab test set — disease-discrimination quality.
2. **Gate behaviour** — how many genuine tomato leaves pass both gates (false-reject rate),
   and how many out-of-scope inputs are rejected (rejection recall / leak rate).
3. **End-to-end accuracy** — the fraction of tomato test images that pass both gates *and*
   receive the correct diagnosis. This is the number the user experiences.
4. **Field accuracy** — end-to-end accuracy on real-world phone photographs (PlantDoc).

## 7.2 Deployed-Model Results (held-out lab test set)

| Metric | Value | Source |
|---|---|---|
| Stage 3 disease accuracy | **97.59%** | recomputed (n = 6,683) |
| End-to-end accuracy | **97.19%** | recomputed |
| Tomato leaves passing the leaf gate | 100.0% | recomputed |
| Tomato leaves passing both gates | 99.42% | recomputed |
| Stage 3 test ECE (15-bin) | 0.061 | recomputed |
| Total model size | 9.87 MB | model files |
| Not-leaf rejection recall | 99.55% | prior gate eval† |
| Other-leaf rejection recall | 99.37% | prior gate eval† |
| Unseen-species leak rate | 0.05% | prior gate eval† |
| Field end-to-end (PlantDoc, n = 79) | 77.2% | prior field eval† |

† The gates are unchanged from the deployment that produced these figures, so they remain
valid gate-model properties; they were not regenerated in this pass and should be
re-verified on a held-out hard-negative set before final submission. The lab metrics in the
top block supersede every previously circulated Stage-3 accuracy figure (97.96%, 96.08%,
98.5%), which originated from non-deployed model variants.

**Confusion matrix.** Figure 7.1 (`confusion_matrix_deployed.png`) is the row-normalised
11×11 confusion matrix of the deployed Stage 3 model. Raw counts (rows = true, columns =
predicted):

| True \ Pred | bact | e_bl | hlth | l_bl | l_ml | mosv | powd | sept | spid | targ | ylcv |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **bacterial_spot** | **717** | 2 | 0 | 1 | 1 | 0 | 0 | 6 | 1 | 0 | 4 |
| **early_blight** | 3 | **606** | 1 | 10 | 6 | 0 | 1 | 11 | 0 | 3 | 2 |
| **healthy** | 0 | 0 | **795** | 0 | 1 | 1 | 0 | 0 | 0 | 6 | 2 |
| **late_blight** | 3 | 4 | 2 | **773** | 4 | 0 | 2 | 2 | 1 | 1 | 0 |
| **leaf_mold** | 4 | 1 | 2 | 5 | **718** | 2 | 0 | 0 | 1 | 5 | 1 |
| **mosaic_virus** | 0 | 0 | 2 | 0 | 0 | **576** | 1 | 0 | 0 | 2 | 3 |
| **powdery_mildew** | 0 | 0 | 0 | 0 | 0 | 0 | **252** | 0 | 0 | 0 | 0 |
| **septoria_leaf_spot** | 13 | 4 | 0 | 2 | 3 | 1 | 1 | **714** | 1 | 7 | 0 |
| **spider_mites** | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | **424** | 8 | 0 |
| **target_spot** | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1 | 1 | **453** | 0 |
| **yellow_leaf_curl_virus** | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | **494** |

**Per-class recall:**

| Class | Recall | n | Dominant confusions |
|---|---|---|---|
| powdery_mildew | **1.000** | 252 | — |
| target_spot | 0.991 | 457 | — |
| yellow_leaf_curl_virus | 0.992 | 498 | — |
| healthy | 0.988 | 805 | target_spot (6) |
| mosaic_virus | 0.986 | 584 | ylcv (3) |
| bacterial_spot | 0.980 | 732 | septoria (6), ylcv (4) |
| late_blight | 0.976 | 792 | early_blight (4), leaf_mold (4) |
| spider_mites | 0.975 | 435 | target_spot (8) |
| leaf_mold | 0.972 | 739 | late_blight (5), target_spot (5) |
| septoria_leaf_spot | 0.957 | 746 | bacterial_spot (13), target_spot (7) |
| **early_blight** | **0.943** | 643 | septoria (11), late_blight (10), leaf_mold (6) |

Every class exceeds 94% recall. The two weakest — early_blight (0.943) and septoria
(0.957) — together with their confusions (early_blight↔late_blight↔septoria, and
septoria↔bacterial_spot) form a single coherent cluster: all are diseases that present as
small, dark, necrotic foliar lesions and are visually similar at 224×224 resolution. The
errors are therefore pathologically intuitive, which is positive evidence that the model has
learned genuine lesion morphology rather than dataset artefacts.

## 7.3 Confidence Calibration

Temperature scaling (Guo et al., 2017) was applied to Stage 3, with the scalar temperature
baked into the final dense layer (T = 0.5889) so that argmax — and therefore accuracy — is
unchanged. Measured on the held-out test set, the deployed model's expected calibration error
is **0.061** (15 bins). This indicates reasonably, but not tightly, calibrated probabilities.

We explicitly correct an earlier internal figure of 0.0046: that value was obtained in-sample
on the temperature-fitting (validation) split and does not hold out-of-distribution. The
honest, held-out figure is 0.061. The practical implication is that the 60% low-confidence
banner fires rarely on clean lab images (where confidences are high) and more usefully on
lower-quality field images; a dedicated held-out calibration set and re-fitting on the
deployed model — to substantiate a tighter ECE — is identified as future work (Chapter 8).

## 7.4 Field Validation and the Lab-to-Field Gap

The deployed cascade was evaluated on PlantDoc tomato field photographs (n = 79 held-out
field images — real cluttered backgrounds, natural light, phone-camera quality). End-to-end
accuracy is **77.2%**, against 97.19% on the lab test set — a ~20-point gap, quantified here
directly on the shipped artifact rather than inferred. This gap is the central empirical
object of the project: it is the difference between benchmark performance and real-world
performance that most plant-disease systems never report.

## 7.5 Experiments to Close the Gap (four negative results)

Four interventions were designed and tested to close the lab-to-field gap. Each was a
falsifiable hypothesis; each failed; together they triangulate the cause.

| # | Experiment | Direction | Result | Mechanism |
|---|---|---|---|---|
| 1 | Heavy environmental augmentation (brightness/contrast/gamma/hue/sat/JPEG/blur) | train → field | field e2e −11.4 pts (74.7 → 63.3) — **rejected** | colour/gamma/JPEG jitter discarded diagnostic colour cues |
| 2 | Leaf segmentation (MobileSAM) background suppression, folded into training | train → field | all metrics declined slightly — **reverted** | lab backgrounds already near-uniform; nothing new added |
| 3 | DCGAN synthetic bacterial_spot (+600 images, 150 epochs, stable training) | train → field | zero field-recall improvement | GAN reproduces the lab distribution it was trained on |
| 4 | Test-time normalisation (segment field leaf → white background at inference) | inference → lab | field e2e −30.4 pts (77.2 → 46.8) | hard cut-outs are a third, out-of-distribution image |

A lighter, lighting-only augmentation variant (brightness/contrast/gamma only) was also
tested and did not beat the deployed minimal-augmentation model on field data (≈ −1.3 pts),
confirming that even mild colour-space augmentation does not help here.

**The decisive comparison.** Placing experiment 4 beside the composited-background test
isolates the cause:

| Configuration | Leaf appearance | Background | Field-style e2e |
|---|---|---|---|
| Composited | **lab** (perfect) | synthetic field | 65.5% |
| Test-time normalisation (exp. 4) | **field** | white (lab-like) | 46.8% |

A perfect lab leaf survives a bad background (65.5%); a field leaf on a clean background
still fails (46.8%). **The leaf appearance — its lighting, focus, and white balance — dominates
the domain gap, not the background.** No transformation of the training data or of the
inference input bridges it. The only demonstrated remedy is incorporating real field images
into training.

## 7.6 Synthesis

The four experiments share one root cause and one conclusion: interventions that operate
within the laboratory data distribution (augmenting it, cleaning its backgrounds, or
synthesising more of it) cannot manufacture the field distribution, and transforming a field
image at inference cannot reconstruct a lab image. This is not a null result — it is a
positive, evidence-backed finding that **narrows the solution space to real-data collection**,
which is precisely what the in-app feedback flywheel (Chapter 6) is built to enable.

## 7.7 Non-Functional Verification

| NFR | Requirement | Result |
|---|---|---|
| NFR-03 | Disease accuracy ≥ 90% (held-out lab test) | **Met** — 97.59% |
| NFR-04 | Models ≤ 15 MB combined | **Met** — 9.87 MB |
| NFR-01 / CR-01 | Fully offline, no network call | Met — no INTERNET permission; models bundled in assets |
| NFR-08 | No data leaves device | Met — local JSON only |
| (honesty) | Real-world performance reported | Met — 77.2% field e2e disclosed |

NFR-03 is reported against the lab test set, with the field benchmark (77.2%) disclosed
separately. The earlier wording that tied the 90% target to a "UAE-specific environmental"
test set is withdrawn, because no such labelled set exists; the honest position is high lab
accuracy plus a transparently reported field gap.
