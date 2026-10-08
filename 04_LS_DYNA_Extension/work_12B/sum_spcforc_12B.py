# Section 12B - sum LS-DYNA spcforc reactions on the inlet (z=0) and outlet (z=0.6 m) end faces at every output time.
# Usage: python sum_spcforc_12B.py <run_dir>     (read-only; ANSYS-bundled CPython)
import os, re, sys, json
W = os.path.dirname(os.path.abspath(__file__)); run = sys.argv[1]
Z = {}
for l in open(os.path.join(W, 'G4_import', 'model', 'nodes.k')):
    if l[:1].isdigit():
        a = l.split(','); Z[int(a[0])] = float(a[3])
txt = open(os.path.join(run, 'spcforc')).read()
fb = re.split(r'output at time =\s+([0-9.E+-]+)', txt)
out = []
for i in range(1, len(fb), 2):
    fi = fo = 0.0; ni = no = 0; hoop = []
    for l in fb[i + 1].splitlines():
        m = re.match(r'\s*node=\s*(\d+) local x,y,z forces =\s+(\S+)\s+(\S+)\s+(\S+)', l)
        if not m: continue
        n = int(m.group(1)); fx, fy, fz = float(m.group(2)), float(m.group(3)), float(m.group(4))
        if n in (25862, 25874, 25886): hoop.append([n, fx, fy, fz])
        if abs(Z[n]) < 1e-9: fi += fz; ni += 1
        elif abs(Z[n] - 0.6) < 1e-9: fo += fz; no += 1
    out.append({'t': float(fb[i]), 'Fz_inlet_N': fi, 'Fz_outlet_N': fo, 'n_inlet': ni, 'n_outlet': no, 'hoop_local_N': hoop})
json.dump(out, open(os.path.join(run, 'spcforc_sum_12B.json'), 'w'), indent=1)
for r in out:
    print('t=%.4f  Fz_in=%.1f N  Fz_out=%.1f N  n_in=%d n_out=%d  hoop=%s' % (r['t'], r['Fz_inlet_N'], r['Fz_outlet_N'], r['n_inlet'], r['n_outlet'], r['hoop_local_N']))
