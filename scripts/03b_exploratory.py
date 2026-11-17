"""EXPLORATORY analyses, decided AFTER seeing the run-2 results (not part of the
frozen protocol; reported separately and labelled as such in the paper).

X1  Is M1's Tier-1 gain a generator artefact? HALLMARK's fabricated DOIs use
    unregistered 5-digit prefixes (10.7777x, 10.9999x, ...). Refit M1 with the
    two DOI-prefix features removed and compare.
X2  Paired stratified bootstrap of AUROC differences on test_public:
    M1 - B2 and M1 - M2 (seed 0 predictions, 2,000 resamples).
"""
import _paths  # noqa: F401
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from citesurf.data import load_split
from citesurf.features import featurise
from citesurf.metrics import auroc, binary_metrics, threshold_at_fpr
from sklearn.model_selection import StratifiedKFold

ROOT = _paths.ROOT
TAB, PRED = ROOT / "results/tables", ROOT / "results/predictions"
GROUPS = ["hallmark", "author_style", "title_style", "id_consistency"]
DROP = ["doi_registrant_len", "doi_registrant_ge_6"]
dev, test = load_split("dev_public"), load_split("test_public")
y_dev, y_test = np.array([r.y for r in dev]), np.array([r.y for r in test])
Xd, names = featurise([r.entry for r in dev], GROUPS)
Xt, _ = featurise([r.entry for r in test], GROUPS)

rows = []
for label, cols in (("M1 (all features)", names), ("M1 without DOI-prefix features", [n for n in names if n not in DROP])):
    idx = [names.index(c) for c in cols]
    for seed in range(5):
        oof = np.zeros(len(dev))
        for tr, va in StratifiedKFold(5, shuffle=True, random_state=seed).split(Xd, y_dev):
            oof[va] = GradientBoostingClassifier(random_state=seed).fit(Xd[tr][:, idx], y_dev[tr]).predict_proba(Xd[va][:, idx])[:, 1]
        t = threshold_at_fpr(y_dev, oof, 0.10)
        s = GradientBoostingClassifier(random_state=seed).fit(Xd[:, idx], y_dev).predict_proba(Xt[:, idx])[:, 1]
        flag = s >= t
        ht = np.array([r.htype for r in test]); tier = np.array([r.tier if r.tier else 0 for r in test])
        bm = binary_metrics(y_test, s, t)
        rows.append({"variant": label, "seed": seed, "test_auroc": auroc(y_test, s), "dr": bm["detection_rate"],
                     "fpr": bm["false_positive_rate"], "dr_fabricated_doi": flag[ht == "fabricated_doi"].mean(),
                     "dr_tier1": flag[(y_test == 1) & (tier == 1)].mean(), "dr_tier3": flag[(y_test == 1) & (tier == 3)].mean()})
x1 = pd.DataFrame(rows).groupby("variant", sort=False).mean(numeric_only=True).drop(columns="seed").reset_index()
x1.to_csv(TAB / "exploratory_x1_doi_prefix.csv", index=False)
print(x1.to_string(float_format=lambda v: f"{v:.3f}"))

# X2 paired bootstrap
def load(model):
    return pd.read_csv(PRED / f"test_public__{model}__train-full__seed0.csv").score.values

s1, s2, s3 = load("M1_extended_gbm"), load("B2_hallmark_gbm"), load("M2_charngram_lr")
rng = np.random.default_rng(0)
pos, neg = np.where(y_test == 1)[0], np.where(y_test == 0)[0]
d12, d13 = [], []
for _ in range(2000):
    i = np.concatenate([rng.choice(pos, len(pos)), rng.choice(neg, len(neg))])
    a = roc_auc_score(y_test[i], s1[i])
    d12.append(a - roc_auc_score(y_test[i], s2[i])); d13.append(a - roc_auc_score(y_test[i], s3[i]))
x2 = pd.DataFrame([
    {"comparison": "M1 - B2", "delta_auroc": auroc(y_test, s1) - auroc(y_test, s2), "ci_lo": np.quantile(d12, .025), "ci_hi": np.quantile(d12, .975), "p_le_0": float(np.mean(np.array(d12) <= 0))},
    {"comparison": "M1 - M2", "delta_auroc": auroc(y_test, s1) - auroc(y_test, s3), "ci_lo": np.quantile(d13, .025), "ci_hi": np.quantile(d13, .975), "p_le_0": float(np.mean(np.array(d13) <= 0))},
])
x2.to_csv(TAB / "exploratory_x2_paired_bootstrap.csv", index=False)
print(x2.to_string(float_format=lambda v: f"{v:.3f}"))
