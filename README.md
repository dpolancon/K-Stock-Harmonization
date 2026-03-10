# K-Stock-Harmonization

Stock-flow consistent capital-stock harmonization for Chile, 1900-1994.

## Repository status

- Frozen accounting reference: Hofman-only baseline in constant 1980 CLP.
- Canonical harmonized baseline: Perez FBKF excluding inventories in constant 2003 CLP.
- Deferred but documented sources: BCCH, ClioLab, and Tafunell remain outside the production baseline in v1.

## Canonical command

Run:

`python codes/run_harmonization.py`

This command writes the public harmonized baseline to:

`outputs/HARMONIZED_PEREZ_2003CLP_v1/`

Required artifacts:

- `harmonized_series_2003CLP_1900_1994.csv`
- `harmonized_series_2003CLP_1900_1994.xlsx`
- `assumptions.yaml`
- `overlap_audit_summary.txt`
- `audit_summary_full_1900_1994.txt`
- `violation_log.csv`
- `summary.md`

## Baseline distinction

The repo keeps two distinct baselines:

- Frozen Hofman accounting reference in 1980 CLP.
  - Main artifacts: `outputs/harmonized_series_1980CLP_1900_1994.csv`, `outputs/survival_fit_hofman_1980.csv`, `outputs/assumptions_baseline_1980.yaml`.
- Canonical Perez harmonized baseline in 2003 CLP.
  - Production surface: `codes/run_harmonization.py`.
  - Control concept: Perez machinery plus construction only.
  - Ex-inventories means excluding inventories, not ex post.

Inventories are excluded from accumulation because the production pipeline models fixed capital only (`ME`, `NRC`, `RC`).

## Documentation

Long-form reverse documentation lives in `docs/`:

- `docs/index.md`
- `docs/notation.md`
- `docs/data-landscape.md`
- `docs/baseline-hofman.md`
- `docs/harmonized-perez.md`
- `docs/validation.md`
- `docs/source-reconciliation.md`
- `docs/code-map.md`
- `docs/reproducibility.md`

## Reproducibility contract

`outputs/HARMONIZED_PEREZ_2003CLP_v1/assumptions.yaml` records:

- canonical command
- git commit
- repo clean/dirty status at generation time
- Python version
- SHA256 hashes of all required pipeline inputs

The Excel workbook is a one-sheet serialization of the same long canonical panel published in the CSV. It does not introduce reshaping or additional reporting logic.

`output/` may contain presentation derivatives such as PDFs, but it is not the public interface of the baseline.

## Citation

Citation metadata is in `CITATION.cff`.
