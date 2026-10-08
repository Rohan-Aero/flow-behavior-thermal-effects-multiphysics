# Coarse-Mesh CFD Audit — Section 6A

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems
**Date:** 2026-09-23 · ANSYS Fluent 2026 R1 (v261), `3ddp -g -py -t4`, batch
**RE-ANALYSIS 2026 — this audit describes newly generated runs, not recovered originals.**
**Label: MESH-INDEPENDENCE / COARSE**

This file records how the coarse-mesh case was built, how it was proven to carry the same physics
as the medium baseline, how convergence was judged, and how the medium baseline was protected.
The results are in `COARSE_CFD_RESULTS.md`.

---

## 1. Protecting the medium baseline

| Measure | Evidence |
|---|---|
| The coarse run executes with its working directory set to `06_Fluent_CFD/Mesh_Independence/Coarse`, so every relative path it writes lands there | `Journals/run_coarse.ps1` |
| The medium case is **read** for its settings with `read_case` (never `read_data`), and nothing is written to `../../` | `Journals/solve_coarse.py` |
| SHA-256 of 21 baseline files (medium case and data, 5B intermediates, setup case, monitors, exports, profiles, results/audit documents, journals, both `.msh` files, `PROJECT_STATE.md`) recorded **before** the first coarse Fluent launch and **after** post-processing | `Audit/medium_baseline_hashes_before.json`, `…_after.json` |
| **Result: 21 / 21 unchanged**; no file in the medium `Case/`, `Data/`, `Monitors/` or `Audit/` folders was modified during Section 6A | same |
| `Journals/solve_baseline.py` and `postprocess_baseline.py` (5B) are untouched; the coarse journals are separate, derived copies | hashes above |

## 2. Same physics — proven, not assumed

### 2.1 Carrying the settings

A probe run (`Journals/probe_replace.py`, no iterations, nothing written outside `Coarse/`)
confirmed that Fluent 2026 R1's settings API has `mesh.replace(file_name, zones)`. The production
journal then:

1. read `../../Case/baseline_medium_final.cas.h5`, **case only**;
2. dumped the full `setup` and `solution` settings trees (`Audit/settings_state_medium_case.json`);
3. called `mesh.replace` with `../../../05_Meshing/Mesh_Coarse/coarse.msh`;
4. dumped the trees again (`Audit/settings_state_coarse_case.json`) and diffed them recursively.

**Differences: 0** (`Audit/settings_diff_medium_vs_coarse_after_replace.json` is an empty list).
This comparison covers:
- solver, models and every material property point;
- every boundary and cell-zone condition;
- schemes, controls, limits, pseudo-time settings;
- all 29 report definitions and their surface lists;
- the initialisation defaults;
- the monitor-file definition.

Fluent printed a warning that "surface groupings have changed" for 15 report definitions. The
diff shows their surface lists are unchanged by name. Fluent's reports return physically correct
values on the coarse zones (for example, inlet area 3.12145 × 10⁻⁴ m² = π·0.01²·0.993587 for a
32-gon), which confirms they act on the right zones.

### 2.2 Deliberate changes after the replace (the only ones)

| Change | Why |
|---|---|
| Momentum, k, ω, energy schemes → first-order upwind for stages 1–2 | reproduces the Section 5B sequence; the medium *final* case carries second order |
| Monitor file → `Monitors/coarse_monitors.out` | keeps the coarse history separate |
| Inconel density re-asserted (option `value`, 8190) and read back | mandatory check; a no-op here, the value was already 8190.0 |

### 2.3 Setup audit — 130 items, three times, each compared with the medium run's own audit

`solve_coarse.py::audit()` reads back the 59 Section 5B items and adds 12 Section 6A items. It
then compares each of the 59 common items with the value the **medium run itself recorded** at the
same stage (`../../Audit/setup_audit_{1_presolve,2_final_schemes,3_final}.json`). Any mismatch
stops the run.

| Audit | Result |
|---|---|
| `setup_audit_1_presolve` (before iteration 1) | **130 / 130** |
| `setup_audit_2_final_schemes` (after the switch at 301) | **130 / 130** |
| `setup_audit_3_final` (after iteration 700) | **130 / 130** |

The items explicitly required by the Section 6A brief, as read back from Fluent before iteration 1:

