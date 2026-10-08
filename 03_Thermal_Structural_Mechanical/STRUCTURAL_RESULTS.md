# Section 7B: structural solutions LC1, LC2 and the pressure check

> **RE-ANALYSIS 2026.** These are new ANSYS Mechanical 2026 R1 (Student) solutions of the newly built Section 7A model,
> driven by the re-analysed CFD temperature field `baseline_medium_final`.
>
> - Nothing here is a recovered internship result.
> - No experimental data exist or are used.
> - Every number below is read from the solved model:
>   - Mechanical result objects;
>   - the full-precision MAPDL nodal and reaction tables written after the solve;
>   - the post-processing in `Results/post_7B.py`.
> - Hand estimates are labelled as such.
>
> **THERMAL-ONLY** = LC1 and LC2. **THERMAL + PRESSURE** = LC2P only.
>
> Audit trail: `STRUCTURAL_AUDIT.md`.

## 1. What was solved

| Case | Restraint (unchanged from 7A) | Load | Status |
|---|---|---|---|
| **LC1** free expansion | 3 inlet-end outer nodes (0/120/240°), U_θ = U_z = 0 in `CS_DUCT_CYL`. Nothing else | mapped CFD T(x,y,z), T_ref = 300 K | **Solved**, 68 s |
| **LC2** axially restrained | U_z = 0 on both complete end faces (1,224 nodes); 3 mid-span outer nodes U_θ = 0; radial free | same field | **Solved**, 64 s |
| **LC2P** = LC2 + pressure | identical to LC2 (checked in the solver input) | same field + **443.41 Pa gauge** on the bore | **Solved**, 63 s |

**Project and model.**

- Project: `Workbench/Flow_Behavior_Thermal_Effects_Structural_7B.wbpj`. This is a *save-as* copy of the 7A project; the 7A project is content-identical before and after.
- All Workbench cells are Up to Date.
- Mesh: 108,252 nodes, 23,400 SOLID186.

**Solver settings.**

- Sparse direct solver in all three cases (D-047). This is a numerical setting only: the 7A default was PCG 1e-8, and the direct solver makes the pressure effect of about 1e-7 resolvable.
- Linear, small deflection, 1 step. No weak springs, no inertia relief.

**Pre-solve gate.** 61 of 61 checks passed before any solve (`Audits/presolve_audit_7B.json`). The first launch stopped at the gate on a check that was too strict; see the audit, §2.

## 2. Temperature actually used by the solver

The nodal temperatures read back from the *solved* database are the mapped CFD field.

- Values: `BFE,TEMP`, 108,252 nodes, 423.84–562.56 K.
- Agreement with the ds.dat BFBLOCK: within 1.6 × 10⁻⁵ K.
- Agreement with the 7A mapping export: within 0.005 K, which is the 2-decimal rounding of that export.
- The field is identical in LC1, LC2 and LC2P.

No uniform, mean, maximum or analytical temperature was used anywhere.

## 3. LC1: free thermal expansion (THERMAL ONLY)

### 3.1 Deformation

| Quantity | Value | Location |
|---|---|---|
| **Max total deformation** | **1.8443 mm** | outlet end, outer edge (z 600 mm, r 20 mm), T 562.28 K |
| Max axial u_z | 1.8429 mm | outlet end, outer surface |
| Free growth ΔL (mean u_z, outlet face − inlet face) | **1.84086 mm** | — |
| Max radial u_r | 0.0716 mm | outer surface, z 587.7 mm |
| Bore growth, mid-span | 32.2 µm | (outer 64.5 µm) |

**Expansion check.** The three estimates are deliberately not forced to agree (Figure F7B_05):

| Estimate | ΔL | vs FE |
|---|---|---|
| **Mechanical LC1** (face-mean u_z) | **1.8409 mm** | — |
| Independent integral ∫ ε̄_th(z) dz over the mapped field (E-weighted section mean; the MPAMOD-consistent secant α) | 1.8408 mm | FE / integral − 1 = **1.3 × 10⁻⁵** |
| Same, written directly from the datasheet secant definition | 1.8409 mm | 4 × 10⁻⁵ |
| One α and the CFD volume-mean temperature (525.5 K) | 1.8372 mm | −0.20 % |
| **Section 2 analytical** (α 13.72 × 10⁻⁶ × 254.7 K × 0.6 m) | **2.096 mm** | FE is **−12.2 %** |

