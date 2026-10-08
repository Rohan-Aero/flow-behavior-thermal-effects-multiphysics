# Parametric trends — Section 9B-2 (Parts O, P, Q, W)

> **RE-ANALYSIS 2026.** Every number in this document is a newly generated ANSYS 2026 R1 Student result of this re-analysis (Fluent CFD of Section 9B-1, Mechanical of Section 9B-2), computed from the solver's own output tables. Nothing is a recovered internship value, and no experimental or measured data exist or are implied.

One-factor-at-a-time study around P00. Every value comes from the solved CFD (9B-1) and Mechanical (9B-2) cases; the 9A screening appears only as a comparison (§5). Percentages are changes from P00 **within one family**. Families are not compared with each other, except through the normalised sensitivity S = (Δy/y₀)/(Δx/x₀), which removes the different step sizes. Data: `Data/trends_9B2.json`. Figures: `Figures/F01…F15`.

## Velocity (V01 21.15 · P00 23.5 · V03 25.85 m/s; ±10 %)

| Quantity | V01 | P00 | V03 | Change V01 | Change V03 | Normalised sensitivity (dy/y)/(dx/x) | Mid-point deviation from linear |
|---|---|---|---|---|---|---|---|
| Pressure drop Δp [Pa] | 379.93 | 438.13 | 499.69 | -13.28 % | +14.05 % | +1.367 | -0.384 % |
| Outlet bulk T [K] | 376.56 | 368.93 | 362.69 | +2.07 % | -1.69 % | -0.188 | -0.187 % |
| Max solid T [K] | 587.47 | 562.58 | 542.10 | +4.42 % | -3.64 % | -0.403 | -0.392 % |
| Solid mean T [K] | 546.96 | 525.48 | 507.78 | +4.09 % | -3.37 % | -0.373 | -0.360 % |
| LC1 axial growth [mm] | 2.0339 | 1.8409 | 1.6842 | +10.49 % | -8.51 % | -0.950 | -0.987 % |
| LC2 max VM [MPa] | 663.00 | 605.16 | 557.54 | +9.56 % | -7.87 % | -0.871 | -0.845 % |
| LC2 mean axial stress [MPa] | -639.05 | -582.44 | -535.85 | -9.72 % | +8.00 % | -0.886 | +0.861 % |
| LC2 end reaction [kN] | 602.29 | 548.94 | 505.03 | +9.72 % | -8.00 % | -0.886 | -0.861 % |
| LC2 utilisation [-] | 0.63472 | 0.57798 | 0.53146 | +9.82 % | -8.05 % | -0.893 | -0.885 % |
| λ₁ [-] | 1.00307 | 1.10805 | 1.21087 | -9.47 % | +9.28 % | +0.938 | +0.097 % |
| P_cr [kN] | 604.14 | 608.25 | 611.53 | -0.67 % | +0.54 % | +0.061 | +0.068 % |

## Heat flux (Q01 7,200 · P00 8,000 · Q03 8,800 W/m²; ±10 %)

| Quantity | Q01 | P00 | Q03 | Change Q01 | Change Q03 | Normalised sensitivity (dy/y)/(dx/x) | Mid-point deviation from linear |
|---|---|---|---|---|---|---|---|
| Pressure drop Δp [Pa] | 419.74 | 438.13 | 456.64 | -4.20 % | +4.22 % | +0.421 | -0.014 % |
| Outlet bulk T [K] | 362.06 | 368.93 | 375.79 | -1.86 % | +1.86 % | +0.186 | +0.001 % |
| Max solid T [K] | 534.45 | 562.58 | 591.13 | -5.00 % | +5.07 % | +0.504 | -0.037 % |
| Solid mean T [K] | 501.07 | 525.48 | 550.31 | -4.65 % | +4.72 % | +0.469 | -0.039 % |
| LC1 axial growth [mm] | 1.6253 | 1.8409 | 2.0641 | -11.71 % | +12.13 % | +1.192 | -0.211 % |
| LC2 max VM [MPa] | 538.53 | 605.16 | 673.02 | -11.01 % | +11.21 % | +1.111 | -0.101 % |
| LC2 mean axial stress [MPa] | -518.23 | -582.44 | -647.83 | +11.02 % | -11.23 % | +1.113 | +0.101 % |
| LC2 end reaction [kN] | 488.42 | 548.94 | 610.57 | -11.02 % | +11.23 % | +1.113 | -0.101 % |
| LC2 utilisation [-] | 0.51290 | 0.57798 | 0.64461 | -11.26 % | +11.53 % | +1.139 | -0.135 % |
| λ₁ [-] | 1.25464 | 1.10805 | 0.98834 | +13.23 % | -10.80 % | -1.202 | -1.214 % |
| P_cr [kN] | 612.79 | 608.25 | 603.45 | +0.75 % | -0.79 % | -0.077 | +0.021 % |

