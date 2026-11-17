#!/usr/bin/env bash
# Get the HALLMARK files this study uses, at a pinned commit, and verify checksums.
# If data/raw/ and the HALLMARK subset in data/external/hallmark/ are already present
# from an earlier run and the checksums match, no download is made.
# Usage: bash scripts/fetch_data.sh
set -euo pipefail
COMMIT=c62d296d1d2e3e6f9cb325e37963b63350ab2ca4
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/data/external/hallmark"
DST="$ROOT/data/raw"

verify() { (cd "$DST" && sha256sum -c "$ROOT/data/SHA256SUMS" --quiet) >/dev/null 2>&1; }

if verify && [ -f "$SRC/scripts/shortcut_control_four_modes.py" ] && [ -d "$SRC/hallmark" ]; then
  echo "data OK: checksums match (already present, no download needed)"
  exit 0
fi

# Shallow fetch of exactly the pinned commit (smaller and more robust than a full clone)
if [ ! -f "$SRC/scripts/shortcut_control_four_modes.py" ]; then
  mkdir -p "$SRC"
  git -C "$SRC" init --quiet
  git -C "$SRC" remote add origin https://github.com/rpatrik96/hallmark.git 2>/dev/null || true
  for attempt in 1 2 3; do
    if git -C "$SRC" -c http.version=HTTP/1.1 fetch --quiet --depth 1 origin "$COMMIT"; then break; fi
    echo "fetch attempt $attempt failed; retrying..." >&2
    [ "$attempt" = 3 ] && { echo "Download failed after 3 attempts. Check your connection and run this script again (see data/README.md)." >&2; exit 1; }
    sleep 3
  done
  git -C "$SRC" checkout --quiet FETCH_HEAD
fi

mkdir -p "$DST/llm_readers"
cp "$SRC/data/v1.2/dev_public.jsonl" "$SRC/data/v1.2/test_public.jsonl" \
   "$SRC/data/v1.2/supplement_chatgpt_citations.jsonl" "$DST/"
cp "$SRC/data/v1.2/baseline_results/bibtexupdater_raw_supplement_chatgpt_citations.jsonl" "$DST/"
cp "$SRC"/results/llm_openrouter_*_test_public_predictions.jsonl "$DST/llm_readers/"
cp "$SRC/LICENSE" "$DST/HALLMARK_LICENSE"
verify && echo "data OK: checksums match"
