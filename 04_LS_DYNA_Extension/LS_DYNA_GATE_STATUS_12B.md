# Section 12B — LS-DYNA gate status (installation verification and baseline gates)

> **Scope.** This section covers installation verification, model compatibility, conversion and baseline gates only.
> **No nonlinear (imperfection or post-buckling) LS-DYNA result exists or is claimed.**
>
> **Not modified:** the final report, the final presentation, every Fluent and Mechanical result, `MASTER_PROJECT_DATA.csv`
> and the Mechanical baseline. SHA-256 values were re-checked after the runs (§5). LS-DYNA values are **not** added to the
> internship deliverables.
>
> **Where the work is.** Everything is under `15_LS_DYNA_Extension/`. The five 12B documents are listed in §6. Solver
> decks, outputs and scripts are under `work_12B/` as the working evidence.

## 1. Gate results

| Gate | Question | Result | Key evidence | Detail |
|---|---|---|---|---|
| **G0** | Is the installation real and usable for implicit work? | **PASS** | LS-DYNA **R16.1** (R16.1-180-gd50332dbe5) Student, **SMP, double precision (I8R8)**. The executable `…\LS-DYNA Suite R16.1 Student\lsdyna\ls-dyna_smp_d_R16.1_…_studentversion.exe` launches from the command line with `LSTC_LICENSE=ansys`. Student licence active (331 days). An implicit one-element test gave the exact hand solution. LS-PrePost 2025 R1 (4.12.6) runs in batch. No explicit-only restriction | `audit/INSTALLATION_CHECK_12B.md` |
| **G1** | Which Student size limit is enforced? | **PASS** | Error 70043 at **128,520 elements** ("exceeds limit 128000"). 131,502 nodes accepted; nodes + elements (254,502) accepted. **The limit counts elements only.** The LC2 model (108,252 nodes, 23,400 elements) runs; no reduced model is needed | `audit/INSTALLATION_CHECK_12B.md` |
| **G2** | Do the needed element and procedures work? | **PASS** | ELFORM 23 (20-node, 14-point) works in linear and nonlinear implicit statics and in `*CONTROL_IMPLICIT_BUCKLE`, with thermal strain and temperature-dependent E. H20 node order = SOLID186 order. **Formulation change documented:** 27-point → 14-point integration. **Solver finding:** NSOLVR 1 does not equilibrate thermal stresses (bar C1: σ_x −2.79 MPa where 0 is exact; B1 +11 %); NSOLVR 12 is required | `inputs/LS_DYNA_IMPORT_AUDIT_12B.md` §2 |
| **G3** | Can the material be represented without inventing data? | **PASS** | MAT_004 with SIGY / ETAN blank: thermo-elastic, **no plasticity, no stress–strain curve**. E(T) is the same 5-point table. The MPAMOD secant α is converted **exactly** to an instantaneous α curve. Restrained bar with T-dependent E: −678.90 vs −678.84 MPa closed form (+0.009 %, 40 steps). Large-deformation (geometric nonlinearity) shown with NSOLVR 12 | `inputs/LS_DYNA_IMPORT_AUDIT_12B.md` §2–3 |
| **G4** | Is the converted model the solved LC2 model? | **PASS** | Nodes, elements, connectivity, material, T_ref (300 K), temperature field (108,252 values), load mechanism, supports, geometry and coordinate system all match. Volume differs by −1.9 × 10⁻⁶ from analytic; no non-positive Jacobian. Two differences documented: the integration rule, and large-deformation vs small-deflection kinematics | `inputs/LS_DYNA_IMPORT_AUDIT_12B.md` §1 |
| **G5** | Does the linear-elastic static solution reproduce Mechanical LC2? | **PASS** | Peak von Mises 605.160 vs 605.161 MPa at the **same node** (outer edge of the inlet face, 437.99 K). Max deformation 0.13556 vs 0.13488 mm (+0.50 %). Radial deformation within 0.2 %. Mean axial stress −587.01 MPa raw (+0.785 %); −582.38 MPa (−0.011 %) after the deformed-area factor measured beforehand. Stress-field RMS difference 1.1 MPa (von Mises). **One internal criterion missed:** the inlet/outlet reaction balance was 1.1 × 10⁻⁵, against the 10⁻⁶ I had set. Diagnostic G5b traced this to 5-digit rounding in the ASCII reaction file. The binary output of the same solution balances to 1.3 × 10⁻⁵ N (2.4 × 10⁻¹¹), and tighter convergence changed no compared quantity beyond print resolution | `results/GATE5_STATIC_COMPARISON_12B.md` |
| **G6** | Does the linear buckling cross-check reproduce λ₁? | **PASS** | **λ₁ = λ₂ = 1.109475** vs 1.10805: **+0.13 % raw**, **−0.64 %** after the kinematic factor measured beforehand (both within ±1 %). Critical load λ₁ × 548.94 kN = **609.0 kN** (Mechanical 608.2 kN). Mode: global guided-column sway (correlation 0.999998 with cos πz/L; ends opposite; mid-span 1.4 × 10⁻⁵; max lateral at an end face). 0.9999998 of the Mechanical mode-1 vector is reproduced. **Deviation:** 10 load steps instead of 40 (run time). Measured prestress effect −0.05 % (reaction), so λ₁ is about 0.05 % high | `results/GATE6_BUCKLING_COMPARISON_12B.md` |

