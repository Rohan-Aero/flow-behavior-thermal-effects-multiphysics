# -*- coding: utf-8 -*-
"""SECTION 8B - temperature-mapping check on every structural mesh (RE-ANALYSIS 2026).
For each mesh, the nodal temperatures Mechanical wrote to the solver input (BFBLOCK, degC) are compared with
 (A) the shape-function re-evaluation of the Fluent solid NODE field (the same source that Mechanical maps: the
     mesh-based External Data of baseline_medium_final), and
 (B) the Fluent finite-volume solution (cell/face reference field),
using the Section 7A validation modules unchanged (parse_ds, source_mesh_interp.HexField, mapping_validation).
Usage: python mapping_check_8B.py <out_json> tag=path_to_ds.dat [tag=path ...]"""
import os, sys, json
import numpy as np
S7A = "<OUTPUT_ROOT>/S7A"
sys.path.insert(0, os.path.join(S7A, "Validation"))
sys.path.insert(0, os.path.join(S7A, "MeshBased"))
from parse_ds import parse
from source_mesh_interp import HexField
from mapping_validation import build_reference, ref_eval
import fluent_solid_mesh_from_case as fm

U = "<PROJECT_ROOT>"
case = os.path.join(U, "06_Fluent_CFD", "Case", "baseline_medium_final.cas.h5")
ncsv = os.path.join(S7A, "MeshBased", "out", "fluent_solid_node_temperature.csv")
src = os.path.join(U, "07_Thermal_Analysis", "Temperature_Source")
X, cf, _, _, _ = fm.read_solid(case)
cells = sorted(cf)
conn = np.array([fm.hex_from_faces(cf[c]) for c in cells])
Xid = np.vstack([np.zeros(3), X])
d = np.loadtxt(ncsv, delimiter=",", skiprows=1)
Tid = np.full(len(Xid), np.nan)
Tid[d[:, 0].astype(int)] = d[:, 1]
H = HexField(Xid, conn, Tid)
R, Z, G, rinfo, D = build_reference(src)
out = {"source": {"case": "baseline_medium_final (same for every mesh)", "node_min_K": float(np.nanmin(Tid)),
                  "node_max_K": float(np.nanmax(Tid))}}
for arg in sys.argv[2:]:
    tag, path = arg.split("=", 1)
    nodes, elems, bf, comps, tref = parse(path)
    ids = np.array(sorted(nodes))
    XX = np.array([nodes[i] for i in ids])
    Tm = np.array([bf.get(i, np.nan) for i in ids]) + 273.15
    has = ~np.isnan(Tm)
    Th, dev = H.evaluate(XX)
    eA = Tm - Th
    r = np.hypot(XX[:, 0], XX[:, 1]); z = XX[:, 2]
    eB = Tm - ref_eval(R, Z, G, r, z, "linear")
    inside = dev <= 1e-9
    band = {}
    for lo, hi in ((0, 14), (14, 586), (586, 600.1)):
        m = (z * 1e3 >= lo) & (z * 1e3 < hi)
        band["%g-%g mm" % (lo, hi)] = {"n": int(m.sum()), "A_max": float(np.nanmax(np.abs(eA[m]))), "B_max": float(np.nanmax(np.abs(eB[m]))),
                                     "B_mean": float(np.nanmean(np.abs(eB[m])))}
    out[tag] = {"ds": os.path.basename(path), "nodes": int(len(ids)), "elements": int(len(elems)), "tref_degC": tref,
                "mapped": int(has.sum()), "unmapped": int((~has).sum()),
                "T_min_K": float(np.nanmin(Tm)), "T_max_K": float(np.nanmax(Tm)),
                "extrapolation_above_source_max_K": float(max(0.0, np.nanmax(Tm) - np.nanmax(Tid))),
                "extrapolation_below_source_min_K": float(max(0.0, np.nanmin(Tid) - np.nanmin(Tm))),
                "nodes_outside_source_mesh": int((~inside).sum()), "outside_max_local_coord_excess": float(dev.max()),
                "A_vs_source_node_field": {"max": float(np.nanmax(np.abs(eA))), "mean": float(np.nanmean(np.abs(eA))),
                                           "max_inside": float(np.nanmax(np.abs(eA[inside]))),
                                           "max_outside": float(np.nanmax(np.abs(eA[~inside]))) if (~inside).any() else 0.0},
                "B_vs_FV_solution": {"max": float(np.nanmax(np.abs(eB))), "mean": float(np.nanmean(np.abs(eB))),
                                     "rms": float(np.sqrt(np.nanmean(eB ** 2)))},
                "by_axial_band": band}
    print(tag, json.dumps({k: out[tag][k] for k in ("nodes", "unmapped", "T_min_K", "T_max_K", "A_vs_source_node_field", "B_vs_FV_solution")}))
json.dump(out, open(sys.argv[1], "w"), indent=1)
