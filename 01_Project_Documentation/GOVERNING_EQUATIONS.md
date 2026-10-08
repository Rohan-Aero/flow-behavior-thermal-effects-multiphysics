# GOVERNING EQUATIONS — Section 2

**RE-ANALYSIS (2026).** Every equation below is standard published theory. What is
re-analysed is the *choice* of which to apply and the parameters fed into them.

---

## 1. Conservation equations (what Fluent actually solves)

Steady, RANS-averaged, variable-density.

**Continuity**

```
d/dx_i (rho u_i) = 0
```

**Momentum** (Reynolds-averaged Navier–Stokes)

```
d/dx_j (rho u_i u_j) = -dp/dx_i + d/dx_j [ mu (du_i/dx_j + du_j/dx_i - (2/3) d_ij du_k/dx_k) ]
                       + d/dx_j ( -rho <u'_i u'_j> )
```

The final term is the Reynolds stress tensor — the closure problem. Gravity is omitted
because Gr/Re² = 4.4 × 10⁻⁵.

**Energy** (fluid)

```
d/dx_i ( u_i (rho E + p) ) = d/dx_i ( k_eff dT/dx_i )     k_eff = k + k_turbulent
```

The viscous-dissipation term is dropped: Br = 1.8 × 10⁻³.

**Energy** (solid — the conjugate domain)

```
d/dx_i ( k_s dT/dx_i ) = 0
```

Steady, no generation. Coupling to the fluid is through continuity of temperature and heat
flux at the shared interface — **that is what makes this a conjugate problem**: wall
temperature is solved, never imposed.

**Turbulence closure — k-ω SST** (Menter, 1994)

```
d/dx_i (rho k u_i)     = d/dx_j ( Gamma_k  dk/dx_j )     + G_k     - Y_k
d/dx_i (rho omega u_i) = d/dx_j ( Gamma_w  domega/dx_j ) + G_omega - Y_omega + D_omega
```

Chosen because it integrates to the wall without wall functions. In conjugate heat
transfer, wall heat flux sets the solid temperature which sets the stress — so a wall
function would *model* the quantity of interest instead of resolving it.

**Equation of state — incompressible ideal gas**

```
rho = p_op / (R T)          R = 287.058 J/kg.K,  p_op = 101 325 Pa
```

Density varies with temperature but **not** with local pressure. Justified because
Δp/p_op = 0.44 %.

---

## 2. Fluid mechanics

| Quantity | Equation | Note |
|---|---|---|
| Flow area | `A_c = pi * r_i^2` | |
| Wetted perimeter | `P_w = pi * D_i` | full circumference is wetted |
| Hydraulic diameter | `D_h = 4 A_c / P_w = D_i` | **exact identity for a circular duct** |
| Volumetric flow | `Q_v = V A_c` | |
| Mass flow | `m_dot = rho V A_c` | constant along the duct |
| Mass flux | `G = m_dot / A_c` | constant even as ρ falls — the useful invariant |
| Reynolds | `Re = rho V D_h / mu = G D_h / mu` | |
| Mach | `Ma = V / sqrt(gamma R T)` | |

**Flow regime thresholds (circular duct):** laminar Re < 2300 · transitional 2300–4000 ·
turbulent Re > 4000.

---

## 3. Pressure drop

**Darcy–Weisbach (major loss)**

```
dp_friction = f (L / D_h) (1/2) rho V^2
```

**Petukhov friction factor** (smooth tube)

```
f = ( 0.790 ln(Re) - 1.64 )^-2          valid 3e3 < Re < 5e6
```

**Thermal acceleration** — momentum change from heating, *not* a loss:

```
dp_acceleration = G^2 ( 1/rho_out - 1/rho_in )
```

**Entry-region increment** — the developing profile costs more than fully developed flow:

```
dp_entry = K(inf) (1/2) rho V^2          K(inf) ~ 0.09 turbulent  (Kays & London)
```

**Minor losses** — `dp = K (1/2) rho V^2`, with K = 0.5 sharp entrance, K = 1.0 sudden exit.

> ⚠ **These two are NOT part of the CFD domain.** The CFD inlet is a velocity inlet at the
> duct entrance (no upstream plenum, no contraction) and the outlet is a pressure outlet at
> the exit plane (no sudden expansion). They are computed for a *real installation* and
> must never be compared against Fluent. **No bends, fittings or area changes exist** in
> this straight constant-area duct, so no further minor losses apply.

**Turbulent hydrodynamic entry length**

```
L_h / D = 1.359 Re^0.25
```

---

## 4. Heat transfer

**Newton's law of cooling** — the definition of *h*:

```
q'' = h ( T_wall - T_bulk )
```

**Nusselt number** — dimensionless wall gradient:

```
Nu = h D_h / k_fluid
```

**Dittus–Boelter (1930)**, heating:

```
Nu = 0.023 Re^0.8 Pr^0.4
```
*Validity:* Re > 10⁴ · 0.6 < Pr < 160 · L/D > 10 · **small wall-to-bulk ΔT**.

