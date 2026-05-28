# TomatoCare Super-Report — Reconciliation Changelog

**Date:** 2026-05-28
**Source merge:** `C:\Users\POTATO\Desktop\updated report.md` (preserved, untouched)
**Corrected output:** `ml/reports/FINAL_REPORT_FULL.md`

## Why these changes
The merged report claimed, in several places, that the system **detects abiotic stress**
(sunscald / heat / salinity) and was **trained on UAE-augmented data** and **tested on a
UAE-conditions test set**. None of this is true of the deployed model: it is an 11-class
tomato-disease classifier (10 diseases + healthy), trained on a PlantVillage-derived dataset
with minimal augmentation, and UAE-style heavy augmentation was a *failed experiment* (Ch 7).
Leaving those claims in would have been indefensible in the viva. Per the agreed decision, all
false abiotic / UAE-environmental **model claims were cut**, while the legitimate UAE *deployment*
context (offline, Arabic/RTL, smallholder accessibility, food security) was kept.

The AI core (Chapter 7) was already correct — its 11×11 confusion matrix matches
`eval_deployed.json` cell-for-cell — and was left intact.

> **IMPORTANT for the Word version:** your merge in Word contains the teammate's figures (UML,
> screenshots) that this Markdown file does not. To keep those figures, apply the changes below
> **in your Word document** rather than regenerating a docx from the Markdown. The corrected
> `FINAL_REPORT_FULL.md` is the authoritative text to copy from.

---

## A. Abiotic / UAE-environmental claims CUT (false model claims)

