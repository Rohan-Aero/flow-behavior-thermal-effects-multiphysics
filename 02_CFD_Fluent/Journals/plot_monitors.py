# -*- coding: utf-8 -*-
"""Section 5A - plot the per-iteration monitors and residuals from the diagnostic run.

Reads Test_Run/s5a_monitors.out (written by Fluent, one line per iteration) and the
solver stdout for the residual history. Nothing here is a converged result: the whole
point of the figure is to show the trends that justify calling the case stable.
"""
from __future__ import print_function
import os, re, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
MON = os.path.join(BASE, "Test_Run", "s5a_monitors.out")
STD = os.path.join(BASE, "Logs", "test150_stdout.txt")
OUT = os.path.join(BASE, "Test_Run")

C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GREY = "#5a5a5a"

# ---- Section 2 analytical reference values (NOT targets, NOT to be matched by tuning)
REF = dict(mdot=8.6866e-3, Q=603.186, dp=441.5, T_out=368.85, T_wall=574.4)
BAND = dict(Q=(600.0, 606.0), dp=(375.0, 510.0), T_out=(365.0, 373.0), T_wall=(534.0, 583.0))

# ---------------------------------------------------------------- read monitors
with open(MON) as fh:
    lines = [l.strip() for l in fh if l.strip()]
hdr = None
rows = []
for l in lines:
    if l.startswith('("Iteration"'):
        hdr = [t.strip('"') for t in re.findall(r'"([^"]+)"', l)]
        continue
    if hdr and re.match(r"^\d+\s", l):
        rows.append([float(x) for x in l.split()])
d = np.array(rows)
col = {n: i for i, n in enumerate(hdr)}
it = d[:, col["Iteration"]]
print("monitors: %d iterations, %d quantities" % (len(it), len(hdr) - 1))

# ---------------------------------------------------------------- read residuals
res_names, res = [], []
with open(STD, errors="ignore") as fh:
    for l in fh:
        if res_names is not None and "iter" in l and "continuity" in l and not res_names:
            res_names = [t for t in l.split() if t not in ("iter", "time/iter")]
        m = re.match(r"^\s*(\d+)((?:\s+[-+]?\d\.\d{4}e[-+]\d\d){5,})", l)
        if m:
            res.append([float(m.group(1))] + [float(x) for x in m.group(2).split()])
R = np.array(res) if res else None
RES_EQ = ["continuity", "x-velocity", "y-velocity", "z-velocity", "energy", "k", "omega"]
print("residual lines: %s" % (0 if R is None else len(R)))


def band(ax, lo, hi, label):
    ax.axhspan(lo, hi, color=C3, alpha=0.10, zorder=0)
    ax.text(0.99, hi, " " + label, transform=ax.get_yaxis_transform(), ha="right",
            va="bottom", fontsize=7, color="#14795a")


fig, axes = plt.subplots(2, 3, figsize=(15.2, 8.0))

# (1) residuals
ax = axes[0, 0]
cols = [C1, "#7aa9e0", "#a8c6ec", "#1d4f86", C2, C3, C4]
if R is not None and R.shape[1] >= 8:
    for j, nm in enumerate(RES_EQ):
        ax.semilogy(R[:, 0], R[:, 1 + j], lw=1.3, color=cols[j], label=nm)
    ax.axhline(1e-4, color=GREY, ls=":", lw=1.0)
    ax.text(2, 1.3e-4, "NR-03 target: 1e-4 (flow/turb)", fontsize=7, color=GREY)
    ax.axhline(1e-6, color=GREY, ls="--", lw=1.0)
    ax.text(2, 1.3e-6, "NR-03 target: 1e-6 (energy)", fontsize=7, color=GREY)
ax.set_xlabel("iteration"); ax.set_ylabel("scaled residual")
ax.set_title("(1) Residuals - monotonic, no oscillation", fontsize=10)
ax.legend(fontsize=7, frameon=False, ncol=2); ax.grid(alpha=0.22)

