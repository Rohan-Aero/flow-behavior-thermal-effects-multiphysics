# Section 12B — Gate 4 (import of the solved LC2 model) with Gate 2/3 compatibility evidence

> **Source.** `08_Structural_Analysis/LC2_Restrained/Solver_Output/LC2_solve_input_ds.dat`, the MAPDL input that
> Mechanical solved for LC2 (SHA-256 `51d80678…5b09`, unchanged). It was **read only**. Nothing in `08_Structural_Analysis`
> was written.
>
> **Converter.** `work_12B/G4_import/convert_lc2_to_lsdyna.py`, run with the Ansys-bundled CPython 3.10. It writes the
> keyword include files to `work_12B/G4_import/model/` and a machine-readable record, `conversion_report.json`.
>
> **Material file.** `work_12B/make_material_12B.py` writes `mat_inconel_thermoelastic.k` and `material_check.json`.
>
> **Scope.** This file documents the translation only. G5 and G6 results are in `../results/`.

## 1. Side-by-side comparison (Gate 4)

| Item | Mechanical LC2 (source deck) | LS-DYNA keyword (converted) | Difference and explanation |
|---|---|---|---|
| **Nodes** | 108,252 (`NBLOCK`, IDs 1–108,252, format `3e20.9e3`) | 108,252, same IDs, `*NODE` written with 10 significant digits (`%.9e`) | **None.** Same IDs and same coordinate precision. All 108,252 nodes are referenced by elements (0 unreferenced) |
| **Elements** | 23,400 (`EBLOCK`, 20 nodes per element) | 23,400 `*ELEMENT_SOLID_H20`, same IDs and connectivity in the same order | **None in topology.** LS-DYNA's H20 node order was checked to be the SOLID186 order with an `H8TOH20` probe: the generated mid-side nodes 9–20 lie on edges 1-2, 2-3, 3-4, 4-1, 5-6, 6-7, 7-8, 8-5, 1-5, 2-6, 3-7, 4-8 (`work_12B/G2G3_compat/h20_order/d3hsp`). Converted volume 5.654856 × 10⁻⁴ m³ vs analytic π(r_o² − r_i²)L = 5.654867 × 10⁻⁴ m³ (−1.9 × 10⁻⁶). The 3 × 3 × 3 Gauss Jacobian check gives no non-positive determinant |
| **Element type** | SOLID186, `keyo,1,2,1`: 20-node quadratic hexahedron, **full integration (3 × 3 × 3 = 27 points)** | `*SECTION_SOLID` **ELFORM 23** (20-node solid formulation): **14 integration points** per element, read from the solver's own `elout` (int. points 1–14) | **Documented formulation change.** Same nodes and interpolation order, but a different integration rule. No hourglass modes are involved. Effect: mostly on local nodal peaks (stress extrapolation and averaging), little on resultants or global stiffness. It is quantified in G5 and G6 and **not** corrected |
| **Material** | `MP,DENS` 8190 kg m⁻³. `EX` 204/199/193/187/180 GPa at 20/100/200/300/400 °C. `NUXY` 0.294. `ALPX` (secant) 12.8/13.3/13.9/14.2/14.8 × 10⁻⁶ °C⁻¹ at 93.33/204.44/315.56/426.67/537.78 °C, defined from 21.11 °C (`MPAMOD` default temperature). Linear elastic and isotropic. `KXX` present, but unused by the structural solve | `*MAT_ELASTIC_PLASTIC_THERMAL` (MAT_004): the same five E points at 293.15–673.15 K and ν = 0.294, α field 0, **SIGY and ETAN blank (no plasticity)**. Thermal strain from `*MAT_ADD_THERMAL_EXPANSION` with an **instantaneous** α(T) curve (LCID 20) | **Exact conversion of the thermal-strain law** (§3). Moduli are linearly interpolated in T in both codes. **No plasticity, no stress–strain curve.** LS-DYNA accumulates ε_th = ∫α_inst dT step by step. A step that straddles one of the jumps in α_inst at the table temperatures leaves a small permanent error; this is visible in bar test B4 as the error jump between T = 352.5 and 378.8 K, across 366.48 K. With 40 load steps the stress matches the closed form to 0.009 % (bar test B5, §2) |
| **Reference temperature** | `toffst,273.15`, `tref,26.85` → **300.00 K** | `*LOAD_THERMAL_VARIABLE_NODE` with TB = 300.0 K for every node. The α curve is built so that ε_th(300 K) = 0 | **None** |
| **Temperature field** | `BF` temperatures on all 108,252 nodes: 150.69–289.41 °C (423.837–562.558 K) | Same 108,252 nodal values in K, written as TS = T − 300 K (6 decimals) and scaled by λ(t) = t (LCID 10), so T(t=1) = TB + TS | **None at the solved state** (rounding ≤ 5 × 10⁻⁷ K). LS-DYNA reaches the field in 40 equal increments, because the thermal strain is accumulated incrementally (row "Material") |
| **Axial load** | No applied force. The axial force comes from the restrained thermal expansion; Mechanical reaction **548.94 kN** | No applied force; same mechanism. Reaction read from `spcforc` | **None in loading.** Because of kinematics (row "Analysis type"), LS-DYNA's reaction is the Cauchy stress on the deformed area: about +0.8 % at this strain level (G2 benchmark, §2) |
| **Supports** | `cmsel,s,_DISPZEROUZ` + `d,all,uz,0`: 1,224 nodes, both end faces (612 + 612). `csys,12` (cylindrical about z) + `nrot,_CM92`, `d,_CM93U,uy,0`: hoop displacement fixed at three nodes | `*BOUNDARY_SPC_SET` on set 1 (the same 1,224 nodes), DOF z. `*BOUNDARY_SPC_NODE` on nodes 25862, 25874 and 25886, DOF y in local systems CID 101–103 (x radial, y hoop, z axial) | **Equivalent.** The same nodes carry the same constraints. The hoop restraint is expressed through one fixed local system per node, instead of MAPDL nodal rotation. Hoop-node reactions are ≤ 10⁻⁵ N in every run, as expected for a self-equilibrated thermal load |
| **Geometry** | Tube: r_i = 10 mm, r_o = 20 mm, L = 600 mm (from the node coordinates) | Same coordinates | **None** |
| **Coordinate system and units** | Global Cartesian, z = tube axis, inlet face at z = 0. SI units (m, kg, s, N, Pa); temperatures in °C with `toffst` 273.15 | Global Cartesian, same axes and origin. SI units; temperatures in **K** | Temperatures shifted by exactly +273.15. No other change |
| **Analysis type and kinematics** | Linear static, small deflection (no `NLGEOM` in the deck; MAPDL default OFF) | Implicit static, **NSOLVR 12** (nonlinear BFGS with equilibrium iterations): **large-deformation kinematics**, 40 steps, no automatic step control | **Documented procedural difference.** The linear option, NSOLVR 1, returns stresses that are **not** in equilibrium under thermal strain. Constant-property bar C1: σx = −2.79 MPa where 0 is exact. Temperature-dependent bar B1: σz +11.2 % in one step. NSOLVR 12 reproduces the closed form (§2). It updates the geometry, so effects of order ε_th (≈ 0.3–0.4 %) appear in reactions and in λ. They are measured in §2 and G6, and are **not** removed by changing physics |
| **Stress output** | Nodal-averaged stresses (`s7b_nodal.csv`, corner nodes) | `eloutdet` nodal-averaged global stresses (`*DATABASE_EXTENT_BINARY` card 3 NODOUT = STRESS_GL) | Both average extrapolated integration-point values at the nodes. The extrapolation differs (27 vs 14 points), so local peaks can differ more than means |

