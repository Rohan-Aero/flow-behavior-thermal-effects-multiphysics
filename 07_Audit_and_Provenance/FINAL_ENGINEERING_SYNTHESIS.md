# FINAL ENGINEERING SYNTHESIS — Section 10A

> **RE-ANALYSIS 2026 — Re-analysed / Assumed / Simulated 2026.** The original Eleation internship files (Feb–May 2025) were lost.
> This synthesis tells the technical story of the **2026 re-analysis**. Every number in it is one of three things:
>
> - an input chosen in 2026;
> - a 2026 hand calculation;
> - a 2026 ANSYS Student 2026 R1 simulation.
>
> No number is recovered internship data. No experimental or measured data exist, and none are implied.

**What this document is.** An engineering synthesis, not report prose. Every value is taken from `MASTER_PROJECT_DATA.csv`
(IDs M001–M182, cited as [Mxxx]). Values without an ID are REPORTED from the named section document. Source files are listed in
`MASTER_TRACEABILITY.md`.

**Modelling levels** (a number means something only together with its level):

| Level | Meaning |
|---|---|
| ANALYTICAL | Section 2 1-D correlations |
| CFD-MEDIUM | official baseline CFD |
| CFD-FINE | verification reference |
| CFD-EXTRAPOLATED | Richardson limits |
| FE-STATIC, FE-BUCKLING | official Mechanical results |
| FE-MESH-STUDY | Section 8B mesh variants |
| 9B cases | parametric CFD + FE |

---

## 1. Engineering problem

- **Component.** A thick-walled Inconel 718 duct, heated uniformly on its outer surface and cooled by turbulent air flowing through its bore. **[Re-analysed]**
- **Question.** How the flow, the conjugate heat transfer and the resulting wall-temperature field load the duct structurally. Three mechanisms are examined:
  - free thermal expansion (LC1);
  - fully restrained axial expansion (LC2);
  - linear stability of the restrained duct.

  The study also covers how these depend on the operating parameters, the design parameters and the end supports.
- **Workflow (one-way):**
  1. Fluent conjugate CFD (steady);
  2. converged solid temperature field;
  3. mesh-based transfer to Mechanical;
  4. static LC1 / LC2;
  5. linear eigenvalue buckling on the LC2 pre-stress;
  6. one-factor parametric study (V, q″, t);
  7. support sensitivity (S1 / S2 / S3).
- **Why one-way coupling is admissible.** The flow-area change from thermal growth is 0.70 % (Section 2) [M015]. No structural feedback to the flow is modelled, and no two-way or FSI result exists.
- **Historical frame.** Only the following are historical facts (`MASTER_ASSUMPTIONS.md` §1.1):
  - the title;
  - the organisation;
  - the period;
  - the engineer;
  - the tools: Workbench, Fluent, Mechanical.

  The problem definition itself is a 2026 re-analysis.

## 2. Geometry

| Item | Value | Basis |
|---|---|---|
| D_i / D_o / t / L | 20 / 40 / 10 / 600 mm [M023–M026] | re-analysed class B (D-008: D_o/D_i = 2, L/D = 30) |
| D_h; flow area | 20 mm; 314.159 mm² [M027, M028] | CAD, VERIFIED |
| Solid volume | 5.654867 × 10⁻⁴ m³ [M029] | CAD, VERIFIED |
| Heated area | 0.0753982 m² true cylinder [M030]; 0.0753444 m² CFD 48-facet [M031] | the 0.071 % difference is exact faceting (F-031) |
| Section (FE) | A 942.48 mm², I 117,810 mm⁴, r_g 11.18 mm, L/r 53.67, D/t 4, R/t 1.5 | 8A |

- **CAD.** SpaceClaim, two bodies (fluid, solid) with shared topology and named selections carried into Fluent and Mechanical (Section 3).
- **CFD vs FE geometry.** The CFD uses the inscribed 48-gon; the FE uses the true circle (A-029). The 0.038 mm chord gap is handled by the mapping (F-038).
- **Thickness cases.** T01 (t 8 mm, D_o 36) and T03 (t 12 mm, D_o 44) were built as new parametric CAD models. Their dimensions, areas and volumes match the analytical values to ≤ 5 × 10⁻¹⁴ % (9B-1).

## 3. Physics

| Aspect | Model | Justification |
|---|---|---|
| Flow | steady, turbulent, incompressible ideal gas (ρ = p_op/RT) | Re 29,958 → 25,545 [M034, M035]; Δp 0.43 % of p_op; Mach ≤ 0.091 (A-004, A-005) |
| Turbulence | k-ω SST, wall resolved (no wall function) | y⁺ max 0.585 [M046] (D-011) |
| Heat transfer | conjugate: air convection + solid conduction, conformal interface, perfect contact | A-020 |
| Heating | uniform q″ = 8000 W/m² on the outer wall (16,000 W/m² at the bore equivalent); adiabatic end faces [M006] | A-010, A-011 (idealisations) |
| Neglected | buoyancy (Ri 4.4 × 10⁻⁵); viscous dissipation (Br 1.8 × 10⁻³); radiation (A-015, not tested) | A-007, A-008, A-015 |
| Air properties | c_p, μ, k piecewise-linear 250–600 K | D-021 |
| Solid properties | k(T), c_p(T) 293–673 K; ρ 8190 kg/m³ [M008, M009] | D-026 |
| Structure | linear elastic, small deflection; E(T), secant α(T) re-referenced to T_ref = 300 K; ν 0.294 [ASSUMED] [M010–M014] | D-036, D-041 |
| Thermal strain | ε_th = α_s(T)·(T − 300 K) on the full mapped field | D-041 |
| Stability | linear eigenvalue buckling on the LC2 thermal pre-stress; λ multiplies the whole LC2 thermal load | 8A |

