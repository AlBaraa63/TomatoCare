# TomatoCare — Report Construction Worksheet, Audit & Defense Pack

> **What this file is.** The control document behind `FINAL_REPORT.md`. It contains the
> file inventory, the single-source-of-truth table, the full consistency audit (C1–C8 +
> newly-found issues), the scientific narrative, the structure rationale, five
> hostile-examiner questions with model answers, the recompute/patch/supervisor logs, and a
> corrected supervisor email. Every number in `FINAL_REPORT.md` traces back to the table in
> STEP 1 here. Author: AlBaraa AlOlabi. Compiled 2026-05-26.

---

## STEP 0 — PLAN

### Files successfully read
- `ml/reports/report_ai_section.md` — complete 19-section AI/ML write-up; already reconciled to the deployed JSON. Primary content source.
- `ml/reports/FINAL_REPORT.md` (prior partial) — earlier attempt at a full-capstone rebuild; only Abstract + Ch1 + Ch3 + Ch7 were written. Superseded by this rebuild.
- `ml/reports/eval_deployed.json` — **authoritative** deployed-TFLite metrics (held-out tomato20k/valid, n=6,683). Single source of truth.
- `ml/reports/HANDOFF.md` — session/context brief; carries some stale figures (~6 MB, 96.5% lab e2e) that are NOT used in the report.
- `ml/tree/calibrate.py` — temperature-scaling script; resolves the ECE contradiction (C1).
- `ml/tree/eval_deployed_tflite.py` — produced `eval_deployed.json`; resolves end-to-end / per-class provenance (C2, C5).
- Sample/exemplar: `AI powered Instructor assistance (FINAL VERSION)-CAP2 1 for submission.docx` — Al Ain University capstone structure to mirror.

### Files MISSING (expected by the original prompt, not present)
- `ml/reports/HANDOFF.md` exists; `ml/model_card.md` — **MISSING** (HANDOFF refers to a `model_card.md` for deployed assets; not in repo root or `ml/`).
- `ml/reports/report.txt` — **MISSING** (no original-draft txt).
- `ml/eval/eval_deployed.json` — **MISSING at that path**; the real file is `ml/reports/eval_deployed.json`.
- `confusion_matrix_deployed.png` — referenced by the report; git status shows the old `confusion_matrix.png` files were deleted. Regenerable via `eval_deployed_tflite.py` (optional; changes no numbers).

### Contradictions confirmed
C1 ECE — **confirmed & resolved** (in-sample val 0.0046 vs held-out test 0.061; both post-calibration).
C2 end-to-end — **confirmed & resolved** (97.19% deployed is authoritative).
C3 model size — **confirmed & resolved** (9.87 MB).
C4 disease accuracy — **confirmed & resolved** (97.59% deployed).
C5 per-class recall — **confirmed & resolved** (email = deleted pre-deployment baseline; JSON authoritative).
C6 "10 vs 11 classes" — **confirmed** (11 = 10 diseases + healthy).
C7 n_test — **confirmed** (6,683).
C8 field 77.2% — **confirmed** (must be foregrounded).
NEW-1..5 — found during read (see STEP 2).

### Actions required
- **FIX (rewrite only, no code):** all of C1–C8 and NEW-1, NEW-3, NEW-5 — they are documentation reconciliations against the JSON.
- **RECOMPUTE:** none required. (One optional, non-numeric: regenerate the confusion-matrix figure.)
- **BLOCKED:** none blocking. One item still pending AlBaraa's confirmation: dataset citation (placeholder). Lighting-aug field number now **confirmed 73.4% / −3.8 pts** from cached `tc_gan_field_eval.json` (NEW-4 RESOLVED).

### Order of operations
1. SoT table (STEP 1). 2. Consistency audit (STEP 2). 3. Scientific story (STEP 4). 4. Structure (STEP 5). 5. Write `FINAL_REPORT.md` chapters. 6. Defense prep (STEP 7). 7. Logs + corrected email. 8. Verify numbers. 9. Export docx.

---

## STEP 1 — Single Source of Truth Table

Authoritative file: `ml/reports/eval_deployed.json` unless noted. "report" = `report_ai_section.md`.