**Why the numbers differ.**

- **The FE equals the integral of the thermal strain of its own field** to 1 part in 10⁵. Free expansion is kinematically free: the length change is exactly the integral of the section-mean thermal strain, whatever its distribution. This agreement verifies the load, the material tables and the restraint together.
- **Section 2 is 12 % higher because of its temperature, not the FE.**
  - Section 2 assumed a uniform 254.7 K rise, i.e. a 554.7 K mean.
  - The CFD field averages 525.5 K. The mean rise is 225.5 K, which is −11.5 %.
  - The inlet third of the CFD duct is much cooler (423–480 K) than the analytical film model predicts (F-027 as corrected in 6B).
  - The remaining −0.7 % is the α(T) table evaluated at the local temperatures instead of one α at 281.6 °C.
- **The "one mean temperature" estimate is within 0.2 %.** For free growth only the mean thermal strain matters; the small residual is the non-linearity of α(T)·ΔT over the 139 K spread.

### 3.2 Stress

| Quantity | Value | Location | T |
|---|---|---|---|
| **Max von Mises** | **24.28 MPa** | **bore (r 10 mm), z = 6.52 mm** (θ −170°; the ring varies by only 0.3 %) | **427.81 K** |
| Max principal (= hoop) | 27.97 MPa | same node | 427.81 K |
| Min principal | −20.97 MPa | outer edge of the inlet face | 437.99 K |
| Max equivalent elastic strain | 1.241 × 10⁻⁴ | same node as max von Mises | — |
| Max von Mises outside the 15 mm end zones | 20.11 MPa | bore, z 15.9 mm | 438.10 K |
| Max von Mises, z = 50–550 mm | 18.23 MPa | bore | — |
| **Mid-span** (θ-mean) | bore: σ_θ +18.31, σ_z +18.39, **VM 18.20 MPa**; outer: σ_θ −11.69, σ_z −11.54, VM 11.68 MPa | — | 531.69 / 539.27 K |

**Why LC1 is not stress-free.** A zero-stress result is not expected. The sources, from largest to smallest:

1. **Through-wall gradient.** The duct is heated at the outer surface.
   - At mid-span, ΔT_wall = 7.58 K; the outer fibre wants to grow more than the bore.
   - The result is bore tension and outer compression, in hoop and axial alike.
   - Timoshenko's thick cylinder with the same wall temperatures gives bore σ_θ = σ_z = 18.55 MPa and outer −11.76 MPa. The FE is −1.3 % and −0.6 % from these (T-013 closed).
2. **Inlet end effect.** This produces the maximum.
   - In the conjugate entrance region the through-wall ΔT is 14.1 K at z = 0 (vs 7.6 K at mid-span), and T rises steeply along z.
   - At the free end face σ_z must vanish. The self-equilibrating stresses redistribute into the hoop direction within about one wall thickness (St Venant).
   - Peak: 24.28 MPa at the bore 6.5 mm inside the face (Figure F7B_03).
   - This point lies inside the F-035 zone: the transferred temperature is less certain there (§12).
3. **Outlet end.** The free face releases σ_z: bore von Mises falls to 0.27 MPa at z = 600 mm and recovers to 17 MPa within 16 mm.
4. **Axial temperature variation along the length** (434 → 560 K section mean). A free tube accommodates a smooth axial gradient almost without stress. The slow drift of mid-length von Mises (20 → 18 MPa) comes from the changing through-wall ΔT and E(T).
5. **Circumferential gradient: negligible.** The ring temperature ripple from the 48-gon source is ≤ 0.05 K, and the von Mises ripple is ≤ 0.3 %.
6. **Constraints: none.**
   - The three support nodes carry reactions of order 10⁻⁶ N.
   - Their von Mises (21.1207 / 21.1201 / 21.1207 MPa) equals the ring mean on the outer inlet edge (21.1185 MPa).
   - The supports therefore add no stress.

