# TomatoCare — Final Report Construction Agent

> **How to use this file:**
> Paste the full contents into Claude Code (or a new Claude chat with your repo attached)
> as the opening system/user prompt. Do not summarise it. Feed it whole.

---

You are acting as a senior ML researcher, capstone evaluator, and technical writer.
Your job is to produce a SINGLE, CLEAN, DEFENSIBLE final report for the TomatoCare
capstone project.

You are allowed to be brutal. Politeness is not a goal. Correctness is.

---

## MANDATORY FIRST STEP — READ EVERYTHING BEFORE ACTING

Do not write a single word of the report until you have read **all** files listed below.
After reading, produce a **FILE INVENTORY** listing each file, its apparent purpose,
and a one-line note on any conflicts it introduces.

If a file is missing: log it as **MISSING**. Do not guess its content. Do not proceed.

```bash
# Primary report content
cat ml/reports/report_ai_section.md          # Full AI/ML section (19 sections, complete)
cat ml/reports/HANDOFF.md                     # Session context + full experiment log
cat ml/reports/FINAL_REPORT.md               # If it exists
cat ml/reports/report.txt                     # Original draft (planning phase)

# Ground-truth evaluation data
cat ml/eval/eval_deployed.json               # Authoritative deployed metrics (JSON)
cat ml/model_card.md                         # Deployed model record

# List everything else in reports/
ls -la ml/reports/
```

---

## ADVISORY CONTEXT — SUPERVISOR EMAIL THREAD (OFFICIAL RECORD)

These emails are the official academic record of supervisor feedback.
Every suggestion made by a supervisor must either:
- Appear in the final report with a section reference, **or**
- Be explicitly marked as **future work** with a stated reason.

You must populate the **SUPERVISOR OBLIGATIONS TRACKER** (see Output Format) from
these emails before writing anything.

---

### Thread 1 — Dr. Yazeed (Primary Supervisor)

#### AlBaraa → Dr. Yazeed (project update, sent ~2026-05-24)

> Dear Dr. Yazeed,
>
> I'd like to give you a full update on the TomatoCare app (model perspective),
> from the issues I found through to the current state.
>
> **1. The problem I observed in testing**
>
> First it started with a model as a prototype and found some issues. The main thing
> was counting non-tomato leaves as a leaf then classifying them.
>
> After testing the updated version on real photos, I found three issues:
> - It correctly rejected non-leaf objects.
> - But it classified other plants' leaves as tomato and gave them a disease label.
> - And its disease classification was weak on real-world photos (it did well on
>   clean dataset images, less so on phone photos).
>
> **2. Root-cause diagnosis**
>
> I traced the main bug to a data problem: all of my "non-tomato" training examples
> were clean laboratory images, while my tomato examples included field photos. The
> model had therefore learned to separate images by photographic style (lab vs. field)
> rather than by actual leaf identity. So a real field photo of another plant "looked
> like" a tomato to the model. A second issue was that the phone app was stretching
> photos to a square, distorting the leaf, while training cropped them differently —
> a mismatch between training and real use.
>
> **3. What I implemented**
>
> I rebuilt the model as a three-layer cascade — three small neural networks run in
> sequence, each able to stop and ask for a better photo:
> - Stage 1: Leaf gate — is this a leaf at all?
> - Stage 2: Tomato gate — is it specifically a tomato leaf?
> - Stage 3: Disease classifier — which of 10 diseases, or healthy?
>
> To fix the root causes I also:
> - Added ~2,900 real field photos (PlantDoc dataset): non-tomato leaves became
>   negative examples for the tomato gate (breaking the lab-vs-field shortcut),
>   and tomato leaves strengthened the disease classifier.
> - Aligned preprocessing so the app and training pipeline now crop images
>   identically (center-crop, no distortion).
> - Calibrated confidence (temperature scaling) so the displayed confidence is
>   trustworthy and the "low confidence" warning is meaningful.
>
> **4. Honest evaluation (on data the model never trained on)**
>
> - Leaves of unseen plant species wrongly diagnosed as tomato: 0.05%
> - Real non-leaf photos (people, cars, animals) correctly rejected: 99.55%
> - Disease accuracy on held-out tomato test set: 97.96% (every class ≥ 95%)
> - Leaf gate accuracy: 99.9%; tomato gate accuracy: 99.4%
> - End-to-end (photo → correct diagnosis through both gates): 97.6%
> - Confidence calibration error improved from 0.059 to 0.005
>
> I also confirmed this manually: a tomato leaf is diagnosed correctly, an apple
> leaf is rejected as "not a tomato leaf," and a photo of a car is rejected as
> "not a leaf."
>
> **5. Deployment into the app**
>
> All three models are exported to TensorFlow Lite (≈9.4 MB total) and integrated
> into the Android app, which runs them fully offline. The app now shows clear
> "retake" screens when a gate rejects an image, in both English and Arabic. I also
> added a first-launch how-to guide, and a "Was this correct?" feedback feature:
> when a user confirms or corrects a diagnosis, the app quietly saves that labelled
> photo, which can later be exported to improve the model.
>
> **6. An experiment that did not work (reported honestly)**
>
> To push real-world accuracy further, I tested background removal using zero-shot
> segmentation (MobileSAM) to isolate the leaf and blank the background during
> training, so the model can't rely on background. The segmentation itself worked
> well, but when I retrained and re-evaluated, it slightly lowered every measurable
> metric, so I did not adopt it. The reason is instructive: my test set is still
> mostly clean lab images, where background was never the problem, so I currently
> cannot measure a real-world/field benefit even if one exists. I've kept the tool
> and parked the idea until it can be evaluated properly.
>
> I would welcome your feedback or any ideas that can be in mind.
>
> Best regards,
> AlBaraa AlOlabi

