# Validation and Admissibility

This document describes how the repository currently validates the promoted harmonized baseline and how those checks should be interpreted in dissertation or paper writing.

## Overlap admissibility

The overlap window is 1950-1994. For each asset and aggregate (`ME`, `NRC`, `RC`, `NR`, `Total`), the canonical pipeline checks:

- negative retirements
- negative depreciation
- retirement rates outside `[0, 1]`
- depreciation rates outside `[0, 1]`

The current canonical run writes these results to `outputs/HARMONIZED_PEREZ_2003CLP_v1/overlap_audit_summary.txt`.

## Full-period admissibility

The full publication window is 1900-1994. The canonical pipeline checks:

- no negative `Kg`
- no negative `Kn`
- no negative `B`
- no additivity failures
- no identity residual failures
- no rate out-of-bounds observations, including the pre-1950 period

The current repository setting is strict: `EARLY_RATE_OUT_MAX = 0` in `codes/run_harmonization.py`.

## Regression requirement

The promoted pipeline is not allowed to drift materially from the already validated extension candidate path. `codes/run_harmonization.py` compares the canonical run against:

- `outputs/EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/`
- `outputs/EXTENSION_CANDIDATE_STOCKS_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/`

If the max absolute difference exceeds the configured tolerances, the command exits with failure.

## Current canonical status

The current committed canonical output bundle records:

- overlap admissibility: pass
- full-period admissibility: pass
- regression against extension candidate: pass

These statuses are summarized in `outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md`.