# (2) mass conservation
ax = axes[0, 1]
ax.plot(it, d[:, col["mdot_in"]] * 1e3, lw=1.6, color=C1, label="inlet")
ax.plot(it, -d[:, col["mdot_out"]] * 1e3, lw=1.6, color=C2, ls="--", label="outlet (sign flipped)")
ax.axhline(REF["mdot"] * 1e3, color=GREY, ls=":", lw=1.1)
ax.text(len(it) * 0.98, REF["mdot"] * 1e3, "analytical 8.687 g/s ", ha="right", va="bottom",
        fontsize=7, color=GREY)
ax.set_xlabel("iteration"); ax.set_ylabel("mass flow  [g/s]")
ax.set_title("(2) Mass flow in vs out", fontsize=10)
ax.legend(fontsize=8, frameon=False); ax.grid(alpha=0.22)
axr = ax.twinx()
axr.semilogy(it, np.abs(d[:, col["mass_imbalance"]]) / d[:, col["mdot_in"]] * 100, lw=1.0,
             color=C3)
axr.set_ylabel("|imbalance| / mdot  [%]", color=C3, fontsize=8)
axr.tick_params(axis="y", labelcolor=C3, labelsize=7)

# (3) heat transfer
ax = axes[0, 2]
band(ax, BAND["Q"][0], BAND["Q"][1], "expected 600-606 W")
ax.plot(it, d[:, col["q_heated_wall"]], lw=1.8, color=C2, label="into HEATED_OUTER_WALL")
ax.plot(it, d[:, col["q_interface"]], lw=1.4, color=C1, label="across the CHT interface")
ax.plot(it, -d[:, col["q_fluid_net"]], lw=1.4, color=C3, ls="--", label="out with the air")
ax.axhline(REF["Q"], color=GREY, ls=":", lw=1.1)
qi = d[:, col["q_interface"]]
ipk = int(np.argmax(qi))
ax.set_ylim(0, max(1.15 * qi.max(), 700))
ax.annotate("startup overshoot\n%.0f W at iter %d" % (qi[ipk], it[ipk]),
            xy=(it[ipk], qi[ipk]), xytext=(it[ipk] + 28, qi[ipk] * 0.92),
            fontsize=7.5, color="#7a3413",
            arrowprops=dict(arrowstyle="->", color="#7a3413", lw=0.9))
ax.set_xlabel("iteration"); ax.set_ylabel("heat rate  [W]")
ax.set_title("(3) Heat path: wall -> solid -> air", fontsize=10)
ax.legend(fontsize=7.5, frameon=False, loc="lower right"); ax.grid(alpha=0.22)

# (4) pressure
ax = axes[1, 0]
band(ax, BAND["dp"][0], BAND["dp"][1], "expected 375-510 Pa")
ax.plot(it, d[:, col["p_in"]] - d[:, col["p_out"]], lw=1.6, color=C1)
ax.axhline(REF["dp"], color=GREY, ls=":", lw=1.1)
ax.text(len(it) * 0.98, REF["dp"], "analytical 441.5 Pa ", ha="right", va="bottom",
        fontsize=7, color=GREY)
ax.set_ylim(300, 950)
ax.set_xlabel("iteration"); ax.set_ylabel("p_in - p_out  [Pa]")
ax.set_title("(4) Pressure drop (CFD-comparable)", fontsize=10)
ax.grid(alpha=0.22)

# (5) temperatures
ax = axes[1, 1]
ax.plot(it, d[:, col["T_out_bulk"]], lw=1.6, color=C1, label="air outlet bulk")
ax.plot(it, d[:, col["T_wall_max"]], lw=1.6, color=C2, label="max wetted-wall T")
ax.plot(it, d[:, col["T_solid_max"]], lw=1.6, color=C4, label="max solid T")
ax.plot(it, d[:, col["T_solid_mean"]], lw=1.6, color=C3, label="volume-mean solid T")
ax.axhline(REF["T_out"], color=GREY, ls=":", lw=1.0)
ts = d[:, col["T_solid_max"]]
ipk = int(np.argmax(ts))
ax.annotate("startup overshoot: %.0f K at iter %d,\n%.0f K above the value it settles to"
            % (ts[ipk], it[ipk], ts[ipk] - ts[-1]),
            xy=(it[ipk], ts[ipk]), xytext=(it[ipk] + 30, ts[ipk] + 8),
            fontsize=7.5, color="#7a3413",
            arrowprops=dict(arrowstyle="->", color="#7a3413", lw=0.9))
