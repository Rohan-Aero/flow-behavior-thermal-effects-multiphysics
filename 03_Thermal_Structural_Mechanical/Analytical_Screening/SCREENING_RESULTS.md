# Section 9A: analytical screening of the parametric cases

> **SCREENING ONLY.** These are neither CFD nor Mechanical results. They come from the frozen Section 2 1-D model (`parametric_screening.py`).
>
> - **Analytical** columns are the raw 1-D model.
> - **Anchored** columns apply the analytical *change* to the solved P00 baseline (CFD 5B, FE 7B/8A):
>   - for temperatures, the rise above 300 K is scaled;
>   - for stresses, the solver thermal strain × E(T) at the anchored mean temperature is scaled;
>   - for λ₁, (E·I) / N is scaled.
> - The purpose is to reject ranges that would leave the valid model before any expensive run.

**Self-check.** The script reproduces the frozen Section 2 baseline: Re_in 2.996e+04 (Section 2: 29957), dp_CFD_comparable 441.5 (Section 2: 441.5), T_out 368.9 (Section 2: 368.85), Q 603.2 (Section 2: 603.19), h_exit 77.83 (Section 2: 77.83), Twi_exit 574.4 (Section 2: 574.43), dT_wall_exit 7.285 (Section 2: 7.28), T_mean_solid 554.7 (Section 2: 554.7). Result: **PASS**.

**Validity limits applied.**

- Air property table 250–600 K. **INVALID** above 600 K; **MARGINAL** within 10 K of it.
- Inconel E, k, c_p and S_y tables 293–673 K. **INVALID** above 673 K.
- Re_min ≥ 10,000 for fully turbulent flow.
- Δp ≤ 1 % of p_op, the basis of the incompressible-ideal-gas model.
- Mach ≤ 0.3.
- y⁺_max ≤ 1 with the baseline first cell.
- Thermal strain ≤ 0.5 % and flow-area change ≤ 1 %, the basis of one-way coupling.
- LC2 utilisation < 1.
- λ₁(S1) < 1 is reported as a **NOTE**, not a rejection.

## 1. Candidate sweep used to choose the ranges (anchored estimates)

