# MASTER PROJECT DATA — Section 10A (single source of truth)

> **RE-ANALYSIS 2026 — Re-analysed / Assumed / Simulated 2026.** The original Eleation internship files (Feb–May 2025) were lost. Every number here is a 2026 re-analysis: an input chosen in 2026, a 2026 hand calculation, or a 2026 ANSYS Student 2026 R1 simulation. No value is recovered internship data, and no experimental or measured data exist.

Machine-readable version: `MASTER_PROJECT_DATA.csv` (182 rows, IDs M001–M182). Every VERIFIED value was recomputed in 10A from the rawest file available (Fluent flux / surface-integral reports, MAPDL nodal, reaction and load-factor tables, the CAD measurement file) by `Scripts/master_data_10A.py`, which imports no earlier post-processing script, and compared with the value documented in the section result file. Status counts: CROSS-CHECKED 3, DECISION 2, INPUT 20, INTERPRETATION 4, REPORTED 29, VERIFIED 124.

**Modelling levels are kept apart.** A number is only meaningful together with its level: `ANALYTICAL (Section 2)` 1-D correlations, `CFD-MEDIUM` the official baseline CFD, `CFD-FINE` the verification reference, `CFD-EXTRAPOLATED` Richardson limits, `FE-STATIC` / `FE-BUCKLING` the official Mechanical results, `FE-MESH-STUDY` the 8B variants, and the 9B parametric cases.

## 1. Official baseline definition (P00)

| ID | Item | Definition | Units | Basis |
|---|---|---|---|---|
| M001 | Fluid | air, incompressible ideal gas (rho = p_op/(R T)); cp, mu, k piecewise-linear 250-600 K (Incropera A.4) | - | D-009, D-021 |
| M002 | Inlet temperature T_in | 300 | K | 02_Engineering_Calculations/baseline_parameters.json |
| M003 | Inlet velocity V_in | 23.5 | m/s | uniform, normal to the inlet |
| M004 | Inlet turbulence intensity | 4.411 (0.16 Re^-1/8, D_h 20 mm) | % | [ASSUMED]; ID collision: called A-020 in the CFD documents, A-020 is 'perfect thermal contact' in ASSUMPTIONS.md |
| M005 | Outlet pressure | 0 Pa gauge at operating pressure 101,325 Pa | Pa | pressure outlet; atmospheric pressure never applied as a structural load |
| M006 | Outer-wall heat flux q'' | 8000 (uniform); end faces adiabatic | W/m2 | D-015; inner-wall equivalent 16,000 W/m2 |
| M007 | Solid material | Inconel 718 (VDM 4127 / Special Metals datasheets) | - | generic datasheet, not lot-specific (A-018) |
| M008 | Solid density | 8190 | kg/m3 | read back from Fluent in 5B (F-023 fixed in 5A) |
| M009 | Solid conductivity / heat capacity (CFD) | k(T), cp(T) piecewise-linear 293-673 K (VDM 4127) | - | D-026 |
| M010 | Young's modulus (FE) | E(T) VDM table, 204 -> 180 GPa over 20-400 C | GPa | D-036 |
| M011 | Thermal expansion (FE) | secant alpha(T) from 70 F, 12.8-14.8 e-6 /K, re-referenced to T_ref by MPAMOD | 1/K | D-036 |
| M012 | Poisson's ratio | 0.294 [ASSUMED] | - | in neither datasheet (T-014 / F-011 open) |
| M013 | Yield strength (assessment) | S_y(T) VDM 4127: 1030 / 1060 / 1040 / 1020 / 1000 MPa at 20 / 100 / 200 / 300 / 400 C, linear, no extrapolation | MPa | typical values, not minimum-guaranteed; the scalar 1020 MPa in Engineering Data is a lower bound and is NOT used for utilisation (F-037, T-031) |
| M014 | Structural reference temperature T_ref | 300 | K | D-041; dT = T(x,y,z) - 300 K on the full mapped field |
| M015 | Coupling | one-way: converged CFD solid temperature -> Mechanical (no structural feedback) | - | flow-area change 0.70 % (Section 2) |
| M016 | CFD final reference mesh | MEDIUM, 159,840 cells (fine mesh 500,580 cells = verification reference only) | - | D-034 |
| M017 | Temperature transfer | mesh-based External Data, Manual / Bucket Volume / Shape Functions / Nearest Node (7A) | - | D-038 |
| M018 | Structural final mesh | mesh B: SOLID186 36 x 5 x 130 (bias 4), 108,252 nodes / 23,400 elements | - | D-040, D-056 |
| M019 | LC1 support (free expansion) | 3 outer-ring nodes on the inlet face (0/120/240 deg), U_theta = U_z = 0 in CS_DUCT_CYL; statically determinate | - | D-042 |
| M020 | LC2 support = S1 (baseline) | U_z = 0 on both complete end faces; 3 mid-span outer nodes U_theta = 0; radial free; ends free to sway, end rotation held (guided column, K = 1) | - | D-043 |
| M021 | Support scenario S2 | U_z = U_theta = 0 on every node of both end faces (ends laterally held and rotation held: clamped-clamped, K = 0.5) | - | 8A LC2NS; sensitivity only |
| M022 | Support scenario S3 | inlet face U_z = U_theta = 0 (clamped); outlet deformable remote point on the axis, U = 0, rotations free (pinned); K = 0.699 | - | 9B-2; sensitivity only |