### 3.3 Reaction check

| Quantity | Value |
|---|---|
| Constrained nodes | 3 (18870, 18882, 18894), rotated to `CS_DUCT_CYL` |
| Largest nodal reaction | **6.6 × 10⁻⁶ N** |
| ΣF (global) | (7.8 × 10⁻⁸, 3.9 × 10⁻⁷, 2.3 × 10⁻⁹) N; magnitude 3.9 × 10⁻⁷ N |
| ΣM about (0,0,0) | (−2.0 × 10⁻⁷, 4.2 × 10⁻⁸, 1.8 × 10⁻⁸) N·m |
| Mechanical Force/Moment Reaction probes on the Direct FE support | identical to the APDL values (3.94 × 10⁻⁷ N; 2.10 × 10⁻⁷ N·m) |
| Scale | the LC2 end reaction is 5.49 × 10⁵ N, so the LC1 reactions are 10⁻¹² of it |

**Reactions ≈ 0**, as they must be for a statically determinate support under a self-equilibrated thermal load.

- The sparse-solver pivots are all positive (min 3.5 × 10⁵, max 7.7 × 10⁹): no rigid-body mode and no singularity.
- Mechanical's "not enough constraints … rigid body motion" warning is its generic check, which ignores Direct FE supports. It is a false alarm here (F-036 closed).

## 4. LC2: axially restrained (THERMAL ONLY)

### 4.1 Deformation

| Quantity | Value | Location |
|---|---|---|
| **Max total deformation** | **0.1349 mm** | outer surface, z 244 mm (T 531.18 K): combination of u_z −0.1085 and u_r +0.0801 mm |
| Axial u_z | 0 at both ends (imposed); **min −0.1088 mm** at z 229.7 mm | outer surface |
| Max radial u_r | **0.0897 mm** | outer surface, z 595.7 mm |

**What the deformation shows.**

- **Interior axial displacement.** The hot outlet part expands against the cooler, stiffer inlet part. Material moves towards the inlet by up to 0.109 mm while the total length stays 600 mm (Figure F7B_02).
- **Radial growth: LC2 exceeds LC1 by the Poisson effect of the axial compression.**
  - At mid-span, outer surface: LC2 82.6 µm vs LC1 64.5 µm, a difference of 18.1 µm.
  - Check: ν · |σ̄_z| · r / E = 0.294 × 582.4 MPa × 20 mm / 189.3 GPa = 18.1 µm.

### 4.2 Stress

| Quantity | Value | Location | T |
|---|---|---|---|
| **Max von Mises** | **605.16 MPa** | **outer edge of the inlet end face** (r 20 mm, z 0; θ −170°, but the ring varies by only 0.0016 %: effectively the whole edge) | **437.99 K** |
| Min principal | −613.50 MPa | same point (axial) | 437.99 K |
| Max principal | +48.58 MPa (hoop) | bore edge of the inlet face | 423.87 K |
| Max equivalent elastic strain | 3.131 × 10⁻³ | outer surface, z 576.5 mm (hottest, lowest E) | 562.22 K |
| Max von Mises outside the 15 mm end zones | 591.22 MPa | outer, z 15.9 mm | 446.76 K |
| Max von Mises, z = 50–550 mm | 587.74 MPa | outer, z 377 mm | 547.97 K |
| Mid-span (θ-mean) | outer: σ_z −593.44, VM 587.72 MPa; bore: σ_z −564.91, VM 574.35 MPa | — | 539.27 / 531.69 K |

**Distribution along the duct** (Figure F7B_02).

- Von Mises is nearly uniform: outer surface 586.4–605.2 MPa, bore 561.3–575.5 MPa.
- The stress is axial compression: the restrained axial force is the same at every section (§4.3).
- The outer fibre is about 28 MPa more compressive than the bore. It is hotter by ΔT_wall and wants to grow more against the same restrained length.

