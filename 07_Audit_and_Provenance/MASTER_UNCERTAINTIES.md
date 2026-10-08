# MASTER UNCERTAINTY REGISTER — Section 10A

> **RE-ANALYSIS 2026 — Re-analysed / Assumed / Simulated 2026.** All sizes below come from 2026 simulations and calculations of
> the re-analysed problem. No experimental data exist, so no uncertainty is a comparison with measurement.

## 1. Rule

**The nine sources are kept separate. No combined uncertainty percentage is formed.**

The sources are of different kinds and cannot be added:

- discretisation errors: 1, 3 in part, 4;
- model-form and idealisation errors: 2, 7, 8, 9;
- data scatter: 5;
- an assumption: 6.

Several are one-sided (known sign). Some are not quantified at all. A root-sum-square or linear sum would therefore have no
mathematical basis. Each entry states what it affects, its size where known, and the evidence.

**Numbering.** The 9B-2 register (`PROJECT_STATE.md` §19.6, `FINAL_PARAMETRIC_AUDIT.md`) lists eight sources, with
"imperfection / nonlinear buckling" as one entry. The 10A brief asks for nine, so that entry is split here into geometric
imperfection (8) and nonlinear material / inelastic buckling (9). The content is unchanged.

## 2. Register

| # | Source | Affects | Size (evidence) | Class |
|---|---|---|---|---|
| 1 | **CFD mesh (discretisation)** | wall temperatures → LC2 stress, end force, λ₁, growth | 6B three-mesh study, status B (approximately convergent). T_max medium 562.58 K vs extrapolated 558.13 K, GCI_fine 3.4 K (1.3 % of the rise); medium band −5.1 / +1.6 K. Nu_fd, f_fd GCI 1.8 %; geometry-adjusted Δp 0.9 %; mid-span ΔT_wall 0.03 K. Structural effect (7B / 8B): LC2 stress −10.1 / +2.8 MPa, local peak −13.7 / +4.3 MPa, λ₁ +1.8 / −0.5 %, free growth −32 / +9 µm, utilisation 0.568–0.581. The medium field is slightly hot, so these results lean conservative. T03 solid layers (M03): ≤ 0.20 K | **secondary** |
| 2 | **CFD thermal-property / turbulence-model form** | h and the whole temperature field | Not quantified by a model-form study. Indicators: CFD Nu_fd 54.17 is 9 % above the property-corrected correlation (49.6) and inside the 44–67 band. CFD f_fd is 10.4 % below Petukhov, a gas-heating effect ×0.910 (F-029, F-034). The CFD–analytical T_max gap is −19.1 K, of which −15.0 K comes from the higher CFD film coefficient and −4.2 K from axial conduction (F-010). The volume-mean rise is ≈ 30 K below Section 2 (F-027). Temperature-basis sensitivity (8A): the Section 2 basis would give λ₁ ≈ 0.98 instead of 1.108. Also: air table ends at 600 K (Q03 air side 583.4 K, F-049); uniform-flux idealisation (A-010); radiation neglected (A-015, T-009); inlet TI assumed (A-020b) | **secondary** (largest thermal source) |
| 3 | **CFD → Mechanical temperature mapping** | local temperatures; LC1 inlet peak most | Mapping error (A) ≤ 0.081 K inside the source mesh (7A), 0.086–0.154 K across the 9B cases. Numbering sensitivity (C00): ≤ 0.081 K; effect LC2 peak 9.5 × 10⁻⁶, λ₁ −4.2 × 10⁻⁷, LC1 inlet peak −0.46 %. Near-inlet transfer limitation (F-035): Fluent node reconstruction differs from cell values by up to 2.6 K within ~11 mm of the inlet; bound on the LC1 inlet peak ±9.8 MPa (≈ 40 % of 24.28 MPa), on the LC2 peak 1.6 % (F-040). Interior values are robust | **smaller** (except the LC1 inlet peak, which drives no decision) |
| 4 | **Structural mesh (discretisation)** | surface stresses | 8B, 7 meshes. LC2 peak and mean: class A; the largest change against mesh B is 4.9 × 10⁻⁴ (recomputed, XC, the coarsest). λ₁ ≤ 5.4 × 10⁻⁵ across all meshes, ≤ 6 × 10⁻⁶ between the fine meshes and B. LC1 mid-span bore σθ −2.1 % vs the 1-D exact value (sign known, F-046); LC1 inlet peak +1.1 %. Thickness meshes (M01 / M02): LC2 mean and λ₁ ≤ 4.2 × 10⁻⁶, LC2 peak ≤ 1.4 × 10⁻⁴ (M01 exceeds the 10⁻⁴ class-A tolerance at one node), LC1 peak ±1.4 % | **smallest** |
| 5 | **Material properties** | E(T), α(T) → stress and end force (∝ E·α); S_y(T) → utilisation | Datasheet tables (VDM 4127 / Special Metals), generic heat (A-018). About ±2 % on E and α (8B assessment). S_y values are typical, not minimum-guaranteed, so the utilisation is not a certified margin (A-022). No temperature-dependent stress–strain curve (F-045) | **secondary** |
| 6 | **Poisson's ratio 0.294 [ASSUMED]** | LC1 radial and hoop stresses; λ₁ only through the shear correction | Not varied (T-014 / F-011). Literature range 0.284–0.294. Section 2 estimate: ≈ 1.4 % on LC1, none on the uniaxial LC2 axial stress | **smaller** |
| 7 | **End-restraint (support) definition** | λ₁ (dominant), which mechanism comes first | S1 1.108 · S3 2.232 · S2 4.300 at identical static stress (< 0.01 % difference): a factor of 3.9 from the supports alone. The mechanism switches from buckling-first (S1) to first-yield-first (S2, S3). The real flange restraint is undefined (T-034). 9A beam-column estimate (rotation-fixed ends): λ₁ ≥ 1.73 needs ≈ 0.71 kN/mm relative lateral stiffness between the ends. Rotational flexibility would lower λ₁ below S1 (conceptual K = 2: λ ≈ 0.28) | **PRIMARY** |
| 8 | **Geometric imperfection** (out-of-straightness, eccentricity, residual stress) | real buckling / deflection behaviour | Not modelled. λ₁ is the bifurcation factor of a perfect tube; imperfections cause lateral deflection growth below λ₁ and lower the real capacity. Size unknown until an imperfection-sensitive nonlinear analysis is run (T-035) | **PRIMARY** (part of stability modelling) |
| 9 | **Nonlinear material / inelastic buckling** | capacity for λ₁ near or above the proportional limit | All cases are intermediate columns: KL/r 49.7–58.3 (S1) < C_c ≈ 60. Elastic σ_E ≈ 650 MPa exceeds the conventional proportional limit. 8A conventional Johnson factors: 1.058 (S1), 1.414 (fixed–pinned), 1.581 (fixed–fixed); squash 1.755. No material-specific tangent-modulus data (T-036) | **PRIMARY** (part of stability modelling) |

