# -*- coding: utf-8 -*-
"""SECTION 10A - MASTER DATA with independent recomputation (RE-ANALYSIS 2026).
Every master value is recomputed here from the rawest file available (Fluent report text files, MAPDL nodal /
reaction / load-factor tables, CAD measurement file) with code written for this audit (no earlier post-processing
script is imported), and compared with the value documented in the section's summary data file.
Status: VERIFIED = recomputed from raw output and equal to the documented value within the stated tolerance;
CROSS-CHECKED = documented value confirmed by an independent second computation in another section;
REPORTED = taken from the section's result file (derived post-processing quantity not recomputed here; reason given);
INPUT = re-analysed input parameter (class B, not a result); MISMATCH = recomputation disagrees (must be explained).
Usage: python master_data_10A.py <project_root> <out_json>"""
import os, sys, json, csv, math, re
sys.dont_write_bytecode = True
import numpy as np
try:
    import pandas as pd
except Exception:
    pd = None
R, OUT = sys.argv[1], sys.argv[2]
P = lambda *a: os.path.join(R, *a)
ITEMS = []


def item(group, param, value, units, level, case, source, method, documented=None, doc_source="", tol=None, status=None, note="", disp=None):
    rel = None
    if status is None:
        if documented is None:
            status = "REPORTED"
        else:
            if isinstance(value, (int, float)) and isinstance(documented, (int, float)):
                rel = abs(value - documented) / max(abs(documented), 1e-300)
                ok = (abs(value - documented) <= tol[1]) if isinstance(tol, tuple) else rel <= (tol if tol is not None else 1e-4)
                status = "VERIFIED" if ok else "MISMATCH"
            else:
                status = "VERIFIED" if str(value) == str(documented) else "MISMATCH"
    ITEMS.append({"group": group, "parameter": param, "value": value, "display": disp, "units": units, "level": level, "case": case,
                  "source": source, "method": method, "documented": documented, "documented_in": doc_source,
                  "rel_diff": rel, "status": status, "note": note})


def load(p):
    if pd is not None:
        return pd.read_csv(p).values.astype(float)
    return np.loadtxt(p, delimiter=",", skiprows=1)


def report(p):
    """Fluent flux / surface-integral report text -> {zone: value}"""
    out = {}
    for l in open(p, errors="ignore"):
        m = re.match(r"^\s*([A-Za-z0-9_\-]+)\s+(-?[0-9.]+(?:e[-+]?[0-9]+)?)\s*$", l.strip("\n"), re.I)
        if m and not l.strip().startswith("-"):
            out[m.group(1)] = float(m.group(2))
    return out


def corners(ds):
    L = open(ds, errors="ignore").read().split("\n")
    i = next(k for k, l in enumerate(L) if l.lower().startswith("eblock")) + 2
    s = set()
    while not L[i].strip().startswith("-1"):
        s.update(int(L[i][k:k + 9]) for k in range(9, 81, 9))
        i += 1
    return s


def eblock_counts(ds):
    return [int(l.split(",")[-1]) for l in open(ds, errors="ignore") if l.lower().startswith("eblock")]


def tref(ds):
    for l in open(ds, errors="ignore"):
        if l.lower().startswith("tref,"):
            return float(l.split(",")[1])
    return None


def sy(tc):
    T = [20, 100, 200, 300, 400]; V = [1030e6, 1060e6, 1040e6, 1020e6, 1000e6]
    for a in range(4):
        if T[a] <= tc <= T[a + 1]:
            return V[a] + (V[a + 1] - V[a]) * (tc - T[a]) / (T[a + 1] - T[a])
    raise ValueError(tc)


def static(nodal, ds, Ri, Ro, react=None):
    a = load(nodal)
    a = a[np.hypot(a[:, 1], a[:, 2]) > 1e-6]            # drop a remote-point pilot on the axis
    cs = corners(ds)
    c = np.isin(a[:, 0].astype(int), list(cs))
    vm = a[:, 12].copy(); vm[~c] = -1
    i = int(np.argmax(vm))
    ut = np.sqrt(a[:, 4] ** 2 + a[:, 5] ** 2 + a[:, 6] ** 2)
    rr_all = np.round(np.hypot(a[:, 1], a[:, 2]), 7)

    def face_mean(z):   # area-weighted face mean: ring means integrated over r dr (trapezoid on the node radii)
        m = np.abs(a[:, 3] - z) < 1e-9
        Rn = np.unique(rr_all[m]); Un = np.array([a[m & (rr_all == x), 6].mean() for x in Rn])
        tz = getattr(np, "trapezoid", None) or np.trapz
        return tz(Un * Rn, Rn) / tz(Rn, Rn)
    uz_in, uz_out = face_mean(0.0), face_mean(0.6)
    u = np.full(len(a), -1.0)
    u[c] = a[c, 12] / np.array([sy(t) for t in a[c, 14]])
    j = int(np.argmax(u))
    r = {"nodes": len(a), "vm_max": a[i, 12], "vm_T_K": a[i, 14] + 273.15, "vm_r_mm": math.hypot(a[i, 1], a[i, 2]) * 1e3, "vm_z_mm": a[i, 3] * 1e3,
         "utot_max": ut.max(), "uz_absmax": np.abs(a[:, 6]).max(), "ur_max": a[:, 4].max(), "dL": uz_out - uz_in,
         "util": u[j], "util_T_K": a[j, 14] + 273.15, "util_Sy": sy(a[j, 14]), "Tmin_C": a[:, 14].min(), "Tmax_C": a[:, 14].max()}
    if react:
        f = np.atleast_2d(load(react))
        r["F_in"] = f[np.abs(f[:, 3]) < 1e-9, 6].sum()
        r["F_sum_mag"] = float(np.sqrt(f[:, 4].sum() ** 2 + f[:, 5].sum() ** 2 + f[:, 6].sum() ** 2))
        r["A"] = math.pi * (Ro ** 2 - Ri ** 2)
        r["sigma_mean"] = -abs(r["F_in"]) / r["A"]
    return r


