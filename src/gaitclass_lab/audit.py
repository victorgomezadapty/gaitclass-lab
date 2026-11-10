"""Data-quality audit: codebook against observed values.

Every flag is reported, nothing is silently corrected. The only analysis-level
assumption is that 'Stance' holds percent of the gait cycle (see FLAGS).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from . import data as D

# Hand-written flags, each backed by numbers computed in column_audit().
FLAGS = {
    "Group": (
        "codebook typo",
        "Codebook lists code 1 twice ('1 = healthy; 1 = hip osteoarthritis') and never code 0, "
        "while the unit says 0-4. Mapping 0 = healthy control is inferred from group sizes.",
    ),
    "Speed": (
        "description error",
        "Description reads 'Meters' while the unit is m/s; observed values are plausible walking speeds in m/s.",
    ),
    "StancePct": (
        "unit mismatch",
        "Unit given as seconds but all values lie between about 56 and 72, which fits percent of the gait cycle, "
        "not seconds. Analysed as percent of gait cycle (assumption).",
    ),
    "StanceDifference": (
        "unit mismatch",
        "Unit given as seconds; values follow the Stance scale and are read as percentage points (assumption).",
    ),
    "KneeMinimum": (
        "implausible scale",
        "Values between about -0.7 and -0.1 are implausible as degrees next to the other knee angles "
        "(degrees, up to about 34). Scale unknown; excluded from primary contrasts.",
    ),
    "KneeMinimumDifference": (
        "implausible scale",
        "Same unknown scale as KneeMinimum (values within about +/-0.45). Excluded from classifier sensitivity features.",
    ),
    "HipMinimum": (
        "min/max swap in description",
        "Described as 'Global hip maximum' but all values are negative (extension), consistent with a minimum. "
        "Raw header is also misspelled 'HipMininimum'.",
    ),
    "AnklePlantarflexion1Difference": (
        "min/max swap in description",
        "Described as side difference of the 'first ankle angle maximum', but the base feature is a local minimum.",
    ),
    "AnkleDorsalflexionDifference": (
        "min/max swap in description",
        "Described as side difference of 'ankle angle minimum', but the base feature is the maximum ankle angle.",
    ),
    "AnklePlantarflexion2Difference": (
        "min/max swap in description",
        "Described as side difference of 'second ankle angle maximum', but the base feature is a local minimum.",
    ),
    "AnkleICDifference": (
        "header mismatch",
        "Raw header is 'DIFF AnkleIC' while the codebook names it 'AnkleICDifference'.",
    ),
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def codebook_alignment(raw: pd.DataFrame, cb: pd.DataFrame) -> pd.DataFrame:
    """Pair codebook rows with raw columns by position and report name agreement."""
    rows = []
    for i, col in enumerate(raw.columns):
        cb_row = cb.iloc[i] if i < len(cb) else None
        cb_name = None if cb_row is None else str(cb_row["Feature Name"]).strip()
        rows.append({
            "position": i + 1,
            "raw_header": str(col),
            "raw_header_has_whitespace": str(col) != str(col).strip(),
            "codebook_name": cb_name,
            "names_match_ignoring_case_and_spaces": cb_name is not None and _norm(col) == _norm(cb_name),
        })
    return pd.DataFrame(rows)


def column_audit(df: pd.DataFrame, raw: pd.DataFrame, cb: pd.DataFrame) -> pd.DataFrame:
    """One row per analysed column: codebook unit/description, observed range and flag."""
    clean_cols = [c for c in df.columns if c not in ("group", "female", "patient")]
    rows = []
    for i, col in enumerate(clean_cols):
        cb_row = cb.iloc[i]
        s = df[col]
        flag, note = FLAGS.get(col, ("", ""))
        rows.append({
            "column": col,
            "raw_header": str(raw.columns[i]),
            "codebook_unit": "" if pd.isna(cb_row["Unit"]) else str(cb_row["Unit"]).strip(),
            "codebook_description": str(cb_row["Description"]).strip(),
            "n_nonmissing": int(s.notna().sum()),
            "min": float(s.min()),
            "max": float(s.max()),
            "mean": float(s.mean()),
            "flag": flag,
            "note": note,
        })
    return pd.DataFrame(rows)


def group_code_check(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["Group"].value_counts().sort_index()
    rows = []
    for code, n in counts.items():
        label = D.GROUP_MAP_INFERRED[int(code)]
        rows.append({
            "code": int(code),
            "observed_n": int(n),
            "label_used": label,
            "reported_n_zenodo_and_paper": D.REPORTED_GROUP_SIZES[label],
            "counts_match": int(n) == D.REPORTED_GROUP_SIZES[label],
            "basis": "inferred from reported group size (codebook lists 1 twice, no 0)" if code == 0
            else "codebook code, confirmed by reported group size",
        })
    return pd.DataFrame(rows)