**Near the restraints.**

- **Outlet end: no rise at all.** Von Mises is 587.2–587.5 MPa over the last 16 mm.
  - U_z = 0 with free in-plane motion is a symmetry-type condition.
  - It creates no geometric stress concentration.
- **Inlet end: von Mises climbs from 587 MPa (z ≈ 25 mm) to 605.2 MPa at the face** (Figure F7B_03).
  - The cause is the entrance-region temperature, not the restraint.
  - The through-wall ΔT is 14.1 K at z = 0 instead of 7.6 K, so the outer fibre is pushed about 20 MPa further into compression.
  - The rise is spread smoothly over 7 element planes (2.1–2.4 mm each).
  - Averaged and unaveraged peaks differ by 0.004 %.
  - It lies in the F-035 zone (§12).

### 4.3 Reactions and equilibrium

| Quantity | Value |
|---|---|
| Inlet end face (612 nodes) ΣF_z | **+548,936.6 N** |
| Outlet end face (612 nodes) ΣF_z | **−548,936.6 N** (sum of both: 1.8 × 10⁻⁸ N) |
| ΣF_x, ΣF_y on the end faces | 0 (only U_z is constrained there) |
| 3 mid-span hoop nodes | 9.5 × 10⁻⁸ N: they only remove rigid-body motion and carry nothing |
| ΣM about (0,0,0) | (−3.1 × 10⁻⁸, −3.3 × 10⁻⁹, 2.4 × 10⁻⁹) N·m |
| Mechanical probes | inlet +548,936.61 N, outlet −548,936.61 N, hoop 9.5 × 10⁻⁸ N: identical |
| Section force ∫σ_z dA along the whole duct (131 sections) | −549.06 kN ± 0.10 kN. Constant, as axial equilibrium requires; the 0.02 % offset is the radial quadrature |
| **Analytical, same CFD field**: N = −∫ε̄_th dz / ∫dz/(Ē(z)A) | **−548,931 N**: FE reaction / analytical − 1 = **1.0 × 10⁻⁵** |
| Mean axial stress N/A | **−582.44 MPa** |

The reactions are large, as they should be for a fully restrained duct, and exactly balanced. Nothing is unexpectedly large or unbalanced.

## 5. Pressure check: LC2P vs LC2

**The load.**

- Uniform **443.41 Pa gauge** normal to the bore (outward).
- 443.41 Pa is the CFD wall static pressure at the first station, the maximum of the CFD distribution p(z) = 407.36 − 681.55·z. It is a bound on the real load.
- It is a differential internal − external pressure: the CFD outlet is at 0 Pa gauge and the outside at ambient.
- **The 101,325 Pa operating pressure is not applied** (D-048).
- It is carried in the solver by 4,680 SURF154 elements on the bore faces only (verified in the input file).

| | LC2 (thermal only) | LC2P (thermal + pressure) | Difference |
|---|---|---|---|
| **Max von Mises** | **605.160873 MPa** | **605.160918 MPa** | **+45 Pa = +0.000045 MPa = +7.4 × 10⁻⁶ %** |
| Location of max | outer edge, inlet face (node 18865) | same node | — |
| Node-wise von Mises change (corner nodes) | — | — | +14 … +161 Pa |
| Max total deformation | 0.134884278 mm | 0.134884295 mm | +1.7 × 10⁻⁸ mm (+1.3 × 10⁻⁵ %) |
| Max radial deformation | 0.0897340 mm | 0.0897340 mm | +2.9 × 10⁻⁸ mm |
| End reactions | ±548,936.61 N | ±548,936.53 N | −0.08 N (Poisson contraction from the pressure) |

**Is it the right pressure?** LC2P − LC2 at mid-span is compared with Lamé plane strain (ε_z = 0, since both ends are held), using the same field:

| | Lamé | FE |
|---|---|---|
| Δσ_θ bore / outer | 739.0 / 295.6 Pa | 736.6 / 295.8 Pa |
| Δσ_r bore | −443.4 Pa | −440.2 Pa |
| Δσ_z | 86.9 Pa | 82–92 Pa |
| Δu_r bore | 4.453 × 10⁻¹¹ m | 4.457 × 10⁻¹¹ m |

The pressure is applied with the right magnitude and direction, and the check does not rest on an assumption. **Conclusion, now confirmed by calculation: the internal pressure is negligible for this duct.** Its effect on the peak stress is 7 parts in 10⁸. The linear-fit distribution is everywhere below this bound, so its effect would be smaller still.

## 6. Local yield strength, utilisation and margin

- **Yield basis (D-050).** S_y(T) interpolated linearly in the VDM 4127 age-hardened table: 1030 / 1060 / 1040 / 1020 / 1000 MPa at 20 / 100 / 200 / 300 / 400 °C.
- The mapped range (150.7–289.4 °C) is inside the table, so **no extrapolation** is needed.
- The Engineering Data scalar of 1020 MPa is **not** used for margins.
- Utilisation = σ_vm / S_y(T_local). Margin = S_y / σ_vm − 1.

| Case | Point | σ_vm | T | S_y(T) | **Utilisation** | **Margin** |
|---|---|---|---|---|---|---|
| LC1 | max von Mises (bore, z 6.5 mm) | 24.28 MPa | 427.81 K (154.7 °C) | 1049.1 MPa | **0.0231** | **42.2** |
| LC2 | max von Mises (outer inlet edge) | 605.16 MPa | 437.99 K (164.8 °C) | **1047.0 MPa** | **0.578** | **0.730** |
| LC2 | highest utilisation outside the end zones (outer, z 562.7 mm) | 587.59 MPa | 561.74 K (288.6 °C) | 1022.3 MPa | 0.575 | 0.740 |
| LC2P | max von Mises | 605.160918 MPa | 437.99 K | 1047.0 MPa | 0.578 | 0.730 |

**Comparisons.**

- With the scalar 1020 MPa, the LC2 peak would read 0.593.
- The cold-end peak and the hot-end interior are almost equally utilised (0.578 vs 0.575). The cold end has 3 % more stress but also about 2.4 % more strength.
- **The location of the governing margin therefore depends on S_y(T)**, which is why a single yield value would mislead.

**Limitations of this margin.** It is a first-yield margin for a linear-elastic, steady-state, perfectly restrained duct.

- **Not included:** buckling (the axial force is 549 kN, see §11 and F-039), fatigue or thermal cycling, creep, weld or joint effects, residual stress, flange compliance, or design-code knock-down factors.
- **Data:** yield values are datasheet values, not design allowables; ν is [ASSUMED].

## 7. Critical locations

| Case | Quantity | Value | Location | Temperature | Yield basis |
|---|---|---|---|---|---|
| LC1 (thermal only) | max von Mises stress | 24.28 MPa | bore r 10 mm, z 6.52 mm, θ −170° (node 19007) | 427.81 K (154.7 °C) | S_y(T) 1049.1 MPa (VDM 4127, linear); U 0.0231; margin 42.2 |
| LC1 (thermal only) | max total deformation | 1.8443 mm | outer edge of the outlet face, r 20 mm, z 600 mm, θ −145° (node 108251) | 562.28 K (289.1 °C) | n/a (deformation) |
| LC2 (thermal only) | max von Mises stress | 605.16 MPa | outer edge of the inlet face, r 20 mm, z 0, θ −170° (node 18865) | 437.99 K (164.8 °C) | S_y(T) 1047.0 MPa; U 0.578; margin 0.730 |
| LC2 (thermal only) | max total deformation | 0.1349 mm | outer surface, r 20 mm, z 244.1 mm, θ 35° (node 104046) | 531.18 K (258.0 °C) | n/a (deformation) |
| LC2P (thermal + pressure) | max von Mises stress | 605.160918 MPa | same node as LC2 (18865) | 437.99 K (164.8 °C) | S_y(T) 1047.0 MPa; U 0.578; margin 0.730 |
| *supplementary* LC2 | max utilisation outside the end zones | 587.59 MPa | outer surface, z 562.7 mm (node 24110) | 561.74 K (288.6 °C) | S_y(T) 1022.3 MPa; U 0.575; margin 0.740 |

