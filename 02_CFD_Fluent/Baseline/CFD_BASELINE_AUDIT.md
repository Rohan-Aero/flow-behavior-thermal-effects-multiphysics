# CFD Baseline Audit — Section 5B

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems
**Date:** 2026-09-23 · ANSYS Fluent 2026 R1 (v261), `3ddp -g -py -t4`, batch
**RE-ANALYSIS 2026 — this audit describes newly generated runs, not recovered originals.**

This file records **how** the baseline was produced and checked: what was corrected before
solving, what was read back from Fluent, how convergence was judged, what went wrong on the
way and how it was caught. The results themselves are in `CFD_BASELINE_RESULTS.md`.

---

## 1. Mandatory pre-solve corrections

### A — Inconel 718 density, verified by reading it back from Fluent

| | |
|---|---|
| History | F-023: in an early Section 5A dry run, `density.option = "constant"` silently fell back and left aluminium's 2719 kg/m³ in the solid. The 5A verification pass caught it and the option was corrected to `"value"`. The 5A setup logs that produced the saved case (`Logs/setup_log_0.txt`, `setup_log_150.txt`) both read back **8190.0** — the 5A 150-iteration test therefore ran with the correct density. |
| Action in 5B | `solve_baseline.py::fix_density()` re-asserts `option = "value"`, `value = 8190`, then reads both back and **raises** (stopping the run) if either differs. |
| Read-back | `option = 'value'`, `value = 8190.0 kg/m³` (`Logs/baseline_log.txt`: *"1A Inconel 718 density = 8190 kg/m3 (read back)"*) |
| Re-checked | in all three setup audits (items "Inconel density option" and "Inconel density [kg/m3]") and in the startup trial |

Density does not enter a steady conduction solution, but it will enter any transient and the
Section 6 mass, so it was fixed at source rather than argued away.

### B — Second-order discretisation (NR-06)

| Equation | Section 5A | Section 5B final |
|---|---|---|
| Pressure | second-order | second-order |
| Momentum | first-order upwind | **second-order upwind** |
| k | first-order upwind | **second-order upwind** |
| ω | first-order upwind | **second-order upwind** |
| Energy | first-order upwind | **second-order upwind** |

The switch was made once, at iteration 301, and each scheme was read back immediately
(`Logs/baseline_log.txt`, "STAGE 3 scheme …") and again in audits 2 and 3. Convergence was only
evaluated on iterations run entirely at second order (§4).

### C — The Section 5A startup overshoot (F-022): smallest defensible intervention

**The problem.** In 5A, flow and energy were solved together from a cold start. The 5A
diagnosis (F-022) was that the cold Inconel absorbed 8 kW/m² faster in pseudo-time than the
air — whose velocity and turbulence fields were themselves still developing — could remove it.
The solid peaked at **761 K (iteration 35)**, 199 K above where it settled, and outside the
293–673 K property table, so k and cₚ were extrapolated during that transient. The trial below
supports that diagnosis: with the flow developed first, the excursion disappears.

**Options considered, least invasive first.** Clipping via solution limits was rejected
outright — it hides the symptom and alters the path. Changing boundary conditions was not
allowed. That left, in increasing order of intervention:

1. **Staged equation activation** — solve flow and turbulence first, then switch energy on.
   Changes no model, property, boundary condition, scheme, relaxation factor or time scale;
   only the order in which equations are switched on. Standard CHT practice.
2. Solid pseudo-time scale factor (`time_solid_scale_factor`).
3. Energy under-relaxation / smaller pseudo-time step.

**Trial** (`Journals/startup_trial.py`, `Logs/trial_A_log.txt`, `Monitors/trial_A_result.json`):
option 1 alone — flow-only 120 iterations, then energy 150 iterations, solid time-scale factor
left at its default 1.0. Result: T_solid_max rose monotonically to **561.78 K at the last
iteration; overshoot 0.00 K**; interface heat never exceeded its final 602.75 W. Option 1 was
therefore sufficient and options 2–3 were not tried.

