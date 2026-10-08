# Parametric structural results — Section 9B-2

> **RE-ANALYSIS 2026.** Every number in this document is a newly generated ANSYS 2026 R1 Student result of this re-analysis (Fluent CFD of Section 9B-1, Mechanical of Section 9B-2), computed from the solver's own output tables. Nothing is a recovered internship value, and no experimental or measured data exist or are implied.

Cases: the baseline P00 (official 7B / 8A solution, reference), the pipeline control C00, and the six design cases V01, V03, Q01, Q03, T01 and T03. Each design case is driven by the **actual 9B-1 CFD temperature field of that case**; no screening temperature is used anywhere. Tables: `PARAMETRIC_STRUCTURAL_RESULTS.csv`; data: `Data/post_9B2_results.json` (written by `Scripts/post_9B2.py` from the raw solver tables).

## 1. Method (unchanged from 7A / 7B / 8A / 8B)

| Item | 9B-2 |
|---|---|
| Model per case | A SAVE-AS copy of the solved 7B Workbench project (`Structural_Cases/<CASE>/Project`). The 7B project is never written to (hash check, §9) |
| Temperature | Mesh-based External Data (7A method): the case's own Fluent solid mesh as CDB master, plus its own node temperatures. Settings re-applied and read back; the Setup cells refreshed; Mechanical's own source minimum/maximum must equal the case file. Manual / Bucket Volume / Shape Functions / Nearest Node |
| Material | Inconel_718_Re_analysis: E(T), secant α(T), ν = 0.294 [ASSUMED]. The solver material block is checked identical to 7B in every case. Yield S_y(T) = VDM 4127 table, linear, 20–400 °C, **no extrapolation** (every case lies inside) |
| Supports (not changed between cases) | LC1: 3 outer-ring nodes at the inlet, U_θ = U_z = 0 (CS_DUCT_CYL). LC2: U_z = 0 on both complete end faces, plus 3 mid-span outer nodes U_θ = 0. Buckling: S1 = LC2 pre-stress, 6 modes, positive multipliers. Node sets re-located at the same positions (outer radius of the case) |
| Solver | sparse direct, linear, small deflection; T_ref 300 K |
| Pre-solve gate | 44–49 checks per case, all PASS before any solve (mesh counts vs formula, quality, extents, support positions, source identity, mapped range, 0 unmapped, object states, solver-input material / constraint sets / temperatures) |
| Pressure (Part N) | not re-run: 7B LC2P showed +45 Pa (+7.4 × 10⁻⁶ %) on the LC2 peak at the CFD maximum wall pressure. The Δp of the design cases (380–500 Pa) is of the same order, so its effect is negligible for every case |

## 2. Structural meshes (Part C)

| Case | Geometry | Divisions (circ × wall × axial, bias) | Radial element | Nodes (limit 128,000) | Elements | Jacobian ratio max | Element quality min | Aspect ratio max | Through-wall node radii |
|---|---|---|---|---|---|---|---|---|---|
| C00 | baseline (Do 40) | 36 × 5 × 130, 4 | 2.00 mm | 108,252 | 23,400 | 1.205 | 0.237 | 4.88 | 11, uniform |
| V01 | baseline (Do 40) | 36 × 5 × 130, 4 | 2.00 mm | 108,252 | 23,400 | 1.205 | 0.237 | 4.88 | 11, uniform |
| V03 | baseline (Do 40) | 36 × 5 × 130, 4 | 2.00 mm | 108,252 | 23,400 | 1.205 | 0.237 | 4.88 | 11, uniform |
| Q01 | baseline (Do 40) | 36 × 5 × 130, 4 | 2.00 mm | 108,252 | 23,400 | 1.205 | 0.237 | 4.88 | 11, uniform |
| Q03 | baseline (Do 40) | 36 × 5 × 130, 4 | 2.00 mm | 108,252 | 23,400 | 1.205 | 0.237 | 4.88 | 11, uniform |
| T01 | T01 (Do 36) | 36 × 4 × 130, 4 | 2.00 mm | 89,424 | 18,720 | 1.205 | 0.237 | 4.88 | 9, uniform |
| T03 | T03 (Do 44) | 36 × 6 × 130, 4 | 2.00 mm | 127,080 | 28,080 | 1.205 | 0.237 | 4.88 | 13, uniform |
| M01 | T01 (Do 36) | 36 × 5 × 130, 4 | 1.60 mm | 108,252 | 23,400 | 1.164 | 0.192 | 5.32 | 11, uniform |
| M02 | T03 (Do 44) | 36 × 5 × 130, 4 | 2.40 mm | 108,252 | 23,400 | 1.245 | 0.279 | 4.88 | 11, uniform |

