# Data license and attribution

## Data

The only data used in this project is the following Zenodo deposit:

> Nüesch, C., Dammeyer, C., Ismailidis, P., Netzer, C., Egloff, C., Mandelli, F., Stoffel, K., &
> Mündermann, A. (2023). Discrete ankle, knee and hip kinematic parameters for overground walking
> assessed using inertial sensors in patients with various orthopaedic conditions [Dataset].
> Zenodo. https://doi.org/10.5281/zenodo.7598463

* License: Creative Commons Attribution 4.0 International (CC BY 4.0),
  https://creativecommons.org/licenses/by/4.0/ (Zenodo license id `cc-by-4.0`, access `open`).
* File: `data/raw/data set GaitClass.xlsx`, unmodified copy of the Zenodo file
  (md5 `806f2df6840f5e65d9a9162226ae7547`).
* The tables in `tables/`, figures in `figures/`, `results/summary.json` and `RESULTS.md` are
  derived from this dataset and are shared under the same CC BY 4.0 terms with the attribution
  above.

### Changes made (CC BY 4.0 section 3(a)(1)(B))

* Header whitespace stripped and five columns renamed for analysis (`Stance` to `StancePct`,
  `StanceDIfference` to `StanceDifference`, `HipMininimum` to `HipMinimum`, `DIFF AnkleIC` to
  `AnkleICDifference`, `KneeMinDifference` to `KneeMinimumDifference`). Values unchanged.
* Group codes labelled with an inferred mapping (0 = healthy control, 1 = hip OA, 2 = knee OA,
  3 = lumbar stenosis, 4 = cervical stenosis). The codebook lists code 1 twice; the mapping for
  code 0 is inferred from the reported group sizes.
* `Stance` analysed as percent of the gait cycle, against the codebook unit "seconds".
* `KneeMinimum` and `KneeMinimumDifference` excluded from models because of an implausible scale.
* Aggregation, statistical modelling and an audit of repeated values. No rows were added,
  removed or edited in the raw file. Sensitivity analyses drop flagged rows in memory only.

The creators and the licensor do not endorse this project or its interpretation.

## Related article (different license)

> Dammeyer, C., Nüesch, C., Visscher, R. M. S., Kim, Y. K., Ismailidis, P., Wittauer, M.,
> Stoffel, K., Acklin, Y., Egloff, C., Netzer, C., & Mündermann, A. (2024). Classification of
> inertial sensor-based gait patterns of orthopaedic conditions using machine learning: A pilot
> study. Journal of Orthopaedic Research, 42(7), 1463 to 1472. https://doi.org/10.1002/jor.25797

The article is licensed CC BY-NC-ND 4.0, which differs from the dataset license. It is cited
only. No text, tables or figures from it are reproduced here, and it is not a data source.

## Code

The code in this project is licensed under the MIT License (see `LICENSE`). The MIT license
does not apply to the data or derived results.

## No other data

No other dataset is used, merged or referenced as input. Adding another source would require
a new license review first.
