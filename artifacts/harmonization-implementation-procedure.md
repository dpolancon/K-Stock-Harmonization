# Effective Procedure Used to Implement Harmonization in This Repository

## Title and purpose

This artifact reconstructs the effective procedure used to implement capital-stock harmonization in this repository, with explicit emphasis on data sources, overlaps, validation, workflow history, and the final production logic. It is designed as a paper-preparatory procedural record that can later be translated into dissertation chapters, method appendices, or publication notes.

## Evidence policy

This document follows the same repo-first synthesis rule used across the reverse-documentation layer.

- The argument is grounded in `README.md`, the files under `docs/`, and the committed `outputs/*/summary.md` corpus.
- `Interpretive synthesis:` marks analytical organization that goes beyond the exact wording of the repo while staying anchored to repo evidence.
- `Not established from repository evidence:` marks procedural or methodological details that the Markdown corpus does not fully specify.
- The write-up does not rely on new code archaeology beyond paths already named in the Markdown corpus.

## Source corpus used for this write-up

The relevant Markdown corpus separates into three layers.

- Repository contract: `README.md`.
- Reverse documentation: `docs/index.md`, `docs/notation.md`, `docs/data-landscape.md`, `docs/baseline-hofman.md`, `docs/harmonized-perez.md`, `docs/validation.md`, `docs/source-reconciliation.md`, `docs/code-map.md`, `docs/reproducibility.md`, and `docs/release-v1.0.0.md`.
- Pipeline and diagnostic summaries: the committed `summary.md` files under `outputs/`.

Taken together, these files are sufficient to reconstruct the implemented procedure at a paper-useful level, even where some micro-decisions remain undocumented in prose.

## Data sources used in the implemented harmonization

The production baseline is not built from every raw source in the repo. `docs/data-landscape.md`, `docs/source-reconciliation.md`, and `README.md` identify a narrower active set.

### Active production inputs

| Source file | Coverage established in repo | Current role in production |
| --- | --- | --- |
| `data/raw/PerezEyzaguirre_DemandaAgregada.xlsx` | 1860-2010 | Canonical aggregate control total in 2003 CLP |
| `data/raw/Hofman2000_GrossInvestment.xlsx` | 1900 onward | Frozen reference investment series and asset-share source |
| `data/raw/Hofman_Kstock_gross_net_19501994.xlsx` | 1950-1994 | Overlap stock observations for the frozen reference, not a direct canonical input |
| `data/raw/Hofman2000_anchors.xlsx` | Anchor information linking 1980 and 2003 spaces | Reporting bridge in the extension history, not the active canonical core |
| `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/lambda_estimates.yaml` | Not a raw source; committed diagnostic artifact | Sole lambda source for the canonical production path |
| `outputs/survival_fit_hofman_1980.csv` | Frozen baseline output | Survival parameter source |
| `outputs/harmonized_series_1980CLP_1900_1994.csv` | Frozen baseline output | Gap-ratio source and accounting reference |

### Additional BCCh and Clio sources in the additive bundle

| Source file | What the repo establishes | Current role |
| --- | --- | --- |
| `data/raw/BCCH_1985_2024.xlsx` | Real net-capital and depreciation tables by asset | Active post-1994 stock-extension input |
| `data/raw/BCCH_ref2018_Pk.xlsx` | First sheet supplies `FBKF_nom` and `FBKF_real` inputs | Active ratio-input source for `1960-2024` `Pk` construction |
| `data/raw/ClioLab_GFKF_Freal_nominal_Pk.xlsx` | Appears to contain gross fixed capital formation and price information | Active backward ratio-growth source for `1940-1959` |
| `data/raw/Kn_ClioLab.xlsx` | Contains net-capital columns by asset | Diagnostic-only stock comparator |
| `data/raw/Tafunell_Ducoing_2016_Kg.xlsx` | Contains gross-stock columns by asset | Still deferred |
| `data/raw/tafunel_2013_Ig.xlsx` | Contains investment-flow columns by asset | Still deferred |

