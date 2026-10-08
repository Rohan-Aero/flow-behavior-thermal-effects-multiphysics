# Section 12B — Gate 6: linear eigenvalue buckling cross-check of LC2 in LS-DYNA

> **Condition.** The brief allows G6 only if G5 passes. The G6 run was started only after G5 had been evaluated
> (`GATE5_STATIC_COMPARISON_12B.md`).
>
> **Model.** Identical to G5: perfect geometry, thermo-elastic, LC2 supports. The prestress is the G5 state at λ = 1 (full
> mapped temperature field). Then `*CONTROL_IMPLICIT_BUCKLE` extracts 6 modes, using the material plus geometric
> stiffness at that state. Deck: `work_12B/G6_buckle/lc2_buckle.k` (= `lc2_static.k` + `*CONTROL_IMPLICIT_BUCKLE 6,1`).
> The completed run uses the same deck with 10 load steps instead of 40
> (`work_12B/G6_buckle_10step/lc2_buckle_10step.k`). This run-time deviation and its measured effect are in §2.
>
> **Reference.** Mechanical LC2 linear buckling (S1), `08_Structural_Analysis/Buckling/BUCKLING_RESULTS.md`:
>
> - λ₁ = λ₂ = 1.10805, about 608.2 kN (λ × 548.94 kN), guided-column sway ∝ cos(πz/L);
> - ends move in opposite directions; mid-span lateral deflection 1.4 × 10⁻⁵ of the maximum;
> - λ₃,₄ = 4.2979; λ₅,₆ = 9.2248.
>
> The mode-1 eigenvector at corner nodes is `…/LC2_Linear_Buckling/Solver_Output/s8a_mode1.csv` (SHA-256 `A5FDC844…`,
> unchanged).
>
> **Post-processing.** `work_12B/mode_check_12B.py` reads `d3eigv` with `lasso-python` (in the session workspace, not on the
> project machine). It fits a rigid-section motion at each of the axial stations, then reports:
>
> - mode character;
> - correlation with cos(nπz/L);
> - the location of the maximum lateral displacement;
> - how much of the Mechanical mode 1 lies in the span of the LS-DYNA mode pair. Modes 1 and 2 are degenerate, so their
>   orientation is arbitrary and a subspace measure is used.

## 1. Acceptance criteria (frozen before the G6 run)

| Quantity | Criterion | Reason |
|---|---|---|
| **λ₁** | **±1 % of 1.10805**, as set in the brief. Checked on the raw LS-DYNA value **and** on the value corrected for the documented kinematic difference | The brief's target. LS-DYNA's buckling step uses the large-deformation prestress state from NSOLVR 12 (G4). The G2 benchmark on the same mesh measures how much this alone raises λ₁: 1.109919 at full load vs 100 × 1.101393 at 1 % load, a factor **1.00774** (analytic (1 + (1+ν)αΔT)² = 1.00794). Corrected λ₁ = raw / 1.00774 |
| Decision on λ₁ | Both within ±1 % → PASS. Only the corrected value within ±1 % → PASS with documented difference. Neither, and unexplained → **STOP (RED)** | Brief: "unless a documented modeling difference explains the discrepancy" |
| Critical load | Reported as λ₁ × 548.94 kN (the Mechanical definition) and as λ₁ × the LS-DYNA reaction | Same definition as 8A; the second value is for completeness only |
| Mode shape | Guided sway: correlation with cos(πz/L) ≥ 0.999; inlet and outlet translations opposite (cos ≤ −0.999); mid-span lateral ≤ 1 % of maximum | The 8A mode description |
| Location of max lateral displacement | At an end face (z = 0 or z = 0.6 m) | The 8A mode description |
| Global vs local | Rigid-section share of the mode ≥ 0.999 (no ovalisation or shell mode) | 8A: all modes beam-type |
| Agreement of mode shape | Share of the Mechanical mode 1 captured by the LS-DYNA mode pair ≥ 0.99 | Direct eigenvector comparison on 28,296 common corner nodes |
| λ₃ (information only) | Reported; no gate | Second guided mode, cos(2πz/L) |

## 2. Runs (what completed and what did not)

| Run | Steps | Outcome | Kept in |
|---|---|---|---|
| G6 run 1, `G6_buckle/lc2_buckle.k` | 40 | **Not completed.** Ended at step 3 when the remote session to the computer dropped and the child process was terminated (exit 0x40010004) | `work_12B/G6_buckle/run1_killed_at_step3_session_disconnect/` |
| G6 run 2, same deck | 40 | **Not completed. Stopped by me at step 2.** With `*CONTROL_IMPLICIT_BUCKLE` the solver factorises out of core on every step (about 4 min per step); its own estimate was 2 h 49 min | `work_12B/G6_buckle/run2_stopped_at_step2_outofcore_too_slow/` |
| **G6 run 3**, `G6_buckle_10step/lc2_buckle_10step.k` | **10** | **Completed.** All 10 steps in equilibrium (2 BFGS iterations each). Buckling eigenproblem solved. *"N o r m a l  t e r m i n a t i o n"* at 2026-10-03 01:02:50, 2,694 s. `eigout`, `d3eigv`, `d3plot`, `nodout`, `eloutdet`, `spcforc` and `d3dump01` written | `work_12B/G6_buckle_10step/` |

**Run-time deviation from the frozen deck.**

- **What changed.** Run 3 is the G6 deck with one change: the load step is Δλ = 0.1 (10 steps) instead of 0.025
  (40 steps). Material, mesh, supports, temperatures, solver and buckling request are unchanged.
