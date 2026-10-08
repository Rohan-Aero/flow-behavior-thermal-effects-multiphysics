# PROJECT CONCEPT — Section 1

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems
**Original internship:** Eleation, February – May 2025
**Engineer:** Rohan Balram Patel, B.Tech Aerospace Engineering
**Date:** 2026-09-18

> ### ⚠ RE-ANALYSIS
> The original project files were lost; a filesystem sweep on 2026-09-18 confirmed no
> original artefact survives on this machine. **Every parameter below was newly selected
> in 2026.** None of these are the original internship values, and no measured or
> experimental data appears anywhere in this project. Nothing here may be described as
> recovered, restored, or original.

---

## 1. Problem Statement

A thick-walled circular duct carries cooling air while its outer surface receives a steady
external heat load. Heat passes from the outer surface, through the solid wall by
conduction, and into the air by forced convection. The resulting non-uniform temperature
field makes the solid try to expand; because that expansion is partly resisted — by the
temperature gradient itself and by whatever holds the duct in place — thermal stress
develops.

The engineering difficulty is that **these physics cannot be assessed separately.** The
flow sets the convective coefficient; the convective coefficient sets the metal
temperature; the metal temperature sets the stress. A conservative guess at any one stage
propagates into a wrong answer at the end. This project solves the chain as a coupled
system and checks every link against independent theory.

## 2. Engineering Objective

Build a reproducible multiphysics model that predicts, for a heated internal-flow duct:

1. the turbulent flow field and pressure loss,
2. the conjugate (fluid ↔ solid) temperature distribution,
3. the resulting thermal expansion, stress and deformation,

and to **verify every stage against independent analytical theory before accepting it.**

The deliverable is not a colourful contour plot. It is a defensible chain of reasoning in
which every number traces to a hand calculation, a published correlation, or a solver run
on a documented machine.

## 3. Research Questions

| # | Question | Answered in |
|---|----------|-------------|
| RQ1 | Do CFD-predicted friction factor and Nusselt number agree with the Petukhov, Dittus–Boelter and Gnielinski correlations, and within what error band? | Section 5 vs Section 2 |
| RQ2 | How is temperature distributed through a thick solid wall, and how much of the total thermal resistance sits in the solid versus the fluid film? | Section 5 |
| RQ3 | Which dominates thermal stress — the through-wall **gradient**, or **restraint** of overall thermal growth? | Section 6 (LC1 vs LC2) |
| RQ4 | Is the duct structurally acceptable at operating temperature, and what governs the margin? | Section 6 |
| RQ5 | Is one-way thermal→structural coupling sufficient, or is two-way required? | Quantified in §12 |

**RQ3 is the heart of the project** — the question an interviewer is most likely to ask,
and the one a purely qualitative study cannot answer.

## 4. Geometry Concept `[RE-ANALYSED]`

A straight circular duct: an air passage surrounded by a concentric solid annulus.

| Parameter | Value | Engineering reason |
|-----------|-------|--------------------|
| Inner (bore) diameter, Dᵢ | **20 mm** | Sets the flow scale. Gives Re = 30 000 at low-subsonic air velocity, and is large enough to resolve a y⁺ ≈ 1 boundary layer without an excessive cell count. |
| Outer diameter, Dₒ | **40 mm** | Chosen so **Dₒ/Dᵢ = 2 exactly**, making ln(Dₒ/Dᵢ) = ln 2 and keeping the thick-walled-cylinder closed-form thermal stress solution a clean validation target. |
| Wall thickness, t | **10 mm** | Thick enough for a measurable through-wall gradient and a genuine 3-D conduction path, not a thin-shell approximation. |
| Heated length, L | **600 mm** | L/D = 30. Turbulent hydrodynamic entry length is **358 mm (x/D = 17.9)**, leaving ~12 diameters of fully developed flow for correlation comparison. |

**Deliberately simple.** No ribs, bends or fillets. Every extra geometric feature would
introduce a modelling choice that cannot be validated against theory — exactly what this
re-analysis must avoid.

