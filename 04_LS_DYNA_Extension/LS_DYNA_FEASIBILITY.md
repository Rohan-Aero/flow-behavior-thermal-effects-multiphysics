# LS-DYNA Nonlinear Buckling Extension — Feasibility Assessment (Section 12A)

> **Scope.** Assessment only. LS-DYNA was **not run**. No report, presentation, Fluent result or Mechanical result was
> changed, and the baseline CFD was not rerun.
>
> LS-DYNA would be an **additional** analysis. The Mechanical baseline stays:
> - **S1 λ₁ = 1.108** (1.10805, M098);
> - **P_cr ≈ 608 kN** (608.25 kN, M099);
> - **N ≈ 548.94 kN** (548,936.6 N, M091).
>
> Audit date 2026-10-02, device `HOST`. The details are in the sub-folders; this file summarises them.

## 1. Installation and licence findings

**LS-DYNA is not installed.** There is no solver executable, no LS-PrePost and no LS-Run, so **no solver version can be
reported** (`audit/MACHINE_AUDIT_12A.md`).

- **Executable searches.**
  - `C:\Program Files\ANSYS Inc` was searched recursively.
  - `dir /s` was run on all of `C:\` and `D:\` for `*lsdyna*.exe`, `*ls-dyna*.exe`, `*lsprepost*.exe`, `*lsrun*.exe`,
    `*mppdyna*.exe` and `*smpdyna*.exe`.
  - Result: `File Not Found` (`audit/raw/`).
- **Ansys Student 2026 R1** (`v261`, package R261RC2P01, installed 2026-09-17).
  - The Structures selection was Aqwa, Autodyn, Material Calibration App, Mechanical Products and Motion. **LS-DYNA was not
    selected**, and no LS-DYNA package was extracted (`install.log`).
  - The expected LS-PrePost path, `ansys\bin\winx64\lsprepost413\lsprepost4.13.exe`, does not exist.
- **Present, but integration only.**
  - The Workbench LS-DYNA ACT extension (`LSDYNA.wbex`, solver extension, analysis templates, keyword manager) is loaded by
    default. The project's Mechanical decks show `/COM, LSDYNA, 2026.1`.
  - It can prepare a model and write a keyword deck, but it cannot solve. It was **not tested**.
  - Also present: the R16 manuals (R16@431ab7b9b, documentation only) and two unrelated sample decks (`mat_pie_lin_pla.k`,
    `simplecar.k`). **No thermal-buckling template.**
- **Licence: no LS-DYNA licence evidence.**
  - Machine variable `LSTC_LICENSE=Ansys` is set. There is no `ANSYSLMD_LICENSE_FILE`, no `ansyslmd.ini` and no licence file.
  - An Ansys License Manager installed on 2026-10-01 from another product's media reports *"No license files were found"*.
    Its CVD service is stopped, and it is not used here.
- **Keyword workflow in the project:** none (no `*.k`, `*.key`, `d3plot`, `d3eigv`).
- **Hardware.**
  - i5-12450HX, 8 cores / 12 threads.
  - 15.71 GB RAM, with 4.2–5.0 GB free during the audit.
  - C: 107 GB free; D: 199 GB free.
- **Ansys LS-DYNA Student (vendor page, unverified here).**
  - Separate `.msi` download.
  - "128K nodes/elements".
  - Includes LS-PrePost and LS-Run.
  - Built-in licence valid until 7/31/27.
  - Educational use only.
  - The page describes explicit simulation and **does not mention implicit**. An Ansys forum answer states that implicit
    LS-DYNA "is not supported in single precision", so a double-precision executable is needed. Whether the Student
    package provides one is **unverified**.

## 2. Available project inputs

**Every item already exists.** The authoritative source is the deck Mechanical solved for LC2:
`08_Structural_Analysis/LC2_Restrained/Solver_Output/LC2_solve_input_ds.dat` (SHA-256 `51d80678…`). Mapping and hashes
are in `inputs/PROJECT_INPUTS_12A.md`.

| Item | Source | Content |
|---|---|---|
| Mesh | deck `NBLOCK` / `EBLOCK` | 108,252 nodes / 23,400 SOLID186 (quadratic hexahedra) |
| Fluent solid temperature | deck `BFBLOCK` | 108,252 mapped nodal values, 423.84–562.56 K. The solved field is used directly, so no new mapping is needed |
| Fluent pressure | `fluent_interface_wall_pressure.csv`, LC2P deck | excluded from LC2 by definition (+45 Pa on the peak, M097) |
| Material | deck MP block, `materials_7A.csv` | E(T), ν, secant α(T) with `MPAMOD`, `TREF` = 300 K |
| LC2 supports | deck `_DISPZEROUZ`, `_CM93U` | U_z = 0 on 1,224 end-face nodes; U_θ = 0 on nodes 25862, 25874, 25886 (mid-span, r = 20 mm) |
| Mode shape | `s8a_mode1.csv`, `s8a_mode2.csv` | S1 sway mode, close to cos(πz/L); **corner nodes only** (28,296) |
| Load and factors | `s7b_react.csv`, `s8a_load_factors.csv` | N 548,936.6 N; λ₁ = λ₂ = 1.108047; λ₃,₄ = 4.29790 |
| Geometry, coordinate system, named selections | STEP; `local,12`; `CMBLOCK` | all present |

## 3. Material-data availability

| Property | Available? | Source |
|---|---|---|
| E(T), 20–400 °C | yes | VDM 4127 [M010] |
| ν | 0.294, **assumed** | [M012, T-014] |
| α(T) | yes, **secant** | Special Metals [M011]. LS-DYNA needs **instantaneous** α, obtained by an exact conversion of the same table |
| S_y(T) | yes, **typical** values | VDM 4127 [M013]; used only for first-yield checks |
| Plastic stress–strain / hardening vs T | **no** | F-045, T-036 |

**Material nonlinearity is UNAVAILABLE.**

- Temperature-dependent **plastic (post-yield) stress–strain data do not exist** in the project.
- No curve will be invented, including bilinear or perfectly plastic substitutes.
- A **geometrically nonlinear, thermo-elastic, imperfect** buckling study remains possible
  (`material_data/MATERIAL_DATA_CHECK_12A.md`).

## 4. Proposed LS-DYNA formulation

Implicit static, geometrically nonlinear, thermo-elastic, with imperfect geometry. The chain is Fluent field → thermal
strain → LC2 restraint → imperfection → geometric nonlinearity. **Material nonlinearity is omitted.** The keyword map and
gates are in `proposed_model/PROPOSED_MODEL_12A.md`.

- **Model.** A scripted conversion of the LC2 deck: node IDs, coordinates and connectivity kept. The SOLID186 → 20-node
  `*ELEMENT_SOLID` node order still has to be mapped and verified (G1).
- **Temperature load.**
  - `*LOAD_THERMAL_VARIABLE_NODE` with TB = 300 K and TS = T_i − 300 K, for all 108,252 nodes.
  - A curve λ(t) scales the whole (T − T_ref), the same load definition as the 8A eigenvalue.
  - λ_max ≤ 1.42, set by the end of the E table at 400 °C.
- **Material.**
  - `*MAT_ELASTIC_PLASTIC_THERMAL` (MAT_004) as thermo-elastic: E(T) and ν, with no SIGY or ETAN.
  - R16 remark 1 includes the Ċ·C⁻¹σ term, which gives total-form elasticity.
  - `*MAT_ADD_THERMAL_EXPANSION` supplies a curve of instantaneous α(T).
  - `*MAT_023` (isotropic) is the alternative. A G0 sub-test with temperature-dependent E checks the formulation.
- **Supports: LC2 unchanged.**
  - U_z = 0 on all 1,224 end-face nodes.
  - U_θ = 0 on the 3 hoop nodes, through node-local coordinate systems.
  - Radial motion and end sway free.
- **Solution.**
  - `*CONTROL_IMPLICIT_SOLUTION` NSOLVR = 12 with automatic steps, double precision.
  - Arc length (ARCMTH = 3) only if a limit point appears. Whether it scales a thermal load curve is unconfirmed.
- **Linear buckling.** `*CONTROL_IMPLICIT_BUCKLE` at λ = 1 must reproduce λ₁ ≈ 1.108 (G4). Intermittent buckling tracks
  the tangent stiffness along the path.

## 5. Recommended element and model approach

- **Preferred: the same mesh B** with `*SECTION_SOLID` ELFORM = 23 (20-node).
  - This keeps the converged Mechanical discretisation (8B: λ₁ changes ≤ 5.4 × 10⁻⁵).
  - 108,252 nodes is under 128K **if** that limit applies to nodes and elements separately, as the MAPDL Student
    limit did. Nodes plus elements is 131,652, so G0 must confirm.
  - Implicit and buckling support for solid ELFORM 23 is **unconfirmed** (G0).
- **Fallback: ELFORM −2 on the 28,296 corner nodes.** This is a new discretisation and must pass G2–G4 itself.
- **Model source: the deck, not the Workbench LS-DYNA system.** Every node, temperature and constraint then stays
  traceable.

## 6. Imperfection strategy

| Option | Finding | Defensible amplitude? |
|---|---|---|
| Normalised eigenmode | S1 mode 1 is available (guided sway, a repeated pair) | shape yes, **amplitude no** |
| Fraction of wall thickness | the mode is global (no local or shell mode, D/t = 4); t is not the controlling length | **no** |
| Manufacturing tolerance | none in the project ("no tolerance data exist", 8A); route undefined; code values for other products not verified | **no** |

**No defensible amplitude exists, so a sensitivity study is proposed.**

- **Shape.** Mode 1 from the converted model's own buckle run, cross-checked with `s8a_mode1.csv` and cos(πz/L).
  - Applied as stress-free node offsets X + w₀·φ̂, with the maximum lateral nodal value equal to 1.
  - `*PERTURBATION_NODE` has no eigenmode type.
- **Amplitudes.** w₀/L = 0, 10⁻⁵, 10⁻⁴, 5 × 10⁻⁴, 10⁻³, 2 × 10⁻³.
  - That is w₀ = 0 – 1.2 mm, or 0 – 0.12 t; about 2.3 decades.
  - One mode-2 orientation run is added; a near-identical response is expected, and any difference is reported.
  - These are **sensitivity values, not tolerances**.
- **Definitions.** For the sway shape, w₀ is the end-face lateral offset:
  - the relative end offset is 2w₀;
  - the maximum deviation from the end-to-end chord is ±0.21 w₀ (S-shaped).
  - Any comparison with a straightness value must use the matching measure.

## 7. Expected outputs

These are planned; none has been produced.

1. **Load–displacement:** λ against relative end sway, and against the axial reaction N(λ), for each w₀.
2. **Nonlinear equilibrium path**, with the perfect-geometry path (P0) as reference.
3. **Onset of instability**, reported separately by each of:
   - (a) the intermittent tangent eigenvalue reaching 1;
   - (b) a Southwell estimate;
   - (c) a limit point, if any.
   - An elastic column under restrained thermal expansion may have **no limit point**. If so, that is reported.
4. **Maximum lateral, axial and total deformation.**
5. **von Mises and axial stress** along the path. The **first-yield load factor of the imperfect elastic model** is the λ at
   which von Mises first reaches typical S_y(T); it is comparable to 1.730 (M096). Beyond it, results are elastic
   extrapolations.
6. **Plastic strain: not available.**
7. **Comparison with λ₁ = 1.108 and P_cr = 608.25 kN.** The nonlinear response is **not assumed** to equal λ₁. The size of
   any difference is measured, not presumed.
8. **Imperfection sensitivity** across the sweep.
9. **Mechanism.**
   - Elastic global (sway) buckling can be identified.
   - Plastic buckling **cannot** be identified without plasticity data; it is only flagged if first yield is reached.

**Wording.** No result will be called a factor of safety, and no real-world structural adequacy will be claimed.

## 8. Limitations

- **No plasticity.**
  - There is no collapse load and no inelastic buckling.
  - The column is intermediate (KL/r 53.67 < C_c 60.2). The 8A conventional Johnson estimate is 1.058; that is an idealised
    S1 indicator, **not a capacity or margin**. Inelastic effects are expected to matter but cannot be modelled.
- **Material data.** S_y values are typical; ν is assumed.
- **Imperfection.** The amplitude is unknown, so only sensitivity is shown. No residual stress, eccentricity or thickness
  variation is modelled.
- **Supports.**
  - These are the idealised LC2 (S1) supports; the real restraint is undefined (T-034).
  - S1 is **not a lower bound**: rotationally flexible ends would lower λ₁ (9A).
  - No support stiffness is invented.
  - T-035 is therefore run on idealised S1, before T-034.
- **Load semantics.**
  - The nonlinear λ scales T − 300 K, and E and α follow the temperature.
  - The 8A eigenvalue scales a fixed stress state.
  - G4 isolates the translation; the semantic difference is then measured.
- **Temperature range.** λ ≤ 1.42. The only extrapolation is the baseline's own: α held constant below 93.33 °C, as in
  MAPDL.
- **Translation.** Node order, CTE conversion and element formulation are new modelling steps, accepted only through
  G1–G4.
- **Validation.** No experimental validation exists or will be claimed. The 8A and 10A uncertainties are inherited.

## 9. Is the analysis feasible on this machine?

**Today: no.** No LS-DYNA solver, LS-PrePost or licence exists, so nothing can be run.

**Conditionally feasible** once the user installs **Ansys LS-DYNA Student** (free, separate `.msi`, admin rights,
accepting the Ansys terms). Claude will not download or install it. Gate G0 can still make the study infeasible.

| Gate | Purpose | On failure |
|---|---|---|
| G0 | Solver runs with its built-in licence alongside `LSTC_LICENSE=Ansys`; implicit double precision available; size limit interpreted; 8A toy benchmark reproduced; ELFORM 23 and MAT_004 E(T) sub-tests | ELFORM −2 / MAT_023; **stop** if there is no implicit capability |
| G1 | Converted mesh: counts, volume, Jacobians | fix the node-order map |
| G2 | LC1: ΔL 1.8409 mm, peak 24.282 MPa | CTE, temperatures, material formulation |
| G3 | LC2: N 548,936.6 N, σ_z −582.44 MPa, peak 605.161 MPa | supports, material formulation |
| G4 | Linear buckle: λ₁ ≈ 1.108 | **stop**: no nonlinear claim |

Tolerances are proposed in `proposed_model/PROPOSED_MODEL_12A.md` §4 and are to be frozen before any run.

- **Runs.** 7 nonlinear runs (P0, I1–I5, I4-m2) after the gate runs.
- **Memory (expectation, not evidence).** The same mesh in MAPDL used 323,529 equations and 5.2 GB in total (51 s static,
  255 s buckling, 4 cores). With 15.7 GB RAM one implicit job is expected to fit if other applications are closed.
  LS-DYNA memory and nonlinear runtime are **not measured**.

**Conclusion.**

- A **geometrically nonlinear, thermo-elastic imperfection-sensitivity study** on the unchanged LC2 model is
  **conditionally feasible**: after installation, and only if G0–G4 pass.
- An **elastic–plastic buckling study is not feasible**, because there is no plastic stress–strain data (T-036).
- The Mechanical results and existing conclusions are unchanged.

**STOPPED after this assessment, as instructed.**