## 2. Geometry

| ID | Parameter | Final value | Units | Modelling level | Status | Source file |
|---|---|---|---|---|---|---|
| M023 | Inner diameter D_i | 20 | mm | INPUT (re-analysed, class B) / CAD | **VERIFIED** | `03_CAD_Geometry/Geometry_Check/cad_measurements.json` |
| M024 | Outer diameter D_o | 40 | mm | INPUT (re-analysed, class B) / CAD | **VERIFIED** | `03_CAD_Geometry/Geometry_Check/cad_measurements.json` |
| M025 | Wall thickness t | 10 | mm | INPUT / CAD | **VERIFIED** | `03_CAD_Geometry/Geometry_Check/cad_measurements.json` |
| M026 | Length L | 600 | mm | INPUT (re-analysed, class B) / CAD | **VERIFIED** | `03_CAD_Geometry/Geometry_Check/cad_measurements.json` |
| M027 | Hydraulic diameter D_h | 20 | mm | CAD | **VERIFIED** | `03_CAD_Geometry/Geometry_Check/cad_measurements.json` |
| M028 | Fluid flow area | 314.159 | mm2 | CAD | **VERIFIED** | `03_CAD_Geometry/Geometry_Check/cad_measurements.json` |
| M029 | Solid volume | 0.0005654867 | m3 | CAD | **VERIFIED** | `03_CAD_Geometry/Geometry_Check/cad_measurements.json` |
| M030 | Heated-wall area (true cylinder) | 0.07539822 | m2 | CAD | **VERIFIED** | `03_CAD_Geometry/Geometry_Check/cad_measurements.json` |
| M031 | Heated-wall area (CFD 48-facet mesh) | 0.07534441 | m2 | CFD-MEDIUM | **VERIFIED** | `06_Fluent_CFD/Audit/fluent_si_areas.txt` |

## 3. Baseline CFD (medium mesh, Section 5B)

