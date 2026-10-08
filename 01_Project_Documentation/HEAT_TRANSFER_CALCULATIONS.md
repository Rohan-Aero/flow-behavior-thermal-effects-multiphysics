# HEAT TRANSFER CALCULATIONS — Section 2

**RE-ANALYSIS (2026).** Computed by `baseline_calculations.py`. **No CFD has been run.**

---

## 1. The three categories — kept strictly separate

Conflating these is the commonest way a thermal analysis goes quietly wrong, so they are
tabulated apart and never mixed.

### (a) Fluid properties — looked up, never chosen

| Property | Inlet (300 K) | Outlet (368.9 K) | Source |
|---|---|---|---|
| Specific heat cₚ | 1007 | 1011 J/kg·K | Incropera Table A.4 |
| Dynamic viscosity μ | 1.846 × 10⁻⁵ | 2.176 × 10⁻⁵ Pa·s | Incropera Table A.4 |
| Thermal conductivity k | 0.02624 | 0.03123 W/m·K | Incropera Table A.4 |
| **Prandtl number Pr** | **0.707** | **0.696** | Incropera Table A.4 |
| Density ρ | 1.1766 | 0.9569 kg/m³ | **computed** from p_op/(RT) |

> Density is deliberately **not** taken from the table. Standard air tables tabulate density
> at 100 kPa, not 101.325 kPa — a 1.3 % discrepancy that would silently break the mass
> balance. Computing ρ from the ideal gas law at the stated operating pressure keeps the
> model self-consistent. See `MATERIAL_PROPERTIES.md`.

### (b) Imposed thermal boundary conditions — chosen, never calculated

| Quantity | Value | Note |
|---|---|---|
| **Outer-surface heat flux q″ₒ** | **8 000 W/m²** | the single imposed thermal load |
| End annular faces | adiabatic | |
| Fluid–solid interface | coupled (conjugate) | temperature **solved**, not imposed |
| Inlet air temperature | 300 K | |

### (c) Calculated quantities — outputs

| Quantity | Value |
|---|---|
| Inner heat-transfer area Aᵢ | 376.99 cm² |
| Outer heated area A_o | 753.98 cm² |
| Inner-surface flux q″ᵢ | 16 000 W/m² |
| Total heat rate Q | 603.19 W |
| Nusselt, convective coefficient, all temperatures | below |

**Area-ratio identity check:** q″ᵢ/q″ₒ = 2.0000 against Dₒ/Dᵢ = 2.0000. The same heat
crosses a smaller area, so the inner flux must be exactly double. The script asserts this
to 10⁻⁹ — a cheap guard against a geometry or area error.

## 2. Choice of Nusselt correlation, justified on four axes

| Axis | This problem | Verdict |
|---|---|---|
| **Geometry** | circular duct, smooth, L/D = 30 > 10 | ✅ both correlations apply |
| **Flow regime** | fully turbulent, Re 25 548 – 29 957 | ✅ inside both validity windows |
| **Thermal BC** | uniform wall **heat flux** (not wall temperature) | ✅ the classical case these were fitted for |
| **Fluid** | air, Pr ≈ 0.70 | ✅ inside D-B (0.6–160) and Gnielinski (0.5–2000) |

**Gnielinski is the primary correlation.** Dittus–Boelter is a simple power law fitted
largely at high Reynolds number and is known to over-predict at Re ≈ 2–3 × 10⁴ — exactly
our range. Gnielinski carries the friction factor explicitly and handles moderate Re
better. Dittus–Boelter is retained as an upper bound because it is the correlation most
readers will reach for, and its spread against Gnielinski (**7.9 %**) is an honest measure
of correlation uncertainty before any other effect is considered.

## 3. 🔴 The validity problem — and the correction

Both correlations are **constant-property**. For gases their usual validity is a
wall-to-bulk temperature difference of order **60 K**.

**In this problem it reaches 206 K.**

This is not a detail. Ignoring it would over-predict *h* by ~20 %, under-predict metal
temperature by ~41 K, and under-predict the restrained thermal stress by ~5 %.

**Correction applied** (Kays & Crawford, turbulent gas, heating), solved iteratively
because T_w depends on *h* which depends on T_w:

```
Nu = Nu_constant-property * ( T_b / T_w )^n          n = 0.5
```

| Quantity at exit | Constant-property | **Property-corrected** | Shift |
|---|---|---|---|
| Nu (Dittus–Boelter) | 66.79 | — | upper bound |
| Nu (Gnielinski) | 61.87 | **49.58** | −20 % |
| h (W/m²·K) | 97.13 | **77.83** | −20 % |
| Inner wall temperature | 533.6 K | **574.4 K** | **+40.8 K** |

**Residual uncertainty.** The exponent *n* is quoted between 0.4 and 0.575 in the
literature. The sensitivity is computed rather than hand-waved:

| n | T_w,i at exit | Mean solid T | LC2 stress | Utilisation |
|---|---|---|---|---|
| 0.400 | 564.1 K | 542.3 K | −624.6 MPa | 0.609 |
| **0.500** | **574.4 K** | **554.7 K** | **−657.2 MPa** | **0.642** |
| 0.575 | 583.2 K | 565.6 K | −685.7 MPa | 0.671 |

