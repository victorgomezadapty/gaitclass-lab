"""Imputation signatures and a leakage-aware classification sensitivity analysis.

The deposit says gaps were filled with the control-group mean (controls) or by nearest
neighbours (patients), and imputed cells are not flagged. Original missingness cannot be
recovered from the file. Here imputed or copied cells are detected from their footprint:
a value with about 15 significant decimals that appears in two or more rows cannot be an
independent measurement, and an exact 0.0 side difference means both sides are identical.
This gives a LOWER BOUND: a cell imputed only once in its column leaves no footprint.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import data as D

SIGNATURE_COLS = D.ANGLE_COLS + D.DIFF_COLS
SEED = 20261110
N_REPEATS = 20
N_SPLITS = 5

DEMOGRAPHIC_FEATURES = ["Age", "female", "BMI"]
GAIT_FEATURES = (
    ["Speed", "StancePct", "StanceDifference"]
    + [c for c in D.ANGLE_COLS if c != "KneeMinimum"]
    + [c for c in D.DIFF_COLS if c != "KneeMinimumDifference"]
)


def suspected_cells(df: pd.DataFrame) -> pd.DataFrame:
    """Boolean frame, True where a cell carries an imputation or copy footprint."""
    out = pd.DataFrame(False, index=df.index, columns=SIGNATURE_COLS)
    for c in SIGNATURE_COLS:
        s = df[c]
        shared = s.duplicated(keep=False) & s.notna()
        zero_diff = (s == 0.0) if c in D.DIFF_COLS else pd.Series(False, index=s.index)
        out[c] = shared | zero_diff
    return out


def shared_value_table(df: pd.DataFrame) -> pd.DataFrame:
    """Every repeated value: column, value, rows sharing it, groups involved."""
    rows = []
    for c in SIGNATURE_COLS:
        s = df[c]
        dup = s[s.duplicated(keep=False)]
        for v, idx in dup.groupby(dup).groups.items():
            sub = df.loc[idx]
            rows.append({
                "column": c,
                "value": float(v),
                "n_rows": len(idx),
                "ids": " ".join(str(int(i)) for i in sub["ID"]),
                "groups": " ".join(D.GROUP_SHORT[g] for g in sub["group"]),
            })
    return pd.DataFrame(rows).sort_values(["n_rows", "column"], ascending=[False, True])


def flag_summary(df: pd.DataFrame, cells: pd.DataFrame) -> pd.DataFrame:
    flagged = cells.any(axis=1)
    rows = []
    for g in D.GROUP_ORDER:
        m = df["group"] == g
        rows.append({
            "group": g,
            "n": int(m.sum()),
            "rows_with_suspected_imputed_cell": int(flagged[m].sum()),
            "pct_rows_flagged": 100 * float(flagged[m].mean()),
            "suspected_cells": int(cells[m].values.sum()),
        })
    return pd.DataFrame(rows)


def link_clusters(df: pd.DataFrame, cells: pd.DataFrame) -> np.ndarray:
    """Connected components of rows that share any repeated value in the same column."""
    parent = list(range(len(df)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for c in SIGNATURE_COLS:
        s = df[c].reset_index(drop=True)
        dup = s[s.duplicated(keep=False)]
        for _, idx in dup.groupby(dup).groups.items():
            idx = list(idx)
            for j in idx[1:]:
                parent[find(j)] = find(idx[0])
    return np.array([find(i) for i in range(len(df))])


def _cv_scores(X, y, groups, model_factory, cluster_aware: bool):
    aucs, baccs = [], []
    for r in range(N_REPEATS):
        if cluster_aware:
            cv = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED + r)
            splits = cv.split(X, y, groups)
        else:
            cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED + r)
            splits = cv.split(X, y)
        prob = np.zeros(len(y))
        pred = np.zeros(len(y))
        for tr, te in splits:
            m = model_factory()
            m.fit(X[tr], y[tr])
            prob[te] = m.predict_proba(X[te])[:, 1]
            pred[te] = m.predict(X[te])
        aucs.append(roc_auc_score(y, prob))
        baccs.append(balanced_accuracy_score(y, pred))
    return np.array(aucs), np.array(baccs)


def _logit():
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000))


def _one_nn():
    return make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=1))


def classification_sensitivity(df: pd.DataFrame, cells: pd.DataFrame) -> pd.DataFrame:
    """Healthy vs patient, as a sensitivity analysis of the leakage risk only.

    Not a replication of the paper's classifier (different software, features,
    preprocessing and splits). Patients are the positive class.
    """
    y_all = df["patient"].to_numpy()
    flagged = cells.any(axis=1).to_numpy()
    clusters = link_clusters(df, cells)
    clean = ~flagged

    scenarios = [
        ("A. demographics only (age, sex, BMI)", DEMOGRAPHIC_FEATURES, _logit, "all", False),
        ("B. imputation flag only (no gait, no demographics)", ["_flag"], _logit, "all", False),
        ("C. gait features, standard CV", GAIT_FEATURES, _logit, "all", False),
        ("D. gait features, cluster-aware CV", GAIT_FEATURES, _logit, "all", True),
        ("E. gait features, flagged rows removed", GAIT_FEATURES, _logit, "clean", False),
        ("F. gait + demographics, standard CV", GAIT_FEATURES + DEMOGRAPHIC_FEATURES, _logit, "all", False),
        ("G. gait + demographics, flagged rows removed", GAIT_FEATURES + DEMOGRAPHIC_FEATURES, _logit, "clean", False),
        ("H. 1-NN on gait features, standard CV", GAIT_FEATURES, _one_nn, "all", False),
        ("I. 1-NN on gait features, cluster-aware CV", GAIT_FEATURES, _one_nn, "all", True),
    ]
    work = df.copy()
    work["_flag"] = flagged.astype(float)
    rows = []
    for name, feats, factory, subset, aware in scenarios:
        m = clean if subset == "clean" else np.ones(len(df), bool)
        X = work.loc[m, feats].to_numpy(float)
        y = y_all[m]
        aucs, baccs = _cv_scores(X, y, clusters[m], factory, aware)
        rows.append({
            "scenario": name,
            "model": "1-nearest neighbour" if factory is _one_nn else "logistic regression (L2)",
            "rows": int(m.sum()),
            "controls": int((y == 0).sum()),
            "patients": int((y == 1).sum()),
            "cv": f"{'stratified group' if aware else 'stratified'} {N_SPLITS}-fold x {N_REPEATS}",
            "auc_mean": float(aucs.mean()),
            "auc_p2_5": float(np.percentile(aucs, 2.5)),
            "auc_p97_5": float(np.percentile(aucs, 97.5)),
            "balanced_accuracy_mean": float(baccs.mean()),
        })
    return pd.DataFrame(rows)


def flag_association(df: pd.DataFrame, cells: pd.DataFrame) -> dict:
    flagged = cells.any(axis=1)
    ctrl = df["Group"] == 0
    a = int((flagged & ctrl).sum()); b = int((~flagged & ctrl).sum())
    c = int((flagged & ~ctrl).sum()); d = int((~flagged & ~ctrl).sum())
    odds, p = stats.fisher_exact([[a, b], [c, d]])
    return {
        "controls_flagged": a, "controls_total": a + b,
        "patients_flagged": c, "patients_total": c + d,
        "odds_ratio_control_vs_patient": float(odds), "fisher_p": float(p),
    }


def control_spread_shrinkage(df: pd.DataFrame, cells: pd.DataFrame) -> pd.DataFrame:
    """Control-group SD with and without suspected cells, per affected column.

    Filling gaps with one constant pulls the control distribution inward, which makes
    controls look more homogeneous than measured data would.
    """
    ctrl = df["Group"] == 0
    rows = []
    for c in SIGNATURE_COLS:
        flagged = cells.loc[ctrl, c]
        if flagged.sum() == 0:
            continue
        s = df.loc[ctrl, c]
        rows.append({
            "column": c,
            "controls_suspected_cells": int(flagged.sum()),
            "control_sd_all": float(s.std(ddof=1)),
            "control_sd_without_suspected": float(s[~flagged].std(ddof=1)),
            "sd_ratio_all_over_clean": float(s.std(ddof=1) / s[~flagged].std(ddof=1)),
        })
    return pd.DataFrame(rows)