def lam(d):
    a = np.atleast_2d(load(os.path.join(d, "s8a_load_factors.csv")))
    return a[:, 1]


# ----------------------------------------------------------------------------------------------- GEOMETRY
cad = json.load(open(P("03_CAD_Geometry", "Geometry_Check", "cad_measurements.json")))
bp = json.load(open(P("02_Engineering_Calculations", "baseline_parameters.json"), encoding="utf-8-sig"))["params"]
Di, Do, L = bp["Di"]["value"], bp["Do"]["value"], bp["L"]["value"]
src_cad = "03_CAD_Geometry/Geometry_Check/cad_measurements.json"
item("Geometry", "Inner diameter D_i", (cad["bbox_fluid"][3] - cad["bbox_fluid"][0]) * 1e3, "mm", "INPUT (re-analysed, class B) / CAD", "P00", src_cad,
     "CAD fluid-body bounding box (SpaceClaim measurement)", Di * 1e3, "02_Engineering_Calculations/baseline_parameters.json", 1e-9)
item("Geometry", "Outer diameter D_o", (cad["bbox_solid"][3] - cad["bbox_solid"][0]) * 1e3, "mm", "INPUT (re-analysed, class B) / CAD", "P00", src_cad,
     "CAD solid-body bounding box", Do * 1e3, "02_Engineering_Calculations/baseline_parameters.json", 1e-9)
item("Geometry", "Wall thickness t", (cad["bbox_solid"][3] - cad["bbox_fluid"][3]) * 1e3, "mm", "INPUT / CAD", "P00", src_cad, "(D_o - D_i)/2 from the CAD boxes",
     (Do - Di) / 2 * 1e3, "02_Engineering_Calculations/baseline_parameters.json", 1e-9)
item("Geometry", "Length L", (cad["bbox_solid"][5] - cad["bbox_solid"][2]) * 1e3, "mm", "INPUT (re-analysed, class B) / CAD", "P00", src_cad,
     "CAD bounding box, axial", L * 1e3, "02_Engineering_Calculations/baseline_parameters.json", 1e-9)
per = cad["area_fluid_wall"] / L
item("Geometry", "Hydraulic diameter D_h", 4 * cad["area_fluid_inlet"] / per * 1e3, "mm", "CAD", "P00", src_cad, "4 A / P with A = CAD inlet area, P = CAD wall area / L",
     Di * 1e3, "exact: D_h = D_i for a circular bore", 1e-9)
item("Geometry", "Fluid flow area", cad["area_fluid_inlet"] * 1e6, "mm2", "CAD", "P00", src_cad, "CAD inlet face area", math.pi * Di ** 2 / 4 * 1e6, "exact pi D_i^2/4", 1e-9)
item("Geometry", "Solid volume", cad["solid_volume_m3"], "m3", "CAD", "P00", src_cad, "CAD body volume", math.pi * (Do ** 2 - Di ** 2) / 4 * L, "exact pi (D_o^2 - D_i^2) L / 4", 1e-9)
item("Geometry", "Heated-wall area (true cylinder)", cad["area_heated_outer"], "m2", "CAD", "P00", src_cad, "CAD face area of HEATED_OUTER_WALL", math.pi * Do * L,
     "exact pi D_o L", 1e-9)
si_a = report(P("06_Fluent_CFD", "Audit", "fluent_si_areas.txt"))
item("Geometry", "Heated-wall area (CFD 48-facet mesh)", si_a["heated_outer_wall"], "m2", "CFD-MEDIUM", "P00", "06_Fluent_CFD/Audit/fluent_si_areas.txt",
     "Fluent surface-integral area report", math.pi * Do * L * math.sin(math.pi / 48) / (math.pi / 48), "inscribed 48-gon lateral area (exact)", 1e-6,
     note="faceting: -0.0714 % vs the true cylinder; explains Q = 602.755 W vs 603.186 W")

# ----------------------------------------------------------------------------------------------- BASELINE CFD (medium)
cj = json.load(open(P("06_Fluent_CFD", "Baseline", "cfd_baseline_results.json"), encoding="utf-8-sig"))
ms = json.load(open(P("09_Mesh_Independence", "mesh_study_results.json"), encoding="utf-8-sig"))
mv = ms["values"]
A5 = "06_Fluent_CFD/Audit/"


def cfd_reports(folder):
    f = lambda n: report(os.path.join(folder, n))
    heat, mass, p, T, tw = f("fluent_flux_heat.txt"), f("fluent_flux_mass.txt"), f("fluent_si_p_area.txt"), f("fluent_si_T_mass.txt"), f("fluent_si_Twall_max.txt")
    return {"dp": p["fluid_inlet"] - p["fluid_outlet"], "T_out": T["fluid_outlet"], "Q": heat["heated_outer_wall"], "Q_int": heat["fluid_solid_interface"],
            "Tmax_facet": tw["heated_outer_wall"], "Tinner_max": tw["fluid_solid_interface"],
            "mdot": mass["fluid_inlet"], "mass_imb_pct": abs(mass["Net"]) / mass["fluid_inlet"] * 100, "energy_imb_pct": abs(heat["Net"]) / heat["heated_outer_wall"] * 100,
            "yp_mean": f("fluent_si_yplus_area.txt")["fluid_solid_interface"], "yp_max": f("fluent_si_yplus_max.txt")["fluid_solid_interface"],
            "yp_min": f("fluent_si_yplus_min.txt")["fluid_solid_interface"], "rho_in": f("fluent_si_rho_area.txt")["fluid_inlet"]}


c5 = cfd_reports(P("06_Fluent_CFD", "Audit"))
lvl = "CFD-MEDIUM (Section 5B, official baseline)"
item("Baseline CFD", "Mesh", "medium: butterfly O-grid hexahedral, 48 circumferential x 90 axial, 12.2 um first fluid layer", "-", lvl, "P00",
     "09_Mesh_Independence/mesh_study_results.json (mesh.medium)", "mesh parameters NT %d / NZ %d" % (ms["mesh"]["medium"]["NT"], ms["mesh"]["medium"]["NZ"]), status="REPORTED",
     note="decision D-034: medium mesh for all downstream work; fine = verification reference")
