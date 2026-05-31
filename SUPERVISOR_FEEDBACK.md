# Supervisor Feedback — Dr. Yazeed Ghadi (2026-05-30)

Reply to AlBaraa's progress-update #2 (see `EMAIL_LOG.md` rows 4–5). Preserved
verbatim below, followed by an **action ledger** mapping each point to its status.
The planning prompt for a Claude.ai (Opus 4.8) session is in
`OPUS_FEEDBACK_PLAN_PROMPT.md`.

> **Single source of truth for any number quoted while acting on this:**
> `eval_deployed.json` (97.59% disease / 97.19% e2e / 77.2% field / 0.061 ECE /
> 9.87 MB / n=6,683). Never revive the cut "UAE-simulation / abiotic" claim.

---

## Verbatim feedback

> Thank you Albara. I have checked it thoroughly. Overall, the project is strong, but to raise it to a higher capstone quality, I suggest these improvements:
>
> **Abstract**
> - Add one final sentence clearly stating the main limitation: field accuracy is still lower than lab accuracy.
> - Avoid saying "without compromising diagnostic accuracy" because field accuracy is 77.2%, so wording should be more careful.
>
> **Chapter 1**
> - Problem statement is strong, but too long. Shorten the table and keep only the real problem, root cause, impact, and solution.
> - Add a small paragraph explaining why tomato was selected specifically, not other crops.
>
> **Chapter 2**
> - Some competitor claims need stronger references, especially accuracy, Arabic support, and offline capability.
> - Add a clearer critical comparison: not only what competitors lack, but why TomatoCare is technically better.
>
> **Chapter 3**
> - Add more detail on dataset split: training, validation, testing percentages.
> - Clearly state whether any images from the same source/plant could appear in both train and test sets.
> - Add ethical handling of user feedback images.
>
> **Chapter 4**
> - Requirements need clearer IDs, for example FR-01, NFR-01, DR-01.
> - Each requirement should have verification method: test, inspection, demo, or measurement.
> - Add accessibility requirements: font size, Arabic readability, color contrast.
>
> **Chapter 5**
> - UML diagrams should be checked for consistency with the actual app.
> - Add a short explanation under each diagram. Do not leave figures to speak for themselves.
> - The ERD may be confusing because the app uses JSON, not a relational database. Rename it as "Data Model Diagram" unless there is an actual database.
>
> **Chapter 6**
> - This is currently the weakest chapter. It needs screenshots of the final app, code-level explanation, folder structure, main components, and implementation challenges.
> - Add the CI/GitHub Actions details here.
> - Add the 42 unit tests summary here or cross-reference Chapter 7.
>
> **Chapter 7**
> - Excellent honesty in reporting the lab-to-field gap.
> - Add lower-end device testing before submission. Samsung S10+ alone is not enough for the "low-end device" claim.
> - Add a table for device performance: device, RAM, Android version, median latency, max latency.
> - Add usability testing with at least 5 users if possible.
> - Add evidence for the fixed bugs: gallery crash, health-rate issue, language/theme switching.
>
> **Conclusion and Future Work**
> - Future work should be more practical: larger UAE field dataset, lower-end device testing, expert agronomist validation, continuous retraining pipeline.
> - Clearly state that the system is advisory, not a replacement for professional diagnosis.
>
> **Formatting and language**
> - Fix spacing issues such as missing commas and awkward phrases.
> - Some paragraphs are too dense; split them.
> - Ensure all figure captions follow the same style.
> - Make sure references are complete and consistently formatted.
>
> The report is promising and technically strong, especially the cascade model, calibration, bilingual offline design, and honest field evaluation. However, before final submission, you must strengthen Chapter 6, add lower-end device evidence, improve requirement traceability, and provide clearer testing evidence for the application features.

---

## Action ledger

Status tags: **DONE** · **QUICK FIX** (wording) · **NEW WRITING** · **NEW WORK** (build/measure) · **DIAGRAM** (redraw). Owner: AlBaraa (AI/report) · App teammate · Diagrams.

