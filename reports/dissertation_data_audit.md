# Repo Audit — Data and Capital-Stock Construction

## 1. Executive summary

This repo is a **Chile harmonized capital-stock construction repo**, not a U.S. direct-source build and not an estimation repo. Its construction architecture has three layers:

1. a frozen Hofman accounting reference in constant 1980 CLP;
2. a canonical Perez-based harmonized fixed-capital panel in constant 2003 CLP for `1900-1994`;
3. an additive BCCh extension bundle that preserves the canonical `1900-1994` history exactly and extends the stock panel to `2024`.

For dissertation purposes, the repo supports the **data/construction layer** well: source selection, inventory exclusion, level normalization (`lambda_choice`), asset-share splitting, Weibull survival fitting, GPIM-style accumulation, gap-ratio reuse, BCCh bridging, and provenance-rich output bundles. The README is **not weak**; it is fairly strong and aligns with the reverse docs in `docs/`.

## 2. Relevant repo map

- `README.md`
- `docs/`
  - `docs/index.md`
  - `docs/notation.md`
  - `docs/data-landscape.md`
  - `docs/baseline-hofman.md`
  - `docs/harmonized-perez.md`
  - `docs/harmonized-bcch.md`
  - `docs/source-reconciliation.md`
  - `docs/reproducibility.md`
  - `docs/code-map.md`
  - `docs/validation.md`
  - `docs/release-v1.1.0.md`
- `codes/`
  - `codes/run_baseline_hofman_1980.py`
  - `codes/run_harmonization.py`
  - `codes/run_harmonization_bcch.py`
- `data/raw/`
  - `data/raw/Hofman2000_GrossInvestment.xlsx`
  - `data/raw/Hofman_Kstock_gross_net_19501994.xlsx`
  - `data/raw/PerezEyzaguirre_DemandaAgregada.xlsx`
  - `data/raw/BCCH_1985_2024.xlsx`
  - `data/raw/BCCH_ref2018_Pk.xlsx`
  - `data/raw/ClioLab_GFKF_Freal_nominal_Pk.xlsx`
  - `data/raw/Kn_ClioLab.xlsx`
- `outputs/`
  - `outputs/assumptions_baseline_1980.yaml`
  - `outputs/survival_fit_hofman_1980.csv`
  - `outputs/survival_fit_notes.txt`
  - `outputs/harmonized_series_1980CLP_1900_1994.csv`
  - `outputs/DIAGNOSTIC_DEFINITION_CROSSWALK_v1/summary.md`
  - `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/lambda_estimates.yaml`
  - `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/summary.md`
  - `outputs/EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md`
  - `outputs/EXTENSION_CANDIDATE_STOCKS_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md`
  - `outputs/HARMONIZED_PEREZ_2003CLP_v1/assumptions.yaml`
  - `outputs/HARMONIZED_PEREZ_2003CLP_v1/harmonized_series_2003CLP_1900_1994.csv`
  - `outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md`
  - `outputs/HARMONIZED_BCCH_2003CLP_v1/assumptions.yaml`
  - `outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_series_2003CLP_1900_2024.csv`
  - `outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_pk_2003base_1940_2024.csv`
  - `outputs/HARMONIZED_BCCH_2003CLP_v1/bcch_bridge_audit_summary_1985_1994.txt`
  - `outputs/HARMONIZED_BCCH_2003CLP_v1/pk_splice_diagnostics.csv`
  - `outputs/HARMONIZED_BCCH_2003CLP_v1/summary.md`
- dissertation-facing artifacts
  - `artifacts/harmonization-implementation-procedure.md`
  - `artifacts/stock-flow-consistent-approach.md`

## 3. File inventory

