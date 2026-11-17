# Judging a reference by how it looks

**ATR Lab 02 · Farigh A. Sabri (MCL2026011), IIITA**

How much does the *surface form* of a citation (which fields it has, how its
authors, title and identifiers are written) reveal about whether it is
fabricated, when nothing is looked up?

This continues my review *Citation Formatting, Fabricated References, and Human Trust in AI-Assisted Scholarly Writing: An Interdisciplinary Review*,
which asked whether a more elaborate citation format raises readers' trust and
found no study that isolates format. Its argument assumes that format carries no
information about whether a reference exists; this project tests that premise. The
human experiment needs participants. This project measures the computational
upper bound: what an idealised reader who notices every visible cue could know.

## Research questions
- **RQ1** On the HALLMARK benchmark, how well do surface-only detectors separate fabricated from real references, and for which error types?
- **RQ2** Does that survive on ChatGPT citations where real and fake share a generator and a format (Walters & Wilder 2023, human-coded)?
- **RQ3** Which cues carry the signal, and what remains when formatting is equalised?

## Main results (from `results/tables/`)
| AUROC [95% CI] | HALLMARK test | HALLMARK test, format equalised | W&W, transfer | W&W, grouped CV |
|---|---|---|---|---|
| B1 completeness rule | 0.515 [0.480, 0.550] | 0.512 | 0.500 | 0.500 |
| B2 HALLMARK surface GBM (reproduced) | 0.764 [0.732, 0.797] | 0.721 | 0.546 | 0.592 |
| M1 extended surface GBM | **0.797** [0.765, 0.825] | **0.748** | 0.549 | **0.679** [0.633, 0.744] |
| M2 char n-gram LR | 0.788 [0.755, 0.819] | 0.746 | 0.525 | 0.629 |
| Reference: 8 zero-shot LLM readers | 0.589–0.778 | | | |
| Reference: bibtex-updater (database lookup) | | | 0.957 [0.934, 0.977] | |

In short: completeness carries no signal. Richer surface cues work on the
synthetic benchmark, mostly for crude Tier-1 errors and partly through benchmark
artefacts. They fall to chance on the human-coded ChatGPT set when trained
elsewhere, and reach only 0.68 when trained on it. Details are in
`paper/Final_Paper.pdf`.

## Reproduce
Requirements: Python ≥ 3.11 (tested on 3.13.18), git, about 5 minutes on 2 CPU cores, no GPU, no API keys.

```bash
git clone https://github.com/farigh-ahmad-sabri/ATR_Lab2_Project.git && cd ATR_Lab2_Project
python -m pip install -r requirements.txt   # use python3 on Linux/macOS
bash scripts/run_all.sh
```

`run_all.sh` runs these steps, each of which was executed for the submitted results:

| Step | Command | Output |
|---|---|---|
| Data at pinned commit + checksums | `bash scripts/fetch_data.sh` | `data/raw/` |
| Environment test | `python3 scripts/00_env_check.py` | `results/logs/environment.json` |
| Unit tests | `python3 -m pytest -q tests` | 8 passed |
| Baseline validation | `python3 scripts/02_validate_baseline.py` | `results/logs/baseline_validation.json` |
| Reported-number reproduction across commits | `bash scripts/02b_reproduce_reported_numbers.sh` | `results/logs/02b_reproduce_reported_numbers.log` (not in run_all; needs full git history) |
| Main experiments (E1–E4, ablation, reference points) | `python3 scripts/03_run_experiments.py` | `results/tables/*.csv`, `results/predictions/*.csv` |
| Exploratory analyses (labelled as such) | `python3 scripts/03b_exploratory.py` | `results/tables/exploratory_*.csv` |
| Figures | `python3 scripts/04_make_figures.py` | `results/figures/`, `paper/figures/` |
| Demo notebook (executed) | `python3 scripts/05_build_notebook.py` | `notebooks/walkthrough.ipynb` |

Google Colab: `!git clone …`, `%cd …`, `!bash scripts/run_all.sh` **[TEST REQUIRED]**. This has not been run on Colab; Colab's preinstalled package versions differ from `requirements.txt`, so results may differ in the third decimal.

Paper: upload `paper/` to Overleaf (pdfLaTeX + BibTeX, acmart). `paper/Final_Paper.pdf` was built locally with XeLaTeX and the Libertinus fonts, because the ACM Libertine fonts are not installed in the build environment; the text is identical.

## Demo notebook
`notebooks/walkthrough.ipynb` is a short walkthrough for the 5-minute demonstration: it loads the
data, shows what a detector sees, prints the main result tables, shows the overview figure and
re-fits M1 live (about 10 s). Run the data step first (`bash scripts/fetch_data.sh` or `run_all.sh`), then
open the notebook in VS Code (Python + Jupyter extensions) or Jupyter, pick the Python that has the
requirements installed (`python -m pip install ipykernel` once), and choose **Run All**.

## Repository layout
```
README.md                 research question and reproduction (this file)
requirements.txt          pinned dependency versions
configs/experiment.yaml   frozen protocol (seeds, splits, metric, threshold rule)
data/README.md            data access, licence, checksums (raw data not committed)
notebooks/                executed walkthrough for the demo
src/citesurf/             data loading, features, detectors, metrics
scripts/                  numbered entry points (00–05) + run_all.sh
tests/                    unit tests
results/                  tables, per-entry predictions, figures, logs
paper/                    LaTeX source, .bib, figures, Final_Paper.pdf
docs/                     research brief (G1), frozen blueprint, self-review
research_decisions.md     literature → experiment decisions and protocol changes
baseline_validation.md    baseline reproduction and deviations
ai_assistance_log.md      AI use, verification and errors caught
```

## Limitations
Detectors stand in for an idealised reader; no human trust is measured. The W&W
set is small (341) and only journal articles. HALLMARK's synthetic fabrications
contain generator artefacts (documented in the paper). Lookup tools and LLM
verifiers were not rerun (no API access from the build environment); their released
per-entry outputs are re-scored as reference points.

## Credits and licence
Code: MIT (see `LICENSE`). Data: HALLMARK v1.2.4 by P. Reizinger and W. Brendel,
MIT licence, https://github.com/rpatrik96/hallmark (arXiv:2607.18360). The W&W
supplement derives from Walters & Wilder, *Scientific Reports* 13:14045 (2023), CC BY 4.0.
`hallmark_features` is ported from HALLMARK's `scripts/shortcut_control_four_modes.py`.

## Minimum reproduction checklist (for a second student)
- [ ] `bash scripts/fetch_data.sh` ends with `data OK: checksums match`
- [ ] `python3 -m pytest -q tests` shows 8 passed
- [ ] `scripts/02_validate_baseline.py` prints `identical-to-original=True` for dev and test
- [ ] `results/tables/main_summary.csv`: M1 on `test_public[full-trained,full-scored]` has `auroc_mean` 0.797
- [ ] `results/tables/main_summary.csv`: M1 on `ww_groupcv` has `auroc_mean` 0.680 (Linux) / 0.679 (Windows); see note below
- [ ] Figures in `results/figures/` match those in the paper

**Cross-platform note.** The submitted results were produced on Windows 11 (Python 3.13.2). On Linux (Python 3.13.18) the same code gives summary AUROCs within 0.001 (largest per-seed difference 0.004, in the ablation). Only the gradient-boosting models differ; the text model and reference points are identical.
