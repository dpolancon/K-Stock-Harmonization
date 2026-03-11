# Notation

This document defines the variables and aggregates used across the frozen Hofman baseline, the canonical Perez harmonized baseline, and the additive BCCh extension bundle.

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
| `Pk` | Investment deflator | Companion price series rebased to `2003=100` in the BCCh bundle |

## Asset groups

| Code | Meaning | Evidence |
| --- | --- | --- |
| `ME` | Machinery and equipment | Present in Hofman, Perez, and BCCh processing paths |
| `NRC` | Non-residential construction | Present in Hofman, Perez, and BCCh processing paths |
| `RC` | Residential construction | Present in Hofman and BCCh paths and recovered in the Perez split through Hofman shares |
| `NR` | Non-residential aggregate | `ME + NRC` |
| `Total` | Total fixed capital | `ME + NRC + RC` |

## Price spaces

| Space | Role |
| --- | --- |
| Constant 1980 CLP | Frozen Hofman accounting reference |
| Constant 2003 CLP | Public harmonized stock publication space |
| `Pk` rebased to `2003=100` | Public investment-deflator publication space for the BCCh bundle |

`docs/harmonized-perez.md` uses "ex inventories" to mean excluding inventories. In both 2003-CLP stock publication surfaces, inventories remain outside capital-stock accumulation.