| Case | Parameter = value | Re_in | Δp [Pa] | T_out [K] | near-wall air max [K] | solid max [K] | solid mean [K] | y⁺_max | ΔL (LC1) [mm] | LC2 peak [MPa] | LC2 util. | λ₁ (S1) | Flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cand_V_0.700 | inlet velocity = 16.45 m/s | 20970 | 265 | 398.4 | 650.3 | 656.4 | 612.8 | 0.428 | 2.631 | 839 | 0.810 | 0.775 | INVALID: near-wall air 650 K above the 600 K air-property table; NOTE: λ₁(S1) < 1 |
| cand_V_0.750 | inlet velocity = 17.625 m/s | 22467 | 292 | 391.8 | 629.5 | 635.7 | 593.4 | 0.455 | 2.458 | 790 | 0.760 | 0.830 | INVALID: near-wall air 629 K above the 600 K air-property table; NOTE: λ₁(S1) < 1 |
| cand_V_0.800 | inlet velocity = 18.8 m/s | 23965 | 319 | 386.1 | 611.1 | 617.5 | 576.4 | 0.481 | 2.303 | 745 | 0.716 | 0.886 | INVALID: near-wall air 611 K above the 600 K air-property table; NOTE: λ₁(S1) < 1 |
| cand_V_0.850 | inlet velocity = 19.975 m/s | 25463 | 348 | 381.1 | 594.8 | 601.4 | 561.4 | 0.507 | 2.165 | 704 | 0.675 | 0.942 | MARGINAL: near-wall air 595 K within 10 K of the 600 K air table; NOTE: λ₁(S1) < 1 |
| cand_V_0.875 | inlet velocity = 20.562 m/s | 26212 | 362 | 378.7 | 587.4 | 594.0 | 554.6 | 0.520 | 2.103 | 685 | 0.656 | 0.970 | NOTE: λ₁(S1) < 1 |
| cand_V_0.900 | inlet velocity = 21.15 m/s | 26961 | 377 | 376.6 | 580.3 | 586.9 | 548.1 | 0.533 | 2.044 | 667 | 0.639 | 0.998 | NOTE: λ₁(S1) < 1 |
| cand_V_1.000 | inlet velocity = 23.5 m/s | 29957 | 438 | 368.9 | 555.3 | 562.1 | 525.5 | 0.585 | 1.841 | 605 | 0.578 | 1.108 | OK |
| cand_V_1.100 | inlet velocity = 25.85 m/s | 32952 | 503 | 362.7 | 534.6 | 541.6 | 506.9 | 0.636 | 1.677 | 554 | 0.528 | 1.217 | OK |
| cand_V_1.125 | inlet velocity = 26.438 m/s | 33701 | 520 | 361.3 | 530.0 | 537.0 | 502.8 | 0.649 | 1.641 | 543 | 0.517 | 1.243 | OK |
| cand_V_1.250 | inlet velocity = 29.375 m/s | 37446 | 607 | 355.2 | 509.5 | 516.7 | 484.6 | 0.712 | 1.482 | 494 | 0.469 | 1.376 | OK |
| cand_V_1.500 | inlet velocity = 35.25 m/s | 44935 | 798 | 346.0 | 478.3 | 485.8 | 457.1 | 0.836 | 1.249 | 420 | 0.398 | 1.633 | OK |
| cand_Q_6000 | outer heat flux = 6000 W/m2 | 29957 | 393 | 351.7 | 486.6 | 492.2 | 462.3 | 0.585 | 1.292 | 433 | 0.411 | 1.578 | OK |
| cand_Q_7000 | outer heat flux = 7000 W/m2 | 29957 | 415 | 360.3 | 520.6 | 526.9 | 493.3 | 0.585 | 1.558 | 517 | 0.492 | 1.309 | OK |
| cand_Q_7200 | outer heat flux = 7200 W/m2 | 29957 | 420 | 362.1 | 527.5 | 533.9 | 499.7 | 0.585 | 1.613 | 535 | 0.509 | 1.264 | OK |
| cand_Q_7500 | outer heat flux = 7500 W/m2 | 29957 | 427 | 364.6 | 537.9 | 544.4 | 509.3 | 0.585 | 1.697 | 561 | 0.535 | 1.202 | OK |
| cand_Q_8000 | outer heat flux = 8000 W/m2 | 29957 | 438 | 368.9 | 555.3 | 562.1 | 525.5 | 0.585 | 1.841 | 605 | 0.578 | 1.108 | OK |
| cand_Q_8500 | outer heat flux = 8500 W/m2 | 29957 | 449 | 373.2 | 572.8 | 579.9 | 542.0 | 0.585 | 1.989 | 650 | 0.622 | 1.026 | OK |
| cand_Q_8800 | outer heat flux = 8800 W/m2 | 29957 | 456 | 375.8 | 583.4 | 590.7 | 552.0 | 0.585 | 2.079 | 678 | 0.649 | 0.981 | NOTE: λ₁(S1) < 1 |
| cand_Q_9000 | outer heat flux = 9000 W/m2 | 29957 | 461 | 377.5 | 590.5 | 597.9 | 558.7 | 0.585 | 2.141 | 696 | 0.668 | 0.953 | MARGINAL: near-wall air 591 K within 10 K of the 600 K air table; NOTE: λ₁(S1) < 1 |
| cand_Q_9500 | outer heat flux = 9500 W/m2 | 29957 | 472 | 381.8 | 608.4 | 616.0 | 575.8 | 0.585 | 2.297 | 743 | 0.714 | 0.888 | INVALID: near-wall air 608 K above the 600 K air-property table; NOTE: λ₁(S1) < 1 |
| cand_Q_10000 | outer heat flux = 10000 W/m2 | 29957 | 483 | 386.1 | 626.3 | 634.2 | 593.0 | 0.585 | 2.455 | 789 | 0.760 | 0.831 | INVALID: near-wall air 626 K above the 600 K air-property table; NOTE: λ₁(S1) < 1 |
| cand_Q_12000 | outer heat flux = 12000 W/m2 | 29957 | 529 | 403.3 | 699.2 | 708.4 | 665.0 | 0.585 | 3.100 | 969 | 0.941 | 0.658 | INVALID: near-wall air 699 K above the 600 K air-property table; INVALID: solid 708 K above the 673 K Inconel E/k/S_y tables; FLAG: thermal expansion outside the small-strain / one-way-coupling basis; NOTE: λ₁(S1) < 1 |
| cand_T_6 | wall thickness = 6 mm | 29957 | 438 | 368.9 | 555.3 | 559.9 | 524.4 | 0.585 | 1.831 | 602 | 0.575 | 0.793 | NOTE: λ₁(S1) < 1 |
| cand_T_8 | wall thickness = 8 mm | 29957 | 438 | 368.9 | 555.3 | 561.1 | 525.0 | 0.585 | 1.836 | 604 | 0.577 | 0.942 | NOTE: λ₁(S1) < 1 |
| cand_T_10 | wall thickness = 10 mm | 29957 | 438 | 368.9 | 555.3 | 562.1 | 525.5 | 0.585 | 1.841 | 605 | 0.578 | 1.108 | OK |
| cand_T_12 | wall thickness = 12 mm | 29957 | 438 | 368.9 | 555.3 | 563.1 | 525.9 | 0.585 | 1.845 | 606 | 0.579 | 1.291 | OK |
| cand_T_14 | wall thickness = 14 mm | 29957 | 438 | 368.9 | 555.3 | 563.9 | 526.4 | 0.585 | 1.849 | 608 | 0.580 | 1.492 | OK |
| cand_Tq_8 | wall thickness = 8 mm | 29957 | 420 | 362.1 | 527.5 | 532.9 | 499.2 | 0.585 | 1.609 | 533 | 0.508 | 1.075 | OK |
| cand_Tq_12 | wall thickness = 12 mm | 29957 | 456 | 375.8 | 583.4 | 591.7 | 552.5 | 0.585 | 2.084 | 679 | 0.651 | 1.143 | OK |
| corner_Vlow_Qhigh | V 0.9x & q 8800 | 26961 | 393 | 384.2 | 611.2 | 618.2 | 577.5 | 0.533 | 2.313 | 748 | 0.719 | 0.882 | INVALID: near-wall air 611 K above the 600 K air-property table; NOTE: λ₁(S1) < 1 |
| corner_Vhigh_Qlow | V 1.1x & q 7200 | 32952 | 483 | 356.4 | 509.1 | 515.6 | 483.4 | 0.636 | 1.472 | 490 | 0.466 | 1.386 | OK |
| corner_Vlow_Qlow | V 0.9x & q 7200 | 26961 | 360 | 368.9 | 549.8 | 556.0 | 519.5 | 0.533 | 1.788 | 589 | 0.562 | 1.141 | OK |
| corner_Vhigh_Qhigh | V 1.1x & q 8800 | 32952 | 523 | 368.9 | 560.4 | 567.9 | 531.1 | 0.636 | 1.891 | 620 | 0.593 | 1.079 | OK |

