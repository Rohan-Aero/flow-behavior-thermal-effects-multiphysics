# Fine-Mesh CFD Audit — Section 6B

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems
**Date:** 2026-09-24 · ANSYS Fluent 2026 R1 (v261), `3ddp -g -py -t4`, batch
**RE-ANALYSIS 2026 — this audit describes newly generated runs, not recovered originals.**
**Label: MESH-INDEPENDENCE / FINE**

This file records how the fine-mesh case was built, how it was proven to carry the same physics as
the medium baseline, how convergence was judged, and how the frozen coarse and medium solutions
were protected. The results are in `FINE_CFD_RESULTS.md`.

---

## 1. Protecting the frozen solutions

| Measure | Evidence |
|---|---|
| The fine run executes with its working directory set to `06_Fluent_CFD/Mesh_Independence/Fine`, so every relative path it writes lands there | `Journals/run_fine.ps1` |
| The medium case is **read** for its settings with `read_case` (never `read_data`); nothing is written outside `Fine/` | `Journals/solve_fine.py` |
| SHA-256 of **24 files** recorded before the first fine Fluent launch: medium case, data, results, monitors, profiles, exports, journal; coarse case, data, results, documents, monitors, profiles, exports, journal; all three `.msh` files; `PROJECT_STATE.md` | `Audit/frozen_solutions_hashes_before.json` |
| Re-hashed after all Section 6B work | `Audit/frozen_solutions_hashes_after.json` (result: see §8) |
| Coarse and medium were **not rerun**; no concrete error was found in either | — |

## 2. Same physics — proven, not assumed

### 2.1 Carrying the settings

The procedure is the one proven in Section 6A:

1. read `../../Case/baseline_medium_final.cas.h5`, **case only**;
2. dump the full `setup` and `solution` settings trees (`Audit/settings_state_medium_case.json`);
3. `mesh.replace` with `../../../05_Meshing/Mesh_Fine/fine.msh`;
4. dump the trees again (`Audit/settings_state_fine_case.json`) and diff them recursively.

**Differences: 0** (`Audit/settings_diff_medium_vs_fine_after_replace.json` is an empty list). The
diff covers solver and models, every material property point, every boundary and cell-zone
condition, schemes, controls, limits, pseudo-time settings, all 29 report definitions, the
initialisation defaults and the monitor-file definition.

### 2.2 Deliberate changes after the replace (the only ones)

| Change | Why |
|---|---|
| Momentum, k, ω, energy schemes → first-order upwind for stages 1–2 | reproduces the Section 5B / 6A sequence; the medium *final* case carries second order |
| Monitor file → `Monitors/fine_monitors.out` | keeps the fine history separate |
| Inconel density re-asserted (option `value`, 8190) and read back | mandatory check; a no-op, the value was already 8190.0 |

### 2.3 Setup audit — 132 items, three times, each compared with the medium run's own audit

`solve_fine.py::audit()` reads back the 59 Section 5B items, the 12 Section 6A items and 2 new
Section 6B items (below). It then compares each of the 59 common items with the value the
**medium run itself recorded** at the same stage. Any mismatch stops the run before iteration 1.

| Audit | Result |
|---|---|
| audit-only dry run (00:12–00:14, no iterations) | **132 / 132**, first attempt (`Audit/auditonly_dryrun_setup_audit_1_presolve.txt`) |
| `setup_audit_1_presolve` (before iteration 1) | **132 / 132** |
| `setup_audit_2_final_schemes` (after the switch at 301) | **132 / 132** |
| `setup_audit_3_final` (after iteration 700) | **132 / 132** |
| Machine-readable comparison with the medium audit, 3 stages × 59 items | `Audit/setup_comparison_vs_medium.csv`: **177 rows, 177 "yes", 0 "no"** |

Items the Section 6B brief names explicitly, as read back before iteration 1:

| Item | Read back | Same as medium |
|---|---|---|
| **Inconel density** | **option `value`, 8190.0 kg/m³** | ✅ |
| **Inlet** | **23.5 m/s** normal to boundary, **300 K**, I = 0.044112, D_h = 0.02 m | ✅ |
| **Heated-wall flux** | `heated_outer_wall` Heat Flux **8000 W/m²**; both solid ends Heat Flux 0 | ✅ |
| Outlet | 0 Pa gauge; prevent reverse flow on | ✅ |
| Turbulence model / wall treatment | k-omega `sst`, `correlation`, low-Re correction off | ✅ |
| Air | incompressible ideal gas, M = 28.966; cₚ, μ, k piecewise-linear = Incropera A.4 | ✅ |
| Inconel k / cₚ | piecewise-linear = VDM 4127 | ✅ |
| Operating pressure, gravity, radiation, energy terms | 101 325 Pa, off, none, all off | ✅ |
| Interface | `Coupled` on both sides | ✅ |
| Numerics (startup) | Coupled, least-squares, pressure second order, others first order, `global-time-step` automatic/conservative, explicit relaxation 0.5 / 0.5, k and ω 0.75 | ✅ |
| Mesh cells / minimum volume | 500,580 / 4.009135 × 10⁻¹¹ m³ | 6A item |
| **Minimum orthogonal quality (Fluent `mesh quality`)** | **0.314386 > 0.1** | **6B item** |
| **Mesh-check warnings / malformed cells** (scan of the "Checking mesh … Done." block) | **none** | **6B item** |
| Zone names and IDs | §3 | 6A item |
| Initialisation defaults | T 300 K, u = v = 0, w 23.5 m/s, p 0 Pa, k 1.6119 m²/s², ω 1655.7 s⁻¹ | 6A item |

## 3. Fine mesh as read by Fluent (verified before iteration 1)

| Check | Result |
|---|---|
| File | `05_Meshing/Mesh_Fine/fine.msh`, 84,643,549 bytes, SHA-256 `436EF76E234109BF5A4E457206DB7E6010A1D9B2F1DFB30A5E2CA3BF509F37DB`, the post-face-winding (F-016) file |
| Cells | 354,780 hexahedral (fluid) + 145,800 hexahedral (solid) = **500,580** |
| Faces | 1,056,852 interior-fluid · 426,600 interior-solid · 2,628 inlet · 2,628 outlet · 9,720 interface (+ 9,720 shadow created by Fluent, conformal) · 9,720 heated outer wall · 1,080 + 1,080 solid ends; 1,520,028 in `size_info` |
| Nodes | 509,320 on read (518,968 across 4 partitions) |
| **Negative volumes** | **none**: minimum 4.009135 × 10⁻¹¹ m³, maximum 6.548914 × 10⁻⁹ m³ |
| Total volume | 7.530256 × 10⁻⁴ m³ = 0.998731 × exact, the 72-gon planar ratio |
| **Malformed cells** | none: the mesh check printed no warnings; all cells hexahedral |
| Orthogonal quality / aspect ratio | minimum 0.314386 at (3.73, 3.73, 2.22) mm, the O-grid core corner; maximum aspect 437.9 in the first wall layer. Both identical to the Section 4 table |
| **Zone names (IDs)** | `fluid_domain` (2) · `solid_domain` (3) · `interior-fluid` (4) · `interior-solid` (5) · `fluid_inlet` (6) · `fluid_outlet` (7) · `fluid_solid_interface` (8) · `heated_outer_wall` (9) · `solid_inlet_end` (10) · `solid_outlet_end` (11) · `fluid_solid_interface-shadow` (12): **identical to the medium and coarse** (`Audit/fine_mesh_zones.json`) |
| Fluid / solid / inlet / outlet / interface / heated wall present | ✅ all six |

## 4. Initialisation

Same as Sections 5B and 6A: a **fresh standard initialisation** to a uniform field (300 K,
w = 23.5 m/s, 0 Pa gauge, k and ω from the inlet). The medium case was read without its data, so
no part of the medium or coarse solution could seed the fine run. The three solutions are
independent.

## 5. Convergence control (identical to Sections 5B and 6A)

- **Stages:** 150 flow-only iterations, then 150 with energy at first order, then one switch to second order.
- **Evaluation:** chunks of 100 iterations, hard cap 3000.
- **Plateau window:** 200 iterations, taken only from second-order rows.
- **Residual targets (NR-03):** 1e-4 for flow and turbulence, 1e-6 for energy.
- **Plateau criteria:** T_out, T_solid_max, T_wall_max and T_outer_max drift < 0.1 K; Δp and Q_interface drift < 0.1 %; ṁ_out drift < 0.01 %.
- **Conservation criteria:** mass imbalance < 0.01 %, energy imbalance < 0.5 %.
- **Confirmation:** 100 more iterations after the first CONVERGED verdict.