nf = sum(1 for _ in open(P("06_Fluent_CFD", "Exports", "cells_fluid.csv"))) - 1
ns = sum(1 for _ in open(P("06_Fluent_CFD", "Exports", "cells_solid.csv"))) - 1
item("Baseline CFD", "Cells (fluid + solid)", nf + ns, "-", lvl, "P00", "06_Fluent_CFD/Exports/cells_fluid.csv + cells_solid.csv", "row count of the cell exports (%d fluid + %d solid)" % (nf, ns),
     ms["mesh"]["medium"]["cells"], "09_Mesh_Independence/mesh_study_results.json", (None, 0))
mu300 = 184.6e-7   # Incropera Table A.4, 300 K (the frozen air table point used by Fluent)
item("Baseline CFD", "Reynolds number, inlet", c5["rho_in"] * 23.5 * Di / mu300, "-", lvl, "P00", A5 + "fluent_si_rho_area.txt", "rho_in (Fluent) x 23.5 m/s x D_i / mu(300 K) = 184.6e-7 Pa s",
     cj["reynolds"]["Re_in_nominalD"], "06_Fluent_CFD/Baseline/cfd_baseline_results.json", 1e-4)
item("Baseline CFD", "Reynolds number, outlet", cj["reynolds"]["Re_out_nominalD"], "-", lvl, "P00", "06_Fluent_CFD/Baseline/cfd_baseline_results.json", "G D / mu(T_out) (5B post-processing)",
     status="REPORTED", note="depends on mu(T_out); cross-checked in 6B: %.0f" % mv["medium"]["Re_out"])
item("Baseline CFD", "Pressure drop (area-weighted static, inlet - outlet)", c5["dp"], "Pa", lvl, "P00", A5 + "fluent_si_p_area.txt", "Fluent surface-integral report",
     cj["pressure"]["dp_total_area"], "06_Fluent_CFD/Baseline/cfd_baseline_results.json", 1e-6)
item("Baseline CFD", "Outlet bulk temperature (mass-weighted)", c5["T_out"], "K", lvl, "P00", A5 + "fluent_si_T_mass.txt", "Fluent surface-integral report",
     cj["temperatures"]["T_out_bulk_monitor"], "06_Fluent_CFD/Baseline/cfd_baseline_results.json", 1e-6)
item("Baseline CFD", "Heat-transfer rate (heated wall)", c5["Q"], "W", lvl, "P00", A5 + "fluent_flux_heat.txt", "Fluent flux report", cj["conservation"]["Q_wall"],
     "06_Fluent_CFD/Baseline/cfd_baseline_results.json", 1e-7, note="= 8000 W/m2 x 48-gon area; the analytical 603.19 W uses the true cylinder")
item("Baseline CFD", "Maximum solid temperature (outer-wall facet)", c5["Tmax_facet"], "K", lvl, "P00", A5 + "fluent_si_Twall_max.txt", "Fluent maximum-of-facet report",
     cj["temperatures"]["T_outer_wall_max"], "06_Fluent_CFD/Baseline/cfd_baseline_results.json", 1e-7)
cs = load(P("06_Fluent_CFD", "Exports", "cells_solid.csv"))
hdr = open(P("06_Fluent_CFD", "Exports", "cells_solid.csv")).readline().strip().split(",")
tcol = [k for k, h in enumerate(hdr) if "temp" in h.lower()]
if tcol:
    item("Baseline CFD", "Maximum solid temperature (hottest cell centre)", float(cs[:, tcol[0]].max()), "K", lvl, "P00", "06_Fluent_CFD/Exports/cells_solid.csv",
         "maximum of the exported solid cell temperatures", cj["temperatures"]["T_solid_max"], "06_Fluent_CFD/Baseline/cfd_baseline_results.json", 1e-7)
mp = json.load(open(P("10_Parametric_Study", "Mapping", "mapping_audit_9B2.json")))["cases"]["C00_PIPELINE_CHECK"]["midspan"]["source_nodes"]["dT_K"]
item("Baseline CFD", "Through-wall dT, mid-span z = 300 mm", cj["through_wall"]["dT_wall_z300"], "K", lvl, "P00", "06_Fluent_CFD/Baseline/cfd_baseline_results.json",
     "5B slab interpolation; cross-checked by the 9B-2 mapping audit on the Fluent node field of the same solution (C00 = P00 field)", mp,
     "10_Parametric_Study/Mapping/mapping_audit_9B2.json (independent node-field evaluation)", (None, 0.005), note="z = 570 mm: %.3f K" % cj["through_wall"]["dT_wall_z570"])
ITEMS[-1]["status"] = "CROSS-CHECKED" if ITEMS[-1]["status"] == "VERIFIED" else ITEMS[-1]["status"]
item("Baseline CFD", "Fully developed Nusselt number (x/D 18-29)", cj["fully_developed"]["Nu_cfd"], "-", lvl, "P00", "06_Fluent_CFD/Baseline/cfd_baseline_results.json",
     "5B slab post-processing of the axial profile; recomputed by the 6B study script from the same profile", mv["medium"]["Nu_fd"], "09_Mesh_Independence/mesh_study_results.json", 1e-3)
ITEMS[-1]["status"] = "CROSS-CHECKED" if ITEMS[-1]["status"] == "VERIFIED" else ITEMS[-1]["status"]
item("Baseline CFD", "Fully developed Darcy friction factor (x/D 18-29)", cj["fully_developed"]["f_cfd"], "-", lvl, "P00", "06_Fluent_CFD/Baseline/cfd_baseline_results.json",
     "as Nu", mv["medium"]["f_fd"], "09_Mesh_Independence/mesh_study_results.json", 1e-3)
