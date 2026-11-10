# Data provenance

| Field | Value |
|-|-|
| Source | Zenodo record 7598463 (https://zenodo.org/records/7598463) |
| Version DOI | 10.5281/zenodo.7598463 |
| Concept DOI | 10.5281/zenodo.7598462 (one version only, checked 10 Nov 2026) |
| Title | Discrete ankle, knee and hip kinematic parameters for overground walking assessed using inertial sensors in patients with various orthopaedic conditions |
| Short name | "GaitClass" comes only from the file name; it is not the deposit title |
| Creators | Nüesch, Corina; Dammeyer, Constanze; Ismailidis, Petros; Netzer, Cordula; Egloff, Christian; Mandelli, Filippo; Stoffel, Karl; Mündermann, Annegret (University Hospital Basel) |
| Published on Zenodo | 2023-02-02 |
| License | CC BY 4.0 (Zenodo license id `cc-by-4.0`, access `open`, files public, no embargo) |
| File | `data set GaitClass.xlsx` (the name contains spaces) |
| Download URL | https://zenodo.org/api/records/7598463/files/data%20set%20GaitClass.xlsx/content |
| md5 | `806f2df6840f5e65d9a9162226ae7547` (matches the checksum published by Zenodo) |
| Size | 88971 bytes |
| Sheets | `Dataset` (206 rows x 28 columns plus one empty column), `Parameter definition` (codebook, 28 rows) |
| Other workbook content | A tiny embedded image and an ink annotation (drawing overlay, no people); Office metadata names two dataset authors as file creator and last editor |
| Identifiers | No names, dates, contact data, record numbers or photos of people. ID is a sequential study number |
| Ethics | Ethics Committee Northwest Switzerland, EKNZ 2022-01511, signed informed consent (as reported in the companion paper) |
| Trial registration | None found (retrospective pooling of earlier projects) |
| Companion paper | Dammeyer C, Nüesch C, Visscher RMS, et al. J Orthop Res 2024;42(7):1463 to 1472. https://doi.org/10.1002/jor.25797, PMID 38341759. License CC BY-NC-ND 4.0 |
| Link between deposit and paper | Inferred, not stated: the Zenodo record has no related identifiers, and no data availability statement pointing to it was seen in the paper. Same research group, same n = 206 and same group sizes |

## How the local copy was made

The workbook was downloaded from the Zenodo API into a separate license check folder on
10 Nov 2026 and then copied (not moved) into `data/raw/`. The md5 was verified on both copies.
The file in `data/raw/` is never edited.

## Rules for this project

1. This Zenodo file is the only data source. Nothing else is merged or used as data. The paper
   is used only for attribution, for the ethics reference and to avoid false replication claims.
   No text, tables or figures from the paper are reproduced.
2. The md5 and size are checked every time the data are loaded (`gaitclass_lab.data.verify_raw`),
   in the analysis script and in the tests. The analysis stops if they do not match.
3. Outputs are aggregates, except `tables/t08_shared_values_imputation_footprints.csv`, which lists
   study ID numbers next to repeated values so the imputation audit can be checked. It contains no
   demographics.
4. Attribution as in `DATA_LICENSE.md` must accompany any reuse of the data or derived results.
5. Status: public. The analysis repository is public at https://github.com/victorgomezadapty/gaitclass-lab. Kaggle links will be added when they are live.
