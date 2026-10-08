# -*- coding: utf-8 -*-
"""SECTION 9B-2 - post-processing of the parametric structural cases and of the support scenarios (RE-ANALYSIS 2026).

Reads, for every case, the raw tables written by the solver (APDL snippets of 7B / 8A, unchanged): s7b_nodal.csv,
s7b_react.csv (LC1, LC2, S3 static), s8a_load_factors.csv, s8a_mode<i>.csv (buckling), the LC2 solver input deck
(EBLOCK -> corner nodes: MAPDL stores SOLID186 nodal stresses at corner nodes only) and the Mechanical summaries.
Computes the same quantities for every case with the same formulas as post_7B.py / post_8B.py, generalised to the
case radii (T01: Do 36 mm, T03: Do 44 mm):
  LC1: max total deformation, free axial growth (face-mean u_z, Simpson over the 2nr+1 radii), max von Mises
       (corner nodes) with location and temperature, support reactions (should be ~0: statically determinate)
  LC2: max von Mises, mean axial stress -|F_inlet|/A, max total / axial / radial deformation, temperature-dependent
       yield S_y(T) (VDM 4127 table, 20-400 degC, linear, no extrapolation) and utilisation vm / S_y(T) at every corner
       node (max anywhere, at the max-vm node, interior 15 mm .. L-15 mm), critical location
  buckling: load factors, lambda1, P_cr = lambda1 x N (N = LC2 end reaction), mode classification (8A mode_shapes.py,
       unchanged) + correlation with the clamped-pinned column shape (for S3)
Usage: python post_9B2.py <project_root> <out_dir>"""
import os, sys, json, math
import numpy as np
from scipy.integrate import simpson

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"<PROJECT_ROOT>"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "10_Parametric_Study", "Results", "Data")
os.makedirs(OUT, exist_ok=True)
S8 = os.path.join(ROOT, "08_Structural_Analysis")
PS = os.path.join(ROOT, "10_Parametric_Study")
SC = os.path.join(PS, "Structural_Cases")
sys.dont_write_bytecode = True   # importing the 8A module must not write a __pycache__ into 08_Structural_Analysis
sys.path.insert(0, os.path.join(S8, "Buckling"))
from mode_shapes import load_mode, classify           # 8A, unchanged

L = 0.6
SY_T = np.array([20, 100, 200, 300, 400.0]); SY_V = np.array([1030, 1060, 1040, 1020, 1000.0]) * 1e6   # as post_7B.py


def Sy_of(Tc):
    if np.any(np.asarray(Tc) < SY_T[0]) or np.any(np.asarray(Tc) > SY_T[-1]):
        raise ValueError("temperature outside the supported yield data (20-400 C) - would need documented extrapolation")
    return np.interp(Tc, SY_T, SY_V)


# tag, variable, value, units, geometry label, Ri, Ro, nr, paths
def case_paths(tag):
    if tag == "P00_BASELINE":   # the official 7B / 8A solution (S1)
        return {"LC1": os.path.join(S8, "LC1_Free_Expansion", "Solver_Output"), "LC2": os.path.join(S8, "LC2_Restrained", "Solver_Output"),
                "BUCKLING": os.path.join(S8, "Buckling", "Mechanical", "LC2_Linear_Buckling", "Solver_Output"),
                "ds": os.path.join(S8, "LC2_Restrained", "Solver_Output", "LC2_solve_input_ds.dat"), "summary": None}
    if tag == "S2_LC2NS_NOSWAY":   # 8A solution, nodal table re-extracted in 9B-2 (S2_REEXTRACT, no solve)
        x = os.path.join(SC, "S2_REEXTRACT")
        return {"LC2": x, "nodal": os.path.join(x, "s2x_nodal.csv"), "totals": os.path.join(x, "s2x_totals.txt"),
                "BUCKLING": os.path.join(S8, "Buckling", "Mechanical", "LC2NS_Linear_Buckling", "Solver_Output"),
                "ds": os.path.join(S8, "Buckling", "Mechanical", "LC2NS_NoSway_Static", "Solver_Output", "ds.dat"), "summary": None}
    if tag == "S3_LC2_INTERMEDIATE":
        c = os.path.join(SC, tag)
        return {"LC2": os.path.join(c, "Solver_Output", "S3_STATIC"), "BUCKLING": os.path.join(c, "Solver_Output", "S3_BUCKLING"),
                "ds": os.path.join(c, "Audits", "Presolve_Inputs", "S3_presolve_ds.dat"), "summary": os.path.join(c, "Audits", "summary_S3_solve.json")}
    c = os.path.join(SC, tag)
    return {"LC1": os.path.join(c, "Solver_Output", "LC1"), "LC2": os.path.join(c, "Solver_Output", "LC2"),
            "BUCKLING": os.path.join(c, "Solver_Output", "BUCKLING"),
            "ds": os.path.join(c, "Audits", "Presolve_Inputs", "%s_LC2_presolve_ds.dat" % tag),
            "summary": os.path.join(c, "Audits", "summary_%s.json" % tag)}


