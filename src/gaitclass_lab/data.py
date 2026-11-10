"""Loading, integrity checks and labelling for the GaitClass workbook.

Only data source: Zenodo record 7598463 (version DOI 10.5281/zenodo.7598463,
concept DOI 10.5281/zenodo.7598462), license cc-by-4.0.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_NAME = "data set GaitClass.xlsx"
RAW_PATH = ROOT / "data" / "raw" / RAW_NAME
EXPECTED_MD5 = "806f2df6840f5e65d9a9162226ae7547"
EXPECTED_BYTES = 88971
EXPECTED_ROWS = 206
EXPECTED_COLS = 28  # plus one fully empty trailing column, dropped on load
ZENODO_RECORD = "https://zenodo.org/records/7598463"
ZENODO_DOI = "10.5281/zenodo.7598463"
ZENODO_CONCEPT_DOI = "10.5281/zenodo.7598462"
ZENODO_FILE_URL = "https://zenodo.org/api/records/7598463/files/data%20set%20GaitClass.xlsx/content"
PAPER_DOI = "10.1002/jor.25797"
PAPER_PMID = "38341759"
ETHICS = "EKNZ 2022-01511"

DATASET_TITLE = (
    "Discrete ankle, knee and hip kinematic parameters for overground walking assessed "
    "using inertial sensors in patients with various orthopaedic conditions"
)
DATASET_CITATION = (
    "Nüesch, C., Dammeyer, C., Ismailidis, P., Netzer, C., Egloff, C., Mandelli, F., "
    "Stoffel, K., & Mündermann, A. (2023). " + DATASET_TITLE + " [Dataset]. Zenodo. "
    "https://doi.org/10.5281/zenodo.7598463. License CC BY 4.0."
)

# Codebook text for Group, as written in the sheet "Parameter definition".
CODEBOOK_GROUP_TEXT = (
    "Participant group [1 = healthy; 1 = hip osteoarthritis; 2 = knee osteoarthritis; "
    "3 = lumbar spinal stenosis; 4 = cervical spinal stenosis]"
)

# Group sizes reported in the Zenodo description and in the paper.
REPORTED_GROUP_SIZES = {
    "healthy control": 96,
    "hip OA": 20,
    "knee OA": 30,
    "lumbar stenosis": 43,
    "cervical stenosis": 17,
}

# INFERRED mapping. The codebook lists code 1 twice and never lists code 0.
# Code 0 is assigned to healthy controls because its count (96) matches the reported
# number of controls; codes 1 to 4 follow the codebook and match the reported sizes.
GROUP_MAP_INFERRED = {
    0: "healthy control",
    1: "hip OA",
    2: "knee OA",
    3: "lumbar stenosis",
    4: "cervical stenosis",
}
GROUP_ORDER = list(GROUP_MAP_INFERRED.values())
GROUP_SHORT = {
    "healthy control": "CTRL",
    "hip OA": "HOA",
    "knee OA": "KOA",
    "lumbar stenosis": "LSS",
    "cervical stenosis": "CSS",
}

# Clean analysis names for the raw columns (raw names keep their typos and spaces).
RENAME = {
    "Stance": "StancePct",
    "StanceDIfference": "StanceDifference",
    "HipMininimum": "HipMinimum",
    "DIFF AnkleIC": "AnkleICDifference",
    "KneeMinDifference": "KneeMinimumDifference",
}

ANGLE_COLS = [
    "AnkleIC", "AnklePlantarflexion1", "AnkleDorsalflexion", "AnklePlantarflexion2",
    "KneeMinimum", "KneeIC", "KneeMaximum", "KneeMinimumTO", "HipMinimum", "HipMaximumStance",
]
DIFF_COLS = [
    "AnkleICDifference", "AnklePlantarflexion1Difference", "AnkleDorsalflexionDifference",
    "AnklePlantarflexion2Difference", "KneeMinimumDifference", "KneeICDifference",
    "KneeMaximumDifference", "KneeMinimumTODifference", "HipMinimumDifference",
    "HipMaximumStanceDifference",
]

# Pre-specified primary features for adjusted contrasts (fixed before looking at contrasts).
# KneeMinimum is excluded because its scale is implausible for degrees (see audit).
PRIMARY_FEATURES = [
    "Speed", "StancePct", "KneeIC", "KneeMaximum", "HipMinimum",
    "HipMaximumStance", "AnkleDorsalflexion", "AnklePlantarflexion2",
]

IDENTIFIER_PATTERNS = [
    "name", "birth", "dob", "date", "address", "street", "zip", "postcode", "phone",
    "email", "mail", "mrn", "record", "insurance", "photo", "image", "initial",
]


def md5sum(path: Path = RAW_PATH) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_raw(path: Path = RAW_PATH) -> None:
    """Raise if the raw file is missing or differs from the Zenodo record."""
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run scripts/fetch_data.py first.")
    size = path.stat().st_size
    digest = md5sum(path)
    if digest != EXPECTED_MD5 or size != EXPECTED_BYTES:
        raise ValueError(f"Raw file does not match {ZENODO_DOI}: md5={digest}, bytes={size}")


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    """Sheet 'Dataset' exactly as deposited, minus the fully empty trailing column."""
    verify_raw(path)
    df = pd.read_excel(path, sheet_name="Dataset")
    empty = [c for c in df.columns if str(c).startswith("Unnamed") and df[c].isna().all()]
    return df.drop(columns=empty)


def load_codebook(path: Path = RAW_PATH) -> pd.DataFrame:
    verify_raw(path)
    cb = pd.read_excel(path, sheet_name="Parameter definition")
    cb.columns = [str(c).strip() for c in cb.columns]
    return cb


def identifier_like_columns(columns) -> list[str]:
    out = []
    for c in columns:
        low = str(c).lower().strip()
        if low == "id":
            continue  # sequential study number, checked separately
        if any(p in low for p in IDENTIFIER_PATTERNS):
            out.append(str(c))
    return out


def prepare(raw: pd.DataFrame) -> pd.DataFrame:
    """Strip header whitespace, give clean names, add the inferred group label.

    No values are changed. 'StancePct' is the raw 'Stance' column renamed under the
    documented assumption that it holds percent of the gait cycle, not seconds.
    """
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns=RENAME)
    df["group"] = pd.Categorical(df["Group"].map(GROUP_MAP_INFERRED), categories=GROUP_ORDER)
    df["female"] = (df["Sex"] == 1).astype(int)
    df["patient"] = (df["Group"] != 0).astype(int)
    return df
