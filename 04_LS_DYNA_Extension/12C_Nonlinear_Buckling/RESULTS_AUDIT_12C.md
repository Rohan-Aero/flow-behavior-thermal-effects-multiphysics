# Section 12C — results audit

> This audits the additional LS-DYNA nonlinear analysis (extension). The original project results are not affected.
>
> **Evidence.** Every statement below is backed by solver files in `runs/<case>/`:
> - `messag`, `stdout.txt`, `d3hsp`, `run_status.txt`;
> - binary `binout` and `d3plot`;
> - extracted series in `results/series/`;
> - checks in `comparisons/`.
>
> Scripts: `results/post_12C_case.py` (device, Ansys CPython); `results/scripts_cloud/*.py` (analysis, plots, tables, checks).

## 1. Compliance with the 12C instructions

| Instruction | Status |
|---|---|
| Use the validated 12B model and the Fluent `baseline_medium_final` field; T_ref 300 K; LC2 supports | **done.** Includes are hash-identical copies (`audit/model_copy_hashes.csv`); the temperature check is in §4 |
| Elastic only, no plasticity invented | **done.** MAT_004 thermo-elastic. VM / S_y(T) is reported as an indicator only |
| Imperfection = validated first mode, normalised; amplitudes are numerical sensitivity values | **done.** 12B G6 mode 1, max lateral = 1. Final scope: A = 0.1 / 0.6 / 1.2 mm (`audit/imperfection_report_12C.json`) |
| Controlled load progression, fine steps near instability | **done.** Δλ 0.025 up to λ = 1; 0.005 for λ 1.0–1.2; 0.01 for 1.2–1.3 |
| Do not loosen convergence; do not change precision | **done.** Tolerances are tighter than the defaults and unchanged in every run. Double precision throughout |
| Do not rerun CFD or change the temperature field | **done** |
| Do not modify report, presentation, MASTER_PROJECT_DATA, Fluent, Mechanical, baseline buckling or 12A/12B files | **done.** Hash audit §6; 0 files changed outside 12C |
| Keep failed or incomplete runs, labelled and separate | **done.** §2. Nothing deleted |
| Three-point scope C1/C3/C5 (user, 2026-10-07); do not run C2/C4/N1/C0b | **done.** Their decks are kept with `NOT_RUN.txt` |
| No factor-of-safety or real-world adequacy claims; not experimental validation; does not replace Mechanical | **done.** Wording checked in every 12C document |

## 2. Run inventory (all attempts, successful and failed)

Times are local times on the project computer.

| Run folder | Start → end | Result | Reason / note |
|---|---|---|---|
| `runs/C5_A1p2/attempt1_stopped_step2_outofcore_low_memory` | 03-10 20:37:00 → stopped at 20:42 | stopped by me, incomplete (last step begun: 5; the folder label "step2" was written from an earlier status reading) | Out-of-core factorisation because of low free memory (Chrome open), about 4× slower. The user closed Chrome |
| `runs/C5_A1p2/attempt2_stopped_step68_lambda1p14_user_restart` | 03-10 20:43:34 → 21:31 (step 68) | **incomplete.** No EXIT line, no restart dump | The PC was restarted from the Start menu at 21:34:07 (System event 1074). Data valid to λ = 1.135; post-processed (`results/series/attempt2_*`) and used only for the reproducibility check |
| `runs/C5_A1p2/attempt3_stopped_step1_outofcore_low_memory_chrome_open` | 07-10 13:38:59 → 13:40 | stopped by me | Out-of-core again: 3.8 GB free, Chrome open |
| `runs/C5_A1p2/attempt4_aborted_at_start_wrong_wrapper_launched` | 07-10 13:41:17 → 13:41 | aborted by me | Launch error. The updated wrapper had not been written, so the old wrapper started. Killed within seconds |
| `runs/C5_A1p2/attempt5_stopped_step1_outofcore_5537MB_free` | 07-10 13:42:21 → 13:43 | stopped by me | Out-of-core at 5.5 GB free. The memory gate was raised and the run relaunched once Chrome was closed |
| **`runs/C5_A1p2`** | 07-10 13:46:02 → 15:07:26 | **completed.** Normal termination, EXIT 0, 90/90 steps | Started in-core; out-of-core from step 11 (free memory dipped). Run time only: bit-identical to attempt 2 (§4) |
| **`runs/C0_A0p0`** | 15:08:06 → 16:14:22 | **completed.** Normal termination, EXIT 0 | Reference; ran before the scope change |
| **`runs/C1_A0p1`** | 16:15:03 → 18:03:11 | **completed.** Normal termination, EXIT 0 | Wrapper replaced at 16:48 (scope change) while the solver kept running; the solver continued without interruption |
| **`runs/C3_A0p6`** | 18:04:13 → 19:17:17 | **completed.** Normal termination, EXIT 0 | — |
| `runs/C2_A0p3`, `runs/C4_A0p9`, `runs/N1_A0p1_halfstep`, `runs/C0b_A0p0_negev1_bifurcation_detect` | — | **not run** | Scope reduced by the user. Decks kept for traceability |

