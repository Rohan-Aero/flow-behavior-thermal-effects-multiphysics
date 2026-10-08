# FLUENT_SETUP_NOTES.md — Section 5A: Fluent setup, physics and diagnostic test solve

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems
**Phase:** Section 5A — baseline case construction and verification
**Date:** 2026-09-19
**Solver:** ANSYS Fluent 2026 R1 (v261), `3ddp`, batch, 4-way parallel

> **RE-ANALYSIS.** Every file here was created in 2026. Nothing is a recovered 2025
> artefact and no original measurement is reproduced. The test solve below is a
> **150-iteration diagnostic, not a converged result**, and must never be quoted as one.

---

## 1. Headline status

| Item | Status |
|---|---|
| Fluent launches, reads the mesh, recognises every zone | ✅ |
| Student licence permits a real solver run, 4-way parallel | ✅ (banner only, no restriction hit) |
| Zero negative-volume cells | ✅ |
| Conjugate interface genuinely coupled | ✅ (through-wall ΔT = 6.86 K, not zero) |
| Heat flux applied exactly once | ✅ (audited: every other wall is Coupled or zero-flux) |
| 150-iteration test: stable, monotonic, no NaN or divergence | ✅ |
| Converged | ❌ **NO — and not claimed** |
| y⁺ achieved | ⚠ preliminary 0.59; **not claimed** (item 15) |

---

## 2. Version and licence — recorded verbatim

Fluent 2026 R1, launched as
`fluent 3ddp -g -py -t4 -i Journals/setup_baseline.py`.

The only licence text Fluent emitted, on every run including the solver run:

```
This is a student version of ANSYS FLUENT. Usage of this product
license is limited to the terms and conditions specified in your ANSYS
license form, additional terms section.
```
```
Info: Your license enables 4-way parallel execution.
```

**That is a product banner, not a failure.** No restriction was hit: 159,840 cells were
read, set up, iterated 150 times on 4 cores, and written back out. The one licence
*error* seen anywhere in this project — `Unexpected license problem; exiting.` in
Section 4 — was traced to orphaned `fl_mpi2610` processes holding a checkout, not to a
model-size limit. Every driver script in this section kills stale Fluent processes
before launching for exactly that reason.

**Still open (T-008):** a 150-iteration diagnostic is not a full solve. Whether a
Student licence will carry the 500,580-cell fine mesh to convergence is untested.

---

## 3. How the case is built

Fluent 2026 R1 ships a **built-in Python console exposing the settings API**
(`solver.setup...`), plus `ansys.fluent.core 0.37.1` inside Fluent's own Python — even
though PyAnsys is absent from the system CPython. The case is therefore built by a
Python journal rather than a TUI prompt chain:

- `06_Fluent_CFD/Journals/setup_baseline.py` — the whole setup, in one auditable file.
- Every setting is applied through a `step()` wrapper that records success or failure;
  nothing can fail silently.
- Every string literal that Fluent might spell differently is chosen from
  `allowed_values()` **at runtime** and logged, rather than typed from memory.
- Section 9b of the script **reads 30 settings back out of Fluent** and compares them to
  what was intended. A mismatch is recorded as a failure, not glossed over.

Supporting files: `Journals/introspect.py`, `introspect2.py`, `probe3.py` (the API maps
that made the above possible), `Journals/run_setup.ps1` (driver), `Journals/plot_monitors.py`.

---

## 4. Mesh loaded

`../05_Meshing/Mesh_Medium/medium.msh` — the **post-face-winding-correction** medium
mesh selected in Section 4.

Zones exactly as Fluent reports them:

| Fluent zone name | Type | Role |
|---|---|---|
| `fluid_domain` | fluid cell zone | 116,640 cells |
| `solid_domain` | solid cell zone | 43,200 cells |
| `fluid_inlet` | velocity-inlet | |
| `fluid_outlet` | pressure-outlet | |
| `fluid_solid_interface` | wall | **the CHT interface, fluid side** |
| `fluid_solid_interface-shadow` | wall | the solid side, auto-created by Fluent |
| `heated_outer_wall` | wall | the only heat input |
| `solid_inlet_end` | wall | adiabatic |
| `solid_outlet_end` | wall | adiabatic |
| `interior-fluid`, `interior-solid` | interior | |

