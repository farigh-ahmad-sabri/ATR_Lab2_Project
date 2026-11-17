"""Surface-only features of a reference. Nothing here performs a lookup.

Group `hallmark` is copied unchanged from HALLMARK's
`scripts/shortcut_control_four_modes.py` (MIT licence, commit c62d296) so that
the reproduced baseline B2 uses exactly the authors' feature set. The other
three groups are this project's extension (model M1).
"""

from __future__ import annotations

import re
import unicodedata

import numpy as np

REFERENCE_YEAR = 2026  # year the benchmark was built; used for "age" and "future" cues


# ---------------------------------------------------------------- group: hallmark
def hallmark_features(entry: dict) -> dict[str, float]:
    """Verbatim port of HALLMARK's `features()` (surface only)."""
    f = entry["fields"]
    author = f.get("author", "")
    title = f.get("title", "")
    venue = f.get("journal", "") + " " + f.get("booktitle", "")
    year = f.get("year", "")
    return {
        "n_fields": len(f),
        "has_doi": float("doi" in f),
        "has_eprint": float("eprint" in f),
        "has_url": float("url" in f),
        "has_pages": float("pages" in f),
        "has_volume": float("volume" in f),
        "has_publisher": float("publisher" in f),
        "has_journal": float("journal" in f),
        "has_booktitle": float("booktitle" in f),
        "title_chars": len(title),
        "title_words": len(title.split()),
        "title_has_colon": float(":" in title),
        "title_has_braces": float("{" in title),
        "author_chars": len(author),
        "n_authors": float(author.count(" and ") + 1 if author else 0),
        "author_has_others": float("others" in author.lower()),
        "venue_chars": len(venue.strip()),
        "venue_mentions_arxiv": float("arxiv" in venue.lower()),
        "venue_mentions_preprint": float("preprint" in venue.lower()),
        "is_article": float(entry.get("bibtex_type") == "article"),
        "is_inproceedings": float(entry.get("bibtex_type") == "inproceedings"),
        "is_misc": float(entry.get("bibtex_type") == "misc"),
        "year_val": float(year) if re.fullmatch(r"\d{4}", year) else 0.0,
        "doi_is_arxiv": float("10.48550" in f.get("doi", "")),
    }


# ------------------------------------------------------------ group: author_style
def _split_authors(author: str) -> list[str]:
    return [a.strip() for a in re.split(r"\s+and\s+", author) if a.strip()]


def _surname(name: str) -> str:
    if "," in name:
        return name.split(",")[0].strip()
    parts = name.split()
    return parts[-1] if parts else ""


def _given(name: str) -> str:
    if "," in name:
        return name.split(",", 1)[1].strip()
    parts = name.split()
    return " ".join(parts[:-1])


def author_style_features(entry: dict) -> dict[str, float]:
    names = [a for a in _split_authors(entry["fields"].get("author", "")) if a.lower() != "others"]
    n = len(names)
    if n == 0:
        return {k: 0.0 for k in (
            "auth_frac_initials", "auth_frac_full_given", "auth_mean_surname_len",
            "auth_max_surname_len", "auth_dup_surname", "auth_frac_hyphen",
            "auth_any_nonascii", "auth_any_digit", "auth_missing")} | {"auth_missing": 1.0}
    givens = [_given(a) for a in names]
    surnames = [_surname(a) for a in names]
    initials = [bool(g) and all(re.fullmatch(r"[A-Z]\.?(-[A-Z]\.?)?", t) for t in g.split()) for g in givens]
    full = [bool(re.search(r"[A-Za-z]{2,}", g)) for g in givens]
    lens = [len(s) for s in surnames]
    return {
        "auth_frac_initials": float(np.mean(initials)),
        "auth_frac_full_given": float(np.mean(full)),
        "auth_mean_surname_len": float(np.mean(lens)),
        "auth_max_surname_len": float(max(lens)),
        "auth_dup_surname": float(len(set(s.lower() for s in surnames)) < n),
        "auth_frac_hyphen": float(np.mean(["-" in s for s in surnames])),
        "auth_any_nonascii": float(any(unicodedata.normalize("NFKD", a) != a or not a.isascii() for a in names)),
        "auth_any_digit": float(any(ch.isdigit() for a in names for ch in a)),
        "auth_missing": 0.0,
    }


