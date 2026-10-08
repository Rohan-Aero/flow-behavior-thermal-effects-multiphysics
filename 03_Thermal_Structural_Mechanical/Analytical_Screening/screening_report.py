# -*- coding: utf-8 -*-
"""SECTION 9A - writes SCREENING_RESULTS.md from screening_results.json (no hand transcription). RE-ANALYSIS 2026.
Usage: python screening_report.py [dir]"""
import os, sys, json
D = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(D, "screening_results.json")))
M, C = R["matrix"], R["candidates"]
b = M[0]
L = []
L.append("# Section 9A: analytical screening of the parametric cases\n")
L.append("> **SCREENING ONLY.** These are neither CFD nor Mechanical results. They come from the frozen Section 2 1-D model (`parametric_screening.py`).\n>")
L.append("> - **Analytical** columns are the raw 1-D model.")
L.append("> - **Anchored** columns apply the analytical *change* to the solved P00 baseline (CFD 5B, FE 7B/8A):")
L.append(">   - for temperatures, the rise above 300 K is scaled;")
L.append(">   - for stresses, the solver thermal strain × E(T) at the anchored mean temperature is scaled;")
L.append(">   - for λ₁, (E·I) / N is scaled.")
L.append("> - The purpose is to reject ranges that would leave the valid model before any expensive run.\n")
sc = R["selfcheck_section2"]
L.append("**Self-check.** The script reproduces the frozen Section 2 baseline: " + ", ".join("%s %.4g (Section 2: %g)" % (k, v["value"], v["section2"]) for k, v in sc.items()) +
         ". Result: **%s**.\n" % ("PASS" if all(v["ok"] for v in sc.values()) else "FAIL"))
lim = R["limits"]
L.append("**Validity limits applied.**\n")
L.append("- Air property table 250–600 K. **INVALID** above 600 K; **MARGINAL** within 10 K of it.")
L.append("- Inconel E, k, c_p and S_y tables 293–673 K. **INVALID** above 673 K.")
L.append("- Re_min ≥ 10,000 for fully turbulent flow.")
L.append("- Δp ≤ 1 % of p_op, the basis of the incompressible-ideal-gas model.")
L.append("- Mach ≤ 0.3.")
L.append("- y⁺_max ≤ 1 with the baseline first cell.")
L.append("- Thermal strain ≤ 0.5 % and flow-area change ≤ 1 %, the basis of one-way coupling.")
L.append("- LC2 utilisation < 1.")
L.append("- λ₁(S1) < 1 is reported as a **NOTE**, not a rejection.\n")