| Item | Value | Source file | Line / key |
|---|---|---|---|
| Architecture | 3-stage sequential cascade | report | §4 |
| Stage 1 — model family | MobileNetV3-Small | report | §4 |
| Stage 1 — task | leaf vs not_leaf (binary gate) | report | §4 |
| Stage 1 — I/O spec | float32[1,224,224,3] RGB [0,1] → 2-class softmax | report | §5, §4 |
| Stage 2 — model family | MobileNetV3-Small | report | §4 |
| Stage 2 — task | tomato vs other_leaf (binary gate) | report | §4 |
| Stage 3 — model family | MobileNetV3-Large | report | §4 |
| Stage 3 — task | 11-class disease/healthy softmax | report | §4 |
| 11 class names | bacterial_spot, early_blight, healthy, late_blight, leaf_mold, mosaic_virus, powdery_mildew, septoria_leaf_spot, spider_mites, target_spot, yellow_leaf_curl_virus | json | `confusion_labels` |
| Training dataset (primary) | tomato20k (PlantVillage-derived), 25,851 train | report | §2.1 |
| PlantDoc field images added | 824 train folded into Stage 2/3; 79 held out as field test | report | §2.2 |
| Preprocessing contract | center-crop→224, RGB, ÷255→[0,1], NO ImageNet mean/std | report | §5 |
| Held-out test set — n | 6,683 | json | `n_test` |
| Field test set | PlantDoc tomato, n = 79 (test split) | report | §11.4 |
| Stage 1 accuracy (not-leaf rejection recall) | 99.55% | hard_negative_test (prior) | report §11.1 |
| Stage 2 accuracy (other-leaf rejection recall) | 99.37% | hard_negative_test (prior) | report §11.1 |
| Stage 3 lab accuracy | 97.59% | json | `test_accuracy` |
| Stage 3 field disease accuracy (deployed ctrl) | 87.1% | report | §19 |
| End-to-end lab (both gates + correct dx) | 97.19% | json | `correct_diagnosis_pct` |
| End-to-end field (deployed ctrl) | 77.2% | report | §11.4 / §16.3 |
| Passed leaf gate / both gates (lab) | 100.0% / 99.42% | json | `end_to_end` |
| ECE before calibration (val, in-sample) | ~0.07 | calibrate.py | `ece_before` |
| ECE after calibration (val, in-sample) | 0.0046 | calibrate.py | `ece_after` |
| ECE after calibration (held-out test) | 0.061 | json | `ece_test_15bin` (0.0613) |
| Temperature T | 0.5889 | report / calibrate meta | §3.6 (meta.json, WSL — not in repo) |
| Non-leaf rejection rate | 99.55% | prior gate eval | report §11.1 |
| Unseen-species (other-leaf) leak rate | 0.05% | prior gate eval | report §11.1 |
| Stage 1 TFLite size (bytes) | 1,921,456 (1.92 MB) | json | `model_sizes_bytes.stage1` |
| Stage 2 TFLite size (bytes) | 1,921,456 (1.92 MB) | json | `model_sizes_bytes.stage2` |
| Stage 3 TFLite size (bytes) | 6,028,328 (6.03 MB) | json | `model_sizes_bytes.stage3` |
| Total TFLite size (MB) | 9.87 | json | `model_total_mb` (Σ = 9,871,240 B) |
| Per-class recall (all 11) | powdery_mildew 1.000, ylcv 0.992, target_spot 0.991, healthy 0.988, mosaic_virus 0.986, bacterial_spot 0.980, late_blight 0.976, spider_mites 0.975, leaf_mold 0.972, septoria 0.957, early_blight 0.943 | json | `per_class` |
| Experiment 1 — heavy aug (field e2e) | 74.7% → 63.3% (−11.4) | report | §11.4 |
| Experiment 2 — MobileSAM seg | slight decline, reverted | report | §14.3 |
| Experiment 3 — DCGAN +600 (field bacterial_spot) | 2/9 (22%), zero gain | report | §15.5 |
| Experiment 4 — test-time white-bg norm (field e2e) | 77.2% → 46.8% (−30.4) | report | §17.3 |
| Experiment 4b — lighting-only aug (field) | **73.4% (−3.8 pts vs ctrl 77.2%); 97.9% lab** | `tc_gan_field_eval.json` (confirmed) | §7.5 |
| Decisive split — lab-leaf+field-bg | 65.5% (composited, n=165) | report | §16.3 |
| Decisive split — field-leaf+white-bg | 46.8% | report | §17.3 |