CASES = [
    ("P00_BASELINE", "baseline", "V 23.5 m/s; q'' 8000 W/m2; t 10 mm", "-", "baseline (Do 40)", 0.010, 0.020, 5),
    ("C00_PIPELINE_CHECK", "pipeline control", "identical to P00", "-", "baseline (Do 40)", 0.010, 0.020, 5),
    ("V01_LOW", "inlet velocity", 21.15, "m/s", "baseline (Do 40)", 0.010, 0.020, 5),
    ("V03_HIGH", "inlet velocity", 25.85, "m/s", "baseline (Do 40)", 0.010, 0.020, 5),
    ("Q01_LOW", "outer-wall heat flux", 7200.0, "W/m2", "baseline (Do 40)", 0.010, 0.020, 5),
    ("Q03_HIGH", "outer-wall heat flux", 8800.0, "W/m2", "baseline (Do 40)", 0.010, 0.020, 5),
    ("T01_THIN", "wall thickness (Q constant)", 8.0, "mm", "T01 (Do 36)", 0.010, 0.018, 4),
    ("T03_THICK", "wall thickness (Q constant)", 12.0, "mm", "T03 (Do 44)", 0.010, 0.022, 6),
    ("M01_T01_STRUCT_NR5", "structural mesh check (T01, 5 through-wall)", 5, "elements", "T01 (Do 36)", 0.010, 0.018, 5),
    ("M02_T03_STRUCT_NR5", "structural mesh check (T03, 5 through-wall)", 5, "elements", "T03 (Do 44)", 0.010, 0.022, 5),
    ("S2_LC2NS_NOSWAY", "support scenario S2", "both end faces U_z = U_theta = 0", "-", "baseline (Do 40)", 0.010, 0.020, 5),
    ("S3_LC2_INTERMEDIATE", "support scenario S3", "inlet clamped, outlet pinned", "-", "baseline (Do 40)", 0.010, 0.020, 5),
]
COL = {k: j for j, k in enumerate("node,x,y,z,ur,ut,uz,sr,st,sz,s1,s3,seqv,ee,T".split(","))}


