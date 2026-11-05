# Stock-Flow Consistent Approach Developed in This Repository

## Title and purpose

This artifact reconstructs the stock-flow consistent approach implemented in this repository from the tracked Markdown corpus. Its purpose is to provide a dissertation-ready methodological narrative that explains how the project defines stock-flow consistency, how that definition is operationalized in the capital-stock series, and where the boundaries of the current approach remain visible in repository evidence.

## Evidence policy

This document is written under a repo-first synthesis rule.

- Substantive claims are grounded in `README.md`, the files under `docs/`, and the committed `outputs/*/summary.md` corpus.
- `Interpretive synthesis:` marks analytical bridges that organize repository evidence into a more paper-ready argument.
- `Not established from repository evidence:` marks questions that the repo does not resolve at the Markdown level.
- Paths are cited inline so the future paper can trace each point back to a committed source.

## What the repo means by a stock-flow consistent approach

In this repository, stock-flow consistency is defined at the level of capital-stock accounting identities rather than as a complete economy-wide macro model. `docs/notation.md`, `docs/baseline-hofman.md`, `docs/harmonized-perez.md`, and `docs/validation.md` show that the active concern is whether investment flows, capital stocks, retirements, depreciation, and the capital gap evolve in a way that satisfies year-to-year stock-flow identities and asset additivity.

The central logic is straightforward. Gross investment `I` feeds the evolution of gross capital stock `Kg` once retirements `R` are taken into account. Net capital stock `Kn` evolves from the same investment flow once depreciation `D` is taken into account. The capital gap `B` is defined as the difference between `Kg` and `Kn`. Aggregates must also add up correctly across asset classes. This identity-based discipline appears both in the frozen Hofman accounting reference documented in `docs/baseline-hofman.md` and in the promoted Perez baseline documented in `docs/harmonized-perez.md`.

`Interpretive synthesis:` the repository uses a narrow but rigorous form of stock-flow consistency. It is narrow because it concerns fixed-capital accounting, not a full system of institutional sectors, financial balances, or behavioral equations. It is rigorous because the production baseline is only accepted if the accounting identities and admissibility checks hold over both the overlap window and the full publication period.

`Not established from repository evidence:` a full transactions-flow matrix, balance-sheet matrix, sectoral behavioral block, or a Godley-Lavoie style macro SFC model. The repo does not document such structures in the Markdown corpus.

## Core notation and identities used in the repository

The common notation is defined in `docs/notation.md`.

- `I`: gross fixed investment flow.
- `Kg`: gross capital stock.
- `Kn`: net capital stock.
- `B`: capital gap, defined as `Kg - Kn`.
- `R`: retirements.
- `D`: depreciation.
- `z`: retirement rate, defined as `R / Kg(t-1)`.
- `delta`: depreciation rate, defined as `D / Kn(t-1)`.
- `DeltaKg`, `DeltaKn`, and `DeltaB`: first differences in the corresponding stock variables.

The operative identities inferred from `docs/notation.md`, `docs/validation.md`, and `outputs/EXTENSION_REPORTING_2003CLP_v1/summary.md` are:

- `DeltaKg = I - R`
- `DeltaKn = I - D`
- `B = Kg - Kn`
- `NR = ME + NRC`
- `Total = ME + NRC + RC`

These identities are not treated as descriptive conveniences. They are validation conditions. `docs/validation.md` and `outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md` show that identity and additivity failures are part of the admissibility gate for the canonical production baseline.

## Asset structure and accounting aggregates

The repository works with a fixed asset taxonomy documented in `docs/notation.md`.

- `ME`: machinery and equipment.
- `NRC`: non-residential construction.
- `RC`: residential construction.
- `NR`: non-residential aggregate, defined as `ME + NRC`.
- `Total`: total fixed capital, defined as `ME + NRC + RC`.

This asset structure matters because the harmonization problem is not solved only at the aggregate level. The canonical Perez baseline starts from an aggregate control total, but it must be split back into the asset structure inherited from Hofman before stock accumulation and validation can proceed. `docs/harmonized-perez.md` and `outputs/EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md` make that point explicit.

## The dual-baseline design: frozen Hofman reference versus promoted Perez baseline

The repository is organized around two baselines, not one. `README.md`, `docs/index.md`, `docs/baseline-hofman.md`, and `docs/harmonized-perez.md` all insist on this distinction.