**Exactly what changed in the production run:**
`solver.solution.controls.equations["temperature"] = False` for iterations 1–150, then `True`.
Nothing else. The pseudo-time settings (automatic, conservative length scale, factor 1.0),
relaxation factors and solution limits are Fluent defaults, identical to 5A, and were read
back in every audit. The production run used 150 flow-only iterations (not the trial's 120)
for margin; by iteration 150 the flow-only residuals were ≤ 1.2 × 10⁻⁶ and Δp had plateaued at
259.11 Pa (isothermal, first-order).

**Evidence it worked in the official run** (`Monitors/baseline_monitors.csv`):
T_solid_max rose monotonically through stage 2 (150 steps, zero decreases) from 300 K to
561.78 K; interface heat rate never exceeded 602.753 W in stage 2; in stage 3 the history
maximum is 562.133 K (iteration 393), **0.006 K** above the final 562.127 K. No temperature
left the property tables at any iteration (fluid 299.998–553.42 K, solid 300.0–562.13 K).

## 2. Continuation or re-initialisation — **B: re-initialised**

The official run did **not** continue from the Section 5A data. It read the audited setup case
(`Baseline_Setup/baseline_setup.cas.h5`), applied correction A, added the extra report
definitions, and started from a fresh standard initialisation (300 K, w = 23.5 m/s,
0 Pa gauge). Reasons: the 5A data carried the extrapolated-property excursion in its history
and was first-order; starting fresh makes the 5B run self-contained, and lets the startup
fix be demonstrated rather than assumed. A steady solution does not depend on its starting
point, so this is a choice of cleanliness and evidence, not of answer.

## 3. Setup audit — every value read back from Fluent

`solve_baseline.py::audit()` reads **59 settings** back out of Fluent and compares each with
the intended value (solver, models, both materials including every piecewise-linear point,
zone materials, every boundary condition, interface coupling, schemes, pseudo-time settings,
relaxation, limits, active equations). Any mismatch raises and stops the run.

| Audit | When | Result |
|---|---|---|
| `setup_audit_1_presolve` | before iteration 1 | **59 / 59** — schemes first-order as intended for the startup |
| `setup_audit_2_final_schemes` | after the switch at 301 | **59 / 59** — only the four scheme rows differ from audit 1 |
| `setup_audit_3_final` | after iteration 700 | **59 / 59** — identical to audit 2 |

Before the official run the same audit was run in **audit-only mode** (`S5B_AUDIT_ONLY`,
no iterations). It stopped the run twice, correctly, before any iteration:

1. **15 failures** — all numeric comparisons failed with `NameError: _close`, because
   `from s5_common import *` does not import underscore names. A bug in the audit, not the
   case. Fixed by importing `_close` explicitly.
2. **1 failure** — "outlet backflow total temperature" could not be read. A probe
   (`Journals/probe_backflow.py`, `Logs/probe_bf_stdout.txt`) showed the settings API
   reports the outlet's backflow thermal and turbulence branches as **inactive while
   `prevent_reverse_flow = True`**. The audit now checks `prevent_reverse_flow == True` and
   records the backflow branch as inactive. This corrects Section 5A's claim that backflow
   temperature and turbulence were set and verified (note appended to `FLUENT_SETUP_NOTES.md`).
   It has no effect on the solution: the converged outlet has **zero** backflow faces.

The third audit-only run passed 59/59 (`Logs/auditonly_log.txt`; the two failing audit-only
logs were overwritten by it — the failures are recorded here and in the session record).

## 4. Convergence control

| Parameter | Value |
|---|---|
| Iteration chunk | 100 |
| Hard cap | 3000 second-order iterations (not approached) |
| Evaluation window | last 200 iterations, **restricted to stage-3 (second-order) rows** |
| Residual criteria (NR-03) | energy < 1e-6; continuity, momentum, k, ω < 1e-4 |
| Physical plateau (NR-04 and additions) | ΔT over window < 0.1 K for T_out, T_solid_max, T_wall_max, T_outer_max; relative drift < 0.1 % for Δp and Q_interface, < 0.01 % for ṁ_out |
| Conservation | mass imbalance < 0.01 %, energy imbalance < 0.5 % |
| Confirmation | after the first CONVERGED verdict, 100 more iterations; every criterion must still hold |

Verdicts: 400 not evaluable (window not yet inside stage 3) · 500 **not converged** (window
contained the scheme-switch transient: T_out drift 0.42 K) · 600 **converged** · 700
**confirmed**. The 500 failure is the check working as intended: had the window included
first-order rows, iteration 500 would have been declared converged on a mixed history.

The scheme switch produced a brief transient — continuity residual 0.22 at iteration 301,
T_out between 368.877 and 369.300 K, Δp between 437.15 and 438.62 Pa, T_fluid_min 2 mK below
300 K at iteration 303 — all decayed before iteration 500 and none reached a limit.

Residual history: `residual.write` produces an empty file in batch mode in this build (seen in
the startup trial), so residuals were parsed from the solver's own console output
(`Logs/baseline_stdout.txt` → `Monitors/residual_history.csv`). That file has 705 rows for 700
iterations: the console repeats the last residual line at five of the chunk/stage boundaries;
the duplicates are identical and harmless.

## 5. Conservation (Fluent's own reports, `Audit/fluent_flux_*.txt`)

| | In | Out | Net | Relative |
|---|---|---|---|---|
| Mass [kg/s] | 0.0086621551 | −0.0086621551 | −6.07 × 10⁻¹⁷ | 7.0 × 10⁻¹³ % |
| Energy [W] | 602.75524 (heated wall) + 16.106809 (inlet enthalpy flux) | −618.86205 (outlet) | −1.84 × 10⁻¹⁰ | 3.1 × 10⁻¹¹ % |

Interface and shadow each carry ±602.75524 W; both solid end faces carry −0 W. Enthalpy fluxes
are relative to Fluent's 298.15 K reference, so only their difference is physical.

## 6. Temperature-range, clipping and limiter scan

| Check | Method | Result |
|---|---|---|
| Solver limit / divergence messages | scan of `baseline_stdout.txt` for "temperature limited", "viscosity limited", "divergence", "floating point", "reversed flow", "nan" — licence banner and echoed script comments filtered out (the first unfiltered scan produced false positives from exactly those) | **0** |
| NaN / Inf in exported fields | count over all seven exports | **0** |
| Final and historical temperatures vs property tables | min/max from exports and every monitor row | inside both tables at every iteration |
| Section 5A 761 K excursion | kept in the 5A record (F-022); not in this solution (§2) | — |

## 7. Export integrity

The solve journal's ASCII export of the two cell zones produced **boundary-face** data (6,912
and 9,600 rows), not cell data: in this build a surface created from a cell zone is the zone's
boundary. It was caught by a row-count check against the known cell counts before any figure
used it. `Journals/export_volume.py` re-read the final case/data and exported cell-centre
values on **90 iso-z surfaces per zone at the slab centres**, giving exactly **116,640** fluid
and **43,200** solid rows (`Audit/volume_export_check.json`). The boundary-face files were
overwritten.

