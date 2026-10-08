# Fine-Mesh CFD Results — Section 6B (mesh-independence study, third point)

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems
**Date:** 2026-09-24 · **Software:** ANSYS Fluent 2026 R1 (v261), `3ddp`, batch, 4 cores (Student)
**RE-ANALYSIS 2026 — newly generated results, not recovered originals. No measured data exists or is used.**
**Label: MESH-INDEPENDENCE / FINE**

> **Status.** The fine case (500,580 cells) is converged. It meets the NR-03 residual targets
> **and** the physical-plateau criteria, conserves mass and energy to round-off, and still holds
> after 100 confirmation iterations. It was solved with **exactly the physics of the official
> medium baseline**; only the mesh changed. The three-mesh assessment (geometry correction,
> Richardson extrapolation, GCI, mesh decision) is in `09_Mesh_Independence/`; this file gives the
> fine solution itself and its raw comparison with the medium mesh.

Companions: `FINE_CFD_AUDIT.md` (set-up, identity with the medium case, convergence control, checks)
· `Fine_vs_Medium.csv` · `fine_cfd_results.json` · `Audit/setup_comparison_vs_medium.csv`.

---

## 1. What was solved

| Item | Fine (this run) | Medium (Section 5B baseline, unchanged) |
|---|---|---|
| Mesh file | `05_Meshing/Mesh_Fine/fine.msh` (post-face-winding fix, F-016; 84,643,549 bytes, SHA-256 `436EF76E…F37DB`, unchanged) | `medium.msh` |
| **Cells** | **500,580** (354,780 fluid + 145,800 solid, all hexahedra) | 159,840 (116,640 + 43,200) |
| Circumferential × axial | **72-sided polygon** × **135 slabs** (4.44 mm) | 48 × 90 (6.67 mm) |
| O-grid core / fluid radial / solid radial layers | 18 × 18 / 32 / 15 | 12 × 12 / 24 / 10 |
| First fluid cell height | 12.2 µm (design, on the O-grid axes), **the same on all three meshes** | 12.2 µm |
| Nodes / faces | 509,320 on read (518,968 across 4 partitions) / 1,520,028 (Fluent `size_info`, incl. the 9,720-face interface shadow) | — |
| Minimum cell volume | 4.009 × 10⁻¹¹ m³ (**no negative volumes**) | positive |
| Minimum orthogonal quality / maximum aspect ratio (Fluent) | 0.314386 / 437.9 (identical to the Section 4 table) | 0.445829 / 654.4 |
| Mesh-check warnings | **none** | none |
| Geometry, BCs, materials, models, numerics | **identical** (0-entry settings diff; 132/132 audit items at three stages) | — |
| Licence | the Student licence accepted the 500,580-cell mesh and ran on 4 cores without restriction | — |

## 2. Solver settings (read back from Fluent, identical to Section 5B)

- **Solver:** pressure-based, steady, Coupled, pseudo-time (`global-time-step`, automatic, conservative, factor 1.0).
- **Turbulence:** k-ω SST, `correlation` ω wall treatment, low-Re correction off.
- **Energy:** on; viscous dissipation, pressure work, kinetic-energy terms off. Gravity and radiation off.
- **Air:** incompressible ideal gas (M = 28.966); cₚ, μ, k piecewise-linear (Incropera A.4).
- **Inconel 718:** **ρ = 8190.0 kg/m³** (option `value`, read back); k and cₚ piecewise-linear (VDM 4127).
- **Boundary conditions:** inlet **23.5 m/s, 300 K**, I = 4.411 %, D_h = 0.02 m; outlet 0 Pa gauge, reverse flow prevented; **8000 W/m²** on `heated_outer_wall`; adiabatic solid ends; coupled interface; operating pressure 101 325 Pa.
- **Discretisation at the end:** pressure second order; momentum, k, ω, energy second-order upwind; least-squares gradients. Fluent default relaxation and limits.

## 3. Convergence

| Stage | Iterations | What |
|---|---|---|
| 1 | 1–150 | flow + k-ω only, energy off, first order |
| 2 | 151–300 | energy on, first order |
| 3 | 301–600 | one switch to second order; evaluated every 100 iterations |
| confirmation | 601–700 | 100 more iterations; every criterion must still hold |

- **Iteration 400:** not evaluable (only 100 second-order rows in the 200-iteration window).
- **Iteration 500:** refused. The window still held the scheme-switch transient: T_out drift 0.263 K, T_solid_max 0.158 K, Δp 0.24 %, Q_interface 0.12 %.
- **Iteration 600:** CONVERGED. **Iteration 700:** CONFIRMED.

**Total: 700 iterations**, 43 min 53 s wall clock (00:14:42 → 00:58:35) including audits and exports.

