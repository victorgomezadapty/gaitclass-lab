"""Integrity, documentation and numeric lock tests for GaitClass Lab."""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gaitclass_lab import analysis as A  # noqa: E402
from gaitclass_lab import audit as AU  # noqa: E402
from gaitclass_lab import data as D  # noqa: E402
from gaitclass_lab import leakage as L  # noqa: E402

PUBLIC_TEXT = ["README.md", "RESULTS.md", "DATA_LICENSE.md", "PROVENANCE.md", "LICENSE"]
FORBIDDEN_DASHES = ["\u2013", "\u2014", "\u2012", "\u2015", "\u2212", "--"]
FORBIDDEN_NAMES = ["optimo", "malqa", "outcare", "riyadh"]


@pytest.fixture(scope="module")
def raw():
    return D.load_raw()


@pytest.fixture(scope="module")
def df(raw):
    return D.prepare(raw)


@pytest.fixture(scope="module")
def summary():
    return json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))


# Integrity

def test_checksum_and_size():
    assert D.RAW_PATH.name == "data set GaitClass.xlsx"
    assert D.RAW_PATH.stat().st_size == 88971
    assert D.md5sum() == "806f2df6840f5e65d9a9162226ae7547"


def test_shape_and_ids(raw):
    assert raw.shape == (206, 28)
    assert sorted(raw["ID"]) == list(range(1, 207))
    assert int(raw.isna().sum().sum()) == 0


def test_no_identifier_columns(raw):
    assert D.identifier_like_columns(raw.columns) == []


def test_codebook_rows():
    assert len(D.load_codebook()) == 28


# Groups and inferred mapping

def test_group_counts(df):
    assert df["Group"].value_counts().sort_index().to_dict() == {0: 96, 1: 20, 2: 30, 3: 43, 4: 17}


def test_codebook_typo_is_real():
    cb = D.load_codebook()
    text = cb.loc[cb["Feature Name"].str.strip() == "Group", "Description"].iloc[0]
    assert "1 = healthy; 1 = hip osteoarthritis" in text
    assert "0 =" not in text


def test_mapping_matches_reported_sizes(df):
    t = AU.group_code_check(df)
    assert t["counts_match"].all()
    assert D.GROUP_MAP_INFERRED[0] == "healthy control"


def test_mapping_documented_as_inferred(summary):
    assert "INFERRED" in summary["group_mapping"]["basis"]
    for name in ["README.md", "RESULTS.md", "DATA_LICENSE.md"]:
        text = (ROOT / name).read_text(encoding="utf-8").lower()
        assert "inferred" in text, name
    assert "never says 0 = healthy" in (ROOT / "RESULTS.md").read_text(encoding="utf-8")


# Audit facts

def test_audit_ranges(df):
    assert 55.8 <= df["StancePct"].min() < 55.9 and 71.7 < df["StancePct"].max() <= 71.8
    assert -0.69 < df["KneeMinimum"].min() < -0.67 and -0.14 < df["KneeMinimum"].max() < -0.12
    assert (df["HipMinimum"] < 0).all()


def test_audit_flags_present(df, raw):
    a = AU.column_audit(df, raw, D.load_codebook())
    flagged = set(a.loc[a["flag"] != "", "column"])
    for c in ["Group", "Speed", "StancePct", "KneeMinimum", "HipMinimum"]:
        assert c in flagged


# Public text rules

def test_no_long_dashes_in_public_text():
    files = [ROOT / n for n in PUBLIC_TEXT] + list((ROOT / "tables").glob("*.csv"))
    files += list((ROOT / "src").rglob("*.py")) + list((ROOT / "scripts").glob("*.py"))
    files += [ROOT / "results" / "summary.json"]
    for f in files:
        text = f.read_text(encoding="utf-8")
        for d in FORBIDDEN_DASHES:
            assert d not in text, f"{f.name} contains {d!r}"


def test_no_forbidden_names():
    files = [ROOT / n for n in PUBLIC_TEXT] + list((ROOT / "src").rglob("*.py"))
    for f in files:
        low = f.read_text(encoding="utf-8").lower()
        for n in FORBIDDEN_NAMES:
            assert n not in low, f"{f.name} mentions {n}"