## Coverage windows, overlaps, and current role of each source

The implemented procedure uses different time roles for different source families.

- The frozen Hofman accounting reference uses the observed stock overlap window `1950-1994` to recover retirements and depreciation and to fit the structural accounting skeleton documented in `docs/baseline-hofman.md`.
- The canonical Perez baseline publishes the period `1900-1994` in `outputs/HARMONIZED_PEREZ_2003CLP_v1/`.
- Perez source coverage extends well beyond the publication window. `outputs/ANCHOR_PEREZ_FBFK_2003CLP_v1/summary.md` records `1860-2010`, but the production baseline only uses the 1900-1994 segment.
- Lambda estimation is informed by comparison periods summarized in `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/summary.md`, including `1900-1949`, `1950-1994`, `1973-1989`, and `1990-1994`.

The production meaning of these windows is clear in the documentation. The overlap period is the admissibility and recovery anchor. The publication period is the final harmonized output span. The longer Perez span is evidentiary background, not a commitment to extend the canonical series past 1994.

`Not established from repository evidence:` a Markdown-level explanation for why the publication horizon stops at 1994 even though Perez continues to 2010. The corpus establishes the implemented cutoff, not the full rationale behind it.
## Effective workflow history from diagnostics to canonical baseline

The repo documents the implemented procedure as a staged history rather than as a single leap. `docs/code-map.md` and the output summaries under `outputs/` make that sequence visible.

### Stage 1: establish the frozen accounting reference

`docs/baseline-hofman.md` places `codes/run_baseline_hofman_1980.py` at the start of the workflow.

- Hofman investment provides the original flow series.
- Hofman observed stocks for `1950-1994` provide the overlap information.
- Retirements and depreciation are recovered from identity closure.
- Weibull survival functions are fit by asset.
- Gap ratios are recovered for use outside the overlap.

This stage matters because the promoted baseline later reuses the resulting survival parameters and gap ratios.

### Stage 2: build the 2003-CLP Perez anchor pack

`outputs/ANCHOR_PEREZ_FBFK_2003CLP_v1/summary.md` shows the first Perez extraction stage.

- Coverage is `1860-2010`.
- Machinery, construction, inventories, and gross internal investment are all observed.
- The committed sanity check confirms that machinery plus construction plus inventories add exactly to gross internal investment.

This stage isolates the raw series from which the ex-inventory control concept can be formed.

### Stage 3: compare baseline and Perez concepts

`outputs/EXTENSION_EXTERNAL_COMPARE_PEREZ_2003CLP_v1/summary.md`, `outputs/EXTENSION_EXTERNAL_COMPARE_PEREZ_FBFK_2003CLP_v1/summary.md`, and `outputs/DIAGNOSTIC_DEFINITION_CROSSWALK_v1/summary.md` document the comparison stage.

- Price space compatibility is treated as yes.
- Comparability is still recorded as `PARTIAL`.
- The primary documented reason is inventories and unresolved definition differences.

This stage establishes that Perez is usable, but not yet directly substitutable without additional reconciliation.

### Stage 4: rule out a simple unit-conversion story

`outputs/DIAGNOSTIC_UNIT_SCALE_AUDIT_v1/summary.md` shows that the best scale pair is `baseline_multiplier=1.0` and `perez_multiplier=1.0`. That matters because it indicates the distance between Hofman and Perez is not solved by simply rescaling units.

### Stage 5: estimate level normalization

`outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/summary.md` defines the decisive bridge.

- Chosen lambda: `4.105381794084627`.
- Choice rule: `lambda_median (robust to outliers)`.
- The comparison is expressed through baseline-to-Perez ratios across multiple windows.
- The normalized `1950-1994` ratio mean moves close to one after applying the chosen lambda.

### Stage 6: create the scaled Perez anchor