def rotated_nodes(ds):
    """Nodal rotations of a solve deck: NMOD lines (angle THXY taken from the deck; THYZ/THZX must be 0) and NROT on a
    node component while a cylindrical LOCAL system at the origin without rotation is active (angle = atan2(y, x) of the
    node, evaluated later). Returns {node: THXY_deg or None} and a small audit dict."""
    L = open(ds, errors="ignore").read().split("\n")
    rot, cms, locs, active = {}, {}, {0: (0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)}, 0
    aud = {"nmod": 0, "nrot_components": [], "nrot_nodes": 0}
    i = 0
    while i < len(L):
        l = L[i].strip()
        ll = l.lower()
        if ll.startswith("cmblock,"):
            p = [x.strip() for x in l.split(",")]
            name, kind, n = p[1].upper(), p[2].upper(), int(p[3])
            i += 2
            vals = []
            while len(vals) < n:
                s_ = L[i].rstrip()
                vals.extend(int(s_[k:k + 10]) for k in range(0, len(s_), 10))
                i += 1
            ids = []
            for v in vals:
                if v < 0:
                    ids.extend(range(ids[-1] + 1, -v + 1))
                else:
                    ids.append(v)
            if kind == "NODE":
                cms[name] = ids
            continue
        if ll.startswith("local,"):
            p = [x.strip() for x in l.split(",")] + [""] * 9
            locs[int(p[1])] = tuple([int(p[2] or 0)] + [float(x or 0) for x in p[3:9]])
        elif ll.startswith("csys,"):
            active = int(l.split(",")[1].split("!")[0])
        elif ll.startswith("nmod,"):
            p = [x.strip() for x in l.split(",")] + [""] * 8
            if float(p[6] or 0) != 0.0 or float(p[7] or 0) != 0.0:
                raise ValueError("NMOD with THYZ/THZX not handled: " + l)
            rot[int(p[1])] = float(p[5] or 0)
            aud["nmod"] += 1
        elif ll.startswith("nrot,"):
            cm = l.split(",")[1].split("!")[0].strip().upper()
            typ, x0, y0, z0, a1, a2, a3 = locs[active]
            if typ != 1 or any(abs(v) > 0 for v in (x0, y0, a1, a2, a3)):
                raise ValueError("NROT in a non-standard CS not handled: csys %d %s" % (active, locs[active]))
            for nd in cms[cm]:
                rot.setdefault(nd, None)
            aud["nrot_components"].append(cm)
            aud["nrot_nodes"] += len(cms[cm])
        i += 1
    return rot, aud


def s2_rotated_node_check(a, ds):
    """Self-check of the S2 table on its own data: the S2 end-face nodes are rotated into CS_DUCT_CYL (NMOD) and carry
    U_theta = 0, so the re-extracted u_theta there must vanish and u_r must be uniform around each end-face ring."""
    rot, aud = rotated_nodes(ds)
    nid = a[:, 0].astype(int)
    m = np.isin(nid, list(rot))
    th_geo = np.degrees(np.arctan2(a[m, 2], a[m, 1]))
    th_deck = np.array([rot[k] if rot[k] is not None else np.nan for k in nid[m]])
    d = np.abs((th_deck - th_geo + 180.0) % 360.0 - 180.0)
    aud["rotated_nodes_in_table"] = int(m.sum())
    aud["max_abs_deck_minus_geometric_angle_deg"] = float(np.nanmax(d)) if m.any() else None
    aud["max_abs_u_theta_at_rotated_nodes_m"] = float(np.abs(a[m, 5]).max()) if m.any() else None
    rr = np.hypot(a[:, 1], a[:, 2])
    for zz in (0.0, 0.6):
        k = m & (np.abs(a[:, 3] - zz) < 1e-9) & (np.abs(rr - rr.max()) < 1e-9)
        aud["outer_ring_u_r_min_max_m_z%.1f" % zz] = [float(a[k, 4].min()), float(a[k, 4].max())] if k.any() else None
    return aud


def corner_nodes(ds):
    Lr = open(ds, errors="ignore").read().split("\n")
    i = [k for k, l in enumerate(Lr) if l.lower().startswith("eblock")][0] + 2
    ids = []
    while not Lr[i].strip().startswith("-1"):
        v = Lr[i]
        ids.extend(int(v[k:k + 9]) for k in range(9, 81, 9))
        i += 1
    return np.unique(ids)


def load(p):
    return np.loadtxt(p, delimiter=",", skiprows=1)


