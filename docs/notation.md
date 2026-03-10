# Notation

This document defines the variables and aggregates used across the frozen Hofman baseline and the canonical Perez harmonized baseline.

## Core variables

| Symbol | Meaning | Interpretation in repo evidence |
| --- | --- | --- |
| `I` | Gross fixed investment flow | Annual flow used for accumulation |
| `Kg` | Gross capital stock | Stock before subtracting the capital gap |
| `Kn` | Net capital stock | Stock after subtracting the capital gap |
| `B` | Capital gap | `Kg - Kn` |
| `R` | Retirements | Implied gross-stock outflow |
| `D` | Depreciation | Implied net-stock outflow |
| `z` | Retirement rate | `R / Kg(t-1)` |
| `delta` | Depreciation rate | `D / Kn(t-1)` |
| `DeltaKg` | Change in gross stock | First difference of `Kg` |
| `DeltaKn` | Change in net stock | First difference of `Kn` |
| `DeltaB` | Change in capital gap | First difference of `B` |

## Asset groups

| Code | Meaning | Evidence |
| --- | --- | --- |
| `ME` | Machinery and equipment | Present in Hofman and Perez processing paths |
| `NRC` | Non-residential construction | Present in Hofman and Perez processing paths |
| `RC` | Residential construction | Present in Hofman paths and recovered in the harmonized split through Hofman shares |
| `NR` | Non-residential aggregate | `ME + NRC` |
| `Total` | Total fixed capital | `ME + NRC + RC` |

## Price spaces

| Space | Role |
| --- | --- |
| Constant 1980 CLP | Frozen Hofman accounting reference |
| Constant 2003 CLP | Canonical harmonized publication space |

`docs/harmonized-perez.md` uses "ex inventories" to mean excluding inventories. In the canonical production path, inventories are not accumulated into capital stock.
