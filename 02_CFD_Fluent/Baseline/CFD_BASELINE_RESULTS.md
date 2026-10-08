# CFD Baseline Results — Section 5B (medium mesh, converged)

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems
**Date:** 2026-09-23 · **Software:** ANSYS Fluent 2026 R1 (v261), `3ddp`, batch, 4 cores (Student)
**RE-ANALYSIS 2026 — newly generated results, not recovered originals. No measured data exists or is used.**

> **Status in one line.** The baseline case on the **medium mesh (159,840 cells)** is converged
> to the NR-03 residual targets **and** a physical plateau, conserves mass and energy to round-off,
> and was confirmed by a further 100 iterations. **Mesh independence has NOT been shown** — the
> coarse and fine meshes have not been solved — so every number below is a medium-mesh value.

Companion documents: `CFD_VS_ANALYTICAL.md` (comparison with Section 2, with explanations),
`CFD_BASELINE_AUDIT.md` (how the run was controlled and checked).
Machine-readable: `Baseline/cfd_baseline_results.json`, `Baseline/CFD_vs_Analytical.csv`.

---

## 1. What was solved

The frozen Section 2 case, unchanged. **Nothing** in the geometry, heat flux, inlet velocity,
material properties, outlet pressure or turbulence model was altered in Section 5B.

| Item | Value |
|---|---|
| Geometry | Dᵢ 20 / Dₒ 40 / L 600 mm Inconel 718 duct, air in the bore (48-gon faceted section) |
| Mesh | `Case/medium_mesh_used_for_baseline.msh` — 159,840 hex cells (116,640 fluid / 43,200 solid), 90 axial slabs |
| Inlet | 23.5 m/s normal, 300 K, I = 4.411 %, Dₕ = 20 mm |
| Outlet | 0 Pa gauge (101 325 Pa operating), prevent-reverse-flow on |
| Heated wall | 8000 W/m² on `heated_outer_wall`; both solid end faces adiabatic |
| Interface | `fluid_solid_interface` / `-shadow`, **Coupled** — wall temperature solved, never imposed |
| Air | incompressible ideal gas (M = 28.966); cₚ, μ, k piecewise-linear, Incropera A.4 |
| Inconel 718 | **ρ = 8190 kg/m³ (read back from Fluent)**; k, cₚ piecewise-linear, VDM 4127 |

## 2. Solver settings of the final solution (read back from Fluent, audit 3 of 3)

| Setting | Value |
|---|---|
| Solver | pressure-based, **steady**, absolute velocity, **Coupled** p-v with pseudo-time (`global-time-step`, automatic, conservative length scale, factor 1.0) |
| Turbulence | **k-ω SST**, `wall_omega_treatment = correlation`, low-Re correction off |
| Energy | on; viscous dissipation, pressure work, kinetic energy terms off (Br = 0.0018, Ec = 0.0027) |
| Gravity / radiation | off / none |
| Gradient | least-squares cell-based |
| Discretisation | pressure **second-order**; momentum, k, ω, energy **second-order upwind** (NR-06) |
| Explicit relaxation | pressure 0.5, momentum 0.5; pseudo-time relaxation k, ω, T 0.75; density, body force, μₜ 1.0 — **Fluent defaults, unchanged** |
| Solution limits | Fluent defaults (T 1–5000 K); **never reached** (§8) |

All 59 audited settings were read back out of Fluent before the first iteration, again after the
scheme switch, and again after the final iteration: **59/59 correct each time**
(`Audit/setup_audit_{1_presolve,2_final_schemes,3_final}.txt`).

## 3. Convergence

### Sequence (fresh standard initialisation: 300 K, w = 23.5 m/s, 0 Pa gauge)

| Stage | Iterations | Equations | Schemes | Purpose |
|---|---|---|---|---|
| 1 | 1–150 | flow + k-ω, **energy off** | first-order upwind | develop the velocity and turbulence fields before any heat is applied |
| 2 | 151–300 | + energy | first-order upwind | bring the thermal field up on a developed flow (checkpoint written) |
| 3 | 301–600 | all | **second-order** | production discretisation; convergence evaluated every 100 iterations |
| confirm | 601–700 | all | second-order | 100 further iterations to prove the converged state holds |

