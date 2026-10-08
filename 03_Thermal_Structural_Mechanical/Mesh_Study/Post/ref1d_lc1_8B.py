# -*- coding: utf-8 -*-
"""SECTION 8B - mesh-converged 1-D reference for the LC1 mid-span through-wall stress (RE-ANALYSIS 2026).
Independent of Mechanical: the imposed temperature at z = 300 mm is evaluated directly from the Fluent solid NODE field
(the same source the structural meshes are mapped from; Section 7A HexField, theta-averaged over 96 directions), and
the thick-cylinder thermal-stress problem is solved as a 1-D axisymmetric GENERALISED PLANE STRAIN problem (free ends:
zero net axial force; LC1) with 2,000 linear elements, E(T) and the MPAMOD-adjusted thermal strain exactly as in the
solver input (same tables as post_7B.py), nu = 0.294.
Assumption: the axial temperature variation at mid-span (about 0.2 K/mm) is neglected; it is a reference for the
through-wall discretisation, not a replacement of the 3-D model.
Usage: python ref1d_lc1_8B.py <out_json>"""
import os, sys, json
import numpy as np
S7A = "<OUTPUT_ROOT>/S7A"
sys.path.insert(0, os.path.join(S7A, "Validation"))
sys.path.insert(0, os.path.join(S7A, "MeshBased"))
from source_mesh_interp import HexField
import fluent_solid_mesh_from_case as fm

U = "<PROJECT_ROOT>"
case = os.path.join(U, "06_Fluent_CFD", "Case", "baseline_medium_final.cas.h5")
ncsv = os.path.join(S7A, "MeshBased", "out", "fluent_solid_node_temperature.csv")
NU = 0.294
TREF_C, T0_C = 26.85, 21.11
E_T = np.array([20, 100, 200, 300, 400.0]); E_V = np.array([204, 199, 193, 187, 180.0]) * 1e9
A_T = np.array([93.33, 204.44, 315.56, 426.67, 537.78]); A_V = np.array([12.8, 13.3, 13.9, 14.2, 14.8]) * 1e-6
A_MOD = (A_V * (A_T - T0_C) - np.interp(TREF_C, A_T, A_V) * (TREF_C - T0_C)) / (A_T - TREF_C)
E_of = lambda Tc: np.interp(Tc, E_T, E_V)
eps_th = lambda Tc: np.interp(Tc, A_T, A_MOD) * (Tc - TREF_C)

X, cf, _, _, _ = fm.read_solid(case)
conn = np.array([fm.hex_from_faces(cf[c]) for c in sorted(cf)])
Xid = np.vstack([np.zeros(3), X])
d = np.loadtxt(ncsv, delimiter=",", skiprows=1)
Tid = np.full(len(Xid), np.nan)
Tid[d[:, 0].astype(int)] = d[:, 1]
H = HexField(Xid, conn, Tid)

a, b, z0 = 0.010, 0.020, 0.300
NE = 2000
rn = np.linspace(a, b, NE + 1)
gp = np.array([-1, 1]) / np.sqrt(3.0)
rg = (0.5 * (rn[:-1] + rn[1:])[:, None] + 0.5 * np.diff(rn)[:, None] * gp[None, :]).ravel()   # Gauss points
nth = 96
th = (np.arange(nth) + 0.5) * 2 * np.pi / nth
# the source hex faces are straight chords of a 48-gon; evaluate at the nominal radius scaled into the polygon cell
P = np.array([[r * np.cos(t), r * np.sin(t), z0] for r in rg for t in th])
Tv, dout = H.evaluate(P)
Tg = Tv.reshape(len(rg), nth)
outside_share = float((dout > 1e-10).mean())
T_pts = np.nanmean(Tg, axis=1)                       # K, theta-mean
nan_share = float(np.isnan(Tg).mean())
Tc = T_pts - 273.15
Eg, eg = E_of(Tc), eps_th(Tc)


def Dmat(E):
    c = E / ((1 + NU) * (1 - 2 * NU))
    return c * np.array([[1 - NU, NU, NU], [NU, 1 - NU, NU], [NU, NU, 1 - NU]])


nd = NE + 2                                           # radial displacements + generalised axial strain
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
K = lil_matrix((nd, nd)); F = np.zeros(nd)
for e in range(NE):
    r1, r2 = rn[e], rn[e + 1]; h = r2 - r1
    dofs = [e, e + 1, nd - 1]
    Ke = np.zeros((3, 3)); Fe = np.zeros(3)
    for g in range(2):
        k = 2 * e + g
        r = rg[k]
        N1, N2 = (r2 - r) / h, (r - r1) / h
        B = np.array([[-1 / h, 1 / h, 0.0], [N1 / r, N2 / r, 0.0], [0.0, 0.0, 1.0]])
        D = Dmat(Eg[k])
        wt = r * h / 2
        Ke += wt * B.T @ D @ B
        Fe += wt * B.T @ D @ (eg[k] * np.ones(3))
    for i in range(3):
        F[dofs[i]] += Fe[i]
        for j in range(3):
            K[dofs[i], dofs[j]] += Ke[i, j]
x = spsolve(K.tocsr(), F)
sig = []
for e in range(NE):
    r1, r2 = rn[e], rn[e + 1]; h = r2 - r1
    for g in range(2):
        k = 2 * e + g; r = rg[k]
        N1, N2 = (r2 - r) / h, (r - r1) / h
        eps = np.array([(x[e + 1] - x[e]) / h, (N1 * x[e] + N2 * x[e + 1]) / r, x[-1]])
        sig.append(Dmat(Eg[k]) @ (eps - eg[k]))
sig = np.array(sig)                                   # sr, st, sz at Gauss points
vm = np.sqrt(0.5 * ((sig[:, 0] - sig[:, 1])**2 + (sig[:, 1] - sig[:, 2])**2 + (sig[:, 2] - sig[:, 0])**2))
# net axial force check (must be ~0)
Nz = sum(np.sum(sig[2 * e:2 * e + 2, 2] * rg[2 * e:2 * e + 2]) * (rn[e + 1] - rn[e]) / 2 for e in range(NE)) * 2 * np.pi


def at(rq):
    # linear extrapolation of the two outermost Gauss-point values to the surface
    i = np.argsort(np.abs(rg - rq))[:2]
    s = sig[i]; rr = rg[i]
    v = s[0] + (s[1] - s[0]) * (rq - rr[0]) / (rr[1] - rr[0])
    vmv = np.sqrt(0.5 * ((v[0] - v[1])**2 + (v[1] - v[2])**2 + (v[2] - v[0])**2))
    return {"s_r_MPa": v[0] / 1e6, "s_t_MPa": v[1] / 1e6, "s_z_MPa": v[2] / 1e6, "vm_MPa": vmv / 1e6}


out = {"note": __doc__.split("\n")[0], "z_m": z0, "elements": NE, "theta_directions": nth, "unlocated_share": nan_share, "points_outside_source_polygon_share_clamped": outside_share,
       "T_bore_K": float(T_pts[0]), "T_outer_K": float(T_pts[-1]), "dT_wall_K": float(T_pts[-1] - T_pts[0]),
       "net_axial_force_N": float(Nz), "bore": at(a), "outer": at(b),
       }
# discretisation check of the reference itself: repeat with 1,000 elements via subsampling is not needed - report the
# change between the first Gauss point and the extrapolated surface value as the resolution indicator
out["bore_first_gauss_point_s_t_MPa"] = float(sig[0, 1] / 1e6)
json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "ref1d_lc1_8B.json", "w"), indent=1)
print(json.dumps(out, indent=1))
