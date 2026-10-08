# Section 8A: buckling audit

> **RE-ANALYSIS 2026.** This audits the new linear-buckling solutions and the hand estimate. Nothing here is a recovered original, and there are no experimental data.
>
> Every "found" value comes from one of these:
>
> - `Buckling/Audits/presolve_audit_8A.json` (checks run inside Mechanical before any solve);
> - `mech_buckling_8A_summary.json` and `mech_buckling_8A_log.txt`;
> - the solver files in `Buckling/Mechanical/*/Solver_Output/`;
> - `Buckling/buckling_hand_results.json` and `fe_modes_8A.json`.

## 1. Verdict

| Area | Status |
|---|---|
| Pre-stress state = LC2 of 7B | **Yes.** Same mesh, BFBLOCK, material and resolved constraints (section-by-section input comparison). The re-solved LC2 reproduces the 7B maximum von Mises and reaction to all printed digits |
| Thermal field | unchanged: the re-exported mapped temperature is byte-identical to the 7A export |
| Buckling set-up | pre-stress environment read back as `LC2_Axially_Restrained`; no loads or supports of its own; perturbation restart keeps all LC2 boundary conditions (`ALLKEEP`) |
| Student licence | the full 108,252-node model solved (Block Lanczos, 6 modes) with no licence message |
| Constraint validation | intended = actual for every DOF (§4) |
| Benchmark | the constant-property toy tube reproduces Euler within the expected shear band, for both end conditions (§3) |
| Solutions | LC2 re-solve, LC2 buckling, LC2NS static and LC2NS buckling all **Solved** (status Done, 0 solver errors). All Workbench cells of the 8A project Up to Date |
| Existing LC1/LC2 results | **not modified.** The 7B project was only opened and saved *as* a new file: its 58 files are SHA-256 identical before and after 8A (`pre8A_7B_project_hashes.json` vs `post8A_7B_project_hashes.json`, 0 differences) |

## 2. Run history (nothing deleted)

| Run | What happened | Kept in |
|---|---|---|
| APDL snippet + method benchmark | Toy tube in MAPDL (§3). The snippet (`s8a_buckle_snippet.inp`: load factors + corner-node mode shapes) ran with 0 errors | `Buckling/Benchmark/` |
| 1 | **Gate FAILED, nothing solved.** The LC2NS check expected `NROT` rotations, but Mechanical writes the nodal rotations of a face Displacement in a cylindrical CS as `NMOD,node,,,,θ` lines. The check was corrected to read NMOD; the model was not changed. The buckling-enum setting also failed harmlessly (not a global name), leaving the multiplier sign on Program Controlled | `Audits/Gate_Run1_FAIL/` (incl. the exact run-1 script, SHA 148908D2FB48) |
| 2 | **Gate FAILED, nothing solved.** 1,202 NMOD rotations for 1,224 end-face nodes. The 22 missing nodes are the nodes at θ = 0 (11 per face), whose cylindrical orientation equals the global one, so Mechanical writes no rotation for them. The check was corrected to require every end-face node to be either correctly rotated (angle error < 10⁻⁶°) or at θ = 0 | `Audits/Gate_Run2_FAIL/` |
| 3 | Gate PASS. LC2 re-solve identical to 7B; **LC2 buckling solved** (λ₁ = 1.10804705). The script then stopped at the image step (the graphics-scaling enum is not a global name in batch Mechanical), so the LC2NS pair was not solved | `Audits/Run3_STOPPED_at_images/` (outputs, logs, script) |
| 4 | Gate PASS. Full rerun from the 7B project (save-as again): LC2 re-solve, LC2 buckling (λ₁ = 1.10804700), images, LC2NS static + buckling | current `Audits/`, `Mechanical/`, `figures/` |

**Run 3 vs run 4.** λ₁ differs by 5 × 10⁻⁸ relative, and λ₃,₄ agree to about 10⁻⁶ (Lanczos convergence tolerance on repeated roots). The repeated eigenvalue pairs may pick any orientation in the cross-section plane: mode 1 lies at 146.9° in run 3 and 162.7° in run 4.

## 3. Benchmark of the method (toy model, not a project result)