| # | Feedback item | Status | Owner | Notes / where |
|---|---|---|---|---|
| Abstract-1 | State field<lab limitation | NEW WRITING | AlBaraa | one sentence in Abstract |
| Abstract-2 | Soften "without compromising accuracy" | QUICK FIX | AlBaraa | field = 77.2% |
| Ch1-1 | Shorten problem-statement table | QUICK FIX | AlBaraa | keep problem/root-cause/impact/solution |
| Ch1-2 | Why tomato (not other crops) | NEW WRITING | AlBaraa | short paragraph |
| Ch2-1 | Stronger competitor references | RESEARCH + WRITING | AlBaraa | accuracy/Arabic/offline citations |
| Ch2-2 | Critical "why we're technically better" | NEW WRITING | AlBaraa | beyond "what they lack" |
| Ch3-1 | Dataset split % | NEW WRITING | AlBaraa | 70/15/15 per `training_config.yaml` |
| Ch3-2 | Same-source train/test leakage statement | NEW WRITING | AlBaraa | state group-aware handling |
| Ch3-3 | Ethical handling of feedback images | RESEARCH + WRITING | AlBaraa | consent, on-device, UAE PDPL 45/2021 |
| Ch4-1 | Requirement IDs (FR/NFR/DR) | **DONE** | AlBaraa | §4.2–4.4 already use FR-01..20 / NFR-01..10 / DR-01..07 |
| Ch4-2 | Verification method per requirement | **DONE** | AlBaraa | **Appendix B** traceability matrix |
| Ch4-3 | Accessibility requirements | NEW WORK | AlBaraa | font scaling, Arabic readability, WCAG contrast + verification |
| Ch5-1 | UML consistency with the app | **DIAGRAM** | Diagrams | Figures 9–17 stale — redraw to shipped app |
| Ch5-2 | Explanation under each diagram | NEW WRITING | AlBaraa/teammate | one paragraph per figure |
| Ch5-3 | ERD → "Data Model Diagram" | QUICK FIX + DIAGRAM | Diagrams | app is JSON, not relational |
| Ch6-1 | Strengthen Ch6 (screenshots, structure, components, challenges) | NEW WRITING (assemble) | AlBaraa + teammate | material exists in `docs/android-app.md`, `meseremnts/`, Fig 6.2 |
| Ch6-2 | Add CI/GitHub Actions details | **DONE** (relocate) | AlBaraa | exists in §7.9 — cross-ref/move to Ch6 |
| Ch6-3 | Unit-tests summary in Ch6 | **DONE** (cross-ref) | AlBaraa | 48 tests in §7.9 / Table 7.5 |
| Ch7-1 | Honesty praised | — | — | no action |
| Ch7-2 | Low-end device test | NEW WORK | AlBaraa | run on ≈API 26 / 2 GB device |
| Ch7-3 | Device-performance table | PARTIAL | AlBaraa | Table 7.6 has S10+; add rows + columns (RAM, Android, median, max) |
| Ch7-4 | Usability test (≥5 users) | NEW WORK | AlBaraa + teammate | tasks, metrics, consent |
| Ch7-5 | Evidence for fixed bugs | NEW WRITING | AlBaraa | before/after + tests (`HomeStatsTest`, decode fix); screenshots |
| Concl-1 | Practical future work | QUICK FIX | AlBaraa | field dataset, low-end, agronomist validation, retraining |
| Concl-2 | Advisory-not-replacement statement | QUICK FIX | AlBaraa | exists as DR-04; make explicit in conclusion |
| Fmt-1 | Spacing / awkward phrasing | COPY-EDIT | AlBaraa | full pass |
| Fmt-2 | Split dense paragraphs | COPY-EDIT | AlBaraa | — |
| Fmt-3 | Consistent figure captions | COPY-EDIT | AlBaraa | one caption style |
| Fmt-4 | Complete + consistent references | COPY-EDIT | AlBaraa | IEEE style |

> Reminder: every Markdown change must also be applied by hand to the mirrored Word `.docx`.


