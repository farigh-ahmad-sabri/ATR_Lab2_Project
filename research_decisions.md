# Research decisions log (literature → experiment)

Evidence labels: **VERIFIED** (checked in the original source or by running code),
**INFERRED** (plausible, needs testing), **UNKNOWN** (no evidence available).
All dates 2026-11-04 unless stated. Work was done with Claude (Anthropic) as an AI
research assistant; see `ai_assistance_log.md` for who did what.

## D1 Starting point: what the review left open
- My review (*Citation Formatting, Fabricated References, and Human Trust in AI-Assisted Scholarly Writing: An Interdisciplinary Review*, updated November 2026) concluded that the direct human test, varying citation format while holding existence and relevance fixed, has not been done, and proposed a factorial experiment for it (its Section 9.1). **VERIFIED** against the updated review text.
- Ding et al. (AAAI 2025) varied presence/relevance, not format. **VERIFIED** (re-read for the review).
- Walters & Wilder (2023): fabricated ChatGPT references followed APA conventions closely. **VERIFIED**.
- Naser (2026, arXiv:2603.03299): a classifier on bibliographic string features alone reached AUC 0.876 (CV) / 0.834 (leave-one-model-out). **VERIFIED** from the paper text; his code and data are **UNKNOWN** (not released). Not cited in the review; found during the Lab 2 literature search.

## D2 Candidate gaps considered (Prompt 02)
| Gap | Testable here? | Decision |
|---|---|---|
| G-a Does citation format raise human trust? (review's main gap) | No: needs participants and ethics approval, and is not feasible in a lab week | Rejected for this lab; kept as future work |
| G-b How much information does the *surface form* of a reference carry about fabrication? (computational counterpart of G-a) | Yes, with a labelled benchmark | **Selected** |
| G-c Do lookup-based verifiers miss "compound" fakes (Ansari 2026)? | Needs Crossref/OpenAlex access | Rejected: APIs unreachable from my environment (D4) |
| G-d Prompt constraints vs hallucination type (Davis & Mahmoud 2026) | Needs LLM API calls | Rejected: no API key/budget |

Why G-b connects to the review: if fabricated references can be told apart from
real ones by how they look, then a reader's reliance on format is partly
justified; if they cannot, it is miscalibrated (the review's Section 6 argument).
**INFERRED** link; it does not measure human trust, and the paper says so.

## D3 Dataset (Prompts 04, 06)
- HALLMARK v1.2.4, MIT licence, GitHub `rpatrik96/hallmark`, pinned commit `c62d296`. Official splits dev_public 1,119 / test_public 831. **VERIFIED** (cloned, licence read, counts checked).
- External set `supplement_chatgpt_citations`: 341 ChatGPT journal citations from Walters & Wilder's supplement, human-coded; 172 VALID / 169 HALLUCINATED. Real and fake share one generator and the same four fields. **VERIFIED** (inspected every field set).
- Leakage: 0 shared keys dev/test, 1 shared title; 0 W&W titles in HALLMARK. **VERIFIED** (`scripts/02_validate_baseline.py`).
- Known benchmark limitation: HALLMARK VALID entries are scraped from DBLP while most hallucinated entries are generated, so surface cues may encode provenance. **VERIFIED** from HALLMARK's own notes (their four-mode shortcut control). This is why the W&W set is used.

## D4 Feasibility
- Hardware: 2 CPU cores, 7 GB RAM. Full pipeline runs in about 4 minutes. **VERIFIED**.
- Network: Crossref, OpenAlex, Semantic Scholar, arXiv, DBLP and Hugging Face all failed to connect from the workspace; GitHub works. **VERIFIED** (curl test). Consequence: no lookup-based tool can be rerun; released per-entry outputs are used as attributed reference points instead.

## D5 Baseline (Prompts 09, 10)
- Chosen: HALLMARK's surface-feature shortcut control (gradient boosting, 24 features). Reproduced exactly at the commit that reported it; difference on v1.2.4 explained by one data-correction commit. **VERIFIED**; see `baseline_validation.md`.

## D6 Research questions and hypotheses (Prompt 05) — frozen before results
See `docs/protocol.md`. H1 surface signal exists on HALLMARK and concentrates in Tier 1; H2 no transfer to W&W; H3 within-W&W grouped CV below 0.80 (Naser 0.876).

## D7 Comparators (Prompt 12)
- B0 majority, B1 completeness rule ("format-trusting reader"), B2 reproduced HALLMARK GBM.
- M1 = B2 with **one isolated change**: three added feature groups (author style, title style, identifier consistency). Same learner and hyper-parameters.
- M2 = character n-gram TF-IDF + logistic regression on the rendered reference (closest available analogue of a string-only classifier).
- Reference points (not rerun): eight zero-shot LLM verifiers on test_public; bibtex-updater 1.4.0 on W&W. Checked that LLM runs made no bibliographic lookups (their `api_sources_queried` lists only the model endpoint).

## D8 Primary metric
AUROC, because DR alone hides false positives and the classes are imbalanced (524 vs 307 on test). Threshold for DR/FPR fixed on dev CV at FPR ≈ 0.10.

## Protocol changes (after freezing)
| # | Change | Reason | Results seen? |
|---|---|---|---|
| PC1 | B0 score changed from training prevalence to constant 0.5 | Run 1 gave B0 AUROC 0.487 in pooled grouped CV: each fold's constant differed, so pooling created a spurious ranking. A majority classifier must sit at 0.5. | Yes (run 1). Only B0 changed; all other numbers identical between runs (checked by diff). Run-1 logs kept in `results/logs/superseded/`. |
| PC2 | Reference-point flag `used_lookups` corrected | Run 1 marked every LLM reader as using lookups because the field contains the model endpoint. Fixed to count only non-model sources. | Yes. No metric changed. |
| PC3 | Added `scripts/03b_exploratory.py` (X1 DOI-prefix removal, X2 paired bootstrap) | X1: run-2 per-type table showed M1 detecting fabricated_doi at 0.83 vs B2 0.14; inspection showed HALLMARK's fake DOIs use unregistered 5-digit prefixes. X2: to quantify M1 vs B2/M2. | Yes; both are labelled **exploratory** everywhere. |

## D9 Interpretation decisions
- W&W transfer: AUROC 0.51–0.55 for all learned models, CIs include 0.5 → H2 supported. Thresholds from HALLMARK give FPR 0.98 on W&W for M1, i.e. the decision rule collapses. **VERIFIED** from results.
- Within-W&W grouped CV: M1 0.679 [0.633, 0.744] (Windows run; 0.680 on Linux) → signal exists but below 0.80 → H3 supported; I do **not** claim this refutes Naser, because his corpus, features and CV scheme differ (**UNKNOWN** details).
- M1 on HALLMARK: 0.797 [0.765, 0.825]; Tier-1 DR 0.805 vs Tier-3 0.482 → H1 supported. Exploratory X1 shows most of the fabricated_doi gain comes from generator DOI prefixes; I report this as a benchmark artefact, not as a detection ability.
- Completeness (B1) carries almost no signal anywhere (AUROC 0.515 on test; 0.500 on W&W where every entry has the same four fields). This is the result most directly tied to the review.

## Status at submission
1. Full pipeline re-run on my own laptop (Windows 11, Python 3.13.2) on 2026-11-04; that run is the one reported. Linux and Windows results agree to within 0.001 AUROC (see `baseline_validation.md`).
2. Three Windows-only problems found and fixed during that run (offline data bundle, Python selection, UTF-8 file reading); logged in `ai_assistance_log.md` item 7.
3. Repository: https://github.com/farigh-ahmad-sabri/ATR_Lab2_Project