**Gate 4: PASS.**

- All ten required items are matched.
- The two differences that remain are both **documented**: the integration rule (ELFORM 23 vs full-integration
  SOLID186), and the solver kinematics (NSOLVR 12 large deformation vs linear small deflection).
- Neither changes the physics: the material law, loads, supports and geometry are the same.

## 2. Gate 2 (element compatibility) and Gate 3 (material) evidence

All tests are synthetic, except the benchmark, which uses the converted LC2 mesh with uniform properties and uniform
ΔT. Decks and outputs are in `work_12B/G2G3_compat/`; the bar evaluation is `eval_bar_tests.py` → `bar_results.json`.

### 2.1 Restrained bar, one ELFORM 23 element (10 × 10 × 20 mm, U_z = 0 on both end faces, lateral faces free)

**Constant properties** (E = 190 GPa, ν = 0.294, α = 13.6 × 10⁻⁶ K⁻¹, ΔT = 225 K). Closed form: σ_z = −EαΔT = −581.40 MPa,
σ_x = σ_y = 0.

| Run | Solver (NSOLVR) | Steps | σ_z (MPa) | σ_x (MPa) |
|---|---|---|---|---|
| C1 | 1, linear | 1 | −583.04 | **−2.79** |
| C4 | 1, linear | 10 | −581.42 | −0.028 |
| C2 | 12, nonlinear | 1 | **−581.40** | 0.0055 |
| C3 | 12, nonlinear | 10 | **−581.40** | 5.5 × 10⁻⁶ |
| C5 / C6 | −1 | 1 / 10 | as C1 / −58.2 (stress of the last increment only, not accumulated) | — |

**Temperature-dependent material, as converted for LC2** (MAT_004 E(T) + exact MPAMOD thermal strain; ramp 300 → 562.56 K).
Closed form: σ_z = −E(T)·ε_th(T) = **−678.840 MPa**.

| Run | Solver | Steps | σ_z (MPa) | Error | σ_x (MPa) |
|---|---|---|---|---|---|
| B1 | 1, linear | 1 | −754.70 | +11.18 % | −134.74 |
| B2 | 1, linear | 10 | −687.00 | +1.20 % | −15.6 |
| B3 | 1, linear | 40 | −681.22 | +0.35 % | −3.95 |
| B4 | 12, nonlinear | 10 | −677.82 | −0.150 % (max along the path 0.44 %) | 1.2 × 10⁻⁵ |
| **B5** | **12, nonlinear** | **40** | **−678.90** | **+0.009 %** (max along the path 0.025 %) | **1.9 × 10⁻⁷** |
| B6 / B7 | −1 | 40 / 160 | −20.8 / −5.2 (last increment only) | — | — |

**Conclusions** (D-101, D-102):

- NSOLVR 1 (linear) does not equilibrate thermal-strain stresses in this solver build.
- NSOLVR −1 does not accumulate stress, so it is unusable.
- NSOLVR 12 with 40 equal steps reproduces the total-form thermo-elastic law, including temperature-dependent E,
  to 0.009 %.
- This is the setting used for G5 and G6.

### 2.2 Benchmark on the converted LC2 mesh (108,252 nodes, 23,400 ELFORM 23 elements)

Uniform ΔT = 225 K, constant E = 190 GPa, ν = 0.294, α = 13.6 × 10⁻⁶ K⁻¹, LC2 supports. Small-strain axial force
N = EαΔT·A_mesh = 547,955.5 N.

| Run | Solver | Inlet reaction (N) | vs N | λ₁ = λ₂ | λ₃ = λ₄ | λ₅ = λ₆ |
|---|---|---|---|---|---|---|
| `bench_meshB` | 1, linear + buckle | 553,858.2 | +1.077 % (spurious, as in C1) | 1.101613 | 4.198829 | 8.771037 |
| `bench_meshB_nl_static` | 12, 1 step | 552,306.2 | +0.794 % | — | — | — |
| **BM1** | **12, 2 steps + buckle, full load** | **552,316.7** | **+0.796 %** | **1.109919** | 4.229416 | 8.831859 |
| **BM2** | **12, 2 steps + buckle, 1 % load** | 5,480.0 (×100 = 548,000) | +0.008 % | **110.1393 → 1.101393** | 419.8435 → 4.198435 | 877.1649 → 8.771649 |

**Reading the benchmark.**

- **The reaction excess at full load is the deformed-area effect.** With NSOLVR 12 the Cauchy stress equals the
  closed form (C2), so the reaction excess is the deformed area, (1 + (1+ν)αΔT)² = 1.007935. Measured: 1.007959.
- **BM2 is kinematics-free.** At 1 % load, deformation effects are 10⁻⁴ of those at full load. So BM2 × 0.01 is the
  small-deformation eigenvalue, the quantity Mechanical computes.
