# -*- coding: utf-8 -*-
"""SECTION 9B-2 Part D - temperature-mapping audit of every parametric structural case (RE-ANALYSIS 2026).

For each case the nodal temperatures Mechanical wrote to the LC2 solver input (BFBLOCK, degC) are compared with:
 (A) the shape-function re-evaluation of the case's OWN Fluent solid NODE field (the same source Mechanical maps: the
     case CDB master + fluent_solid_node_temperature.csv), using the Section 7A module source_mesh_interp.HexField
     unchanged. This is the mapping (interpolation) error itself.
 (B) the Fluent finite-volume wall-face temperatures of the case (Exports/wall_outer.csv, wall_interface.csv; theta-mean
     per axial slab, linear in z) on the outer and bore surface nodes. This is a surface check against the FV solution
     (the 7A cell-centre reference grid is not rebuilt: the parametric journal does not export solid cell centres).
Also: unmapped nodes, nodes outside the source mesh (48-gon chord gap -> Nearest Node / projection), mapped vs source
temperature range, and the mid-span (z = L/2) through-wall dT and radially area-weighted section mean of the mapped
field vs the source node field on the same plane.
Acceptance (fixed before the audit was run): no unmapped node; (A) <= 0.25 K (the 7A acceptance band of the
FV comparison; the accepted 7A baseline value of (A) is 0.092 K and is reported alongside); no extrapolation beyond the
source node range by more than 0.05 K; mid-span through-wall dT and section mean preserved within 0.05 K.
Usage: python mapping_audit_9B2.py <uploads_root> <s9b2_root> <out_json>
"""
import os, sys, json
import numpy as np

S7A = "<OUTPUT_ROOT>/S7A"
sys.path.insert(0, os.path.join(S7A, "Validation"))
sys.path.insert(0, os.path.join(S7A, "MeshBased"))
from parse_ds import parse
from source_mesh_interp import HexField
import fluent_solid_mesh_from_case as fm

UP, S9, OUTJ = sys.argv[1:4]
PS = os.path.join(UP, "10_Parametric_Study")
CASES = {  # case: (Ri, Ro, family)
    "C00_PIPELINE_CHECK": (0.010, 0.020, "baseline geometry (mesh B)"),
    "V01_LOW": (0.010, 0.020, "baseline geometry (mesh B)"),
    "V03_HIGH": (0.010, 0.020, "baseline geometry (mesh B)"),
    "Q01_LOW": (0.010, 0.020, "baseline geometry (mesh B)"),
    "Q03_HIGH": (0.010, 0.020, "baseline geometry (mesh B)"),
    "T01_THIN": (0.010, 0.018, "T01 thin wall (36 x 4 x 130)"),
    "T03_THICK": (0.010, 0.022, "T03 thick wall (36 x 6 x 130)"),
}
L = 0.6


def trap(f, x):
    return float(np.sum(0.5 * (f[1:] + f[:-1]) * (x[1:] - x[:-1])))


def wall(p):
    a = np.loadtxt(p, delimiter=",", skiprows=1)
    z, T = a[:, 3], a[:, 8]
    zs = np.unique(np.round(z, 7))
    Tm = np.array([T[np.abs(z - v) < 1e-6].mean() for v in zs])
    ptp = max(float(np.ptp(T[np.abs(z - v) < 1e-6])) for v in zs)
    return zs, Tm, ptp


def plane_stats(r, th, T, zmask, Ri, Ro):
    """theta-mean through-wall dT (outer - inner) and radially area-weighted mean on one axial plane"""
    rr = np.round(r[zmask], 7); tt = T[zmask]; thh = np.round(th[zmask], 4)
    rads = np.unique(rr)
    prof = np.array([tt[rr == v].mean() for v in rads])
    inner = tt[np.abs(rr - Ri) < 1e-6]; outer = tt[np.abs(rr - Ro) < 1e-6]
    return {"dT_K": float(outer.mean() - inner.mean()), "mean_K": trap(prof * rads, rads) / trap(rads, rads),
            "n_radii": int(len(rads)), "theta_ptp_outer_K": float(np.ptp(outer)), "theta_ptp_inner_K": float(np.ptp(inner))}