`outputs/ANCHOR_PEREZ_FBFK_2003CLP_v2_SCALED/summary.md` records the scaled anchor pack.

- Coverage remains `1860-2010`.
- The add-up check for scaled machinery plus scaled construction against scaled ex-inventory total is exact.
- The summary states explicitly that scaling is a level normalization bridge, not a unit conversion.

### Stage 7: construct the candidate investment block

`outputs/EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md` documents the first stock-ready candidate.

- The candidate definition is scaled Perez FBKF ex inventories split by Hofman asset shares.
- Coverage is `1900-1994`.
- Normalized shares sum to one by construction.
- Negative candidate investment counts are zero.
- The add-up difference is zero.

This stage converts an aggregate mother series into an asset-level investment panel that can enter stock accumulation.

### Stage 8: construct candidate stocks

`outputs/EXTENSION_CANDIDATE_STOCKS_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md` shows the next stage.

- Candidate stocks are accumulated from the scaled Perez investment block.
- Frozen Hofman survival parameters are reused.
- Negativity, add-up, and identity checks all pass in the committed summary.

This is the critical stage where the repo demonstrates that the Perez mother series can live inside the inherited stock-flow closure.

### Stage 9: promote the candidate path into the canonical production baseline

`docs/harmonized-perez.md`, `docs/validation.md`, `docs/reproducibility.md`, and `outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md` record the final promotion.

- The canonical command is `python codes/run_harmonization.py`.
- The public output bundle is `outputs/HARMONIZED_PEREZ_2003CLP_v1/`.
- Overlap admissibility, full-period admissibility, regression alignment, and reproducibility are hard requirements.

`Interpretive synthesis:` the effective workflow is cumulative. Each extension stage reduces one source of uncertainty until the repo can claim that the Perez path is no longer only a diagnostic candidate but a production-quality harmonized baseline.

## Step-by-step implemented procedure now used in production

The current production procedure is documented most directly in `README.md`, `docs/harmonized-perez.md`, `docs/validation.md`, `docs/reproducibility.md`, and `outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md`.

1. Start from Perez aggregate fixed-capital formation in `data/raw/PerezEyzaguirre_DemandaAgregada.xlsx`.
2. Define the production control concept as machinery plus construction, excluding inventories.
3. Read the chosen lambda from `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/lambda_estimates.yaml`.
4. Scale the Perez ex-inventory aggregate by `lambda_choice`.
5. Read Hofman investment shares from `data/raw/Hofman2000_GrossInvestment.xlsx`.
6. Normalize those shares and use them to split the scaled aggregate into `ME`, `NRC`, and `RC`.
7. Read frozen Hofman survival parameters from `outputs/survival_fit_hofman_1980.csv`.
8. Accumulate gross and net stocks using the inherited closure logic documented for the baseline and candidate-stock stages.
9. Read frozen-baseline information from `outputs/harmonized_series_1980CLP_1900_1994.csv` in order to reuse gap-ratio structure.
10. Build the harmonized panel for `1900-1994` in `2003 CLP`.
11. Run overlap admissibility checks for `1950-1994`.
12. Run full-period admissibility checks for `1900-1994`.
13. Run regression checks against the extension candidate outputs.
14. Write the public output bundle, including provenance metadata and audit summaries.

This is the procedure that now defines the repository's public baseline contract.

## Addendum: effective procedure for the BCCh extension bundle

The repository now exposes a second 2003-CLP publication surface through `codes/run_harmonization_bcch.py` and `outputs/HARMONIZED_BCCH_2003CLP_v1/`.

The effective procedure is:

1. Read the committed canonical Perez panel for `1900-1994`.
2. Read BCCh real net stocks and depreciation by asset from sheets `1` and `2` of `data/raw/BCCH_1985_2024.xlsx`.
3. Crosswalk BCCh assets to `RC`, `NRC`, and `ME`, and recompute `NR` and `Total` from components.
4. Compute asset-specific `1994` bridge factors from canonical `Kn / BCCh Kn`.
5. Apply the same bridge factor to BCCh `D`, preserving BCCh depreciation rates.
6. Hold the legacy panel fixed through `1994`.
7. Infer `1995-2024` real investment from `I = DeltaKn + D`.
8. Append that inferred investment history to the legacy investment block.
9. Reuse the frozen Hofman survival parameters to reconstruct `Kg` and `R` through `2024`.
10. Publish the extended stock panel plus bridge diagnostics and provenance metadata.
11. Build a companion `Pk` series from the ratio `FBKF_nom / FBKF_real` rebased to `2003=100` for `1960-2024`, chain ClioLab ratio-deflator growth backward to `1940`, and write ratio-only splice diagnostics.

This addendum does not change the v1 canonical contract. It adds a new, non-breaking extension bundle whose first requirement is exact preservation of the committed `1900-1994` history.
## Lambda normalization and why it is a level bridge rather than a unit conversion

The lambda step is one of the most important methodological choices in the repo. Three files are decisive here: `outputs/DIAGNOSTIC_UNIT_SCALE_AUDIT_v1/summary.md`, `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/summary.md`, and `outputs/ANCHOR_PEREZ_FBFK_2003CLP_v2_SCALED/summary.md`.

The unit-scale audit indicates that the baseline-versus-Perez gap is not solved by choosing different powers-of-ten multipliers. The best pair remains `1.0` for both sides. That result supports the later claim that simple unit mismatch is not the core problem.

The level-normalization diagnostic then estimates the magnitude of the persistent gap between baseline and Perez ex-inventory totals. The chosen bridge is `lambda_median = 4.105381794084627`, explicitly selected as robust to outliers. The diagnostic also shows why this step is effective: after normalization by `lambda_median`, the ratio mean in `1950-1994` moves from about `4.108780` to about `1.000828`.

The scaled anchor summary turns that logic into a procedural rule by stating directly that scaling is a level normalization bridge, not a unit conversion. This wording is methodologically important for later writing because it prevents overstating what lambda accomplishes.

`Interpretive synthesis:` lambda is the repo's operational answer to a persistent level discrepancy between conceptually related but not identical source series. It is a measurement-reconciliation device, not a proof that Hofman and Perez are interchangeable in origin or definition.

`Not established from repository evidence:` a formal estimator comparison beyond the reported candidates `lambda_median`, `lambda_mean`, and `lambda_trim10`, or a formal statistical model of why the median is optimal beyond the stated robustness argument.

## Hofman shares, survival reuse, and gap-ratio reuse

The promoted baseline does not derive every structural component from Perez. Instead, the repo reuses structural elements from the frozen Hofman baseline.

### Hofman shares

`docs/harmonized-perez.md` and `outputs/EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md` show that normalized Hofman investment shares are used to split the scaled aggregate Perez control total into `ME`, `NRC`, and `RC`. This is how the repo moves from a two-component Perez control concept to a three-asset fixed-capital panel.

### Survival reuse

`docs/baseline-hofman.md`, `docs/harmonized-perez.md`, and `outputs/EXTENSION_CANDIDATE_STOCKS_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md` show that survival parameters are inherited from the frozen Hofman fit. The repo therefore assumes that the validated stock-flow closure developed in the frozen reference remains structurally informative for the harmonized path.

### Gap-ratio reuse

`docs/baseline-hofman.md`, `docs/harmonized-perez.md`, and `README.md` state that frozen-baseline gap ratios recovered from `outputs/harmonized_series_1980CLP_1900_1994.csv` are reused in the promoted path. This makes the harmonized net-stock path depend not only on Perez flows, but also on a structural net-to-gross relation inherited from the reference series.

`Interpretive synthesis:` the repo's harmonization procedure is hybrid by design. Perez provides the promoted aggregate flow basis, while Hofman provides the structural decomposition and stock-flow closure needed to make the final series internally coherent.