- **Why.** Run time only.
- **Effect on the prestress.** It was measured directly by comparing run 3's full-load state with the approved G5
  40-step state (`compare_runs_12B.py` → `G6_buckle_10step/compare_vs_G5_static.json`).

| Full-load state (t = 1) | G5, 40 steps | G6 run 3, 10 steps | Difference |
|---|---|---|---|
| Inlet reaction | 553,247.0 N | 552,954.4 N | **−0.053 %** |
| Mean σ_z over all 108,252 nodes | — | — | ratio 0.99951 (**−0.049 %**); mean Δσ_z +0.29 MPa |
| Von Mises field, 108,252 nodes | — | — | RMS 0.32 MPa, max 0.83 MPa |
| σ_z field | — | — | RMS 0.35 MPa, max 1.17 MPa |
| Peak von Mises | 605.160 MPa, node 18865 | 604.602 MPa, node 89468 | −0.092 %. Same ring: outer edge of the inlet face, r = 20 mm, z = 0, 437.97 K |

- **Size and cause.** The 10-step prestress is 0.05 % smaller in magnitude. This is the steps-straddling-the-α-jump
  effect quantified in bar tests B4/B5.
- **Effect on λ₁.** The geometric stiffness is linear in the stress, so λ₁ of run 3 is high by about the same 0.05 %.
  The equivalent at the 40-step prestress is estimated as λ₁ × 0.99947 and is shown below as a check. The gate is
  judged on the computed value.

## 3. Result

| Mode | LS-DYNA λ (run 3) | Mechanical λ (8A) | Difference |
|---|---|---|---|
| 1, 2 (pair) | **1.109475** | **1.10805** | **+0.129 %** |
| 3, 4 (pair) | 4.222592 | 4.29790 | −1.75 % (information) |
| 5, 6 (pair) | 8.814080 | 9.22482 | −4.45 % (information) |

| Check (§1) | Value | Criterion | Result |
|---|---|---|---|
| λ₁ raw | 1.109475 (+0.129 %) | ±1 % | **PASS** |
| λ₁ corrected for large-deformation kinematics (÷ 1.00774, G2 benchmark) | 1.100954 (**−0.640 %**) | ±1 % | **PASS** |
| *Check:* λ₁ at the 40-step prestress (× 0.99947), raw / corrected | 1.108888 (+0.076 %) / 1.100371 (−0.693 %) | ±1 % | within |
| **Critical load**, Mechanical definition λ₁ × 548.94 kN | **609.03 kN** (Mechanical 608.25 kN, +0.13 %) | reported | — |
| Critical load, λ₁ × LS-DYNA reaction (deformed configuration; information) | 613.49 kN | reported | — |
| Mode shape: correlation with cos(πz/L) | 0.999998 (both modes of the pair) | ≥ 0.999 | **PASS** |
| Inlet vs outlet translation | cos = −1.000 (ends move in opposite directions) | ≤ −0.999 | **PASS** |
| Mid-span lateral / maximum | 1.43 × 10⁻⁵ (Mechanical 1.4 × 10⁻⁵) | ≤ 1 % | **PASS** |
| Location of maximum lateral displacement | at an end face (z = 0.6 m; the pair partner at an end face as well) | end face | **PASS** |
| Global vs local | rigid-section share 0.999999; largest section distortion 0.16 % of the lateral amplitude (shear warping); no ovalisation or shell mode | ≥ 0.999 | **PASS: global** |
| Agreement with the Mechanical mode-1 eigenvector (28,296 corner nodes) | 0.9999998 of it lies in the span of LS-DYNA modes 1–2. The pair is orthogonal (lateral directions 173.9° and 83.9°) | ≥ 0.99 | **PASS** |
| Mechanical mode 3 vs LS-DYNA modes 3–4 (information) | 0.9999996 | — | same shape (cos 2πz/L, ends together) |

**Gate 6: PASS.** Both the raw and the corrected λ₁ are within ±1 % of the Mechanical value. The mode is the same global
guided-column sway mode. The only deviation is the documented step count, and its effect on λ₁ (≈ 0.05 %) is quantified
above.

## 4. Explanation of the differences

- **Raw +0.13 % vs corrected −0.64 %.** Two documented effects of opposite sign.
  - **Large-deformation kinematics, +0.77 %.** It was measured on the same mesh before G6 (BM1 / BM2). The buckling
    step uses the deformed geometry, with I and A grown by (1 + (1+ν)ε)², and the Cauchy prestress.
  - **Element formulation, about −0.65 %.** This is what remains in the kinematics-free value. It agrees with an
    estimate made independently of G6:
    - the same-mesh benchmark gives the kinematics-free ELFORM 23 value 1.1014, 0.25 % **below** its Engesser–Cowper
      hand value (1.1041);
    - Mechanical's SOLID186 LC2 value 1.1080 is 0.40 % **above** its own Engesser hand value (1.1036, 8A);
    - the ratio of the two predicts −0.64 %, against −0.64 % observed.
  - **Interpretation.** The 14-point ELFORM 23 element is slightly more flexible in this bending–shear mode than
    full-integration SOLID186. This is a formulation difference; the physics was not changed to remove it.
- **Higher modes, −1.75 % and −4.45 %.** These are not gated. The difference grows as the half-wavelength shortens
  (cos 2πz/L, then cos 3πz/L), the trend expected if the integration-rule difference stiffens the shear-dominated
  response differently. It was not investigated further. The shapes themselves agree (Mechanical mode 3: 0.9999996).
- **`d3eigv` geometry.** It is the deformed (prestressed) configuration: the node coordinates differ from Mechanical's
  undeformed coordinates by up to 0.11 mm. Mode vectors were taken as the eigenvector state minus that geometry.