The first baseline is the frozen Hofman accounting reference in constant 1980 CLP. It is produced by `codes/run_baseline_hofman_1980.py` and published in `outputs/harmonized_series_1980CLP_1900_1994.csv`. It is frozen because the repo treats it as the benchmark object from which survival parameters, gap ratios, and asset shares are drawn. It is not the baseline that is being republished as the canonical harmonized series.

The second baseline is the canonical harmonized Perez baseline in constant 2003 CLP. It is produced by `codes/run_harmonization.py` and published in `outputs/HARMONIZED_PEREZ_2003CLP_v1/`. This is the series the repo now treats as the public harmonized output.

The dual design matters conceptually. The repo does not replace Hofman with Perez in a wholesale way. Instead, it preserves Hofman as the accounting and structural reference while promoting Perez as the aggregate investment mother series used for the published harmonized baseline.

`Interpretive synthesis:` the project resolves the tension between continuity and replacement by splitting functions across sources. Hofman supplies structural closure and benchmark accounting discipline. Perez supplies the promoted aggregate flow basis in the publication price space.
## How stock-flow closure is operationalized in this repo

### Frozen Hofman closure

`docs/baseline-hofman.md` explains the logic of the frozen accounting reference.

- Hofman gross investment provides the flow input.
- Observed Hofman gross and net capital stocks for 1950-1994 provide the overlap observations.
- The overlap is used to recover implied retirements and depreciation.
- Weibull survival functions are fit by asset.
- Pre-1950 stocks are anchored to the observed 1950 levels.
- The capital gap is extended through asset-specific `B/Kg` ratios outside the observed overlap.

The outcome is an internally coherent accounting reference. `outputs/overlap_audit_summary.txt`, summarized in `docs/baseline-hofman.md`, records zero negative implied retirements and zero negative implied depreciation for `Total` in the overlap. At the same time, `docs/baseline-hofman.md` notes that the frozen baseline still has seven retirement-rate out-of-bounds observations over the full 1900-1994 horizon. That is why the frozen series remains a reference object rather than the final admissibility benchmark for publication.

### Promoted Perez closure

`docs/harmonized-perez.md` and `outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md` explain the production logic of the promoted baseline.

1. Read Perez aggregate fixed-capital flows from `data/raw/PerezEyzaguirre_DemandaAgregada.xlsx`.
2. Define the control total as machinery plus construction, excluding inventories.
3. Read `lambda_choice` from `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/lambda_estimates.yaml`.
4. Scale the Perez aggregate by that lambda.
5. Split the scaled total into `ME`, `NRC`, and `RC` using normalized Hofman investment shares from `data/raw/Hofman2000_GrossInvestment.xlsx`.
6. Reuse frozen Hofman survival parameters from `outputs/survival_fit_hofman_1980.csv`.
7. Reuse frozen-baseline gap ratios from `outputs/harmonized_series_1980CLP_1900_1994.csv`.
8. Emit the full panel, audit summaries, regression checks, and provenance metadata into `outputs/HARMONIZED_PEREZ_2003CLP_v1/`.

The SFC property is preserved because the promoted baseline still obeys the same identity and additivity closure. What changes is the mother investment series and the publication price space. What remains inherited is the structural machinery that allows investment to generate stock paths without breaking accounting coherence.

## Why inventories are excluded from accumulation

The inventory issue is central to the repository definition of comparability. `README.md` states that the canonical Perez harmonized baseline uses machinery plus construction only, and that `ex-inventories` means excluding inventories, not ex post. `docs/harmonized-perez.md` and `outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md` repeat that inventories are excluded from accumulation because the production pipeline models fixed capital only in `ME`, `NRC`, and `RC`.

The same point also appears negatively in the diagnostic corpus. `outputs/DIAGNOSTIC_DEFINITION_CROSSWALK_v1/summary.md` records comparability as `PARTIAL` due to inventory inclusion and broader definition differences. The canonical production design responds by excluding inventories from the control concept rather than trying to accumulate inventory variation into the capital-stock system.

`Interpretive synthesis:` excluding inventories is not a cosmetic convention. It is the boundary condition that allows the repo to treat the promoted series as fixed-capital formation and therefore to carry it through the same stock-flow closure used for fixed-capital stocks.