**Governing physical picture (confirmed by every later phase).**

- The air film carries most of the thermal resistance: R_cond/R_conv = 0.035 in Section 2, and the film takes 96.6 % of the wall-to-air temperature difference.
- The wall therefore runs hot (≈ 525 K mean) with only a small through-wall gradient.
- Free expansion (LC1) produces small stresses. Preventing the expansion (LC2) produces a large, almost uniform axial compression. That compression is the column load for buckling.

## 4. Analytical baseline (Section 2, ANALYTICAL level — kept as the historical reference, not a final result)

| Quantity | Section 2 value | Final simulated value (for orientation) |
|---|---|---|
| Q (true cylinder) | 603.186 W [M071] | 602.755 W CFD-MEDIUM on the 48-gon [M038] |
| T_out | 368.85 K [M072] | 368.93 K [M037] |
| Δp (CFD-comparable) | 441.53 Pa [M073] | 438.13 Pa [M036] |
| Max solid T (outer wall, exit) | 581.71 K [M074] | 562.58 K [M039] |
| Through-wall ΔT (exit station) | 7.285 K [M075] | 7.36 K at z = 570 mm; 7.581 K mid-span [M041] |
| Free axial growth | 2.0964 mm [M076] | 1.8409 mm [M085] |
| LC1 peak von Mises (Timoshenko, mid-span) | 16.313 MPa [M077] | 18.20 MPa mid-span bore; 24.282 MPa inlet-end peak [M086] |
| LC2 axial stress (−E·α·ΔT_mean) | −657.227 MPa [M078] | mean −582.440 MPa [M092] |
| S_y at 281.6 °C | 1023.7 MPa [M079] | S_y(T) at the critical node 1047.0 MPa [M094] |
| LC2 utilisation | 0.6420 [M080] | 0.5780 [M095] |
| LC2 / LC1 ratio | 40.3× | 32× mid-span; 25× peak to peak |

**Why the levels differ.** Each difference is explained; none was reconciled by editing either side.

- **Q, T_out.** The CFD Q is exactly the 48-gon lateral-area ratio (−0.071 %). T_out +0.08 K is the matching faceting effect.
- **T_max −19.1 K.** −15.0 K comes from the higher CFD film coefficient (83.6 vs 77.5 W/m²K) and −4.2 K from axial conduction at the adiabatic outlet end (F-010). Mesh refinement moves the CFD further from the analytical value, so the gap is not a mesh artefact.
- **Mean temperature rise.** Section 2 has 254.7 K, the CFD ≈ 225.5 K (−11 %, F-027). The cause is the film coefficient along the whole duct, the thermal entrance and axial conduction at the cold inlet end (inlet wall 423 K in the CFD vs 529.6 K in Section 2). Free growth and LC2 stress scale with this rise. Section 2 rescaled to the CFD mean rise gives −581.9 MPa, against the FE −582.44 MPa.
- **S_y values.** 1023.7 MPa (Section 2, at the mean temperature), 1020 MPa (7A Engineering Data scalar, a lower bound, not used for utilisation) and 1047.0 MPa (7B, at the critical-node temperature) are three different quantities (L-14).

**Section 2 central hypothesis:** "restraint dominates the through-wall gradient by ≈ 40×". It was **confirmed in kind**, at 32× mid-span in the FE.

## 5. CFD methodology

| Item | Setting |
|---|---|
| Software | ANSYS Fluent 2026 R1 Student (4-core cap), Workbench |
| Solver | pressure-based coupled, steady, absolute velocity |
| Discretisation | first order to iteration 300, then second-order upwind on all equations |
| Staging (D-030) | flow + k-ω for iterations 1–150; + energy 151–300; second order 301–600; confirmation 601–700 |
| Mesh (official) | **medium, 159,840 cells** [M033]: butterfly O-grid hexahedra, 48 circumferential × 90 axial, 12.2 µm first fluid layer, 24 inflation layers; 116,640 fluid + 43,200 solid cells; conformal fluid–solid interface; orthogonal quality min 0.446, skewness max 0.760 |
| Inlet | 23.5 m/s uniform, 300 K, TI 4.411 % (0.16 Re^−1/8) [M002–M004] (A-020b, ID collision noted in L-04) |
| Outlet | 0 Pa gauge; operating pressure 101,325 Pa [M005] |
| Walls | outer: q″ 8000 W/m²; ends: adiabatic; interface: coupled |
| Post-processing | area-weighted static pressure (Δp); mass-weighted T_out; flux reports (Q, balances); maximum-of-facet report (T_max); exports of the cell and node fields |
| Run cost | 700 iterations, 12 min 58 s on 4 cores |