| Item | Read back | Same as medium |
|---|---|---|
| Air density / property model | `incompressible-ideal-gas`, M = 28.966; cₚ, μ, k piecewise-linear, all 8 points = Incropera A.4 | ✅ |
| **Inconel density** | **option `value`, 8190.0 kg/m³** — the corrected Section 5B value; the 5A 2719 kg/m³ error is not present | ✅ |
| Inconel k / cₚ | piecewise-linear, all 5 points = VDM 4127 | ✅ |
| Wall heat flux | `heated_outer_wall` Heat Flux 8000 W/m²; both ends Heat Flux 0 | ✅ |
| Inlet velocity / temperature | 23.5 m/s normal to boundary / 300 K; I = 0.044112, Dₕ = 0.02 m | ✅ |
| Outlet pressure | 0 Pa gauge; prevent reverse flow on | ✅ |
| Turbulence model | k-omega, `sst`, low-Re correction off | ✅ |
| Wall treatment | `wall_omega_treatment = correlation` | ✅ |
| Operating pressure, gravity, radiation, energy terms | 101 325 Pa, off, none, all off | ✅ |
| Interface | `Coupled` on both sides | ✅ |
| Mesh | 51,840 cells (Fluent `size_info`), min volume 2.049 × 10⁻¹⁰ m³ > 0 | 6A item |
| Zone names and IDs | as §3 | 6A item |
| Initialisation defaults | T 300 K, u = v = 0, w 23.5 m/s, p 0 Pa (k 1.6119, ω 1655.7 from the inlet, as medium) | 6A item |

**Audit-only dry runs before the production run.** The first audit-only run stopped, correctly,
before any iteration, with **3 failures, all in the new 6A checks themselves, none in the physics**:

1. The settings API lists no interior zones, so the expected-interior list was wrong. The
   interiors are now confirmed from Fluent's own replace output (zone IDs 4 and 5).
2. Fluent stores the monitor file name with doubled backslashes. The check now normalises path
   separators.
3. The initialisation-defaults key is `pressure`, not `gauge-pressure`.

All 59 medium-comparison rows passed in that run. The second audit-only run passed 130/130
(`Logs/auditonly_log.txt`, `Audit/auditonly_dryrun_setup_audit_1_presolve.txt`). The first run's
text log was overwritten by the second; its failures are recorded here.

## 3. Coarse mesh as read by Fluent

| Check | Result |
|---|---|
| File | `05_Meshing/Mesh_Coarse/coarse.msh`, 7,965,362 bytes, SHA-256 `5C0DE888DCAFB7FAB94E3ABD3CF24139EAE8527750E7137598971646D26D4A98`, written after the F-016 face-winding fix |
| Cells | 38,400 hexahedral (fluid) + 13,440 hexahedral (solid) = **51,840** |
| Faces | 113,600 interior-fluid · 38,176 interior-solid · 640 inlet · 640 outlet · 1,920 interface · 1,920 heated outer wall · 224 + 224 solid ends; `fluid_solid_interface-shadow` created by Fluent (conformal) |
| Nodes | 53,741 on read (55,629 across 4 partitions in `size_info`) |
| **Negative volumes** | **none**: minimum 2.049465 × 10⁻¹⁰ m³, maximum 1.056568 × 10⁻⁷ m³ |
| Total volume | 7.491468 × 10⁻⁴ m³ = 0.993587 × exact, the 32-gon planar ratio (Section 4 value reproduced) |
| **Zone names (IDs)** | `fluid_domain` (2) · `solid_domain` (3) · `interior-fluid` (4) · `interior-solid` (5) · `fluid_inlet` (6) · `fluid_outlet` (7) · `fluid_solid_interface` (8) · `heated_outer_wall` (9) · `solid_inlet_end` (10) · `solid_outlet_end` (11) · `fluid_solid_interface-shadow` (12) — identical to the medium |

## 4. Initialisation

This is the same philosophy as Section 5B: a **fresh standard initialisation** to a uniform field
(300 K, w = 23.5 m/s, 0 Pa gauge, k and ω from the inlet). The medium case was read without its
data, so no part of the medium solution could seed the coarse run. The comparison is therefore
between two independent solutions.

## 5. Convergence control (identical to Section 5B)

- **Stages:** 150 flow-only iterations, then 150 with energy at first order, then one switch to second order.
- **Evaluation:** chunks of 100 iterations, with a hard cap of 3000.
- **Plateau window:** 200 iterations, taken only from second-order rows.
- **Residual targets (NR-03):** below the NR-03 values.
- **Plateau criteria:**
  - T_out, T_solid_max, T_wall_max and T_outer_max drift < 0.1 K;
  - Δp and Q_interface drift < 0.1 %;
  - ṁ_out drift < 0.01 %.