**Total: 700 iterations** (400 of them second-order). Wall clock 12 min 58 s including the three
audits, case/data writing, reports and exports (`Logs/baseline_driver.txt`).

### Convergence evaluations (`Audit/convergence_evaluations.json`)

| Iteration | Result | Reason |
|---|---|---|
| 400 | not evaluable | only 100 second-order rows; the 200-iteration drift window must lie wholly inside stage 3 |
| 500 | **not converged** | window 301–500 still contained the scheme-switch transient: T_out drift 0.42 K, T_solid_max 0.40 K, Δp 0.33 %, Q_interface 0.17 % — all above target |
| 600 | **CONVERGED** | every criterion met |
| 700 | **CONFIRMED** | every criterion still met after 100 more iterations |

### Final state (iteration 700)

| Criterion | Target | Achieved |
|---|---|---|
| Continuity residual | < 1 × 10⁻⁴ | **9.0 × 10⁻¹¹** |
| x / y / z momentum | < 1 × 10⁻⁴ | 3.7 × 10⁻¹⁶ / 3.1 × 10⁻¹⁶ / 1.6 × 10⁻¹⁴ |
| k / ω | < 1 × 10⁻⁴ | 7.2 × 10⁻¹³ / 2.0 × 10⁻¹³ |
| Energy | < 1 × 10⁻⁶ | **1.6 × 10⁻¹⁴** |
| T_out drift, last 200 it (NR-04) | < 0.1 K | **2.3 × 10⁻⁶ K** |
| T_solid_max / T_wall_max / T_outer_max drift | < 0.1 K | 7.1 × 10⁻⁶ / 0 / 0 K |
| Δp relative drift | < 0.1 % | 6.9 × 10⁻⁸ % |
| Q_interface relative drift | < 0.1 % | 3.5 × 10⁻⁷ % |
| ṁ_out relative drift | < 0.01 % | 1.3 × 10⁻⁸ % |
| Mass imbalance | < 0.01 % | **7.0 × 10⁻¹³ %** |
| Energy imbalance | < 0.5 % | **3.1 × 10⁻¹¹ %** |

The residuals fell to round-off, which is expected here: the case is steady, smooth and
well-posed, the coupled solver was allowed to run to a genuine fixed point, and nothing was
stopped at the first moment the targets were crossed. The physical monitors — not the
residuals — are the convergence evidence (NR-04); they are flat to within 10⁻⁵ K. Figure 16.

## 4. Flow results

| Quantity | Value | Source |
|---|---|---|
| Mass flow in / out | **8.662155 g/s** / 8.662155 g/s | Fluent flux report |
| — vs frozen 8.686 g/s | −0.280 % | 48-gon planar area ratio 0.997147 (−0.285 %) plus Fluent's R = 287.0425 vs 287.058 (+0.005 %) |
| Mass flux G | 27.651 kg/m²s | ṁ / Fluent inlet area 3.13263 × 10⁻⁴ m² |
| **Re inlet / outlet** (D = 20 mm) | **29 958 / 25 545** | μ at 300 K and at the outlet bulk T |
| Re on the 48-gon Dₕ (19.957 mm) | 29 894 / 25 490 | for reference |
| Regime | turbulent throughout (slab Re ≥ 25 540) | |
| Inlet / outlet area-mean velocity | 23.500 / **28.894 m/s** | Fluent area average |
| Maximum velocity | 34.99 m/s (outlet centreline) | cell data |
| Centreline / bulk at the outlet | 1.211 | |
| Bulk Mach, inlet / outlet | 0.0677 / **0.0750** | V_b / √(γRT_b) |
| Maximum local Mach | 0.097 (outlet centreline, 34.99 m/s at 323 K) | face data |
| Reverse-flow cells / outlet faces | **0 / 0** (outlet w ≥ 0.40 m/s everywhere) | |
| Max radial / swirl velocity | 0.54 / 0.013 m/s | secondary flow negligible |
| Velocity development | w_max/w_b reaches 98 % of its exit value at x/D ≈ 17.8 (99 % at 20.8) | Figure 13 |

### Pressure drop — definition and result

**Definition used for every CFD Δp in this project:**
Δp = (area-weighted static gauge pressure on `fluid_inlet`) − (area-weighted static gauge
pressure on `fluid_outlet`). The outlet value is 0 Pa by the boundary condition.

