# Section 12B Gate 5 - compare the LS-DYNA LC2 run with the Mechanical LC2 solution (read-only on project files).
# Usage: python post_lc2_12B.py <run_dir> <time>   (ANSYS-bundled CPython with numpy)
import os, sys, re, json, math
import numpy as np
W = os.path.dirname(os.path.abspath(__file__)); P = os.path.abspath(os.path.join(W, '..', '..'))
run = sys.argv[1]; tsel = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
MECH = os.path.join(P, r'08_Structural_Analysis\LC2_Restrained\Solver_Output')
# model: nodes, corner nodes, temperatures
X = {}; 
for l in open(os.path.join(W, 'G4_import', 'model', 'nodes.k')):
    if l[:1].isdigit():
        a = l.split(','); X[int(a[0])] = np.array([float(a[1]), float(a[2]), float(a[3])])
corner = set(); el = open(os.path.join(W, 'G4_import', 'model', 'elements_h20.k')).read().splitlines()
for k, l in enumerate(el):
    if re.match(r'^\d+,1$', l): corner.update(int(v) for v in el[k + 1].split(',')[:8])
TK = {}
for l in open(os.path.join(W, 'G4_import', 'model', 'temps_lc2.k')):
    if l[:1].isdigit():
        a = l.split(','); TK[int(a[0])] = 300.0 + float(a[1])
def block_at(text, pattern, t):
    parts = re.split(pattern, text)
    best = None
    for i in range(1, len(parts), 2):
        if abs(float(parts[i]) - t) < 1e-6: best = parts[i + 1]
    return best
# ---- LS-DYNA nodal displacements (nodout) ----
txt = open(os.path.join(run, 'nodout')).read()
b = block_at(txt, r'at time\s+([0-9.E+-]+)\s*\)', tsel)
U = {}
for l in b.splitlines():
    m = re.match(r'^\s*(\d+)\s+(.+)$', l)
    if m and len(l) > 60:
        s = l[10:]; vals = [float(s[i:i + 12]) for i in range(0, 36, 12)]
        U[int(m.group(1))] = np.array(vals)
# ---- LS-DYNA nodal averaged global stress (eloutdet) ----
txt = open(os.path.join(run, 'eloutdet')).read()
nb = re.split(r'n o d a l  s t r e s s  c a l c u l a t i o n s.*?at time\s+([0-9.E+-]+)\s*\)', txt)
S = {}
for i in range(1, len(nb), 2):
    if abs(float(nb[i]) - tsel) < 1e-6:
        lines = nb[i + 1].splitlines(); nid = None
        for l in lines:
            m = re.match(r'^\s+(\d+)-\s*$', l)
            if m: nid = int(m.group(1)); continue
            if nid and 'surface' in l:
                v = [float(x) for x in l.split()[2:8]]; S[nid] = np.array(v); nid = None
def vm(s):
    sx, sy, sz, sxy, syz, szx = s
    return math.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3 * (sxy ** 2 + syz ** 2 + szx ** 2))
# ---- LS-DYNA reactions (spcforc) at tsel: inlet face z = 0 ----
txt = open(os.path.join(run, 'spcforc')).read()
fb = re.split(r'output at time =\s+([0-9.E+-]+)', txt)
Fz_in = Fz_out = None; F_hoop = []
for i in range(1, len(fb), 2):
    if abs(float(fb[i]) - tsel) < 1e-6:
        fi = fo = 0.0; F_hoop = []
        for l in fb[i + 1].splitlines():
            m = re.match(r'\s*node=\s*(\d+) local x,y,z forces =\s+(\S+)\s+(\S+)\s+(\S+)', l)
            if m:
                n = int(m.group(1)); fz = float(m.group(4))
                if n in (25862, 25874, 25886): F_hoop.append((n, float(m.group(2)), float(m.group(3)), fz))
                elif abs(X[n][2]) < 1e-9: fi += fz
                elif abs(X[n][2] - 0.6) < 1e-9: fo += fz
        Fz_in, Fz_out = fi, fo
A_nom = math.pi * (0.02 ** 2 - 0.01 ** 2)
# ---- Mechanical baseline ----
M = {}
for l in open(os.path.join(MECH, 's7b_nodal.csv')).read().splitlines()[1:]:
    a = [float(x) for x in l.split(',')]; M[int(a[0])] = a
def ur(n, u):
    x, y = X[n][0], X[n][1]; r = math.hypot(x, y); return (u[0] * x + u[1] * y) / r
