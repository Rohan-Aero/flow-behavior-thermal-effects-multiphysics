# -*- coding: utf-8 -*-
"""SECTION 9A - independent check of the parametric plan (RE-ANALYSIS 2026).
Written separately from parametric_screening.py and support_sensitivity_hand.py. It re-derives key screening numbers
with plain closed-form expressions (not the marching model), checks mesh/licence arithmetic, the case matrix file and
the support references against the solved 8A files. Every check prints PASS/FAIL.
Usage: python verify_9A.py <10_Parametric_Study_dir> <project_root> <out_json>"""
import os, sys, json, csv, math, re
S9, ROOT, OUTJ = sys.argv[1], sys.argv[2], sys.argv[3]
res = []


def chk(name, ok, detail):
    res.append({"check": name, "pass": bool(ok), "detail": detail}); print("PASS" if ok else "FAIL", name, "|", detail)


SR = json.load(open(os.path.join(S9, "Analytical_Screening", "screening_results.json")))
M = {r["case"]: r for r in SR["matrix"]}
# 1. Reynolds number and mass flow from first principles (air at 300 K, p/(RT), Incropera mu)
rho, mu, D = 101325 / (287.058 * 300), 1.846e-5, 0.02
for c, V in (("P00_BASELINE", 23.5), ("V01_LOW", 21.15), ("V03_HIGH", 25.85)):
    Re = rho * V * D / mu
    chk("%s: Re_in = rho V D / mu" % c, abs(Re / M[c]["Re_in"] - 1) < 1e-4, "%.1f vs %.1f" % (Re, M[c]["Re_in"]))
# 2. heat input and outlet temperature by energy balance (cp at the mean bulk temperature)
for c, q, Do in (("Q01_LOW", 7200, 0.04), ("Q03_HIGH", 8800, 0.04), ("T01_THIN", 8000 * 0.04 / 0.036, 0.036), ("T03_THICK", 8000 * 0.04 / 0.044, 0.044)):
    Q = q * math.pi * Do * 0.6
    chk("%s: Q = q'' pi Do L" % c, abs(Q / M[c]["Q_W"] - 1) < 1e-6, "%.3f W vs %.3f W" % (Q, M[c]["Q_W"]))
mdot = rho * 23.5 * math.pi * 0.01 ** 2
for c in ("Q01_LOW", "Q03_HIGH"):
    Q = M[c]["Q_W"]; Tout = 300 + Q / (mdot * 1008.5)
    chk("%s: T_out by energy balance (cp 1008.5) within 0.5 K of the marching model" % c, abs(Tout - M[c]["T_out_K"]) < 0.5, "%.2f vs %.2f K" % (Tout, M[c]["T_out_K"]))
# 3. thickness cases: lambda ratio = r_g^2 ratio x (sigma ratio)^-1 ; sigma unchanged to 0.3 %
rg2 = lambda Do: (Do ** 2 + 0.02 ** 2) / 16
for c, Do in (("T01_THIN", 0.036), ("T03_THICK", 0.044)):
    lam = 1.108047 * rg2(Do) / rg2(0.04)
    chk("%s: lambda1(S1) ~ r_g^2 scaling within 1 %%" % c, abs(lam / M[c]["anch_lambda1_S1"] - 1) < 0.01, "%.4f vs %.4f" % (lam, M[c]["anch_lambda1_S1"]))
# 4. operating cases: lambda ~ 1/N (E I nearly unchanged) within 2 %
for c in ("V01_LOW", "V03_HIGH", "Q01_LOW", "Q03_HIGH"):
    lam = 1.108047 * 548.9366 / M[c]["anch_LC2_N_kN"]
    chk("%s: lambda1 ~ 1/N within 2 %%" % c, abs(lam / M[c]["anch_lambda1_S1"] - 1) < 0.02, "%.4f vs %.4f" % (lam, M[c]["anch_lambda1_S1"]))
# 5. mesh / licence arithmetic
nodes = lambda nc, nr, na: nc * ((nr + 1) * (na + 1) * 2 + nr * (na + 1) + (nr + 1) * na)
for lab, (nc, nr, na), exp, fits in (("T01 FE 36x4x130", (36, 4, 130), 89424, True), ("T03 FE 36x6x130", (36, 6, 130), 127080, True),
                                     ("t = 14 mm FE 36x7x130", (36, 7, 130), 145908, False), ("M01/M02 FE 36x5x130", (36, 5, 130), 108252, True)):
    n = nodes(nc, nr, na)
    chk("%s: nodes %d, fits 128,000 = %s" % (lab, exp, fits), n == exp and (n < 128000) == fits, "%d" % n)


def layers(t, h1=0.5e-3, gmax=1.1470001):
    for n in range(2, 40):
        lo, hi = 1.0000001, 3.0
        for _ in range(200):
            g = 0.5 * (lo + hi)
            s = h1 * (g ** n - 1) / (g - 1)
            lo, hi = (g, hi) if s < t else (lo, g)
        if g <= gmax:
            return n, g
for t, n_exp in ((0.008, 9), (0.010, 10), (0.012, 12)):
    n, g = layers(t)
    chk("CFD solid layers for t = %.0f mm (first 0.5 mm, growth <= 1.147)" % (t * 1e3), n == n_exp, "n %d, g %.4f" % (n, g))
