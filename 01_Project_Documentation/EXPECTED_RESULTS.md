# EXPECTED RESULTS — engineering ranges for checking ANSYS

**Section 2 · 2026-09-18 · RE-ANALYSIS (2026)**

> ### How to use this file
> These are **ranges, not predictions.** No CFD or FEA has been run, and no exact
> simulation value is being invented here. Each range comes from an analytical baseline
> plus an honest estimate of the uncertainty in the method that produced it.
>
> - **Inside the range** → the simulation is behaving. Proceed.
> - **Outside the range** → stop and diagnose. Do **not** adjust the model until it agrees;
>   find out *why* it disagrees.
> - **The "red flag" column** names the specific failure each deviation usually indicates.

---

## 1. Fluid mechanics

| Parameter | Expected range | Basis | 🚩 If outside |
|---|---|---|---|
| Reynolds number, inlet | 29 400 – 30 500 | ρVD/μ, ±2 % on property spread | Inlet BC or property model wrong |
| Reynolds number, outlet | 25 000 – 26 100 | Falls as μ rises with T | Energy equation not converged |
| Outlet velocity | 27.5 – 30.3 m/s | G/ρ_out, ±5 % | Density model not temperature-dependent |
| Mach number (max) | 0.070 – 0.080 | V/√(γRT) | — |
| **Flow regime** | **Turbulent throughout** | Re ≥ 25 548 ≫ 4000 | Any laminar region means a BC error |
| Darcy friction factor | **0.022 – 0.027** | Petukhov 0.0241 ±10 % | Low → mesh too coarse near wall; high → y⁺ far too large |
| Hydrodynamic entry length | x/D ≈ 15 – 20 | 1.359·Re^0.25 = 17.9 | — |

## 2. Pressure drop

| Parameter | Expected range | Basis | 🚩 If outside |
|---|---|---|---|
| **Δp across the CFD domain** | **375 – 510 Pa** | 441.5 Pa ±15 % (friction 263 + acceleration 149 + entry 29) | Much higher → check for spurious inlet losses; much lower → wall shear under-resolved |
| — friction component | 224 – 303 Pa | Darcy–Weisbach ±15 % | |
| — acceleration component | 127 – 171 Pa | G²(1/ρ_out − 1/ρ_in) ±15 % | Missing entirely → density is constant, not ideal-gas |
| Δp / p_operating | < 1 % | 0.44 % computed | > 5 % invalidates incompressible ideal gas |
| ⚠ Installation total (**not** CFD) | 850 – 1150 Pa | Adds K=0.5 entrance + K=1.0 exit | **Never compare this against Fluent** |

## 3. Heat transfer

| Parameter | Expected range | Basis | 🚩 If outside |
|---|---|---|---|
| **Total heat rate Q** | **600 – 606 W** | q″ₒ·A_o = 603.2 W, ±0.5 % — conservation, not correlation | **Hard failure.** BC or convergence error |
| **Outlet bulk temperature** | **365 – 373 K** | Energy balance 368.9 K, ±1 % | **Hard failure.** Independent of h — a miss means BCs or convergence |
| Bulk temperature profile | **Linear** in x | Constant imposed flux | Non-linear → flux not uniform, or not converged |
| **Fully developed Nu (x/D > 18)** | **44 – 67** | 49.6 property-corrected (expected) to 66.8 constant-property Dittus–Boelter (upper bound) | Below 44 → near-wall mesh under-resolved; above 67 → property variation not captured |
| h at exit | 70 – 97 W/m²·K | Corresponds to the Nu band | |
| **Peak inner wall temperature** | **534 – 583 K** | 574.4 K corrected; bounds are constant-property (534 K) and n = 0.575 (583 K) | Above 583 K → h under-predicted; below 534 K → property correction over-applied |
| Wall-to-bulk ΔT at exit | 165 – 215 K | q″ᵢ/h across the h band | |
| **Through-wall ΔT** | **6.6 – 8.0 K** | Fourier 7.28 K ±10 % | Near zero → interface not actually coupled (this is the key conjugate check) |
| **Maximum solid temperature** | **541 – 591 K** | Outer wall at exit, 581.7 K, across the same bounds | Above 650 °C would exceed the alloy's service range — it does not come close |
| y⁺ on the conjugate wall | **≤ 1** target, < 5 acceptable | Wall-resolved SST | > 5 → wall heat flux is modelled, not resolved; solid temperature unreliable |

