# 12C figures F2-F4, F7 from the extracted series (actual LS-DYNA values) + analysis_12C.json.
import json, csv, os, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT = '<OUTPUT_ROOT>/S12C/15_LS_DYNA_Extension/12C_Nonlinear_Buckling/plots'
A = json.load(open('analysis_12C.json')); P_MECH = 608.249; N_LC2 = 548.937; LAM_MECH = 1.10805; LAM_G6 = 1.109475
COL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']; INK = '#0b0b0b'; INK2 = '#52514e'; SURF = '#fcfcfb'
cases = [('C0_A0p0', 0.0), ('C1_A0p1', 0.1), ('C3_A0p6', 0.6), ('C5_A1p2', 1.2)]   # three-point study C1/C3/C5 (scope set by user 2026-10-07) + C0 perfect-geometry reference (completed before the scope change)
plt.rcParams.update({'font.size': 10, 'axes.edgecolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2})
def S(c):
    rows = list(csv.DictReader(open(f'series/{c}_series.csv')))
    return {k: np.array([float(r[k]) if r[k] != '' else np.nan for r in rows]) for k in rows[0]}
def N_of(c, s):
    f = f'series/{c}_N_binout.csv'
    if os.path.exists(f):
        d = np.loadtxt(f, delimiter=',', skiprows=1); return np.interp(s['t'], d[:, 0], d[:, 1]) / 1e3
    return s['Fz_in_N'] / 1e3
def style(a):
    a.set_facecolor(SURF); a.grid(color='#e4e3df', lw=0.6)
    for sp in ('top', 'right'): a.spines[sp].set_visible(False)
avail = [(c, a) for c, a in cases if os.path.exists(f'series/{c}_series.csv')]
CC = {'C0_A0p0': INK2, 'C1_A0p1': COL[0], 'C3_A0p6': COL[1], 'C5_A1p2': COL[2]}
LBL = lambda c, a: f'{a:.1f} mm (perfect reference)' if a == 0 else f'{a:.1f} mm ({c[:2]})'
# ---- F2: perfect case ----
if os.path.exists('series/C0_A0p0_series.csv'):
    s = S('C0_A0p0'); N = N_of('C0_A0p0', s)
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.0), facecolor=SURF)
    for a in ax: style(a)
    ax[0].plot(s['lambda'], N, color=COL[0], lw=2, marker='o', ms=3, label='LS-DYNA, perfect geometry (A = 0)')
    ax[0].axhline(P_MECH, color=INK2, ls='--', lw=1); ax[0].text(0.02, P_MECH + 8, 'Mechanical linear P_cr = 608.2 kN', color=INK2, fontsize=8.5)
    ax[0].axvline(LAM_MECH, color=INK2, ls=':', lw=1); ax[0].text(LAM_MECH + 0.005, 60, 'λ₁ Mechanical = 1.108', color=INK2, fontsize=8.5, rotation=90)
    ax[0].set_xlabel('load parameter λ (scales T − 300 K)'); ax[0].set_ylabel('axial compression N (inlet reaction) [kN]')
    ax[0].set_title('Axial force along the path', fontsize=10, loc='left')
    ax[1].plot(s['lambda'], s['lat_max_mm'], color=COL[0], lw=2, marker='o', ms=3)
    ax[1].set_xlabel('load parameter λ'); ax[1].set_ylabel('max lateral section translation [mm]')
    ax[1].set_title('Lateral response (perfect geometry): output-resolution noise only,\n< 3e-7 mm at every λ — no bifurcation develops', fontsize=9.5, loc='left')
    fig.suptitle('Fig. 2 — LS-DYNA nonlinear response, perfect geometry 0.0 mm (reference run C0, additional analysis 12C)', x=0.01, ha='left', fontsize=11)
    fig.tight_layout(); fig.savefig(f'{OUT}/F2_lsdyna_0p0mm_response.png', dpi=150); plt.close(fig)