`/mesh/check` on load: **zero negative-volume cells**, min volume 9.051023e-11 m³,
total 7.518309e-04 m³ — identical to the Section 4 record.

**Naming note.** The Section 3/4 named selection `FLUID_WALL` and the Fluent zone
`fluid_solid_interface` are the *same surface*. The fluid's only lateral boundary is the
interface, so "no-slip on FLUID_WALL" is satisfied by the fluid side of the coupled wall
pair; there is no separate zone to set. Likewise `SOLID_INNER_INTERFACE` is
`fluid_solid_interface-shadow`.

---

## 5. Solver settings — and where each came from

| Setting | Value | Source |
|---|---|---|
| Solver type | **pressure-based** | Mach ≤ 0.075, incompressible-ideal-gas (A-005) |
| Time | **steady** | A-004 — all BCs time-invariant |
| Velocity formulation | **absolute** | no rotating frame |
| Operating pressure | **101 325 Pa** | frozen baseline `p_op` |
| Gravity | **OFF** | A-007 — Gr/Re² = 4.3 × 10⁻⁵ ≪ 0.1 |
| Energy equation | **ON** | the whole problem is heat transfer |
| Turbulence | **k-ω SST** | D-011 |
| Wall treatment | SST blended, `wall_omega_treatment = correlation` | default; wall-resolved mesh |
| Radiation | **off** | A-015 (flagged, F-007) and A-019 |

---

## 6. Materials

### Air — `fluid_domain`

| Property | Model | Source |
|---|---|---|
| Density | **incompressible ideal gas**, ρ = p_op/(R·T) | D-009, D-021 |
| Molecular weight | 28.966 kg/kmol (standard dry air) | see the density check below |
| cₚ | **piecewise-linear**, 8 points, 250–600 K | Incropera & DeWitt Table A.4 |
| μ | **piecewise-linear**, 8 points, 250–600 K | Incropera & DeWitt Table A.4 |
| k | **piecewise-linear**, 8 points, 250–600 K | Incropera & DeWitt Table A.4 |

Temperature-dependent cₚ, μ and k are used because the Section 2 analytical model was an
**axially marched** solution over the same table — constant properties would make the CFD
a different model, not the same one solved differently. Every point was written and then
**read back and compared** before the script continued.

> **Density check.** The CFD inlet mass flow is 8.662155 g/s. The mesh inlet is an
> inscribed 48-gon, area ratio 0.997147, so the implied density is
> 8.662155e-3 / (3.141593e-4 × 0.997147 × 23.5) = **1.176659 kg/m³**, against the frozen
> analytical 101 325/(287.058 × 300) = **1.176590 kg/m³**. Agreement to **+0.006 %**.
> D-021 exists because a textbook-table density would have been 1.3 % wrong; this is 200×
> smaller than that and can be ignored.

### Inconel 718 — `solid_domain`

Created as a new material `inconel-718` (Fluent's default `aluminum` is a placeholder
that the `.msh` carries, **not** a project decision — see F-021).

| Property | Model | Source |
|---|---|---|
| ρ | 8190 kg/m³ constant | Special Metals; does not enter a steady-state result |
| cₚ | **piecewise-linear**, 5 points, 293–673 K | VDM Alloy 718 Data Sheet 4127 |
| k | **piecewise-linear**, 5 points, 293–673 K (11.5 → 17.1 W/m·K) | VDM 4127 |

> **Deviation from the analytical model, declared (D-026).** Section 2 used a single
> k = 15.22 W/m·K evaluated at the exit-station wall temperature. The CFD uses the full
> temperature-dependent curve from the same datasheet. This is a refinement, not a change
> of baseline: the wall runs from ~300 K at inlet to ~560 K at exit, over which k varies
> by 32 %, and a 1-D single-station model had no way to represent that. At the exit
> temperature the curve returns 15.2 W/m·K — the frozen value, to 0.1 %.

