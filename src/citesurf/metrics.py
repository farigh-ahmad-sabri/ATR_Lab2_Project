"""Metrics. Positive class = HALLUCINATED (y=1). Higher AUROC/DR/MCC/F1 is better;
lower FPR is better."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import f1_score, matthews_corrcoef, roc_auc_score


def check_inputs(y, s):
    y = np.asarray(y)
    s = np.asarray(s, dtype=float)
    if y.shape != s.shape:
        raise ValueError(f"label/score length mismatch {y.shape} vs {s.shape}")
    if np.isnan(s).any():
        raise ValueError("NaN scores")
    if set(np.unique(y)) - {0, 1}:
        raise ValueError("labels must be 0/1")
    return y, s


def auroc(y, s) -> float:
    y, s = check_inputs(y, s)
    return float(roc_auc_score(y, s))


def bootstrap_auroc_ci(y, s, n=1000, seed=0, ci=0.95) -> tuple[float, float]:
    """Stratified bootstrap (resample positives and negatives separately)."""
    y, s = check_inputs(y, s)
    rng = np.random.default_rng(seed)
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    vals = []
    for _ in range(n):
        idx = np.concatenate([rng.choice(pos, len(pos)), rng.choice(neg, len(neg))])
        vals.append(roc_auc_score(y[idx], s[idx]))
    a = (1 - ci) / 2
    return float(np.quantile(vals, a)), float(np.quantile(vals, 1 - a))


def threshold_at_fpr(y, s, target=0.10) -> float:
    """Smallest threshold t such that FPR(score >= t) <= target, chosen on
    training-split predictions only. Ties are kept on the same side."""
    y, s = check_inputs(y, s)
    neg = np.sort(s[y == 0])[::-1]
    k = int(np.floor(target * len(neg)))  # number of negatives allowed above t
    if k >= len(neg):
        return float(neg[-1])
    # threshold strictly above the (k+1)-th largest negative score
    t = np.nextafter(neg[k], np.inf)
    return float(t)


def binary_metrics(y, s, t) -> dict[str, float]:
    y, s = check_inputs(y, s)
    p = (s >= t).astype(int)
    tp = int(((p == 1) & (y == 1)).sum())
    fp = int(((p == 1) & (y == 0)).sum())
    fn = int(((p == 0) & (y == 1)).sum())
    tn = int(((p == 0) & (y == 0)).sum())
    return {
        "detection_rate": tp / (tp + fn) if tp + fn else float("nan"),
        "false_positive_rate": fp / (fp + tn) if fp + tn else float("nan"),
        "mcc": float(matthews_corrcoef(y, p)) if len(set(p)) > 1 else 0.0,
        "f1": float(f1_score(y, p, zero_division=0)),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }
