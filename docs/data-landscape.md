# Data Landscape

This document inventories the raw files present in `data/raw/`, their observed coverage, and their current role in the harmonization workflow.

## Active production inputs

| File | Observed coverage in repo | Evidence | Current role |
| --- | --- | --- | --- |
| `data/raw/Hofman2000_GrossInvestment.xlsx` | 1900 onward | `Gross_Investment_Ig_Hofman2000` sheet; used by `codes/run_baseline_hofman_1980.py` and `codes/run_harmonization.py` | Frozen reference investment series and asset-share source |
| `data/raw/Hofman_Kstock_gross_net_19501994.xlsx` | 1950-1994 | `Kg` and `Kn` sheets; used by `codes/run_baseline_hofman_1980.py` | Overlap stock observations for the frozen accounting reference |
| `data/raw/Hofman2000_anchors.xlsx` | 1950 anchors in 1980 and 2003 price spaces | Used by extension reporting scripts | Reporting-space bridge from 1980 CLP to 2003 CLP |
| `data/raw/PerezEyzaguirre_DemandaAgregada.xlsx` | 1860-2010 | `Demanda Agregada` sheet; machinery, construction, inventories, and gross internal investment columns | Canonical aggregate control total in the promoted harmonized baseline |

## Deferred but central to source reconciliation

| File | Observed coverage in repo | What can be established from repository evidence | Current status |
| --- | --- | --- | --- |
| `data/raw/BCCH_1985_2024.xlsx` | File name suggests 1985-2024 | Workbook exists; active code does not parse it; unit and concept are not established from active repo logic | Deferred |
| `data/raw/BCCH_ref2018_Pk.xlsx` | 1960 onward in first sheet | First sheet contains `FBKF_nom`, `FBKF_real`, and `Pk` columns | Deferred |
| `data/raw/ClioLab_GFKF_Freal_nominal_Pk.xlsx` | 1940 onward in first sheet | First sheet contains `FBKFNOM`, `FBKFREAL`, and `Pk` columns | Deferred |
| `data/raw/Kn_ClioLab.xlsx` | 1900 onward in first sheet | First sheet contains `Kn_ME`, `Kn_C_CL`, and total net capital columns | Deferred |
| `data/raw/Tafunell_Ducoing_2016_Kg.xlsx` | 1900 onward in first sheet | First sheet contains `Kg_ME`, `Kg_NRC`, and `Kg_NR` columns | Deferred |
| `data/raw/tafunel_2013_Ig.xlsx` | 1856 onward in first sheet | First sheet contains `Ig_ME`, `Ig_NRC`, and `Ig_tot` columns | Deferred |

## Current overlap logic

- The frozen Hofman accounting reference uses the observed overlap window 1950-1994 for stock identities and survival recovery.
- The promoted harmonized baseline keeps the 1900-1994 publication window but uses Perez aggregate investment in 2003 CLP, scaled by `lambda_choice`, then split by normalized Hofman shares.
- Repository evidence for BCCH, ClioLab, and Tafunell stops at file presence and raw-sheet headers; there are no active production code references beyond the deferred-source list in `codes/run_harmonization.py`.

## Comparability status

`outputs/DIAGNOSTIC_DEFINITION_CROSSWALK_v1/summary.md` records comparability as `PARTIAL`. The active repository reason is the difference between fixed-capital formation excluding inventories and broader investment definitions that may include inventories or unresolved concept differences.
