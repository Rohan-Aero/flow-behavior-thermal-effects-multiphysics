# Section 12A — Proposed LS-DYNA Model (definition only; nothing built or run)

> This is a proposal. No keyword file has been written and no solver run made. Every input comes from the existing LC2
> deck (`inputs/PROJECT_INPUTS_12A.md`).
>
> Keyword names and behaviour are taken from the installed *LS-DYNA Keyword User's Manual R16* (PDF page numbers given);
> they must be re-confirmed against the solver that is actually installed (gate G0).

## 1. Baseline carried over unchanged

| Item | Value | Source |
|---|---|---|
| Material | Inconel 718 (re-analysis data set), thermo-elastic | `materials_7A.csv`; M010–M012 |
| Stress-free reference | T_ref = 300 K | M014 / `TREF,26.85` |
| Thermal load | mapped Fluent solid field, 108,252 nodal temperatures, 423.84–562.56 K | LC2 deck `BFBLOCK` |
| Supports | LC2 = S1: U_z = 0 on 1,224 end-face nodes; U_θ = 0 on 3 mid-span outer nodes; radial and lateral free | LC2 deck; D-043 |
| Mesh | mesh B: 108,252 nodes / 23,400 quadratic hexahedra | M081, M082 |
| Reference values | N = 548,936.6 N; λ₁ = 1.10805; P_cr = 608.25 kN; first-yield factor 1.730 | M091, M098, M099, M096 |

## 2. Keyword map (LC2 deck → LS-DYNA)

| Purpose | LS-DYNA keyword | Definition | Manual (R16) |
|---|---|---|---|
| Nodes | `*NODE` | 108,252 records, IDs and coordinates (m) from `NBLOCK`. Imperfect runs add the offset X + w₀·φ̂ (§5) | — |
| Elements | `*ELEMENT_SOLID` (20-node: cards 2 + 3) | 23,400 elements from `EBLOCK`. **SOLID186 → LS-DYNA H20 node order to be mapped by script and verified** (G1) | Vol I p. 2687–2688 |
| Section | `*SECTION_SOLID` ELFORM = 23 | "20-node solid formulation". Fallback ELFORM = −2 on an 8-node corner-node mesh (G0 decides) | Vol I p. 3693 |
| Material | `*MAT_ELASTIC_PLASTIC_THERMAL` | T = 293.15 / 373.15 / 473.15 / 573.15 / 673.15 K. E = 204 / 199 / 193 / 187 / 180 GPa. PR = 0.294. ALPHA = 0. **SIGY, ETAN not defined** (thermo-elastic). R16 remark 1 includes the Ċ·C⁻¹σ term, so for small strain σ̇ = d(Cε_e)/dt, i.e. total-form elasticity as in MAPDL. Checked by a G0 sub-test. Alternative: `*MAT_023`, isotropic, hyperelastic total form | Vol II p. 237–239 (alt. p. 321) |
| Thermal expansion | `*MAT_ADD_THERMAL_EXPANSION` + `*DEFINE_CURVE` | instantaneous α(T), exact conversion of the secant table re-referenced to 300 K (`material_data/`) | Vol II p. 209–210 |
| Temperature load | `*LOAD_THERMAL_VARIABLE_NODE` | per node: TS = T_i − 300 K, TB = 300 K, LCID = λ(t). T = TB + TS·λ(t); the reference (initial) temperature is TB + TS·λ(0) = 300 K | Vol I p. 3468 |
| Load factor | `*DEFINE_CURVE` λ(t) | 0 → 1 (LC2 state) → λ_max ≤ 1.42 (temperature-table limit) | — |
| End faces | `*SET_NODE_LIST` + `*BOUNDARY_SPC_SET` | the 1,224 `_DISPZEROUZ` nodes, DOFZ = 1 (global) | Vol I p. 805 |
| Hoop nodes | `*DEFINE_COORDINATE_SYSTEM` ×3 + `*BOUNDARY_SPC_NODE` ×3 | nodes 25862 / 25874 / 25886. Local x = radial, y = hoop, z = axial at each node; DOFY = 1 only (equal to Mechanical `nrot` + `d,uy`) | Vol I p. 805 |
| Implicit control | `*CONTROL_IMPLICIT_GENERAL`, `*CONTROL_IMPLICIT_AUTO`, `*CONTROL_TERMINATION` | static implicit; automatic step size; end time maps to λ_max | — |
| Nonlinear solver | `*CONTROL_IMPLICIT_SOLUTION` | NSOLVR = 12 (BFGS, default). Arc length (card 3, ARCMTH = 3) only if a limit point is met. **Whether arc length scales a thermal load curve is unconfirmed** | Vol I p. 1665–1670 |
| Buckling | `*CONTROL_IMPLICIT_BUCKLE` | G4: NMODE = 6 at λ = 1, BCKMTH = 1 (Lanczos). Path runs: NMODE < 0 (intermittent buckling at chosen λ) | Vol I p. 1596–1597 |
| Output | `*DATABASE_BINARY_D3PLOT`, `*DATABASE_SPCFORC`, `*DATABASE_NODOUT` + `*DATABASE_HISTORY_NODE`, `*DATABASE_GLSTAT`, `*DATABASE_ELOUT` | reaction N(λ); history nodes on the end-face outer ring (0°, 90°, 180°, 270°) and at mid-span; stresses for von Mises and σ_z | — |
| Precision | double-precision executable | required for implicit; recommended for buckling | Vol I p. 1597, remark 5 |