| ID | Parameter | Final value | Units | Modelling level | Status | Source file |
|---|---|---|---|---|---|---|
| M032 | Mesh | medium: butterfly O-grid hexahedral, 48 circumferential x 90 axial, 12.2 um first fluid layer | - | CFD-MEDIUM (Section 5B, official baseline) | **REPORTED** | `09_Mesh_Independence/mesh_study_results.json (mesh.medium)` |
| M033 | Cells (fluid + solid) | 159840 | - | CFD-MEDIUM (Section 5B, official baseline) | **VERIFIED** | `06_Fluent_CFD/Exports/cells_fluid.csv + cells_solid.csv` |
| M034 | Reynolds number, inlet | 29958 | - | CFD-MEDIUM (Section 5B, official baseline) | **VERIFIED** | `06_Fluent_CFD/Audit/fluent_si_rho_area.txt` |
| M035 | Reynolds number, outlet | 25545 | - | CFD-MEDIUM (Section 5B, official baseline) | **REPORTED** | `06_Fluent_CFD/Baseline/cfd_baseline_results.json` |
| M036 | Pressure drop (area-weighted static, inlet - outlet) | 438.13 | Pa | CFD-MEDIUM (Section 5B, official baseline) | **VERIFIED** | `06_Fluent_CFD/Audit/fluent_si_p_area.txt` |
| M037 | Outlet bulk temperature (mass-weighted) | 368.93 | K | CFD-MEDIUM (Section 5B, official baseline) | **VERIFIED** | `06_Fluent_CFD/Audit/fluent_si_T_mass.txt` |
| M038 | Heat-transfer rate (heated wall) | 602.755 | W | CFD-MEDIUM (Section 5B, official baseline) | **VERIFIED** | `06_Fluent_CFD/Audit/fluent_flux_heat.txt` |
| M039 | Maximum solid temperature (outer-wall facet) | 562.58 | K | CFD-MEDIUM (Section 5B, official baseline) | **VERIFIED** | `06_Fluent_CFD/Audit/fluent_si_Twall_max.txt` |
| M040 | Maximum solid temperature (hottest cell centre) | 562.13 | K | CFD-MEDIUM (Section 5B, official baseline) | **VERIFIED** | `06_Fluent_CFD/Exports/cells_solid.csv` |
| M041 | Through-wall dT, mid-span z = 300 mm | 7.581 | K | CFD-MEDIUM (Section 5B, official baseline) | **CROSS-CHECKED** | `06_Fluent_CFD/Baseline/cfd_baseline_results.json` |
| M042 | Fully developed Nusselt number (x/D 18-29) | 54.17 | - | CFD-MEDIUM (Section 5B, official baseline) | **CROSS-CHECKED** | `06_Fluent_CFD/Baseline/cfd_baseline_results.json` |
| M043 | Fully developed Darcy friction factor (x/D 18-29) | 0.02163 | - | CFD-MEDIUM (Section 5B, official baseline) | **CROSS-CHECKED** | `06_Fluent_CFD/Baseline/cfd_baseline_results.json` |
| M044 | y+ minimum (conjugate wall) | 0.208 | - | CFD-MEDIUM (Section 5B, official baseline) | **VERIFIED** | `06_Fluent_CFD/Audit/fluent_si_yplus_*.txt` |
| M045 | y+ area mean (conjugate wall) | 0.241 | - | CFD-MEDIUM (Section 5B, official baseline) | **VERIFIED** | `06_Fluent_CFD/Audit/fluent_si_yplus_*.txt` |
| M046 | y+ maximum (conjugate wall) | 0.585 | - | CFD-MEDIUM (Section 5B, official baseline) | **VERIFIED** | `06_Fluent_CFD/Audit/fluent_si_yplus_*.txt` |
| M047 | Mass imbalance | 7.0e-13 | % | CFD-MEDIUM (Section 5B, official baseline) | **VERIFIED** | `06_Fluent_CFD/Audit/fluent_flux_mass.txt` |
| M048 | Energy imbalance | 3.1e-11 | % | CFD-MEDIUM (Section 5B, official baseline) | **VERIFIED** | `06_Fluent_CFD/Audit/fluent_flux_heat.txt` |
| M049 | Convergence | converged at iteration 600, confirmed at 700 (continuity 9.0e-11) | - | CFD-MEDIUM (Section 5B, official baseline) | **REPORTED** | `06_Fluent_CFD/Audit/run_summary.json` |

Notes: the maximum solid temperature is quoted as the **outer-wall facet maximum** (Fluent maximum-of-facet report); the hottest cell centre is also listed. Q = 602.755 W is 8000 W/m² × the inscribed 48-gon area; 603.186 W is the same flux on the true cylinder (Section 2) — both are correct for their geometry.

## 4. CFD mesh study (Section 6A/6B: coarse, fine reference, extrapolated)