## Wall thickness (T01 8 · P00 10 · T03 12 mm; Do 36 / 40 / 44 mm; ±20 %; total heat input Q held constant)

| Quantity | T01 | P00 | T03 | Change T01 | Change T03 | Normalised sensitivity (dy/y)/(dx/x) | Mid-point deviation from linear |
|---|---|---|---|---|---|---|---|
| Max solid T [K] | 561.97 | 562.58 | 563.07 | -0.11 % | +0.09 % | +0.005 | +0.010 % |
| Solid mean T [K] | 524.54 | 525.48 | 526.38 | -0.18 % | +0.17 % | +0.009 | +0.004 % |
| LC1 max deformation [mm] | 1.8355 | 1.8443 | 1.8528 | -0.48 % | +0.46 % | +0.023 | +0.007 % |
| LC1 axial growth [mm] | 1.8328 | 1.8409 | 1.8487 | -0.44 % | +0.42 % | +0.022 | +0.007 % |
| LC1 max VM [MPa] | 20.87 | 24.28 | 27.21 | -14.05 % | +12.04 % | +0.652 | +1.001 % |
| LC2 max VM [MPa] | 602.31 | 605.16 | 607.74 | -0.47 % | +0.43 % | +0.022 | +0.023 % |
| LC2 mean axial stress [MPa] | -580.05 | -582.44 | -584.75 | +0.41 % | -0.40 % | +0.020 | -0.007 % |
| LC2 max deformation [mm] | 0.1317 | 0.1349 | 0.1385 | -2.36 % | +2.65 % | +0.125 | -0.142 % |
| LC2 end reaction [kN] | 408.19 | 548.94 | 705.43 | -25.64 % | +28.51 % | +1.354 | -1.434 % |
| LC2 utilisation [-] | 0.57432 | 0.57798 | 0.58125 | -0.63 % | +0.57 % | +0.030 | +0.033 % |
| λ₁ [-] | 0.94497 | 1.10805 | 1.28702 | -14.72 % | +16.15 % | +0.772 | -0.717 % |
| P_cr [kN] | 385.73 | 608.25 | 907.89 | -36.58 % | +49.26 % | +2.146 | -6.340 % |

## 4. What the trends mean

**Velocity.** Lower velocity means less cooling capacity at the same heat input. V01 (−10 %) raises the outlet temperature by +7.62 K, the maximum solid temperature by +24.89 K and the solid mean by +21.48 K. The restrained thermal force follows the mean temperature (end reaction +9.72 %), so λ₁ falls by 9.47 % to 1.0031. V03 (+10 %) does the opposite (λ₁ 1.2109, +9.28 %). Δp changes by -13.3 % / +14.1 %, a local exponent Δp ∝ V^1.37. This is below the 1.75–2 of isothermal turbulent duct flow; part of the static pressure drop accelerates the heated air, and that part grows when the air heats more (lower V). The split was not isolated in 9B-1. The LC2 peak von Mises changes slightly less than the mean axial stress (+9.56 % / -7.87 % against +9.72 % / -8.00 % in magnitude): the peak adds a local inlet-end part to the uniform axial stress, and the wall temperature at the critical node changes less than the duct mean (V01: +12.40 K against +21.48 K).

**Heat flux.** q″ is the load itself. ±10 % moves the solid mean by -24.41 / +24.82 K; the solid-mean rise above the 300 K inlet changes by -10.8 / +11.0 %, slightly more than proportionally (the cause was not isolated). The restrained force follows (end reaction -11.02 / +11.23 %). λ₁ goes to 1.2546 (Q01) and 0.9883 (Q03). Q03 sits below the linear stability limit, and it is the case of largest LC2 stress (673.02 MPa) and utilisation (0.6446). Δp changes only through the air temperature (density, viscosity, acceleration of the heated air) (-4.2 / +4.2 %).

**Wall thickness (Q held).** Temperatures move by less than 1 K (-0.94 / +0.90 K on the solid mean). The thermal *stress* level therefore barely changes (LC2 max VM -0.47 / +0.43 %), and the growth is almost the same. What changes is the section: the end force scales with the area A (-25.6 / +28.5 %), while the Euler load scales with the bending stiffness EI (P_cr -36.6 / +49.3 %). Because λ₁ ∝ I/(A·ε_th) ∝ r_g², the thin wall **loses** stability margin (λ₁ 0.9450) and the thick wall **gains** it (λ₁ 1.2870). Thickness is the one variable of the three that changes λ₁ through the section rather than through the temperatures; its normalised effect on λ₁ (S = +0.772) is of the same order as those of V (+0.938) and q″ (-1.202). The LC1 peak stress changes by -14.0 / +12.0 % with the through-wall temperature difference (mid-span ΔT 6.44 / 7.58 / 8.61 K for 8 / 10 / 12 mm).