The θ values are the nodes the maximum happens to fall on. The rings vary by only 0.3 % (LC1) and 0.0016 % (LC2), so physically each peak is a ring. Machine-readable version: `Results/critical_locations_7B.csv`.

## 8. Axial profiles

The figures plot θ-averaged values at the 131 element corner planes, from the full-precision nodal table.

- `Figures/F7B_01_LC1_axial_profiles.png`: temperature (bore, outer, section mean), section-mean u_z, von Mises (bore and outer).
- `Figures/F7B_02_LC2_axial_profiles.png`: the same, plus axial stress (bore and outer).
- Data: `Results/axial_profile_LC1.csv`, `axial_profile_LC2.csv`, `axial_profile_LC2P.csv`. Each has 131 rows and also contains u_r, σ_θ, the section force, the thermal strain and E(T).

Summary of the profiles:

- **Temperature.** Rises from 434 K (section mean at the inlet) to 560 K (outlet).
- **u_z.**
  - LC1: rises monotonically from 0 to 1.842 mm.
  - LC2: falls to −0.109 mm at z ≈ 230 mm and returns to 0.
- **Von Mises.**
  - LC1: the inlet-end peak (24 MPa, bore), a mid-length plateau of 18–20 MPa at the bore and 10–12 MPa at the outer surface, and relief at the outlet face.
  - LC2: flat at 587 MPa (outer) and 574 MPa (bore), with the entrance-region rise to 605 MPa.

## 9. Comparison with Section 2

| Quantity | Section 2 (analytical) | 7B FE | Difference | Physical explanation |
|---|---|---|---|---|
| Free axial growth | 2.096 mm | **1.841 mm** | −12.2 % | CFD mean rise 225.5 K vs 254.7 K (−11.5 %): the cooler entrance third and the higher CFD film coefficient (F-027, 6B), plus α(T) at local temperatures. The FE equals its own ∫ε_th dz to 10⁻⁵ |
| Bore growth (mid-span) | 34.94 µm | 32.2 µm | −7.8 % | local bore T 531.7 K vs 554.7 K |
| LC1 peak von Mises | 16.31 MPa (mid-span theory) | **24.28 MPa** (inlet end, z 6.5 mm) | +49 % | End effect of the conjugate entrance region, absent from the long-tube theory |
| LC1 mid-span bore σ_θ | 16.31 MPa | 18.31 MPa | +12.3 % | Three factors: (1) ΔT_wall 7.58 vs 7.28 K (×1.041); (2) **tangent** CTE 14.9 × 10⁻⁶ vs secant 13.72 × 10⁻⁶ (×1.087), because a gradient stress depends on dε_th/dT and Section 2 used the secant value; (3) E (×1.006). Section 2 re-evaluated with these factors gives 18.57 MPa; Timoshenko gives 18.55; the FE gives 18.31 (−1.3 %) |
| LC2 axial stress | −657.2 MPa | mean **−582.4 MPa**; peak von Mises 605.2 MPa | −11.4 % (mean) | same temperature basis: −657.2 × 225.5/254.7 = −581.9 MPa. The FE mean matches this to 0.1 %. The peak is 3.9 % above the mean because of the entrance-region through-wall gradient |
| Utilisation LC2 | 0.642 (S_y 1023.7 MPa at 281.6 °C) | **0.578** (S_y(T) at the peak) | −10 % | lower stress (cooler field) and higher local S_y at the cold-end peak |
| Margin LC2 | 0.56 | **0.73** | — | as above |
| LC2 / LC1 ratio | 40.3× | 24.9× (peak/peak); **32.3×** (mid-span max/max) | — | LC1's peak is an end effect; at mid-span, where the Section 2 model applies, the ratio is inside the 30–50 band |
| Expected bands (Section 2) | LC1 13–20 MPa; LC2 600–700 MPa; U 0.60–0.70 | LC1 18.2 (mid) / 24.3 (peak); LC2 582 (mean) / 605 (peak); U 0.578 | — | The bands were drawn on the hotter Section 2 basis. The shifts are the temperature basis, not a model error |

