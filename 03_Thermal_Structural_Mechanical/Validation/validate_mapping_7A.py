# -*- coding: utf-8 -*-
"""Section 7A - verification of the Fluent -> Mechanical temperature transfer (production model).

Inputs (all written by ANSYS; nothing here is created by hand):
  Mechanical solver input files (no solve):  08_Structural_Analysis/Mechanical_Setup/Input_Files/LC{1,2}_*_ds.dat
      NBLOCK/EBLOCK = structural mesh, BFBLOCK TEMP = mapped nodal temperatures [degC], TREF, components
  Fluent (read-only exports of baseline_medium_final, 07_Thermal_Analysis/Temperature_Source):
      fluent_solid_cells.csv (43,200 cell values), fluent_solid_face_*.csv (boundary face values),
      EnSight/solid_domain_T.* (Fluent node values) -> Mapping/MeshBased/fluent_solid_node_temperature.csv,
      the case file (solid mesh, for the exact shape-function re-evaluation)
Checks:
  (A) mapping implementation: mapped T vs the Fluent node field evaluated with the source hexahedra's own
      trilinear shape functions at every Mechanical node (what a mesh-based mapping must return)
  (B) transfer vs the Fluent finite-volume solution: mapped T vs an independent reference built from the
      cell-centre and boundary-face values (tensor grid in r, z; linear and cubic) - includes the
      node-reconstruction difference of the source field itself
  (C) engineering quantities: min/max, mid-span inner/outer wall, through-wall dT, volume mean, axial profiles
Outputs: Validation/*.json, *.csv, *.md tables; Figures/F7A_0*.png (post-processed data, not ANSYS screenshots)
RE-ANALYSIS 2026.
"""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from parse_ds import parse, classify
from mapping_validation import build_reference, ref_eval, rd
from source_mesh_interp import HexField
sys.path.insert(0, os.path.join(HERE, '..', 'Mapping', 'Scripts'))
sys.path.insert(0, os.path.join(HERE, '..', 'MeshBased'))
import fluent_solid_mesh_from_case as fm

# ---------------- SOLID186 20-node serendipity (ANSYS node order I..P, Q..T, U..X, Y..B) ----------------
C8 = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)
MID = np.array([[0, -1, -1], [1, 0, -1], [0, 1, -1], [-1, 0, -1], [0, -1, 1], [1, 0, 1], [0, 1, 1], [-1, 0, 1],
                [-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]], float)
NAT = np.vstack([C8, MID])


def shape20(x):
    """x (q,3) -> N (q,20), dN (q,20,3)"""
    q = len(x); N = np.zeros((q, 20)); dN = np.zeros((q, 20, 3))
    for a, (xi, et, ze) in enumerate(NAT):
        X, Y, Z = x[:, 0], x[:, 1], x[:, 2]
        if a < 8:
            f = (1 + xi * X) * (1 + et * Y) * (1 + ze * Z) / 8.0
            g = xi * X + et * Y + ze * Z - 2
            N[:, a] = f * g
            dN[:, a, 0] = xi * (1 + et * Y) * (1 + ze * Z) / 8.0 * g + f * xi
            dN[:, a, 1] = et * (1 + xi * X) * (1 + ze * Z) / 8.0 * g + f * et
            dN[:, a, 2] = ze * (1 + xi * X) * (1 + et * Y) / 8.0 * g + f * ze
        else:
            c = [xi, et, ze]
            k = [i for i in range(3) if c[i] == 0][0]
            o = [i for i in range(3) if i != k]
            v = [X, Y, Z]
            a1 = (1 + c[o[0]] * v[o[0]]); a2 = (1 + c[o[1]] * v[o[1]]); b = (1 - v[k] ** 2)
            N[:, a] = b * a1 * a2 / 4.0
            dN[:, a, k] = -2 * v[k] * a1 * a2 / 4.0
            dN[:, a, o[0]] = b * c[o[0]] * a2 / 4.0
            dN[:, a, o[1]] = b * a1 * c[o[1]] / 4.0
    return N, dN


