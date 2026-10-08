# Section 12B - compare two LS-DYNA LC2 static states at time t (read-only): reactions, peak von Mises and the nodal stress field.
# Usage: python compare_runs_12B.py <run_ref> <run_test> <time>   e.g. G5_static (40 steps) vs G6_buckle_10step (10 steps)
import os, re, sys, json, math
import numpy as np
W = os.path.dirname(os.path.abspath(__file__))
ref, tst, tsel = sys.argv[1], sys.argv[2], float(sys.argv[3])
Z = {}
for l in open(os.path.join(W, 'G4_import', 'model', 'nodes.k')):
    if l[:1].isdigit():
        a = l.split(','); Z[int(a[0])] = float(a[3])
def stresses(run):
    txt = open(os.path.join(run, 'eloutdet')).read()
    nb = re.split(r'n o d a l  s t r e s s  c a l c u l a t i o n s.*?at time\s+([0-9.E+-]+)\s*\)', txt)
    S = {}
    for i in range(1, len(nb), 2):
        if abs(float(nb[i]) - tsel) < 1e-6:
            nid = None
            for l in nb[i + 1].splitlines():
                m = re.match(r'^\s+(\d+)-\s*$', l)
                if m: nid = int(m.group(1)); continue
                if nid and 'surface' in l:
                    S[nid] = np.array([float(x) for x in l.split()[2:8]]); nid = None
    return S
def reac(run):
    txt = open(os.path.join(run, 'spcforc')).read()
    fb = re.split(r'output at time =\s+([0-9.E+-]+)', txt)
    for i in range(1, len(fb), 2):
        if abs(float(fb[i]) - tsel) < 1e-6:
            fi = fo = 0.0
            for l in fb[i + 1].splitlines():
                m = re.match(r'\s*node=\s*(\d+) local x,y,z forces =\s+(\S+)\s+(\S+)\s+(\S+)', l)
                if m:
                    n = int(m.group(1)); fz = float(m.group(4))
                    if abs(Z[n]) < 1e-9: fi += fz
                    elif abs(Z[n] - 0.6) < 1e-9: fo += fz
            return fi, fo
def vm(s):
    sx, sy, sz, sxy, syz, szx = s
    return math.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3 * (sxy ** 2 + syz ** 2 + szx ** 2))
Sr, St = stresses(ref), stresses(tst)
common = sorted(set(Sr) & set(St))
vr = np.array([vm(Sr[n]) for n in common]); vt = np.array([vm(St[n]) for n in common])
szr = np.array([Sr[n][2] for n in common]); szt = np.array([St[n][2] for n in common])
Fr, Ft = reac(ref), reac(tst)
kr, kt = int(np.argmax(vr)), int(np.argmax(vt))
res = {'ref': ref, 'test': tst, 'time': tsel, 'n_nodes': len(common),
       'reaction_inlet_N': [Fr[0], Ft[0]], 'reaction_inlet_rel_diff': Ft[0] / Fr[0] - 1,
       'peak_vm_MPa': [float(vr[kr] / 1e6), float(vt[kt] / 1e6)], 'peak_vm_node': [common[kr], common[kt]],
       'peak_vm_rel_diff': float(vt[kt] / vr[kr] - 1),
       'vm_diff_MPa': {'rms': float(np.sqrt(((vt - vr) ** 2).mean()) / 1e6), 'max_abs': float(np.abs(vt - vr).max() / 1e6)},
       'sz_diff_MPa': {'rms': float(np.sqrt(((szt - szr) ** 2).mean()) / 1e6), 'max_abs': float(np.abs(szt - szr).max() / 1e6),
                       'mean': float((szt - szr).mean() / 1e6)},
       'mean_sz_ratio_test_over_ref': float(szt.mean() / szr.mean())}
out = os.path.join(tst, 'compare_vs_' + os.path.basename(os.path.normpath(ref)) + '.json')
json.dump(res, open(out, 'w'), indent=1)
for k, v in res.items(): print(k, v)