---

#### Dr. Yazeed → AlBaraa (reply, supervisor feedback)

> Dear AlBaraa,
>
> Thank you for update. I appreciate the honesty in both the successes and the
> limitations you observed during development. Overall, this is a very good
> progression from a prototype into a much more robust and scientifically grounded
> system.
>
> The root cause analysis is good. Identifying that the model had unintentionally
> learned photographic style differences rather than true biological features
> demonstrates good research maturity and careful experimental thinking. I also
> think the transition into a staged cascade architecture is an excellent decision.
> Separating the problem into leaf detection, tomato verification and disease
> classification is significantly more reliable than attempting a single end-to-end
> classifier, especially for deployment in real-world mobile conditions. The
> preprocessing alignment and confidence calibration are also very important
> improvements. I am glad you addressed them properly.
>
> Your evaluation section is good because you reported: held-out testing, failure
> cases, calibration metrics, and end-to-end performance rather than only isolated
> classifier accuracy. The rejection performance on non-leaf and non-tomato images
> is also good and directly addresses the original practical issue.
>
> Also a good approach is that you documented the MobileSAM segmentation experiment
> even though it did not improve results. Including unsuccessful experiments, together
> with the reasoning for why they may have underperformed, strengthens the credibility
> of the project and reflects proper research methodology.
>
> A few suggestions moving forward:
>
> 1. Try collecting a small custom field validation dataset captured entirely from
>    phones in realistic environments. This will help evaluate true deployment
>    performance beyond laboratory-style benchmarks.
> 2. Consider reporting confusion matrices for the disease classes in the final
>    report to better analyze remaining edge cases.
> 3. If time permits, you may also explore lightweight augmentation techniques
>    focused on lighting variation and motion blur, since these are common in
>    mobile usage.
>
> The offline TensorFlow Lite deployment, bilingual UX flow, and user-feedback
> collection feature add strong practical value to the capstone and show good
> product thinking in addition to machine learning work. Very good work overall.
> Please continue documenting everything carefully for the final report and
> presentation.
>
> Regards,
> Yazeed

---

#### AlBaraa → Dr. Yazeed (follow-up reply, status: DRAFTED — verify numbers before sending)