out = {"note": "RE-ANALYSIS 2026 - Section 9B-2 mapping audit (Part D)", "cases": {}}
for case, (Ri, Ro, fam) in CASES.items():
    ds = os.path.join(PS, "Structural_Cases", case, "Audits", "Presolve_Inputs", "%s_LC2_presolve_ds.dat" % case)
    if not os.path.isfile(ds):
        print("missing", ds)
        continue
    casef = os.path.join(PS, "CFD_Cases", case, "Case", "%s_final.cas.h5" % case)
    ncsv = os.path.join(S9, "Mapping", case, "fluent_solid_node_temperature.csv")
    X, cf, _, _, _ = fm.read_solid(casef)
    cells = sorted(cf)
    conn = np.array([fm.hex_from_faces(cf[c]) for c in cells])
    Xid = np.vstack([np.zeros(3), X])
    d = np.loadtxt(ncsv, delimiter=",", skiprows=1)
    Tid = np.full(len(Xid), np.nan)
    Tid[d[:, 0].astype(int)] = d[:, 1]
    H = HexField(Xid, conn, Tid)
    nodes, elems, bf, comps, tref = parse(ds)
    ids = np.array(sorted(nodes))
    XX = np.array([nodes[i] for i in ids])
    Tm = np.array([bf.get(i, np.nan) for i in ids]) + 273.15
    has = ~np.isnan(Tm)
    Th, dev = H.evaluate(XX)
    eA = Tm - Th
    r = np.hypot(XX[:, 0], XX[:, 1]); z = XX[:, 2]; th = np.degrees(np.arctan2(XX[:, 1], XX[:, 0]))
    inside = dev <= 1e-9
    band = {}
    for lo, hi in ((0, 14), (14, 586), (586, 600.1)):
        m = (z * 1e3 >= lo) & (z * 1e3 < hi)
        band["%g-%g mm" % (lo, hi)] = {"n": int(m.sum()), "A_max_K": float(np.nanmax(np.abs(eA[m])))}
    # (B) surface check vs FV wall-face temperatures
    ex = os.path.join(PS, "CFD_Cases", case, "Exports")
    B = {}
    for lab, fname, rad in (("outer", "wall_outer.csv", Ro), ("bore", "wall_interface.csv", Ri)):
        zs, Tw, ptp = wall(os.path.join(ex, fname))
        m = np.abs(r - rad) < 1e-7
        eB = Tm[m] - np.interp(z[m], zs, Tw)
        mi = m & (z > 0.014) & (z < 0.586)
        eBi = Tm[mi] - np.interp(z[mi], zs, Tw)
        B[lab] = {"nodes": int(m.sum()), "max_abs_K": float(np.abs(eB).max()), "mean_K": float(eB.mean()),
                  "rms_K": float(np.sqrt((eB ** 2).mean())), "max_abs_14_586mm_K": float(np.abs(eBi).max()),
                  "fluent_face_theta_ptp_max_K": ptp}
    # mid-span plane: mapped vs source node field
    zm = np.abs(z - L / 2) < 1e-7
    mapped_mid = plane_stats(r, th, Tm, zm, Ri, Ro)
    Xs = X[np.unique(conn) - 1]; Ts = Tid[np.unique(conn)]
    rs = np.hypot(Xs[:, 0], Xs[:, 1]); zsrc = Xs[:, 2]; ths = np.degrees(np.arctan2(Xs[:, 1], Xs[:, 0]))
    src_mid = plane_stats(rs, ths, Ts, np.abs(zsrc - L / 2) < 1e-7, Ri, Ro)
    out["cases"][case] = {
        "family": fam, "ds": os.path.basename(ds), "nodes": int(len(ids)), "elements": int(len(elems)), "tref_degC": tref,
        "source": {"case_file": os.path.basename(casef), "source_nodes": int(len(np.unique(conn))), "source_cells": int(len(conn)),
                   "source_radial_layers": int(len(H.r_edges) - 1), "node_T_min_K": float(np.nanmin(Ts)), "node_T_max_K": float(np.nanmax(Ts))},
        "mapped": int(has.sum()), "unmapped": int((~has).sum()),
        "T_min_K": float(np.nanmin(Tm)), "T_max_K": float(np.nanmax(Tm)),
        "extrapolation_above_source_max_K": float(max(0.0, np.nanmax(Tm) - np.nanmax(Ts))),
        "extrapolation_below_source_min_K": float(max(0.0, np.nanmin(Ts) - np.nanmin(Tm))),
        "nodes_outside_source_mesh": int((~inside).sum()), "outside_max_local_coord_excess": float(dev.max()),
        "A_vs_source_node_field": {"max_K": float(np.nanmax(np.abs(eA))), "mean_abs_K": float(np.nanmean(np.abs(eA))),
                                   "rms_K": float(np.sqrt(np.nanmean(eA ** 2))),
                                   "max_inside_K": float(np.nanmax(np.abs(eA[inside]))),
                                   "max_outside_K": float(np.nanmax(np.abs(eA[~inside]))) if (~inside).any() else 0.0,
                                   "by_axial_band": band},
        "B_vs_fluent_wall_faces": B,
        "midspan": {"mapped": mapped_mid, "source_nodes": src_mid,
                    "dT_diff_K": mapped_mid["dT_K"] - src_mid["dT_K"], "mean_diff_K": mapped_mid["mean_K"] - src_mid["mean_K"]},
    }
    c = out["cases"][case]
    c["checks"] = {"no unmapped nodes": c["unmapped"] == 0,
                   "mapping error (A) max <= 0.25 K": c["A_vs_source_node_field"]["max_K"] <= 0.25,
                   "no extrapolation beyond the source node range > 0.05 K": max(c["extrapolation_above_source_max_K"], c["extrapolation_below_source_min_K"]) <= 0.05,
                   "mid-span through-wall dT preserved within 0.05 K": abs(c["midspan"]["dT_diff_K"]) <= 0.05,
                   "mid-span section mean preserved within 0.05 K": abs(c["midspan"]["mean_diff_K"]) <= 0.05}
    c["ALL_PASS"] = all(c["checks"].values())
    # information: the accepted 7A / 8B baseline value of (A) on mesh B is 0.092 K (CFD_TO_MECHANICAL_MAPPING_AUDIT.md)
    c["A_max_minus_7A_baseline_0.092K"] = c["A_vs_source_node_field"]["max_K"] - 0.092
    print(case, json.dumps({"unmapped": c["unmapped"], "T": [round(c["T_min_K"], 3), round(c["T_max_K"], 3)],
                            "A_max": round(c["A_vs_source_node_field"]["max_K"], 4), "outside": c["nodes_outside_source_mesh"],
                            "mid dT map/src": [round(mapped_mid["dT_K"], 4), round(src_mid["dT_K"], 4)],
                            "mid mean map/src": [round(mapped_mid["mean_K"], 4), round(src_mid["mean_K"], 4)],
                            "B outer/bore max": [round(B["outer"]["max_abs_K"], 3), round(B["bore"]["max_abs_K"], 3)], "PASS": c["ALL_PASS"]}))
json.dump(out, open(OUTJ, "w"), indent=1)
