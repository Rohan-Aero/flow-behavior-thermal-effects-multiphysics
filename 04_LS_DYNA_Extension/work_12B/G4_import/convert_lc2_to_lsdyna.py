# Section 12B Gate 4 - scripted conversion of the solved Mechanical LC2 deck to LS-DYNA keyword include files.
# Source (read only): 08_Structural_Analysis/LC2_Restrained/Solver_Output/LC2_solve_input_ds.dat
# Units: m, kg, s, N, Pa, K.  Node IDs and element IDs are kept.  Run with the ANSYS-bundled CPython (numpy).
import os, sys, json, hashlib, math
import numpy as np
P = r'<PROJECT_ROOT>'
SRC = os.path.join(P, r'08_Structural_Analysis\LC2_Restrained\Solver_Output\LC2_solve_input_ds.dat')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model')
os.makedirs(OUT, exist_ok=True)
rep = {'source': SRC, 'source_sha256': hashlib.sha256(open(SRC, 'rb').read()).hexdigest()}
L = open(SRC, encoding='utf-8', errors='replace').read().splitlines()
low = [l.strip().lower() for l in L]
def find(prefix, start=0):
    for i in range(start, len(L)):
        if low[i].startswith(prefix):
            return i
    raise KeyError(prefix)
# ---- nodes (NBLOCK, format (1i9,3e20.9e3)) ----
i = find('nblock') + 2
nodes = {}
while L[i].strip() != '-1':
    s = L[i]; nid = int(s[0:9]); xyz = (float(s[9:29]), float(s[29:49]), float(s[49:69]))
    nodes[nid] = xyz; i += 1
rep['nodes'] = len(nodes); rep['node_id_range'] = [min(nodes), max(nodes)]
# ---- elements (EBLOCK COMPACT, (21i9): element id + 20 nodes I..P,Q..X,Y,Z,A,B) ----
assert 'et,1,186' in low[find('et,1,186')]
i = find('eblock') + 2
elems = {}
while L[i].strip() != '-1':
    s = L[i]; f = [int(s[k:k + 9]) for k in range(0, len(s.rstrip()), 9)]
    assert len(f) == 21, ('unexpected EBLOCK record length', i, len(f))
    elems[f[0]] = f[1:]; i += 1
rep['elements'] = len(elems)
used = set(n for c in elems.values() for n in c)
rep['nodes_referenced'] = len(used); rep['nodes_unreferenced'] = len(set(nodes) - used)
# ---- TREF, materials (echo only; the LS-DYNA material is written from these values) ----
rep['tref_C'] = float(L[find('tref,')].split(',')[1])
mat = {}
for k in range(find('/wb,mat,start'), find('/wb,mat,end')):
    t = L[k].split('!')[0].strip()
    if t.upper().startswith('MPDATA'):
        p = [x.strip() for x in t.split(',')]
        mat[p[1].upper()] = [float(x) for x in p[4:] if x]
    if t.upper().startswith('MP,DENS'):
        mat['DENS'] = [float(t.split(',')[3])]
    if t.upper().startswith('MPAMOD'):
        mat['MPAMOD_DEFTEMP_C'] = [float(t.split(',')[2])]
rep['mpdata'] = mat
# ---- components ----
def cmblock(name):
    k = next(j for j, l in enumerate(L) if l.upper().startswith('CMBLOCK,' + name.upper() + ' ') or l.upper().startswith('CMBLOCK,' + name.upper() + ','))
    n = int(L[k].split(',')[3]); vals = []; j = k + 2
    while len(vals) < n:
        vals += [int(x) for x in L[j].split()]; j += 1
    out = []
    for a, v in enumerate(vals):
        out += list(range(vals[a - 1] + 1, -v + 1)) if v < 0 else [v]
    return out
endz = cmblock('_DISPZEROUZ'); hoop = cmblock('_CM93U'); inlet = cmblock('SOLID_INLET_END'); outlet = cmblock('SOLID_OUTLET_END')
lc1sup = cmblock('NS_LC1_SUPPORT_3NODES_INLET_OUTE')
rep.update(n_endface_uz=len(endz), hoop_nodes=hoop, n_inlet=len(inlet), n_outlet=len(outlet), lc1_support_nodes=lc1sup)
assert sorted(endz) == sorted(set(inlet) | set(outlet))
# constraint commands actually present
rep['d_commands'] = [L[k].strip() for k in range(len(L)) if low[k].startswith('d,')]
rep['nrot_commands'] = [L[k].strip() for k in range(len(L)) if low[k].startswith('nrot')]
# ---- temperatures (BFBLOCK, deg C) ----
i = find('bfblock') + 2
temp = {}
while not low[i].startswith('bf,end'):
    a = L[i].split(); temp[int(a[0])] = float(a[1]); i += 1
