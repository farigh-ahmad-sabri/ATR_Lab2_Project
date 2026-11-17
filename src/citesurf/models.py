"""Detectors compared in the study. Each exposes fit(entries, y) and score(entries)
where a higher score means 'more likely hallucinated'."""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from .features import completeness, featurise, render


class Majority:
    """B0: always predicts the most frequent training label.

    The score is a fixed constant (0.5), not the training prevalence: with the
    prevalence, pooled cross-validation predictions get a different constant per
    fold and the pooled AUROC drifts away from 0.5 (seen in run 1 on W&W: 0.487).
    """

    name = "B0_majority"

    def fit(self, entries, y):
        self.label = int(np.mean(y) >= 0.5)
        return self

    def score(self, entries):
        return np.full(len(entries), 0.5)


class CompletenessRule:
    """B1: a 'format-trusting reader'. The less complete a reference looks, the
    more suspicious it is. No learning beyond the threshold chosen later."""

    name = "B1_completeness_rule"

    def fit(self, entries, y):
        return self

    def score(self, entries):
        return np.array([(6 - completeness(e)) / 6 for e in entries], dtype=float)


class FeatureGBM:
    """B2 / M1: gradient boosting on surface features (sklearn defaults, as in HALLMARK)."""

    def __init__(self, groups, seed=0, name=None):
        self.groups = list(groups)
        self.seed = seed
        self.name = name or "GBM[" + "+".join(self.groups) + "]"

    def fit(self, entries, y):
        X, self.feature_names = featurise(entries, self.groups)
        self.model = GradientBoostingClassifier(random_state=self.seed).fit(X, y)
        return self

    def score(self, entries):
        X, names = featurise(entries, self.groups)
        assert names == self.feature_names, "feature mismatch between fit and score"
        return self.model.predict_proba(X)[:, 1]


class CharNgramLR:
    """M2: character 2-5-gram TF-IDF of the rendered reference + logistic regression."""

    name = "M2_charngram_lr"

    def __init__(self, seed=0, ngram_range=(2, 5), min_df=2, C=1.0):
        self.seed = seed
        self.pipe = make_pipeline(
            TfidfVectorizer(analyzer="char_wb", ngram_range=tuple(ngram_range), min_df=min_df, sublinear_tf=True),
            LogisticRegression(C=C, max_iter=5000, random_state=seed),
        )

    def fit(self, entries, y):
        self.pipe.fit([render(e) for e in entries], y)
        return self

    def score(self, entries):
        return self.pipe.predict_proba([render(e) for e in entries])[:, 1]


def build(name: str, seed: int = 0, cfg: dict | None = None):
    cfg = cfg or {}
    groups = cfg.get("features", {}).get("groups", {})
    if name == "B0_majority":
        return Majority()
    if name == "B1_completeness_rule":
        return CompletenessRule()
    if name == "B2_hallmark_gbm":
        return FeatureGBM(groups.get("hallmark", ["hallmark"]), seed, name)
    if name == "M1_extended_gbm":
        return FeatureGBM(groups.get("extended", ["hallmark", "author_style", "title_style", "id_consistency"]), seed, name)
    if name == "M2_charngram_lr":
        p = cfg.get("models", {}).get("M2_charngram_lr", {})
        return CharNgramLR(seed, p.get("ngram_range", (2, 5)), p.get("min_df", 2), p.get("C", 1.0))
    raise KeyError(name)


MODEL_NAMES = ["B0_majority", "B1_completeness_rule", "B2_hallmark_gbm", "M1_extended_gbm", "M2_charngram_lr"]
DETERMINISTIC = {"B0_majority", "B1_completeness_rule"}
