# CLAUDE.md — TomatoCare project context for Claude Code

## What this project is

TomatoCare is a **fully offline, bilingual (English/Arabic) Android app** that diagnoses tomato
leaf diseases on-device. It is an Al Ain University capstone (Bachelor of Software Engineering,
Spring 2026). The team has five members; the work is split into two tracks:

- **AI / ML (AlBaraa AlOlabi, 202210405)** — dataset, training, evaluation, TFLite export, report.
  This is the primary user of Claude Code. AlBaraa owns everything under `ml/` and `reports/`.
- **App / UI-UX (Ahmed, Kazi, Iyad, Fares)** — Android Kotlin/Compose screens, CameraX,
  TFLite inference engine, navigation, bilingual strings, treatments, testing.

Supervisor: **Dr. Yazeed Ghadi** (Al Ain University). External advisor: **Dr. Armagan Elibol**
(Heriot-Watt University Dubai, GAN guidance).

## The model — what it actually is

A **3-stage MobileNetV3 TFLite cascade**, not a single classifier:

| Stage | Model | Size | Job |
|-------|-------|------|-----|
| 1 — Leaf gate | MobileNetV3-Small | 1.92 MB | Reject non-leaf images |
| 2 — Tomato gate | MobileNetV3-Small | 1.92 MB | Reject non-tomato leaves |
| 3 — Disease classifier | MobileNetV3-Large | 6.03 MB | Classify into **11 classes** (10 diseases + healthy) |

Total: **9.87 MB**, float16 quantisation. The 11 classes are: bacterial_spot, early_blight,
healthy, late_blight, leaf_mold, mosaic_virus, powdery_mildew, septoria_leaf_spot, spider_mites,
target_spot, yellow_leaf_curl_virus.

### Model evolution (v0 → v1 → deployed)

1. **v0 — TomatoCareNet** (from-scratch custom 4-block CNN + SE attention + GAP): 91.17% lab,
   10 classes, 4 merged datasets. First-ever attempt. Provenance: `reports/PROJECT_JOURNEY.md`.
2. **v1 — Single MobileNetV3-Large + `not_tomato` reject class**: Capstone 1 prototype.
   Exposed a safety failure — non-tomato inputs silently labelled as diseases with high confidence.
3. **Deployed — 3-stage cascade**: dedicated gates fix the OOD safety problem; each gate is a
   separate objective. This is what ships.

Present this as a deliberate three-iteration engineering progression, not as failures.

## Single source of truth — numbers

**`reports/eval_deployed.json`** (canonical live copy: `ml/reports/eval_deployed.json`).
Every metric in the report, README, and any document must trace back to this file.

| Metric | Value |
|--------|-------|
| Disease accuracy (held-out lab, n=6,683) | **97.59%** |
| End-to-end accuracy (lab) | **97.19%** |
| Field accuracy (PlantDoc, n=79) | **77.2%** |
| Field disease accuracy | 87.1% |
| ECE (held-out test, 15-bin, post-calibration) | **0.061** |
| Temperature T | 0.5889 |
| Model size | **9.87 MB** (1.92 + 1.92 + 6.03) |
| Weakest recalls | early_blight 0.943, septoria 0.957 |
| Gate safety | non-leaf reject 99.55%, non-tomato-leaf reject 99.37%, leak 0.05% |
| Decisive composited split | lab-leaf+field-bg **65.5%** vs field-leaf+white-bg **46.8%** |

**If you are about to write a number, check it against this table first.** Never invent,
round differently, or "improve" a metric. If a document disagrees with this table,
the table (and the JSON) wins.

## Key rules

1. **Never fabricate or adjust numbers.** If unsure, read `reports/eval_deployed.json`.
2. **No false claims about the model.** The system does NOT detect abiotic stress (sunscald,
   heat, salinity). It is an 11-class tomato-disease classifier. The `stress_type` field in the
   app is static descriptive metadata, not a learned prediction.
3. **Don't touch app code unless asked.** AlBaraa owns `ml/` and `reports/`. The `android/`
   tree is the app team's. Ask before editing anything under `android/`.
4. **Don't commit unless asked.** Stage changes, show diffs, but wait for an explicit "commit."
5. **The .docx is hand-built.** The authoritative Markdown is `reports/FINAL_REPORT_REVISED.md`,
   but the Word submission was built by hand in Word. If the MD changes, warn that the Word file
   needs manual updating too.
6. **Field accuracy (77.2%) is a strength, not a weakness.** Present it honestly and prominently.
   It is the floor we measured, not hid. The feedback flywheel is the plan to close the gap.
