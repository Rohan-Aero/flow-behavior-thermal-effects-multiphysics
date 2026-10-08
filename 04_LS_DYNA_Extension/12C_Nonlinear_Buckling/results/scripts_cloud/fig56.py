# F5 deformed shape and F6 von Mises field of C5_A1p2 (A = 1.2 mm) at the maximum attained load (end state, t = 0.9, lambda = 1.3).
# Source: C5 d3plot (geometry file) + d3plot02 (states t = 0.70..0.90), read with lasso. Displacement = state coords - geometry.
import json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from lasso.dyna import D3plot, ArrayType as A
exec(open('plots_12C.py').read().split('avail =')[0].split("A = json.load")[0])   # palette, OUT
COL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']; INK = '#0b0b0b'; INK2 = '#52514e'; SURF = '#fcfcfb'
def style(a):
    a.set_facecolor(SURF); a.grid(color='#e4e3df', lw=0.6)
    for sp in ('top', 'right'): a.spines[sp].set_visible(False)
d = D3plot('d3/C5/d3plot'); X = d.arrays[A.node_coordinates]; t = d.arrays[A.global_timesteps]
U = d.arrays[A.node_displacement] - X[None]; T = d.arrays[A.node_temperature]
lam = np.interp(t, [0, 0.4, 0.8, 0.9], [0, 1.0, 1.2, 1.3])
Z0 = {}
for l in open('<PROJECT_ROOT>/15_LS_DYNA_Extension/work_12B/G4_import/model/nodes.k'):
    if l[:1].isdigit(): q = l.split(','); Z0[int(q[0])] = float(q[3])
z = X[:, 2]; zs = np.round(np.array([Z0[n] for n in d.arrays[A.node_ids]]), 6); st = np.unique(zs)   # stations from the perfect 12B mesh
k = -1  # final state
# section-mean lateral translation per axial station (rigid-section sway)
idx = np.searchsorted(st, zs)
xc = np.bincount(idx, X[:, 0]) / np.bincount(idx); yc = np.bincount(idx, X[:, 1]) / np.bincount(idx)
rl = np.hypot(X[:, 0] - xc[idx], X[:, 1] - yc[idx])
def sect(Ui):
    ux = np.bincount(idx, Ui[:, 0]) / np.bincount(idx); uy = np.bincount(idx, Ui[:, 1]) / np.bincount(idx); return ux, uy
ux, uy = sect(U[k]); ang = np.arctan2(uy[-1] - uy[0], ux[-1] - ux[0]); e = np.array([np.cos(ang), np.sin(ang)])
out = {'state_t': float(t[k]), 'lambda': float(lam[k]), 'sway_dir_deg': float(np.degrees(ang))}
# F5
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={'width_ratios': [1.25, 1]})
a = ax[0]; style(a)
for j in range(len(t)):
    uxj, uyj = sect(U[j]); w = (uxj * e[0] + uyj * e[1]) * 1e3; w = w - w.mean()
    a.plot(st * 1e3, w, color=COL[j % 6], lw=1.6)
    if j in (0, 2, len(t) - 1): a.text(st[-1] * 1e3 + 6, w[-1], f'λ = {lam[j]:.2f}', color=COL[j % 6], va='center', fontsize=9)
