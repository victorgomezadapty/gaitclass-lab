"""Descriptive statistics and age and sex adjusted group contrasts."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint

from . import data as D

REF = "healthy control"


def mean_ci(x: pd.Series) -> tuple[float, float, float, float]:
    x = x.dropna().astype(float)
    n = len(x)
    m, sd = x.mean(), x.std(ddof=1)
    half = stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n)
    return m, sd, m - half, m + half


def describe_by_group(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    for col in cols:
        for g in D.GROUP_ORDER:
            x = df.loc[df["group"] == g, col]
            m, sd, lo, hi = mean_ci(x)
            q1, med, q3 = x.quantile([0.25, 0.5, 0.75])
            rows.append({
                "variable": col, "group": g, "n": int(x.notna().sum()),
                "mean": m, "sd": sd, "ci95_low": lo, "ci95_high": hi,
                "median": med, "q1": q1, "q3": q3, "min": x.min(), "max": x.max(),
            })
    return pd.DataFrame(rows)


def demographics(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for g in D.GROUP_ORDER:
        sub = df[df["group"] == g]
        n = len(sub)
        k = int(sub["female"].sum())
        lo, hi = proportion_confint(k, n, method="wilson")
        am, asd, alo, ahi = mean_ci(sub["Age"])
        bm, bsd, blo, bhi = mean_ci(sub["BMI"])
        rows.append({
            "group": g, "n": n,
            "age_mean": am, "age_sd": asd, "age_ci95_low": alo, "age_ci95_high": ahi,
            "age_median": sub["Age"].median(), "age_min": int(sub["Age"].min()), "age_max": int(sub["Age"].max()),
            "bmi_mean": bm, "bmi_sd": bsd, "bmi_ci95_low": blo, "bmi_ci95_high": bhi,
            "female_n": k, "female_pct": 100 * k / n,
            "female_pct_ci95_low": 100 * lo, "female_pct_ci95_high": 100 * hi,
        })
    return pd.DataFrame(rows)


def demographic_tests(df: pd.DataFrame) -> dict:
    groups = [df.loc[df["group"] == g, "Age"] for g in D.GROUP_ORDER]
    kw_age = stats.kruskal(*groups)
    groups_b = [df.loc[df["group"] == g, "BMI"] for g in D.GROUP_ORDER]
    kw_bmi = stats.kruskal(*groups_b)
    tab = pd.crosstab(df["group"], df["female"])
    chi = stats.chi2_contingency(tab)
    ctrl = df.loc[df["Group"] == 0, "Age"]
    pat = df.loc[df["Group"] != 0, "Age"]
    return {
        "age_kruskal_h": float(kw_age.statistic), "age_kruskal_p": float(kw_age.pvalue),
        "bmi_kruskal_h": float(kw_bmi.statistic), "bmi_kruskal_p": float(kw_bmi.pvalue),
        "sex_chi2": float(chi.statistic), "sex_chi2_p": float(chi.pvalue),
        "age_patients_minus_controls": float(pat.mean() - ctrl.mean()),
        "age_controls_vs_patients_mannwhitney_p": float(stats.mannwhitneyu(ctrl, pat).pvalue),
    }


def _fit(feature: str, data: pd.DataFrame, covars: list[str]):
    rhs = f"C(group, Treatment(reference='{REF}'))"
    if covars:
        rhs += " + " + " + ".join(covars)
    return smf.ols(f"{feature} ~ {rhs}", data=data).fit(cov_type="HC3")


def group_contrasts(df: pd.DataFrame, features: list[str], covars: list[str], label: str) -> pd.DataFrame:
    """Each patient group minus controls, OLS with HC3 robust SE, Holm across all rows."""
    rows = []
    data = df.copy()
    data["group"] = data["group"].astype(str)
    for f in features:
        res = _fit(f, data, covars)
        ci = res.conf_int()
        ctrl_sd = data.loc[data["group"] == REF, f].std(ddof=1)
        for g in D.GROUP_ORDER[1:]:
            term = f"C(group, Treatment(reference='{REF}'))[T.{g}]"
            est = res.params[term]
            rows.append({
                "model": label, "feature": f, "group": g, "n": int(res.nobs),
                "difference_vs_control": est,
                "ci95_low": ci.loc[term, 0], "ci95_high": ci.loc[term, 1],
                "p": res.pvalues[term],
                "standardised_difference": est / ctrl_sd,
                "std_ci95_low": ci.loc[term, 0] / ctrl_sd,
                "std_ci95_high": ci.loc[term, 1] / ctrl_sd,
            })
    out = pd.DataFrame(rows)
    out["p_holm"] = multipletests(out["p"], method="holm")[1]
    return out


def age_effect(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Age slope per 10 years within the adjusted model, to show the confounding pathway."""
    data = df.copy()
    data["group"] = data["group"].astype(str)
    data["Age10"] = data["Age"] / 10
    rows = []
    for f in features:
        res = _fit(f, data, ["Age10", "female"])
        ci = res.conf_int()
        rows.append({
            "feature": f, "age_per_10y": res.params["Age10"],
            "ci95_low": ci.loc["Age10", 0], "ci95_high": ci.loc["Age10", 1],
            "p": res.pvalues["Age10"],
        })
    return pd.DataFrame(rows)