`Not established from repository evidence:` a fully elaborated theoretical defense of why inventories should be excluded in all possible capital-accounting frameworks. What is established is the practical repo decision and its role in preserving comparability within this implementation.

## What harmonization means here in stock-flow consistent terms

The repository uses the word harmonization in a specific sense. It does not mean forcing all available Chilean capital datasets into a single unified empirical truth. Instead, the Markdown corpus shows a narrower and more operational meaning.

From `docs/source-reconciliation.md`, `docs/data-landscape.md`, `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/summary.md`, and `outputs/EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md`, harmonization consists of:

- selecting a canonical aggregate control concept in a common price space;
- measuring the level gap between Hofman and Perez;
- treating the level gap through lambda normalization rather than as a unit conversion issue;
- preserving the asset structure and stock-flow closure inherited from the frozen reference;
- admitting the resulting series only if identity, additivity, and rate checks pass.

This means harmonization is implemented as disciplined substitution under constraints. Perez replaces Hofman as the aggregate investment mother series in the published baseline, but only after scaling, asset reallocation, inherited structural parameters, and strict admissibility checks.

`Interpretive synthesis:` in SFC terms, harmonization here is the controlled replacement of one flow origin while preserving the accounting mechanism that maps flows into internally coherent stocks.
## Methodological limits and unresolved comparability issues

The repository is explicit that the source reconciliation problem is not fully closed.

First, `docs/source-reconciliation.md` and `outputs/DIAGNOSTIC_DEFINITION_CROSSWALK_v1/summary.md` mark Hofman-versus-Perez comparability as `PARTIAL`. The repo resolves this operationally, but not conceptually once and for all.

Second, `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/summary.md` and `outputs/ANCHOR_PEREZ_FBFK_2003CLP_v2_SCALED/summary.md` state that lambda is a level-normalization bridge rather than a unit conversion. This is an important limitation. The scaling factor reconciles levels in practice, but it does not by itself prove conceptual identity between the underlying series.

Third, `docs/source-reconciliation.md` now documents BCCH as part of the additive extension bundle, ClioLab as a `Pk` backcast and diagnostic source, and Tafunell as still deferred. The source hierarchy is therefore implementation-specific rather than a blanket judgment about empirical value.

Fourth, the repo distinguishes sharply between the frozen benchmark and the promoted public baseline. That distinction is methodologically honest, but it also means the project still depends on an inherited structural skeleton from Hofman even after Perez is promoted.

`Not established from repository evidence:` a complete sensitivity analysis across alternative survival families, alternative share systems, or alternative source promotion rules. The Markdown corpus demonstrates the chosen route, not an exhaustive menu of rejected routes.

`Not established from repository evidence:` exact conceptual reconciliation of all Chilean source families into a single theory of fixed-capital measurement.

## Implications for dissertation and paper framing

The current repository supports several strong claims.

- The project implements a fixed-capital stock-flow consistent accounting closure for Chilean capital-stock series.
- The production baseline is now the Perez-based harmonized series in constant 2003 CLP, documented in `README.md`, `docs/harmonized-perez.md`, and `outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md`.
- The promoted baseline passes overlap admissibility, full-period admissibility, regression checks against the validated extension candidate path, and rerun reproducibility checks.
- The treatment of source scope is explicit: Perez is promoted for the canonical `1900-1994` baseline, Hofman is frozen as the accounting reference, BCCH extends the bundle from `1995` onward, ClioLab supports the `Pk` backcast and diagnostics, and Tafunell remains deferred.

Several claims should be framed more carefully in later writing.

- The repo does not establish a full macroeconomic SFC model; it establishes a capital-accounting SFC procedure.
- The repo does not claim complete conceptual equivalence between Hofman and Perez; it claims an operationally valid harmonization under partial comparability.
- The repo does not establish that deferred sources are inferior; it establishes that only some of them are wired into active production, and only in tightly delimited roles.

`Interpretive synthesis:` a good dissertation framing is to present this repository as a capital-accounting harmonization project that adopts stock-flow consistency as an admissibility discipline. That claim is stronger, cleaner, and better supported than a claim to full-system SFC modeling.

## Appendix: Markdown evidence map used for this artifact