| Criterion (same as 5B) | Target | Fine, final (iteration 700) |
|---|---|---|
| Continuity | < 1e-4 | **1.9 × 10⁻¹⁰** |
| x / y / z momentum | < 1e-4 | 5.3 × 10⁻¹⁶ / 5.3 × 10⁻¹⁶ / 1.7 × 10⁻¹⁴ |
| k / ω | < 1e-4 | 5.2 × 10⁻¹³ / 2.8 × 10⁻¹³ |
| Energy | < 1e-6 | **8.6 × 10⁻¹⁵** |
| T_out drift, last 200 it | < 0.1 K | **2.8 × 10⁻⁶ K** |
| T_solid_max / T_wall_max / T_outer_max drift | < 0.1 K | 8.4 × 10⁻⁶ / 0 / 0 K (monitor resolution) |
| Δp / Q_interface / ṁ_out relative drift | < 0.1 % / 0.1 % / 0.01 % | 8.9 × 10⁻⁸ % / 4.1 × 10⁻⁷ % / 1.3 × 10⁻⁸ % |
| Mass imbalance | < 0.01 % | **3.9 × 10⁻¹² %** |
| Energy imbalance | < 0.5 % | **6.2 × 10⁻¹¹ %** |

## 4. Results — MESH-INDEPENDENCE / FINE

All definitions are identical to Sections 5B and 6A (same post-processing code; only the mesh
constants changed).

### Flow

| Quantity | Fine |
|---|---|
| Inlet / outlet mass flow (Fluent flux report) | **8.675920 / 8.675920 g/s** |
| **Δp — area-weighted static gauge pressure, inlet face minus outlet face** | **439.12 Pa** (mass-weighted: identical) |
| — wall shear / 1-D acceleration / profile development | 244.28 / 149.13 / 45.97 Pa (momentum balance closes to −0.26 Pa, −0.059 %) |
| Re inlet / outlet (D = 20 mm, G = ṁ/A = 27.651 kg/m²s) | **29 958 / 25 549** |
| Outlet area-mean velocity; maximum velocity | 28.89 m/s; 34.97 m/s (outlet centreline); Mach 0.09 |
| Reverse-flow cells / outlet faces | 0 / 0 |

### Thermal

| Quantity | Fine |
|---|---|
| **Outlet temperature, mass-weighted** (Fluent surface integral) | **368.851 K** |
| Outlet mixing-cup (enthalpy); energy balance on this mesh's own Q and ṁ | 368.910 K; 368.914 K |
| **Heat-transfer rate (heated wall)** | **602.994 W** (= 8000 W/m² × the 72-gon outer area, to 10⁻¹⁰) |
| Fluid enthalpy gain (outlet − inlet flux, Fluent report) | 619.124 − 16.130 = 602.994 W |
| **Maximum solid temperature** | **560.83 K** (outer-wall facet maximum, outlet end); hottest cell centre 560.60 K (r = 19.55 mm, z = 597.8 mm) |
| Minimum solid temperature | 423.09 K (cell centre, inlet end); inner-wall facet minimum 422.17 K; outer-wall minimum 438.87 K |
| Peak inner-wall temperature | 553.50 K |
| Area-average inner / outer wall temperature | 519.44 / 527.18 K |
| Volume-mean solid temperature | 524.18 K |
| **Through-wall ΔT at mid-span, z = 300 mm (matched location)** | **7.597 K** (T_wi 530.17 K, T_wo 537.77 K, T_b 334.65 K) |
| Through-wall ΔT at z = 570 mm (the 5B reported station) | 7.378 K (1-D thick-wall with local k: 7.427 K) |
| h at mid-span; bore heat flux there | 81.29 W/m²K; 15 894 W/m² |
| Fully developed Nu, x/D 18–29 (slab mean / exact window) | **54.66** / 54.66 |
| Fully developed Darcy f, x/D 18–29 (slab mean / exact window) | **0.02181** / 0.021810 |

The through-wall ΔT is taken at **matched physical locations**: linear interpolation between slab
centres to exactly z = 300 mm (and 570 mm), the same operation as on the coarse and medium meshes.
The first-slab value (16.69 K at z = 2.2 mm) is an inlet-edge value and is not compared.

### y⁺ on the conjugate wall (from the converged fine solution)

| Minimum | Area mean | Median | 95th pct | 99th pct | Maximum | ≤ 1 | ≤ 0.5 |
|---|---|---|---|---|---|---|---|
| **0.209** | **0.2427** (Fluent: 0.24267) | 0.238 | 0.291 | 0.391 | **0.653** (first slab, z = 2.2 mm) | **100 %** | 99.26 % |

