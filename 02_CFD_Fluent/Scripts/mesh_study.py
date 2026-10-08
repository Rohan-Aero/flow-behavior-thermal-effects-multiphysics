# -*- coding: utf-8 -*-
"""
Section 6B - THREE-MESH INDEPENDENCE STUDY (coarse 51,840 / medium 159,840 / fine 500,580 cells).

Reads ONLY saved, converged Fluent results (read-only):
  06_Fluent_CFD/Mesh_Independence/Coarse/{coarse_cfd_results.json, Profiles/axial_profiles_cfd.csv, Exports/wall_interface.csv}
  06_Fluent_CFD/{Baseline/cfd_baseline_results.json, Profiles/axial_profiles_cfd.csv, Exports/wall_interface.csv}
  06_Fluent_CFD/Mesh_Independence/Fine/{fine_cfd_results.json, Profiles/axial_profiles_cfd.csv, Exports/wall_interface.csv}
  06_Fluent_CFD/Diagnostics/F029_Isothermal/iso_results.json      (F-029 diagnostic, optional)
  02_Engineering_Calculations/baseline_results.csv                  (frozen Section 2)
Writes only into 09_Mesh_Independence/.

Method (all choices are explained in 09_Mesh_Independence/Mesh_Independence_Report.md and MESH_INDEPENDENCE_AUDIT.md):
  * matched definitions: every location-dependent quantity is re-evaluated from each mesh's slab profile at the
    same physical z (linear interpolation between slab centres) or over the same exact window (x/D 18-29)
  * geometry (polygon faceting) separated from resolution: exact corrections where conservation fixes them
    (mass flow, heat input, bulk temperatures); estimated, NOT applied, where only a correlation relates them
  * grid convergence after Celik et al. (2008, ASME J. Fluids Eng. 130, 078001): apparent order by fixed-point
    iteration with the actual refinement ratios r = (N_fine/N_coarse)^(1/3), Richardson extrapolation and GCI
    only where convergence is monotonic and the apparent order is credible
RE-ANALYSIS 2026 - not an original internship result.
"""
from __future__ import print_function
import os, json, math, csv, shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)                                     # 09_Mesh_Independence
ROOT = os.path.dirname(OUT)
CFD = os.path.join(ROOT, "06_Fluent_CFD")
DIRS = {k: os.path.join(OUT, k) for k in ("Raw_Data", "Geometry_Correction", "Comparison_Tables", "Plots", "Uncertainty")}
for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

LEVELS = ["coarse", "medium", "fine"]
SRC = {"coarse": os.path.join(CFD, "Mesh_Independence", "Coarse"), "medium": CFD,
       "fine": os.path.join(CFD, "Mesh_Independence", "Fine")}
JSONF = {"coarse": "coarse_cfd_results.json", "medium": os.path.join("Baseline", "cfd_baseline_results.json"),
         "fine": "fine_cfd_results.json"}
MESH = {"coarse": dict(cells=51840, NT=32, NZ=60, NR=18, NRS=7, NC=8),
        "medium": dict(cells=159840, NT=48, NZ=90, NR=24, NRS=10, NC=12),
        "fine": dict(cells=500580, NT=72, NZ=135, NR=32, NRS=15, NC=18)}
WALLCLOCK_MIN = {"coarse": 9.0, "medium": 13.0, "fine": None}      # fine filled from its driver log if present
L, D, RI, RO, QPP, P_OP = 0.600, 0.020, 0.010, 0.020, 8000.0, 101325.0
AIR_T = np.array([250., 300., 350., 400., 450., 500., 550., 600.])
AIR_CP = np.array([1006., 1007., 1009., 1014., 1021., 1030., 1040., 1051.])
_Tg = np.linspace(250.0, 600.0, 70001)
_cp = np.interp(_Tg, AIR_T, AIR_CP)
_hg = np.concatenate([[0.0], np.cumsum(0.5 * (_cp[1:] + _cp[:-1]) * np.diff(_Tg))])
h_of_T = lambda T: float(np.interp(T, _Tg, _hg))
T_of_h = lambda h: float(np.interp(h, _hg, _Tg))
C = {"coarse": "#eb6834", "medium": "#2a78d6", "fine": "#1baf7a"}
GREY = "#5a5a5a"
PROV = ("ANSYS Fluent 2026 R1, three converged solutions with identical physics (coarse 51,840 / medium 159,840 / "
        "fine 500,580 cells); matplotlib render of exported Fluent results. RE-ANALYSIS 2026.")


def read_profile(path):
    with open(path) as fh:
        fh.readline()
        hdr = fh.readline().strip().split(",")
        a = np.loadtxt(fh, delimiter=",")
    return {h: a[:, i] for i, h in enumerate(hdr)}


def read_ascii(path):
    with open(path) as fh:
        cols = [c.strip() for c in fh.readline().strip().split(",")]
        a = np.loadtxt(fh, delimiter=",")
    return {c: a[:, i] for i, c in enumerate(cols[:a.shape[1]])}


def window_mean(x, y, a=18.0, b=29.0):
    xs = np.linspace(a, b, 2201)
    return float(np.trapz(np.interp(xs, x, y), xs) / (b - a))


# ============================================================================
# 1. load
# ============================================================================
R, P, W = {}, {}, {}
for lv in LEVELS:
    R[lv] = json.load(open(os.path.join(SRC[lv], JSONF[lv])))
    P[lv] = read_profile(os.path.join(SRC[lv], "Profiles", "axial_profiles_cfd.csv"))
    wi = read_ascii(os.path.join(SRC[lv], "Exports", "wall_interface.csv"))
    wi["th"] = np.degrees(np.arctan2(wi["y-coordinate"], wi["x-coordinate"])) % 360.0
    W[lv] = wi
    shutil.copy(os.path.join(SRC[lv], JSONF[lv]), os.path.join(DIRS["Raw_Data"], "%s_cfd_results.json" % lv))
    shutil.copy(os.path.join(SRC[lv], "Profiles", "axial_profiles_cfd.csv"),
                os.path.join(DIRS["Raw_Data"], "%s_axial_profiles_cfd.csv" % lv))
drv = os.path.join(SRC["fine"], "Logs", "fine_driver.txt")
if os.path.isfile(drv):
    import datetime as _dt
    st = en = None
    for l in open(drv):
        t = _dt.datetime.strptime(l[:19], "%Y-%m-%d %H:%M:%S")
        if "launching" in l:
            st = t
        if "fluent exited" in l:
            en = t
    if st and en:
        WALLCLOCK_MIN["fine"] = (en - st).total_seconds() / 60.0
ana = {}
with open(os.path.join(ROOT, "02_Engineering_Calculations", "baseline_results.csv")) as fh:
    for r in csv.reader(fh):
        if len(r) == 4 and r[0] and not r[0].startswith("#") and r[0] != "section":
            try:
                ana[r[1]] = float(r[2])
            except ValueError:
                pass
ISO = None
isop = os.path.join(CFD, "Diagnostics", "F029_Isothermal", "iso_results.json")
ISOPROF = None
if os.path.isfile(isop):
    ISO = json.load(open(isop))
    ISOPROF = read_profile(os.path.join(CFD, "Diagnostics", "F029_Isothermal", "iso_f_profile.csv"))

# ============================================================================
# 2. geometry of the inscribed polygons (exact)
# ============================================================================
GEO = {}
for lv in LEVELS + ["circle"]:
    N = MESH[lv]["NT"] if lv != "circle" else None
    if N is None:
        GEO[lv] = dict(N="inf", planar=1.0, lateral=1.0, Dh_over_D=1.0, apothem_over_R=1.0)
    else:
        GEO[lv] = dict(N=N, planar=(N / (2 * math.pi)) * math.sin(2 * math.pi / N),
                       lateral=math.sin(math.pi / N) / (math.pi / N), Dh_over_D=math.cos(math.pi / N),
                       apothem_over_R=math.cos(math.pi / N))
    g = GEO[lv]
    g["flow_area_m2"] = math.pi * RI ** 2 * g["planar"]
    g["wetted_perimeter_m"] = 2 * math.pi * RI * g["lateral"]
    g["outer_area_m2"] = 2 * math.pi * RO * L * g["lateral"]
    g["Q_expected_W"] = QPP * g["outer_area_m2"]
    g["Q_over_mdot_factor"] = g["lateral"] / g["planar"]

