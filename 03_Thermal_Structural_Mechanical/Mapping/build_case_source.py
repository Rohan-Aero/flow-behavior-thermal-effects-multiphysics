# -*- coding: utf-8 -*-
"""Section 9B-2 - MESH-BASED temperature source (Mechanical External Data) for every parametric case.

RE-ANALYSIS 2026 helper: re-keys newly generated Fluent node temperatures; no value is created or interpolated.

Identical method to Section 7A (07_Thermal_Analysis/Mapping/MeshBased/build_mesh_based_source.py and
fluent_solid_mesh_from_case.py, both imported unchanged):
  master  = the case's own Fluent solid_domain mesh, read from ITS case file (Fluent node / cell ids), written as an
            MAPDL NBLOCK/EBLOCK input that MAPDL turns into a native CDB (CDWRITE)
  data    = the case's own Fluent NODE temperatures (EnSight Gold export written by solve_param.py), keyed by node id
Checks per case (report JSON):
  EnSight nodes <-> case nodes one-to-one by coordinates; EnSight hexa8 connectivity == connectivity rebuilt from the
  case faces; no NaN; node-temperature range; the solid-mesh node/element blocks compared with the P00 (7A) master
  (V/Q/C00 must be identical, so the 7A CDB is the master for them); for C00 the node temperatures must be identical
  to the 7A file (the C00 EnSight export is byte-identical to the 7A one).
The 7A cross-check against Fluent's double-precision ASCII boundary-node export is not repeated per case (that
export is not written by the parametric journal); the EnSight float32 node values were shown in 7A to agree with the
double-precision values to 3.0e-5 K, and the same exporter is used here.
Usage: python build_case_source.py <uploads_root> <case> <out_dir> <ref_7A_dir>
"""
import os, sys, json, hashlib
import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "S7A_MeshBased"))
import fluent_solid_mesh_from_case as fm           # 7A, unchanged
import build_mesh_based_source as bm               # 7A, unchanged (read_ensight_part)


def blocks(inp):
    """NBLOCK and EBLOCK body lines of an MAPDL input written by the 7A writer (title lines excluded)."""
    L = open(inp).read().splitlines()
    i0 = [i for i, l in enumerate(L) if l.startswith("NBLOCK")][0]
    i1 = [i for i, l in enumerate(L) if l.startswith("ALLSEL")][0]
    return L[i0:i1]


