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
- Generated at UTC: 2026-11-05T21:00:39Z
- Git commit: f558ca81d4ca937d3e4433870534f6ba4bb9028b
- Repo status at generation: dirty
- Command: python codes/run_harmonization_bcch.py

## Bridge factors (1994)
- ME: 6.296786961409
- NRC: 1.069109782405
- RC: 0.964691049191

## Pk splice
- Primary source 1960-2024: ratio deflator `FBKF_nom / FBKF_real` from `data/raw/BCCH_ref2018_Pk.xlsx`, rebased to 2003=100.
- Backcast source 1940-1959: ClioLab ratio-deflator growth chained to the BCCh ratio level at 1960.

## Notes
- BCCh published totals for stocks and depreciation are used only as extraction audits; production aggregates are recomputed from components.
- `Kn_ClioLab.xlsx` and BCCh total real FBKF remain diagnostic-only inputs.
- Years 2023 and 2024 are flagged as provisional and preliminary, respectively, in the diagnostic and Pk outputs.
