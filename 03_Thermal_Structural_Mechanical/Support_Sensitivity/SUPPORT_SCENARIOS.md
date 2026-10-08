# Section 9A: support / end-restraint sensitivity — scenario definition (no runs yet)

> **RE-ANALYSIS 2026.** This is a planning document.
>
> - S1 and S2 reuse the **solved** Section 8A results. S3 is **proposed, not solved**.
> - The hand numbers come from `support_sensitivity_hand.py`. That script is calibrated to the 8A FE and checked by an independent beam FE (`support_spring_check_beamFE.py`, all targets matched to < 0.2 %). These are planning estimates, not results.
> - **This is a separate sensitivity study (Question B). It is not mixed with the design variables (Question A).** All support scenarios use the P00 baseline geometry, temperature field, material and mesh.

## 1. Why a separate support study is needed

**The dominant uncertainty is the support, not the mesh.** Section 8B showed that the structural mesh moves λ₁ by ≤ 10⁻⁵, while the end restraint moves it by a factor of about 4. The support is therefore the largest structural uncertainty.

**The real restraint is not defined** (T-034). The report must not present one idealised support as universally representative. Three **discrete, physically interpretable** end conditions are defined instead. **No support stiffness is assumed**, because no basis exists for one.

## 2. The scenarios

| ID | Name | Mechanical definition (boundary conditions only; everything else = P00) | Physical meaning | Status |
|---|---|---|---|---|
| **S1_LC2_CURRENT** | current idealised LC2 | both end faces **U_z = 0 on every face node** (ends stay plane, so they cannot rotate); radial and lateral free; 3 mid-span outer nodes U_θ = 0 (rigid-body removal only) | **guided column:** end rotation prevented, ends free to sway sideways (K = 1) | **solved in 8A** (reuse) |
| **S2_LC2_LATERALLY_GUIDED** | ends laterally held | both end faces U_z = 0 **and U_θ = 0** on every face node (cylindrical CS); radial free (thermal growth permitted); no hoop nodes | **clamped, no sway** (K = 0.5): both flanges rigidly attached to a stiff structure | **solved in 8A as "LC2NS"** (reuse) |
| **S3_LC2_INTERMEDIATE** | one end clamped, other end pinned | **inlet (cold) face:** U_z = 0 and U_θ = 0 on every face node (as S2). **Outlet (hot) face:** Remote Displacement, **Deformable** behaviour, pilot on the axis at z = 600 mm, U_x = U_y = U_z = 0, **rotations free**. No hoop nodes | **fixed–pinned** (K = 0.699): upstream flange rigid; downstream end located axially and laterally but free to rotate (a spherical seat, gimbal or loose sleeve) | **proposed** |

**Why S3 is defensible.**

- It combines two idealisations that are each exact in their own terms: a clamped end and a pinned end. It does not invent a stiffness.
- It sits between S1 and S2 in end fixity: one end is held laterally, one end can rotate.

**Why the S3 outlet uses a Deformable remote point.**

- It constrains only the *average* motion of the face. The face can therefore still expand radially (thermal growth) and warp.
- A Rigid remote point would lock the face's radial growth. That would add an artificial thermal constraint stress at the outlet.

### 2.1 Conceptual scenarios (hand only, no FE; they bound the picture)

| End condition | K | λ₁ (Euler, E(z)) | Why it is shown |
|---|---|---|---|
| Pinned–pinned (rotation free, laterally held) | 1.0 | 1.114 | holding the ends laterally **without** rotational fixity gives no gain over S1 |
| Imperfect guided (AISC design K = 1.2) | 1.2 | 0.78 | a small end rotation already takes the ideal column below 1 |
| One end rotation-free and sway-free | 2.0 | 0.28 | **S1 is not a lower bound.** It assumes perfect rotational fixity of both flanges |

## 3. Planning estimates per scenario