| ID | Parameter | Final value | Units | Modelling level | Status | Source file |
|---|---|---|---|---|---|---|
| M050 | fine: cells | 500580 | - | CFD-FINE (Section 6B, verification reference) | **REPORTED** | `09_Mesh_Independence/mesh_study_results.json` |
| M051 | fine: pressure drop | 439.12 | Pa | CFD-FINE (Section 6B, verification reference) | **VERIFIED** | `06_Fluent_CFD/Mesh_Independence/Fine/Audit/fluent_si_p_area.txt` |
| M052 | fine: outlet bulk temperature | 368.85 | K | CFD-FINE (Section 6B, verification reference) | **VERIFIED** | `06_Fluent_CFD/Mesh_Independence/Fine/Audit/fluent_si_T_mass.txt` |
| M053 | fine: heat-transfer rate | 602.994 | W | CFD-FINE (Section 6B, verification reference) | **VERIFIED** | `06_Fluent_CFD/Mesh_Independence/Fine/Audit/fluent_flux_heat.txt` |
| M054 | fine: maximum solid temperature (outer-wall facet) | 560.83 | K | CFD-FINE (Section 6B, verification reference) | **VERIFIED** | `06_Fluent_CFD/Mesh_Independence/Fine/Audit/fluent_si_Twall_max.txt` |
| M055 | fine: through-wall dT mid-span | 7.597 | K | CFD-FINE (Section 6B, verification reference) | **REPORTED** | `09_Mesh_Independence/mesh_study_results.json` |
| M056 | fine: Nu_fd / f_fd | 54.66 / 0.02181 | - | CFD-FINE (Section 6B, verification reference) | **REPORTED** | `09_Mesh_Independence/mesh_study_results.json` |
| M057 | fine: y+ max | 0.653 | - | CFD-FINE (Section 6B, verification reference) | **VERIFIED** | `06_Fluent_CFD/Mesh_Independence/Fine/Audit/fluent_si_yplus_max.txt` |
| M058 | coarse: cells | 51840 | - | CFD-COARSE (Section 6A, mesh study only) | **REPORTED** | `09_Mesh_Independence/mesh_study_results.json` |
| M059 | coarse: pressure drop | 437.09 | Pa | CFD-COARSE (Section 6A, mesh study only) | **VERIFIED** | `06_Fluent_CFD/Mesh_Independence/Coarse/Audit/fluent_si_p_area.txt` |
| M060 | coarse: outlet bulk temperature | 369.12 | K | CFD-COARSE (Section 6A, mesh study only) | **VERIFIED** | `06_Fluent_CFD/Mesh_Independence/Coarse/Audit/fluent_si_T_mass.txt` |
| M061 | coarse: heat-transfer rate | 602.217 | W | CFD-COARSE (Section 6A, mesh study only) | **VERIFIED** | `06_Fluent_CFD/Mesh_Independence/Coarse/Audit/fluent_flux_heat.txt` |
| M062 | coarse: maximum solid temperature (outer-wall facet) | 565.40 | K | CFD-COARSE (Section 6A, mesh study only) | **VERIFIED** | `06_Fluent_CFD/Mesh_Independence/Coarse/Audit/fluent_si_Twall_max.txt` |
| M063 | coarse: through-wall dT mid-span | 7.554 | K | CFD-COARSE (Section 6A, mesh study only) | **REPORTED** | `09_Mesh_Independence/mesh_study_results.json` |
| M064 | coarse: Nu_fd / f_fd | 53.38 / 0.02134 | - | CFD-COARSE (Section 6A, mesh study only) | **REPORTED** | `09_Mesh_Independence/mesh_study_results.json` |
| M065 | coarse: y+ max | 0.522 | - | CFD-COARSE (Section 6A, mesh study only) | **VERIFIED** | `06_Fluent_CFD/Mesh_Independence/Coarse/Audit/fluent_si_yplus_max.txt` |
| M066 | Richardson extrapolated maximum solid temperature | 558.13 | K | CFD-EXTRAPOLATED (Section 6B) | **REPORTED** | `09_Mesh_Independence/mesh_study_results.json` |
| M067 | Richardson extrapolated through-wall dT mid-span | 7.620 | K | CFD-EXTRAPOLATED (Section 6B) | **REPORTED** | `09_Mesh_Independence/mesh_study_results.json` |
| M068 | Richardson extrapolated Nu_fd | 55.43 | - | CFD-EXTRAPOLATED (Section 6B) | **REPORTED** | `09_Mesh_Independence/mesh_study_results.json` |
| M069 | Richardson extrapolated f_fd | 0.02212 | - | CFD-EXTRAPOLATED (Section 6B) | **REPORTED** | `09_Mesh_Independence/mesh_study_results.json` |
| M070 | Richardson extrapolated pressure drop (geometry-adjusted) | 441.81 | Pa | CFD-EXTRAPOLATED (Section 6B) | **REPORTED** | `09_Mesh_Independence/mesh_study_results.json` |

## 5. Section 2 analytical values (historical modelling level, not final results)

| ID | Parameter | Final value | Units | Modelling level | Status | Source file |
|---|---|---|---|---|---|---|
| M071 | heat-transfer rate (true cylinder) | 603.186 | W | ANALYTICAL (Section 2, 1-D correlations; not a CFD/FE result) | **REPORTED** | `02_Engineering_Calculations/baseline_results.csv` |
| M072 | outlet bulk temperature | 368.85 | K | ANALYTICAL (Section 2, 1-D correlations; not a CFD/FE result) | **REPORTED** | `02_Engineering_Calculations/baseline_results.csv` |
| M073 | pressure drop, CFD-comparable | 441.53 | Pa | ANALYTICAL (Section 2, 1-D correlations; not a CFD/FE result) | **REPORTED** | `02_Engineering_Calculations/baseline_results.csv` |
| M074 | maximum solid temperature (outer wall, exit) | 581.71 | K | ANALYTICAL (Section 2, 1-D correlations; not a CFD/FE result) | **REPORTED** | `02_Engineering_Calculations/baseline_results.csv` |
| M075 | through-wall dT (exit station) | 7.285 | K | ANALYTICAL (Section 2, 1-D correlations; not a CFD/FE result) | **REPORTED** | `02_Engineering_Calculations/baseline_results.csv` |
| M076 | free axial growth | 2.0964 | mm | ANALYTICAL (Section 2, 1-D correlations; not a CFD/FE result) | **REPORTED** | `02_Engineering_Calculations/baseline_results.csv` |
| M077 | LC1 peak von Mises (Timoshenko, mid-span) | 16.313 | MPa | ANALYTICAL (Section 2, 1-D correlations; not a CFD/FE result) | **REPORTED** | `02_Engineering_Calculations/baseline_results.csv` |
| M078 | LC2 axial stress (sigma = -E alpha dT_mean) | -657.227 | MPa | ANALYTICAL (Section 2, 1-D correlations; not a CFD/FE result) | **REPORTED** | `02_Engineering_Calculations/baseline_results.csv` |
| M079 | yield strength at 281.6 C | 1023.7 | MPa | ANALYTICAL (Section 2, 1-D correlations; not a CFD/FE result) | **REPORTED** | `02_Engineering_Calculations/baseline_results.csv` |
| M080 | LC2 utilisation | 0.6420 | - | ANALYTICAL (Section 2, 1-D correlations; not a CFD/FE result) | **REPORTED** | `02_Engineering_Calculations/baseline_results.csv` |

## 6. Static structural (Section 7B, official)

| ID | Parameter | Final value | Units | Modelling level | Status | Source file |
|---|---|---|---|---|---|---|
| M081 | Structural nodes | 108252 | - | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC2_Restrained/Solver_Output/s7b_nodal.csv` |
| M082 | Structural elements (SOLID186, quadratic hex) | 23400 | - | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC2_Restrained/Solver_Output/LC2_solve_input_ds.dat` |
| M083 | Reference temperature T_ref | 300 | K | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC2_Restrained/Solver_Output/LC2_solve_input_ds.dat` |
| M084 | LC1 maximum total deformation | 1.8443 | mm | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC1_Free_Expansion/Solver_Output/s7b_nodal.csv` |
| M085 | LC1 free axial growth dL | 1.8409 | mm | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC1_Free_Expansion/Solver_Output/s7b_nodal.csv` |
| M086 | LC1 maximum von Mises stress | 24.282 | MPa | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC1_Free_Expansion/Solver_Output/s7b_nodal.csv` |
| M087 | LC1 critical temperature (at max von Mises) | 427.81 | K | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC1_Free_Expansion/Solver_Output/s7b_nodal.csv` |
| M088 | LC1 reaction resultant | 9.0e-07 | N | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC1_Free_Expansion/Solver_Output/s7b_react.csv` |
| M089 | LC2 maximum total deformation | 0.1349 | mm | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC2_Restrained/Solver_Output/s7b_nodal.csv` |
| M090 | LC2 maximum von Mises stress | 605.161 | MPa | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC2_Restrained/Solver_Output/s7b_nodal.csv` |
| M091 | LC2 end reaction (axial) | 548936.6 | N | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC2_Restrained/Solver_Output/s7b_react.csv` |
| M092 | LC2 mean axial stress | -582.440 | MPa | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC2_Restrained/Solver_Output/s7b_react.csv` |
| M093 | LC2 critical temperature (at max von Mises) | 437.99 | K | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC2_Restrained/Solver_Output/s7b_nodal.csv` |
| M094 | Local yield strength S_y(T) at the critical node | 1047.0 | MPa | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) + VDM 4127 table | **VERIFIED** | `08_Structural_Analysis/LC2_Restrained/Solver_Output/s7b_nodal.csv` |
| M095 | LC2 yield utilisation (max vm / S_y(T)) | 0.5780 | - | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC2_Restrained/Solver_Output/s7b_nodal.csv` |
| M096 | First-yield load factor (1 / utilisation) | 1.730 | - | FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B) | **VERIFIED** | `08_Structural_Analysis/LC2_Restrained/Solver_Output/s7b_nodal.csv` |
| M097 | Pressure effect on LC2 max von Mises (LC2P - LC2) | 45 | Pa | FE-STATIC (Section 7B LC2P, 443.41 Pa bound) | **VERIFIED** | `08_Structural_Analysis/Pressure_Check/Solver_Output/s7b_nodal.csv` |

