# Coarse-Mesh CFD Results — Section 6A (mesh-independence study, point 1 of 2 additional)

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems
**Date:** 2026-09-23 · **Software:** ANSYS Fluent 2026 R1 (v261), `3ddp`, batch, 4 cores (Student)
**RE-ANALYSIS 2026 — newly generated results, not recovered originals. No measured data exists or is used.**
**Label: MESH-INDEPENDENCE / COARSE**

> **Status.** The coarse case (51,840 cells) is converged: it meets the NR-03 residual targets
> **and** the physical-plateau criteria, conserves mass and energy to round-off, and still holds
> after 100 confirmation iterations. It was solved with **exactly the physics of the official
> medium baseline**. Only the mesh changed. **This file does not draw a mesh-independence
> conclusion.** The fine mesh has not been solved, so nothing here is extrapolated and no GCI is
> computed. The differences from the medium mesh are reported raw.

Companions: `COARSE_CFD_AUDIT.md` (how the run was set up, controlled and checked) ·
`Coarse_vs_Medium.csv` · `coarse_cfd_results.json` · mesh record
`05_Meshing/Mesh_Independence/Coarse/COARSE_MESH_RECORD.md`.

---

## 1. What was solved

| Item | Coarse (this run) | Medium (Section 5B baseline, unchanged) |
|---|---|---|
| Mesh file | `05_Meshing/Mesh_Coarse/coarse.msh` (post-face-winding fix; SHA-256 `5C0DE888…4A98`) | `medium.msh` |
| **Cells** | **51,840** (38,400 fluid + 13,440 solid, all hexahedra) | 159,840 (116,640 + 43,200) |
| Circumferential × axial | **32-sided polygon** × **60 slabs** (10.0 mm) | 48 × 90 (6.67 mm) |
| Fluid / solid radial layers | 18 / 7 | 24 / 10 |
| First fluid cell height | 12.2 µm (design, on the O-grid axes) | 12.2 µm |
| Minimum cell volume | 2.049 × 10⁻¹⁰ m³ (**no negative volumes**) | positive |
| Geometry, BCs, materials, models, numerics | **identical** | — |

**How "identical" was established rather than assumed.** Fluent read the medium baseline case
for its settings only (its data was **not** read). Fluent's own `mesh.replace` then swapped in
`coarse.msh`, keeping every setting. A full dump of the settings tree (`setup` + `solution`)
taken before and after the replace differs in **0** entries. On top of that, all 59 items of the
Section 5B setup audit were read back and compared item by item with the medium run's own audit
files at all three stages. Every one matched (§2 of the audit).

## 2. Solver settings (read back from Fluent)

These are the same settings as Section 5B:

- **Solver:** pressure-based, steady, Coupled pressure–velocity, pseudo-time stepping (`global-time-step`, automatic, conservative, factor 1.0).
- **Turbulence:** k-ω SST, `correlation` ω wall treatment, low-Re correction off.
- **Energy:** on; viscous dissipation, pressure work and kinetic-energy terms off.
- **Gravity / radiation:** off / off.
- **Air:** incompressible ideal gas (M = 28.966). Inconel 718 ρ = 8190.0 kg/m³ (option `value`). All piecewise-linear property curves are identical point for point.
- **Boundary conditions:** 23.5 m/s / 300 K / I = 4.411 % inlet; 0 Pa outlet; 8000 W/m² on the heated wall; adiabatic ends; coupled interface; operating pressure 101 325 Pa.
- **Discretisation:** least-squares gradients. At the end the schemes are pressure second-order and momentum, k, ω and energy second-order upwind.
- **Relaxation and limits:** Fluent defaults, the same as the medium run.

## 3. Convergence

| Stage | Iterations | What |
|---|---|---|
| 1 | 1–150 | flow + k-ω only, energy off, first order (the Section 5B startup) |
| 2 | 151–300 | energy on, first order |
| 3 | 301–600 | one switch to second order; evaluated every 100 iterations |
| confirmation | 601–700 | 100 more iterations; every criterion must still hold |

Convergence was evaluated four times:
- **Iteration 400:** not evaluable, because the 200-iteration window must lie wholly in second order.
- **Iteration 500:** refused, because the window still contained the scheme-switch transient (T_out drift 0.62 K, Δp 0.46 %).
- **Iteration 600:** CONVERGED.
- **Iteration 700:** CONFIRMED.

**Total: 700 iterations**, 9 min 02 s wall clock including audits and exports.

