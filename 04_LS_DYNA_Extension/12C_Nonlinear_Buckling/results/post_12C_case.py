# Section 12C - extract the response history of one nonlinear run (read-only on solver output). ANSYS-bundled CPython (numpy).
# Usage: python post_12C_case.py <run_dir>   -> results/<case>_series.csv, results/<case>_summary.json
import os, re, sys, json, math
import numpy as np
R = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(R)
run = os.path.abspath(sys.argv[1]); case = os.path.basename(run)
LAM = [(0.0, 0.0), (0.4, 1.0), (0.8, 1.2), (0.9, 1.3)]                      # LCID 10 of every 12C deck
lam = lambda t: float(np.interp(t, [p[0] for p in LAM], [p[1] for p in LAM]))
X = {}
for l in open(os.path.join(B, 'model', 'nodes.k')):
    if l[:1].isdigit():
        a = l.split(','); X[int(a[0])] = np.array([float(a[1]), float(a[2]), float(a[3])])
TK = {}
for l in open(os.path.join(B, 'model', 'temps_lc2.k')):
    if l[:1].isdigit():
        a = l.split(','); TK[int(a[0])] = float(a[1])                     # T - 300 K
SY = [(293.15, 1030e6), (373.15, 1060e6), (473.15, 1040e6), (573.15, 1020e6), (673.15, 1000e6)]   # VDM 4127 typical (7B D-050)
sy = lambda T: float(np.interp(T, [p[0] for p in SY], [p[1] for p in SY]))
# ---------- nodout (monitor nodes) ----------
blocks = re.split(r'n o d a l   p r i n t   o u t   f o r   t i m e  s t e p\s+\d+\s+\( at time\s+([0-9.E+-]+)\s*\)', open(os.path.join(run, 'nodout')).read())
TN, UN = [], []
for i in range(1, len(blocks), 2):
    d = {}
    for l in blocks[i + 1].splitlines():
        if len(l) > 60 and l[:10].strip().isdigit():
            s = l[10:]; d[int(l[:10])] = np.array([float(s[j:j + 12]) for j in range(0, 36, 12)])
    if d and (not UN or len(d) == len(UN[0])): TN.append(float(blocks[i])); UN.append(d)   # skip a truncated last block
mon = sorted(UN[0]); ang = {n: round(math.degrees(math.atan2(X[n][1], X[n][0])) % 360, 3) for n in mon}
ring = [n for n in mon if abs(math.hypot(X[n][0], X[n][1]) - 0.02) < 1e-7 and ang[n] in (0.0, 90.0, 180.0, 270.0)]
zs = sorted(set(round(X[n][2], 9) for n in ring)); st = {z: [n for n in ring if round(X[n][2], 9) == z] for z in zs}
st = {z: v for z, v in st.items() if len(v) == 4}; zs = sorted(st)
zmid = min(zs, key=lambda z: abs(z - 0.3))
rows = []
for t, d in zip(TN, UN):
    T = {z: np.mean([d[n][:2] for n in st[z]], axis=0) for z in zs}           # section translation (x, y)
    lat = {z: float(np.hypot(*T[z])) for z in zs}
    zmax = max(zs, key=lambda z: lat[z])
    ur = {}
    for z in zs:
        v = []
        for n in st[z]:
            er = X[n][:2] / np.hypot(*X[n][:2]); v.append(float(np.dot(d[n][:2] - T[z], er)))
        ur[z] = v
    oval = max(max(v) - min(v) for v in ur.values())                          # ovalisation indicator
    allu = max(float(np.linalg.norm(d[n])) for n in mon)
    rows.append({'t': t, 'lambda': lam(t), 'sway_end_rel_mm': float(np.hypot(*(T[zs[-1]] - T[zs[0]])) * 1e3),
                 'lat_inlet_mm': lat[zs[0]] * 1e3, 'lat_outlet_mm': lat[zs[-1]] * 1e3, 'lat_mid_mm': lat[zmid] * 1e3,
                 'lat_max_mm': lat[zmax] * 1e3, 'z_lat_max_m': zmax, 'ur_mid_mean_mm': float(np.mean(ur[zmid]) * 1e3),
                 'oval_max_mm': oval * 1e3, 'uz_mid_mean_mm': float(np.mean([d[n][2] for n in st[zmid]]) * 1e3),
                 'uz_min_mm': float(min(d[n][2] for n in mon) * 1e3), 'u_total_max_monitor_mm': allu * 1e3,
                 'outlet_dir_deg': float(math.degrees(math.atan2(T[zs[-1]][1], T[zs[-1]][0])))})
# ---------- spcforc (ASCII, 5 digits; binout is used for precise balance) ----------
fb = re.split(r'output at time =\s+([0-9.E+-]+)', open(os.path.join(run, 'spcforc')).read())
F = {}
for i in range(1, len(fb), 2):
    fi = fo = 0.0
    for l in fb[i + 1].splitlines():
        m = re.match(r'\s*node=\s*(\d+) local x,y,z forces =\s+(\S+)\s+(\S+)\s+(\S+)', l)
        if m:
            n = int(m.group(1)); fz = float(m.group(4))
            if abs(X[n][2]) < 1e-9: fi += fz
            elif abs(X[n][2] - 0.6) < 1e-9: fo += fz
    F[round(float(fb[i]), 6)] = (fi, fo)