ITEMS[-1]["status"] = "CROSS-CHECKED" if ITEMS[-1]["status"] == "VERIFIED" else ITEMS[-1]["status"]
for k, n, dk in (("yp_min", "y+ minimum", "min"), ("yp_mean", "y+ area mean", "area_mean"), ("yp_max", "y+ maximum", "max")):
    item("Baseline CFD", n + " (conjugate wall)", c5[k], "-", lvl, "P00", A5 + "fluent_si_yplus_*.txt", "Fluent surface-integral report", cj["yplus"][dk],
         "06_Fluent_CFD/Baseline/cfd_baseline_results.json", 1e-6)
item("Baseline CFD", "Mass imbalance", c5["mass_imb_pct"], "%", lvl, "P00", A5 + "fluent_flux_mass.txt", "|net| / inlet mass flow", cj["conservation"]["mass_imbalance_pct"],
     "06_Fluent_CFD/Baseline/cfd_baseline_results.json", 1e-3)
item("Baseline CFD", "Energy imbalance", c5["energy_imb_pct"], "%", lvl, "P00", A5 + "fluent_flux_heat.txt", "|net| / heated-wall heat rate", abs(cj["conservation"]["energy_imbalance_pct"]),
     "06_Fluent_CFD/Baseline/cfd_baseline_results.json", 1e-2, note="flux report prints 7 digits: net -1.839e-10 W vs monitor -1.855e-10 W")
rs = json.load(open(P("06_Fluent_CFD", "Audit", "run_summary.json"), encoding="utf-8-sig"))
item("Baseline CFD", "Convergence", "converged at iteration 600, confirmed at 700 (continuity %.1e)" % rs["final_eval"]["residuals"]["continuity"], "-", lvl, "P00",
     "06_Fluent_CFD/Audit/run_summary.json", "D-030 criteria (residuals + 200-iteration plateau + conservation) evaluated by the 5B journal", status="REPORTED" if rs["converged"] else "MISMATCH")

# ----------------------------------------------------------------------------------------------- CFD mesh study (fine reference, coarse, extrapolated)
for tag, fold, cells in (("fine", "Fine", 500580), ("coarse", "Coarse", 51840)):
    cr = cfd_reports(P("06_Fluent_CFD", "Mesh_Independence", fold, "Audit"))
    lv = "CFD-FINE (Section 6B, verification reference)" if tag == "fine" else "CFD-COARSE (Section 6A, mesh study only)"
    src = "06_Fluent_CFD/Mesh_Independence/%s/Audit/" % fold
    item("CFD mesh study", "%s: cells" % tag, mv[tag]["cells"], "-", lv, tag, "09_Mesh_Independence/mesh_study_results.json", "mesh record", status="REPORTED")
    item("CFD mesh study", "%s: pressure drop" % tag, cr["dp"], "Pa", lv, tag, src + "fluent_si_p_area.txt", "Fluent report", mv[tag]["dp"], "09_Mesh_Independence/mesh_study_results.json", 1e-6)
    item("CFD mesh study", "%s: outlet bulk temperature" % tag, cr["T_out"], "K", lv, tag, src + "fluent_si_T_mass.txt", "Fluent report", mv[tag]["T_out"], "09_Mesh_Independence/mesh_study_results.json", 1e-6)
    item("CFD mesh study", "%s: heat-transfer rate" % tag, cr["Q"], "W", lv, tag, src + "fluent_flux_heat.txt", "Fluent report", mv[tag]["Q"], "09_Mesh_Independence/mesh_study_results.json", 1e-6)
    item("CFD mesh study", "%s: maximum solid temperature (outer-wall facet)" % tag, cr["Tmax_facet"], "K", lv, tag, src + "fluent_si_Twall_max.txt", "Fluent report", mv[tag]["T_max"],
         "09_Mesh_Independence/mesh_study_results.json", 1e-6)
    item("CFD mesh study", "%s: through-wall dT mid-span" % tag, mv[tag]["dTw_300"], "K", lv, tag, "09_Mesh_Independence/mesh_study_results.json", "6B matched-location interpolation", status="REPORTED")
    item("CFD mesh study", "%s: Nu_fd / f_fd" % tag, "%.2f / %.5f" % (mv[tag]["Nu_fd"], mv[tag]["f_fd"]), "-", lv, tag, "09_Mesh_Independence/mesh_study_results.json", "6B window means", status="REPORTED")
    item("CFD mesh study", "%s: y+ max" % tag, cr["yp_max"], "-", lv, tag, src + "fluent_si_yplus_max.txt", "Fluent report", mv[tag]["yp_max"], "09_Mesh_Independence/mesh_study_results.json", 1e-6)
g = ms["gci"]
for key, n, u in (("T_max", "maximum solid temperature", "K"), ("dTw_300", "through-wall dT mid-span", "K"), ("Nu_fd", "Nu_fd", "-"), ("f_fd", "f_fd", "-"), ("dp_geoadj", "pressure drop (geometry-adjusted)", "Pa")):
    if key in g and g[key].get("phi_ext") is not None:
        item("CFD mesh study", "Richardson extrapolated %s" % n, g[key]["phi_ext"], u, "CFD-EXTRAPOLATED (Section 6B)", "3 meshes", "09_Mesh_Independence/mesh_study_results.json",
             "Celik (2008) with r21 %.4f, r32 %.4f; apparent order %.2f; GCI_fine %.3g %%" % (g[key]["r21"], g[key]["r32"], g[key].get("p", float("nan")), g[key].get("GCI21_pct", float("nan"))),
             status="REPORTED", note="limit of this refinement path only (F-032)")

# ----------------------------------------------------------------------------------------------- SECTION 2 ANALYTICAL (historical modelling level)
an = {}
for r in csv.DictReader(l for l in open(P("02_Engineering_Calculations", "baseline_results.csv")) if not l.startswith('"#')):
    an[r["quantity"]] = float(r["value"])
