# -*- coding: utf-8 -*-
"""Section 7A - independent verification of the Fluent -> Mechanical temperature mapping.

Inputs
  Fluent source (read-only exports of baseline_medium_final, 07_Thermal_Analysis/Temperature_Source):
      fluent_solid_cells.csv, fluent_solid_face_<zone>.csv, fluent_solid_node_<zone>.csv
  Mechanical (written by Mechanical itself, no solve): the solver input file ds.dat containing the structural
      mesh (NBLOCK / EBLOCK) and the mapped nodal temperatures (BFBLOCK TEMP), plus Mechanical's own
      ExportToTextFile of the imported load.
Reference
  The Fluent solid field is axisymmetric to 1.5e-4 K, so an independent reference T_ref(r, z) is built on the
  tensor grid (inner face, 10 cell layers, outer face) x (z = 0, 90 slab centres, z = 0.6) from the Fluent values,
  circumferentially averaged. It is evaluated at every Mechanical node with (a) linear and (b) cubic interpolation.
  The mapping error is T_mapped - T_ref; the linear/cubic spread measures the reference's own uncertainty.
RE-ANALYSIS 2026 - post-processed simulation data; not an ANSYS screenshot.
"""
import os, sys, json, math
import numpy as np
from scipy.interpolate import RegularGridInterpolator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_ds import parse, classify


def rd(p):
    with open(p) as fh:
        h = [c.strip() for c in fh.readline().split(',')]
        a = np.loadtxt(fh, delimiter=',')
    return {c: a[:, i] for i, c in enumerate(h)}


def build_reference(src):
    C = rd(os.path.join(src, 'fluent_solid_cells.csv'))
    O = rd(os.path.join(src, 'fluent_solid_face_heated_outer_wall.csv'))
    I = rd(os.path.join(src, 'fluent_solid_face_fluid_solid_interface-shadow.csv'))
    E0 = rd(os.path.join(src, 'fluent_solid_face_solid_inlet_end.csv'))
    E1 = rd(os.path.join(src, 'fluent_solid_face_solid_outlet_end.csv'))
    rc = np.hypot(C['x-coordinate'], C['y-coordinate'])
    rl = np.unique(np.round(rc, 7))                  # 10 layer centroid radii
    zc = np.unique(np.round(C['z-coordinate'], 7))   # 90 slab centres
    assert len(rl) == 10 and len(zc) == 90, (len(rl), len(zc))
    ri = float(np.mean(np.hypot(I['x-coordinate'], I['y-coordinate'])))
    ro = float(np.mean(np.hypot(O['x-coordinate'], O['y-coordinate'])))
    R = np.concatenate([[ri], rl, [ro]])
    Z = np.concatenate([[0.0], zc, [0.6]])
    G = np.full((len(R), len(Z)), np.nan)
    circ = []
    for j, z in enumerate(zc):
        m = np.abs(C['z-coordinate'] - z) < 1e-6
        for i, r in enumerate(rl):
            mm = m & (np.abs(rc - r) < 1e-6)
            G[i + 1, j + 1] = C['temperature'][mm].mean()
            circ.append(np.ptp(C['temperature'][mm]))
        G[0, j + 1] = I['temperature'][np.abs(I['z-coordinate'] - z) < 1e-6].mean()
        G[-1, j + 1] = O['temperature'][np.abs(O['z-coordinate'] - z) < 1e-6].mean()
    for E, jj in ((E0, 0), (E1, len(Z) - 1)):
        re_ = np.hypot(E['x-coordinate'], E['y-coordinate'])
        for i, r in enumerate(rl):
            G[i + 1, jj] = E['temperature'][np.abs(re_ - r) < 1e-6].mean()
        # corner values: linear extrapolation along the end-face row to the inner / outer face radius
        G[0, jj] = G[1, jj] + (G[2, jj] - G[1, jj]) * (R[0] - R[1]) / (R[2] - R[1])
        G[-1, jj] = G[-2, jj] + (G[-2, jj] - G[-3, jj]) * (R[-1] - R[-2]) / (R[-2] - R[-3])
    assert not np.isnan(G).any()
    info = dict(r_grid_mm=list(np.round(R * 1e3, 5)), n_z=len(Z), circ_ptp_max_K=float(np.max(circ)),
                inner_face_r_mm=ri * 1e3, outer_face_r_mm=ro * 1e3)
    return R, Z, G, info, dict(C=C, O=O, I=I, E0=E0, E1=E1)