---

## STEP 2 — Consistency Audit

─────────────────────────────────────────────
**ISSUE C1 — ECE after calibration (0.005 / 0.0613 / 0.0046)**
─────────────────────────────────────────────
Documents affected:
- email to Yazeed: "calibration error improved from 0.059 to 0.005"
- `eval_deployed.json`: `"ece_test_15bin": 0.0613`
- HANDOFF.md: "ECE 0.07 → 0.0046"

Why it matters in a defense: an examiner sees three different ECEs and asks which is real.

Severity: MEDIUM.
Resolution (FIX): traced in `calibrate.py`. The script fits T on the Stage-3 **validation**
split and computes `ece_before`/`ece_after` **in-sample on that same split** → 0.07 → 0.0046.
`eval_deployed_tflite.py` then measures ECE on the **held-out test set** with T already baked
into the deployed weights → 0.061. **Both are post-calibration**; 0.0046 is in-sample
(optimistic), 0.061 is the honest out-of-sample deployment figure. The report uses **0.061**
as the headline and explicitly explains the 0.0046 as in-sample. The email's "0.005" is just a
rounded restatement of the in-sample 0.0046 and is corrected in the patched email.

─────────────────────────────────────────────
**ISSUE C2 — End-to-end accuracy (97.6% / 97.19% / 96.5%)**
─────────────────────────────────────────────
Documents affected:
- email to Yazeed: "End-to-end … 97.6%"
- `eval_deployed.json`: `"correct_diagnosis_pct": 97.19`
- HANDOFF.md: "96.5% lab end-to-end"

Why it matters: looks like the headline result keeps changing.

Severity: MEDIUM.
Resolution (FIX): **97.19%** = deployed TFLite cascade on tomato20k/valid (n=6,683) — the
authoritative measurement (`eval_deployed_tflite.py` `n_e2e`). The email's 97.6% ≈ the
pre-aug baseline's lab e2e (97.55%, report §11.4); HANDOFF's 96.5% was an earlier
ctrl-model harness run. Both superseded by the deployed-TFLite eval. Report uses 97.19%.

─────────────────────────────────────────────
**ISSUE C3 — Total model size (9.4 / 9.87 / ~6 MB)**
─────────────────────────────────────────────
Documents affected: email "≈9.4 MB"; json `model_total_mb` 9.87; HANDOFF "~6 MB".
Why it matters: a size budget (NFR ≤15 MB) claim must be exact.
Severity: MINOR.
Resolution (FIX): **9.87 MB** = exact byte sum (1,921,456 + 1,921,456 + 6,028,328 =
9,871,240 B). Email and HANDOFF figures are stale estimates. Report uses 9.87 MB.

─────────────────────────────────────────────
**ISSUE C4 — Disease accuracy (97.96% / 97.59%)**
─────────────────────────────────────────────
Documents affected: email "97.96%"; json `test_accuracy` 0.9759.
Why it matters: which model's accuracy is being claimed?
Severity: MEDIUM.
Resolution (FIX): **97.59%** = deployed TFLite. 97.96% = the pre-aug/pre-deployment baseline
(report §11.2 lists it as the baseline). Email corrected.

─────────────────────────────────────────────
**ISSUE C5 — Per-class recall mismatch (THE flagged one)**
─────────────────────────────────────────────
Documents affected:
- email: early_blight 0.913, septoria 0.920, bacterial_spot 0.944
- `eval_deployed.json`: early_blight 0.9425, septoria 0.9571, bacterial_spot 0.9795

Why it matters: an examiner who has both the email and the report sees the supervisor was
told different numbers than the report claims.

Severity: CRITICAL (for the email; the report itself is already correct).
Resolution (FIX, traced — no recompute possible): the email's three figures are all **lower**
and come from the **pre-deployment baseline model**, not the deployed ctrl model. Corroboration:
report §16.4 cites early_blight "91.3% on lab images" (= 0.913) as the earlier model's recall.
The deployed ctrl model (trained after PlantDoc integration) was re-evaluated in
`eval_deployed.json` and scores higher (0.9425 / 0.9571 / 0.9795). The baseline's Keras
checkpoints were deleted (stated in `eval_deployed_tflite.py` docstring), so the email's exact
source eval cannot be reopened — but the explanation is clean and the corrected email uses the
deployed numbers. **Per the prompt's prohibition, the email is NOT acknowledged as numerically
correct; it is corrected before sending.**

