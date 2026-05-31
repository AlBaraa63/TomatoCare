# TomatoCare — Team Handoff & Remaining Work

**From:** AlBaraa AlOlabi (CV / model + report lead)
**Date:** 2026-05-31
**Purpose:** Hand the remaining report items to the team, with clear owners, and a
simple routine for keeping Dr. Yazeed updated.

> **Read first:** the supervisor's feedback and its status are in
> `reports/SUPERVISOR_FEEDBACK.md`. The single source of truth for every number is
> `reports/eval_deployed.json` — **never change a metric.** The Word `.docx` mirrors
> the Markdown report; any text change must be applied in both.

---

## 1. Where the report stands now

The AI/model content is complete and the report has been revised to address almost
all of Dr. Yazeed's feedback. **What I (AlBaraa) have already done:**

- Abstract: added the field-vs-lab limitation; removed the "without compromising
  accuracy" wording.
- Ch1: shortened the problem table; added the "why tomato" paragraph.
- Ch2: strengthened competitor references + a technical "why we are better" comparison.
- Ch3: dataset split, train/test leakage statement, ethical handling of feedback images.
- Ch4: requirement IDs + verification methods (Appendix B traceability); accessibility
  requirements (NFR-11/12/13).
- Ch5: relabelled the ERD as "Data Model Diagram"; explanation under each figure.
- Ch6: folder structure, key components, CI pipeline, 48 unit tests, three implementation
  challenges with fixes.
- Ch7: device-performance table (S10+ latency), regression evidence for the fixed bugs.
- Ch8/9: practical future work; advisory-not-replacement statement.
- Formatting: removed em dashes and § symbols (now "Section"); fixed a Ch2 editing artefact.

**The clean, revised Markdown is `report.md` (repo root).**

---

## 2. What the team must do (with owners)

Owners are suggested from the project roles; adjust as needed.

### A. UML diagrams — **Iyad (System Architect & Documentation)**
The diagrams (Figures 9–17: Use Case, Layered Architecture, two Sequence, State Chart,
Data Model, Class, Activity) are **stale** — they predate the current app, which now has a
bottom navigation bar, the Disease Encyclopedia, dark mode, and the feedback flywheel.
- Redraw each diagram to match the **shipped** app.
- The chapter prose already describes the correct, current behaviour — make the diagrams
  agree with it.
- Insert the redrawn images into the Word document.

### B. App screenshots — **Ahmed (UI/UX)** + Iyad
- Figure 6.2: a montage of the key screens (Home dashboard, Scan, Result, Encyclopedia,
  Settings) ideally in **both English and Arabic** and **light + dark**.
- Figure 7.3: the on-device inference screenshots (showing "Diagnosed on-device in N ms")
  are already captured in the **`meseremnts/`** folder — insert them.

### C. Model figures — Iyad
- Insert the three ML figures from **`reports/figures/`**: confusion matrix, GAN sample
  grid, lab-vs-field bar chart.

### D. Device performance — **Fares (QA & Integration)** + Kazi
- Run the latency protocol on a **genuine low/mid-end device** (≈ Android API 26 / 2 GB
  RAM). Scan ~10 leaves and read the "Diagnosed on-device in N ms" value off the screen.
- Add the device row to **Table 7.6** (device · RAM · Android version · median · max latency).
  S10+ is already in the table; one lower-end device is what's missing.

### E. Usability study — **Fares** (+ everyone recruits participants)
- Run the usability protocol already written in Ch7 with **at least 5 participants**.
- Fill **Table 7.7** with task completion, time, and SUS scores.

### F. Final report audit & copy-edit — **Iyad** (lead), all review
- Consistency audit: every number must match `reports/eval_deployed.json`; no contradictions
  between chapters.
- Copy-edit: split dense paragraphs, make all figure captions one consistent style, confirm
  all 37 references are cited in-text and IEEE-formatted.
- Confirm the front matter (student IDs, examiner names, dates) is complete.

---

## 3. Hard rules (do not break)

- **Numbers are frozen.** 97.59% disease (lab), 97.19% end-to-end (lab), 77.2% field,
  0.061 ECE, 9.87 MB, n=6,683. Source: `reports/eval_deployed.json`.
- **Never reintroduce the "UAE-simulation / abiotic" claim.** The model is **not** trained on
  simulated UAE data and does **not** detect abiotic stress. Simulating field variation was
  *tested and failed* (see Ch7) — the deployed model uses flip-only augmentation.
- **Do not overclaim "low-end."** Until the low-end device test (item D) is done, the report
  must say the S10+ result is a flagship measurement and low-end testing is in progress.
- **Keep `.docx` and `report.md` in sync** — apply every text change in both.

---

## 4. How to keep Dr. Yazeed updated

- **Single point of contact.** One person (AlBaraa or Iyad) sends supervisor emails, so he
  receives one consistent thread, not five.
- **Log every email** in `reports/EMAIL_LOG.md` (who → whom, date, purpose, status).
- **Update cadence:** send a short, **bulleted** progress note when each milestone lands
  (diagrams done; device test done; usability study done; final audit done). Dr. Yazeed
  specifically asked for bullets/sections, not long paragraphs.
- **Before final submission:** send him the complete PDF (all figures + tables filled) for a
  final check, with enough lead time before the deadline.
- **What to report each time:** what changed, what's next, and anything you need from him.

---

## 5. Quick reference — where things live

| Asset | Location |
|---|---|
| Clean revised report (Markdown) | `report.md` (repo root) |
| Supervisor feedback + status ledger | `reports/SUPERVISOR_FEEDBACK.md` |
| Email tracker | `reports/EMAIL_LOG.md` |
| Frozen metrics (source of truth) | `reports/eval_deployed.json` |
| Model figures to insert | `reports/figures/` |
| Device/inference screenshots | `meseremnts/` |
| Viva prep (6 Q&A) | `reports/AUDIT_AND_VIVA_PACK.md` |
| App internals reference | `docs/android-app.md` |