7. **Four negative experiments are a positive finding.** Heavy aug (−11.4 pts), MobileSAM
   segmentation (slight decline), DCGAN +600 synthetic (zero gain), test-time white-bg
   normalization (−30.4 pts). Together with the composited 65.5% vs 46.8%, they triangulate
   that **leaf appearance, not background, dominates the domain gap**. This is a controlled
   investigation with a conclusion — never present it as "we failed four times."

## Repository layout

```
TomatoCare/
├── CLAUDE.md               ← you are here
├── README.md               ← public project overview (corrected 2026-05-28)
│
├── reports/                ← ALL report docs live here
│   ├── README.md           ← INDEX: file map, status legend, number source-of-truth
│   ├── FINAL_REPORT_REVISED.md   ← AUTHORITATIVE master report (Ch 1–9)
│   ├── AUDIT_AND_VIVA_PACK.md    ← audit, 5 viva Q&A, patch log, corrected email draft
│   ├── RECONCILIATION_CHANGELOG.md ← why abiotic/UAE model claims were cut
│   ├── EMAIL_LOG.md        ← correspondence tracker (Yazeed ✅, Elibol awaiting)
│   ├── PROJECT_JOURNEY.md  ← v0 first-attempt narrative (preserved verbatim)
│   ├── eval_deployed.json  ← frozen snapshot of source-of-truth metrics
│   ├── figures/            ← confusion matrix, lab-vs-field bar, GAN samples
│   └── archive/            ← 5 superseded docs (HANDOFF, old reports, etc.)
│
├── ml/                     ← Python ML pipeline (AlBaraa)
│   ├── configs/            ← training_config.yaml
│   ├── dataset/            ← raw/, augmented/, splits/
│   ├── models/             ← checkpoints/, tflite/
│   ├── reports/            ← CANONICAL pipeline outputs (eval_deployed.json, PNGs, scripts)
│   ├── scripts/            ← pipeline scripts
│   └── utils/              ← dataset_loader, model_factory, seed
│
├── android/                ← Kotlin/Compose app (app team)
│   └── app/src/main/
│       ├── assets/         ← 3 TFLite models + treatments.json + labels.json + model_card.md
│       └── kotlin/com/tomatocare/  ← screens, ViewModels, inference, storage
│
└── docs/                   ← developer docs (getting-started, architecture, ml-pipeline, etc.)
```

## Correspondence status (as of 2026-05-28)

See `reports/EMAIL_LOG.md` for the full tracker.

- **Dr. Yazeed** — replied and **approved** 2026-05-27. No action needed. A corrected-numbers
  follow-up email is drafted (in the audit pack) but ON HOLD since he already approved.
- **Dr. Elibol** — sent 2026-05-25 (GAN pivot explanation). **Still awaiting reply.**

## Common tasks

### "Check if a number in the report is correct"
1. Read `reports/eval_deployed.json` (or `ml/reports/eval_deployed.json`).
2. Grep `reports/FINAL_REPORT_REVISED.md` for the number.
3. Compare. The JSON wins.

### "Update the report"
1. Edit `reports/FINAL_REPORT_REVISED.md`.
2. **Warn AlBaraa** that the hand-built `.docx` will need the same change applied in Word.

### "Add a new email to the log"
Edit `reports/EMAIL_LOG.md`. Add a row to the table. Use status: CLOSED / HOLD / AWAITING / TODO.

### "Run the evaluation pipeline"
```bash
python -m ml.scripts.eval_model          # or the specific eval script
python ml/reports/gen_fig7_2.py           # regenerate lab-vs-field bar chart
```
Canonical outputs land in `ml/reports/`. Copy updated snapshots to `reports/` if needed.

### "Prepare for viva"
Read `reports/AUDIT_AND_VIVA_PACK.md` — it has the 5 hostile-examiner questions with model
answers, the full consistency audit, and the scientific story.

## What NOT to do

- Do NOT claim the model detects abiotic stress, was trained on UAE-augmented data, or was
  tested on a UAE-conditions test set. These were false claims that were cut — see
  `reports/RECONCILIATION_CHANGELOG.md` for the full story.
- Do NOT use "ten classes" / "ten conditions" when referring to the model output. It is **11**
  (10 diseases + healthy). "Ten tomato diseases" is correct (there are 10 diseases).
- Do NOT reference `reports/archive/` files as current — they are superseded.
- Do NOT push to remote without asking.
- Do NOT edit the `.docx` from Claude Code — edits go in the Markdown; AlBaraa applies them
  to Word manually.

## Working style

AlBaraa values honest, direct help. Lead with what is already correct, then the minimal path
to fix what isn't. Keep numbers traceable. Under deadline pressure, be concise — don't pad
responses with caveats he already knows about. If something is wrong, say so plainly.
