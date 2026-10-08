# Section 8A: LC2 stability check (linear buckling)

> **RE-ANALYSIS 2026.** These are new ANSYS Mechanical 2026 R1 (Student) linear-buckling solutions of the re-analysed duct in its solved LC2 state, plus an independent hand estimate.
>
> - Nothing here is a recovered internship result, and no experimental data exist or are used.
> - The pre-stress is the actual LC2 thermal-structural state: the mapped CFD temperature field, T_ref 300 K, and the LC2 supports.
> - The thermal field was **not** replaced by an arbitrary load.
> - The existing LC1/LC2 results were **not** modified. LC2 was re-solved in a save-as copy and reproduced 7B exactly (§2).
> - **Hand calculation:** `BUCKLING_HAND_CALCULATION.md`. **Audit trail:** `BUCKLING_AUDIT.md`.

## 1. Answers

| Question | Answer |
|---|---|
| Applied LC2 compressive load | **N = 548,936.6 N** (end reaction), i.e. a mean axial stress of **582.44 MPa**. The 605.16 MPa von Mises peak is a local stress, not the column load |
| Analytical estimates | Euler with E(z) (shear-corrected in brackets), load factor = P_cr/N: **guided (= LC2 supports) 1.119 (1.104)**; pinned–pinned 1.114 (1.099); fixed–pinned 2.29 (2.22); fixed–fixed 4.47 (4.23). Johnson inelastic: 1.058 / 1.058 / 1.414 / 1.581 |
| Slenderness | L/r = 53.67 (r = 11.18 mm). KL/r = 53.7 (K = 1), 37.5 (K = 0.7), 26.8 (K = 0.5) |
| Euler appropriate? | **Only as a first estimate.** All cases are intermediate columns (KL/r < C_c = 60.2), and σ_E ≈ 650 MPa exceeds the conventional proportional limit. Euler is an elastic upper bound |
| ANSYS Linear Buckling solved? | **Yes.** Linear Buckling linked to the LC2 static solution; 108,252 nodes, within the Student limit; Block Lanczos; 6 modes |
| First load factor | **λ₁ = 1.1080** (mode 2 = 1.1080, the same mode in the orthogonal plane) |
| Dominant mode | **Global column (Euler-type) sway buckling.** The two end planes stay perpendicular to the axis but translate sideways in opposite directions; there is no lateral deflection at mid-span. Cross-section distortion is < 10⁻⁶ of the lateral motion, so there is no shell or local mode |
| How close to the applied load | The predicted instability load is only **10.8 % above** the applied LC2 force, about 24 K more mean temperature rise. First yield occurs at about 1.73 × the LC2 state, so **under the LC2 idealisation the duct would become unstable before it yields** |

## 2. Model and workflow

**The model.** The solved 7B project was saved as `Buckling/Workbench/Flow_Behavior_Thermal_Effects_Buckling_8A.wbpj`, and an *Eigenvalue (Linear) Buckling* system was added whose Setup receives the LC2 Solution. The pre-stress environment was read back from Mechanical as `LC2_Axially_Restrained`.

**What MAPDL does** (`Mechanical/LC2_Linear_Buckling/Solver_Output/ds.dat`, `solve.out`):

- It restarts from the LC2 static solution as a linear perturbation: `antype,,restart,,,perturbation` and `perturb,buckle,,CURRENT,ALLKEEP`.
- It keeps all LC2 boundary conditions.
- It builds the stress-stiffness matrix from the LC2 stress state.
- It solves [K + λ K_σ] φ = 0 with Block Lanczos (`bucopt,lanb,6,,,range`: positive multipliers only).
- The solver notes: "the prior (base) analysis is LINEAR, use the total load prescribed… to calculate the critical eigen-buckling loads".

**What λ means here.** λ multiplies the **whole LC2 load state**, which is the restrained thermal loading of the mapped temperature field.

**The pre-stress state is the 7B one.** Linking the buckling system switches LC2 to "pre-stressed" output, so LC2 was re-solved in the copy. The re-solved maximum von Mises (605,160,873.381 Pa) and inlet reaction (548,936.6138 N) are **identical** to 7B to all printed digits. Its solver input matches the 7B input section by section: nodes, elements, BFBLOCK, material and resolved constraints.