| Criterion (same as 5B) | Target | Coarse, final |
|---|---|---|
| Continuity | < 1e-4 | **1.2 × 10⁻¹⁰** |
| x / y / z momentum | < 1e-4 | 5.9 × 10⁻¹⁶ / 5.1 × 10⁻¹⁶ / 4.2 × 10⁻¹⁴ |
| k / ω | < 1e-4 | 1.9 × 10⁻¹² / 4.1 × 10⁻¹³ |
| Energy | < 1e-6 | **5.0 × 10⁻¹⁴** |
| T_out drift, last 200 it | < 0.1 K | **2.8 × 10⁻⁶ K** |
| T_solid_max / T_wall_max / T_outer_max drift | < 0.1 K | 1.0 × 10⁻⁵ / 6.1 × 10⁻⁵ / 0 K |
| Δp / Q_interface / ṁ_out relative drift | < 0.1 % / 0.1 % / 0.01 % | 7.5 × 10⁻⁸ % / 4.2 × 10⁻⁷ % / 1.7 × 10⁻⁸ % |
| Mass imbalance | < 0.01 % | **1.2 × 10⁻¹³ %** |
| Energy imbalance | < 0.5 % | **2.0 × 10⁻¹¹ %** |

## 4. Results — MESH-INDEPENDENCE / COARSE

All definitions are identical to Section 5B.

### Flow

| Quantity | Coarse |
|---|---|
| Inlet / outlet mass flow (Fluent flux report) | **8.631231 / 8.631231 g/s** |
| **Δp — area-weighted static gauge pressure, inlet face minus outlet face** | **437.09 Pa** (mass-weighted: identical) |
| — wall shear / 1-D acceleration / profile development | 241.02 / 149.71 / 46.42 Pa (momentum balance closes to −0.010 %) |
| Re inlet / outlet (D = 20 mm, G = ṁ/A from Fluent) | **29 958 / 25 535** |
| Outlet area-mean velocity; maximum velocity | 28.90 m/s; 34.99 m/s (outlet centreline) |
| Reverse-flow cells / outlet faces | 0 / 0 |

No entrance or exit losses are included. The Δp is directly comparable with the medium's 438.13 Pa.

### Thermal

| Quantity | Coarse |
|---|---|
| **Outlet temperature, mass-weighted** (Fluent surface integral) | **369.115 K** (369.1156 K from the exported outlet faces, as used in the CSV) |
| Outlet mixing-cup (enthalpy) | 369.178 K |
| **Heat-transfer rate (heated wall)** | **602.217 W** |
| Fluid enthalpy gain (outlet − inlet flux, Fluent report) | 618.269 − 16.051 = 602.217 W |
| **Maximum solid temperature** | **565.40 K** (outer-wall facet maximum, outlet end); hottest cell centre 564.65 K (r = 18.5 mm, z = 595 mm) |
| Peak inner-wall temperature | 558.12 K |
| **Through-wall ΔT at mid-span, z = 300 mm** | **7.554 K** |
| Through-wall ΔT at z = 570 mm (the 5B reported station) | 7.334 K |
| Inner / outer / bulk temperature at mid-span | 534.24 / 541.80 / 334.81 K |
| h at mid-span; fully developed Nu; fully developed Darcy f (x/D 18.25–28.75) | 79.69 W/m²K; **53.38**; **0.02134** |

The through-wall ΔT is taken at **matched physical locations**. Both meshes are linearly
interpolated between slab centres at z = 300 mm, and again at 570 mm. The first-slab values
(13.54 K at z = 5 mm on the coarse mesh, 15.12 K at z = 3.3 mm on the medium) are **not** a
matched location and are not compared.

### y⁺ on the conjugate wall (recomputed from the converged coarse solution)

| Minimum | Area mean | Median | 95th pct | Maximum | ≤ 1 | ≤ 0.5 |
|---|---|---|---|---|---|---|
| **0.207** | **0.238** (Fluent: 0.23811778) | 0.233 | 0.286 | **0.522** (first slab, z = 5 mm) | **100 %** | 99.2 % |

The first-cell-centre wall distance is 5.23–6.02 µm, the same O-grid pattern as the medium mesh
(F-028). **The coarse mesh remains appropriate for the SST `correlation` wall treatment.** Every
face sits inside the viscous sublayer, so wall shear and heat flux are resolved, not modelled by a
wall function. The coarse mesh reuses the medium's 12.2 µm first layer; the y⁺ value above was
nonetheless recomputed from this solution, not assumed.

### Conservation (same definitions as Section 5B)

| | Value |
|---|---|
| Mass: in − out | +1.0 × 10⁻¹⁷ kg/s → **1.2 × 10⁻¹³ %** |
| Energy: wall heat input vs fluid enthalpy gain; net over all boundaries | 602.2173 vs 602.2173 W; net −1.27 × 10⁻¹⁰ W (Fluent flux report) / −1.23 × 10⁻¹⁰ W (per-iteration monitor, the 5B definition used in the criterion) → **2.0 × 10⁻¹¹ %** (2.1 × 10⁻¹¹ % from the flux report) |