def static_metrics(a, cm, RI, RO):
    # the pilot node of a remote point (S3) sits on the axis: not part of the solid
    a = a[np.hypot(a[:, 1], a[:, 2]) > 0.5 * RI]
    x, y, z = a[:, 1], a[:, 2], a[:, 3]
    r = np.hypot(x, y); th = np.degrees(np.arctan2(y, x)); TC = a[:, 14]; TK = TC + 273.15
    corner = np.isin(a[:, 0].astype(int), cm)
    zr = np.round(z, 7); rr = np.round(r, 7)

    def loc(j):
        surf = "outer" if abs(r[j] - RO) < 1e-7 else ("bore" if abs(r[j] - RI) < 1e-7 else "interior r")
        face = "inlet face" if abs(z[j]) < 1e-7 else ("outlet face" if abs(z[j] - L) < 1e-7 else "")
        return {"node": int(a[j, 0]), "r_mm": round(r[j] * 1e3, 3), "z_mm": round(z[j] * 1e3, 3), "theta_deg": round(th[j], 1),
                "T_K": round(TK[j], 3), "surface": surf, "end_face": face}
    vm = np.where(corner, a[:, 12], -1); j = int(np.argmax(vm))
    ut = np.sqrt(a[:, 4] ** 2 + a[:, 5] ** 2 + a[:, 6] ** 2); k = int(np.argmax(ut))
    m = {"max_vm_Pa": float(vm[j]), "max_vm_loc": loc(j), "max_utot_m": float(ut[k]), "max_utot_loc": loc(k),
         "max_uz_m": float(a[:, 6].max()), "min_uz_m": float(a[:, 6].min()), "max_abs_uz_m": float(np.abs(a[:, 6]).max()),
         "max_ur_m": float(a[:, 4].max()), "max_ur_loc": loc(int(np.argmax(a[:, 4]))), "max_abs_ut_m": float(np.abs(a[:, 5]).max()),
         "T_range_K": [float(TK.min()), float(TK.max())], "corner_nodes": int(corner.sum()), "nodes": int(len(a))}
    # lateral (beam) displacement of the section centroid: mean u_x, u_y per corner plane (S3 check of rigid-body / sway)
    ux = a[:, 4] * np.cos(np.radians(th)) - a[:, 5] * np.sin(np.radians(th))
    uy = a[:, 4] * np.sin(np.radians(th)) + a[:, 5] * np.cos(np.radians(th))
    planes = np.unique(zr[corner])
    lat = np.array([np.hypot(ux[zr == q].mean(), uy[zr == q].mean()) for q in planes])
    m["max_section_lateral_translation_m"] = float(lat.max())

    def ring(zz, rad, col):
        q = corner & (np.abs(z - zz) < 1e-7) & (np.abs(r - rad) < 1e-7)
        return float(a[q, col].mean()) if q.any() else float("nan")
    m["midspan"] = {"bore_st_Pa": ring(L / 2, RI, 8), "bore_sz_Pa": ring(L / 2, RI, 9), "bore_vm_Pa": ring(L / 2, RI, 12),
                    "outer_st_Pa": ring(L / 2, RO, 8), "outer_sz_Pa": ring(L / 2, RO, 9), "outer_vm_Pa": ring(L / 2, RO, 12),
                    "bore_T_K": ring(L / 2, RI, 14) + 273.15, "outer_T_K": ring(L / 2, RO, 14) + 273.15}

    def face_mean_uz(zz):
        q = np.abs(z - zz) < 1e-7
        rad = np.unique(rr[q]); u = np.array([a[q & (rr == v), 6].mean() for v in rad])
        return float(simpson(u * rad, x=rad) / simpson(rad, x=rad))
    m["dL_face_mean_m"] = face_mean_uz(L) - face_mean_uz(0.0)
    mi = corner & (z > 0.015) & (z < L - 0.015)
    ji = int(np.argmax(np.where(mi, a[:, 12], -1)))
    m["max_vm_interior_Pa"] = float(a[ji, 12]); m["max_vm_interior_loc"] = loc(ji)
    # utilisation with the temperature-dependent yield strength at every corner node
    sy = Sy_of(TC)
    u = np.where(corner, a[:, 12] / sy, 0.0)
    iu = int(np.argmax(u))
    ki = int(np.argmax(np.where(mi, u, 0.0)))
    m["utilisation"] = {"max": float(u[iu]), "max_loc": loc(iu), "vm_at_max_Pa": float(a[iu, 12]), "Sy_at_max_Pa": float(sy[iu]),
                        "at_max_vm": float(u[j]), "Sy_at_max_vm_Pa": float(sy[j]),
                        "interior_max": float(u[ki]), "interior_loc": loc(ki), "Sy_interior_Pa": float(sy[ki]),
                        "with_scalar_1020MPa_for_reference": float(vm[j] / 1020e6)}
    return m