# ============================================================================
# 3. per-mesh quantities, identical definitions
# ============================================================================
V = {}
for lv in LEVELS:
    r, p = R[lv], P[lv]
    at = lambda arr, z: float(np.interp(z, p["z"], arr))
    cons, pr, tm, yp, fd, mc = r["conservation"], r["pressure"], r["temperatures"], r["yplus"], r["fully_developed"], r["mixing_cup"]
    v = dict(
        cells=MESH[lv]["cells"], NT=MESH[lv]["NT"],
        mdot_gs=1e3 * cons["mdot_in"], mdot_out_gs=1e3 * cons["mdot_out"],
        dp=pr["dp_total_area"], dp_wall=pr["dp_wall_shear"], dp_acc=pr["dp_accel_1D_cfd_densities"],
        dp_prof=pr["dp_profile_development"],
        Re_in=r["reynolds"]["Re_in_nominalD"], Re_out=r["reynolds"]["Re_out_nominalD"],
        T_out=tm["T_out_bulk_monitor"], T_mix=mc["T_out_mixing_cup"], T_eb=mc["T_out_from_cfd_energy_balance"],
        Q=cons["Q_wall"], Q_fluid=cons["Q_fluid"],
        T_max=tm["T_outer_wall_max"], T_max_cell=tm["T_solid_max"], T_min=tm["T_solid_min"],
        T_inner_max=tm["T_inner_wall_max"], T_inner_min=tm["T_inner_wall_min"],
        T_outer_min=tm["T_outer_wall_min"], T_inner_avg=tm["T_inner_wall_area_avg"], T_outer_avg=tm["T_outer_wall_area_avg"],
        T_solid_mean=tm["T_solid_mean_volume"],
        dTw_300=at(p["dTwall"], 0.300), dTw_570=at(p["dTwall"], 0.570),
        Twi_300=at(p["Twi"], 0.300), Two_300=at(p["Two"], 0.300), Tb_300=at(p["Tb_mass"], 0.300),
        h_300=at(p["h"], 0.300), qi_300=at(p["qi"], 0.300),
        Nu_fd=window_mean(p["x_over_D"], p["Nu"]), f_fd=window_mean(p["x_over_D"], p["f_shear"]),
        Nu_fd_slabmean=fd["Nu_cfd"], f_fd_slabmean=fd["f_cfd"],
        f_pet_fd=window_mean(p["x_over_D"], (0.790 * np.log(p["Re"]) - 1.64) ** -2),
        TwTb_fd=window_mean(p["x_over_D"], p["Twi"] / p["Tb_mass"]),
        yp_min=yp["min"], yp_mean=yp["area_mean"], yp_max=yp["max"], yp_fd=window_mean(p["x_over_D"], p["yplus_avg"]),
        yp_le1=100 * yp["frac_area_le_1"], yp_max_z_mm=yp["location_of_max_mm"]["z"],
        ywall_min_um=yp["first_cell_centre_distance_um"]["min"], ywall_max_um=yp["first_cell_centre_distance_um"]["max"],
        mass_imb_pct=cons["mass_imbalance_pct"], energy_imb_pct=abs(cons["net_all_boundaries_pct"]),
        iters=r["run"]["total_iters"], converged=r["run"]["converged"],
        first_slab_z_mm=1e3 * float(p["z"][0]), last_slab_z_mm=1e3 * float(p["z"][-1]),
    )
    # ---- exact geometric corrections (conservation), to the TRUE CIRCLE
    g = GEO[lv]
    dh = v["Q"] / (1e-3 * v["mdot_gs"])                                   # enthalpy rise on this mesh
    dh_circle = dh * g["planar"] / g["lateral"]                           # same solution, true-circle Q/mdot
    v["dTgeo_exit"] = T_of_h(h_of_T(300.0) + dh) - T_of_h(h_of_T(300.0) + dh_circle)
    v["dTgeo_mid"] = (v["Tb_300"] - 300.0) * (1.0 - g["planar"] / g["lateral"])
    v["mdot_corr"] = v["mdot_gs"] / g["planar"]
    v["Q_corr"] = v["Q"] / g["lateral"]
    v["q_outer_avg"] = v["Q"] / g["outer_area_m2"]
    v["q_inner_avg"] = v["Q"] / (0.5 * g["outer_area_m2"])
    v["T_out_corr"] = v["T_out"] - v["dTgeo_exit"]
    v["T_mix_corr"] = v["T_mix"] - v["dTgeo_exit"]
    v["T_max_corr"] = v["T_max"] - v["dTgeo_exit"]
    v["T_inner_max_corr"] = v["T_inner_max"] - v["dTgeo_exit"]
    v["Twi_300_corr"] = v["Twi_300"] - v["dTgeo_mid"]
    v["Two_300_corr"] = v["Two_300"] - v["dTgeo_mid"]
    # ---- estimated (correlation-based, NOT applied) geometric influence on dp, relative to the true circle
    G = r["reynolds"]["G"]
    Rf = r["fully_developed"]["R_fluent"]
    acc = G ** 2 * Rf * v["dTgeo_exit"] / P_OP                            # exact 1-D ideal-gas acceleration part
    fric_Dh = v["dp_wall"] * (g["Dh_over_D"] ** -1.2 - 1.0)               # Dh^-1.2 (Blasius-type) scaling
    fric_rho = v["dp_wall"] * (v["dTgeo_mid"] / (0.5 * (300.0 + v["T_out"])))
    v["dp_geo_est"] = acc + fric_Dh + fric_rho
    v["dp_geo_parts"] = dict(acceleration_exact_1D=acc, friction_Dh_estimate=fric_Dh, friction_density_estimate=fric_rho)
    v["dp_geoadj"] = v["dp"] - v["dp_geo_est"]
    v["dTw_geo_est_pct"] = 100 * (g["apothem_over_R"] - 1.0)             # thick-wall log scaling with the apothem
    v["h_geo_est_pct"] = 100 * (g["Dh_over_D"] ** -0.2 - 1.0)            # h ~ Dh^-0.2 at fixed G
    V[lv] = v
json.dump(V, open(os.path.join(DIRS["Raw_Data"], "three_mesh_values.json"), "w"), indent=2, default=float)

# ============================================================================
# 4. grid convergence (Celik et al. 2008)
# ============================================================================
N1, N2, N3 = MESH["fine"]["cells"], MESH["medium"]["cells"], MESH["coarse"]["cells"]
r21 = (N1 / N2) ** (1 / 3.)
r32 = (N2 / N3) ** (1 / 3.)


def gci(phi3, phi2, phi1, noise=0.0):
    """phi3 coarse, phi2 medium, phi1 fine."""
    e32, e21 = phi3 - phi2, phi2 - phi1
    out = dict(eps32=e32, eps21=e21, r21=r21, r32=r32)
    scale = max(abs(phi1), 1e-30)
    if abs(e21) <= noise * scale and abs(e32) <= noise * scale:
        out.update(kind="within noise", R=float("nan"))
        return out
    Rr = e21 / e32 if e32 != 0 else float("inf")
    out["R"] = Rr
    if Rr < 0:
        out.update(kind="oscillatory", U_osc=0.5 * (max(phi1, phi2, phi3) - min(phi1, phi2, phi3)))
        return out
    if Rr >= 1:
        out.update(kind="divergent or not in asymptotic range")
        return out
    s = 1.0
    p = abs(math.log(abs(e32 / e21))) / math.log(r21)
    for _ in range(200):
        q = math.log((r21 ** p - s) / (r32 ** p - s))
        pn = abs(math.log(abs(e32 / e21)) + q) / math.log(r21)
        if abs(pn - p) < 1e-10:
            p = pn
            break
        p = pn
    out["kind"] = "monotonic"
    out["p"] = p
    credible = 0.5 <= p <= 4.0
    out["p_credible"] = credible
    pu, Fs = (min(p, 2.0), 1.25) if credible else (2.0, 3.0)
    out["p_used"], out["Fs"] = pu, Fs
    out["phi_ext"] = (r21 ** p * phi1 - phi2) / (r21 ** p - 1) if credible else float("nan")
    out["e_a21"] = abs((phi1 - phi2) / phi1)
    out["e_ext21"] = abs((out["phi_ext"] - phi1) / out["phi_ext"]) if credible else float("nan")
    out["GCI21_pct"] = 100 * Fs * out["e_a21"] / (r21 ** pu - 1)
    e_a32 = abs((phi2 - phi3) / phi2)
    out["GCI32_pct"] = 100 * Fs * e_a32 / (r32 ** pu - 1)
    out["asymptotic_ratio"] = out["GCI32_pct"] / (r21 ** pu * out["GCI21_pct"]) if out["GCI21_pct"] > 0 else float("nan")
    return out