**Why full 3-D rather than 2-D axisymmetric:** the problem as posed *is* axisymmetric, and
a 2-D axisymmetric CFD model would be far cheaper. Full 3-D is used anyway so that (a) the
structural analysis is a true 3-D thermo-elastic solution, and (b) the framework extends
to non-axisymmetric heating without rebuilding. This is an honest cost paid for a stated
reason.

## 5. Fluid `[RE-ANALYSED]`

**Air**, modelled as an **incompressible ideal gas**.

- *Why air:* aerospace-relevant coolant (bleed air, ram air, avionics cooling) with
  thoroughly published properties. It is also deliberately a **poor** coolant — which is
  the point. With air, metal temperature rather than air temperature becomes the design
  driver, a realistic engineering situation worth demonstrating.
- *Why incompressible ideal gas:* density falls ~19 % from 300 K to 369 K, so constant
  density is wrong. But the computed pressure drop is **412 Pa — 0.41 % of operating
  pressure** — so density has no meaningful pressure dependence. ρ = p_op/(RT) is therefore
  the correct model; full compressibility would add cost and solver stiffness for no gain.
- *Properties:* Incropera & DeWitt Table A.4, air at 1 atm. μ and k are temperature-dependent
  (μ varies ~20 % over the range); cₚ is held constant because it varies under 1.5 %.

## 6. Solid Material `[RE-ANALYSED]`

**Inconel 718** (aerospace nickel superalloy), Special Metals datasheet.

| Property | Value at operating temperature |
|----------|-------------------------------|
| Thermal conductivity k | 15.3 W/m·K (≈ 575 K) |
| Young's modulus E | 188.5 GPa (≈ 555 K) |
| Mean CTE α (from 294 K) | 13.9 × 10⁻⁶ /K |
| Poisson's ratio ν | 0.294 |
| Yield strength Sᵧ | 1060 MPa (≈ 555 K) |
| Density ρ | 8190 kg/m³ |

**Three reasons:**

1. Service temperature comfortably covers the computed **574 K (301 °C)** peak metal
   temperature — the material is not used outside its range.
2. **Low thermal conductivity** produces a measurable through-wall gradient. Aluminium
   would be nearly isothermal through the wall and would soften at these temperatures.
3. **High yield strength keeps both load cases elastic**, so linear analysis stays valid.
   With 316L stainless (hot Sᵧ ≈ 170 MPa) the restrained case would yield by a factor of
   four, requiring plasticity and destroying the clean LC1/LC2 comparison.

Properties are evaluated **at operating temperature, not room temperature** — a
non-conservative error otherwise.

*Worth noting for interview:* thermally, a cheap stainless would cope with 301 °C easily.
Inconel is required by the **structural** case, not the thermal one. The material choice is
driven by restraint, not by heat.

## 7. Operating Conditions `[RE-ANALYSED]`

| Quantity | Value |
|----------|-------|
| Operating pressure | 101 325 Pa |
| Inlet air temperature | 300 K (also the stress-free reference) |
| Inlet velocity | 23.5 m/s |
| Mass flow rate | 8.69 g/s |
| **Reynolds number** | **29 957 (inlet) → 25 548 (outlet)** |
| Mach number | 0.068 → 0.075 |
| Outlet bulk temperature | 368.9 K |
| Exit velocity | 28.9 m/s (accelerates as the gas heats) |

### Flow regime and turbulence model

- **Regime: fully turbulent.** Re = 29 957 at inlet, 25 548 at outlet — comfortably above
  the Re > 10⁴ threshold for Dittus–Boelter validity, never approaching transition. This
  matters: a Reynolds number decaying into the transitional range would invalidate every
  correlation used for verification.
- **Turbulence model: k-ω SST, wall-resolved (y⁺ ≤ 1).** SST integrates to the wall without
  wall functions. Conjugate heat transfer is acutely sensitive to near-wall resolution
  because **wall heat flux sets solid temperature, which sets stress** — a wall-function
  error would propagate straight into the final answer. A cheaper k-ε + wall function model
  would *model* the very quantity of interest instead of resolving it.
  *(Verified on this machine: Fluent 2026 R1 defaults to k-ω SST.)*
