# Support sensitivity — Section 9B-2 (Parts K, L, M, U)

> **RE-ANALYSIS 2026.** Every number in this document is a newly generated ANSYS 2026 R1 Student result of this re-analysis (Fluent CFD of Section 9B-1, Mechanical of Section 9B-2), computed from the solver's own output tables. Nothing is a recovered internship value, and no experimental or measured data exist or are implied.

All three scenarios use the **baseline design** (P00 CFD temperature field, mesh B, material, T_ref 300 K, sparse solver). Only the end supports differ. This is a sensitivity to an *undefined* real end restraint (T-034); it is kept separate from the design-variable cases. No scenario is ranked or labelled as preferable.

## 1. Definitions

| Scenario | Inlet end (z = 0) | Outlet end (z = 0.6 m) | Other | Column idealisation | Source |
|---|---|---|---|---|---|
| **S1** (= LC2, baseline) | U_z = 0 on every face node; radial and lateral free | same | 3 mid-span outer nodes U_θ = 0 (rigid rotation only) | ends held against rotation, free to sway: guided column, K = 1 | 7B static, 8A buckling |
| **S2** (8A LC2NS) | U_z = U_θ = 0 on every face node (CS_DUCT_CYL); radial free | same | none | ends held against sway and rotation: clamped–clamped, K = 0.5 | 8A static and buckling; nodal table re-extracted in 9B-2 (no re-solve) |
| **S3** (new) | U_z = U_θ = 0 on every face node (CS_DUCT_CYL); radial free → clamped | deformable remote displacement: pilot on the axis at z = 0.6 m, U_x = U_y = U_z = 0, rotations free → pinned | none | clamped–pinned, K = 0.699 | 9B-2 (after B03) |

## 2. B03 toy benchmark of the S3 implementation (Part L; not a project result)

**Why a benchmark.** S3 is the first support in this project that uses a remote point (MPC contact, force-distributed). Before the real case was solved, the exact formulation Mechanical wrote into the S3 solver input was copied into the 8A constant-property toy tube, where the answer is known: E 190 GPa, ν 0.294, α 13.6 × 10⁻⁶ /K, uniform ΔT 225 K, SOLID186, esize 5 mm.

The copied formulation:

- the pilot node and a TARGE170 element;
- CONTA174 contact elements on the outlet-face element faces (generated with ESURF), with the key options of the real deck: MPC algorithm, bonded always, force-distributed (deformable) constraint (`keyo,tid,2,1`, `keyo,tid,4,111111`, `keyo,cid,12,5`, `keyo,cid,4,1`, `keyo,cid,2,2`);
- the inlet face nodes rotated to the cylindrical CS, with U_θ = U_z = 0.

Files: `Structural_Cases/B03_S3_TOY_BENCH/` (b03_main.inp, b03_main.out, b03_check.py, b03_results.json; `B03_BENCHMARK.md`). The header comment of b03_main.inp still names CONTA175 (written before the real deck was inspected); the element type actually defined and used is CONTA174 (`et,2,174` + ESURF), as in the real deck. The comment was left unchanged because the file is the one that ran.

Two toy runs:

- **run 1** used the free 8A toy mesh (esize 5 mm; 37,911 nodes; 62 outlet contact faces);
- **run 2** used a structured mesh with 36 equal circumferential sectors, like the real model (82,585 nodes; 144 outlet contact faces).

| Check | Run 1 as first formulated | Run 1, reformulated checks | Run 2 (structured) |
|---|---|---|---|
| 1 solve completed, no errors, no pivot / rigid-body messages | PASS | PASS | PASS |
| 2a inlet axial force = E alpha dT A within 0.1 % | PASS | PASS | PASS |
| 2b pilot axial force = - inlet axial force (equilibrium, 1e-6) | PASS | PASS | PASS |
| 2c outlet face nodes carry no constraint; one constrained pilot | PASS | PASS | PASS |
| 2d no lateral reaction resultant (< 1e-6 x N) | **FAIL** | PASS | PASS |
| 3 static state: no rigid lateral translation of any section (LS fit < 1e-4 x free radial growth) | **FAIL** | PASS | PASS |
| 3b static axial stress = -E alpha dT (corner nodes, mid-span, 0.1 %) | - | PASS | PASS |
| 4 lambda1 between shear-corrected and plain clamped-pinned Euler | PASS | PASS | PASS |
| 5a mode 1 global lateral (beam share > 0.99, ovalisation < 1 %) | PASS | PASS | PASS |
| 5b mode 1 fixed-pinned shape (corr > 0.99) | PASS | PASS | PASS |
| 5c max lateral deflection at 0.55-0.65 L from the clamped inlet | PASS | PASS | PASS |
| 5d modes 1-2 orthogonal pair (split < 1e-4, 90 +- 1 deg) | PASS | PASS | PASS |

**Why two checks were reformulated after run 1.** Neither change touched the model.

- **Static lateral translation.** Run 1 measured the node-mean of (u_x, u_y) per section: 4.59e-06 m. On the free mesh the face nodes are unevenly distributed (node centroid 1.2 mm off the axis). Under uniform radial growth, that mean equals the radial strain times the node centroid, so it is **not** a translation. A least-squares fit of translation + radial growth + rotation per section gives 2.8e-09 m (run 1) and 2.5e-11 m (run 2), i.e. no rigid lateral motion.
- **Lateral reaction.** The absolute 10⁻³ N limit was set before the run. Run 1 gave 0.013 N (2.4e-08 × N), numerical noise of the unstructured mesh. The limit is now relative, 10⁻⁶ × N. Run 2 gives 1.1e-04 N, which would also meet the original limit.
- Run 2 is the independent confirmation: with an even face mesh (as in the real S3 model) every quantity is symmetric to round-off.