**Launch method.**
- Runs are launched detached through WMI with `run_lsdyna.cmd`: `LSTC_LICENSE=ansys`, `ncpu = 4`, `memory=20m`.
- The wrapper scripts are `runs/keepawake_chain.ps1` (original chain), `runs/chain2_C0b.ps1` (never started a run) and
  `runs/chain3_C1_C3.ps1` (final). Each holds a per-process "system required" request against idle sleep and waits for free
  memory before each case. No power or system setting was changed.
- The full log is `runs/chain_log.txt`.

## 3. Deviations and findings

| ID | Finding | Effect | Handling |
|---|---|---|---|
| A1 | Scope reduced from six amplitudes plus checks to the three-point study C1/C3/C5 (user instruction) | Trends between points are not resolved; there is no step-size check (N1) and no bifurcation detection (C0b) | Reported as a three-point study, not a sweep |
| A2 | **Perfect case: bifurcation not identifiable.** R16.1 documents the default NEGEV = 2 as "ignore negative eigenvalues" (`d3hsp`), so no warning is printed. C0 stays on the straight path to λ = 1.3 (N = 720.7 kN > P_cr). Lateral response stays at output resolution (< 3e-7 mm). Its step from 3e-8 to 2.6e-7 mm near λ ≈ 1.11 is at nodout print resolution and is not interpreted | No instability load from C0 | Recorded as "not identifiable". The characteristic load comes from the imperfect cases (Southwell) |
| A3 | **Elastic validity exceeded.** VM / S_y(T) = 1 at λ = 1.109 / 1.031 / 0.974 (C1 / C3 / C5). C5 exceeds 1 already at λ = 1 (1.055) | Response beyond these points, including all peak stresses of 1100–1720 MPa, is outside the elastic model's validity | Reported as indicators. No plasticity added |
| A4 | **C1 lateral sway alternates step to step** between λ 0.70 and 1.045 (≈ ±0.08 mm on 0.3–2.9 mm). Cause: the lateral DOF is a small part of the global displacement norm used in the convergence test. N, stresses and later sway are smooth | Southwell C1 changes by ≤ ±0.8 kN when only even or only odd steps are used | Reported. Tolerances not changed |
| A5 | `eloutdet` (element set 2) contains only the end regions, z ≤ 0.03 and z ≥ 0.57 m (21,096 nodes). The mid-span layer was not written | No nodal mid-span stresses | Mid-span stresses taken from d3plot element centroids, λ 1.15–1.3 (`comparisons/crit_check_12C.json`) |
| A6 | Five C5 attempts before the completed run (memory, user restart, launch error) | none on results (§4 reproducibility) | All kept and labelled |
| A7 | C5 out-of-core from step 11 | run time only | Bit-identical to the in-core attempt 2 |

**STOP conditions.** None was reached:
- no error termination;
- no non-convergence or step cut;
- no NaN;
- no unexplained discrepancy with 12B or Mechanical;
- no change to a protected file.

## 4. Quality checks

