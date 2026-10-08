# FLUID MECHANICS AND PRESSURE-DROP CALCULATIONS — Section 2

**RE-ANALYSIS (2026).** Computed by `baseline_calculations.py`. **No CFD has been run**
— nothing here is tuned to match a simulation.

---

## 1. Geometry and flow rates

| Quantity | Symbol | Value | Units | Equation |
|---|---|---|---|---|
| Cross-sectional flow area | A_c | **314.159** | mm² | π rᵢ² |
| Wetted perimeter | P_w | **62.832** | mm | π Dᵢ |
| Hydraulic diameter | D_h | **20.000** | mm | 4A_c/P_w |
| Volumetric flow rate | Q_v | **7.383** | L/s | V_in A_c |
| Mass flow rate | ṁ | **8.686** | g/s | ρ_in V_in A_c |
| Mass flux | G | **27.650** | kg/m²·s | ṁ/A_c |

**On the hydraulic diameter:** for a circular duct `D_h = 4(πD²/4)/(πD) = D` exactly. The
script asserts `|D_h − Dᵢ| < 10⁻¹²` as a dimensional-consistency check — it returned
3 × 10⁻¹⁸ m. Trivial here, but it would catch a units error immediately in a
non-circular duct.

**On the mass flux:** ṁ and G are constant along the duct while ρ and V are not. G is
therefore the natural variable for a heated duct, and is what the marching solution uses.

## 2. Velocity, Reynolds and Mach

| Station | ρ (kg/m³) | V (m/s) | Re | Ma |
|---|---|---|---|---|
| Inlet (300.0 K) | 1.1766 | **23.50** | **29 957** | 0.0677 |
| Outlet (368.9 K) | 0.9569 | **28.89** | **25 548** | 0.0750 |

**The flow accelerates by 23 % without any area change.** Density falls as the gas heats,
and with ṁ fixed, V = G/ρ must rise. This is real physics, it contributes 149 Pa of
pressure change, and CFD must reproduce it.

**Reynolds number falls** from 29 957 to 25 548 because viscosity rises faster with
temperature than density falls. Worth stating explicitly: quoting "Re = 30 000" for the
whole duct would be wrong by 15 %.

## 3. Flow regime — and why the Section 1 turbulence model is right

| Threshold | Value | This flow |
|---|---|---|
| Laminar | Re < 2300 | no |
| Transitional | 2300 < Re < 4000 | no |
| **Turbulent** | Re > 4000 | **yes, Re ≥ 25 548 everywhere** |

**The flow is fully turbulent over the entire duct**, with a 6× margin above the
transition threshold at its weakest point. A single turbulent treatment is valid end to
end — no laminar-transitional blending is needed.

### Why k-ω SST, wall-resolved at y⁺ ≤ 1

1. **The physics demands near-wall resolution.** The resistance analysis shows the air-side
   film carries **96.6 %** of the total thermal resistance. Wall heat flux sets metal
   temperature, which sets every stress in the project. A wall function would *model*
   exactly the quantity the project is trying to compute.
2. **SST integrates to the wall.** k-ω behaviour near the wall, k-ε in the free stream,
   without the wall-function assumption of a universal log-law temperature profile — an
   assumption that is least reliable when properties vary strongly, which is precisely this
   case (wall-to-bulk ΔT = 206 K).
3. **The mesh cost is affordable.** First cell 12.2 µm, 18 inflation layers, ≈ 168 000
   cells total — comfortable on 4 cores and 15.7 GB.
4. **Nothing more elaborate is justified.** There is no separation, no adverse pressure
   gradient, no swirl and no curvature. A Reynolds-stress model or LES would add cost and
   uncertainty without addressing any mechanism present in this geometry.
5. **It is the solver default**, confirmed on this machine during Section 1 licence
   verification — so it is also the least surprising choice for a reviewer.

## 4. Pressure drop

**Friction factor — Petukhov**, `f = (0.790 ln Re − 1.64)⁻²`, valid 3 × 10³ < Re < 5 × 10⁶.
Our Re range sits comfortably inside. Mean value along the duct: **f = 0.02413**.

Dynamic pressure: **324.9 Pa** at inlet, **399.5 Pa** at outlet.

### Breakdown

| Component | Equation | Value (Pa) | In the CFD domain? |
|---|---|---|---|
| **Major — wall friction** | f(L/D_h)·½ρV² | **263.2** | ✅ yes |
| **Thermal acceleration** | G²(1/ρ_out − 1/ρ_in) | **149.1** | ✅ yes |
| Entry-region increment | K(∞)·½ρV², K(∞)=0.09 | **29.2** | ✅ yes |
| **TOTAL — compare against Fluent** | | **441.5** | |
| Minor — sharp entrance | K=0.5 | 162.4 | ❌ **no** |
| Minor — sudden exit | K=1.0 | 399.5 | ❌ **no** |
| **TOTAL — real installation** | | **1003.4** | |

### ⚠ The minor losses must not be compared against CFD

The CFD domain begins at a **velocity inlet on the duct entrance plane** — there is no
upstream plenum and no contraction, so no entrance loss exists. It ends at a **pressure
outlet on the exit plane** — there is no downstream sudden expansion, so no exit loss
exists. Both are computed because a *real installation* would incur them, and because a
reviewer should see that they are the dominant term in a real system.

**A flagged observation:** the installation minor losses (562 Pa) **exceed** the friction
loss (263 Pa) by more than a factor of two. For a duct only 30 diameters long that is
entirely expected — but it means quoting "the pressure drop" without saying which boundary
is meant would be misleading by a factor of 2.3.

**No bends, fittings, valves or area changes exist** in this straight constant-area duct,
so no further minor losses apply.

### Consistency checks

- Δp_CFD / p_op = **0.44 %** → pressure has no meaningful effect on density, confirming
  the incompressible-ideal-gas model.
- Δp per unit length = **736 Pa/m** — an ordinary figure for a 20 mm air duct at ~25 m/s.

## 5. Entry length

```
L_h / D = 1.359 Re^0.25  ->  L_h = 358 mm  (x/D = 17.9)
```

The duct is 600 mm, so roughly the **first 18 diameters are developing** and the last **12
are effectively fully developed**. Two consequences:

- Fully developed Nusselt and friction factor must be extracted at **x/D > 18**, not
  averaged over the whole duct.
- Elevated Nusselt in the entry region is **expected physics**, not a CFD error. Its decay
  toward the fully developed value is itself a validation that the near-wall mesh is
  behaving.

## 6. Values for `EXPECTED_RESULTS.md`

| Quantity | Baseline | Suggested acceptance |
|---|---|---|
| Re (inlet / outlet) | 29 957 / 25 548 | ±2 % |
| Friction factor | 0.0241 | ±10 % |
| Δp (CFD-comparable) | 441.5 Pa | ±15 % |
| Outlet velocity | 28.89 m/s | ±5 % |
| Entry length | x/D ≈ 18 | qualitative |