- **First cell height 12.2 µm**, from the Petukhov friction factor at inlet (the most
  demanding station). 18 inflation layers at growth 1.2 give a 1.56 mm prism stack ≈ 16 %
  of the pipe radius.

### Steady vs transient

**Steady-state.** All boundary conditions are time-invariant and the quantity sought is the
equilibrium thermal-stress state. A transient solve would multiply cost by 1–2 orders of
magnitude to reach the same final answer. Start-up and shutdown transients are a legitimate
follow-on study, but a *different* question.

### Energy equation

**Required and enabled.** Two secondary terms were checked and neglected with numbers, not
assertions:

| Check | Value | Verdict |
|-------|-------|---------|
| Buoyancy — Richardson number Gr/Re² | **4.26 × 10⁻⁵** ≪ 0.1 | Pure forced convection; gravity omitted |
| Viscous dissipation — Brinkman number | **2.30 × 10⁻³** ≪ 1 | Negligible |
| Péclet number Re·Pr | 17 806 | Strongly advection-dominated |

## 8. Inlet Condition `[RE-ANALYSED]`

**Velocity inlet:** 23.5 m/s, 300 K, turbulence intensity 4.4 % (I = 0.16 Re^(−1/8)),
turbulent length scale = hydraulic diameter = 20 mm.

*Why a velocity inlet:* inlet temperature and operating pressure are both fixed, so inlet
density is fixed, so a velocity inlet **fixes the mass flow exactly**. That makes the global
energy balance Q = ṁ·cₚ·ΔT_b an exact arithmetic check on the converged solution — the
single most diagnostic validation available.

## 9. Outlet Condition `[RE-ANALYSED]`

**Pressure outlet**, 0 Pa gauge, backflow temperature 370 K.

*Why:* the standard well-posed choice for subsonic internal flow discharging to ambient. It
lets the solver determine the outlet profile rather than imposing one — which matters here
because the flow **accelerates from 23.5 to 28.9 m/s purely from heating**.

## 10. Heating Condition `[RE-ANALYSED]`

**Uniform heat flux q″ = 8 000 W/m² on the outer cylindrical surface.** Both end annular
faces **adiabatic**. The fluid–solid interface is a **coupled (conjugate) wall** — its
temperature is solved, never prescribed.

Consequences: Q = **603.2 W**, inner-surface flux q″ᵢ = **16 000 W/m²** (= q″ₒ·Dₒ/Dᵢ),
linear heat rate q′ = 1005 W/m.

*Why constant heat flux rather than fixed wall temperature or external convection:*

1. Constant q″ gives a **linear bulk temperature rise** and a **constant wall-to-bulk
   difference** in the developed region — both exactly checkable against theory.
2. Total heat input is known *a priori*, so energy conservation becomes a hard pass/fail test.
3. A convection BC would require inventing an external h and T∞ — two more unjustifiable
   numbers in a project that must minimise them.

*Why this magnitude — and why it changed.* An initial selection of 12 000 W/m² was
**rejected during Section 1**. The correlation-validity check (§ASSUMPTIONS A-006) showed
that with the property-variation correction applied, the restrained load case reached
**105 % of hot yield** — and whether it passed or failed flipped with the correction
exponent, which has real literature spread (n = 0.4–0.575). A design point whose verdict
depends on a coefficient's third significant figure is not defensible. At 8 000 W/m² both
load cases stay **clearly elastic under either treatment** (utilisation 0.50 uncorrected,
0.63 corrected), so the conclusion is robust.

*Why adiabatic ends:* isolates one-dimensional radial conduction and avoids an arbitrary
end-loss assumption that could not be justified.

## 11. Structural Constraints `[RE-ANALYSED]`

Two load cases share **one identical temperature field** — only the restraint differs. This
is the experiment that answers RQ3.

| Case | Restraint | Isolates |
|------|-----------|----------|
| **LC1** | Statically determinate: one end restrained axially, minimal extra restraint to remove rigid-body motion. Free radial and axial growth. | Stress from the temperature **gradient** alone |
| **LC2** | Both end faces fully restrained axially. | Stress from **restrained thermal growth** |

