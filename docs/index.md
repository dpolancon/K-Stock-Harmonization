# Reverse Documentation Index

This repository exposes two citable 2003-CLP publication surfaces plus a frozen Hofman accounting reference. The documentation set is designed so claims about concepts, inputs, transformations, and validation remain traceable to versioned code and committed artifacts.

## Canonical repository objects

- Frozen accounting reference: `codes/run_baseline_hofman_1980.py` and `outputs/harmonized_series_1980CLP_1900_1994.csv`
- Canonical harmonized baseline: `codes/run_harmonization.py` and `outputs/HARMONIZED_PEREZ_2003CLP_v1/`
- Additive BCCh extension bundle: `codes/run_harmonization_bcch.py` and `outputs/HARMONIZED_BCCH_2003CLP_v1/`
- Citation metadata: `CITATION.cff`

## How to use this documentation

- Read `docs/notation.md` for variables, aggregates, and price-space conventions.
- Read `docs/data-landscape.md` for active, diagnostic, and deferred sources.
- Read `docs/baseline-hofman.md` for the frozen accounting reference.
- Read `docs/harmonized-perez.md` for the promoted `1900-1994` production baseline.
- Read `docs/harmonized-bcch.md` for the additive `1900-2024` BCCh extension bundle.
- Read `docs/validation.md` for admissibility, bridge, and splice checks.
- Read `docs/source-reconciliation.md` for how Perez, BCCh, ClioLab, and Tafunell are positioned.
- Read `docs/code-map.md` for the script-to-output map.
- Read `docs/reproducibility.md` for command-level provenance and rerun expectations.
- Read `docs/release-v1.0.0.md` and `docs/release-v1.1.0.md` for the release-scoped status of the public surfaces.

## What is citable

The public baseline artifact bundle is `outputs/HARMONIZED_PEREZ_2003CLP_v1/`. It contains the canonical `1900-1994` harmonized panel, machine-readable provenance, and audit summaries.

The public BCCh extension bundle is `outputs/HARMONIZED_BCCH_2003CLP_v1/`. It contains the additive `1900-2024` stock panel, the companion `Pk` series for `1940-2024`, machine-readable provenance, and BCCh-specific diagnostics.

The frozen Hofman 1980 baseline remains citable as the accounting reference against which both 2003-CLP publication surfaces are defined and checked.

## Evidence discipline

This documentation avoids undocumented inferences. When a point is not established by active code or committed outputs, it should be treated as not established from repository evidence.
