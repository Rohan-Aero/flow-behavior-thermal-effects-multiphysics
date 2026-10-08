# C00_PIPELINE_CHECK — CFD case audit (Section 9B-1)

> **RE-ANALYSIS 2026.** Automation-integrity record of this case, generated from the raw audit files.

## 1. Intended vs actual change

Intended change (param_cases.py): `{}`

Settings diff after mesh replace: **0** differences (must be 0).

Settings diff after the intended change (full settings tree, `Audit/frozen_physics_gate.json`): **0** paths

Unexpected paths: 0 · intended-but-absent: 0 · gate: **PASS**

## 2. Unchanged settings (read back from Fluent and compared with P00's own audit)

| Audit stage | Items | Failed | Rows identical to P00 | Rows changed as intended |
|---|---|---|---|---|
| 1_presolve | 133 | 0 | 59 | — |
| 2_final_schemes | 133 | 0 | 59 | — |
| 3_final | 133 | 0 | 59 | — |

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
| stage3+200 (iter 500) | no | drift T_out_bulk over 200 it [K], drift T_solid_max over 200 it [K], drift T_wall_max over 200 it [K], drift T_outer_max over 200 it [K], rel drift dp_area over 200 it, rel drift q_interface over 200 it |
| stage3+300 (iter 600) | yes | none |
| confirmation+400 (iter 700) | yes | none |

Final evaluation values:

| Criterion | Value | Target |
|---|---|---|
| residual continuity | 9.020e-11 | 1.0e-04 |
| residual x-velocity | 3.716e-16 | 1.0e-04 |
| residual y-velocity | 3.144e-16 | 1.0e-04 |
| residual z-velocity | 1.577e-14 | 1.0e-04 |
| residual k | 7.220e-13 | 1.0e-04 |
| residual omega | 2.033e-13 | 1.0e-04 |
| residual energy | 1.562e-14 | 1.0e-06 |
| drift T_out_bulk over 200 it [K] | 2.283e-06 | 1.0e-01 |
| drift T_solid_max over 200 it [K] | 7.065e-06 | 1.0e-01 |
| drift T_wall_max over 200 it [K] | 0.000e+00 | 1.0e-01 |
| drift T_outer_max over 200 it [K] | 0.000e+00 | 1.0e-01 |
| rel drift dp_area over 200 it | 6.858e-10 | 1.0e-03 |
| rel drift q_interface over 200 it | 3.527e-09 | 1.0e-03 |
| rel drift mdot_out over 200 it | 1.324e-10 | 1.0e-04 |
| mass imbalance \|in-out\|/in | 7.009e-15 | 1.0e-04 |
| energy imbalance \|sum Q\|/Q_wall | 3.078e-13 | 5.0e-03 |

## 5. Property tables and solver messages (every iteration of every stage)

Checked by the journal after every iterate call (7 checks, all ok: True) and re-checked here from the raw monitor file.

| Monitor | History min [K] | History max [K] | Iteration of max | Converged [K] |
|---|---|---|---|---|
| T_fluid_max | 300.000 | 553.419 | 393 | 553.413 |
| T_fluid_min | 299.998 | 300.000 | 157 | 300.000 |
| T_wall_max | 300.000 | 555.273 | 392 | 555.267 |
| T_out_bulk | 300.000 | 369.300 | 308 | 368.932 |
| T_in_bulk | 300.000 | 300.000 | 1 | 300.000 |
| T_solid_max | 300.000 | 562.133 | 393 | 562.127 |
| T_solid_min | 300.000 | 424.857 | 310 | 423.966 |
| T_outer_max | 300.000 | 562.583 | 392 | 562.577 |
| T_outer_avg | 300.000 | 528.471 | 380 | 528.463 |
| T_inner_avg | 300.000 | 520.748 | 380 | 520.740 |

Solver messages matching limiter / reversed-flow / divergence formats: none

## 6. Heat input, balances, exports

| Check | Value |
|---|---|
| q″ set / area-average read back [W/m²] | 8000.000000 / 8000.000000 |
| Heated area (Fluent) [m²] | 7.534440500e-02 |
| Q Fluent / q″·A [W] | 602.755240 / 602.755240 |
| Q vs P00 | +0.0000e+00 (relative) |
| Mass imbalance | 7.009e-15 (target < 1e-4) |
| Energy imbalance | 3.078e-13 (target < 5e-3) |
| Volume export rows | {"cells_fluid.csv": 116640, "cells_solid.csv": 43200} |
| EnSight files | {"solid_domain_T.encas": 287, "solid_domain_T.geo": 2427848, "solid_domain_T.scl1": 260792, "solid_domain_T.vel": 779592, "solid_domain_T.xml": 882} |

## 7. Versions

| Item | Value |
|---|---|
| Fluent | Ansys Fluent 2026 R1 |
| Journal `solve_param.py` SHA-256 | `9A4754C62249D708239D1A08C6738BCB7DDBC982DE1092B91FB6083D22B78802 (archived v1)` |
| `param_cases.py` SHA-256 | `A8B865F57E6186CE33AD7312FA2E78FE00C7C2384D8049DB0365E5B7E889B7BD (archived v1)` |

C00 was solved with journal version 1 (archived as `Journals/Archive/solve_param_v1_used_for_C00.py` and `param_cases_v1_used_for_C00.py`; the version-1 journal did not yet record its own hash, so the archived file hashes are given above). Version 2, used for every parametric case, differs only in lines that C00 does not execute (the V-case initial-field rule and the hash record) and one audit-row label; the diff is `Journals/Archive/diff_v1_to_v2_*.txt`.

**Overall: CONVERGED_VALID**