## 6. CFD convergence

| Criterion | Result (medium) |
|---|---|
| Convergence decision | refused at 500 (second-order transient; T_out drift 0.42 K); **converged at 600, confirmed at 700** [M049] |
| Final residuals | continuity 9.0 × 10⁻¹¹; momentum ≤ 1.6 × 10⁻¹⁴; k / ω ≤ 7.2 × 10⁻¹³; energy 1.6 × 10⁻¹⁴ |
| Physical monitors | T_out drift over the last 200 iterations 2.3 × 10⁻⁶ K |
| Conservation | mass imbalance 7.0 × 10⁻¹³ % [M047]; energy imbalance 3.1 × 10⁻¹¹ % [M048] |
| Range checks | fluid 299.998–553.42 K and solid 300–562.13 K, inside both property tables at every iteration; 0 limiter / divergence messages; 0 reverse-flow cells |
| Discretisation-order sensitivity | first → second order: T_solid,max +0.34 K, Δp −0.19 % |

- The fine and coarse meshes converged with the same schedule. Fine imbalances: 3.9 × 10⁻¹² % / 6.2 × 10⁻¹¹ %.
- All 7 parametric CFD cases converged at 600 and held at 700: mass ≤ 4.2 × 10⁻¹⁴, energy ≤ 1.3 × 10⁻¹², drift ≤ 6.1 × 10⁻⁵ K.

## 7. Mesh independence (Section 6A / 6B)

| Quantity | Coarse 51,840 | **Medium 159,840** | Fine 500,580 | Extrapolated | M→F change | Status |
|---|---|---|---|---|---|---|
| Δp [Pa] | 437.09 [M059] | **438.13** | 439.12 [M051] | 441.81 (geometry-adjusted) [M070] | +0.23 % | B |
| T_out [K] | 369.12 [M060] | **368.93** | 368.85 [M052] | — (geometry) | −0.08 K | D (faceting) |
| Q [W] | 602.217 [M061] | **602.755** | 602.994 [M053] | 603.186 (exact circle) | +0.04 % | D (faceting) |
| T_max [K] | 565.40 [M062] | **562.58** | 560.83 [M054] | 558.13 [M066] | −1.75 K | B |
| ΔT_wall mid-span [K] | 7.554 [M063] | **7.581** | 7.597 [M055] | 7.620 [M067] | +0.21 % | B |
| Nu_fd | 53.38 | **54.17** | 54.66 [M056] | 55.43 [M068] | +0.91 % | B |
| f_fd | 0.02134 | **0.02163** | 0.02181 [M056] | 0.02212 [M069] | +0.85 % | B |
| y⁺ max | 0.522 [M065] | **0.585** | 0.653 [M057] | — | — | B / E (sampling) |

- **Method.** Celik (2008) with r ≈ 1.46. The geometric faceting changes (ṁ, Q, T_out) were separated **exactly** and are never called mesh error (D-035).
- **Result.** Status **B, approximately convergent**, for every flow and thermal quantity. No quantity is still changing materially. The apparent order is 1.2–1.6, below the formal 2 (F-032). **Strict mesh independence is not claimed.**
- **GCI (fine):**
  - T_max 3.4 K (1.3 % of the rise);
  - Nu_fd and f_fd 1.8 %;
  - Δp (geometry-adjusted) 0.89 %;
  - ΔT_wall 0.029 K.
- **Decision D-034: medium = official baseline; fine = verification reference only.**
  - The medium error is small and conservative for the structural phase: T_max +4.4 K and volume mean +3.1 K above the extrapolated values; mid-span ΔT_wall 0.04 K low.
  - The fine solid (≈ 157 k nodes) would not fit the measured 128,000-node Student structural limit.
- **Friction finding (F-029).** The medium f_fd is −10.4 % from Petukhov (PR-04 marginally not met; not re-interpreted). Decomposition: Re basis × 1.011 · isothermal SST × 0.974 · gas heating × 0.910. It is mainly a variable-property (gas-heating) effect that the constant-property correlation omits. About 5 points remain unresolved (F-034).

## 8. Thermal field (CFD-MEDIUM, official)

| Quantity | Value |
|---|---|
| Heat input / output | Q 602.755 W [M038] = interface heat rate; air ΔT_bulk 68.93 K (300 → 368.93 K) [M037] |
| Max solid temperature | **562.58 K** (outer-wall facet) [M039]; hottest cell centre 562.13 K [M040]; at the outer wall near the adiabatic outlet end |
| Peak inner-wall (interface) temperature | 555.27 K |
| Solid temperature range (nodes) | 423.84–562.54 K; coldest at the inlet end |
| Volume-mean solid temperature | 525.48 K (mean rise ≈ 225.5 K above T_ref) |
| Through-wall ΔT | **7.581 K at mid-span** [M041]; 7.36 K at z = 570 mm; up to 15.1 K in the first inlet slab (conjugate entrance effect) |
| Fully developed Nu / f (x/D 18–29) | 54.17 / 0.02163 [M042, M043]; the window is still slightly developing (F-033) |
| y⁺ (conjugate wall) | min 0.208 / area mean 0.241 / max 0.585 [M044–M046]; 100 % ≤ 1 |

