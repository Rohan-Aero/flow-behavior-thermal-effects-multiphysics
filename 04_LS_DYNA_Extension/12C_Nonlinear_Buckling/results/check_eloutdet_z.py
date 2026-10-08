# One-off check: which axial positions are covered by the nodal stresses in eloutdet (first output state).
import re, sys, os
run = sys.argv[1]; B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Z = {}
for l in open(os.path.join(B, 'model', 'nodes.k')):
    if l[:1].isdigit():
        a = l.replace(',', ' ').split(); Z[int(a[0])] = float(a[3])
nodes = set(); elems = 0; state = 0
with open(os.path.join(run, 'eloutdet')) as f:
    for l in f:
        if 'n o d a l  s t r e s s' in l:
            state += 1
            if state > 2: break
            continue
        m = re.match(r'^\s+(\d+)-\s*$', l)
        if m and state == 2: nodes.add(int(m.group(1)))
zs = sorted(Z[n] for n in nodes if n in Z)
bins = {}
for z in zs: bins[round(z, 2)] = bins.get(round(z, 2), 0) + 1
print('nodes', len(nodes), 'z-bins', bins)
