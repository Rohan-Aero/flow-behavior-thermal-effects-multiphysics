# Section 9B-1: CFD meshes for the thickness cases (T01_THIN, T03_THICK)

> **RE-ANALYSIS 2026.** The two meshes are newly generated. The P00 medium mesh (`06_Fluent_CFD/Case/medium_mesh_used_for_baseline.msh`) was used unchanged for C00, V01, V03, Q01 and Q03, and it was never rewritten.

## 1. Strategy (rule M-1 of `Planning/MESH_YPLUS_MATERIAL_POLICY.md`)

- **Generator.** The meshes come from the unchanged Section 4 generator `05_Meshing/Scripts/make_mesh.py` (SHA-256 `F2217FE0…`). It is imported, never edited, by `param_mesh.py`.
- **Interpreter.** They were built with the ANSYS-bundled CPython 3.10.19 and numpy 1.23.5, the interpreter that made the Section 4 meshes.
- **What changes.** Only the outer radius (the module globals `RO`, `DO`, set on a fresh import of the module for each geometry) and the number of solid layers.
- **Fluid mesh: identical to P00.**
  - NC 12 (48 facets), NR 24, NZ 90.
  - First cell 12.2 µm, growth 1.2091.
  - Core radius 4.5 mm.
- **Solid layers.** First layer 0.5 mm, growth ≤ 1.147 (P00: 10 layers, g 1.1469), and the smallest layer count that meets the rule is used.

| | T01_THIN | P00 | T03_THICK |
|---|---|---|---|
| Wall thickness | 8 mm | 10 mm | 12 mm |
| Solid layers (growth) | **9 (1.1388)**; 8 would need 1.1917 | 10 (1.1469) | **12 (1.1191)**; 11 would need 1.1474 |
| Last solid layer | 1.414 mm | 1.717 mm | 1.724 mm |

## 2. Proof that the wrapper changes nothing else

Step 0 of `param_mesh.py` regenerated the P00 medium mesh through the wrapper (Do 40 mm, 10 layers). The result is **byte-identical** to the P00 mesh: SHA-256 `2C6FCFB31108654D…` for both, 26,292,846 bytes. The regenerated copy was deleted after the hash match, and only the hash record is kept (`mesh_checks_9B1.json → wrapper_validation`).

## 3. Mesh checks (generator side, `mesh_checks_9B1.json`)

| Check | T01_THIN | T03_THICK |
|---|---|---|
| Cells, total / fluid / solid | **155,520** / 116,640 / 38,880 | **168,480** / 116,640 / 51,840 |
| Faces: interface / heated wall / each solid end | 4,320 / 4,320 / 432 | 4,320 / 4,320 / 576 |
| Negative or zero-volume cells | 0 | 0 |
| Cells without exactly 6 faces; unused nodes | 0; none | 0; none |
| Fluid volume vs exact 48-gon | rel 2 × 10⁻¹⁶ | rel 2 × 10⁻¹⁶ |
| Solid volume vs exact 48-gon | rel 2 × 10⁻¹⁶ | rel 0 |
| Heated-wall area vs exact 48-facet area | 0.067809964 m², rel 0 | 0.082878845 m², rel 2 × 10⁻¹⁶ |
| Fluid node coordinates vs P00 (every axial level) | **bitwise identical** | **bitwise identical** |
| Fluid cell connectivity vs P00 | identical | identical |
| Interface conformity | 4,320 of 4,320 interface faces pair one fluid cell with one solid cell; all interface nodes on r = 10 mm | same |
| Heated-wall nodes on r = Do/2 | yes | yes |
| Max aspect ratio (estimate): fluid first cell / solid first / solid last | 546 / 13.3 / 4.7 | 546 / 13.3 / 3.9 |
| File, SHA-256 | `Mesh_T01_THIN/T01_THIN.msh`, `D2CB86B952E5BE6D…`, 25.6 MB | `Mesh_T03_THICK/T03_THICK.msh`, `9B6CC26C153BD447…`, 27.8 MB |

**Conformal by construction.** The fluid wall nodes and the solid inner nodes are the same nodes (Section 4 design).

## 4. Fluent's own mesh check (pre-solve, before any iteration)

Read back by `solve_param.py` after `mesh.replace` and recorded in each case's `Audit/case_mesh_zones.json` and `setup_audit_1_presolve.json`, before the first iteration:

| Fluent check | T01_THIN | P00 mesh (C00, V, Q) | T03_THICK |
|---|---|---|---|
| Cells printed by Fluent | 155,520 (= expected) | 159,840 | 168,480 (= expected) |
| Minimum cell volume [m³] | 9.051023 × 10⁻¹¹ (> 0) | 9.051023 × 10⁻¹¹ | 9.051023 × 10⁻¹¹ (> 0) |
| Minimum orthogonal quality | 0.445829 (> 0.1) | 0.445829 | 0.445829 (> 0.1) |
| Mesh-check warnings | none | none | none |
| Zone names and ids after replace | identical to P00 (2, 3, 4–12) | — | identical to P00 |
| Settings diff after replace | 0 | 0 | 0 |

**Why the minimum volume and orthogonal quality are identical in all three.** Both extremes lie in the fluid mesh, which is bitwise the same:

- the smallest cell is a first-layer wall cell;
- the lowest orthogonal quality is at a corner of the O-grid core.

The thickness meshes change only the solid layers, and those are well-shaped: aspect ratio ≤ 13.3, growth ≤ 1.139.

## 5. Near-wall resolution and y⁺ suitability

- The fluid near-wall mesh is bitwise identical to P00: first cell 12.2 µm, and the same 24 inflation layers.
- The inlet air state is unchanged (23.5 m/s, 300 K), so the pre-run y⁺ estimate equals P00's (0.585 maximum, at the inlet). The reuse threshold is 0.8.
- Thickness changes only the wall heat-flux distribution. Downstream heating raises ν at the wall and lowers y⁺ there.
- The measured y⁺ is in `CFD_Results/PARAMETRIC_CFD_TABLE.md`.

## 6. Licence and cost

- The largest mesh (T03, 168,480 cells) is 5.4 % above P00, far below the 500,580-cell mesh solved in Section 6B.
- Generation took 5 s (T01) and 13 s (T03).

**Not done here.** M03 (CFD solid-layer adequacy at t = 12 mm, 12 → 18 layers) is planned in 9A. It is **not** in the approved 9B-1 case list, so it was not run. It remains pending.