- **V / Q / C00 reuse mesh B unchanged.** The solver-input node and element blocks are identical to 7B (gate check). The temperature check of §3 gave no reason to change it.
- **T01 / T03 use the geometry-specific meshes of 9A.** They have the same 2.0 mm radial element as mesh B, the same 36 × 130 divisions and axial bias, and they were generated on the 9B-1 SpaceClaim models. Node count = the swept-hex formula (89,424 / 127,080 < 128,000).
- **Axial resolution** (130 divisions, bias 4, first element 2.13 mm) is that of mesh B. 8B showed it converged for LC2 and λ₁ (FA +152 divisions: ≤ 0.004 %).
- **Through-wall resolution of the thickness extremes (9A rows M01 / M02).** The same case was re-solved with 5 through-wall elements (T01: 1.6 mm; T03: 2.4 mm, a coarsening, because refinement exceeds 128,000 nodes). Result:

| Check | Reference | LC2 max VM | LC2 mean axial stress | λ₁ | LC1 max VM | LC1 mid-span bore σθ | LC1 max deformation | Class A (LC2, λ₁ ≤ 10⁻⁴) |
|---|---|---|---|---|---|---|---|---|
| M01 | T01 | +1.40e-04 | -3.92e-06 | -4.20e-06 | +1.39 % | +0.83 % | +3.20e-06 | **FAIL** |
| M02 | T03 | -8.47e-05 | +2.40e-06 | +2.49e-06 | -1.15 % | -0.63 % | -1.55e-06 | **PASS** |