# ---------- glstat ----------
G = {}; cur = None
for l in open(os.path.join(run, 'glstat')):
    if l.strip().startswith('time....'): cur = round(float(l.split()[-1]), 6); G[cur] = {}
    elif cur is not None and ('internal energy' in l or 'external work' in l or 'total energy....' in l):
        key = 'IE' if 'internal' in l else ('EW' if 'external' in l else 'TE'); G[cur][key] = float(l.split()[-1])
# ---------- eloutdet (nodal stresses of element subset 2) ----------
S = {}; tcur = None; nid = None
with open(os.path.join(run, 'eloutdet')) as f:
    for l in f:
        if 'n o d a l  s t r e s s' in l:
            m = re.search(r'at time\s+([0-9.E+-]+)', l); tcur = round(float(m.group(1)), 6); S[tcur] = {}; nid = None; continue
        if 'e l e m e n t   s t r e s s' in l: tcur = None; continue
        if tcur is None: continue
        m = re.match(r'^\s+(\d+)-\s*$', l)
        if m: nid = int(m.group(1)); continue
        if nid and 'surface' in l:
            v = [float(x) for x in l.split()[2:8]]; S[tcur][nid] = v; nid = None
def vm(s):
    sx, sy_, sz, sxy, syz, szx = s
    return math.sqrt(0.5 * ((sx - sy_) ** 2 + (sy_ - sz) ** 2 + (sz - sx) ** 2) + 3 * (sxy ** 2 + syz ** 2 + szx ** 2))
SS = {}
for t, d in S.items():
    if not d: continue
    vms = {n: vm(s) for n, s in d.items()}; nmax = max(vms, key=vms.get)
    util = {n: vms[n] / sy(300.0 + lam(t) * TK[n]) for n in vms}; nu = max(util, key=util.get)
    szmin = min(d, key=lambda n: d[n][2]); szmax = max(d, key=lambda n: d[n][2])
    SS[t] = {'vm_max_MPa': vms[nmax] / 1e6, 'vm_max_node': nmax, 'vm_max_z_m': float(X[nmax][2]), 'vm_max_r_m': float(math.hypot(*X[nmax][:2])),
             'vm_max_T_K': 300.0 + lam(t) * TK[nmax], 'vm_18865_MPa': vms.get(18865, float('nan')) / 1e6, 'vm_mid_max_MPa': max((v for n, v in vms.items() if abs(X[n][2] - 0.3) <= 0.0041), default=float('nan')) / 1e6,
             'util_max': util[nu], 'util_node': nu, 'util_z_m': float(X[nu][2]),
             'sz_min_MPa': d[szmin][2] / 1e6, 'sz_max_MPa': d[szmax][2] / 1e6, 'sz_max_node': szmax}
# ---------- solver log: iterations, reformations, warnings ----------
it = []; cur = None
for l in open(os.path.join(run, 'messag'), errors='ignore'):
    m = re.search(r'Equilibrium iterations summary step\s+(\d+) t=\s*([0-9.E+-]+)', l)
    if m: cur = {'step': int(m.group(1)), 't': float(m.group(2))}; it.append(cur); continue
    if cur is not None:
        if 'Number of iterations to converge' in l: cur['iter'] = int(l.split()[-1])
        elif 'Number of stiffness reformations' in l: cur['reform'] = int(l.split()[-1])
txt = open(os.path.join(run, 'stdout.txt'), errors='ignore').read()
warn = sorted(set(re.findall(r'\*\*\* Warning (\d+)', txt)))
negev = len(re.findall(r'negative eigenvalue', txt, re.I))
normal = 'N o r m a l    t e r m i n a t i o n' in txt
# ---------- merge on nodout times ----------
for r in rows:
    k = round(r['t'], 6)
    if k in F: r['Fz_in_N'], r['Fz_out_N'] = F[k]
    if k in G: r.update({'IE_J': G[k].get('IE'), 'EW_J': G[k].get('EW')})
    if k in SS: r.update(SS[k])
    r['T_18865_K'] = 300.0 + r['lambda'] * TK[18865]
keys = []
for r in rows:
    for k in r:
        if k not in keys: keys.append(k)
os.makedirs(os.path.join(R, 'series'), exist_ok=True)
with open(os.path.join(R, 'series', f'{case}_series.csv'), 'w') as f:
    f.write(','.join(keys) + '\n')
    for r in rows: f.write(','.join('' if r.get(k) is None else (f'{r[k]:.9g}' if isinstance(r.get(k), float) else str(r.get(k))) for k in keys) + '\n')
summ = {'case': case, 'normal_termination': normal, 'n_output_points': len(rows), 't_final': rows[-1]['t'] if rows else None,
        'lambda_final': rows[-1]['lambda'] if rows else None, 'steps': len(it), 'max_iter': max((s.get('iter', 0) for s in it), default=None),
        'total_reformations': sum(s.get('reform', 0) for s in it), 'warnings': warn, 'negative_eigenvalue_mentions': negev,
        'n_monitor_stations': len(zs), 'eloutdet_states': len(SS), 'iterations_per_step': [(s['t'], s.get('iter'), s.get('reform')) for s in it]}
json.dump(summ, open(os.path.join(R, 'series', f'{case}_summary.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in summ.items() if k != 'iterations_per_step'}))