**The model.** It has the same geometry as the duct, but constant E = 190 GPa, ν = 0.294, α = 13.6 × 10⁻⁶ /K and a uniform ΔT = 225 K (MAPDL, SOLID186, 37,910 nodes). The exact answers are known:

- N = E α ΔT A = 547,958 N (FE reaction: 547,960 N);
- Euler P = π²EI/(KL)²;
- Engesser shear correction with Cowper k = 0.620.

| End condition | FE λ₁ | Euler | Euler + shear | FE/Euler | Shape |
|---|---|---|---|---|---|
| LC2-type: U_z on end faces + 3 mid-span hoop nodes (guided, K = 1) | 1.1176 | 1.1199 | 1.1040 | 0.998 | cos(πz/L), correlation 1.000; λ₃ = 4.340 = the clamped shape |
| No-sway: U_z and U_θ on end faces (clamped, K = 0.5) | 4.3422 | 4.4796 | 4.237 | 0.969 | 1 − cos(2πz/L), correlation 1.000 |

**What the benchmark shows.**

1. The thermal-prestress eigen-buckling scales the restrained thermal force as intended.
2. The LC2 support set behaves as a guided column: the mid-span hoop nodes do not raise the load.
3. The FE falls between the plain and the shear-corrected Euler values.
4. The mode-classification script identifies the shapes correctly.

## 4. Constraint validation (buckling model = LC2 supports)

Actual = read from the solver input (`LC2_presolve_8A_ds.dat`, resolved to DOF, value and node set). The perturbation run restarts from this LC2 solution and "keeps all boundary conditions" (`solve.out`).

| Degree of freedom | Intended (LC2) | Actual | Status |
|---|---|---|---|
| U_z, inlet end face (612 nodes) | 0 | `d,all,uz,0` on component `_DISPZEROUZ`: 1,224 nodes = both complete end faces (node-id sum 80,282,530, identical to 7B) | ✅ |
| U_z, outlet end face (612 nodes) | 0 | same component | ✅ |
| U_x, U_y (radial and lateral) on the end faces | free (radial growth permitted) | no D | ✅. Consequence: the end planes may translate sideways, so the buckling model is a **guided column (K = 1)** |
| Rotation of the end planes | prevented, as a consequence of full-face U_z (plane stays plane) | implicit in `d,uz` on every face node (solid elements have no rotational DOFs) | ✅ |
| U_θ at nodes 25862 / 25874 / 25886 (mid-span, r = 20 mm, 0/120/240°) | 0, removes lateral rigid-body motion and twist only | `nrot` to local CS 12 (cylindrical) + `d,…,uy,0` on those 3 nodes | ✅. LC2 reactions about 10⁻⁷ N (7B); mode-1 lateral deflection at mid-span 1.4 × 10⁻⁵ of the maximum, so it does not restrain the mode |
| U_r, U_z at the hoop nodes | free | no D | ✅ |
| Barrel (all other nodes) | free: no accidental fixation | no D, no CP/CE, no weak springs; no other element blocks | ✅ |
| Buckling analysis | no loads or supports of its own | none (object list); perturbation `ALLKEEP` | ✅ |
| Pressure | none (thermal-only pre-stress) | both pressure objects suppressed; no 443.41 in the input | ✅ |

**LC2NS sensitivity (not the LC2 definition).**

- U_z = 0 and U_θ = 0 (`d,uy` in the rotated nodal systems) on the same 1,224 end-face nodes.
- The nodal systems are cylindrical: 1,202 NMOD rotations with an angle error below 10⁻⁶°, and the 22 unrotated nodes all lie at θ = 0.
- There are no mid-span hoop nodes and no other constraints.

## 5. Checks on the LC2 buckling solution

