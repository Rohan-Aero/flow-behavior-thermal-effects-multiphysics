# 08_Structural_Analysis/Mesh_Study: Section 8B structural mesh sensitivity

> **RE-ANALYSIS 2026.** These are new ANSYS Mechanical 2026 R1 (Student) solutions.
>
> - They are not recovered internship results, and there are no experimental data.
> - The official 7B/8A results live in `../LC1_Free_Expansion`, `../LC2_Restrained`, `../Pressure_Check` and `../Buckling`. They were not changed.

## Read first

| File | Content |
|---|---|
| `STRUCTURAL_MESH_STUDY.csv` | one row per mesh: nodes, elements, LC1/LC2 stress and deformation, λ₁, critical buckling load, status (+ mean axial stress, free growth, pressure effect) |
| `STRUCTURAL_MESH_COMPARISON.md` | static LC1/LC2/LC2P mesh study: design under the licence limit, mesh quality, mapping, results, convergence classes, inlet region, error types, recommendation |
| `BUCKLING_MESH_COMPARISON.md` | λ₁…λ₆, critical loads, mode consistency, buckling convergence, buckling uncertainty ranking |
| `STRUCTURAL_MESH_AUDIT.md` | audit questions and answers, run history, gates, integrity, remaining uncertainty |

## Mesh variants (quadratic SOLID186 swept hex; circumferential × through-wall × axial, axial bias)

| Tag | Divisions | Nodes | Role |
|---|---|---|---|
| XC | 21 × 3 × 76, bias 4 | 24,171 | family level 1 (extra coarse) |
| C | 27 × 4 × 98, bias 4 | 50,652 | family level 2 (COARSE) |
| **B** | 36 × 5 × 130, bias 4 | 108,252 | family level 3 = **BASELINE, selected** (re-meshed; bit-identical to 7B) |
| FR | 36 × 6 × 130, bias 4 | 127,080 | FINE, through-wall, at the licence limit |
| FA | 36 × 5 × 152, bias 4 | 126,468 | FINE, axial, at the licence limit |
| FC | 42 × 5 × 130, bias 4 | 126,294 | FINE, circumferential, at the licence limit |
| IL | 36 × 5 × 130, bias 8 | 108,252 | local inlet-bias check (static only; separate sensitivity) |

## Folders

| Folder | Content |
|---|---|
| `Scripts/` | `wb_meshstudy_8B_template.wbjn`; run journals `_A` (XC, C, IL), `_B` (B, FR, FA), `_C` (FC); `mech_meshstudy_8B.py` (re-mesh, gate, solve, extract, images); `hash_7B_post8B.ps1` |
| `Variants/<tag>/Audits/` | pre-solve gate JSON, summary JSON, Mechanical log, imported temperature exports, `Presolve_Inputs/` (the exact solver input decks) |
| `Variants/<tag>/Solver_Output/<case>/` | LC1, LC2, LC2P, BUCKLING: solve.out, file0.err, s7b_nodal / s7b_react / s7b_totals / s7b_prrsol tables, structural-error export, s8a load factors and mode shapes |
| `Projects/` | solved Workbench save-as copies `MS8B_<tag>.wbpj` (traceability only) |
| `Post/` | `post_8B.py`, `mapping_check_8B.py`, `mesh_geometry_8B.py`, `ref1d_lc1_8B.py`, `ref1d_split_8B.py`, `tables_8B.py`, `plots_8B.py`, `mode_shapes.py` (8A, unchanged); `out/` holds every computed JSON, table and log |
| `figures/` | F8B_01…F8B_09 (data plots from solver tables) · `Mechanical/` (40 unedited Mechanical renders) |
| `Audits/` | pre/post hashes of the 7B project and their comparison (IDENTICAL, 58/58); WB driver logs; `Verification_8B/` (independent verification, 120/120 PASS) |

## Reproduce the post-processing

```
python Post/post_8B.py <project_root> Post/out
python Post/mapping_check_8B.py Post/out/mapping_check_<tag>.json <tag>=Variants/<tag>/Audits/Presolve_Inputs/<tag>_LC2_presolve_ds.dat
python Post/mesh_geometry_8B.py Post/out/mesh_geometry.json <tag>=<ds.dat> ...
python Post/ref1d_lc1_8B.py Post/out/ref1d_lc1_8B.json
python Post/ref1d_split_8B.py <project_root> Post/out/ref1d_split_8B.json
python Post/tables_8B.py Post/out
python Post/plots_8B.py Post/out figures figures/Mechanical
python Audits/Verification_8B/verify_8B.py <project_root> verify_8B_result.json Post/out/post_8B_results.json
```

**Path note.** `mapping_check_8B.py` and `ref1d_lc1_8B.py` import the Section 7A validation modules. Their location is set at the top of each script (cloud workspace path). On the device, point them to `07_Thermal_Analysis/Validation` and `07_Thermal_Analysis/Mapping/MeshBased`.
