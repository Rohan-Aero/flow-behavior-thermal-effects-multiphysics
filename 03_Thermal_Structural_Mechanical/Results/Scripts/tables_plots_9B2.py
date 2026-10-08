# -*- coding: utf-8 -*-
"""SECTION 9B-2 Parts O-U - result tables, normalised changes and the 15 trend figures (RE-ANALYSIS 2026).

Inputs : Results/Data/post_9B2_results.json (post_9B2.py, from the raw solver tables of each case)
         CFD_Results/PARAMETRIC_CFD_RESULTS.csv (Section 9B-1)
Outputs: Results/PARAMETRIC_STRUCTURAL_RESULTS.csv, Results/SUPPORT_SENSITIVITY_RESULTS.csv,
         Results/Data/trends_9B2.json (values, % changes vs P00, local sensitivities), Results/Figures/F01..F15 *.png
Every figure is newly generated from the re-analysis's own simulation results (no recovered or measured data).
Usage: python tables_plots_9B2.py <parametric_study_root>
"""
import os, sys, json, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PS = sys.argv[1]
RES = os.path.join(PS, "Results")
FIG = os.path.join(RES, "Figures")
DAT = os.path.join(RES, "Data")
os.makedirs(FIG, exist_ok=True)
R = json.load(open(os.path.join(DAT, "post_9B2_results.json")))["cases"]
CFD = {}
with open(os.path.join(PS, "CFD_Results", "PARAMETRIC_CFD_RESULTS.csv")) as fh:
    rows = [l for l in fh if not l.startswith("#")]
for r in csv.DictReader(rows):
    CFD[r["case"]] = r
CFD["P00_BASELINE"] = CFD.get("P00_BASELINE")
PI_LABEL = ("pre-buckling equilibrium result; linear stability criterion indicates loss of stability before the applied "
            "load level")
MPa, mm, kN = 1e-6, 1e3, 1e-3
DESIGN = ["P00_BASELINE", "V01_LOW", "V03_HIGH", "Q01_LOW", "Q03_HIGH", "T01_THIN", "T03_THICK"]
FAM = {"V": ("V01_LOW", "P00_BASELINE", "V03_HIGH"), "Q": ("Q01_LOW", "P00_BASELINE", "Q03_HIGH"), "T": ("T01_THIN", "P00_BASELINE", "T03_THICK")}
XVAL = {"V": {"V01_LOW": 21.15, "P00_BASELINE": 23.5, "V03_HIGH": 25.85}, "Q": {"Q01_LOW": 7200, "P00_BASELINE": 8000, "Q03_HIGH": 8800},
        "T": {"T01_THIN": 8.0, "P00_BASELINE": 10.0, "T03_THICK": 12.0}}
XLAB = {"V": "Inlet velocity [m/s]", "Q": "Outer-wall heat flux q'' [W/m$^2$]", "T": "Wall thickness [mm] (Do 36 / 40 / 44 mm; Q held constant)"}


def status(tag):
    E = R[tag]
    lam = E.get("buckling", {}).get("lambda1")
    s = "SOLVED - VALID (checks in FINAL_PARAMETRIC_AUDIT.md)"
    if lam is not None and lam < 1.0:
        s += "; lambda1 < 1: LC2 static stress = " + PI_LABEL
    return s


def mode_short(tag):
    m = R[tag].get("buckling", {}).get("modes", {}).get("1")
    if not m:
        return ""
    corr = dict(m["correlation_with_reference_shapes"]); corr["fixed-pinned"] = m.get("corr_fixed_pinned", 0.0)
    best = max(corr, key=lambda k: abs(corr[k]))
    name = {"guided_n1 cos(pi z/L)": "guided column cos(pi z/L)", "guided_n2 / clamped_n1 cos(2pi z/L)": "clamped column 1-cos(2 pi z/L)",
            "pinned_n1 sin(pi z/L)": "pinned column sin(pi z/L)", "fixed-pinned": "fixed-pinned column"}[best]
    glob = m["beam_type_share_of_inplane_motion"] > 0.99 and m["max_ovalisation_over_max_lateral"] < 0.01
    return "%s lateral (Euler) mode, %s shape (corr %.4f), max at z = %.0f mm; modes 1-2 = orthogonal pair (split %.1e)" % (
        "global" if glob else "NON-global", name, abs(corr[best]), m["z_of_max_lateral_mm"], R[tag]["buckling"]["pair_split_rel"])