**Most sensitive quantity per parameter** (largest |S| among the listed quantities):

| Parameter | Most sensitive quantity | S | Next |
|---|---|---|---|
| V | Pressure drop Δp [Pa] | +1.367 | LC1 axial growth [mm] (-0.950), λ₁ [-] (+0.938) |
| Q | λ₁ [-] | -1.202 | LC1 axial growth [mm] (+1.192), LC2 utilisation [-] (+1.139) |
| T | P_cr [kN] | +2.146 | LC2 end reaction [kN] (+1.354), λ₁ [-] (+0.772) |

For V and q″ every structural response follows the change of the wall temperature (growth, restrained force, stresses, utilisation and λ₁ all with |S| = 0.87–1.20). For t the temperatures are almost insensitive (|S| ≤ 0.009) and the section-driven quantities (P_cr, end reaction, λ₁) dominate.

## 5. Against the 9A screening (comparison only)

| Case | λ₁ screened (9A) | λ₁ FE (9B-2) | Difference | LC2 max VM screened [MPa] | FE [MPa] | Utilisation screened | FE | LC1 ΔL screened [mm] | FE [mm] |
|---|---|---|---|---|---|---|---|---|---|
| P00 | 1.1080 | 1.1080 | +0.00 % | 605.16 | 605.16 | 0.5780 | 0.5780 | 1.8409 | 1.8409 |
| V01 | 0.9978 | 1.0031 | +0.52 % | 667.19 | 663.00 | 0.6389 | 0.6347 | 2.0442 | 2.0339 |
| V03 | 1.2165 | 1.2109 | -0.46 % | 554.44 | 557.54 | 0.5284 | 0.5315 | 1.6767 | 1.6842 |
| Q01 | 1.2645 | 1.2546 | -0.78 % | 534.63 | 538.53 | 0.5091 | 0.5129 | 1.6132 | 1.6253 |
| Q03 | 0.9810 | 0.9883 | +0.75 % | 677.80 | 673.02 | 0.6494 | 0.6446 | 2.0792 | 2.0641 |
| T01 | 0.9419 | 0.9450 | +0.32 % | 603.78 | 602.31 | 0.5766 | 0.5743 | 1.8364 | 1.8328 |
| T03 | 1.2914 | 1.2870 | -0.34 % | 606.41 | 607.74 | 0.5792 | 0.5813 | 1.8449 | 1.8487 |

The screening was anchored to P00 and scaled 1-D. It flagged λ₁ < 1 for V01, Q03, T01; the FE results give λ₁ < 1 for Q03, T01; V01 lies just above 1 in the FE result (λ₁ 1.0031), within 0.31 % of the limit, so its classification is sensitive to the modelling uncertainties of `FINAL_PARAMETRIC_AUDIT.md` §3. The λ₁ differences (≤ 0.78 %) are attributed in 9B-1 (F-050) to developing flow and axial wall conduction, which the solved fields contain and the screening did not.

## 6. Interaction limitation (Part W)

- This is a **one-factor-at-a-time** study. It does not identify variable interactions. 9A estimated the V × q″ interaction at about 8–11 % of the main effects, so combined off-baseline states (for example low V *and* high q″) cannot be obtained by adding the one-factor changes.
- The mid-point deviation from linearity is listed for each quantity. It shows the local curvature *along one axis only*.
- **No response surface is fitted, and nothing is extrapolated beyond the ±10 % (V, q″) and ±20 % (t) steps.**

## 7. Figures (Part Q; baseline marked in every plot)

- `Figures/F01_V_vs_pressure_drop.png`
- `Figures/F02_V_vs_outlet_temperature.png`
- `Figures/F03_V_vs_max_solid_temperature.png`
- `Figures/F04_V_vs_LC2_stress.png`
- `Figures/F05_V_vs_lambda1.png`
- `Figures/F06_q_vs_outlet_temperature.png`
- `Figures/F07_q_vs_max_solid_temperature.png`
- `Figures/F08_q_vs_LC2_stress.png`
- `Figures/F09_q_vs_lambda1.png`
- `Figures/F10_t_vs_max_deformation.png`
- `Figures/F11_t_vs_LC2_stress.png`
- `Figures/F12_t_vs_lambda1.png`
- `Figures/F13_t_vs_critical_buckling_load.png`
- `Figures/F14_support_vs_lambda1.png`
- `Figures/F15_support_vs_LC2_stress.png`