**Not used:**

- pressure (LC2 excludes it; +45 Pa effect, M097);
- gravity;
- contact;
- plasticity (unavailable);
- any support spring or added restraint (none defined in the project; T-034).

## 3. Load path and its meaning

1. **Step A, λ: 0 → 1.** Reaches the LC2 state. With perfect geometry the result is expected to agree with the linear LC2
   baseline within the G3 tolerances, because LC2 strains are small (thermal strain at most about 0.36 %). That agreement
   is checked, not assumed (G5).
2. **Step B, λ: 1 → λ_max (≤ 1.42).** Continues the same thermal field, scaled.

**Semantics.**

- λ scales (T − 300 K). E(T) and α(T) follow the scaled temperature.
- The 8A eigenvalue scales the λ = 1 stress state with properties fixed.
- The perfect-geometry nonlinear response therefore need not coincide with 1.108. Its relation to λ₁ is measured
  (G4 compared with P0/G5), not presumed.

A displacement-controlled variant (prescribed uniform end shortening) would change the load path. It is **not adopted**
and needs explicit approval if ever wanted.

## 4. Gates (proposed tolerances, to be frozen before any run)

| Gate | Run | Acceptance | On failure |
|---|---|---|---|
| G0 | (i) Installation: double-precision implicit executable present; built-in licence works alongside `LSTC_LICENSE=Ansys`; the 128K limit interpreted (nodes and elements separately, or combined: 131,652). (ii) The existing 8A toy-tube benchmark (`Buckling/Benchmark/`: constant properties, uniform ΔT, sway and no-sway BCs) rebuilt in LS-DYNA and solved implicit + buckle with ELFORM 23 and −2. (iii) A restrained bar with the project's E(T) and α(T) under a uniform temperature rise, checked against the closed-form total-form stress σ = −E(T)·ε_th(T) | (ii) λ matches the 8A MAPDL benchmark within 1 %; (iii) stress within 0.1 % of closed form for MAT_004 (and MAT_023) | ELFORM −2 and/or MAT_023 path; **stop** if there is no implicit or double-precision capability, or if the size limit excludes the model |
| G1 | Converted model, no solve | 108,252 nodes, 23,400 elements, all 1,224 + 3 SPC nodes found; volume equal to the Mechanical mesh volume 5.65486 × 10⁻⁴ m³ (`MESH_7A.md`) within ±1 × 10⁻⁵ relative; positive Jacobians | fix the node-order map |
| G2 | LC1 linear (LC1 supports from the LC1 deck) | ΔL 1.8409 mm ± 0.5 %; max von Mises 24.282 MPa ± 2 % | CTE conversion, temperatures, material formulation (MAT_004 against MAT_023) |
| G3 | LC2 linear (λ = 1, small deflection) | reaction 548,936.6 N ± 0.5 %; mean σ_z −582.44 MPa ± 0.5 %; max von Mises 605.161 MPa ± 2 % | supports, material formulation, CTE conversion |
| G4 | LC2 + `*CONTROL_IMPLICIT_BUCKLE` | λ₁ = λ₂ = 1.108 ± 1 %; λ₃ = 4.298 ± 1 %; mode-1 correlation with cos(πz/L) ≥ 0.999 | **stop**: no nonlinear claim without G4 |
| G5 (= run P0) | Perfect geometry, nonlinear, intermittent buckle | diagnostic, not a hard gate: at λ = 1 the state must agree with G3 within the G3 tolerances; lowest tangent eigenvalue reported against λ | investigate before the sweep |

