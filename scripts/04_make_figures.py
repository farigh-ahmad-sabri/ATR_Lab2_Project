"""Regenerate every figure in the paper from the CSVs in results/tables/.
Writes PDF + PNG to results/figures/ and copies PDFs to paper/figures/."""
import _paths  # noqa: F401
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from citesurf.data import load_split  # noqa: E402
from citesurf.features import completeness  # noqa: E402

ROOT = _paths.ROOT
TAB, FIG = ROOT / "results/tables", ROOT / "results/figures"
FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": "#52514e",
                     "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.labelcolor": "#0b0b0b",
                     "legend.frameon": False})
MODELS = {"B1_completeness_rule": ("B1 completeness rule", "#2a78d6", "s"),
          "B2_hallmark_gbm": ("B2 HALLMARK surface GBM", "#eb6834", "o"),
          "M1_extended_gbm": ("M1 extended surface GBM", "#1baf7a", "D"),
          "M2_charngram_lr": ("M2 char n-gram LR", "#eda100", "^")}
GRID = "#e7e6e2"


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf"); fig.savefig(FIG / f"{name}.png", dpi=300)
    (ROOT / "paper/figures").mkdir(parents=True, exist_ok=True)
    shutil.copy(FIG / f"{name}.pdf", ROOT / "paper/figures" / f"{name}.pdf")
    plt.close(fig)


def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ---------------------------------------------------------------- Fig: AUROC overview
summ = pd.read_csv(TAB / "main_summary.csv")
refs = pd.read_csv(TAB / "reference_points.csv")
conds = [("test_public[full-trained,full-scored]", "HALLMARK test\n(full records)"),
         ("test_public[eq-trained,eq-scored]", "HALLMARK test\n(format equalised)"),
         ("ww_transfer[full-trained]", "W&W ChatGPT\n(transfer from HALLMARK)"),
         ("ww_groupcv", "W&W ChatGPT\n(trained on W&W, grouped CV)")]
fig, ax = plt.subplots(figsize=(6.8, 2.9))
off = np.linspace(-0.27, 0.27, len(MODELS))
for j, (m, (lab, col, mk)) in enumerate(MODELS.items()):
    for i, (ev, _) in enumerate(conds):
        r = summ[(summ.model == m) & (summ.eval_set == ev)].iloc[0]
        x = i + off[j]
        ax.errorbar(x, r.auroc_mean, yerr=[[r.auroc_mean - r.auroc_ci_lo], [r.auroc_ci_hi - r.auroc_mean]],
                    fmt=mk, color=col, ms=5, mec="white", mew=0.8, elinewidth=1.4, capsize=0, label=lab if i == 0 else None, zorder=3)
llm = refs[refs.eval_set == "test_public"]
ax.fill_between([-0.42, 0.42], llm.auroc.min(), llm.auroc.max(), color="#9a9993", alpha=0.18, lw=0, zorder=1)
ax.text(0.0, (llm.auroc.min() + llm.auroc.max()) / 2 - 0.04, f"shaded: 8 LLM readers\n(AUROC {llm.auroc.min():.2f}–{llm.auroc.max():.2f})", ha="center", va="center", fontsize=6.3, color="#52514e")
btu = refs[refs.eval_set == "ww"].iloc[0]
for i in (2, 3):
    ax.plot([i - 0.42, i + 0.42], [btu.auroc] * 2, color="#52514e", lw=1.2, ls="--", zorder=2)
ax.text(2.5, btu.auroc + 0.012, f"database lookup (bibtex-updater) {btu.auroc:.2f}", ha="center", fontsize=6.5, color="#52514e")
ax.axhline(0.5, color="#52514e", lw=0.8, ls=":")
ax.text(3.45, 0.505, "chance", fontsize=6.5, color="#52514e", ha="right", va="bottom")
ax.set_xticks(range(len(conds))); ax.set_xticklabels([c[1] for c in conds], fontsize=7)
ax.set_ylabel("AUROC (95% bootstrap CI)"); ax.set_ylim(0.42, 1.0); ax.set_xlim(-0.5, 3.5)
ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True); clean(ax)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=4, fontsize=6.8, handletextpad=0.3, columnspacing=1.0)
fig.tight_layout(); save(fig, "fig_auroc_overview")

