"""Parse a Mechanical-written MAPDL input (ds.dat): nodes, SOLID186 connectivity, BF TEMP block, components.
RE-ANALYSIS 2026 helper (Section 7A)."""
import numpy as np, re

def parse(path):
    L = open(path, errors='ignore').read().split('\n')
    i = 0; nodes = {}; elems = []; bf = {}; comps = {}; tref = None; info = {}
    n = len(L)
    while i < n:
        s = L[i].strip(); low = s.lower()
        if low.startswith('nblock'):
            i += 2
            while i < n and not L[i].strip().startswith('-1'):
                t = L[i]
                nid = int(t[0:9]); x = float(t[9:29]); y = float(t[29:49]); z = float(t[49:69]) if len(t) > 49 else 0.0
                nodes[nid] = (x, y, z); i += 1
        elif low.startswith('eblock'):
            i += 2
            while i < n and not L[i].strip().startswith('-1'):
                v = [int(L[i][k:k+9]) for k in range(0, len(L[i].rstrip()), 9)]
                elems.append(v); i += 1
        elif low.startswith('bfblock'):
            i += 2
            while i < n and not L[i].strip().lower().startswith('bf,end'):
                t = L[i]
                if t.strip():
                    bf[int(t[0:9])] = float(t[9:29])
                i += 1
        elif low.startswith('cmblock'):
            p = s.split(','); name = p[1].strip(); cnt = int(p[3]); i += 2; vals = []
            while len(vals) < cnt:
                t = L[i]; vals += [int(t[k:k+10]) for k in range(0, len(t.rstrip()), 10)]; i += 1
            ids = []
            for k, v in enumerate(vals):
                if v < 0:
                    ids += list(range(vals[k-1] + 1, -v + 1))
                else:
                    ids.append(v)
            comps[name] = np.array(ids); continue
        elif low.startswith('tref'):
            tref = float(s.split(',')[1])
        i += 1
    return nodes, elems, bf, comps, tref

def classify(elems):
    """SOLID186 'COMPACT' eblock line = element id followed by its 20 node ids (first 8 = corner nodes)."""
    corner = set(); mid = set()
    for v in elems:
        ids = v[1:21]
        corner.update(ids[:8]); mid.update(ids[8:])
    return corner, mid - corner
