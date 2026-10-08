# Geometry (polygon faceting) correction — Section 6B

**RE-ANALYSIS 2026.** The data are in `faceting_ratios.csv` and `geometry_corrections.csv` in
this folder, both written by `../Scripts/mesh_study.py`.

## Why a correction is needed (F-031)

The three meshes do not represent the same cross-section. Each is an O-grid whose outer ring is
an **inscribed regular N-gon**: N = 32 (coarse), 48 (medium) and 72 (fine). Refining the mesh
therefore also changes the **geometry**. The flow area, the wetted perimeter and the heated outer
area all grow toward the circle's values as N rises. A difference caused by this is not
discretisation error of the solution. It must be separated out before any convergence statement is
made.

## Exact geometric ratios (regular N-gon inscribed in a circle of radius R)

| Quantity | Formula | N = 32 | N = 48 | N = 72 | circle |
|---|---|---|---|---|---|
| Flow area / πR² | (N/2π)·sin(2π/N) | 0.9935869 | 0.9971467 | 0.9987312 | 1 |
| Perimeter / 2πR (= outer heated area ratio, = inner wall area ratio) | sin(π/N)/(π/N) | 0.9983944 | 0.9992862 | 0.9996827 | 1 |
| Hydraulic diameter / D (= apothem / R) | cos(π/N) | 0.9951847 | 0.9978589 | 0.9990482 | 1 |
| Heat input per unit mass flow, (Q/ṁ) / circle | lateral/planar | 1.0048386 | 1.0021457 | 1.0009527 | 1 |

## Which quantities the geometry changes, and how each is treated

| Quantity | Mechanism | Treatment |
|---|---|---|
| **Mass flow ṁ** | uniform 23.5 m/s × polygon area | **exact**: ṁ / planar ratio. After this, the three meshes should agree to round-off |
| **Heat input Q** | 8000 W/m² × polygon outer area | **exact**: Q / lateral ratio = 603.186 W on every mesh. Heat flux per unit heated area is 8000 W/m² by construction, and the mean bore flux is 16 000 W/m², because inner and outer polygons are similar with area ratio ½ |
| **Outlet temperature** | energy conservation: Δh = Q/ṁ, which is raised by lateral/planar | **exact**: T_out,corr = T_out − ΔT_geo, where ΔT_geo = T(h₃₀₀ + Q/ṁ) − T(h₃₀₀ + (Q/ṁ)·planar/lateral), using the solver's own cₚ(T) table |
| **Bulk temperature along the duct** | same, in proportion to the heat absorbed so far | **exact**: at mid-span ΔT_geo,mid = (T_b,300 − 300)(1 − planar/lateral) |
| **Wall and solid temperatures** | T_wall = T_bulk + q″/h + wall ΔT. The bulk part shifts exactly as above; the mean bore flux is unchanged | **exact for the bulk part**: T_max,corr = T_max − ΔT_geo,exit; mid-span wall T − ΔT_geo,mid. The small D_h influence on h is estimated only (below) |
| Reynolds number (D = 20 mm) | G = ṁ/A is unchanged by faceting | none needed; the outlet value moves only through T_out(μ) |
| **Pressure drop** | (1) 1-D acceleration G²(1/ρ_out − 1/ρ_in) rises with T_out; (2) friction ∝ τ_w·P/A = 4τ_w/D_h with τ_w ∝ D_h^−0.2 at fixed G; (3) friction ∝ 1/ρ_mean | (1) **exact** under 1-D ideal gas: G²RΔT_geo/p_op. (2) **estimated** with the Blasius-type exponent: Δp_f·(D_h/D)^−1.2. (3) **estimated**: Δp_f·ΔT_geo,mid/T_mean. The sum is reported as an *estimate*; the geometry-adjusted Δp is shown alongside the raw value, never instead of it |
| Through-wall ΔT | conduction across a polygonal annulus; the thick-wall log law scaled by the apothem gives ΔT ∝ cos(π/N) | **estimated only** (−0.48 / −0.21 / −0.10 % vs circle); not applied |
| h, Nu (D = 20 mm) | h ∝ D_h^−0.2 at fixed G (Dittus–Boelter scaling) | **estimated only** (+0.10 / +0.04 / +0.02 % vs circle); negligible, not applied |
| Friction factor f = 8τ_wρ_b/G² | τ_w ∝ D_h^−0.2 at fixed G | **estimated only** (+0.10 / +0.04 / +0.02 %); negligible, not applied |
| y⁺ | first-layer height is constant; the O-grid spacing pattern changes with N | not a faceting correction; see the y⁺ section of the report |

**Rules followed.**
- A correction is applied to a headline number only if conservation or the exact geometry fixes it.
- Correlation-based scalings are shown as estimates, with their basis. They are used only to judge how much of a raw change *could* be geometric.
- Every raw value stays in the tables and on the plots.

## Results of the corrections (from `geometry_corrections.csv`)

| Mesh | ṁ raw → corrected [g/s] | Q raw → corrected [W] | T_out raw → corrected [K] | ΔT_geo exit / mid-span [K] | T_max raw → bulk-corrected [K] |
|---|---|---|---|---|---|
| coarse (32-gon) | 8.63123 → **8.68694** | 602.217 → **603.186** | 369.115 → **368.783** | 0.332 / 0.168 | 565.40 → 565.07 |
| medium (48-gon) | 8.66216 → **8.68694** | 602.755 → **603.186** | 368.932 → **368.785** | 0.147 / 0.074 | 562.58 → 562.43 |
| fine (72-gon) | 8.67592 → **8.68694** | 602.994 → **603.186** | 368.851 → **368.786** | 0.065 / 0.033 | 560.83 → 560.77 |

| Estimated Δp geometric parts [Pa] | Acceleration (exact, 1-D) | Friction via D_h (estimate) | Friction via mean density (estimate) | Raw Δp → geometry-adjusted |
|---|---|---|---|---|
| coarse | 0.720 | 1.400 | 0.121 | 437.09 → 434.85 |
| medium | 0.319 | 0.625 | 0.054 | 438.13 → 437.13 |
| fine | 0.142 | 0.279 | 0.024 | 439.12 → 438.68 |

**Checks that the corrections are right, not just plausible.**
- ṁ and Q collapse onto one value each (differences ~10⁻¹² %), so the solver applied the inlet
  velocity and the wall flux exactly on each polygon.
- The heat flux averaged over the outer wall is 8000.0000 W/m² and over the bore 16 000.0000 W/m²
  on every mesh. The inner and outer polygons are similar with area ratio exactly ½.
- Richardson extrapolation of the **raw** ṁ, Q and T_out, which converge at the polygon's second
  order (apparent p = 2.18–2.20 with the cell-count ratios), returns 8.68657 g/s, 603.179 W and
  368.790 K. These are within 0.004 %, 0.001 % and 0.004 K of the exact circle values. The
  extrapolation machinery recovers a known answer.

**Share of each raw change that is geometric** (coarse→medium / medium→fine):
- ṁ 100 % / 100 %; Q 100 % / 100 %; T_out 101 % / 101 % (**exact**; status D);
- T_max 7 % / 5 % (exact bulk part only), so T_max changes are resolution;
- through-wall ΔT ≈ 76 % / 56 % (**estimate**), so the ΔT status is capped at B;
- Nu, h, f ≈ −4 % / −3 % of their changes (estimate), which is negligible;
- raw Δp: the estimated geometric part (−1.24 / −0.55 Pa) opposes the raw change (+1.03 / +0.99 Pa).

Outlet Re (D = 20 mm) changes only through μ(T_out); it is classed D with T_out.
