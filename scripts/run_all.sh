#!/usr/bin/env bash
# Reproduce every result and figure from scratch (about 5 minutes on 2 CPU cores).
set -euo pipefail
# Read/write UTF-8 everywhere (Windows defaults to cp1252)
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
# Use whichever Python has the project's libraries (Windows may have both python and python3)
PY=""
for cand in python python3 py; do
  if command -v "$cand" >/dev/null 2>&1 && "$cand" -c "import numpy, sklearn" >/dev/null 2>&1; then PY="$cand"; break; fi
done
if [ -z "$PY" ]; then echo "No Python with numpy/scikit-learn found. Run: python -m pip install -r requirements.txt" >&2; exit 1; fi
echo "using Python: $(command -v "$PY")"
cd "$(dirname "$0")/.."
bash scripts/fetch_data.sh
"$PY" scripts/00_env_check.py
"$PY" -m pytest -q tests
"$PY" scripts/02_validate_baseline.py  | tee results/logs/02_validate_baseline.log
"$PY" scripts/03_run_experiments.py    > results/logs/03_run_experiments.log 2>&1
"$PY" scripts/03b_exploratory.py       | tee results/logs/03b_exploratory.log
"$PY" scripts/04_make_figures.py
"$PY" scripts/05_build_notebook.py
echo "done: see results/tables and results/figures"
