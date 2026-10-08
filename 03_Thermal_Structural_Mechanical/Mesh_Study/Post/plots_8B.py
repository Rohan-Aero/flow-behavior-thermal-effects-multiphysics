# -*- coding: utf-8 -*-
"""SECTION 8B - mesh-study figures (RE-ANALYSIS 2026). Every curve/point is read from out/post_8B_results.json,
which post_8B.py computes from the solver tables of the solved meshes. Figure 1 and part of figure 8 assemble the
unedited Mechanical renders exported by mech_meshstudy_8B.py (Mesh_Study/figures/Mechanical)."""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out")
FIG = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "fig")
REND = sys.argv[3] if len(sys.argv) > 3 else "<PROJECT_ROOT>/08_Structural_Analysis/Mesh_Study/figures/Mechanical"
os.makedirs(FIG, exist_ok=True)
R = json.load(open(os.path.join(OUT, "post_8B_results.json")))
M = R["meshes"]
C1, C2, C3, C4, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#8a5cd1", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2.0,
                     "legend.frameon": False, "figure.dpi": 130})
FOOT = "RE-ANALYSIS 2026 - Section 8B; values from the solved Mechanical/MAPDL models of each mesh (APDL snippet tables)"
FAM = [t for t in ("XC", "C", "B") if t in M]
EXTRA = [t for t in ("FR", "FA", "FC", "IL") if t in M]
NE = {t: M[t]["divisions"]["circumferential"] * M[t]["divisions"]["through_wall"] * M[t]["divisions"]["axial"] for t in M if t != "B_official"}
H = {t: (NE["B"] / NE[t]) ** (1 / 3) for t in NE}          # relative element size (baseline = 1)
STYLE = {"FR": ("s", C2, "FR: through-wall 6 (licence limit)"), "FA": ("^", C3, "FA: axial 152 (licence limit)"),
         "FC": ("v", "#c4a000", "FC: circumferential 42 (licence limit)"),
         "IL": ("D", C4, "IL: inlet bias 8 (local check)")}
LBL = {"XC": "XC 21x3x76", "C": "C 27x4x98", "B": "B 36x5x130", "FR": "FR 36x6x130", "FA": "FA 36x5x152", "FC": "FC 42x5x130", "IL": "IL 36x5x130 b8"}


def foot(fig):
    fig.text(0.01, 0.005, FOOT, fontsize=7, color=MUTED)


def getv(t, keys):
    v = M.get(t)
    for k in keys:
        if v is None:
            return None
        v = v.get(k) if isinstance(v, dict) else None
    return v


LEG = {"LC2 max von Mises [Pa]": "upper left", "LC1 mid-span bore hoop stress [Pa]": "center left", "lambda_1": "lower right",
       "critical buckling load [N]": "lower right", "LC2 max von Mises 15-585 mm [Pa]": "upper center"}
NLOC = {"LC1 mid-span bore hoop stress [Pa]": (0.98, 0.84, "right"), "LC1 max von Mises [Pa]": (0.02, 0.45, "left"),
        "LC2 max von Mises [Pa]": (0.98, 0.02, "right")}


