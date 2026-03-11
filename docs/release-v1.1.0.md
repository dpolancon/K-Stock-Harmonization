# Release Note: v1.1.0

This release adds a new, non-breaking BCCh extension bundle to the repository. It does not replace the canonical Perez `1900-1994` surface established in `v1.0.0`.

## Release scope

- New additive production command: `python codes/run_harmonization_bcch.py`
- New public artifact bundle: `outputs/HARMONIZED_BCCH_2003CLP_v1/`
- Legacy canonical surface retained unchanged: `outputs/HARMONIZED_PEREZ_2003CLP_v1/`
- New documentation surface: `docs/harmonized-bcch.md`

## Methodology added in this release

- Preserve every canonical `1900-1994` row exactly from the Perez harmonized panel.
- Parse BCCh real `Kn` and `D` by asset from `data/raw/BCCH_1985_2024.xlsx`.
- Apply a `1994` hard-anchor bridge by asset on `Kn`, with the same factor applied to `D`.
- Infer `1995-2024` real investment from scaled BCCh `Kn` and `D`.
- Reuse frozen Hofman survival parameters to reconstruct `Kg` and `R` through `2024`.
- Publish a companion `Pk` series using the BCCh ratio deflator (`FBKF_nom / FBKF_real`) for `1960-2024` and chained ClioLab ratio growth for `1940-1959`.

## Validation status

- Legacy `1900-1994` history preserved exactly: `PASS`
- BCCh raw extraction add-up audit: `PASS`
- Full-period admissibility `1900-2024`: `PASS`
- Rate bounds `1995-2024`: `PASS`
- `Pk(2003)=100` and continuous `1940-2024` coverage: `PASS`

## Included BCCh artifacts

- `outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_series_2003CLP_1900_2024.csv`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_series_2003CLP_1900_2024.xlsx`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_pk_2003base_1940_2024.csv`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_pk_2003base_1940_2024.xlsx`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/assumptions.yaml`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/bcch_bridge_audit_summary_1985_1994.txt`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/audit_summary_full_1900_2024.txt`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/violation_log.csv`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/bcch_bridge_diagnostics.csv`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/pk_splice_diagnostics.csv`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/summary.md`

## Interpretation note

The BCCh extension is additive. It extends the validated real harmonization forward without reopening the canonical Perez resolution for `1900-1994`. The production deflator is the ratio `FBKF_nom / FBKF_real`, and `pk_splice_diagnostics.csv` is limited to ratio-build diagnostics for rebasing, chaining, source flags, and the single `1960` switch.