| | Value |
|---|---|
| **Δp, static, inlet → outlet (area-weighted)** | **438.13 Pa** |
| Same, mass-weighted | 438.13 Pa (identical to within 10⁻⁸ Pa) |
| Δp / p_operating | 0.43 % — incompressible-ideal-gas assumption holds |

Its analytical counterpart is the **CFD-comparable** 441.53 Pa (friction + acceleration +
entry, D-019). The 1003.4 Pa installation figure contains entrance and exit losses that do not
exist in this domain and is never compared with Fluent (T-022).

Decomposition from the axial momentum balance on the exported field (closes to −0.197 Pa,
−0.045 %): **wall shear 242.87 Pa + 1-D acceleration 149.31 Pa + momentum-flux profile
development 46.15 Pa** (outlet β = 1.058). Figure 17. Fluent's own wall-force report,
F_wall,z = 0.076082 N, equals the exported-face integral to 4 × 10⁻¹¹ relative.

Fluent also reports total pressure (`Audit/fluent_si_p0_area.txt`: 759.77 Pa inlet,
425.16 Pa outlet, area-weighted). It is a different quantity, has no analytical counterpart in
Section 2, and is **not** combined with or substituted for the static Δp anywhere.

## 5. Thermal results

### Heat flow

| Quantity | Value |
|---|---|
| **Heat into `heated_outer_wall`** | **602.755 W** |
| Heat across the fluid–solid interface | 602.755 W (differs from the wall by 9 × 10⁻¹⁰ W) |
| Heat carried out by the air (enthalpy out − in, Fluent flux report) | 618.862 − 16.107 = 602.755 W |
| Heat through the solid end faces | 0 W (adiabatic, as imposed) |
| vs frozen 603.186 W | **−0.0714 %** = lateral-area ratio sin(π/48)/(π/48) − 1 = −0.0714 % |

### Temperatures

| Quantity | Value |
|---|---|
| Inlet bulk | 300.000 K |
| **Outlet bulk, mass-weighted static T** | **368.932 K** |
| Outlet mixing-cup (enthalpy-weighted, inverted with the cₚ table) | 368.993 K |
| Bulk-temperature rise | 68.93 K; linear in z to within 0.57 K (R² = 0.99994) |
| **Maximum solid temperature** | **562.58 K** (outer-wall facet maximum, outlet end); hottest cell centre 562.13 K at r = 19.1 mm, z = 596.7 mm |
| Minimum solid temperature | 423.97 K (cell centre), inlet end; inner-wall facet minimum 423.21 K |
| Volume-mean solid temperature | 525.48 K (whole duct — see F-027 before comparing) |
| Inner wall (interface) min / area-mean / max | 423.21 / 520.74 / **555.27 K** |
| Outer wall min / area-mean / max | 438.33 / 528.46 / 562.58 K |
| Maximum fluid temperature | 553.41 K (at the wall, outlet end) |

### Through-wall temperature difference (outer − inner, circumferential average)

| Station | ΔT_wall |
|---|---|
| **z = 570 mm (x/D 28.5) — reported value, clear of the adiabatic end** | **7.361 K** |
| z = 300 mm (mid-span) | 7.581 K |
| last slab (z = 596.7 mm) | 7.310 K |
| **first slab (z = 3.3 mm)** | **15.119 K** — maximum |

The through-wall ΔT is 1-D only away from the ends. At the inlet end the cold air and thin
thermal boundary layer make h very high (Nu ≈ 240 in the first slab); the bore draws
**38 471 W/m², 2.4 × the 1-D 16 000 W/m²**, and heat conducts axially through the Inconel to
supply it. The bore flux recovers to within 1 % of 16 000 W/m² by z ≈ 250 mm and falls to
15 644 W/m² in the last slab next to the adiabatic outlet end face. Figures 8 and 12.

### Heat-transfer coefficient and friction