| Path | Type | Scope | Main function | Key objects | Priority |
| --- | --- | --- | --- | --- | --- |
| `README.md` | doc | repo contract | Defines the three public surfaces and production commands | `run_baseline_hofman_1980.py`, `run_harmonization.py`, `run_harmonization_bcch.py` | High |
| `docs/notation.md` | doc | shared method | Defines stock-flow notation and gross/net concepts | `I`, `Kg`, `Kn`, `B`, `R`, `D`, `z`, `delta`, `Pk` | High |
| `docs/data-landscape.md` | doc | sources | States which raw inputs are active, diagnostic, or deferred | Perez, Hofman, BCCh, ClioLab, Tafunell | High |
| `docs/baseline-hofman.md` | doc | baseline reference | Explains overlap recovery, Weibull fitting, anchoring, and gap extension | overlap `1950-1994`, Weibull, `B/Kg` | High |
| `docs/harmonized-perez.md` | doc | canonical Chile baseline | Explains the canonical `1900-1994` 2003-CLP construction | `lambda_choice`, Hofman shares, survival reuse, gap-ratio reuse | High |
| `docs/harmonized-bcch.md` | doc | Chile extension | Explains the additive BCCh splice and `Pk` construction | `1994` hard anchor, `I = DeltaKn + D`, `Pk` ratio splice | High |
| `docs/source-reconciliation.md` | doc | source harmonization | States source hierarchy and partial comparability | Hofman vs Perez, BCCh role, Clio role, Tafunell deferred | High |
| `docs/reproducibility.md` | doc | reproducibility | States command-level provenance contract | `assumptions.yaml`, `input_hashes`, `git_commit` | High |
| `docs/code-map.md` | doc | repo navigation | Separates active endpoints from historical diagnostics | three active endpoints | Medium |
| `codes/run_baseline_hofman_1980.py` | script | frozen accounting reference | Recovers implied retirements/depreciation, fits survival, reconstructs pre-1950 stocks | `overlap_recovery`, `fit_survival`, `anchor_pre1950_kg`, `extend_gap_ratio` | High |
| `codes/run_harmonization.py` | script | canonical Chile harmonization | Builds Perez-based asset investment block and accumulates stocks in 2003 CLP | `build_investment_block`, `accumulate_stocks`, `build_net_block`, `compute_depreciation` | High |
| `codes/run_harmonization_bcch.py` | script | BCCh extension | Preserves legacy panel, bridges BCCh `Kn`/`D`, infers post-1994 `I`, rebuilds `Kg`/`R` | `build_bridge_factors`, `scale_bcch_blocks`, `build_full_investment`, `accumulate_gross_and_retirements` | High |
| `data/raw/Hofman2000_GrossInvestment.xlsx` | raw data | baseline + share system | Flow input for frozen baseline and asset-share source for Perez split | `Ig_ME`, `Ig_NRC`, `Ig_RC`, `Ig_tot` | High |
| `data/raw/Hofman_Kstock_gross_net_19501994.xlsx` | raw data | baseline overlap | Gross and net observed stocks for recovery window | `Kg`, `Kn`, overlap `1950-1994` | High |
| `data/raw/PerezEyzaguirre_DemandaAgregada.xlsx` | raw data | canonical mother series | Aggregate control total in 2003 CLP, excluding inventories in production | machinery, construction, inventories | High |
| `data/raw/BCCH_1985_2024.xlsx` | raw data | extension | Net stocks and depreciation by asset for post-1994 extension | BCCh `Kn`, BCCh `D` | High |
| `data/raw/BCCH_ref2018_Pk.xlsx` | raw data | extension deflator | Primary `Pk` ratio-deflator source for `1960-2024` | `FBKF_nom`, `FBKF_real` | Medium |
| `data/raw/ClioLab_GFKF_Freal_nominal_Pk.xlsx` | raw data | extension deflator | Backcast growth source for `Pk` `1940-1959` | chained ratio growth | Medium |
| `outputs/assumptions_baseline_1980.yaml` | output metadata | baseline method lock | Locks survival family, parameters, anchor rule, and gap extension | Weibull params, anchor rule, `gap_extension` | High |
| `outputs/survival_fit_hofman_1980.csv` | output data | retirement/service lives | Stores fitted survival parameters reused downstream | `family`, `scale`, `shape`, `mean_life`, `rmse` | High |
| `outputs/DIAGNOSTIC_DEFINITION_CROSSWALK_v1/summary.md` | diagnostic output | comparability | Records unresolved source-definition comparability | `comparability_flag=PARTIAL` | Medium |
| `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/lambda_estimates.yaml` | diagnostic output | parameter locking | Stores the chosen level-normalization bridge | `lambda_choice`, `lambda_rule`, `n_obs` | High |
| `outputs/EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md` | diagnostic output | candidate build | Documents the pre-production asset split logic | normalized Hofman shares, candidate `I` | Medium |
| `outputs/EXTENSION_CANDIDATE_STOCKS_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md` | diagnostic output | candidate stocks | Documents candidate stock accumulation before promotion | inherited survival, identity checks | Medium |
| `outputs/HARMONIZED_PEREZ_2003CLP_v1/assumptions.yaml` | output metadata | canonical bundle | Locks canonical assumptions and input hashes | `lambda_choice`, provenance, input hashes | High |
| `outputs/HARMONIZED_PEREZ_2003CLP_v1/harmonized_series_2003CLP_1900_1994.csv` | output data | canonical bundle | Public canonical harmonized panel | `I`, `Kg`, `Kn`, `B`, `R`, `D` | High |
| `outputs/HARMONIZED_BCCH_2003CLP_v1/assumptions.yaml` | output metadata | extension bundle | Locks BCCh bridge factors and splice rules | `bridge_factors_1994`, `pk_splice_rule` | High |
| `outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_series_2003CLP_1900_2024.csv` | output data | extension bundle | Public extended Chile stock panel | legacy-preserved panel plus `1995-2024` extension | High |
| `outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_pk_2003base_1940_2024.csv` | output data | extension bundle | Companion investment-deflator surface | `Pk` rebased to `2003=100` | Medium |
| `artifacts/harmonization-implementation-procedure.md` | artifact doc | dissertation drafting | High-level procedural narrative from repo evidence | workflow stages, source roles | Medium |
| `artifacts/stock-flow-consistent-approach.md` | artifact doc | dissertation drafting | High-level stock-flow narrative from repo evidence | identity logic, closure language | Medium |

