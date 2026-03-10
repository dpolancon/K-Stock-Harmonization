# Code Map

This map links scripts to their committed outputs and methodological role.

| Script | Role in repository | Main committed output |
| --- | --- | --- |
| `codes/run_baseline_hofman_1980.py` | Frozen Hofman accounting reference | `outputs/harmonized_series_1980CLP_1900_1994.csv` |
| `codes/extension_reporting_2003clp_v1.py` | Reporting-space conversion of frozen baseline | `outputs/EXTENSION_REPORTING_2003CLP_v1/` |
| `codes/anchor_pack_perez_fbfk_2003clp_v1.py` | Perez raw anchor pack in 2003 CLP | `outputs/ANCHOR_PEREZ_FBFK_2003CLP_v1/` |
| `codes/anchor_pack_perez_fbfk_2003clp_v2_scaled.py` | Perez anchor pack after lambda scaling | `outputs/ANCHOR_PEREZ_FBFK_2003CLP_v2_SCALED/` |
| `codes/diagnostic_definition_crosswalk_v1.py` | Comparability diagnostics between baseline and Perez concepts | `outputs/DIAGNOSTIC_DEFINITION_CROSSWALK_v1/` |
| `codes/diagnostic_level_normalization_lambda_perez_vs_baseline_2003clp_v1.py` | Lambda estimation for level normalization | `outputs/DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1/` |
| `codes/diagnostic_unit_scale_audit_perez_vs_baseline_2003clp_v1.py` | Unit-scale audit | `outputs/DIAGNOSTIC_UNIT_SCALE_AUDIT_v1/` |
| `codes/extension_investment_block_candidate_perez_scaled_hofman_shares_2003clp_v1.py` | Candidate Perez investment block after scaling and Hofman split | `outputs/EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/` |
| `codes/extension_candidate_stocks_from_investment_block_perez_scaled_hofman_shares_2003clp_v1.py` | Candidate stock reconstruction from the scaled Perez block | `outputs/EXTENSION_CANDIDATE_STOCKS_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1/` |
| `codes/extension_external_compare_perez_2003clp_v1.py` | Raw baseline-versus-Perez comparison | `outputs/EXTENSION_EXTERNAL_COMPARE_PEREZ_2003CLP_v1/` |
| `codes/extension_external_compare_perez_fbfk_2003clp_v1.py` | Perez FBKF comparison stage | `outputs/EXTENSION_EXTERNAL_COMPARE_PEREZ_FBFK_2003CLP_v1/` |
| `codes/extension_external_compare_perez_fbfk_2003clp_v2.py` | Follow-up Perez FBKF comparison stage | `outputs/EXTENSION_EXTERNAL_COMPARE_PEREZ_FBFK_2003CLP_v2/` |
| `codes/extension_external_compare_perez_fbfk_2003clp_v3_scaled.py` | Scaled Perez FBKF comparison stage | `outputs/EXTENSION_EXTERNAL_COMPARE_PEREZ_FBFK_2003CLP_v3_SCALED/` |
| `codes/capital_stock_series_perez_toggle_b_2003clp_v1.py` | Earlier candidate stock experiment with fixed-capital closure | `outputs/CAPITAL_STOCK_SERIES_PEREZ_TOGGLE_B_2003CLP_v1/` |
| `codes/run_harmonization.py` | Canonical production baseline in 2003 CLP | `outputs/HARMONIZED_PEREZ_2003CLP_v1/` |

## Reading rule

For dissertation-level reverse documentation, the scripts above should be read as a history with one active endpoint:

- frozen reference endpoint: `codes/run_baseline_hofman_1980.py`
- production endpoint: `codes/run_harmonization.py`

All other scripts are historical diagnostics, bridges, or candidate builders.