> Dear Dr. Yazeed,
>
> Thank you for the detailed and encouraging feedback.
>
> I wanted to let you know that I have already acted on all three of your suggestions:
>
> **1. Confusion matrices**
>
> I have now added a full 11×11 confusion matrix (heatmap + raw count table +
> per-class recall) to the final report. The matrix was computed on the 6,682-image
> held-out test set. The clearest finding is that the three weakest classes —
> early_blight (0.913), septoria_leaf_spot (0.920), and bacterial_spot (0.944) —
> all produce small, dark necrotic lesions that are visually similar at mobile-camera
> resolution, which is consistent with what dermatological literature would expect.
>
> **2. Lightweight augmentation (lighting variation)**
>
> This experiment was already completed before your email arrived. I implemented a
> lighting-only augmentation pipeline (brightness, contrast, and gamma — no colour
> jitter or blur) and retrained Stage 3. Unfortunately the result was negative:
> field accuracy dropped from 77.2% to 73.4%, while lab accuracy improved
> marginally. This is now documented in the report as Experiment 4 (§16). Regarding
> motion blur specifically: I have not tested that in isolation yet, and it is a
> reasonable next step if time permits.
>
> **3. Custom field validation dataset**
>
> I do not currently have access to UAE tomato fields for direct photo collection.
> To address this, I have built a field data feedback flywheel directly into the
> app (§13 of the report): every diagnosis result shows a one-tap feedback card
> that lets the user confirm or correct the prediction, and a background exporter
> packages those labelled photos for future retraining. This collects real field
> images from actual users as the app is used, which I believe is the most
> sustainable approach for closing the lab-to-field gap — especially since all four
> of my controlled experiments (augmentation, segmentation, GAN, and inference-time
> normalisation) confirmed the gap cannot be closed synthetically.
>
> I will continue documenting everything carefully for the final report and
> presentation.
>
> Best regards,
> AlBaraa AlOlabi

> ⚠️ **AGENT WARNING — DO NOT IGNORE:**
> The per-class recall figures quoted in this email do NOT match `eval_deployed.json`:
>
> | Class | Email quote | eval_deployed.json |
> |---|---|---|
> | early_blight | 0.913 | **0.9425** |
> | septoria_leaf_spot | 0.920 | **0.9571** |
> | bacterial_spot | 0.944 | **0.9795** |
>
> Also: "6,682-image" vs JSON `n_test: 6683` (off by one).
>
> This must be resolved in Step 2 before the email is acknowledged as correct.
> Determine which evaluation run produced the email figures. If the email
> numbers are from a different eval (field test? earlier model?), document that
> clearly. The correct figures must be confirmed before Dr. Yazeed's reply cites
> the confusion matrix.

---

### Thread 2 — Dr. Armagan Elibol (Heriot-Watt Dubai, Secondary Advisor)

#### Dr. Elibol → AlBaraa

> Hello Albara,
>
> That is good news for your graduation and capstone, my ideas are usually good :)
>
> Use something like https://github.com/raj-shah14/Synthetic-Leaf-Generation-Using-GAN-and-Classification-using-CNN
> to generate leaf image or tomato leaf image and try to use it for the point 1
> custom validation dataset.
>
> Keep in touch,
> Armagan Elibol

---

#### AlBaraa → Dr. Elibol (sent 2026-05-25, reply pending)

> Dear Dr. Elibol,
>
> Thank you for the suggestion and this is what I have done.
>
> **What we built.** Following the approach in the repository you shared, I
> implemented a DCGAN and trained it on our weakest class bacterial spot (2,503
> images), which was the hardest condition for the model on real field photos. It
> trained stably for 150 epochs with no mode collapse, and generated 600 synthetic
> leaf images. The output quality was good: starting blurry and noisy, the generator
> progressively learned realistic leaf shapes, green tones, and disease-like dark
> mottling. I'm happy to share the sample grids and code.
>
> **One observation about the output.** Because our training images for that class
> are ~96% lab-photographed (PlantVillage), the GAN faithfully learned that
> distribution and the synthetic leaves appear on clean, uniform lab-style
> backgrounds rather than cluttered field backgrounds.
>
> **How we applied it (and one adjustment).** Your idea was to use the synthetic
> images as the custom validation set. After thinking it through, we chose to use
> real field images (PlantDoc) as the validation set instead, and to use the GAN
> images as training augmentation. Our reasoning: a validation set needs to represent
> the real-world distribution we ultimately care about, whereas a generator can only
> reproduce the distribution it was trained on — so validating real-world accuracy
> on synthetic images would not measure the lab-to-field gap that is our core
> challenge. We felt synthetic data was better suited to expanding training than
> to validating.
>
> **The result.** We ran a clean A/B test (same training recipe, with vs. without
> the 600 synthetic images) and evaluated both on the real field photos. The GAN
> augmentation did not improve field accuracy on bacterial spot (it stayed flat,
> and end-to-end accuracy was unchanged-to-slightly-lower). This is consistent with
> the observation above: because the synthetic data mirrors the lab distribution, it
> does not help close the lab-to-field gap.
>
> **What we concluded.** This was actually a valuable negative result. Together with
> two other experiments (heavy data augmentation and leaf segmentation, which
> similarly did not help on field images), it points clearly to the same conclusion:
> the bottleneck is real field data, not more synthetic or transformed lab data.
> We've therefore built an in-app feedback mechanism so the app collects and labels
> real UAE field images over time — which is the data that should finally close the
> gap.
>
> Thank you again. I hope that I have done everything on the right track.
>
> Best regards,
> AlBaraa AlOlabi

