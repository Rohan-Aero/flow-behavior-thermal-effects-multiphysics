# -*- coding: utf-8 -*-
"""SECTION 9A - independent check of the lateral-stiffness formula in support_sensitivity_hand.py (RE-ANALYSIS 2026).
Euler-Bernoulli beam finite elements (60 elements) with the consistent geometric stiffness matrix; both ends held against
rotation, base held laterally, a lateral spring k at the top end. The lowest eigenvalue must match k_required() of the
hand script. Planning check only - not a model of the duct."""
import math, json, sys, os
import numpy as np
from scipy.linalg import eigh
EI, L, ne, N = 22186.0, 0.6, 60, 548936.6
h = L / ne


def pcr(k):
    n = 2 * (ne + 1); K = np.zeros((n, n)); G = np.zeros((n, n))
    ke = EI / h**3 * np.array([[12, 6*h, -12, 6*h], [6*h, 4*h*h, -6*h, 2*h*h], [-12, -6*h, 12, -6*h], [6*h, 2*h*h, -6*h, 4*h*h]])
    ge = 1 / (30*h) * np.array([[36, 3*h, -36, 3*h], [3*h, 4*h*h, -3*h, -h*h], [-36, -3*h, 36, -3*h], [3*h, -h*h, -3*h, 4*h*h]])
    for e in range(ne):
        d = [2*e, 2*e+1, 2*e+2, 2*e+3]; K[np.ix_(d, d)] += ke; G[np.ix_(d, d)] += ge
    K[2*ne, 2*ne] += k
    free = [i for i in range(n) if i not in (0, 1, 2*ne + 1)]
    w = eigh(K[np.ix_(free, free)], G[np.ix_(free, free)], eigvals_only=True)
    return w[w > 0].min()


here = os.path.dirname(os.path.abspath(__file__))
H = json.load(open(os.path.join(here, "support_sensitivity_hand.json")))
res = []
for r in H["required_lateral_stiffness"]:
    lam_fe = pcr(r["k_N_per_mm"] * 1e3) / N
    res.append({"target": r["target_lambda1"], "k_N_per_mm": r["k_N_per_mm"], "beamFE_lambda": lam_fe, "ok": bool(abs(lam_fe / r["target_lambda1"] - 1) < 2e-3)})
    print("k %7.0f N/mm  target %.3f  beam FE %.4f" % (r["k_N_per_mm"], r["target_lambda1"], lam_fe))
json.dump({"note": "check of the hand formula only", "checks": res, "all_ok": bool(all(x["ok"] for x in res))},
          open(os.path.join(here, "support_spring_check_beamFE.json"), "w"), indent=1)
print("ALL OK" if all(x["ok"] for x in res) else "MISMATCH")