First-cell-centre wall distance at mid-span: 5.17–6.08 µm, i.e. an equivalent first layer of
10.3 µm (O-grid diagonals) to 12.2 µm (axes), the same pattern as the other two meshes (F-028).
**SST compatibility: the fine mesh is appropriate for k-ω SST with the `correlation` wall
treatment.** Every wall face is inside the viscous sublayer (y⁺ ≤ 0.65), so wall shear and heat
flux are resolved rather than bridged by a wall function. Because all three meshes share the same
first-layer height, near-wall resolution in the wall-normal direction is **not** what the study
refines (see `09_Mesh_Independence/Mesh_Independence_Report.md` §8).

### Conservation (same definitions as Section 5B)

| | Value |
|---|---|
| Mass: in − out | −3.4 × 10⁻¹⁶ kg/s (monitor) → **3.9 × 10⁻¹² %** |
| Energy: wall heat input vs fluid enthalpy gain; net over all boundaries | 602.9944 vs 602.9944 W; net −3.73 × 10⁻¹⁰ W (monitor, the 5B criterion definition; Fluent flux report −3.73 × 10⁻¹⁰ W) → **6.2 × 10⁻¹¹ %** |
| Heat by face integration vs Fluent report | 602.9944 W both (interface and outer wall) |

## 5. Physical sanity check

| Check | Result |
|---|---|
| Pressure decreases downstream | ✅ slab-average pressure falls monotonically over all 135 slabs |
| Temperature rises through the heated region | ✅ bulk temperature rises monotonically, 300 → 368.85 K |
| Heat flows from wall into fluid | ✅ bore heat flux > 0 in every slab (min 15 064 W/m²); T_inner > T_bulk and T_outer > T_inner everywhere |
| NaN / Inf | ✅ 0 in all exports |
| Non-physical values | ✅ fluid 300.0–551.7 K, solid 423.1–560.6 K, inside their property tables at every iteration; 0 limiter or divergence messages |
| Unexpected reverse flow | ✅ 0 cells with w < 0; outlet w ≥ 0.39 m/s |
| Mass / energy conservation | ✅ round-off (above) |
| Startup | ✅ stage 2 rose monotonically (0 decreases in 150 steps); history maximum 560.682 K at iteration 302 is 0.080 K above the final value; T_fluid_min dipped 0.23 mK below 300 K at iteration 301 (scheme switch) and recovered |

## 6. Raw comparison with the medium mesh (two points; the three-point verdict is in 09)

