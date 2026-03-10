# Release Note: v1.0.0

This release establishes the first canonical, citable harmonized baseline in this repository. It promotes the Perez-based `FBKF ex inventories` production path in constant `2003 CLP`, while preserving the Hofman-only `1980 CLP` baseline as a frozen accounting reference.

## Release scope

- Canonical production command: `python codes/run_harmonization.py`
- Canonical public artifact bundle: `outputs/HARMONIZED_PEREZ_2003CLP_v1/`
- Frozen accounting reference retained: `outputs/harmonized_series_1980CLP_1900_1994.csv`
- Reverse-documentation corpus added under `docs/`
- Citation metadata added in `CITATION.cff`

## Canonical methodology locked in this release

- Primary price space: `2003 CLP`
- Control concept: `FBKF ex inventories`
- Inventory treatment: inventories are excluded from fixed-capital accumulation
- Aggregate Perez investment is scaled by `lambda_choice` from `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/lambda_estimates.yaml`
- Asset split is derived from normalized Hofman investment shares
- Survival parameters are reused from the frozen Hofman baseline fit

## Validation status

- Overlap audit `1950-1994`: `PASS`
- Full-period audit `1900-1994`: `PASS`
- Regression check against extension-candidate outputs: `PASS`
- Canonical output bundle reproducibility across consecutive reruns: `PASS`

## Included canonical artifacts

- `outputs/HARMONIZED_PEREZ_2003CLP_v1/harmonized_series_2003CLP_1900_1994.csv`
- `outputs/HARMONIZED_PEREZ_2003CLP_v1/harmonized_series_2003CLP_1900_1994.xlsx`
- `outputs/HARMONIZED_PEREZ_2003CLP_v1/assumptions.yaml`
- `outputs/HARMONIZED_PEREZ_2003CLP_v1/overlap_audit_summary.txt`
- `outputs/HARMONIZED_PEREZ_2003CLP_v1/audit_summary_full_1900_1994.txt`
- `outputs/HARMONIZED_PEREZ_2003CLP_v1/violation_log.csv`
- `outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md`

## Deferred sources

The following sources remain documented but deferred from the v1 production baseline:

- `BCCH_1985_2024.xlsx`
- `BCCH_ref2018_Pk.xlsx`
- `ClioLab_GFKF_Freal_nominal_Pk.xlsx`
- `Kn_ClioLab.xlsx`
- `Tafunell_Ducoing_2016_Kg.xlsx`
- `tafunel_2013_Ig.xlsx`

## Dissertation and paper use

This release is intended to support dissertation-grade traceability. Claims about concepts, transformations, admissibility, and source scope should be backed by the code, documentation, and committed artifacts included in this tagged state.
