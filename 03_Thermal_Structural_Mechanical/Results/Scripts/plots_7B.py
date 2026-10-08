# -*- coding: utf-8 -*-
"""SECTION 7B - plots drawn from the solved 7B model data (RE-ANALYSIS 2026).
Every curve is read from out/axial_profile_*.csv or out/post_7B_results.json, which post_7B.py computes from the MAPDL nodal
table (s7b_nodal.csv) written by the solve. These are data plots, not Mechanical screenshots; the Mechanical renders are in
08_Structural_Analysis/Figures/Mechanical."""
import os, json, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.environ.get("S7B_OUT", "<OUTPUT_ROOT>/S7B/Post/out")
FIG = os.environ.get("S7B_FIG", "<OUTPUT_ROOT>/S7B/Post/fig")
os.makedirs(FIG, exist_ok=True)
R = json.load(open(os.path.join(OUT, "post_7B_results.json")))
C1, C2, C3, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2.0,
                     "legend.frameon": False, "figure.dpi": 130})
FOOT = "RE-ANALYSIS 2026 - plotted from the Section 7B Mechanical/MAPDL solution (s7b_nodal.csv, corner-node stresses)"


def prof(c):
    rows = list(csv.DictReader(open(os.path.join(OUT, "axial_profile_%s.csv" % c))))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


P = {c: prof(c) for c in ("LC1", "LC2", "LC2P")}


def foot(fig):
    fig.text(0.01, 0.005, FOOT, fontsize=7, color=MUTED)