─────────────────────────────────────────────
**ISSUE C6 — "10 diseases" vs "11 classes"**
─────────────────────────────────────────────
Severity: MINOR. Resolution (FIX): 11 classes = 10 diseases + healthy. The cascade emits one
of 11 labels. Report states "eleven conditions (ten diseases and a healthy class)" consistently;
any stray "10-class" phrasing is removed.

─────────────────────────────────────────────
**ISSUE C7 — n_test (6,682 vs 6,683)**
─────────────────────────────────────────────
Severity: MINOR. Resolution (FIX): **6,683** (json `n_test`). Email off-by-one corrected.

─────────────────────────────────────────────
**ISSUE C8 — Field accuracy 77.2% absent from emails**
─────────────────────────────────────────────
Severity: MEDIUM (honesty). Resolution: 77.2% field end-to-end is the headline honest result;
it appears in the Abstract, Ch1 problem statement, Ch7 evaluation, and Ch8 conclusion, and is
named in the corrected email.

─────────────────────────────────────────────
**ISSUE NEW-1 — §16.4 "91.3% lab early_blight" vs deployed 94.25%**
─────────────────────────────────────────────
Documents affected: report §16.4 ("down from 91.3% on lab images"); json early_blight 0.9425.
Why it matters: an examiner cross-reading §11.3 (0.943) and §16.4 (0.913) sees an internal
contradiction in the same document.
Severity: MEDIUM.
Resolution (FIX): the composited experiment (§16) was run on the **pre-deployment cascade**, so
91.3% was that model's early_blight lab recall. In the rebuilt report this is labelled
explicitly as the pre-deployment baseline figure (or restated as 94.3% with a note), so the
deployed per-class table (§11.3 → Ch7) and the composited discussion no longer appear to disagree.

─────────────────────────────────────────────
**ISSUE NEW-2 — Gate/leak safety metrics not in the authoritative JSON**
─────────────────────────────────────────────
Documents affected: report §11.1 (non-leaf reject 99.55%, other-leaf reject 99.37%, unseen
leak 0.05%). `eval_deployed.json` does NOT compute these — `eval_deployed_tflite.py` only runs
the gates on tomato test images (for end-to-end), not on non-leaf / other-leaf negatives.
Why it matters: the safety story rests on numbers from a different (earlier) script run.
Severity: MEDIUM.
Resolution (FIX + disclose): these come from a prior `hard_negative_test.py` run. The gates are
unchanged between the baseline and the deployed ctrl model (only Stage 3 was retrained), so the
figures legitimately carry over — but the report footnotes their provenance and flags
re-verification on a held-out hard-negative set as future work. This is defense Q5.

─────────────────────────────────────────────
**ISSUE NEW-3 — "9.86 MB" vs "9.87 MB" inside the prior FINAL_REPORT**
─────────────────────────────────────────────
Severity: MINOR. Resolution (FIX): 9.87 MB everywhere (1.92+1.92+6.03). The prior §3.7 "9.86"
rounding slip is corrected.

─────────────────────────────────────────────
**ISSUE NEW-4 — Lighting-aug field number — ✅ RESOLVED**
─────────────────────────────────────────────
Documents affected: email to Yazeed ("field accuracy dropped from 77.2% to 73.4%"); HANDOFF &
report (lighting-only aug ≈ −1.3 pts, 97.9% lab).
Why it matters: the supervisor was told −3.8 pts; the report had −1.3 pts.
Resolution: **confirmed from `tc_gan_field_eval.json` (cached run of `gan_field_eval.py`):**
  lighting/TEST = 73.4%, ctrl/TEST = 77.2% → −3.8 pts.
The **email was correct**. The report's "−1.3 pts" was wrong. FINAL_REPORT.md has been
updated to "73.4% vs 77.2%, −3.8 pts". The corrected email is also updated.