---

## 7. Cell-zone assignment — verified in Fluent

| Zone | Material | Read back from Fluent |
|---|---|---|
| `fluid_domain` | air | ✅ `'air'` |
| `solid_domain` | inconel-718 | ✅ `'inconel-718'` |

---

## 8. Boundary conditions

| Zone | Condition | Value | Verified |
|---|---|---|---|
| `fluid_inlet` | velocity-inlet, magnitude normal to boundary | **23.5 m/s** | ✅ |
| | static temperature | **300 K** | ✅ |
| | turbulence: intensity + hydraulic diameter | **I = 4.411 %**, Dₕ = 0.020 m | ✅ |
| `fluid_outlet` | pressure-outlet | **0 Pa gauge** (= 101 325 Pa abs) | ✅ |
| | backflow total temperature | 300 K | ✅ |
| | backflow turbulence | I = 4.411 %, Dₕ = 0.020 m | ✅ |
| | prevent reverse flow | on | ✅ |
| `fluid_solid_interface` | wall, no-slip, **Coupled** | temperature *solved*, never imposed | ✅ |
| `fluid_solid_interface-shadow` | wall, **Coupled** | | ✅ |
| `heated_outer_wall` | wall, **Heat Flux** | **8000 W/m²** | ✅ |
| `solid_inlet_end` | wall, Heat Flux | **0** (adiabatic, A-011) | ✅ |
| `solid_outlet_end` | wall, Heat Flux | **0** (adiabatic, A-011) | ✅ |

**Turbulence intensity is new to this section** and is recorded as assumption **A-020**:
I = 0.16·Re⁻¹ᐟ⁸ = 0.16 × 29957⁻⁰·¹²⁵ = **4.411 %**, the standard fully-developed-pipe
estimate. It is `[ASSUMED]`. Its influence is confined to the first few diameters; the
correlation comparisons in Section 5B are taken at x/D > 18 (A-017), where the inlet
turbulence has been forgotten.

> The script also checks whether Fluent stores intensity as a fraction or a percentage by
> reading the shipped default (0.05) and matching its scale. A factor-of-100 error here
> would have been invisible and would have poisoned the near-wall solution.

### Heat-path audit — the flux is applied exactly once

Item 8 of the brief warns against double-counting. The script walks every wall and
records its thermal condition:

```
heated_outer_wall             condition=Heat Flux  flux=8000 W/m2   <- the only input
fluid_solid_interface         condition=Coupled    flux=None
fluid_solid_interface-shadow  condition=Coupled    flux=None
solid_inlet_end               condition=Heat Flux  flux=0
solid_outlet_end              condition=Heat Flux  flux=0
```

Any non-zero flux on a second wall would have been raised as `DOUBLE HEAT INPUT`. None was.

---

## 9. Numerical methods — conservative startup

| Setting | Startup value (this section) | Final value (Section 5B) |
|---|---|---|
| Pressure–velocity coupling | **Coupled** | Coupled |
| Pseudo-time method | on, `coupled_solver = global-time-step` (Fluent default) | to be tuned — see F-022 |
| Gradient | least-squares cell-based | same |
| Pressure | second-order | second-order |
| Momentum | **first-order upwind** | second-order upwind (NR-06) |
| Turbulent kinetic energy | **first-order upwind** | second-order upwind |
| Specific dissipation rate | **first-order upwind** | second-order upwind |
| Energy | **first-order upwind** | second-order upwind |

First order is a deliberate startup choice, not the answer. **NR-06 requires
second-order everywhere for the final solution**, and that switch belongs to Section 5B.

The explicit Courant number is **inactive** under the pseudo-time formulation — Fluent
governs the step through the pseudo-time time-scale factor instead. The script attempts
to set it, records that it is inactive, and does not pretend otherwise.

---

## 10. Initialisation

Standard initialisation, defaults computed from `fluid_inlet` and then explicitly forced:

```
temperature 300 K · x-velocity 0 · y-velocity 0 · z-velocity 23.5 m/s · gauge pressure 0 Pa
```