**Licence.** The Student licence ran the linear buckling of the full 108,252-node model without any licence message. The eigen-solve took 272 s. The Lanczos workspace ran in-core; the sparse factorisation ran out-of-core, which is only a performance warning.

## 3. Results: LC2 supports (U_z = 0 on both end faces, radial free, 3 mid-span hoop nodes)

| Mode | Load factor λ | Critical axial force λ·N | Shape (from the corner-node eigenvector, `mode_shapes.py`) |
|---|---|---|---|
| **1** | **1.10805** | **608.2 kN** | guided-column sway, n = 1: lateral deflection ∝ cos(πz/L) (correlation 1.000); ends deflect in opposite directions; mid-span lateral deflection 1.4 × 10⁻⁵ of the maximum; 99.9999 % rigid-section (beam) motion |
| 2 | 1.10805 | 608.2 kN | the same mode in the orthogonal plane (90.0° from mode 1). The pair is repeated because the section is axisymmetric |
| 3 | 4.29790 | 2359.3 kN | second guided mode ∝ cos(2πz/L) (correlation 0.9999): both ends move together relative to mid-span. This is the clamped–clamped (no-sway) Euler shape |
| 4 | 4.29791 | 2359.3 kN | orthogonal pair of mode 3 |
| 5 | 9.22482 | 5063.8 kN | third bending mode (cos 3πz/L type) |
| 6 | 9.22483 | 5063.8 kN | orthogonal pair of mode 5 |

**Where the instability acts.** Mode 1 is a whole-length column mode.

- The largest lateral displacement is at the two **end faces**, which translate sideways relative to each other.
- The bending curvature is largest in the end sections, which are held against rotation, and zero at mid-span.
- The inlet end, where the LC2 von Mises peak already sits, therefore also receives the largest buckling bending stress.

**No local or shell mode appears.** None of the six lowest modes shows ovalisation, lobing or an end-local shape. The cross-section in-plane distortion is below 10⁻⁶ of the lateral motion in all six. This confirms the hand screen (`BUCKLING_HAND_CALCULATION.md` §6).

**Figures.**

- `figures/Mechanical/LC2_Linear_Buckling_Mode_1_Total_Deformation_{iso,side_YZ,top_XZ}.png` and `…Mode_2_…`: Mechanical renders, auto-scaled deformation. Mode shapes have no physical amplitude.
- `figures/F8A_01_buckling_mode_1_shape.png`, `F8A_02_buckling_mode_2_shape.png`: the lateral deflection of the duct axis extracted from the eigenvectors.

## 4. Comparison of FE and hand estimates (LC2 supports = guided column, K = 1)

| Estimate | Load factor | FE vs estimate |
|---|---|---|
| **FE linear buckling (mode 1)** | **1.1080** | — |
| Euler, E(z) Rayleigh | 1.1194 | −1.0 % |
| Euler + Engesser shear correction | 1.1036 | +0.4 % |
| Euler, hot-end E (lowest) | 1.1040 | +0.4 % |
| Johnson (conventional inelastic) | 1.058 | +4.7 % |

**Agreement.** The FE eigenvalue sits between the plain and the shear-corrected Euler values, exactly as in the constant-property benchmark (`BUCKLING_AUDIT.md` §3). This confirms three things:

- the supports act as a guided column (K = 1);
- the mid-span hoop constraint does not stiffen the mode;
- the FE load factor scales the correct force (548.9 kN).

**What the FE value is and is not.** It is an **elastic** bifurcation value: it uses E(T), not a tangent modulus.

- The corresponding stress, 1.108 × 582.4 = 645 MPa, lies in the intermediate range, where inelasticity lowers the real capacity.
- The Johnson figure (1.06) indicates the likely direction and size of that reduction. It is not a material-specific result (no stress–strain curve is available).

## 5. End-condition sensitivity (LC2NS, NOT the LC2 definition)