**Structure of the field.**

- The wall temperature rises along the duct with the air bulk temperature, offset by the film temperature difference (≈ 186 K at the outlet end: interface peak 555.27 K vs outlet bulk 368.93 K).
- The inlet end is cold because the heat-transfer coefficient is high in the thermal entrance and axial conduction runs towards the cold end.
- The outlet end is hottest because the end face is adiabatic.
- Radially the wall is almost isothermal: 7.6 K through 10 mm, against a ≈ 225 K mean rise.

**For the structure** this means:

- LC1 sees a small radial gradient, plus axial end effects at the inlet.
- LC2 sees a large, almost uniform mean ΔT.

## 9. CFD → structural mapping (Section 7A)

| Item | Result |
|---|---|
| Source | converged medium solution `baseline_medium_final` (hash-verified, unchanged by every later run) |
| Method (D-038) | mesh-based External Data. Master = the Fluent solid mesh (as a CDB); data = Fluent's own node temperatures (48,048 nodes). Manual / Bucket Volume / Shape Functions; outside option Nearest Node |
| Rejected first | point-cloud triangulation (27,696 nodes unmapped, up to 4.0 K error); Program Controlled mesh-based (2.35 K at the chord-gap nodes). Kriging / RBF and the Workbench Fluent-system route did not work. Evidence kept |
| Coverage | **108,252 / 108,252 nodes, 0 unmapped**; mapped range 423.84–562.56 K vs source nodes 423.84–562.54 K |
| Error (A): vs exact shape-function evaluation | ≤ **0.081 K** inside the source mesh; mean 0.002 K |
| Error (B): vs the independent FV reference | max 2.57 K at the bore within ~11 mm of the inlet (Fluent node reconstruction, F-035); ≤ 0.25 K over z = 14–586 mm |
| Engineering checks | mid-span ΔT_wall 7.580 vs 7.581 K; volume mean 525.520 vs 525.483 K |
| Effect bounds | LC1 inlet peak ±9.8 MPa (≈ 40 % of 24.28 MPa, F-040); LC2 peak ≤ 1.6 %; interior values robust |
| Repeated per case | every 9B case passed the same mapping check: (A) 0.086–0.154 K; mid-span ΔT and section mean preserved within 0.0011 / 0.0079 K |

## 10. Static structural analysis (Section 7B, FE-STATIC, official)

**Model:**

- mesh B, SOLID186 36 × 5 × 130 (bias 4): **108,252 nodes / 23,400 quadratic hexahedra** [M081, M082];
- T_ref 300 K [M083];
- sparse direct solver; linear, small deflection.

**Supports:**

- LC1 [M019]: statically determinate 3-node support;
- LC2 = S1 [M020]: U_z = 0 on both complete end faces, 3 mid-span U_θ nodes, radial free.

| Quantity | LC1 free expansion | LC2 axially restrained (S1) |
|---|---|---|
| Max total deformation | **1.8443 mm** [M084] (outer edge of the outlet face) | **0.1349 mm** [M089] (outer surface, z ≈ 244 mm) |
| Free axial growth ΔL | **1.8409 mm** [M085] (area-weighted face mean; = ∫ε_th dz to 1.3 × 10⁻⁵) | — (restrained) |
| Max von Mises | **24.282 MPa** [M086] at the bore, z = 6.5 mm (inlet end effect); mid-span bore 18.20 MPa | **605.161 MPa** [M090] at the outer edge of the inlet face (z = 0, r = 20 mm) |
| Temperature at the maximum | 427.81 K [M087] | 437.99 K [M093] |
| Reactions | ≈ 0 (9.0 × 10⁻⁷ N) [M088] | ±548,936.6 N end force [M091]; N(z) constant; equals the analytical restrained force of the same field to 10⁻⁵ |
| Mean axial stress | ≈ 0 | **−582.440 MPa** [M092]; interior 587–591 MPa von Mises; mid-span outer 593.4 / bore 564.9 MPa axial |
| Local S_y(T) at the critical node | — | 1047.0 MPa [M094] |
| Yield utilisation (σ_vM / S_y(T)) | 0.023 | **0.5780** [M095]; first-yield factor 1.730 [M096]; first-yield margin (S_y/σ − 1) 0.730 |

**Readings.**

- **Restraint dominates.** LC2 / LC1 is 32× at mid-span and 25× peak to peak. The design driver is the axial restraint, not the through-wall gradient.
- **Where the LC2 peak sits.** The 605.16 MPa is a **local peak**. It combines the uniform axial compression with the inlet-end temperature gradient. The column load measure is the end force of 548.94 kN, equal to 582.44 MPa mean.
- **Pressure is negligible (LC2P).** The CFD maximum wall pressure of 443.41 Pa was applied uniformly as a bound. It changes the LC2 peak by +45 Pa, i.e. 7.4 × 10⁻⁶ % [M097]. A Lamé check agreed within 0.3 %.
- **The static state is elastic in every case.** The maximum utilisation is 0.645 (Q03). The static yield indicator is **not** a structural margin, because stability governs under S1 (§12, L-05).
- **CFD-mesh effect on the structure (6B band).**
  - LC2 stress −10.1 / +2.8 MPa;
  - local peak −13.7 / +4.3 MPa;
  - free growth −32 / +9 µm;
  - utilisation 0.568–0.581.

  The medium field is slightly hot, so these results lean conservative.

