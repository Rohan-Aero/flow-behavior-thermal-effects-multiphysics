# Section 12C — LS-DYNA nonlinear thermo-structural buckling: three-point imperfection sensitivity study

> **What this is.** This is an *additional* geometrically nonlinear LS-DYNA analysis, run as an extension of the internship
> project. It is **not** part of the original project results.
>
> **The original project / Mechanical results are unchanged:**
> - λ₁ = 1.10805, P_cr = 608.25 kN, LC2 load 548.94 kN;
> - final report, presentation, `MASTER_PROJECT_DATA.csv`, Fluent and Mechanical files: SHA-256 re-checked (§10).
>
> **What this is not:**
> - not experimental validation;
> - not a replacement for the Mechanical eigenvalue result;
> - not a statement of real-world structural adequacy.
>
> No value here is a factor of safety. λ is a load multiplier on the temperature rise (T − 300 K).
>
> **Scope.** A **three-point** imperfection sensitivity study: C1 = 0.1 mm, C3 = 0.6 mm, C5 = 1.2 mm. It is **not a full
> sweep**; the user reduced the scope on 2026-10-07.
> - The perfect-geometry run **C0** (0.0 mm) had already finished. It is reported only as a reference path.
> - C2 (0.3 mm), C4 (0.9 mm), N1 (step-size check) and C0b (bifurcation detection) were **not run**.
>
> **Supporting files.** `IMPERFECTION_SENSITIVITY.csv`, `MECHANICAL_vs_LSDYNA.csv`, `RESULTS_AUDIT_12C.md`,
> `LS_DYNA_FINAL_ENGINEERING_SYNTHESIS.md`, `plots/F1–F8`, `comparisons/`, `results/`, `runs/`.

## 1. Model and loading (unchanged from the validated 12B model)

| Item | 12C setting |
|---|---|
| Geometry, mesh, supports | 12B LC2 model (108,252 nodes, 23,400 ELFORM 23 20-node solids), LC2 supports; include files are hash-identical copies (`audit/model_copy_hashes.csv`) |
| Material | MAT_004 thermo-elastic with E(T), ν = 0.294, exact MPAMOD instantaneous-α curve. **Elastic only — no plasticity** |
| Temperature | Fluent `baseline_medium_final` field mapped in 12B (423.84–562.56 K), T_ref = 300 K. Load T(λ) = 300 K + λ·(T_Fluent − 300 K); the CFD and the field are unchanged |
| Solver | LS-DYNA R16.1 Student, SMP, double precision; implicit NSOLVR 12 (BFGS, large deformation) |
| Convergence | DCTOL 1e-4, ECTOL 1e-3, RCTOL 1e-4 (tighter than the defaults, never loosened) |
| Load steps | λ 0 → 1.0 in 40 steps (Δλ 0.025); 1.0 → 1.2 in 40 steps (Δλ 0.005, fine near instability); 1.2 → 1.3 in 10 steps (Δλ 0.01). Automatic step control was active but never cut a step |
| Imperfection | Validated mode 1 from the 12B G6 buckling run (`d3eigv`). Normalised to a maximum lateral nodal value of 1, then scaled by A. Correlation with the Mechanical mode 1: 0.9999999 (F1). These are **numerical sensitivity amplitudes, not tolerances** |

## 2. Runs

| Case | A [mm] | Status | λ reached | Run time | Notes |
|---|---|---|---|---|---|
| **C1** | 0.1 | **completed**, normal termination, EXIT 0 | 1.30 | 16:15 → 18:03 (108 min) | in-core |
| **C3** | 0.6 | **completed**, normal termination, EXIT 0 | 1.30 | 18:04 → 19:17 (73 min) | in-core |
| **C5** | 1.2 | **completed**, normal termination, EXIT 0 | 1.30 | 13:46 → 15:07 (81 min) | factorised out of core from step 11 (Warning 60120); affects run time only, results reproduced bit-for-bit (§9) |
| C0 (reference) | 0.0 | completed, normal termination, EXIT 0 | 1.30 | 15:08 → 16:14 (66 min) | finished before the scope change; reference only |
| C5 attempts 1–5 | 1.2 | stopped / incomplete; kept in `runs/C5_A1p2/attempt*` | — | — | see `RESULTS_AUDIT_12C.md` §2 |
| C2, C4, N1, C0b | — | **not run** (scope reduction) | — | — | `NOT_RUN.txt` in each folder |