lvA = "ANALYTICAL (Section 2, 1-D correlations; not a CFD/FE result)"
srcA = "02_Engineering_Calculations/baseline_results.csv"
for k, n, u, sc in (("Q_total", "heat-transfer rate (true cylinder)", "W", 1), ("T_out_bulk", "outlet bulk temperature", "K", 1), ("dp_total_CFD_comparable", "pressure drop, CFD-comparable", "Pa", 1),
                    ("T_wall_outer_exit", "maximum solid temperature (outer wall, exit)", "K", 1), ("dT_through_wall", "through-wall dT (exit station)", "K", 1),
                    ("free_axial_growth", "free axial growth", "mm", 1e3), ("LC1_vonMises_max", "LC1 peak von Mises (Timoshenko, mid-span)", "MPa", 1e-6),
                    ("LC2_axial", "LC2 axial stress (sigma = -E alpha dT_mean)", "MPa", 1e-6), ("Sy_at_Ts", "yield strength at 281.6 C", "MPa", 1e-6), ("LC2_utilisation", "LC2 utilisation", "-", 1)):
    item("Section 2 analytical", n, an[k] * sc, u, lvA, "Section 2", srcA, "Section 2 script baseline_calculations.py (frozen 2026-09-18)", status="REPORTED",
         note="superseded for final use by the CFD / FE values; kept as the analytical modelling level")

# ----------------------------------------------------------------------------------------------- STRUCTURAL (7B) from raw MAPDL tables
S8 = P("08_Structural_Analysis")
ds2 = os.path.join(S8, "LC2_Restrained", "Solver_Output", "LC2_solve_input_ds.dat")
lc1 = static(os.path.join(S8, "LC1_Free_Expansion", "Solver_Output", "s7b_nodal.csv"), os.path.join(S8, "LC1_Free_Expansion", "Solver_Output", "LC1_solve_input_ds.dat"), 0.01, 0.02,
             os.path.join(S8, "LC1_Free_Expansion", "Solver_Output", "s7b_react.csv"))
lc2 = static(os.path.join(S8, "LC2_Restrained", "Solver_Output", "s7b_nodal.csv"), ds2, 0.01, 0.02, os.path.join(S8, "LC2_Restrained", "Solver_Output", "s7b_react.csv"))
lc2p = static(os.path.join(S8, "Pressure_Check", "Solver_Output", "s7b_nodal.csv"), os.path.join(S8, "Pressure_Check", "Solver_Output", "LC2P_solve_input_ds.dat"), 0.01, 0.02,
              os.path.join(S8, "Pressure_Check", "Solver_Output", "s7b_react.csv"))
lvS = "FE-STATIC (Section 7B, official; mapped medium CFD field, mesh B)"
sL1, sL2 = "08_Structural_Analysis/LC1_Free_Expansion/Solver_Output/", "08_Structural_Analysis/LC2_Restrained/Solver_Output/"
item("Structural", "Structural nodes", lc2["nodes"], "-", lvS, "P00 mesh B", sL2 + "s7b_nodal.csv", "row count of the MAPDL nodal table", 108252, "08_Structural_Analysis/Mesh/MESH_7A.md", (None, 0))
eb = eblock_counts(ds2)
item("Structural", "Structural elements (SOLID186, quadratic hex)", eb[0], "-", lvS, "P00 mesh B", sL2 + "LC2_solve_input_ds.dat", "EBLOCK element count of the solver input", 23400,
     "08_Structural_Analysis/Mesh/MESH_7A.md", (None, 0))
item("Structural", "Reference temperature T_ref", tref(ds2) + 273.15, "K", lvS, "P00", sL2 + "LC2_solve_input_ds.dat", "TREF command of the solver input (deg C) + 273.15", 300.0,
     "D-041", (None, 1e-6))
item("Structural", "LC1 maximum total deformation", lc1["utot_max"] * 1e3, "mm", lvS, "P00 LC1", sL1 + "s7b_nodal.csv", "max |u| over all nodes", 1.8443, "08_Structural_Analysis/Results/results_summary_7B.csv", (None, 5e-5))
item("Structural", "LC1 free axial growth dL", lc1["dL"] * 1e3, "mm", lvS, "P00 LC1", sL1 + "s7b_nodal.csv", "area-weighted face mean of u_z, outlet minus inlet (ring means integrated over r dr)", 1.8409,
     "08_Structural_Analysis/STRUCTURAL_RESULTS.md", (None, 5e-5))
item("Structural", "LC1 maximum von Mises stress", lc1["vm_max"] / 1e6, "MPa", lvS, "P00 LC1", sL1 + "s7b_nodal.csv", "max over corner nodes (EBLOCK of the solver input)", 24.282,
     "08_Structural_Analysis/Results/results_summary_7B.csv", (None, 5e-4), note="bore, r %.1f mm, z %.1f mm (inlet end effect; F-035/F-040 zone). Mid-span bore 18.20 MPa" % (lc1["vm_r_mm"], lc1["vm_z_mm"]))
item("Structural", "LC1 critical temperature (at max von Mises)", lc1["vm_T_K"], "K", lvS, "P00 LC1", sL1 + "s7b_nodal.csv", "T_used at the max-vm node", 427.81, "08_Structural_Analysis/STRUCTURAL_RESULTS.md", (None, 0.005))
item("Structural", "LC1 reaction resultant", lc1["F_sum_mag"], "N", lvS, "P00 LC1", sL1 + "s7b_react.csv", "|sum of nodal reactions|", 3.94e-7, "08_Structural_Analysis/Results/results_summary_7B.csv", (None, 1e-5),
     note="statically determinate 3-node support: reactions ~ 0")
