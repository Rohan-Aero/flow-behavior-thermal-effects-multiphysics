# -*- coding: utf-8 -*-
"""SECTION 8B - post-processing of the structural mesh study (RE-ANALYSIS 2026).
Reads, for every mesh, the raw tables written by the solver (APDL snippets: s7b_nodal.csv, s7b_react.csv,
s8a_load_factors.csv, s8a_mode<i>.csv), the solver input deck (EBLOCK -> corner nodes; MAPDL stores SOLID186 nodal
stresses at corner nodes only), and the Mechanical summaries (maxima, averaged vs unaveraged von Mises, structural
error). Computes the same quantities for every mesh, the Richardson / GCI assessment of the systematic family
XC -> C -> B (constant refinement ratio r = 1.303 in element size), and the differences of the licence-limited
directional refinements FR (through-wall), FA (axial) and FC (circumferential) and of the inlet-bias sensitivity IL.
Usage: python post_8B.py [project_root] [out_dir]"""
import os, sys, json, csv, math
import numpy as np
from scipy.integrate import simpson

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mode_shapes import load_mode, classify

ROOT = sys.argv[1] if len(sys.argv) > 1 else "<PROJECT_ROOT>"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
S8 = os.path.join(ROOT, "08_Structural_Analysis")
MS = os.path.join(S8, "Mesh_Study")
A_SEC = math.pi * (0.02**2 - 0.01**2)
MESHES = [  # tag, circumferential, through-wall, axial, bias, role
    ("XC", 21, 3, 76, 4.0, "extra-coarse (systematic family, level 1)"),
    ("C", 27, 4, 98, 4.0, "coarse (systematic family, level 2)"),
    ("B", 36, 5, 130, 4.0, "baseline (systematic family, level 3; official 7B/8A mesh)"),
    ("FR", 36, 6, 130, 4.0, "fine - through-wall refinement at the licence limit"),
    ("FA", 36, 5, 152, 4.0, "fine - axial refinement at the licence limit"),
    ("FC", 42, 5, 130, 4.0, "fine - circumferential refinement at the licence limit"),
    ("IL", 36, 5, 130, 8.0, "inlet-bias local sensitivity (separate check, not in the family)"),
]
R_FAMILY = (23400 / 10584) ** (1 / 3)
U7B = {"LC1": 0.1539241680870641, "LC2": 505.582655274445, "LC2P": 505.58265532015605}   # post_7B_results.json
E_T = lambda t: np.interp(t, [20, 100, 200, 300, 400], [204e9, 199e9, 193e9, 187e9, 180e9])


def paths(tag):
    if tag == "B_official":   # the 7B / 8A files (same mesh as B)
        return {"LC1": os.path.join(S8, "LC1_Free_Expansion", "Solver_Output"), "LC2": os.path.join(S8, "LC2_Restrained", "Solver_Output"),
                "LC2P": os.path.join(S8, "Pressure_Check", "Solver_Output"),
                "BUCKLING": os.path.join(S8, "Buckling", "Mechanical", "LC2_Linear_Buckling", "Solver_Output"),
                "ds": os.path.join(S8, "Mechanical_Setup", "Input_Files", "LC2_Axially_Restrained_ds.dat"), "summary": None}
    v = os.path.join(MS, "Variants", tag)
    return {k: os.path.join(v, "Solver_Output", k) for k in ("LC1", "LC2", "LC2P", "BUCKLING")} | {
        "ds": os.path.join(v, "Audits", "Presolve_Inputs", "%s_LC2_presolve_ds.dat" % tag),
        "summary": os.path.join(v, "Audits", "summary_%s.json" % tag)}


def corner_nodes(ds):
    L = open(ds, errors="ignore").read().split("\n")
    i = [k for k, l in enumerate(L) if l.lower().startswith("eblock")][0] + 2
    ids = []
    while not L[i].strip().startswith("-1"):
        v = L[i]
        ids.extend(int(v[k:k + 9]) for k in range(9, 81, 9))   # element id, then 8 corner nodes
        i += 1
    return np.unique(ids)


def load(p):
    return np.loadtxt(p, delimiter=",", skiprows=1)


COL = {k: j for j, k in enumerate("node,x,y,z,ur,ut,uz,sr,st,sz,s1,s3,seqv,ee,T".split(","))}