def test_status_and_attribution(summary):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    kaggle_dataset = "https://www.kaggle.com/datasets/vctorandrsgmezlpez/inertial-gait-kinematics-in-oa-and-stenosis"
    kaggle_notebook = "https://www.kaggle.com/code/vctorandrsgmezlpez/gaitclass-lab-inertial-gait-re-analysis"
    assert "status: public" in readme.lower()
    assert "https://github.com/victorgomezadapty/gaitclass-lab" in readme
    assert kaggle_dataset in readme
    assert kaggle_notebook in readme
    assert "will be added when they are live" not in readme.lower()
    assert {u.rstrip(".,);") for u in re.findall(r"https://www\.kaggle\.com/\S+", readme)} == {kaggle_dataset, kaggle_notebook}
    results = (ROOT / "RESULTS.md").read_text(encoding="utf-8")
    assert "status: public" in results.lower()
    assert "https://github.com/victorgomezadapty/gaitclass-lab" in results
    provenance = (ROOT / "PROVENANCE.md").read_text(encoding="utf-8")
    assert "status: public" in provenance.lower()
    assert "https://github.com/victorgomezadapty/gaitclass-lab" in provenance
    assert kaggle_dataset in provenance
    assert kaggle_notebook in provenance
    assert "will be added when they are live" not in provenance.lower()
    assert {u.rstrip(".,);") for u in re.findall(r"https://www\.kaggle\.com/\S+", provenance)} == {kaggle_dataset, kaggle_notebook}
    assert summary["status"] == "public"
    figure_source = (ROOT / "src" / "gaitclass_lab" / "figures.py").read_text(encoding="utf-8")
    assert "Public re-analysis." in figure_source
    assert D.DATASET_TITLE in readme.replace("\n", " ")
    for name in ["README.md", "DATA_LICENSE.md", "RESULTS.md"]:
        text = (ROOT / name).read_text(encoding="utf-8").replace("\n", " ").replace("> ", "")
        for creator in ["Nüesch, C.", "Dammeyer, C.", "Ismailidis, P.", "Netzer, C.", "Egloff, C.",
                        "Mandelli, F.", "Stoffel, K.", "Mündermann, A."]:
            assert creator in text, (name, creator)
        assert "10.5281/zenodo.7598463" in text
        assert "10.1002/jor.25797" in text
    assert "CC BY-NC-ND 4.0" in (ROOT / "DATA_LICENSE.md").read_text(encoding="utf-8")


def test_no_replication_claim():
    for name in ["README.md", "RESULTS.md"]:
        text = (ROOT / name).read_text(encoding="utf-8").lower()
        assert "not a replication" in text
        assert "82.3" not in text and "51.4" not in text  # paper accuracies are not quoted


def test_webp_twins():
    pngs = sorted((ROOT / "figures").glob("*.png"))
    assert len(pngs) == 6
    for p in pngs:
        assert p.with_suffix(".webp").exists()


# Numeric locks

def test_demographic_locks(summary):
    d = summary["demographics"]
    assert d["healthy control"]["age_mean"] == 62.5
    assert d["knee OA"]["age_mean"] == 69.1
    assert d["lumbar stenosis"]["age_mean"] == 71.0


def test_contrast_locks(df, summary):
    c = summary["contrasts"]
    assert c["n_contrasts_per_model"] == 32
    assert c["significant_holm_unadjusted"] == 19
    assert c["significant_holm_age_sex_adjusted"] == 18
    adj = A.group_contrasts(df, D.PRIMARY_FEATURES, ["Age", "female"], "adj")
    row = adj[(adj.feature == "KneeMaximum") & (adj.group == "knee OA")].iloc[0]
    assert row.difference_vs_control == pytest.approx(-7.823, abs=0.001)


def test_imputation_locks(df, summary):
    cells = L.suspected_cells(df)
    assert int(cells.values.sum()) == 95
    assert int(cells.any(axis=1).sum()) == 38
    a = L.flag_association(df, cells)
    assert (a["controls_flagged"], a["patients_flagged"]) == (27, 11)
    assert summary["imputation"]["original_missingness_recoverable"] is False


def test_leakage_locks(summary):
    lc = summary["leakage_classification"]
    assert lc["B. imputation flag only (no gait, no demographics)"]["auc_mean"] == pytest.approx(0.557, abs=0.002)
    assert lc["A. demographics only (age, sex, BMI)"]["auc_mean"] == pytest.approx(0.699, abs=0.002)
    assert lc["C. gait features, standard CV"]["auc_mean"] == pytest.approx(0.777, abs=0.002)


def test_readme_numbers_match_summary(summary):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    lc = summary["leakage_classification"]
    for v in [lc["B. imputation flag only (no gait, no demographics)"]["auc_mean"],
              lc["A. demographics only (age, sex, BMI)"]["auc_mean"],
              lc["C. gait features, standard CV"]["auc_mean"]]:
        assert f"{v:.3f}" in readme
    c = summary["contrasts"]
    assert f"{c['significant_holm_unadjusted']} pass Holm" in readme
    assert re.search(rf"{c['significant_holm_age_sex_adjusted']} after\s+age and sex", readme)