## 5. Physical sanity check

| Check | Result |
|---|---|
| Pressure decreases downstream | ✅ slab-average pressure falls monotonically over all 60 slabs |
| Temperature rises through the heated region | ✅ bulk temperature rises monotonically, 300 → 369.1 K |
| Heat flows from wall into fluid | ✅ bore heat flux > 0 in every slab (min 14 584 W/m²); T_inner > T_bulk and T_outer > T_inner everywhere |
| NaN / Inf | ✅ 0 in all exports |
| Non-physical values | ✅ fluid 300.0–556.3 K, solid 425.4–564.7 K, both inside their property tables at every iteration; 0 limiter messages |
| Unexpected reverse flow | ✅ 0 cells with w < 0; outlet w ≥ 0.39 m/s |
| Mass / energy conservation | ✅ round-off (above) |
| Startup | ✅ stage 2 rose monotonically (0 decreases); history maximum 564.667 K at it. 385 is 0.015 K above the final value |

Nothing abnormal was found, so nothing needed diagnosing before continuing.

## 6. Comparison against the medium result (raw, two points — no verdict)

| Quantity | Coarse | Medium | Coarse − medium | % of medium | From polygon faceting alone |
|---|---|---|---|---|---|
| Inlet mass flow | 8.6312 g/s | 8.6622 g/s | −0.0309 g/s | **−0.357 %** | **−0.357 %** |
| Heat-transfer rate | 602.217 W | 602.755 W | −0.538 W | **−0.089 %** | **−0.089 %** |
| Re inlet | 29 958 | 29 958 | 0 | 0.000 % | 0 (G unchanged) |
| **Pressure drop** | **437.09 Pa** | **438.13 Pa** | −1.03 Pa | **−0.24 %** | — |
| — wall shear term | 241.02 | 242.87 | −1.85 Pa | −0.76 % | — |
| **Outlet T, mass-weighted** | **369.115 K** | **368.932 K** | **+0.183 K** | +0.050 % | +0.185 K (energy balance on each mesh's own Q and ṁ) |
| **Max solid temperature** | **565.40 K** | **562.58 K** | **+2.83 K** | **+0.50 %** | — |
| Peak inner-wall temperature | 558.12 K | 555.27 K | +2.86 K | +0.51 % | — |
| **Through-wall ΔT, mid-span** | **7.554 K** | **7.581 K** | −0.027 K | **−0.35 %** | — |
| Through-wall ΔT, z = 570 mm | 7.334 K | 7.361 K | −0.026 K | −0.35 % | — |
| h, mid-span | 79.69 | 80.69 W/m²K | −1.00 | −1.24 % | — |
| Fully developed Nu | 53.38 | 54.17 | −0.79 | **−1.46 %** | — |
| Fully developed f | 0.02134 | 0.02163 | −0.00029 | −1.33 % | — |
| y⁺ min / mean / max | 0.207 / 0.238 / 0.522 | 0.208 / 0.241 / 0.585 | — | −0.6 / −1.2 / −10.8 % | — |
| Mass / energy imbalance | 1.2e-13 / 2.0e-11 % | 7.0e-13 / 3.1e-11 % | — | — | — |

What the differences are made of, from the data rather than argued:

1. **Mass flow and heat rate differ by exactly the geometry.** The coarse section is a 32-gon
   and the medium a 48-gon, both inscribed in the 20 and 40 mm circles. The planar-area ratio
   predicts −0.3570 % in ṁ and the lateral-area ratio −0.0892 % in Q. The solver returns
   −0.3570 % and −0.0892 %. This is **geometric discretisation** (faceting), not solution error.
2. **The +0.18 K in outlet temperature is entirely that geometry.** Q/ṁ is 0.27 % higher on the
   32-gon. An energy balance on each mesh's own Q and ṁ predicts +0.185 K; the CFD gives +0.183 K.
3. **The +2.83 K in maximum solid temperature is almost all in the air film**, split at the
   outlet end the same way as Section 5B:
   - +2.59 K comes from h being 1.37 % lower on the coarse mesh (82.81 vs 83.95 W/m²K in the last slab).
   - +0.18 K comes from the bulk (faceting, item 2).
   - +0.08 K comes from the bore flux.
   - −0.03 K comes from the metal.

   The lower h is the coarse mesh's own discretisation effect: fully developed Nu is 1.46 % lower. The coarse mesh has fewer radial layers across the near-wall region (fluid growth rate 1.318 vs 1.209), fewer circumferential cells and 50 % longer axial cells. The smaller polygon hydraulic diameter would push h the other way, by about +0.05 %, which is negligible. These two meshes alone do not show which refinement direction dominates.
4. **The metal conducts the same way on both meshes.** The through-wall ΔT differs by −0.35 % at both matched stations.
5. **y⁺ maximum −10.8 % is a sampling location, not a physics change.** Both maxima sit in the
   first slab, but the coarse first-slab centre is at 5.0 mm against 3.3 mm, further from the
   inlet leading edge where shear peaks. Mean y⁺ differs by −1.2 %.

**Not concluded here:** whether any of these differences is small enough, which mesh is
adequate, or the extrapolated (Richardson / GCI) values. NR-02 is defined over three levels. It
is assessed only once the fine mesh is solved (Section 6B or later).

## 7. Figures (`Figures/`, all from exported Fluent data; matplotlib renders, not GUI screenshots)

| File | Shows |
|---|---|
| `figC01_coarse_convergence.png` | residuals, T_out / T_solid_max, Δp, heat rates; stages marked |
| `figC02_axial_temperatures_vs_medium.png` | bulk, inner- and outer-wall temperature vs z, coarse vs medium, and their difference |
| `figC03_through_wall_dT_vs_medium.png` | through-wall ΔT vs z, with the matched stations marked |
| `figC04_pressure_vs_medium.png` | slab-average static pressure vs z |
| `figC05_heat_flux_h_vs_medium.png` | bore heat flux and h vs z |
| `figC06_yplus_vs_medium.png` | y⁺ along the duct and around the circumference near mid-span |
| `figC07_nu_f_vs_medium.png` | local Nu and f vs x/D, fully developed window shaded |
| `figC08_coarse_fields.png` | coarse air and Inconel temperature, axial velocity (meridional) |
| `figC09_coarse_midspan_section.png` | coarse mid-span cross-section: 32-gon, cell centres coloured by T |
| `figC10_differences_vs_medium.png` | raw % differences with the faceting-only expectation marked |

## 8. Files

| Folder (under `06_Fluent_CFD/Mesh_Independence/Coarse/`) | Content |
|---|---|
| `Case/` | `coarse_final.cas.h5`, `coarse_intermediate_end_stage2_firstorder.cas.h5/.dat.h5`, `coarse_mesh_used_for_study.msh` (byte-identical copy, same SHA-256) |
| `Data/` | `coarse_final.dat.h5` |
| `Monitors/` | `coarse_monitors.out` (29 report definitions, every iteration), `coarse_monitors.csv`, `residual_history.csv` |
| `Exports/` | `cells_fluid.csv` (38,400 rows), `cells_solid.csv` (13,440), wall and boundary face exports |
| `Profiles/` | `axial_profiles_cfd.csv` (60 slabs), `yplus_distribution.csv` |
| `Audit/` | three setup audits (130 items each), settings-state dumps and diff, convergence evaluations, Fluent flux / surface-integral reports, medium-baseline hash records before and after |
| `Journals/` | `solve_coarse.py`, `postprocess_coarse.py`, `probe_replace.py`, `s5_common.py` (copy), `run_coarse.ps1`, `launch_coarse.ps1` |
| `Logs/` | probe, audit-only and production run logs, stdout and transcripts; post-processing log |
| root | `COARSE_CFD_RESULTS.md`, `COARSE_CFD_AUDIT.md`, `Coarse_vs_Medium.csv`, `coarse_cfd_results.json` |

## 9. Concerns

- **Faceting is part of what the mesh study measures.** ṁ and Q change with the polygon, and so
  does T_out. Any later extrapolation must either treat Q and ṁ as geometric or compare
  area-normalised quantities (heat flux, G). Otherwise the geometry error gets mixed into the
  solution-error estimate.
- **The outlet boundary cell.** At the outflow boundary Fluent's outlet face temperature equals
  the adjacent cell's, so the last slab's bulk value is the outlet value on both meshes. That slab
  sits at a different z on each mesh (595 vs 596.7 mm). Slab-by-slab bulk differences are
  therefore not like-for-like in the last slab (Figure C2b). The reported outlet temperature is
  unaffected.
- **The fully developed window is sampled on different slab centres** (x/D 18.25–28.75 coarse,
  18.17–28.83 medium). Both window means are consistent definitions, but they are not
  bit-identical windows.
- **F-029 remains open.** The coarse f (0.02134) is 1.3 % below the medium's, which moves it
  further below the Section 2 value. Whether refinement moves it back up is for the fine mesh to show.