def reactions(p, kind):
    a = np.atleast_2d(load(p))
    n = a[:, 0].astype(int); x, y, z = a[:, 1], a[:, 2], a[:, 3]
    fx, fy, fz = a[:, 4].copy(), a[:, 5].copy(), a[:, 6].copy()
    r = np.hypot(x, y)
    if kind == "LC1":
        rot = np.ones(len(n), bool)
    elif kind == "LC2":
        rot = ~((np.abs(z) < 1e-9) | (np.abs(z - L) < 1e-9))          # the 3 Direct FE hoop nodes
    else:   # S3: every inlet-face node is in CS_DUCT_CYL (NMOD); the pilot (r = 0) is global
        rot = (np.abs(z) < 1e-9) & (r > 1e-6)
    th = np.arctan2(y, x)
    gx = np.where(rot, fx * np.cos(th) - fy * np.sin(th), fx); gy = np.where(rot, fx * np.sin(th) + fy * np.cos(th), fy)
    F = np.array([gx.sum(), gy.sum(), fz.sum()])
    M = np.array([(y * fz - z * gy).sum(), (z * gx - x * fz).sum(), (x * gy - y * gx).sum()])
    out = {"n_constrained": int(len(n)), "sumF_N": F.tolist(), "sumF_mag_N": float(np.linalg.norm(F)), "sumM_mag_Nm": float(np.linalg.norm(M)),
           "max_nodal_N": float(np.abs(np.c_[gx, gy, fz]).max())}
    if kind != "LC1":
        inl = np.abs(z) < 1e-9
        out["inlet_Fz_N"] = float(fz[inl].sum()); out["outlet_Fz_N"] = float(fz[~inl].sum())
        out["inlet_F_lateral_N"] = float(np.hypot(gx[inl].sum(), gy[inl].sum()))
        out["outlet_F_lateral_N"] = float(np.hypot(gx[~inl].sum(), gy[~inl].sum()))
        if kind == "S3":
            pil = r < 1e-6
            out["pilot_nodes"] = int(pil.sum())
            out["pilot_F_N"] = [float(gx[pil].sum()), float(gy[pil].sum()), float(fz[pil].sum())]
            out["outlet_face_nodes_constrained"] = int(((np.abs(z - L) < 1e-9) & ~pil).sum())
    return out


KL_FP = 4.493409457909064     # tan(kL) = kL, fixed-pinned column


def fixed_pinned_corr(curve):
    zz = np.array(curve["z_m"]); w = np.array(curve["w_norm"])
    k = KL_FP / L
    ref = np.sin(k * zz) - k * zz + KL_FP * (1 - np.cos(k * zz))       # clamped at z = 0, pinned at z = L
    a1 = w - w.mean(); b1 = ref - ref.mean()
    return float(np.dot(a1, b1) / (np.linalg.norm(a1) * np.linalg.norm(b1) + 1e-30)), float(zz[np.argmax(np.abs(ref))] * 1e3)


def mode_label(c):
    corr = dict(c["correlation_with_reference_shapes"])
    corr["fixed_pinned (inlet clamped, outlet pinned)"] = c.get("corr_fixed_pinned", 0.0)
    best = max(corr, key=lambda k: abs(corr[k]))
    kind = "global lateral (Euler column) mode" if c["beam_type_share_of_inplane_motion"] > 0.99 and c["max_ovalisation_over_max_lateral"] < 0.01 \
        else "mode with cross-section deformation (shell / local)"
    return "%s; shape %s (|corr| %.4f)" % (kind, best, abs(corr[best]))


