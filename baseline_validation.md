# Baseline validation report (Gate G2, Prompt 10)

**Baseline:** HALLMARK's surface-feature shortcut control
(`scripts/shortcut_control_four_modes.py` in `rpatrik96/hallmark`, MIT licence).
It trains a gradient-boosting classifier on 24 features that can be read off a
BibTeX entry without any lookup, and reports the detection rate (DR) for four
"real-paper" hallucination types against VALID entries, using 5-fold stratified
CV (`random_state=0`).

**Why this baseline:** it is the only published, runnable surface-only detector
on a benchmark with ground truth that I could access from this environment, and
it is the closest available implementation of the string-only idea that Naser
(2026) reports (his code and data are not released). Logs:
`results/logs/02_validate_baseline.log`, `results/logs/02b_reproduce_reported_numbers.log`,
`results/logs/baseline_validation.json`.

## Checks

| # | Check | Result | Status |
|---|---|---|---|
| 1 | Original script runs unchanged on v1.2.4 (pinned commit `c62d296`) | dev DR 0.456 / FPR 0.040; test DR 0.440 / FPR 0.107 | VERIFIED |
| 2 | My port (`src/citesurf/features.py::hallmark_features` + my loader) gives the same CV predictions | identical DR and FPR on both splits (asserted in code) | VERIFIED |
| 3 | My metric code agrees with HALLMARK's official `hallmark.evaluation.metrics` (`evaluate`, `auroc`) on the same predictions | DR, FPR and AUROC equal to 1e-9 | VERIFIED |
| 4 | Reported numbers (README: dev 0.468, test 0.388) reproduce | exactly, at commit `fa0cc7b` (2026-09-04, where they were written) and at `908a405~1` | VERIFIED |
| 5 | Cause of the difference between (1) and (4) | v1.2.4 data correction, commit `908a405` (2026-10-15): 18 entries reverted VALID→HALLUCINATED, 13 truncated fields restored. Counts change 158/513 → 160/504 (dev) and 139/312 → 141/307 (test). Running the script before and after this one commit reproduces both sets of numbers. | VERIFIED |
| 6 | Leakage: shared keys / titles between dev and test | 0 keys; 1 title (a hallucinated entry) out of 831 | VERIFIED, negligible |
| 7 | Leakage: W&W external set vs HALLMARK splits | 0 shared titles | VERIFIED |
| 8 | Label-bearing fields hidden from detectors (`label`, `hallucination_type`, `subtests`, `explanation`, `generation_method`, `source`, …) | loader keeps only `bibtex_type` and `fields` (`src/citesurf/data.py::visible`) | VERIFIED by code inspection + unit test |

## Deviations from the original baseline in the main study (deliberate)

| Deviation | Reason | Effect on comparability |
|---|---|---|
| Positives = **all 14** hallucination types, not only the four real-paper modes | The research question is about fabrication in general | B2 numbers in the main tables are not comparable to the 0.456/0.440 above; those are reported only for validation |
| Train on `dev_public`, evaluate once on held-out `test_public` (instead of CV within each split) | Prevents tuning on the evaluation data | Standard train/test protocol |
| Primary metric AUROC (+ DR/FPR at a dev-chosen threshold) instead of DR at the default 0.5 cut-off | DR alone hides the false-positive cost; a threshold chosen on dev keeps FPR comparable across models | Thresholds are frozen before test scoring |

## Uncertain / not verifiable here

| Item | Status |
|---|---|
| Naser (2026) string-only classifier (AUC 0.876) | UNKNOWN code/data; compared only as a published number |
| Released LLM-reader and bibtex-updater outputs | Produced by the HALLMARK authors at earlier dates; I re-score their per-entry outputs against v1.2.4 labels but cannot rerun them (no API access from this workspace). Treated as attributed reference points, not baselines I validated. |
| Lookup-based tools on `test_public` | Not rerun: Crossref/OpenAlex/Semantic Scholar are unreachable from the workspace (all returned connection failures on 2026-11-04). |

## Needs correction
None outstanding. The baseline is preserved unchanged in `data/external/hallmark/scripts/`; my reimplementation is tested for identical output.

Clean-room check (2026-11-04): fresh copy without data/ or results/, `bash scripts/run_all.sh`, 4 min 53 s; all 12 result tables identical to the submitted ones (|diff| < 1e-9). Log: `results/logs/cleanroom_rerun.log`.

Cross-platform check (2026-11-04): the full pipeline was then run on the student's laptop (Windows 11, Python 3.13.2, same library versions). Tables without gradient boosting (reference points, false-positive/miss lists, feature importances) are identical. Gradient-boosting results differ by at most 0.0008 in any summary AUROC and 0.004 in any single per-seed ablation value; at three decimals only M1's W&W grouped-CV result changes (0.680 → 0.679, CI [0.634, 0.745] → [0.633, 0.744]). Cause: INFERRED floating-point differences between platforms affecting near-tied splits; not investigated further. The laptop run is the one reported in the paper.