a.set_xlim(0, 690); a.set_xlabel('Axial position z (mm)  [0 = inlet face]'); a.set_ylabel('Section lateral translation in sway plane (mm)\n(mean over length removed)')
a.set_title('Lateral deflection along the tube, C5 (A = 1.2 mm)', loc='left', fontsize=10, color=INK)
w = ux * e[0] + uy * e[1]; out['sway_end_rel_mm'] = float((w[-1] - w[0]) * 1e3); out['mid_minus_ends_mean_mm'] = float((w[len(st) // 2] - 0.5 * (w[0] + w[-1])) * 1e3)
# outline in sway plane, true scale and x10 lateral scale
a = ax[1]; style(a); thn = np.degrees(np.arctan2(X[:, 1] - yc[idx], X[:, 0] - xc[idx]) - ang); thn = (thn + 180) % 360 - 180
for g in (0, 180):
    m = (rl > 0.0199) & (np.abs(((thn - g) + 180) % 360 - 180) < 2.0); o = np.argsort(z[m]); p = X[m, 0] * e[0] + X[m, 1] * e[1]
    a.plot(p[o] * 1e3, z[m][o] * 1e3, color=INK2, lw=1, ls='--')
    a.plot((p + U[k][m, 0] * e[0] + U[k][m, 1] * e[1])[o] * 1e3, (z[m] + U[k][m, 2])[o] * 1e3, color=COL[1], lw=1.8)
a.set_xlim(-40, 40); a.set_xlabel('Position in sway plane (mm)'); a.set_ylabel('z (mm)')
a.set_title('Outline in sway plane, λ = 1.30\norange deformed, dashed imperfect geometry\n(lateral axis stretched)', loc='left', fontsize=9.5, color=INK)
fig.suptitle('F5  LS-DYNA nonlinear (extension) — deformed shape at the maximum attained load, t = 0.9', x=0.01, ha='left', fontsize=11, color=INK)
fig.tight_layout(); fig.savefig(f'{OUT}/F5_deformed_shape_critical_state.png', dpi=150); plt.close(fig)
# F6: element (centroid) von Mises, global-frame stress
S = d.arrays[A.element_solid_stress][k, :, 0, :]
vm = np.sqrt(0.5 * ((S[:, 0] - S[:, 1]) ** 2 + (S[:, 1] - S[:, 2]) ** 2 + (S[:, 2] - S[:, 0]) ** 2) + 3 * (S[:, 3] ** 2 + S[:, 4] ** 2 + S[:, 5] ** 2)) / 1e6
C = X[d.arrays[A.element_solid_node_indexes]].mean(1); Ce = zs[d.arrays[A.element_solid_node_indexes]].mean(1); cx = np.interp(Ce, st, xc); cy = np.interp(Ce, st, yc)
rc = np.hypot(C[:, 0] - cx, C[:, 1] - cy); th = np.degrees(np.arctan2(C[:, 1] - cy, C[:, 0] - cx) - ang); th = (th + 180) % 360 - 180
outer = rc > rc.max() - 1e-3
i = np.argmax(vm); out.update({'vm_elem_max_MPa': float(vm.max()), 'vm_elem_max_z_mm': float(C[i, 2] * 1e3), 'vm_elem_max_r_mm': float(rc[i] * 1e3), 'vm_elem_max_theta_deg': float(th[i])})
Tn = T[k]; out['T_node18865_K'] = float(Tn[np.where(d.arrays[A.node_ids] == 18865)[0][0]]); out['T_max_K'] = float(Tn.max()); out['T_min_K'] = float(Tn.min())
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={'width_ratios': [1.6, 1]})
a = ax[0]; zz = np.r_[Ce[outer], Ce[outer], Ce[outer]] * 1e3; tt = np.r_[th[outer] - 360, th[outer], th[outer] + 360]; vv = np.tile(vm[outer], 3)
sc = a.tripcolor(zz, tt, vv, shading='gouraud', cmap='viridis')
cb = fig.colorbar(sc, ax=a, pad=0.01); cb.set_label('von Mises, element centroid (MPa)')
a.set_xlabel('z (mm)'); a.set_ylabel('Angle from sway direction (°)'); a.set_xlim(0, 600); a.set_ylim(-180, 180); a.set_yticks([-180, -90, 0, 90, 180])
a.set_title('Outer element layer, unrolled', loc='left', fontsize=10, color=INK)
a = ax[1]; style(a)
for lo, hi, cl, lab in ((-15, 15, COL[1], 'θ ≈ 0°'), (165, 195, COL[0], 'θ ≈ 180°')):
    m = outer & (((th - lo) % 360) <= (hi - lo)); o = np.argsort(C[m, 2])
    a.plot(C[m, 2][o] * 1e3, vm[m][o], '.', ms=3, color=cl); a.text(C[m, 2][o][-1] * 1e3, vm[m][o][-1], ' ' + lab, color=cl, fontsize=8.5, va='center')
a.set_xlim(0, 760); a.set_xlabel('z (mm)'); a.set_ylabel('von Mises (MPa)')
a.set_title('Along the two extreme generators', loc='left', fontsize=10, color=INK)
fig.suptitle(f'F6  LS-DYNA nonlinear (extension) — C5 (A = 1.2 mm) at λ = 1.30: element von Mises, max {vm.max():.0f} MPa at z = {C[i,2]*1e3:.1f} mm', x=0.01, ha='left', fontsize=11, color=INK)
fig.text(0.01, 0.005, 'Elastic model (no plasticity). Stresses above S_y(T) (≈1000-1060 MPa) are outside the validity of the model and are not physical. θ measured from the sway direction.', fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(f'{OUT}/F6_stress_field_critical_state.png', dpi=150); plt.close(fig)
json.dump(out, open('fig56_C5.json', 'w'), indent=1); print(out)
