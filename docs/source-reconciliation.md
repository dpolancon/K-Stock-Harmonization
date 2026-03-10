# Source Reconciliation

This chapter explains how the repository currently reconciles the main source families and why only part of that source landscape enters the production baseline.

## Hofman versus Perez

The active repository resolution is asymmetric:

- Hofman defines the frozen accounting reference in 1980 CLP.
- Perez defines the promoted aggregate investment control total in 2003 CLP.

The bridge between them is not a unit conversion. `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/summary.md` states explicitly that the chosen lambda is a level-normalization bridge. `outputs/DIAGNOSTIC_DEFINITION_CROSSWALK_v1/summary.md` records comparability as `PARTIAL`, not fully resolved.

The current production design accepts that partial comparability and handles it operationally by:

- excluding inventories from the canonical control total
- scaling the Perez aggregate with `lambda_choice`
- inheriting Hofman asset shares, survival parameters, and gap ratios

## Perez

Perez is the only non-Hofman source family that currently enters the production baseline. Repository evidence establishes:

- coverage: 1860-2010 in the committed anchor summaries
- price space: 2003 pesos from sheet headers and committed summaries
- concept used in production: machinery plus construction, excluding inventories

Perez is included because it is the only non-Hofman source already wired into the complete active chain from raw data to a committed candidate stock path and now to the promoted baseline.

## BCCH

Two BCCH workbooks are present in `data/raw/`:

- `BCCH_1985_2024.xlsx`
- `BCCH_ref2018_Pk.xlsx`

Repository evidence for active use is limited. `codes/run_harmonization.py` lists both files as deferred sources, but no production script reads them. `BCCH_ref2018_Pk.xlsx` shows `FBKF_nom`, `FBKF_real`, and `Pk` in its first sheet. `BCCH_1985_2024.xlsx` is present but its active role, exact concept, and unit treatment are not established from code.

Current exclusion reason:

- no active harmonization code path
- no committed crosswalk from BCCH concepts into the fixed-capital baseline
- no decision log in repo that promotes BCCH above the Perez path

## ClioLab

Two ClioLab-related workbooks are present:

- `ClioLab_GFKF_Freal_nominal_Pk.xlsx`
- `Kn_ClioLab.xlsx`

The first workbook appears, from file name and headers, to provide gross fixed capital formation and a price index. The second provides net-capital columns by asset. Neither workbook is consumed by active production code.

Current exclusion reason:

- no active code integration
- no committed bridge from ClioLab flows/stocks to the promoted accounting closure
- no published admissibility comparison in repo that would justify replacing the Perez-first route

## Tafunell

Two Tafunell-related workbooks are present:

- `tafunel_2013_Ig.xlsx`
- `Tafunell_Ducoing_2016_Kg.xlsx`

Repository evidence shows investment-flow columns in the former and gross-stock columns in the latter. Again, there are no active production code references beyond deferred-source listing.

Current exclusion reason:

- no active harmonization step
- no committed price-space reconciliation into the production baseline
- no documented decision in repo that resolves Tafunell against Perez and Hofman for publication use

## Current repository position

For v1 publication, the repository is methodologically explicit:

- Perez is the promoted production mother series.
- Hofman remains the frozen accounting reference.
- BCCH, ClioLab, and Tafunell are part of the documented empirical landscape, but not part of the production baseline.

This is a defensible dissertation position because the exclusion is documented as an implementation and comparability status, not as a claim that those sources lack value.