def conv_panel(ax, keys, scale, ylabel, title, extrap_name=None, note=None, ref=None):
    xs = [H[t] for t in FAM]; ys = [getv(t, keys) * scale for t in FAM]
    ax.plot(xs, ys, "-o", color=C1, label="systematic family XC-C-B (r = 1.30)")
    for t, x, y in zip(FAM, xs, ys):
        ax.annotate(t, (x, y), textcoords="offset points", xytext=(4, 5), fontsize=8, color=C1)
    for t in EXTRA:
        v = getv(t, keys)
        if v is None:
            continue
        mk, col, lab = STYLE[t]
        ax.plot([H[t]], [v * scale], mk, color=col, ms=7, label=lab)
    if extrap_name and extrap_name in R["family_assessment"]:
        fa = R["family_assessment"][extrap_name]
        if fa.get("extrapolated") is not None:
            ax.axhline(fa["extrapolated"] * scale, color=MUTED, lw=1, ls="--", label="Richardson extrapolation of XC-C-B (h -> 0)")
    if ref is not None:
        ax.axhline(ref[0], color=INK, lw=1.2, ls=":", label=ref[1])
    if note:
        nx, ny, ha = NLOC.get(extrap_name, (0.02, 0.02, "left"))
        ax.text(nx, ny, note, transform=ax.transAxes, fontsize=7, color=MUTED, va="bottom", ha=ha)
    ax.ticklabel_format(axis="y", useOffset=False, style="plain")
    b = getv("B", keys) * scale
    ax2 = ax.secondary_yaxis("right", functions=(lambda y: (y / b - 1) * 100, lambda p: b * (1 + p / 100)))
    ax2.set_ylabel("change vs baseline [%]", color=MUTED, fontsize=8)
    ax.set_xlabel("relative element size h/h_B = (N_elem,B / N_elem)^(1/3)")
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left", fontsize=10)
    ax.invert_xaxis()
    ax.legend(fontsize=7, loc=LEG.get(extrap_name, "best"))


def conv_fig(fname, title, panels):
    fig, axs = plt.subplots(1, len(panels), figsize=(max(5.2 * len(panels), 8.5), 4.2))
    axs = np.atleast_1d(axs)
    for ax, p in zip(axs, panels):
        conv_panel(ax, *p)
    fig.suptitle(title, x=0.01, ha="left", fontsize=11)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    foot(fig)
    fig.savefig(os.path.join(FIG, fname))
    plt.close(fig)


# 1. structural mesh comparison: Mechanical end-face renders + node counts vs licence
try:
    from PIL import Image
    tags = [t for t in ("XC", "C", "B", "FR", "FA", "FC") if os.path.isfile(os.path.join(REND, "%s_mesh_end_face.png" % t))]
    fig = plt.figure(figsize=(16, 7.2))
    wd = 0.98 / max(len(tags), 1)
    for i, t in enumerate(tags):
        ax = fig.add_axes([0.01 + i * wd, 0.40, wd - 0.006, 0.52])
        im = Image.open(os.path.join(REND, "%s_mesh_end_face.png" % t)).convert("RGB")
        w, h = im.size
        im = im.crop((int(w * 0.28), int(h * 0.05), int(w * 0.72), int(h * 0.92)))
        ax.imshow(im)
        ax.set_axis_off()
        d = M[t]["divisions"]
        ax.set_title("%s\n%d circ x %d wall x %d axial\n%s nodes" % (t, d["circumferential"], d["through_wall"], d["axial"],
                                                                 format(M[t]["LC2"]["nodes"], ",")), fontsize=9)
    ax = fig.add_axes([0.07, 0.07, 0.88, 0.25])
    allt = [t for t in ("XC", "C", "B", "FR", "FA", "FC", "IL") if t in M]
    ax.barh(range(len(allt)), [M[t]["LC2"]["nodes"] for t in allt], color=[C1 if t in FAM else STYLE[t][1] for t in allt])
    ax.axvline(128000, color=INK, lw=1.5)
    ax.text(127500, len(allt) - 0.35, "Student limit 128,000 nodes ", fontsize=8, ha="right")
    ax.set_yticks(range(len(allt)))
    ax.set_yticklabels([LBL[t] for t in allt], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("nodes (quadratic SOLID186)")
    fig.suptitle("Structural mesh family - end-face meshes exported from Mechanical (top) and node counts (bottom)", x=0.01, ha="left", fontsize=11)
    foot(fig)
    fig.savefig(os.path.join(FIG, "F8B_01_structural_mesh_comparison.png"))
    plt.close(fig)
except Exception as e:
    print("figure 1 skipped:", e)

REF = json.load(open(os.path.join(OUT, "ref1d_lc1_8B.json")))
CFD = "CFD-mesh effect on this quantity (Section 6B): "
conv_fig("F8B_02_LC2_stress_vs_mesh.png", "LC2 (thermal only) - stress vs mesh size", [
    (("LC2", "max_vm_Pa"), 1e-6, "max von Mises [MPa]", "peak von Mises (outer edge, inlet face)", "LC2 max von Mises [Pa]",
     CFD + "-2.3 / +0.7 %\n(the whole axis range here is < 0.07 %)"),
    (("LC2", "mean_axial_stress_Pa"), -1e-6, "|mean axial stress| N/A [MPa] (compression)", "mean axial stress (magnitude)", "LC2 mean axial stress [Pa]",
     CFD + "-1.7 / +0.5 %\n(the whole axis range here is < 0.002 %)"),
    (("LC2", "max_vm_interior_Pa"), 1e-6, "max von Mises 15-585 mm [MPa]", "interior maximum (outside the end zones)", "LC2 max von Mises 15-585 mm [Pa]",
     "sampling of a flat maximum between node planes\n(whole range < 0.4 %)")])
conv_fig("F8B_03_LC2_deformation_vs_mesh.png", "LC2 (thermal only) - deformation vs mesh size", [
    (("LC2", "max_utot_m"), 1e3, "max total deformation [mm]", "total deformation", "LC2 max total deformation [m]", "whole axis range < 0.003 %"),
    (("LC2", "min_uz_m"), 1e3, "min axial displacement [mm]", "axial displacement", "LC2 min axial displacement [m]", "whole axis range < 0.01 %"),
    (("LC2", "max_ur_m"), 1e3, "max radial displacement [mm]", "radial displacement", "LC2 max radial displacement [m]", "whole axis range < 0.005 %")])
conv_fig("F8B_04_LC1_stress_vs_mesh.png", "LC1 (free expansion) - stress vs mesh size", [
    (("LC1", "max_vm_Pa"), 1e-6, "max von Mises [MPa]", "peak von Mises (bore, z = 6.5-8.7 mm)", "LC1 max von Mises [Pa]",
     "inlet temperature-transfer bound (F-035): +/-9.8 MPa\npeak lies between node planes: non-monotonic"),
    (("LC1", "midspan", "bore_st_Pa"), 1e-6, "mid-span bore hoop stress [MPa]", "mid-span bore hoop stress (z = 300 mm)", "LC1 mid-span bore hoop stress [Pa]",
     CFD + "-0.2 / +0.6 % (through-wall dT)",
     (REF["bore"]["s_t_MPa"], "1-D exact, same imposed field (ref1d_lc1_8B.py)"))])
conv_fig("F8B_05_LC1_deformation_vs_mesh.png", "LC1 (free expansion) - deformation vs mesh size", [
    (("LC1", "max_utot_m"), 1e3, "max total deformation [mm]", "total deformation", "LC1 max total deformation [m]", CFD + "-1.7 / +0.5 %\n(axis range < 0.004 %)"),
    (("LC1", "dL_face_mean_m"), 1e3, "free axial growth [mm]", "axial growth (face-mean)", "LC1 free growth dL [m]", CFD + "-32 / +9 um (-1.7 / +0.5 %)\n(axis range < 0.004 %)")])
conv_fig("F8B_06_lambda1_vs_mesh.png", "LC2 linear buckling - first load factor vs mesh size", [
    (("buckling", "lambda1"), 1, "lambda_1", "first eigenvalue (load factor)", "lambda_1", CFD + "+1.8 / -0.5 % (8A)\n(the whole axis range here is < 0.006 %)"),
    (("buckling", "lambda2"), 1, "lambda_2", "second eigenvalue (orthogonal pair)", None, "repeated root of the axisymmetric section")])
conv_fig("F8B_07_critical_load_vs_mesh.png", "LC2 linear buckling - critical load vs mesh size", [
    (("buckling", "critical_load_N"), 1e-3, "critical load lambda_1 x N [kN]", "critical axial load", "critical buckling load [N]",
     "P_cr = lambda_1 x end reaction; whole axis range < 0.005 %")])

# 8. mode 1 comparison (lateral deflection of the duct axis from each mesh's eigenvector) + renders
fig = plt.figure(figsize=(14, 7.5))
ax = fig.add_axes([0.06, 0.52, 0.9, 0.40])
cols = {"XC": "#9bbbe6", "C": "#5c95dc", "B": C1, "FR": C2, "FA": C3, "FC": "#c4a000"}
for t in ("B", "XC", "C", "FR", "FA", "FC"):
    c = getv(t, ("buckling", "modes", "1"))
    if not c:
        continue
    z = np.array(c["_curve"]["z_m"]) * 1e3; w = np.array(c["_curve"]["w_norm"])
    corr = c["correlation_with_reference_shapes"]; best = max(corr, key=lambda k: abs(corr[k]))
    w = w * (1 if corr[best] >= 0 else -1)
    if t == "B":
        from scipy.interpolate import CubicSpline
        splB = CubicSpline(z, w)
    dev = "" if t == "B" else ", max |w - w_B| = %.1e" % np.max(np.abs(w - splB(z)))
    ax.plot(z, w, color=cols[t], lw=2 if t == "B" else 1.4, label="%s: lambda_1 = %.7f%s" % (LBL[t], M[t]["buckling"]["lambda1"], dev))
s = np.linspace(0, 1, 200)
ax.plot(s * 600, np.cos(np.pi * s), color=MUTED, ls="--", lw=1, label="guided-column shape cos(pi z/L)")
ax.set_xlabel("axial position z [mm]")
ax.set_ylabel("lateral deflection (normalised)")
ax.set_title("Mode 1 of every mesh - lateral deflection of the duct axis (eigenvector sign/amplitude arbitrary)", loc="left", fontsize=10)
ax.legend(fontsize=7.5, loc="lower left", ncol=2)
try:
    from PIL import Image
    tags = [t for t in ("XC", "C", "B", "FR", "FA", "FC") if os.path.isfile(os.path.join(REND, "%s_BK_Mode_1_side_YZ.png" % t))]
    wd = 0.98 / max(len(tags), 1)
    for i, t in enumerate(tags):
        a2 = fig.add_axes([0.01 + i * wd, 0.03, wd - 0.006, 0.40])
        im = Image.open(os.path.join(REND, "%s_BK_Mode_1_side_YZ.png" % t)).convert("RGB")
        w_, h_ = im.size
        a2.imshow(im.crop((0, 0, int(w_ * 0.80), h_)))
        a2.set_axis_off()
        ang = M[t]["buckling"]["modes"]["1"]["lateral_direction_deg"]
        a2.set_title("%s: side view (YZ), mode plane at %.0f deg" % (t, ang), fontsize=7.5)
    fig.text(0.01, 0.445, "Mechanical renders (unedited exports, auto-scaled). Mode 1 and 2 are a repeated pair: the bending plane is arbitrary, "
             "so the projected amplitude in a fixed view differs between meshes.", fontsize=7.5, color=MUTED)
except Exception as e:
    print("figure 8 renders skipped:", e)
foot(fig)
fig.savefig(os.path.join(FIG, "F8B_08_mode1_comparison.png"))
plt.close(fig)

# 9. inlet region
fig, axs = plt.subplots(1, 2, figsize=(13, 4.6))
for t in ("XC", "C", "B", "FR", "FA", "FC", "IL"):
    if t not in M:
        continue
    col = cols.get(t, C4)
    for ax, case, key, lab in ((axs[0], "LC2", "outer_vm_MPa", "LC2 outer surface r = 20 mm"),
                               (axs[1], "LC1", "bore_vm_MPa", "LC1 bore r = 10 mm")):
        p = M[t][case]["inlet_profile"]
        ax.plot(p["z_mm"], p[key], "-o", ms=3, color=col, lw=1.6 if t == "B" else 1.1, label=LBL[t])
        ax.set_title("%s - theta-mean von Mises, first 30 mm" % lab, loc="left", fontsize=10)
for ax in axs:
    ax.set_xlabel("z [mm] from the inlet face")
    ax.set_ylabel("von Mises [MPa]")
    ax.legend(fontsize=7.5)
fig.tight_layout(rect=(0, 0.03, 1, 1))
foot(fig)
fig.savefig(os.path.join(FIG, "F8B_09_inlet_region_stress.png"))
plt.close(fig)
print("figures written to", FIG)