| Where | Change |
|---|---|
| **Abstract** | Rewritten. Removed "biotic↔abiotic indistinguishable", "supplemented with UAE-condition images (sun/dust/heat)", "ten-category model", "UAE-specific held-out test set", "biotic/abiotic badge". Now describes the honest 3-stage cascade, 11 classes, offline EN/AR, calibration, and the 97.59% lab / 77.2% field result. |
| **§1.1 Introduction** | Reframed the core problem from "biotic↔abiotic confusion" to disease-identification difficulty + safe rejection of out-of-scope inputs (aligns with §1.4). |
| **§1.1 (competitors)** | Removed "not trained on UAE-specific patterns of stress"; kept the offline/Arabic/cost critique. |
| **§1.2.2** | "the trained MobileNetV3-Large model" → "its three cascade models". |
| **§1.2.3** | Removed "abiotic stress patterns … simulate … biotic disease"; saline-soil kept as a growing-method context only. |
| **§1.3** | Removed "biotic-vs-abiotic stress badge" from the results list. |
| **§1.4 Problem Statement** | Deleted requirement clause "(b) distinguish biotic disease from abiotic stress" (renumbered c→b, d→c). Removed the same clause from "A Successful Solution". |
| **§1.6 Scope** | "specified and optimised for UAE … high temperatures, intense sunlight, salinity" → "intended for deployment in the UAE … where offline operation and Arabic support are essential". |
| **§2.1 intro** | Removed "the academic basis of distinguishing between biotic and abiotic stress"; also corrected the stale §2.8/2.9/2.10 cross-refs to match the real section numbers (2.7–2.12). |
| **§2.2** | "test set that factors in UAE-specialized environmental conditions" → honest field-evaluation methodology. |
| **§2.4** | Removed "augments PlantVillage with UAE-simulation transformations"; reframed to "deployed = minimal aug; heavy field-simulation aug tested and rejected (Ch 7)". Clarified PlantVillage native tomato = 10 classes; tomato20k extends to 11 (adds powdery mildew). |
| **§2.7 Table 2** | Deleted the "UAE-Specific Abiotic Stress Detection ✓" row; replaced with "Honest Lab-to-Field Accuracy Reporting ✓". |
| **§2.7 prose + app reviews** | Removed the abiotic-gap claims from the comparative prose and from the Farmonaut / Flora Incognita / Plantix / Agrio limitation paragraphs (we can't criticise competitors for lacking something we also don't do). Kept offline/Arabic/cost critiques. |
| **§2.12 Research Gaps** | Was "5 gaps" incl. biotic/abiotic (#1) and UAE-abiotic test data (#5). Now **4 gaps**: offline, Arabic, UAE-localised treatment, and the unreported lab-to-field gap. Closing paragraph de-claimed. |
| **§3.6 Sprint 4** | "application of UAE-specific augmentations" → "augmentation comparison (deployed flip-only; heavy field-simulation aug tested and rejected, Ch 7)". |
| **§4.3 NFR-03** | "held-out test set that incorporates UAE-specific environmental conditions" → "held-out laboratory test set, with field accuracy additionally measured (Ch 7)". |
| **§8 Conclusion** | Rewrote the abiotic-heavy opening paragraphs (1–5): removed the abiotic-confusion premise, the "UAE-augmented training", the "test set includes UAE abiotic patterns", and the "biotic/abiotic badge"; kept the (correct) AI-contribution paragraphs. |

## B. Teammate-owned artifacts — minimal fix + **FLAG for your teammate**
These are in the app/design chapters. The abiotic claim was neutralised but the underlying
design element (a `stress_type` field / badge) is your teammate's — they should decide whether to
**keep it as static metadata or remove it entirely**:

| Where | Change | Flag |
|---|---|---|
| **§4.2 FR-07** | "colour-coded biotic or abiotic stress badge" → "severity indicator". | Confirm the app no longer renders a biotic/abiotic badge. |
| **§4.4 DR-02** | Rewritten: the system presents one of 11 trained conditions; abiotic stress is **out of scope** and surfaces a low-confidence warning. "Does not claim to detect abiotic stress." | Confirm with teammate. |
| **§5.4 ERD** | `stress_type` reframed as *static descriptive metadata* (each disease = biotic, healthy = neither), not a learned prediction. "ten tomato leaf types" → "eleven". | Teammate may drop `stress_type` from the ERD/JSON/class diagrams; the diagram **images** still show it. |
| **§3.9 JSON schema** | "stress-type (BIOTIC versus ABIOTIC)" → "a static stress_type label (descriptive metadata)". | — |
| **§5.8** | Removed "biotic/abiotic stress badge" from the inference-layer description. | — |
| **Team roles (§3.2)** | "biotic/abiotic badge component" → "result and severity badge component". | — |
| **List of Figures** | "Figure 2: Visual Similarities Sunscald (Abiotic) vs Early Blight (Biotic)" → "Figure 2: Visual similarity between tomato leaf disease symptoms". | The underlying image should show two similar **diseases**, or be removed. |

## C. Mechanical consistency fixes
- **"ten" → "eleven"**: Abstract, §2.5 ("ten tomato classes"), §5.1.2 ("ten output classes"), §5.4 ERD ("ten tomato leaf types"). (Note: "ten tomato **diseases**" is correct and was kept — there are 10 diseases + 1 healthy = 11 classes.)
- **Single model → cascade**: Abstract, §1.2.2, §8 — corrected to the 3-stage cascade (2× MobileNetV3-Small gates + MobileNetV3-Large classifier, 9.87 MB).
- **Chapter 8 duplicate removed**: three full paragraphs were duplicated verbatim — the second copy was deleted.
- **Chapter 9 renumbered**: list was numbered 5–11 → now **1–7**.
- **Stray empty objective "7."** in §1.5 removed (six objectives, as stated).

## D. Verified, left unchanged (already correct)
- Chapter 7 confusion matrix (11×11) = `eval_deployed.json`, cell-for-cell.
- 97.59% disease / 97.19% e2e / 77.2% field / 0.061 ECE / T=0.5889 / 9.87 MB / n=6,683.
- Lighting-aug 73.4% (−3.8 pts), four domain-gap experiments, composited 65.5% vs 46.8%.
- References [1]–[35] (superset, incl. the corrected `ashishmotwani` dataset citation [35]).

## E. Open items for you (non-blocking)
1. **`project journey.txt` v1 story — RESOLVED (2026-05-28).** Confirmed the real progression: from-scratch **TomatoCareNet** (custom 4-block CNN + SE attention, 91.17%) → single **MobileNetV3-Large + not_tomato reject** (Capstone 1 prototype) → **3-stage cascade** (deployed). Folded into **§1.4** (Problem Statement "The Problem Of") and **§3.8.3** (Cascade Architecture) as a deliberate three-iteration engineering progression — each step a measured response to the previous one's limitation, framed as a project result rather than a sequence of failures. Numbers used: 91.17% (TomatoCareNet held-out); four merged datasets (PlantVillage, PlantDoc, TomatoVillage, supplementary Kaggle tomato set).
2. **Cover page** still says "Capstone Project 1" — confirm that label matches what you are submitting.
3. **TOC section numbers** (Ch 1.2.x and Ch 2.x) drift from the body by one in places. Word regenerates the TOC from heading styles on *Update Field*, which fixes this automatically — no manual edit needed if you update the field in Word.
4. **Student IDs** for all five members are already filled on the cover.