## 8. Post-processing checks

| Check | Result |
|---|---|
| Heat-flux sign convention | fixed per surface by comparing the face integral with Fluent's flux report |
| Heat by face integration vs Fluent report | 602.7552 W both (report printed as 602.75524 W) |
| Energy by enthalpy face re-analysis | 602.726 W (−0.005 %) — interpolation, not solver error |
| Momentum balance, (p_in − p_out)A vs F_wall + ΔM | closes to −0.197 Pa (−0.045 %) |
| F_wall from faces vs Fluent force report | equal to 4 × 10⁻¹¹ relative |
| Mixing-cup T_out vs energy-balance prediction on the faceted mesh | 368.993 vs 368.996 K |
| Slab mass flow reconstructed from cell centres | −1.36 % in the first slab, +0.31 % in the second, then small — cell-centre re-analysis error where the inlet profile is steepest. **Post-processing artefact**; Fluent's flux report (exact) is used for every mass-flow-dependent result |
| Slab selection | by slab index with tolerance 0.25·Δz (an early float-equality selection dropped slabs and crashed one figure — fixed) |
| Figure captions | checked against the plotted data; five captions that contradicted their figures were corrected before release |
| Comparison table | the "inner-wall temperature at exit station" row first compared the analytical value at z = 600 mm with the CFD value at z = 570 mm. Replaced by station-matched rows (z = 570 mm) plus a peak-to-peak PR-06 row; the h and through-wall rows were given station-matched companions |

## 9. Findings raised in this phase

| # | Finding | Severity | Status |
|---|---|---|---|
| F-028 | The first fluid cell is **≈ 12.1–12.2 µm only on the four O-grid axes (θ = 0/90/180/270°; 12.2 µm design, 12.13 µm from the cell nearest the axis)**, about **10.4 µm at the diagonals** (cell-centre distance 5.19–6.06 µm). The Section 4 notes state 12.2 µm uniformly. Super-ellipse geometry predicts a ratio 0.845; measured 0.856 | Low | Harmless (thinner, not thicker; y⁺ ≤ 0.59). Explains the geometric 15 % circumferential y⁺ variation against 0.078 % in wall shear. Correction note appended to `MESH_NOTES.md` |
| F-029 | Fully developed Darcy f = 0.02163 is **10.4 % below** Section 2's 0.02413 (PR-04 ±10 %: marginally not met) and 1.7 % below the EXPECTED_RESULTS lower bound 0.022 | Medium | Gas heating accounts for about 4 points (Petukhov (T_w/T_b)^−0.1). Remainder is SST model or mesh — to be settled by the mesh study, not re-interpreted |
| — | Backflow branch inactive under prevent-reverse-flow; 5A notes over-claimed its verification | Low | Corrected (§3) |

## 10. File inventory for this phase

| File | Role |
|---|---|
| `Journals/solve_baseline.py` | production solve: density fix, reports, three audits, staged startup, convergence loop, outputs |
| `Journals/s5_common.py` | shared helpers: logged steps, verified setters, read-back, report-file parser |
| `Journals/startup_trial.py` · `run_trial.ps1` | startup study (trial A) |
| `Journals/export_volume.py` | cell-centre volume export on iso-z surfaces |
| `Journals/postprocess_baseline.py` | every derived number, CSV, JSON and figure in `Baseline/`, `Profiles/`, `Figures/` |
| `Journals/run_baseline.ps1` · `launch_detached.ps1` · `peek.ps1` · `presolve_check.ps1` · `check_exports.ps1` · `organise_5b.ps1` | drivers and checks |
| `Journals/probe_backflow.py` · `introspect3.py` | API probes |
| `Logs/baseline_*.txt/.trn`, `auditonly_*`, `trial_A_*`, `export_volume_*`, `postprocess_log.txt` | complete run records |

**Reproduce:** `fluent 3ddp -g -py -t4 -i Journals/solve_baseline.py` (from `06_Fluent_CFD`),
then the same for `Journals/export_volume.py`, then run `Journals/postprocess_baseline.py`
with ANSYS's bundled CPython 3.10.

## 11. Not done in this phase, by instruction

Coarse and fine meshes not solved · no mesh-independence claim · no parametric study ·
no Mechanical / thermal-stress work · no report.
