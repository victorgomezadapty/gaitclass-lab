# GaitClass Lab

A transparent, reproducible re-analysis of an open table of gait kinematics from people with
hip or knee osteoarthritis (OA), lumbar or cervical spinal stenosis, and healthy controls,
measured with inertial sensors.

**Status: public.** The analysis repository is public at
https://github.com/victorgomezadapty/gaitclass-lab. Kaggle links will be added when they are live.

## About the name

The deposit's official title is *Discrete ankle, knee and hip kinematic parameters for overground
walking assessed using inertial sensors in patients with various orthopaedic conditions*
(Zenodo, DOI 10.5281/zenodo.7598463). "GaitClass" is only the short name taken from the
deposited file (`data set GaitClass.xlsx`) and used as this project's short name.

## What this project is

* A re-analysis of one open dataset (Zenodo, CC BY 4.0): 206 participants, one row each, with
  age, sex, BMI, walking speed, stance and sagittal hip, knee and ankle angles of the "affected"
  side plus side differences. Values are per participant means; there are no raw sensor signals.
* An audit of the codebook against the values, with every mismatch flagged and none silently fixed.
* Descriptive statistics by group with 95% CIs, and age and sex adjusted group contrasts for a
  pre-specified set of 8 features.
* A check of how the depositors' gap filling (imputation) could leak group information into
  any analysis, with a leakage aware sensitivity analysis.

## What this project is not

* Not a new clinical study, and not a diagnostic or screening tool.
* Not a replication of the companion paper's machine learning classifier. The paper's accuracies
  are not reproduced, compared or "beaten" here.
* Not a reuse of the paper's content. The paper (CC BY-NC-ND 4.0) is cited only.

## From the deposit, inferred, added

| Item | Source |
|-|-|
| 206 rows, group codes, values, codebook text, imputation method description | Deposit |
| Group code 0 = healthy control | **Inferred** from reported group sizes (the codebook lists code 1 twice) |
| Stance read as % of gait cycle, KneeMinimum scale treated as unknown | **Inferred** from value ranges |
| Ethics reference, participant flow, affected side rule, steps per trial | Companion paper (cited, not copied) |
| Audit tables, adjusted contrasts, imputation footprints, leakage analysis | Added by this project |

## Main results

All numbers are in [RESULTS.md](RESULTS.md) and `results/summary.json`.

* n = 206 by code: 0 = 96, 1 = 20, 2 = 30, 3 = 43, 4 = 17, matching the reported sizes. Mapping
  0 = healthy control, 1 = hip OA, 2 = knee OA, 3 = lumbar stenosis, 4 = cervical stenosis is
  inferred.
* 11 columns carry a data quality flag. Stance is labelled seconds but ranges 55.83 to 71.77;
  KneeMinimum ranges -0.68 to -0.13, implausible as degrees; HipMinimum is described as
  "Global hip maximum" although every value is negative.
* Controls are younger (mean age 62.5) than knee OA (69.1) and lumbar stenosis (71.0) and are not
  age matched. Patients had advanced disease (surgical candidates), so results do not describe
  early disease.
* Of 32 pre-specified group by feature contrasts, 19 pass Holm correction unadjusted, 18 after
  age and sex adjustment, 15 with BMI added and 15 after removing rows with imputation footprints.
  The largest adjusted differences are lower peak knee flexion in stance in knee OA (-7.82 degrees,
  95% CI -9.99 to -5.66) and lumbar stenosis (-4.67, -6.82 to -2.51).
* Imputation footprints (values repeated with about 15 decimals, or exact 0.0 side differences) are
  found in 38 rows: 27 of 96 controls and 11 of 110 patients (OR 3.52, Fisher p 0.001). One value
  is shared by 15 controls and 4 knee OA patients. The original missingness cannot be recovered.
* Leakage sensitivity (healthy vs patient, not a diagnostic model): the imputation flag alone
  gives AUC 0.557; demographics alone 0.699; gait features 0.777 with standard cross validation,
  0.768 cluster aware, 0.757 with flagged rows removed.

## Project layout

| Path | Content |
|-|-|
| `data/raw/data set GaitClass.xlsx` | Unmodified Zenodo file (CC BY 4.0), md5 checked on every load |
| `src/gaitclass_lab/` | `data` (load, checksum, labels), `audit`, `analysis`, `leakage`, `figures`, `report` |
| `scripts/run_analysis.py` | Runs everything and regenerates `tables/`, `figures/`, `results/summary.json`, `RESULTS.md` |
| `scripts/fetch_data.py` | Re-downloads the file from Zenodo only if missing, then checks the md5 |
| `tests/` | Integrity, mapping, documentation and numeric lock tests |
| `tables/` | 11 CSV tables (aggregates; t08 lists study IDs for the imputation audit) |
| `figures/` | 6 figures as PNG with WebP twins |
| `DATA_LICENSE.md`, `PROVENANCE.md`, `LICENSE` | Source, licenses, hash, attribution and changes |

## How to run

Python 3.13.5 was used. From the project root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/run_analysis.py
.venv/bin/python -m pytest -q
```

Everything runs offline on the local workbook in about 10 seconds. Cross validation uses fixed
seeds, so reruns give the same numbers on the same library versions.

## Methods in brief

* md5 and byte size verified before every load; the analysis stops on mismatch.
* Means with t based 95% CIs, medians and IQRs; Wilson CIs for proportions; Kruskal Wallis and
  chi square tests for group differences in age, BMI and sex.
* Contrasts: OLS per feature with group (reference healthy control), age and sex; HC3 robust
  standard errors; Holm correction across 32 contrasts. Sensitivity: plus BMI, and without
  flagged rows. Speed is not a covariate because it lies on the causal pathway.
* Imputation footprints: repeated high precision values within a column, and exact 0.0 side
  differences. Leakage analysis: logistic regression and 1 nearest neighbour, stratified 5 fold
  cross validation repeated 20 times, with and without grouping rows that share imputed values.

## Limitations

Retrospective data from one research group and one sensor system, sagittal plane only, small
and unequal groups, controls younger and leaner, advanced disease only, codebook errors
resolved by stated assumptions, imputed values that cannot all be identified, and an affected
side rule that differs between OA groups and the other groups. Details in
[RESULTS.md](RESULTS.md#9-limitations).

## Data, citation and license

Data: Nüesch, C., Dammeyer, C., Ismailidis, P., Netzer, C., Egloff, C., Mandelli, F., Stoffel, K.,
& Mündermann, A. (2023). Discrete ankle, knee and hip kinematic parameters for overground walking
assessed using inertial sensors in patients with various orthopaedic conditions [Dataset]. Zenodo.
https://doi.org/10.5281/zenodo.7598463. License CC BY 4.0.

Companion paper (cite only, CC BY-NC-ND 4.0): Dammeyer C, Nüesch C, Visscher RMS, et al.
Classification of inertial sensor-based gait patterns of orthopaedic conditions using machine
learning: A pilot study. J Orthop Res. 2024;42(7):1463 to 1472. https://doi.org/10.1002/jor.25797.
PMID 38341759. Ethics: EKNZ 2022-01511.

This is the only data source. Code: MIT (`LICENSE`). Data and derived outputs: CC BY 4.0
(`DATA_LICENSE.md`). The creators do not endorse this re-analysis.