Reference (stress-free) temperature **300 K**, matching assembly/inlet conditions.

**Predicted outcome (to be tested by FEA, not assumed):**

| | LC1 | LC2 | Ratio |
|---|---|---|---|
| Constant-property temperatures | 17.0 MPa | −539 MPa | 32× |
| Property-corrected temperatures | 16.5 MPa | −668 MPa | **40×** |
| Utilisation of hot yield | 0.016 | **0.63** | — |
| Margin of safety | 61 | **0.59** | — |

If confirmed, **the design driver is the mounting arrangement, not the thermal gradient.**

## 12. Coupling Strategy — one-way, with quantitative justification

**Conjugate heat transfer (fluid ↔ solid thermal) is fully two-way and solved
simultaneously inside Fluent.** This is the core physics and is not simplified.

**The thermal → structural link is one-way** (CFD temperatures mapped to Mechanical).
Justification is a number, not a preference:

- Free radial growth of the bore = **35 µm**, i.e. **0.35 % of the radius**
- Resulting flow-area change = **0.71 %**
- Turbulence-model uncertainty on Nusselt number ≈ **5–15 %**

The deformation-induced change to the flow is **an order of magnitude smaller than the
model uncertainty already present**. Two-way coupling via System Coupling would cost 5–10×
the runtime and memory to resolve a change buried in noise — indefensible on a 15.7 GB
laptop, and indefensible on a cluster too.

*This distinction — two-way CHT, one-way thermo-structural — is precisely the nuance an
interviewer will probe. State it in exactly those terms.*

## 13. Expected Outputs

**Flow**
1. Velocity field; development from uniform inlet to fully developed turbulent profile
2. Pressure drop split into friction (263 Pa) and thermal acceleration (149 Pa)
3. Wall shear stress and friction factor vs Petukhov (f ≈ 0.0241)
4. y⁺ distribution — a mesh-quality verification, not a result

**Thermal**
5. Bulk temperature Tb(x) — expected linear, 300 → 369 K
6. Local and average Nusselt number vs Dittus–Boelter and Gnielinski
7. Conjugate temperature field in the solid: radial and axial distributions
8. Inner/outer wall temperature profiles; through-wall ΔT ≈ 7.2 K
9. Global energy balance closure

**Structural**
10. Displacement field; axial growth and bore dilation
11. Radial, hoop, axial and von Mises stress vs the thick-walled-cylinder closed form
12. LC1 vs LC2 comparison
13. Margin of safety against hot yield

**Verification**
14. Mesh independence across three refinement levels
15. Consolidated theory-vs-CFD-vs-FEA comparison table with error percentages

## 14. Physics Chain

```
 AIR FLOW           CONVECTION          CONDUCTION          EXPANSION          STRESS
 Re 29 957     →    h  78-97       →   dT_wall 7.2 K   →   a = 13.9e-6/K  →  LC1   16.5 MPa
    -> 25 548       W/m2K              T_metal 574 K       bore +35 um       LC2 -668 MPa
 k-w SST y+~1       Nu  50-62          (301 degC)          Tref = 300 K      MoS 0.59
      |                  |                    |                  |                 |
      +--- ANSYS Fluent: conjugate, TWO-WAY ---+                  |                 |
                                               +-- ONE-WAY map -->+- ANSYS Mechanical
```

## 15. Why This Problem Is Defensible in an Interview

- Every stage has an **independent analytical check** — Petukhov, Dittus–Boelter,
  Gnielinski, the 1-D energy balance, and the Timoshenko thick-cylinder solution.
- Every simplification is justified by a **computed dimensionless number**, not by assertion.
- The geometry is simple enough that nothing hides behind mesh complexity.
- It produces a **genuine engineering conclusion** — restraint dominates gradient by ~40× —
  rather than just pictures.
- A design parameter was **changed because a validity check failed**, and the reasoning is
  documented. That trail is worth more in an interview than a result that was right first
  time.
- The honest limitations — Student 4-core cap, RANS uncertainty, correlations outside their
  strict validity range, version mismatch with the 2025 original — are all documented
  rather than glossed over.