item("Structural", "LC2 maximum total deformation", lc2["utot_max"] * 1e3, "mm", lvS, "P00 LC2", sL2 + "s7b_nodal.csv", "max |u|", 0.1349, "08_Structural_Analysis/Results/results_summary_7B.csv", (None, 5e-5))
item("Structural", "LC2 maximum von Mises stress", lc2["vm_max"] / 1e6, "MPa", lvS, "P00 LC2", sL2 + "s7b_nodal.csv", "max over corner nodes", 605.160873, "08_Structural_Analysis/Results/results_summary_7B.csv", (None, 5e-7),
     note="outer edge of the inlet face (r %.0f mm, z %.0f mm)" % (lc2["vm_r_mm"], lc2["vm_z_mm"]))
item("Structural", "LC2 end reaction (axial)", abs(lc2["F_in"]), "N", lvS, "P00 LC2", sL2 + "s7b_react.csv", "sum of FZ over the inlet-face nodes", 548936.6, "08_Structural_Analysis/Results/results_summary_7B.csv", (None, 0.05))
item("Structural", "LC2 mean axial stress", lc2["sigma_mean"] / 1e6, "MPa", lvS, "P00 LC2", sL2 + "s7b_react.csv", "-|F| / (pi (R_o^2 - R_i^2))", -582.44, "08_Structural_Analysis/STRUCTURAL_RESULTS.md", (None, 0.005))
item("Structural", "LC2 critical temperature (at max von Mises)", lc2["vm_T_K"], "K", lvS, "P00 LC2", sL2 + "s7b_nodal.csv", "T_used at the max-vm node", 437.99, "08_Structural_Analysis/STRUCTURAL_RESULTS.md", (None, 0.005))
item("Structural", "Local yield strength S_y(T) at the critical node", lc2["util_Sy"] / 1e6, "MPa", lvS + " + VDM 4127 table", "P00 LC2", sL2 + "s7b_nodal.csv",
     "linear interpolation of the VDM 4127 table (20-400 C) at T of the max vm/S_y node", 1047.0, "08_Structural_Analysis/STRUCTURAL_RESULTS.md", (None, 0.05))
item("Structural", "LC2 yield utilisation (max vm / S_y(T))", lc2["util"], "-", lvS, "P00 LC2", sL2 + "s7b_nodal.csv", "max over corner nodes of vm / S_y(T_node)", 0.5780,
     "08_Structural_Analysis/Results/results_summary_7B.csv", (None, 5e-5))
item("Structural", "First-yield load factor (1 / utilisation)", 1 / lc2["util"], "-", lvS, "P00 LC2", sL2 + "s7b_nodal.csv", "linear-elastic scaling to first yield at the critical node", 1.73,
     "08_Structural_Analysis/Buckling/BUCKLING_RESULTS.md", (None, 0.005))
item("Structural", "Pressure effect on LC2 max von Mises (LC2P - LC2)", (lc2p["vm_max"] - lc2["vm_max"]), "Pa", "FE-STATIC (Section 7B LC2P, 443.41 Pa bound)", "P00 LC2P",
     "08_Structural_Analysis/Pressure_Check/Solver_Output/s7b_nodal.csv", "difference of the corner-node maxima", 45.0, "08_Structural_Analysis/STRUCTURAL_RESULTS.md", (None, 1.0),
     note="relative %.1e (negligible)" % ((lc2p["vm_max"] - lc2["vm_max"]) / lc2["vm_max"]))

# ----------------------------------------------------------------------------------------------- BUCKLING
fm = json.load(open(os.path.join(S8, "Buckling", "fe_modes_8A.json")))["FE_load_factors"]
B8 = os.path.join(S8, "Buckling", "Mechanical")
s2s = static(P("10_Parametric_Study", "Structural_Cases", "S2_REEXTRACT", "s2x_nodal.csv"), ds2, 0.01, 0.02)
fs2 = np.atleast_2d(load(os.path.join(B8, "LC2NS_NoSway_Static", "Solver_Output", "s7b_react.csv"))) if os.path.isfile(os.path.join(B8, "LC2NS_NoSway_Static", "Solver_Output", "s7b_react.csv")) else None
F2 = abs(fs2[np.abs(fs2[:, 3]) < 1e-9, 6].sum()) if fs2 is not None else float(open(P("10_Parametric_Study", "Structural_Cases", "S2_REEXTRACT", "s2x_totals.txt")).read().split("sum_RF_FZ_N")[1].split()[0])
F2src = "08_Structural_Analysis/Buckling/Mechanical/LC2NS_NoSway_Static/Solver_Output/s7b_react.csv" if fs2 is not None else "10_Parametric_Study/Structural_Cases/S2_REEXTRACT/s2x_totals.txt"
RSRC = {"S1": "08_Structural_Analysis/LC2_Restrained/Solver_Output/s7b_react.csv", "S2": F2src,
        "S3": "10_Parametric_Study/Structural_Cases/S3_LC2_INTERMEDIATE/Solver_Output/S3_STATIC/s7b_react.csv"}
S3d = P("10_Parametric_Study", "Structural_Cases", "S3_LC2_INTERMEDIATE", "Solver_Output")
s3s = static(os.path.join(S3d, "S3_STATIC", "s7b_nodal.csv"), P("10_Parametric_Study", "Structural_Cases", "S3_LC2_INTERMEDIATE", "Audits", "Presolve_Inputs", "S3_presolve_ds.dat"), 0.01, 0.02,
             os.path.join(S3d, "S3_STATIC", "s7b_react.csv"))