A uniform 300 K cold start for both fluid and solid — physically the state before the
heater is switched on. Nothing is initialised from a previous or future solution.

---

## 11. Monitors

Residuals for continuity, x/y/z-momentum, energy, k and ω, **plus fourteen physical
report definitions written to `Test_Run/s5a_monitors.out` every iteration**:

`mdot_in · mdot_out · mass_imbalance · q_heated_wall · q_interface · q_fluid_net ·
p_in · p_out · T_out_bulk · T_wall_max · T_solid_max · T_solid_mean · v_out_max · yplus_max`

Pressure drop is `p_in − p_out`, both of which are logged every iteration. A Fluent
`expression` report for Δp was also created but returns empty in this build, so the
derived difference is the number used and the expression report is not relied on.

Per NR-04, **convergence is not defined by residuals**: the physical monitors above are
the criterion, and they are still drifting.

---

## 12. Test solve — 150 iterations, diagnostic only

### Residual behaviour

| Equation | iteration 2 | iteration 150 | NR-03 target | met? |
|---|---|---|---|---|
| continuity | 1.000 | **3.279e-04** | 1e-4 | **no** |
| x-velocity | 1.62e-05 | 8.153e-10 | 1e-4 | yes |
| y-velocity | 1.59e-05 | 8.081e-10 | 1e-4 | yes |
| z-velocity | 1.19e-02 | 1.359e-07 | 1e-4 | yes |
| energy | 1.07e-04 | 2.782e-08 | 1e-6 | yes |
| k | 9.59e-01 | 2.232e-06 | 1e-4 | yes |
| ω | 4.89e-01 | 1.698e-05 | 1e-4 | yes |

Monotonic after the first few iterations, no oscillation, no stalling.

### Physical monitors at iteration 150

| Quantity | CFD @150 | Section 2 analytical | Difference | Expected band |
|---|---|---|---|---|
| Inlet mass flow | **8.662155 g/s** | 8.6866 g/s | −0.281 % | — |
| Mass imbalance | 1.348e-08 kg/s | 0 | 1.6e-04 % of ṁ | — |
| Q into heated wall | **602.7552 W** | 603.186 W | **−0.071 %** | 600–606 W ✅ |
| Q across the interface | 602.7762 W | — | — | — |
| Q out with the air | 603.0718 W | — | — | — |
| Energy closure | −0.317 W | 0 | 0.053 % of input | — |
| Δp = p_in − p_out | **438.935 Pa** | 441.5 Pa | −0.58 % | 375–510 Pa ✅ |
| Outlet bulk temperature | **368.969 K** | 368.85 K | **+0.032 %** | 365–373 K ✅ |
| Max wetted-wall temperature | 555.054 K | 574.4 K (exit) | −3.37 % | 534–583 K ✅ |
| Max solid temperature | 561.915 K | — | — | — |
| Volume-mean solid temperature | 525.171 K | 554.7 K | *different quantity* | — |
| **Through-wall ΔT** | **6.861 K** | — | — | **6.6–8.0 K ✅** |
| Max outlet velocity | 34.953 m/s | 28.89 m/s bulk | centreline/bulk = 1.21 | typical ✅ |
| Max y⁺ | **0.5916** | — | **PRELIMINARY** | ≤ 1 |

Figure: `Test_Run/s5a_test_diagnostics.png`. Raw table: `Test_Run/s5a_test_summary.txt`.

### The three checks that actually matter

1. **Heat rate 602.755 W vs 603.186 W analytical.** The difference is not solver error.
   The mesh represents the cylinder as an inscribed 48-sided prism, whose lateral area
   ratio is sin(π/48)/(π/48) = 0.999286 — i.e. **−0.0714 %**. The CFD is low by
   **−0.0714 %**. They agree to six figures. The boundary condition is applied correctly
   and the deficit is purely geometric faceting.
2. **Through-wall ΔT = 6.861 K, inside the 6.6–8.0 K band.** PROJECT_STATE §6 names
   this as the test of whether the conjugate interface is genuinely coupled: a value
   collapsing to zero would mean it is not. It does not.