def v(tag, *keys):
    x = R.get(tag)
    for k in keys:
        if x is None:
            return None
        x = x.get(k) if isinstance(x, dict) else None
    return x


# ------------------------------------------------------------------ Part T table
cols = ["Case", "Variable", "Value", "Geometry", "Nodes", "Max deformation [mm]", "Axial growth [mm]", "LC1 max stress [MPa]",
        "LC2 max stress [MPa]", "LC2 mean axial stress [MPa]", "Critical temperature [K]", "Yield strength [MPa]",
        "Yield utilization [-]", "Lambda1 [-]", "Critical buckling load [kN]", "Buckling mode", "Status"]
out = []
for tag in ["P00_BASELINE", "C00_PIPELINE_CHECK"] + DESIGN[1:]:
    E = R.get(tag)
    if E is None:
        out.append({"Case": tag, "Status": "NOT AVAILABLE - case stopped (no value fabricated or interpolated)"})
        continue
    u = E["LC2"]["utilisation"]
    out.append({"Case": tag, "Variable": E["variable"], "Value": ("%s %s" % (E["value"], E["units"])).replace(" -", ""),
                "Geometry": E["geometry"], "Nodes": E["LC2"]["nodes"],
                "Max deformation [mm]": round(E["LC1"]["max_utot_m"] * mm, 5), "Axial growth [mm]": round(E["LC1"]["dL_face_mean_m"] * mm, 5),
                "LC1 max stress [MPa]": round(E["LC1"]["max_vm_Pa"] * MPa, 3), "LC2 max stress [MPa]": round(E["LC2"]["max_vm_Pa"] * MPa, 3),
                "LC2 mean axial stress [MPa]": round(E["LC2"]["mean_axial_stress_Pa"] * MPa, 3),
                "Critical temperature [K]": round(u["max_loc"]["T_K"], 2), "Yield strength [MPa]": round(u["Sy_at_max_Pa"] * MPa, 1),
                "Yield utilization [-]": round(u["max"], 4), "Lambda1 [-]": round(E["buckling"]["lambda1"], 5),
                "Critical buckling load [kN]": round(E["buckling"]["critical_load_N"] * kN, 2), "Buckling mode": mode_short(tag),
                "Status": status(tag) if tag != "P00_BASELINE" else "OFFICIAL BASELINE (7B / 8A solution, reference)"})
with open(os.path.join(RES, "PARAMETRIC_STRUCTURAL_RESULTS.csv"), "w", newline="", encoding="utf-8") as fh:
    fh.write("# RE-ANALYSIS 2026 - Section 9B-2 parametric structural results (newly generated ANSYS Mechanical solutions, "
             "not recovered data). Max deformation = LC1 (free expansion) max total deformation; axial growth = LC1 face-mean "
             "dL; critical temperature / yield strength / utilisation at the LC2 node of maximum vm/S_y(T).\n")
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    for r in out:
        w.writerow(r)

# ------------------------------------------------------------------ Part U table
SUP = [("S1", "P00_BASELINE", "LC2 (baseline): U_z = 0 on both complete end faces (radial free); 3 mid-span outer nodes U_theta = 0 "
                              "(rigid-body rotation only); ends free to translate laterally, end rotation held by U_z = 0 on the full face -> guided (sway) column (K = 1)"),
       ("S2", "S2_LC2NS_NOSWAY", "U_z = 0 and U_theta = 0 on every node of both end faces (CS_DUCT_CYL, radial free); no hoop nodes -> "
                                 "both ends clamped against lateral translation and rotation (K = 0.5)"),
       ("S3", "S3_LC2_INTERMEDIATE", "inlet face U_z = U_theta = 0 on every node (radial free) -> clamped; outlet face deformable remote "
                                     "displacement, pilot on the axis at z = 0.6 m, Ux = Uy = Uz = 0, rotations free -> pinned (K = 0.699)")]