## 7. Linear buckling and support scenarios

| ID | Parameter | Final value | Units | Modelling level | Status | Source file |
|---|---|---|---|---|---|---|
| M098 | S1 lambda1 | 1.10805 | - | FE-BUCKLING (linear eigenvalue, perfect tube, LC2 thermal pre-stress) | **VERIFIED** | `08_Structural_Analysis/Buckling/Mechanical/LC2_Linear_Buckling/Solver_Output/s8a_load_factors.csv` |
| M099 | S1 critical load P_cr = lambda1 x N | 608.25 | kN | FE-BUCKLING (linear eigenvalue, perfect tube, LC2 thermal pre-stress) | **VERIFIED** | `08_Structural_Analysis/Buckling/Mechanical/LC2_Linear_Buckling/Solver_Output/s8a_load_factors.csv + 08_Structural_Analysis/LC2_Restrained/Solver_Output/s7b_react.csv` |
| M100 | S1 dominant mode | global guided-column sway (ends translate in opposite directions, end rotation held), cos(pi z/L) | - | FE-BUCKLING (linear eigenvalue, perfect tube, LC2 thermal pre-stress) | **REPORTED** | `08_Structural_Analysis/Buckling/fe_modes_8A.json` |
| M101 | S2 lambda1 | 4.29995 | - | FE-BUCKLING (linear eigenvalue, perfect tube, LC2 thermal pre-stress) | **VERIFIED** | `08_Structural_Analysis/Buckling/Mechanical/LC2NS_Linear_Buckling/Solver_Output/s8a_load_factors.csv` |
| M102 | S2 critical load P_cr = lambda1 x N | 2360.40 | kN | FE-BUCKLING (linear eigenvalue, perfect tube, LC2 thermal pre-stress) | **VERIFIED** | `08_Structural_Analysis/Buckling/Mechanical/LC2NS_Linear_Buckling/Solver_Output/s8a_load_factors.csv + 10_Parametric_Study/Structural_Cases/S2_REEXTRACT/s2x_totals.txt` |
| M103 | S2 dominant mode | global clamped-clamped column, 1 - cos(2 pi z/L) | - | FE-BUCKLING (linear eigenvalue, perfect tube, LC2 thermal pre-stress) | **REPORTED** | `08_Structural_Analysis/Buckling/fe_modes_8A.json` |
| M104 | S3 lambda1 | 2.23224 | - | FE-BUCKLING (linear eigenvalue, perfect tube, LC2 thermal pre-stress) | **VERIFIED** | `10_Parametric_Study/Structural_Cases/S3_LC2_INTERMEDIATE/Solver_Output/S3_BUCKLING/s8a_load_factors.csv` |
| M105 | S3 critical load P_cr = lambda1 x N | 1225.36 | kN | FE-BUCKLING (linear eigenvalue, perfect tube, LC2 thermal pre-stress) | **VERIFIED** | `10_Parametric_Study/Structural_Cases/S3_LC2_INTERMEDIATE/Solver_Output/S3_BUCKLING/s8a_load_factors.csv + 10_Parametric_Study/Structural_Cases/S3_LC2_INTERMEDIATE/Solver_Output/S3_STATIC/s7b_react.csv` |
| M106 | S3 dominant mode | global fixed-pinned column, max lateral at 0.605 L | - | FE-BUCKLING (linear eigenvalue, perfect tube, LC2 thermal pre-stress) | **REPORTED** | `10_Parametric_Study/Results/Data/post_9B2_results.json` |
| M107 | S1 lambda2 / lambda3 | 1.10805 / 4.2979 | - | FE-BUCKLING (linear eigenvalue, perfect tube, LC2 thermal pre-stress) | **REPORTED** | `08_Structural_Analysis/Buckling/Mechanical/LC2_Linear_Buckling/Solver_Output/s8a_load_factors.csv` |