chk("CFD cell counts T01 / T03 / M03", 116640 + 9 * 48 * 90 == 155520 and 116640 + 12 * 48 * 90 == 168480 and 116640 + 18 * 48 * 90 == 194400, "155,520 / 168,480 / 194,400")
# 6. y+ scaling ~ V^0.9 cross-check
for c, V in (("V01_LOW", 21.15), ("V03_HIGH", 25.85)):
    yp = 0.58484 * (V / 23.5) ** 0.9
    chk("%s: y+ max ~ V^0.9 within 2 %% of the screening estimate, and <= 0.8" % c, abs(yp / M[c]["anch_yplus_max"] - 1) < 0.02 and M[c]["anch_yplus_max"] <= 0.8, "%.3f vs %.3f" % (yp, M[c]["anch_yplus_max"]))
# 7. validity: every proposed design case valid, air <= 590 K; rejected candidates flagged
for c in ("V01_LOW", "V03_HIGH", "Q01_LOW", "Q03_HIGH", "T01_THIN", "T03_THICK"):
    chk("%s: no INVALID flag, near-wall air <= 590 K, solid <= 663 K" % c, M[c]["valid"] and M[c]["anch_T_interface_max_K"] <= 590 and M[c]["anch_T_solid_max_K"] <= 663,
        "%.1f K / %.1f K" % (M[c]["anch_T_interface_max_K"], M[c]["anch_T_solid_max_K"]))
CA = {r["case"]: r for r in SR["candidates"]}
for c in ("cand_V_0.800", "cand_Q_9500", "cand_Q_10000", "corner_Vlow_Qhigh"):
    chk("%s is rejected (INVALID)" % c, not CA[c]["valid"], CA[c]["flags"][:60])
chk("self-check vs Section 2 reproduced", all(v["ok"] for v in SR["selfcheck_section2"].values()), "8 quantities")
# 8. case matrix file
rows = list(csv.DictReader(open(os.path.join(S9, "Case_Matrix", "PARAMETRIC_CASE_MATRIX.csv"), encoding="utf-8")))
req = ["Case", "Parameter", "Value", "Units", "Geometry change?", "Mesh change?", "CFD required?", "Mechanical required?", "Expected trend", "Reason", "Status"]
chk("matrix: required columns in order", list(rows[0].keys()) == req, ", ".join(rows[0].keys()))
pat = re.compile(r"^[PCVQTMSB]\d{2}_[A-Z0-9_]+$|^S[123]_LC2_[A-Z_]+$")
chk("matrix: every case name follows the convention", all(pat.match(r["Case"]) for r in rows), "%d rows" % len(rows))
n_cfd = sum(1 for r in rows if r["CFD required?"].startswith("Yes"))
chk("matrix: 8 new Fluent runs", n_cfd == 8, "%d" % n_cfd)
mech = 0
for r in rows:
    m = r["Mechanical required?"]
    if m.startswith("Yes (LC1, LC2, BK-S1"):
        mech += 3
    elif m.startswith("Yes (LC2 static + BK)"):
        mech += 2
chk("matrix: 29 Mechanical analyses (+ 1 MAPDL benchmark)", mech == 29 and any("MAPDL" in r["Mechanical required?"] for r in rows), "%d" % mech)
chk("matrix: P00 is the solved reference; aliases point to P00", rows[0]["Case"] == "P00_BASELINE" and all("alias" in r["Status"].lower() for r in rows if r["Case"][3:] == "_BASELINE" and r["Case"] != "P00_BASELINE"), "")
# 9. support references = solved 8A files
def lf(p):
    return [float(l.split(",")[1]) for l in open(p).read().splitlines()[1:] if l.strip()]
B8 = os.path.join(ROOT, "08_Structural_Analysis", "Buckling", "Mechanical")
l1 = lf(os.path.join(B8, "LC2_Linear_Buckling", "Solver_Output", "s8a_load_factors.csv"))[0]
l2 = lf(os.path.join(B8, "LC2NS_Linear_Buckling", "Solver_Output", "s8a_load_factors.csv"))[0]
H = json.load(open(os.path.join(S9, "Support_Sensitivity", "support_sensitivity_hand.json")))
chk("S1 / S2 lambda1 in the support study = 8A solver files", abs(H["P_S1_FE_kN"] * 1e3 / H["N_N"] - l1) < 1e-6 and abs(H["P_S2_FE_kN"] * 1e3 / H["N_N"] - l2) < 1e-5,
    "S1 %.6f (8A %.6f), S2 %.5f (8A %.5f)" % (H["P_S1_FE_kN"] * 1e3 / H["N_N"], l1, H["P_S2_FE_kN"] * 1e3 / H["N_N"], l2))
BF = json.load(open(os.path.join(S9, "Support_Sensitivity", "support_spring_check_beamFE.json")))
chk("required-stiffness formula confirmed by the independent beam FE", BF["all_ok"], "%d targets" % len(BF["checks"]))
out = {"summary": "%d/%d PASS" % (sum(r["pass"] for r in res), len(res)), "checks": res}
json.dump(out, open(OUTJ, "w"), indent=1)
print(out["summary"])