## 4. Shared methodological relevance

- **Depreciation vs retirement**
  - `docs/notation.md` defines `R` and `D`.
  - `codes/run_baseline_hofman_1980.py` recovers `R_imp` and `D_imp` from the overlap and fits survival to retirements.
  - `codes/run_harmonization.py` keeps retirement and depreciation distinct through `accumulate_stocks()` and `compute_depreciation()`.
  - `codes/run_harmonization_bcch.py` preserves that distinction by taking BCCh `D` as an input but reconstructing `R` from inherited survival logic.
- **Gross vs net capital stock**
  - `docs/notation.md`, `docs/baseline-hofman.md`, and `docs/harmonized-perez.md` are the core narrative files.
  - `codes/run_baseline_hofman_1980.py` builds `Kg`, then derives `Kn` via the capital gap.
  - `codes/run_harmonization.py` reproduces the same split with `build_net_block()`.
  - `codes/run_harmonization_bcch.py` makes the BCCh extension explicit: BCCh supplies `Kn` and `D`; the repo reconstructs `Kg` and `R`.
- **GPIM recursion**
  - `codes/run_baseline_hofman_1980.py` provides the core kernel functions: `retirement_from_survival()` and `stock_from_survival()`.
  - `codes/run_harmonization.py` applies the same recursion to the Perez-based investment block in `accumulate_stocks()`.
  - `codes/run_harmonization_bcch.py` reuses the same survival recursion to extend `Kg` and `R` after the BCCh splice.
- **Parameter locking**
  - `outputs/assumptions_baseline_1980.yaml` locks Weibull family and parameters.
  - `outputs/survival_fit_hofman_1980.csv` locks fitted service-life inputs.
  - `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/lambda_estimates.yaml` locks `lambda_choice`.
  - `outputs/HARMONIZED_PEREZ_2003CLP_v1/assumptions.yaml` and `outputs/HARMONIZED_BCCH_2003CLP_v1/assumptions.yaml` lock production-time assumptions and hashes.
- **Source provenance**
  - `docs/data-landscape.md` and `docs/source-reconciliation.md` are the best prose sources.
  - The two production `assumptions.yaml` files record source paths and SHA256 hashes.
- **Reproducibility / assumptions**
  - `README.md` and `docs/reproducibility.md` define the contract.
  - The two public output bundles provide the dissertation-ready reproducibility surface.

## 5. Country-specific role of this repo

This repo is **Chile harmonized capital-stock construction**.

It should appear in the dissertation as the **Chile data-construction and harmonization repository**: a repo that starts from a frozen Hofman accounting reference, promotes Perez as the canonical aggregate mother series for `1900-1994`, and then adds a BCCh forward extension to `2024` without rewriting the validated canonical history. It should **not** be described as a U.S. direct-source capital-stock construction repo.

