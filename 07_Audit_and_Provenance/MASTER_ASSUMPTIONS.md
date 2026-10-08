# MASTER ASSUMPTIONS — Section 10A

> **RE-ANALYSIS 2026 — Re-analysed / Assumed / Simulated 2026.**

## 1. Original-data limitation (governing statement)

**The original internship project files were lost.** A filesystem sweep on 2026-09-18 (`00_admin/software_inventory.md`) found no
original ANSYS artefact.

The current work is a **technical re-analysis made in 2026**. This covers the geometry, boundary conditions, material selections,
analytical calculations, CFD simulations, structural simulations and results.

Only surviving documented internship information may be described as historical fact. Everything else must be labelled
**re-analysed**, **assumed**, **calculated 2026** or **simulated 2026**.

### 1.1 What is historical fact (as documented by the engineer in Section 0)

| Fact | Where it is recorded |
|---|---|
| Project title: *Flow Behavior and Thermal Effects in Multiphysics Systems* | `PROJECT_STATE.md` header, `01_Requirements/PROJECT_CONCEPT.md` |
| Organisation: Eleation | same |
| Internship period: February – May 2025 | same |
| Engineer: Rohan Balram Patel, B.Tech Aerospace Engineering | same |
| Tools of the original internship: ANSYS Workbench, Fluent, Mechanical | `00_admin/software_inventory.md` §1.4 ("all three tools documented on the original internship") |

### 1.2 What is NOT known about the original work (must not be asserted)

| Item | Status |
|---|---|
| A-001: the original used a Student / academic ANSYS licence | unconfirmed (T-002 open) |
| A-002: the original was a single coupled case, not a parametric campaign | unconfirmed (T-003 open) |
| Original geometry, dimensions, materials, loads, meshes, results, figures, conclusions | **unknown**: every value in this project is a 2026 choice or a 2026 result |
| Any measured or experimental data | **none exist and none were invented**. Validation is against theory and published correlations only |
| Software version | the re-analysis runs ANSYS Student **2026 R1 (v261)**; a 2025 original would have used 2024 R2 / 2025 R1 (F-001) |

### 1.3 Labels to use

| Label | Meaning | Examples |
|---|---|---|
| **Re-analysed (class B)** | input value chosen in 2026 with a stated rationale | D_i 20 mm, V_in 23.5 m/s, q″ 8000 W/m², Inconel 718 |
| **Assumed** | engineering assumption (idealisation) made in 2026 | steady state, uniform flux, ν = 0.294, idealised supports |
| **Calculated 2026 (class C)** | derived by hand or by script from class-B inputs | Section 2 analytical values (603.19 W, 581.7 K, −657.2 MPa, 2.096 mm) |
| **Simulated 2026** | output of an ANSYS 2026 R1 Student solve in this project | 562.58 K, 605.16 MPa, λ₁ 1.108 |

**No parameter is class A** (documented from surviving evidence). The class-A slot is kept in `baseline_parameters.json` only to
make its absence explicit.

## 2. Re-analysed inputs (class B) of the official baseline P00

| Group | Input | Value | Rationale / decision |
|---|---|---|---|
| Geometry | D_i / D_o / t / L | 20 / 40 / 10 / 600 mm | D-008: D_o/D_i = 2 (ln 2); L/D = 30 |
| Fluid | air, incompressible ideal gas | ρ = p_op/(RT); property tables 250–600 K | D-009, D-021 |
| Operating | T_in / V_in / outlet | 300 K / 23.5 m/s / 0 Pa gauge at 101,325 Pa | D-009; Re ≈ 30,000 |
| Thermal BC | outer-wall flux; ends | 8000 W/m² uniform; adiabatic end faces | D-015 (12 → 8 kW/m² to stay elastic) |
| Solid | Inconel 718 | ρ 8190 kg/m³; k(T), c_p(T), E(T), secant α(T), S_y(T) from VDM 4127 / Special Metals | D-010, D-026, D-036 |
| Structural | T_ref | 300 K | D-041 |
| Structural | LC1 / LC2 (S1) supports | 3-node determinate support / U_z = 0 on both end faces + 3 mid-span hoop nodes | D-042, D-043 |
| Parametric | V ±10 %, q″ ±10 %, t 8 / 12 mm (Q held) | one factor at a time | D-058, D-060 |

## 3. Final status of every assumption

Status key: **VALID** (still used; supported by later results) · **SUPERSEDED** (replaced by a later model choice; the Section 1
text is historical) · **RESOLVED** (the open question was answered) · **OPEN** (not verified) · **ASSUMED** (a retained idealisation,
not testable within this project).

### 3.1 Section 1 register (`01_Requirements/ASSUMPTIONS.md`)