def static_metrics(a, cm, case):
    x, y, z = a[:, 1], a[:, 2], a[:, 3]
    r = np.hypot(x, y); th = np.degrees(np.arctan2(y, x)); TK = a[:, 14] + 273.15
    corner = np.isin(a[:, 0].astype(int), cm)
    zr = np.round(z, 7); rr = np.round(r, 7)
    loc = lambda j: {"node": int(a[j, 0]), "r_mm": round(r[j] * 1e3, 3), "z_mm": round(z[j] * 1e3, 3), "theta_deg": round(th[j], 1),
                     "T_K": round(TK[j], 2)}
    vm = np.where(corner, a[:, 12], -1); j = int(np.argmax(vm))
    ut = np.sqrt(a[:, 4]**2 + a[:, 5]**2 + a[:, 6]**2); k = int(np.argmax(ut))
    m = {"max_vm_Pa": float(vm[j]), "max_vm_loc": loc(j), "max_utot_m": float(ut[k]), "max_utot_loc": loc(k),
         "max_uz_m": float(a[:, 6].max()), "min_uz_m": float(a[:, 6].min()), "max_ur_m": float(a[:, 4].max()),
         "max_ur_loc": loc(int(np.argmax(a[:, 4]))), "min_uz_loc": loc(int(np.argmin(a[:, 6]))),
         "T_range_K": [float(TK.min()), float(TK.max())], "corner_nodes": int(corner.sum()), "nodes": int(len(a))}

    def ring(zz, rad, col):
        q = corner & (np.abs(z - zz) < 1e-7) & (np.abs(r - rad) < 1e-7)
        return float(a[q, col].mean()) if q.any() else float("nan")
    m["midspan"] = {"bore_st_Pa": ring(0.3, 0.01, 8), "bore_sz_Pa": ring(0.3, 0.01, 9), "bore_vm_Pa": ring(0.3, 0.01, 12),
                    "outer_st_Pa": ring(0.3, 0.02, 8), "outer_sz_Pa": ring(0.3, 0.02, 9), "outer_vm_Pa": ring(0.3, 0.02, 12)}
    # face-mean axial displacement (Simpson over all 2nr+1 radii of the corner plane)
    def face_mean_uz(zz):
        q = np.abs(z - zz) < 1e-7
        rad = np.unique(rr[q]); u = np.array([a[q & (rr == v), 6].mean() for v in rad])
        return float(simpson(u * rad, x=rad) / simpson(rad, x=rad))
    m["dL_face_mean_m"] = face_mean_uz(0.6) - face_mean_uz(0.0)
    # inlet region profiles (theta-mean, corner planes)
    zc = np.unique(zr[corner]); zin = zc[zc <= 0.0301]
    prof = {"z_mm": (zin * 1e3).tolist(), "bore_vm_MPa": [ring(q, 0.01, 12) / 1e6 for q in zin],
            "outer_vm_MPa": [ring(q, 0.02, 12) / 1e6 for q in zin]}
    m["inlet_profile"] = prof
    b = np.array(prof["bore_vm_MPa"]); o = np.array(prof["outer_vm_MPa"])
    m["inlet"] = {"bore_peak_MPa": float(b.max()), "bore_peak_z_mm": float(zin[np.argmax(b)] * 1e3),
                  "outer_at_face_MPa": float(o[0]), "outer_peak_MPa": float(o.max()), "outer_peak_z_mm": float(zin[np.argmax(o)] * 1e3)}
    # interior maximum (15-585 mm)
    mi = corner & (z > 0.015) & (z < 0.585)
    ji = int(np.argmax(np.where(mi, a[:, 12], -1)))
    m["max_vm_interior_Pa"] = float(a[ji, 12]); m["max_vm_interior_loc"] = loc(ji)
    return m


def reactions(p, case):
    a = np.atleast_2d(load(p))
    n = a[:, 0].astype(int); x, y, z = a[:, 1], a[:, 2], a[:, 3]
    fx, fy, fz = a[:, 4].copy(), a[:, 5].copy(), a[:, 6].copy()
    if case == "LC1" or len(n) > 3:
        # rotated (Direct FE) nodes: the 3 support nodes of LC1, the 3 hoop nodes of LC2 -> nodes not on an end face in LC2
        rot = np.ones(len(n), bool) if case == "LC1" else ~((np.abs(z) < 1e-9) | (np.abs(z - 0.6) < 1e-9))
        th = np.arctan2(y, x)
        gx = np.where(rot, fx * np.cos(th) - fy * np.sin(th), fx); gy = np.where(rot, fx * np.sin(th) + fy * np.cos(th), fy)
        fx, fy = gx, gy
    F = np.array([fx.sum(), fy.sum(), fz.sum()])
    M = np.array([(y * fz - z * fy).sum(), (z * fx - x * fz).sum(), (x * fy - y * fx).sum()])
    out = {"n_constrained": int(len(n)), "sumF_N": F.tolist(), "sumF_mag_N": float(np.linalg.norm(F)), "sumM_mag_Nm": float(np.linalg.norm(M)),
           "max_nodal_N": float(np.abs(np.c_[fx, fy, fz]).max())}
    if case != "LC1":
        out["inlet_Fz_N"] = float(fz[np.abs(z) < 1e-9].sum()); out["outlet_Fz_N"] = float(fz[np.abs(z - 0.6) < 1e-9].sum())
        out["hoop_nodes_max_N"] = float(np.abs(np.c_[fx, fy, fz][~((np.abs(z) < 1e-9) | (np.abs(z - 0.6) < 1e-9))]).max())
    return out


