"""Environment test (Prompt 08). Prints versions, seeds a tiny model twice and
checks the two runs agree, and confirms the data files are present.
Expected output: version lines, 'determinism OK', 'data OK', exit code 0."""
import _paths  # noqa: F401
import platform, sys, json, hashlib
from pathlib import Path
import numpy, pandas, sklearn, scipy, matplotlib, yaml
from sklearn.ensemble import GradientBoostingClassifier

ROOT = _paths.ROOT
info = {"python": sys.version.split()[0], "platform": platform.platform(),
        "numpy": numpy.__version__, "pandas": pandas.__version__, "scikit-learn": sklearn.__version__,
        "scipy": scipy.__version__, "matplotlib": matplotlib.__version__, "pyyaml": yaml.__version__}
for k, v in info.items():
    print(f"{k:14s} {v}")
rng = numpy.random.default_rng(0)
X = rng.normal(size=(200, 5)); y = (X[:, 0] + rng.normal(size=200) > 0).astype(int)
a = GradientBoostingClassifier(random_state=0).fit(X, y).predict_proba(X)[:, 1]
b = GradientBoostingClassifier(random_state=0).fit(X, y).predict_proba(X)[:, 1]
assert numpy.allclose(a, b); print("determinism OK")
sums = (ROOT / "data/SHA256SUMS").read_text(encoding="utf-8").split("\n")
bad = []
for line in filter(None, sums):
    h, p = line.split(maxsplit=1)
    f = ROOT / "data/raw" / p
    if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest() != h:
        bad.append(p)
if bad:
    sys.exit(f"data problem: {bad}; run bash scripts/fetch_data.sh")
print("data OK:", len(sums) - sums.count(""), "files verified")
(ROOT / "results/logs").mkdir(parents=True, exist_ok=True)
(ROOT / "results/logs/environment.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
