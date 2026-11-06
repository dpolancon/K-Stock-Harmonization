# HARMONIZED_PEREZ_2003CLP_v1 summary

Canonical harmonized baseline built from Perez FBKF ex inventories scaled by lambda_choice and split by normalized Hofman shares.
Frozen Hofman 1980 baseline remains unchanged.

## Status
- Primary price space: 2003 CLP
- Control concept: FBKF ex inventories
- Inventories excluded from accumulation: True
- Meets overlap admissibility bar: True
- Meets full-period admissibility bar: True
- Regression vs extension candidate: True
- Early rate out-of-bounds count (<1950): 0
- Early rate tolerance (max allowed): 0

## Provenance
- Generated at UTC: 2026-11-05T20:59:49Z
- Git commit: f558ca81d4ca937d3e4433870534f6ba4bb9028b
- Repo status at generation: dirty
- Command: python codes/run_harmonization.py

## Regression vs extension candidate
- investment_max_abs_diff_ME: 0.000000001863
- investment_max_abs_diff_NRC: 0.000000001863
- investment_max_abs_diff_RC: 0.000000000931
- investment_max_abs_diff_Total: 0.000000007451
- kg_max_abs_diff_ME: 7733.434991672635
- kg_max_abs_diff_NRC: 8387.591648668051
- kg_max_abs_diff_RC: 5541.963920116425
- kg_max_abs_diff_Total: 21662.990560412407
- kn_max_abs_diff_ME: 3825313.659825406969
- kn_max_abs_diff_NRC: 3194023.539645850658
- kn_max_abs_diff_RC: 8258765.617356799543
- kn_max_abs_diff_Total: 14611519.766046911478

## Deferred non-Perez sources
- BCCH_1985_2024.xlsx
- BCCH_ref2018_Pk.xlsx
- ClioLab_GFKF_Freal_nominal_Pk.xlsx
- Kn_ClioLab.xlsx
- Tafunell_Ducoing_2016_Kg.xlsx
- tafunel_2013_Ig.xlsx

## Notes
- Inventories remain outside fixed-capital accumulation because the repo models fixed capital only (ME, NRC, RC).
- The canonical production command is `codes/run_harmonization.py`.
- The canonical production artifacts are written to `outputs/HARMONIZED_PEREZ_2003CLP_v1/`.
- Exact required-input hashes are recorded in `assumptions.yaml`.