| Iteration | Verdict |
|---|---|
| 400 | not evaluable (100 second-order rows) |
| 500 | **refused**: switch transient still in the window (T_out 0.263 K, T_solid_max 0.158 K, Δp 0.24 %, Q_interface 0.12 %, ṁ_out 0.008 %) |
| 600 | **converged** |
| 700 | **confirmed** |

The switch transient followed the same pattern as the other two meshes:
- the continuity residual jumped to 0.171 at iteration 301 (coarse 0.26);
- T_out moved within 368.840–369.103 K and Δp within 438.35–439.38 Pa in iterations 301–500;
- T_fluid_min dipped 0.23 mK below 300 K at iteration 301.

All of it decayed before iteration 600.

**Startup:** T_solid_max rose monotonically through stage 2 (zero decreases in 150 steps) to
560.636 K; Q_interface never exceeded 602.992 W in stage 2. The whole-history maximum, 560.682 K at
iteration 302, is **0.080 K** above the final value. No overshoot occurred and no temperature left
the property tables.

**First- to second-order change** (iteration 300 → 700):

| | Coarse | Medium | Fine |
|---|---|---|---|
| T_solid_max | +0.67 K | +0.34 K | **−0.033 K** |
| Δp | −1.10 Pa | −0.81 Pa | **−0.53 Pa** |
| T_out | +0.002 K | — | +0.004 K |
| y⁺ max | −1.1 % | — | −1.3 % |

The scheme-order sensitivity of the peak temperature falls from +0.67 K to +0.34 K and then to
−0.03 K, and that of Δp from −1.10 to −0.53 Pa. On the fine mesh the first-order solution is
already close to the second-order one, as expected when the discretisation error shrinks.

## 6. Conservation and limit checks

| Check | Result |
|---|---|
| Fluent mass flux report | in 0.0086759203, out −0.0086759203, net −3.37 × 10⁻¹⁶ kg/s |
| Fluent heat flux report | wall 602.99441, interface ±602.99441, inlet 16.130015, outlet −619.12443, ends −0, net −3.73 × 10⁻¹⁰ W |
| Heat by face integration vs Fluent report | 602.9944 W both; = 8000 × 72-gon outer area to 2 × 10⁻¹¹ |
| Momentum balance on the exports | closes to −0.26 Pa (−0.059 %) |
| Limit / divergence / reversed-flow / NaN messages in the solver output | **0** |
| NaN / Inf in exports | **0** |
| Export row counts | 354,780 fluid, 145,800 solid: exactly the cell counts (`Audit/volume_export_check.json`) |

## 7. Post-processing and definitions

`Journals/postprocess_fine.py` is `postprocess_coarse.py` with only the mesh constants changed
(polygon sides 72, slabs 135, file names). Every definition is therefore identical across the three
meshes:
- Δp (area-weighted static, inlet − outlet); mass-weighted outlet T and mixing-cup T;
- heat rates from Fluent's reports; y⁺ statistics; slab averages;
- fully developed window (x/D 18–29); f = 8τ_w ρ_b / G²;
- mid-span and z = 570 mm quantities interpolated linearly between slab centres.

**Post-processing observations:**
- Cell-reconstructed slab mass flow: −0.93 % in the first slab and +0.26 % in the second (steep
  inlet profile), then within 0.04 %. The Fluent flux report is used for every ṁ-dependent quantity.
- The derivation of `postprocess_fine.py` from the coarse script was checked by assertions on every
  string replacement; three assertion failures during derivation (replacement order, and one
  keyword argument, `coarse=dict(` → `fine=dict(`) were fixed before the script was run. No result
  was produced by a partially converted script.
- The comparison against the medium case reads the medium's saved results and profiles only.

## 8. Frozen-solution check after Section 6B

All 24 files were re-hashed after the fine run, the isothermal F-029 diagnostic and the final
three-mesh analysis. **24 / 24 are identical** to the pre-run hashes
(`Audit/frozen_solutions_hashes_after.json`, one `identical: true` entry per file). The files
include the medium and coarse case and data, their results, profiles and exports, all three
`.msh` files and `PROJECT_STATE.md`. `PROJECT_STATE.md` was then updated in two ways only: the
three header status lines (lines 8–10) were changed and the Section 6B block was appended.
`Audit/project_state_append_check.json` records both hashes, the three changed lines before and
after, and that every other original line is identical.

## 9. Not done in this phase, by instruction

- No Mechanical, structural analysis, parametric study or final report.
- Coarse and medium were not rerun and their results were not altered.
- The `PROJECT_STATE.md` history is unchanged; a Section 6B block is appended.