# ---- F3: load vs lateral displacement, all amplitudes (+ normalised) ----
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4), facecolor=SURF)
for a in ax: style(a)
for i, (c, amp) in enumerate(avail):
    s = S(c); N = N_of(c, s); tot = s['sway_end_rel_mm'] + 2 * amp
    ax[0].plot(tot, N, color=CC[c], lw=2, ls=':' if amp == 0 else '-', label=LBL(c, amp))
    ax[0].text(tot[-1], N[-1], f' {amp:.1f}', color=INK, fontsize=8, va='center')
    if amp > 0:
        ax[1].plot(s['sway_end_rel_mm'] / (2 * amp), N / P_MECH, color=CC[c], lw=2, label=LBL(c, amp))
ax[0].axhline(P_MECH, color=INK2, ls='--', lw=1); ax[0].text(0.5, P_MECH + 6, 'Mechanical linear P_cr 608.2 kN', color=INK2, fontsize=8.5)
ax[0].axhline(N_LC2, color=INK2, ls=':', lw=1); ax[0].text(0.5, N_LC2 - 22, 'LC2 load 548.9 kN', color=INK2, fontsize=8.5)
ax[0].set_xlabel('total relative sway of the end faces, initial + additional [mm]'); ax[0].set_ylabel('axial compression N [kN]')
ax[0].set_title('Load – lateral displacement', fontsize=10, loc='left'); ax[0].legend(title='imperfection', frameon=False, fontsize=8)
ax[1].axhline(1.0, color=INK2, ls='--', lw=1); ax[1].set_xscale('log')
ax[1].set_xlabel('additional sway / initial sway  δ / w₀ [–] (log)'); ax[1].set_ylabel('N / P_cr,Mechanical [–]')
ax[1].set_title('Normalised', fontsize=10, loc='left'); ax[1].legend(title='imperfection', frameon=False, fontsize=8)
fig.suptitle('Fig. 3 — Load – lateral displacement, three-point imperfection study C1/C3/C5 + perfect reference (LS-DYNA 12C, extension)', x=0.01, ha='left', fontsize=11)
fig.tight_layout(); fig.savefig(f'{OUT}/F3_load_lateral_all.png', dpi=150); plt.close(fig)
# ---- F4: amplitude vs characteristic loads ----
fig, ax = plt.subplots(figsize=(6.8, 4.2), facecolor=SURF); style(ax)
imp = [(c, a) for c, a in avail if a > 0]; amps = [A[c]['A_mm'] for c, _ in imp]
ax.plot(amps, [A[c]['N_max_kN'] for c, _ in imp], color=COL[0], lw=2, marker='o', ms=6, label='maximum attained N (λ ≤ 1.3)')
for c, a in imp: ax.annotate('interior max' if A[c]['interior_peak'] else 'end of run,\nstill rising', (a, A[c]['N_max_kN']), textcoords='offset points', xytext=(6, -18), fontsize=7.5, color=INK2)
sw = [(A[c]['A_mm'], A[c].get('N_southwell_kN')) for c, _ in imp if A[c].get('N_southwell_kN')]
if sw: ax.plot([p[0] for p in sw], [p[1] for p in sw], color=COL[1], lw=2, marker='s', ms=6, label='Southwell estimate of N_cr')
on = [(A[c]['A_mm'], A[c].get('N_onset_1pct_kN')) for c, _ in imp if A[c].get('N_onset_1pct_kN')]
if on: ax.plot([p[0] for p in on], [p[1] for p in on], color=COL[2], lw=2, marker='^', ms=6, label='onset: N 1 % below perfect path')
ax.axhline(P_MECH, color=INK2, ls='--', lw=1); ax.text(0.62, P_MECH + 8, 'Mechanical linear P_cr 608.2 kN', color=INK2, fontsize=8.5); ax.set_xlim(0, 1.3)
ax.set_xlabel('imperfection amplitude A [mm] (numerical sensitivity values)'); ax.set_ylabel('axial compression [kN]')
ax.legend(frameon=False, fontsize=8.5); ax.set_title('Fig. 4 — Imperfection amplitude vs characteristic loads (three points)', fontsize=11, loc='left')
fig.tight_layout(); fig.savefig(f'{OUT}/F4_amplitude_vs_characteristic_load.png', dpi=150); plt.close(fig)
# ---- F7: Mechanical vs nonlinear ----
fig, ax = plt.subplots(figsize=(8.5, 4.2), facecolor=SURF); style(ax)
imp7 = [(c, a) for c, a in avail if a > 0]
lab = ['Mechanical\nlinear (8A)', 'LS-DYNA\nlinear (12B G6)'] + [f'{A[c]["A_mm"]:.1f} mm {c[:2]}\n' + ('interior max' if A[c]['interior_peak'] else 'at λ = 1.3') for c, _ in imp7]
val = [P_MECH, LAM_G6 * N_LC2] + [A[c]['N_max_kN'] for c, _ in imp7]
cols = [INK2, '#9a9993'] + [CC[c] for c, _ in imp7]
b = ax.bar(range(len(val)), val, color=cols, width=0.6)
for k, v in enumerate(val): ax.text(k, v + 4, f'{v:.0f}', ha='center', fontsize=8.5, color=INK)
ax.set_xticks(range(len(val))); ax.set_xticklabels(lab, fontsize=8)
for k, (c, _) in enumerate(imp7): ax.plot(k + 2, A[c]['N_southwell_kN'], marker='_', ms=28, mew=2.5, color=INK); ax.text(k + 2.33, A[c]['N_southwell_kN'], f"Southwell {A[c]['N_southwell_kN']:.0f}", fontsize=7.5, va='center', color=INK)
ax.set_ylim(min(val) * 0.9, max(val) * 1.04); ax.set_ylabel('critical / maximum axial compression [kN]')
ax.set_title('Fig. 7 — Mechanical linear P_cr vs LS-DYNA nonlinear maximum attained N (not safety factors)', fontsize=10.5, loc='left')
fig.tight_layout(); fig.savefig(f'{OUT}/F7_mechanical_vs_nonlinear.png', dpi=150); plt.close(fig)
print('figures written for', [c for c, _ in avail])
# ---- F8: three-case comparison of peak stress and lateral displacement along the path ----
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), facecolor=SURF)
for a in ax: style(a)
for c, amp in avail:
    s = S(c); ok = ~np.isnan(s['vm_max_MPa'])
    ax[0].plot(s['lambda'][ok], s['vm_max_MPa'][ok], color=CC[c], lw=2, ls=':' if amp == 0 else '-', label=LBL(c, amp))
    ly = A[c].get('lambda_first_yield_indicator')
    if ly: ax[0].plot([ly], [np.interp(ly, s['lambda'][ok], s['vm_max_MPa'][ok])], 'o', color=CC[c], ms=6)
    if amp > 0: ax[1].plot(s['lambda'], s['lat_max_mm'], color=CC[c], lw=2, label=LBL(c, amp))
