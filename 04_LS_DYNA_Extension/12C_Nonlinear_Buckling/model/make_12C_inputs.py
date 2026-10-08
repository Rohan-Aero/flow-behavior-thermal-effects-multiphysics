# Section 12C - build imperfection node files, monitor/element sets and case decks from the validated 12B model (read-only inputs).
import numpy as np, json, os, hashlib
from lasso.dyna import D3plot
U = "<PROJECT_ROOT>/15_LS_DYNA_Extension/work_12B"
OUT = "<OUTPUT_ROOT>/S12C/15_LS_DYNA_Extension/12C_Nonlinear_Buckling"
for d in ('imperfection', 'model', 'runs', 'audit'): os.makedirs(f"{OUT}/{d}", exist_ok=True)
# --- validated geometry (nodes.k of 12B) ---
hdr, X0 = [], {}
for l in open(f"{U}/G4_import/model/nodes.k"):
    if l[:1].isdigit():
        a = l.split(','); X0[int(a[0])] = np.array([float(a[1]), float(a[2]), float(a[3])])
    else: hdr.append(l.rstrip('\n'))
ids = np.array(sorted(X0)); XX = np.array([X0[i] for i in ids])
# --- validated mode 1 from 12B G6 (d3eigv; geometry there is the prestressed state, mode = state - geometry) ---
d = D3plot(f"{U}/G6_buckle_10step/d3eigv")
did = d.arrays['node_ids']; phi_all = d.arrays['node_displacement'][0] - d.arrays['node_coordinates']
pos = {int(n): k for k, n in enumerate(did)}
phi = np.array([phi_all[pos[i]] for i in ids])
lat = np.hypot(phi[:, 0], phi[:, 1]); kmax = int(np.argmax(lat))
phin = phi / lat[kmax]          # normalisation: max nodal lateral (x-y) magnitude = 1
z = XX[:, 2]; r = np.hypot(XX[:, 0], XX[:, 1])
endf = (np.abs(z) < 1e-9) | (np.abs(z - 0.6) < 1e-9)
hoop = np.isin(ids, [25862, 25874, 25886])
th = np.degrees(np.arctan2(phin[kmax, 1], phin[kmax, 0]))
rep = {'source_mode': 'work_12B/G6_buckle_10step/d3eigv mode 1 (lambda 1.109475)',
       'normalisation': 'phi_hat = phi / max_n sqrt(phi_x^2+phi_y^2); imperfect X = X_12B + A*phi_hat (full 3-D vector)',
       'max_lateral_node': int(ids[kmax]), 'max_lateral_node_xyz_m': XX[kmax].tolist(), 'max_lateral_direction_deg': float(th),
       'max_abs_axial_component_hat': float(np.abs(phin[:, 2]).max()),
       'max_abs_uz_hat_on_end_faces': float(np.abs(phin[endf, 2]).max()),
       'max_lateral_hat_at_hoop_nodes': float(np.hypot(phin[hoop, 0], phin[hoop, 1]).max()),
       'lambda_eig': float(d.arrays['timesteps'][0]), 'files': {}}
amps = {'A0p1': 0.1e-3, 'A0p3': 0.3e-3, 'A0p6': 0.6e-3, 'A0p9': 0.9e-3, 'A1p2': 1.2e-3}
for tag, A in amps.items():
    Xi = XX + A * phin
    fn = f"{OUT}/imperfection/nodes_{tag}.k"
    with open(fn, 'w', newline='\n') as f:
        f.write('*KEYWORD\n$ 12C imperfect geometry: validated 12B nodes + A*phi_hat (mode 1, max lateral = 1), A = %.4f mm\n*NODE\n' % (A * 1e3))
        for n, x in zip(ids, Xi): f.write(f'{n},{x[0]:.9e},{x[1]:.9e},{x[2]:.9e}\n')
        f.write('*END\n')
    # check: realised max lateral offset
    dd = Xi - XX
    rep['files'][tag] = {'A_mm': A * 1e3, 'realised_max_lateral_mm': float(np.hypot(dd[:, 0], dd[:, 1]).max() * 1e3),
                         'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest()}
np.save('phin.npy', phin); np.save('ids.npy', ids)
# --- monitor node set 21: outer surface r = 20 mm at theta 0/90/180/270 deg, every node plane; + critical + hoop nodes ---
ang = np.degrees(np.arctan2(XX[:, 1], XX[:, 0])) % 360
outer = np.abs(r - 0.02) < 1e-7
mon = []
for a0 in (0, 90, 180, 270):
    sel = outer & (np.minimum(np.abs(ang - a0), 360 - np.abs(ang - a0)) < 1e-4)
    mon += list(ids[sel])
mon = sorted(set(mon) | {18865, 89468, 25862, 25874, 25886})
# --- element subset 2 for eloutdet: centroid z <= 30 mm, >= 570 mm, or |z - 300| <= 4 mm ---
E = []; el = open(f"{U}/G4_import/model/elements_h20.k").read().splitlines()
for k, l in enumerate(el):
    if l.endswith(',1') and l.count(',') == 1 and l.split(',')[0].isdigit():
        eid = int(l.split(',')[0]); cn = [int(v) for v in el[k + 1].split(',')[:8]]
        zc = np.mean([X0[c][2] for c in cn]); E.append((eid, zc))
sub = [e for e, zc in E if zc <= 0.030 or zc >= 0.570 or abs(zc - 0.3) <= 0.004]
with open(f"{OUT}/model/monitor_sets_12C.k", 'w', newline='\n') as f:
    f.write('*KEYWORD\n$ 12C output sets: 21 = monitor nodes (outer surface 0/90/180/270 deg, all node planes, + 18865 89468 + hoop nodes)\n')
    f.write('$ 2 = solid subset for eloutdet (centroid z <= 30 mm, >= 570 mm, |z-300| <= 4 mm)\n*SET_NODE_LIST\n21\n')
    for i in range(0, len(mon), 8): f.write(','.join(str(v) for v in mon[i:i + 8]) + '\n')
    f.write('*SET_SOLID\n2\n')
    for i in range(0, len(sub), 8): f.write(','.join(str(v) for v in sub[i:i + 8]) + '\n')
    f.write('*END\n')
rep['n_monitor_nodes'] = len(mon); rep['n_subset_elements'] = len(sub); rep['n_elements'] = len(E)
json.dump(rep, open(f"{OUT}/audit/imperfection_report_12C.json", 'w'), indent=1)
print(json.dumps({k: v for k, v in rep.items() if k != 'files'}, indent=1)); print(rep['files'])