## 2. Decision: YELLOW: proceed to 12C only when instructed, under the conditions of §4

**Definitions used.**

- **GREEN:** every gate passes with no deviation from the frozen plan and no missed criterion.
- **YELLOW:** every gate passes on the brief's criteria, but with documented deviations, offsets or missed internal
  criteria that are explained quantitatively. Further work may proceed under stated conditions.
- **RED:** a gate fails, or a difference is unexplained. Do not proceed.

**Reasons.**

1. All seven gates pass on the brief's own criteria.
   - G5: all six required comparisons.
   - G6: λ₁ within ±1 %, both raw and corrected; same global mode.
2. It is not GREEN, for four reasons:
   - **(a)** two systematic, documented offsets remain between the LS-DYNA and Mechanical formulations, and any later
     comparison must carry them:
     - large-deformation kinematics: reaction +0.79 %, λ about +0.77 %, u_z +0.67 %;
     - integration rule: kinematics-free λ₁ about −0.65 %.
   - **(b)** the completed G6 used 10 load steps instead of the frozen 40. The effect, about 0.05 %, was measured, not
     assumed.
   - **(c)** one internal G5 criterion (reaction balance ≤ 10⁻⁶) was missed. G5b then showed that the solution meets the criterion, and that the miss came from the 5-digit ASCII output.
   - **(d)** buckling runs on this machine run out of core, at about 4 min per step.
3. No failed gate and no unexplained difference, so it is not RED.

## 3. Missed criteria and deviations

| Item | What happened | Explanation | Effect |
|---|---|---|---|
| G5 reaction balance | 1.1 × 10⁻⁵ against ≤ 10⁻⁶ | Not convergence: G5b with residual ratio 6 × 10⁻¹¹ gives identical ASCII sums. It is 5-digit print rounding (bound 45 N); the binary output balances to 1.3 × 10⁻⁵ N | 6.2 N on 553 kN; 1/450 of the reaction tolerance |
| G6 step count | 10 steps instead of 40 | Run time: buckling forces an out-of-core factorisation. 40-step run 1 was ended by a session drop; run 2 was stopped at about 4 min per step | Prestress 0.05 % smaller; λ₁ about 0.05 % high; both gates still pass with margin |
| G5 §1 rationale for displacements | expected O(ε²) differences | u_z is a difference of strains, so the large-deformation effect on it is O(ε): +0.67 % | criterion (±1 %) unchanged and met |
| Higher buckling modes (not gated) | λ₃ −1.75 %, λ₅ −4.45 % | Integration-rule difference growing with shorter wavelength (plausible; not investigated) | none on the gate. Shapes agree (0.9999996) |

## 4. Recommendation for 12C (not started)

LS-DYNA has reproduced the Mechanical LC2 baseline closely enough for further work, with known and quantified offsets.
If and when 12C is instructed, the 12A plan (P0, then the imperfection sweep I1–I5 and the I4-m2 orientation check, with
w₀/L = 0 … 2 × 10⁻³ as sensitivity values) can proceed on these conditions:

1. **Model.** Use the G5 deck as the base: NSOLVR 12, ELFORM 23 on mesh B, MAT_004 thermo-elastic (no plasticity) and
   the exact α curve. Keep λ ≤ 1.42 (end of the E table, D-098).
   - Keep at least 40 equal steps up to λ = 1. Use smaller steps near and beyond the expected limit or bifurcation
     region, and consider the arc-length option (NSOLVR 12 with ARCMTH = 3) if equilibrium is lost.
   - Do not request `*CONTROL_IMPLICIT_BUCKLE` in the long nonlinear runs. It forces an out-of-core solution of every
     step (about 4 min per step against about 17 s in core).
2. **Imperfection shape.** Use the LS-DYNA mode 1 of G6 from `G6_buckle_10step/d3eigv`. It covers all 108,252 nodes
   (resolves F-062) and matches the Mechanical mode to 0.9999998.
   - The `d3eigv` geometry is the prestressed configuration. Take the mode as the eigenvector state minus that geometry,
     and normalise the lateral amplitude before scaling to w₀.
   - Run the orthogonal mode 2 for the orientation check.
3. **Convergence.** Activate the residual criterion (RCTOL) and print the norms (NLPRINT 2), as in G5b. Read reactions
   from `binout` (or another higher-precision output), not only from the 5-digit ASCII `spcforc`.
4. **Reporting against Mechanical.**
   - Always give raw LS-DYNA values together with the large-deformation offsets measured here: reaction +0.79 %, λ about
     +0.77 %, u_z +0.67 %.
   - Note the element-formulation offset on the kinematics-free λ₁ (about −0.65 %).
   - Never equate a nonlinear limit or bifurcation load with λ₁, and never call any LS-DYNA result a factor of safety
     (12A wording rules).
5. **Launch.** Start long runs detached (WMI), and only when the previous solver has released its memory. A run started
   while memory is still held goes out of core and runs 2–5 times slower.
6. **Unchanged limits.** Elastic only (D-095). Idealised S1 supports, so T-034 still controls every stability
   statement. No real-world adequacy claim.

## 5. Integrity

- **SHA-256 re-checked on 2026-10-03 after all runs.** Every value equals the earlier record:

  | File | SHA-256 (prefix) |
  |---|---|
  | report PDF | `7F8F32AD…` |
  | report DOCX | `2D40820C…` |
  | presentation PPTX | `02EAB433…` |
  | `MASTER_PROJECT_DATA.csv` | `727ADD0A…` |
  | Fluent baseline case | `84D6511B…` |
  | Fluent baseline data | `F05837C5…` |
  | LC2 solver deck | `51D80678…` |
  | `s7b_nodal.csv` | `DC650A0C…` |
  | `s8a_mode1.csv` | `A5FDC844…` |
  | `BUCKLING_RESULTS.md` | `5BABD2DC…` |

- **Changed files.** A scan of the whole project tree found **0 files** created or changed outside
  `15_LS_DYNA_Extension/` since the end of 12A. The exception is `PROJECT_STATE.md`, updated at the end of 12B.
- **Read-only access.** The Mechanical baseline files were only read: the LC2 deck, `s7b_nodal.csv` and the
  `s8a_mode*.csv` modes.
- **No completion claim without proof.** Every run reported as completed has *"N o r m a l  t e r m i n a t i o n"*
  in its `stdout.txt`; G5, G5b and G6 also have an `EXIT 0` line in `run_status.txt`. In all, 26 runs completed
  normally. G1 probes P4 and P5 end in the expected limit error.
- **Stopped runs.** Four were stopped or incomplete: G5b attempts 1–2 and G6 runs 1–2. They are kept in labelled
  folders and are not used as results.

## 6. 12B documents

| File | Content |
|---|---|
| `LS_DYNA_GATE_STATUS_12B.md` | this file |
| `audit/INSTALLATION_CHECK_12B.md` | G0, G1 |
| `inputs/LS_DYNA_IMPORT_AUDIT_12B.md` | G4 side-by-side table; G2/G3 evidence; exact CTE conversion |
| `results/GATE5_STATIC_COMPARISON_12B.md` | G5 criteria, results, explanations, G5b |
| `results/GATE6_BUCKLING_COMPARISON_12B.md` | G6 criteria, runs, results, explanations |

The 12A files in this folder (`README.md`, `results/README.md`) still describe the pre-installation state. They were
left unchanged because the brief allowed only these five files plus `PROJECT_STATE.md` (T-044).