| Quantity | Fine | Medium | Fine − medium | % of medium | Polygon geometry alone |
|---|---|---|---|---|---|
| Inlet mass flow | 8.6759 g/s | 8.6622 g/s | +0.0138 g/s | **+0.159 %** | **+0.159 %** (planar ratio) |
| Heat-transfer rate | 602.994 W | 602.755 W | +0.239 W | **+0.040 %** | **+0.040 %** (lateral ratio) |
| **Pressure drop** | **439.12 Pa** | **438.13 Pa** | +0.99 Pa | **+0.23 %** | partly (estimate in 09) |
| — wall-shear term | 244.28 | 242.87 | +1.41 | +0.58 % | — |
| **Outlet T, mass-weighted** | **368.851 K** | **368.932 K** | **−0.081 K** | −0.022 % | −0.082 K (energy balance on each mesh's own Q and ṁ) |
| **Max solid temperature** | **560.83 K** | **562.58 K** | **−1.75 K** | −0.31 % (−0.66 % of the 262.6 K rise) | −0.08 K (bulk part) |
| Peak inner-wall temperature | 553.50 K | 555.27 K | −1.76 K | −0.32 % | — |
| **Through-wall ΔT, mid-span** | **7.597 K** | **7.581 K** | +0.016 K | **+0.21 %** | ≈ +0.009 K (apothem estimate) |
| Through-wall ΔT, z = 570 mm | 7.378 K | 7.361 K | +0.017 K | +0.23 % | — |
| h, mid-span | 81.29 | 80.69 W/m²K | +0.60 | +0.74 % | — |
| Fully developed Nu (slab mean) | 54.66 | 54.17 | +0.49 | **+0.90 %** | ≈ −0.02 % |
| Fully developed f (slab mean) | 0.02181 | 0.02163 | +0.00019 | **+0.87 %** | ≈ −0.02 % |
| y⁺ min / mean / max | 0.209 / 0.243 / 0.653 | 0.208 / 0.241 / 0.585 | — | +0.4 / +0.7 / +11.7 % | max: sampling position |
| Mass / energy imbalance | 3.9e-12 / 6.2e-11 % | 7.0e-13 / 3.1e-11 % | — | round-off | — |

What the data show on their own:

1. **ṁ, Q and T_out move by exactly the polygon geometry**, as between coarse and medium. The
   72-gon is closer to the circle, so it carries more air (+0.159 %) and receives slightly more heat
   (+0.040 %); Q/ṁ falls, so T_out falls by 0.081 K against 0.082 K predicted by the energy balance.
2. **The −1.75 K in maximum solid temperature is resolution, not geometry.** Only 0.08 K comes from
   the bulk shift. The rest is the air film: h is 0.74 % higher at mid-span and Nu 0.90 % higher in
   the developed region. The metal conducts the same way (through-wall ΔT +0.21 %).
3. **Every change is smaller than the coarse→medium change and has the same sign** (T_max −2.83 →
   −1.75 K; exact-window Nu +1.48 → +0.91 % and f +1.35 → +0.85 %; Δp +0.24 → +0.23 %). The pressure-drop step did
   not shrink in raw form; the geometric split in `09_Mesh_Independence` explains why.
4. **First- to second-order sensitivity keeps shrinking.** T_solid_max changed +0.67 K (coarse),
   +0.34 K (medium) and **−0.03 K** (fine) at the scheme switch; Δp −1.10, −0.81 and −0.53 Pa.
5. **y⁺ max +11.7 % is a sampling position.** The maximum sits in the first slab on every mesh,
   whose centre moves toward the inlet leading edge (5.0 → 3.3 → 2.2 mm). Mean y⁺ changes 0.7 %.

## 7. Figures (`Figures/`, all from exported Fluent data; matplotlib renders, not GUI screenshots)

| File | Shows |
|---|---|
| `figF01_fine_convergence.png` | residuals, T_out / T_solid_max, Δp, heat rates; stages marked |
| `figF02_axial_temperatures_vs_medium.png` | bulk, inner- and outer-wall temperature vs z, fine vs medium, and their difference |
| `figF03_through_wall_dT_vs_medium.png` | through-wall ΔT vs z, matched stations marked |
| `figF04_pressure_vs_medium.png` | slab-average static pressure vs z |
| `figF05_heat_flux_h_vs_medium.png` | bore heat flux and h vs z |
| `figF06_yplus_vs_medium.png` | y⁺ along the duct and around the circumference near mid-span |
| `figF07_nu_f_vs_medium.png` | local Nu and f vs x/D, fully developed window shaded |
| `figF08_fine_fields.png` | air and Inconel temperature, axial velocity (meridional) |
| `figF09_fine_midspan_section.png` | mid-span cross-section: 72-gon, cell centres coloured by T |
| `figF10_differences_vs_medium.png` | raw % differences with the faceting-only expectation marked |

## 8. Files

| Folder (under `06_Fluent_CFD/Mesh_Independence/Fine/`) | Content |
|---|---|
| `Case/` | `fine_final.cas.h5`, `fine_intermediate_end_stage2_firstorder.cas.h5/.dat.h5` |
| `Data/` | `fine_final.dat.h5` |
| `Monitors/` | `fine_monitors.out` (29 report definitions, every iteration), `fine_monitors.csv`, `residual_history.csv` |
| `Exports/` | `cells_fluid.csv` (354,780 rows), `cells_solid.csv` (145,800), wall and boundary face exports |
| `Profiles/` | `axial_profiles_cfd.csv` (135 slabs), `yplus_distribution.csv` |
| `Audit/` | three setup audits (132 items each), settings-state dumps and diff, `setup_comparison_vs_medium.csv`, convergence evaluations, Fluent flux / surface-integral reports, frozen-solution hashes before and after |
| `Journals/` | `solve_fine.py`, `postprocess_fine.py`, `s5_common.py` (copy), `run_fine.ps1`, `launch_fine.ps1` |
| `Logs/` | audit-only and production run logs, stdout, transcripts; post-processing log |
| root | `FINE_CFD_RESULTS.md`, `FINE_CFD_AUDIT.md`, `Fine_vs_Medium.csv`, `fine_cfd_results.json` |

The fine mesh itself is read from `05_Meshing/Mesh_Fine/fine.msh` and was not copied (85 MB);
its SHA-256 is recorded before and after the run.

## 9. Concerns specific to the fine run

- **Minimum orthogonal quality 0.314** (at the O-grid core corner, r ≈ 5.3 mm, first slab) and 540
  cells (0.11 %) with skewness > 0.80 are the Section 4 flag for this level. The solution shows no
  local anomaly there: residuals fell to round-off, and the core is far from the walls where the
  quantities of interest are formed.
- **The first-layer height is the same on all three meshes** (12.2 µm). The study therefore
  refines circumferential, axial and outer-radial resolution but **not** the wall-normal size of the
  first cell. This is deliberate (every mesh is wall-resolved), but it limits the formal order of
  convergence that can be observed (see 09, §6).
- **Outlet boundary cell and window sampling:** as on the other meshes, the last slab's bulk value is
  the outlet value, and the slab-mean fully developed window is sampled on the fine mesh's own slab
  centres (x/D 18.11–29.00). The three-mesh study therefore uses exact-window means (x/D 18–29,
  interpolated), which differ from the slab means by < 0.03 %.