QTY = [
    # key, label, units, fmt, geometry note, is_geometry_corrected_variant_of
    ("mdot_gs", "Mass flow (inlet)", "g/s", "%.4f", "exact: planar area of the polygon", None),
    ("mdot_corr", "Mass flow / planar-area ratio", "g/s", "%.4f", "exact correction", "mdot_gs"),
    ("dp", "Pressure drop, static (area-wtd, inlet - outlet)", "Pa", "%.2f", "estimated: Dh and bulk-T effects", None),
    ("dp_geoadj", "Pressure drop, geometry-adjusted (estimate)", "Pa", "%.2f", "estimated correction", "dp"),
    ("dp_wall", "  wall-shear term", "Pa", "%.2f", "estimated: perimeter/area (Dh)", None),
    ("dp_acc", "  1-D acceleration term", "Pa", "%.2f", "exact: via T_out", None),
    ("T_out", "Outlet temperature, mass-weighted", "K", "%.3f", "exact: Q/mdot of the polygon", None),
    ("T_out_corr", "Outlet temperature, geometry-corrected", "K", "%.3f", "exact correction", "T_out"),
    ("Q", "Heat-transfer rate", "W", "%.3f", "exact: outer area of the polygon", None),
    ("Q_corr", "Heat-transfer rate / lateral-area ratio", "W", "%.3f", "exact correction", "Q"),
    ("T_max", "Maximum solid temperature (outer-wall facet max)", "K", "%.2f", "exact part: bulk shift at exit", None),
    ("T_max_corr", "Maximum solid temperature, geometry-corrected", "K", "%.2f", "exact bulk correction", "T_max"),
    ("T_max_cell", "Maximum solid temperature (cell centre)", "K", "%.2f", "bulk shift at exit", None),
    ("T_min", "Minimum solid temperature (cell centre)", "K", "%.2f", "inlet end; negligible bulk shift", None),
    ("T_inner_max", "Peak inner-wall temperature", "K", "%.2f", "exact part: bulk shift at exit", None),
    ("Twi_300", "Inner-wall temperature, mid-span", "K", "%.2f", "exact part: bulk shift at mid-span", None),
    ("Two_300", "Outer-wall temperature, mid-span", "K", "%.2f", "exact part: bulk shift at mid-span", None),
    ("Twi_300_corr", "Inner-wall temperature, mid-span, geometry-corrected", "K", "%.2f", "exact bulk correction", "Twi_300"),
    ("dTw_300", "Through-wall dT, MID-SPAN z = 300 mm", "K", "%.3f", "estimated: apothem scaling", None),
    ("dTw_570", "Through-wall dT, z = 570 mm", "K", "%.3f", "estimated: apothem scaling", None),
    ("h_300", "h, mid-span", "W/m2K", "%.2f", "estimated: Dh^-0.2, negligible", None),
    ("Nu_fd", "Fully developed Nu (exact window x/D 18-29)", "-", "%.2f", "estimated: Dh^-0.2, negligible", None),
    ("f_fd", "Fully developed Darcy f (exact window x/D 18-29)", "-", "%.5f", "estimated: Dh^-0.2, negligible", None),
    ("T_solid_mean", "Volume-mean solid temperature", "K", "%.2f", "exact part: mean bulk shift", None),
    ("yp_min", "y+ minimum", "-", "%.3f", "O-grid spacing pattern", None),
    ("yp_mean", "y+ area mean", "-", "%.3f", "", None),
    ("yp_fd", "y+ mean, fully developed window", "-", "%.3f", "", None),
    ("yp_max", "y+ maximum", "-", "%.3f", "first-slab sampling position differs", None),
    ("Re_out", "Reynolds number, outlet", "-", "%.0f", "via T_out (exact)", None),
    ("mass_imb_pct", "Mass imbalance", "%", "%.1e", "", None),
    ("energy_imb_pct", "Energy imbalance", "%", "%.1e", "", None),
]
NOISE = 2e-6          # relative changes below this are round-off for single-precision-coordinate exports
# Absolute temperatures are judged on their RISE above the 300 K inlet: a 1 K change is 0.2 % of 560 K but 0.4 %
# of the 260 K rise that the CFD actually computes. Percentages of absolute kelvin would flatter the result.
TEMP_ABS = {"T_out", "T_out_corr", "T_max", "T_max_corr", "T_max_cell", "T_min", "T_inner_max", "Twi_300", "Two_300",
            "Twi_300_corr", "T_solid_mean"}
T_REF = 300.0
GC = {}
rows_raw = []
for key, lab, u, fmt, gnote, base in QTY:
    c, m, f = V["coarse"][key], V["medium"][key], V["fine"][key]
    off = T_REF if key in TEMP_ABS else 0.0
    g = gci(c - off, m - off, f - off, noise=NOISE) if key not in ("mass_imb_pct", "energy_imb_pct") else {"kind": "n/a"}
    if "phi_ext" in g and g.get("p_credible"):
        g["phi_ext"] = g["phi_ext"] + off
    g["basis"] = "rise above 300 K" if off else "value"
    if "GCI21_pct" in g:
        g["GCI21_abs"] = g["GCI21_pct"] / 100 * abs(f - off)
        g["GCI32_abs"] = g["GCI32_pct"] / 100 * abs(m - off)
    GC[key] = g
    rows_raw.append(dict(key=key, quantity=lab, units=u, coarse=c, medium=m, fine=f,
                         d_CM=m - c, pct_CM=100 * (m - c) / c, d_MF=f - m, pct_MF=100 * (f - m) / m,
                         d_CF=f - c, pct_CF=100 * (f - c) / c, geometry=gnote,
                         pctrise_CM=100 * (m - c) / (c - off) if off else None,
                         pctrise_MF=100 * (f - m) / (m - off) if off else None))

# ============================================================================
# 5. geometric share of each raw change, and status classification
# ============================================================================
def geo_change(key, a, b):
    """Change from mesh a to mesh b that the polygon geometry alone explains (exact or estimated)."""
    va, vb = V[a], V[b]
    if key == "mdot_gs":
        return va["mdot_gs"] * (GEO[b]["planar"] / GEO[a]["planar"] - 1)
    if key == "Q":
        return va["Q"] * (GEO[b]["lateral"] / GEO[a]["lateral"] - 1)
    if key in ("T_out", "T_max", "T_max_cell", "T_inner_max"):
        return vb["dTgeo_exit"] - va["dTgeo_exit"]
    if key in ("Twi_300", "Two_300"):
        return vb["dTgeo_mid"] - va["dTgeo_mid"]
    if key == "T_solid_mean":
        return 0.5 * (vb["dTgeo_exit"] - va["dTgeo_exit"])
    if key == "dp":
        return vb["dp_geo_est"] - va["dp_geo_est"]
    if key == "dp_acc":
        return vb["dp_geo_parts"]["acceleration_exact_1D"] - va["dp_geo_parts"]["acceleration_exact_1D"]
    if key == "dp_wall":
        return (vb["dp_geo_parts"]["friction_Dh_estimate"] + vb["dp_geo_parts"]["friction_density_estimate"]) - \
               (va["dp_geo_parts"]["friction_Dh_estimate"] + va["dp_geo_parts"]["friction_density_estimate"])
    if key in ("dTw_300", "dTw_570"):
        return va[key] * ((1 + vb["dTw_geo_est_pct"] / 100) / (1 + va["dTw_geo_est_pct"] / 100) - 1)
    if key in ("h_300", "Nu_fd"):
        return va[key] * ((1 + vb["h_geo_est_pct"] / 100) / (1 + va["h_geo_est_pct"] / 100) - 1)
    if key == "f_fd":
        return va[key] * ((GEO[b]["Dh_over_D"] / GEO[a]["Dh_over_D"]) ** -0.2 - 1)
    if key == "Re_out":
        return None
    return None


EXACT_GEO = {"mdot_gs", "Q", "T_out", "T_max", "T_max_cell", "T_inner_max", "Twi_300", "Two_300", "T_solid_mean", "dp_acc"}
STATUS = {}
for row in rows_raw:
    key = row["key"]
    gCM, gMF = geo_change(key, "coarse", "medium"), geo_change(key, "medium", "fine")
    row["geo_CM"], row["geo_MF"] = gCM, gMF
    row["res_CM"] = row["d_CM"] - gCM if gCM is not None else None
    row["res_MF"] = row["d_MF"] - gMF if gMF is not None else None
    g = GC[key]
    rel_MF = abs(row["pctrise_MF"]) if row["pctrise_MF"] is not None else abs(row["pct_MF"])
    geo_dominated = (gCM is not None and abs(row["d_CM"]) > 0 and abs(gCM) >= 0.5 * abs(row["d_CM"])
                     and key in EXACT_GEO)
    if key in ("mass_imb_pct", "energy_imb_pct"):
        st = "A"
        why = "round-off on every mesh"
    elif key == "yp_max":
        st = "E"
        why = ("not a convergence metric: the maximum sits in the first slab, whose centre moves toward the inlet "
               "leading edge as the mesh is refined (%.1f / %.1f / %.1f mm); every value <= 1" %
               tuple(V[l_]["first_slab_z_mm"] for l_ in LEVELS))
    elif key in ("mdot_corr", "Q_corr"):
        st = "A"
        why = "after the exact area correction all three meshes agree to round-off"
    elif geo_dominated:
        st = "D"
        why = "raw change is mostly the polygon geometry (%.0f %% of coarse->medium)" % (100 * gCM / row["d_CM"])
    elif g.get("kind") == "within noise":
        st = "A"
        why = "changes below round-off"
    elif g.get("kind") == "monotonic":
        if rel_MF < 0.5 and g["R"] < 0.8 and g.get("p_credible"):
            st = "A"
            why = "monotonic, R = %.2f, p = %.2f, medium->fine %.2f %%%s" % (
                g["R"], g["p"], row["pctrise_MF"] if row["pctrise_MF"] is not None else row["pct_MF"],
                " of the rise" if row["pctrise_MF"] is not None else "")
        elif rel_MF < 1.0:
            st = "B"
            why = "monotonic, R = %.2f, p = %s, medium->fine %.2f %%%s" % (
                g["R"], ("%.2f" % g["p"]) if g.get("p_credible") else "not credible (%.2f)" % g["p"],
                row["pctrise_MF"] if row["pctrise_MF"] is not None else row["pct_MF"],
                " of the rise" if row["pctrise_MF"] is not None else "")
        else:
            st = "C"
            why = "monotonic but medium->fine still %.2f %%%s" % (
                row["pctrise_MF"] if row["pctrise_MF"] is not None else row["pct_MF"],
                " of the rise" if row["pctrise_MF"] is not None else "")
    elif g.get("kind") == "oscillatory":
        spread = 100 * 2 * g["U_osc"] / abs(row["fine"])
        st = "B" if spread < 0.5 else "E"
        why = "oscillatory, total spread %.2f %%" % spread
    else:
        st = "C" if rel_MF >= 0.5 else "E"
        why = "change did not shrink (R = %.2f); medium->fine %.2f %%" % (g.get("R", float("nan")), row["pct_MF"])
    if (gCM is not None and key not in EXACT_GEO and abs(row["d_CM"]) > 0 and st not in ("D",)
            and key not in ("mdot_corr", "Q_corr")):
        why += "; estimated geometric part of coarse->medium change: %+.3g (raw %+.3g)" % (gCM, row["d_CM"])
    # --- caps added after the first run (review of the status list, Section 6B) ---
    if key == "Re_out":
        st = "D"
        why = ("changes only through mu(T_out) at fixed G = mdot/A; the T_out change is geometric "
               "(same apparent order p = %.2f as T_out)" % g.get("p", float("nan")))
    if key == "dp_geoadj" and st == "A":
        st = "B"
        why += "; capped at B because the adjustment itself is an estimate"
    if (st == "A" and gCM is not None and key not in EXACT_GEO and abs(row["d_CM"]) > 0
            and abs(gCM) >= 0.5 * abs(row["d_CM"])):
        st = "B"
        why += ("; capped at B: the ESTIMATED geometric share of coarse->medium is %.0f %%, so a discretisation-only "
                "trend cannot be isolated (residual changes %+.3g, %+.3g)" % (100 * gCM / row["d_CM"],
                                                                              row["res_CM"], row["res_MF"]))
    STATUS[key] = (st, why)
    row["status"], row["status_basis"] = st, why

# ============================================================================
# 6. write tables
# ============================================================================
def f_(fmt, x):
    try:
        return fmt % x
    except Exception:
        return str(x)


with open(os.path.join(DIRS["Comparison_Tables"], "three_mesh_raw_table.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# Raw three-mesh comparison, identical definitions; C = coarse 51,840, M = medium 159,840, F = fine "
                "500,580 cells. RE-ANALYSIS 2026."])
    w.writerow(["quantity", "units", "coarse", "medium", "fine", "C_to_M_abs", "C_to_M_pct", "M_to_F_abs", "M_to_F_pct",
                "C_to_F_abs", "C_to_F_pct"])
    for r_ in rows_raw:
        w.writerow([r_["quantity"], r_["units"], "%.8g" % r_["coarse"], "%.8g" % r_["medium"], "%.8g" % r_["fine"],
                    "%.5g" % r_["d_CM"], "%.4f" % r_["pct_CM"], "%.5g" % r_["d_MF"], "%.4f" % r_["pct_MF"],
                    "%.5g" % r_["d_CF"], "%.4f" % r_["pct_CF"]])
with open(os.path.join(DIRS["Geometry_Correction"], "faceting_ratios.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# Inscribed regular N-gon vs true circle (R_i = 10 mm, R_o = 20 mm, L = 600 mm). Exact geometry."])
    w.writerow(["section", "N", "planar_area_ratio", "lateral_perimeter_ratio", "Dh_over_D_and_apothem_over_R",
                "flow_area_m2", "wetted_perimeter_m", "outer_heated_area_m2", "Q_at_8000W_m2", "Q_over_mdot_factor"])
    for lv in ["circle"] + LEVELS:
        g = GEO[lv]
        w.writerow([lv, g["N"], "%.7f" % g["planar"], "%.7f" % g["lateral"], "%.7f" % g["Dh_over_D"],
                    "%.8e" % g["flow_area_m2"], "%.8e" % g["wetted_perimeter_m"], "%.8e" % g["outer_area_m2"],
                    "%.4f" % g["Q_expected_W"], "%.7f" % g["Q_over_mdot_factor"]])
with open(os.path.join(DIRS["Geometry_Correction"], "geometry_corrections.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# Geometric corrections to the TRUE CIRCLE. 'exact' = fixed by conservation; 'estimate' = correlation "
                "scaling, reported but NOT applied to any headline value. RE-ANALYSIS 2026."])
    w.writerow(["mesh", "N", "mdot_raw_gs", "mdot_corr_gs", "Q_raw_W", "Q_corr_W", "q_outer_avg_W_m2", "q_inner_avg_W_m2",
                "dT_geo_exit_K_exact", "dT_geo_midspan_K_exact", "T_out_raw", "T_out_corr", "T_max_raw", "T_max_corr",
                "dp_raw", "dp_geo_acceleration_exact_Pa", "dp_geo_friction_Dh_estimate_Pa",
                "dp_geo_friction_density_estimate_Pa", "dp_geoadjusted_estimate", "dTwall_geo_estimate_pct",
                "h_Nu_geo_estimate_pct"])
    for lv in LEVELS:
        v = V[lv]
        gp = v["dp_geo_parts"]
        w.writerow([lv, MESH[lv]["NT"], "%.6f" % v["mdot_gs"], "%.6f" % v["mdot_corr"], "%.4f" % v["Q"], "%.4f" % v["Q_corr"],
                    "%.4f" % v["q_outer_avg"], "%.4f" % v["q_inner_avg"], "%.4f" % v["dTgeo_exit"], "%.4f" % v["dTgeo_mid"],
                    "%.4f" % v["T_out"], "%.4f" % v["T_out_corr"], "%.3f" % v["T_max"], "%.3f" % v["T_max_corr"],
                    "%.3f" % v["dp"], "%.3f" % gp["acceleration_exact_1D"], "%.3f" % gp["friction_Dh_estimate"],
                    "%.3f" % gp["friction_density_estimate"], "%.3f" % v["dp_geoadj"], "%.3f" % v["dTw_geo_est_pct"],
                    "%.3f" % v["h_geo_est_pct"]])
with open(os.path.join(DIRS["Uncertainty"], "gci_analysis.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# Celik et al. (2008) procedure; 1 = fine, 2 = medium, 3 = coarse; r21 = %.4f, r32 = %.4f from total "
                "cells. GCI only where monotonic with credible apparent order. RE-ANALYSIS 2026." % (r21, r32)])
    w.writerow(["quantity", "units", "phi3_coarse", "phi2_medium", "phi1_fine", "eps32", "eps21", "R_eps21_over_eps32",
                "behaviour", "p_apparent", "p_credible", "p_used", "Fs", "phi_extrapolated", "e_a21_pct", "e_ext21_pct",
                "GCI_fine21_pct", "GCI_medium32_pct", "asymptotic_ratio", "U_oscillatory_half_range", "basis",
                "GCI_fine21_abs", "GCI_medium32_abs"])
    for key, lab, u, fmt, gnote, base in QTY:
        g = GC[key]
        if g.get("kind") == "n/a":
            continue
        w.writerow([lab, u, "%.8g" % V["coarse"][key], "%.8g" % V["medium"][key], "%.8g" % V["fine"][key],
                    "%.5g" % g.get("eps32", float("nan")), "%.5g" % g.get("eps21", float("nan")),
                    "%.4f" % g.get("R", float("nan")), g.get("kind"), "%.3f" % g.get("p", float("nan")),
                    g.get("p_credible", ""), "%.2f" % g.get("p_used", float("nan")), g.get("Fs", ""),
                    "%.8g" % g.get("phi_ext", float("nan")), "%.4f" % (100 * g.get("e_a21", float("nan"))),
                    "%.4f" % (100 * g.get("e_ext21", float("nan"))), "%.4f" % g.get("GCI21_pct", float("nan")),
                    "%.4f" % g.get("GCI32_pct", float("nan")), "%.3f" % g.get("asymptotic_ratio", float("nan")),
                    "%.5g" % g.get("U_osc", float("nan")), g.get("basis", ""), "%.5g" % g.get("GCI21_abs", float("nan")),
                    "%.5g" % g.get("GCI32_abs", float("nan"))])

MASTER_KEYS = [("mdot_gs", "%.4f"), ("mdot_corr", "%.4f"), ("dp", "%.2f"), ("dp_geoadj", "%.2f"), ("T_out", "%.3f"),
               ("T_out_corr", "%.3f"), ("Q", "%.2f"), ("Q_corr", "%.2f"), ("T_max", "%.2f"), ("T_max_corr", "%.2f"),
               ("T_min", "%.2f"), ("T_inner_max", "%.2f"), ("Twi_300", "%.2f"), ("Two_300", "%.2f"),
               ("dTw_300", "%.3f"), ("dTw_570", "%.3f"), ("h_300", "%.2f"), ("Nu_fd", "%.2f"), ("f_fd", "%.5f"),
               ("T_solid_mean", "%.2f"), ("Re_out", "%.0f"), ("yp_mean", "%.3f"), ("yp_max", "%.3f"), ("yp_min", "%.3f"),
               ("mass_imb_pct", "%.1e"), ("energy_imb_pct", "%.1e")]
byk = {r_["key"]: r_ for r_ in rows_raw}
with open(os.path.join(OUT, "MESH_INDEPENDENCE_RESULTS.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# Master table, Section 6B three-mesh study. Status: A clearly convergent, B approximately convergent, "
                "C still changing materially, D affected by geometry/faceting, E inconclusive. RE-ANALYSIS 2026."])
    w.writerow(["quantity", "units", "coarse_51840", "medium_159840", "fine_500580", "coarse_to_medium_pct",
                "medium_to_fine_pct", "coarse_to_medium_pct_of_rise", "medium_to_fine_pct_of_rise", "geometry_part_C_to_M", "geometry_part_M_to_F", "geometry_basis",
                "extrapolated", "GCI_fine_pct", "GCI_fine_abs", "GCI_basis", "status", "status_basis"])
    CIRCLE = {"mdot_gs": "mdot_corr", "Q": "Q_corr", "T_out": "T_out_corr"}
    for key, fmt in MASTER_KEYS:
        r_ = byk[key]
        g = dict(GC[key])
        basis_txt = r_["status_basis"]
        if r_["status"] == "D":
            # a GCI would present geometric convergence toward the circle as discretisation uncertainty: suppress it
            if key in CIRCLE and g.get("p_credible"):
                circ = V["fine"][CIRCLE[key]]
                basis_txt += ("; Richardson limit %.6g vs exact circle value %.6g (%+.4f %%): the sequence converges "
                              "geometrically to the circle, which confirms the procedure; no GCI quoted" %
                              (g["phi_ext"], circ, 100 * (g["phi_ext"] / circ - 1)))
            for k_ in ("GCI21_pct", "GCI21_abs"):
                g.pop(k_, None)
        imb = key in ("mass_imb_pct", "energy_imb_pct")
        w.writerow([r_["quantity"], r_["units"], f_(fmt, r_["coarse"]), f_(fmt, r_["medium"]), f_(fmt, r_["fine"]),
                    "" if imb else "%+.3f" % r_["pct_CM"], "" if imb else "%+.3f" % r_["pct_MF"],
                    "" if r_["pctrise_CM"] is None else "%+.3f" % r_["pctrise_CM"],
                    "" if r_["pctrise_MF"] is None else "%+.3f" % r_["pctrise_MF"],
                    "" if r_["geo_CM"] is None else "%+.4g" % r_["geo_CM"],
                    "" if r_["geo_MF"] is None else "%+.4g" % r_["geo_MF"], r_["geometry"],
                    f_(fmt, g["phi_ext"]) if g.get("p_credible") else "",
                    ("%.3f" % g["GCI21_pct"]) if "GCI21_pct" in g else "",
                    ("%.4g" % g["GCI21_abs"]) if "GCI21_abs" in g else "", g.get("basis", ""),
                    r_["status"], basis_txt])

# ============================================================================
# 7. F-029 and F-027 evidence
# ============================================================================
F029 = dict(f_fd={lv: V[lv]["f_fd"] for lv in LEVELS}, f_fd_slabmean={lv: V[lv]["f_fd_slabmean"] for lv in LEVELS},
            f_petukhov_local={lv: V[lv]["f_pet_fd"] for lv in LEVELS},
            f_petukhov_heated_local={lv: V[lv]["f_pet_fd"] * V[lv]["TwTb_fd"] ** -0.1 for lv in LEVELS},
            f_section2=ana.get("f_mean"), gci=GC["f_fd"],
            geometry_Dh_effect_pct={lv: 100 * (GEO[lv]["Dh_over_D"] ** -0.2 - 1) for lv in LEVELS},
            local_f_fine_xD={x: float(np.interp(x, P["fine"]["x_over_D"], P["fine"]["f_shear"])) for x in (5, 10, 18, 23.5, 29)},
            isothermal=ISO)
fext = GC["f_fd"].get("phi_ext") if GC["f_fd"].get("p_credible") else V["fine"]["f_fd"]
F029["gap_vs_section2_pct"] = {lv: 100 * (V[lv]["f_fd"] / ana["f_mean"] - 1) for lv in LEVELS}
F029["gap_extrapolated_vs_section2_pct"] = 100 * (fext / ana["f_mean"] - 1)
F029["gap_fine_vs_petukhov_local_pct"] = 100 * (V["fine"]["f_fd"] / V["fine"]["f_pet_fd"] - 1)
F029["gap_fine_vs_petukhov_heated_pct"] = 100 * (V["fine"]["f_fd"] / (V["fine"]["f_pet_fd"] * V["fine"]["TwTb_fd"] ** -0.1) - 1)
if ISO:
    # multiplicative decomposition of the medium-mesh gap f_CFD / f_Section2 (all window means, x/D 18-29):
    #   f_med/f_S2 = [f_Pet(Re_window,heated)/f_S2] x [f_iso/f_Pet(Re_iso)] x [(f_med/f_iso)/(f_Pet(Re_h)/f_Pet(Re_iso))]
    #   = Reynolds-number basis x SST isothermal (medium mesh, incl. mesh + development) x heating (CFD)
    hm = ISO["heated_medium"]
    f_iso, f_pi = ISO["f_fd_exact_window"], ISO["f_petukhov"]
    ch = dict(re_basis=hm["f_petukhov_at_Re"] / ana["f_mean"],
              sst_isothermal_medium=f_iso / f_pi,
              heating_cfd=(hm["f_fd_exact_window"] / f_iso) / (hm["f_petukhov_at_Re"] / f_pi),
              heating_petukhov_m_minus0p1=hm["Tw_over_Tb"] ** -0.1,
              mesh_medium_to_extrapolated=fext / V["medium"]["f_fd"],
              mesh_medium_to_fine=V["fine"]["f_fd"] / V["medium"]["f_fd"],
              iso_development_xD29_over_window=ISO["f_local_xD29"] / f_iso,
              iso_rise_xD18_to_29=ISO["f_local_xD29"] / ISO["f_local_xD18"],
              iso_xD29_vs_petukhov=ISO["f_local_xD29"] / f_pi,
              heated_medium_consistency=hm["f_fd_exact_window"] / V["medium"]["f_fd"])
    ch["iso_mesh_corrected_vs_petukhov"] = f_iso * ch["mesh_medium_to_extrapolated"] / f_pi
    ch["heating_beyond_m_minus0p1"] = ch["heating_cfd"] / ch["heating_petukhov_m_minus0p1"]
    ch["product"] = ch["re_basis"] * ch["sst_isothermal_medium"] * ch["heating_cfd"]
    ch["medium_over_section2"] = V["medium"]["f_fd"] / ana["f_mean"]
    lt = math.log(ch["medium_over_section2"])
    ch["share_of_gap_pct_log"] = {k_: 100 * math.log(ch[k_]) / lt for k_ in ("re_basis", "sst_isothermal_medium", "heating_cfd")}
    F029["decomposition_medium"] = ch
    with open(os.path.join(DIRS["Comparison_Tables"], "f029_decomposition.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["# F-029: multiplicative decomposition of the medium-mesh friction-factor gap vs Section 2 (window x/D 18-29). "
                    "Isothermal factor from the CFD isothermal diagnostic on the medium mesh. RE-ANALYSIS 2026."])
        w.writerow(["factor", "value", "percent"])
        for k_ in ("re_basis", "sst_isothermal_medium", "heating_cfd", "product", "medium_over_section2",
                   "heating_petukhov_m_minus0p1", "heating_beyond_m_minus0p1", "mesh_medium_to_fine",
                   "mesh_medium_to_extrapolated", "iso_mesh_corrected_vs_petukhov", "iso_development_xD29_over_window",
                   "iso_rise_xD18_to_29", "iso_xD29_vs_petukhov", "heated_medium_consistency"):
            w.writerow([k_, "%.6f" % ch[k_], "%+.3f" % (100 * (ch[k_] - 1))])
F027 = dict(T_max_analytical=ana["T_wall_outer_exit"], T_max={lv: V[lv]["T_max"] for lv in LEVELS},
            T_max_corr={lv: V[lv]["T_max_corr"] for lv in LEVELS},
            gap_vs_analytical={lv: V[lv]["T_max"] - ana["T_wall_outer_exit"] for lv in LEVELS},
            T_max_extrapolated=GC["T_max"].get("phi_ext"), T_max_corr_extrapolated=GC["T_max_corr"].get("phi_ext"),
            dTw_300={lv: V[lv]["dTw_300"] for lv in LEVELS})

# ============================================================================
# 8. downstream (structural) sensitivity - Section 2 closed forms, per kelvin
# ============================================================================
E, ALPHA = ana["E_at_Ts"], ana["alpha"]
SIG_PER_K = E * ALPHA / 1e6                                         # MPa per K of uniform temperature (LC2)
# raw peak temperature: Mechanical receives the raw medium field, so compare raw with raw (the bulk-correction
# difference, 0.07 K, is reported separately as U_Tmax_bulk_correction_effect_K)
g_Tmax = GC["T_max"]
U_T = g_Tmax.get("GCI21_abs", g_Tmax.get("U_osc", float("nan")))
U_T_med = abs(V["medium"]["T_max"] - (g_Tmax.get("phi_ext") if g_Tmax.get("p_credible") else V["fine"]["T_max"]))
U_T_med_corr = abs(V["medium"]["T_max"] - GC["T_max_corr"]["phi_ext"]) if GC["T_max_corr"].get("p_credible") else float("nan")
g_dT = GC["dTw_300"]
U_dT = (abs(V["medium"]["dTw_300"] - g_dT["phi_ext"]) if g_dT.get("p_credible") else
        max(abs(V["fine"]["dTw_300"] - V["medium"]["dTw_300"]), abs(V["medium"]["dTw_300"] - V["coarse"]["dTw_300"])))
g_Tm = GC["T_solid_mean"]
U_Tmean = abs(V["medium"]["T_solid_mean"] - g_Tm["phi_ext"]) if g_Tm.get("p_credible") else float("nan")
DOWN = dict(E_Pa=E, alpha=ALPHA, sigma_LC2_per_K_MPa=SIG_PER_K, LC2_sigma_MPa=ana["LC2_axial"] / 1e6,
            LC1_sigma_MPa=ana["LC1_vonMises_max"] / 1e6, dT_mean_above_ref=ana["dT_above_ref"],
            free_growth_mm=1e3 * ana["free_axial_growth"],
            U_Tmax_fine_GCI_K=U_T, U_Tmax_medium_vs_best_K=U_T_med,
            U_Tmax_medium_raw_vs_circle_extrapolated_K=U_T_med_corr,
            U_Tmax_bulk_correction_effect_K=U_T_med_corr - U_T_med, U_dTwall_K=U_dT,
            model_gap_Tmax_vs_analytical_K=V["medium"]["T_max"] - ana["T_wall_outer_exit"])
for tag, dTK in (("mesh_medium", U_T_med), ("model_vs_analytical", abs(DOWN["model_gap_Tmax_vs_analytical_K"]))):
    DOWN["LC2_dsigma_MPa_" + tag] = SIG_PER_K * dTK
    DOWN["LC2_dsigma_pct_" + tag] = 100 * dTK / ana["dT_above_ref"]
    DOWN["growth_dmm_" + tag] = 1e3 * ana["free_axial_growth"] * dTK / ana["dT_above_ref"]
# free axial growth follows the volume-mean solid temperature, not the peak: alpha * L * dT_mean
DOWN["U_Tsolidmean_medium_vs_best_K"] = U_Tmean
DOWN["growth_dmm_mesh_medium_from_Tmean"] = 1e3 * ALPHA * L * U_Tmean
DOWN["growth_pct_mesh_medium_of_CFD_mean_rise"] = 100 * U_Tmean / (V["medium"]["T_solid_mean"] - T_REF)
DOWN["LC1_dsigma_pct_mesh"] = 100 * U_dT / V["medium"]["dTw_300"]
DOWN["LC1_dsigma_MPa_mesh"] = DOWN["LC1_dsigma_pct_mesh"] / 100 * ana["LC1_vonMises_max"] / 1e6
DOWN["Q_mesh_resolution_pct"] = 100 * (max(V[l]["Q_corr"] for l in LEVELS) - min(V[l]["Q_corr"] for l in LEVELS)) / V["fine"]["Q_corr"]
with open(os.path.join(DIRS["Uncertainty"], "downstream_impact.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# Effect of CFD uncertainty on Section 2 closed-form structural quantities (per-kelvin sensitivities). "
                "RE-ANALYSIS 2026."])
    for k_, v_ in DOWN.items():
        w.writerow([k_, "%.6g" % v_ if isinstance(v_, float) else v_])

RESULT = dict(mesh=MESH, geometry=GEO, values=V, refinement=dict(r21=r21, r32=r32), gci=GC,
              table=rows_raw, status=STATUS, F029=F029, F027=F027, downstream=DOWN, wallclock_min=WALLCLOCK_MIN)
json.dump(RESULT, open(os.path.join(OUT, "mesh_study_results.json"), "w"), indent=2, default=float)

# ============================================================================
# 9. plots
# ============================================================================
cells = np.array([MESH[lv]["cells"] for lv in LEVELS])


def finish(fig, name, cap=""):
    import textwrap
    txt = textwrap.fill((cap + "  " if cap else "") + PROV, width=int(fig.get_figwidth() * 17))
    fig.text(0.5, -0.01, txt, ha="center", va="top", fontsize=7.2, color=GREY)
    fig.savefig(os.path.join(DIRS["Plots"], name), dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("   plot", name)


def conv_plot(ax, key, keycorr=None, label="", unit="", ref=None, reflabel=""):
    raw = np.array([V[lv][key] for lv in LEVELS])
    ax.plot(cells, raw, "o-", color="k", lw=1.5, ms=7, label="raw CFD")
    for lv, x, y in zip(LEVELS, cells, raw):
        ax.plot([x], [y], "o", color=C[lv], ms=9, zorder=5)
    g = GC[key]
    if keycorr is not None:
        cor = np.array([V[lv][keycorr] for lv in LEVELS])
        ax.plot(cells, cor, "s--", color="#8a3ffc", lw=1.3, ms=6,
                label="geometry-adjusted (ESTIMATE, see Geometry_Correction)" if keycorr == "dp_geoadj"
                else "geometry-corrected (exact)")
        g = GC[keycorr]
        fine_v = cor[-1]
    else:
        fine_v = raw[-1]
    if g.get("p_credible"):
        ax.axhline(g["phi_ext"], color=GREY, lw=0.9, ls=":", label="Richardson extrapolated (p = %.2f)" % g["p"])
        U = g["GCI21_abs"]
        ax.errorbar([cells[-1] * 1.12], [fine_v], yerr=[[U], [U]], fmt="none", ecolor=GREY, capsize=4,
                    label="GCI(fine) = %.3g %s (%.2f %% of %s)" % (U, unit, g["GCI21_pct"],
                                                               "rise" if g.get("basis") == "rise above 300 K" else "value"))
    if ref is not None:
        ax.axhline(ref, color="#d12771", lw=1.0, ls="-.", label=reflabel)
    ax.set_xscale("log")
    ax.set_xticks(cells)
    ax.set_xticklabels(["coarse\n51,840", "medium\n159,840", "fine\n500,580"])
    ax.set_xlim(cells[0] / 1.4, cells[-1] * 1.4)
    ax.set_ylabel("%s [%s]" % (label, unit))
    ax.legend(fontsize=7.8)
    ax.grid(alpha=0.25)


PL = [
    ("MI01_cells_vs_pressure_drop.png", "dp", "dp_geoadj", "Static pressure drop", "Pa", None, "",
     "Raw = area-weighted static inlet - outlet (Section 5B definition). 'Geometry-adjusted' removes the exact 1-D "
     "acceleration part and the ESTIMATED D_h/density friction part of the polygon effect (see Geometry_Correction)."),
    ("MI02_cells_vs_outlet_temperature.png", "T_out", "T_out_corr", "Outlet temperature (mass-weighted)", "K", None, "",
     "Correction is exact: energy conservation with each polygon's own Q/mdot, referred to the true circle."),
    ("MI03_cells_vs_heat_transfer_rate.png", "Q", "Q_corr", "Heat-transfer rate", "W", None, "",
     "Raw Q = 8000 W/m2 x the polygon's outer area; divided by the lateral-area ratio it is 603.186 W on every mesh."),
    ("MI04_cells_vs_max_solid_temperature.png", "T_max", "T_max_corr", "Maximum solid temperature", "K", None, "",
     "Outer-wall facet maximum at the outlet end. Correction removes only the exact bulk-temperature shift of the polygon."),
    ("MI05_cells_vs_midspan_through_wall_dT.png", "dTw_300", None, "Through-wall dT at z = 300 mm", "K", None, "",
     "Circumferential averages, interpolated to exactly z = 300 mm on every mesh (no inlet-slab values)."),
    ("MI06_cells_vs_nusselt.png", "Nu_fd", None, "Fully developed Nu (x/D 18-29)", "-", None, "",
     "Exact-window mean of local Nu = h D / k_air(T_b), D = 20 mm."),
    ("MI07_cells_vs_friction_factor.png", "f_fd", None, "Fully developed Darcy f (x/D 18-29)", "-", None, "",
     "f = 8 tau_w rho_b / G^2, exact-window mean."),
]
for name, key, keyc, lab, u, ref, refl, cap in PL:
    fig, ax = plt.subplots(1, 1, figsize=(8.6, 5.4))
    if key == "f_fd":
        conv_plot(ax, key, keyc, lab, u, ana["f_mean"], "Section 2 analytical 0.0241")
        ax.axhline(V["fine"]["f_pet_fd"] * V["fine"]["TwTb_fd"] ** -0.1, color="#eda100", lw=1.0, ls="--",
                   label="Petukhov with heating correction, CFD conditions")
        if ISO:
            ax.axhline(ISO["f_fd_exact_window"], color="#1192e8", lw=1.0, ls=(0, (1, 1)),
                       label="CFD isothermal diagnostic (medium)")
        ax.legend(fontsize=7.4)
    elif key == "T_max":
        conv_plot(ax, key, keyc, lab, u)
        ax2 = ax.twinx()
        ax2.set_ylabel("vs Section 2 analytical 581.71 K [K]", color="#d12771")
        lo, hi = ax.get_ylim()
        ax2.set_ylim(lo - ana["T_wall_outer_exit"], hi - ana["T_wall_outer_exit"])
    else:
        conv_plot(ax, key, keyc, lab, u, ref, refl)
    ax.set_title(lab + " vs mesh", fontsize=10.5)
    finish(fig, name, cap)

# y+ statistics
fig, axes = plt.subplots(1, 2, figsize=(14, 5.2), gridspec_kw=dict(wspace=0.28))
ax = axes[0]
for key, lab, mk in (("yp_min", "minimum", "v"), ("yp_mean", "area mean", "o"), ("yp_fd", "fully developed mean", "s"),
                     ("yp_max", "maximum", "^")):
    ax.plot(cells, [V[lv][key] for lv in LEVELS], mk + "-", lw=1.3, label=lab)
ax.axhline(1.0, color="k", lw=0.8)
ax.set_xscale("log"); ax.set_xticks(cells); ax.set_xticklabels(["coarse", "medium", "fine"])
ax.set_ylim(0, 1.1); ax.set_ylabel("y+ (Fluent, cell centre)"); ax.legend(fontsize=8)
ax.set_title("(a) y+ statistics; max sits in the first slab (centre %.1f / %.1f / %.1f mm)" %
             tuple(V[lv]["first_slab_z_mm"] for lv in LEVELS), fontsize=9.2)
ax = axes[1]
for lv in LEVELS:
    wi = W[lv]
    nz = MESH[lv]["NZ"]
    dz_ = L / nz
    k = np.clip((wi["z-coordinate"] / dz_).astype(int), 0, nz - 1)
    kc = int(np.argmin(abs((np.arange(nz) + 0.5) * dz_ - 0.3)))
    m = k == kc
    o = np.argsort(wi["th"][m])
    ax.plot(wi["th"][m][o], wi["y-plus"][m][o], "-", color=C[lv], lw=1.2,
            label="%s, N = %d, slab z = %.1f mm" % (lv, MESH[lv]["NT"], (kc + 0.5) * dz_ * 1e3))
ax.set_xlabel("theta [deg]"); ax.set_ylabel("y+"); ax.legend(fontsize=8)
ax.set_title("(b) around the wall near mid-span: O-grid pattern (thinner first layer at the diagonals)", fontsize=9.2)
fig.suptitle("Figure MI08 - y+ on the conjugate wall, three meshes", fontsize=11)
finish(fig, "MI08_yplus_statistics_vs_mesh.png", "Same 12.2 um design first layer on all meshes; every face y+ <= 1.")

# profiles overlay
fig, axes = plt.subplots(2, 2, figsize=(15, 9.2), gridspec_kw=dict(hspace=0.32, wspace=0.22))
for lv in LEVELS:
    p = P[lv]
    axes[0, 0].plot(p["z"] * 1e3, p["Twi"], color=C[lv], lw=1.3, label=lv)
    axes[0, 1].plot(p["z"] * 1e3, p["dTwall"], color=C[lv], lw=1.2, label=lv)
    axes[1, 0].plot(p["x_over_D"], p["Nu"], color=C[lv], lw=1.2, label=lv)
    axes[1, 1].plot(p["x_over_D"], p["f_shear"], color=C[lv], lw=1.2, label=lv)
axes[0, 0].set_ylabel("inner-wall T [K]"); axes[0, 0].set_xlabel("z [mm]")
axes[0, 1].set_ylabel("through-wall dT [K]"); axes[0, 1].set_xlabel("z [mm]"); axes[0, 1].set_ylim(7.0, 9.0)
axes[1, 0].set_ylabel("local Nu"); axes[1, 0].set_xlabel("x/D"); axes[1, 0].set_ylim(45, 90)
axes[1, 1].set_ylabel("local Darcy f"); axes[1, 1].set_xlabel("x/D"); axes[1, 1].set_ylim(0.019, 0.026)
for ax in axes.flat:
    ax.legend(fontsize=8); ax.grid(alpha=0.25)
for ax in (axes[1, 0], axes[1, 1]):
    ax.axvspan(18, 29, color="#eeeeee", lw=0)
axes[0, 1].axvline(300, color=GREY, lw=0.8, ls=":")
fig.suptitle("Figure MI09 - Axial profiles on the three meshes (raw)", fontsize=11)
finish(fig, "MI09_profiles_three_meshes.png", "Grey band: fully developed window. Dotted: mid-span.")

# raw vs corrected differences bar chart
keys_bar = ["mdot_gs", "Q", "T_out", "dp", "T_max", "dTw_300", "Nu_fd", "f_fd"]
labs_bar = ["mass flow", "heat rate", "T_out (% of rise)", "dp", "T_max solid (% of rise)", "dT_wall mid", "Nu fd", "f fd"]
fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), sharey=True)
for ax, (a, b, t) in zip(axes, (("coarse", "medium", "coarse -> medium"), ("medium", "fine", "medium -> fine"))):
    y = np.arange(len(keys_bar))
    den = [(V[a][k] - T_REF) if k in TEMP_ABS else V[a][k] for k in keys_bar]   # temperatures: % of the rise
    tot = [100 * (V[b][k] - V[a][k]) / d_ for k, d_ in zip(keys_bar, den)]
    geo = [100 * (geo_change(k, a, b) or 0.0) / d_ for k, d_ in zip(keys_bar, den)]
    ax.barh(y - 0.2, tot, 0.38, color=GREY, label="raw change")
    ax.barh(y + 0.2, geo, 0.38, color="#8a3ffc", label="geometry alone (exact or estimated)")
    ax.axvline(0, color="k", lw=0.7)
    ax.set_yticks(y); ax.set_yticklabels(labs_bar); ax.invert_yaxis()
    ax.set_title(t, fontsize=10); ax.set_xlabel("% of the coarser mesh value (temperatures: % of their rise above 300 K)"); ax.legend(fontsize=8)