def mech_summary(p):
    if not p or not os.path.isfile(p):
        return None
    S = json.load(open(p))
    return {"results": {c: S["cases"][c].get("results", {}) for c in S.get("cases", {})}, "mesh": S.get("mesh"),
            "mesh_metrics": S.get("mesh_metrics"), "fatal": S.get("FATAL"), "final_states": S.get("final_states"),
            "support_nodes": S.get("support_nodes"), "mapping": S.get("mapping"),
            "solve_s": {c: S["cases"][c].get("solve_wall_s") for c in S.get("cases", {})},
            "messages": {c: S["cases"][c].get("messages") for c in S.get("cases", {})}}


R = {"note": "RE-ANALYSIS 2026 - Section 9B-2 parametric structural results, computed from the raw solver tables", "cases": {}}
for tag, var, val, units, geo, RI, RO, nr in CASES:
    P = case_paths(tag)
    nodal2 = P.get("nodal", os.path.join(P["LC2"], "s7b_nodal.csv"))
    if not os.path.isfile(nodal2):
        print("not available:", tag)
        continue
    A_SEC = math.pi * (RO ** 2 - RI ** 2)
    cm = corner_nodes(P["ds"])
    E = {"variable": var, "value": val, "units": units, "geometry": geo, "Ri_m": RI, "Ro_m": RO, "nr": nr, "A_m2": A_SEC,
         "paths": {k: v for k, v in P.items() if v}}
    kinds = [("LC1", "LC1"), ("LC2", "LC2")] if "LC1" in P else ([("LC2", "S2")] if "totals" in P else [("LC2", "S3")])
    for case, kind in kinds:
        a = load(nodal2 if case == "LC2" else os.path.join(P[case], "s7b_nodal.csv"))
        if kind == "S2":
            E["S2_rotated_node_check"] = s2_rotated_node_check(a, P["ds"])
        E[case] = static_metrics(a, cm, RI, RO)
        if kind == "S2":
            tl = open(P["totals"]).read().split("\n")
            fin = float([l for l in tl if l.startswith("inlet_face_nodes")][0].split()[-1])
            fout = float([l for l in tl if l.startswith("outlet_face_nodes")][0].split()[-1])
            E[case]["reactions"] = {"inlet_Fz_N": fin, "outlet_Fz_N": fout, "source": "s2x_totals.txt (RF FZ summed per end face)"}
        else:
            E[case]["reactions"] = reactions(os.path.join(P[case], "s7b_react.csv"), kind)
    E["LC2"]["mean_axial_stress_Pa"] = -abs(E["LC2"]["reactions"]["inlet_Fz_N"]) / A_SEC
    lf = os.path.join(P["BUCKLING"], "s8a_load_factors.csv")
    if os.path.isfile(lf):
        lam = np.atleast_2d(load(lf))[:, 1]
        N = abs(E["LC2"]["reactions"]["inlet_Fz_N"])
        modes = {}
        for m in range(1, 7):
            fm_ = os.path.join(P["BUCKLING"], "s8a_mode%d.csv" % m)
            if os.path.isfile(fm_):
                mo = load_mode(fm_)
                keep = np.hypot(mo["x"], mo["y"]) > 1e-6        # a remote-point pilot node (S3) is not part of the tube
                c = classify(dict((kk, vv[keep]) for kk, vv in mo.items()))
                c["corr_fixed_pinned"], c["fixed_pinned_ref_zmax_mm"] = fixed_pinned_corr(c["_curve"])
                c["label"] = mode_label(c)
                if m > 2:
                    c.pop("_curve", None)
                modes[m] = c
        E["buckling"] = {"load_factors": lam.tolist(), "lambda1": float(lam[0]), "lambda2": float(lam[1]), "lambda3": float(lam[2]),
                         "critical_load_N": float(lam[0] * N), "applied_N": N, "pair_split_rel": float((lam[1] - lam[0]) / lam[0]),
                         "modes": modes, "dominant_mode": modes[1]["label"] if 1 in modes else None}
    E["mechanical"] = mech_summary(P["summary"])
    R["cases"][tag] = E
    print("loaded", tag, "LC2 vm %.4f MPa" % (E["LC2"]["max_vm_Pa"] / 1e6), "lambda1 %s" % E.get("buckling", {}).get("lambda1"))
