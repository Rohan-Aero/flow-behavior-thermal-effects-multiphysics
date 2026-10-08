# Section 12B Gate 3 - compare restrained-bar results with the closed form sigma_z = -E(T) eps_th(T) (sigma_x = sigma_y = 0).
import os, re, json, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import importlib.util
spec = importlib.util.spec_from_file_location('m', os.path.join(HERE, '..', 'make_material_12B.py'))
src = open(os.path.join(HERE, '..', 'make_material_12B.py'), encoding='utf-8-sig').read().split('# curve points')[0]
ns = {'__file__': os.path.join(HERE, '..', 'make_material_12B.py')}; exec(src, ns)
eps_th, lin, TE, EE = ns['eps_th'], ns['lin'], ns['TE'], ns['EE']
TMAX = 562.5576399
res = {}
for v in sorted(os.listdir(os.path.join(HERE, 'bar'))):
    f = os.path.join(HERE, 'bar', v, 'elout')
    if not os.path.exists(f): continue
    txt = open(f).read()
    blocks = re.split(r'at time\s+', txt)[1:]
    rows = []
    for b in blocks:
        t = float(b.split()[0].rstrip(')'))
        m = re.search(r'\n\s+1-\s+1\s*\n\s+\d+\s+(\S+)\s+(\S+)\s+(\S+)', b)
        sx, sy, sz = (float(m.group(k)) for k in (1, 2, 3))
        Tk = 300.0 + t * (TMAX - 300.0); Tc = Tk - 273.15
        sz_cf = -lin(Tc, TE, EE) * eps_th(Tc)
        rows.append({'t': t, 'T_K': Tk, 'sz_MPa': sz / 1e6, 'sx_MPa': sx / 1e6, 'sz_closed_MPa': sz_cf / 1e6,
                     'rel_err_sz': (sz - sz_cf) / sz_cf if sz_cf else 0.0})
    res[v] = rows
    last = rows[-1]
    print(f"{v:16s} t={last['t']:.2f} T={last['T_K']:.2f}K  sz={last['sz_MPa']:.3f}  closed={last['sz_closed_MPa']:.3f}  err={100*last['rel_err_sz']:+.3f}%  sx={last['sx_MPa']:.3f}  max|err| over path={100*max(abs(r['rel_err_sz']) for r in rows[1:]):.3f}%")
json.dump(res, open(os.path.join(HERE, 'bar_results.json'), 'w'), indent=1)