def mech_summary(tag):
    p = paths(tag)["summary"]
    if tag == "B_official":
        S7 = json.load(open(os.path.join(S8, "Audits", "mech_solve_7B_summary.json")))
        res = {}
        for c in ("LC1", "LC2", "LC2P"):
            rr = S7["cases"][c]["results"]
            res[c] = {("%s_%s" % (c, k)): {"Maximum": v.get("Maximum_value"), "Minimum": v.get("Minimum_value")} for k, v in rr.items()}
        return {"results": res, "mesh_metrics": S7.get("mesh_metrics"), "solve_s": {c: S7["cases"][c].get("solve_wall_s") for c in ("LC1", "LC2", "LC2P")}}
    if not os.path.isfile(p):
        return None
    S = json.load(open(p))
    return {"results": {c: S["cases"][c].get("results", {}) for c in S["cases"] if c != "BUCKLING"},
            "mesh_metrics": S.get("mesh_metrics"), "mesh": S.get("mesh"), "solve_s": {c: S["cases"][c].get("solve_wall_s") for c in S["cases"]},
            "fatal": S.get("FATAL"), "final_states": S.get("final_states"), "support_nodes": S.get("support_nodes"), "mapping": S.get("mapping")}


def structural_error_total(tag, case):
    if tag == "B_official":
        p = os.path.join(S8, "Exports", case, "%s_Structural_Error.txt" % case)
    else:
        p = os.path.join(paths(tag)[case], "%s_%s_Structural_Error.txt" % (tag, case))
    if not os.path.isfile(p):
        return None
    v = []
    for ln in open(p, errors="ignore").read().splitlines()[1:]:
        q = ln.split("\t")
        try:
            v.append(float(q[1]))
        except Exception:
            pass
    return {"total_J": float(np.sum(v)), "max_J": float(np.max(v)), "n": len(v)}


R = {"note": "RE-ANALYSIS 2026 - Section 8B mesh study, computed from the raw solver tables", "meshes": {}}
for tag, nc, nr, na, bias, role in MESHES + [("B_official", 36, 5, 130, 4.0, "official 7B/8A solution (identity check of B)")]:
    P = paths(tag)
    if not os.path.isfile(os.path.join(P["LC2"], "s7b_nodal.csv")):
        continue
    cm = corner_nodes(P["ds"])
    E = {"divisions": {"circumferential": nc, "through_wall": nr, "axial": na, "axial_bias": bias}, "role": role}
    for case in ("LC1", "LC2", "LC2P"):
        f = os.path.join(P[case], "s7b_nodal.csv")
        if os.path.isfile(f):
            a = load(f)
            E[case] = static_metrics(a, cm, case)
            E[case]["reactions"] = reactions(os.path.join(P[case], "s7b_react.csv"), case)
            se = structural_error_total(tag, case)
            if se:
                # energy-norm estimate sqrt(e / (U + e)); U = strain energy of the 7B baseline solution (post_7B.py), a
                # global quantity that does not depend on the mesh at the precision needed here
                se["strain_energy_U_7B_J"] = U7B[case]
                se["energy_norm_error_pct"] = 100 * math.sqrt(se["total_J"] / (U7B[case] + se["total_J"]))
                E[case]["structural_error"] = se
    if "LC2" in E:
        E["LC2"]["mean_axial_stress_Pa"] = -abs(E["LC2"]["reactions"]["inlet_Fz_N"]) / A_SEC
    if "LC2P" in E:
        E["pressure_effect_max_vm_Pa"] = E["LC2P"]["max_vm_Pa"] - E["LC2"]["max_vm_Pa"]
    lf = os.path.join(P["BUCKLING"], "s8a_load_factors.csv")
    if os.path.isfile(lf):
        lam = np.atleast_2d(load(lf))[:, 1]
        N = abs(E["LC2"]["reactions"]["inlet_Fz_N"])
        modes = {}
        for m in range(1, 7):
            fm_ = os.path.join(P["BUCKLING"], "s8a_mode%d.csv" % m)
            if os.path.isfile(fm_):
                c = classify(load_mode(fm_))
                c.pop("_curve", None) if m > 2 else None
                modes[m] = c
        d12 = abs(modes[1]["lateral_direction_deg"] - modes[2]["lateral_direction_deg"]) % 180 if 1 in modes and 2 in modes else None
        E["buckling"] = {"load_factors": lam.tolist(), "lambda1": float(lam[0]), "lambda2": float(lam[1]), "lambda3": float(lam[2]), "lambda4": float(lam[3]),
                         "lambda5": float(lam[4]), "lambda6": float(lam[5]),
                         "critical_load_N": float(lam[0] * N), "pair_split_rel": float((lam[1] - lam[0]) / lam[0]),
                         "pair_angle_deg": d12, "modes": modes}
    E["mechanical"] = mech_summary(tag)
    R["meshes"][tag] = E
    print("loaded", tag)