## 7b. Support sensitivity (static)

| ID | Parameter | Final value | Units | Modelling level | Status | Source file |
|---|---|---|---|---|---|---|
| M108 | S2 static max von Mises (re-extracted) | 605.160 | MPa | FE-STATIC (8A LC2NS) | **VERIFIED** | `10_Parametric_Study/Structural_Cases/S2_REEXTRACT/s2x_nodal.csv` |
| M109 | S3 static max von Mises | 605.160 | MPa | FE-STATIC (9B-2 S3) | **VERIFIED** | `10_Parametric_Study/Structural_Cases/S3_LC2_INTERMEDIATE/Solver_Output/S3_STATIC/s7b_nodal.csv` |
| M110 | S1 / S2 / S3 axial reaction | 548936.6 / 548936.6 / 548936.7 | N | FE-STATIC | **REPORTED** | `reaction tables (7B LC2, 8A LC2NS, 9B-2 S3)` |

## 8. Structural mesh sensitivity (Section 8B)

| ID | Parameter | Final value | Units | Modelling level | Status | Source file |
|---|---|---|---|---|---|---|
| M111 | XC: LC2 max von Mises | 604.867 | MPa | FE-MESH-STUDY (Section 8B) | **VERIFIED** | `08_Structural_Analysis/Mesh_Study/Variants/XC/Solver_Output/LC2/s7b_nodal.csv` |
| M112 | XC: lambda1 | 1.10799 | - | FE-MESH-STUDY (Section 8B) | **VERIFIED** | `08_Structural_Analysis/Mesh_Study/Variants/XC/Solver_Output/BUCKLING/s8a_load_factors.csv` |
| M113 | C: LC2 max von Mises | 605.096 | MPa | FE-MESH-STUDY (Section 8B) | **VERIFIED** | `08_Structural_Analysis/Mesh_Study/Variants/C/Solver_Output/LC2/s7b_nodal.csv` |
| M114 | C: lambda1 | 1.10803 | - | FE-MESH-STUDY (Section 8B) | **VERIFIED** | `08_Structural_Analysis/Mesh_Study/Variants/C/Solver_Output/BUCKLING/s8a_load_factors.csv` |
| M115 | B: LC2 max von Mises | 605.161 | MPa | FE-MESH-STUDY (Section 8B) | **VERIFIED** | `08_Structural_Analysis/Mesh_Study/Variants/B/Solver_Output/LC2/s7b_nodal.csv` |
| M116 | B: lambda1 | 1.10805 | - | FE-MESH-STUDY (Section 8B) | **VERIFIED** | `08_Structural_Analysis/Mesh_Study/Variants/B/Solver_Output/BUCKLING/s8a_load_factors.csv` |
| M117 | FR: LC2 max von Mises | 605.220 | MPa | FE-MESH-STUDY (Section 8B) | **VERIFIED** | `08_Structural_Analysis/Mesh_Study/Variants/FR/Solver_Output/LC2/s7b_nodal.csv` |
| M118 | FR: lambda1 | 1.10804 | - | FE-MESH-STUDY (Section 8B) | **VERIFIED** | `08_Structural_Analysis/Mesh_Study/Variants/FR/Solver_Output/BUCKLING/s8a_load_factors.csv` |
| M119 | FA: LC2 max von Mises | 605.140 | MPa | FE-MESH-STUDY (Section 8B) | **VERIFIED** | `08_Structural_Analysis/Mesh_Study/Variants/FA/Solver_Output/LC2/s7b_nodal.csv` |
| M120 | FA: lambda1 | 1.10805 | - | FE-MESH-STUDY (Section 8B) | **VERIFIED** | `08_Structural_Analysis/Mesh_Study/Variants/FA/Solver_Output/BUCKLING/s8a_load_factors.csv` |
| M121 | FC: LC2 max von Mises | 605.170 | MPa | FE-MESH-STUDY (Section 8B) | **VERIFIED** | `08_Structural_Analysis/Mesh_Study/Variants/FC/Solver_Output/LC2/s7b_nodal.csv` |
| M122 | FC: lambda1 | 1.10804 | - | FE-MESH-STUDY (Section 8B) | **VERIFIED** | `08_Structural_Analysis/Mesh_Study/Variants/FC/Solver_Output/BUCKLING/s8a_load_factors.csv` |
| M123 | IL: LC2 max von Mises | 605.134 | MPa | FE-MESH-STUDY (Section 8B) | **VERIFIED** | `08_Structural_Analysis/Mesh_Study/Variants/IL/Solver_Output/LC2/s7b_nodal.csv` |
| M124 | max /change/ vs mesh B: LC2 peak / lambda1 | 4.9e-04 / 5.4e-05 | - | FE-MESH-STUDY (Section 8B) | **VERIFIED** | `recomputed above` |