**Purpose.** The real duct will sit between flanges whose lateral stiffness is unknown. A second static + buckling pair was therefore solved with **U_z = 0 and U_θ = 0 on both complete end faces** (cylindrical CS, radial still free). This holds the ends against lateral sway as well as rotation. The temperature field, material and mesh are identical to LC2.

It is a bounding sensitivity case. It is not a claim that the real supports are clamped.

**Same pre-stress.** The LC2NS static state matches LC2:

- end reaction 548,936.61 N (identical);
- maximum von Mises 605.1596 MPa vs 605.1609 MPa, a 2 × 10⁻⁶ difference. The end U_θ restraint does not change the axisymmetric thermal state.

| Mode | Load factor λ | Critical force | Shape |
|---|---|---|---|
| **1 (and 2)** | **4.29995** | 2360.4 kN | clamped–clamped (no-sway) Euler shape 1 − cos(2πz/L) (correlation 1.000): largest lateral deflection at mid-span, none at the ends; 99.999 % rigid-section motion |
| 3 (and 4) | 8.35615 | 4587.0 kN | second clamped mode (antisymmetric; largest deflection at z ≈ 184 mm) |
| 5 (and 6) | 15.4244 | 8467.0 kN | third bending mode |

**Comparison with the hand estimate.** Hand fixed–fixed Euler with E(z): 4.471; with shear: 4.229. The FE (4.300) lies between them, as in the benchmark. It also equals mode 3 of the LC2 model (4.298), because a guided column's second mode is the clamped shape.

**What this sensitivity shows.**

- Holding the ends laterally removes the sway mode and raises the *elastic* buckling factor about fourfold, from 1.108 to 4.300.
- That elastic value corresponds to 4.3 × 582 = 2,500 MPa, far above yield, so it is not a real capacity.
- With lateral end restraint the duct becomes a stocky column. Its capacity is then limited by material yield and inelastic buckling: Johnson ≈ 1.58, squash 1.75, first yield of the LC2 stress state 1.73.
- **The end supports decide whether the duct is stability-critical (sway free, λ ≈ 1.1) or yield-critical (laterally held, about 1.6–1.7).**

## 6. Load factor vs applied load

| Quantity | Value |
|---|---|
| Applied axial force (LC2) | 548,936.6 N |
| Critical axial force, FE mode 1 (LC2 supports) | 608,248 N |
| **Buckling load factor (FE)** | **1.108**: instability at +10.8 % load |
| Hand range, LC2 supports (Johnson … Euler) | 1.06 … 1.12 |
| Hand range, all plausible end conditions (Johnson … Euler) | 1.06 … 4.47 |
| First-yield factor of the LC2 stress state (7B, 1/0.578) | 1.73 |
| Equivalent temperature margin (approximate) | about +24 K of mean temperature rise (225.5 → about 250 K) |
| On the Section 2 temperature basis (254.7 K rise = 1.129 × N) | λ ≈ 1.108/1.129 = **0.98**, i.e. below 1 |

**A factor of 1.108 does not mean "safe".** It is a *theoretical elastic bifurcation* of a *perfect* tube with *idealised* supports (§7). A load factor this close to 1 means that very small departures from the ideal (well within normal tolerances) can remove the margin entirely.

## 7. What linear buckling does and does not establish

**It does establish:**

- the load multiplier at which the ideal, perfectly straight, linear-elastic structure under the LC2 stress pattern has a bifurcation (an alternative equilibrium);
- the shape of that bifurcation mode;
- the ranking of the modes.

**It does not establish:**

- the load at which a *real* duct collapses or deflects excessively;
- the post-buckling path;
- any effect of plasticity;
- the effect of geometric imperfections;
- the change of E(T) if the temperature rose further. The eigen-solution keeps the stiffness of the present temperature state while λ scales the thermal load; for λ ≈ 1.1 the extra heating would lower E by only about 0.5 %.

**A real duct.** For a real structure the linear eigenvalue is generally an *upper* estimate of the instability load.