| Check | Found |
|---|---|
| Eigen-solver | Block Lanczos, `bucopt,lanb,6,,,range` (positive multipliers); 6 eigenvalues converged |
| Solver messages | 0 errors. Warnings: "element shape checking inactive" (Mechanical default; shape quality covered in 7B) and "distributed sparse solver out-of-core" (performance only). Run 3 also had "elapsed time exceeds CPU time" (performance only). The LC2NS static adds the expected "ALPX below the supplied range at 26.85 °C" note (7B §4) |
| Load multipliers | Mechanical `LoadMultiplier` property = APDL `SET,LIST` = the `s8a_load_factors.csv` values |
| Repeated pairs | λ₁ = λ₂ to 1.3 × 10⁻⁷ and λ₃ = λ₄ to 2 × 10⁻⁶, as expected for an axisymmetric section; the pair members are orthogonal (90.0°) |
| Mode character | all 6 modes are beam-type (≥ 99.99 % rigid-section motion); ovalisation < 10⁻⁶ of the lateral amplitude, so there is no local or shell mode |
| Consistency with the hand estimate | λ₁ = 1.1080 lies between Euler E(z) (1.1194) and Euler + shear (1.1036), the same ordering as the benchmark |
| λ₃ vs no-sway Euler | 4.298 vs 4.471 (Euler E(z)) / 4.229 (+ shear): in the expected band |

## 6. LC2NS sensitivity solution

| Check | Found |
|---|---|
| Static pre-stress | Solved (77 s). End reaction 548,936.61 N, identical to LC2. Maximum von Mises 605.1596 MPa (LC2: 605.1609 MPa) |
| Buckling | Solved (272 s), 6 modes: λ = 4.29995, 4.29995, 8.35615, 8.35615, 15.4244, 15.4244. 0 errors |
| Mode character | all beam-type (≥ 99.99 % rigid-section motion); mode 1 = clamped shape with the largest deflection at mid-span, none at the ends |
| Hand consistency | 4.300 lies between Euler K = 0.5 with E(z) (4.471) and Euler + shear (4.229) |
| Status | a **sensitivity bound only**. The real end restraint is undefined |

## 7. Hand-calculation checks

- **Section properties.** A = 942.48 mm², I = 117,810 mm⁴, r = 11.180 mm, recomputed by formula.
- **E(z).** Integrated from the actual 7B nodal temperatures, E_b = ∫E y² dA / I on all 261 node planes. The volume-mean temperature from the same integration, 525.53 K, matches the 7A value of 525.52 K. That validates the quadrature.
- **Applied force.** Read from the solver reaction table, not re-entered by hand.
- **Johnson and Euler regimes.** C_c = 60.2 and all KL/r < C_c, so every case is flagged as intermediate.
- **Shell formula.** Explicitly marked as outside its validity; used only to rule out local buckling.

## 8. Independent verification

`Audits/Verification_8A/verify_8A.py` is written separately from the calculation, classification and Mechanical scripts. It reads only the raw solver files, and all 17 checks pass (`verify_8A_result.json`):

- the applied force from the re-solve reaction table, equal to 7B;
- N/A and r;
- the six load factors of each buckling run, identical in solve.out, the snippet CSV and Mechanical's LoadMultiplier;
- 0 solver errors;
- guided Euler recomputed with a different E weighting: 1.1198 vs 1.1194;
- λ₁ between the plain and the shear-corrected Euler values;
- the Johnson values;
- the constraint sets re-parsed from the input decks: U_z on exactly the 1,224 end-face nodes; U_θ only on the 3 hoop nodes; the LC2NS NMOD rotations;
- the mode-1 shapes checked directly from the raw eigenvectors: guided sway with the ends moving in opposite directions (cos = −1.000) and mid-span 1.4 × 10⁻⁵; LC2NS clamped with the ends at 0.2 % of mid-span;
- the 7B project hashes unchanged.

The first pass had a bug in the *verifier's* own CMBLOCK parser: it counted node ids instead of entries. That bug was fixed in the verifier. No model or result was touched.

## 9. Integrity

- The temperature field, geometry, mesh, material and LC2 restraints were **not** changed.
- LC2 was re-solved only because the buckling link requires pre-stress files, and it reproduced 7B exactly.
- The no-sway case is a separately named sensitivity analysis. It is not presented as the LC2 result.
- Mechanical images are unedited `Graphics.ExportImage` output. Mode shapes are shown auto-scaled, because an eigenvector has no physical amplitude.
- Data plots are labelled as plotted from the solver tables.
- No nonlinear collapse result was produced or implied.