All four completed runs:
- used 90 steps at the nominal step size;
- needed 2–5 equilibrium iterations per step;
- produced no error or negative-eigenvalue message.

## 3. Results at the LC2 temperature field (λ = 1) and at the end of the analysis (λ = 1.3)

N is the axial compression, i.e. the inlet-face reaction from `binout`.

| Quantity | C0 (ref., 0.0 mm) | **C1 (0.1 mm)** | **C3 (0.6 mm)** | **C5 (1.2 mm)** |
|---|---|---|---|---|
| N at λ = 1 [kN] | 553.25 | 552.17 | 531.19 | 503.46 |
| N at λ = 1 vs C0 | — | −0.19 % | −3.99 % | −9.00 % |
| Max lateral section translation at λ = 1 [mm] | < 1e-6 | 0.85 | 3.71 | 5.32 |
| Peak von Mises at λ = 1 [MPa] | 605.2 | 689.7 (+14 %) | 966.3 (+60 %) | 1103.7 (+82 %) |
| VM / S_y(T) at λ = 1 (elastic-validity indicator) | 0.578 | 0.659 | 0.923 | **1.055** |
| Max N reached, λ ≤ 1.3 [kN] | 720.69 (end of run; no instability) | **601.00 at λ = 1.185** (interior maximum) | 572.41 at λ = 1.3 (still rising) | 545.32 at λ = 1.3 (still rising) |
| N at λ = 1.3 [kN] | 720.69 | 598.95 | 572.41 | 545.32 |
| Max lateral section translation at λ = 1.3 [mm] | < 1e-6 | 10.04 | 10.60 | 11.02 |
| Additional relative end sway at λ = 1.3 [mm] | 0 | 19.96 | 21.09 | 21.93 |
| Max axial displacement (monitored surface) at λ = 1.3 [mm] | −0.14 | −1.17 | −1.23 | −1.28 |
| Mid-span radial displacement at λ = 1.3 [mm] | 0.110 | 0.092 | 0.089 | 0.085 |
| Max total displacement (monitored) at λ = 1.3 [mm] | 0.18 | 10.14 | 10.70 | 11.12 |
| Peak von Mises (nodal, end regions), λ ≤ 1.3 [MPa] | 787.5 | 1677.2 | 1706.8 | 1721.2 |
| Most compressive axial stress σ_z at λ = 1 / 1.3 [MPa] | −613 / −798 | −698 / −1695 | −976 / −1725 | −1115 / −1740 |
| Max VM / S_y(T), λ ≤ 1.3 | 0.758 | 1.623 | 1.652 | 1.666 |
| Equilibrium iterations per step (min / max / mean) | 2 / 2 / 2.0 | 2 / 5 / 3.43 | 2 / 5 / 3.67 | 2 / 5 / 3.77 |

**Temperatures at the critical locations** are the same in every case, because the load is the same scaled field:
- outer edge of the inlet face (nodes 18865 / 89494): 437.99 K at λ = 1, 479.39 K at λ = 1.3;
- mid-span outer surface: 539.26 K at λ = 1;
- outlet-face outer edge: 561.9–562.3 K at λ = 1.

The d3plot temperatures at λ = 1.3 agree between C1, C3 and C5 to 0.0 K.

**Energy (`glstat`).**
- External work is 0, because there is no applied force: the loading is thermal strain against the supports.
- LS-DYNA's internal energy is computed from total strain increments, so for this loading it is negative. Its values at
  λ = 1.3 are −912.6 (C0), −855.5 (C1), −827.8 (C3) and −795.7 J (C5).
- It changes monotonically and smoothly in every case.
- A balance of internal energy against external work is not a meaningful check here (audit §4).

**Stresses above S_y(T) are not physical.** The model is elastic only. Once VM / S_y(T) passes 1, the model is outside
its range of validity, so peak stresses of 1100–1720 MPa are indicators, not predicted stresses.

## 4. Load – lateral response, onset, maximum load, instability and post-instability trend

**Criteria.** They were defined before the results were read (`comparisons/analysis_12C.json`):

| Criterion | Definition |
|---|---|
| Onset of nonlinear response | First λ at which N of the imperfect case is more than 1 % below N of the perfect path (C0) at the same λ |
| Maximum attained load | Largest N in λ ≤ 1.3. It counts as an **interior maximum** (limit point) only if N later drops by more than 0.1 % |
| Characteristic (critical) load | Southwell plot: δ/N against δ, fitted over N ∈ [0.5, 0.95]·N_max on the rising branch. N_cr = 1 / slope. The intercept gives an estimate of the initial imperfection, w₀, as a consistency check |
| Instability point | An interior maximum of N, or for the perfect case a bifurcation flagged by the solver. If neither occurs, the result is *not identifiable as a limit point* and the Southwell load is the characteristic load |
| Elastic-validity indicator | Nodal VM / S_y(T) = 1, with S_y(T) from VDM 4127 at the local temperature. This is an indicator only; plasticity is not modelled |