NOTE = {"S1": "Official 7B/8A baseline. Sway of the ends is not restrained, so the lowest mode is the guided-column shape.",
        "S2": "8A sensitivity solution (static max vm and reaction from 8A; nodal table re-extracted in 9B-2 without re-solving). "
              "Idealised rigid flanges: no end sway and no end rotation.",
        "S3": "Solved in 9B-2 after the B03 toy benchmark passed. Intermediate between S1 and S2: one end clamped, one end pinned."}
srows = []
for sc, tag, dfn in SUP:
    E = R.get(tag)
    if E is None:
        srows.append({"Scenario": sc, "Support definition": dfn, "Interpretation notes": "NOT AVAILABLE - not solved (no value fabricated)"})
        continue
    lam = E["buckling"]["lambda1"]
    srows.append({"Scenario": sc, "Support definition": dfn, "Max stress [MPa]": round(E["LC2"]["max_vm_Pa"] * MPa, 3),
                  "Mean axial stress [MPa]": round(E["LC2"]["mean_axial_stress_Pa"] * MPa, 3),
                  "Deformation [mm]": round(E["LC2"]["max_utot_m"] * mm, 5), "Lambda1 [-]": round(lam, 5),
                  "Critical load [kN]": round(E["buckling"]["critical_load_N"] * kN, 2), "Dominant mode": mode_short(tag),
                  "Interpretation notes": NOTE[sc] + (" lambda1 < 1: the static stress is a " + PI_LABEL + "." if lam < 1 else
                                                      " lambda1 > 1: linear stability margin at the applied thermal load (linear eigenvalue, no imperfections).")})
with open(os.path.join(RES, "SUPPORT_SENSITIVITY_RESULTS.csv"), "w", newline="", encoding="utf-8") as fh:
    fh.write("# RE-ANALYSIS 2026 - Section 9B-2 support sensitivity at the baseline design (P00 temperature field, mesh B). "
             "Max stress = max von Mises; deformation = max total deformation of the static (pre-stress) state. No scenario is ranked or labelled as preferable.\n")
    w = csv.DictWriter(fh, fieldnames=["Scenario", "Support definition", "Max stress [MPa]", "Mean axial stress [MPa]", "Deformation [mm]",
                                       "Lambda1 [-]", "Critical load [kN]", "Dominant mode", "Interpretation notes"])
    w.writeheader()
    for r in srows:
        w.writerow(r)

# ------------------------------------------------------------------ trends, % change, local sensitivities
Q = {"dp_Pa": ("CFD", "dp_Pa"), "T_out_K": ("CFD", "T_out_K"), "T_solid_max_K": ("CFD", "T_solid_max_K"),
     "T_solid_mean_K": ("CFD", "T_solid_mean_K"),
     "LC1_max_utot_mm": ("S", "LC1", "max_utot_m"), "LC1_dL_mm": ("S", "LC1", "dL_face_mean_m"), "LC1_max_vm_MPa": ("S", "LC1", "max_vm_Pa"),
     "LC2_max_vm_MPa": ("S", "LC2", "max_vm_Pa"), "LC2_mean_axial_MPa": ("S", "LC2", "mean_axial_stress_Pa"),
     "LC2_max_utot_mm": ("S", "LC2", "max_utot_m"), "LC2_max_ur_mm": ("S", "LC2", "max_ur_m"), "LC2_end_reaction_kN": ("S", "LC2", "reactions", "inlet_Fz_N"),
     "LC2_utilisation": ("S", "LC2", "utilisation", "max"), "lambda1": ("S", "buckling", "lambda1"), "Pcr_kN": ("S", "buckling", "critical_load_N")}
