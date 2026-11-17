# AI Assistance and Verification Log (Prompt 18)

**Project:** Judging a Reference by How It Looks: How Much Does Surface Form Reveal About Fabricated Citations?
**Student:** Farigh A. Sabri (MCL2026011), IIITA · **Course:** AI Tools for Research, Lab 02
**Period covered:** 4–14 November 2026

---

## 1. Overview of AI Assistance

**Tool.** Claude (Anthropic), used in the Claude app as a research assistant and coding agent. The session was configured for model id `claude-opus-5-5`; the model that served each response is not recorded in the project files. It worked in a sandboxed Linux workspace (Python, shell, GitHub read access). Crossref, OpenAlex, Semantic Scholar and LLM APIs were not reachable from it. From 4 November it could also work in a linked Linux workspace on my laptop and, with my approval, operate VS Code there.

**Scope of AI support (brief §10).** Ideation, literature-to-experiment mapping, code generation, debugging, analysis, visualisation, LaTeX drafting, repository documentation and packaging.

**Starting material.** My review paper, my earlier repository and the official instruction sheet.

The official 18-prompt framework provided the structure for the research workflow. The activities and corresponding outputs are documented prompt-wise below.

**How to read this log.** Each activity separates four kinds of work:

| Label | Meaning |
|---|---|
| **AI-generated** | Code, text or analysis produced by Claude |
| **Human review / decision** | What I decided, corrected, requested or approved |
| **Execution** | Where a run actually happened: Claude's Linux workspace (Python 3.13.18), or my laptop (Windows 11, Python 3.13.2) |
| **Independent verification** | A check against something the AI did not produce: the original HALLMARK script and metric code, earlier commits of the HALLMARK repository, a clean re-run, or a second machine |

Evidence labels follow the brief: **VERIFIED** (checked against a source or a real run), **INFERRED** (plausible, untested), **UNKNOWN** (no evidence).

---

## 2. Prompt-wise Activity Record (Prompts 01–18)

| Prompt | Official objective | AI-generated work | Human role | Execution / verification | Evidence |
|---|---|---|---|---|---|
| 01 | Accountable research workspace | Decision log with VERIFIED / INFERRED / UNKNOWN labels | Supplied the review, earlier repository and instruction sheet | Entries checked against the review text | `research_decisions.md` |
| 02 | Evidence-based research gaps | Four candidate gaps; the human-trust experiment rejected for this lab (needs participants and ethics approval) | Gap kept in the submitted project | Each gap traced to the review | `research_decisions.md` D1–D2 |
| 03 | Literature → executable experiment | Linked Walters & Wilder, Naser and Ding to the HALLMARK benchmark; pathway B with an A (reproduction) component | — | Papers read at source | `research_decisions.md` D1, D3 |
| 04 | Feasibility, novelty, access | Tested hardware and network: all scholarly APIs blocked, GitHub reachable | — | Connection tests run (VERIFIED) | `research_decisions.md` D4 |
| 05 | Questions and success criteria | RQ1–RQ3; H1–H3 with "supported if / contradicted if" | — | Fixed before any project model was scored | `docs/research_brief.md`, `docs/protocol.md` |
| 06 | Datasets and comparators | HALLMARK v1.2.4 (pinned commit) and its Walters & Wilder ChatGPT set | — | Licence read (MIT); every split counted; field sets inspected; checksums recorded | `data/README.md`, `data/SHA256SUMS` |
| 07 | Freeze the blueprint before results | Frozen YAML: splits, metric, threshold rule, seeds, bootstrap | — | Later changes logged as PC1–PC3 | `configs/experiment.yaml`, `docs/protocol.md` |
| 08 | Coding environment | Environment check: versions, determinism, checksums | Ran it on my laptop | Passed on Linux and Windows | `scripts/00_env_check.py`, `results/logs/environment.json` |
| 09 | Vibe-code one module at a time | `data.py`, `features.py`, `models.py`, `metrics.py`; 8 unit tests | — | Tests pass on Linux and Windows | `src/citesurf/`, `tests/test_core.py` |
| 10 | Verify and reproduce the baseline | Port of HALLMARK's surface-feature control | — | Original script run unchanged; predictions identical; metrics equal HALLMARK's official functions to 1e-9; reported numbers reproduced at the authors' commit | `baseline_validation.md`, `scripts/02_validate_baseline.py`, `scripts/02b_reproduce_reported_numbers.sh` |
| 11 | Debug using actual evidence | Fixes for each real error (Section 4) | Reported the Windows errors from my own runs | Each fix re-run; run-1 outputs kept | §4 items 1–2 and 8; `results/logs/superseded/` |
| 12 | Defensible contribution | M1 = one isolated change (three feature groups); M2 text model | — | Same learner and settings as B2 | `research_decisions.md` D7 |
| 13 | Evaluate real outputs only | Input checks (lengths, NaN, label set, unique keys), AUROC with bootstrap CIs, per-type, ablation, format equalisation | — | Every paper number traced to a CSV | `src/citesurf/metrics.py`, `scripts/03_run_experiments.py`, `results/tables/` |
| 14 | Interpret, including negatives | Negative transfer reported; DOI-prefix gain labelled a benchmark artefact; exploratory analyses labelled | — | Exploratory refit (X1) and paired bootstrap (X2) | `scripts/03b_exploratory.py`, `research_decisions.md` D9 |
| 15 | Evidence-grounded LaTeX manuscript | ACM draft written from the result tables | Updated after my laptop run and my revised review | Claims checked against tables before compiling (§4 item 6) | `paper/` |
| 16 | Technical peer review | Major/minor concerns with remedies | — | Remedies checked in the paper text | `docs/self_review.md` |
| 17 | Reproducible GitHub documentation | README, `run_all.sh`, demo notebook; repository upload plan | Approved the upload plan with three conditions; chose ATR naming | Clean-room and end-to-end re-runs (§3 G); upload status in §3 H | `README.md`, `scripts/run_all.sh`, `notebooks/walkthrough.ipynb` |
| 18 | Audit the human–AI collaboration | This log | Defined its structure and its honesty requirements | Entries limited to recorded events | `ai_assistance_log.md` |

