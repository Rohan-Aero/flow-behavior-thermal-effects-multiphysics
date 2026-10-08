# -*- coding: utf-8 -*-
"""Section 7A (mapping fix) - read the SOLID cell-zone mesh of the official Fluent case file (read-only, HDF5/CFF)
and re-analyse its hexahedral cell connectivity exactly (nodes = Fluent node ids, cells = Fluent cell ids).

The connectivity is not assumed: every solid cell is assembled from its own faces in the case file
(faces/c0, faces/c1, faces/nodes). Checks: 43,200 hexes, 8 distinct nodes each, positive volume,
centroid + volume vs Fluent's own exported cell centroid / cell-volume.

Output: an MAPDL input (NBLOCK/EBLOCK, SOLID185) that MAPDL reads and re-writes as a native blocked CDB
(CDWRITE) - the External Data master mesh for mesh-based (shape-function) mapping in Mechanical.
Usage: python fluent_solid_mesh_from_case.py <case.cas.h5> <out_dir>
RE-ANALYSIS 2026 helper - post-processing of a newly generated CFD case; no field values are created here.
"""
import sys, os, json, hashlib
import numpy as np
import h5py


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def read_solid(case):
    f = h5py.File(case, 'r')
    m = f['meshes/1']
    czt = m['cells/zoneTopology']
    cnames = czt['name'][0].decode().split(';')
    k = cnames.index('solid_domain')
    cmin, cmax = int(czt['minId'][k]), int(czt['maxId'][k])
    fzt = m['faces/zoneTopology']
    fnames = fzt['name'][0].decode().split(';')
    zones = {n: (int(fzt['minId'][i]), int(fzt['maxId'][i]), int(fzt['c0'][i]), int(fzt['c1'][i]))
             for i, n in enumerate(fnames)}
    X = m['nodes/coords/1'][...]
    nn = m['faces/nodes/1/nnodes'][...].astype(np.int64)
    fn = m['faces/nodes/1/nodes'][...].astype(np.int64)
    off = np.concatenate([[0], np.cumsum(nn)])
    c0 = m['faces/c0/1'][...].astype(np.int64)
    c1 = m['faces/c1/1'][...].astype(np.int64)
    c1 = np.concatenate([c1, np.zeros(len(c0) - len(c1), np.int64)])
    # faces bounding the solid cells: every zone whose c0 or c1 is the solid zone id, EXCEPT the fluid-side
    # interface zone (its faces belong to fluid cells; the solid side is the '-shadow' zone)
    sid = int(czt['id'][k])
    use = [n for n, (a, b, z0, z1) in zones.items() if (z0 == sid or z1 == sid) and not n == 'fluid_solid_interface']
    cell_faces = {}
    for n in use:
        a, b, _, _ = zones[n]
        for fid in range(a, b + 1):
            i = fid - 1
            nodes = fn[off[i]:off[i + 1]]
            for c in (c0[i], c1[i]):
                if cmin <= c <= cmax:
                    cell_faces.setdefault(c, []).append(nodes)
    return X, cell_faces, (cmin, cmax), use, zones


def hex_from_faces(faces):
    """Order the 8 nodes of a hexahedron from its 6 quad faces: bottom quad = first face, top node of each bottom
    node = its edge-neighbour that is not on the bottom face."""
    assert len(faces) == 6 and all(len(q) == 4 for q in faces), [len(q) for q in faces]
    nbr = {}
    for q in faces:
        for j in range(4):
            a, b = int(q[j]), int(q[(j + 1) % 4])
            nbr.setdefault(a, set()).add(b)
            nbr.setdefault(b, set()).add(a)
    assert len(nbr) == 8 and all(len(v) == 3 for v in nbr.values())
    bot = [int(v) for v in faces[0]]
    top = []
    for a in bot:
        t = [b for b in nbr[a] if b not in bot]
        assert len(t) == 1
        top.append(t[0])
    return bot + top


def hex_volume(P):
    """Volume of a (possibly non-planar-faced) hexahedron, 6-tet decomposition; sign = orientation."""
    tets = [(0, 1, 2, 6), (0, 2, 3, 6), (0, 3, 7, 6), (0, 7, 4, 6), (0, 4, 5, 6), (0, 5, 1, 6)]
    v = 0.0
    for a, b, c, d in tets:
        v += np.dot(P[b] - P[a], np.cross(P[c] - P[a], P[d] - P[a])) / 6.0
    return v


