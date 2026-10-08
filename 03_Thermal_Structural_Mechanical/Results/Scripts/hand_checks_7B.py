# -*- coding: utf-8 -*-
"""SECTION 7B - small hand checks used to EXPLAIN the FE results (RE-ANALYSIS 2026). Not FE results; indicative only.
Inputs: geometry and datasheet tables (Section 2 / 7A), FE values from out/post_7B_results.json."""
import json, math, os
import numpy as np
R = json.load(open(os.path.join(os.environ.get("S7B_OUT", "<OUTPUT_ROOT>/S7B/Post/out"), "post_7B_results.json")))
ri, ro, L, nu = 0.010, 0.020, 0.600, 0.294
A = math.pi * (ro**2 - ri**2); I = math.pi / 4 * (ro**4 - ri**4); rg = math.sqrt(I / A)
E_T = [20, 100, 200, 300, 400]; E_V = [204e9, 199e9, 193e9, 187e9, 180e9]
SY_T = [20, 100, 200, 300, 400]; SY_V = [1030e6, 1060e6, 1040e6, 1020e6, 1000e6]
H = {"note": "RE-ANALYSIS 2026 - indicative hand checks for interpretation; NOT finite-element results"}
# 1. Section 2 LC1 (16.31 MPa) re-evaluated with the CFD mid-span wall: factor decomposition
m = R["LC1_midspan_vs_timoshenko"]
H["LC1_section2_factors"] = {"dT_ratio": m["dT_wall_K"] / 7.28, "alpha_tangent_over_section2_secant": m["alpha_used"] / 13.72e-6,
                             "E_ratio": m["E_used_Pa"] / 188.1e9,
                             "section2_rescaled_MPa": 16.31 * m["dT_wall_K"] / 7.28 * m["alpha_used"] / 13.72e-6 * m["E_used_Pa"] / 188.1e9,
                             "timoshenko_CFD_bore_hoop_MPa": m["timoshenko_bore"]["s_t"] / 1e6, "FE_bore_hoop_MPa": m["FE_bore"]["s_t"] / 1e6}
# 2. LC2/LC1 ratio
pk1 = R["extremes"]["LC1"]["von_mises_Pa"]["max"]; pk2 = R["extremes"]["LC2"]["von_mises_Pa"]["max"]
mid2 = R["LC2_profile_summary"]["midspan"]["seqv_outer_Pa"]; mid1 = m["FE_bore"]["vm"]
H["LC2_over_LC1"] = {"peak_over_peak": pk2 / pk1, "midspan_max_over_midspan_max": mid2 / mid1, "section2": 40.3, "expected_band": [30, 50]}
# 3. local temperature-transfer uncertainty in the inlet zone (F-035: up to 2.57 K at the bore, z ~ 3 mm) -> bound on local stress
Tc = R["utilisation"]["LC1"]["at_max_vm"]["loc"]["T_C"]
E = float(np.interp(Tc, E_T, E_V)); a_tan = 13.8e-6
H["F035_local_bound"] = {"dT_K": 2.57, "E_Pa": E, "alpha_tan": a_tan,
                         "bound_MPa": E * a_tan * 2.57 / (1 - nu) / 1e6,
                         "meaning": "stress change if a 2.57 K local temperature error were fully constrained (E alpha dT/(1-nu)); an upper bound, not a computed value"}
# 4. stability: LC2 carries a uniform compressive force. Linear static FE does not assess buckling.
N = abs(R["LC2_axial"]["FE_reaction_inlet_Fz_N"]); s_app = N / A
Th = 562.5 - 273.15
Eh = float(np.interp(Th, E_T, E_V)); Sy = float(np.interp(Th, SY_T, SY_V))
out = {}
for lab, K in (("ends clamped, no lateral sway (K = 0.5)", 0.5), ("ends clamped, lateral sway free (K = 1.0)", 1.0)):
    lam = K * L / rg
    sE = math.pi**2 * Eh / lam**2
    lam_t = math.sqrt(2 * math.pi**2 * Eh / Sy)
    scr = sE if lam > lam_t else Sy - (Sy**2 / (4 * math.pi**2 * Eh)) * lam**2
    out[lab] = {"slenderness": lam, "euler_MPa": sE / 1e6, "johnson_transition_slenderness": lam_t, "critical_MPa": scr / 1e6,
                "ratio_to_applied": scr / s_app}
H["buckling_indicative"] = {"applied_mean_stress_MPa": s_app / 1e6, "N_kN": N / 1e3, "radius_of_gyration_mm": rg * 1e3,
                            "E_hot_Pa": Eh, "Sy_hot_Pa": Sy, "cases": out,
                            "note": "hand estimate with hot-end properties (lowest E and S_y); Euler/Johnson, perfect straight tube; the LC2 FE end faces are free to translate laterally (only U_z held), the 3 mid-span hoop nodes hold the mid-section. Needs an eigenvalue buckling analysis with the real end conditions."}
# 5. small-deflection validity
H["small_deflection"] = {"max_total_deformation_LC1_mm": R["extremes"]["LC1"]["total_deformation_m"]["max"] * 1e3,
                         "max_elastic_strain_LC2": R["extremes"]["LC2"]["equiv_elastic_strain"]["max"], "wall_mm": 10.0}
json.dump(H, open(os.path.join(os.environ.get("S7B_OUT", "<OUTPUT_ROOT>/S7B/Post/out"), "hand_checks_7B.json"), "w"), indent=1)
print(json.dumps(H, indent=1))
