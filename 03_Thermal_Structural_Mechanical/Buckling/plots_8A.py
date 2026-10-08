# -*- coding: utf-8 -*-
"""SECTION 8A - buckling figures (RE-ANALYSIS 2026).
Data plots drawn from (a) the hand calculation (buckling_hand_results.json) and (b) the Mechanical linear-buckling
solution: load factors and corner-node mode shapes written by the APDL snippet (s8a_load_factors.csv, s8a_mode<i>.csv).
The Mechanical renders of the mode shapes are separate files in Buckling/figures/Mechanical/ (unedited exports).
Usage: python plots_8A.py [project_root] [out_dir]"""
import os, sys, json, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mode_shapes import load_mode, classify

ROOT = sys.argv[1] if len(sys.argv) > 1 else "<PROJECT_ROOT>"
OUTF = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "figures")
os.makedirs(OUTF, exist_ok=True)
BK = os.path.join(ROOT, "08_Structural_Analysis", "Buckling")
H = json.load(open(os.path.join(HERE, "buckling_hand_results.json")))
N = H["applied_load"]["applied_axial_compression_N"]
C1, C2, C3, C4, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#8a5cd1", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2.0,
                     "legend.frameon": False, "figure.dpi": 130})
FOOT = "RE-ANALYSIS 2026 - Section 8A; hand estimates from buckling_calculations.py, FE from the Mechanical linear buckling (APDL snippet tables)"


def foot(fig, txt=FOOT):
    fig.text(0.01, 0.005, txt, fontsize=7, color=MUTED)


def lf_table(case):
    p = os.path.join(BK, "Mechanical", case, "Solver_Output", "s8a_load_factors.csv")
    if not os.path.isfile(p):
        return None
    a = np.atleast_2d(np.loadtxt(p, delimiter=",", skiprows=1))
    return {int(r[0]): float(r[1]) for r in a}


FE = {c: lf_table(c) for c in ("LC2_Linear_Buckling", "LC2NS_Linear_Buckling")}
FY = 1 / 0.578   # first-yield load factor of LC2 (7B utilisation 0.578 at the peak)
res = {"FE_load_factors": FE, "modes": {}}

# ---------------- Figures 1 and 2: mode shapes 1 and 2 (lateral deflection along the duct) ----------------
for case, tag in (("LC2_Linear_Buckling", "LC2 supports (U_z = 0 on end faces, sway free)"),
                  ("LC2NS_Linear_Buckling", "sensitivity: ends also held laterally (no sway)")):
    for m in range(1, 7):
        p = os.path.join(BK, "Mechanical", case, "Solver_Output", "s8a_mode%d.csv" % m)
        if os.path.isfile(p):
            c = classify(load_mode(p))
            res["modes"].setdefault(case, {})[m] = c
for m in (1, 2):
    fig, ax = plt.subplots(1, 1, figsize=(9, 3.6))
    for case, col, lab in (("LC2_Linear_Buckling", C1, "LC2 supports (sway free)"), ("LC2NS_Linear_Buckling", C2, "no-sway sensitivity")):
        c = res["modes"].get(case, {}).get(m)
        if c is None:
            continue
        z = np.array(c["_curve"]["z_m"]) * 1e3
        w = np.array(c["_curve"]["w_norm"])
        # eigenvector sign is arbitrary: align it with the best-matching reference shape for display
        corr = c["correlation_with_reference_shapes"]
        best = max(corr, key=lambda k: abs(corr[k]))
        w = w * (1 if corr[best] >= 0 else -1)
        ax.plot(z, w, color=col, label="%s: mode %d, LF = %.4f" % (lab, m, FE[case][m]))
        ax.plot(z, np.array(c["_curve"]["ovalisation_norm"]), color=col, lw=1, ls=":",
                label="%s: cross-section ovalisation (n = 2), same scale" % lab)
    s = np.linspace(0, 1, 200)
    ax.plot(s * 600, np.cos(np.pi * s), color=MUTED, lw=1, ls="--", label="reference: guided column n = 1, cos(pi z/L)")
    ax.plot(s * 600, np.cos(2 * np.pi * s), color=MUTED, lw=1, ls="-.", label="reference: clamped no-sway / guided n = 2, cos(2 pi z/L)")
    ax.text(0.99, 0.02, "eigenvector sign and amplitude are arbitrary", transform=ax.transAxes, ha="right", fontsize=7, color=MUTED)
    ax.set_xlabel("axial position z [mm]  (inlet z = 0, outlet z = 600)")
    ax.set_ylabel("lateral deflection of the section\n(normalised eigenvector)")
    ax.set_title("Buckling mode %d - lateral deflection of the duct axis (from the FE eigenvector)" % m, loc="left", fontsize=11)
    ax.legend(fontsize=7.5, loc="lower left")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    foot(fig)
    fig.savefig(os.path.join(OUTF, "F8A_0%d_buckling_mode_%d_shape.png" % (m, m)))
    plt.close(fig)

# ---------------- Figure 3: critical-load summary ----------------
cases = H["cases"]
labels, euler, eshear, john = [], [], [], []
for c in cases:
    labels.append(c["case"].replace(" (fixed-fixed, sway free)", "\n(rotation fixed, sway free)\n= LC2 FE supports")
                  .replace(" (cold end fixed)", "\n(inlet fixed)").replace(" (hot end fixed)", "\n(outlet fixed)")
                  .replace("fixed-fixed", "fixed-fixed\n(no sway)"))
    euler.append(c["Pcr_euler_rayleigh_EIz_N"] / 1e3)
    eshear.append(c["Pcr_euler_shear_rayleigh_EIz_N"] / 1e3)
    john.append(c["johnson_hot"]["Pcr_N"] / 1e3)
