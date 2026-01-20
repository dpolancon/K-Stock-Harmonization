# BASELINE_1980_HOFMAN_v1  
**Jointly Stock–Flow Consistent Capital Stocks for Chile (1900–1994)**

## Status
🔒 **FROZEN BASELINE — DO NOT MODIFY**

This directory contains the frozen reference implementation of the **Hofman-only,
1980-price baseline** for reconstructing gross and net capital stocks in Chile using
a jointly stock–flow consistent (j-SFC) framework.

All subsequent harmonization work (Perez integration, deflators, alternative splices,
robustness checks) **must branch from this baseline** and must not overwrite it.

---

## Purpose of this Baseline

This baseline establishes the **maximum internally coherent reconstruction** that can
be achieved using:

- Hofman (2000) investment and stock data only
- Native valuation: **constant 1980 Chilean pesos**
- No external control totals
- No deflators
- No cross-source scaling

It answers the question:

> *“What does the data look like when the accounting identities work exactly as intended?”*

This baseline is the **accounting reference point** for all later harmonization steps.

---

## Data Sources Used (Exclusively)

- **Hofman (2000)**  
  *Standardised capital stock estimates in Latin America*  
  - Gross fixed capital formation (by asset)
  - Gross capital stock (Kg)
  - Net capital stock (Kn)
  - Asset categories:
    - Machinery & Equipment (ME)
    - Non-Residential Construction (NRC)
    - Residential Construction (RC)

No Perez-Eyzaguirre, ClioLab, Tafunell, Díaz–Wagner, or deflated series are used here.

---

## Valuation and Units

- **Prices**: Constant **1980 CLP**
- **Additivity**: Preserved exactly (no chain weighting)
- **Accounting space**: Fully additive, identity-safe

---

## Methodological Closure

### Core Identities (j-SFC)

For each asset \( a \):

- Gross stock:
  \[
  \Delta K^g_{a,t} = I^g_{a,t} - R_{a,t}
  \]

- Net stock:
  \[
  \Delta K^n_{a,t} = I^g_{a,t} - D_{a,t}
  \]

- Implied flows:
  \[
  R_{a,t} = I^g_{a,t} - \Delta K^g_{a,t}
  \]
  \[
  D_{a,t} = I^g_{a,t} - \Delta K^n_{a,t}
  \]

- Rates:
  \[
  z_{a,t} = R_{a,t} / K^g_{a,t-1}
  \]
  \[
  \delta_{a,t} = D_{a,t} / K^n_{a,t-1}
  \]

These rates are **diagnostics**, not calibration parameters.

---

## Retirement & Survival Logic

- **Observed period (1950–1994)**:
  - Retirements and depreciation recovered directly from identities
  - No imposed schedules

- **Estimated survival functions**:
  - Weibull fits to implied retirements in the overlap
  - Used only to reconstruct **pre-1950** stocks

Estimated mean service lives (overlap-based):

| Asset | Mean Life (years) |
|------|------------------|
| ME   | ~14 |
| NRC  | ~38 |
| RC   | ~47 |

---

## Pre-1950 Reconstruction Strategy

- **Anchoring**:
  - Pre-1950 stocks are scaled to exactly hit observed \( K^g_{1950} \) by asset

- **Gap extension rule**:
  - The **median overlap capital gap ratio**  
    \[
    B_t / K^g_t
    \]
    (where \( B_t = K^g_t - K^n_t \))  
    is extended backward by asset to recover net stocks.

This rule is simple, transparent, and identity-preserving.

---

## Diagnostics Summary

### Overlap Period (1950–1994)

- Negative retirements: **0 / 45 years**
- Negative depreciation: **0 / 45 years**
- All admissibility constraints satisfied

### Full Period (1900–1994)

- No negative stocks
- Early-period rate warnings only (expected in retropolation)
- No identity violations

This is the **only run** that passes all j-SFC admissibility checks without qualification.

---

## Outputs

Key files:

- `harmonized_series_1980CLP_1900_1994.csv`
- `rates_1900_1994.csv`
- `audit_full_1900_1994.csv`
- `survival_fit_hofman_1980.csv`
- `assumptions_baseline_1980.yaml`
- `violation_log_baseline_1980.csv`

---

## Naming & Versioning

This baseline is locked as:

