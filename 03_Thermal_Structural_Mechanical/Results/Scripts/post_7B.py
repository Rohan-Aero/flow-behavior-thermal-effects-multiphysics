# -*- coding: utf-8 -*-
"""
SECTION 7B - post-processing of the LC1 / LC2 / LC2P Mechanical solutions (RE-ANALYSIS 2026).

Every number here is computed from files written by the 7B Mechanical/MAPDL solve:
  <case>/Solver_Output/s7b_nodal.csv  full-precision nodal table (RSYS 12 = CS_DUCT_CYL) written by the APDL post snippet
  <case>/Solver_Output/s7b_react.csv  reaction of every constrained node (nodal CS)
  Audits/mech_solve_7B_summary.json   Mechanical result objects (max/min), probes, messages, states
  Exports/<case>/*.txt                Mechanical text exports (cross-check)
plus the 7A inputs (material tables, mapped temperature export, ds.dat EBLOCK for element centroids) and the
Section 2 / 6B values quoted in PROJECT_STATE.md. No result is typed in by hand; nothing is fitted or tuned.
"""
import os, json, math, re, csv
import numpy as np

ROOT = os.environ.get("S7B_PROJECT_ROOT", "<PROJECT_ROOT>")  # set to the project folder when re-running
S8 = os.path.join(ROOT, "08_Structural_Analysis")
OUT = os.environ.get("S7B_OUT", "<OUTPUT_ROOT>/S7B/Post/out")
FIGD = os.environ.get("S7B_FIG", "<OUTPUT_ROOT>/S7B/Post/fig")
os.makedirs(OUT, exist_ok=True)
os.makedirs(FIGD, exist_ok=True)
CASES = {"LC1": "LC1_Free_Expansion", "LC2": "LC2_Restrained", "LC2P": "Pressure_Check"}
L, RI, RO = 0.600, 0.010, 0.020
A_SEC = math.pi * (RO ** 2 - RI ** 2)
TREF_C, T0_C = 26.85, 21.11  # T_ref = 300 K; zero-strain datum of the secant CTE table (70 F)
NU = 0.294  # [ASSUMED]

# ------------------------------------------------------------------ material (exactly the Engineering Data tables)
E_T = np.array([20, 100, 200, 300, 400.0]); E_V = np.array([204, 199, 193, 187, 180.0]) * 1e9
A_T = np.array([93.33, 204.44, 315.56, 426.67, 537.78]); A_V = np.array([12.8, 13.3, 13.9, 14.2, 14.8]) * 1e-6
SY_T = np.array([20, 100, 200, 300, 400.0]); SY_V = np.array([1030, 1060, 1040, 1020, 1000.0]) * 1e6  # VDM 4127 age-hardened


def E_of(Tc):
    return np.interp(Tc, E_T, E_V)  # linear, constant outside (as MAPDL)


def alpha_sec(Tc):
    return np.interp(Tc, A_T, A_V)


# MAPDL MPAMOD: the secant table (datum T0) is converted at its own temperature points to datum TREF, then interpolated
A_MOD = (A_V * (A_T - T0_C) - alpha_sec(TREF_C) * (TREF_C - T0_C)) / (A_T - TREF_C)


def eps_th(Tc):
    """thermal strain the solver applies: alpha'(T) (T - TREF), alpha' = MPAMOD-adjusted table, linear interpolation"""
    return np.interp(Tc, A_T, A_MOD) * (Tc - TREF_C)


def eps_th_direct(Tc):
    """same physics written directly from the datasheet secant definition (sensitivity to the interpolation form)"""
    return alpha_sec(Tc) * (Tc - T0_C) - alpha_sec(TREF_C) * (TREF_C - T0_C)


def Sy_of(Tc):
    if np.any(np.asarray(Tc) < SY_T[0]) or np.any(np.asarray(Tc) > SY_T[-1]):
        raise ValueError("temperature outside the supported yield data (20-400 C) - would need documented extrapolation")
    return np.interp(Tc, SY_T, SY_V)


# ------------------------------------------------------------------ loaders
COLS = ["node", "x", "y", "z", "ur", "ut", "uz", "sr", "st", "sz", "s1", "s3", "seqv", "epel", "T"]


def load_nodal(case):
    p = os.path.join(S8, CASES[case], "Solver_Output", "s7b_nodal.csv")
    a = np.loadtxt(p, delimiter=",", skiprows=1)
    d = {k: a[:, i] for i, k in enumerate(COLS)}
    d["node"] = d["node"].astype(int)
    d["r"] = np.hypot(d["x"], d["y"])
    d["th"] = np.degrees(np.arctan2(d["y"], d["x"]))
    d["usum"] = np.sqrt(d["ur"] ** 2 + d["ut"] ** 2 + d["uz"] ** 2)
    d["TK"] = d["T"] + 273.15
    d["file"] = p
    return d


def load_connectivity():
    """SOLID186 connectivity from the solver input (EBLOCK COMPACT: element id + 20 nodes; first 8 = corner nodes)"""
    p = os.path.join(S8, "Mechanical_Setup", "Input_Files", "LC2_Axially_Restrained_ds.dat")
    el = []
    with open(p) as f:
        for ln in f:
            if ln.lower().startswith("eblock,21,compact"):
                next(f)
                for ln2 in f:
                    if ln2.strip() == "-1":
                        break
                    el.append([int(t) for t in ln2.split()])
                break
    el = np.array(el)
    assert el.shape == (23400, 21), el.shape
    return el


def load_react(case):
    p = os.path.join(S8, CASES[case], "Solver_Output", "s7b_react.csv")
    a = np.loadtxt(p, delimiter=",", skiprows=1, ndmin=2)
    return {"node": a[:, 0].astype(int), "x": a[:, 1], "y": a[:, 2], "z": a[:, 3], "rfx": a[:, 4], "rfy": a[:, 5],
            "rfz": a[:, 6], "file": p}


def where(d, i):
    return {"node": int(d["node"][i]), "x_mm": round(1e3 * d["x"][i], 4), "y_mm": round(1e3 * d["y"][i], 4),
            "z_mm": round(1e3 * d["z"][i], 4), "r_mm": round(1e3 * d["r"][i], 4), "theta_deg": round(d["th"][i], 3),
            "T_K": round(d["TK"][i], 3), "T_C": round(d["T"][i], 3)}


def surface(d, i):
    r, z = d["r"][i], d["z"][i]
    s = []
    if abs(r - RI) < 1e-7: s.append("bore (inner surface)")
    if abs(r - RO) < 1e-7: s.append("outer surface")
    if abs(z) < 1e-7: s.append("inlet end face")
    if abs(z - L) < 1e-7: s.append("outlet end face")
    return " / ".join(s) if s else "interior of wall"


# ------------------------------------------------------------------ section integration (corner z-planes)
def planes(d):
    zr = np.round(d["z"], 9)
    zs = np.unique(zr)
    out = []
    for z in zs:
        idx = np.where(zr == z)[0]
        out.append((z, idx, len(idx) == 612))
    return out


def section_integral(d, idx, f):
    """integral of f over the annulus at one corner z-plane: theta-average at each radius (72 values at corner radii,
    36 at mid radii), then Simpson per element radially (corner, mid, corner) - exact for f linear in r."""
    r = np.round(d["r"][idx], 9)
    rs = np.unique(r)
    fbar = np.array([np.mean(f[idx][r == rv]) for rv in rs])
    if len(rs) != 11:
        raise ValueError("unexpected radial node count %d" % len(rs))
    tot = 0.0
    for k in range(0, 10, 2):
        ra, rm, rb = rs[k], rs[k + 1], rs[k + 2]
        ga, gm, gb = [2 * math.pi * rr * ff for rr, ff in ((ra, fbar[k]), (rm, fbar[k + 1]), (rb, fbar[k + 2]))]
        tot += (rb - ra) / 6.0 * (ga + 4 * gm + gb)
    return tot, rs, fbar


def section_integral_corner(d, idx, f):
    """integral over the annulus using corner nodes only (6 corner radii x 36 theta), trapezoid in r of 2 pi r f_bar(r)"""
    idx = idx[CN[idx]]
    r = np.round(d["r"][idx], 9)
    rs = np.unique(r)
    if len(rs) != 6:
        raise ValueError("unexpected corner radius count %d" % len(rs))
    fbar = np.array([np.mean(f[idx][r == rv]) for rv in rs])
    return float(np.trapezoid(2 * np.pi * rs * fbar, rs)), rs, fbar


def theta_avg_at(d, idx, radius):
    m = np.abs(d["r"][idx] - radius) < 1e-7
    return idx[m]


# ------------------------------------------------------------------ run
R = {"note": "RE-ANALYSIS 2026 - computed from the 7B Mechanical/MAPDL solution files; nothing typed in by hand"}
summ = json.load(open(os.path.join(S8, "Audits", "mech_solve_7B_summary.json")))
pre = json.load(open(os.path.join(S8, "Audits", "presolve_audit_7B.json")))
R["gate"] = pre["gate"]
R["n_presolve_checks"] = len(pre["checks"])
D = {c: load_nodal(c) for c in CASES}
EL = load_connectivity()
CORNER_NODES = np.unique(EL[:, 1:9])
CN = np.isin(D["LC1"]["node"], CORNER_NODES)  # stresses/strains exist only at corner nodes (see below)
R["stress_nodes"] = {"corner_nodes": int(CN.sum()), "midside_nodes": int((~CN).sum()),
                     "midside_stress_all_zero": bool(all(np.all(D[c][q][~CN] == 0.0) for c in CASES for q in ("seqv", "sz", "st", "sr", "s1", "s3", "epel"))),
                     "note": "MAPDL keeps averaged nodal stresses of SOLID186 at the 8 corner nodes only; *VGET returns 0 at midside nodes "
                             "(the 'undefined entities' warning). All stress and strain statistics below use the corner nodes; "
                             "displacements and temperatures are used at all nodes."}
RX = {c: load_react(c) for c in CASES}
for c in CASES:
    assert len(D[c]["node"]) == 108252, (c, len(D[c]["node"]))
    assert np.array_equal(D[c]["node"], D["LC1"]["node"])

# ---------------- 1. temperature actually used by the solver = mapped CFD field
mapx = np.loadtxt(os.path.join(ROOT, "07_Thermal_Analysis", "Mapping", "Mechanical_Export", "LC1_imported_body_temperature.txt"),
                  skiprows=1, encoding="latin-1")
mp = dict(zip(mapx[:, 0].astype(int), mapx[:, 1]))
mT = np.array([mp[n] for n in D["LC1"]["node"]])
bf = {}
dsp = os.path.join(S8, "Mechanical_Setup", "Input_Files", "LC2_Axially_Restrained_ds.dat")
with open(dsp) as f:
    on = False
    for ln in f:
        l = ln.strip().lower()
        if l.startswith("bfblock"):
            on = True
            next(f)
            continue
        if on:
            if l.startswith("bf,end"):
                break
            p = ln.split()
            bf[int(p[0])] = float(p[1])
bT = np.array([bf[n] for n in D["LC1"]["node"]])
R["temperature_check"] = {}
for c in CASES:
    R["temperature_check"][c] = {
        "T_used_min_K": float(D[c]["TK"].min()), "T_used_max_K": float(D[c]["TK"].max()),
        "max_abs_diff_vs_7A_mapped_export_K": float(np.max(np.abs(D[c]["T"] - mT))),
        "max_abs_diff_vs_ds.dat_BFBLOCK_K": float(np.max(np.abs(D[c]["T"] - bT))),
        "nodes": int(len(D[c]["T"]))}
R["temperature_check"]["note"] = ("T_used = PRNSOL/*VGET BFE,TEMP from the solved database: the nodal temperature MAPDL applied. The 7A export "
                                  "has 2 decimals (0.005 K rounding); the BFBLOCK has 10 significant digits.")

# ---------------- 2. geometry of planes
PL = planes(D["LC1"])
CORNER = [(z, idx) for (z, idx, isc) in PL if isc]
R["mesh_planes"] = {"z_planes": len(PL), "corner_planes": len(CORNER),
                    "first_element_axial_length_mm": round(1e3 * (CORNER[1][0] - CORNER[0][0]), 4),
                    "largest_element_axial_length_mm": round(1e3 * max(CORNER[i + 1][0] - CORNER[i][0] for i in range(len(CORNER) - 1)), 4)}


def profiles(c):
    d = D[c]
    rows = []
    for z, idx in CORNER:
        eth = eps_th(d["T"])
        Ez = E_of(d["T"])
        A, _, _ = section_integral(d, idx, np.ones_like(d["T"]))
        Nz, _, _ = section_integral_corner(d, idx, d["sz"])
        A6, _, _ = section_integral_corner(d, idx, np.ones_like(d["sz"]))
        Tm, _, _ = section_integral(d, idx, d["TK"])
        em, _, _ = section_integral(d, idx, eth)
        EA, _, _ = section_integral(d, idx, Ez)
        Eem, _, _ = section_integral(d, idx, Ez * eth)
        uzm, _, _ = section_integral(d, idx, d["uz"])
        bi, bo = theta_avg_at(d, idx, RI), theta_avg_at(d, idx, RO)
        ci, co = bi[CN[bi]], bo[CN[bo]]
        ic = idx[CN[idx]]
        rows.append({"z_m": z, "A_m2": A, "N_z_N": Nz * A_SEC / A6, "N_z_trapezoid_raw_N": Nz, "T_mean_K": Tm / A, "T_bore_K": d["TK"][bi].mean(), "T_outer_K": d["TK"][bo].mean(),
                     "eps_th_mean": em / A, "eps_th_Eweighted": Eem / EA, "E_mean_Pa": EA / A,
                     "uz_mean_m": uzm / A, "uz_outer_m": d["uz"][bo].mean(), "uz_bore_m": d["uz"][bi].mean(),
                     "ur_outer_m": d["ur"][bo].mean(), "ur_bore_m": d["ur"][bi].mean(),
                     "seqv_bore_Pa": d["seqv"][ci].mean(), "seqv_outer_Pa": d["seqv"][co].mean(),
                     "seqv_max_in_plane_Pa": d["seqv"][ic].max(),
                     "sz_bore_Pa": d["sz"][ci].mean(), "sz_outer_Pa": d["sz"][co].mean(),
                     "st_bore_Pa": d["st"][ci].mean(), "st_outer_Pa": d["st"][co].mean(),
                     "sr_max_abs_Pa": np.abs(d["sr"][ic]).max(), "epel_outer": d["epel"][co].mean()})
    return rows


PROF = {c: profiles(c) for c in CASES}
for c in CASES:
    with open(os.path.join(OUT, "axial_profile_%s.csv" % c), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(PROF[c][0].keys()))
        w.writeheader()
        for r in PROF[c]:
            w.writerow(r)

zc = np.array([r["z_m"] for r in PROF["LC1"]])
Acheck = np.array([r["A_m2"] for r in PROF["LC1"]])
R["section_area_check"] = {"A_numeric_m2": float(Acheck.mean()), "A_exact_m2": A_SEC,
                           "rel_err": float(Acheck.mean() / A_SEC - 1)}


def zint(y):
    return float(np.trapezoid(y, zc))


# ---------------- 3. extraction per case
def extract(c):
    d = D[c]
    out = {}
    for q, lab in (("usum", "total_deformation_m"), ("uz", "axial_deformation_uz_m"), ("ur", "radial_deformation_ur_m"),
                   ("seqv", "von_mises_Pa"), ("s1", "max_principal_Pa"), ("s3", "min_principal_Pa"), ("epel", "equiv_elastic_strain"),
                   ("sz", "axial_stress_Pa"), ("st", "hoop_stress_Pa"), ("sr", "radial_stress_Pa")):
        if q in ("seqv", "s1", "s3", "epel", "sz", "st", "sr"):
            ii = np.where(CN)[0]
            i, j = int(ii[np.argmax(d[q][ii])]), int(ii[np.argmin(d[q][ii])])
        else:
            i, j = int(np.argmax(d[q])), int(np.argmin(d[q]))
        out[lab] = {"max": float(d[q][i]), "max_at": where(d, i), "max_surface": surface(d, i),
                    "min": float(d[q][j]), "min_at": where(d, j), "min_surface": surface(d, j)}
    return out


EX = {c: extract(c) for c in CASES}
R["extremes"] = EX

# Mechanical's own result objects (native values) for cross-check
MECH = {}
for c in CASES:
    res = summ["cases"][c]["results"]
    MECH[c] = {k: {"max": v.get("Maximum_value"), "min": v.get("Minimum_value"), "state": v.get("state")}
               for k, v in res.items() if "Maximum_value" in v}
R["mechanical_native"] = MECH


def xcheck(c, mech_name, ours, which="max"):
    m = MECH[c].get(mech_name, {}).get(which)
    return {"mechanical": m, "apdl_table": ours, "rel_diff": (None if (m is None or ours == 0) else (m - ours) / abs(ours))}


R["native_vs_table"] = {}
for c in CASES:
    e = EX[c]
    R["native_vs_table"][c] = {
        "total_def_max": xcheck(c, "Total_Deformation", e["total_deformation_m"]["max"]),
        "uz_max": xcheck(c, "Axial_Deformation_Uz_global", e["axial_deformation_uz_m"]["max"]),
        "uz_min": xcheck(c, "Axial_Deformation_Uz_global", e["axial_deformation_uz_m"]["min"], "min"),
        "ur_max": xcheck(c, "Radial_Deformation_Ur_CS_DUCT_CYL", e["radial_deformation_ur_m"]["max"]),
        "vm_max": xcheck(c, "Equivalent_Stress_averaged", e["von_mises_Pa"]["max"]),
        "s1_max": xcheck(c, "Maximum_Principal_Stress", e["max_principal_Pa"]["max"]),
        "s3_min": xcheck(c, "Minimum_Principal_Stress", e["min_principal_Pa"]["min"], "min"),
        "epel_max": xcheck(c, "Equivalent_Elastic_Strain", e["equiv_elastic_strain"]["max"]),
        "vm_unaveraged_max": MECH[c].get("Equivalent_Stress_UNaveraged", {}).get("max"),
        "structural_error_max": MECH[c].get("Structural_Error", {}).get("max")}

# ---------------- 4. reactions and equilibrium
ROT = {"LC1": [18870, 18882, 18894], "LC2": [25862, 25874, 25886], "LC2P": [25862, 25874, 25886]}


def reactions(c):
    r = RX[c]
    th = np.arctan2(r["y"], r["x"])
    rot = np.isin(r["node"], ROT[c])
    fx = np.where(rot, r["rfx"] * np.cos(th) - r["rfy"] * np.sin(th), r["rfx"])
    fy = np.where(rot, r["rfx"] * np.sin(th) + r["rfy"] * np.cos(th), r["rfy"])
    fz = r["rfz"]
    F = np.array([fx.sum(), fy.sum(), fz.sum()])
    M = np.array([(r["y"] * fz - r["z"] * fy).sum(), (r["z"] * fx - r["x"] * fz).sum(), (r["x"] * fy - r["y"] * fx).sum()])
    grp = {}
    for lab, m in (("inlet_end_face_z0", np.abs(r["z"]) < 1e-7), ("outlet_end_face_zL", np.abs(r["z"] - L) < 1e-7),
                   ("rotated_direct_FE_nodes", rot)):
        if m.any():
            grp[lab] = {"n": int(m.sum()), "Fx": float(fx[m].sum()), "Fy": float(fy[m].sum()), "Fz": float(fz[m].sum()),
                        "max_abs_nodal": float(np.max(np.abs(np.concatenate([fx[m], fy[m], fz[m]]))))}
    rows = [{"node": int(n), "x": float(x), "y": float(y), "z": float(z), "RF_nodalCS": [float(a), float(b), float(cc)],
             "F_global": [float(p), float(q), float(s)]}
            for n, x, y, z, a, b, cc, p, q, s in zip(r["node"], r["x"], r["y"], r["z"], r["rfx"], r["rfy"], r["rfz"], fx, fy, fz)
            if n in ROT[c]]
    return {"n_constrained_nodes": int(len(r["node"])), "sum_F_N": F.tolist(), "sum_M_about_origin_Nm": M.tolist(),
            "groups": grp, "rotated_nodes": rows, "max_abs_nodal_reaction_N": float(np.max(np.abs(np.concatenate([fx, fy, fz]))))}


RE = {c: reactions(c) for c in CASES}
R["reactions"] = RE
# section force N(z) along the whole duct (internal equilibrium)
R["section_force"] = {}
for c in CASES:
    N = np.array([p["N_z_N"] for p in PROF[c]])
    R["section_force"][c] = {"N_min_N": float(N.min()), "N_max_N": float(N.max()), "N_mean_N": float(N.mean()),
                             "N_midspan_N": float(N[np.argmin(np.abs(zc - 0.3))])}

# ---------------- 5. LC1 free expansion: FE vs independent integral vs analytical
d1 = D["LC1"]
p1 = PROF["LC1"]
uz_out_mean = p1[-1]["uz_mean_m"]
uz_in_mean = p1[0]["uz_mean_m"]
dL_fe = uz_out_mean - uz_in_mean
eth_mean_z = np.array([p["eps_th_mean"] for p in p1])
eth_E_z = np.array([p["eps_th_Eweighted"] for p in p1])
dL_int_area = zint(eth_mean_z)
dL_int_E = zint(eth_E_z)
eth_direct_mean = []
for z, idx in CORNER:
    A, _, _ = section_integral(d1, idx, np.ones_like(d1["T"]))
    v, _, _ = section_integral(d1, idx, eps_th_direct(d1["T"]))
    eth_direct_mean.append(v / A)
dL_int_direct = zint(np.array(eth_direct_mean))
Tvol = zint(np.array([p["T_mean_K"] for p in p1])) / L
dL_simple_cfd_mean = float(eps_th(Tvol - 273.15) * L)
R["LC1_expansion"] = {
    "FE_dL_mean_face_m": dL_fe, "FE_uz_outlet_face_mean_m": uz_out_mean, "FE_uz_inlet_face_mean_m": uz_in_mean,
    "FE_uz_outlet_outer_mean_m": p1[-1]["uz_outer_m"], "FE_uz_outlet_bore_mean_m": p1[-1]["uz_bore_m"],
    "FE_uz_max_m": EX["LC1"]["axial_deformation_uz_m"]["max"],
    "independent_integral_area_mean_m": dL_int_area, "independent_integral_E_weighted_m": dL_int_E,
    "independent_integral_direct_secant_form_m": dL_int_direct,
    "simple_estimate_CFD_volume_mean_T_m": dL_simple_cfd_mean, "CFD_volume_mean_T_K": Tvol,
    "section2_analytical_m": 2.096e-3, "section2_basis": "alpha 13.72e-6 x 254.7 K x 0.600 m (uniform mean rise, Section 2)",
    "FE_vs_integral_E_rel": dL_fe / dL_int_E - 1, "FE_vs_section2_rel": dL_fe / 2.096e-3 - 1,
    "integral_vs_section2_rel": dL_int_E / 2.096e-3 - 1}
# bore / radial growth
mid = int(np.argmin(np.abs(zc - 0.3)))
R["LC1_radial"] = {"ur_outer_midspan_m": p1[mid]["ur_outer_m"], "ur_bore_midspan_m": p1[mid]["ur_bore_m"],
                   "ur_bore_simple_alphaDT_r_m": float(eps_th(p1[mid]["T_bore_K"] - 273.15) * RI),
                   "section2_bore_growth_m": 34.94e-6}
# LC1 mid-span through-wall stress vs Timoshenko (log T distribution) with the CFD mid-span wall temperatures
Tb, To = p1[mid]["T_bore_K"], p1[mid]["T_outer_K"]
dT = To - Tb
Em = float(E_of(0.5 * (Tb + To) - 273.15))
am = float((eps_th(To - 273.15) - eps_th(Tb - 273.15)) / (To - Tb))  # tangent-like alpha over the wall range
a, b = RI, RO
lnb = math.log(b / a)


# Timoshenko & Goodier thick cylinder, radial temperature T(r), generalised plane strain with free ends (zero net axial
# force), constant E and alpha evaluated for the local wall temperature range. Integrals evaluated numerically.
def timo_numeric(r_eval):
    """plane-strain generalised (free ends) thick-cylinder thermal stress for T(r) = Ta + dT ln(r/a)/ln(b/a), constant E, alpha"""
    rr = np.linspace(a, b, 20001)
    Tr = dT * np.log(rr / a) / lnb  # rise above bore temperature (only differences matter)
    I = lambda r: np.trapezoid(Tr[rr <= r] * rr[rr <= r], rr[rr <= r]) if r > a else 0.0
    Ib = I(b)
    Tmean = 2 * Ib / (b ** 2 - a ** 2)
    k = Em * am / (1 - NU)
    out = {}
    for r in r_eval:
        Ir = I(r)
        Trr = dT * math.log(r / a) / lnb
        s_r = k / r ** 2 * ((r ** 2 - a ** 2) / (b ** 2 - a ** 2) * Ib - Ir)
        s_t = k / r ** 2 * ((r ** 2 + a ** 2) / (b ** 2 - a ** 2) * Ib + Ir - Trr * r ** 2)
        s_z = k * (Tmean - Trr)  # free ends: zero net axial force
        out[r] = {"s_r": s_r, "s_t": s_t, "s_z": s_z, "vm": math.sqrt(0.5 * ((s_r - s_t) ** 2 + (s_t - s_z) ** 2 + (s_z - s_r) ** 2))}
    return out


tm = timo_numeric([a, b])
bi, bo = theta_avg_at(d1, CORNER[mid][1], RI), theta_avg_at(d1, CORNER[mid][1], RO)
bi, bo = bi[CN[bi]], bo[CN[bo]]
R["LC1_midspan_vs_timoshenko"] = {
    "z_m": float(zc[mid]), "T_bore_K": Tb, "T_outer_K": To, "dT_wall_K": dT, "E_used_Pa": Em, "alpha_used": am,
    "FE_bore": {"s_t": float(d1["st"][bi].mean()), "s_z": float(d1["sz"][bi].mean()), "s_r": float(d1["sr"][bi].mean()), "vm": float(d1["seqv"][bi].mean())},
    "FE_outer": {"s_t": float(d1["st"][bo].mean()), "s_z": float(d1["sz"][bo].mean()), "s_r": float(d1["sr"][bo].mean()), "vm": float(d1["seqv"][bo].mean())},
    "timoshenko_bore": tm[a], "timoshenko_outer": tm[b],
    "section2": {"hoop_bore_MPa": 16.31, "hoop_outer_MPa": -10.34, "vm_peak_MPa": 16.31, "dT_wall_K": 7.28}}

# ---------------- 6. LC2 restrained: mean axial stress vs analytical on the CFD basis
p2 = PROF["LC2"]
Ebar = np.array([p["E_mean_Pa"] for p in p2])
N_an = -dL_int_E / zint(1.0 / (Ebar * A_SEC))
N_fe = R["section_force"]["LC2"]["N_mean_N"]
R["LC2_axial"] = {
    "FE_section_force_N": N_fe, "FE_reaction_inlet_Fz_N": RE["LC2"]["groups"]["inlet_end_face_z0"]["Fz"],
    "FE_reaction_outlet_Fz_N": RE["LC2"]["groups"]["outlet_end_face_zL"]["Fz"],
    "FE_mean_axial_stress_Pa": N_fe / A_SEC, "analytical_CFD_field_N": N_an, "analytical_CFD_field_mean_stress_Pa": N_an / A_SEC,
    "FE_vs_analytical_rel": N_fe / N_an - 1,
    "section2_stress_Pa": -657.2e6, "section2_basis": "-E alpha dT with E 188.1 GPa, alpha 13.72e-6, dT 254.7 K (uniform)",
    "section2_rescaled_to_CFD_mean_rise_Pa": -657.2e6 * (Tvol - 300.0) / 254.7}
R["LC2_profile_summary"] = {
    "seqv_outer_min_max_MPa": [min(p["seqv_outer_Pa"] for p in p2) / 1e6, max(p["seqv_outer_Pa"] for p in p2) / 1e6],
    "seqv_bore_min_max_MPa": [min(p["seqv_bore_Pa"] for p in p2) / 1e6, max(p["seqv_bore_Pa"] for p in p2) / 1e6],
    "midspan": {k: p2[mid][k] for k in ("seqv_bore_Pa", "seqv_outer_Pa", "sz_bore_Pa", "sz_outer_Pa", "st_bore_Pa", "st_outer_Pa", "T_bore_K", "T_outer_K")}}


# near-restraint vs interior
def zone_max(c, q="seqv"):
    d = D[c]
    zz = d["z"]
    out = {}
    for lab, m in (("inlet_zone_z<15mm", zz < 0.015), ("outlet_zone_z>585mm", zz > 0.585), ("interior_15-585mm", (zz >= 0.015) & (zz <= 0.585)),
                   ("interior_50-550mm", (zz >= 0.05) & (zz <= 0.55))):
        ii = np.where(m & CN)[0]
        k = ii[np.argmax(d[q][ii])]
        out[lab] = {"max_Pa": float(d[q][k]), "at": where(d, k), "surface": surface(d, k)}
    return out


R["zones"] = {c: zone_max(c) for c in CASES}

# ---------------- 7. pressure effect (LC2P - LC2), full precision
d2, d3 = D["LC2"], D["LC2P"]
dvm = (d3["seqv"] - d2["seqv"])[CN]
R["pressure"] = {
    "definition": "LC2P = LC2 + uniform 443.41 Pa gauge on the bore (CFD wall maximum; bound of p(z) = 407.36 - 681.55 z)",
    "vm_max_LC2_Pa": float(d2["seqv"].max()), "vm_max_LC2P_Pa": float(d3["seqv"].max()),
    "vm_max_diff_Pa": float(d3["seqv"].max() - d2["seqv"].max()),
    "vm_max_diff_pct": float(100 * (d3["seqv"].max() - d2["seqv"].max()) / d2["seqv"].max()),
    "same_max_node": bool(np.argmax(d3["seqv"]) == np.argmax(d2["seqv"])),
    "nodewise_dvm_min_Pa": float(dvm.min()), "nodewise_dvm_max_Pa": float(dvm.max()),
    "usum_max_LC2_m": float(d2["usum"].max()), "usum_max_LC2P_m": float(d3["usum"].max()),
    "usum_max_diff_m": float(d3["usum"].max() - d2["usum"].max()),
    "ur_max_LC2_m": float(d2["ur"].max()), "ur_max_LC2P_m": float(d3["ur"].max()),
    "mech_native_vm_max_LC2": MECH["LC2"].get("Equivalent_Stress_averaged", {}).get("max"),
    "mech_native_vm_max_LC2P": MECH["LC2P"].get("Equivalent_Stress_averaged", {}).get("max")}
# Lame check at mid-span (plane strain, eps_z = 0 because both ends are held)
idx = CORNER[mid][1]
p = 443.41
Eb = float(E_of(d2["T"][theta_avg_at(d2, idx, RI)].mean()))
lam = {"s_t_bore": p * (b ** 2 + a ** 2) / (b ** 2 - a ** 2), "s_r_bore": -p, "s_t_outer": 2 * p * a ** 2 / (b ** 2 - a ** 2), "s_r_outer": 0.0,
       "s_z": NU * 2 * p * a ** 2 / (b ** 2 - a ** 2),
       "u_r_bore_m": (1 + NU) * p * a / (Eb * (b ** 2 - a ** 2)) * ((1 - 2 * NU) * a ** 2 + b ** 2)}
fe = {}
for lab, rad in (("bore", RI), ("outer", RO)):
    ii = theta_avg_at(d2, idx, rad)
    for q in ("st", "sr", "sz", "ur"):
        jj = ii[CN[ii]] if q != "ur" else ii
        fe["%s_%s" % (q, lab)] = float((d3[q][jj] - d2[q][jj]).mean())
R["pressure"]["lame_check_midspan"] = {"lame_constant_E_plane_strain": lam, "FE_LC2P_minus_LC2": fe, "E_bore_Pa": Eb}

