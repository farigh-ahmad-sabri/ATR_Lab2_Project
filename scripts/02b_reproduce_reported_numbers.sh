#!/usr/bin/env bash
# Shows that HALLMARK's reported shortcut-control numbers (DR 0.468 dev / 0.388 test)
# are reproduced exactly at the commit that reported them, and that the v1.2.4
# relabel (commit 908a405) is what moves them to 0.456 / 0.440.
set -euo pipefail
# Use whichever Python has the project's libraries (Windows may have both python and python3)
PY=""
for cand in python python3 py; do
  if command -v "$cand" >/dev/null 2>&1 && "$cand" -c "import numpy, sklearn" >/dev/null 2>&1; then PY="$cand"; break; fi
done
if [ -z "$PY" ]; then echo "No Python with numpy/scikit-learn found. Run: python -m pip install -r requirements.txt" >&2; exit 1; fi
echo "using Python: $(command -v "$PY")"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$ROOT/data/external/hallmark_history"
[ -d "$TMP/.git" ] || git clone --quiet https://github.com/rpatrik96/hallmark.git "$TMP"
cd "$TMP"
for c in fa0cc7b 908a405~1 908a405; do
  git checkout --quiet "$c"
  echo "== commit $c"
  "$PY" -X utf8 -I scripts/shortcut_control_four_modes.py | grep -E "^---|gradient boosting"
done
git checkout --quiet c62d296d1d2e3e6f9cb325e37963b63350ab2ca4