l1 = lam(os.path.join(B8, "LC2_Linear_Buckling", "Solver_Output")); l2 = lam(os.path.join(B8, "LC2NS_Linear_Buckling", "Solver_Output")); l3 = lam(os.path.join(S3d, "S3_BUCKLING"))
lvB = "FE-BUCKLING (linear eigenvalue, perfect tube, LC2 thermal pre-stress)"
for sc, lf, F, src, doc, docv, mode in (("S1", l1, abs(lc2["F_in"]), "08_Structural_Analysis/Buckling/Mechanical/LC2_Linear_Buckling/Solver_Output/s8a_load_factors.csv", "08_Structural_Analysis/Buckling/fe_modes_8A.json", fm["LC2_Linear_Buckling"]["1"],
                                         "global guided-column sway (ends translate in opposite directions, end rotation held), cos(pi z/L)"),
                                        ("S2", l2, F2, "08_Structural_Analysis/Buckling/Mechanical/LC2NS_Linear_Buckling/Solver_Output/s8a_load_factors.csv", "08_Structural_Analysis/Buckling/fe_modes_8A.json", fm["LC2NS_Linear_Buckling"]["1"],
                                         "global clamped-clamped column, 1 - cos(2 pi z/L)"),
                                        ("S3", l3, abs(s3s["F_in"]), "10_Parametric_Study/Structural_Cases/S3_LC2_INTERMEDIATE/Solver_Output/S3_BUCKLING/s8a_load_factors.csv", "10_Parametric_Study/Results/SUPPORT_SENSITIVITY_RESULTS.csv", 2.23224,
                                         "global fixed-pinned column, max lateral at 0.605 L")):
    item("Buckling", "%s lambda1" % sc, float(lf[0]), "-", lvB, "P00 %s" % sc, src, "first positive load factor of the MAPDL eigenvalue solution", docv, doc, 1e-5 if sc != "S3" else (None, 5e-6))
    item("Buckling", "%s critical load P_cr = lambda1 x N" % sc, float(lf[0]) * F / 1e3, "kN", lvB, "P00 %s" % sc, src + " + " + RSRC[sc], "lambda1 x end reaction of the pre-stress state",
         {"S1": 608.25, "S2": 2360.40, "S3": 1225.36}[sc], "10_Parametric_Study/Results/SUPPORT_SENSITIVITY_RESULTS.csv", (None, 0.01))
    item("Buckling", "%s dominant mode" % sc, mode, "-", lvB, "P00 %s" % sc, doc if sc != "S3" else "10_Parametric_Study/Results/Data/post_9B2_results.json",
         "corner-node eigenvector classification (8A mode_shapes; beam share > 0.9999, no ovalisation)", status="REPORTED")
item("Buckling", "S1 lambda2 / lambda3", "%.5f / %.4f" % (l1[1], l1[2]), "-", lvB, "P00 S1", "08_Structural_Analysis/Buckling/Mechanical/LC2_Linear_Buckling/Solver_Output/s8a_load_factors.csv",
     "load factors 2 and 3", status="REPORTED", note="modes 1-2 are an orthogonal pair")
item("Support sensitivity", "S2 static max von Mises (re-extracted)", s2s["vm_max"] / 1e6, "MPa", "FE-STATIC (8A LC2NS)", "P00 S2", "10_Parametric_Study/Structural_Cases/S2_REEXTRACT/s2x_nodal.csv",
     "max over corner nodes", 605.160, "10_Parametric_Study/Results/SUPPORT_SENSITIVITY_RESULTS.csv", (None, 5e-4))
item("Support sensitivity", "S3 static max von Mises", s3s["vm_max"] / 1e6, "MPa", "FE-STATIC (9B-2 S3)", "P00 S3", "10_Parametric_Study/Structural_Cases/S3_LC2_INTERMEDIATE/Solver_Output/S3_STATIC/s7b_nodal.csv",
     "max over corner nodes (pilot excluded)", 605.160, "10_Parametric_Study/Results/SUPPORT_SENSITIVITY_RESULTS.csv", (None, 5e-4))
item("Support sensitivity", "S1 / S2 / S3 axial reaction", "%.1f / %.1f / %.1f" % (abs(lc2["F_in"]), F2, abs(s3s["F_in"])), "N", "FE-STATIC", "P00", "reaction tables (7B LC2, 8A LC2NS, 9B-2 S3)",
     "sum of FZ on the inlet face", status="REPORTED", note="identical to < 1e-6: the axial restraint sets the force in every scenario")

# ----------------------------------------------------------------------------------------------- STRUCTURAL MESH SENSITIVITY (8B)
ms8 = {}
for r in csv.DictReader(open(os.path.join(S8, "Mesh_Study", "STRUCTURAL_MESH_STUDY.csv"), encoding="utf-8")):
    ms8[r["Mesh"].split()[0]] = r
V8 = os.path.join(S8, "Mesh_Study", "Variants")
base = {}
for tag in ("XC", "C", "B", "FR", "FA", "FC", "IL"):
    d = os.path.join(V8, tag)
    ds = os.path.join(d, "Audits", "Presolve_Inputs", "%s_LC2_presolve_ds.dat" % tag)
    if not os.path.isfile(ds):
        continue
    s = static(os.path.join(d, "Solver_Output", "LC2", "s7b_nodal.csv"), ds, 0.01, 0.02, os.path.join(d, "Solver_Output", "LC2", "s7b_react.csv"))
    lv8 = "FE-MESH-STUDY (Section 8B)"
    item("Structural mesh sensitivity", "%s: LC2 max von Mises" % tag, s["vm_max"] / 1e6, "MPa", lv8, tag, "08_Structural_Analysis/Mesh_Study/Variants/%s/Solver_Output/LC2/s7b_nodal.csv" % tag,
         "max over corner nodes of this variant", float(ms8[tag]["LC2 Stress [MPa]"]), "08_Structural_Analysis/Mesh_Study/STRUCTURAL_MESH_STUDY.csv", (None, 5e-4))
    base[tag] = {"vm": s["vm_max"], "sig": s["sigma_mean"]}
    bk = os.path.join(d, "Solver_Output", "BUCKLING")
    if os.path.isfile(os.path.join(bk, "s8a_load_factors.csv")):
        lfv = float(lam(bk)[0])
        item("Structural mesh sensitivity", "%s: lambda1" % tag, lfv, "-", lv8, tag, "08_Structural_Analysis/Mesh_Study/Variants/%s/Solver_Output/BUCKLING/s8a_load_factors.csv" % tag,
             "first load factor", float(ms8[tag]["λ1"]), "08_Structural_Analysis/Mesh_Study/STRUCTURAL_MESH_STUDY.csv", (None, 5e-7))
        base[tag]["lam"] = lfv