| | C1 (0.1 mm) | C3 (0.6 mm) | C5 (1.2 mm) |
|---|---|---|---|
| Onset (N 1 % below perfect path) | λ = 1.070, N = 587.1 kN | λ = 0.825, N = 448.9 kN | λ = 0.375, N = 202.3 kN |
| Elastic-validity indicator reached | λ = 1.109, N = 597.3 kN | λ = 1.031, N = 541.7 kN | λ = 0.974, N = 495.5 kN |
| Maximum attained N | **601.0 kN at λ = 1.185, interior maximum** | 572.4 kN at λ = 1.3, no maximum | 545.3 kN at λ = 1.3, no maximum |
| Instability point | Interior maximum at λ = 1.185 (N = 601.0 kN). It is not a collapse (see trend) | not identifiable as a limit point within λ ≤ 1.3 | not identifiable as a limit point within λ ≤ 1.3 |
| Southwell N_cr (R²) | 612.3 kN (0.99997) | 611.1 kN (0.999999) | 607.7 kN (0.999996) |
| Southwell spread over 5 fit-window variants | 608.6 – 613.3 kN | 610.9 – 612.2 kN | 607.2 – 610.0 kN |
| Southwell w₀ estimate vs imposed end offset 2A | 0.181 / 0.2 mm | 1.111 / 1.2 mm | 2.196 / 2.4 mm |
| Post-instability / late trend | after the maximum, N falls slowly (−0.34 % by λ = 1.3) while sway grows almost linearly with λ | N approaches the critical load from below; sway grows almost linearly with λ | same as C3, further below |

**Interpretation (F3, F4, F8).**

- **Load path.** All three cases follow the classical response of an imperfect strut under deformation-controlled thermal
  loading. Lateral deflection grows from the start in proportion to the imperfection. N then flattens towards the critical
  load, and beyond it the excess thermal expansion is taken up by bowing at an almost constant N.
- **Same curve after normalising.** Plotted as N / P_cr against δ / w₀ (F3, right), the three curves collapse onto one
  curve. This is the behaviour expected for amplification of a single global mode.
- **C1 maximum.**
  - Only the smallest imperfection, C1, comes close enough to the critical load to show a maximum: 601.0 kN, 98.8 % of the
    Mechanical P_cr.
  - The slow decline afterwards matches the fall in the heated tube's own critical load. As λ grows, the scaled
    temperatures rise and E(T) falls.
  - A stiffness-weighted average of E(T) over the mesh gives P_cr ≈ 608.2 kN at λ = 1, 603.5 kN at λ = 1.108, 599.9 kN at
    λ = 1.185 and 594.5 kN at λ = 1.3.
  - This is an estimate only, and it ignores the kinematic and element offsets of 12B. It shows that the C1 maximum is the
    heated-state critical load being reached, not a collapse.
- **No sudden failure.** No case shows snap-through, a sudden loss of load, a change of mode or a secondary bifurcation.

## 5. Critical location, mid-span, global vs local

- **Peak stress location.** In every case and at every λ, the peak nodal von Mises stress is on the **outer edge of the
  inlet face** (r = 20 mm, z = 0; nodes 89494 / 89468 / 18865, all 437.99 K at λ = 1).
  - In C0 the peak node is 18865, as in Mechanical 7B and 12B G5.
  - In the imperfect cases the peak moves around the same ring to the side where bending adds to compression, node 89494.
- **End faces vs mid-span.** At λ = 1.3 the highest element-centroid stress is in the element layer at the inlet face:
  1619 / 1646 / 1658 MPa for C1 / C3 / C5. The outlet-face layer is next, at 1582 / 1607 / 1619 MPa. The **mid-span**
  stress is much lower, at 666 / 639 / 612 MPa.
  - The bending moment of the guided sway mode is zero at mid-span. Mid-span therefore carries only the axial and thermal
    components, and is **not** a critical location.
  - These figures are d3plot element-centroid values, not nodal values; `eloutdet` covers only the end regions (audit §4).
