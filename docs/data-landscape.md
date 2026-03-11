# Data Landscape

This document inventories the raw files present in `data/raw/`, their observed coverage, and their current role in the harmonization workflow.

## Active production inputs

| File | Observed coverage in repo | Current role |
| --- | --- | --- |
| `data/raw/Hofman2000_GrossInvestment.xlsx` | 1900 onward | Frozen reference investment series and asset-share source for the Perez baseline |
| `data/raw/Hofman_Kstock_gross_net_19501994.xlsx` | 1950-1994 | Overlap stock observations for the frozen accounting reference |
| `data/raw/Hofman2000_anchors.xlsx` | 1950 anchors in 1980 and 2003 spaces | Reporting-space bridge in the historical extension chain |
| `data/raw/PerezEyzaguirre_DemandaAgregada.xlsx` | 1860-2010 | Canonical aggregate control total for `outputs/HARMONIZED_PEREZ_2003CLP_v1/` |
| `data/raw/BCCH_1985_2024.xlsx` | 1985-2024 | Component net stocks and depreciation for the post-1994 BCCh extension |
| `data/raw/BCCH_ref2018_Pk.xlsx` | 1960-2024 | Ratio-input source for the BCCh deflator for `1960-2024` |
| `data/raw/ClioLab_GFKF_Freal_nominal_Pk.xlsx` | 1940-2010 | Backward ratio-growth source for `Pk`, chained to the BCCh 1960 level |
| `outputs/survival_fit_hofman_1980.csv` | 1900-1994 fit output | Survival parameter source reused by both 2003-CLP publication surfaces |
| `outputs/HARMONIZED_PEREZ_2003CLP_v1/harmonized_series_2003CLP_1900_1994.csv` | 1900-1994 | Exact legacy surface preserved inside the BCCh extension bundle |

## Diagnostic-only inputs

| File | Observed coverage in repo | Current role |
| --- | --- | --- |
| `data/raw/Kn_ClioLab.xlsx` | 1900-2010 | Secondary comparison surface for BCCh net-stock levels |

## Deferred but still outside active production

| File | Observed coverage in repo | Current status |
| --- | --- | --- |
| `data/raw/Tafunell_Ducoing_2016_Kg.xlsx` | 1900 onward | Deferred |
| `data/raw/tafunel_2013_Ig.xlsx` | 1856 onward | Deferred |

## Current overlap logic

- The frozen Hofman accounting reference uses the observed overlap window `1950-1994` for stock identities and survival recovery.
- The canonical Perez baseline publishes `1900-1994` and uses Perez aggregate investment in `2003 CLP`, scaled by `lambda_choice`, then split by normalized Hofman shares.
- The additive BCCh bundle preserves every `1900-1994` row from the canonical Perez panel exactly, then uses scaled BCCh `Kn` and `D` from `1995-2024`.
- The BCCh extension uses a `1994` asset-specific hard anchor on `Kn` and applies the same factor to `D`, preserving BCCh depreciation rates while keeping the repo’s 2003-CLP stock history fixed through `1994`.
- The companion `Pk` series uses the BCCh ratio deflator (`FBKF_nom / FBKF_real`) for `1960-2024` and chained ClioLab ratio-deflator growth for `1940-1959`.

## Comparability status

`outputs/DIAGNOSTIC_DEFINITION_CROSSWALK_v1/summary.md` still records Hofman-versus-Perez comparability as `PARTIAL`. The BCCh extension bundle does not replace that canonical Perez resolution; it adds a forward splice that preserves the validated `1900-1994` history exactly and uses BCCh only for the post-1994 extension plus the companion `Pk` surface.
