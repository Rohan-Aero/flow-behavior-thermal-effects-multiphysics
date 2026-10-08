# Coarse Mesh Record — Section 6A (mesh-independence study)

**RE-ANALYSIS 2026 · Label: MESH-INDEPENDENCE / COARSE**
This folder holds the mesh-side record of the coarse-mesh CFD run. The run itself (case, data,
monitors, exports, journals, figures, audit) is in `06_Fluent_CFD/Mesh_Independence/Coarse/`;
see `COARSE_CFD_RESULTS.md` and `COARSE_CFD_AUDIT.md` there.

## Mesh used

| Item | Value |
|---|---|
| File | `05_Meshing/Mesh_Coarse/coarse.msh` (Section 4, `Scripts/make_mesh.py`), **not modified** |
| Size / SHA-256 | 7,965,362 bytes · `5C0DE888DCAFB7FAB94E3ABD3CF24139EAE8527750E7137598971646D26D4A98` (identical before and after Section 6A) |
| Version | the corrected post-face-winding mesh (F-016): it reads with strictly positive volumes |
| Copy used in the run | `06_Fluent_CFD/Mesh_Independence/Coarse/Case/coarse_mesh_used_for_study.msh`, same SHA-256 |
| Topology | butterfly O-grid, 100 % hexahedra; NC / Nθ / NR / NRS / NZ = 8 / 32 / 18 / 7 / 60 |

## As read by ANSYS Fluent 2026 R1 (via `mesh.replace` onto the medium case settings)

| Check | Result |
|---|---|
| Cells | **51,840** = 38,400 fluid + 13,440 solid hexahedra (Fluent `size_info`) |
| Faces | 159,264 total: interior-fluid 113,600 · interior-solid 38,176 · inlet 640 · outlet 640 · interface 1,920 (+ shadow, created by Fluent) · heated outer wall 1,920 · solid ends 224 + 224 |
| Nodes | 53,741 on read; 55,629 counted across 4 partitions |
| **Negative-volume cells** | **none**: minimum cell volume 2.049465 × 10⁻¹⁰ m³ |
| Total volume | 7.491468 × 10⁻⁴ m³ (0.993587 × the exact cylinder, the 32-gon ratio; same as Section 4) |
| Fluid zone | `fluid_domain` (id 2) |
| Solid zone | `solid_domain` (id 3) |
| Inlet | `fluid_inlet` (id 6, velocity-inlet) |
| Outlet | `fluid_outlet` (id 7, pressure-outlet) |
| Wall / interface | `fluid_solid_interface` (id 8) + `fluid_solid_interface-shadow` (id 12), coupled |
| Heated outer wall | `heated_outer_wall` (id 9) |
| Other | `solid_inlet_end` (10), `solid_outlet_end` (11), `interior-fluid` (4), `interior-solid` (5) |

All zone names and IDs are identical to the medium mesh (`coarse_mesh_zones.json`).

Section 4 quality for this level (unchanged, `Mesh_Quality/MESH_QUALITY_TABLE.md`): minimum
orthogonal quality 0.448186, maximum aspect ratio 974.5, maximum equiangle skewness 0.6564.

## Geometry the coarse mesh represents

| | Coarse (32-gon) | Medium (48-gon) |
|---|---|---|
| Planar area ratio (N/2π)·sin(2π/N) | 0.993587 | 0.997147 |
| Lateral area ratio sin(π/N)/(π/N) | 0.998394 | 0.999286 |
| Polygon hydraulic diameter | 19.904 mm | 19.957 mm |

These ratios are reproduced exactly by the CFD mass flow (−0.357 % vs medium) and heat input
(−0.089 % vs medium). The mesh study therefore contains a **geometric** discretisation component
alongside the solution-discretisation error.

## Near-wall resolution on the converged coarse solution

| Quantity | Value |
|---|---|
| First-cell-centre wall distance (slab at z = 295 mm) | 5.23–6.02 µm → first layer ≈ 10.5 µm (O-grid diagonals) to ≈ 12.0 µm (near the axes); design 12.2 µm on the axes (F-028 pattern, same as the medium mesh) |
| y⁺ min / area mean / max | **0.207 / 0.238 / 0.522**; 100 % of the wall ≤ 1 |
| Verdict for SST, `correlation` ω wall treatment | wall-resolved; appropriate |

Figures copied here: `figC06_yplus_vs_medium.png`, `figC09_coarse_midspan_section.png`.

**No mesh-independence conclusion is drawn here.** The fine mesh has not been solved yet.