- **Conservation criteria:** mass imbalance < 0.01 %, energy imbalance < 0.5 %.
- **Confirmation:** 100 more iterations after the first CONVERGED verdict.

| Iteration | Verdict |
|---|---|
| 400 | not evaluable (100 second-order rows) |
| 500 | **refused**: switch transient still in the window (T_out 0.62 K, T_solid_max 0.64 K, Δp 0.46 %, Q_interface 0.20 %, ṁ_out 0.024 %) |
| 600 | **converged** |
| 700 | **confirmed** |

The switch transient followed the same pattern as the medium run:
- the continuity residual jumped to 0.26 at iteration 301;
- T_out moved within 369.037–369.661 K and Δp within 435.86–437.85 Pa;
- T_fluid_min dipped 0.4 mK below 300 K at iteration 303.

All of it decayed before iteration 600.

**Startup:** T_solid_max rose monotonically through stage 2 (zero decreases in 150 steps) to
563.99 K. The interface heat never exceeded 602.2154 W in stage 2. The whole-history maximum,
564.667 K at iteration 385, is **0.015 K** above the final value. No overshoot occurred, and no
temperature left the property tables.

**First- to second-order change on the coarse mesh** (iteration 300 → 700):
- T_solid_max +0.67 K and T_wall_max +0.67 K;
- T_out +0.002 K;
- Δp −1.10 Pa (−0.25 %);
- y⁺_max −1.1 %.

The temperature change is about twice the medium's (+0.67 vs +0.34 K) and the Δp change 1.4 times
the medium's (−1.10 vs −0.81 Pa). A coarser mesh would be expected to be more sensitive to the
scheme order.

## 6. Conservation and limit checks

| Check | Result |
|---|---|
| Fluent mass flux report | in 0.0086312313, out −0.0086312313, net +1.04 × 10⁻¹⁷ kg/s |
| Fluent heat flux report | wall 602.21731, interface ±602.21731, inlet 16.051369, outlet −618.26868, ends −0, net −1.27 × 10⁻¹⁰ W |
| Heat by face integration vs Fluent report | 602.2173 W both; = 8000 × 32-gon outer area to 10⁻¹⁰ |
| Momentum balance on the exports | closes to −0.043 Pa (−0.010 %) |
| Limit / divergence / reversed-flow / NaN messages in the solver output | **0** |
| NaN / Inf in exports | **0** |
| Export row counts | 38,400 fluid, 13,440 solid: exactly the cell counts (`Audit/volume_export_check.json`) |

## 7. Post-processing and definitions

`Journals/postprocess_coarse.py` reuses the Section 5B post-processing code with only the
mesh-specific constants changed: polygon sides 48 → 32, slabs 90 → 60, file names. Every
definition is therefore the same:
- Δp (area-weighted static, inlet − outlet);
- mass-weighted outlet T and mixing-cup T;
- heat rates from Fluent's reports;
- y⁺ statistics;
- slab averages;
- the fully developed window (x/D 18–29);
- f = 8τ_w ρ_b / G².

Mid-span and z = 570 mm quantities are interpolated linearly between slab centres on both
meshes. The medium values in the comparison come from the medium's own saved results and
profiles, which were read only.

**Post-processing observations:**
- The cell-reconstructed slab mass flow is −1.96 % in the first slab, where the inlet profile is
  steepest, then +0.41 % and +0.11 % in the second and third slabs, and within 0.05 % from the
  fourth slab on. The medium figures are −1.36 % and +0.31 %, then within 0.03 %. The Fluent flux report is used for every
  mass-flow-dependent quantity.
- At the outflow boundary Fluent's outlet face temperature equals the adjacent cell's, so the
  last slab's bulk value is the outlet value on both meshes. The last slab sits at a different z
  on each mesh (595 vs 596.7 mm), so the slab-by-slab bulk difference there is not like-for-like
  (Figure C2b caption).
- Figure C10 was re-rendered once to move value labels that overlapped the axis labels. The
  numbers did not change.

## 8. Not done in this phase, by instruction

- The fine mesh was not solved.
- No mesh-independence conclusion, GCI or extrapolation has been made.
- No final mesh has been selected.
- No Mechanical, parametric study or report work has been done.
- The medium baseline and the `PROJECT_STATE.md` history are unchanged; a new section is appended for this phase.
