# Reverse Documentation Index

This repository now exposes a citable canonical harmonized baseline for Chilean capital stocks in constant 2003 CLP, while preserving a frozen Hofman-only accounting reference in constant 1980 CLP. The purpose of this documentation set is to make every major claim traceable to versioned code or versioned artifacts already present in the repository.

## Canonical repository objects

- Frozen accounting reference: `codes/run_baseline_hofman_1980.py` and `outputs/harmonized_series_1980CLP_1900_1994.csv`
- Canonical harmonized baseline: `codes/run_harmonization.py` and `outputs/HARMONIZED_PEREZ_2003CLP_v1/`
- Citation metadata: `CITATION.cff`

## How to use this documentation

- Read `docs/notation.md` for variables, asset groups, and price spaces.
- Read `docs/data-landscape.md` for source coverage and current usage.
- Read `docs/baseline-hofman.md` for the frozen accounting reference.
- Read `docs/harmonized-perez.md` for the promoted production baseline.
- Read `docs/validation.md` for admissibility and audit interpretation.
- Read `docs/source-reconciliation.md` for the treatment of Perez, BCCH, ClioLab, and Tafunell sources.
- Read `docs/code-map.md` for the script-to-output map.
- Read `docs/reproducibility.md` for the execution contract and provenance fields.

## What is citable

The public baseline artifact bundle is `outputs/HARMONIZED_PEREZ_2003CLP_v1/`. It contains the harmonized panel, machine-readable provenance, and the human-readable audit summaries needed to support dissertation or paper claims.

The frozen Hofman 1980 baseline remains citable as the accounting reference against which the promoted harmonized baseline is defined and checked.

## Evidence discipline

This documentation intentionally avoids undocumented inferences about methodology. When a point is not established by active code or committed outputs, it is marked as not established from repository evidence.