| Check | Criterion | Result | Verdict |
|---|---|---|---|
| Normal termination | "N o r m a l  t e r m i n a t i o n" and EXIT 0 | C0, C1, C3, C5: yes | PASS |
| Equilibrium (convergence) | every step converged within the tightened tolerances | 90/90 steps; 2–5 iterations (means 2.0 / 3.43 / 3.67 / 3.77); no step cut | PASS |
| Reaction balance | \|F_inlet + F_outlet\| / \|F_inlet\| small | ≤ 2.1e-7 (C0), 1.7e-5 (C1), 8.5e-6 (C3), 7.1e-6 (C5); ASCII and binout N agree to ≤ 7 N | PASS |
| Temperature consistency | node T = 300 + λ·ΔT_Fluent | Node 18865: 437.99 K at λ = 1, 479.385 K at λ = 1.3 in every case. Field range at λ = 1.3: 460.99–641.32 K = 300 + 1.3 × (123.84 … 262.56). d3plot T identical across C1/C3/C5 (0.0 K) | PASS |
| Load history | λ(t) as specified | max \|λ − λ_spec\| = 2e-16 at all 91 output times | PASS |
| Energy | smooth, no jumps; balance where meaningful | External work = 0 (thermal strain, no applied force). LS-DYNA internal energy is negative for this loading and decreases monotonically with no jumps. An IE = EW balance is not applicable | PASS (smoothness only; see F-075) |
| Spikes | no isolated jumps in N or sway (25 % slope test, schedule kinks excluded) | N: none (the C1 flag at λ 1.19 is the maximum). Sway: C3/C5 none; C1 alternation A4 | PASS with A4 |
| Critical location | peak at the outer edge of the inlet face (~438 K) | Every case and every λ: z = 0, r = 20 mm, 437.99 K at λ = 1. Mid-span element stress 612–666 MPa at λ = 1.3, much lower than the end layers (1582–1658 MPa) | PASS |
| Mode shape, global vs local | global guided sway, no local mode | Mid-span lateral 0.13–0.18 % of the end value; sway direction −6.14° (imperfection −6.11°); ovalisation ≤ 0.041 mm; cos-shaped profile (F5) | PASS: global |
| Sensitivity consistency | trends monotonic in A; Southwell w₀ ≈ imposed | Onset, N(λ = 1), VM(λ = 1) and N_max all monotonic in A. w₀ estimate 91–93 % of 2A | PASS |
| Reproducibility | identical inputs give identical outputs | C5 final vs attempt 2: max abs. difference 0 over 68 points | PASS |
| Baseline link | C0 at λ = 1 equals 12B G5 | 553.246 vs 553.247 kN; 605.2 vs 605.160 MPa at node 18865 | PASS |

## 5. What is not verified

- **Mesh independence** of the nonlinear response: no 12C mesh study exists.
- **Step-size sensitivity:** N1 was removed from scope.
- **Bifurcation load of the perfect geometry:** C0b was not run.
- **Response beyond the elastic-validity indicator**, which would need plasticity.
- **Any physical tolerance or real imperfection.** The amplitudes are numerical.

## 6. Protected-file hash audit

Run on 2026-10-07 after all runs finished: `audit/hash_audit_12C.ps1` → `audit/hash_audit_12C.csv`,
`audit/changed_outside_12C.txt`. Re-run at the end of 12C; result in `PROJECT_STATE.md` §27.

| File | SHA-256 (prefix) | Status |
|---|---|---|
| Report PDF `13_Report/Final_Report/…Internship_Report.pdf` | 7F8F32ADB39CD260 | unchanged |
| Report DOCX | 2D40820C27BD5525 | unchanged |
| Presentation PPTX `14_Presentation/Final/…` | 02EAB433F6004679 | unchanged |
| `11_Final_Audit/MASTER_PROJECT_DATA.csv` | 727ADD0A71BE7901 | unchanged |
| Fluent `baseline_medium_final.cas.h5` | 84D6511B66C3B553 | unchanged |
| Fluent `baseline_medium_final.dat.h5` | F05837C5C27E022F | unchanged |
| LC2 deck `LC2_solve_input_ds.dat` | 51D806783ABC26AC | unchanged |
| `s7b_nodal.csv` | DC650A0C2532296A | unchanged |
| `s8a_mode1.csv` | A5FDC844DDDEBBDA | unchanged |
| `BUCKLING_RESULTS.md` | 5BABD2DC621995F4 | unchanged |

Files changed after the end of 12B (2026-10-03 01:36:53):
- outside `15_LS_DYNA_Extension`: **0**;
- inside `15_LS_DYNA_Extension` but outside `12C_Nonlinear_Buckling` (12A/12B files): **0**.