| Source path | Role in this artifact | Evidence type |
| --- | --- | --- |
| `README.md` | Canonical framing of baselines, inventory exclusion, and public interface | Conceptual |
| `docs/index.md` | Defines citable objects and evidence discipline | Conceptual |
| `docs/notation.md` | Supplies the variable system, identities, and asset taxonomy | Conceptual |
| `docs/data-landscape.md` | Establishes source inventory, overlaps, and active versus diagnostic source status | Conceptual |
| `docs/baseline-hofman.md` | Documents the frozen accounting reference and its closure logic | Conceptual |
| `docs/harmonized-perez.md` | Documents the promoted baseline and its production logic | Conceptual |
| `docs/validation.md` | Defines overlap, full-period, and regression admissibility | Conceptual |
| `docs/source-reconciliation.md` | Explains partial comparability and source selection logic | Conceptual |
| `docs/code-map.md` | Places the active and historical scripts in methodological sequence | Procedural |
| `docs/reproducibility.md` | Defines the reproducibility contract and provenance fields | Procedural |
| `docs/release-v1.0.0.md` | Records the locked public release position of the methodology | Status |
| `outputs/ANCHOR_PEREZ_FBFK_2003CLP_v1/summary.md` | Establishes Perez coverage and the ex-inventory aggregate identity | Diagnostic |
| `outputs/ANCHOR_PEREZ_FBFK_2003CLP_v2_SCALED/summary.md` | Establishes scaled Perez anchoring and the meaning of lambda | Diagnostic |
| `outputs/DIAGNOSTIC_DEFINITION_CROSSWALK_v1/summary.md` | Establishes `PARTIAL` comparability and inventory-related definition limits | Diagnostic |
| `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/summary.md` | Establishes lambda magnitude, selection rule, and normalized ratio behavior | Diagnostic |
| `outputs/DIAGNOSTIC_UNIT_SCALE_AUDIT_v1/summary.md` | Establishes that the issue is not resolved by a simple unit conversion | Diagnostic |
| `outputs/EXTENSION_EXTERNAL_COMPARE_PEREZ_2003CLP_v1/summary.md` | Provides early baseline-versus-Perez comparison context | Diagnostic |
| `outputs/EXTENSION_EXTERNAL_COMPARE_PEREZ_FBFK_2003CLP_v1/summary.md` | Provides ex-inventory comparison ratios before scaling | Diagnostic |
| `outputs/EXTENSION_EXTERNAL_COMPARE_PEREZ_FBFK_2003CLP_v2/summary.md` | Shows the scale-audit stage did not alter the comparison | Diagnostic |
| `outputs/EXTENSION_EXTERNAL_COMPARE_PEREZ_FBFK_2003CLP_v3_SCALED/summary.md` | Shows the effect of lambda scaling on baseline-versus-Perez distance | Diagnostic |
| `outputs/EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md` | Establishes candidate investment block logic and distance metrics | Diagnostic |
| `outputs/EXTENSION_CANDIDATE_STOCKS_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md` | Establishes candidate stock reconstruction under inherited closure | Diagnostic |
| `outputs/EXTENSION_REPORTING_2003CLP_v1/summary.md` | Confirms identity preservation under reporting-space conversion | Diagnostic |
| `outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md` | Establishes final canonical status for the Perez `1900-1994` bundle | Status |

## Addendum: BCCh extension bundle

The repository now also documents an additive BCCh publication surface in `outputs/HARMONIZED_BCCH_2003CLP_v1/`.

- The BCCh bundle preserves the canonical Perez `1900-1994` history exactly.
- Post-1994 `Kn` and `D` are supplied by BCCh after a `1994` hard-anchor bridge in the repo’s 2003-CLP level space.
- Post-1994 `I` is inferred through the same stock-flow identity used elsewhere in the repo: `I = DeltaKn + D`.
- `Kg` and `R` remain products of the inherited Hofman survival closure, so the extension stays inside the repo’s fixed-capital SFC discipline.
- A companion `Pk` series is published for `1940-2024`, using the BCCh ratio deflator (`FBKF_nom / FBKF_real`) as the primary source and chained ClioLab ratio growth only for the pre-1960 backcast.

`Interpretive synthesis:` this extends the repo’s SFC logic without reopening the canonical Perez resolution. The BCCh bundle is therefore best read as a forward splice under the existing accounting closure, not as a replacement mother series for the entire century.
