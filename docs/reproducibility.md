## Master reproduction command

To execute all three production stages in sequence and verify full audit compliance in a single command, run:

`python run_all.py`

This master runner executes the frozen Hofman 1980 baseline, the canonical Perez 2003 baseline, and the additive BCCh extension bundle, and verifies that all required output files exist and pass admissibility audits.

## Canonical `1900-1994` command

Run:

`python codes/run_harmonization.py`

Expected output directory:

`outputs/HARMONIZED_PEREZ_2003CLP_v1/`

Required inputs:

- `data/raw/PerezEyzaguirre_DemandaAgregada.xlsx`
- `data/raw/Hofman2000_GrossInvestment.xlsx`
- `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/lambda_estimates.yaml`
- `outputs/survival_fit_hofman_1980.csv`
- `outputs/harmonized_series_1980CLP_1900_1994.csv`

## Additive BCCh `1900-2024` command

Run:

`python codes/run_harmonization_bcch.py`

Expected output directory:

`outputs/HARMONIZED_BCCH_2003CLP_v1/`

Required inputs:

- `outputs/HARMONIZED_PEREZ_2003CLP_v1/harmonized_series_2003CLP_1900_1994.csv`
- `outputs/survival_fit_hofman_1980.csv`
- `data/raw/BCCH_1985_2024.xlsx`
- `data/raw/BCCH_ref2018_Pk.xlsx`
- `data/raw/ClioLab_GFKF_Freal_nominal_Pk.xlsx`
- `data/raw/Kn_ClioLab.xlsx`

The BCCh assumptions file records hashes for all of them in `outputs/HARMONIZED_BCCH_2003CLP_v1/assumptions.yaml`.

## Required provenance fields

Both public assumptions files record:

- `git_commit`
- `generated_at_utc`
- `python_version`
- `command`
- `repo_status`
- `input_hashes`

The BCCh bundle also records:

- `bridge_factors_1994`
- `bcch_start_year`
- `pk_splice_rule`
- source-quality flags for recent BCCh years

`generated_at_utc` is stable across repeated runs when no substantive artifact content changes. This makes both public output bundles idempotent under rerun.

## Expected run result

The canonical Perez command is expected to:

- exit with code `0`
- report pass on overlap admissibility
- report pass on full-period admissibility
- report pass on regression against the extension candidate path

The BCCh extension command is expected to:

- exit with code `0`
- preserve every `1900-1994` row from the canonical Perez panel exactly
- report pass on the BCCh bridge extraction audit
- report pass on the full-period `1900-2024` admissibility audit
- report pass on `Pk(2003)=100` and continuous `1940-2024` coverage

These outcomes are written to `summary.md` and the audit text files in each output directory.
