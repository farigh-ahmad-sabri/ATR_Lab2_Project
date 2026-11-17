"""Gate G3 — main experiments, following configs/experiment.yaml (protocol v1.0).

E1  dev_public -> test_public, all models, seeds 0-4
E2  dev_public -> Walters & Wilder ChatGPT set (transfer), full and format-equalised training
E3  within W&W: stratified group 5-fold CV, groups = literature-review topic
E4  format equalisation on test_public
A1  feature-group ablation of M1 (E1 and E2)
R   released reference points (LLM readers on test_public, bibtex-updater on W&W), re-scored

Usage: python scripts/03_run_experiments.py [--config configs/experiment.yaml]
"""
import _paths  # noqa: F401
import argparse
import json
import time

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold

from citesurf.data import equalise, load_split, ww_topic
from citesurf.features import render
from citesurf.metrics import auroc, binary_metrics, bootstrap_auroc_ci, threshold_at_fpr
from citesurf.models import DETERMINISTIC, MODEL_NAMES, FeatureGBM, build

ROOT = _paths.ROOT
ap = argparse.ArgumentParser()
ap.add_argument("--config", default=str(ROOT / "configs/experiment.yaml"))
args = ap.parse_args()
cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
SEEDS = cfg["seeds"]
BS = cfg["evaluation"]["bootstrap"]
TAB, PRED = ROOT / "results/tables", ROOT / "results/predictions"
TAB.mkdir(parents=True, exist_ok=True)
PRED.mkdir(parents=True, exist_ok=True)
t0 = time.time()

dev, test, ww = load_split("dev_public"), load_split("test_public"), load_split("supplement_chatgpt_citations")
E = lambda recs, eq=False: [equalise(r.entry) if eq else r.entry for r in recs]  # noqa: E731
Y = lambda recs: np.array([r.y for r in recs])  # noqa: E731
y_dev, y_test, y_ww = Y(dev), Y(test), Y(ww)


def dev_threshold(name, seed, eq=False, model_factory=None):
    """Threshold at FPR 0.10 from 5-fold CV predictions on dev only."""
    cv = StratifiedKFold(5, shuffle=True, random_state=seed)
    oof = np.zeros(len(dev))
    for tr, va in cv.split(np.zeros(len(dev)), y_dev):
        m = (model_factory() if model_factory else build(name, seed, cfg))
        m.fit([E(dev, eq)[i] for i in tr], y_dev[tr])
        oof[va] = m.score([E(dev, eq)[i] for i in va])
    return threshold_at_fpr(y_dev, oof, 0.10), auroc(y_dev, oof)


def row(model, evalset, seed, y, s, t, **extra):
    m = binary_metrics(y, s, t)
    return {"model": model, "eval_set": evalset, "seed": seed, "n": len(y), "n_pos": int(y.sum()),
            "auroc": auroc(y, s), "threshold": t, **{k: m[k] for k in ("detection_rate", "false_positive_rate", "mcc", "f1")}, **extra}


def save_pred(tag, recs, s):
    pd.DataFrame({"key": [r.key for r in recs], "y": [r.y for r in recs], "score": s,
                  "htype": [r.htype for r in recs], "tier": [r.tier for r in recs],
                  "generation_method": [r.generation_method for r in recs]}).to_csv(PRED / f"{tag}.csv", index=False)


rows = []
# ------------------------------------------------------------------ E1, E2, E4
for name in MODEL_NAMES:
    for seed in (SEEDS[:1] if name in DETERMINISTIC else SEEDS):
        for eq in (False, True):
            tag = "eq" if eq else "full"
            t, dev_auc = dev_threshold(name, seed, eq)
            m = build(name, seed, cfg).fit(E(dev, eq), y_dev)
            s_test = m.score(E(test, eq))
            rows.append(row(name, f"test_public[{tag}-trained,{tag}-scored]", seed, y_test, s_test, t, train=tag, dev_cv_auroc=dev_auc))
            save_pred(f"test_public__{name}__train-{tag}__seed{seed}", test, s_test)
            s_ww = m.score(E(ww))
            rows.append(row(name, f"ww_transfer[{tag}-trained]", seed, y_ww, s_ww, t, train=tag, dev_cv_auroc=dev_auc))
            save_pred(f"ww_transfer__{name}__train-{tag}__seed{seed}", ww, s_ww)
            if not eq:  # E4a: full-trained model, equalised test records
                s_teq = m.score(E(test, True))
                rows.append(row(name, "test_public[full-trained,eq-scored]", seed, y_test, s_teq, t, train=tag, dev_cv_auroc=dev_auc))
        print(f"{name}: done ({time.time() - t0:.0f}s)", flush=True)

