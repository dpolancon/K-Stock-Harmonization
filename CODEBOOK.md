# Master Codebook and Data Dictionary

## Dataset Title
**Harmonized Net and Gross Capital Stocks, Depreciation Rates, and Price Index for Chile (1900–2024)**

## Master Output File
- **CSV Surface**: `outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_master_dataset_2003CLP_1900_2024.csv`
- **Excel Surface**: `outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_master_dataset_2003CLP_1900_2024.xlsx`

## Overview & Scope
This codebook defines the complete set of variables in the master publication dataset. The dataset provides continuous, stock-flow consistent estimates of real gross and net capital stocks, investment flows, retirements, depreciation, implicit rates of depletion and depreciation, and the capital price deflator for Chile from 1900 to 2024.

- **Temporal Coverage**: 1900–2024 (125 annual observations).
- **Price Space**: Constant 2003 Chilean Pesos (2003 CLP).
- **Asset Categories** (`asset`):
  1. `ME`: Machinery & Equipment
  2. `NRC`: Non-Residential Construction
  3. `RC`: Residential Construction
  4. `NR`: Non-Residential Total (`ME + NRC`)
  5. `Total`: Total Fixed Capital Stock (`ME + NRC + RC`)

---

## Data Dictionary

| Variable Name | Type | Units / Format | Primary Source / Method | Variable Description & Identity |
| :--- | :--- | :--- | :--- | :--- |
| `year` | Integer | YYYY (1900–2024) | Primary timeline | Calendar year of observation |
| `asset` | Categorical | String (`ME`, `NRC`, `RC`, `NR`, `Total`) | Asset classification | Capital asset classification tag |
| `I` | Float | Millions of 2003 CLP | Perez (1900–1994), BCCh inferred (1995–2024) | Real Gross Fixed Capital Formation (Investment) |
| `Kg` | Float | Millions of 2003 CLP | Generalized Perpetual Inventory Method (GPIM) | Real Gross Capital Stock ($K_{g,t} = K_{g,t-1} + I_t - R_t$) |
| `Kn` | Float | Millions of 2003 CLP | Perez canonical (1900–1994), BCCh bridged (1995–2024) | Real Net Capital Stock ($K_{n,t} = K_{n,t-1} + I_t - D_t$) |
| `B` | Float | Millions of 2003 CLP | Stock-flow identity | Capacity Backlog / Discarded Capital ($B_t = K_{g,t} - K_{n,t}$) |
| `R` | Float | Millions of 2003 CLP | Weibull survival convolution | Real Gross Retirements / Disposals ($R_t = \sum_{\tau} I_{t-\tau} f(\tau)$) |
| `D` | Float | Millions of 2003 CLP | Perez canonical (1900–1994), BCCh bridged (1995–2024) | Real Consumption of Fixed Capital (Depreciation) |
| `DeltaKg` | Float | Millions of 2003 CLP | Stock difference | Annual change in gross capital stock ($\Delta K_{g,t} = K_{g,t} - K_{g,t-1}$) |
| `DeltaKn` | Float | Millions of 2003 CLP | Stock difference | Annual change in net capital stock ($\Delta K_{n,t} = K_{n,t} - K_{n,t-1}$) |
| `DeltaB` | Float | Millions of 2003 CLP | Backlog difference | Annual change in capacity backlog ($\Delta B_t = B_t - B_{t-1}$) |
| `z` | Float | Annual fraction | Implicit rate calculation | Rate of Gross Disposals / Depletion ($z_t = R_t / K_{g,t-1}$) |
| `delta` | Float | Annual fraction | Implicit rate calculation | Rate of Net Depreciation ($\delta_t = D_t / K_{n,t-1}$) |
| `Pk_2003base` | Float | Index (2003 = 100) | BCCh ratio (1960–2024), ClioLab backcast (1940–1959) | Capital Price Index ($P_k$). Populated for 1940–2024; null for 1900–1939. |
| `residual_kg` | Float | Millions of 2003 CLP | Identity audit | Gross accumulation residual ($\Delta K_{g,t} - (I_t - R_t)$) |
| `residual_kn` | Float | Millions of 2003 CLP | Identity audit | Net accumulation residual ($\Delta K_{n,t} - (I_t - D_t)$) |
| `I_residual` | Float | Millions of 2003 CLP | Additivity audit | Asset sum residual ($I_{\text{Total}} - (I_{\text{ME}} + I_{\text{NRC}} + I_{\text{RC}})$) |

---

## Variable Definitions & Methodological Details

### 1. Stock-Flow Accounting Framework
The dataset operates under strict stock-flow consistency:
- **Gross Stock Accumulation**:
  $$\Delta K_{g,t} = I_t - R_t \implies K_{g,t} = K_{g,t-1} + I_t - R_t$$
- **Net Stock Accumulation**:
  $$\Delta K_{n,t} = I_t - D_t \implies K_{n,t} = K_{n,t-1} + I_t - D_t$$
- **Capacity Backlog Identity**:
  $$B_t = K_{g,t} - K_{n,t} \implies \Delta B_t = R_t - D_t$$

### 2. Implicit Depletion and Depreciation Rates
- **Gross Disposals / Depletion Rate ($z_t$)**: The ratio of annual gross retirements to the previous year's gross capital stock:
  $$z_t = \frac{R_t}{K_{g,t-1}}$$
- **Net Depreciation Rate ($\delta_t$)**: The ratio of annual consumption of fixed capital to the previous year's net capital stock:
  $$\delta_t = \frac{D_t}{K_{n,t-1}}$$

### 3. Capital Price Deflator ($P_k$)
- **1960–2024**: Derived directly from Central Bank of Chile (BCCh) official national accounts as the ratio deflator:
  $$P_{k,t}^{\text{raw}} = \frac{\text{FBKF}_{\text{nominal}, t}}{\text{FBKF}_{\text{real}, t}}$$
  rebased such that $P_k(2003) = 100.0$.
- **1940–1959**: Backcast using chained annual growth rates from the ClioLab investment deflator ratio, anchored to the BCCh 1960 level:
  $$P_{k,t} = P_{k,t+1} \times \left( \frac{P_{k,t}^{\text{Clio}}}{P_{k,t+1}^{\text{Clio}}} \right)$$

---

## Provenance & Quality Flags
- **1900–1994**: Historical rows preserved exactly from the canonical Perez 2003 CLP baseline.
- **1995–2024**: BCCh forward extension using 1994 hard-anchor bridge factors.
- **2023**: Flagged as `provisional` in official BCCh reporting.
- **2024**: Flagged as `preliminary` in official BCCh reporting.