| ID | Assumption (Section 1) | Final status | Evidence / what supersedes it |
|---|---|---|---|
| A-001 | Original used a Student-type licence | **OPEN** | T-002; never asserted |
| A-002 | Original was a single coupled case | **OPEN** | T-003; never asserted |
| A-003 | Student solver limits partly unverified | **RESOLVED** | Fluent 4-core cap verified; 500,580 cells solved without restriction (F-004); Mechanical/MAPDL limit **measured** at 128,000 nodes (T-026, `08_Structural_Analysis/Licence_Check/LICENCE_CHECK_7A.md`) |
| A-004 | Steady state | **VALID** | time-invariant BCs; converged steady solutions |
| A-005 | Incompressible ideal gas | **VALID** | Δp 438 Pa = 0.43 % of p_op; Mach ≤ 0.091 at the maximum outlet velocity (5B) |
| A-006 | Constant-property correlations outside validity (corrected with n = 0.5) | **SUPERSEDED** for final values | Fluent solves with variable properties; CFD Nu_fd 54.17 lies in the 44–67 band, implied n ≈ 0.36 (F-006). The correction remains only in the Section 2 analytical level |
| A-007 | Buoyancy neglected | **VALID** | Ri = 4.4 × 10⁻⁵ |
| A-008 | Viscous dissipation neglected | **VALID** | Br = 1.8 × 10⁻³ (Section 2) |
| A-009 | One-way thermal → structural coupling | **VALID** | flow-area change 0.70 % (Section 2); D-013, D-037 |
| A-010 | Uniform heat flux on the outer surface | **ASSUMED** (retained idealisation) | imposes a known Q; non-uniform heating (bending) is future work |
| A-011 | Adiabatic end faces | **ASSUMED** | Fluent: end-face heat flux −0 W |
| A-012 | Linear elastic, no plasticity or creep; "ample elastic margin at 0.63 utilisation" | **VALID for the static stress; justification SUPERSEDED** | FE utilisation ≤ 0.645 (all cases) keeps the statics elastic, but 8A shows the S1 idealisation is **stability-limited** (λ₁ 1.108; Q03 / T01 < 1). The static-yield margin is not a structural margin (F-043) |
| A-013 | E, α, S_y at mean operating temperature, constant | **SUPERSEDED** | 7A/7B: temperature-dependent E(T) and secant α(T) in the solver (D-036); S_y(T) at the local node temperature (D-050) |
| A-014 | Hydraulically smooth walls | **ASSUMED** | not tested |
| A-015 | Internal surface-to-surface radiation neglected | **ASSUMED / OPEN** | S2S sensitivity never run (T-009); estimated conservative for the wall temperature (F-007) |
| A-016 | Stress-free reference temperature 300 K | **VALID** (definition) | TREF 26.85 °C in every solver input (verified M083) |
| A-017 | Correlation comparison only for x/D > 18 | **VALID**, with a caveat | window still slightly developing (F-033; Nu_fd, f_fd biased 1–2 %) |
| A-018 | Generic datasheet properties | **ASSUMED** | uncertainty source U5 |
| A-019 | Air non-participating in radiation | **VALID** | physics |
| A-020 | Perfect thermal contact at the fluid–solid interface | **VALID** | coupled conformal interface (T-015) |

### 3.2 Assumptions introduced after Section 1

| ID (this register) | Assumption | Status | Evidence |
|---|---|---|---|
| A-020b | Inlet turbulence intensity 4.411 % (0.16 Re^−1/8, D_h 20 mm) | **ASSUMED** | **ID collision:** `PROJECT_STATE.md` §9 and `06_Fluent_CFD/FLUENT_SETUP_NOTES.md` call this "A-020", but `ASSUMPTIONS.md` already uses A-020 for perfect thermal contact. Refer to it as A-020b. Influence limited to the first diameters |
| A-021 | Poisson's ratio 0.294 | **ASSUMED** | in neither datasheet (T-014 / F-011 open); literature 0.284–0.294 |
| A-022 | S_y(T) = VDM 4127 typical values (1030 / 1060 / 1040 / 1020 / 1000 MPa at 20 / 100 / 200 / 300 / 400 °C) | **ASSUMED** | typical, not minimum-guaranteed; utilisation is not a certified margin. The Engineering Data scalar 1020 MPa is a lower bound that is not used for utilisation (F-037) |
| A-023 | Secant α(T) datum 70 °F re-referenced to T_ref by MPAMOD | **VALID** | the MAPDL warning "ALPX evaluated at 26.85 °C" is explained (7B) |
| A-024 | Supports are idealised: S1 = LC2 baseline, S2 / S3 sensitivities; the real flange restraint is undefined | **ASSUMED / OPEN** | T-034; primary uncertainty for stability (U7) |
| A-025 | Perfectly straight tube; no imperfection, residual stress or load eccentricity | **ASSUMED** | linear eigenvalue buckling; T-035 open (U8) |
| A-026 | Buckling linear elastic; inelastic effects only via conventional Johnson estimates (8A) | **ASSUMED** | no temperature-dependent stress–strain data (F-045, T-036; U9) |
| A-027 | Structural pressure load negligible | **VALID** | LC2P: +45 Pa on 605.16 MPa (7.4 × 10⁻⁶ %); not re-run for the design cases (Δp of the same order, D-071) |
| A-028 | Thickness cases hold the total heat input Q constant | definition (D-060) | isolates the section effect |
| A-029 | CFD geometry is the inscribed 48-gon; the FE uses the true circle | **VALID** | exact faceting ratios (F-031); 0.038 mm chord gap handled by the mapping (F-038) |
| A-030 | Mapped temperature within ~11 mm of the inlet carries the Fluent node-reconstruction limitation | **ASSUMED** (bounded) | F-035; LC1 inlet peak bound ±9.8 MPa (F-040) |
| A-031 | Operating envelope limited by the 600 K air property table | **VALID** (constraint) | Q03 air-side maximum 583.4 K (F-047, F-049) |

## 4. Consequences for how results may be described

- Every final number is a **2026 simulation or calculation of a re-analysed problem**. Nothing may be called an internship result.
- Three things may not be called verified against reality: the supports (A-024), the imperfection-free geometry (A-025), and the material data (A-018, A-021, A-022).
- λ₁ values are idealised linear stability indicators. The static utilisation is a first-yield indicator. Neither is a real-world factor of safety.
