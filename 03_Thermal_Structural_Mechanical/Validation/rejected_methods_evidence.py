# -*- coding: utf-8 -*-
"""Section 7A - evidence for the transfer methods that were tried and rejected (throwaway probe projects).
Same two checks as validate_mapping_7A.py: (A) vs the Fluent node field evaluated with the source hexahedra's shape
functions, (B) vs the independent finite-volume reference (cell + face values). RE-ANALYSIS 2026."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'MeshBased')); sys.path.insert(0, os.path.join(HERE, '..', 'Mapping', 'Scripts'))
from parse_ds import parse
from mapping_validation import build_reference, ref_eval
from source_mesh_interp import HexField
import fluent_solid_mesh_from_case as fm


def run(root, out):
    src = os.path.join(root, '07_Thermal_Analysis', 'Temperature_Source')
    case = os.path.join(root, '06_Fluent_CFD', 'Case', 'baseline_medium_final.cas.h5')
    X, cf, _, _, _ = fm.read_solid(case); cells = sorted(cf); conn = np.array([fm.hex_from_faces(cf[c]) for c in cells])
    Xid = np.vstack([np.zeros(3), X]); d = np.loadtxt(os.path.join(root, '07_Thermal_Analysis', 'Mapping', 'MeshBased', 'fluent_solid_node_temperature.csv'), delimiter=',', skiprows=1)
    Tid = np.full(len(Xid), np.nan); Tid[d[:, 0].astype(int)] = d[:, 1]; H = HexField(Xid, conn, Tid)
    R, Z, G, _, _ = build_reference(src)
    wb = os.path.join(root, '08_Structural_Analysis', 'Workbench')
    cases = [("PC-V1 point cloud (cells+faces), Triangulation, outside=Projection, mesh 48x5x100", 'probe2/probe4_V1_PointCloud_Tri_Projection_ds.dat'),
             ("PC-V2 point cloud (cells+faces), Triangulation, outside=Nearest Node, mesh 48x5x100", 'probe2/probe4_V2_PointCloud_Tri_Nearest_ds.dat'),
             ("PC-V3 point cloud, 'Bucket Volume' requested (log shows identical result to V1)", 'probe2/probe4_V3_Bucket_Tri_Projection_ds.dat'),
             ("MB-P0 mesh-based CDB master, Program Controlled (Bucket/Shape Fn, outside=Weighted Avg), mesh M36", 'probe9/probe9_P0_ProgramControlled_ds.dat'),
             ("MB-P2 mesh-based CDB master, Bucket Volume + Shape Functions, outside=Nearest Node, mesh M36 (SELECTED)", 'probe9/probe9_P2_Bucket_ShapeFn_Nearest_ds.dat')]
    res = []
    for label, rel in cases:
        p = os.path.join(wb, rel)
        if not os.path.exists(p):
            res.append({"case": label, "file": rel, "status": "file not available"}); continue
        nodes, elems, bf, comps, tref = parse(p)
        ids = np.array(sorted(nodes)); XX = np.array([nodes[i] for i in ids]); r = np.hypot(XX[:, 0], XX[:, 1]); z = XX[:, 2]
        Tm = np.array([bf.get(i, np.nan) for i in ids]) + 273.15; has = ~np.isnan(Tm)
        Th, dev = H.evaluate(XX); Tl = ref_eval(R, Z, G, r, z, 'linear')
        eA = np.abs(Tm - Th)[has]; eB = np.abs(Tm - Tl)[has]
        far = has & (z > 0.014) & (z < 0.586)
        res.append({"case": label, "file": rel, "nodes": int(len(ids)), "mapped": int(has.sum()), "unmapped_no_BF": int((~has).sum()),
                    "outside_nodes_component": int(len(comps.get('OUTSIDE_NODES', []))),
                    "A_max_K": float(eA.max()), "A_mean_K": float(eA.mean()), "B_max_K": float(eB.max()), "B_mean_K": float(eB.mean()),
                    "B_max_K_z14_586mm": float(np.abs(Tm - Tl)[far].max())})
    json.dump(res, open(os.path.join(out, 'rejected_methods_evidence.json'), 'w'), indent=1)
    for x in res:
        print(json.dumps(x))


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
