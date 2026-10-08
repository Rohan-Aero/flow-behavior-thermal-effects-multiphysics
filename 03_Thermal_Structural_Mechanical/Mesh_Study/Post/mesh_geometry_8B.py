# -*- coding: utf-8 -*-
"""SECTION 8B - independent geometric check of every structural mesh (RE-ANALYSIS 2026).
Reads the NBLOCK / EBLOCK that Mechanical wrote to each variant's solver input (<tag>_LC2_presolve_ds.dat) and checks,
without using Mechanical's own metrics:
  * node and element counts; every element has 20 distinct nodes; no unreferenced or coincident nodes
  * connectivity: every hex face is shared by exactly two elements except the boundary faces, whose number must be
    2*nc*na (bore + outer surface) + 2*nc*nr (two end faces) for a conformal swept annulus
  * inverted / degenerate elements: corner Jacobian determinant (edge triple product) at all 8 corners > 0
  * element dimensions: through-wall, circumferential (bore and outer) and axial sizes; geometric aspect ratio
    (longest / shortest corner edge) - a different definition from Mechanical's normalised 'Aspect Ratio'
Usage: python mesh_geometry_8B.py <out_json> tag=path_to_ds.dat [tag=path ...]"""
import sys, json
import numpy as np

# SOLID186 corner order I J K L (face 1) M N O P (face 2): for each corner, its three edge neighbours (right-handed)
NB = {0: (1, 3, 4), 1: (2, 0, 5), 2: (3, 1, 6), 3: (0, 2, 7), 4: (7, 5, 0), 5: (4, 6, 1), 6: (5, 7, 2), 7: (6, 4, 3)}
FACES = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]


def read(ds):
    L = open(ds, errors="ignore").read().split("\n")
    i = [k for k, l in enumerate(L) if l.lower().startswith("nblock")][0] + 2
    ids, xyz = [], []
    while not L[i].strip().startswith("-1"):
        v = L[i]
        ids.append(int(v[:9])); xyz.append([float(v[9 + 20 * j:29 + 20 * j]) for j in range(3)])
        i += 1
    j = [k for k, l in enumerate(L) if l.lower().startswith("eblock")][0]
    hdr = L[j]
    i = j + 2
    el = []
    while not L[i].strip().startswith("-1"):
        v = L[i]
        f = [int(v[k:k + 9]) for k in range(0, len(v.rstrip()), 9)]
        el.append(f)
        i += 1
    return np.array(ids), np.array(xyz), el, hdr


def check(ds, nc, nr, na):
    ids, X, el, hdr = read(ds)
    pos = {n: k for k, n in enumerate(ids)}
    conn = np.array([[pos[n] for n in e[1:21]] for e in el])        # compact EBLOCK: element id + 20 nodes
    corner = conn[:, :8]
    out = {"eblock_header": hdr.strip(), "nodes": int(len(ids)), "elements": int(len(el))}
    out["elements_with_20_distinct_nodes"] = int(sum(len(set(r)) == 20 for r in conn))
    out["unreferenced_nodes"] = int(len(ids) - len(np.unique(conn)))
    q = np.round(X / 1e-9).astype(np.int64)
    out["coincident_node_pairs"] = int(len(q) - len(np.unique(q, axis=0)))
    # face sharing
    fc = {}
    for e in corner:
        for f in FACES:
            key = tuple(sorted(e[list(f)]))
            fc[key] = fc.get(key, 0) + 1
    cnt = np.array(list(fc.values()))
    out["faces_shared_by_2"] = int((cnt == 2).sum())
    out["boundary_faces"] = int((cnt == 1).sum())
    out["faces_shared_by_more_than_2"] = int((cnt > 2).sum())
    out["boundary_faces_expected"] = 2 * nc * na + 2 * nc * nr
    # corner Jacobians
    P = X[corner]                                                   # (ne, 8, 3)
    dets = np.empty((len(P), 8))
    for c, (a, b, d) in NB.items():
        dets[:, c] = np.einsum("ij,ij->i", np.cross(P[:, a] - P[:, c], P[:, b] - P[:, c]), P[:, d] - P[:, c])
    out["corner_jacobian_min_m3"] = float(dets.min())
    out["elements_with_nonpositive_corner_jacobian"] = int((dets <= 0).any(axis=1).sum())
    # sign convention check: all positive or all negative is a consistent orientation
    out["corner_jacobian_all_same_sign"] = bool((dets > 0).all() or (dets < 0).all())
    elen = np.stack([np.linalg.norm(P[:, a] - P[:, b], axis=1) for a, b in EDGES], axis=1)
    ar = elen.max(axis=1) / elen.min(axis=1)
    out["geometric_aspect_ratio_max"] = float(ar.max())
    out["geometric_aspect_ratio_mean"] = float(ar.mean())
    # dimensions from the corner-node grid
    cn = np.unique(corner)
    r = np.hypot(X[cn, 0], X[cn, 1]); z = X[cn, 2]
    rl = np.unique(np.round(r, 7)); zl = np.unique(np.round(z, 7))
    out["corner_radial_levels_mm"] = [round(v * 1e3, 4) for v in rl]
    out["through_wall_divisions_found"] = int(len(rl) - 1)
    out["axial_divisions_found"] = int(len(zl) - 1)
    dz = np.diff(zl) * 1e3
    out["axial_element_length_mm"] = {"min": float(dz.min()), "max": float(dz.max()), "ratio": float(dz.max() / dz.min()),
                                      "at_inlet_z0": float(dz[0]), "at_outlet_z600": float(dz[-1])}
    out["axial_node_planes_first_30mm"] = [round(v * 1e3, 4) for v in zl if v <= 0.0301]
    ring = cn[(np.abs(r - 0.02) < 1e-7) & (np.abs(z - zl[len(zl) // 2]) < 1e-7)]
    out["circumferential_divisions_found"] = int(len(ring))
    out["circumferential_size_mm"] = {"bore_r10": 2 * np.pi * 10 / len(ring), "outer_r20": 2 * np.pi * 20 / len(ring)}
    out["radial_size_mm"] = float(np.diff(rl).mean() * 1e3)
    out["PASS"] = bool(out["elements_with_20_distinct_nodes"] == out["elements"] and out["unreferenced_nodes"] == 0
                       and out["coincident_node_pairs"] == 0 and out["faces_shared_by_more_than_2"] == 0
                       and out["boundary_faces"] == out["boundary_faces_expected"]
                       and out["elements_with_nonpositive_corner_jacobian"] == 0
                       and out["through_wall_divisions_found"] == nr and out["axial_divisions_found"] == na
                       and out["circumferential_divisions_found"] == nc and out["elements"] == nc * nr * na)
    return out


DIV = {"XC": (21, 3, 76), "C": (27, 4, 98), "B": (36, 5, 130), "FR": (36, 6, 130), "FA": (36, 5, 152), "FC": (42, 5, 130),
       "IL": (36, 5, 130), "B_official": (36, 5, 130)}
if __name__ == "__main__":
    res = {}
    for arg in sys.argv[2:]:
        tag, path = arg.split("=", 1)
        res[tag] = check(path, *DIV[tag])
        print(tag, json.dumps({k: v for k, v in res[tag].items() if k not in ("corner_radial_levels_mm", "axial_node_planes_first_30mm")}))
    json.dump(res, open(sys.argv[1], "w"), indent=1)