# ---------------- 8. local yield, utilisation, margin
UT = {}
for c in CASES:
    d = D[c]
    sy = Sy_of(d["T"])
    u = np.where(CN, d["seqv"] / sy, 0.0)
    i_vm = int(np.argmax(np.where(CN, d["seqv"], 0.0)))
    i_u = int(np.argmax(u))
    UT[c] = {"at_max_vm": {"vm_Pa": float(d["seqv"][i_vm]), "Sy_T_Pa": float(sy[i_vm]), "utilisation": float(u[i_vm]),
                           "margin_Sy_over_vm_minus_1": float(sy[i_vm] / d["seqv"][i_vm] - 1), "loc": where(d, i_vm), "surface": surface(d, i_vm)},
             "max_utilisation_anywhere": {"vm_Pa": float(d["seqv"][i_u]), "Sy_T_Pa": float(sy[i_u]), "utilisation": float(u[i_u]),
                                          "margin": float(sy[i_u] / d["seqv"][i_u] - 1), "loc": where(d, i_u), "surface": surface(d, i_u)},
             "with_scalar_1020MPa_for_reference": float(d["seqv"][i_vm] / 1020e6)}
    ii = np.where((d["z"] >= 0.015) & (d["z"] <= 0.585) & CN)[0]
    k = ii[np.argmax(u[ii])]
    UT[c]["max_utilisation_interior_15-585mm"] = {"vm_Pa": float(d["seqv"][k]), "Sy_T_Pa": float(sy[k]), "utilisation": float(u[k]),
                                                  "margin": float(sy[k] / d["seqv"][k] - 1), "loc": where(d, k), "surface": surface(d, k)}
R["utilisation"] = UT
R["yield_basis"] = {"table_C": SY_T.tolist(), "table_MPa": (SY_V / 1e6).tolist(), "interpolation": "linear between VDM 4127 points",
                    "range_used_C": [float(D["LC1"]["T"].min()), float(D["LC1"]["T"].max())], "extrapolation": "none needed"}

# ---------------- 9. 6B temperature uncertainty (linear sensitivities of THIS solution; no new solve)
mid_eth_slope = float((eps_th(Tvol - 273.15 + 0.5) - eps_th(Tvol - 273.15 - 0.5)))  # d(eps_th)/dT at the volume mean
crit = UT["LC2"]["at_max_vm"]["loc"]
Tc = crit["T_C"]
E_c = float(E_of(Tc))
a_tan_c = float(eps_th(Tc + 0.5) - eps_th(Tc - 0.5))
R["uncertainty_6B"] = {
    "source": "PROJECT_STATE 12.9 (6B three-mesh study): peak solid T -5.1/+1.6 K (best estimate -4.4 K); volume-mean T -3.6/+1.0 K "
              "(best -3.1 K); through-wall dT mid-span -0.013/+0.045 K",
    "LC1_growth": {"d_dL_dTmean_m_per_K": mid_eth_slope * L,
                   "range_m": [mid_eth_slope * L * -3.6, mid_eth_slope * L * 1.0], "best_estimate_m": mid_eth_slope * L * -3.1},
    "LC2_axial_stress_uniform_shift": {"note": "a uniform shift dT of the whole field changes the restrained mean stress by about -E_bar alpha_tan dT",
                                       "dsigma_per_K_Pa": float(-Ebar.mean() * mid_eth_slope),
                                       "range_Pa": [float(-Ebar.mean() * mid_eth_slope * -3.6), float(-Ebar.mean() * mid_eth_slope * 1.0)],
                                       "best_estimate_Pa": float(-Ebar.mean() * mid_eth_slope * -3.1)},
    "LC2_local_peak": {"T_crit_K": crit["T_K"], "E_crit_Pa": E_c, "alpha_tan_crit": a_tan_c,
                       "note": "upper bound on the local change if the peak-temperature uncertainty applied fully at the critical point",
                       "range_Pa": [E_c * a_tan_c * -5.1, E_c * a_tan_c * 1.6]},
    "LC1_through_wall": {"note": "mid-span through-wall stress scales with dT_wall", "rel_range": [-0.013 / dT, 0.045 / dT]}}


