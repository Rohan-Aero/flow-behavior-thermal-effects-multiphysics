# Workbench: Section 7B additions (RE-ANALYSIS 2026)

**The solved project** is `Flow_Behavior_Thermal_Effects_Structural_7B.wbpj` (+ `_7B_files`).

- It is a *save-as* copy of the 7A project, with one added system, "LC2P Restrained Thermal + Pressure". That system shares Engineering Data, Geometry and Model with LC1, and takes the same External Data temperature link.
- LC1, LC2 and LC2P are solved, and every cell is Up to Date.
- The 7A project `Flow_Behavior_Thermal_Effects_Structural.wbpj` is kept unsolved and content-identical: see the SHA records in `../Audits`.

**Scripts** (`Scripts/`):

| Script | What it does |
|---|---|
| `wb_solve_7B.wbjn` | Workbench journal: save-as, add LC2P, run `mech_solve_7B.py`, save |
| `mech_solve_7B.py` | runs inside Mechanical: 61-check pre-solve gate, LC2P set-up, sparse direct solver, result objects and reaction probes, APDL post snippet, solve LC1 → LC2 → LC2P, exports, images |
| `s7b_post_snippet.inp` | APDL post-processing snippet: reactions and the full-precision nodal table |
| `wb_zoom_images_7B.wbjn` + `mech_zoom_images_7B.py` | read-only image export from the solved project; exits without saving |
| `launch_detached.ps1` | detached launcher used for the MAPDL snippet test |

**Launch command** (from PowerShell):

`Scripts/launch_wb.ps1 -Journal <journal> -Tag <tag> -WorkDir ..\Audits`