- **Reading.** The LC2 mean axial stress and λ₁ change by at most 4.2e-06 and the LC2 peak by at most 1.4e-04 (relative). M01 exceeds the 10⁻⁴ class-A tolerance on the LC2 peak only. The LC2 peak is a single node at the outer edge of the inlet face, a stress-concentration point whose value depends on the local discretisation; the change is 34× smaller than the T01 change against P00 (0.47 %), so no trend, λ₁ < 1 classification or utilisation statement is affected. The LC1 peak (bore, near the inlet) changes by +1.39 % / -1.15 %: a through-wall discretisation uncertainty of about ±1.4 % on the LC1 stresses of T01 / T03 (≈ 2 % of S_y; no decision depends on them).
- The 4- and 6-division meshes are therefore kept for T01 / T03; these differences are carried as structural-mesh uncertainty (`FINAL_PARAMETRIC_AUDIT.md` §3, #4).

## 3. Temperature mapping (Part D)

Detail per geometry family: `Mapping/MAPPING_AUDIT_9B2.md`.

| Case | Unmapped | Mechanical source min / max = case CSV | Mapped range [K] | (A) mapping error max [K] | Mid-span ΔT mapped / source [K] | Mid-span mean mapped / source [K] |
|---|---|---|---|---|---|---|
| C00 | 0 | 423.837 / 562.544 | 423.837 – 562.566 | 0.096 | 7.580 / 7.581 | 536.36 / 536.36 |
| V01 | 0 | 435.916 / 587.433 | 435.916 – 587.455 | 0.103 | 7.378 / 7.379 | 559.14 / 559.13 |
| V03 | 0 | 413.884 / 542.066 | 413.884 – 542.088 | 0.090 | 7.754 / 7.755 | 517.60 / 517.59 |
| Q01 | 0 | 410.597 / 534.415 | 410.597 – 534.435 | 0.086 | 7.034 / 7.035 | 510.61 / 510.61 |
| Q03 | 0 | 437.279 / 591.092 | 437.279 – 591.115 | 0.106 | 8.089 / 8.090 | 562.57 / 562.56 |
| T01 | 0 | 417.966 / 561.927 | 417.966 – 561.941 | 0.154 | 6.436 / 6.437 | 535.84 / 535.83 |
| T03 | 0 | 428.783 / 563.044 | 428.783 – 563.058 | 0.105 | 8.607 / 8.608 | 536.84 / 536.83 |

## 4. LC1 — free thermal expansion (Part F)

| Case | Value | Max total deformation [mm] | Axial growth ΔL [mm] | Max von Mises [MPa] | Critical location | T there [K] | Reaction magnitude ΣF [N] | Change vs P00 (deformation / ΔL / VM) |
|---|---|---|---|---|---|---|---|---|
| P00 | V 23.5 m/s · q″ 8000 W/m² · t 10 mm | 1.8443 | 1.8409 | 24.282 | bore, r 10 mm, z 6.5 mm | 427.81 | 3.9e-07 | - / - / - |
| C00 | = P00 | 1.8443 | 1.8409 | 24.169 | bore, r 10 mm, z 6.5 mm | 427.89 | 4.2e-07 | +0.00 % / +0.00 % / -0.46 % |
| V01 | V 21.15 m/s | 2.0375 | 2.0339 | 24.925 | bore, r 10 mm, z 6.5 mm | 440.24 | 5.0e-07 | +10.48 % / +10.49 % / +2.65 % |
| V03 | V 25.85 m/s | 1.6874 | 1.6842 | 23.532 | bore, r 10 mm, z 6.5 mm | 417.71 | 3.9e-07 | -8.51 % / -8.51 % / -3.09 % |
| Q01 | q″ 7,200 W/m² | 1.6284 | 1.6253 | 21.704 | bore, r 10 mm, z 6.5 mm | 414.20 | 3.7e-07 | -11.71 % / -11.71 % / -10.62 % |
| Q03 | q″ 8,800 W/m² | 2.0680 | 2.0641 | 26.649 | bore, r 10 mm, z 6.5 mm | 441.79 | 5.2e-07 | +12.13 % / +12.13 % / +9.75 % |
| T01 | t 8 mm (Do 36) | 1.8355 | 1.8328 | 20.872 | bore, r 10 mm, z 6.5 mm | 422.25 | 3.6e-07 | -0.48 % / -0.44 % / -14.05 % |
| T03 | t 12 mm (Do 44) | 1.8528 | 1.8487 | 27.206 | bore, r 10 mm, z 6.5 mm | 432.73 | 5.7e-07 | +0.46 % / +0.42 % / +12.04 % |

- The LC1 support is statically determinate. Reactions are ≈ 0 (≤ 5.7e-07 N) in every case, so LC1 stresses come only from the non-uniform temperature field.
- The critical LC1 location is **the bore, 6.5 mm from the inlet face** in every case (the steep axial temperature rise at the inlet end). The maximum deformation is at the outer edge of the outlet face (free growth plus radial growth).
- LC1 stresses are small (≈ 2 % of S_y). They are listed for completeness and drive no decision.

## 5. LC2 — axially restrained thermal expansion (Part G)

| Case | Max von Mises [MPa] | Mean axial stress [MPa] | End reaction [kN] | Max total deformation [mm] | Max axial deformation |u_z| [mm] | Max radial deformation u_r [mm] | Critical location (max vm/S_y) | Critical T [K] | S_y(T) there [MPa] | Utilisation vm/S_y(T) | λ₁ | Static-state status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P00 | 605.161 | -582.440 | 548.94 | 0.1349 | 0.1088 | 0.0897 | outer edge of the inlet face (r 20 mm, z 0) | 437.99 | 1047.0 | 0.5780 | 1.1080 | static equilibrium below the linear stability limit (λ₁ > 1) |
| C00 | 605.167 | -582.440 | 548.94 | 0.1349 | 0.1088 | 0.0897 | outer edge of the inlet face (r 20 mm, z 0) | 437.99 | 1047.0 | 0.5780 | 1.1080 | static equilibrium below the linear stability limit (λ₁ > 1) |
| V01 | 663.001 | -639.053 | 602.29 | 0.1502 | 0.1217 | 0.0993 | outer edge of the inlet face (r 20 mm, z 0) | 450.38 | 1044.6 | 0.6347 | 1.0031 | static equilibrium below the linear stability limit (λ₁ > 1) |
| V03 | 557.544 | -535.853 | 505.03 | 0.1224 | 0.0983 | 0.0820 | outer edge of the inlet face (r 20 mm, z 0) | 427.76 | 1049.1 | 0.5315 | 1.2109 | static equilibrium below the linear stability limit (λ₁ > 1) |
| Q01 | 538.526 | -518.230 | 488.42 | 0.1189 | 0.0958 | 0.0792 | outer edge of the inlet face (r 20 mm, z 0) | 423.38 | 1050.0 | 0.5129 | 1.2546 | static equilibrium below the linear stability limit (λ₁ > 1) |
| Q03 | 673.024 | -647.830 | 610.57 | 0.1512 | 0.1220 | 0.1007 | outer edge of the inlet face (r 20 mm, z 0) | 452.79 | 1044.1 | 0.6446 | 0.9883 | **pre-buckling equilibrium result; linear stability criterion indicates loss of stability before the applied load level** |
| T01 | 602.309 | -580.048 | 408.19 | 0.1317 | 0.1106 | 0.0806 | outer edge of the inlet face (r 18 mm, z 0) | 429.52 | 1048.7 | 0.5743 | 0.9450 | **pre-buckling equilibrium result; linear stability criterion indicates loss of stability before the applied load level** |
| T03 | 607.735 | -584.750 | 705.43 | 0.1385 | 0.1067 | 0.0989 | outer edge of the inlet face (r 22 mm, z 0) | 445.36 | 1045.6 | 0.5813 | 1.2870 | static equilibrium below the linear stability limit (λ₁ > 1) |

Changes against P00 (the same definitions):

| Case | LC2 max VM | Mean axial stress | End reaction | Max total deformation | Utilisation |
|---|---|---|---|---|---|
| C00 | +0.00 % | -0.00 % | +0.00 % | -0.00 % | +0.00 % |
| V01 | +9.56 % | -9.72 % | +9.72 % | +11.39 % | +9.82 % |
| V03 | -7.87 % | +8.00 % | -8.00 % | -9.24 % | -8.05 % |
| Q01 | -11.01 % | +11.02 % | -11.02 % | -11.85 % | -11.26 % |
| Q03 | +11.21 % | -11.23 % | +11.23 % | +12.13 % | +11.53 % |
| T01 | -0.47 % | +0.41 % | -25.64 % | -2.36 % | -0.63 % |
| T03 | +0.43 % | -0.40 % | +28.51 % | +2.65 % | +0.57 % |

**Cases with λ₁ < 1 (Part I): Q03, T01.** For these cases the LC2 static stress is labelled: *pre-buckling equilibrium result; linear stability criterion indicates loss of stability before the applied load level*. The static Mechanical solution is the idealised equilibrium of the mathematical load case. It is **not** claimed that the duct physically reaches that state without additional stabilisation.
- The mean axial stress follows the mean thermal strain of the whole duct, because the end force is uniform along the length.
- The peak von Mises stress sits at the outer edge of the inlet face in every case: the uniform restrained axial stress plus a local part where the face is held flat (U_z = 0 on every node) and the outer fibre is the hottest point of the section.
- For T01 and T03 the stress level hardly changes: the restrained thermal stress depends on the temperatures (solid mean -0.94 / +0.90 K), not on the section. The end force scales with the cross-section area (T01 -25.6 %, T03 +28.5 %).

## 6. Linear buckling, S1 supports (Part H)

| Case | λ₁ | λ₂ | λ₃ | Critical load P_cr = λ₁·N [kN] | Applied N [kN] | Dominant mode (mode 1) | Classification | λ₁ vs 1 |
|---|---|---|---|---|---|---|---|---|
| P00 | 1.10805 | 1.10805 | 4.2979 | 608.25 | 548.94 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm | global Euler column mode (beam share 0.999999, ovalisation 3.0e-11); modes 1–2 an orthogonal pair (split 1.3e-07) | > 1 |
| C00 | 1.10805 | 1.10805 | 4.2979 | 608.25 | 548.94 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm | global Euler column mode (beam share 0.999999, ovalisation 1.6e-10); modes 1–2 an orthogonal pair (split 1.7e-07) | > 1 |
| V01 | 1.00307 | 1.00307 | 3.8902 | 604.14 | 602.29 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm | global Euler column mode (beam share 0.999999, ovalisation 1.0e-10); modes 1–2 an orthogonal pair (split 7.8e-08) | > 1 |
| V03 | 1.21087 | 1.21087 | 4.6975 | 611.53 | 505.03 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm | global Euler column mode (beam share 0.999999, ovalisation 1.7e-10); modes 1–2 an orthogonal pair (split 4.6e-08) | > 1 |
| Q01 | 1.25464 | 1.25464 | 4.8674 | 612.79 | 488.42 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm | global Euler column mode (beam share 0.999999, ovalisation 1.1e-10); modes 1–2 an orthogonal pair (split 3.5e-08) | > 1 |
| Q03 | 0.98834 | 0.98834 | 3.8332 | 603.45 | 610.57 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm | global Euler column mode (beam share 0.999999, ovalisation 1.5e-10); modes 1–2 an orthogonal pair (split 1.4e-07) | **< 1** |
| T01 | 0.94497 | 0.94497 | 3.6767 | 385.73 | 408.19 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm | global Euler column mode (beam share 0.999999, ovalisation 8.5e-11); modes 1–2 an orthogonal pair (split 8.2e-08) | **< 1** |
| T03 | 1.28702 | 1.28702 | 4.9760 | 907.89 | 705.43 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm | global Euler column mode (beam share 0.999999, ovalisation 1.2e-10); modes 1–2 an orthogonal pair (split 4.4e-08) | > 1 |

- The mode is the same in every case: global sway of a guided column. The end sections translate in opposite directions and stay perpendicular, with no mid-span deflection. No shell, ovalisation or local mode appears in any case.
- λ₁ is a *linear* (eigenvalue) bifurcation factor of the idealised straight tube. It includes no imperfection, no plasticity and no large-deflection effect, and it is not a design margin (8A).

## 7. First yield vs buckling (Part J)

Both factors multiply the **same LC2 thermal load state**.

- **First-yield factor = 1 / utilisation.** It is the linear-elastic scaling of the LC2 stresses at which vm reaches S_y(T) at the critical node; S_y is held at the operating temperature.
- **λ₁** is the factor at which the straight tube bifurcates.

They are reported separately. No single factor of safety is formed.

| Case | First-yield utilisation | First-yield factor | Linear buckling factor λ₁ | Occurs first in the idealised model |
|---|---|---|---|---|
| P00 | 0.5780 | 1.730 | 1.1080 | buckling (λ₁ 1.108 < first-yield factor 1.730) |
| C00 | 0.5780 | 1.730 | 1.1080 | buckling (λ₁ 1.108 < first-yield factor 1.730) |
| V01 | 0.6347 | 1.575 | 1.0031 | buckling (λ₁ 1.003 < first-yield factor 1.575) |
| V03 | 0.5315 | 1.882 | 1.2109 | buckling (λ₁ 1.211 < first-yield factor 1.882) |
| Q01 | 0.5129 | 1.950 | 1.2546 | buckling (λ₁ 1.255 < first-yield factor 1.950) |
| Q03 | 0.6446 | 1.551 | 0.9883 | buckling (λ₁ 0.988 < first-yield factor 1.551) |
| T01 | 0.5743 | 1.741 | 0.9450 | buckling (λ₁ 0.945 < first-yield factor 1.741) |
| T03 | 0.5813 | 1.720 | 1.2870 | buckling (λ₁ 1.287 < first-yield factor 1.720) |

In every case with the S1 supports, **elastic bifurcation comes before first yield**. The LC2 idealisation is stability-controlled, as found in 8A for P00; the utilisation values are therefore **not** structural margins.
Slenderness with the S1 effective length (K = 1, L = 600 mm; r_g = √(R_i² + R_o²)/2): P00 53.7, V01 53.7, V03 53.7, Q01 53.7, Q03 53.7, T01 58.3, T03 49.7. All are below C_c ≈ 60 (8A, P00 properties; E and S_y at the operating temperatures differ by < 1 % between cases), i.e. intermediate columns. Their Euler stress is above the conventional proportional limit, so the elastic λ₁ is an upper estimate of an inelastic buckling load (8A: Johnson 1.058 for P00). Johnson values of the other cases were not computed.

## 8. Critical locations (Part S)

| Case | Max LC2 stress location | T there [K] | S_y(T) there [MPa] | λ₁ | Dominant buckling location / mode |
|---|---|---|---|---|---|
| P00 | outer edge of the inlet face (r 20 mm, z 0) | 437.99 | 1047.0 | 1.1080 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm |
| C00 | outer edge of the inlet face (r 20 mm, z 0) | 437.99 | 1047.0 | 1.1080 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm |
| V01 | outer edge of the inlet face (r 20 mm, z 0) | 450.38 | 1044.6 | 1.0031 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm |
| V03 | outer edge of the inlet face (r 20 mm, z 0) | 427.76 | 1049.1 | 1.2109 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm |
| Q01 | outer edge of the inlet face (r 20 mm, z 0) | 423.38 | 1050.0 | 1.2546 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm |
| Q03 | outer edge of the inlet face (r 20 mm, z 0) | 452.79 | 1044.1 | 0.9883 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm |
| T01 | outer edge of the inlet face (r 18 mm, z 0) | 429.52 | 1048.7 | 0.9450 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm |
| T03 | outer edge of the inlet face (r 22 mm, z 0) | 445.36 | 1045.6 | 1.2870 | global guided-column sway, cos(πz/L) (corr 1.0000); max lateral at z = 600 mm |

- **The critical LC2 location does not move with velocity, heat flux or thickness.**
  It stays at the outer edge of the inlet face (the circumferential position varies only within numerical noise on an axisymmetric field). Its temperature follows the inlet-end wall temperature of each case.
- Away from the end faces (15 mm ≤ z ≤ L − 15 mm) the largest *von Mises stress* is on the outer surface near the inlet (P00: 591.2 MPa at z = 15.9 mm), while the largest *utilisation* is on the outer surface at the hot outlet end, where S_y(T) is lower (P00: 0.5748 at z = 562.7 mm, against 0.5780 at the inlet-face edge).
- The buckling mode and its location (largest curvature at the rotation-held end sections, sway of the ends) are the same in every design case.
- Support-scenario locations: `SUPPORT_SENSITIVITY_RESULTS.md`.

## 9. Controls and integrity

| Control | Result |
|---|---|
| C00 pipeline control vs 7B / 8A (tolerance 10⁻⁵, 9A row C00) | LC2 max VM 605.1666 (9.51e-06); end reaction 548,936.8 (3.33e-07); λ₁ 1.10804654 vs 1.10804700 (-4.15e-07); LC1 ΔL 3.57e-07. The C00 source has Fluent's re-numbered node ids, so up to 0.08 K of numbering-dependent mapping difference remains (§3). Its only visible effect is on the LC1 inlet-bore peak: 24.169 (-0.46 %) |
| Earlier C00 run with the cached P00 source (run 2) | bit-identical to 7B/8A (LC2 VM 605,160,873.381 Pa; λ₁ 1.1080470); kept in `Structural_Cases/Audits/Run2_C00_before_setup_refresh` |
| Source identity guard | the Mechanical source min/max check stopped T01 run 1, which had imported the cached P00 data; fixed by refreshing the Setup cells (D-068) |
| Baseline integrity | `08_Structural_Analysis`: every file identical to the pre-9B-2 hash record (verification V7) |
