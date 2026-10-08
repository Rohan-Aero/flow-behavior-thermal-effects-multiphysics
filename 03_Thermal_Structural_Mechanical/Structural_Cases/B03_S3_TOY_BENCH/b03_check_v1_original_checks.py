# -*- coding: utf-8 -*-
"""SECTION 9B-2 Part L - evaluation of the B03_S3_TOY_BENCH benchmark (RE-ANALYSIS 2026). Not project results.
Checks (fixed before the run, 9A SUPPORT_SCENARIOS.md 'B03' acceptance):
  1. the solve completes without errors, pivot / rigid-body warnings (no unrestrained rigid-body motion)
  2. reactions: inlet axial force = E alpha dT A within 0.1 %; pilot axial force = - inlet force (equilibrium);
     no lateral reaction resultant
  3. deformation shape of the static state: no lateral translation of any section (symmetric load), uniform radial growth
  4. column behaviour: lambda1 between the plain and the shear-corrected clamped-pinned Euler values (K = 0.6992)
  5. buckling mode: global lateral (beam-type) mode, fixed-pinned shape (correlation > 0.99), maximum lateral deflection
     at 0.55-0.65 L from the clamped (inlet) end; modes 1-2 = an orthogonal pair
Usage: python b03_check.py <bench_dir> <project_root>"""
import os, sys, json, math, re
import numpy as np

D, ROOT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(ROOT, "08_Structural_Analysis", "Buckling"))
from mode_shapes import load_mode, classify            # 8A, unchanged

E, NU, ALPHA, DT = 190e9, 0.294, 13.6e-6, 225.0
RI, RO, L = 0.010, 0.020, 0.6
A = math.pi * (RO ** 2 - RI ** 2); I = math.pi / 4 * (RO ** 4 - RI ** 4)
N_EXACT = E * ALPHA * DT * A
K_FP = 0.6992
m_ = RI / RO
K_SHEAR = 6 * (1 + NU) * (1 + m_ ** 2) ** 2 / ((7 + 6 * NU) * (1 + m_ ** 2) ** 2 + (20 + 12 * NU) * m_ ** 2)   # Cowper (as 8A)
P_E = math.pi ** 2 * E * I / (K_FP * L) ** 2
G = E / (2 * (1 + NU))
P_ES = P_E / (1 + P_E / (K_SHEAR * G * A))
R = {"note": "RE-ANALYSIS 2026 - B03 toy benchmark of the S3 supports (method check only, NOT project results)",
     "exact": {"N_N": N_EXACT, "Euler_K0.6992_N": P_E, "Euler_shear_N": P_ES, "lambda_Euler": P_E / N_EXACT,
               "lambda_Euler_shear": P_ES / N_EXACT, "K_shear_Cowper": K_SHEAR}}
out = open(os.path.join(D, "b03_main.out"), errors="ignore").read()
R["solver_messages"] = {"errors": len(re.findall(r"\*\*\* ERROR \*\*\*", out)), "warnings": len(re.findall(r"\*\*\* WARNING \*\*\*", out)),
                        "pivot_or_rigid_body": len(re.findall(r"(?i)small pivot|negative pivot|zero pivot|rigid body motion|singular|unconstrained|insufficient constraint", out)),
                        # (normal output contains 'maximum/minimum pivot' and 'TOTAL RIGID BODY MASS MATRIX'; only warnings are counted)
                        "min_pivot_lines": re.findall(r"minimum pivot.*", out)[:4],
                        "end_marker": "B03-END" in out}
wl = []
lines = out.splitlines()
for i, l in enumerate(lines):
    if "*** WARNING ***" in l:
        wl.append(" ".join(x.strip() for x in lines[i:i + 4]))
R["solver_messages"]["warning_texts"] = wl[:20]
# reactions (7B snippet table; inlet nodes in CS 12, pilot global)
a = np.atleast_2d(np.loadtxt(os.path.join(D, "s7b_react.csv"), delimiter=",", skiprows=1))
x, y, z = a[:, 1], a[:, 2], a[:, 3]; r = np.hypot(x, y); th = np.arctan2(y, x)
fx, fy, fz = a[:, 4], a[:, 5], a[:, 6]
rot = (np.abs(z) < 1e-9) & (r > 1e-6)
gx = np.where(rot, fx * np.cos(th) - fy * np.sin(th), fx); gy = np.where(rot, fx * np.sin(th) + fy * np.cos(th), fy)
inl = np.abs(z) < 1e-9; pil = r < 1e-6
R["reactions"] = {"constrained_nodes": int(len(a)), "inlet_nodes": int(inl.sum()), "pilot_nodes": int(pil.sum()),
                  "outlet_face_nodes_constrained": int(((np.abs(z - L) < 1e-9) & ~pil).sum()),
                  "inlet_Fz_N": float(fz[inl].sum()), "pilot_Fz_N": float(fz[pil].sum()),
                  "inlet_lateral_N": float(np.hypot(gx[inl].sum(), gy[inl].sum())), "pilot_lateral_N": float(np.hypot(gx[pil].sum(), gy[pil].sum())),
                  "N_exact_N": N_EXACT}