| Quantity | Run 1 (free mesh) | Run 2 (structured) | Exact / theory |
|---|---|---|---|
| Axial force [N] | 547,961.3 | 547,955.5 | E α ΔT A = 547,956.6 |
| Pilot force + inlet force [N] | 3.07e-06 | 2.47e-06 | 0 |
| Mid-span axial stress (corner nodes) [MPa] | -581.400 | -581.400 | −E α ΔT = -581.400 |
| Mid-span radial growth, outer [µm] | 79.1928 | 79.1928 | (1+ν) α ΔT r_o = 79.1928 |
| **λ₁** | **2.23761** | **2.23766** | Euler (K = 0.6992) 2.29078; + Cowper shear (k = 0.620) 2.22563 |
| FE / Euler; FE / (Euler + shear) | 0.9768; 1.0054 | 0.9768; 1.0054 | between the bounds |
| Mode 1 fixed–pinned correlation; z of max lateral | 0.999994; 360 mm | 0.999994; 360 mm | 1; 0.605 L = 363 mm |
| Modes 1–2 | orthogonal pair, split 1.3e-06 | orthogonal pair, split 3.8e-07 | degenerate pair |

**B03 result: PASS.** The implementation copied from the real deck behaves as intended. There is no rigid-body motion. Both reactions are exact. The static state is uniform. λ₁ lies inside the clamped–pinned Euler band, and the mode is the fixed–pinned shape with its maximum at 0.6 L from the clamped end. The real S3 case was solved only after this result.

## 3. Real S3 model (Part M)

| Item | Result |
|---|---|
| Model | save-as copy of the 7B project (`Structural_Cases/S3_LC2_INTERMEDIATE/Project`) with a new Static Structural system (shared Engineering Data / Geometry / Model; fed by the same External Data) and a Linear Buckling system on it, built like the 8A S2 pair |
| Solver input (deck mode, before B03) | SOLID186 block and nodal temperatures identical to the 7B LC2 input; all 7B nodes present plus 1 pilot node; element blocks: 23,400 SOLID186 + 180 outlet-face CONTA174, plus the TARGE170 pilot element |
| Pre-solve gate (solve mode) | PASS (22 checks), incl. deck identical to the one copied into B03 |
| Mapped temperature | identical to the S1 (LC2) mapping (pre-solve gate check) |

## 4. S1 / S2 / S3 comparison (Part U; `SUPPORT_SENSITIVITY_RESULTS.csv`)

| Scenario | Max von Mises [MPa] | Location | Mean axial stress [MPa] | Axial reaction [kN] | Max total deformation [mm] | Max section lateral translation (static) [m] | λ₁ | λ₂ | P_cr [kN] | Dominant mode | First-yield factor | Occurs first (idealised) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | 605.161 | outer edge of the inlet face (r 20 mm, z 0) | -582.440 | 548.94 | 0.1349 | 8.0e-12 | 1.1080 | 1.1080 | 608.2 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm | 1.730 | buckling (λ₁ 1.108 < first-yield factor 1.730) |
| S2 | 605.160 | outer edge of the inlet face (r 20 mm, z 0) | -582.440 | 548.94 | 0.1349 | 9.8e-15 | 4.2999 | 4.2999 | 2360.4 | global clamped-column, 1 − cos(2πz/L) (corr 1.0000); max lateral at z = 300 mm | 1.730 | first yield (first-yield factor 1.730 < λ₁ 4.300) |
| S3 | 605.160 | outer edge of the inlet face (r 20 mm, z 0) | -582.440 | 548.94 | 0.1349 | 9.7e-15 | 2.2322 | 2.2322 | 1225.4 | global fixed-pinned column (corr 1.0000); max lateral at z = 363 mm | 1.730 | first yield (first-yield factor 1.730 < λ₁ 2.232) |

S3 reactions: inlet F_z 548,936.68 N, pilot F_z -548,936.68 N (sum -2.10e-09 N); lateral resultants 5.3e-08 / 2.4e-08 N; outlet-face nodes carrying a constraint: 0 (the pilot carries the outlet support, as intended).

## 5. Physical interpretation (no ranking)

- **Static stress is almost insensitive to the end condition.** The end force is set by the restrained mean thermal strain, which the axial restraint fixes in all three scenarios. The mean axial stress is the same to 1.2e-05 %, and the peak differs by 2.1e-04 %. The supports decide *how the axial force can escape sideways* (the stability), not how large it is.
- **Stability is dominated by the end condition.** λ₁ = 1.1080 (S1, ends free to sway) → 2.2322 (S3, one end clamped, one pinned) → 4.2999 (S2, both ends clamped). The FE ratios 1 : 2.015 : 3.881 follow the effective length (Euler 1 / K² = 1 : 2.047 : 4 for K = 1, 0.699, 0.5); they are lower, increasingly so for the shorter effective lengths, which is consistent with shear flexibility and the axial variation of E(T). The mode shape follows the support (guided sway / fixed–pinned / clamped).
- **Which mechanism comes first changes with the support.** With S1 the idealised duct bifurcates before first yield. With S3 and S2 the elastic bifurcation factor is above the first-yield factor (1.73), so first yield — and, for these intermediate columns, inelastic buckling (8A: Johnson 1.41 for fixed–pinned, 1.58 for fixed–fixed; squash 1.75) — would come first. The structural conclusion (stability-controlled or yield-controlled) therefore depends on a support condition the project does not define (T-034).
- **S3 against the hand estimate** (8A fixed–pinned Euler with E(z) 2.29, with shear 2.22; 9A anchored estimate 2.221): FE λ₁ 2.2322.
- All three are linear eigenvalue results of a perfect tube; imperfections and plasticity would lower them (T-035).