SCALE = {"LC1_max_utot_mm": mm, "LC1_dL_mm": mm, "LC1_max_vm_MPa": MPa, "LC2_max_vm_MPa": MPa, "LC2_mean_axial_MPa": MPa, "LC2_max_utot_mm": mm,
         "LC2_max_ur_mm": mm, "LC2_end_reaction_kN": kN, "Pcr_kN": kN}


def val(tag, q):
    spec = Q[q]
    if spec[0] == "CFD":
        c = CFD.get(tag)
        return float(c[spec[1]]) if c else None
    x = v(tag, *spec[1:])
    return None if x is None else x * SCALE.get(q, 1.0)


TR = {"note": "RE-ANALYSIS 2026 - Section 9B-2 one-factor-at-a-time trends (values, % change vs P00, local sensitivity)", "families": {}}
for f, tags in FAM.items():
    F = {"x": [XVAL[f][t] for t in tags], "cases": list(tags), "quantities": {}}
    for q in Q:
        ys = [val(t, q) for t in tags]
        if any(y is None for y in ys):
            F["quantities"][q] = {"values": ys, "note": "incomplete"}
            continue
        y0 = ys[1]
        pct = [100.0 * (y - y0) / abs(y0) for y in ys]
        x = np.array(F["x"], float)
        # central difference -> normalised sensitivity (d y / y0) / (d x / x0); curvature check from the 3 points
        sens = ((ys[2] - ys[0]) / y0) / ((x[2] - x[0]) / x[1])
        lin_dev = (ys[1] - 0.5 * (ys[0] + ys[2])) / abs(y0) * 100.0
        F["quantities"][q] = {"values": ys, "pct_change_vs_P00": pct, "normalised_sensitivity": sens,
                              "midpoint_deviation_from_linear_pct": lin_dev,
                              "monotonic": bool((ys[0] - ys[1]) * (ys[1] - ys[2]) > 0)}
    TR["families"][f] = F
json.dump(TR, open(os.path.join(DAT, "trends_9B2.json"), "w"), indent=1)

# ------------------------------------------------------------------ figures (15)
plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 150})


def fig_family(fn, f, q, ylab, title, extra=None):
    tags = FAM[f]
    x = [XVAL[f][t] for t in tags]
    y = [val(t, q) for t in tags]
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.plot(x, y, "o--", color="#1f5f9f", lw=1.0, ms=7, label="solved cases (dashed line only connects them)")
    ax.plot([x[1]], [y[1]], "s", color="#c0392b", ms=9, label="P00 baseline (reference)", zorder=5)
    ax.axhline(y[1], color="#c0392b", lw=0.8, ls="--", alpha=0.6)
    for xi, yi in zip(x, y):
        ax.annotate("%.4g\n(%+.1f %%)" % (yi, 100 * (yi - y[1]) / abs(y[1])), (xi, yi), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=8)
    if extra:
        extra(ax, x, y)
    ax.set_xlabel(XLAB[f]); ax.set_ylabel(ylab); ax.set_title(title, fontsize=10)
    ax.margins(y=0.25)
    ax.legend(fontsize=8, loc="best")
    fig.text(0.99, 0.01, "RE-ANALYSIS 2026 - newly generated simulation results", ha="right", fontsize=6, color="gray")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, fn)); plt.close(fig)


def lam_line(ax, x, y):
    ax.axhline(1.0, color="k", lw=1.0, ls=":", label="\u03bb\u2081 = 1 (applied thermal load)")