def ref_eval(R, Z, G, r, z, method):
    """Evaluate the reference; outside [R0, R-1] extrapolate linearly in r with the end slopes."""
    f = RegularGridInterpolator((R, Z), G, method=method)
    rr = np.clip(r, R[0], R[-1])
    zz = np.clip(z, Z[0], Z[-1])
    t = f(np.c_[rr, zz])
    fo = RegularGridInterpolator((R, Z), G, method='linear')
    hi = r > R[-1]
    if hi.any():
        s = (fo(np.c_[np.full(hi.sum(), R[-1]), zz[hi]]) - fo(np.c_[np.full(hi.sum(), R[-2]), zz[hi]])) / (R[-1] - R[-2])
        t[hi] = t[hi] + s * (r[hi] - R[-1])
    lo = r < R[0]
    if lo.any():
        s = (fo(np.c_[np.full(lo.sum(), R[1]), zz[lo]]) - fo(np.c_[np.full(lo.sum(), R[0]), zz[lo]])) / (R[1] - R[0])
        t[lo] = t[lo] + s * (r[lo] - R[0])
    return t


def analyse(ds_path, src, export_txt=None):
    nodes, elems, bf, comps, tref = parse(ds_path)
    corner, mid = classify(elems)
    ids = np.array(sorted(nodes))
    X = np.array([nodes[i] for i in ids])
    r = np.hypot(X[:, 0], X[:, 1]); z = X[:, 2]
    has = np.array([i in bf for i in ids])
    Tm = np.array([bf.get(i, np.nan) for i in ids]) + 273.15      # ds.dat temperatures are in degC
    R, Z, G, info, D = build_reference(src)
    Tlin = ref_eval(R, Z, G, r, z, 'linear')
    Tcub = ref_eval(R, Z, G, r, z, 'cubic')
    e = Tm - Tlin
    res = dict(ds=os.path.basename(ds_path), nodes=len(ids), elements=len(elems), corner_nodes=len(corner),
               midside_nodes=len(mid), mapped_nodes=int(has.sum()), unmapped_nodes=int((~has).sum()),
               tref_degC=tref, components={k: int(len(v)) for k, v in comps.items()}, reference=info)
    if has.any():
        ae = np.abs(e[has])
        res.update(T_mapped_min=float(np.nanmin(Tm)), T_mapped_max=float(np.nanmax(Tm)),
                   err_max_abs=float(ae.max()), err_mean_abs=float(ae.mean()), err_rms=float(np.sqrt((ae ** 2).mean())),
                   err_mean_signed=float(e[has].mean()), err_p99_abs=float(np.percentile(ae, 99)),
                   ref_lin_vs_cub_max=float(np.max(np.abs(Tlin - Tcub))),
                   err_vs_cubic_max_abs=float(np.max(np.abs(Tm[has] - Tcub[has]))))
        k = int(np.argmax(np.where(has, np.abs(e), -1)))
        res['err_max_location'] = dict(node=int(ids[k]), r_mm=float(r[k] * 1e3), z_mm=float(z[k] * 1e3),
                                       T_mapped=float(Tm[k]), T_ref=float(Tlin[k]))
        for nm, m in (('inner_surface', np.abs(r - 0.010) < 1e-7), ('outer_surface', np.abs(r - 0.020) < 1e-7),
                      ('interior', (r > 0.010 + 1e-7) & (r < 0.020 - 1e-7)),
                      ('end_faces', (z < 1e-9) | (z > 0.6 - 1e-9))):
            mm = m & has
            if mm.any():
                res['err_' + nm] = dict(n=int(mm.sum()), max_abs=float(np.abs(e[mm]).max()),
                                        mean_abs=float(np.abs(e[mm]).mean()), mean_signed=float(e[mm].mean()))
    return res, dict(ids=ids, X=X, r=r, z=z, has=has, Tm=Tm, Tlin=Tlin, Tcub=Tcub, R=R, Z=Z, G=G, D=D,
                     corner=corner, bf=bf, comps=comps)


if __name__ == '__main__':
    ds, src = sys.argv[1], sys.argv[2]
    res, _ = analyse(ds, src)
    print(json.dumps(res, indent=1))
