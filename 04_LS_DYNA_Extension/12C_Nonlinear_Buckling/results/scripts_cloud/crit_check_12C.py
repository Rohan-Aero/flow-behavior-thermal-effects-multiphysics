# Critical-location, mid-span, global-vs-local and temperature checks from d3plot states t = 0.70..0.90 (lambda 1.15..1.30)
# of C1, C3, C5 (geometry file + last d3plot file). Element-centroid stresses (one value per element in d3plot).
import json, numpy as np
from lasso.dyna import D3plot, ArrayType as A
Z0 = {}
for l in open('<PROJECT_ROOT>/15_LS_DYNA_Extension/work_12B/G4_import/model/nodes.k'):
    if l[:1].isdigit(): q = l.split(','); Z0[int(q[0])] = float(q[3])
res = {}; Tref = None
for k, c in (('C1', 'C1_A0p1'), ('C3', 'C3_A0p6'), ('C5', 'C5_A1p2')):
    d = D3plot(f'd3/{k}/d3plot'); X = d.arrays[A.node_coordinates]; t = d.arrays[A.global_timesteps]
    lam = np.interp(t, [0, 0.4, 0.8, 0.9], [0, 1.0, 1.2, 1.3]); ids = d.arrays[A.node_ids]
    zs = np.round(np.array([Z0[n] for n in ids]), 6); st = np.unique(zs); idx = np.searchsorted(st, zs); cnt = np.bincount(idx)
    E = d.arrays[A.element_solid_node_indexes]; Ce = zs[E].mean(1)
    T = d.arrays[A.node_temperature]
    if Tref is None: Tref = T[-1]
    out = {'t': t.tolist(), 'lambda': lam.tolist(), 'T_maxabs_diff_vs_C1_final_K': float(np.abs(T[-1] - Tref).max()),
           'T_node18865_final_K': float(T[-1][np.where(ids == 18865)[0][0]]), 'states': []}
    for j in range(len(t)):
        U = d.arrays[A.node_displacement][j] - X
        ux = np.bincount(idx, U[:, 0]) / cnt; uy = np.bincount(idx, U[:, 1]) / cnt
        lat = np.hypot(ux, uy); res_r = np.hypot(U[:, 0] - ux[idx], U[:, 1] - uy[idx])   # in-plane deviation from rigid section translation
        S = d.arrays[A.element_solid_stress][j, :, 0, :]
        vm = np.sqrt(0.5 * ((S[:, 0] - S[:, 1]) ** 2 + (S[:, 1] - S[:, 2]) ** 2 + (S[:, 2] - S[:, 0]) ** 2) + 3 * (S[:, 3] ** 2 + S[:, 4] ** 2 + S[:, 5] ** 2)) / 1e6
        mid = np.abs(Ce - 0.3) <= 0.005; inl = Ce <= 0.005; outl = Ce >= 0.595
        i = int(np.argmax(vm))
        out['states'].append({'t': float(t[j]), 'lambda': float(lam[j]), 'vm_elem_max_MPa': float(vm[i]), 'vm_elem_max_z_mm': float(Ce[i] * 1e3),
            'vm_inlet_layer_max_MPa': float(vm[inl].max()), 'vm_outlet_layer_max_MPa': float(vm[outl].max()), 'vm_midspan_max_MPa': float(vm[mid].max()),
            'lat_end_mm': float(max(lat[0], lat[-1]) * 1e3), 'lat_mid_mm': float(lat[len(st) // 2] * 1e3),
            'section_distortion_max_mm': float(res_r.max() * 1e3)})
    res[c] = out
    s = out['states'][-1]; print(c, 'T diff %.2e K' % out['T_maxabs_diff_vs_C1_final_K'], {k2: round(v, 3) for k2, v in s.items()})
json.dump(res, open('crit_check_12C.json', 'w'), indent=1)