FIGS = [
    ("F01_V_vs_pressure_drop.png", "V", "dp_Pa", "Pressure drop [Pa]", "Inlet velocity vs pressure drop (CFD, 9B-1)", None),
    ("F02_V_vs_outlet_temperature.png", "V", "T_out_K", "Outlet bulk temperature [K]", "Inlet velocity vs outlet temperature (CFD)", None),
    ("F03_V_vs_max_solid_temperature.png", "V", "T_solid_max_K", "Max solid temperature [K]", "Inlet velocity vs max solid temperature (CFD)", None),
    ("F04_V_vs_LC2_stress.png", "V", "LC2_max_vm_MPa", "LC2 max von Mises [MPa]", "Inlet velocity vs LC2 max von Mises stress", None),
    ("F05_V_vs_lambda1.png", "V", "lambda1", "\u03bb\u2081 [-]", "Inlet velocity vs first buckling load factor \u03bb\u2081 (S1 supports)", lam_line),
    ("F06_q_vs_outlet_temperature.png", "Q", "T_out_K", "Outlet bulk temperature [K]", "Heat flux vs outlet temperature (CFD)", None),
    ("F07_q_vs_max_solid_temperature.png", "Q", "T_solid_max_K", "Max solid temperature [K]", "Heat flux vs max solid temperature (CFD)", None),
    ("F08_q_vs_LC2_stress.png", "Q", "LC2_max_vm_MPa", "LC2 max von Mises [MPa]", "Heat flux vs LC2 max von Mises stress", None),
    ("F09_q_vs_lambda1.png", "Q", "lambda1", "\u03bb\u2081 [-]", "Heat flux vs first buckling load factor \u03bb\u2081 (S1 supports)", lam_line),
    ("F10_t_vs_max_deformation.png", "T", "LC1_max_utot_mm", "LC1 max total deformation [mm]", "Wall thickness vs max deformation (LC1 free expansion)", None),
    ("F11_t_vs_LC2_stress.png", "T", "LC2_max_vm_MPa", "LC2 max von Mises [MPa]", "Wall thickness vs LC2 max von Mises stress", None),
    ("F12_t_vs_lambda1.png", "T", "lambda1", "\u03bb\u2081 [-]", "Wall thickness vs first buckling load factor \u03bb\u2081 (S1 supports)", lam_line),
    ("F13_t_vs_critical_buckling_load.png", "T", "Pcr_kN", "Critical buckling load P_cr [kN]", "Wall thickness vs critical buckling load", None),
]
made = []
for fn, f, q, yl, ti, ex in FIGS:
    if all(val(t, q) is not None for t in FAM[f]):
        fig_family(fn, f, q, yl, ti, ex)
        made.append(fn)


def fig_support(fn, key, ylab, title, hline=None):
    labs, ys = [], []
    for sc, tag, _ in SUP:
        if tag in R:
            labs.append({"S1": "S1 guided\n(baseline LC2)", "S2": "S2 clamped-\nclamped", "S3": "S3 clamped-\npinned"}[sc])
            ys.append(val(tag, key))
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    cols_ = ["#c0392b" if l.startswith("S1") else "#1f5f9f" for l in labs]
    b = ax.bar(labs, ys, color=cols_, width=0.55)
    for bi, yi in zip(b, ys):
        ax.annotate("%.4g" % yi, (bi.get_x() + bi.get_width() / 2, yi), textcoords="offset points", xytext=(0, 3), ha="center", fontsize=9)
    if hline is not None:
        ax.axhline(hline, color="k", lw=1.0, ls=":")
    ax.set_ylabel(ylab); ax.set_title(title, fontsize=10)
    ax.margins(y=0.15)
    fig.text(0.99, 0.01, "RE-ANALYSIS 2026 - newly generated simulation results; S1 = baseline (red)", ha="right", fontsize=6, color="gray")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, fn)); plt.close(fig)
    made.append(fn)


fig_support("F14_support_vs_lambda1.png", "lambda1", "\u03bb\u2081 [-]", "Support scenario vs first buckling load factor (baseline design)", 1.0)
fig_support("F15_support_vs_LC2_stress.png", "LC2_max_vm_MPa", "Max von Mises of the static state [MPa]",
            "Support scenario vs max von Mises stress (baseline design)")
json.dump({"figures": made}, open(os.path.join(DAT, "figures_9B2.json"), "w"), indent=1)
print("tables written; figures:", len(made))
for r in out:
    print({k: r.get(k) for k in ("Case", "LC2 max stress [MPa]", "Yield utilization [-]", "Lambda1 [-]")})
for r in srows:
    print({k: r.get(k) for k in ("Scenario", "Max stress [MPa]", "Lambda1 [-]", "Deformation [mm]")})