## 3. Ranking supported by the evidence

1. **Primary: the end-support condition and the stability modelling (sources 7, 8, 9).**
   - The support choice alone changes λ₁ by a factor of 3.9 and reverses the order of the mechanisms.
   - Imperfections and inelasticity can only lower the real capacity below the linear λ₁, by an unquantified amount.
2. **Secondary: the thermal field and its model (sources 2, 1, 5).**
   - The model-form indicators (19 K on T_max; ≈ 30 K on the mean rise between the analytical and CFD levels) are larger than the CFD mesh band (−5.1 / +1.6 K).
   - The material scatter (≈ ±2 %) is of the same order as the CFD mesh effect on stress and λ₁.
3. **Smaller: mapping, structural discretisation and ν (sources 3, 4, 6).** Each changes the governing LC2 and λ₁ results by ≤ 10⁻⁴ (mapping, mesh) or has no effect on them (ν). The exception is the LC1 inlet peak (mapping ±9.8 MPa), which drives no decision.

This ordering matches the 8B buckling-uncertainty ranking: supports ≫ temperature basis ≫ CFD mesh ≈ material ≫ mapping ≫ structural mesh.

## 4. What the uncertainties mean for the λ₁ < 1 classification (indicative)

The CFD-mesh band (+1.8 / −0.5 %) and the material band (≈ ±2 %) were established for P00. Applied indicatively to the parametric cases:

| Case | λ₁ (S1) | Distance from 1 | Reading |
|---|---|---|---|
| V01 | 1.00307 | +0.31 % | inside the thermal / material bands: its side of 1 is **not robust** |
| Q03 | 0.98834 | −1.17 % | inside the bands: its side of 1 is **not robust** |
| T01 | 0.94497 | −5.50 % | outside the thermal / material bands; inside the support uncertainty |
| P00 | 1.10805 | +10.8 % | outside the thermal / material bands; inside the support uncertainty |

Every S1 classification sits inside the support uncertainty (source 7) and above the unquantified imperfection / inelastic
reductions (8, 9). The λ₁ values rank the design cases only within the idealised S1 model.

## 5. Method limitations that are not numerical uncertainties

- **One factor at a time.** The V × q″ interaction is about 8–11 % of the main effects (9A). Combined off-baseline states cannot be obtained by adding the one-factor changes, and no response surface was fitted.
- **Operating envelope.** V ±10 %, q″ ±10 % and t ±20 % only. The limits come from the 600 K air table and the 128,000-node licence.
- **Linear eigenvalue buckling only.** No post-buckling path, collapse load or deflection limit was computed.