# ------------------------------------------------------------------ E3 within-W&W grouped CV
groups = np.array([ww_topic(r.key) for r in ww])
for name in MODEL_NAMES:
    for seed in (SEEDS[:1] if name in DETERMINISTIC else SEEDS):
        cv = StratifiedGroupKFold(5, shuffle=True, random_state=seed)
        oof = np.zeros(len(ww))
        for tr, va in cv.split(np.zeros(len(ww)), y_ww, groups):
            m = build(name, seed, cfg).fit([ww[i].entry for i in tr], y_ww[tr])
            oof[va] = m.score([ww[i].entry for i in va])
        rows.append({"model": name, "eval_set": "ww_groupcv", "seed": seed, "n": len(ww), "n_pos": int(y_ww.sum()),
                     "auroc": auroc(y_ww, oof), "threshold": np.nan, "detection_rate": np.nan,
                     "false_positive_rate": np.nan, "mcc": np.nan, "f1": np.nan, "train": "ww_cv"})
        save_pred(f"ww_groupcv__{name}__seed{seed}", ww, oof)
print(f"E3 done ({time.time() - t0:.0f}s)", flush=True)

res = pd.DataFrame(rows)
res.to_csv(TAB / "main_results_per_seed.csv", index=False)

# ------------------------------------------------------------------ summary + bootstrap CIs
summ = []
for (model, ev), g in res.groupby(["model", "eval_set"], sort=False):
    ycol = y_ww if ev.startswith("ww") else y_test
    # CI on the seed-averaged score (one prediction file per seed)
    if ev.startswith("ww_groupcv"):
        files = [f"ww_groupcv__{model}__seed{s}" for s in g.seed]
    elif ev.startswith("ww_transfer"):
        files = [f"ww_transfer__{model}__train-{g.train.iloc[0]}__seed{s}" for s in g.seed]
    elif "eq-scored" in ev and "full-trained" in ev:
        files = None
    else:
        files = [f"test_public__{model}__train-{g.train.iloc[0]}__seed{s}" for s in g.seed]
    lo = hi = np.nan
    if files:
        s_avg = np.mean([pd.read_csv(PRED / f"{f}.csv").score.values for f in files], axis=0)
        lo, hi = bootstrap_auroc_ci(ycol, s_avg, BS["n_resamples"], BS["seed"], BS["ci"])
    summ.append({"model": model, "eval_set": ev, "n_seeds": len(g),
                 "auroc_mean": g.auroc.mean(), "auroc_sd": g.auroc.std(ddof=1) if len(g) > 1 else 0.0,
                 "auroc_ci_lo": lo, "auroc_ci_hi": hi,
                 "dr_mean": g.detection_rate.mean(), "fpr_mean": g.false_positive_rate.mean(),
                 "mcc_mean": g.mcc.mean(), "f1_mean": g.f1.mean()})
summary = pd.DataFrame(summ)
summary.to_csv(TAB / "main_summary.csv", index=False)
print(summary.to_string(float_format=lambda v: f"{v:.3f}"))

# ------------------------------------------------------------------ per type / tier (E1, full)
pt = []
for name in MODEL_NAMES:
    g = res[(res.model == name) & (res.eval_set == "test_public[full-trained,full-scored]")]
    for seed, t in zip(g.seed, g.threshold):
        p = pd.read_csv(PRED / f"test_public__{name}__train-full__seed{seed}.csv")
        p["flag"] = p.score >= t
        for ht, gg in p[p.y == 1].groupby("htype"):
            pt.append({"model": name, "seed": seed, "group": ht, "kind": "type", "tier": int(gg.tier.iloc[0]), "n": len(gg), "dr": gg.flag.mean()})
        for tier, gg in p[p.y == 1].groupby("tier"):
            neg = p[p.y == 0]
            pt.append({"model": name, "seed": seed, "group": f"tier{int(tier)}", "kind": "tier", "tier": int(tier), "n": len(gg), "dr": gg.flag.mean(),
                       "auroc_vs_valid": auroc(np.r_[np.ones(len(gg)), np.zeros(len(neg))].astype(int), np.r_[gg.score, neg.score])})
        for gm, gg in p[p.y == 1].groupby("generation_method"):
            pt.append({"model": name, "seed": seed, "group": gm, "kind": "generation_method", "n": len(gg), "dr": gg.flag.mean()})
        pt.append({"model": name, "seed": seed, "group": "VALID (FPR)", "kind": "valid", "n": int((p.y == 0).sum()), "dr": p[p.y == 0].flag.mean()})
per_type = pd.DataFrame(pt)
per_type.to_csv(TAB / "per_type_per_seed.csv", index=False)
agg = per_type.groupby(["model", "kind", "group"], as_index=False).agg(n=("n", "first"), tier=("tier", "first"), dr=("dr", "mean"),
                                                                        auroc_vs_valid=("auroc_vs_valid", "mean") if "auroc_vs_valid" in per_type else ("dr", "mean"))
agg.to_csv(TAB / "per_type_summary.csv", index=False)

# ------------------------------------------------------------------ A1 ablation
groups_full = cfg["features"]["groups"]["extended"]
ab = []
for drop in [None] + groups_full:
    keep = [g for g in groups_full if g != drop]
    for seed in SEEDS:
        m = FeatureGBM(keep, seed).fit(E(dev), y_dev)
        ab.append({"dropped": drop or "(none)", "seed": seed, "test_auroc": auroc(y_test, m.score(E(test))),
                   "ww_auroc": auroc(y_ww, m.score(E(ww))),
                   "test_eq_auroc": auroc(y_test, FeatureGBM(keep, seed).fit(E(dev, True), y_dev).score(E(test, True)))})