| Quantity | S1 (8A, solved) | S2 (8A, solved) | S3 (estimate) |
|---|---|---|---|
| λ₁ FE | **1.108** | **4.300** | about 2.2: FE/Euler ratios of S1 (0.99) and S2 (0.96) applied to Euler 2.286 give 2.20–2.26 |
| λ₁ Euler with E(z) / + shear (hand) | 1.119 / 1.104 | 4.471 / 4.229 | 2.286 / 2.221 |
| Johnson (conventional inelastic) | 1.058 | 1.581 | 1.414 |
| First-yield factor of the LC2 state | about 1.73 | about 1.73 | about 1.73 (static state essentially unchanged) |
| Elastic bifurcation before first yield? | **yes: stability governs** | no | no: yield / inelastic behaviour governs |
| Expected mode | global sway: ends opposite, zero at mid-span | clamped shape: maximum at mid-span | fixed–pinned column shape: maximum at about 0.6 L from the clamped end |
| LC2 static peak VM / mean axial stress | 605.16 / −582.44 MPa | 605.16 / −582.44 MPa (LC2NS) | expected the same to about 0.1 % (same thermal restraint); local differences only near the outlet face |

**How the governing mechanism changes.**

- **S1:** stability governs.
- **S2 and S3:** the elastic bifurcation moves above the first-yield factor, so yield or inelastic behaviour (not modelled; F-044/F-045) governs instead.

**The support definition alone changes the structural conclusion.** That is exactly the question this study answers.

## 4. What lateral stiffness would be required (a design requirement, not an assumed value)

**The question.** For ends held against rotation and joined by a lateral (relative-sway) spring k, how large must k be to reach a given λ₁?

**The method.**

- Exact beam-column theory: k = EI a³ / (2(u − tan u)), u = aL/2, a = √(P/EI).
- EI is calibrated to the solved FE sway load (608.2 kN).
- The no-sway limit is the solved FE value (2,360 kN, λ₁ = 4.300).
- Verified by a separate beam finite-element eigen-analysis.

| Target λ₁ | 1.2 | 1.5 | 1.73 (first yield) | 2.0 | 2.5 | 3.0 | 4.30 (no-sway limit) |
|---|---|---|---|---|---|---|---|
| Required relative lateral stiffness between the ends | 104 N/mm | 445 N/mm | 709 N/mm | 1,021 N/mm | 1,610 N/mm | 2,212 N/mm | ≥ 3,875 N/mm |

**Use in the project.**

- This turns T-034 into a measurable requirement: *"a support system that provides at least about 0.7 kN/mm of lateral stiffness between the ends, with rotationally stiff flanges, moves the elastic bifurcation above first yield."*
- **Not planned as FE cases.** No real support stiffness is known, so no stiffness value is simulated as if it were real.
- **The requirement assumes perfectly rotation-fixed ends.** Rotational flexibility lowers λ₁ (§2.1), so the true requirement is higher.

## 5. Runs required in Section 9B

| Case | Analyses | Notes |
|---|---|---|
| S1_LC2_CURRENT | none; reuse 8A (`Buckling/Mechanical/LC2_Linear_Buckling`, 7B `LC2_Restrained`) | re-extract the outputs with the parametric post-processor for identical definitions |
| S2_LC2_LATERALLY_GUIDED | none; reuse 8A (`LC2NS_NoSway_Static`, `LC2NS_Linear_Buckling`) | same |
| B03_S3_TOY_BENCH | 1 MAPDL linear buckling of the 8A constant-property toy tube with the S3 boundary conditions | method check: FE must fall between plain and shear-corrected Euler (K = 0.699), as in the 8A benchmarks. Not a project result |
| S3_LC2_INTERMEDIATE | LC2 static + linear buckling on mesh B (save-as copy of the 7B project; the 7B project is never written) | pre-solve gate (§6); 1 pilot node added (108,253 nodes) |

## 6. Acceptance checks for S3 (before its results are used)

1. **Written solver input:**
   - U_z and U_θ are on exactly the 1,224/2 = 612 inlet-face nodes.
   - The outlet face nodes carry no D constraint.
   - One remote pilot node with UX = UY = UZ = 0 and free rotations.
   - An RBE3-type (deformable) coupling to the 612 outlet-face nodes.
   - No other constraints.
2. **Static equilibrium:** the inlet reaction equals the pilot reaction, and the axial force is within 1 % of the S1 value (548.94 kN). Otherwise the axial restraint is not "full".
3. **Mid-span mean axial stress** within 0.5 % of S1 (−582.44 MPa), and the peak location and value reported with any change.
4. **Buckling mode classified** with `mode_shapes.py`. The expected shape is fixed–pinned. The pilot-node region is checked for local, artificial modes.
5. **The benchmark (B03) passed** before the project S3 result is reported.