> **Status:** Reply from Dr. Elibol pending as of 2026-05-25.
> When received: add reply to this section and check for new report obligations.

---

## KNOWN CONTRADICTIONS — VERIFY EACH IN STEP 2

| # | Issue | Values seen | Most likely truth | Required action |
|---|---|---|---|---|
| C1 | ECE after calibration | 0.005 (email to Yazeed), 0.0613 (eval_deployed.json), 0.0046 (HANDOFF.md) | HANDOFF 0.0046 = post-calibration; JSON 0.0613 may be pre-calibration or different run | Trace temperature scaling code; confirm which JSON key is pre vs post |
| C2 | End-to-end accuracy | 97.6% (email), 97.19% (JSON `correct_diagnosis_pct`), 96.5% (HANDOFF lab baseline) | JSON = deployed TFLite on lab set; 96.5% may be a different model version | Trace each to exact test set and model version |
| C3 | Total model size | 9.4 MB (email), 9.87 MB (JSON `model_total_mb`), ~6 MB (HANDOFF) | JSON 9.87 MB is most precise | Patch email figure and HANDOFF |
| C4 | Disease accuracy | 97.96% (email), 97.59% (JSON `test_accuracy`) | JSON = TFLite deployed; email may be pre-export Keras | Confirm which model was evaluated |
| C5 | Per-class recall (3 classes) | See email vs JSON table in Thread 1 | JSON is authoritative | Identify source of email figures before sending |
| C6 | "10 diseases" vs "11 classes" | Varies by document | 11 = 10 diseases + healthy (correct) | Patch all "10 class" references |
| C7 | n_test | 6,682 (email) vs 6,683 (JSON) | JSON | Off-by-one; patch email |
| C8 | Field accuracy baseline | 77.2% (HANDOFF) — absent from emails | HANDOFF | Must appear prominently in report |

---

## STEP 0 — PLAN BEFORE ACTING (MANDATORY — DO NOT SKIP)

Before doing anything else, produce a written plan in this exact format:

```
PLAN
====

Files successfully read:
  - [filename]: [one-line purpose]
  - ...

Files MISSING:
  - [filename]: [what it was expected to contain]

Contradictions confirmed (from the table above + any new ones):
  C1: [confirmed / cannot confirm yet — reason]
  C2: ...
  (continue for all)

Actions required:
  FIX (rewrite only, no code):
    - [description of fix]
  RECOMPUTE (must run a script):
    - [exact bash command] — [what it will produce]
  BLOCKED (need human input before proceeding):
    - [specific question for AlBaraa]

Proposed order of operations:
  1. Resolve BLOCKED items (list them)
  2. Run RECOMPUTE items in this order: ...
  3. Fill Step 1 table
  4. Complete consistency audit
  5. Write narrative (Step 4)
  6. Design structure (Step 5)
  7. Rewrite sections (Step 6)
  8. Defense prep (Step 7)

Risks:
  - [anything that could invalidate the report if not addressed]
```

**STOP HERE AND WAIT** if there are any BLOCKED items.
Do not proceed to Step 1 until all BLOCKED items are resolved by the user.

---

## STEP 1 — Single Source of Truth Table

