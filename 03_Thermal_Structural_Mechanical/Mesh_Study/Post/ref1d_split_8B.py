# -*- coding: utf-8 -*-
"""SECTION 8B - split of the LC1 mid-span bore-stress discretisation error (RE-ANALYSIS 2026).
Solves the same 1-D generalised-plane-strain problem as ref1d_lc1_8B.py (2,000 elements), but with the temperature
profile AS THE STRUCTURAL MESH REPRESENTS IT: the theta-mean nodal temperatures (T_used_C, corner + midside nodes) of
each mesh at z = 300 mm, interpolated quadratically inside each through-wall element (the SOLID186 temperature
interpolation). The difference to the exact-profile reference is the temperature-representation part of the error;
the rest of the FE-vs-reference difference is stress recovery at the surface.
Usage: python ref1d_split_8B.py <project_root> <out_json>"""
import os, sys, json
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
ROOT, OUTJ = sys.argv[1], sys.argv[2]
V = os.path.join(ROOT, "08_Structural_Analysis", "Mesh_Study", "Variants")
NU, TREF_C, T0_C = 0.294, 26.85, 21.11
E_T = np.array([20, 100, 200, 300, 400.0]); E_V = np.array([204, 199, 193, 187, 180.0]) * 1e9
A_T = np.array([93.33, 204.44, 315.56, 426.67, 537.78]); A_V = np.array([12.8, 13.3, 13.9, 14.2, 14.8]) * 1e-6
A_MOD = (A_V * (A_T - T0_C) - np.interp(TREF_C, A_T, A_V) * (TREF_C - T0_C)) / (A_T - TREF_C)
E_of = lambda Tc: np.interp(Tc, E_T, E_V)
eps_th = lambda Tc: np.interp(Tc, A_T, A_MOD) * (Tc - TREF_C)
a, b, NE = 0.010, 0.020, 2000


def solve(Tfun):
    rn = np.linspace(a, b, NE + 1); gp = np.array([-1, 1]) / np.sqrt(3.0)
    rg = (0.5 * (rn[:-1] + rn[1:])[:, None] + 0.5 * np.diff(rn)[:, None] * gp[None, :]).ravel()
    Tc = Tfun(rg); Eg, eg = E_of(Tc), eps_th(Tc)
    D = lambda E: E / ((1 + NU) * (1 - 2 * NU)) * np.array([[1 - NU, NU, NU], [NU, 1 - NU, NU], [NU, NU, 1 - NU]])
    nd = NE + 2; K = lil_matrix((nd, nd)); F = np.zeros(nd)
    for e in range(NE):
        r1, r2 = rn[e], rn[e + 1]; h = r2 - r1; dofs = [e, e + 1, nd - 1]; Ke = np.zeros((3, 3)); Fe = np.zeros(3)
        for g in range(2):
            k = 2 * e + g; r = rg[k]; N1, N2 = (r2 - r) / h, (r - r1) / h
            B = np.array([[-1 / h, 1 / h, 0], [N1 / r, N2 / r, 0], [0, 0, 1.0]]); wt = r * h / 2
            Ke += wt * B.T @ D(Eg[k]) @ B; Fe += wt * B.T @ D(Eg[k]) @ (eg[k] * np.ones(3))
        for i in range(3):
            F[dofs[i]] += Fe[i]
            for j in range(3):
                K[dofs[i], dofs[j]] += Ke[i, j]
    x = spsolve(K.tocsr(), F)
    s = []
    for k in (0, 1):
        r = rg[k]; h = rn[1] - rn[0]; N1, N2 = (rn[1] - r) / h, (r - rn[0]) / h
        eps = np.array([(x[1] - x[0]) / h, (N1 * x[0] + N2 * x[1]) / r, x[-1]]); s.append(D(Eg[k]) @ (eps - eg[k]))
    s = np.array(s); v = s[0] + (s[1] - s[0]) * (a - rg[0]) / (rg[1] - rg[0])
    return v / 1e6


out = {}
for t in ("XC", "C", "B", "FR", "FA", "FC"):
    A = np.loadtxt(os.path.join(V, t, "Solver_Output", "LC1", "s7b_nodal.csv"), delimiter=",", skiprows=1)
    m = np.abs(A[:, 3] - 0.3) < 1e-9
    r = np.round(np.hypot(A[m, 1], A[m, 2]), 7); T = A[m, 14]
    lv = np.unique(r)
    Tm = np.array([T[r == q].mean() for q in lv])            # corner and midside radial levels
    fe_st = A[m, 8][r == lv[0]].mean() / 1e6                # FE bore hoop stress incl. midside nodes (0 there) -> use corner only below
    ne = (len(lv) - 1) // 2

    def Tq(rr, lv=lv, Tm=Tm, ne=ne):
        out = np.empty_like(rr)
        for e in range(ne):
            r0, r1, r2 = lv[2 * e:2 * e + 3]; t0, t1, t2 = Tm[2 * e:2 * e + 3]
            s = (rr >= r0 - 1e-12) & (rr <= r2 + 1e-12)
            x = rr[s]
            out[s] = (t0 * (x - r1) * (x - r2) / ((r0 - r1) * (r0 - r2)) + t1 * (x - r0) * (x - r2) / ((r1 - r0) * (r1 - r2))
                      + t2 * (x - r0) * (x - r1) / ((r2 - r0) * (r2 - r1)))
        return out
    v = solve(Tq)
    out[t] = {"through_wall_elements": ne, "radial_levels": len(lv), "T_bore_K": float(Tm[0] + 273.15), "T_outer_K": float(Tm[-1] + 273.15),
              "ref1d_with_mesh_temperature_bore_s_t_MPa": float(v[1])}
    print(t, out[t])
json.dump(out, open(OUTJ, "w"), indent=1)