**The central Section 2 finding holds.** Restraint dominates the through-wall gradient by about 30× (mid-span) and 25× (peaks). The design driver is the mounting, not the thermal gradient.

## 10. 6B temperature uncertainty carried into the structural results

- **Source.** The 6B three-mesh study (PROJECT_STATE §12.9), i.e. the numerical uncertainty of the medium CFD field:
  - peak solid T −5.1 / +1.6 K (best estimate −4.4 K);
  - volume-mean T −3.6 / +1.0 K (best −3.1 K);
  - mid-span through-wall ΔT −0.013 / +0.045 K.
- **Method.** Linear sensitivities of *this* solution (no new solve, nothing invented):

| Result | Sensitivity | 6B range | Best estimate | Relative |
|---|---|---|---|---|
| LC1 free growth | 8.88 µm/K of mean T | −32.0 / +8.9 µm | −27.5 µm | −1.7 / +0.5 % |
| LC2 axial stress (uniform shift) | −2.82 MPa/K | magnitude −10.1 / +2.8 MPa | −8.7 MPa | −1.7 / +0.5 % |
| LC2 peak (bound using the peak-T uncertainty at the critical point) | E·α_tan = 2.69 MPa/K | −13.7 / +4.3 MPa | — | −2.3 / +0.7 % |
| LC2 utilisation at the peak (uniform stress shift, S_y at the nominal local T) | — | 0.568 / 0.581 | 0.570 (0.569 if S_y is shifted with T as well) | — |
| LC1 through-wall stress | ∝ ΔT_wall | −0.17 / +0.59 % | — | about −0.03 / +0.11 MPa at mid-span |

**Direction and scope.**

- The medium CFD field is slightly *hot*, so the FE results are slightly **conservative**.
- These are mesh-uncertainty bounds only. The CFD model uncertainties (h / Nu correlation: 19 K on T_max; gas-heating friction; radiation) are larger. They are not propagated because no data quantify them beyond the Section 2 vs CFD comparison (§9), which is itself such a sensitivity.

## 11. Limitations

1. **Linear, elastic, small deflection, steady state.** The peak strain of 0.31 % and U < 0.58 are consistent with elastic behaviour. There is no plasticity, creep, transient or cycling.
2. **LC2 restraint is idealised.**
   - The end planes are rigid and perfectly held, so the restraint stress is an upper bound.
   - Real flanges, gaskets and bolts have compliance that relieves part of it.
3. **Stability is not assessed (F-039).** LC2 puts 549 kN of compression into a 600 mm tube. An indicative Euler / Johnson hand estimate (not FE) with hot-end properties gives:
   - critical stress ≈ 920 MPa (1.58 × the applied 582 MPa) if the ends are held against lateral sway (K = 0.5);
   - only ≈ 616 MPa (1.06 ×) if they can sway (K = 1).

   The LC2 model's end faces are free laterally (only U_z held). **An eigenvalue buckling analysis with the real end conditions is needed before the LC2 yield margin can be called a structural margin.**
4. **Material.** ν = 0.294 is [ASSUMED]. E, α and S_y are datasheet values, not design allowables.
5. **Inlet-end temperature (F-035).** Both peaks lie within 7 mm of the inlet face, where the transferred temperature is less certain (up to 2.6 K at the bore). The local stress bound E α ΔT/(1 − ν) is ±9.8 MPa (a bound, not a computed value):
   - ≈ 40 % of the LC1 peak;
   - 1.6 % of the LC2 peak.

   The LC1 peak should be read as indicative; the interior values (18–20 MPa) are robust.
6. **Mesh.** One structural mesh. The sensitivity study is prepared but not run (T-029/T-033): see the audit, §12.
7. **Loads not included.** Wall shear traction from the flow (of order 1 Pa), gravity, fitting loads.