# ---------------- 10. mesh-sensitivity PREPARATION (inspection only; nothing refined)
XY = {n: i for i, n in enumerate(D["LC1"]["node"])}
cen_idx = np.vectorize(XY.get)(EL[:, 1:9])
cz = D["LC1"]["z"][cen_idx].mean(axis=1)
cr = D["LC1"]["r"][cen_idx].mean(axis=1)
MS = {}
for c in CASES:
    se = np.loadtxt(os.path.join(S8, "Exports", c, "%s_Structural_Error.txt" % c), skiprows=1)
    emap = dict(zip(se[:, 0].astype(int), se[:, 1]))
    err = np.array([emap[e] for e in EL[:, 0]])
    order = np.argsort(err)[::-1]
    tot = err.sum()
    zones = {"inlet z<15mm": cz < 0.015, "outlet z>585mm": cz > 0.585, "interior": (cz >= 0.015) & (cz <= 0.585)}
    MS[c] = {"total_J": float(tot), "max_J": float(err.max()), "mean_J": float(err.mean()),
             "share_by_zone": {k: float(err[m].sum() / tot) for k, m in zones.items()},
             "elements_by_zone": {k: int(m.sum()) for k, m in zones.items()},
             "top10": [{"element": int(EL[i, 0]), "err_J": float(err[i]), "z_mm": round(1e3 * cz[i], 3), "r_mid_mm": round(1e3 * cr[i], 3)} for i in order[:10]]}
    # element error vs axial position (per ring of 36 x 5 elements)
    zr = np.round(cz, 7)
    zs = np.unique(zr)
    MS[c]["ring_error_first5_mm_J"] = [(round(1e3 * z, 3), float(err[zr == z].sum())) for z in zs[:5]]
    MS[c]["ring_error_mid_J"] = float(err[zr == zs[len(zs) // 2]].sum())
    MS[c]["ring_error_last3_mm_J"] = [(round(1e3 * z, 3), float(err[zr == z].sum())) for z in zs[-3:]]
# strain energy U (for normalising the structural error): u = [s_r^2+s_t^2+s_z^2 - 2 nu (s_r s_t + s_t s_z + s_z s_r)]/(2E),
# shear neglected (the cylindrical components are near-principal here), integrated over corner planes (trapezoid r and z)
for c in CASES:
    d = D[c]
    Eloc = E_of(d["T"])
    ued = (d["sr"] ** 2 + d["st"] ** 2 + d["sz"] ** 2 - 2 * NU * (d["sr"] * d["st"] + d["st"] * d["sz"] + d["sz"] * d["sr"])) / (2 * Eloc)
    Uz = np.array([section_integral_corner(d, idx, ued)[0] for z, idx in CORNER])
    U = float(np.trapezoid(Uz, zc))
    MS[c]["strain_energy_J"] = U
    MS[c]["energy_norm_error_estimate_pct"] = float(100 * math.sqrt(MS[c]["total_J"] / (U + MS[c]["total_J"])))
R["mesh_sensitivity_prep"] = {"structural_error": MS,
                              "averaged_vs_unaveraged_vm_max": {c: {"averaged_Pa": MECH[c]["Equivalent_Stress_averaged"]["max"],
                                                                     "unaveraged_Pa": MECH[c]["Equivalent_Stress_UNaveraged"]["max"],
                                                                     "rel_diff": MECH[c]["Equivalent_Stress_UNaveraged"]["max"] / MECH[c]["Equivalent_Stress_averaged"]["max"] - 1}
                                                                for c in CASES},
                              "element_sizes": {"axial_first_mm": R["mesh_planes"]["first_element_axial_length_mm"],
                                                "axial_largest_mm": R["mesh_planes"]["largest_element_axial_length_mm"],
                                                "radial_mm": 2.0, "circumferential_deg": 10.0, "circumferential_outer_arc_mm": 2 * math.pi * 20 / 36}}
# near-end gradient of the peak quantities (plane by plane, max over the plane at the surface of the peak)
def near_end(c, radius, q="seqv", n=12, end="inlet"):
    d = D[c]
    rows = []
    seq = CORNER[:n] if end == "inlet" else CORNER[::-1][:n]
    for z, idx in seq:
        ii = theta_avg_at(d, idx, radius)
        ii = ii[CN[ii]]
        rows.append((round(1e3 * z, 4), float(d[q][ii].max()), float(d[q][ii].mean()), float(d["TK"][ii].mean())))
    return rows
R["near_end"] = {"LC1_bore_inlet_vm": near_end("LC1", RI), "LC1_outer_inlet_vm": near_end("LC1", RO),
                 "LC2_outer_inlet_vm": near_end("LC2", RO), "LC2_bore_inlet_vm": near_end("LC2", RI),
                 "LC2_outer_outlet_vm": near_end("LC2", RO, end="outlet"), "LC1_bore_outlet_vm": near_end("LC1", RI, end="outlet"),
                 "columns": ["z_mm", "max_over_theta_Pa", "theta_mean_Pa", "T_mean_K"]}
# circumferential ripple at the LC2 peak ring and LC1 support ring
def ring(c, z, radius):
    d = D[c]
    m = (np.abs(d["z"] - z) < 1e-7) & (np.abs(d["r"] - radius) < 1e-7) & CN
    ii = np.where(m)[0]
    return {"n": int(len(ii)), "vm_min_Pa": float(d["seqv"][ii].min()), "vm_max_Pa": float(d["seqv"][ii].max()),
            "vm_mean_Pa": float(d["seqv"][ii].mean()), "T_min_K": float(d["TK"][ii].min()), "T_max_K": float(d["TK"][ii].max()),
            "theta_of_vm_max": float(d["th"][ii][np.argmax(d["seqv"][ii])]), "theta_of_T_max": float(d["th"][ii][np.argmax(d["TK"][ii])])}
R["rings"] = {"LC2_inlet_outer_ring": ring("LC2", 0.0, RO), "LC2_midspan_outer_ring": ring("LC2", 0.3, RO),
              "LC1_inlet_outer_ring": ring("LC1", 0.0, RO), "LC1_inlet_bore_plane_z6.52": ring("LC1", CORNER[3][0], RI)}
sup = [int(np.where(D["LC1"]["node"] == n)[0][0]) for n in ROT["LC1"]]
R["rings"]["LC1_support_nodes_vm_Pa"] = {int(D["LC1"]["node"][i]): float(D["LC1"]["seqv"][i]) for i in sup}

# ---------------- 11. Mechanical export (5 significant digits) vs full-precision table at the corner nodes
XC = {}
for c in ("LC1", "LC2"):
    ex = np.loadtxt(os.path.join(S8, "Exports", c, "%s_Equivalent_Stress_averaged.txt" % c), skiprows=1)
    em = dict(zip(ex[:, 0].astype(int), ex[:, 1]))
    ii = np.where(CN)[0]
    v = np.array([em[n] for n in D[c]["node"][ii]])
    XC[c] = {"corner_nodes": int(len(ii)), "max_rel_diff": float(np.max(np.abs(v / D[c]["seqv"][ii] - 1)))}
R["export_vs_table_vm"] = XC

json.dump(R, open(os.path.join(OUT, "post_7B_results.json"), "w"), indent=1, default=float)
print(json.dumps({k: R[k] for k in ("gate", "temperature_check", "LC1_expansion", "LC2_axial", "pressure", "utilisation")}, indent=1, default=float)[:12000])