common = sorted(corner & set(S) & set(M))
vm_ls = {n: vm(S[n]) for n in S}
n_ls = max(common, key=lambda n: vm_ls[n]); n_me = max(common, key=lambda n: M[n][12])
dvm = np.array([vm_ls[n] - M[n][12] for n in common]); dsz = np.array([S[n][2] - M[n][9] for n in common])
allU = sorted(set(U) & set(M))
umag_ls = {n: float(np.linalg.norm(U[n])) for n in allU}
n_u_ls = max(allU, key=lambda n: umag_ls[n]); n_u_me = max(allU, key=lambda n: math.sqrt(M[n][4] ** 2 + M[n][5] ** 2 + M[n][6] ** 2))
ur_ls = {n: ur(n, U[n]) for n in allU}
du_r = np.array([ur_ls[n] - M[n][4] for n in allU]); du_z = np.array([U[n][2] - M[n][6] for n in allU])
mid_outer = [n for n in allU if abs(X[n][2] - 0.3) < 1e-9 and abs(math.hypot(X[n][0], X[n][1]) - 0.02) < 1e-9]
res = {
 'run': run, 'time': tsel, 'n_nodout': len(U), 'n_eloutdet_nodes': len(S), 'n_common_corner': len(common),
 'reaction_inlet_Fz_N': Fz_in, 'reaction_outlet_Fz_N': Fz_out, 'hoop_node_forces_local_N': F_hoop,
 'mean_axial_stress_MPa_from_inlet_reaction': -abs(Fz_in) / A_nom / 1e6 if Fz_in is not None else None,
 'max_vm_corner_MPa': vm_ls[n_ls] / 1e6, 'max_vm_node': n_ls, 'max_vm_xyz_m': X[n_ls].tolist(), 'max_vm_r_m': float(math.hypot(*X[n_ls][:2])), 'max_vm_T_K': TK[n_ls],
 'mech_max_vm_MPa': M[n_me][12] / 1e6, 'mech_max_vm_node': n_me, 'mech_max_vm_T_K': M[n_me][14] + 273.15,
 'vm_diff_corner_MPa': {'max_abs': float(np.abs(dvm).max() / 1e6), 'rms': float(np.sqrt((dvm ** 2).mean()) / 1e6)},
 'sz_diff_corner_MPa': {'max_abs': float(np.abs(dsz).max() / 1e6), 'rms': float(np.sqrt((dsz ** 2).mean()) / 1e6)},
 'max_total_disp_mm': umag_ls[n_u_ls] * 1e3, 'max_total_disp_node': n_u_ls, 'max_total_disp_xyz_m': X[n_u_ls].tolist(),
 'mech_max_total_disp_mm': math.sqrt(sum(M[n_u_me][k] ** 2 for k in (4, 5, 6))) * 1e3, 'mech_max_total_disp_node': n_u_me,
 'u_r_range_mm': [min(ur_ls.values()) * 1e3, max(ur_ls.values()) * 1e3], 'mech_u_r_range_mm': [min(M[n][4] for n in allU) * 1e3, max(M[n][4] for n in allU) * 1e3],
 'u_r_midspan_outer_mm': float(np.mean([ur_ls[n] for n in mid_outer]) * 1e3), 'mech_u_r_midspan_outer_mm': float(np.mean([M[n][4] for n in mid_outer]) * 1e3),
 'u_r_diff_mm': {'max_abs': float(np.abs(du_r).max() * 1e3), 'rms': float(np.sqrt((du_r ** 2).mean()) * 1e3)},
 'u_z_diff_mm': {'max_abs': float(np.abs(du_z).max() * 1e3)},
 'max_lateral_disp_mm': max(math.hypot(U[n][0] - ur_ls[n] * X[n][0] / math.hypot(*X[n][:2]), U[n][1] - ur_ls[n] * X[n][1] / math.hypot(*X[n][:2])) for n in allU) * 1e3,
}
k_vm = int(np.argmax(np.abs(dvm))); k_sz = int(np.argmax(np.abs(dsz)))
interior = np.array([15e-3 <= X[n][2] <= 0.585 for n in common])
res['max_abs_vm_diff_at'] = {'node': common[k_vm], 'xyz_m': X[common[k_vm]].tolist(), 'diff_MPa': float(dvm[k_vm] / 1e6)}
res['max_abs_sz_diff_at'] = {'node': common[k_sz], 'xyz_m': X[common[k_sz]].tolist(), 'diff_MPa': float(dsz[k_sz] / 1e6)}
res['interior_15_585mm_diff_MPa'] = {'n': int(interior.sum()), 'vm_rms': float(np.sqrt((dvm[interior] ** 2).mean()) / 1e6), 'vm_max_abs': float(np.abs(dvm[interior]).max() / 1e6),
                                     'sz_rms': float(np.sqrt((dsz[interior] ** 2).mean()) / 1e6), 'sz_max_abs': float(np.abs(dsz[interior]).max() / 1e6),
                                     'sz_mean': float(dsz[interior].mean() / 1e6)}
k_uz = int(np.argmax(np.abs(du_z)))
res['max_abs_uz_diff_at'] = {'node': allU[k_uz], 'xyz_m': X[allU[k_uz]].tolist(), 'diff_mm': float(du_z[k_uz] * 1e3), 'mech_uz_mm': float(M[allU[k_uz]][6] * 1e3)}
res['mech_max_total_disp_xyz_m'] = X[n_u_me].tolist()
res['uz_range_mm'] = [float(min(U[n][2] for n in allU) * 1e3), float(max(U[n][2] for n in allU) * 1e3)]
res['mech_uz_range_mm'] = [float(min(M[n][6] for n in allU) * 1e3), float(max(M[n][6] for n in allU) * 1e3)]
json.dump(res, open(os.path.join(run, 'post_12B.json'), 'w'), indent=1)
for k, v in res.items():
    if k != 'hoop_node_forces_local_N': print(k, v)
print('hoop', F_hoop)