fe = [FE["LC2_Linear_Buckling"][1] * N / 1e3 if FE["LC2_Linear_Buckling"] else np.nan, np.nan, np.nan, np.nan,
      FE["LC2NS_Linear_Buckling"][1] * N / 1e3 if FE["LC2NS_Linear_Buckling"] else np.nan]
y = np.arange(len(labels))
fig, ax = plt.subplots(1, 1, figsize=(10, 5.6))
hgt = 0.19
ax.barh(y - 1.5 * hgt, euler, hgt, color=C1, label="Euler, E(z) Rayleigh (elastic, hand)")
ax.barh(y - 0.5 * hgt, eshear, hgt, color="#7fb0ea", label="Euler + shear correction (hand)")
ax.barh(y + 0.5 * hgt, fe, hgt, color=C3, label="Mechanical linear buckling, mode 1 (FE, elastic)")
ax.barh(y + 1.5 * hgt, john, hgt, color=C2, label="Johnson inelastic estimate (hand, conventional)")
ax.axvline(N / 1e3, color=INK, lw=1.6)
ax.text(N / 1e3, 1.01, "applied LC2 force %.1f kN" % (N / 1e3), fontsize=8, color=INK, ha="right", transform=ax.get_xaxis_transform())
ax.axvline(FY * N / 1e3, color=MUTED, lw=1.2, ls="--")
ax.text(FY * N / 1e3, 1.01, " first yield in LC2 (x%.2f)" % FY, fontsize=8, color=MUTED, ha="left", transform=ax.get_xaxis_transform())
for yy, v in zip(y, euler):
    ax.text(v, yy - 1.5 * hgt, " %.0f" % v, va="center", fontsize=7, color=MUTED)
for yy, v in zip(y, fe):
    if np.isfinite(v):
        ax.text(v, yy + 0.5 * hgt, " %.0f" % v, va="center", fontsize=7, color=MUTED)
for yy, v in zip(y, john):
    ax.text(v, yy + 1.5 * hgt, " %.0f" % v, va="center", fontsize=7, color=MUTED)
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=8)
ax.invert_yaxis()
ax.set_xlabel("critical axial force [kN]")
ax.set_title("LC2 critical-load summary - hand estimates and FE vs the applied restrained force", loc="left", fontsize=11, pad=16)
ax.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.45, -0.12), ncol=2)
fig.tight_layout(rect=(0, 0.03, 1, 1))
foot(fig)
fig.savefig(os.path.join(OUTF, "F8A_03_critical_load_summary.png"))
plt.close(fig)

# ---------------- Figure 4: load-factor comparison ----------------
items = [
    ("FE linear buckling, LC2 supports (mode 1)", FE["LC2_Linear_Buckling"][1] if FE["LC2_Linear_Buckling"] else np.nan, C3),
    ("Euler guided K = 1, E(z)", cases[0]["LF_euler_rayleigh_EIz"], C1),
    ("Euler guided K = 1, + shear", cases[0]["LF_euler_shear_rayleigh_EIz"], "#7fb0ea"),
    ("Euler guided K = 1, hot-end E", cases[0]["LF_euler_hot_E"], "#7fb0ea"),
    ("Johnson guided / pinned (inelastic)", cases[0]["johnson_hot"]["LF"], C2),
    ("Euler pinned-pinned, E(z)", cases[1]["LF_euler_rayleigh_EIz"], C1),
    ("Johnson fixed-pinned", cases[2]["johnson_hot"]["LF"], C2),
    ("Johnson fixed-fixed (no sway)", cases[4]["johnson_hot"]["LF"], C2),
    ("FE linear buckling, no-sway sensitivity (mode 1)", FE["LC2NS_Linear_Buckling"][1] if FE["LC2NS_Linear_Buckling"] else np.nan, C3),
    ("Euler fixed-pinned, E(z)", cases[2]["LF_euler_rayleigh_EIz"], C1),
    ("Euler fixed-fixed, E(z)", cases[4]["LF_euler_rayleigh_EIz"], C1),
]
fig, ax = plt.subplots(1, 1, figsize=(10, 5.2))
yy = np.arange(len(items))
ax.barh(yy, [v for _, v, _ in items], 0.6, color=[c for _, _, c in items])
for i, (lab, v, _) in enumerate(items):
    if np.isfinite(v):
        ax.text(v, i, "  %.3f" % v, va="center", fontsize=8, color=INK)
ax.axvline(1.0, color=INK, lw=1.6)
ax.text(1.0, 1.01, "LF = 1: applied LC2 state ", fontsize=8, color=INK, ha="right", transform=ax.get_xaxis_transform())
ax.axvline(FY, color=MUTED, lw=1.2, ls="--")
ax.text(FY, 1.01, " first yield x%.2f" % FY, fontsize=8, color=MUTED, transform=ax.get_xaxis_transform())
ax.set_yticks(yy)
ax.set_yticklabels([lab for lab, _, _ in items], fontsize=8)
ax.invert_yaxis()
ax.set_xlabel("buckling load factor = critical load / applied LC2 load")
ax.set_xlim(0, max(v for _, v, _ in items if np.isfinite(v)) * 1.15)
ax.set_title("Buckling load factors (a factor above 1 is not by itself 'safe')", loc="left", fontsize=11, pad=16)
fig.tight_layout(rect=(0, 0.03, 1, 1))
foot(fig)
fig.savefig(os.path.join(OUTF, "F8A_04_load_factor_comparison.png"))
plt.close(fig)

for case in res["modes"]:
    for m in res["modes"][case]:
        res["modes"][case][m] = dict((k, v) for k, v in res["modes"][case][m].items() if not k.startswith("_"))
json.dump(res, open(os.path.join(HERE, "fe_modes_8A.json"), "w"), indent=1)
print(json.dumps(res, indent=1)[:6000])