if "B" in base:
    dv = max(abs(v["vm"] / base["B"]["vm"] - 1) for k, v in base.items())
    dl = max(abs(v["lam"] / base["B"]["lam"] - 1) for k, v in base.items() if "lam" in v)
    item("Structural mesh sensitivity", "max |change| vs mesh B: LC2 peak / lambda1", "%.1e / %.1e" % (dv, dl), "-", "FE-MESH-STUDY (Section 8B)", "all variants", "recomputed above",
         "max over XC, C, FR, FA, FC (IL: static only) of the relative change against B", status="VERIFIED" if dv < 1e-3 and dl < 1e-4 else "MISMATCH",
         note="LC1 bore surface stress: -2.1 % vs the 1-D exact value (8B, F-046) - the only mesh-sensitive quantity")

# ----------------------------------------------------------------------------------------------- PARAMETRIC (9B-1 CFD + 9B-2 FE)
PS = P("10_Parametric_Study")
cfdcsv = {r["case"]: r for r in csv.DictReader(l for l in open(os.path.join(PS, "CFD_Results", "PARAMETRIC_CFD_RESULTS.csv")) if not l.startswith("#"))}
stcsv = {r["Case"]: r for r in csv.DictReader(l for l in open(os.path.join(PS, "Results", "PARAMETRIC_STRUCTURAL_RESULTS.csv"), encoding="utf-8") if not l.startswith("#"))}
GEO = {"V01_LOW": (0.010, 0.020), "V03_HIGH": (0.010, 0.020), "Q01_LOW": (0.010, 0.020), "Q03_HIGH": (0.010, 0.020), "T01_THIN": (0.010, 0.018), "T03_THICK": (0.010, 0.022)}
for case, (ri, ro) in GEO.items():
    cr = cfd_reports(os.path.join(PS, "CFD_Cases", case, "Audit"))
    lvP = "CFD (9B-1) + FE static / buckling (9B-2), S1 supports"
    csrc = "10_Parametric_Study/CFD_Cases/%s/Audit/" % case
    dcsv = "10_Parametric_Study/CFD_Results/PARAMETRIC_CFD_RESULTS.csv"
    item("Parametric", "%s: pressure drop" % case, cr["dp"], "Pa", lvP, case, csrc + "fluent_si_p_area.txt", "Fluent report", float(cfdcsv[case]["dp_Pa"]), dcsv, 1e-6)
    item("Parametric", "%s: outlet bulk temperature" % case, cr["T_out"], "K", lvP, case, csrc + "fluent_si_T_mass.txt", "Fluent report", float(cfdcsv[case]["T_out_K"]), dcsv, 1e-6)
    item("Parametric", "%s: maximum solid temperature (outer-wall facet)" % case, cr["Tmax_facet"], "K", lvP, case, csrc + "fluent_si_Twall_max.txt", "Fluent report",
         float(cfdcsv[case]["T_solid_max_K"]), dcsv, 1e-6)
    sc_dir = os.path.join(PS, "Structural_Cases", case)
    dsx = os.path.join(sc_dir, "Audits", "Presolve_Inputs", "%s_LC2_presolve_ds.dat" % case)
    so = os.path.join(sc_dir, "Solver_Output")
    a1 = static(os.path.join(so, "LC1", "s7b_nodal.csv"), dsx, ri, ro)
    a2 = static(os.path.join(so, "LC2", "s7b_nodal.csv"), dsx, ri, ro, os.path.join(so, "LC2", "s7b_react.csv"))
    lf = float(lam(os.path.join(so, "BUCKLING"))[0])
    r = stcsv[case]; dsc = "10_Parametric_Study/Results/PARAMETRIC_STRUCTURAL_RESULTS.csv"
    ssrc = "10_Parametric_Study/Structural_Cases/%s/Solver_Output/" % case
    item("Parametric", "%s: LC1 maximum deformation" % case, a1["utot_max"] * 1e3, "mm", lvP, case, ssrc + "LC1/s7b_nodal.csv", "max |u|", float(r["Max deformation [mm]"]), dsc, (None, 5e-6))
    item("Parametric", "%s: LC1 maximum von Mises" % case, a1["vm_max"] / 1e6, "MPa", lvP, case, ssrc + "LC1/s7b_nodal.csv", "max over corner nodes", float(r["LC1 max stress [MPa]"]), dsc, (None, 5e-4))
    item("Parametric", "%s: LC2 maximum von Mises" % case, a2["vm_max"] / 1e6, "MPa", lvP, case, ssrc + "LC2/s7b_nodal.csv", "max over corner nodes", float(r["LC2 max stress [MPa]"]), dsc, (None, 5e-4))
    item("Parametric", "%s: LC2 yield utilisation" % case, a2["util"], "-", lvP, case, ssrc + "LC2/s7b_nodal.csv", "max vm / S_y(T)", float(r["Yield utilization [-]"]), dsc, (None, 5e-5))
    item("Parametric", "%s: lambda1 (S1)" % case, lf, "-", lvP, case, ssrc + "BUCKLING/s8a_load_factors.csv", "first load factor", float(r["Lambda1 [-]"]), dsc, (None, 5e-6))
    item("Parametric", "%s: critical load P_cr" % case, lf * abs(a2["F_in"]) / 1e3, "kN", lvP, case, ssrc + "BUCKLING/s8a_load_factors.csv + " + ssrc + "LC2/s7b_react.csv", "lambda1 x end reaction", float(r["Critical buckling load [kN]"]), dsc, (None, 0.005))

out = {"note": "RE-ANALYSIS 2026 - Section 10A master data, recomputed from raw files", "items": ITEMS,
       "counts": {s: sum(1 for i in ITEMS if i["status"] == s) for s in sorted(set(i["status"] for i in ITEMS))}}
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(out["counts"])
for i in ITEMS:
    if i["status"] == "MISMATCH":
        print("MISMATCH", i["group"], i["parameter"], i["value"], i["documented"], i["documented_in"])