ax.set_xlabel("iteration"); ax.set_ylabel("temperature  [K]")
ax.set_title("(5) Temperatures - startup overshoot, then still drifting", fontsize=10)
ax.legend(fontsize=7.5, frameon=False, loc="lower right"); ax.grid(alpha=0.22)

# (6) through-wall dT and y+
ax = axes[1, 2]
dT = d[:, col["T_solid_max"]] - d[:, col["T_wall_max"]]
band(ax, 6.6, 8.0, "expected 6.6-8.0 K")
ax.plot(it, dT, lw=1.8, color=C2, label="T_solid_max - T_wall_max")
ax.set_ylim(0, 12)
ax.set_xlabel("iteration"); ax.set_ylabel("through-wall temperature difference  [K]")
ax.set_title("(6) Conjugate coupling is real (zero would mean it is not)", fontsize=10)
ax.grid(alpha=0.22)
ax.legend(fontsize=7.5, frameon=False, loc="lower left")
axr = ax.twinx()
axr.plot(it, d[:, col["yplus_max"]], lw=1.3, color=C1)
axr.axhline(1.0, color=C1, ls=":", lw=1.0)
axr.set_ylabel("max y+  (preliminary)", color=C1, fontsize=8)
axr.set_ylim(0, 3.5)
axr.tick_params(axis="y", labelcolor=C1, labelsize=7)

fig.suptitle("Section 5A diagnostic solve - 150 iterations on the 159,840-cell medium mesh."
             "  THIS IS NOT A CONVERGED SOLUTION.", fontsize=11.5, y=0.995)
fig.text(0.5, -0.015,
         "Shaded bands are the Section 2 ANALYTICAL expectation ranges, shown for orientation "
         "only. No solver setting was tuned to land inside them.\nANSYS Fluent 2026 R1, "
         "pressure-based coupled, steady, k-omega SST, first-order startup discretisation. "
         "RE-ANALYSIS 2026 - not an original internship result.",
         ha="center", va="top", fontsize=7.6, color=GREY, linespacing=1.5)
