# ASSUMPTIONS REGISTER — Section 1

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems (RE-ANALYSIS, 2026)
**Date:** 2026-09-18

> Every assumption below was made in 2026. None is inherited from the lost 2025 original.
> Severity reflects **how much the final answer would move if the assumption were wrong**,
> not how likely it is to be wrong.

**Legend —** `[ASSUMED]` engineering choice · `[JUSTIFIED]` supported by a computed number ·
`[LITERATURE]` published data · `[UNVERIFIED]` not yet confirmed and should be

---

## 🔴 FLAGGED — assumptions that materially affect the answer

### A-006 · Constant-property correlations are applied outside their strict validity range
**Severity: HIGH · Status: `[JUSTIFIED]` with correction applied · Affects: Nu, wall temperature, all stress**

Dittus–Boelter and Gnielinski are **constant-property** correlations. For gases their
usual stated validity is a wall-to-bulk temperature difference of order **60 K**. In this
problem that difference reaches **165 K (constant-property) to 205 K (corrected)** — far
outside the range — because air is a poor coolant and the imposed flux is substantial.

Ignoring this would **overstate h and understate metal temperature**, which propagates
directly into the stress result.

**Treatment.** The Kays & Crawford property-ratio correction for turbulent gas heating is
applied and solved iteratively (wall temperature depends on h, which depends on wall
temperature):

```
Nu = Nu_constant-property × (Tb / Tw)^n        n = 0.5
```

| Quantity at exit | Constant-property | Property-corrected | Shift |
|---|---|---|---|
| Nusselt number | 61.9 | **49.6** | −20 % |
| h (W/m²·K) | 97.2 | **77.9** | −20 % |
| Inner wall temperature | 533.5 K | **574.3 K** | **+40.8 K** |
| Volume-mean solid temperature | 506.8 K | **554.6 K** | +47.8 K |
| LC2 axial stress | −539 MPa | **−668 MPa** | +24 % |

**Residual uncertainty.** The exponent *n* is quoted in the literature between **0.4 and
0.575**. The verification band was widened accordingly rather than quoting a single number:
accept CFD Nusselt anywhere in **44–67**, expecting a value near 50.

**Why this is not fatal.** Fluent solves with temperature-dependent air properties and a
wall-resolved boundary layer, so it captures this effect *natively*. The correction exists
only to set an honest expectation for what CFD should produce — the CFD result does not
depend on it.

**A subtle point worth stating in interview:** the correction moves the **wall**
temperature, not the **bulk** temperature. Bulk temperature is fixed by the energy balance
(Q = ṁcₚΔT) and is completely independent of h. That is exactly why outlet bulk temperature
is the most robust verification target available.

---

### A-015 · Surface-to-surface radiation inside the duct is neglected
**Severity: MEDIUM · Status: `[ASSUMED]`, partially justified · Affects: axial wall temperature distribution**

At a peak inner-wall temperature of 574 K, σT⁴ ≈ **6.2 kW/m²** against an applied inner
flux of 16 kW/m² — not obviously negligible in absolute terms.

**Why it is nevertheless reasonable:**

- Net radiative exchange depends on temperature **differences between surfaces that see
  each other**, not on absolute emissive power. The duct is **circumferentially isothermal**
  (axisymmetric heating), so ring-to-ring exchange at the same axial station is net zero.
- Axially, wall temperature spans ~475 → 574 K, but **view factors between axially distant
  ring elements in a long thin tube are small**, so axial radiative redistribution is a
  second-order smoothing effect, not a first-order heat path.
- Air is effectively **transparent in the infrared**, so there is no participating-medium
  absorption to model.

**Effect if wrong:** would slightly flatten the axial wall-temperature profile — reducing
peak metal temperature and mildly reducing LC2 stress. **The current assumption is therefore
conservative.**

**Recommended follow-up:** enable Fluent's Surface-to-Surface (S2S) radiation model with
ε ≈ 0.75 (oxidised Inconel) as a sensitivity case in a later phase. Not required for the
baseline.

---

### A-003 · ANSYS Student solver size limits are partly unverified
**Severity: MEDIUM · Status: partly `[VERIFIED]`, partly `[UNVERIFIED]` · Affects: achievable mesh**

| Limit | Status |
|-------|--------|
| Fluent parallel execution capped at **4 cores** | ✅ **VERIFIED** — Fluent transcript, 2026-09-18: *"Your license enables 4-way parallel execution"* |
| Fluent cell limit (commonly quoted 1 024 000) | ❌ **UNVERIFIED** — quoted from general knowledge, not measured on this install |
| Mechanical node/element limit (commonly quoted 128 000) | ❌ **UNVERIFIED** — same |

The planned mesh (**~167 760 cells**, **~48 048 solid nodes**) sits far below any plausible
limit, so the project is not at risk. **But the numbers must not be presented as fact until
measured.** They will be confirmed empirically during the Section 4 mesh independence study,
where the finest mesh level naturally tests the ceiling.

---

### A-001 / A-002 · Facts about the original internship that cannot be recovered
**Severity: LOW for the physics, HIGH for how the work is described · Status: `[UNVERIFIED]`**

