# Validation and Admissibility

This document describes how the repository validates its two public 2003-CLP publication surfaces and how those checks should be interpreted.

## Canonical Perez baseline

The canonical `1900-1994` pipeline in `codes/run_harmonization.py` keeps the original validation contract:

- overlap admissibility on `1950-1994`
- full-period admissibility on `1900-1994`
- regression alignment against the validated extension-candidate path

The committed results are recorded in:

- `outputs/HARMONIZED_PEREZ_2003CLP_v1/overlap_audit_summary.txt`
- `outputs/HARMONIZED_PEREZ_2003CLP_v1/audit_summary_full_1900_1994.txt`
- `outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md`

## BCCh bridge audit

The additive BCCh bundle introduces a bridge-specific validation layer before the `1995-2024` stock extension is accepted.

The bridge audit checks:

- BCCh raw component sums match BCCh published totals in sheets `1` and `2`
- the asset crosswalk to `RC`, `NRC`, `ME` is additively consistent
- the `1994` hard anchor preserves the legacy `1900-1994` panel exactly
- overlap ratio diagnostics are written for `Kn` and `D` over `1985-1994`

These results are written to:

- `outputs/HARMONIZED_BCCH_2003CLP_v1/bcch_bridge_audit_summary_1985_1994.txt`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/bcch_bridge_diagnostics.csv`

## BCCh full-period admissibility

The additive `1900-2024` bundle checks:

- no negative `Kg`
- no negative `Kn`
- no negative `B`
- no additivity failures
- no identity residual failures
- no rate out-of-bounds observations over the full span, including `1995-2024`

The current committed result is written to:

- `outputs/HARMONIZED_BCCH_2003CLP_v1/audit_summary_full_1900_2024.txt`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/summary.md`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/violation_log.csv`

## Pk splice checks

The BCCh companion deflator bundle checks:

- continuous coverage from `1940` to `2024`
- `Pk(2003)=100`
- a single source switch at `1960`
- ratio-only diagnostics for rebasing, chained Clio `1940-1959` growth, and year-quality flags

These results are written to:

- `outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_pk_2003base_1940_2024.csv`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/pk_splice_diagnostics.csv`

The production deflator for `1960-2024` is the ratio `FBKF_nom / FBKF_real`, rebased to `2003=100`. `pk_splice_diagnostics.csv` documents that ratio build rather than an alternative workbook field.