## 6. Main text vs appendix handoff

- **Main text, compressed**
  - One paragraph on the three-layer architecture: frozen Hofman reference, canonical Perez harmonized panel, additive BCCh extension.
  - One paragraph on the source hierarchy: Perez as promoted control total, Hofman as structural skeleton, BCCh as forward extension, ClioLab only for `Pk` backcast and diagnostics.
  - One paragraph on the stock logic: inventory exclusion, `lambda_choice`, Hofman shares, Weibull survival reuse, gap-ratio reuse, and exact preservation of the pre-1995 canonical history in the BCCh bundle.
- **Appendix only**
  - Exact overlap and admissibility windows.
  - Full GPIM/survival recursion mechanics and kernel functions.
  - Exact Weibull parameters and mean service lives by asset.
  - `1994` bridge factors and `Pk` splice details.
  - Diagnostic history: crosswalk, unit-scale audit, lambda diagnostics, candidate investment-block and candidate-stock stages.
  - Provenance fields, input hashes, and release-style output lists.

## 7. Immediate writing-use outputs

- **Shared data architecture**
  - `README.md`
  - `docs/index.md`
  - `docs/notation.md`
  - `docs/data-landscape.md`
  - `docs/source-reconciliation.md`
  - `docs/reproducibility.md`
- **Country subsection**
  - `docs/harmonized-perez.md`
  - `docs/harmonized-bcch.md`
  - `outputs/HARMONIZED_PEREZ_2003CLP_v1/summary.md`
  - `outputs/HARMONIZED_BCCH_2003CLP_v1/summary.md`
- **GPIM / retirement appendix**
  - `codes/run_baseline_hofman_1980.py`
  - `outputs/assumptions_baseline_1980.yaml`
  - `outputs/survival_fit_hofman_1980.csv`
  - `outputs/survival_fit_notes.txt`
  - `codes/run_harmonization.py`
- **Source-reconciliation appendix**
  - `docs/source-reconciliation.md`
  - `outputs/DIAGNOSTIC_DEFINITION_CROSSWALK_v1/summary.md`
  - `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/summary.md`
  - `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/lambda_estimates.yaml`
  - `outputs/EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md`
  - `outputs/EXTENSION_CANDIDATE_STOCKS_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/summary.md`

## 8. Gaps or messiness

- The repo is well documented overall, but the construction logic is split across README, reverse docs, code, and output summaries rather than one single dissertation-facing methods memo.
- The dual baseline language can be narratively awkward: Hofman is frozen but still structurally central, while Perez is canonical for publication.
- GPIM mechanics are most explicit in code, not prose; the docs are clear on workflow but lighter on exact recursion details.
- Historical diagnostic stages are numerous and can distract from the three active endpoints if listed without filtering.
- `tmp/HARMONIZED_BCCH_2003CLP_v1_precommit/` duplicates a public bundle and is not a clean dissertation-facing surface.
- There is an untracked file, `artifacts/stock-flow-consistent-approach_US.md`, whose `_US` suffix is narratively misleading in a Chile repo.
- `data/raw/Hofman2000_anchors.xlsx` appears in documentation as part of reporting-space history, but it is not central to the active canonical construction path.

## 9. Evidence snippets

- `README.md`
  - "Stock-flow consistent capital-stock harmonization for Chile."
- `docs/baseline-hofman.md`
  - "Fits Weibull survival functions by asset."
- `outputs/assumptions_baseline_1980.yaml`
  - "survival_family: ... ME: weibull ... NRC: weibull ... RC: weibull"
- `codes/run_harmonization.py`
  - `investment["I_control_scaled"] = investment["I_control_ex_inventory"] * lambda_choice`
- `outputs/DIAGNOSTIC_DEFINITION_CROSSWALK_v1/summary.md`
  - "comparability_flag=PARTIAL"
- `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/summary.md`
  - "Chosen lambda: 4.105381794084627"
- `docs/harmonized-bcch.md`
  - "Infer post-1994 real investment with `I_t = DeltaKn_t + D_t`."
- `outputs/HARMONIZED_BCCH_2003CLP_v1/bcch_bridge_audit_summary_1985_1994.txt`
  - "Legacy history through 1994 preserved exactly: True"