abl = pd.DataFrame(ab)
abl.to_csv(TAB / "ablation_per_seed.csv", index=False)
ab_s = abl.groupby("dropped", sort=False).agg(test_auroc=("test_auroc", "mean"), test_sd=("test_auroc", "std"),
                                               test_eq_auroc=("test_eq_auroc", "mean"), ww_auroc=("ww_auroc", "mean"), ww_sd=("ww_auroc", "std")).reset_index()
base = ab_s.iloc[0]
for c in ("test_auroc", "test_eq_auroc", "ww_auroc"):
    ab_s[f"delta_{c}"] = ab_s[c] - base[c]
ab_s.to_csv(TAB / "ablation_summary.csv", index=False)
print(ab_s.to_string(float_format=lambda v: f"{v:.3f}"))

# ------------------------------------------------------------------ feature importance (M1 seed 0)
m1 = FeatureGBM(groups_full, 0).fit(E(dev), y_dev)
imp = pd.DataFrame({"feature": m1.feature_names, "importance": m1.model.feature_importances_}).sort_values("importance", ascending=False)
imp.to_csv(TAB / "m1_feature_importance.csv", index=False)

# ------------------------------------------------------------------ error analysis: hardest misses
p = pd.read_csv(PRED / "test_public__M1_extended_gbm__train-full__seed0.csv")
t_m1 = res[(res.model == "M1_extended_gbm") & (res.seed == 0) & (res.eval_set == "test_public[full-trained,full-scored]")].threshold.iloc[0]
miss = p[(p.y == 1) & (p.score < t_m1)].sort_values("score").head(25).copy()
by_key = {r.key: r for r in test}
miss["citation"] = [render(by_key[k].entry) for k in miss.key]
miss.to_csv(TAB / "m1_hardest_misses.csv", index=False)
fp = p[(p.y == 0) & (p.score >= t_m1)].sort_values("score", ascending=False).head(15).copy()
fp["citation"] = [render(by_key[k].entry) for k in fp.key]
fp.to_csv(TAB / "m1_false_positives.csv", index=False)

# ------------------------------------------------------------------ R: released reference points
ref = []
for f in sorted((ROOT / "data/raw/llm_readers").glob("*.jsonl")):
    preds = {json.loads(l)["bibtex_key"]: json.loads(l) for l in open(f, encoding="utf-8")}
    ys, ss, labs = [], [], []
    for r in test:
        pr = preds.get(r.key)
        if pr is None or pr["label"] not in ("VALID", "HALLUCINATED"):
            continue
        c = float(pr.get("confidence", 0.5))
        ys.append(r.y); ss.append(c if pr["label"] == "HALLUCINATED" else 1 - c); labs.append(pr["label"] == "HALLUCINATED")
    ys, ss, labs = np.array(ys), np.array(ss), np.array(labs)
    lo, hi = bootstrap_auroc_ci(ys, ss, BS["n_resamples"], BS["seed"], BS["ci"])
    # api_sources_queried holds the model endpoint itself (e.g. "openrouter/google/gemini-2.5-pro");
    # only a non-model source would mean a bibliographic lookup was made.
    used_lookup = any(any(not str(src).startswith("openrouter/") for src in (json.loads(l).get("api_sources_queried") or []))
                      for l in open(f, encoding="utf-8"))
    ref.append({"reference": f.stem.replace("_test_public_predictions", ""), "eval_set": "test_public", "n_answered": len(ys),
                "auroc": auroc(ys, ss), "auroc_ci_lo": lo, "auroc_ci_hi": hi,
                "dr_own_labels": labs[ys == 1].mean(), "fpr_own_labels": labs[ys == 0].mean(), "used_lookups": used_lookup})
btu = {json.loads(l)["key"]: json.loads(l) for l in open(ROOT / "data/raw/bibtexupdater_raw_supplement_chatgpt_citations.jsonl", encoding="utf-8")}
ys = np.array([r.y for r in ww if r.key in btu]); ss = np.array([1 - float(btu[r.key]["p_valid"]) for r in ww if r.key in btu])
lo, hi = bootstrap_auroc_ci(ys, ss, BS["n_resamples"], BS["seed"], BS["ci"])
ref.append({"reference": "bibtex-updater 1.4.0 (database lookup; HALLMARK release)", "eval_set": "ww", "n_answered": len(ys),
            "auroc": auroc(ys, ss), "auroc_ci_lo": lo, "auroc_ci_hi": hi,
            "dr_own_labels": 0.929, "fpr_own_labels": 0.076, "used_lookups": True})  # DR/FPR as reported in HALLMARK docs (attributed)
refs = pd.DataFrame(ref)
refs.to_csv(TAB / "reference_points.csv", index=False)
print(refs.to_string(float_format=lambda v: f"{v:.3f}"))
print(f"total runtime {time.time() - t0:.0f}s")
