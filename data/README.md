# Data

No raw data is committed. `bash scripts/fetch_data.sh` clones HALLMARK at commit
`c62d296d1d2e3e6f9cb325e37963b63350ab2ca4` (v1.2.4) into `data/external/hallmark`,
copies the files below into `data/raw/`, and checks them against `data/SHA256SUMS`.

| File | What it is | Size | Used for |
|---|---|---|---|
| `dev_public.jsonl` | HALLMARK dev split: 504 VALID, 615 HALLUCINATED | 1,119 | training, threshold selection |
| `test_public.jsonl` | HALLMARK test split: 307 VALID, 524 HALLUCINATED | 831 | held-out evaluation |
| `supplement_chatgpt_citations.jsonl` | ChatGPT (GPT-3.5/GPT-4) journal citations from Walters & Wilder (2023), human-coded; HALLMARK conversion | 341 (172/169) | external evaluation |
| `bibtexupdater_raw_supplement_chatgpt_citations.jsonl` | released per-entry output of bibtex-updater 1.4.0 on the set above | 341 | reference point (database lookup) |
| `llm_readers/*.jsonl` | released per-entry zero-shot predictions of 8 LLMs on test_public | 831 each | reference points (no lookup) |

**Licence.** HALLMARK is MIT-licensed (copy saved as `data/raw/HALLMARK_LICENSE`).
Walters & Wilder's supplementary data are CC BY 4.0 (*Scientific Reports* 13:14045).

**What a detector sees.** `src/citesurf/data.py` keeps only `bibtex_type` and
`fields` from each record. Labels, hallucination types, sub-test results,
explanations, provenance and dates are removed before features are computed.

**Partitions.** Official HALLMARK splits are used unchanged. Within the W&W set,
cross-validation folds are grouped by literature-review topic (40 topics, taken
from the key `ww_<n>_t<topic>_c<id>`).

**If the download fails** (e.g. "Connection was reset"): run
`bash scripts/fetch_data.sh` again. It fetches only the pinned commit, retries
three times, and skips the download once `data/raw/` and `data/external/hallmark/`
are present with matching checksums. Raw data is not stored in this repository.