3. **Outlet bulk temperature 368.969 K vs 368.85 K, +0.032 %.** This is the
   conservation-only quantity (Q = ṁcₚΔT) that ENGINEERING_THEORY identifies as
   independent of the turbulence model — so it converges first and hardest. It has.

### Why this is not convergence

Continuity is 3.3× above target and the temperatures are still drifting
(T_out_bulk fell 0.006 K over the last two iterations; T_solid_mean is still falling).
The solid has the longest time constant in the problem and has not settled. NR-04
requires < 0.1 K drift in outlet bulk temperature — close, but the solid field behind it
is not there yet.

---

## 13. Problems found, and what was done

| # | Problem | Resolution |
|---|---|---|
| a | **Batch hang at `OK to overwrite? [cancel]`** — indistinguishable from a hung solver | `file.batch_options.confirm_overwrite = False`, and the driver deletes every output file before launching |
| b | Setting `air.density.option` raised `api-set-var: the object is not active` **while succeeding** | Option setters now verify by read-back and ignore the spurious exception |
| c | Writing a scalar `.value` onto `incompressible-ideal-gas` (which has no scalar) raised the same error | `set_prop` only writes a value when there is one to write |
| d | Piecewise-linear data rejected in three plausible formats | Read the shipped default state: Fluent wants `[{'item': T, 'value': v}, …]`. All 17 points now written **and read back and compared** |
| e | `density.option = "constant"` silently fell back — the allowed name is `"value"`, so Inconel kept aluminium's 2719 kg/m³ | Caught by the verification pass as `MISMATCH inconel density got 2719 expected 8190`, then fixed |
| f | Some leaves are compound (`.value`), some are plain reals; `turbulent_intensity` is the latter | Generic `setv()` helper tries both and verifies |
| g | Monitor file silently not written on the first attempt | `frequency_of='iteration'`, `active=True` set explicitly, and a post-run check that **fails loudly** if the file is absent |
| h | Fluent `expression` report for Δp computes empty in this build | Δp taken as `p_in − p_out`, both logged every iteration |
| i | Explicit Courant number inactive under pseudo-time | Recorded as expected behaviour, not forced |

None of these changed a physical input. Items (b)–(f) are exactly why the verification
pass exists: (e) in particular would have put the wrong solid density into the case with
no error message at all.

### ⚠ F-022 — startup temperature overshoot

The solid temperature **overshoots to 761 K at iteration 35 — 199 K above the value it
settles to (562 K)** — before decaying smoothly back. The interface heat rate peaks at
641.5 W at iteration 38 against a steady 603 W. Δp peaks near 930 Pa in the first few
iterations.

This is **not divergence and not an oscillation**: it is a single smooth excursion that
decays monotonically, and by iteration 100 everything is settled. The cause is the
pseudo-time scaling — a cold-initialised Inconel wall absorbs the 8 kW/m² far faster in
pseudo-time than the air can carry it away, so the solid runs hot before the fluid
catches up.

It does not affect the steady answer, but it is recorded because:
- 761 K is outside the 293–673 K range of the tabulated Inconel property curves, so the
  properties were **extrapolated** during the transient. Harmless here (the end state is
  inside the range) but it would not be if a property curve turned over.
- On the fine mesh, or with second-order discretisation, a larger overshoot could trip a
  temperature limiter.

**Action for Section 5B:** set an explicit solid time-scale factor (or run the first
~100 iterations at a reduced pseudo-time scale) so the overshoot is suppressed rather
than merely survived. Tracked as **T-020**.

---

## 14. y⁺ — not claimed

Fluent reports **max y⁺ = 0.5916** on the fluid/solid interface at iteration 150, and the
monitor has been flat at that value since about iteration 20.

**This is preliminary.** It comes from a solution that has not converged, at first-order
momentum discretisation, and wall shear is precisely the quantity that will change when
second-order is switched on. The Section 1 target of y⁺ ≤ 1 is *indicated* but is **not
declared met**. T-010 stays open until a converged, second-order solution is in hand.

