# Numerical Uncertainty and Downstream Impact — Section 6B

**RE-ANALYSIS 2026.** Numbers: `gci_analysis.csv`, `downstream_impact.csv` (this folder), written by
`../Scripts/mesh_study.py`.

## 1. Method

- **Grid convergence:** Celik et al. (2008), *Procedure for Estimation and Reporting of
  Uncertainty Due to Discretization in CFD Applications*, ASME J. Fluids Eng. 130, 078001.
- **Refinement ratios** from total cell counts: r₂₁ = 1.4631 (fine/medium), r₃₂ = 1.4555 (medium/coarse).
- **Apparent order p:** fixed-point iteration of the Celik equation with the unequal ratios.
- **Richardson extrapolation:** only when the convergence is monotonic (0 < R < 1) **and**
  0.5 ≤ p ≤ 4.
- **GCI:** Fs = 1.25 with p capped at 2. Where p is not credible, the Fs = 3, p = 2 fallback is
  used, and the value is labelled as such.
- **Absolute temperatures** are analysed as their rise above the 300 K inlet (φ − 300). The GCI is
  quoted in kelvin and as % of the rise, never as % of the absolute temperature.
- **Geometric (faceting) changes** are not treated as discretisation uncertainty; no GCI is quoted
  for ṁ, Q or T_out (see `../Geometry_Correction/GEOMETRY_CORRECTION.md`).

## 2. Numerical uncertainty of the CFD quantities

| Quantity | Fine value | GCI fine | Medium value | GCI medium | Extrapolated |
|---|---|---|---|---|---|
| Peak solid temperature | 560.83 K | ±3.4 K (1.3 % of rise) | 562.58 K | ±5.6 K (2.1 %) | 558.1 K |
| Peak solid temperature, bulk-corrected | 560.77 K | ±3.4 K | 562.43 K | ±5.5 K | 558.1 K |
| Peak inner-wall temperature | 553.50 K | ±3.4 K | 555.27 K | ±5.6 K | 550.8 K |
| Volume-mean solid temperature | 524.18 K | ±2.3 K | 525.48 K | ±3.9 K | 522.3 K |
| Through-wall ΔT, mid-span | 7.597 K | ±0.029 K (0.39 %) | 7.581 K | ±0.049 K (0.65 %) | 7.620 K |
| Through-wall ΔT, z = 570 mm | 7.378 K | ±0.037 K (0.51 %) | 7.361 K | ±0.058 K (0.79 %) | 7.407 K |
| Nu_fd (x/D 18–29) | 54.66 | ±1.8 % | 54.17 | ±2.9 % | 55.43 |
| f_fd (x/D 18–29) | 0.02181 | ±1.8 % | 0.02163 | ±2.8 % | 0.02212 |
| Δp, geometry-adjusted (estimate) | 438.68 Pa | ±3.9 Pa (0.89 %) | 437.13 Pa | ±5.9 Pa (1.34 %) | 441.8 Pa |
| Δp, raw (p not credible; Fs = 3 fallback) | 439.12 Pa | ±2.6 Pa (0.60 %) | 438.13 Pa | ±2.8 Pa (0.63 %) | — |
| T_out, geometry-corrected | 368.786 K | ±0.002 K | 368.785 K | ±0.003 K | 368.787 K |

The GCI is an uncertainty band (≈ 95 % in Roache's sense), not a guaranteed bound. Its limits
are listed in the report, §6.4. The main one: the first-layer height was not refined, so any error
tied to it is not captured.

**Useful reading of the table:**
- the medium mesh's error relative to the extrapolated value is **+4.4 K** on the peak temperature,
  **+3.1 K** on the volume mean and **−0.040 K** on the through-wall ΔT;
- all of these lie inside the medium GCI band.

## 3. Downstream (structural) impact of using the medium mesh

Closed-form sensitivities (frozen Section 2 values): E = 188.1 GPa, α = 13.72 × 10⁻⁶ /K, L = 600 mm.
- Restrained axial stress, LC2: σ = −E·α·ΔT → **2.58 MPa per K** of local temperature.
- Free axial growth: α·L·ΔT_mean → **8.23 µm per K** of mean solid temperature.
- Through-wall-gradient stress, LC1: proportional to the through-wall ΔT (16.31 MPa at 7.28 K in Section 2).

| Effect | Medium − extrapolated | Structural consequence | Direction |
|---|---|---|---|
| Peak solid temperature | +4.44 K (+4.52 K against the circle-corrected extrapolation) | **+11.5 MPa** on the 657 MPa LC2 axial stress (**+1.7 %**) | conservative |
| Volume-mean solid temperature | +3.15 K | **+0.026 mm** of free axial growth (+1.4 % of the CFD mean rise of 225.5 K) | conservative |
| Through-wall ΔT (mid-span) | −0.040 K (−0.52 %) | **−0.09 MPa** on the 16.3 MPa LC1 stress (−0.5 %) | slightly non-conservative, negligible |
| Heat input (polygon vs circle) | −0.07 % | bulk temperature −0.15 K at exit | negligible |

**For scale.** The CFD-vs-Section 2 peak-temperature difference (−19.1 K on the medium mesh) is a
**modelling** difference worth ≈ 49 MPa (7.5 %) on LC2. That is 4× the mesh effect. The film
coefficient, not the mesh, is the uncertainty to carry forward (F-006, F-010).

## 4. Recommended uncertainty statement for Section 7

The fine-mesh GCI band brackets the value on this refinement path. Expressed relative to the
**medium** value that Section 7 will use:

| Quantity | Medium | Band from the fine-mesh GCI | Relative to medium | Best estimate relative to medium |
|---|---|---|---|---|
| Peak solid temperature | 562.58 K | 557.5 – 564.2 K | −5.1 / +1.6 K | −4.4 K |
| Volume-mean solid temperature | 525.48 K | 521.9 – 526.5 K | −3.6 / +1.0 K | −3.1 K |
| Through-wall ΔT, mid-span | 7.581 K | 7.567 – 7.626 K | −0.013 / +0.045 K | +0.040 K |

> The medium-mesh CFD temperature field used for the structural analysis carries a numerical (mesh)
> uncertainty of **−5.1 / +1.6 K on the peak solid temperature** (best estimate 4.4 K below the
> medium value), **−3.6 / +1.0 K on the volume-mean solid temperature**, and **−0.01 / +0.05 K on
> the through-wall ΔT**. In structural terms that is at most ≈ 2 % on restrained thermal stress,
> < 1 % on the through-wall-gradient stress and ≈ 0.03 mm on free axial growth. It is small next to
> the heat-transfer model uncertainty.

Every refinement lowered the solid temperatures, so the medium field is expected to be slightly
conservative for stress and growth. The positive side of each band covers the chance that the
Richardson estimate overshoots.
