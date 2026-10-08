# 12C Fig. 1 - Mechanical linear buckling mode 1 (8A, corner nodes) vs LS-DYNA G6 mode 1 (12B): section lateral translation vs z.
import csv, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from lasso.dyna import D3plot
M = "<PROJECT_ROOT>/08_Structural_Analysis/Buckling/Mechanical/LC2_Linear_Buckling/Solver_Output/s8a_mode1.csv"
rows = np.array([[float(x) for x in r] for r in list(csv.reader(open(M)))[1:]])
def profile(xyz, u):
    z = np.round(xyz[:, 2], 7); zu = np.unique(z)
    T = np.array([u[z == q, :2].mean(0) for q in zu])
    w, v = np.linalg.eigh(T.T @ T); t = T @ v[:, -1]; t = t / t[np.argmax(np.abs(t))]
    if t[-1] < 0: t = -t
    return zu, t
zm, tm = profile(rows[:, 1:4], rows[:, 4:7])
d = D3plot("<PROJECT_ROOT>/15_LS_DYNA_Extension/work_12B/G6_buckle_10step/d3eigv")
X = d.arrays['node_coordinates']; U = d.arrays['node_displacement'][0] - X
zl, tl = profile(X, U)
plt.rcParams.update({'font.size': 10, 'axes.edgecolor': '#52514e', 'axes.labelcolor': '#0b0b0b', 'xtick.color': '#52514e', 'ytick.color': '#52514e'})
fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.2), gridspec_kw={'width_ratios': [1.25, 1]}, facecolor='#fcfcfb')
for a in ax: a.set_facecolor('#fcfcfb'); a.grid(color='#e4e3df', lw=0.6); [a.spines[s].set_visible(False) for s in ('top', 'right')]
zz = np.linspace(0, 0.6, 200)
ax[0].plot(zz * 1e3, np.cos(np.pi * zz / 0.6) * -1, color='#52514e', lw=1, ls=':', label='−cos(πz/L) (guided column)')
ax[0].plot(zm * 1e3, tm, color='#eb6834', lw=2, label='Mechanical 8A mode 1, λ₁ = 1.10805')
ax[0].plot(zl * 1e3, tl, color='#2a78d6', lw=2, ls='--', label='LS-DYNA 12B G6 mode 1, λ₁ = 1.109475')
ax[0].set_xlabel('axial position z [mm] (inlet face z = 0)'); ax[0].set_ylabel('normalised lateral translation of the section [–]')
ax[0].set_title('Section lateral translation, normalised to ±1', fontsize=10, loc='left')
ax[0].legend(frameon=False, fontsize=8.5, loc='upper left')
# side view of the mode shape (Mechanical, outer generators in the sway plane), exaggerated
sel = np.abs(np.hypot(rows[:, 1], rows[:, 2]) - 0.02) < 1e-6
for sgn in (1, -1):
    pass
amp = 15.0
ax[1].plot(zm * 1e3, amp * tm + 20, color='#eb6834', lw=2); ax[1].plot(zm * 1e3, amp * tm - 20, color='#eb6834', lw=2)
ax[1].plot([0, 600], [20, 20], color='#9a9993', lw=1, ls='--'); ax[1].plot([0, 600], [-20, -20], color='#9a9993', lw=1, ls='--')
ax[1].set_xlabel('z [mm]'); ax[1].set_ylabel('lateral position of outer surface [mm]')
ax[1].set_title('Side view, Mechanical mode 1 (exaggerated ×15)', fontsize=10, loc='left')
ax[1].text(330, -2, 'undeformed: dashed\nends sway in opposite\ndirections; mid-span ≈ 0', fontsize=8.5, color='#52514e')
fig.suptitle('Fig. 1 — Linear buckling mode reference (original Mechanical result; LS-DYNA 12B cross-check)', x=0.01, ha='left', fontsize=11)
fig.tight_layout(); fig.savefig('<OUTPUT_ROOT>/S12C/15_LS_DYNA_Extension/12C_Nonlinear_Buckling/plots/F1_mechanical_mode_reference.png', dpi=150)
print('corr', np.corrcoef(np.interp(zl, zm, tm), tl)[0, 1])