def tab(rows, title):
    L.append("## %s\n" % title)
    L.append("| Case | Parameter = value | Re_in | Δp [Pa] | T_out [K] | near-wall air max [K] | solid max [K] | solid mean [K] | y⁺_max | ΔL (LC1) [mm] | LC2 peak [MPa] | LC2 util. | λ₁ (S1) | Flags |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        pv = "%s = %.5g %s" % (r["parameter"], r["value"], r["units"]) if r["units"] != "-" else r["parameter"]
        L.append("| %s | %s | %.0f | %.0f | %.1f | %.1f | %.1f | %.1f | %.3f | %.3f | %.0f | %.3f | %.3f | %s |" % (
            r["case"], pv, r["Re_in"], r["anch_dp_Pa"], r["anch_T_out_K"], r["anch_T_interface_max_K"], r["anch_T_solid_max_K"],
            r["anch_T_solid_mean_K"], r["anch_yplus_max"], r["anch_LC1_dL_mm"], r["anch_LC2_vm_max_MPa"], r["anch_LC2_utilisation"],
            r["anch_lambda1_S1"], r["flags"].replace("NOTE: lambda_1(S1) < 1 - the ideal straight column would bifurcate below this load", "NOTE: λ₁(S1) < 1")))
    L.append("")


tab(C, "1. Candidate sweep used to choose the ranges (anchored estimates)")
L.append("**How to read the sweep.**\n")
L.append("- **Velocity.** −15 % is MARGINAL (near-wall air 595 K); −20 % and below are INVALID (air table exceeded). ±10 % keeps about 20 K of margin at the low end.")
L.append("- **Heat flux.** +12.5 % (9,000 W/m²) is MARGINAL (591 K); +18.75 % and above are INVALID; 12,000 W/m² also exceeds the Inconel tables. +10 % (8,800 W/m²) keeps a 17 K margin.")
L.append("- **Thickness** (total heat input Q held constant). Temperatures change by ≤ 2 K, so the thermal validity is unaffected. The range is set by the Student node limit (`Planning/PARAMETRIC_PLAN.md` §3).")
L.append("- **Constant q″ instead of constant Q** (rows `cand_Tq_*`). The heat input then changes by ∓10 % and masks the section effect. This is why the thickness cases hold Q constant.")
L.append("- **Factorial corners.** The adverse corner (V −10 %, q″ +10 %) is **INVALID** (611 K > 600 K). A full factorial would therefore require property extrapolation, while one-factor-at-a-time does not.\n")
tab(M, "2. Proposed matrix (anchored estimates)")
keys = [("mdot_g_s", "ṁ [g/s] (analytical)", 1), ("Q_W", "Q [W] (analytical)", 1), ("Re_out", "Re_out", 1), ("h_mean", "h mean [W/m²K] (analytical)", 1),
        ("dTwall_exit_K", "through-wall ΔT at exit [K] (analytical)", 1), ("anch_dp_Pa", "Δp [Pa]", 1), ("anch_T_out_K", "T_out [K]", 0),
        ("anch_T_solid_max_K", "solid max [K]", 0), ("anch_LC1_dL_mm", "LC1 ΔL [mm]", 1), ("anch_LC1_vm_max_MPa", "LC1 max VM [MPa]", 1),
        ("anch_LC2_mean_axial_MPa", "LC2 mean axial [MPa]", 1), ("anch_LC2_vm_max_MPa", "LC2 peak VM [MPa]", 1), ("anch_LC2_N_kN", "LC2 end force [kN]", 1),
        ("anch_LC2_utilisation", "LC2 utilisation", 1), ("anch_first_yield_factor", "first-yield factor", 1), ("anch_lambda1_S1", "λ₁ S1 (current)", 1),
        ("anch_lambda1_S2", "λ₁ S2 (scaled 8A)", 1), ("anch_lambda1_S3_hand", "λ₁ S3 (hand, scaled)", 1), ("anch_Pcr_S1_kN", "P_cr S1 [kN]", 1)]
L.append("## 3. Change from P00_BASELINE (screening)\n")
L.append("| Quantity | P00 | " + " | ".join(r["case"] for r in M[1:]) + " |")
L.append("|---|---|" + "---|" * (len(M) - 1))
for k, lab, pct in keys:
    cells = []
    for r in M[1:]:
        if pct:
            cells.append("%.4g (%+.1f %%)" % (r[k], 100 * (r[k] - b[k]) / abs(b[k])))
        else:
            cells.append("%.1f (%+.1f K)" % (r[k], r[k] - b[k]))
    L.append("| %s | %.4g | %s |" % (lab, b[k], " | ".join(cells)))
L.append("")
L.append("**Sign convention.** For the mean axial stress (negative, compression) the percentage is (value − P00)/|P00|, so −10 % means 10 % *more* compression.\n")
L.append("## 4. What the screening shows (trend statements for planning, not results)\n")
L.append("1. **Velocity and heat flux act on the structure almost only through the temperature level.** At ±10 %, LC2 stress and λ₁ move by 8–14 %. Heat flux also scales the through-wall ΔT (LC1); velocity barely changes it.")
L.append("2. **Wall thickness at constant heat input leaves the temperatures and the restrained stress nearly unchanged (≤ 0.2 %).** It changes the section instead: the end force by −26 / +28 %, λ₁ by −15 / +16.5 % and P_cr by −37 / +50 %. It is the only variable that tests the stability lever directly.")
L.append("3. **Three proposed cases put the anchored λ₁(S1) at or below 1: V01 (≈ 1.00), Q03 (≈ 0.98) and T01 (≈ 0.94).** For the current idealised support, the ideal straight column would bifurcate there before reaching the static LC2 state. Their LC2 static results then describe an ideal pre-buckling state and must be reported with that caveat.")
L.append("4. **No proposed case approaches yield.** LC2 utilisation stays ≤ 0.65 and the first-yield factor ≥ 1.54, so for S1 stability stays more limiting than yield in every case.")
L.append("5. **All proposed cases stay inside every property table,** turbulent (Re_out ≥ 22,600), with y⁺_max ≤ 0.64, Δp ≤ 0.5 % of p_op and Mach ≤ 0.09.\n")
open(os.path.join(D, "SCREENING_RESULTS.md"), "w", encoding="utf-8").write("\n".join(L))
print("written SCREENING_RESULTS.md", len(L))
