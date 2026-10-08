# ENGINEERING THEORY — Section 2

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems
**Original internship:** Eleation, February – May 2025
**Date:** 2026-09-18

> ### ⚠ RE-ANALYSIS
> The original project data was lost. Every parameter here is **class B (re-analysed /
> assumed)** or **class C (calculated)**. **No parameter is class A** — no surviving
> evidence exists. Nothing in this phase is tuned to match a simulation, because **no CFD
> has been run yet.**

---

## 1. Why this phase exists

A CFD result is a number on a screen. It becomes an *engineering* result only when
something independent says it is plausible. This phase builds that independent
something — a complete analytical model of the same problem, derived from first
principles and published correlations, **before** any mesh exists.

The order matters and is not negotiable: **theory first, simulation second.** If the
analytical baseline were built after seeing CFD output, it would inevitably be nudged
toward agreement, and the verification would be worthless.

## 2. The physical chain

Five physical processes in series, each feeding the next:

| # | Process | Governed by | Sets |
|---|---------|-------------|------|
| 1 | Turbulent internal flow | Navier–Stokes + RANS closure | velocity field, wall shear, pressure drop |
| 2 | Forced convection | Newton's law of cooling, Nu correlations | heat transfer coefficient *h* |
| 3 | Conduction in the solid | Fourier's law (cylindrical) | through-wall temperature drop |
| 4 | Thermal expansion | ε = α ΔT | strain the metal *wants* to take |
| 5 | Thermal stress | Hooke's law with thermal strain | stress where that strain is prevented |

**The critical insight is that the chain has one bottleneck.** The solid carries only
**3.4 %** of the total thermal resistance; the air-side film carries **96.6 %**. So metal
temperature — and therefore every stress in the project — is governed almost entirely by
*h*, not by the metal's conductivity. An error in the turbulence model propagates
straight through to the structural answer. This is why so much of Section 2 is spent on
getting *h* honest rather than precise.

## 3. Governing physics, and what is deliberately left out

### Retained

- **Conservation of mass, momentum and energy** in the fluid (steady, RANS-averaged).
- **Temperature-dependent fluid properties** — μ varies ~20 % and *k* ~18 % over the
  operating range.
- **Variable density via the ideal gas law**, ρ = p_op/(RT). Density falls 19 % from inlet
  to outlet; treating it as constant would lose the flow acceleration entirely.
- **Conjugate conduction** in the solid with temperature-dependent k(T).
- **Temperature-dependent solid structural properties** — E falls ~8 % and yield ~4 % over
  the range.

### Removed, each with a number

| Neglected effect | Criterion | Value | Verdict |
|---|---|---|---|
| Buoyancy / natural convection | Richardson Gr/Re² | **4.37 × 10⁻⁵** ≪ 0.1 | negligible |
| Viscous dissipation | Brinkman Br | **1.82 × 10⁻³** ≪ 1 | negligible |
| Compressibility | Mach | **≤ 0.075** ≪ 0.3 | negligible |
| Pressure-driven density change | Δp/p_op | **0.44 %** | negligible |
| Axial conduction in the solid | axial gradient 75 K/m vs radial 728 K/m | ratio 0.10 | second order |
| Pressure (hoop) stress | p·rᵢ/t at Δp gauge | **0.0004 MPa** vs 657 MPa thermal | negligible |
| Internal surface radiation | see `MATERIAL_PROPERTIES.md` / ASSUMPTIONS A-015 | net axial potential σ(T⁴max−T⁴min) ≈ 1.7 kW/m² vs 16 kW/m² applied ≈ **11 %**, cut further by small view factors | **flagged, conservative** |

Every one of these is a computed number, not an assertion. That is the standard the whole
project is held to.

## 4. The three verification layers

The CFD and FEA will each be checked at three independent levels. They are listed in
order of how hard they are to fake:

**Layer 1 — Conservation.** Q = ṁ cₚ ΔT. This involves no correlation, no turbulence
model, and no property uncertainty beyond cₚ. **Outlet bulk temperature is fixed by the
energy balance alone and is completely independent of *h*.** If Fluent disagrees here, the
boundary conditions or the convergence are wrong — full stop. Target: **603.2 W, 368.9 K**.

**Layer 2 — Correlations.** Petukhov friction factor, Dittus–Boelter and Gnielinski
Nusselt numbers. These carry real uncertainty (5–15 %) and, in this problem, are being
used near the edge of their validity. The acceptance band is deliberately wide and
honestly stated rather than narrow and false.

**Layer 3 — Closed-form elasticity.** The Timoshenko thick-walled-cylinder solution for a
logarithmic radial temperature field. Exact for an infinitely long cylinder with free
ends — so agreement away from the end faces validates the thermal mapping and the FEA
itself, while disagreement *near* the ends is expected physics, not error.

## 5. The engineering question this project answers

> **Does thermal stress in a heated duct come from the temperature gradient through the
> wall, or from restraint of the duct's overall thermal growth?**

The analytical model answers it before any simulation runs:

| | LC1 — free expansion | LC2 — fully restrained |
|---|---|---|
| Peak stress | **16.3 MPa** | **−657 MPa** |
| Utilisation of hot yield | 0.016 | **0.642** |
| Margin of safety | 61 | **0.56** |

**A factor of 40.** The gradient contributes almost nothing; restraint dominates
completely. If the FEA confirms this, the design driver is the mounting arrangement, not
the thermal load — and the engineering recommendation writes itself: the duct must be
allowed to grow.

This conclusion is robust. Across the entire literature range of the property-correction
exponent (n = 0.4 to 0.575) the utilisation moves only from 0.61 to 0.67 — the design
stays elastic throughout, and the 40× ratio barely moves.

## 6. What would falsify this

Stating this in advance is what makes it engineering rather than storytelling. The
baseline is wrong if:

- the CFD energy balance misses 603 W by more than 0.5 % **with converged residuals**;
- the CFD Nusselt number lands outside **44–67** — below means the near-wall mesh is
  under-resolved or y⁺ is too coarse; above means the property variation is not being
  captured;
- the through-wall ΔT departs far from **7.3 K** — that would mean the conjugate interface
  is not actually coupled;
- the FEA LC2 axial stress is not close to **−E α ΔT** away from the end faces — that
  would mean the temperature mapping has failed;
- LC2 utilisation reaches 1.0 — linear-elastic analysis would then be invalid and
  plasticity would be required.

## 7. Documents in this phase

| File | Contents |
|------|----------|
| `BASELINE_PARAMETERS.md` | The frozen parameter sheet with A/B/C provenance |
| `GOVERNING_EQUATIONS.md` | Every equation used, with validity range |
| `FLUID_CALCULATIONS.md` | Fluid mechanics and pressure drop |
| `HEAT_TRANSFER_CALCULATIONS.md` | Convection, energy balance, conduction |
| `THERMAL_STRESS_ESTIMATE.md` | Expansion and approximate stress |
| `MATERIAL_PROPERTIES.md` | Property audit with sources and audit findings |
| `EXPECTED_RESULTS.md` | Expected ranges — the CFD/FEA sanity check |
| `baseline_calculations.py` | The executable model (self-testing) |
| `baseline_results.csv` | 65 computed quantities |
| `calculation_plots/` | 6 figures |