**The effect of thermal restraint.** Because the LC2 compression comes from restrained expansion (displacement control), exceeding the critical state would appear as progressive lateral bowing that sheds part of the axial force, not as a sudden collapse. That bowing adds bending stress to the 582 MPa compression and therefore brings first yield forward (see §8).

## 8. Why a factor close to 1 is concerning (qualitative, no invented numbers)

- **Geometric imperfections.** Any out-of-straightness, wall-thickness variation or end-face squareness error makes the duct bow from the start of heating. Deflection grows sharply as the load approaches the critical value (amplification ≈ 1/(1 − N/N_cr)), so the bending stress is amplified well before λ = 1.108. This was not quantified: no tolerance data exist, and no nonlinear analysis was run.
- **Residual stress.** Welding or forming residual stresses add to the 582 MPa compression and can cause early local yielding, which lowers the tangent stiffness.
- **Restraint uncertainty.** This is the largest single factor.
  - Ends free to sway (the LC2 idealisation) give λ ≈ 1.1.
  - Ends clamped laterally give an elastic λ ≈ 4.3 (§5), but that capacity is then limited by inelastic behaviour (Johnson 1.58, squash 1.75).
  - Partial lateral stiffness lies in between, and a K of about 1.2 for imperfectly guided ends would give λ < 1.
  - The actual flange and support design is **not defined** in this project.
- **Material uncertainty.**
  - E(T), α(T) and S_y(T) are datasheet values; ν is [ASSUMED].
  - The stress–strain curve that governs inelastic buckling in the 600–650 MPa range is not available.
- **Thermal-field uncertainty.**
  - The restrained force scales with the mean temperature rise.
  - The 6B CFD mesh uncertainty (−3.6/+1.0 K on the mean) moves λ by only about +1.8/−0.5 %.
  - The CFD *model* uncertainty is larger (Nu/h correlation: about 19 K on T_max).
  - The Section 2 temperature basis would already give λ < 1.
- **Nonlinear post-buckling behaviour.** Not analysed. A geometrically and materially nonlinear analysis with an imperfection would be needed to predict the actual deflection and the load at yield or collapse.

## 9. Conclusion

**Under the LC2 idealisation, stability, not first yield, governs.**

- With both end planes held against axial motion but free to translate sideways, the FE predicts a global sway-buckling load only **10.8 % above** the applied restrained thermal force (λ₁ = 1.108). The hand estimates confirm it: 1.06–1.12.
- First yield of the unbuckled duct would occur only at about 1.73 × the LC2 state.
- The first-yield utilisation of 0.578 found in 7B **is not a structural margin**.

**The component cannot be called safe on the present evidence.** Whether the real duct is adequate depends on:

- the lateral and rotational stiffness of its end supports;
- geometric tolerances;
- the inelastic material behaviour.

None of these is defined in this project.

## 10. Remaining limitations and unresolved stability concerns

1. **F-043 (High).** LC2 as idealised (sway-free ends) has an elastic buckling load factor of only 1.108, below the first-yield factor of 1.73. The real end restraint must be specified before any margin is claimed.
2. **F-044 (Medium).** No imperfection-sensitive or nonlinear (large-deflection + plasticity) buckling analysis has been performed. The collapse or excessive-deflection load of a real duct is unknown and expected to be *below* the linear value.
3. **F-045 (Medium).** Inelastic buckling data are missing: no stress–strain / tangent-modulus data for age-hardened Inconel 718 at 150–290 °C. The Johnson values are conventional, not material-specific.
4. **The end-condition range is wide:** λ from about 0.8 (imperfect guided, design K = 1.2) to about 4.3 (elastic, clamped against sway). Only the two FE bounds and the hand range are quantified.
5. **Thermal-field model uncertainty** (h/Nu correlation, radiation) is not propagated beyond the 6B mesh uncertainty. The Section 2 basis shows that a hotter field would give λ < 1.
6. **One structural mesh** (the same as 7B). The global mode is resolved by 130 axial divisions, and the benchmark agrees with theory to within 0.3 % and 3 %. A buckling mesh study was not run (not requested).
7. **Poisson's ratio [ASSUMED]:** a small effect on the global mode.