def integrate(elems, node_xyz, node_T):
    g = np.array([-np.sqrt(0.6), 0.0, np.sqrt(0.6)]); w = np.array([5, 8, 5]) / 9.0
    P = np.array([[a, b, c] for a in g for b in g for c in g]); Wq = np.array([a * b * c for a in w for b in w for c in w])
    N, dN = shape20(P)
    conn = np.array([e[1:21] for e in elems])
    X = node_xyz[conn]                                   # (ne,20,3)
    J = np.einsum('qak,eaj->eqjk', dN, X)                # (ne,q,3,3)
    detJ = np.linalg.det(J)
    Tq = np.einsum('qa,ea->eq', N, node_T[conn])
    V = (detJ * Wq).sum(axis=1)
    return float(V.sum()), float((detJ * Wq * Tq).sum() / V.sum()), float(detJ.min())


def main(root, out_val, out_fig):
    os.makedirs(out_val, exist_ok=True); os.makedirs(out_fig, exist_ok=True)
    src = os.path.join(root, '07_Thermal_Analysis', 'Temperature_Source')
    inpdir = os.path.join(root, '08_Structural_Analysis', 'Mechanical_Setup', 'Input_Files')
    case = os.path.join(root, '06_Fluent_CFD', 'Case', 'baseline_medium_final.cas.h5')
    ncsv = os.path.join(root, '07_Thermal_Analysis', 'Mapping', 'MeshBased', 'fluent_solid_node_temperature.csv')
    # Fluent source mesh + node field
    X, cf, _, _, _ = fm.read_solid(case)
    cells = sorted(cf); conn = np.array([fm.hex_from_faces(cf[c]) for c in cells])
    Xid = np.vstack([np.zeros(3), X])
    d = np.loadtxt(ncsv, delimiter=',', skiprows=1)
    Tid = np.full(len(Xid), np.nan); Tid[d[:, 0].astype(int)] = d[:, 1]
    H = HexField(Xid, conn, Tid)
    R, Z, G, rinfo, D = build_reference(src)
    C = D['C']
    fl_T = np.concatenate([C['temperature'], D['O']['temperature'], D['I']['temperature'], D['E0']['temperature'], D['E1']['temperature']])
    fluent = dict(cell_min=float(C['temperature'].min()), cell_max=float(C['temperature'].max()),
                  face_min=float(fl_T.min()), face_max=float(fl_T.max()),
                  node_min=float(np.nanmin(Tid)), node_max=float(np.nanmax(Tid)),
                  vol_mean=float((C['temperature'] * C['cell-volume']).sum() / C['cell-volume'].sum()),
                  volume_m3=float(C['cell-volume'].sum()))
    results = {"fluent_source": fluent, "reference": rinfo}
    lcs = {}
    for tag in ("LC1_Free_Expansion", "LC2_Axially_Restrained"):
        ds = os.path.join(inpdir, tag + '_ds.dat')
        nodes, elems, bf, comps, tref = parse(ds)
        ids = np.array(sorted(nodes)); XX = np.array([nodes[i] for i in ids])
        nmax = ids.max(); xyz = np.zeros((nmax + 1, 3)); xyz[ids] = XX
        Tm_id = np.full(nmax + 1, np.nan)
        for k, v in bf.items():
            Tm_id[k] = v + 273.15
        Tm = Tm_id[ids]; has = ~np.isnan(Tm)
        r = np.hypot(XX[:, 0], XX[:, 1]); z = XX[:, 2]
        Th, dev = H.evaluate(XX)
        eA = Tm - Th
        Tlin = ref_eval(R, Z, G, r, z, 'linear'); Tcub = ref_eval(R, Z, G, r, z, 'cubic')
        eB = Tm - Tlin
        Vs, Tmean, detmin = integrate(elems, xyz, np.nan_to_num(Tm_id))
        corner, mid = classify(elems)
        res = dict(ds=ds, nodes=int(len(ids)), elements=int(len(elems)), corner_nodes=len(corner), midside_nodes=len(mid),
                   tref_degC=tref, mapped=int(has.sum()), unmapped=int((~has).sum()),
                   components={k: int(len(v)) for k, v in comps.items()},
                   T_min=float(np.nanmin(Tm)), T_max=float(np.nanmax(Tm)),
                   nodes_outside_source_mesh=int((dev > 1e-9).sum()), outside_max_local_coord_excess=float(dev.max()),
                   A_vs_shape_function_eval=dict(max=float(np.nanmax(np.abs(eA))), mean=float(np.nanmean(np.abs(eA))),
                                                 max_inside=float(np.nanmax(np.abs(eA[dev <= 1e-9]))),
                                                 max_outside=float(np.nanmax(np.abs(eA[dev > 1e-9]))) if (dev > 1e-9).any() else 0.0),
                   B_vs_FV_reference=dict(max=float(np.nanmax(np.abs(eB))), mean=float(np.nanmean(np.abs(eB))),
                                          rms=float(np.sqrt(np.nanmean(eB ** 2))), p99=float(np.nanpercentile(np.abs(eB), 99)),
                                          mean_signed=float(np.nanmean(eB)),
                                          ref_lin_cub_spread_max=float(np.max(np.abs(Tlin - Tcub)))),
                   volume_m3=Vs, vol_mean_T=Tmean, min_detJ=detmin)
        zb = {}
        for lo, hi in ((0, 7), (7, 14), (14, 30), (30, 100), (100, 300), (300, 500), (500, 586), (586, 593.4), (593.4, 600.1)):
            m = (z * 1e3 >= lo) & (z * 1e3 < hi)
            zb["%g-%g mm" % (lo, hi)] = dict(n=int(m.sum()), maxB=float(np.nanmax(np.abs(eB[m]))), meanB=float(np.nanmean(np.abs(eB[m]))),
                                            maxA=float(np.nanmax(np.abs(eA[m]))))
        res['error_by_axial_band'] = zb
        for th in (0.1, 0.25, 0.5, 1.0, 2.0):
            m = np.abs(eB) > th
            res['B_nodes_above_%gK' % th] = dict(n=int(m.sum()), z_max_mm=float(z[m].max() * 1e3) if m.any() else None,
                                                 z_min_mm=float(z[m].min() * 1e3) if m.any() else None)
        # engineering quantities at mid-span z = 300 mm (node plane in both meshes)
        def ring(mask_r, zz):
            m = mask_r & (np.abs(z - zz) < 1e-7)
            return float(np.nanmean(Tm[m])), int(m.sum())
        inner = np.abs(r - 0.010) < 1e-7; outer = np.abs(r - 0.020) < 1e-7
        res['midspan'] = dict(T_inner=ring(inner, 0.3), T_outer=ring(outer, 0.3))
        res['ends'] = dict(inlet_inner=ring(inner, 0.0), inlet_outer=ring(outer, 0.0),
                           outlet_inner=ring(inner, 0.6), outlet_outer=ring(outer, 0.6))
        lcs[tag] = res
        results[tag] = res
        if tag.startswith('LC1'):
            keep = dict(XX=XX, r=r, z=z, Tm=Tm, Th=Th, Tlin=Tlin, eA=eA, eB=eB, dev=dev)
    # Fluent engineering quantities on the same basis
    nid = np.where(~np.isnan(Tid))[0]; nr = np.hypot(Xid[nid, 0], Xid[nid, 1]); nz = Xid[nid, 2]
    def fring(rr, zz):
        m = (np.abs(nr - rr) < 1e-7) & (np.abs(nz - zz) < 1e-7)
        return float(Tid[nid][m].mean()), int(m.sum())
    # face-value (finite-volume) wall temperatures interpolated to z = 300 mm from the two adjacent slab centres
    def fface(Fd, zz):
        zc = np.unique(np.round(Fd['z-coordinate'], 7)); tz = np.array([Fd['temperature'][np.abs(Fd['z-coordinate'] - q) < 1e-6].mean() for q in zc])
        return float(np.interp(zz, zc, tz))
    fluent['midspan_node'] = dict(T_inner=fring(0.010, 0.3), T_outer=fring(0.020, 0.3))
    fluent['midspan_face'] = dict(T_inner=fface(D['I'], 0.3), T_outer=fface(D['O'], 0.3))
    fluent['ends_node'] = dict(inlet_inner=fring(0.010, 0.0), inlet_outer=fring(0.020, 0.0),
                               outlet_inner=fring(0.010, 0.6), outlet_outer=fring(0.020, 0.6))
    # ---------------- comparison table ----------------
    L1 = lcs['LC1_Free_Expansion']
    rows = [
        ("Solid T minimum [K]", "%.3f (node) / %.3f (face)" % (fluent['node_min'], fluent['face_min']), L1['T_min'], fluent['node_min']),
        ("Solid T maximum [K]", "%.3f (node) / %.3f (cell)" % (fluent['node_max'], fluent['cell_max']), L1['T_max'], fluent['node_max']),
        ("Mid-span inner wall T, z = 300 mm [K]", "%.3f (node) / %.3f (face)" % (fluent['midspan_node']['T_inner'][0], fluent['midspan_face']['T_inner']),
         L1['midspan']['T_inner'][0], fluent['midspan_node']['T_inner'][0]),
        ("Mid-span outer wall T, z = 300 mm [K]", "%.3f (node) / %.3f (face)" % (fluent['midspan_node']['T_outer'][0], fluent['midspan_face']['T_outer']),
         L1['midspan']['T_outer'][0], fluent['midspan_node']['T_outer'][0]),
        ("Mid-span through-wall dT (outer - inner) [K]", "%.3f (node) / %.3f (face)" % (
            fluent['midspan_node']['T_outer'][0] - fluent['midspan_node']['T_inner'][0], fluent['midspan_face']['T_outer'] - fluent['midspan_face']['T_inner']),
         L1['midspan']['T_outer'][0] - L1['midspan']['T_inner'][0],
         fluent['midspan_node']['T_outer'][0] - fluent['midspan_node']['T_inner'][0]),
        ("Inlet end, inner edge T [K]", "%.3f (node)" % fluent['ends_node']['inlet_inner'][0], L1['ends']['inlet_inner'][0], fluent['ends_node']['inlet_inner'][0]),
        ("Outlet end, outer edge T [K]", "%.3f (node)" % fluent['ends_node']['outlet_outer'][0], L1['ends']['outlet_outer'][0], fluent['ends_node']['outlet_outer'][0]),
        ("Volume-mean solid T [K]", "%.3f (cell-volume weighted)" % fluent['vol_mean'], L1['vol_mean_T'], fluent['vol_mean']),
        ("Solid volume [m3]", "%.6e (48-gon)" % fluent['volume_m3'], L1['volume_m3'], fluent['volume_m3']),
    ]
    tab = ["| Quantity | Fluent Source | Mechanical Mapped | Difference (mapped - Fluent node basis) |", "|---|---|---|---|"]
    for q, s, m, ref in rows:
        tab.append("| %s | %s | %.6g | %+.4g |" % (q, s, m, m - ref))
    results['comparison_table_md'] = "\n".join(tab)
    json.dump(results, open(os.path.join(out_val, 'mapping_validation_7A.json'), 'w'), indent=1, default=float)
    open(os.path.join(out_val, 'MAPPING_ERROR_TABLE.md'), 'w').write(
        "# Section 7A - mapping error table (generated by validate_mapping_7A.py)\n\n"
        "RE-ANALYSIS 2026 - post-processed simulation data.\n\n" + results['comparison_table_md'] + "\n")
    # axial profiles csv
    k = keep
    zr7 = np.round(k['z'], 7); zz = np.unique(zr7)
    with open(os.path.join(out_val, 'axial_profiles_mapped_vs_fluent.csv'), 'w') as fh:
        fh.write('z_m,T_inner_mapped_K,T_outer_mapped_K,T_inner_fluent_node_field_K,T_outer_fluent_node_field_K,T_inner_FVref_K,T_outer_FVref_K\n')
        for q in zz:
            mi = (np.abs(k['r'] - 0.010) < 1e-7) & (zr7 == q)
            mo = (np.abs(k['r'] - 0.020) < 1e-7) & (zr7 == q)
            if mi.any() and mo.any():
                fh.write('%.6f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f\n' % (q, k['Tm'][mi].mean(), k['Tm'][mo].mean(), k['Th'][mi].mean(),
                                                                   k['Th'][mo].mean(), k['Tlin'][mi].mean(), k['Tlin'][mo].mean()))
    make_figures(out_fig, k, C, D, Tid, Xid, nid, R, Z, G, L1, fluent)
    print(json.dumps({t: {kk: lcs[t][kk] for kk in ('nodes', 'elements', 'mapped', 'unmapped', 'T_min', 'T_max', 'A_vs_shape_function_eval',
                                                    'B_vs_FV_reference', 'vol_mean_T', 'volume_m3', 'nodes_outside_source_mesh')}
                      for t in lcs}, indent=1, default=float))
    print(results['comparison_table_md'])
    return results