fig.tight_layout()
p = os.path.join(OUT, "s5a_test_diagnostics.png")
fig.savefig(p, dpi=165, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("wrote", p)

# ---------------------------------------------------------------- text summary
last = d[-1]
A_out_exact = math.pi * 0.040 * 0.600
poly48 = math.sin(math.pi / 48.0) / (math.pi / 48.0)
area48 = (48.0 / (2 * math.pi)) * math.sin(2 * math.pi / 48.0)
rows = [
    ("iterations", "%d" % it[-1], "", ""),
    ("mass flow in", "%.6f g/s" % (last[col["mdot_in"]] * 1e3), "8.6866 g/s",
     "%+.3f %%" % ((last[col["mdot_in"]] / REF["mdot"] - 1) * 100)),
    ("mass imbalance", "%.3e kg/s" % last[col["mass_imbalance"]], "0",
     "%.2e %% of mdot" % (abs(last[col["mass_imbalance"]]) / last[col["mdot_in"]] * 100)),
    ("Q into outer wall", "%.4f W" % last[col["q_heated_wall"]], "603.186 W",
     "%+.3f %%" % ((last[col["q_heated_wall"]] / REF["Q"] - 1) * 100)),
    ("Q across interface", "%.4f W" % last[col["q_interface"]], "", ""),
    ("Q out with the air", "%.4f W" % (-last[col["q_fluid_net"]]), "", ""),
    ("energy closure", "%.4f W" % (last[col["q_heated_wall"]] + last[col["q_fluid_net"]]), "0",
     "%.3f %% of input" % (abs(last[col["q_heated_wall"]] + last[col["q_fluid_net"]])
                           / last[col["q_heated_wall"]] * 100)),
    ("dp (p_in - p_out)", "%.3f Pa" % (last[col["p_in"]] - last[col["p_out"]]), "441.5 Pa",
     "%+.2f %%" % (((last[col["p_in"]] - last[col["p_out"]]) / REF["dp"] - 1) * 100)),
    ("T outlet bulk", "%.3f K" % last[col["T_out_bulk"]], "368.85 K",
     "%+.3f %%" % ((last[col["T_out_bulk"]] / REF["T_out"] - 1) * 100)),
    ("T max wetted wall", "%.3f K" % last[col["T_wall_max"]], "574.4 K (exit)",
     "%+.2f %%" % ((last[col["T_wall_max"]] / REF["T_wall"] - 1) * 100)),
    ("T max solid", "%.3f K" % last[col["T_solid_max"]], "", ""),
    ("T mean solid (volume)", "%.3f K" % last[col["T_solid_mean"]], "554.7 K (exit mid-wall)",
     "different quantity"),
    ("through-wall dT", "%.3f K" % (last[col["T_solid_max"]] - last[col["T_wall_max"]]),
     "6.6-8.0 K", "in band" if 6.6 <= last[col["T_solid_max"]] - last[col["T_wall_max"]] <= 8.0
     else "OUT OF BAND"),
    ("max outlet velocity", "%.3f m/s" % last[col["v_out_max"]], "28.89 m/s bulk",
     "centreline/bulk = %.3f" % (last[col["v_out_max"]] / 28.89)),
    ("max y+ (PRELIMINARY)", "%.4f" % last[col["yplus_max"]], "target <= 1",
     "not a converged value"),
    ("solid T startup peak", "%.1f K at iter %d" % (d[:, col["T_solid_max"]].max(),
                                                    it[int(np.argmax(d[:, col["T_solid_max"]]))]),
     "n/a", "+%.0f K over the settled value - decays smoothly, see F-022"
     % (d[:, col["T_solid_max"]].max() - last[col["T_solid_max"]])),
    ("interface Q startup peak", "%.1f W at iter %d" % (d[:, col["q_interface"]].max(),
                                                        it[int(np.argmax(d[:, col["q_interface"]]))]),
     "n/a", "same transient"),
]
if R is not None:
    for j, nm in enumerate(RES_EQ):
        rows.append(("residual " + nm, "%.4e" % R[-1, 1 + j],
                     "1e-6" if nm == "energy" else "1e-4",
                     "met" if R[-1, 1 + j] < (1e-6 if nm == "energy" else 1e-4) else "NOT met"))

w = max(len(r[0]) for r in rows)
txt = ["Section 5A diagnostic solve - final-iteration values",
       "RE-ANALYSIS 2026. NOT a converged solution; do not quote as a result.",
       "",
       "%-*s  %-22s  %-24s  %s" % (w, "quantity", "CFD @150 iterations",
                                   "Section 2 analytical", "comparison"),
       "-" * (w + 76)]
for a, b, c, e in rows:
    txt.append("%-*s  %-22s  %-24s  %s" % (w, a, b, c, e))
txt += ["",
        "Geometric note: the mesh represents the circular section by an inscribed",
        "48-sided polygon. That accounts for the CFD being below the analytical value by",
        "  %.4f %% on heated-wall area (lateral, sin(pi/N)/(pi/N) = %.6f)" % ((poly48 - 1) * 100, poly48),
        "  %.4f %% on inlet area   (planar,  (N/2pi)sin(2pi/N) = %.6f)" % ((area48 - 1) * 100, area48),
        "It is a discretisation effect, not a physics or boundary-condition error."]
q = os.path.join(OUT, "s5a_test_summary.txt")
with open(q, "w") as fh:
    fh.write("\n".join(txt))
print("\n".join(txt))
print("wrote", q)