## 4. Thermal expansion

| Parameter | Expected range | Basis | 🚩 If outside |
|---|---|---|---|
| Volume-mean solid temperature | 542 – 566 K | Across the n = 0.4 – 0.575 range | |
| Thermal strain ε_th | 3300 – 3700 µε | α ΔT with the above | |
| **Free axial growth ΔL** | **1.95 – 2.25 mm** | ε_th · L = 2.096 mm | Far off → reference temperature not set to 300 K |
| Free bore growth Δr | 32 – 38 µm | ε_th · rᵢ = 34.9 µm | |
| Flow-area change | < 1 % | 0.700 % | > 2 % would undermine the one-way coupling justification |

## 5. Thermal stress

| Parameter | Expected range | Basis | 🚩 If outside |
|---|---|---|---|
| **LC1 peak von Mises (mid-span)** | **13 – 20 MPa** | Timoshenko 16.3 MPa ±20 % | Much higher → check the temperature import, not the solver |
| LC1 hoop at bore | +13 to +20 MPa **tension** | Bore is the cold side | **Wrong sign is a real error** — it would mean the thermal field is inverted |
| LC1 hoop at outer surface | −8 to −13 MPa **compression** | Outer is the hot side | Wrong sign, as above |
| LC1 radial stress at both surfaces | ≈ 0 | Free surfaces | Non-zero → constraint leaking onto a free face |
| **LC2 axial stress (mid-span)** | **600 – 700 MPa compressive** | −E α ΔT = −657 MPa; n-range gives 625–686 | Far off → temperature import failed |
| **LC2 utilisation of hot yield** | **0.60 – 0.70** | Against S_y = 1023.7 MPa at temperature | **≥ 1.0 invalidates linear-elastic analysis** — plasticity would be required |
| LC2 margin of safety | 0.43 – 0.67 | S_y/\|σ\| − 1 | Negative → design unacceptable as restrained |
| **LC2 / LC1 ratio** | **30 – 50×** | 40.3 computed | **This is the headline finding.** A ratio near 1 would mean a load case is set up wrongly |
| Stress at constrained end faces | **not bounded** | Singularity | Expected. Do **not** treat as a result; exclude from comparison |

## 6. Numerical quality

| Parameter | Expected | Basis |
|---|---|---|
| Energy residual | < 1 × 10⁻⁶ | Standard for conjugate heat transfer |
| Continuity, momentum, turbulence residuals | < 1 × 10⁻⁴ | |
| Outlet bulk temperature drift | < 0.1 K over the last 200 iterations | Physical convergence monitor — residuals alone are not proof |
| Energy imbalance reported by Fluent | < 0.5 % | |
| Mesh independence | < 3 % change in Nu and peak solid T across 3 levels | |
| Orthogonal quality | > 0.1 | Fluent guidance |
| Maximum skewness | < 0.95 | Fluent guidance |

---

## 7. The three checks that matter most

If time is short, these three catch almost every real error:

1. **Total heat rate = 603 W ± 0.5 %.** Pure conservation. No correlation, no turbulence
   model. If this fails, nothing else is worth looking at.
2. **Through-wall ΔT ≈ 7.3 K.** If this collapses toward zero, the fluid and solid are not
   actually thermally coupled — the single most common conjugate-setup mistake.
3. **LC2/LC1 ratio ≈ 40.** If this comes out near 1, one of the two load cases has the
   wrong restraint applied.

## 8. What the ranges deliberately do **not** do

- They are **not** tightened to make the project look precise. The Nusselt band is wide
  (44–67) because the correlations are genuinely being used outside their comfortable
  validity range, and pretending otherwise would be dishonest.
- They contain **no invented CFD values**. Every bound traces to an analytical result plus
  a stated uncertainty.
- They will **not** be revised after seeing the CFD. If a result falls outside, that is a
  finding to investigate and report — not a reason to widen the range retrospectively.
