# V01_LOW — CFD case audit (Section 9B-1)

> **RE-ANALYSIS 2026.** Automation-integrity record of this case, generated from the raw audit files.

## 1. Intended vs actual change

Intended change (param_cases.py): `{"V_IN": 21.15, "TI": 0.04469689751121414}`

Settings diff after mesh replace: **0** differences (must be 0).

Settings diff after the intended change (full settings tree, `Audit/frozen_physics_gate.json`): **2** paths

| Path | P00 | Case |
|---|---|---|
| `/setup/boundary_conditions/velocity_inlet/fluid_inlet/momentum/velocity_magnitude/value` | 23.5 | 21.15 |
| `/setup/boundary_conditions/velocity_inlet/fluid_inlet/turbulence/turbulent_intensity` | 0.04411209588036475 | 0.04469689751121414 |

Unexpected paths: 0 · intended-but-absent: 0 · gate: **PASS**

## 2. Unchanged settings (read back from Fluent and compared with P00's own audit)

| Audit stage | Items | Failed | Rows identical to P00 | Rows changed as intended |
|---|---|---|---|---|
| 1_presolve | 133 | 0 | 57 | inlet velocity [m/s], inlet turbulent intensity [-] |
| 2_final_schemes | 133 | 0 | 57 | inlet velocity [m/s], inlet turbulent intensity [-] |
| 3_final | 133 | 0 | 57 | inlet velocity [m/s], inlet turbulent intensity [-] |

The common rows cover solver, models, materials (all six property curves), cell-zone materials, every boundary condition, schemes, pseudo-time controls, limits and equations.

## 3. Mesh

| Item | Value |
|---|---|
| File | `../../../06_Fluent_CFD/Case/medium_mesh_used_for_baseline.msh` |
| SHA-256 | `2C6FCFB31108654DB2361449127761ECF687D7446C740C33C0BB350877363479` |
| Cells (printed by Fluent) / expected | 159840 / 159840 |
| Minimum cell volume [m³] | 9.051023e-11 |
| Minimum orthogonal quality (Fluent) | 0.445829 |
| Mesh-check warnings | none |

## 4. Convergence

| Evaluation | Converged | Failing checks |
|---|---|---|
| stage3+100 (iter 400) | not evaluable | residuals ok, stage-3 rows 100 < 200 |
| stage3+200 (iter 500) | no | drift T_out_bulk over 200 it [K], drift T_solid_max over 200 it [K], drift T_wall_max over 200 it [K], drift T_outer_max over 200 it [K], rel drift dp_area over 200 it, rel drift q_interface over 200 it, rel drift mdot_out over 200 it |
| stage3+300 (iter 600) | yes | none |
| confirmation+400 (iter 700) | yes | none |

Final evaluation values:

| Criterion | Value | Target |
|---|---|---|
| residual continuity | 8.343e-11 | 1.0e-04 |
| residual x-velocity | 4.298e-16 | 1.0e-04 |
| residual y-velocity | 3.531e-16 | 1.0e-04 |
| residual z-velocity | 1.998e-14 | 1.0e-04 |
| residual k | 9.282e-13 | 1.0e-04 |
| residual omega | 3.296e-13 | 1.0e-04 |
| residual energy | 1.444e-14 | 1.0e-06 |
| drift T_out_bulk over 200 it [K] | 4.713e-06 | 1.0e-01 |
| drift T_solid_max over 200 it [K] | 1.453e-05 | 1.0e-01 |
| drift T_wall_max over 200 it [K] | 6.104e-05 | 1.0e-01 |
| drift T_outer_max over 200 it [K] | 6.104e-05 | 1.0e-01 |
| rel drift dp_area over 200 it | 7.333e-10 | 1.0e-03 |
| rel drift q_interface over 200 it | 5.515e-09 | 1.0e-03 |
| rel drift mdot_out over 200 it | 2.063e-10 | 1.0e-04 |
| mass imbalance \|in-out\|/in | 7.566e-15 | 1.0e-04 |
| energy imbalance \|sum Q\|/Q_wall | 1.337e-12 | 5.0e-03 |

## 5. Property tables and solver messages (every iteration of every stage)

Checked by the journal after every iterate call (7 checks, all ok: True) and re-checked here from the raw monitor file.

| Monitor | History min [K] | History max [K] | Iteration of max | Converged [K] |
|---|---|---|---|---|
| T_fluid_max | 300.000 | 578.614 | 378 | 578.586 |
| T_fluid_min | 299.997 | 300.000 | 160 | 300.000 |
| T_wall_max | 300.000 | 580.404 | 377 | 580.377 |
| T_out_bulk | 300.000 | 376.963 | 308 | 376.557 |
| T_in_bulk | 300.000 | 300.000 | 1 | 300.000 |
| T_solid_max | 300.000 | 587.058 | 377 | 587.031 |
| T_solid_min | 300.000 | 437.179 | 309 | 436.049 |
| T_outer_max | 300.000 | 587.495 | 377 | 587.467 |
| T_outer_avg | 300.000 | 549.958 | 309 | 549.869 |
| T_inner_avg | 300.000 | 542.426 | 309 | 542.334 |

Solver messages matching limiter / reversed-flow / divergence formats: none

## 6. Heat input, balances, exports

| Check | Value |
|---|---|
| q″ set / area-average read back [W/m²] | 8000.000000 / 8000.000000 |
| Heated area (Fluent) [m²] | 7.534440500e-02 |
| Q Fluent / q″·A [W] | 602.755240 / 602.755240 |
| Q vs P00 | +0.0000e+00 (relative) |
| Mass imbalance | 7.566e-15 (target < 1e-4) |
| Energy imbalance | 1.337e-12 (target < 5e-3) |
| Volume export rows | {"cells_fluid.csv": 116640, "cells_solid.csv": 43200} |
| EnSight files | {"solid_domain_T.encas": 287, "solid_domain_T.geo": 2427848, "solid_domain_T.scl1": 260792, "solid_domain_T.vel": 779592, "solid_domain_T.xml": 882} |

## 7. Versions

| Item | Value |
|---|---|
| Fluent | Ansys Fluent 2026 R1 |
| Journal `solve_param.py` SHA-256 | `8205529CA5FE21C0524417EDCCE11F7DCC8224414D208858E32E082544BCA10B` |
| `param_cases.py` SHA-256 | `06FEE3EAEDA60968799F123695D1B5C782D5CCE91258612952B5CB885D478346` |

**Overall: CONVERGED_VALID**

