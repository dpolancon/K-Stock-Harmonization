# Source Reconciliation

This chapter explains how the repository currently reconciles the main source families and why they enter different publication surfaces in different ways.

## Hofman versus Perez

The active repository resolution remains asymmetric:

- Hofman defines the frozen accounting reference in 1980 CLP.
- Perez defines the promoted aggregate investment control total in 2003 CLP for the canonical `1900-1994` publication surface.

The bridge between them is not a unit conversion. `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/summary.md` states explicitly that the chosen lambda is a level-normalization bridge. `outputs/DIAGNOSTIC_DEFINITION_CROSSWALK_v1/summary.md` records comparability as `PARTIAL`, not fully resolved.

The canonical production design handles that partial comparability operationally by:

- excluding inventories from the canonical control total
- scaling the Perez aggregate with `lambda_choice`
- inheriting Hofman asset shares, survival parameters, and gap ratios

## Perez

Perez remains the promoted mother series for the canonical `1900-1994` bundle:

- coverage: `1860-2010` in the committed anchor summaries
- price space: `2003 CLP`
- concept used in production: machinery plus construction, excluding inventories

Perez is still the only non-Hofman source family that enters the repo’s validated `1900-1994` stock-flow closure end to end.

## BCCH

Two BCCh workbooks now enter the additive extension bundle:

- `BCCH_1985_2024.xlsx`
- `BCCH_ref2018_Pk.xlsx`

Current role:

- `BCCH_1985_2024.xlsx` supplies real `Kn` and `D` by asset for `1985-2024`
- the repo crosswalks BCCh asset names to `RC`, `NRC`, `ME`
- `NR` and `Total` are recomputed from components
- BCCh published totals are used only as extraction audits
- a `1994` hard anchor maps BCCh `Kn` into the repo’s 2003-CLP stock level surface
- the same asset factor is applied to `D`, preserving BCCh depreciation rates

This does not replace the Perez baseline. It creates an additive `1900-2024` bundle that keeps the validated `1900-1994` canonical history fixed and uses BCCh only from `1995` onward.

For `Pk`, BCCh is the primary source for `1960-2024` through the ratio deflator `FBKF_nom / FBKF_real`, rebased to `2003=100`. The workbook also carries a BCCh-supplied `Pk` field, but that field is non-production and does not enter the current public diagnostics.

## ClioLab

Two ClioLab-related workbooks remain relevant, but with narrower roles:

- `ClioLab_GFKF_Freal_nominal_Pk.xlsx`
- `Kn_ClioLab.xlsx`

Current role:

- `ClioLab_GFKF_Freal_nominal_Pk.xlsx` provides the ratio-deflator growth path used to backcast `1940-1959`, chained to the BCCh ratio level at `1960`
- `Kn_ClioLab.xlsx` is diagnostic only and is used to compare secondary level patterns against the BCCh extension

ClioLab therefore enters the repo only as a deflator backcast and a diagnostic stock comparator. It is not used as a primary production stock input.

## Tafunell

The Tafunell family remains outside the active publication surfaces:

- `tafunel_2013_Ig.xlsx`
- `Tafunell_Ducoing_2016_Kg.xlsx`

Current exclusion reason:

- no active integration into either the canonical Perez bundle or the BCCh extension bundle
- no committed price-space reconciliation that would justify promotion into production

## Current repository position

For the current repo state, the source hierarchy is explicit:

- Hofman remains the frozen accounting reference
- Perez remains the promoted mother series for the canonical `1900-1994` bundle
- BCCh now supplies the forward extension from `1995` onward and the primary ratio-deflator surface from `1960` onward
- ClioLab supplies only the `1940-1959` `Pk` backcast growth path and stock diagnostics
- Tafunell remains deferred

This keeps the validated Perez-first real harmonization intact while allowing a stock-flow-consistent BCCh splice for the later period.
