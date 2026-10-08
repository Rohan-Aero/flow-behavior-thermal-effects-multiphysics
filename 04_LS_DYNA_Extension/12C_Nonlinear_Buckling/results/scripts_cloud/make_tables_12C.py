# Builds IMPERFECTION_SENSITIVITY.csv and MECHANICAL_vs_LSDYNA.csv from analysis_12C.json (three-point study + C0 reference).
import json, csv
OUT = '<OUTPUT_ROOT>/S12C/15_LS_DYNA_Extension/12C_Nonlinear_Buckling'
A = json.load(open('analysis_12C.json'))
P_MECH, N_LC2, LAM_MECH, LAM_G6 = 608.249215, 548.9366, 1.10805, 1.109475
f = lambda v, d=1: '' if v is None else f'{v:.{d}f}'
def obs(c, a):
    if c == 'C0_A0p0':
        return ('Perfect-geometry reference (not one of the three sensitivity points). Stays straight to lambda = 1.3 (lateral <= 3e-7 mm); '
                'N passes P_cr without bifurcating; no negative-eigenvalue flag (NEGEV = 2 ignores them) -> bifurcation load not identifiable from this run')
    s = 'interior maximum of N at lambda = %.3f, then N decreases slowly while sway keeps growing' % a['lambda_at_Nmax'] if a['interior_peak'] else \
        'N still rising at the end of the analysis (lambda = 1.3); no maximum within the analysed range'
    y = (' ; elastic-validity indicator VM/S_y(T) = 1 reached at lambda = %.3f (N = %.1f kN)' % (a['lambda_first_yield_indicator'], a['N_first_yield_indicator_kN'])
         if a.get('lambda_first_yield_indicator') else ' ; VM/S_y(T) < 1 throughout')
    return 'Global guided sway (cos-shaped, ends opposite, mid-span ~0, ovalisation <= %.3f mm); %s%s' % (a['oval_max_final_mm'], s, y)
import numpy as np, pandas as pd
def sw_range(c):
    d = pd.read_csv(f'series/{c}_series.csv'); n = pd.read_csv(f'series/{c}_N_binout.csv'); N = np.interp(d.t, n.t, n.Fz_inlet_N) / 1e3; s = d.sway_end_rel_mm.values
    k = np.argmax(N); i = np.arange(len(N)); r = []
    for lo, hi, par in ((0.5, 0.95, None), (0.5, 0.95, 0), (0.5, 0.95, 1), (0.6, 0.95, None), (0.5, 0.9, None)):
        m = (N > lo * N.max()) & (N < hi * N.max()) & (i <= k) & (s > 0)
        if par is not None: m &= (i % 2 == par)
        p = np.polyfit(s[m], s[m] / N[m], 1); r.append(1 / p[0])
    return min(r), max(r)
