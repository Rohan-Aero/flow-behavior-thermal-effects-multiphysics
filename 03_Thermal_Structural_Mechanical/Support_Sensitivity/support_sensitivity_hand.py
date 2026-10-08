# -*- coding: utf-8 -*-
"""
SECTION 9A - support / end-restraint scenarios: hand estimates for PLANNING (RE-ANALYSIS 2026)

NOT a finite-element result. It combines
  (a) the solved Section 8A values (FE lambda_1 for S1 and S2, hand Euler/Johnson for every end condition), and
  (b) classical beam-column theory for a column whose ends are held against rotation and joined by a
      LATERAL spring k (relative sway stiffness). This does NOT assume a support stiffness: it answers
      "what lateral stiffness would be REQUIRED to move lambda_1 from the sway value towards the no-sway value?"

Sway branch (ends rotation-fixed, relative lateral translation resisted by spring k), exact for a prismatic column:
    w'''' + a^2 w'' = 0,  a^2 = P/EI;  BCs w(0)=w'(0)=w'(L)=0,  EI w'''(L) + P w'(L) = shear balance with k w(L)
    ->  k = EI a^3 / (2 (u - tan u)),   u = aL/2 in (pi/2, pi)
    k -> 0 gives aL = pi (K = 1, sway);  the branch reaches the no-sway (symmetric, clamped) load when
    k = 4 pi^2 EI / L^3 (Euler) - beyond that the no-sway mode governs and k no longer matters.
EI is CALIBRATED to the solved FE sway load (P_S1 = lambda_1,S1 * N), so shear and E(z) effects of the real model
are carried implicitly; the no-sway limit is the solved FE value (lambda_1,S2 * N).
Usage: python support_sensitivity_hand.py [out_dir]
"""
import os, sys, json, math
import numpy as np
from scipy.optimize import brentq

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
L = 0.600
N = 548936.6137530407                 # LC2 end reaction (8A)
LAM_S1, LAM_S2 = 1.10804700, 4.29995  # 8A FE (official)
FIRST_YIELD = 1 / 0.578               # 7B utilisation 0.578 -> ~1.73
HAND = {  # 8A buckling_hand_results.json (Euler with E(z) Rayleigh; + shear; Johnson hot-end S_y/E)
    "guided (S1)": {"K": 1.0, "euler": 1.11938, "euler_shear": 1.10359, "johnson": 1.058},
    "pinned-pinned": {"K": 1.0, "euler": 1.11424, "euler_shear": 1.09852, "johnson": 1.058},
    "fixed-pinned, cold end fixed (S3)": {"K": 0.6992, "euler": 2.28580, "euler_shear": 2.22079, "johnson": 1.414},
    "fixed-fixed, no sway (S2)": {"K": 0.5, "euler": 4.47113, "euler_shear": 4.22903, "johnson": 1.581},
}
P_S1, P_S2 = LAM_S1 * N, LAM_S2 * N
EI = P_S1 * L ** 2 / math.pi ** 2                       # calibrated to the FE sway load


def k_required(P):
    a = math.sqrt(P / EI); u = a * L / 2
    if u <= math.pi / 2:
        return 0.0
    if u >= math.pi:
        return float("inf")
    return EI * a ** 3 / (2 * (u - math.tan(u)))


def lam_from_k(k):
    if k <= 0:
        return LAM_S1
    f = lambda P: k_required(P) - k
    P_hi = min(P_S2, 4 * P_S1 * 0.999999)
    if f(P_hi) < 0:
        return P_S2 / N
    return brentq(f, P_S1 * (1 + 1e-9), P_hi) / N


out = {"note": "PLANNING ESTIMATE - hand/beam theory calibrated to the 8A FE; not a finite-element result",
       "N_N": N, "EI_calibrated_Nm2": EI, "P_S1_FE_kN": P_S1 / 1e3, "P_S2_FE_kN": P_S2 / 1e3, "first_yield_factor": FIRST_YIELD}
# discrete scenarios
sc = []
for name, h in HAND.items():
    fe = LAM_S1 if name.startswith("guided") else (LAM_S2 if name.startswith("fixed-fixed") else None)
    lam_el = fe if fe else h["euler_shear"]
    sc.append({"end_condition": name, "K": h["K"], "lambda_FE_8A": fe, "lambda_euler_Ez": h["euler"], "lambda_euler_shear": h["euler_shear"],
               "lambda_johnson_conventional": h["johnson"],
               "elastic_bifurcation_before_first_yield": bool(lam_el < FIRST_YIELD)})
# conceptual lower side: rotational freedom at a sway-free end (not proposed for FE)
sc.append({"end_condition": "one end rotation-free, sway free (K = 2) - conceptual only", "K": 2.0, "lambda_FE_8A": None,
           "lambda_euler_Ez": HAND["guided (S1)"]["euler"] / 4, "lambda_euler_shear": None, "lambda_johnson_conventional": None,
           "elastic_bifurcation_before_first_yield": True})
sc.append({"end_condition": "imperfect guided, AISC design K = 1.2 - information only", "K": 1.2, "lambda_FE_8A": None,
           "lambda_euler_Ez": HAND["guided (S1)"]["euler"] / 1.44, "lambda_euler_shear": None, "lambda_johnson_conventional": None,
           "elastic_bifurcation_before_first_yield": True})
out["scenarios"] = sc
# required lateral (relative sway) stiffness
k_switch = brentq(lambda k: lam_from_k(k) - LAM_S2 * 0.999999, 1e3, 1e9) if lam_from_k(1e9) >= LAM_S2 * 0.999999 else None
targets = [1.2, 1.5, FIRST_YIELD, 2.0, 2.5, 3.0]
out["required_lateral_stiffness"] = [{"target_lambda1": t, "k_N_per_mm": k_required(t * N) / 1e3} for t in targets]
out["k_switch_to_no_sway_N_per_mm"] = k_switch / 1e3 if k_switch else None
out["k_euler_threshold_4pi2EI_L3_N_per_mm"] = 4 * math.pi ** 2 * EI / L ** 3 / 1e3
kk = np.logspace(1, 4, 13)          # N/mm
out["lambda_vs_k"] = [{"k_N_per_mm": float(k), "lambda1": lam_from_k(k * 1e3)} for k in kk]
json.dump(out, open(os.path.join(OUT, "support_sensitivity_hand.json"), "w"), indent=1)
print("EI_cal %.0f N m2 | P_S1 %.1f kN | P_S2 %.1f kN" % (EI, P_S1 / 1e3, P_S2 / 1e3))
for s in sc:
    print(" %-58s K %.4g  FE %s  Euler %.3f  +shear %s  Johnson %s  bifurcation<first-yield %s" % (
        s["end_condition"], s["K"], s["lambda_FE_8A"], s["lambda_euler_Ez"], s["lambda_euler_shear"], s["lambda_johnson_conventional"],
        s["elastic_bifurcation_before_first_yield"]))
for r in out["required_lateral_stiffness"]:
    print(" lambda1 = %.2f needs k = %.0f N/mm" % (r["target_lambda1"], r["k_N_per_mm"]))
print(" branch meets FE no-sway load at k = %.0f N/mm (Euler threshold 4pi^2EI/L^3 = %.0f N/mm)" % (out["k_switch_to_no_sway_N_per_mm"], out["k_euler_threshold_4pi2EI_L3_N_per_mm"]))
for r in out["lambda_vs_k"]:
    print("   k %8.1f N/mm -> lambda1 %.3f" % (r["k_N_per_mm"], r["lambda1"]))
