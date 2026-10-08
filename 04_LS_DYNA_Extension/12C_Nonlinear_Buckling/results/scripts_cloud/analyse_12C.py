# Section 12C - combine per-case series (device post_12C_case.py) + binout reactions -> characteristic loads, tables.
import json, csv, os, glob, math
import numpy as np
from lasso.dyna import Binout
SER = 'series'; BIN = 'binout'
P_MECH = 608.249215   # kN, 8A: 1.10805 x 548.9366
N_LC2 = 548.9366      # kN
cases = [('C0_A0p0', 0.0), ('C1_A0p1', 0.1), ('C3_A0p6', 0.6), ('C5_A1p2', 1.2)]   # three-point study C1/C3/C5 (scope set by user 2026-10-07) + C0 perfect-geometry reference (completed before the scope change)
import sys
OUTJ = 'analysis_12C.json'
if len(sys.argv) > 2:  # single extra case, e.g. an archived incomplete attempt or N1
    cases = [(sys.argv[1], float(sys.argv[2]))]; OUTJ = f'analysis_{sys.argv[1]}.json'
Z = {}
for l in open("<PROJECT_ROOT>/15_LS_DYNA_Extension/work_12B/G4_import/model/nodes.k"):
    if l[:1].isdigit():
        a = l.split(','); Z[int(a[0])] = float(a[3])
def read_series(c):
    rows = list(csv.DictReader(open(f'{SER}/{c}_series.csv')))
    out = {k: np.array([float(r[k]) if r.get(k) not in (None, '') else np.nan for r in rows]) for k in rows[0]}
    return out
def binreac(c):
    f = f'{BIN}/{c}/binout'
    if not os.path.exists(f): return None
    b = Binout(f); t = b.read('spcforc', 'time'); ids = b.read('spcforc', 'force_ids'); fz = b.read('spcforc', 'z_force')
    inl = np.array([abs(Z[i]) < 1e-9 for i in ids]); out = np.array([abs(Z[i] - 0.6) < 1e-9 for i in ids])
    o = {'t': t, 'Fin': fz[:, inl].sum(1), 'Fout': fz[:, out].sum(1), 'res': b.read('spcforc', 'z_resultant')}
    np.savetxt(f'{SER}/{c}_N_binout.csv', np.column_stack([o['t'], o['Fin'], o['Fout'], o['res']]), delimiter=',',
               header='t,Fz_inlet_N,Fz_outlet_N,z_resultant_all_spc_N', comments='', fmt='%.10g')
    return o
lamf = lambda t: np.interp(t, [0, 0.4, 0.8, 0.9], [0, 1.0, 1.2, 1.3])
res = {}
base = None
for c, A in cases:
    if not os.path.exists(f'{SER}/{c}_series.csv'): continue
    s = read_series(c); br = binreac(c)
    if br is not None:
        N = np.interp(s['t'], br['t'], br['Fin']) / 1e3; bal = np.max(np.abs(br['Fin'] + br['Fout']) / np.maximum(np.abs(br['Fin']), 1))
    else:
        N = s['Fz_in_N'] / 1e3; bal = np.nan
    lam = s['lambda']; dl = s['sway_end_rel_mm']          # additional relative sway of the end faces (w.r.t. own initial geometry)
    w0_rel = 2.0 * A                                     # initial relative end offset of the mode (outlet +A, inlet -A at max)
    r = {'A_mm': A, 'lambda': lam, 'N_kN': N, 'sway_add_mm': dl, 'sway_tot_mm': dl + w0_rel, 'bal_max_rel': float(bal)}
    if c == 'C0_A0p0': base = (lam, N)
    res[c] = (r, s)
summary = {}
for c, (r, s) in res.items():
    lam, N, d = r['lambda'], r['N_kN'], r['sway_add_mm']
    k = int(np.nanargmax(N)); Nmax = float(N[k]); lam_at = float(lam[k])
    interior_peak = bool(k < len(N) - 1 and N[-1] < Nmax * 0.999)
    out = {'A_mm': r['A_mm'], 'N_max_kN': Nmax, 'lambda_at_Nmax': lam_at, 'interior_peak': interior_peak, 'N_final_kN': float(N[-1]),
           'lambda_final': float(lam[-1]), 'sway_add_final_mm': float(d[-1]), 'lat_max_final_mm': float(s['lat_max_mm'][-1]),
           'reaction_balance_max_rel': r['bal_max_rel']}
    # onset of nonlinear response: N_imperfect / N_perfect < 0.99
    if base is not None and c != 'C0_A0p0':
        Np = np.interp(lam, base[0], base[1]); ratio = N / np.where(Np > 0, Np, np.nan)
        idx = np.where((lam > 0.05) & (ratio < 0.99))[0]
        out['lambda_onset_1pct'] = float(lam[idx[0]]) if len(idx) else None
        out['N_onset_1pct_kN'] = float(N[idx[0]]) if len(idx) else None
    # Southwell: d/N vs d linear for the pre-critical branch N in [0.5, 0.95] N_max (increasing part only)
    if r['A_mm'] > 0:
        m = (N > 0.5 * Nmax) & (N < 0.95 * Nmax) & (np.arange(len(N)) <= k) & (d > 0)
        if m.sum() >= 4:
            x = d[m]; y = d[m] / N[m]; p = np.polyfit(x, y, 1); yh = np.polyval(p, x)
            r2 = 1 - ((y - yh) ** 2).sum() / ((y - y.mean()) ** 2).sum()
            out.update({'N_southwell_kN': float(1 / p[0]), 'southwell_R2': float(r2), 'southwell_n': int(m.sum()),
                        'southwell_w0_est_mm': float(p[1] / p[0])})
    # stress along the path
    vm = s.get('vm_max_MPa'); ut = s.get('util_max')
    if vm is not None:
        ok = ~np.isnan(vm)
        out['vm_max_MPa_overall'] = float(np.nanmax(vm)); out['vm_max_lambda'] = float(lam[ok][np.nanargmax(vm[ok])])
        out['vm_at_lambda1_MPa'] = float(np.interp(1.0, lam[ok], vm[ok]))
        out['vm_at_Nmax_MPa'] = float(np.interp(lam_at, lam[ok], vm[ok]))
        u = ut[ok]; l2 = lam[ok]; j = np.where(u >= 1.0)[0]
        if len(j):
            j0 = j[0]; lam_y = float(np.interp(1.0, [u[j0 - 1], u[j0]], [l2[j0 - 1], l2[j0]])) if j0 > 0 else float(l2[j0])
            out['lambda_first_yield_indicator'] = lam_y
            out['N_first_yield_indicator_kN'] = float(np.interp(lam_y, lam, N))
        else:
            out['lambda_first_yield_indicator'] = None
        out['util_max_overall'] = float(np.nanmax(ut))
        out['vm_max_location_final'] = {'z_m': float(s['vm_max_z_m'][ok][-1]), 'r_m': float(s['vm_max_r_m'][ok][-1]), 'T_K': float(s['vm_max_T_K'][ok][-1])}
    out['oval_max_final_mm'] = float(s['oval_max_mm'][-1]); out['lat_mid_final_mm'] = float(s['lat_mid_mm'][-1])
    summary[c] = out
json.dump(summary, open(OUTJ, 'w'), indent=1)
for c, o in summary.items(): print(c, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in o.items() if k != 'vm_max_location_final'})