## 11. Structural mesh sensitivity (Section 8B)

**Seven meshes were solved on the same mapped field:**

- a coarsening family XC → C → B (r = 1.303);
- licence-limited single-direction refinements FR (through-wall), FA (axial) and FC (circumferential), each at 98.7–99.3 % of the 128,000-node limit;
- a local inlet-bias check IL.

A uniform fine mesh is impossible under the node limit: 151,359 nodes would be the minimum.

| Quantity | Result | Class |
|---|---|---|
| LC2 peak von Mises | B 605.161 MPa; FR 605.220 / FA 605.140 / FC 605.170 / IL 605.134 / C 605.096 / XC 604.867 MPa [M111–M123]; extrapolated 605.187 MPa | **A** (largest change vs B 4.9 × 10⁻⁴, at XC [M124]) |
| LC2 mean axial stress | −582.440 MPa within 7 × 10⁻⁶ | A |
| λ₁ | 1.10799 (XC) … 1.10805 (B) [M112–M122]; fine meshes within 6 × 10⁻⁶ of B | **A** (≤ 5.4 × 10⁻⁵ across all meshes [M124]) |
| LC1 deformation / ΔL | ≤ 3 × 10⁻⁵ | A |
| LC1 mid-span bore σθ | B 18.309 MPa vs 1-D exact 18.698 MPa for the same field: **−2.1 %** (FR −1.5 %) | C at a small absolute level (0.39 MPa); sign known (under-prediction; surface-stress recovery on 2 mm elements) |
| LC1 inlet peak | +1.1 % (FR, FA), +0.9 % (IL), −0.3 % (FC) | B; far inside the mapping bound ±9.8 MPa |

- **Decision.** Mesh B retained (D-056). The governing LC2 and buckling results are converged on it. Refinement improves only the LC1 surface stresses, which drive no decision.
- **Thickness cases (9B-2).**
  - T01 36 × 4 × 130: 89,424 nodes.
  - T03 36 × 6 × 130: 127,080 nodes.
  - Check meshes M01 / M02 (5 through-wall elements): LC2 mean and λ₁ changed ≤ 4.2 × 10⁻⁶, and LC2 peak ≤ 1.4 × 10⁻⁴. M01 exceeds the 10⁻⁴ class-A tolerance at one inlet-edge node; this is reported, not relaxed.
- **Error types kept separate.**
  - CFD mesh: dominant for LC2 and λ₁.
  - Mapping: dominant for the LC1 inlet peak.
  - Structural mesh: negligible for LC2 and λ₁.

## 12. Linear buckling (Section 8A, FE-BUCKLING, S1 = LC2 supports)

| Quantity | Result |
|---|---|
| Applied column load | N = 548,936.6 N (thermal, displacement-controlled) = 582.44 MPa mean axial stress |
| **λ₁ (= λ₂, orthogonal pair)** | **1.10805** [M098]; next pair 4.2979 [M107], then 9.225 |
| P_cr = λ₁·N | **608.25 kN** [M099] |
| Dominant mode | global guided-column sway [M100]: end planes stay perpendicular but translate sideways in opposite directions; mid-span lateral deflection ≈ 0; shape cos(πz/L) (correlation 0.999997); 99.9999 % rigid-section motion; no ovalisation, shell or local mode |
| Hand check | Euler with E(z) (Rayleigh) 1.119; with shear correction 1.104. FE 1.108 lies between them (−1.0 % / +0.4 %). A constant-property toy benchmark reproduced Euler |
| Column class | intermediate: KL/r 53.7 < C_c ≈ 60; elastic σ_E ≈ 650 MPa exceeds the conventional proportional limit. Conventional Johnson (inelastic) estimate 1.058; squash 1.755 |
| Local / shell buckling | not credible for R/t = 1.5 and D/t = 4 (compact section); no local mode in the FE |
| Temperature reading | λ₁ = 1.108 corresponds to ≈ 10.8 % more restrained thermal strain, i.e. ≈ +24 K of mean temperature. On the Section 2 temperature basis λ₁ would be ≈ 0.98 |

**Interpretation (applied in every document; [M179], [M180]).**

- λ₁ is a **linear eigenvalue bifurcation indicator** of an ideal, perfectly straight tube with idealised supports. It contains no imperfection, no plasticity and no large-deflection effect.
- It is **not a collapse load and not a real-world factor of safety**.
- **Yield vs buckling (S1).** λ₁ = 1.108 is below the first-yield factor 1.730. In the idealised S1 model, elastic bifurcation therefore comes **before** first yield: S1 is **stability-limited**, and close to instability.
- The static yield utilisation of 0.578 describes the pre-buckling stress state only.

## 13. Support sensitivity (8A S2, 9B-2 S3; at P00)

