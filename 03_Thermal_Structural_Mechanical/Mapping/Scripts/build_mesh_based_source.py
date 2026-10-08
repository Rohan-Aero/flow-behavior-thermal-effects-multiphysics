# -*- coding: utf-8 -*-
"""Section 7A (mapping fix) - assemble the MESH-BASED temperature source for Mechanical External Data.

Inputs (all native Fluent outputs of baseline_medium_final, read-only):
  case file            06_Fluent_CFD/Case/baseline_medium_final.cas.h5   (solid_domain nodes + cells, double precision)
  EnSight Gold export  07_Thermal_Analysis/Temperature_Source/EnSight/solid_domain_T.geo/.scl1
                       (Fluent's own export: solid mesh + Fluent NODE temperatures, C binary float32)
  ASCII node export    07_Thermal_Analysis/Temperature_Source/fluent_solid_zone_nodes.csv (boundary nodes, double)
Outputs (07_Thermal_Analysis/Mapping/MeshBased):
  build_fluent_solid_cdb.inp        MAPDL input (NBLOCK/EBLOCK SOLID185, Fluent node/cell ids) -> CDWRITE -> CDB
  fluent_solid_node_temperature.csv node_id,T_K  (Fluent node values, one row per solid node)
  mesh_based_source_report.json     every check below
Checks: EnSight nodes <-> case nodes one-to-one by coordinates; EnSight hexa8 connectivity == connectivity rebuilt
from the case faces; EnSight node T vs double-precision ASCII node export on the boundary nodes.
No value is interpolated or created here: the temperatures are Fluent's node values, only re-keyed by node id.
Usage: python build_mesh_based_source.py <project_root> <out_dir>
RE-ANALYSIS 2026 helper.
"""
import os, sys, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fluent_solid_mesh_from_case as fm


def read_ensight_part(geo, scl, part_name="solid_domain"):
    b = open(geo, 'rb').read()
    p = [0]

    def s80():
        t = b[p[0]:p[0] + 80].decode(errors='ignore').strip('\x00 ').strip(); p[0] += 80; return t

    def i4(n=1):
        a = np.frombuffer(b, np.int32, n, p[0]); p[0] += 4 * n; return a

    def f4(n):
        a = np.frombuffer(b, np.float32, n, p[0]); p[0] += 4 * n; return a
    hdr = [s80() for _ in range(5)]
    assert hdr[0] == 'C Binary' and hdr[3] == 'node id assign' and hdr[4] == 'element id assign', hdr
    parts = {}
    while p[0] < len(b):
        assert s80() == 'part'
        pn = int(i4()[0]); desc = s80(); assert s80() == 'coordinates'
        nn = int(i4()[0]); X = np.c_[f4(nn), f4(nn), f4(nn)]
        els = {}
        while p[0] < len(b):
            et = b[p[0]:p[0] + 80].decode(errors='ignore').strip('\x00 ').strip()
            if et == 'part':
                break
            p[0] += 80; ne = int(i4()[0])
            npe = {'hexa8': 8, 'penta6': 6, 'tetra4': 4, 'pyramid5': 5, 'quad4': 4, 'tria3': 3}[et]
            els[et] = i4(ne * npe).reshape(ne, npe).copy()
        parts[desc] = (pn, X, els)
    pn, X, els = parts[part_name]
    v = open(scl, 'rb').read(); q = 0
    vdesc = v[:80].decode(errors='ignore').strip('\x00 ').strip(); q = 80
    T = None
    while q < len(v):
        assert v[q:q + 80].decode(errors='ignore').strip('\x00 ').strip() == 'part'; q += 80
        vpn = int(np.frombuffer(v, np.int32, 1, q)[0]); q += 4
        loc = v[q:q + 80].decode(errors='ignore').strip('\x00 ').strip(); q += 80
        n = parts_nn = [pp[1].shape[0] for pp in parts.values() if pp[0] == vpn][0]
        a = np.frombuffer(v, np.float32, n, q); q += 4 * n
        if vpn == pn:
            assert loc == 'coordinates', loc      # node-centred values
            T = a.astype(np.float64)
    return dict(part=pn, X=X.astype(np.float64), els=els, T=T, var_desc=vdesc, parts=sorted(parts))


