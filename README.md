# K-Stock-Harmonization

Stock-flow consistent capital-stock harmonization for Chile.

## Repository status

- Frozen accounting reference: Hofman-only baseline in constant 1980 CLP.
- Canonical harmonized baseline: Perez FBKF excluding inventories in constant 2003 CLP for `1900-1994`.
- Additive BCCh extension bundle: BCCh-forward extension in constant 2003 CLP for `1900-2024`, preserving the `1900-1994` canonical history exactly.
- Diagnostic-only sources: `Kn_ClioLab.xlsx` and BCCh total real FBKF are retained for audit use, not as primary production inputs.
- Deferred source family: Tafunell remains outside the active production surfaces.

## Production commands

### Canonical v1 baseline

Run:

`python codes/run_harmonization.py`

This command writes the canonical baseline to:

`outputs/HARMONIZED_PEREZ_2003CLP_v1/`

Required artifacts:

- `harmonized_series_2003CLP_1900_1994.csv`
- `harmonized_series_2003CLP_1900_1994.xlsx`
- `assumptions.yaml`
- `overlap_audit_summary.txt`
- `audit_summary_full_1900_1994.txt`
- `violation_log.csv`
- `summary.md`

### BCCh extension bundle

Run:

`python codes/run_harmonization_bcch.py`

This command writes the additive BCCh bundle to:

`outputs/HARMONIZED_BCCH_2003CLP_v1/`

Required artifacts:

- `harmonized_series_2003CLP_1900_2024.csv`
- `harmonized_series_2003CLP_1900_2024.xlsx`
- `harmonized_pk_2003base_1940_2024.csv`
- `harmonized_pk_2003base_1940_2024.xlsx`
- `assumptions.yaml`
- `bcch_bridge_audit_summary_1985_1994.txt`
- `audit_summary_full_1900_2024.txt`
- `violation_log.csv`
- `bcch_bridge_diagnostics.csv`
- `pk_splice_diagnostics.csv`
- `summary.md`

## Surface distinction

The repo now keeps three public surfaces:

- Frozen Hofman accounting reference in 1980 CLP.
  - Main artifacts: `outputs/harmonized_series_1980CLP_1900_1994.csv`, `outputs/survival_fit_hofman_1980.csv`, `outputs/assumptions_baseline_1980.yaml`.
- Canonical Perez harmonized baseline in 2003 CLP.
  - Production surface: `codes/run_harmonization.py`.
  - Control concept: Perez machinery plus construction only.
  - Inventories are excluded from accumulation.
- Additive BCCh extension bundle in 2003 CLP.
  - Production surface: `codes/run_harmonization_bcch.py`.
  - Legacy `1900-1994` rows are preserved exactly from the canonical Perez bundle.
  - BCCh net stocks and depreciation extend the series from `1995` onward.
- The companion `Pk` series uses the ratio deflator (`FBKF_nom / FBKF_real`) for BCCh `1960-2024` and chained ClioLab ratio growth for `1940-1959`.

## Documentation

Long-form reverse documentation lives in `docs/`:

- `docs/index.md`
- `docs/notation.md`
- `docs/data-landscape.md`
- `docs/baseline-hofman.md`
- `docs/harmonized-perez.md`
- `docs/harmonized-bcch.md`
- `docs/validation.md`
- `docs/source-reconciliation.md`
- `docs/code-map.md`
- `docs/reproducibility.md`
- `docs/release-v1.0.0.md`
- `docs/release-v1.1.0.md`

## Reproducibility contract

Both public output bundles write machine-readable provenance:

- `outputs/HARMONIZED_PEREZ_2003CLP_v1/assumptions.yaml`
- `outputs/HARMONIZED_BCCH_2003CLP_v1/assumptions.yaml`

These files record the production command, git commit, repo clean/dirty status, Python version, and SHA256 hashes for required inputs.

The Excel workbooks are one-sheet serializations of the published CSV outputs. They do not introduce reshaping or additional reporting logic.

`output/` may contain presentation derivatives such as PDFs, but it is not a public data interface.

## Citation

Citation metadata is in `CITATION.cff`.
