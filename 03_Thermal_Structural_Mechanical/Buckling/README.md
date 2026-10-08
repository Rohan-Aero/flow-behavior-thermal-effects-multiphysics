# Buckling (Section 8A): LC2 stability check

RE-ANALYSIS 2026. This is new work on the re-analysed duct. It contains no recovered internship results and no measurements.

## Documents

| File | Content |
|---|---|
| `BUCKLING_RESULTS.md` | **Start here.** Answers, FE linear-buckling results, interpretation, limitations |
| `BUCKLING_HAND_CALCULATION.md` | Independent hand estimate: load basis, section properties, E(T), Euler for four end conditions, Euler applicability, Johnson, local/shell screen |
| `BUCKLING_AUDIT.md` | Pre-solve gate, run history, method benchmark, DOF validation table, solver checks, independent verification |

## Scripts and data

| File | What it does |
|---|---|
| `buckling_calculations.py` | Hand estimate → `buckling_hand_results.json`. Run as `python buckling_calculations.py "<project root>"` |
| `mode_shapes.py` | Classifies eigen-modes from `Mechanical/*/Solver_Output/s8a_mode<i>.csv` |
| `plots_8A.py` | Draws `figures/F8A_01…04` and writes `fe_modes_8A.json`. Run as `python plots_8A.py "<project root>"` |
| `Workbench/Scripts/wb_buckling_8A.wbjn`, `mech_buckling_8A.py`, `s8a_buckle_snippet.inp` | The Workbench/Mechanical build and solve (save-as of the 7B project; LC2 buckling + LC2NS sensitivity) |
| `Audits/Verification_8A/verify_8A.py` | Independent re-check from the raw solver files: 17 checks, all pass |

## Folders

| Folder | Contents |
|---|---|
| `figures/` | F8A_01 mode 1 · F8A_02 mode 2 · F8A_03 critical-load summary · F8A_04 load-factor comparison (data plots) |
| `figures/Mechanical/` | Unedited Mechanical renders of modes 1–4 for LC2 and LC2NS (auto-scaled mode shapes) |
| `Mechanical/` | Solver output of the LC2 re-solve, LC2 buckling, LC2NS static and LC2NS buckling |
| `Benchmark/` | Toy-tube MAPDL benchmark of the method (constant properties, uniform ΔT; not project results) |
| `Audits/` | Gate JSON, logs, pre/post hash records of the 7B project, failed and stopped runs (kept), verification |
| `Workbench/` | `Flow_Behavior_Thermal_Effects_Buckling_8A.wbpj` (solved) |

## Key numbers

| Quantity | Value |
|---|---|
| Applied force | N = 548,936.6 N (582.44 MPa mean axial stress) |
| Slenderness | L/r = 53.67 |
| FE λ₁, LC2 supports | **1.108**: guided-column sway mode |
| Hand estimate, LC2 supports | 1.06 (Johnson) to 1.12 (Euler) |
| FE λ₁, ends also held laterally (sensitivity) | 4.300 (elastic; yield-limited in reality at about 1.6–1.75) |
| First yield of the LC2 state (7B) | about 1.73 |