| Scenario | Physical definition | Static max VM / mean axial | λ₁ | P_cr | Mode | Mechanism in the idealised model |
|---|---|---|---|---|---|---|
| **S1** (= LC2) | both end faces U_z = 0; 3 mid-span U_θ nodes; ends free to sway, end rotation held (K = 1) | 605.161 / −582.440 MPa | **1.10805** [M098] | 608.25 kN | guided sway | elastic bifurcation first (1.108 < 1.730) |
| **S2** | U_z = U_θ = 0 on every node of both end faces: clamped–clamped (K = 0.5) | 605.160 [M108] / −582.440 MPa | **4.29995** [M101] | 2,360.40 kN [M102] | clamped column, maximum at mid-span [M103] | first yield first (1.730 < 4.300) |
| **S3** | inlet clamped; outlet on a deformable remote point on the axis, U = 0, rotations free: fixed–pinned (K = 0.699) | 605.160 [M109] / −582.440 MPa | **2.23224** [M104] | 1,225.36 kN [M105] | fixed–pinned, maximum lateral at 0.605 L [M106] | first yield first (1.730 < 2.232) |

The scenarios are listed in the S1 / S2 / S3 order of definition. They are **not** ranked.

- **Static state.** The static stress does not depend on the support (< 0.01 %). The end force is 548,936.6 / 548,936.6 / 548,936.7 N [M110].
- **Stability.** Stability depends almost entirely on the support. The FE ratios are 1 : 2.015 : 3.881 (S1 : S3 : S2), against the Euler ratios 1 : 2.047 : 4.
- **Mechanism switch.** The governing mechanism changes with the support: bifurcation first under S1, first yield (or inelastic buckling; Johnson 1.41 / 1.58) first under S2 / S3 [M181].
- **S3 verification.** Before the real S3 solve, the exact S3 formulation from the solver input (TARGE170 pilot + CONTA174, MPC bonded, force-distributed) was checked on a constant-property toy tube: B03, **PASS** in 2 runs.
  - The toy λ₁ of 2.2377 lies between the plain (2.2908) and the shear-corrected (2.2256) clamped–pinned Euler values.
  - The reactions equal E·α·ΔT·A.
  - There is no rigid-body motion.
- **S2 data.** Re-extracted with MAPDL /POST1 and a fresh /CLEAR session. An earlier shared-session run was archived; no reported number used it.
- **What the real flange needs (9A, conceptual).** A beam-column estimate for rotation-fixed ends gives the relative lateral stiffness between the ends:
  - λ₁ 1.5 needs ≈ 0.45 kN/mm;
  - λ₁ 1.73 (first yield) needs ≈ 0.71 kN/mm;
  - full no-sway needs ≈ 3.9 kN/mm.

  Rotational end flexibility would lower λ₁ below S1 (conceptual K = 2: λ ≈ 0.28). **S1 is therefore not a lower bound.**
- **Consequence.** The structural conclusion depends on the real end restraint, which is undefined (T-034). This describes the model's sensitivity. It is **not** a support recommendation.

## 14. Parametric study (9B-1 CFD + 9B-2 FE; S1 supports; actual simulations)

**Design.**

- One factor at a time around P00.
- The ranges are set by the 600 K air property table (V low, q″ high) and by the 128,000-node licence (t high).
- Every case uses its own solved CFD field, mapped with the 7A method.
- No screening temperature, uniform temperature or interpolated value is used.
- A control case, C00, reproduces P00: LC2 +9.5 × 10⁻⁶, λ₁ −4.2 × 10⁻⁷.

| Case | Δp [Pa] | T_out [K] | T_max [K] | LC1 def. [mm] | LC1 VM [MPa] | LC2 VM [MPa] | λ₁ | P_cr [kN] | Utilisation |
|---|---|---|---|---|---|---|---|---|---|
| P00 (baseline) | 438.13 | 368.93 | 562.58 | 1.8443 | 24.282 | 605.161 | 1.10805 | 608.25 | 0.5780 |
| V01 (V 21.15 m/s) | 379.93 | 376.56 | 587.47 | 2.0375 | 24.925 | 663.001 | 1.00307 | 604.14 | 0.6347 |
| V03 (V 25.85 m/s) | 499.69 | 362.69 | 542.10 | 1.6874 | 23.532 | 557.544 | 1.21087 | 611.53 | 0.5315 |
| Q01 (q″ 7,200 W/m²) | 419.74 | 362.06 | 534.45 | 1.6284 | 21.704 | 538.526 | 1.25464 | 612.79 | 0.5129 |
| Q03 (q″ 8,800 W/m²) | 456.64 | 375.79 | 591.13 | 2.0680 | 26.649 | 673.024 | 0.98834 | 603.45 | 0.6446 |
| T01 (t 8 mm, D_o 36; Q held) | 438.11 | 368.93 | 561.97 | 1.8355 | 20.872 | 602.309 | 0.94497 | 385.73 | 0.5743 |
| T03 (t 12 mm, D_o 44; Q held) | 438.14 | 368.93 | 563.07 | 1.8528 | 27.206 | 607.735 | 1.28702 | 907.89 | 0.5813 |