# ------------------------------------------------------------- group: title_style
def title_style_features(entry: dict) -> dict[str, float]:
    t = entry["fields"].get("title", "").replace("{", "").replace("}", "")
    words = re.findall(r"[A-Za-z][A-Za-z'\-]*", t)
    content = [w for w in words[1:] if len(w) > 3]
    caps = [w[0].isupper() for w in content]
    return {
        "title_frac_capitalised": float(np.mean(caps)) if caps else 0.0,
        "title_n_digits": float(sum(ch.isdigit() for ch in t)),
        "title_has_question": float("?" in t),
        "title_ends_punct": float(t.rstrip()[-1:] in ".!?" if t.strip() else 0),
        "title_n_colons": float(t.count(":")),
        "title_mean_word_len": float(np.mean([len(w) for w in words])) if words else 0.0,
        "title_has_acronym": float(bool(re.search(r"\b[A-Z]{2,}[a-z]*\b", t))),
    }


# --------------------------------------------------------- group: id_consistency
_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
_ARXIV_DOI_RE = re.compile(r"arxiv\.(\d{2})(\d{2})\.\d{4,5}", re.I)
_YEAR_IN_TEXT = re.compile(r"(?<!\d)(19[5-9]\d|20[0-3]\d)(?!\d)")


def id_consistency_features(entry: dict) -> dict[str, float]:
    """Cues a careful reader could check by eye: is the DOI well formed, and does
    the year hidden inside a DOI or URL agree with the stated year?"""
    f = entry["fields"]
    doi = f.get("doi", "").strip()
    url = f.get("url", "").strip()
    year_s = f.get("year", "")
    year = int(year_s) if re.fullmatch(r"\d{4}", year_s) else None
    reg = re.match(r"^10\.(\d+)/", doi)
    arx = _ARXIV_DOI_RE.search(doi) or _ARXIV_DOI_RE.search(url)
    # arXiv ids encode yymm of first submission; a paper cannot be published before it
    arxiv_gap = (year - (2000 + int(arx.group(1)))) if (arx and year) else 0
    years_in_ids = [int(y) for y in _YEAR_IN_TEXT.findall(doi + " " + url)]
    return {
        "doi_well_formed": float(bool(_DOI_RE.match(doi))) if doi else 0.0,
        "doi_registrant_len": float(len(reg.group(1))) if reg else 0.0,
        "doi_registrant_ge_6": float(bool(reg) and len(reg.group(1)) >= 6),
        "arxiv_year_gap": float(arxiv_gap),
        "arxiv_before_publication_violated": float(arx is not None and year is not None and arxiv_gap < 0),
        "id_year_mismatch": float(year is not None and bool(years_in_ids) and year not in years_in_ids),
        "url_contains_doi": float(bool(doi) and doi.lower() in url.lower()),
        "year_in_future": float(year is not None and year > REFERENCE_YEAR),
        "year_age": float(REFERENCE_YEAR - year) if year else -1.0,
        "year_missing": float(year is None),
    }


GROUPS = {
    "hallmark": hallmark_features,
    "author_style": author_style_features,
    "title_style": title_style_features,
    "id_consistency": id_consistency_features,
}


def featurise(entries: list[dict], groups: list[str]) -> tuple[np.ndarray, list[str]]:
    rows = []
    for e in entries:
        d: dict[str, float] = {}
        for g in groups:
            d.update(GROUPS[g](e))
        rows.append(d)
    names = sorted(rows[0])
    X = np.array([[r[n] for n in names] for r in rows], dtype=float)
    return X, names


def completeness(entry: dict) -> int:
    """How 'finished' a reference looks: 0-6 visible components present."""
    f = entry["fields"]
    parts = [
        bool(f.get("author")),
        bool(f.get("title")),
        bool(f.get("year")),
        bool(f.get("journal") or f.get("booktitle")),
        bool(f.get("doi") or f.get("url")),
        bool(f.get("pages") or f.get("volume")),
    ]
    return int(sum(parts))


def render(entry: dict) -> str:
    """Plain-text rendering of a reference, as a reader would see it."""
    f = entry["fields"]
    venue = f.get("journal") or f.get("booktitle") or ""
    bits = [f.get("author", ""), f.get("year", ""), f.get("title", ""), venue, f.get("doi", ""), f.get("url", "")]
    return ". ".join(b for b in bits if b)