def main(root, out):
    os.makedirs(out, exist_ok=True)
    case = os.path.join(root, '06_Fluent_CFD', 'Case', 'baseline_medium_final.cas.h5')
    ens = os.path.join(root, '07_Thermal_Analysis', 'Temperature_Source', 'EnSight')
    asc = os.path.join(root, '07_Thermal_Analysis', 'Temperature_Source', 'fluent_solid_zone_nodes.csv')
    X, cf, (cmin, cmax), use, zones = fm.read_solid(case)
    cells = sorted(cf)
    conn = np.array([fm.hex_from_faces(cf[c]) for c in cells])
    nodes = np.unique(conn)
    E = read_ensight_part(os.path.join(ens, 'solid_domain_T.geo'), os.path.join(ens, 'solid_domain_T.scl1'))
    rep = dict(case=case, case_sha256=fm.sha(case),
               ensight_geo_sha256=fm.sha(os.path.join(ens, 'solid_domain_T.geo')),
               ensight_scl1_sha256=fm.sha(os.path.join(ens, 'solid_domain_T.scl1')),
               ensight_parts=E['parts'], ensight_variable=E['var_desc'],
               case_solid_cells=len(cells), case_solid_nodes=int(len(nodes)),
               ensight_nodes=int(E['X'].shape[0]), ensight_hexa8=int(E['els'].get('hexa8', np.zeros((0, 8))).shape[0]),
               ensight_other_element_types=[k for k in E['els'] if k != 'hexa8'])
    # 1) node correspondence by coordinates (EnSight float32 vs case float64)
    tree = cKDTree(X[nodes - 1])
    d, i = tree.query(E['X'])
    ens2case = nodes[i]
    rep['node_match_max_dist_m'] = float(d.max())
    rep['node_match_one_to_one'] = bool(len(np.unique(i)) == len(nodes) == E['X'].shape[0])
    # 2) connectivity equivalence (as node sets per element)
    ehex = ens2case[E['els']['hexa8'] - 1]
    sa = set(tuple(sorted(r)) for r in conn.tolist())
    sb = set(tuple(sorted(r)) for r in ehex.tolist())
    rep['connectivity_identical_as_sets'] = bool(sa == sb)
    rep['connectivity_symmetric_difference'] = len(sa ^ sb)
    # 3) node temperatures keyed by case node id
    T = np.full(int(nodes.max()) + 1, np.nan)
    T[ens2case] = E['T']
    Tn = T[nodes]
    rep['node_T_min_K'] = float(Tn.min()); rep['node_T_max_K'] = float(Tn.max()); rep['node_T_nan'] = int(np.isnan(Tn).sum())
    # 4) float32 EnSight node values vs double-precision ASCII node export on the solid boundary nodes
    with open(asc) as fh:
        h = [c.strip() for c in fh.readline().split(',')]
        a = np.loadtxt(fh, delimiter=',')
    A = {c: a[:, k] for k, c in enumerate(h)}
    da, ia = tree.query(np.c_[A['x-coordinate'], A['y-coordinate'], A['z-coordinate']])
    diff = T[nodes[ia]] - A['temperature']
    rep['ascii_boundary_nodes'] = int(len(da)); rep['ascii_match_max_dist_m'] = float(da.max())
    rep['ensight_vs_ascii_node_T_max_abs_K'] = float(np.abs(diff).max())
    # outputs
    csv = os.path.join(out, 'fluent_solid_node_temperature.csv')
    with open(csv, 'w', newline='\n') as fh:
        fh.write('node_id,T_K\n')
        for n, t in zip(nodes, Tn):
            fh.write('%d,%.9g\n' % (n, t))
    rep['node_temperature_csv'] = csv; rep['node_temperature_csv_sha256'] = fm.sha(csv)
    # MAPDL input -> CDB (reuse the writer)
    fm.main(case, out, save_npy=False)
    rep['mapdl_input'] = os.path.join(out, 'build_fluent_solid_cdb.inp')
    rep['mapdl_input_sha256'] = fm.sha(rep['mapdl_input'])
    ok = (rep['node_match_one_to_one'] and rep['node_match_max_dist_m'] < 1e-7 and rep['connectivity_identical_as_sets']
          and rep['node_T_nan'] == 0 and rep['ensight_vs_ascii_node_T_max_abs_K'] < 1e-3)
    rep['ALL_CHECKS_PASS'] = bool(ok)
    json.dump(rep, open(os.path.join(out, 'mesh_based_source_report.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
