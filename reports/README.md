# TomatoCare — Reports & Documentation Index

This folder is the single home for the **capstone report and all its provenance**. If you are
looking for "the report," it is **`FINAL_REPORT_REVISED.md`**. Everything else here exists to
support, audit, or explain it.

> **Scope note.** This folder currently covers the **AI/model** half of the capstone (owner:
> AlBaraa AlOlabi). The app / UI-UX team's own working documents are intentionally *not* gathered
> here yet.

---

## Status legend
| Tag | Meaning |
|---|---|
| **AUTHORITATIVE** | The current, submit-ready source of truth. Trust this. |
| **PROVENANCE** | Supporting / historical record that explains how we got here. Accurate, but not the thing you submit. |
| **ARCHIVED** | Superseded. Kept for traceability only — see `archive/`. Do **not** quote numbers from these. |

---

## File map

| File | Status | What it is |
|---|---|---|
| **`FINAL_REPORT_REVISED.md`** | **AUTHORITATIVE** | The master capstone report (Ch 1–9 + front matter + references + appendices). Fully reconciled to `eval_deployed.json`; the hand-built `.docx` submission mirrors this text. **This supersedes `archive/FINAL_REPORT_FULL.md`.** |
| `eval_deployed.json` | **AUTHORITATIVE** (snapshot) | Frozen copy of the deployed-cascade metrics — the single source of truth for every number. The canonical live copy stays in `../ml/reports/`. |
| `figures/` | **AUTHORITATIVE** (snapshot) | Copies of the three report figures: `confusion_matrix_deployed.png`, `lab_vs_field_accuracy.png`, `gan_samples_epoch150.png`. Canonical copies live in `../ml/reports/`. |
| `AUDIT_AND_VIVA_PACK.md` | **PROVENANCE** | The control/audit doc: source-of-truth table, full consistency audit (C1–C8 + NEW-1..5), scientific story, **6 hostile-examiner Q&A**, patch/recompute/supervisor logs, and a corrected supervisor email draft. Read this before a viva. |
| `RECONCILIATION_CHANGELOG.md` | **PROVENANCE** | Documents *why* the abiotic/UAE-environmental model claims were cut and lists every reconciliation made when distilling the merged super-report into the master. |
| `EMAIL_LOG.md` | **PROVENANCE** | Single tracker for all project correspondence (who → whom, date, purpose, status, next action). |
| `PROJECT_JOURNEY.md` | **PROVENANCE** | AlBaraa's original v0 narrative — the first-ever attempt (from-scratch TomatoCareNet, 91.17%). Preserved verbatim with a provenance header. |
| `archive/` | **ARCHIVED** | Five superseded documents + an `archive/README.md` explaining why each was retired. |

---

## The single number source-of-truth

Every metric in the report traces back to **`eval_deployed.json`** (deployed 3-stage TFLite cascade,
evaluated on the held-out `tomato20k/valid` split):

| Metric | Value |
|---|---|
| Disease accuracy (held-out lab test) | **97.59%** |
| End-to-end accuracy (lab) | **97.19%** |
| Field accuracy (PlantDoc, n=79) | **77.2%** |
| ECE (held-out test, 15-bin, post-calibration) | **0.061** |
| Temperature T | 0.5889 |
| Total model size | **9.87 MB** (1.92 + 1.92 + 6.03) |
| Held-out test n | **6,683** |
| Classes | **11** (10 diseases + healthy) |
| Two weakest recalls | early_blight 0.943, septoria_leaf_spot 0.957 |

If any document here disagrees with this table, the table wins and that document is stale.

---

## Where the live pipeline outputs live

`../ml/reports/` stays **code-only / canonical-output** territory and is the source these snapshots
were copied from:
- `eval_deployed.json` (canonical) and the three figures (canonical)
- `gen_fig7_2.py`, `md_to_docx.py` (regeneration scripts)

Nothing that regenerates those outputs was moved, so the pipeline still works. The copies in this
folder are frozen snapshots for self-contained reading.

---

## How the docs relate (one paragraph)

`PROJECT_JOURNEY.md` is where it began (v0, the from-scratch CNN). The model then evolved through a
single MobileNetV3 + reject-class prototype to the deployed 3-stage cascade — that progression and
its measured results are written up in **`FINAL_REPORT_REVISED.md`**, the document you submit.
`eval_deployed.json` fixes every number in it; `RECONCILIATION_CHANGELOG.md` records the corrections
that made it defensible; `AUDIT_AND_VIVA_PACK.md` is the audit trail + viva prep behind those
numbers; and `EMAIL_LOG.md` tracks the supervisor/external correspondence around it. The `archive/`
holds the earlier drafts those documents replaced.

For **developer-level** reference (script names, config YAML, Docker, Kotlin code), see `../docs/`:
`ml-pipeline.md` (ML training stages), `architecture.md` (system design), `android-app.md` (app
internals), `getting-started.md` (onboarding), `docker.md`, `functional_tests.md` (FR-01..FR-28
matrix), `nfr_verification.md` (NFR sign-off). These were updated 2026-05-29 to match the deployed
cascade, the current app (Encyclopedia, dark mode, feedback flywheel, dashboard), and
`eval_deployed.json`.

For **open-source / onboarding**, the repo root carries `../README.md` (overview + model-acquisition
+ CI badge), `../CONTRIBUTING.md` (contributor setup, tests, conventions), and `../CHANGELOG.md`
(engineering log). The app-level testing story (unit tests + CI) is written up in
`FINAL_REPORT_REVISED.md` §7.9; on-device functional/integration/system/acceptance results remain the
QA lead's to record there.