`Not established from repository evidence:` a Markdown-level account of alternative share systems, alternative survival transfer rules, or alternative net-gap reconstruction rules that were considered and rejected.

## Validation framework: overlap, full-period, regression, reproducibility

The validation framework is defined in `docs/validation.md`, `docs/reproducibility.md`, `docs/release-v1.0.0.md`, and `outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md`.

### Overlap admissibility

The overlap window is `1950-1994`. The canonical pipeline checks, by asset and aggregate:

- negative retirements;
- negative depreciation;
- retirement rates outside `[0, 1]`;
- depreciation rates outside `[0, 1]`.

The current committed canonical result is a pass.

### Full-period admissibility

The publication window is `1900-1994`. The canonical pipeline checks:

- no negative `Kg`;
- no negative `Kn`;
- no negative `B`;
- no additivity failures;
- no identity residual failures;
- no rate out-of-bounds observations, including the pre-1950 period.

`docs/validation.md` also states that the current setting is strict: `EARLY_RATE_OUT_MAX = 0`. The committed canonical result is a pass.

### Regression alignment

The canonical series must remain aligned with the previously validated extension candidate outputs:

- `outputs/EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/`
- `outputs/EXTENSION_CANDIDATE_STOCKS_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/`

`outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md` reports max absolute differences that are effectively at floating-point scale, and the overall regression result is `True`.

### Reproducibility

`docs/reproducibility.md` and the canonical `assumptions.yaml` define the provenance contract.

- canonical command;
- git commit;
- generation timestamp;
- repo clean or dirty status;
- Python version;
- SHA256 input hashes.

The repo also requires idempotent reruns when no substantive content changes. `docs/release-v1.0.0.md` records that canonical output bundle reproducibility across consecutive reruns passes.

`Not established from repository evidence:` the exact numeric tolerances used for every regression comparison, apart from the documented strict early-rate setting and the reported pass outcome.
## Source-scope note after the BCCh integration

`docs/source-reconciliation.md` is the controlling source for deferred-source treatment.

### BCCH

The repo documents two BCCH workbooks.

- `data/raw/BCCH_1985_2024.xlsx`
- `data/raw/BCCH_ref2018_Pk.xlsx`

In the current repo state, both workbooks now enter the additive BCCh bundle: the stock workbook for post-1994 `Kn` and `D`, and the `Pk` workbook as the source of the `FBKF_nom / FBKF_real` ratio inputs used to build the `1960-2024` deflator surface.

### ClioLab

The repo documents two ClioLab-related workbooks.

- `data/raw/ClioLab_GFKF_Freal_nominal_Pk.xlsx`
- `data/raw/Kn_ClioLab.xlsx`

The current repo uses the first workbook as the `Pk` growth source for the `1940-1959` backcast and the second as a diagnostic-only stock comparator. ClioLab still does not replace the Perez or BCCh mother series in any active stock panel.

### Tafunell

The repo documents two Tafunell-related workbooks.

- `data/raw/tafunel_2013_Ig.xlsx`
- `data/raw/Tafunell_Ducoing_2016_Kg.xlsx`

The documented exclusion reasons are no active harmonization step, no committed price-space reconciliation into the production baseline, and no documented decision that resolves Tafunell against Perez and Hofman for publication use.

The important point for later writing is that source-role limits are procedural and documentary, not dismissive. The repo treats BCCH as active in the additive extension bundle, ClioLab as active only in narrow deflator and diagnostic roles, and Tafunell as still deferred.

## Practical writing notes for a future paper

The current repo supports several claims strongly.

- The implemented harmonization procedure is explicit, versioned, and reproducible.
- The public baseline is now Perez-based, ex inventories, and expressed in constant `2003 CLP`.
- The final production route is backed by a staged diagnostic history rather than by an unexplained one-step substitution.
- Validation is multi-layered: overlap, full-period, regression, and provenance stability.

Several claims should be framed with care.