def main(up, case, out, ref7a):
    os.makedirs(out, exist_ok=True)
    cd = os.path.join(up, "10_Parametric_Study", "CFD_Cases", case)
    casef = os.path.join(cd, "Case", "%s_final.cas.h5" % case)
    ens = os.path.join(cd, "EnSight")
    X, cf, (cmin, cmax), use, zones = fm.read_solid(casef)
    cells = sorted(cf)
    conn = np.array([fm.hex_from_faces(cf[c]) for c in cells])
    nodes = np.unique(conn)
    E = bm.read_ensight_part(os.path.join(ens, "solid_domain_T.geo"), os.path.join(ens, "solid_domain_T.scl1"))
    rep = dict(case=case, case_file=casef, case_sha256=fm.sha(casef),
               ensight_geo_sha256=fm.sha(os.path.join(ens, "solid_domain_T.geo")),
               ensight_scl1_sha256=fm.sha(os.path.join(ens, "solid_domain_T.scl1")),
               ensight_variable=E["var_desc"], case_solid_cells=len(cells), case_solid_nodes=int(len(nodes)),
               ensight_nodes=int(E["X"].shape[0]), ensight_hexa8=int(E["els"].get("hexa8", np.zeros((0, 8))).shape[0]),
               ensight_other_element_types=[k for k in E["els"] if k != "hexa8"])
    tree = cKDTree(X[nodes - 1])
    d, i = tree.query(E["X"])
    ens2case = nodes[i]
    rep["node_match_max_dist_m"] = float(d.max())
    rep["node_match_one_to_one"] = bool(len(np.unique(i)) == len(nodes) == E["X"].shape[0])
    ehex = ens2case[E["els"]["hexa8"] - 1]
    sa = set(tuple(sorted(r)) for r in conn.tolist())
    sb = set(tuple(sorted(r)) for r in ehex.tolist())
    rep["connectivity_identical_as_sets"] = bool(sa == sb)
    T = np.full(int(nodes.max()) + 1, np.nan)
    T[ens2case] = E["T"]
    Tn = T[nodes]
    rep["node_T_min_K"], rep["node_T_max_K"], rep["node_T_nan"] = float(Tn.min()), float(Tn.max()), int(np.isnan(Tn).sum())
    r = np.hypot(X[nodes - 1, 0], X[nodes - 1, 1])
    rep["node_r_min_mm"], rep["node_r_max_mm"] = float(r.min() * 1e3), float(r.max() * 1e3)
    rep["node_z_min_m"], rep["node_z_max_m"] = float(X[nodes - 1, 2].min()), float(X[nodes - 1, 2].max())
    csv = os.path.join(out, "fluent_solid_node_temperature.csv")
    with open(csv, "w", newline="\n") as fh:
        fh.write("node_id,T_K\n")
        for n, t in zip(nodes, Tn):
            fh.write("%d,%.9g\n" % (n, t))
    rep["node_temperature_csv_sha256"] = fm.sha(csv)
    # MAPDL input (7A writer), then a case-specific title line (the 7A writer names the P00 case in its title)
    fm.main(casef, out, save_npy=False)
    inp = os.path.join(out, "build_fluent_solid_cdb.inp")
    txt = open(inp).read().replace("Fluent solid_domain mesh (baseline_medium_final.cas.h5)",
                                   "Fluent solid_domain mesh (%s_final.cas.h5)" % case)
    open(inp, "w", newline="\n").write(txt)
    rep["mapdl_input_sha256"] = fm.sha(inp)
    # comparison with the P00 (7A) master. Fluent renumbers node ids when a mesh is loaded by mesh.replace, so the
    # comparison is made BY COORDINATES (the 7A NBLOCK), not by id; each case always uses its OWN master + data pair.
    ref_inp = os.path.join(ref7a, "build_fluent_solid_cdb.inp")
    rep["mesh_blocks_identical_to_P00_7A_textually"] = bool(blocks(inp) == blocks(ref_inp))
    RL = blocks(ref_inp)
    NL = RL[2:[i for i, l in enumerate(RL) if l.startswith("N,R5.3")][0]]          # the NBLOCK body only
    ref_nodes = np.array([[float(l[27:48]), float(l[48:69]), float(l[69:90])] for l in NL])
    ref_ids = np.array([int(l[:9]) for l in NL])
    ref_csv = os.path.join(ref7a, "fluent_solid_node_temperature.csv")
    a = np.loadtxt(ref_csv, delimiter=",", skiprows=1)
    TP = dict(zip(a[:, 0].astype(int), a[:, 1]))
    if len(ref_nodes) == len(nodes):
        dd, ii = cKDTree(ref_nodes).query(X[nodes - 1])
        rep["same_node_coordinates_as_P00"] = bool(dd.max() < 1e-9 and len(np.unique(ii)) == len(nodes))
        rep["node_coordinate_match_max_dist_m"] = float(dd.max())
        if rep["same_node_coordinates_as_P00"]:
            # compare the values as WRITTEN to the CSV files (%.9g of the float32 EnSight values) on both sides
            bw = np.loadtxt(csv, delimiter=",", skiprows=1)
            TC = dict(zip(bw[:, 0].astype(int), bw[:, 1]))
            dT = np.array([TC[n] for n in nodes]) - np.array([TP[k] for k in ref_ids[ii]])
            rep["node_T_minus_P00_by_coordinates_K"] = {"min": float(dT.min()), "max": float(dT.max()), "mean": float(dT.mean()),
                                                         "identical": bool(np.all(dT == 0.0))}
    else:
        rep["same_node_coordinates_as_P00"] = False
    ok = (rep["node_match_one_to_one"] and rep["node_match_max_dist_m"] < 1e-7 and rep["connectivity_identical_as_sets"]
          and rep["node_T_nan"] == 0 and 293.15 <= rep["node_T_min_K"] and rep["node_T_max_K"] <= 673.15)
    if case == "C00_PIPELINE_CHECK":
        ok = ok and rep.get("same_node_coordinates_as_P00") and rep["node_T_minus_P00_by_coordinates_K"]["identical"]
    rep["ALL_CHECKS_PASS"] = bool(ok)
    json.dump(rep, open(os.path.join(out, "case_source_report.json"), "w"), indent=1)
    print("%-20s nodes %d cells %d  T %.3f-%.3f K  same node coords as P00 %s  dT vs P00 %s  PASS %s"
          % (case, len(nodes), len(cells), rep["node_T_min_K"], rep["node_T_max_K"], rep.get("same_node_coordinates_as_P00"),
             rep.get("node_T_minus_P00_by_coordinates_K"), ok))


if __name__ == "__main__":
    main(*sys.argv[1:5])