- **Global mode, no local mode.** The response is a **global guided sway** in all three cases (F5, `comparisons/crit_check_12C.json`):
  - mid-span lateral movement is 0.13–0.18 % of the end translation;
  - the ends move in opposite directions;
  - the sway direction is −6.14°, the same as the imperfection direction (−6.11°);
  - ovalisation is ≤ 0.041 mm, against 10–11 mm of end translation.

  There is no ovalisation, shell-type or local mode.

## 6. Comparison with Mechanical (original project)

Mechanical reference values: λ₁ = 1.108, P_cr = 608.25 kN, LC2 load 548.94 kN. Full table: `MECHANICAL_vs_LSDYNA.csv`.

| LS-DYNA quantity (extension) | Value [kN] | Ratio to Mechanical P_cr | Difference |
|---|---|---|---|
| Linear eigenvalue P_cr (12B G6, λ₁ = 1.1095) | 609.03 | 1.0013 | +0.13 % |
| Max attained N, C1 (interior maximum) | 601.00 | 0.9881 | −1.19 % |
| Max attained N, C3 (at λ = 1.3, still rising) | 572.41 | 0.9411 | −5.89 % |
| Max attained N, C5 (at λ = 1.3, still rising) | 545.32 | 0.8965 | −10.35 % |
| Southwell N_cr, C1 / C3 / C5 | 612.3 / 611.1 / 607.7 | 1.0067 / 1.0046 / 0.9990 | +0.67 / +0.46 / −0.10 % |
| N at λ = 1, perfect reference C0, against the LC2 load 548.94 kN | 553.25 | — | +0.79 % against the Mechanical LC2 reaction (large-deformation kinematics, 12B D-105) |

**Reading.**

- **The critical load agrees.** The nonlinear analysis places the critical load of the imperfect structures at
  607.7–612.3 kN. This is −0.1 % to +0.7 % of the Mechanical eigenvalue load, with Southwell fit-window spread up to
  ±2.4 kN. **The magnitude of the Mechanical λ₁ is therefore supported, not replaced.**
- **The response is not linear.** The analysis also shows what the eigenvalue cannot:
  - the response is not "straight until 608 kN";
  - with these numerical imperfections, lateral deflection and stresses grow well before the critical load;
  - the maximum force actually transmitted within λ ≤ 1.3 ranges from 98.8 % down to 89.7 % of P_cr.
- **λ₁ is a load multiplier only.** It is not a factor of safety. No 12C value is one either.

## 7. Imperfection-sensitivity table (three-point study)

| Imperfection | Instability / Characteristic Load | Max Lateral Displacement | Max von Mises | Key Observation |
|---|---|---|---|---|
| 0.1 mm (C1) | Interior maximum **601.0 kN** at λ = 1.185. Southwell 612.3 kN | 10.04 mm at λ = 1.3 (0.85 mm at λ = 1) | 1677 MPa at λ = 1.3 (690 MPa at λ = 1) | Stays near the perfect path until λ ≈ 1.07, then sways rapidly. Shallow maximum, then slow decline (E(T) falling). VM / S_y = 1 at λ = 1.109 |
| 0.6 mm (C3) | **Not identifiable** as a limit point within λ ≤ 1.3. Southwell 611.1 kN; largest attained N 572.4 kN | 10.60 mm at λ = 1.3 (3.71 mm at λ = 1) | 1707 MPa at λ = 1.3 (966 MPa at λ = 1) | Departs from the perfect path at λ = 0.825. N still rising at λ = 1.3. VM / S_y = 1 at λ = 1.031 |
| 1.2 mm (C5) | **Not identifiable** as a limit point within λ ≤ 1.3. Southwell 607.7 kN; largest attained N 545.3 kN | 11.02 mm at λ = 1.3 (5.32 mm at λ = 1) | 1721 MPa at λ = 1.3 (1104 MPa at λ = 1) | Departs at λ = 0.375. VM / S_y(T) **exceeds 1 already at λ = 1** (1.055, at λ = 0.974). N still rising at λ = 1.3 |
| 0.0 mm (C0, reference only) | **Not identifiable.** No bifurcation flagged (NEGEV = 2 ignores negative eigenvalues). The path stays straight past P_cr to 720.7 kN at λ = 1.3 | < 1e-6 mm (output resolution) | 787.5 MPa at λ = 1.3 (605.2 MPa at λ = 1, = 12B G5) | Shows that a perfect model on a Newton path does not buckle by itself. Not a physical capacity |

**Effect of imperfection amplitude (three points only; trends between the points are not resolved).**