assert set(temp) == set(nodes)
TK = {n: t + 273.15 for n, t in temp.items()}
rep['n_temperatures'] = len(TK); rep['T_K_min'] = min(TK.values()); rep['T_K_max'] = max(TK.values())
# ---- write include files (comma-delimited free format) ----
def w(name, lines):
    with open(os.path.join(OUT, name), 'w', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
w('nodes.k', ['*KEYWORD', '$ mesh B nodes from LC2_solve_input_ds.dat NBLOCK (m)', '*NODE'] +
  [f'{n},{x:.9e},{y:.9e},{z:.9e}' for n, (x, y, z) in sorted(nodes.items())] + ['*END'])
el = ['*KEYWORD', '$ mesh B SOLID186 -> 20-node *ELEMENT_SOLID; node order I..P,Q..X,Y,Z,A,B kept (= LS-DYNA H20 order, verified 12B G2)', '*ELEMENT_SOLID_H20']
for e, c in sorted(elems.items()):
    el += [f'{e},1', ','.join(map(str, c[:10])), ','.join(map(str, c[10:]))]
w('elements_h20.k', el + ['*END'])
def setlist(sid, title, ids):
    out = ['*SET_NODE_LIST_TITLE', title, f'{sid}']
    for k in range(0, len(ids), 8):
        out.append(','.join(map(str, ids[k:k + 8])))
    return out
w('sets.k', ['*KEYWORD'] + setlist(1, 'LC2_ENDFACES_UZ0 (=_DISPZEROUZ)', sorted(endz)) + setlist(2, 'LC2_HOOP_3NODES (=_CM93U)', hoop)
  + setlist(3, 'SOLID_INLET_END', sorted(inlet)) + setlist(4, 'SOLID_OUTLET_END', sorted(outlet)) + setlist(5, 'ALL_NODES', sorted(nodes)) + ['*END'])
cs = ['*KEYWORD', '$ node-local Cartesian systems: x = radial, y = hoop (theta), z = axial (= CS_DUCT_CYL at each hoop node)']
spc = ['*KEYWORD', '*BOUNDARY_SPC_SET', '$ LC2: U_z = 0 on both complete end faces (global), radial/hoop free', '1,0,0,0,1,0,0,0', '*BOUNDARY_SPC_NODE', '$ LC2: U_theta = 0 at 3 mid-span outer nodes']
for k, n in enumerate(hoop):
    x, y, z = nodes[n]; th = math.atan2(y, x); c, s_ = math.cos(th), math.sin(th)
    cs += ['*DEFINE_COORDINATE_SYSTEM', f'{101 + k},0.0,0.0,0.0,{c:.7f},{s_:.7f},0.0,0', f'{-s_:.7f},{c:.7f},0.0']
    spc.append(f'{n},{101 + k},0,1,0,0,0,0')
w('csys_hoop.k', cs + ['*END']); w('spc_lc2.k', spc + ['*END'])
tl = ['*KEYWORD', '$ mapped Fluent field (BFBLOCK) in K: T = TB + TS*lambda(t), TB = 300 K, TS = T_i - 300 K, LCID 10', '*LOAD_THERMAL_VARIABLE_NODE']
tl += [f'{n},{TK[n] - 300.0:.6f},300.0,10' for n in sorted(TK)]
w('temps_lc2.k', tl + ['*END'])
# ---- geometric checks: H20 Jacobians and volume (3x3x3 Gauss) ----
xi = np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1],
               [0,-1,-1],[1,0,-1],[0,1,-1],[-1,0,-1],[0,-1,1],[1,0,1],[0,1,1],[-1,0,1],
               [-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]], float)   # ANSYS/LS-DYNA H20 order
g = np.array([-math.sqrt(0.6), 0.0, math.sqrt(0.6)]); wg = np.array([5/9, 8/9, 5/9])
def dN(r, s, t):
    d = np.zeros((20, 3))
    for a in range(20):
        ra, sa, ta = xi[a]
        if a < 8:
            f = (1 + r*ra) * (1 + s*sa) * (1 + t*ta) / 8; q = r*ra + s*sa + t*ta - 2
            d[a] = [ra*(1+s*sa)*(1+t*ta)/8*q + f*ra/(1+r*ra)*0 + (1+r*ra)*(1+s*sa)*(1+t*ta)/8*ra,
                    sa*(1+r*ra)*(1+t*ta)/8*q + (1+r*ra)*(1+s*sa)*(1+t*ta)/8*sa,
                    ta*(1+r*ra)*(1+s*sa)/8*q + (1+r*ra)*(1+s*sa)*(1+t*ta)/8*ta]
        elif ra == 0:
            d[a] = [-2*r*(1+s*sa)*(1+t*ta)/4, (1-r*r)*sa*(1+t*ta)/4, (1-r*r)*(1+s*sa)*ta/4]
        elif sa == 0:
            d[a] = [ra*(1-s*s)*(1+t*ta)/4, -2*s*(1+r*ra)*(1+t*ta)/4, (1+r*ra)*(1-s*s)*ta/4]
        else:
            d[a] = [ra*(1+s*sa)*(1-t*t)/4, (1+r*ra)*sa*(1-t*t)/4, -2*t*(1+r*ra)*(1+s*sa)/4]
    return d
DN = [(dN(r, s, t), wg[i]*wg[j]*wg[k]) for i, r in enumerate(g) for j, s in enumerate(g) for k, t in enumerate(g)]
X = np.zeros((max(nodes) + 1, 3))
for n, c in nodes.items(): X[n] = c
vol = 0.0; jmin = 1e30; jneg = 0
for e, c in elems.items():
    xe = X[c]
    for d, wt in DN:
        dj = np.linalg.det(d.T @ xe); vol += dj * wt; jmin = min(jmin, dj); jneg += dj <= 0
rep['volume_m3'] = vol; rep['min_detJ'] = jmin; rep['n_gauss_detJ_le_0'] = int(jneg)
rep['L_m'] = max(c[2] for c in nodes.values()) - min(c[2] for c in nodes.values())
json.dump(rep, open(os.path.join(OUT, 'conversion_report.json'), 'w'), indent=1)
for k in ('nodes', 'elements', 'nodes_unreferenced', 'n_endface_uz', 'hoop_nodes', 'n_temperatures', 'T_K_min', 'T_K_max', 'volume_m3', 'min_detJ', 'n_gauss_detJ_le_0', 'tref_C'):
    print(k, rep[k])
print('d', rep['d_commands']); print('mpdata', rep['mpdata'])