---

## 3. Significant AI-Assisted Activities

**A. Research gap and question (Prompts 02–05)**
- *AI proposal:* study the computational counterpart of the review's human-trust gap: how much the surface of a reference reveals about fabrication. The human experiment was set aside because it needs participants.
- *Human decision:* the direction was retained in the submitted project. No separate approval step for it is recorded.
- *Verification:* feasibility checked by real connection tests; the gap traced to the review text.
- *Outcome:* `research_decisions.md` D1–D4, `docs/research_brief.md`.

**B. Data and leakage audit (Prompt 06)**
- *AI proposal:* HALLMARK v1.2.4 plus its Walters & Wilder ChatGPT set (real and fake citations share one generator and one format).
- *Execution:* fetched at a pinned commit; checksums recorded.
- *Verification:* 0 shared keys between dev and test, 1 shared title out of 831, 0 overlap with W&W; label-bearing fields removed by the loader.
- *Outcome:* `data/README.md`, `data/SHA256SUMS`, `scripts/fetch_data.sh`.

**C. Baseline reproduction (Prompts 09–10)**
- *AI proposal:* reuse HALLMARK's own shortcut-control script as the baseline.
- *Execution:* original script run unchanged, then at three commits of the HALLMARK history.
- *Independent verification:* my port gives identical predictions; metrics match HALLMARK's official code; the published 0.468 / 0.388 reproduce exactly before data commit `908a405`, and 0.456 / 0.440 after it.
- *Outcome:* `baseline_validation.md`.

**D. Frozen protocol and experiments (Prompts 07, 12–13)**
- *AI proposal:* frozen config; B0–B2 baselines, M1 (one isolated change) and M2; AUROC with bootstrap CIs; five deeper analyses.
- *Execution:* run 1 and run 2 in Claude's workspace; three protocol changes logged (PC1–PC3).
- *Code/result change:* B0 score and a reference-point flag corrected after run 1; only B0 moved (0.487 → 0.500).
- *Outcome:* `results/tables/`, `results/predictions/`, `results/logs/`.

**E. Interpretation (Prompt 14)**
- *AI proposal:* report the transfer failure as a finding; treat the DOI-prefix gain as a benchmark artefact; label analyses decided after results as exploratory.
- *Verification:* exploratory refit without DOI-prefix features (fabricated-DOI detection 0.83 → 0.31; AUROC 0.797 → 0.784).
- *Outcome:* `research_decisions.md` D9, paper Sections 6–7.

**F. Manuscript (Prompt 15)**
- *AI-generated:* ACM paper written from the result tables.
- *Human-driven changes:* numbers updated to my laptop run; framing updated to match my revised review paper.
- *Verification:* every quoted number compared with the tables by script; three overstated claims corrected before compiling (§4 item 6).
- *Outcome:* `paper/main.tex`, `paper/Final_Paper.pdf`.

**G. Reproducibility runs (Prompts 08, 17)**