R["reactions"]["inlet_Fz_rel_err"] = abs(R["reactions"]["inlet_Fz_N"]) / N_EXACT - 1
R["reactions"]["equilibrium_rel"] = (R["reactions"]["inlet_Fz_N"] + R["reactions"]["pilot_Fz_N"]) / N_EXACT
# static deformation shape
nd = np.loadtxt(os.path.join(D, "s7b_nodal.csv"), delimiter=",", skiprows=1)
nd = nd[np.hypot(nd[:, 1], nd[:, 2]) > 1e-6]
xs, ys, zs = nd[:, 1], nd[:, 2], nd[:, 3]; ths = np.arctan2(ys, xs); rs = np.hypot(xs, ys)
ux = nd[:, 4] * np.cos(ths) - nd[:, 5] * np.sin(ths); uy = nd[:, 4] * np.sin(ths) + nd[:, 5] * np.cos(ths)
zr = np.round(zs, 7)
lat = [np.hypot(ux[zr == q].mean(), uy[zr == q].mean()) for q in np.unique(zr)]
mid = np.abs(zs - 0.3) < 1e-7
R["static_shape"] = {"max_section_lateral_translation_m": float(max(lat)), "max_abs_u_theta_m": float(np.abs(nd[:, 5]).max()),
                     "max_abs_u_z_m": float(np.abs(nd[:, 6]).max()),
                     "midspan_u_r_outer_m": float(nd[mid & (np.abs(rs - RO) < 1e-7), 4].mean()),
                     "midspan_u_r_outer_free_expansion_m": (1 + NU) * ALPHA * DT * RO,
                     "midspan_s_z_Pa": float(nd[mid, 9].mean()), "exact_s_z_Pa": -E * ALPHA * DT}
# buckling
lf = np.atleast_2d(np.loadtxt(os.path.join(D, "s8a_load_factors.csv"), delimiter=",", skiprows=1))[:, 1]
modes = {}
KL = 4.493409457909064
for k in range(1, 7):
    m = load_mode(os.path.join(D, "s8a_mode%d.csv" % k))
    keep = np.hypot(m["x"], m["y"]) > 1e-6          # the pilot node is not part of the tube section
    m = dict((kk, vv[keep]) for kk, vv in m.items())
    c = classify(m)
    zz = np.array(c["_curve"]["z_m"]); w = np.array(c["_curve"]["w_norm"]); kk_ = KL / L
    ref = np.sin(kk_ * zz) - kk_ * zz + KL * (1 - np.cos(kk_ * zz))
    c["corr_fixed_pinned"] = float(np.dot(w - w.mean(), ref - ref.mean()) / (np.linalg.norm(w - w.mean()) * np.linalg.norm(ref - ref.mean())))
    c.pop("_curve")
    modes[k] = c
R["buckling"] = {"load_factors": lf.tolist(), "lambda1": float(lf[0]), "FE_over_Euler": float(lf[0] / (P_E / N_EXACT)),
                 "FE_over_Euler_shear": float(lf[0] / (P_ES / N_EXACT)), "pair_split_rel": float((lf[1] - lf[0]) / lf[0]),
                 "modes": modes}
m1, m2 = modes[1], modes[2]
ang = abs(((m1["lateral_direction_deg"] - m2["lateral_direction_deg"]) + 90) % 180 - 90)
C = {
    "1 solve completed, no errors, no pivot / rigid-body messages":
        R["solver_messages"]["errors"] == 0 and R["solver_messages"]["pivot_or_rigid_body"] == 0 and R["solver_messages"]["end_marker"],
    "2a inlet axial force = E alpha dT A within 0.1 %": abs(R["reactions"]["inlet_Fz_rel_err"]) <= 1e-3,
    "2b pilot axial force = - inlet axial force (equilibrium, 1e-6)": abs(R["reactions"]["equilibrium_rel"]) <= 1e-6,
    "2c outlet face nodes carry no constraint; one constrained pilot": R["reactions"]["outlet_face_nodes_constrained"] == 0 and R["reactions"]["pilot_nodes"] == 1,
    "2d no lateral reaction resultant (< 1e-3 N = 2e-9 x N)": R["reactions"]["inlet_lateral_N"] < 1e-3 and R["reactions"]["pilot_lateral_N"] < 1e-3,
    "3 static state: no section translates laterally (< 1e-9 m)": R["static_shape"]["max_section_lateral_translation_m"] < 1e-9,
    "4 lambda1 between shear-corrected and plain clamped-pinned Euler": P_ES / N_EXACT <= lf[0] <= P_E / N_EXACT,
    "5a mode 1 global lateral (beam share > 0.99, ovalisation < 1 %)": m1["beam_type_share_of_inplane_motion"] > 0.99 and m1["max_ovalisation_over_max_lateral"] < 0.01,
    "5b mode 1 fixed-pinned shape (corr > 0.99)": abs(m1["corr_fixed_pinned"]) > 0.99,
    "5c max lateral deflection at 0.55-0.65 L from the clamped inlet": 0.55 * L * 1e3 <= m1["z_of_max_lateral_mm"] <= 0.65 * L * 1e3,
    "5d modes 1-2 orthogonal pair (split < 1e-4, 90 +- 1 deg)": abs(R["buckling"]["pair_split_rel"]) < 1e-4 and abs(ang - 90) < 1.0,
}
R["angle_between_modes_1_2_deg"] = ang
R["checks"] = C
R["B03_PASS"] = bool(all(C.values()))
json.dump(R, open(os.path.join(D, "b03_results.json"), "w"), indent=1, default=float)
for k, v in C.items():
    print("%-4s %s" % ("PASS" if v else "FAIL", k))
print("lambda1 FE %.5f | Euler %.5f | Euler+shear %.5f | N FE %.1f exact %.1f" % (lf[0], P_E / N_EXACT, P_ES / N_EXACT, abs(R["reactions"]["inlet_Fz_N"]), N_EXACT))
print("B03 PASS:", R["B03_PASS"])