## 5. Imperfection and run matrix

- **Shape φ̂.**
  - Mode 1 from G4 (LS-DYNA `d3eigv`, all nodes).
  - Normalised so that the maximum lateral nodal value is 1; for the sway mode that is at the end faces.
  - Cross-checks: the 8A corner-node eigenvector `s8a_mode1.csv` and cos(πz/L).
  - Applied as stress-free initial coordinates.
- **Definitions.** For the sway mode:
  - w₀ is the lateral offset of each end face;
  - the relative end offset is 2w₀;
  - the maximum deviation from the end-to-end chord is ±0.21 w₀, an S-shape at z ≈ 0.22 L and 0.78 L.

| Run | w₀/L | w₀ [mm] | w₀/t | Purpose |
|---|---|---|---|---|
| P0 | 0 | 0 | 0 | perfect-geometry reference (G5) |
| I1 | 1 × 10⁻⁵ | 0.006 | 0.0006 | near-perfect trigger |
| I2 | 1 × 10⁻⁴ | 0.06 | 0.006 | sensitivity |
| I3 | 5 × 10⁻⁴ | 0.30 | 0.03 | sensitivity |
| I4 | 1 × 10⁻³ | 0.60 | 0.06 | sensitivity |
| I5 | 2 × 10⁻³ | 1.20 | 0.12 | sensitivity |
| I4-m2 | 1 × 10⁻³ (mode 2) | 0.60 | 0.06 | orientation check: near-identical response expected (axisymmetric field; 3 hoop nodes at 120°); the difference is reported |

These amplitudes are **sensitivity values spanning about 2.3 decades (10⁻⁵ to 2 × 10⁻³ of L), not tolerances**. No project or
product tolerance exists. In total there are 7 nonlinear runs (P0, I1–I5, I4-m2) after the linear gate runs.

## 6. Post-processing definitions (fixed in advance)

- **Lateral response.** Relative end sway δ(λ) = lateral displacement of the outlet end-ring centroid minus that of the
  inlet end ring, taken from the history nodes.
- **Axial force.** N(λ) = Σ SPC force in z on the inlet face.
- **Onset of instability** is reported by all three of:
  - (a) the lowest intermittent tangent eigenvalue crossing 1;
  - (b) the Southwell slope of δ/λ against δ;
  - (c) a limit point, if any.
  - These are never merged into one "capacity".
- **First-yield load factor of the imperfect elastic model.**
  - The smallest λ with von Mises_node ≥ S_y(T_node(λ)).
  - S_y uses the VDM typical table, linear interpolation, no extrapolation, at corner nodes.
  - This is the same method as M094–M096.
- **Required labels.** Each curve and table is marked "geometrically nonlinear, thermo-elastic, idealised LC2 (S1)
  supports, imperfection amplitude = sensitivity value".
- **Wording.** No "factor of safety", "safe" or "adequate" wording.

## 7. Size and resources

- 108,252 nodes / 23,400 elements: under the published "128K nodes/elements" if the limit applies to each separately, as
  the measured MAPDL Student limit (128,000 nodes) does. Nodes plus elements is 131,652, so G0 confirms.
- The same mesh in MAPDL needed 323,529 equations and 5.2 GB (4 processes).
- LS-DYNA memory and runtime per nonlinear path are **not measured**. They are recorded at G3 and G5 before the sweep is
  scheduled.