Every cell must trace to a specific file + line number or JSON key.
Write **MISSING** if the value cannot be found in any document.
Write **CONFLICT** if two sources disagree and the conflict is unresolved.

| Item | Value | Source file | Line / key |
|---|---|---|---|
| Architecture | | | |
| Stage 1 — model family | | | |
| Stage 1 — task | | | |
| Stage 1 — input/output spec | | | |
| Stage 2 — model family | | | |
| Stage 2 — task | | | |
| Stage 3 — model family | | | |
| Stage 3 — task | | | |
| All 11 class names (list) | | | |
| Training dataset (primary) | | | |
| PlantDoc field images added | | | |
| Preprocessing contract (exact) | | | |
| Held-out test set — n | | | |
| Field test set — dataset name + n | | | |
| Stage 1 accuracy | | | |
| Stage 2 accuracy | | | |
| Stage 3 lab accuracy | | | |
| Stage 3 field accuracy | | | |
| End-to-end lab (gate + classifier) | | | |
| End-to-end field | | | |
| ECE before calibration | | | |
| ECE after calibration | | | |
| Temperature T value | | | |
| Non-leaf rejection rate | | | |
| Other-leaf misclassification rate | | | |
| Stage 1 TFLite size (bytes) | | | |
| Stage 2 TFLite size (bytes) | | | |
| Stage 3 TFLite size (bytes) | | | |
| Total TFLite size (MB) | | | |

---

## STEP 2 — Consistency Audit

For every contradiction — including all pre-flagged items (C1–C8) and any new ones
you find during your file read — produce an entry in this format:

```
─────────────────────────────────────────────
ISSUE ID:    [C1 / C2 / ... / NEW-1 / ...]
NAME:        [short descriptive name]
─────────────────────────────────────────────
Documents affected:
  - [file]: "[exact quote]"
  - [file]: "[exact quote]"

Why this matters in a defense:
  [1–2 sentences on how a hostile examiner uses this against you]

Severity:    CRITICAL / MEDIUM / MINOR

Recommended action:
  [ ] FIX      — rewrite only, no code needed
  [ ] RECOMPUTE — must rerun a script
  [ ] BLOCKED  — need human input

If RECOMPUTE:
  Exact command: [full bash command]
  Expected output: [what file/metric will be produced]
  Where to log result: RECOMPUTE LOG

If BLOCKED:
  Question for AlBaraa: [specific, answerable question]
─────────────────────────────────────────────
```

---

## STEP 3 — Recompute Protocol

For every item marked RECOMPUTE in Step 2:

### Before running:
1. State hypothesis: "I expect the correct value to be X because..."
2. Write the exact command with all flags
3. **Wait for user confirmation** — do not run without explicit approval

### When running:
- Capture full stdout and stderr to a log file
- Record: date/time, script path, all arguments, Python env used, GPU/CPU
- Record: dataset path and version used

### After running:
- Capture all output metrics
- Capture confusion matrix if produced
- Compare against the previous value explicitly: "was X, now Y, delta = Z"
- Update the Step 1 table immediately
- Log in RECOMPUTE LOG (see Output Format)

### If retraining is required:
Document ALL of the following before starting:
- Dataset version and split (train/val/test exact counts)
- Augmentation flags used
- Model architecture and pretrained weights source
- Learning rate, batch size, epochs, early stopping config
- Random seed
- Hardware used
After training: run full evaluation, not just training loss.
Do not consider a retrain complete until eval_deployed.json equivalent exists.

**Rule:** Do not retrain unless the contradiction cannot be resolved by tracing
existing logs or eval files. Retrain is the last resort, not the first.

---

## STEP 4 — The Scientific Story (Internal Compass)

Write the authoritative project narrative. This is NOT a report section yet —
it is the single reference that every report section must be consistent with.

Structure it as follows:

**1. The v1 failure**
What specifically went wrong, why it was a safety problem (not just an accuracy
problem), and what the observable symptom was.

**2. The cascade solution**
The architectural rationale — why three stages beats one classifier with a reject
class. Be mechanistic, not vague.

**3. The domain gap — measured**
Lab accuracy vs field accuracy (exact numbers from Step 1 table).
What PlantDoc is and why it was the right field proxy.
This is the honest story. Do not soften it.