# ---------------- Richardson / GCI on the systematic family XC -> C -> B (Celik et al. 2008 procedure, constant r) -------
def gci(f3, f2, f1, r=R_FAMILY, Fs=1.25):
    """f3 coarsest (XC), f2 (C), f1 finest (B)."""
    e32, e21 = f2 - f3, f1 - f2
    out = {"XC": f3, "C": f2, "B": f1, "r": r, "change_XC_to_C_rel": e32 / f2 if f2 else None, "change_C_to_B_rel": e21 / f1 if f1 else None}
    if e21 == 0:
        out.update(behaviour="exactly converged", p=None, extrapolated=f1, GCI_fine=0.0)
        return out
    R_ = e21 / e32 if e32 != 0 else float("inf")
    out["convergence_ratio_R"] = R_
    if 0 < R_ < 1:
        p = math.log(abs(e32 / e21)) / math.log(r)
        ext = f1 + e21 / (r**p - 1)
        out.update(behaviour="monotonic convergence", p=p, extrapolated=ext, GCI_fine=Fs * abs(e21 / f1) / (r**p - 1),
                   baseline_error_vs_extrapolated_rel=(f1 - ext) / ext)
    elif -1 < R_ < 0:
        out.update(behaviour="oscillatory convergence", p=None, extrapolated=None,
                   GCI_fine=None, oscillation_band_rel=abs(max(f1, f2, f3) - min(f1, f2, f3)) / abs(f1) / 2)
    else:
        out.update(behaviour="divergent / not in asymptotic range", p=None, extrapolated=None, GCI_fine=None)
    return out


def g(tag, *keys):
    v = R["meshes"].get(tag)
    for k in keys:
        if v is None:
            return None
        v = v.get(k) if isinstance(v, dict) else None
    return v


QUANT = {
    "LC1 max von Mises [Pa]": ("LC1", "max_vm_Pa"), "LC1 max total deformation [m]": ("LC1", "max_utot_m"),
    "LC1 free growth dL [m]": ("LC1", "dL_face_mean_m"), "LC1 mid-span bore hoop stress [Pa]": ("LC1", "midspan", "bore_st_Pa"),
    "LC1 mid-span bore von Mises [Pa]": ("LC1", "midspan", "bore_vm_Pa"),
    "LC1 inlet bore peak (theta-mean) [MPa]": ("LC1", "inlet", "bore_peak_MPa"),
    "LC2 max von Mises [Pa]": ("LC2", "max_vm_Pa"), "LC2 mean axial stress [Pa]": ("LC2", "mean_axial_stress_Pa"),
    "LC2 max total deformation [m]": ("LC2", "max_utot_m"), "LC2 min axial displacement [m]": ("LC2", "min_uz_m"),
    "LC2 max radial displacement [m]": ("LC2", "max_ur_m"), "LC2 end reaction [N]": ("LC2", "reactions", "inlet_Fz_N"),
    "LC2 max von Mises 15-585 mm [Pa]": ("LC2", "max_vm_interior_Pa"), "LC2 outer edge at inlet face (theta-mean) [MPa]": ("LC2", "inlet", "outer_at_face_MPa"),
    "lambda_1": ("buckling", "lambda1"), "critical buckling load [N]": ("buckling", "critical_load_N"),
    "lambda_3": ("buckling", "lambda3"), "lambda_5": ("buckling", "lambda5"),
    "LC1 energy-norm error [%]": ("LC1", "structural_error", "energy_norm_error_pct"),
    "LC2 energy-norm error [%]": ("LC2", "structural_error", "energy_norm_error_pct"),
    "LC1 max von Mises unaveraged [Pa]": ("mechanical", "results", "LC1", "LC1_Equivalent_Stress_UNaveraged", "Maximum"),
    "LC2 max von Mises unaveraged [Pa]": ("mechanical", "results", "LC2", "LC2_Equivalent_Stress_UNaveraged", "Maximum"),
}
R["family_assessment"] = {}
R["directional_fine"] = {}
for name, keys in QUANT.items():
    vals = {t: g(t, *keys) for t in ("XC", "C", "B", "FR", "FA", "FC", "IL", "B_official")}
    if all(vals[t] is not None for t in ("XC", "C", "B")):
        R["family_assessment"][name] = gci(vals["XC"], vals["C"], vals["B"])
    R["directional_fine"][name] = {t: ((vals[t] - vals["B"]) / vals["B"] if (vals.get(t) is not None and vals.get("B")) else None)
                                   for t in ("FR", "FA", "FC", "IL", "B_official")} | {"values": vals}