ax[0].axhspan(1000, 1060, color='#e4e3df', alpha=0.8, lw=0); ax[0].text(0.02, 1075, 'S_y(T) range 1000–1060 MPa (VDM 4127)', color=INK2, fontsize=8.5)
ax[0].set_xlabel('load parameter λ'); ax[0].set_ylabel('max von Mises, monitored end regions [MPa]')
ax[0].set_title('Peak stress (dots: VM / S_y(T) = 1 at the peak node)', fontsize=10, loc='left'); ax[0].legend(frameon=False, fontsize=8)
ax[1].axvline(LAM_MECH, color=INK2, ls=':', lw=1); ax[1].text(LAM_MECH - 0.01, 0.5, 'λ₁ Mechanical 1.108', color=INK2, fontsize=8.5, rotation=90, ha='right')
ax[1].set_xlabel('load parameter λ'); ax[1].set_ylabel('max lateral section translation [mm]')
ax[1].set_title('Lateral displacement (end faces)', fontsize=10, loc='left'); ax[1].legend(frameon=False, fontsize=8)
fig.suptitle('Fig. 8 — Three-point study: peak stress and lateral displacement vs load parameter (elastic model; values above S_y(T) not physical)', x=0.01, ha='left', fontsize=10.5)
fig.tight_layout(); fig.savefig(f'{OUT}/F8_three_case_stress_displacement.png', dpi=150); plt.close(fig)
