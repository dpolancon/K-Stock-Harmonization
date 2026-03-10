# Reproducibility

This repository is reproducible at the canonical-baseline level through a committed command and a committed artifact bundle.

## Canonical command

Run:

`python codes/run_harmonization.py`

Expected output directory:

`outputs/HARMONIZED_PEREZ_2003CLP_v1/`

## Required inputs

The canonical pipeline depends on the following inputs:

- `data/raw/PerezEyzaguirre_DemandaAgregada.xlsx`
- `data/raw/Hofman2000_GrossInvestment.xlsx`
- `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/lambda_estimates.yaml`
- `outputs/survival_fit_hofman_1980.csv`
- `outputs/harmonized_series_1980CLP_1900_1994.csv`

The pipeline records SHA256 hashes for all of them in `outputs/HARMONIZED_PEREZ_2003CLP_v1/assumptions.yaml`.

## Required provenance fields

The canonical assumptions file records:

- `git_commit`
- `generated_at_utc`
- `python_version`
- `command`
- `repo_status`
- `input_hashes`

`generated_at_utc` is stable across repeated runs when no substantive artifact content changes. This makes the canonical output bundle idempotent under rerun, which is required for merge-time reproducibility checks.

## Expected run result

The canonical command is expected to:

- exit with code 0
- report pass on overlap admissibility
- report pass on full-period admissibility
- report pass on regression against the extension candidate path

These outcomes are written to `summary.md`, `overlap_audit_summary.txt`, and `audit_summary_full_1900_1994.txt` in the canonical output directory.