rows = []
for c in ['C1_A0p1', 'C3_A0p6', 'C5_A1p2', 'C0_A0p0']:
    if c not in A: continue
    a = A[c]; ref = c == 'C0_A0p0'
    char = 'not identifiable (no bifurcation flagged; N_max at lambda = 1.3 is the end of the analysis, not an instability)' if ref else \
        (f"{a['N_max_kN']:.1f} kN = interior maximum of N (Southwell N_cr {a['N_southwell_kN']:.1f} kN)" if a['interior_peak'] else
         f"no maximum within lambda <= 1.3; Southwell N_cr {a['N_southwell_kN']:.1f} kN (largest attained N {a['N_max_kN']:.1f} kN)")
    rows.append({'Study role': 'reference (perfect geometry)' if ref else 'three-point study', 'Case': c,
        'Imperfection [mm]': f(a['A_mm']), 'Instability/Characteristic Load': char,
        'Max Lateral Displacement [mm] (max section translation at lambda=1.3)': f(a['lat_max_final_mm'], 3),
        'Additional relative end sway at lambda=1.3 [mm]': f(a['sway_add_final_mm'], 3),
        'Max von Mises [MPa] (nodal, end-region monitored elements, lambda<=1.3; elastic model)': f(a['vm_max_MPa_overall']),
        'Max von Mises at lambda=1 [MPa]': f(a['vm_at_lambda1_MPa']),
        'Key Observation': obs(c, a),
        'N_max [kN]': f(a['N_max_kN'], 2), 'lambda at N_max': f(a['lambda_at_Nmax'], 3), 'Interior peak': a['interior_peak'],
        'N at lambda=1.3 [kN]': f(a['N_final_kN'], 2), 'Southwell N_cr [kN]': f(a.get('N_southwell_kN'), 2),
        'Southwell R2': f(a.get('southwell_R2'), 5), 'Southwell range over 5 fit-window variants [kN]': '' if ref else '%.1f - %.1f' % sw_range(c), 'Southwell w0 estimate [mm] (imposed 2A)': f(a.get('southwell_w0_est_mm'), 3),
        'Onset lambda (N 1% below perfect path)': f(a.get('lambda_onset_1pct'), 3), 'Onset N [kN]': f(a.get('N_onset_1pct_kN'), 1),
        'lambda at VM/S_y(T)=1': f(a.get('lambda_first_yield_indicator'), 4), 'N at VM/S_y(T)=1 [kN]': f(a.get('N_first_yield_indicator_kN'), 1),
        'max VM/S_y(T)': f(a.get('util_max_overall'), 3)})
with open(f'{OUT}/IMPERFECTION_SENSITIVITY.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
m = [['Quantity', 'Source', 'Value [kN]', 'Ratio to Mechanical P_cr', 'Difference to Mechanical P_cr [%]', 'Note']]
add = lambda q, s, v, n: m.append([q, s, f'{v:.2f}', f'{v / P_MECH:.4f}', f'{100 * (v / P_MECH - 1):+.2f}', n])
add('Linear eigenvalue critical load P_cr = lambda1 x 548.94 kN (lambda1 = 1.10805)', 'Original project: Mechanical 8A (unchanged)', P_MECH, 'reference value of the original project')
add('Linear eigenvalue critical load (lambda1 = 1.109475)', 'LS-DYNA 12B G6 (extension)', LAM_G6 * N_LC2, 'linear buckling cross-check; +0.13 % raw, -0.64 % kinematics-corrected')
add('LC2 applied axial compression (Mechanical reaction, lambda = 1)', 'Original project: Mechanical (unchanged)', N_LC2, 'lambda1 = P_cr / 548.94 kN = 1.108 is a load multiplier, not a factor of safety')
if 'C0_A0p0' in A:
    add('Axial compression at lambda = 1, perfect geometry', 'LS-DYNA 12C C0 (reference)', 553.246, 'equals 12B G5 (553.247 kN); +0.79 % vs Mechanical = large-deformation kinematics (12B D-105)')
for c in ['C1_A0p1', 'C3_A0p6', 'C5_A1p2']:
    if c not in A: continue
    a = A[c]
    add(f"Maximum attained axial compression, A = {a['A_mm']:.1f} mm", 'LS-DYNA 12C nonlinear (extension)', a['N_max_kN'],
        f"at lambda = {a['lambda_at_Nmax']:.3f}; " + ('interior maximum' if a['interior_peak'] else 'still rising at lambda = 1.3 (end of analysis)'))
    add(f"Southwell estimate of the critical load, A = {a['A_mm']:.1f} mm", 'LS-DYNA 12C nonlinear (extension)', a['N_southwell_kN'],
        f"fit over N in [0.5, 0.95] N_max, R2 = {a['southwell_R2']:.5f}, w0 estimate {a['southwell_w0_est_mm']:.3f} mm vs imposed {2 * a['A_mm']:.1f} mm")
with open(f'{OUT}/MECHANICAL_vs_LSDYNA.csv', 'w', newline='') as fh: csv.writer(fh).writerows(m)
print(len(rows), 'sensitivity rows;', len(m) - 1, 'comparison rows')