---

## 15. Files produced

```
06_Fluent_CFD/
├── FLUENT_SETUP_NOTES.md          ← this file
├── Baseline_Setup/
│   └── baseline_setup.cas.h5      the fully configured case, BEFORE any iteration
├── Journals/
│   ├── setup_baseline.py          the whole setup + test solve, one auditable file
│   ├── introspect.py, introspect2.py, probe3.py   API maps for this Fluent build
│   ├── plot_monitors.py           diagnostics figure + summary table
│   ├── run_setup.ps1, run_fluent.ps1, scan_test.ps1, tidy.ps1
├── Test_Run/
│   ├── test_150iters.cas.h5 / .dat.h5    case + data after the diagnostic solve
│   ├── s5a_monitors.out           14 quantities × 150 iterations
│   ├── s5a_test_diagnostics.png   six-panel diagnostic figure
│   └── s5a_test_summary.txt       final-iteration comparison table
└── Logs/
    ├── setup_log_150.txt          every setup action and its outcome
    ├── setup_summary_150.json     machine-readable settings + verification + monitors
    ├── setup_transcript_150.trn   Fluent's own transcript
    ├── test150_stdout.txt         full solver output incl. residual history
    ├── introspect*_dump.txt, probe3_dump.txt
    └── Fluent_raw/                raw .trn and cleanup scripts
```

---

## 16. State at the end of Section 5A

**Ready for the full baseline solve.** The case is built, every setting has been read
back out of Fluent and checked, the physics chain behaves correctly, and 150 iterations
run cleanly with no numerical trouble.

Before the Section 5B production run:
1. Switch momentum, k, ω and energy to **second-order upwind** (NR-06).
2. Address the pseudo-time startup overshoot (**T-020**, F-022).
3. Run to the NR-03 residual targets **and** the NR-04 physical-plateau criterion.
4. Then, and only then, assess y⁺ (T-010) and extract Nu and f at x/D > 18 (T-012).

**Not done and not claimed in this section:** convergence, mesh independence, y⁺
verification, final CFD results, any thermal or structural analysis.

---

## 17. Correction notes added in Section 5B (2026-09-23)

1. **Outlet backflow (§8) — over-stated.** The rows "backflow total temperature 300 K ✅" and
   "backflow turbulence I = 4.411 %, Dₕ = 0.020 m ✅" claim a verification that did not
   happen. With `prevent_reverse_flow = True`, Fluent 2026 R1's settings API reports the
   outlet's backflow thermal and turbulence branches as **inactive** and their values cannot
   be read back (`Journals/probe_backflow.py`, `Logs/probe_bf_stdout.txt`). They were not
   verified, and they play no part in the solution: the converged Section 5B outlet has
   **zero** backflow faces. The Section 5B audit checks `prevent_reverse_flow == True` and
   records the backflow branch as inactive instead.
2. **Inconel density (§13 e) — scope clarified.** The 2719 kg/m³ fallback occurred in an early
   dry run only. Both logged setup runs that produced the saved case read back
   **8190.0 kg/m³** (`Logs/setup_log_0.txt`, `Logs/setup_log_150.txt`), so the 5A 150-iteration
   test ran with the correct density. Section 5B re-asserted and read it back again (8190.0).
3. **§16 items 1–4 are done** in Section 5B: second-order schemes (read back), startup
   overshoot removed by **staged equation activation** (flow + turbulence first, then energy —
   no change to pseudo-time, relaxation or limits; overshoot 0.006 K), NR-03 + NR-04
   convergence at iteration 600 confirmed at 700, y⁺ and fully developed Nu/f extracted.
   See `Baseline/CFD_BASELINE_RESULTS.md` and `Baseline/CFD_BASELINE_AUDIT.md`.
4. **The diagnostic numbers in this file are superseded.** The 150-iteration values in this file were a
   first-order, unconverged diagnostic. The converged baseline values are in
   `Baseline/CFD_BASELINE_RESULTS.md`; nothing in this file should be quoted as a result.

