"""Gate G2 — baseline validation.

1. Run HALLMARK's own shortcut-control script unchanged and capture its output.
2. Re-implement that control with this project's code (port of the feature set,
   data loader and metric functions) and check the predictions are identical.
3. Cross-check this project's DR/FPR/AUROC against HALLMARK's official
   `hallmark.evaluation.metrics` on the same predictions.
4. Leakage audit across dev/test/external splits.

Writes results/logs/baseline_validation.json and results/logs/hallmark_control_stdout.txt.
"""
import _paths  # noqa: F401
import json
import re
import subprocess
import sys

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from citesurf.data import load_split
from citesurf.features import featurise
from citesurf.metrics import auroc, binary_metrics

ROOT = _paths.ROOT
HM = ROOT / "data/external/hallmark"
FOUR = {"wrong_venue", "preprint_as_published", "partial_author_list", "arxiv_version_mismatch"}
REPORTED = {"dev_public": 0.468, "test_public": 0.388}  # HALLMARK README, gradient boosting DR
out = {}

# 1 ---------------------------------------------------------------- original script
# -X utf8: the original script opens the data without an encoding, which fails on
# Windows (default cp1252). The flag changes only the default text encoding; the
# script itself is run unmodified.
res = subprocess.run([sys.executable, "-X", "utf8", "-I", str(HM / "scripts/shortcut_control_four_modes.py")],
                     capture_output=True, text=True, encoding="utf-8", cwd=HM)
if res.returncode != 0:
    sys.exit("HALLMARK script failed:\n" + res.stderr)
(ROOT / "results/logs/hallmark_control_stdout.txt").write_text(res.stdout, encoding="utf-8")
orig = {}
split = None
for line in res.stdout.splitlines():
    m = re.match(r"--- (\w+):", line)
    if m:
        split = m.group(1)
    m = re.match(r"\s+gradient boosting\s+DR ([\d.]+)\s+FPR ([\d.]+)", line)
    if m:
        orig[split] = {"dr": float(m.group(1)), "fpr": float(m.group(2))}
out["original_script"] = orig
print("HALLMARK script (unchanged):", orig)

# 2 ---------------------------------------------------------------- port fidelity
out["port"] = {}
for name in ("dev_public", "test_public"):
    recs = [r for r in load_split(name) if r.y == 0 or r.htype in FOUR]
    X, _ = featurise([r.entry for r in recs], ["hallmark"])
    y = np.array([r.y for r in recs])
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    pred = cross_val_predict(GradientBoostingClassifier(random_state=0), X, y, cv=cv)
    bm = binary_metrics(y, pred.astype(float), 0.5)
    same = abs(bm["detection_rate"] - orig[name]["dr"]) < 5e-4 and abs(bm["false_positive_rate"] - orig[name]["fpr"]) < 5e-4
    out["port"][name] = {"n_pos": int(y.sum()), "n_neg": int((y == 0).sum()),
                         "dr": round(bm["detection_rate"], 4), "fpr": round(bm["false_positive_rate"], 4),
                         "matches_original_script": bool(same), "reported_in_hallmark_readme": REPORTED[name],
                         "diff_vs_reported": round(bm["detection_rate"] - REPORTED[name], 4)}
    print(f"port {name}: DR {bm['detection_rate']:.3f} FPR {bm['false_positive_rate']:.3f} "
          f"identical-to-original={same}  reported DR {REPORTED[name]}")
    assert same, "port does not reproduce HALLMARK's script"

# 3 ---------------------------------------------------------------- metric cross-check
sys.path.insert(0, str(HM))
from hallmark.dataset.schema import BenchmarkEntry, Prediction  # noqa: E402
from hallmark.evaluation import metrics as hm  # noqa: E402

raw = [json.loads(l) for l in open(ROOT / "data/raw/test_public.jsonl", encoding="utf-8")]
entries = [BenchmarkEntry.from_dict(r) for r in raw]
rng = np.random.default_rng(123)
y = np.array([int(r["label"] == "HALLUCINATED") for r in raw])
score = np.clip(0.6 * y + rng.normal(0.2, 0.3, len(y)), 0.001, 0.999)  # synthetic scores, for checking only
preds = [Prediction(bibtex_key=r["bibtex_key"], label="HALLUCINATED" if s >= 0.5 else "VALID",
                    confidence=float(s if s >= 0.5 else 1 - s)) for r, s in zip(raw, score)]
ev = hm.evaluate(entries, preds)
mine = binary_metrics(y, score, 0.5)
cross = {"hallmark_dr": ev.detection_rate, "mine_dr": mine["detection_rate"],
         "hallmark_fpr": ev.false_positive_rate, "mine_fpr": mine["false_positive_rate"],
         "hallmark_auroc": hm.auroc(entries, preds), "mine_auroc": auroc(y, score)}
cross["agree"] = all(abs(cross[f"hallmark_{k}"] - cross[f"mine_{k}"]) < 1e-9 for k in ("dr", "fpr", "auroc"))
out["metric_crosscheck"] = cross
print("metric cross-check:", {k: round(v, 6) if isinstance(v, float) else v for k, v in cross.items()})
assert cross["agree"]

# 4 ---------------------------------------------------------------- leakage audit
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())  # noqa: E731
dev, test, ww = load_split("dev_public"), load_split("test_public"), load_split("supplement_chatgpt_citations")
t_dev = {norm(r.entry["fields"].get("title", "")) for r in dev}
t_test = {norm(r.entry["fields"].get("title", "")) for r in test}
leak = {
    "shared_keys_dev_test": len({r.key for r in dev} & {r.key for r in test}),
    "shared_titles_dev_test": len(t_dev & t_test),
    "shared_titles_ext_vs_hallmark": len({norm(r.entry["fields"].get("title", "")) for r in ww} & (t_dev | t_test)),
    "dev_counts": {"valid": sum(r.y == 0 for r in dev), "hallucinated": sum(r.y for r in dev)},
    "test_counts": {"valid": sum(r.y == 0 for r in test), "hallucinated": sum(r.y for r in test)},
    "ext_counts": {"valid": sum(r.y == 0 for r in ww), "hallucinated": sum(r.y for r in ww)},
    "ext_topics": len({int(r.key.split('_t')[1].split('_')[0]) for r in ww}),
}
out["leakage"] = leak
print("leakage audit:", leak)
(ROOT / "results/logs/baseline_validation.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print("wrote results/logs/baseline_validation.json")
