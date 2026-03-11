# HARMONIZED_BCCH_2003CLP_v1 summary

Additive BCCh extension bundle in constant 2003 CLP.
The legacy Perez-based 1900-1994 production surface remains frozen and is preserved exactly inside this bundle.

## Status
- Legacy 1900-1994 history preserved exactly: True
- BCCh forward-extension start year: 1995
- Full-period admissibility: True
- Pk coverage: 1940-2024
- Pk(2003)=100 check: True

## Provenance
- Generated at UTC: 2026-03-11T04:09:34Z
- Git commit: 57bd6129f8a870162b3288b79bf521022d645e16
- Repo status at generation: clean
- Command: python codes/run_harmonization_bcch.py

## Bridge factors (1994)
- ME: 5.888124411554
- NRC: 1.033303538667
- RC: 1.049933189026

## Pk splice
- Primary source 1960-2024: ratio deflator `FBKF_nom / FBKF_real` from `data/raw/BCCH_ref2018_Pk.xlsx`, rebased to 2003=100.
- Backcast source 1940-1959: ClioLab ratio-deflator growth chained to the BCCh ratio level at 1960.

## Notes
- BCCh published totals for stocks and depreciation are used only as extraction audits; production aggregates are recomputed from components.
- `Kn_ClioLab.xlsx` and BCCh total real FBKF remain diagnostic-only inputs.
- Years 2023 and 2024 are flagged as provisional and preliminary, respectively, in the diagnostic and Pk outputs.