**How to read the sweep.**

- **Velocity.** −15 % is MARGINAL (near-wall air 595 K); −20 % and below are INVALID (air table exceeded). ±10 % keeps about 20 K of margin at the low end.
- **Heat flux.** +12.5 % (9,000 W/m²) is MARGINAL (591 K); +18.75 % and above are INVALID; 12,000 W/m² also exceeds the Inconel tables. +10 % (8,800 W/m²) keeps a 17 K margin.
- **Thickness** (total heat input Q held constant). Temperatures change by ≤ 2 K, so the thermal validity is unaffected. The range is set by the Student node limit (`Planning/PARAMETRIC_PLAN.md` §3).
- **Constant q″ instead of constant Q** (rows `cand_Tq_*`). The heat input then changes by ∓10 % and masks the section effect. This is why the thickness cases hold Q constant.
- **Factorial corners.** The adverse corner (V −10 %, q″ +10 %) is **INVALID** (611 K > 600 K). A full factorial would therefore require property extrapolation, while one-factor-at-a-time does not.

## 2. Proposed matrix (anchored estimates)

| Case | Parameter = value | Re_in | Δp [Pa] | T_out [K] | near-wall air max [K] | solid max [K] | solid mean [K] | y⁺_max | ΔL (LC1) [mm] | LC2 peak [MPa] | LC2 util. | λ₁ (S1) | Flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P00_BASELINE | baseline | 29957 | 438 | 368.9 | 555.3 | 562.1 | 525.5 | 0.585 | 1.841 | 605 | 0.578 | 1.108 | OK |
| V01_LOW | inlet velocity = 21.15 m/s | 26961 | 377 | 376.6 | 580.3 | 586.9 | 548.1 | 0.533 | 2.044 | 667 | 0.639 | 0.998 | NOTE: λ₁(S1) < 1 |
| V03_HIGH | inlet velocity = 25.85 m/s | 32952 | 503 | 362.7 | 534.6 | 541.6 | 506.9 | 0.636 | 1.677 | 554 | 0.528 | 1.217 | OK |
| Q01_LOW | outer heat flux = 7200 W/m2 | 29957 | 420 | 362.1 | 527.5 | 533.9 | 499.7 | 0.585 | 1.613 | 535 | 0.509 | 1.264 | OK |
| Q03_HIGH | outer heat flux = 8800 W/m2 | 29957 | 456 | 375.8 | 583.4 | 590.7 | 552.0 | 0.585 | 2.079 | 678 | 0.649 | 0.981 | NOTE: λ₁(S1) < 1 |
| T01_THIN | wall thickness = 8 mm | 29957 | 438 | 368.9 | 555.3 | 561.1 | 525.0 | 0.585 | 1.836 | 604 | 0.577 | 0.942 | NOTE: λ₁(S1) < 1 |
| T03_THICK | wall thickness = 12 mm | 29957 | 438 | 368.9 | 555.3 | 563.1 | 525.9 | 0.585 | 1.845 | 606 | 0.579 | 1.291 | OK |