def make_figures(out, k, C, D, Tid, Xid, nid, R, Z, G, L1, fluent):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import tri
    note = 'RE-ANALYSIS 2026 - post-processed simulation data (Python), not an ANSYS screenshot'
    # --- r-z section fields (theta-averaged) ---
    rc = np.hypot(C['x-coordinate'], C['y-coordinate']); zc = C['z-coordinate']
    rl = np.unique(np.round(rc, 7)); zl = np.unique(np.round(zc, 7))
    Fcell = np.array([[C['temperature'][(np.abs(rc - a) < 1e-6) & (np.abs(zc - b) < 1e-6)].mean() for b in zl] for a in rl])
    r = k['r']; z = k['z']
    key = np.round(r * 1e7).astype(np.int64) * 10 ** 7 + np.round(z * 1e7).astype(np.int64)
    uk, inv = np.unique(key, return_inverse=True)
    Tm_rz = np.bincount(inv, k['Tm']) / np.bincount(inv); eB_rz = np.bincount(inv, k['eB']) / np.bincount(inv)
    eA_rz = np.bincount(inv, np.abs(k['eA'])) / np.bincount(inv)
    r_rz = np.bincount(inv, r) / np.bincount(inv); z_rz = np.bincount(inv, z) / np.bincount(inv)
    vmin, vmax = 420, 565
    # structured (z, r) grid for display: element-boundary z-planes carry all 11 radii (corner + radial mid-side nodes)
    rr7 = np.round(r_rz, 7); zz7 = np.round(z_rz, 7)
    rr_u = np.unique(rr7); zz_u = np.unique(zz7)
    full = [q for q in zz_u if len(np.unique(rr7[zz7 == q])) == len(rr_u)]
    Zg = np.array(full); Rg = rr_u
    Tg = np.full((len(Rg), len(Zg)), np.nan); Eg = np.full_like(Tg, np.nan)
    for jz, q in enumerate(Zg):
        m = zz7 == q
        for ir, a in enumerate(Rg):
            mm = m & (rr7 == a)
            Tg[ir, jz] = Tm_rz[mm].mean(); Eg[ir, jz] = eB_rz[mm].mean()
    # F1 Fluent solid T
    fig, ax = plt.subplots(figsize=(11, 3.4))
    re = np.concatenate([[0.010], (rl[:-1] + rl[1:]) / 2, [0.020]])
    ze = np.concatenate([[0.0], (zl[:-1] + zl[1:]) / 2, [0.6]])
    pc = ax.pcolormesh(ze * 1e3, re * 1e3, Fcell, cmap='inferno', vmin=vmin, vmax=vmax, shading='flat')
    fig.colorbar(pc, ax=ax, label='T [K]')
    ax.set_xlabel('z [mm] (flow direction)'); ax.set_ylabel('r [mm]')
    ax.set_title('F7A-01  Fluent solid temperature, baseline_medium_final (cell values, circumferential mean)\n'
                 'T %.2f - %.2f K (cells); 10 graded layers x 90 slabs' % (C['temperature'].min(), C['temperature'].max()), fontsize=9)
    fig.text(0.01, 0.01, note, fontsize=6, color='gray'); fig.tight_layout(); fig.savefig(os.path.join(out, 'F7A_01_fluent_solid_T_rz.png'), dpi=160); plt.close(fig)
    # F2 Mechanical imported field
    fig, ax = plt.subplots(figsize=(11, 3.4))
    cf_ = ax.pcolormesh(Zg * 1e3, Rg * 1e3, Tg, shading='gouraud', cmap='inferno', vmin=vmin, vmax=vmax)
    fig.colorbar(cf_, ax=ax, label='T [K]')
    ax.set_xlabel('z [mm]'); ax.set_ylabel('r [mm]')
    ax.set_title('F7A-02  Mechanical imported body temperature (mapped nodal values from the solver input file, circumferential mean)\n'
                 'M36 mesh: %d nodes, SOLID186; T %.2f - %.2f K' % (L1['nodes'], L1['T_min'], L1['T_max']), fontsize=9)
    fig.text(0.01, 0.01, note, fontsize=6, color='gray'); fig.tight_layout(); fig.savefig(os.path.join(out, 'F7A_02_mechanical_imported_T_rz.png'), dpi=160); plt.close(fig)
    # F3 side-by-side + difference
    fig, axs = plt.subplots(3, 1, figsize=(11, 8.2), sharex=True)
    pc = axs[0].pcolormesh(ze * 1e3, re * 1e3, Fcell, cmap='inferno', vmin=vmin, vmax=vmax, shading='flat'); fig.colorbar(pc, ax=axs[0], label='T [K]')
    axs[0].set_title('Fluent (cell values, one colour per cell)', fontsize=9)
    cf_ = axs[1].pcolormesh(Zg * 1e3, Rg * 1e3, Tg, shading='gouraud', cmap='inferno', vmin=vmin, vmax=vmax); fig.colorbar(cf_, ax=axs[1], label='T [K]')
    axs[1].set_title('Mechanical (mapped nodal values on element-boundary planes, gouraud-shaded)', fontsize=9)
    lim = max(0.5, float(np.percentile(np.abs(eB_rz), 99.5)))
    cf2 = axs[2].pcolormesh(Zg * 1e3, Rg * 1e3, Eg, shading='gouraud', cmap='coolwarm', vmin=-lim, vmax=lim); fig.colorbar(cf2, ax=axs[2], label='mapped - FV reference [K]', extend='both')
    axs[2].set_title('Difference vs independent finite-volume reference (cell + face values); max |diff| %.2f K (inlet corner), mean %.3f K'
                     % (L1['B_vs_FV_reference']['max'], L1['B_vs_FV_reference']['mean']), fontsize=9)
    for a in axs:
        a.set_ylabel('r [mm]')
    axs[2].set_xlabel('z [mm]')
    fig.suptitle('F7A-03  Fluent source vs Mechanical imported temperature (circumferential means)', fontsize=10)
    fig.text(0.01, 0.005, note, fontsize=6, color='gray'); fig.tight_layout(); fig.savefig(os.path.join(out, 'F7A_03_side_by_side_and_difference.png'), dpi=160); plt.close(fig)
    # F4 axial variation
    Ii = D['I']; Oo = D['O']
    zi = np.unique(np.round(Ii['z-coordinate'], 7)); Ti = np.array([Ii['temperature'][np.abs(Ii['z-coordinate'] - q) < 1e-6].mean() for q in zi])
    zo = np.unique(np.round(Oo['z-coordinate'], 7)); To = np.array([Oo['temperature'][np.abs(Oo['z-coordinate'] - q) < 1e-6].mean() for q in zo])
    mi = np.abs(r_rz - 0.010) < 1e-7; mo = np.abs(r_rz - 0.020) < 1e-7
    oi = np.argsort(z_rz[mi]); oo = np.argsort(z_rz[mo])
    fig, axs = plt.subplots(2, 1, figsize=(10, 7), sharex=True, gridspec_kw={'height_ratios': [3, 1.3]})
    axs[0].plot(zi * 1e3, Ti, 'o', ms=3, color='tab:blue', label='Fluent inner wall (face values)')
    axs[0].plot(zo * 1e3, To, 'o', ms=3, color='tab:red', label='Fluent outer wall (face values)')
    axs[0].plot(z_rz[mi][oi] * 1e3, Tm_rz[mi][oi], '-', color='navy', lw=1.2, label='Mechanical mapped, inner surface nodes')
    axs[0].plot(z_rz[mo][oo] * 1e3, Tm_rz[mo][oo], '-', color='darkred', lw=1.2, label='Mechanical mapped, outer surface nodes')
    axs[0].set_ylabel('T [K]'); axs[0].legend(fontsize=8); axs[0].grid(alpha=0.3)
    axs[0].set_title('F7A-04  Axial wall-temperature variation: Fluent source vs Mechanical imported field', fontsize=10)
    axs[1].plot(zo * 1e3, To - np.interp(zo, zi, Ti), 'o', ms=3, color='k', label='Fluent through-wall dT (face values)')
    axs[1].plot(z_rz[mo][oo] * 1e3, Tm_rz[mo][oo] - np.interp(z_rz[mo][oo], z_rz[mi][oi], Tm_rz[mi][oi]), '-', color='tab:green', label='Mechanical mapped dT')
    axs[1].set_xlabel('z [mm]'); axs[1].set_ylabel('T_out - T_in [K]'); axs[1].legend(fontsize=8); axs[1].grid(alpha=0.3)
    fig.text(0.01, 0.005, note, fontsize=6, color='gray'); fig.tight_layout(); fig.savefig(os.path.join(out, 'F7A_04_axial_wall_temperature.png'), dpi=160); plt.close(fig)
    # F5 through-wall at mid-span
    fig, ax = plt.subplots(figsize=(7.5, 5))
    j = np.argmin(np.abs(zl - 0.3)); j2 = j + 1 if zl[j] < 0.3 else j - 1
    for jj, mk in ((j, 's'), (j2, 'D')):
        ax.plot(rl * 1e3, Fcell[:, jj], mk, color='tab:orange', ms=5, label='Fluent cell values, z = %.2f mm' % (zl[jj] * 1e3))
    fi = fluent['midspan_face']['T_inner']; fo = fluent['midspan_face']['T_outer']
    ax.plot([10, 20], [fi, fo], '^', color='tab:purple', ms=7, label='Fluent wall face values interpolated to z = 300 mm')
    nr = np.hypot(Xid[nid, 0], Xid[nid, 1]); nz = Xid[nid, 2]; mnode = np.abs(nz - 0.3) < 1e-7
    ru = np.unique(np.round(nr[mnode], 7)); tu = [Tid[nid][mnode][np.abs(nr[mnode] - q) < 1e-6].mean() for q in ru]
    ax.plot(ru * 1e3, tu, 'o', mfc='none', color='k', ms=7, label='Fluent node values, z = 300 mm')
    m = np.abs(z_rz - 0.3) < 1e-7; o = np.argsort(r_rz[m])
    ax.plot(r_rz[m][o] * 1e3, Tm_rz[m][o], '-x', color='tab:green', label='Mechanical mapped nodes, z = 300 mm')
    ax.set_xlabel('r [mm]'); ax.set_ylabel('T [K]'); ax.grid(alpha=0.3); ax.legend(fontsize=7)
    ax.set_title('F7A-05  Through-wall temperature at mid-span (z = 300 mm)\nmapped dT = %.3f K; Fluent node dT = %.3f K'
                 % (L1['midspan']['T_outer'][0] - L1['midspan']['T_inner'][0],
                    fluent['midspan_node']['T_outer'][0] - fluent['midspan_node']['T_inner'][0]), fontsize=9)
    fig.text(0.01, 0.005, note, fontsize=6, color='gray'); fig.tight_layout(); fig.savefig(os.path.join(out, 'F7A_05_through_wall_midspan.png'), dpi=160); plt.close(fig)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