| Quantity | Value |
|---|---|
| h at z = 570 mm / last slab | 83.64 / 83.95 W/m²K (h = q″ᵢ/(T_wi − T_b,mass)) |
| Nu at the last slab | 53.47 |
| **Fully developed Nu, mean over x/D 18.2–28.8 (T-012)** | **54.17** |
| **Fully developed Darcy f, same window, f = 8τ_w ρ_b/G²** | **0.02163** |
| T_w/T_b in the window | 1.548 |
| Constant-property Gnielinski / Dittus–Boelter at the CFD conditions | 63.5 / 68.6 |
| Kays & Crawford-corrected (n = 0.5) at the CFD conditions | 51.0 |
| Exponent n implied by the CFD | ≈ 0.36 |
| Petukhov f / heating-corrected (T_w/T_b)^−0.1 | 0.02440 / 0.02336 |

## 6. y⁺ on the conjugate wall (recomputed from the converged second-order solution)

| Statistic | Value |
|---|---|
| **Minimum** | **0.208** (z = 357 mm, θ = 41°) |
| **Area-weighted mean** | **0.241** (Fluent's own surface integral: 0.2409596) |
| Median / 95th / 99th percentile (by area) | 0.236 / 0.288 / 0.499 |
| **Maximum** | **0.585** (z = 3.3 mm, first slab — highest wall shear, thinnest boundary layer) |
| Mean over the fully developed window | 0.229 |
| Area with y⁺ ≤ 1 / ≤ 0.5 | **100 %** / 99.07 % |
| First-cell-centre wall distance | 5.19–6.06 µm |

**Judgement against the wall treatment.** SST k-ω with Fluent's `correlation` ω wall treatment
integrates the equations through the viscous sublayer when the first cell centre lies within it
(y⁺ ≲ 1). Every face of the conjugate wall satisfies that, so wall shear and wall heat flux are
**resolved, not modelled by a wall function**. NR-01 (y⁺ ≤ 1 target) is met with margin, and
T-010 is closed on the medium mesh. y⁺ here is Fluent's cell-centre value, i.e. based on half
the first-layer height.

The circumferential y⁺ pattern is geometric, not physical: wall shear varies only 0.078 %
around the circumference while y⁺ varies 15.5 %, because the first layer is ≈ 12.1–12.2 µm
on the four O-grid axes (12.2 µm design) and about 10.4 µm at the diagonals (F-028). This is harmless — it
is below 12.2 µm, not above — and is recorded, not changed.

The Section 5A diagnostic's y⁺_max = 0.5916 (first-order, not converged) moved to 0.5848.

## 7. Conservation

| | Value |
|---|---|
| Mass: in − out (Fluent flux report) | −6.07 × 10⁻¹⁷ kg/s → **7.0 × 10⁻¹³ %** of ṁ |
| Energy: net over all boundaries (Fluent flux report) | −1.84 × 10⁻¹⁰ W → **3.1 × 10⁻¹¹ %** of Q |
| Interface vs heated wall | −1.5 × 10⁻¹⁰ % |
| Energy by face-value re-analysis from exported enthalpy | 602.726 W (−0.005 %; post-processing interpolation, not solver error) |

## 8. Temperature range, extrapolation and clipping

| Check | Result |
|---|---|
| Fluid, final: 300.0–553.4 K vs property table 250–600 K | ✅ inside — **no extrapolation** |
| Solid, final: 424.0–562.1 K vs property table 293.15–673.15 K | ✅ inside — **no extrapolation** |
| Fluid, whole Section 5B history: 299.998–553.42 K | ✅ inside (a 2 mK undershoot below the 300 K inlet at iteration 303, just after the scheme switch; decayed) |
| Solid, whole Section 5B history: 300.0–562.133 K | ✅ inside |
| Section 5B startup overshoot | **none**: stage 2 rose monotonically to 561.78 K; the history maximum 562.133 K (iteration 393) is 0.006 K above the final value |
| Fluent "temperature limited", "viscosity limited", divergence, floating-point or reversed-flow messages | **0** |
| NaN / Inf in the exported fields | **0** |
| Section 5A excursion (761 K at iteration 35, F-022) | a **different run**; stays in the 5A record. The 5B baseline was re-initialised from the setup case (not continued from 5A data), so that excursion cannot be in this solution |

## 9. Engineering sanity checks against `EXPECTED_RESULTS.md` (ranges fixed in Section 2, not revised)

| Parameter | Expected range | CFD | |
|---|---|---|---|
| Re inlet / outlet | 29 400–30 500 / 25 000–26 100 | 29 958 / 25 545 | ✅ ✅ |
| Outlet velocity | 27.5–30.3 m/s | 28.89 m/s | ✅ |
| Mach (max) | 0.070–0.080 (bulk basis) | 0.0750 bulk; 0.097 local centreline | ✅ on the range's own bulk basis; the local maximum is a different definition and ≪ 0.3 |
| Flow regime | turbulent throughout | slab Re ≥ 25 540 | ✅ |
| **Darcy f** | **0.022–0.027** | **0.02163** | ❌ **1.7 % below the lower bound** — F-029 |
| Hydrodynamic entry length | x/D ≈ 15–20 | ≈ 17.8 (98 % of exit w_max/w_b) | ✅ |
| **Δp across the CFD domain** | **375–510 Pa** | **438.1 Pa** | ✅ |
| — friction component | 224–303 Pa | 242.9 Pa (wall shear) | ✅ |
| — acceleration component | 127–171 Pa | 149.3 Pa | ✅ |
| Δp / p_op | < 1 % | 0.43 % | ✅ |
| **Total heat rate** | **600–606 W** | **602.76 W** | ✅ |
| **Outlet bulk temperature** | **365–373 K** | **368.93 K** | ✅ |
| Bulk-temperature profile | linear | linear to 0.57 K over 69 K | ✅ |
| **Fully developed Nu** | **44–67** | **54.2** | ✅ |
| h at exit | 70–97 W/m²K | 83.95 W/m²K | ✅ |
| **Peak inner-wall temperature** | **534–583 K** | **555.27 K** | ✅ |
| Wall-to-bulk ΔT at exit | 165–215 K | 186.3 K | ✅ |
| **Through-wall ΔT** | **6.6–8.0 K** | **7.36 K** at x/D 28.5 (15.1 K in the first slab — a local conjugate end effect, not a coupling failure) | ✅ |
| **Maximum solid temperature** | **541–591 K** | **562.58 K** | ✅ |
| y⁺ | ≤ 1 | max 0.585 | ✅ |
| Energy / continuity-momentum-turbulence residuals | < 1e-6 / < 1e-4 | 1.6e-14 / ≤ 9.0e-11 | ✅ |
| T_out drift, last 200 it | < 0.1 K | 2.3e-6 K | ✅ |
| Energy imbalance | < 0.5 % | 3.1e-11 % | ✅ |
| Orthogonal quality / skewness (medium mesh) | > 0.1 / < 0.95 | 0.446 / 0.760 | ✅ |
| Mesh independence | < 3 % in Nu and peak T | — | ⏳ not attempted in 5B |
| Volume-mean solid temperature (Section 4 of the ranges) | 542–566 K | 525.5 K (whole-duct volume average) | ⚠ not the same quantity — the range was built from the exit-station mid-wall value (F-027); Section 6 must compare on a matched basis |

**One range is missed: the fully developed friction factor**, by 1.7 % of the lower bound.
The range's red-flag note says "low → mesh too coarse near wall"; that cause is argued against
by y⁺ ≤ 0.59 everywhere, but only the mesh study can settle it. About 4 of the 10.4 percentage
points are the standard gas-heating reduction of f that the range did not include. Recorded as
F-029, not re-interpreted.

## 10. First- vs second-order (the end of stage 2 vs the final solution)

| | End of stage 2 (first-order, it 300) | Final (second-order, it 700) | Change |
|---|---|---|---|
| T_out bulk | 368.930 K | 368.932 K | +0.003 K |
| T_solid_max | 561.784 K | 562.127 K | +0.343 K |
| T_wall_max (inner) | 554.922 K | 555.267 K | +0.345 K |
| Δp | 438.939 Pa | 438.126 Pa | −0.81 Pa (−0.19 %) |
| y⁺_max | 0.5916 | 0.5848 | −1.1 % |

The discretisation order moves the answer by well under 0.1 % in temperature and 0.2 % in Δp
on this mesh. This is a sensitivity, **not** a mesh-independence result.

## 11. Figures (all generated from exported Fluent data by `Journals/postprocess_baseline.py`)

These are matplotlib renders of the exported Fluent solution arrays, **not** Fluent GUI screenshots.

| # | File | Shows |
|---|---|---|
| 1 | `fig01_velocity_contour.png` | axial velocity on a longitudinal section and cross-sections |
| 2 | `fig02_velocity_vectors.png` | in-plane velocity vectors (secondary flow ≤ 0.54 m/s) |
| 3 | `fig03_streamlines.png` | streamlines on the longitudinal section |
| 4 | `fig04_pressure_contour.png` | static pressure field |
| 5 | `fig05_fluid_temperature_contour.png` | fluid temperature, thermal boundary-layer growth |
| 6 | `fig06_solid_temperature_contour.png` | solid temperature, axial and through-wall |
| 7 | `fig07_outer_wall_temperature.png` | heated outer-wall temperature vs z, against Section 2 |
| 8 | `fig08_wall_heat_flux.png` | bore heat flux vs z — the 2.4 × inlet peak and the end-face dip |
| 9 | `fig09_yplus.png` | y⁺ distribution, axial and circumferential |
| 10 | `fig10_pressure_axial.png` | slab-averaged pressure vs z |
| 11 | `fig11_bulk_temperature_axial.png` | bulk and wall temperatures vs z against the Section 2 march |
| 12 | `fig12_through_wall_temperature.png` | through-wall ΔT vs z against 1-D Fourier |
| 13 | `fig13_velocity_profiles.png` | radial velocity profiles at several stations |
| 14 | `fig14_radial_temperature.png` | radial temperature through air and metal |
| 15 | `fig15_nusselt_friction.png` | local Nu and f vs x/D with the correlations |
| 16 | `fig16_convergence.png` | residuals and physical monitors, all 700 iterations, stages marked |
| 17 | `fig17_pressure_decomposition.png` | Δp split: wall shear / acceleration / profile development vs analytical |

## 12. Data produced

| Folder | Content |
|---|---|
| `Case/` | `baseline_medium_final.cas.h5`, `intermediate_end_stage2_firstorder_iter300.cas.h5`, `medium_mesh_used_for_baseline.msh` |
| `Data/` | `baseline_medium_final.dat.h5`, `intermediate_end_stage2_firstorder_iter300.dat.h5` |
| `Monitors/` | `baseline_monitors.out` (29 report definitions, every iteration), `baseline_monitors.csv`, `residual_history.csv`, startup-trial files |
| `Exports/` | `cells_fluid.csv` (116,640 rows), `cells_solid.csv` (43,200), `wall_interface.csv`, `wall_outer.csv`, `wall_solid_ends.csv`, `boundary_inlet.csv`, `boundary_outlet.csv` |
| `Profiles/` | `axial_profiles_cfd.csv` (90 slabs × 29 quantities), `yplus_distribution.csv` |
| `Audit/` | setup audits ×3, convergence evaluations, run summary, Fluent flux and surface-integral reports, volume-export check |
| `Baseline/` | this file, `CFD_VS_ANALYTICAL.md`, `CFD_BASELINE_AUDIT.md`, `CFD_vs_Analytical.csv`, `cfd_baseline_results.json` |
| `Figures/` | 17 figures above |

## 13. What is not claimed, and what remains open

- **Mesh independence (NR-02) — not attempted.** Coarse and fine meshes are unsolved. Every
  value here, and especially Nu, f and the wall temperatures, may move with refinement.
- **Fully developed f is 10.4 % below Section 2 (PR-04 ±10 % marginally not met; 1.7 % below
  the EXPECTED_RESULTS band).** F-029. Open until the mesh study.
- **Wall temperature is 19 K below the Section 2 estimate.** Explained quantitatively
  (15.0 K from h, 4.2 K from axial conduction at the outlet end) in `CFD_VS_ANALYTICAL.md`.
  Which of the two — the SST model or the n = 0.5 correction — is closer to reality cannot
  be decided without measured data, and none exists.
- **Internal radiation is excluded** (A-015, F-007, T-009). It would move heat from the hot
  outlet-end wall to cooler wall upstream and lower the peak further.
- **Inlet turbulence intensity 4.411 % is assumed** (A-020). Its influence is confined to the
  entry region; the fully developed values are taken at x/D > 18.
- **Axial temperature gradients at both duct ends** (15.1 K through-wall at the inlet) are real
  conjugate effects the Section 2 closed form does not contain; Section 6 must compare FEA with
  the closed form at mid-span only (T-013).