| Date | Where | Started by | Result | Record |
|---|---|---|---|---|
| 4 Nov | Claude's Linux workspace (Python 3.13.18), fresh copy without data or results | Claude | `run_all.sh` completed in 4 min 53 s; 8 tests passed; baseline identical to the original script. The session's table-by-table comparison found all 12 tables identical. | `results/logs/cleanroom_rerun.log` |
| 4 Nov, about 15:07–15:15 IST | My laptop, Git Bash (Windows 11, Python 3.13.2) | Me | Three Windows errors found (§4 item 8; reported by me in the session, not saved as log files); after the fixes the pipeline completed (experiment step 284 s). **These are the reported results.** | `results/logs/environment.json`, `02_validate_baseline.log`, `03_run_experiments.log`, `03b_exploratory.log` |
| 14 Nov | My laptop, submission zip unpacked into a fresh test folder | Claude, on my laptop with my approval | Reported in the session: all steps passed; all 12 tables identical to the submitted ones (largest difference 0.0); notebook rebuilt (live M1 AUROC 0.797) | Not retained in project files: its log (`zip_check_log.txt`) was in the temporary test folder, which was later deleted |

**H. Repository preparation (Prompt 17), status on 14 November 2026**
- *Upload plan (AI-generated):* proposed directory tree; lists of files to add, update and exclude; conflicts and missing items.
- *Approval (human):* I approved the plan with three conditions: remove the `data_bundle.zip` reference from `data/README.md`; use my configured git identity rather than a guessed email; the Claude commit trailer is optional.
- *Checks performed:* the project was scanned for keys, tokens, emails and local paths (none found except Claude's workspace path inside `results/logs/cleanroom_rerun.log`, kept as a run record).
- *Local changes actually made (14 Nov, project folder only):*
  - `data/README.md` and `scripts/fetch_data.sh`: `data_bundle.zip` references replaced by the pinned-download procedure.
  - `LICENSE`: GitHub's existing MIT text kept, with a HALLMARK third-party notice appended.
  - `.gitignore`: local-only entries added (`.vscode/`, `.ipynb_checkpoints/`, `.env`, `Thumbs.db`, `.DS_Store`).
  - These changes postdate the submission zip and are not in it.
- *GitHub push:* **not performed as of this log.** No git repository has been initialised in the project folder, and the GitHub branch `lab2-citation-surface` has not been created. Claude had no GitHub write access; the planned method is to push from my own Git Bash with my configured identity.

---

## 4. AI Limitations, Manual Corrections and Verification

All items are real events from this project.

1. **AI bug in a baseline (caught by a sanity check).** Claude's first majority-class baseline used the training prevalence as its score. In pooled grouped cross-validation on the W&W set this gave AUROC 0.487, which is impossible for a constant predictor. Cause: a different constant per fold. Fixed to a constant 0.5; diffed the two runs to confirm nothing else moved. Logged as PC1.
2. **AI misread a data field.** Claude flagged all eight released LLM verifiers as "used lookups" because `api_sources_queried` was non-empty. Inspection showed it holds only the model endpoint (e.g. `openrouter/google/gemini-2.5-pro`). Corrected (PC2). This mattered for the argument: these runs are genuine "reader without lookup" comparators.
3. **The AI's extension partly exploited a benchmark artefact.** Claude's M1 feature set included DOI-prefix length, and M1 jumped from 0.14 to 0.83 detection on `fabricated_doi`. The actual DOIs showed that HALLMARK's generator uses unregistered prefixes such as `10.7777x` and `10.9999x`. An exploratory refit without those features dropped the rate to 0.31. Reported as an artefact, not as a detection skill (PC3, X1).
4. **An inference that was then verified.** The reproduced baseline gave DR 0.456 / 0.440 instead of the reported 0.468 / 0.388. Claude's first explanation (the v1.2.4 relabel) was only a guess; it was then checked by running the original script at three commits. The reported numbers reproduce exactly before commit `908a405` and change after it.
5. **Errors from earlier stages of this course, caught by verification.** (a) The AI-drafted original paper said the 46% fabrication rate in Linardon et al. came from body dysmorphic disorder; the source table shows it was binge eating disorder (specialised prompts). (b) While regenerating my review paper, Claude changed the paper's title without being asked; I caught this and had it restored.
6. **AI overstatements in the paper draft, caught before compiling.** Checking every claim against the result tables found three: (a) a statement that author-name and title-style features carried the W&W cross-validation signal, which no analysis had tested (removed); (b) "about a quarter" of M1's margin attributed to field presence, when the tables give 0.049 of 0.297, about a sixth (corrected); (c) a misdescription of how the HALLMARK authors explained their venue-length feature (corrected).
7. **Font problem.** The ACM Libertine fonts are not installed in the workspace. The local PDF is built with XeLaTeX and the Libertinus fonts (the maintained fork of Linux Libertine); `paper/main.tex` itself is the unmodified pdfLaTeX/acmart source that Overleaf compiles.
8. **Problems found only when I ran it on my own Windows laptop.** None of these appeared in Claude's Linux test runs; they were found because I executed the pipeline myself.
   - (a) `git clone` of HALLMARK failed with "Connection was reset". Claude added an offline data bundle and made `fetch_data.sh` skip the download when checksums match. The bundle is not part of the repository; the pinned download is the supported method.
   - (b) `run_all.sh` picked `python3`, which on my laptop is a different Python from the one `pip` installed into (`ModuleNotFoundError: numpy`). Fixed by selecting whichever Python can import numpy and scikit-learn.
   - (c) The HALLMARK script crashed because Windows Python reads files as cp1252 and the data is UTF-8. Fixed by running it with `-X utf8` (script unchanged) and opening every file as UTF-8 in my code.
9. **Results differ slightly between Windows and Linux.** My laptop run matched the Linux run to within 0.001 AUROC; one reported value changed in the third decimal (0.680 → 0.679). The paper reports my laptop's numbers and states the cross-platform difference.
10. **A stray file in the submission zip.** Claude's first zip attempt on my laptop failed partway and left a 1.7 MB partial file (`ziffviqW`) in the project folder, which the next zip included. It was noticed in VS Code's file list and moved to `data/external/_stray_partial_zip`; the file's timestamp is 4 November. It is still inside the project folder, but `data/external/` is excluded from the submission zip and listed in `.gitignore`, so it is not part of the submitted or uploaded contents. The zip was then rebuilt without it. The final submission zip (`ATR_Lab02_MCL2026011_CitationSurface.zip`, built 14 November) has 173 entries and is 1,718,135 bytes; it passes an integrity test and contains no file from `data/external/`.
11. **Review paper updated after Lab 2 was built.** I revised my review paper (new title, five-part taxonomy, factorial design in its Section 9.1). Claude checked the Lab 2 project against the updated review: code, data and results were unaffected. The review's title and three descriptive sentences in the Lab 2 paper, README, brief and decision log were updated to match it, and Naser (2026) is now marked as found during Lab 2 rather than cited in the review.

---

## 5. Decisions Requiring Human Judgement

**Decisions I made:**
- Staying inside the topic of my own review (the lab requires continuity), and supplying the review, earlier repository and instruction sheet as the starting evidence.
- Deciding my review paper's title myself: when Claude changed it without being asked during the review-paper stage, I corrected it.
- Running the full pipeline on my own laptop, and reporting that run as the official one.
- Revising my review paper, then asking for the Lab 2 project to be checked against the new version.
- Requesting an end-to-end check of the final submission zip on my laptop.
- Using **ATR** naming for the project, zip and repository.
- Choosing my own GitHub repository (`farigh-ahmad-sabri/ATR_Lab2_Project`) as the upload target, and approving the upload plan with three conditions (§3 H). The push itself had not been made at the time of this log.

**Proposed by Claude and kept in the submitted project:**
- Testing the computational counterpart of the review's human-trust gap, because a participant study was not possible in this lab.
- Using the Walters & Wilder ChatGPT set as the external test, because real and fake references there share one generator and format.
- Reporting the negative transfer result as it is, rather than tuning until something transfers.
- Presenting the DOI-prefix gain as a weakness of the benchmark, not a strength of M1.

---

## 6. Lessons Learned

- Code that runs is not code that is right: two of the three real bugs in Section 4 produced plausible-looking numbers.
- Asking the AI to write down hypotheses and thresholds before results made the later "this looks too good" check possible.
- Per-type tables were where both the artefact and the generator bias became visible; overall AUROC hid them.
- Tests passing on one machine are not enough: three bugs appeared only when I ran the pipeline on my own Windows laptop.
- AI-written prose needs the same checking as AI-written code: three claims in the paper draft went beyond what the tables showed.
- Packaging is part of the work: a leftover temporary file reached the submission zip and was only caught by looking at the folder.

---

## 7. Remaining Risks and Limitations

- The W&W set is small (341); its CIs are wide.
- HALLMARK labels have been corrected several times; another release may move the numbers slightly.
- Released LLM and bibtex-updater outputs were produced by other people under conditions I cannot inspect.
- Gradient-boosting results differ slightly between operating systems (up to 0.0008 in summary AUROC); the reported numbers are from Windows.
- Reproduction depends on downloading HALLMARK from GitHub at a pinned commit; unstable connections can interrupt it (seen on my laptop).
- `results/logs/cleanroom_rerun.log` records the original AITR folder name and Claude's workspace path; it is kept unchanged as a run record.