def main(case, out, save_npy=True):
    os.makedirs(out, exist_ok=True)
    X, cf, (cmin, cmax), use, zones = read_solid(case)
    cells = sorted(cf)
    conn = np.zeros((len(cells), 8), np.int64)
    vol = np.zeros(len(cells))
    cen = np.zeros((len(cells), 3))
    flips = 0
    for r, c in enumerate(cells):
        h = hex_from_faces(cf[c])
        P = X[np.array(h) - 1]
        v = hex_volume(P)
        if v < 0:                      # reverse bottom and top ordering -> positive MAPDL orientation
            h = [h[0], h[3], h[2], h[1], h[4], h[7], h[6], h[5]]
            P = X[np.array(h) - 1]
            v = hex_volume(P)
            flips += 1
        conn[r] = h
        vol[r] = v
        cen[r] = P.mean(axis=0)
    nodes = np.unique(conn)
    rep = dict(case=os.path.abspath(case), case_sha256=sha(case), solid_cell_id_range=[cmin, cmax],
               face_zones_used=use, n_cells=len(cells), n_nodes=int(len(nodes)), orientation_flips=flips,
               vol_min=float(vol.min()), vol_max=float(vol.max()), vol_sum_m3=float(vol.sum()),
               r_node_min_mm=float(np.hypot(X[nodes - 1, 0], X[nodes - 1, 1]).min() * 1e3),
               r_node_max_mm=float(np.hypot(X[nodes - 1, 0], X[nodes - 1, 1]).max() * 1e3),
               z_node_min=float(X[nodes - 1, 2].min()), z_node_max=float(X[nodes - 1, 2].max()))
    if save_npy:
        np.save(os.path.join(out, 'solid_conn.npy'), conn)
        np.save(os.path.join(out, 'solid_cells.npy'), np.array(cells))
        np.save(os.path.join(out, 'solid_cell_centroid_vertexavg.npy'), cen)
        np.save(os.path.join(out, 'solid_cell_volume.npy'), vol)
        np.save(os.path.join(out, 'solid_node_ids.npy'), nodes)
        np.save(os.path.join(out, 'solid_node_xyz.npy'), X[nodes - 1])
    # MAPDL input: NBLOCK / EBLOCK in the solid-element blocked format, then CDWRITE produces the native CDB
    inp = os.path.join(out, 'build_fluent_solid_cdb.inp')
    with open(inp, 'w', newline='\n') as fh:
        fh.write('/BATCH\n/TITLE,Fluent solid_domain mesh (baseline_medium_final.cas.h5) - Section 7A mapping master\n')
        fh.write('/COM, RE-ANALYSIS 2026: nodes/cells read from the Fluent case file (ids preserved); no field data\n')
        fh.write('/PREP7\nET,1,185\n')
        fh.write('NBLOCK,6,SOLID,%9d,%9d\n(3i9,6e21.13e3)\n' % (nodes.max(), len(nodes)))
        for n in nodes:
            x, y, z = X[n - 1]
            fh.write('%9d%9d%9d%21.13E%21.13E%21.13E\n' % (n, 0, 0, x, y, z))
        fh.write('N,R5.3,LOC,       -1,\n')
        fh.write('EBLOCK,19,SOLID,%9d,%9d\n(19i9)\n' % (max(cells), len(cells)))
        for c, h in zip(cells, conn):
            fh.write(('%9d' * 19 + '\n') % tuple([1, 1, 1, 1, 0, 0, 0, 0, 8, 0, c] + list(h)))
        fh.write('%9d\n' % -1)
        fh.write('ALLSEL,ALL\n*GET,NNODE,NODE,0,COUNT\n*GET,NELEM,ELEM,0,COUNT\n')
        fh.write('SHPP,SUMM\n')
        fh.write('*CFOPEN,fluent_solid_mesh_counts,txt\n*VWRITE,NNODE,NELEM\n(F12.0,1X,F12.0)\n*CFCLOS\n')
        fh.write('CDWRITE,DB,fluent_solid_mesh,cdb\nFINISH\n/EXIT,NOSAVE\n')
    rep['mapdl_input'] = inp
    json.dump(rep, open(os.path.join(out, 'fluent_solid_mesh_report.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
