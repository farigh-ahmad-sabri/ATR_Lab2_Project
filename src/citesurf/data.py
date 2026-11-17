"""Loading HALLMARK records and removing every field that could leak the label.

A detector in this study may only see what a reader of a reference list sees:
the BibTeX entry type and its fields (author, title, venue, year, DOI, ...).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"

SPLIT_FILES = {
    "dev_public": RAW / "dev_public.jsonl",
    "test_public": RAW / "test_public.jsonl",
    "supplement_chatgpt_citations": RAW / "supplement_chatgpt_citations.jsonl",
}

# What a detector is allowed to read.
VISIBLE_KEYS = ("bibtex_type", "fields")


@dataclass(frozen=True)
class Record:
    key: str
    entry: dict          # only VISIBLE_KEYS
    y: int               # 1 = HALLUCINATED, 0 = VALID
    htype: str | None    # hallucination type (for analysis only, never a feature)
    tier: int | None
    generation_method: str | None


def visible(rec: dict) -> dict:
    """Copy of the record with only reader-visible content."""
    fields = {str(k).lower(): str(v) for k, v in (rec.get("fields") or {}).items()}
    return {"bibtex_type": rec.get("bibtex_type"), "fields": fields}


def load_split(name: str) -> list[Record]:
    path = SPLIT_FILES[name]
    if not path.exists():
        raise FileNotFoundError(f"{path} missing; run `bash scripts/fetch_data.sh` first")
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r["label"] not in ("VALID", "HALLUCINATED"):
                raise ValueError(f"unexpected label {r['label']!r} in {name}")
            out.append(
                Record(
                    key=r["bibtex_key"],
                    entry=visible(r),
                    y=int(r["label"] == "HALLUCINATED"),
                    htype=r.get("hallucination_type"),
                    tier=r.get("difficulty_tier"),
                    generation_method=r.get("generation_method"),
                )
            )
    keys = [x.key for x in out]
    if len(keys) != len(set(keys)):
        raise ValueError(f"duplicate bibtex_key in {name}")
    return out


_WW_TOPIC = re.compile(r"^ww_\d+_t(\d+)_")


def ww_topic(key: str) -> int:
    """Topic id of a Walters & Wilder citation, from keys like ww_35_t4_c402."""
    m = _WW_TOPIC.match(key)
    if not m:
        raise ValueError(f"not a W&W key: {key}")
    return int(m.group(1))


def equalise(entry: dict) -> dict:
    """Render an entry in the minimal format used by the W&W set.

    Keeps author, title, year and one venue string; drops DOI, URL, pages,
    volume, publisher, etc., and sets the entry type to 'article'. This removes
    differences in *how much* is written while keeping *what* is written.
    """
    f = entry["fields"]
    venue = f.get("journal") or f.get("booktitle") or ""
    new = {k: f[k] for k in ("author", "title", "year") if k in f}
    if venue:
        new["journal"] = venue
    return {"bibtex_type": "article", "fields": new}