## 3. Change from P00_BASELINE (screening)

| Quantity | P00 | V01_LOW | V03_HIGH | Q01_LOW | Q03_HIGH | T01_THIN | T03_THICK |
|---|---|---|---|---|---|---|---|
| ṁ [g/s] (analytical) | 8.686 | 7.818 (-10.0 %) | 9.555 (+10.0 %) | 8.686 (+0.0 %) | 8.686 (+0.0 %) | 8.686 (+0.0 %) | 8.686 (+0.0 %) |
| Q [W] (analytical) | 603.2 | 603.2 (+0.0 %) | 603.2 (+0.0 %) | 542.9 (-10.0 %) | 663.5 (+10.0 %) | 603.2 (+0.0 %) | 603.2 (-0.0 %) |
| Re_out | 2.555e+04 | 2.264e+04 (-11.4 %) | 2.846e+04 (+11.4 %) | 2.591e+04 (+1.4 %) | 2.52e+04 (-1.4 %) | 2.555e+04 (+0.0 %) | 2.555e+04 (+0.0 %) |
| h mean [W/m²K] (analytical) | 73.96 | 67.19 (-9.1 %) | 80.62 (+9.0 %) | 75.42 (+2.0 %) | 72.57 (-1.9 %) | 73.96 (+0.0 %) | 73.96 (+0.0 %) |
| through-wall ΔT at exit [K] (analytical) | 7.285 | 7.048 (-3.2 %) | 7.471 (+2.6 %) | 6.784 (-6.9 %) | 7.721 (+6.0 %) | 6.177 (-15.2 %) | 8.286 (+13.8 %) |
| Δp [Pa] | 438.1 | 376.9 (-14.0 %) | 503 (+14.8 %) | 420 (-4.1 %) | 456.2 (+4.1 %) | 438.1 (+0.0 %) | 438.1 (+0.0 %) |
| T_out [K] | 368.9 | 376.6 (+7.6 K) | 362.7 (-6.3 K) | 362.1 (-6.9 K) | 375.8 (+6.9 K) | 368.9 (+0.0 K) | 368.9 (+0.0 K) |
| solid max [K] | 562.1 | 586.9 (+24.8 K) | 541.6 (-20.5 K) | 533.9 (-28.3 K) | 590.7 (+28.6 K) | 561.1 (-1.0 K) | 563.1 (+0.9 K) |
| LC1 ΔL [mm] | 1.841 | 2.044 (+11.0 %) | 1.677 (-8.9 %) | 1.613 (-12.4 %) | 2.079 (+12.9 %) | 1.836 (-0.2 %) | 1.845 (+0.2 %) |
| LC1 max VM [MPa] | 24.28 | 23.43 (-3.5 %) | 24.87 (+2.4 %) | 22.57 (-7.0 %) | 25.65 (+5.6 %) | 20.05 (-17.4 %) | 28.27 (+16.4 %) |
| LC2 mean axial [MPa] | -582.4 | -642.1 (-10.3 %) | -533.6 (+8.4 %) | -514.6 (+11.7 %) | -652.3 (-12.0 %) | -581.1 (+0.2 %) | -583.6 (-0.2 %) |
| LC2 peak VM [MPa] | 605.2 | 667.2 (+10.3 %) | 554.4 (-8.4 %) | 534.6 (-11.7 %) | 677.8 (+12.0 %) | 603.8 (-0.2 %) | 606.4 (+0.2 %) |
| LC2 end force [kN] | 548.9 | 605.2 (+10.3 %) | 502.9 (-8.4 %) | 485 (-11.7 %) | 614.8 (+12.0 %) | 408.9 (-25.5 %) | 704.1 (+28.3 %) |
| LC2 utilisation | 0.578 | 0.6389 (+10.5 %) | 0.5284 (-8.6 %) | 0.5091 (-11.9 %) | 0.6494 (+12.4 %) | 0.5766 (-0.2 %) | 0.5792 (+0.2 %) |
| first-yield factor | 1.73 | 1.565 (-9.5 %) | 1.893 (+9.4 %) | 1.964 (+13.5 %) | 1.54 (-11.0 %) | 1.734 (+0.2 %) | 1.727 (-0.2 %) |
| λ₁ S1 (current) | 1.108 | 0.9978 (-9.9 %) | 1.217 (+9.8 %) | 1.264 (+14.1 %) | 0.981 (-11.5 %) | 0.9419 (-15.0 %) | 1.291 (+16.5 %) |
| λ₁ S2 (scaled 8A) | 4.3 | 3.872 (-9.9 %) | 4.721 (+9.8 %) | 4.907 (+14.1 %) | 3.807 (-11.5 %) | 3.655 (-15.0 %) | 5.011 (+16.5 %) |
| λ₁ S3 (hand, scaled) | 2.221 | 2 (-9.9 %) | 2.438 (+9.8 %) | 2.535 (+14.1 %) | 1.966 (-11.5 %) | 1.888 (-15.0 %) | 2.588 (+16.5 %) |
| P_cr S1 [kN] | 608.2 | 603.9 (-0.7 %) | 611.8 (+0.6 %) | 613.2 (+0.8 %) | 603.2 (-0.8 %) | 385.2 (-36.7 %) | 909.2 (+49.5 %) |