# averaged vs unaveraged peak (Mechanical result objects)
R["peak_averaged_vs_unaveraged"] = {}
for tag in R["meshes"]:
    ms = R["meshes"][tag]["mechanical"]
    if not ms:
        continue
    row = {}
    for c in ("LC1", "LC2"):
        rr = ms["results"].get(c, {})
        av = rr.get("%s_Equivalent_Stress_averaged" % c, {}).get("Maximum")
        un = rr.get("%s_Equivalent_Stress_UNaveraged" % c, {}).get("Maximum")
        if av and un:
            row[c] = {"averaged_Pa": av, "unaveraged_Pa": un, "diff_rel": (un - av) / av}
    R["peak_averaged_vs_unaveraged"][tag] = row
json.dump(R, open(os.path.join(OUT, "post_8B_results.json"), "w"), indent=1, default=float)

# ---------------- the required table ----------------
STATUS = {"XC": "family level 1 (coarsest)", "C": "family level 2", "B": "family level 3 = baseline; SELECTED",
          "FR": "licence-limited fine (through-wall)", "FA": "licence-limited fine (axial)", "FC": "licence-limited fine (circumferential)", "IL": "inlet-bias sensitivity (static only)"}
rows = []
STATUS["B_official"] = "official 7B/8A solution of the baseline mesh (identity reference for B)"
ORDER = []
for m in MESHES:
    ORDER.append(m)
    if m[0] == "B":
        ORDER.append(("B_official", 36, 5, 130, 4.0, "official"))
for tag, nc, nr, na, bias, role in ORDER:
    E = R["meshes"].get(tag)
    if not E:
        continue
    rows.append({"Mesh": "%s (%dx%dx%d, bias %g)" % (tag, nc, nr, na, bias), "Nodes": E["LC2"]["nodes"],
                 "Elements": nc * nr * na, "LC1 Stress [MPa]": round(E["LC1"]["max_vm_Pa"] / 1e6, 4),
                 "LC1 Deformation [mm]": round(E["LC1"]["max_utot_m"] * 1e3, 5), "LC2 Stress [MPa]": round(E["LC2"]["max_vm_Pa"] / 1e6, 4),
                 "LC2 Deformation [mm]": round(E["LC2"]["max_utot_m"] * 1e3, 6),
                 "\u03bb1": round(E["buckling"]["lambda1"], 6) if "buckling" in E else "",
                 "Critical Buckling Load [kN]": round(E["buckling"]["critical_load_N"] / 1e3, 2) if "buckling" in E else "",
                 "Status": STATUS[tag],
                 "LC2 mean axial stress [MPa]": round(E["LC2"]["mean_axial_stress_Pa"] / 1e6, 4),
                 "LC1 free growth [mm]": round(E["LC1"]["dL_face_mean_m"] * 1e3, 5),
                 "LC2 pressure effect on max VM [Pa]": round(E["pressure_effect_max_vm_Pa"], 1) if "pressure_effect_max_vm_Pa" in E else ""})
with open(os.path.join(OUT, "STRUCTURAL_MESH_STUDY.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(json.dumps(rows, indent=1))