**4. The four falsified hypotheses**
For each experiment, in this structure:
- Hypothesis (what was expected to help and why)
- Method (brief — what was changed)
- Result (exact numbers — delta from baseline)
- What it proved (what mechanistic conclusion follows)

The four experiments:
1. Heavy UAE augmentation (brightness / contrast / gamma / hue / sat / JPEG / blur)
2. MobileSAM leaf segmentation
3. DCGAN synthetic bacterial_spot (+600 images)
4. Test-time normalisation (segment field leaf → white background)
(Plus: lighting-only augmentation as Experiment 4b / §16)

**5. The decisive insight**
The composited background experiment results:
- Lab leaf + field background → 65.5%
- Field leaf + white background → 46.8%
What this proves: the leaf appearance drives the gap, not the background.
Why this means synthetic approaches cannot close it.

**6. What is deployed and why**
The ctrl model (minimal aug = flip only), why it was chosen over the experiment
variants, what calibration was applied, and what the feedback flywheel does.

**7. What remains open**
Honest future work only. No overclaiming. No presenting built features as future.

**Framing rule:** The four negative results ARE the scientific contribution.
They form a controlled investigation that leads to a clean, reproducible conclusion.
Frame them as findings, not failures.

---

## STEP 5 — Final Report Structure

Design the chapter/section structure. For each entry provide:
- Section title
- 2-sentence scope description
- Required figures and tables (with specific metric references from Step 1)
- Content to REMOVE from the current draft (outdated, wrong-tense, contradicted)

Constraints:
- No "biotic vs abiotic" framing anywhere in the document
- The domain gap investigation must be its own dedicated section
- The four experiments must appear in a unified "Experiments" section framed as
  a structured investigation, not scattered as limitations
- Anything already built must be in past tense
- The feedback flywheel must be described as implemented, not proposed
- No section may contain a number that is not in the Step 1 table

---

## STEP 6 — Rewrite Critical Sections

Write each section in full. Apply these rules to every word:
- Every number traces to the Step 1 table — no exceptions
- No future tense for completed work
- No hedging on confirmed results ("appears to," "seems to," "may suggest")
- Field accuracy (77.2%) must appear prominently — it is the honest result, not
  a footnote
- The four failed experiments are presented as a controlled scientific investigation
  with a conclusion, not as "things that didn't work"

---

### 6.1 Abstract (250 words maximum)

Must mention: the cascade architecture, three stages and their tasks, lab accuracy,
field accuracy, the domain gap quantification, calibration ECE before and after,
offline TFLite deployment, and the feedback flywheel.

Do not mention "biotic vs abiotic."

---

### 6.2 Problem Statement

**Must open with the v1 failure, not with "tomatoes are an important crop."**

First paragraph: describe the specific failure mode of v1 — what input caused it,
what the model did, and why this is a safety problem in a real agricultural context.
Include the misclassification rate of non-tomato inputs if that number exists in
the source documents.

Second paragraph: the root cause (data distribution mismatch — lab negatives vs
field positives).

Third paragraph: the scope of the solution required.

---

### 6.3 Research Objectives

Numbered list. Each objective must be tagged:
- **[MET]** — with a pointer to the result
- **[PARTIALLY MET]** — with an honest explanation
- **[DEFERRED]** — with a reason (not just "future work")

Do not include any objective that was quietly abandoned without explanation.
Do not include any objective that was never attempted.

---

### 6.4 Methodology

Must cover, in this order:

1. **Cascade design rationale** — why this architecture, why three stages,
   what the alternative was and why it failed

2. **Preprocessing contract** — exact specification, byte-identical between
   training and inference:
   - Input format: float32[1, 224, 224, 3]
   - Colour space: RGB
   - Resize method: center-crop to square, then resize to 224
   - Normalisation: divide by 255 → [0, 1]
   - NOT applied: ImageNet mean/std normalisation

3. **Data pipeline**
   - PlantVillage: what it contains, how it was split
   - PlantDoc: what it is, how it was integrated, why it matters
   - Class counts and split sizes

4. **Temperature scaling**
   - What it is and why it was applied
   - T value used
   - ECE before and after

