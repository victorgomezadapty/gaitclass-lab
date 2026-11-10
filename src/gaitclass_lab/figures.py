"""Figures. Each PNG gets a WebP twin for possible later use on a case page."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

from . import data as D  # noqa: E402

plt.rcParams.update({
    "axes.unicode_minus": False,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})
COLORS = {
    "healthy control": "#4C72B0", "hip OA": "#DD8452", "knee OA": "#C44E52",
    "lumbar stenosis": "#8172B3", "cervical stenosis": "#55A868",
}
SOURCE = "Data: Nüesch et al. 2023, Zenodo 10.5281/zenodo.7598463, CC BY 4.0. Public re-analysis."


def _save(fig, path: Path) -> list[Path]:
    fig.canvas.draw()
    bottom = fig.get_tightbbox(fig.canvas.get_renderer()).y0 / fig.get_figheight()
    fig.text(0.01, bottom - 0.015, SOURCE, fontsize=7, color="#555555", ha="left", va="top")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    webp = path.with_suffix(".webp")
    Image.open(path).save(webp, "WEBP", quality=90, method=6)
    return [path, webp]


def fig_group_counts(groups: pd.DataFrame, path: Path):
    fig, ax = plt.subplots(figsize=(9, 3.8))
    x = np.arange(len(groups))
    ax.bar(x - 0.2, groups["observed_n"], 0.4, label="observed in file",
           color=[COLORS[g] for g in groups["label_used"]])
    ax.bar(x + 0.2, groups["reported_n_zenodo_and_paper"], 0.4, label="reported (Zenodo, paper)",
           color="white", edgecolor="#333333", hatch="//")
    labels = [f"code {c}\n{l.replace(' ', chr(10))}" + ("\n(inferred)" if c == 0 else "") for c, l in
              zip(groups["code"], groups["label_used"])]
    ax.set_xticks(x, labels, fontsize=8)
    for xi, n in zip(x, groups["observed_n"]):
        ax.text(xi - 0.2, n + 1, str(n), ha="center", fontsize=8)
    ax.set_ylabel("participants")
    ax.set_title("Group codes: observed counts match reported sizes\n"
                 "Codebook lists code 1 twice; code 0 = control is inferred", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    return _save(fig, path)


def fig_data_quality(df: pd.DataFrame, path: Path):
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
    ax = axes[0]
    ax.hist(df["StancePct"], bins=20, color="#888888")
    ax.set_title("'Stance', codebook unit: seconds", fontsize=9)
    ax.set_xlabel("value as deposited")
    ax.set_ylabel("participants")
    ax.text(0.03, 0.97, f"range {df['StancePct'].min():.1f} to {df['StancePct'].max():.1f}\n"
            "fits % of gait cycle,\nnot seconds", transform=ax.transAxes, va="top", fontsize=8)
    ax = axes[1]
    for i, col in enumerate(["KneeMinimum", "KneeIC", "KneeMaximum", "KneeMinimumTO"]):
        y = df[col]
        ax.scatter(np.full(len(y), i) + np.random.default_rng(i).uniform(-0.15, 0.15, len(y)), y,
                   s=6, alpha=0.5, color="#C44E52" if col == "KneeMinimum" else "#888888")
    ax.set_xticks(range(4), ["KneeMin", "KneeIC", "KneeMax", "KneeMinTO"], fontsize=8)
    ax.set_ylabel("value as deposited (codebook: degrees)")
    ax.set_title("KneeMinimum sits near 0 on another scale", fontsize=9)
    ax = axes[2]
    ax.hist(df["HipMinimum"], bins=20, color="#888888")
    ax.axvline(0, color="#333333", lw=0.8)
    ax.set_title("'HipMinimum', described as\n'Global hip maximum'", fontsize=9)
    ax.set_xlabel("degrees (all values below 0)")
    ax.set_ylabel("participants")
    fig.suptitle("Codebook and value mismatches flagged, not corrected", fontsize=10, y=1.03)
    fig.subplots_adjust(wspace=0.35)
    return _save(fig, path)


def fig_age(df: pd.DataFrame, path: Path):
    fig, ax = plt.subplots(figsize=(7, 3.6))
    data = [df.loc[df["group"] == g, "Age"] for g in D.GROUP_ORDER]
    ax.boxplot(data, widths=0.5, showfliers=False)
    for i, (g, y) in enumerate(zip(D.GROUP_ORDER, data), start=1):
        ax.scatter(np.full(len(y), i) + np.random.default_rng(i).uniform(-0.18, 0.18, len(y)), y,
                   s=8, alpha=0.6, color=COLORS[g])
        ax.text(i, 96, f"mean {y.mean():.1f}", ha="center", fontsize=8)
    ax.set_xticks(range(1, 6), [f"{g.replace(' ', chr(10))}\nn={len(y)}" for g, y in zip(D.GROUP_ORDER, data)], fontsize=8)
    ax.set_ylim(20, 100)
    ax.set_ylabel("age (years)")
    ax.set_title("Controls are not age matched to knee OA and lumbar stenosis", fontsize=10)
    return _save(fig, path)


def fig_contrasts(adj: pd.DataFrame, path: Path):
    feats = list(dict.fromkeys(adj["feature"]))
    groups = D.GROUP_ORDER[1:]
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    yt, yl = [], []
    y = 0
    for f in feats:
        for k, g in enumerate(groups):
            r = adj[(adj["feature"] == f) & (adj["group"] == g)].iloc[0]
            ax.errorbar(r["standardised_difference"], y,
                        xerr=[[r["standardised_difference"] - r["std_ci95_low"]],
                              [r["std_ci95_high"] - r["standardised_difference"]]],
                        fmt="o", ms=4, color=COLORS[g], label=g if f == feats[0] else None,
                        mfc=COLORS[g] if r["p_holm"] < 0.05 else "white")
            y += 1
        yt.append(y - 2.5); yl.append(f)
        y += 1
    ax.axvline(0, color="#333333", lw=0.8)
    ax.set_yticks(yt, yl, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("difference vs controls, in control SD units (95% CI)")
    ax.set_title("Age and sex adjusted contrasts vs healthy controls\n"
                 "filled marker: Holm adjusted p below 0.05", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=4)
    return _save(fig, path)


def fig_imputation(flags: pd.DataFrame, path: Path):
    fig, ax = plt.subplots(figsize=(7, 3.4))
    x = np.arange(len(flags))
    ax.bar(x, flags["pct_rows_flagged"], color=[COLORS[g] for g in flags["group"]])
    for xi, (k, n) in enumerate(zip(flags["rows_with_suspected_imputed_cell"], flags["n"])):
        ax.text(xi, flags["pct_rows_flagged"].iloc[xi] + 0.8, f"{k}/{n}", ha="center", fontsize=8)
    ax.set_xticks(x, flags["group"], fontsize=8)
    ax.set_ylabel("% of rows with a suspected\nimputed or copied cell")
    ax.set_title("Imputation footprints are more frequent in controls (lower bound)", fontsize=10)
    return _save(fig, path)


def fig_leakage(cls: pd.DataFrame, path: Path):
    fig, ax = plt.subplots(figsize=(7.5, 4))
    y = np.arange(len(cls))
    ax.errorbar(cls["auc_mean"], y, xerr=[cls["auc_mean"] - cls["auc_p2_5"], cls["auc_p97_5"] - cls["auc_mean"]],
                fmt="o", color="#333333", ms=4)
    ax.axvline(0.5, color="#999999", lw=0.8, ls=":")
    ax.set_yticks(y, cls["scenario"], fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlim(0.4, 1.0)
    ax.set_xlabel("ROC AUC, healthy vs patient (mean and 2.5 to 97.5 percentile over CV repeats)")
    ax.set_title("Leakage sensitivity analysis, not a diagnostic model", fontsize=10)
    return _save(fig, path)
