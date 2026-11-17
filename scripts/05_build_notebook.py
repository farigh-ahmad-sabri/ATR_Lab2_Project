"""Build notebooks/walkthrough.ipynb and execute it in-process, storing the real
outputs. (Jupyter is not installed in the build environment, so cells are run
with exec(); the notebook also runs normally in Jupyter/Colab after
`bash scripts/fetch_data.sh`.) Use it for the 5-minute demo."""
import _paths  # noqa: F401
import base64
import contextlib
import io
import json

ROOT = _paths.ROOT
CELLS = [
    ("md", "# Walkthrough: how much does the surface of a reference reveal?\n"
           "Run `bash scripts/fetch_data.sh` first. Every number below is computed live from `data/raw/` or read from `results/tables/`."),
    ("code", "import sys, pathlib\nROOT = pathlib.Path.cwd().parent if pathlib.Path.cwd().name == 'notebooks' else pathlib.Path.cwd()\n"
             "sys.path.insert(0, str(ROOT / 'src'))\nimport pandas as pd, numpy as np\n"
             "from citesurf.data import load_split, equalise\nfrom citesurf.features import featurise, render, completeness\nprint('ROOT =', ROOT.name)"),
    ("md", "## 1. The data a detector is allowed to see"),
    ("code", "dev, test, ww = load_split('dev_public'), load_split('test_public'), load_split('supplement_chatgpt_citations')\n"
             "for n, s in [('dev', dev), ('test', test), ('W&W', ww)]:\n"
             "    print(f'{n:5s} n={len(s):4d}  hallucinated={sum(r.y for r in s):4d}  valid={sum(1-r.y for r in s):4d}')\n"
             "r = test[0]\nprint('\\nvisible keys:', list(r.entry))\nprint('rendered   :', render(r.entry))\nprint('label      :', r.y, r.htype)"),
    ("md", "## 2. One real and one fabricated ChatGPT citation (W&W): same fields, same format"),
    ("code", "real = next(x for x in ww if x.y == 0); fake = next(x for x in ww if x.y == 1)\n"
             "for x in (real, fake):\n    print(x.y, '|', render(x.entry), '| completeness', completeness(x.entry))"),
    ("md", "## 3. Surface features for one entry (extended set M1)"),
    ("code", "X, names = featurise([test[0].entry], ['hallmark','author_style','title_style','id_consistency'])\n"
             "print(len(names), 'features'); print(dict(list(zip(names, X[0].round(2)))[:12]))"),
    ("md", "## 4. Main results (from `results/tables/main_summary.csv`)"),
    ("code", "s = pd.read_csv(ROOT / 'results/tables/main_summary.csv')\n"
             "keep = ['test_public[full-trained,full-scored]','test_public[eq-trained,eq-scored]','ww_transfer[full-trained]','ww_groupcv']\n"
             "t = s[s.eval_set.isin(keep) & (s.model != 'B0_majority')].pivot(index='model', columns='eval_set', values='auroc_mean')[keep]\n"
             "print(t.round(3).to_string())"),
    ("code", "print(pd.read_csv(ROOT / 'results/tables/reference_points.csv')[['reference','eval_set','auroc','used_lookups']].round(3).to_string(index=False))"),
    ("md", "## 5. Figure: AUROC across conditions"),
    ("img", "results/figures/fig_auroc_overview.png"),
    ("md", "## 6. Quick rerun of one component (for the viva): M1 on test_public, seed 0"),
    ("code", "from citesurf.models import build\nfrom citesurf.metrics import auroc\nimport numpy as np\n"
             "m = build('M1_extended_gbm', 0).fit([r.entry for r in dev], np.array([r.y for r in dev]))\n"
             "print('M1 test AUROC (live):', round(auroc(np.array([r.y for r in test]), m.score([r.entry for r in test])), 3))"),
]


def main():
    ns, cells, count = {}, [], 0
    import os
    os.chdir(ROOT / "notebooks")
    for kind, src in CELLS:
        if kind == "md":
            cells.append({"cell_type": "markdown", "metadata": {}, "source": src})
            continue
        count += 1
        if kind == "img":
            data = base64.b64encode((ROOT / src).read_bytes()).decode()
            code = f"from IPython.display import Image\nImage(filename=str(ROOT / '{src}'))"
            cells.append({"cell_type": "code", "execution_count": count, "metadata": {}, "source": code,
                          "outputs": [{"output_type": "display_data", "metadata": {}, "data": {"image/png": data, "text/plain": "<Image>"}}]})
            continue
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exec(compile(src, f"<cell {count}>", "exec"), ns)
        cells.append({"cell_type": "code", "execution_count": count, "metadata": {}, "source": src,
                      "outputs": [{"output_type": "stream", "name": "stdout", "text": buf.getvalue()}]})
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    (ROOT / "notebooks/walkthrough.ipynb").write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print("wrote notebooks/walkthrough.ipynb with", count, "executed cells")
    for c in cells:
        if c["cell_type"] == "code" and c["outputs"] and c["outputs"][0].get("text"):
            print(c["outputs"][0]["text"].rstrip())


main()