| Increasing A from 0.1 to 1.2 mm | Effect |
|---|---|
| Onset of nonlinear response | moves earlier: λ 1.07 → 0.83 → 0.38 |
| N at λ = 1 | falls: −0.2 % → −4.0 % → −9.0 % against the perfect path |
| Peak VM at λ = 1 | rises: +14 % → +60 % → +82 % |
| Elastic-validity indicator | reached earlier: λ 1.109 → 1.031 → 0.974 |
| Maximum attained N | falls: 601.0 → 572.4 → 545.3 kN |
| Critical (Southwell) load | essentially **independent** of A: 612.3 / 611.1 / 607.7 kN |
| Lateral displacement at λ = 1.3 | similar in all cases (10.0–11.0 mm). The post-critical sway is set by the excess thermal expansion, not by A |

## 8. Nonlinear-response classification

**Stable, symmetric, imperfection-amplified bending of a thermally loaded, end-restrained column in a single global
guided-sway mode.**

- **Mode.** Global, cos(πz/L), the same as Mechanical mode 1.
- **Stability.** Stable: no snap-through, no collapse, no limit point except the shallow C1 maximum, which follows the
  falling critical load of the heated state.
- **Imperfection sensitivity.**
  - The *load–deflection* response is imperfection-sensitive: onset, deflection and stress at a given λ depend strongly on A.
  - The *critical load* is imperfection-insensitive: the Southwell estimates are within 1 % of each other and of the
    Mechanical value.
- **Elastic validity.** The elastic model is valid up to the indicator values above. Response beyond those points would
  need an elastic-plastic model, which is outside 12C by instruction.

## 9. Mesh and numerical checks (small and targeted; mesh independence is **not** claimed)

| Check | Result |
|---|---|
| Reproducibility | The completed C5 run and the interrupted C5 attempt 2 (3 Oct, in-core) are **bit-identical** over the shared 68 output points (λ ≤ 1.135): sway, N, VM, IE, lateral. Out-of-core factorisation and launch history do not affect results (`comparisons/C5_reproducibility_attempt2_vs_final.csv`) |
| Baseline consistency | C0 at λ = 1: N = 553.246 kN and peak VM 605.2 MPa at node 18865, against 12B G5 553.247 kN / 605.160 MPa |
| Southwell consistency | The back-calculated w₀ is 91–93 % of the imposed end offset 2A for all three cases. The fit-window spread is ≤ 4.7 kN |
| Equilibrium | Inlet + outlet reaction imbalance ≤ 1.7 × 10⁻⁵ of N. ASCII `spcforc` and `binout` N agree within 7 N |
| Load history | The λ schedule is reproduced exactly at all 91 output times. All steps converged at the nominal size |
| Spikes | No spikes in N for any case. C3 and C5 show no spikes in sway. **C1 sway alternates step to step** between λ 0.70 and 1.045 (≈ ±0.08 mm on 0.3–2.9 mm); it is smooth afterwards and N is unaffected (audit F-072) |
| Mesh refinement / step-size study | **Not performed.** The planned step-size check N1 was removed from scope. The mesh is the Mechanical mesh B, validated in 12B against Mechanical; no 12C mesh study exists |

## 10. Protection check

All 10 protected files have **unchanged** SHA-256 hashes (`audit/hash_audit_12C.csv`):
- report PDF / DOCX;
- presentation PPTX;
- `MASTER_PROJECT_DATA.csv`;
- Fluent baseline case and data;
- LC2 deck;
- `s7b_nodal.csv`, `s8a_mode1.csv`;
- `BUCKLING_RESULTS.md`.

**0 files** outside `15_LS_DYNA_Extension/12C_Nonlinear_Buckling/` changed after the end of 12B, including the 12A/12B
files (`audit/changed_outside_12C.txt`). The exception is `PROJECT_STATE.md`, updated at the end of 12C as instructed.

## 11. Figures

| Figure | Content |
|---|---|
| F1 | Mechanical mode-1 reference and the LS-DYNA mode used for the imperfection |
| F2 | 0.0 mm reference response |
| F3 | Load – lateral displacement, C1/C3/C5 + reference, and the normalised version |
| F4 | Amplitude against maximum attained N, Southwell load and onset |
| F5 | Deformed shape at the maximum attained load, C5 (λ = 1.3) |
| F6 | von Mises field at the same state |
| F7 | Mechanical λ₁ / P_cr against the nonlinear results |
| F8 | Three-case peak stress and lateral displacement against λ |
