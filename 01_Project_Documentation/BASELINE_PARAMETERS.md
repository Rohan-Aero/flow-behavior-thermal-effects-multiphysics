# FROZEN BASELINE PARAMETER SHEET — Section 2, Step 1

**Frozen on:** 2026-09-18 · **Machine-readable copy:** `baseline_parameters.json`

> ### ⚠ CLASSIFICATION NOTICE
> **No parameter in this project is class A.** The original internship data was lost and a
> filesystem sweep on 2026-09-18 confirmed no surviving artefact. Class A is retained in the
> scheme only to make its absence explicit and impossible to overlook.

| Class | Meaning | Count |
|-------|---------|-------|
| **A** | Documented from surviving evidence | **0** |
| **B** | Re-analysed / assumed during the 2026 re-analysis | **17** |
| **C** | Calculated from other parameters | all derived quantities |

---

## Geometry

| Parameter | Symbol | Value | Units | Class | Basis |
|---|---|---|---|---|---|
| Inner (bore) diameter | Dᵢ | 0.020 | m | **B** | Section 1 D-008 — gives Re = 30 000 at low-subsonic velocity |
| Outer diameter | Dₒ | 0.040 | m | **B** | Section 1 D-008 — Dₒ/Dᵢ = 2 exactly → ln 2 → clean closed-form check |
| Wall thickness | t | 0.010 | m | **C** | (Dₒ − Dᵢ)/2 |
| Heated length | L | 0.600 | m | **B** | Section 1 D-008 — L/D = 30 |
| Flow area | A_c | 314.159 | mm² | **C** | π rᵢ² |
| Wetted perimeter | P_w | 62.832 | mm | **C** | π Dᵢ |
| Hydraulic diameter | D_h | 20.000 | mm | **C** | 4A_c/P_w — **exactly Dᵢ** for a circular duct |

## Fluid and operating conditions

| Parameter | Symbol | Value | Units | Class | Basis |
|---|---|---|---|---|---|
| Working fluid | — | Air | — | **B** | Section 1 D-009 |
| Density model | ρ | incompressible ideal gas | — | **B** | ρ = p_op/(RT); Δp/p = 0.44 % |
| Inlet temperature | T_in | 300.0 | K | **B** | Standard ambient; also the stress-free reference |
| Operating (absolute) pressure | p_op | 101 325 | Pa | **B** | Sea-level static |
| Inlet velocity | V_in | 23.5 | m/s | **B** | Set to hit Re = 30 000 |
| Outlet pressure | p_out | 0 (gauge) | Pa | **B** | Pressure outlet discharging to ambient |
| Specific gas constant | R | 287.058 | J/kg·K | **B** | Standard dry air |
| Ratio of specific heats | γ | 1.4 | — | **B** | Used only for Mach number |
| Volumetric flow rate | Q_v | 7.383 | L/s | **C** | V·A_c |
| **Mass flow rate** | ṁ | **8.686** | **g/s** | **C** | ρ_in V A_c |
| Mass flux | G | 27.650 | kg/m²·s | **C** | ṁ/A_c — invariant along the duct |

## Thermal boundary condition

| Parameter | Symbol | Value | Units | Class | Basis |
|---|---|---|---|---|---|
| **Heat flux on outer surface** | q″ₒ | **8 000** | **W/m²** | **B** | Section 1 D-015 — re-selected from 12 000 after the correlation-validity check |
| End annular faces | — | adiabatic | — | **B** | Isolates 1-D radial conduction |
| Fluid–solid interface | — | coupled (conjugate) | — | **B** | Wall temperature is *solved*, never imposed |
| Inner-surface heat flux | q″ᵢ | 16 000 | W/m² | **C** | q″ₒ·(Dₒ/Dᵢ) |
| Total heat rate | Q | 603.19 | W | **C** | q″ₒ·A_o |

> **There is no imposed wall temperature anywhere in this model.** That is the point of a
> conjugate analysis: wall temperature is an output, not an input.

## Solid material — Inconel 718

| Parameter | Symbol | Value | Units | Class | Basis |
|---|---|---|---|---|---|
| Material | — | Inconel 718, age-hardened | — | **B** | Section 1 D-010 |
| Density | ρ_s | 8190 | kg/m³ | **B** | Special Metals; 0.9 % source spread — does not enter any steady-state result |
| Thermal conductivity at 575 K | k_s | 15.22 | W/m·K | **B** | VDM datasheet, interpolated |
| Specific heat at 555 K | c_p,s | 481 | J/kg·K | **B** | VDM datasheet — unused in steady state |
| Young's modulus at 555 K | E | 188.1 | GPa | **B** | VDM datasheet, interpolated |
| Poisson's ratio | ν | 0.294 | — | **B** | Literature 0.284–0.294; upper end taken (conservative for LC1) |
| Mean CTE at 555 K | α | 13.72 × 10⁻⁶ | 1/K | **B** | Special Metals mean CTE from 21 °C |
| **Hot yield strength at 555 K** | S_y | **1023.7** | **MPa** | **B** | VDM datasheet — **revised down from 1060 by the Section 2 audit** |

## Structural support assumptions

| Case | Restraint | Class | Purpose |
|---|---|---|---|
| **LC1** | One end restrained axially; minimal additional restraint to remove rigid-body motion. Radial and axial growth free. | **B** | Isolates stress from the temperature **gradient** |
| **LC2** | Both end faces fully restrained axially. | **B** | Isolates stress from **restrained thermal growth** |
| Reference temperature | T_ref = 300 K (stress-free) | **B** | Assembly / inlet condition |
| Material model | Linear elastic, no plasticity, no creep | **B** | Valid while utilisation < 1 (max 0.64) |
| Pressure loading | Neglected | **B** | p·rᵢ/t = 0.0004 MPa vs 657 MPa thermal |

## Correlation and loss parameters

| Parameter | Symbol | Value | Class | Note |
|---|---|---|---|---|
| Property-variation exponent | n | 0.5 | **B** | Kays & Crawford; literature 0.4–0.575, sensitivity computed |
| Sharp entrance loss | K_in | 0.5 | **B** | **Not in the CFD domain** — installation only |
| Sudden exit loss | K_out | 1.0 | **B** | **Not in the CFD domain** — installation only |
| Entry-region increment | K(∞) | 0.09 | **B** | **Is** in the CFD domain (developing flow) |

---

## Changes made in Section 2 — declared, not silent

Section 1 froze the design. The Section 2 property audit refined four *material property*
values against published mill datasheets. **No geometry, fluid, boundary condition or
design decision was altered.**

| Property | Section 1 | Section 2 (audited) | Δ | Why |
|---|---|---|---|---|
| **Yield strength S_y** | 1060 MPa | **1023.7 MPa** | **−3.4 %** | 🔴 Section 1 value was **non-conservative**. VDM datasheet is lower. Corrected. |
| Mean CTE α | 13.9 × 10⁻⁶ | 13.72 × 10⁻⁶ | −1.3 % | Interpolated to the actual mean solid temperature rather than a nearby table row |
| Young's modulus E | 188.5 GPa | 188.1 GPa | −0.2 % | VDM datasheet — independent confirmation to within 0.2 % |
| Specific heat c_p,s | 435 J/kg·K | 481 J/kg·K | +10.6 % | Section 1 value was low; **irrelevant** — unused in a steady-state solution |

**Net effect on the conclusion:** LC2 moves from −668 to **−657 MPa**, utilisation from
0.63 to **0.642**, margin of safety from 0.59 to **0.56**. The Section 1 finding is
confirmed, slightly tightened, and now rests on a verified source.