| ID | Assumption | Needs |
|----|-----------|-------|
| A-001 | The original internship used a Student/academic ANSYS licence comparable to the one installed here. | **Confirmation from Rohan** |
| A-002 | The original project was a single coupled case, not a parametric study campaign. | **Confirmation from Rohan** |

These change nothing technically, but they change what may honestly be said about the
original work. Until confirmed, neither should be asserted in the report.

---

## 🟢 JUSTIFIED — assumptions supported by a computed number

| ID | Assumption | Justification | Status |
|----|-----------|---------------|--------|
| A-004 | **Steady-state** analysis is sufficient. | All BCs are time-invariant; the equilibrium thermal-stress state is the quantity sought. A transient solve costs 1–2 orders of magnitude more to reach the same answer. | `[JUSTIFIED]` |
| A-005 | Air modelled as **incompressible ideal gas** (density varies with T, not p). | Pressure drop is **412 Pa = 0.41 %** of operating pressure → density has no meaningful pressure dependence. Mach 0.068–0.075 ≪ 0.3. | `[JUSTIFIED]` |
| A-007 | **Buoyancy / natural convection neglected**; gravity omitted. | Richardson number **Gr/Re² = 4.26 × 10⁻⁵** ≪ 0.1 (Gr = 27 789). Pure forced convection. | `[JUSTIFIED]` |
| A-008 | **Viscous dissipation neglected.** | Brinkman number **Br = 2.30 × 10⁻³** ≪ 1 (Ec = 3.33 × 10⁻³). | `[JUSTIFIED]` |
| A-009 | **One-way** thermal→structural coupling. | Free bore growth 35 µm = 0.35 % of radius → **0.71 % flow-area change**, an order of magnitude below the 5–15 % turbulence-model uncertainty on Nu. Two-way costs 5–10× for a change buried in noise. | `[JUSTIFIED]` |
| A-017 | Fully developed flow assumed **only** for x/D > 18 when comparing to correlations. | Turbulent entry length L_h = 1.359·D·Re^0.25 = **358 mm (x/D = 17.9)**. The entry region is reported separately, not averaged in. | `[JUSTIFIED]` |

---

## ⚪ STANDARD — conventional modelling assumptions

| ID | Assumption | Note | Status |
|----|-----------|------|--------|
| A-010 | Uniform heat flux on the outer cylindrical surface. | An idealisation of a real thermal environment, chosen because it makes energy input known *a priori* and the bulk temperature rise exactly checkable. | `[ASSUMED]` |
| A-011 | End annular faces **adiabatic**. | Isolates 1-D radial conduction; avoids an arbitrary end-loss coefficient that could not be justified. | `[ASSUMED]` |
| A-012 | **Linear elastic** material; no plasticity, no creep. | Valid because both load cases stay below hot yield (max utilisation **0.63**). Creep is negligible for Inconel 718 at 301 °C — it becomes relevant above ~550 °C. | `[JUSTIFIED]` |
| A-013 | Structural properties (E, α, Sᵧ) evaluated at **mean operating temperature**, held constant within a load case. | E varies ~4 % and Sᵧ ~4 % over the actual 475–581 K span. Using room-temperature values would be a non-conservative error; using mean-operating values is standard practice. | `[LITERATURE]` |
| A-014 | **Hydraulically smooth** walls; no surface roughness. | Petukhov and Gnielinski both assume smooth pipe. A machined duct is close to smooth at these Reynolds numbers. Roughness would raise both f and Nu. | `[ASSUMED]` |
| A-016 | Stress-free reference temperature **300 K**, equal to inlet/assembly temperature. | Defines the datum from which thermal strain is measured. | `[ASSUMED]` |
| A-018 | Inconel 718 properties from a **generic published datasheet**, not a specific heat or lot. | Real material certificates vary by a few percent. Acceptable for a design study; would need lot-specific data for a certification analysis. | `[LITERATURE]` |
| A-019 | Air treated as a **non-participating medium** for radiation. | Physically correct — air is essentially transparent in the infrared. | `[JUSTIFIED]` |
| A-020 | Perfect thermal contact at the fluid–solid interface (no contact resistance). | Correct by definition for a conjugate fluid–solid interface; there is no joint here. | `[JUSTIFIED]` |

---

## Assumptions that would change the conclusion if wrong

Ranked by impact on the central finding (RQ3: restraint vs gradient):

1. **A-006** — if the property correction were much larger than assumed, metal temperature
   and hence LC2 stress would rise further. At n = 0.575 the utilisation approaches 0.7;
   still elastic, and **the LC2 ≫ LC1 conclusion is unaffected**.
2. **A-010/A-011** — a non-uniform or one-sided heat flux would break axisymmetry and
   introduce bending, adding a stress mechanism not present here. **This is the single most
   interesting extension** for a follow-on study.
3. **A-015** — radiation would flatten the axial profile and slightly *reduce* LC2 stress.
   Current assumption is conservative.
4. **A-012** — irrelevant unless the design point moves; at 0.63 utilisation there is
   ample elastic margin.

**The central finding — that restraint dominates the through-wall gradient by roughly 40×
— survives every one of these.** That robustness is the point of documenting them.