# 9A M01 / M02: structural mesh adequacy of the thickness extremes (acceptance: LC2 and lambda1 change <= 1e-4)
MM = {}
for mtag, ref in (("M01_T01_STRUCT_NR5", "T01_THIN"), ("M02_T03_STRUCT_NR5", "T03_THICK")):
    if mtag in R["cases"] and ref in R["cases"]:
        A_, B_ = R["cases"][ref], R["cases"][mtag]
        q = {"LC2 max vm": (A_["LC2"]["max_vm_Pa"], B_["LC2"]["max_vm_Pa"]),
             "LC2 mean axial stress": (A_["LC2"]["mean_axial_stress_Pa"], B_["LC2"]["mean_axial_stress_Pa"]),
             "LC2 max total deformation": (A_["LC2"]["max_utot_m"], B_["LC2"]["max_utot_m"]),
             "LC2 utilisation": (A_["LC2"]["utilisation"]["max"], B_["LC2"]["utilisation"]["max"]),
             "lambda1": (A_["buckling"]["lambda1"], B_["buckling"]["lambda1"]),
             "LC1 max vm": (A_["LC1"]["max_vm_Pa"], B_["LC1"]["max_vm_Pa"]),
             "LC1 max total deformation": (A_["LC1"]["max_utot_m"], B_["LC1"]["max_utot_m"]),
             "LC1 dL": (A_["LC1"]["dL_face_mean_m"], B_["LC1"]["dL_face_mean_m"]),
             "LC1 mid-span bore hoop stress": (A_["LC1"]["midspan"]["bore_st_Pa"], B_["LC1"]["midspan"]["bore_st_Pa"])}
        MM[mtag] = {"reference": ref, "changes": {k: {"case": a_, "mesh_check": b_, "rel": (b_ - a_) / abs(a_)} for k, (a_, b_) in q.items()}}
        MM[mtag]["class_A_LC2_lambda1_le_1e-4"] = all(abs(MM[mtag]["changes"][k]["rel"]) <= 1e-4 for k in ("LC2 max vm", "LC2 mean axial stress", "lambda1"))
R["structural_mesh_checks_M01_M02"] = MM
# validation of the S2 re-extraction: the same MAPDL file applied to the 8A LC2 re-solve (S1) must reproduce the table
# the 7B snippet wrote for that solution in 8A
v1 = os.path.join(SC, "S2_REEXTRACT", "s1x_nodal.csv")
v0 = os.path.join(S8, "Buckling", "Mechanical", "LC2_prestress_resolve", "Solver_Output", "s7b_nodal.csv")
if os.path.isfile(v1) and os.path.isfile(v0):
    A1, A0 = load(v1), load(v0)
    same_nodes = A1.shape == A0.shape and bool(np.all(A1[:, 0] == A0[:, 0]))
    R["S2_reextraction_validation"] = {"nodes_equal": same_nodes,
                                       "max_abs_diff_per_column": {k: float(np.abs(A1[:, j] - A0[:, j]).max()) for k, j in COL.items()} if same_nodes else None,
                                       "max_abs_ur_ut_8A_m": [float(np.abs(A0[:, 4]).max()), float(np.abs(A0[:, 5]).max())],
                                       "max_vm_s1x_Pa": float(A1[:, 12].max()), "max_vm_8A_table_Pa": float(A0[:, 12].max()),
                                       "note": "Run 2 (each result file read in its own MAPDL database after /CLEAR); raw tables, no correction. "
                                               "Run 1 read S1 with the S2 nodal rotations still in the database (Structural_Cases/S2_REEXTRACT/Run1_shared_session/README.md); "
                                               "the S2 table is identical in Run 1 and Run 2."}
    print("S2 re-extraction validation", R["S2_reextraction_validation"])
json.dump(R, open(os.path.join(OUT, "post_9B2_results.json"), "w"), indent=1, default=float)
print("written", os.path.join(OUT, "post_9B2_results.json"))
