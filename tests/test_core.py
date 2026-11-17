import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from citesurf.data import equalise, load_split, visible, ww_topic  # noqa: E402
from citesurf.features import GROUPS, completeness, featurise, id_consistency_features  # noqa: E402
from citesurf.metrics import binary_metrics, bootstrap_auroc_ci, threshold_at_fpr  # noqa: E402

REC = {"bibtex_key": "k", "bibtex_type": "inproceedings", "label": "HALLUCINATED",
       "hallucination_type": "fabricated_doi", "subtests": {"doi_resolves": False},
       "explanation": "fake", "fields": {"Author": "A. B and C. D", "title": "T", "year": "2021",
                                          "booktitle": "ICML", "doi": "10.1234/x.2019.5"}}


def test_visible_drops_label_metadata():
    v = visible(REC)
    assert set(v) == {"bibtex_type", "fields"}
    assert "author" in v["fields"]  # keys lower-cased


def test_all_feature_groups_finite_on_real_data():
    entries = [r.entry for r in load_split("test_public")[:200]]
    for g in GROUPS:
        X, names = featurise(entries, [g])
        assert np.isfinite(X).all(), g
        assert len(names) == X.shape[1]


def test_id_year_mismatch():
    f = id_consistency_features(visible(REC))
    assert f["id_year_mismatch"] == 1.0 and f["doi_well_formed"] == 1.0


def test_equalise_keeps_content_drops_extras():
    e = equalise(visible(REC))
    assert e["fields"] == {"author": "A. B and C. D", "title": "T", "year": "2021", "journal": "ICML"}
    assert completeness(e) == 4


def test_ww_topic():
    assert ww_topic("ww_35_t14_c1401") == 14
    with pytest.raises(ValueError):
        ww_topic("abc")


def test_threshold_respects_target_fpr():
    rng = np.random.default_rng(0)
    y = np.r_[np.zeros(500), np.ones(500)].astype(int)
    s = np.r_[rng.normal(0, 1, 500), rng.normal(1, 1, 500)]
    t = threshold_at_fpr(y, s, 0.10)
    m = binary_metrics(y, s, t)
    assert m["false_positive_rate"] <= 0.10 and m["false_positive_rate"] >= 0.09


def test_bootstrap_ci_contains_point():
    rng = np.random.default_rng(1)
    y = np.r_[np.zeros(100), np.ones(100)].astype(int)
    s = np.r_[rng.normal(0, 1, 100), rng.normal(0.8, 1, 100)]
    lo, hi = bootstrap_auroc_ci(y, s, n=200)
    from sklearn.metrics import roc_auc_score
    assert lo <= roc_auc_score(y, s) <= hi


def test_metric_input_checks():
    with pytest.raises(ValueError):
        binary_metrics([0, 1], [0.1], 0.5)