- **The kinematic factor on λ₁ is 1.109919 / 1.101393 = 1.00774.** It is close to the same area / second-moment
  factor, 1.00794. It is applied in G6 as a documented correction, not as a change to the model.
- **The kinematics-free λ₁ = 1.1014 sits in the hand-calculation band**, for the guided column (K = 1),
  I = π(r_o⁴ − r_i⁴)/4:
  - Euler: π²EI/(L²N) = 1.1199;
  - Euler with Engesser shear correction (Cowper κ = 0.620 for r_i/r_o = 0.5): 1.1041.
  - LS-DYNA is 0.25 % below the shear-corrected value. Mechanical's LC2 λ₁ = 1.1080 is 0.4 % above its own
    shear-corrected hand value (1.1036, 8A), so a difference of this size between ELFORM 23 and SOLID186 is
    plausible. G6 measures it directly.
- **Mode character:** global guided sway in every case (`mode_check_12B.py` on BM1):
  - correlation with cos(πz/L) = 1.0000; ends opposite (cos = −1.000);
  - mid-span lateral < 10⁻¹²; maximum at an end face;
  - rigid-section share 0.999999.

### 2.3 Gate 2 and Gate 3 summary

| Requirement (brief) | Evidence | Result |
|---|---|---|
| Static implicit with the needed solid | ELFORM 23 bar C1–C6, B1–B7; benchmark | **PASS** |
| Nonlinear implicit | NSOLVR 12: C2, C3, B4, B5, BM1, BM2; equilibrium in 2 iterations per step | **PASS** |
| Eigenvalue / buckling | `*CONTROL_IMPLICIT_BUCKLE` on the full mesh: bench, BM1, BM2 (6 modes each, `eigout` + `d3eigv`) | **PASS** |
| Thermal strain | C2: σ_z = −581.40 MPa = closed form; σ_x ≈ 0 | **PASS** (with NSOLVR 12) |
| Temperature-dependent elastic properties | B5: −678.90 vs −678.84 MPa (+0.009 %) | **PASS** (40 steps) |
| Formulation change | SOLID186, 27-point full integration → ELFORM 23, 14 points; same nodes and order | **Documented** (§1) |
| Material: no plasticity, no invented curve | MAT_004 with SIGY and ETAN blank; no stress–strain data used or created | **PASS** |
| Thermo-elastic with geometric nonlinearity | NSOLVR 12 is a large-deformation formulation; B5 and BM1 show it with T-dependent E and with thermal strain | **PASS** |

## 3. Thermal-expansion conversion (exact from the source data)

- **MAPDL side.** MAPDL reads `ALPX` as a secant coefficient defined from 21.11 °C (`MPAMOD` default). It modifies the
  coefficient to the analysis reference temperature T_ref = 26.85 °C, point by point:
  α′ᵢ = [αᵢ(Tᵢ − 21.11) − α_ref(26.85 − 21.11)] / (Tᵢ − 26.85), with α_ref = α at 21.11 °C = 12.8 × 10⁻⁶ (held
  constant below the first table point).
  - This gives α′ = 12.800 / 13.316 / 13.922 / 14.220 / 14.822 × 10⁻⁶ K⁻¹.
  - MAPDL then uses ε_th(T) = α′(T)·(T − T_ref), with α′ interpolated linearly in T.
- **LS-DYNA side.** LS-DYNA integrates an **instantaneous** coefficient: ε_th = ∫α_inst dT.
- **The conversion.** Differentiating the MAPDL law gives α_inst(T) = α′(T) + (dα′/dT)(T − T_ref). This is linear
  inside each table interval and steps at the table points. It is written as curve LCID 20, with paired points ±10⁻⁴ K
  either side of each step, so the integral reproduces MAPDL's ε_th(T) at every temperature.
- **Only source data are used:** the five ALPX values, their five temperatures, 21.11 °C and T_ref. No value was added.
- **Check** (`material_check.json`): ε_th at 423.84 / 525.48 / 562.56 K = 1.61815 / 3.06139 / 3.61790 × 10⁻³.
  - The bar test B5 confirms the integrated law against the closed form to 0.009 %.
  - Reading the table as continuous instead of point-wise would change ε_th by ≤ 2.8 × 10⁻⁴ relative (not used).