5. **Experiments section**
   Each experiment in a consistent schema:
   - Experiment ID and name
   - Hypothesis
   - Implementation
   - Evaluation method
   - Result (exact numbers vs baseline)
   - Conclusion

---

### 6.5 Evaluation

Structure:

1. **Lab results** — table with per-class recall + overall accuracy, reference to
   confusion matrix figure

2. **Field results** — table with field accuracy and end-to-end field accuracy.
   Do not present this as a secondary result. It is the primary deployment metric.

3. **Gate metrics** — stage 1 and stage 2 rejection rates for non-leaf and
   other-leaf inputs

4. **Calibration** — ECE before and after, with a one-sentence explanation of
   what ECE measures and why it matters for user trust

5. **Capability statement** — explicit declaration of what the system can and
   cannot do. Include the known edge cases (early_blight vs septoria_leaf_spot,
   background-dependent classes).

---

## STEP 7 — Defense Preparation

Generate exactly **5 questions** a hostile examiner will ask.
For each, write a model answer that is:
- Honest — does not hide the 77.2% field number or the four failed experiments
- Specific — uses exact numbers from the Step 1 table
- Not defensive — treats the negative results as the scientific contribution

**Required questions (must include all five):**

1. "Your field accuracy is 77% — is this system actually deployable in the real world?"

2. "You ran four experiments and all of them failed to improve field accuracy.
   Doesn't that suggest you simply ran out of ideas rather than conducting
   real research?"

3. "How do you know temperature scaling improved calibration and not something
   else you changed at the same time?"

4. "The per-class recall figures in your email to your supervisor differ from
   the numbers in your evaluation JSON. Which is correct, and how did that
   discrepancy occur?"

5. [Generate this one from the most dangerous contradiction or gap you found in
   Step 2 — something specific to this project that was not pre-flagged above.]

---

## OUTPUT FORMAT

Write to: `ml/reports/FINAL_REPORT_DRAFT.md`

Structure with clear `## STEP N` headers. Each step must be self-contained so
the student can review phases independently.

Append the following three tables at the very end of the file:

---

### RECOMPUTE LOG

| Date | Script path | Arguments used | Key metric output | Step 1 cells updated |
|---|---|---|---|---|
| | | | | |

---

### PATCH LOG

| Document patched | Section | Old value | New value | Reason |
|---|---|---|---|---|
| | | | | |

---

### SUPERVISOR OBLIGATIONS TRACKER

| Supervisor | Suggestion | Status | Report section reference |
|---|---|---|---|
| Dr. Yazeed | Collect custom field validation dataset | PARTIAL — flywheel built; no direct collection | §13 |
| Dr. Yazeed | Report confusion matrices for disease classes | DONE — verify numbers match JSON | §[TBD] |
| Dr. Yazeed | Lightweight augmentation: lighting variation | DONE — negative result documented | §16 |
| Dr. Yazeed | Lightweight augmentation: motion blur | NOT DONE — future work | §future |
| Dr. Elibol | GAN synthetic images for validation | DONE — pivoted to training aug; A/B tested | §[TBD] |
| Dr. Elibol | Reply pending as of 2026-05-25 | AWAITING | — |

---

## ABSOLUTE PROHIBITIONS

The following are hard rules. Any violation invalidates the output.

- **Do not invent numbers.** If a value is MISSING, write MISSING.
- **Do not smooth over contradictions.** Surface them even if they are embarrassing.
- **Do not hide the field accuracy.** 77.2% is the headline honest result.
  It appears in the abstract, problem statement, evaluation, and defense prep.
- **Do not present future tense for completed work.** The cascade is built.
  The flywheel is built. The calibration is applied. Past tense throughout.
- **Do not write "further research is needed" for things already done.**
- **Do not present the four failed experiments as failures or limitations.**
  They are a controlled investigation with a reproducible, clean conclusion.
- **Do not proceed past Step 0 if there are BLOCKED items unresolved.**
- **Do not run a retrain without:**
  (a) user confirmation, (b) full parameter documentation, (c) a complete eval run after.
- **Do not acknowledge the email to Dr. Yazeed as numerically correct** until
  the per-class recall discrepancy (C5) is resolved.

---

*End of prompt. Feed this file whole to Claude Code. Do not summarise.*
