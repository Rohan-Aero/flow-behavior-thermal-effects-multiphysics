# Q03_HIGH — CFD case audit (Section 9B-1)

> **RE-ANALYSIS 2026.** Automation-integrity record of this case, generated from the raw audit files.

## 1. Intended vs actual change

Intended change (param_cases.py): `{"QPP": 8800.0}`

Settings diff after mesh replace: **0** differences (must be 0).

Settings diff after the intended change (full settings tree, `Audit/frozen_physics_gate.json`): **1** paths

| Path | P00 | Case |
|---|---|---|
| `/setup/boundary_conditions/wall/heated_outer_wall/thermal/heat_flux/value` | 8000.0 | 8800.0 |

Unexpected paths: 0 · intended-but-absent: 0 · gate: **PASS**

## 2. Unchanged settings (read back from Fluent and compared with P00's own audit)

| Audit stage | Items | Failed | Rows identical to P00 | Rows changed as intended |
|---|---|---|---|---|
| 1_presolve | 133 | 0 | 58 | heated wall flux [W/m2] |
| 2_final_schemes | 133 | 0 | 58 | heated wall flux [W/m2] |
| 3_final | 133 | 0 | 58 | heated wall flux [W/m2] |

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
| residual continuity | 9.079e-11 | 1.0e-04 |
| residual x-velocity | 2.957e-16 | 1.0e-04 |
| residual y-velocity | 2.957e-16 | 1.0e-04 |
| residual z-velocity | 1.573e-14 | 1.0e-04 |
| residual k | 7.402e-13 | 1.0e-04 |
| residual omega | 1.718e-13 | 1.0e-04 |
| residual energy | 1.252e-14 | 1.0e-06 |
| drift T_out_bulk over 200 it [K] | 3.645e-06 | 1.0e-01 |
| drift T_solid_max over 200 it [K] | 1.156e-05 | 1.0e-01 |
| drift T_wall_max over 200 it [K] | 0.000e+00 | 1.0e-01 |
| drift T_outer_max over 200 it [K] | 0.000e+00 | 1.0e-01 |
| rel drift dp_area over 200 it | 3.037e-10 | 1.0e-03 |
| rel drift q_interface over 200 it | 4.942e-09 | 1.0e-03 |
| rel drift mdot_out over 200 it | 1.591e-10 | 1.0e-04 |
| mass imbalance \|in-out\|/in | 4.226e-14 | 1.0e-04 |
| energy imbalance \|sum Q\|/Q_wall | 3.121e-13 | 5.0e-03 |

## 5. Property tables and solver messages (every iteration of every stage)

Checked by the journal after every iterate call (7 checks, all ok: True) and re-checked here from the raw monitor file.

| Monitor | History min [K] | History max [K] | Iteration of max | Converged [K] |
|---|---|---|---|---|
| T_fluid_max | 300.000 | 581.397 | 386 | 581.384 |
| T_fluid_min | 299.998 | 300.000 | 157 | 300.000 |
| T_wall_max | 300.000 | 583.365 | 386 | 583.352 |
| T_out_bulk | 300.000 | 376.196 | 308 | 375.793 |
| T_in_bulk | 300.000 | 300.000 | 1 | 300.000 |
| T_solid_max | 300.000 | 590.662 | 386 | 590.649 |
| T_solid_min | 300.000 | 438.460 | 310 | 437.421 |
| T_outer_max | 300.000 | 591.140 | 386 | 591.127 |
| T_outer_avg | 300.000 | 553.509 | 371 | 553.492 |
| T_inner_avg | 300.000 | 545.253 | 371 | 545.235 |

Solver messages matching limiter / reversed-flow / divergence formats: none

## 6. Heat input, balances, exports

| Check | Value |
|---|---|
| q″ set / area-average read back [W/m²] | 8800.000000 / 8800.000000 |
| Heated area (Fluent) [m²] | 7.534440500e-02 |
| Q Fluent / q″·A [W] | 663.030760 / 663.030764 |
| Q vs P00 | +1.0000e-01 (relative) |
| Mass imbalance | 4.226e-14 (target < 1e-4) |
| Energy imbalance | 3.121e-13 (target < 5e-3) |
| Volume export rows | {"cells_fluid.csv": 116640, "cells_solid.csv": 43200} |
| EnSight files | {"solid_domain_T.encas": 287, "solid_domain_T.geo": 2427848, "solid_domain_T.scl1": 260792, "solid_domain_T.vel": 779592, "solid_domain_T.xml": 882} |

## 7. Versions

| Item | Value |
|---|---|
| Fluent | Ansys Fluent 2026 R1 |
| Journal `solve_param.py` SHA-256 | `8205529CA5FE21C0524417EDCCE11F7DCC8224414D208858E32E082544BCA10B` |
| `param_cases.py` SHA-256 | `06FEE3EAEDA60968799F123695D1B5C782D5CCE91258612952B5CB885D478346` |

**Overall: CONVERGED_VALID**