## 12. Figures

**From the solved Mechanical model** (`Figures/Mechanical/`, 1600 × 900 PNG):

- Views: `_iso` and `_side`.
- True-scale deformation: read back as scaling "True", multiplier 1.0.
- These are the renders Mechanical exported; nothing was edited.

| Brief item | LC1 | LC2 | LC2P |
|---|---|---|---|
| temperature | `LC1_00_Imported_Temperature_*` | `LC2_00_Imported_Temperature_*` | `LC2P_00_…` |
| total deformation | `LC1_Total_Deformation_*` | `LC2_Total_Deformation_*` | `LC2P_Total_Deformation_*` |
| axial deformation | `LC1_Axial_Deformation_Uz_global_*` | `LC2_Axial_Deformation_Uz_global_*` | `LC2P_…` |
| von Mises | `LC1_Equivalent_Stress_averaged_*` | `LC2_Equivalent_Stress_averaged_*` | **`LC2P_Equivalent_Stress_averaged_*`** (pressure comparison with LC2) |
| principal stress | `LC1_Maximum/Minimum_Principal_Stress_*` | `LC2_Maximum/Minimum_Principal_Stress_*` | `LC2P_…` |
| equivalent elastic strain | `LC1_Equivalent_Elastic_Strain_*` | `LC2_Equivalent_Elastic_Strain_*` | `LC2P_…` |
| reaction force | `LC1_Force_Reaction_LC1_SUPPORT_3NODES_DirectFE_*` (≈ 10⁻⁷ N: no visible arrow) | `LC2_Force_Reaction_LC2_INLET_END_*`, `…_OUTLET_END_*`, `…_HOOP_3NODES_DirectFE_*` | `LC2P_…` |
| extra | radial deformation; hoop, radial and axial stress; unaveraged von Mises | same | same |

**`Figures/Mechanical/Zoom/`** holds 11 side views centred on the inlet or outlet end. The camera zoom commands were ignored in batch mode (F-042), so these are not true close-ups. The quantitative close-up is F7B_03.

**Data plots** (`Figures/F7B_0x`, plotted from the solution tables and labelled as such):

1. LC1 axial profiles
2. LC2 axial profiles
3. inlet-zone detail (von Mises per element plane, LC1 and LC2)
4. pressure effect (LC2P − LC2 von Mises along z)
5. expansion comparison
6. section-force equilibrium (LC2 and LC1)

## 13. Files

```
08_Structural_Analysis/
  STRUCTURAL_RESULTS.md (this file) · STRUCTURAL_AUDIT.md
  LC1_Free_Expansion/Solver_Output/  solve.out, file0.err, s7b_nodal.csv (full-precision nodal table), s7b_react.csv,
                                     s7b_prrsol.txt, s7b_totals.txt, LC1_solve_input_ds.dat (exact solver input)
  LC2_Restrained/Solver_Output/      the same for LC2
  Pressure_Check/Solver_Output/      the same for LC2P
  Exports/LC1|LC2|LC2P/              Mechanical text exports of every result object (5 significant digits)
  Results/                           post_7B_results.json, results_summary_7B.csv, critical_locations_7B.csv,
                                     axial_profile_*.csv, hand_checks_7B.json, Scripts/ (post_7B.py, plots_7B.py, tables_7B.py,
                                     hand_checks_7B.py)
  Figures/                           F7B_01…06 (data plots) · Mechanical/ (86 renders) · Mechanical/Zoom/ (11)
  Audits/                            presolve_audit_7B.json, mech_solve_7B_log.txt, mech_solve_7B_summary.json, wb logs,
                                     hash records, Gate_Run1_FAIL/, APDL_snippet_test/, Presolve_Inputs/
  Workbench/Flow_Behavior_Thermal_Effects_Structural_7B.wbpj (+ _files, solved)
  Workbench/Scripts/                 wb_solve_7B.wbjn, mech_solve_7B.py, s7b_post_snippet.inp, wb/mech_zoom_images_7B.*
```