- The procedure solves an implementation problem under partial comparability; it does not close every conceptual debate about source equivalence.
- The repo documents why inventories are excluded, but it does not provide a general theoretical treatise on inventories and capital measurement.
- The promoted baseline remains structurally dependent on Hofman through shares, survival parameters, and gap ratios.
- Deferred sources are documented as deferred, not falsified.

`Interpretive synthesis:` a strong paper strategy is to present the final series as a harmonized fixed-capital baseline produced through staged source reconciliation under stock-flow consistency constraints. That phrasing is fully compatible with the repo evidence and avoids overclaiming conceptual closure.

## Appendix: Markdown evidence map used for this artifact

| Source path | Role in this artifact | Evidence type |
| --- | --- | --- |
| `README.md` | Defines the public contract, active baseline distinction, and inventory exclusion | Procedural |
| `docs/index.md` | Defines the documentation architecture and citable objects | Conceptual |
| `docs/notation.md` | Supplies variable and aggregate definitions used in procedure narration | Conceptual |
| `docs/data-landscape.md` | Supplies active and deferred source inventory plus overlap logic | Procedural |
| `docs/baseline-hofman.md` | Supplies the structural reference procedure reused by the canonical path | Procedural |
| `docs/harmonized-perez.md` | Supplies the canonical production logic and output contract | Procedural |
| `docs/validation.md` | Supplies admissibility definitions and audit logic | Procedural |
| `docs/source-reconciliation.md` | Supplies source-promotion and deferred-source rationale | Procedural |
| `docs/code-map.md` | Supplies the staged workflow history across scripts and outputs | Procedural |
| `docs/reproducibility.md` | Supplies the provenance and rerun contract | Procedural |
| `docs/release-v1.0.0.md` | Supplies the locked release status of the production baseline | Status |
| `outputs/ANCHOR_PEREZ_FBFK_2003CLP_v1/summary.md` | Supplies Perez coverage and ex-inventory construction checks | Diagnostic |
| `outputs/ANCHOR_PEREZ_FBFK_2003CLP_v2_SCALED/summary.md` | Supplies scaled Perez anchor logic and level-bridge wording | Diagnostic |
| `outputs/DIAGNOSTIC_DEFINITION_CROSSWALK_v1/summary.md` | Supplies the formal `PARTIAL` comparability result | Diagnostic |
| `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/summary.md` | Supplies chosen lambda, candidates, and normalized ratios | Diagnostic |
| `outputs/DIAGNOSTIC_UNIT_SCALE_AUDIT_v1/summary.md` | Supplies the evidence against a simple unit-conversion explanation | Diagnostic |
| `outputs/EXTENSION_EXTERNAL_COMPARE_PEREZ_2003CLP_v1/summary.md` | Supplies early baseline-versus-Perez comparison evidence | Diagnostic |
| `outputs/EXTENSION_EXTERNAL_COMPARE_PEREZ_FBFK_2003CLP_v1/summary.md` | Supplies ex-inventory comparison ratios before scaling | Diagnostic |
| `outputs/EXTENSION_EXTERNAL_COMPARE_PEREZ_FBFK_2003CLP_v2/summary.md` | Supplies the comparison stage after unit-scale audit | Diagnostic |
| `outputs/EXTENSION_EXTERNAL_COMPARE_PEREZ_FBFK_2003CLP_v3_SCALED/summary.md` | Supplies the comparison stage after lambda scaling | Diagnostic |
| `outputs/EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md` | Supplies candidate investment-block construction evidence | Diagnostic |
| `outputs/EXTENSION_CANDIDATE_STOCKS_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md` | Supplies candidate stock reconstruction evidence | Diagnostic |
| `outputs/EXTENSION_REPORTING_2003CLP_v1/summary.md` | Supplies reporting-space conversion context and identity preservation | Diagnostic |
| `outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md` | Supplies final canonical validation, regression, and deferred-source status | Status |