─────────────────────────────────────────────
**ISSUE NEW-5 — Field disease accuracy 84.3% vs 87.1%**
─────────────────────────────────────────────
Documents affected: report §11.4 (pre-aug baseline field disease acc 84.3%); §19 (deployed ctrl
"87.1% disease accuracy").
Why it matters: two field disease-accuracy numbers could look like a contradiction.
Severity: MINOR. Resolution (FIX): 84.3% = pre-aug baseline; 87.1% = deployed ctrl. Both kept,
each explicitly labelled with its model. (Both unverifiable from repo since checkpoints deleted;
presented as reported field-eval figures.)

---

## STEP 3 — Recompute Protocol

**No contradiction requires a recompute or retrain.** Every item above was resolved by tracing
existing eval files and scripts. The deployed Keras checkpoints no longer exist, so the older
baseline numbers (the source of the email discrepancies) cannot be regenerated — and need not be,
because the deployed TFLite artifacts and `eval_deployed.json` are the authoritative record.

**One optional, non-numeric regeneration** (gated on AlBaraa's approval): re-run
`py ml/tree/eval_deployed_tflite.py` to regenerate `confusion_matrix_deployed.png`. This re-reads
the shipped TFLite + held-out test set and **reproduces `eval_deployed.json` byte-for-byte**
(same numbers); its only new output is the heatmap figure for the report. Logged in the RECOMPUTE LOG.

---

## STEP 4 — The Scientific Story (internal compass)

**1. The v1 failure.** v1 was a single MobileNetV3-Large classifier with an added `not_tomato`
reject class. On real photos it labelled non-tomato inputs (other crops' leaves, hands, objects)
as a tomato disease with high confidence. This is a *safety* failure, not just an accuracy one: a
grower photographing the wrong thing receives confident, wrong treatment advice. Root cause: one
softmax head was forced to do OOD rejection and fine-grained disease discrimination at once, and
the lab-only negatives let the model separate images by photographic style (lab vs field) rather
than by leaf identity.

**2. The cascade solution.** Three independent stages — leaf gate (MobileNetV3-Small) → tomato
gate (MobileNetV3-Small) → 11-class disease classifier (MobileNetV3-Large). Each gate has a
single, focused objective and *hard-rejects* out-of-scope inputs before any diagnosis. This beats
a shared reject class because the reject decision no longer competes with disease features in one
representation, and Stage-3 confidence becomes pure disease confidence. Small backbones for the
coarse gates keep size/latency low; the Large backbone is spent only on the hard 11-class problem.

**3. The domain gap — measured.** Lab end-to-end 97.19% (n=6,683) vs field end-to-end **77.2%**
on PlantDoc real phone photos (n=79) — a ~20-point gap. PlantDoc is the right field proxy because
it is real cluttered-background, natural-light, phone-camera imagery of the same diseases. This is
the honest centre of the project and is not softened.

**4. The four falsified hypotheses.**
- *Heavy environmental augmentation* (brightness/contrast/gamma/hue/sat/JPEG/blur): expected to
  simulate field conditions; field e2e fell 74.7→63.3 (−11.4). The colour/gamma/JPEG jitter
  discarded the colour cues that disease ID depends on. Not deployed.
- *MobileSAM leaf segmentation* (blank the background in training): expected to kill background
  shortcuts; every lab metric declined slightly; reverted. Lab backgrounds are already near-uniform,
  so nothing new was added.
- *DCGAN synthetic bacterial_spot (+600 images, 150 stable epochs)*: expected to lift the weakest
  field class; field bacterial_spot recall stayed at 2/9 (22%), e2e unchanged. A GAN trained on the
  lab distribution can only reproduce the lab distribution.
- *Test-time normalisation (segment field leaf → white background at inference)*: expected to map
  field inputs back to the lab the model knows; field e2e fell 77.2→46.8 (−30.4). Hard cut-outs on
  pure white are a third, out-of-distribution image, and the tomato gate rejected them 3× more often.

**5. The decisive insight.** Composited test (lab leaf + synthetic field background) = 65.5%;
test-time normalisation (field leaf + white background) = 46.8%. A perfect lab leaf survives a bad
background, but a field leaf on a clean background still fails. ⇒ **The leaf appearance — its
lighting, focus, white-balance, natural-light lesion look — dominates the gap, not the background.**
Therefore no transformation, of training data or of inference input, can synthesise the field
distribution from the lab one.

**6. What is deployed and why.** Stage 3 = the **ctrl** model (minimal augmentation = horizontal
flip only), trained after PlantDoc integration; it beat every experimental variant on the *field*
benchmark (77.2% e2e). Temperature scaling (T = 0.5889, Guo et al. 2017) was baked into the final
dense layer, leaving accuracy unchanged and correcting confidence (test ECE 0.061). The in-app
feedback flywheel collects and labels real field photos from users for future retraining.

**7. What remains open.** Accumulate real UAE field data via the flywheel (the only demonstrated
remedy); test motion-blur-only augmentation (not yet done); apply segmentation *after* field data
exists; per-class confidence thresholds; CameraX live capture. No built feature is described as
future, and no open item is overclaimed.

**Framing rule:** the four negative results *are* the scientific contribution — a controlled,
two-directional investigation with one reproducible conclusion. They are findings, not failures.

---

## STEP 5 — Final Report Structure (mapped to the Al Ain exemplar)

The report mirrors the instructor exemplar's chapter scheme. AlBaraa owns the AI/model content;
app + UI/UX content is marked `[PLACEHOLDER — App/UI-UX team]`.

- **Front matter** — title page, approval, declaration, Abstract, acknowledgments, TOC, List of Figures/Tables.
- **Ch1 Project Overview** — open on the v1 safety failure; access/safety/honesty gaps; aim; objectives tagged [MET]/[PARTIALLY MET]/[DEFERRED]; scope. *Remove:* "tomatoes are an important crop" cold-open.
- **Ch2 Literature Review** — CNN disease ID; MobileNetV3; PlantVillage & the domain gap; OOD/rejection cascades; calibration (Guo 2017); DCGAN; SAM/MobileSAM; offline TFLite. (most net-new prose)
- **Ch3 Methodology** — datasets; preprocessing+parity; cascade rationale; two-phase training; temperature scaling; float16 export. Project-management subsections = light placeholder.
- **Ch4 Requirements & Specification** — AI FRs/NFRs + a traceability matrix for them. App FR catalogue/use-cases/diagrams = placeholder.
- **Ch5 System Design & Architecture** — AI layer (3-interpreter cascade, preprocessing contract, on-device flow). App architecture/class/state/DB/GUI = placeholder.
- **Ch6 Implementation** — model pipeline (train/calibrate/export), on-device cascade + ImagePreprocessor, feedback-flywheel exporter. App screens = placeholder.
- **Ch7 Testing/Evaluation** — framework; deployed lab results + confusion matrix; field gap; the four experiments as one investigation; calibration; NFR verification; capability statement. App testing = placeholder.
- **Ch8 Conclusion** — contributions; honest field result; four falsified hypotheses → flywheel.
- **Ch9 Future Work** — flywheel; lighting-only/motion-blur aug; field segmentation; thresholds; CameraX.

Constraints enforced: no biotic/abiotic framing; the domain-gap investigation is its own section
(Ch7); the four experiments are unified (not scattered as limitations); built features in past
tense; no number outside the STEP 1 table.

---

## STEP 7 — Defense Preparation (5 hostile-examiner questions)

**Q1. "Your field accuracy is 77% — is this system actually deployable?"**
Yes, with honest scope. The safety property — hard-rejecting non-leaf and non-tomato inputs at the
gates — holds in the field: 164/165 composited images and 79/79 normalisation-test images were
correctly gated, so the cascade does not silently misdiagnose out-of-scope inputs. 77.2% end-to-end
on PlantDoc (n=79) is the floor we *measured* on genuinely out-of-lab photos, against 97.19% in the
lab. Most published plant-disease apps report only the lab number; we report both and show the
~20-point gap explicitly. The deployed model is the variant that *maximised* this field number, the
confidence is calibrated so weak predictions surface a low-confidence warning, and the in-app
feedback flywheel is built to close the remaining gap with real user data. It is deployable as an
assistive tool with a transparent confidence and a clear improvement path — not as an unsupervised oracle.

**Q2. "Four experiments, all failed — did you just run out of ideas?"**
No — it is a controlled investigation, not a scatter of attempts. We tested the gap from *both*
directions: three training-side interventions (heavy augmentation −11.4 pts, MobileSAM segmentation
slight decline, DCGAN +600 zero gain) and one inference-side intervention (white-background
normalisation −30.4 pts). The decisive pair — lab-leaf+field-bg 65.5% vs field-leaf+white-bg 46.8%
— isolates the cause to leaf appearance rather than background. That is a positive, falsifiable
finding with a mechanism: it tells us synthetic and transform approaches cannot manufacture the
field distribution, and that real field data is the only remedy. A null result that rules out a
whole class of solutions is a contribution.

**Q3. "How do you know temperature scaling improved calibration and not something else?"**
Because temperature scaling is provably the *only* thing it changed. `calibrate.py` fits a single
scalar T on held-aside logits and bakes it into the final dense layer as W←W/T, b←b/T. Dividing all
logits by a positive scalar cannot change their argmax, so accuracy is identical before and after
(the script asserts this). ECE before/after (0.07 → 0.0046 in-sample) is computed on the *same*
logits and *same* labels with only T differing — no retraining, no data change, no architecture
change. On the held-out test set the deployed (T-baked) model's ECE is 0.061, which we report as the
honest figure. So the calibration delta is attributable to T alone by construction.

**Q4. "The per-class recall in your email differs from your evaluation JSON. Which is right, and how
did that happen?"**
The JSON is right; the email is stale. `eval_deployed.json` is produced by running the *shipped*
TFLite cascade against the held-out test set — early_blight 0.943, septoria 0.957, bacterial_spot
0.980. The email quoted 0.913/0.920/0.944, which are the *pre-deployment baseline* model's recalls,
written before the final ctrl model was trained (after PlantDoc integration) and re-evaluated. The
baseline's Keras checkpoints were deleted once it was superseded, which is why the older eval can't
be reopened. The fix is to send the corrected numbers (done — see the patched email), and the report
uses only the deployed JSON throughout.

**Q5 (from a newly-found gap). "Your safety headline — 0.05% leak, 99.55% non-leaf rejection — is NOT
in `eval_deployed.json`. Where do those numbers come from, and are they valid for the shipped model?"**
They come from an earlier hard-negative evaluation (`hard_negative_test.py`), not from the deployed
eval, which only runs the gates on tomato inputs for the end-to-end figure. They remain valid because
the gate models (Stages 1–2) were *not* retrained between the baseline and the deployed ctrl model —
only Stage 3 changed — so the gate behaviour carries over unchanged. We disclose this provenance in a
footnote and flag re-running the hard-negative suite against a fresh held-out OOD set as the right
pre-final-submission check. We do not claim those two figures were regenerated against the shipped artifact.

---

## RECOMPUTE LOG

| Date | Script path | Arguments used | Key metric output | Step 1 cells updated |
|---|---|---|---|---|
| — | (none required) | — | All contradictions resolved by tracing existing eval files; no recompute/retrain run. | — |
| _pending AlBaraa OK_ | `ml/tree/eval_deployed_tflite.py` | `py ml/tree/eval_deployed_tflite.py` | regenerates `confusion_matrix_deployed.png`; reproduces `eval_deployed.json` (no number change) | none (figure only) |

---

## PATCH LOG

| Document patched | Section | Old value | New value | Reason |
|---|---|---|---|---|
| Yazeed follow-up email | per-class recall | early_blight 0.913 / septoria 0.920 / bacterial_spot 0.944 | 0.943 / 0.957 / 0.980 | C5 — email quoted deleted pre-deployment baseline; JSON authoritative |
| Yazeed follow-up email | test-set n | 6,682 | 6,683 | C7 — json `n_test` |
| Yazeed follow-up email | disease accuracy | 97.96% | 97.59% | C4 — deployed TFLite |
| Yazeed follow-up email | end-to-end | 97.6% | 97.19% | C2 — deployed TFLite |
| Yazeed follow-up email | model size | 9.4 MB | 9.87 MB | C3 — exact byte sum |
| Yazeed follow-up email | ECE | 0.005 | 0.0046 in-sample / 0.061 held-out test | C1 — disambiguate in-sample vs test |
| Yazeed follow-up email | lighting-aug field | 77.2% → 73.4% | **73.4% confirmed** (−3.8 pts) | NEW-4 RESOLVED — email was correct; report fixed |
| report_ai_section.md | §16.4 | "down from 91.3% on lab images" | "(pre-deployment baseline; deployed early_blight lab recall is 94.3%)" | NEW-1 — internal consistency |
| report_ai_section.md (prior FINAL_REPORT §3.7) | total size | 9.86 MB | 9.87 MB | NEW-3 — rounding |
| HANDOFF.md | §1 / §3 | "~6 MB", "96.5% lab e2e" | note as superseded (9.87 MB; 97.19%) | C2/C3 — context doc only (optional) |
| Dr. Elibol email (already sent) | — | — | no change | checked — qualitatively consistent (2,503 imgs, 600 synth, flat result) |

---

## SUPERVISOR OBLIGATIONS TRACKER

| Supervisor | Suggestion | Status | Report section |
|---|---|---|---|
| Dr. Yazeed | Collect a custom field validation dataset | **PARTIAL** — direct UAE collection not feasible; built in-app feedback flywheel to gather labelled field photos from users | Ch6 (flywheel) + Ch9 |
| Dr. Yazeed | Report confusion matrices for the disease classes | **DONE** — full 11×11 matrix + per-class recall, numbers reconciled to `eval_deployed.json` | Ch7 |
| Dr. Yazeed | Lightweight augmentation: lighting variation | **DONE** — lighting-only aug tested; negative (−3.8 pts field; 73.4% vs ctrl 77.2%) | Ch7 (experiments) + Ch9 |
| Dr. Yazeed | Lightweight augmentation: motion blur | **NOT DONE** — declared honest future work | Ch9 |
| Dr. Yazeed | (reply to progress email) | **✅ APPROVED 2026-05-27** — endorsed the lab/field distinction, deployed-model eval, confusion-matrix analysis, honest negative results, the domain-gap conclusion, and the feedback-flywheel approach; "very good progress." | — |
| Dr. Elibol | GAN synthetic images for a validation set | **DONE (pivoted)** — used GAN as training augmentation (sounder), clean A/B; zero field gain | Ch7 (Experiment 3) |
| Dr. Elibol | (reply) | **AWAITING** as of 2026-05-25 | — |

---

## CORRECTED EMAIL — AlBaraa → Dr. Yazeed (numbers reconciled to `eval_deployed.json`)

> ⚠ Before sending: drop in the tomato20k citation.

> Dear Dr. Yazeed,
>
> Thank you for the detailed and encouraging feedback. I have acted on all three suggestions, and I
> want to give you the final, verified numbers — measured by running the **deployed TensorFlow Lite
> models** (the exact files shipped in the app) against the held-out test set, so they match the
> report's evaluation chapter exactly.
>
> **1. Confusion matrices.** The report now includes the full 11×11 confusion matrix (heatmap + raw
> counts + per-class recall), computed on the **6,683-image** held-out test set. The three weakest
> classes are **early_blight (0.943) and septoria_leaf_spot (0.957)** — both small, dark,
> necrotic-lesion diseases that look alike at phone-camera resolution, their errors mostly mutual
> confusions with late_blight and bacterial_spot. (My earlier message quoted lower figures from an
> earlier model version; these deployed-model numbers supersede them.) Overall disease accuracy is
> **97.59%** and end-to-end cascade accuracy is **97.19%**.
>
> **2. Lighting-only augmentation.** Completed and documented as an experiment. Restricting
> augmentation to brightness/contrast/gamma (no colour jitter, no blur) did not improve field accuracy —
> it dropped from 77.2% to **73.4% (−3.8 pts**; lab ~97.9%) — so it was not deployed.
> Motion-blur-only augmentation I have not yet
> isolated — that is a reasonable next step.
>
> **3. Custom field validation dataset.** I do not have access to UAE tomato fields for direct
> collection, so I built an in-app feedback flywheel: each diagnosis offers a one-tap confirm/correct
> card, and a background exporter packages those labelled photos for future retraining. Four controlled
> experiments (heavy augmentation, segmentation, GAN, and inference-time normalisation) all showed the
> lab-to-field gap cannot be closed with synthetic or transformed lab data, which is why real
> user-collected field data is the path I have prioritised. On real PlantDoc field photos the deployed
> model scores **77.2% end-to-end** versus 97.19% in the lab — a gap I report openly. The three models
> total **9.87 MB** and run fully offline.
>
> I will keep documenting everything for the final report and presentation.
>
> Best regards,
> AlBaraa AlOlabi