**The design stays elastic across the entire range.** The conclusion does not depend on
which value of *n* is chosen — which is exactly why the heat flux was reduced in Section 1.

**Crucially, Fluent does not need this correction.** It solves with temperature-dependent
properties and a wall-resolved boundary layer, so it captures the effect natively. The
correction exists only to set an honest expectation for what CFD *should* produce.

## 4. Energy balance — the strongest check in the project

```
Q = m_dot * c_p * ( T_out - T_in )
```

| Quantity | Value |
|---|---|
| Heat input (imposed) | **603.19 W** |
| Mass flow rate | 8.686 g/s |
| Mean specific heat | 1008.5 J/kg·K |
| Inlet temperature | 300.0 K |
| **Outlet temperature** | **368.85 K** |
| **Temperature rise** | **68.85 K** |
| Q recovered from ṁcₚΔT | 603.19 W |
| **Closure error** | **0.0005 %** |

**Why this matters more than any other check:** the energy balance contains **no heat
transfer coefficient, no turbulence model and no correlation**. Outlet bulk temperature is
fixed by conservation alone.

That gives a clean diagnostic rule for the CFD phase:

- Outlet temperature wrong → **boundary conditions or convergence** are wrong.
- Outlet temperature right but wall temperature wrong → **turbulence model or near-wall
  mesh** is wrong.

Two different failure modes, cleanly separated by one number.

## 5. Axial development

With uniform heat flux, bulk temperature rises **linearly** — a distinctive signature that
is easy to check on a CFD plot:

```
dT_b/dx = q''_i * P_w / ( m_dot * c_p )  =  114.8 K/m
```

| Station | x/D | T_bulk | T_wall,inner | T_wall,outer |
|---|---|---|---|---|
| Inlet | 0 | 300.0 K | 529.6 K | 537.3 K |
| Mid | 15 | 334.5 K | 550.5 K | 558.0 K |
| Exit | 30 | 368.9 K | **574.4 K** | **581.7 K** |

Note that the **wall-to-bulk difference falls** slightly along the duct (229.6 → 205.6 K)
(229.6 -> 216.0 -> 205.6 K) because *h* rises as the air heats. Under strictly constant properties it would be exactly
constant; the variation is a direct signature of the property effect.

## 6. Conduction through the solid wall

Fourier, cylindrical, steady, no generation:

```
T(r) = T(r_i) + ( q' / (2 pi k_s) ) ln( r / r_i )          q' = 1005.3 W/m
```

| Quantity | Value |
|---|---|
| Solid conductivity at wall temperature | 15.22 W/m·K |
| **Conduction resistance R_cond** | **0.01208 K/W** |
| **Convection resistance R_conv** | **0.34082 K/W** |
| **Resistance ratio R_cond/R_conv** | **0.0354** |
| **Through-wall temperature drop** | **7.28 K** |
| Mean radial gradient | 728.5 K/m |

### 🔑 The single most important number in the thermal analysis

> **The metal carries only 3.4 % of the total thermal resistance. The air-side film
> carries 96.6 %.**

Three consequences that shape everything downstream:

1. **The wall is nearly isothermal radially** — 7.3 K across 10 mm of metal. So the
   gradient-driven stress (LC1) is inevitably small, and the LC1 ≪ LC2 result is a
   structural consequence of the *thermal* physics, not an accident of the load case.
2. **Metal temperature is governed by h, not by k_s.** A 20 % error in *h* moves the metal
   temperature by ~41 K; a 20 % error in k_s moves it by ~1.5 K. Turbulence-model error
   propagates strongly into the stress result; solid-property error barely does.
3. **Choosing a higher-conductivity alloy would barely help.** Doubling k_s would remove
   only 3.6 K of a 274 K total rise. If this duct ran too hot, the fix is more airflow, not
   better metal — a genuinely useful design conclusion.

### Assumptions in the conduction model

- **Steady state** — no storage term. Boundary conditions are time-invariant.
- **Radial 1-D** — axial conduction neglected: the axial gradient is **74.7 K/m** against a
  radial **728.5 K/m**, a ratio of **0.10**. Second order, and its effect would be to
  smooth the axial profile slightly.
- **Temperature-dependent k(T)** — not a constant. k rises from 11.5 to 17.1 W/m·K over
  20–400 °C, a 49 % variation that a constant value would misrepresent.

## 7. Values for `EXPECTED_RESULTS.md`

| Quantity | Baseline | Suggested acceptance |
|---|---|---|
| Total heat rate | 603.2 W | ±0.5 % (conservation) |
| Outlet bulk temperature | 368.9 K | ±3 % |
| Fully developed Nu (x/D > 18) | 49.6 corrected · 61.9–66.8 constant-property | accept **44–67** |
| h at exit | 77.8 W/m²·K | accept 70–97 |
| Peak inner wall temperature | 574.4 K | ±5 % |
| Through-wall ΔT | 7.3 K | ±10 % |