fig.suptitle("Figure MI10 - How much of each change is polygon geometry", fontsize=11)
finish(fig, "MI10_geometry_vs_resolution.png", "Exact: mass flow, heat rate, T_out, bulk part of T_max. Estimated "
       "(not applied to headline values): dp friction D_h/density part, dT_wall apothem scaling, Nu/f D_h^-0.2.")

# F-029 evidence: local friction factor, three heated meshes + isothermal diagnostic
if ISO:
    fig, ax = plt.subplots(1, 1, figsize=(11.5, 5.6))
    for lv in LEVELS:
        ax.plot(P[lv]["x_over_D"], P[lv]["f_shear"], color=C[lv], lw=1.3, label="heated CFD, %s" % lv)
    ax.plot(ISOPROF["x_over_D"], ISOPROF["f"], color="#1192e8", lw=1.6, ls="--",
            label="ISOTHERMAL CFD diagnostic (energy off), medium mesh")
    ax.axhline(ISO["f_petukhov"], color="k", lw=0.9, ls=":", label="Petukhov, Re = %.0f (isothermal)" % ISO["Re"])
    ax.axhline(ana["f_mean"], color="#d12771", lw=0.9, ls="-.", label="Section 2 value %.5f" % ana["f_mean"])
    ax.axhline(ISO["heated_medium"]["f_petukhov_heating_m_minus0p1"], color="#eda100", lw=0.9, ls="--",
               label="Petukhov x (Tw/Tb)^-0.1 at heated window conditions")
    ax.axvspan(18, 29, color="#eeeeee", lw=0)
    ax.set_xlim(0, 30); ax.set_ylim(0.019, 0.030)
    ax.set_xlabel("x/D"); ax.set_ylabel("Darcy f = 8 tau_w rho_b / G^2"); ax.legend(fontsize=7.8, ncol=2)
    ax.grid(alpha=0.25)
    ax.set_title("Figure MI11 - F-029 evidence: friction factor along the duct", fontsize=10.5)
    finish(fig, "MI11_F029_friction_evidence.png", "Grey band: window x/D 18-29. The isothermal f still rises "
           "%.1f %% across the window at constant Re, so the window is not fully developed." %
           (100 * (ISO["f_local_xD29"] / ISO["f_local_xD18"] - 1)))

print("r21 = %.4f, r32 = %.4f" % (r21, r32))
for r_ in rows_raw:
    g = GC[r_["key"]]
    print("%-52s C %-12.6g M %-12.6g F %-12.6g  CM %+8.4f%%  MF %+8.4f%%  %s p=%s ext=%s GCI=%s  [%s] %s" % (
        r_["quantity"][:52], r_["coarse"], r_["medium"], r_["fine"], r_["pct_CM"], r_["pct_MF"], g.get("kind"),
        ("%.2f" % g["p"]) if "p" in g else "-", ("%.6g" % g["phi_ext"]) if g.get("p_credible") else "-",
        ("%.3f%%" % g["GCI21_pct"]) if "GCI21_pct" in g else "-", r_["status"], r_["status_basis"]))
print("F029:", json.dumps({k: v for k, v in F029.items() if k not in ("isothermal", "gci")}, default=float))
print("F027:", json.dumps(F027, default=float))
print("DOWN:", json.dumps(DOWN, default=float))
print("MESH-STUDY-DONE")