All 54 design-case values were re-read in 10A from each case's Fluent reports and MAPDL tables: **VERIFIED**.

**Mechanisms (the evidence for findings J, K, L).**

- **Velocity (±10 %): cooling capacity.**
  - Δp −13.3 / +14.1 % (local exponent 1.37).
  - Wall temperatures +24.9 / −20.5 K on T_max; solid mean +21.5 / −17.7 K.
  - The structure follows the temperature: end force +9.7 / −8.0 %; λ₁ 1.003 / 1.211.
  - P_cr changes < 0.7 %, because the section is unchanged.
- **Heat flux (±10 %): the thermal load itself.**
  - T_max −28.1 / +28.6 K.
  - End force and LC2 von Mises −11.0 / +11.2 %; λ₁ 1.255 / 0.988.
  - Δp only ±4.2 %, through the air temperature.
  - The temperature response is slightly more than proportional; the cause is not isolated (L-07).
- **Wall thickness (8 / 12 mm, total heat input held constant): the section.**
  - Temperatures change < 1 K.
  - LC2 stress level −0.47 / +0.43 %.
  - A −25.3 / +28.0 % and end force −25.6 / +28.5 %.
  - I −36.7 / +49.5 % and P_cr −36.6 / +49.3 %.
  - λ₁ ∝ I/(A·ε_th) ∝ r_g² gives 0.945 / 1.287.
  - LC1 peak −14.0 / +12.0 %, following the through-wall ΔT (6.44 / 7.58 / 8.61 K).
- **Normalised sensitivity S = (Δy/y)/(Δx/x), most sensitive quantity per parameter:**
  - V → Δp (+1.37);
  - q″ → λ₁ (−1.20);
  - t → P_cr (+2.15).

  Thickness acts on λ₁ through the section (S +0.77). V and q″ act through the temperature (S +0.94 / −1.20). The magnitudes are of the same order.
- **Invariants.**
  - The LC2 critical location is the outer edge of the inlet face in every case.
  - The LC1 critical location is the bore, 6.5 mm from the inlet.
  - The buckling mode is the guided sway in every case.
- **λ₁ < 1: Q03 (0.98834) and T01 (0.94497)** [M182].
  - Their LC2 static stresses are **idealised pre-buckling equilibrium results**: the linear stability criterion indicates loss of stability before the applied load level.
  - They are not described as physically stable operating states.
- **V01 (1.00307) is extremely close to 1** (+0.31 %). Its side of 1 lies inside the thermal and material uncertainty bands, so it is not robust. The same holds for Q03 (−1.17 %).
- **Yield vs buckling.** Under S1, λ₁ is below the first-yield factor in all seven cases, so all are stability-first. No case is yield-limited (utilisation ≤ 0.645).
- **Screening.** The 9A screening agrees with the FE λ₁ within ≤ 0.78 %. It had placed V01 at ≤ 1; the FE value supersedes it (L-12). No conclusion cites a screening value.
- **Interaction.** One factor at a time. The V × q″ interaction is ≈ 8–11 % of the main effects. Combined off-baseline states cannot be obtained by adding the one-factor changes. No response surface was fitted and nothing is extrapolated.

## 15. Major findings (each verified in `FINAL_ENGINEERING_AUDIT.md` §8)

1. **CFD (A, B, C).**
   - The baseline CFD is converged and conserves mass and energy (imbalances ≤ 3.1 × 10⁻¹¹ %).
   - The medium mesh is approximately convergent (status B, not strictly mesh-independent).
   - Its error for the structural phase is small and slightly conservative.
2. **Thermal mechanism.** The air film carries the thermal resistance. The wall is hot (T_max 562.58 K, mean ≈ 525 K) and nearly isothermal through its thickness (7.58 K at mid-span).
3. **Restraint dominates (D).**
   - Free expansion gives 24.28 MPa (inlet-end peak) and 1.84 mm of growth.
   - Full axial restraint gives an end force of 548.94 kN, a mean axial stress of −582.44 MPa and a local peak of 605.16 MPa, i.e. 57.8 % of the local S_y(T).
   - LC2 / LC1 is 32× at mid-span.
4. **Numerical robustness of the structural results (E, I).**
   - The structural mesh changes LC2 and λ₁ by ≤ 5 × 10⁻⁴.
   - Pressure loading is negligible (7.4 × 10⁻⁶ %).
   - The mapping error is ≤ 0.081 K in the interior.
5. **Stability governs S1 (F, G).**
   - λ₁ = 1.108, below the first-yield factor 1.730.
   - The idealised S1 model is stability-limited and close to instability.
   - λ₁ is an idealised linear indicator, not a factor of safety.
6. **The support controls stability (H).**
   - λ₁ 1.108 / 2.232 / 4.300 for S1 / S3 / S2 at an identical static stress.
   - The mechanism switches from bifurcation-first (S1) to first-yield-first (S2, S3).
7. **Parameter mechanisms (J, K, L).**
   - V acts on cooling and Δp, and on the structure indirectly through the temperature.
   - q″ acts directly on temperature and thermal stress.
   - t acts on the section, i.e. the end force and the buckling capacity, with a small temperature effect.
   - At +10 % q″ or −20 % t, λ₁ (S1) falls below 1; at −10 % V it reaches 1.003.
