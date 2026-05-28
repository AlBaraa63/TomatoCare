# TomatoCare — Correspondence / Email Log

**Owner:** AlBaraa AlOlabi (AI/model half of the capstone)
**Last updated:** 2026-05-28
**Purpose:** one place to track every project email — who sent it, to whom, when, what for, and
whether we are still waiting on a reply. This is the **authoritative status** for correspondence;
draft bodies live in `AUDIT_AND_VIVA_PACK.md`.

> Dates marked **(confirm)** are best-effort and should be checked against your sent-mail before
> relying on them. The single source of truth for all numbers quoted in any email is
> `eval_deployed.json` (97.59% disease / 97.19% e2e / 77.2% field / 0.061 ECE / 9.87 MB / n=6,683).

---

## Status legend
- **CLOSED** — replied to / resolved; no action needed.
- **HOLD** — drafted but intentionally not sent (no longer needed, or waiting on a precondition).
- **AWAITING** — sent; waiting on the other party to reply.
- **TODO** — needs to be written/sent by us.

---

## Log

| # | From → To | Date sent | Purpose | Status | Outcome / Next action |
|---|---|---|---|---|---|
| 1 | AlBaraa → **Dr. Yazeed Ghadi** (supervisor, Al Ain University) | ~2026-05-25 (confirm) | Progress update: deployed-model evaluation, lab-vs-field accuracy distinction, confusion-matrix analysis, honest negative experiments, domain-gap conclusion, feedback-flywheel plan. | **CLOSED** | **✅ Replied & APPROVED 2026-05-27.** Endorsed the lab/field distinction, deployed eval, confusion-matrix analysis, honest negative results, domain-gap conclusion, and flywheel; "very good progress." No further action. ⚠ Note: this earlier message quoted **pre-deployment baseline** numbers (97.96% / 0.913·0.920·0.944 / 9.4 MB / n=6,682), since superseded by the corrected report — see row 2. |
| 2 | AlBaraa → **Dr. Yazeed Ghadi** | — (not sent) | Corrected-numbers follow-up: restate the metrics from the deployed cascade (97.59% disease, 97.19% e2e, recall 0.943/0.957/0.980, n=6,683, 9.87 MB, ECE 0.061 test / 0.0046 in-sample, lighting-aug 73.4% / −3.8 pts). | **HOLD** | Supervisor **already approved** (row 1), so this is not queued to send. Draft preserved in `AUDIT_AND_VIVA_PACK.md` → "CORRECTED EMAIL". If ever sent, add the tomato20k dataset citation first. |
| 3 | AlBaraa → **Dr. Armagan Elibol** (Heriot-Watt University Dubai) | 2026-05-25 | GAN-pivot explanation: used DCGAN as *training augmentation* (sounder) rather than a synthetic validation set; clean A/B over 2,503 images + 600 synthetic; result was flat (zero field gain). | **AWAITING** | **No reply yet** as of 2026-05-28. Content checked and qualitatively consistent with the report (no correction needed). **Next:** send a brief follow-up if no reply within a few days. |

---

## Notes
- **Why row 1 quoted different numbers than the report.** The progress email predated the final
  deployed (control) cascade and temperature calibration; its figures are the older from-baseline
  model. The deployed numbers in `eval_deployed.json` and `FINAL_REPORT_REVISED.md` supersede them.
  Because the supervisor approved on 2026-05-27, no correction email is required — the corrected
  draft (row 2) is kept only as a record.
- **If an examiner asks about the email/report number gap:** see `AUDIT_AND_VIVA_PACK.md` → Defense
  Q4 ("the per-class recall in your email differs from your evaluation JSON…").