# ---------------------------------------------------------------- Fig: per-type DR (B2 vs M1)
pt = pd.read_csv(TAB / "per_type_summary.csv")
types = pt[(pt.kind == "type") & (pt.model == "M1_extended_gbm")].sort_values(["tier", "group"])
fig, ax = plt.subplots(figsize=(6.8, 2.7))
x = np.arange(len(types))
w = 0.38
for k, m in enumerate(["B2_hallmark_gbm", "M1_extended_gbm"]):
    lab, col, _ = MODELS[m]
    vals = [pt[(pt.kind == "type") & (pt.model == m) & (pt.group == g)].dr.iloc[0] for g in types.group]
    ax.bar(x + (k - 0.5) * w, vals, w * 0.92, color=col, label=lab, edgecolor="white", lw=0.5)
fpr = {m: pt[(pt.kind == "valid") & (pt.model == m)].dr.iloc[0] for m in ("B2_hallmark_gbm", "M1_extended_gbm")}
ax.axhline(fpr["M1_extended_gbm"], color="#52514e", lw=0.8, ls=":", label=f"M1 false-positive rate on real refs ({fpr['M1_extended_gbm']:.2f})")
for t in (1, 2):
    b = (types.tier <= t).sum() - 0.5
    ax.axvline(b, color="#b9b8b2", lw=0.8)
for t, name in ((1, "Tier 1 (easy)"), (2, "Tier 2 (medium)"), (3, "Tier 3 (hard)")):
    xs = x[types.tier.values == t]
    ax.text(xs.mean(), 1.06, name, ha="center", fontsize=7, color="#52514e")
ax.set_xticks(x); ax.set_xticklabels([f"{g.replace('_', ' ')} ({n})" for g, n in zip(types.group, types.n)], rotation=40, ha="right", fontsize=6.5)
ax.set_ylabel("Detection rate at dev-fixed\nthreshold (mean of 5 seeds)"); ax.set_ylim(0, 1.12)
ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True); clean(ax)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.07), fontsize=6.8, ncol=3)
fig.tight_layout(); save(fig, "fig_per_type")

# ---------------------------------------------------------------- Fig: ablation
ab = pd.read_csv(TAB / "ablation_summary.csv").iloc[1:]
fig, ax = plt.subplots(figsize=(3.4, 2.6))
y = np.arange(len(ab))
cols = [("delta_test_auroc", "HALLMARK test, full", "#1baf7a"), ("delta_test_eq_auroc", "HALLMARK test, equalised", "#2a78d6"), ("delta_ww_auroc", "W&W transfer", "#eb6834")]
h = 0.26
for k, (c, lab, col) in enumerate(cols):
    ax.barh(y + (1 - k) * h, ab[c], h * 0.9, color=col, label=lab, edgecolor="white", lw=0.4)
ax.set_yticks(y); ax.set_yticklabels([d.replace("_", " ") for d in ab.dropped], fontsize=7)
ax.axvline(0, color="#52514e", lw=0.8); ax.set_xlabel("Change in AUROC when group is removed from M1", fontsize=7)
ax.invert_yaxis(); ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True); clean(ax)
ax.legend(fontsize=6.2, loc="upper center", bbox_to_anchor=(0.45, -0.28), ncol=2)
fig.tight_layout(); save(fig, "fig_ablation")

# ---------------------------------------------------------------- Fig: completeness distribution
fig, axes = plt.subplots(1, 2, figsize=(6.8, 1.9), sharey=True)
for ax, (split, title) in zip(axes, (("test_public", "HALLMARK test_public"), ("supplement_chatgpt_citations", "W&W ChatGPT citations"))):
    recs = load_split(split)
    df = pd.DataFrame({"c": [completeness(r.entry) for r in recs], "y": [r.y for r in recs]})
    levels = range(3, 7)
    for k, (yv, lab, col) in enumerate(((0, "real", "#2a78d6"), (1, "hallucinated", "#eb6834"))):
        sub = df[df.y == yv]
        share = [(sub.c == lv).mean() for lv in levels]
        ax.bar(np.array(list(levels)) + (k - 0.5) * 0.38, share, 0.35, color=col, label=f"{lab} (n={len(sub)})", edgecolor="white", lw=0.4)
    ax.set_title(title, fontsize=7.5); ax.set_ylim(0, 1.25); ax.set_xticks(list(levels)); ax.set_xlabel("Visible components present (of 6)", fontsize=7)
    ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True); clean(ax); ax.legend(fontsize=6.5, loc="upper right")
axes[0].set_ylabel("Share of references")
fig.tight_layout(); save(fig, "fig_completeness")
print("figures written to", FIG)