**Gnielinski (1976)** — primary correlation here:

```
Nu = ( (f/8)(Re - 1000) Pr ) / ( 1 + 12.7 sqrt(f/8) ( Pr^(2/3) - 1 ) )
```
*Validity:* 3 × 10³ < Re < 5 × 10⁶ · 0.5 < Pr < 2000. Preferred because it carries the
friction factor explicitly and is more accurate at Re ≈ 2–3 × 10⁴, where Dittus–Boelter —
a power law fitted at higher Re — over-predicts.

**Property-variation correction** (Kays & Crawford, turbulent gas, heating):

```
Nu = Nu_constant-property * ( T_b / T_w )^n          n ~ 0.5   (literature 0.4 - 0.575)
```

> ⚠ **Both correlations above are constant-property.** For gases their usual validity is a
> wall-to-bulk difference of order 60 K. Here it reaches **206 K**. This correction is
> therefore mandatory, and is solved iteratively because T_w depends on h which depends on
> T_w. See `MATERIAL_PROPERTIES.md` and `EXPECTED_RESULTS.md`.

**Energy balance** — the strongest check available:

```
Q = m_dot c_p ( T_out - T_in )
```

**Bulk temperature march** at constant imposed flux:

```
dT_b/dx = q''_i P_w / ( m_dot c_p )      ->  T_b rises LINEARLY
```

**Area-ratio identity** (a dimensional-consistency check):

```
q''_i = q''_o * ( D_o / D_i )            same Q through a smaller area
```

---

## 5. Conduction in the solid

**Fourier's law, cylindrical, steady, no generation:**

```
q' = -k_s (2 pi r) dT/dr        ->      T(r) = T(r_i) + ( q' / (2 pi k_s) ) ln( r / r_i )
```

Temperature rises **logarithmically** with radius; the outer surface is the hot side.

**Through-wall temperature drop**

```
dT_wall = ( q' / (2 pi k_s) ) ln( r_o / r_i )
```

**Thermal resistances (per unit length of duct, here for the full length L):**

```
R_conduction = ln(r_o / r_i) / ( 2 pi k_s L )
R_convection = 1 / ( h A_i )
```

Their ratio is the single most diagnostic number in the thermal problem: **R_cond/R_conv =
0.035**, so the metal is 3.4 % of the resistance and the air film is 96.6 %.

---

## 6. Thermal expansion and stress

**Thermal strain (free):**

```
eps_thermal = alpha ( T - T_ref )
```

**Hooke's law with thermal strain (3-D):**

```
eps_ij = (1/E) [ (1 + nu) sigma_ij - nu sigma_kk d_ij ] + alpha (T - T_ref) d_ij
```

**Stress appears only where thermal strain is PREVENTED** — by external restraint, or by
neighbouring material at a different temperature. Free expansion at uniform temperature
produces displacement and **zero** stress.

**LC2 — fully restrained bar (approximate):**

```
sigma_z = -E alpha ( T_mean - T_ref )
```
Valid form for LC2 because axial restraint is total; approximate because it uses a single
volume-mean temperature for a non-uniform field. **Not applicable to LC1 at all.**

**LC1 — Timoshenko & Goodier thick-walled cylinder**, logarithmic temperature, free ends,
plane strain, with `Ta = T_i - T_o`, `C = alpha E Ta / (2(1-nu) ln(b/a))`:

```
sigma_r     = C [ -ln(b/r) - (a^2/(b^2-a^2))(1 - b^2/r^2) ln(b/a) ]
sigma_theta = C [ 1 - ln(b/r) - (a^2/(b^2-a^2))(1 + b^2/r^2) ln(b/a) ]
sigma_z     = C [ 1 - 2 ln(b/r) - 2 (a^2/(b^2-a^2)) ln(b/a) ]
```

**von Mises:**

```
sigma_vM = sqrt( 0.5 [ (sr-st)^2 + (st-sz)^2 + (sz-sr)^2 ] )
```

**Margin of safety** against hot yield (yield at operating temperature, never room
temperature):

```
MoS = S_y(T) / |sigma| - 1
```

---

## 7. Dimensionless groups and what each one decides

| Group | Definition | Decides |
|---|---|---|
| Reynolds | `rho V D / mu` | laminar vs turbulent → which correlation applies |
| Prandtl | `mu c_p / k` | relative thickness of velocity and thermal boundary layers |
| Nusselt | `h D / k` | how much convection beats pure conduction (Nu = 1 would be conduction only) |
| Mach | `V / a` | whether density responds to pressure |
| Grashof | `g beta dT D^3 / nu^2` | strength of buoyancy |
| Richardson | `Gr / Re^2` | **whether buoyancy matters at all** (< 0.1 → no) |
| Eckert | `V^2 / (c_p dT)` | kinetic energy vs thermal energy |
| Brinkman | `Ec * Pr` | **whether viscous heating matters** (≪ 1 → no) |
| Péclet | `Re * Pr` | advection vs conduction in the fluid |
| Resistance ratio | `R_cond / R_conv` | **whether the metal or the film controls temperature** |