**Sign convention.** For the mean axial stress (negative, compression) the percentage is (value − P00)/|P00|, so −10 % means 10 % *more* compression.

## 4. What the screening shows (trend statements for planning, not results)

1. **Velocity and heat flux act on the structure almost only through the temperature level.** At ±10 %, LC2 stress and λ₁ move by 8–14 %. Heat flux also scales the through-wall ΔT (LC1); velocity barely changes it.
2. **Wall thickness at constant heat input leaves the temperatures and the restrained stress nearly unchanged (≤ 0.2 %).** It changes the section instead: the end force by −26 / +28 %, λ₁ by −15 / +16.5 % and P_cr by −37 / +50 %. It is the only variable that tests the stability lever directly.
3. **Three proposed cases put the anchored λ₁(S1) at or below 1: V01 (≈ 1.00), Q03 (≈ 0.98) and T01 (≈ 0.94).** For the current idealised support, the ideal straight column would bifurcate there before reaching the static LC2 state. Their LC2 static results then describe an ideal pre-buckling state and must be reported with that caveat.
4. **No proposed case approaches yield.** LC2 utilisation stays ≤ 0.65 and the first-yield factor ≥ 1.54, so for S1 stability stays more limiting than yield in every case.
5. **All proposed cases stay inside every property table,** turbulent (Re_out ≥ 22,600), with y⁺_max ≤ 0.64, Δp ≤ 0.5 % of p_op and Mach ≤ 0.09.
