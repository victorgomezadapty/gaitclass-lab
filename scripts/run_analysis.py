"""Run the full GaitClass Lab analysis offline from the local workbook.

Usage (from the project root):
    .venv/bin/python scripts/run_analysis.py

Writes tables/, figures/ (PNG and WebP), results/summary.json and RESULTS.md.
"""
from __future__ import annotations

import json
import platform
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gaitclass_lab import analysis as A  # noqa: E402
from gaitclass_lab import audit as AU  # noqa: E402
from gaitclass_lab import data as D  # noqa: E402
from gaitclass_lab import figures as F  # noqa: E402
from gaitclass_lab import leakage as L  # noqa: E402
from gaitclass_lab.report import write_results_md  # noqa: E402

TABLES, FIGS, RES = ROOT / "tables", ROOT / "figures", ROOT / "results"


def r(x, k=3):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), k)


def main() -> None:
    for p in (TABLES, FIGS, RES):
        p.mkdir(exist_ok=True)
    log = []

    raw = D.load_raw()
    cb = D.load_codebook()
    df = D.prepare(raw)
    log.append(f"md5 {D.md5sum()} bytes {D.RAW_PATH.stat().st_size} shape {raw.shape}")

    # 1. inventory and audit
    align = AU.codebook_alignment(raw, cb)
    audit = AU.column_audit(df, raw, cb)
    groups = AU.group_code_check(df)
    align.to_csv(TABLES / "t01_column_inventory_and_codebook_alignment.csv", index=False)
    audit.to_csv(TABLES / "t02_data_quality_audit.csv", index=False)
    groups.to_csv(TABLES / "t03_group_codes_inferred_mapping.csv", index=False)

    # 2. demographics and kinematics by group
    demo = A.demographics(df)
    demo_tests = A.demographic_tests(df)
    demo.to_csv(TABLES / "t04_demographics_by_group.csv", index=False)
    desc = A.describe_by_group(df, ["Age", "BMI"] + D.PRIMARY_FEATURES + ["KneeMinimum"])
    desc.to_csv(TABLES / "t05_features_by_group.csv", index=False)

    # 3. contrasts
    unadj = A.group_contrasts(df, D.PRIMARY_FEATURES, [], "unadjusted")
    adj = A.group_contrasts(df, D.PRIMARY_FEATURES, ["Age", "female"], "adjusted for age and sex")
    adj_bmi = A.group_contrasts(df, D.PRIMARY_FEATURES, ["Age", "female", "BMI"], "adjusted for age, sex and BMI")
    cells = L.suspected_cells(df)
    clean = df[~cells.any(axis=1)]
    adj_clean = A.group_contrasts(clean, D.PRIMARY_FEATURES, ["Age", "female"],
                                  "adjusted for age and sex, flagged rows removed")
    pd.concat([unadj, adj, adj_bmi, adj_clean]).to_csv(TABLES / "t06_group_contrasts.csv", index=False)
    age_eff = A.age_effect(df, D.PRIMARY_FEATURES)
    age_eff.to_csv(TABLES / "t07_age_effect_per_10_years.csv", index=False)

    # 4. imputation footprints and leakage
    shared = L.shared_value_table(df)
    flags = L.flag_summary(df, cells)
    assoc = L.flag_association(df, cells)
    shrink = L.control_spread_shrinkage(df, cells)
    cls = L.classification_sensitivity(df, cells)
    shared.to_csv(TABLES / "t08_shared_values_imputation_footprints.csv", index=False)
    flags.to_csv(TABLES / "t09_imputation_flags_by_group.csv", index=False)
    shrink.to_csv(TABLES / "t10_control_spread_shrinkage.csv", index=False)
    cls.to_csv(TABLES / "t11_leakage_classification_sensitivity.csv", index=False)

    # figures
    made = []
    made += F.fig_group_counts(groups, FIGS / "fig01_group_codes.png")
    made += F.fig_data_quality(df, FIGS / "fig02_data_quality_audit.png")
    made += F.fig_age(df, FIGS / "fig03_age_by_group.png")
    made += F.fig_contrasts(adj, FIGS / "fig04_adjusted_contrasts.png")
    made += F.fig_imputation(flags, FIGS / "fig05_imputation_footprints.png")
    made += F.fig_leakage(cls, FIGS / "fig06_leakage_sensitivity.png")

    def contrast_dict(t):
        return {f"{row.feature}|{row.group}": {
            "diff": r(row.difference_vs_control), "ci95": [r(row.ci95_low), r(row.ci95_high)],
            "std_diff": r(row.standardised_difference), "p_holm": r(row.p_holm, 4)}
            for row in t.itertuples()}

    def n_sig(t):
        return int((t["p_holm"] < 0.05).sum())

    sig_unadj = set(unadj.loc[unadj.p_holm < 0.05, ["feature", "group"]].itertuples(index=False, name=None))
    sig_adj = set(adj.loc[adj.p_holm < 0.05, ["feature", "group"]].itertuples(index=False, name=None))
    sig_clean = set(adj_clean.loc[adj_clean.p_holm < 0.05, ["feature", "group"]].itertuples(index=False, name=None))

    summary = {
        "status": "public",
        "generated_local_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "source": {
            "title": D.DATASET_TITLE, "short_name": "GaitClass (file and project short name only)",
            "zenodo_record": D.ZENODO_RECORD, "doi": D.ZENODO_DOI, "concept_doi": D.ZENODO_CONCEPT_DOI,
            "license_id": "cc-by-4.0", "file": D.RAW_NAME, "bytes": D.EXPECTED_BYTES, "md5": D.EXPECTED_MD5,
            "paper_doi": D.PAPER_DOI, "paper_pmid": D.PAPER_PMID, "paper_license": "CC BY-NC-ND 4.0",
            "ethics": D.ETHICS, "citation": D.DATASET_CITATION,
        },
        "n_participants": int(len(df)),
        "n_columns": int(raw.shape[1]),
        "group_counts_by_code": {str(k): int(v) for k, v in df["Group"].value_counts().sort_index().items()},
        "group_mapping": {"mapping": {str(k): v for k, v in D.GROUP_MAP_INFERRED.items()},
                          "basis": "INFERRED from group sizes reported on Zenodo and in the paper; "
                                   "the codebook lists code 1 twice and never code 0",
                          "codebook_text": D.CODEBOOK_GROUP_TEXT},
        "missing_cells_in_file": int(raw.isna().sum().sum()),
        "direct_identifier_columns": D.identifier_like_columns(raw.columns),
        "audit": {
            "flagged_columns": [c for c, f in zip(audit["column"], audit["flag"]) if f],
            "n_flagged_columns": int((audit["flag"] != "").sum()),
            "codebook_name_mismatches": int((~align["names_match_ignoring_case_and_spaces"]).sum()),
            "headers_with_whitespace": int(align["raw_header_has_whitespace"].sum()),
            "stance_range": [r(df["StancePct"].min(), 2), r(df["StancePct"].max(), 2)],
            "knee_minimum_range": [r(df["KneeMinimum"].min(), 2), r(df["KneeMinimum"].max(), 2)],
            "knee_maximum_range": [r(df["KneeMaximum"].min(), 2), r(df["KneeMaximum"].max(), 2)],
            "hip_minimum_max_value": r(df["HipMinimum"].max(), 2),
            "speed_range": [r(df["Speed"].min(), 2), r(df["Speed"].max(), 2)],
        },
        "demographics": {
            row.group: {"n": int(row.n), "age_mean": r(row.age_mean, 1), "age_sd": r(row.age_sd, 1),
                        "age_ci95": [r(row.age_ci95_low, 1), r(row.age_ci95_high, 1)],
                        "bmi_mean": r(row.bmi_mean, 1), "female_pct": r(row.female_pct, 1)}
            for row in demo.itertuples()},
        "demographic_tests": {k: r(v, 6) for k, v in demo_tests.items()},
        "contrasts": {
            "features_prespecified": D.PRIMARY_FEATURES,
            "n_contrasts_per_model": int(len(adj)),
            "significant_holm_unadjusted": n_sig(unadj),
            "significant_holm_age_sex_adjusted": n_sig(adj),
            "significant_holm_age_sex_bmi_adjusted": n_sig(adj_bmi),
            "significant_holm_adjusted_flagged_removed": n_sig(adj_clean),
            "lost_after_age_sex_adjustment": sorted("|".join(x) for x in sig_unadj - sig_adj),
            "gained_after_age_sex_adjustment": sorted("|".join(x) for x in sig_adj - sig_unadj),
            "lost_after_removing_flagged_rows": sorted("|".join(x) for x in sig_adj - sig_clean),
            "rows_after_removing_flagged": int(len(clean)),
            "adjusted": contrast_dict(adj),
            "unadjusted": contrast_dict(unadj),
        },
        "imputation": {
            "detectable_suspected_cells": int(cells.values.sum()),
            "rows_flagged": int(cells.any(axis=1).sum()),
            "by_group": {row.group: {"flagged": int(row.rows_with_suspected_imputed_cell), "n": int(row.n)}
                         for row in flags.itertuples()},
            "fisher_controls_vs_patients": {k: (v if isinstance(v, int) else r(v, 4)) for k, v in assoc.items()},
            "largest_shared_value": {"column": shared.iloc[0]["column"], "n_rows": int(shared.iloc[0]["n_rows"]),
                                     "groups": ", ".join(f"{n} {g}" for g, n in
                                                                   pd.Series(shared.iloc[0]["groups"].split()).value_counts().items())},
            "original_missingness_recoverable": False,
        },
        "leakage_classification": {row.scenario: {"rows": int(row.rows), "auc_mean": r(row.auc_mean),
                                                  "auc_p2_5_p97_5": [r(row.auc_p2_5), r(row.auc_p97_5)],
                                                  "balanced_accuracy": r(row.balanced_accuracy_mean)}
                                   for row in cls.itertuples()},
        "outputs": {"tables": sorted(p.name for p in TABLES.glob("*.csv")),
                    "figures": sorted(p.name for p in made)},
    }
    (RES / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_results_md(ROOT / "RESULTS.md", summary, audit=audit, groups=groups, demo=demo, adj=adj,
                     unadj=unadj, adj_clean=adj_clean, flags=flags, shared=shared, shrink=shrink,
                     cls=cls, age_eff=age_eff)
    log.append(f"tables {len(summary['outputs']['tables'])} figures {len(made)}")
    (RES / "run_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))


if __name__ == "__main__":
    main()