## 9. Parametric cases (9B-1 CFD + 9B-2 FE, S1 supports; actual simulations, not screening)

| Case | Δp [Pa] | T_out [K] | T_max [K] | LC1 def. [mm] | LC1 VM [MPa] | LC2 VM [MPa] | λ₁ | P_cr [kN] | Utilisation |
|---|---|---|---|---|---|---|---|---|---|
| **P00 (baseline)** | 438.13 | 368.93 | 562.58 | 1.8443 | 24.282 | 605.161 | 1.10805 | 608.25 | 0.5780 |
| V01 (V 21.15 m/s) | 379.93 | 376.56 | 587.47 | 2.0375 | 24.925 | 663.001 | 1.00307 | 604.14 | 0.6347 |
| V03 (V 25.85 m/s) | 499.69 | 362.69 | 542.10 | 1.6874 | 23.532 | 557.544 | 1.21087 | 611.53 | 0.5315 |
| Q01 (q'' 7,200 W/m²) | 419.74 | 362.06 | 534.45 | 1.6284 | 21.704 | 538.526 | 1.25464 | 612.79 | 0.5129 |
| Q03 (q'' 8,800 W/m²) | 456.64 | 375.79 | 591.13 | 2.0680 | 26.649 | 673.024 | 0.98834 | 603.45 | 0.6446 |
| T01 (t 8 mm, D_o 36) | 438.11 | 368.93 | 561.97 | 1.8355 | 20.872 | 602.309 | 0.94497 | 385.73 | 0.5743 |
| T03 (t 12 mm, D_o 44) | 438.14 | 368.93 | 563.07 | 1.8528 | 27.206 | 607.735 | 1.28702 | 907.89 | 0.5813 |

All 54 parametric values above are VERIFIED (recomputed from each case's Fluent reports and MAPDL tables). λ₁ < 1: **Q03, T01** (Part I label: pre-buckling equilibrium result; linear stability criterion indicates loss of stability before the applied load level); **V01** is 0.31 % above 1.

## 10. Interpretation rows

| ID | Parameter | Final value | Units | Modelling level | Status | Source file |
|---|---|---|---|---|---|---|
| M179 | Buckling interpretation (all scenarios) | lambda1 is a LINEAR EIGENVALUE bifurcation indicator of an ideal, perfectly straight tube with idealised supports; no imperfection, no plasticity, no large deflection; it is NOT a collapse load and NOT a factor of safety | - | INTERPRETATION | **INTERPRETATION** | `08_Structural_Analysis/Buckling/BUCKLING_RESULTS.md` |
| M180 | S1 governing mechanism (idealised model) | lambda1 1.108 < first-yield factor 1.730: elastic bifurcation of the idealised S1 model comes before first yield (stability-limited); lambda1 this close to 1 means the idealised model is close to instability | - | INTERPRETATION | **INTERPRETATION** | `master rows S1 lambda1 and first-yield factor` |
| M181 | S2 / S3 governing mechanism (idealised model) | first-yield factor 1.730 < lambda1 (S3 2.232, S2 4.300): first yield (or inelastic buckling, 8A Johnson 1.41 / 1.58) comes before the elastic bifurcation | - | INTERPRETATION | **INTERPRETATION** | `master rows S2/S3 lambda1 and first-yield factor` |
| M182 | Cases with lambda1 < 1 (S1) | Q03 (0.98834) and T01 (0.94497): LC2 static stress = pre-buckling equilibrium result; linear stability criterion indicates loss of stability before the applied load level. V01 (1.00307) is 0.31 % above 1 | - | INTERPRETATION | **INTERPRETATION** | `10_Parametric_Study/Results/PARAMETRIC_STRUCTURAL_RESULTS.md` |