8. **Section 2 hypothesis.** "Restraint dominates the gradient" is confirmed in kind (32× vs 40×). The quantitative gaps come from the lower CFD mean temperature rise (225.5 vs 254.7 K, F-027) and the gas-heating friction effect (F-029). They are explained, not errors.

**Exact conclusion (as in `FINAL_ENGINEERING_AUDIT.md` §15).**

- Within the re-analysed, idealised model, the evidence supports three things:
  - a quantified characterisation of the thermal-stress mechanism;
  - its sensitivity to the operating and design parameters;
  - its dependence on the end restraint.
- Under the baseline S1 idealisation, the duct is stability-limited, with a linear buckling factor of 1.108.
- The evidence does **not** support a statement that a real component is structurally adequate. That statement would need three things that were not defined or modelled:
  - the real end restraint;
  - imperfection-sensitive nonlinear buckling;
  - inelastic material data.

## 16. Limitations

The full registers are in `MASTER_UNCERTAINTIES.md` (nine separate sources, no combined percentage) and `MASTER_ASSUMPTIONS.md`.

1. **Re-analysis.** The original data are lost. No result can be compared with the 2025 internship, and none is presented as a recovered original.
2. **No experimental validation.** Verification is against theory, correlations and internal consistency only. The CFD model form (turbulence model, property variation) is not validated.
3. **Idealised supports** (primary for stability). S1 / S2 / S3 are bounding-type idealisations. The real flange stiffness is undefined (T-034).
4. **Perfect geometry and linear buckling** (primary). There is no imperfection, eccentricity or residual stress, and no post-buckling path. λ₁ is an upper-bound-type bifurcation value (T-035).
5. **Linear elastic material** (primary for capacity). The columns are intermediate (KL/r ≈ 50–58 < C_c ≈ 60). Inelastic behaviour is only estimated with conventional Johnson factors. There are no temperature-dependent stress–strain data (T-036, F-045). S_y values are typical, not minimum-guaranteed (A-022).
6. **Thermal model.**
   - Uniform heat flux and adiabatic ends are idealisations (A-010, A-011).
   - Radiation is neglected and untested (A-015, T-009).
   - The inlet TI is assumed (A-020b).
   - The air table ends at 600 K, which limits the envelope; Q03 reaches 583.4 K air-side.
7. **CFD mesh.** Approximately convergent (status B), not strictly mesh-independent. Apparent order 1.2–1.6. The first layer was not refined in the study (F-032).
8. **Inlet-end transfer.** Within ~11 mm of the inlet, the Fluent node reconstruction limits the mapped temperature accuracy (up to 2.6 K). This bounds the LC1 inlet peak at ±9.8 MPa (F-035, F-040).
9. **ν = 0.294** is assumed, not sourced (T-014).
10. **Study design.**
    - One factor at a time, over a narrow envelope (±10 % V and q″, ±20 % t); no interactions.
    - Pressure was not re-applied in the design cases (justified by LC2P).
    - Steady state only; no start-up or thermal-cycling (fatigue) assessment.
11. **Software.** ANSYS Student 2026 R1. Node limit 128,000 (measured), which excluded a uniform fine structural mesh and the fine CFD field as the structural source. A 2025 original would have used a different release.

## 17. Future work (to close the open items; nothing here has been done)

| Priority | Work | Closes |
|---|---|---|
| 1 | Define the real end restraint: flange lateral and rotational stiffness from the mounting design, or a measured value; re-run the buckling with elastic supports | T-034, uncertainty U7 |
| 2 | Imperfection-sensitive geometrically nonlinear analysis: seed the imperfection from mode 1 at tolerance-based amplitudes; load–deflection path to the limit point | T-035, U8 |
| 3 | Elastic–plastic analysis with temperature-dependent Inconel 718 stress–strain curves (lot or specification minimum data); inelastic buckling | T-036, F-045, U9 |
| 4 | Sourced Poisson's ratio (with its temperature dependence) and minimum-guaranteed S_y(T) | T-014, A-022 |
| 5 | CFD model-form study: an alternative turbulence model or transition treatment; internal S2S radiation; an inlet TI sweep | F-029, F-034, T-009, A-020b |
| 6 | Designed experiment (factorial or response surface) over V, q″, t, including interactions; extend the air property table beyond 600 K if the envelope is widened | one-factor-at-a-time limitation, A-031 |
| 7 | Non-uniform (circumferential) heating: thermal bending interacting with the column mode | A-010 |
| 8 | Transient start-up / shut-down and thermal-cycling (low-cycle fatigue) assessment | steady-state limitation |
| 9 | Experimental validation of the thermal field (wall thermocouples, Δp) on a representative rig; this is the only route to validated rather than verified results | limitation 2 |
| 10 | Confirm the facts about the original internship (licence type, scope) from surviving records, if any are found | T-002, T-003 |

---

*Section 10A synthesis. No report prose and no presentation. All numbers trace to `MASTER_PROJECT_DATA.csv` / `MASTER_TRACEABILITY.md`.*