def axial(case, title, fname, panels):
    p = P[case]
    z = p["z_m"] * 1e3
    fig, axs = plt.subplots(len(panels), 1, figsize=(9, 2.35 * len(panels)), sharex=True)
    for ax, (ylab, series) in zip(axs, panels):
        for lab, key, scale, col in series:
            ax.plot(z, p[key] * scale, color=col, label=lab)
        ax.set_ylabel(ylab)
        ax.legend(loc="best", fontsize=8)
    axs[-1].set_xlabel("axial position z [mm]  (inlet z = 0, outlet z = 600)")
    axs[0].set_title(title, loc="left", fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    foot(fig)
    fig.savefig(os.path.join(FIG, fname))
    plt.close(fig)


axial("LC1", "LC1 free expansion - axial profiles (theta-averaged, corner planes)", "F7B_01_LC1_axial_profiles.png", [
    ("temperature [K]", [("bore r = 10 mm", "T_bore_K", 1, C1), ("outer r = 20 mm", "T_outer_K", 1, C2), ("section mean", "T_mean_K", 1, C3)]),
    ("axial displacement u_z [mm]", [("section mean", "uz_mean_m", 1e3, C1)]),
    ("von Mises [MPa]", [("bore", "seqv_bore_Pa", 1e-6, C1), ("outer", "seqv_outer_Pa", 1e-6, C2)]),
])
axial("LC2", "LC2 axially restrained - axial profiles (theta-averaged, corner planes)", "F7B_02_LC2_axial_profiles.png", [
    ("temperature [K]", [("bore r = 10 mm", "T_bore_K", 1, C1), ("outer r = 20 mm", "T_outer_K", 1, C2), ("section mean", "T_mean_K", 1, C3)]),
    ("axial displacement u_z [mm]", [("section mean", "uz_mean_m", 1e3, C1)]),
    ("von Mises [MPa]", [("bore", "seqv_bore_Pa", 1e-6, C1), ("outer", "seqv_outer_Pa", 1e-6, C2)]),
    ("axial stress s_z [MPa]", [("bore", "sz_bore_Pa", 1e-6, C1), ("outer", "sz_outer_Pa", 1e-6, C2)]),
])

# inlet-zone detail (element boundaries = corner planes)
NE = R["near_end"]
fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
for ax, keys, title in ((axs[0], ("LC1_bore_inlet_vm", "LC1_outer_inlet_vm"), "LC1 - first 12 element planes at the inlet"),
                        (axs[1], ("LC2_outer_inlet_vm", "LC2_bore_inlet_vm"), "LC2 - first 12 element planes at the inlet")):
    for k, col, lab in ((keys[0], C1 if "bore" in keys[0] else C2, keys[0].split("_")[1]), (keys[1], C1 if "bore" in keys[1] else C2, keys[1].split("_")[1])):
        a = np.array(NE[k])
        ax.plot(a[:, 0], a[:, 1] / 1e6, color=col, marker="o", markersize=4, label=lab + " (max over theta)")
    ax.axvspan(0, 11, color=GRID, alpha=0.6, lw=0)
    ax.text(5.5, 0.97, "F-035 zone\n(T transfer uncertainty)", ha="center", va="top", fontsize=7, color=MUTED,
            transform=ax.get_xaxis_transform())
    ax.set_xlabel("z [mm]  (markers = element corner planes)")
    ax.set_ylabel("von Mises [MPa]")
    ax.set_title(title, loc="left", fontsize=10)
    ax.legend(fontsize=8)
fig.tight_layout(rect=(0, 0.03, 1, 1))
foot(fig)
fig.savefig(os.path.join(FIG, "F7B_03_inlet_zone_detail.png"))
plt.close(fig)

# pressure effect: LC2P - LC2 von Mises along z (full-precision tables)
z = P["LC2"]["z_m"] * 1e3
fig, ax = plt.subplots(figsize=(9, 3.4))
for key, col, lab in (("seqv_bore_Pa", C1, "bore"), ("seqv_outer_Pa", C2, "outer")):
    ax.plot(z, P["LC2P"][key] - P["LC2"][key], color=col, label=lab)
pr = R["pressure"]
ax.set_ylabel("von Mises change [Pa]")
ax.set_xlabel("z [mm]")
ax.set_title("Pressure check: von Mises of LC2P (thermal + 443.41 Pa) minus LC2 (thermal only)", loc="left", fontsize=10)
ax.text(0.99, 0.95, "max von Mises: LC2 %.6f MPa, LC2P %.6f MPa\ndifference +%.0f Pa (+%.1e %%)" % (pr["vm_max_LC2_Pa"] / 1e6, pr["vm_max_LC2P_Pa"] / 1e6, pr["vm_max_diff_Pa"], pr["vm_max_diff_pct"]),
        transform=ax.transAxes, ha="right", va="top", fontsize=8, color=INK)
ax.legend(fontsize=8, loc="upper center", ncol=2)
ax.text(0.01, 0.03, "theta-averaged; point-to-point scatter of about +/-15 Pa (2.5e-8 of 590 MPa) is round-off between two separate solves",
        transform=ax.transAxes, fontsize=7, color=MUTED)
fig.tight_layout(rect=(0, 0.04, 1, 1))
foot(fig)
fig.savefig(os.path.join(FIG, "F7B_04_pressure_effect.png"))
plt.close(fig)

# expansion comparison (horizontal bars, one axis)
ex = R["LC1_expansion"]
labs = ["Section 2 analytical\n(uniform 254.7 K rise)", "estimate: CFD volume-mean T\n(525.5 K, one alpha)", "independent integral of\nthermal strain over the field", "Mechanical LC1\n(mean outlet-face u_z)"]
vals = [ex["section2_analytical_m"], ex["simple_estimate_CFD_volume_mean_T_m"], ex["independent_integral_E_weighted_m"], ex["FE_dL_mean_face_m"]]
fig, ax = plt.subplots(figsize=(8, 3.2))
cols = [MUTED, C3, C1, C2]
ax.barh(range(4), [v * 1e3 for v in vals], color=cols, height=0.55)
for i, v in enumerate(vals):
    ax.text(v * 1e3 + 0.01, i, "%.4f mm" % (v * 1e3), va="center", fontsize=8, color=INK)
ax.set_yticks(range(4))
ax.set_yticklabels(labs, fontsize=8)
ax.set_xlim(0, 2.4)
ax.set_xlabel("free axial growth of the 600 mm duct [mm]")
ax.set_title("LC1 free thermal expansion - FE vs independent checks", loc="left", fontsize=10)
ax.grid(axis="y", visible=False)
fig.tight_layout(rect=(0, 0.04, 1, 1))
foot(fig)
fig.savefig(os.path.join(FIG, "F7B_05_expansion_comparison.png"))
plt.close(fig)

# equilibrium: section force N(z) (two panels, different scales)
fig, axs = plt.subplots(1, 2, figsize=(10, 3.2))
axs[0].plot(z, P["LC2"]["N_z_N"] / 1e3, color=C2, label="section force from s_z (corner-node trapezoid)")
fz = R["reactions"]["LC2"]["groups"]["inlet_end_face_z0"]["Fz"]
axs[0].axhline(-fz / 1e3, color=INK, lw=1, ls="--", label="-(inlet reaction) = %.1f kN" % (-fz / 1e3))
axs[0].set_ylim(-560, -540)
axs[0].set_title("LC2 axial force along the duct", loc="left", fontsize=10)
axs[0].set_ylabel("N(z) [kN]")
axs[0].set_xlabel("z [mm]")
axs[0].legend(fontsize=7, loc="lower right")
axs[1].plot(z, P["LC1"]["N_z_N"], color=C1, label="LC1 section force from s_z")
axs[1].set_title("LC1 axial force along the duct (should be ~0)", loc="left", fontsize=10)
axs[1].set_ylabel("N(z) [N]")
axs[1].set_xlabel("z [mm]")
axs[1].legend(fontsize=7)
fig.tight_layout(rect=(0, 0.04, 1, 1))
foot(fig)
fig.savefig(os.path.join(FIG, "F7B_06_section_force_equilibrium.png"))
plt.close(fig)
print(sorted(os.listdir(FIG)))
