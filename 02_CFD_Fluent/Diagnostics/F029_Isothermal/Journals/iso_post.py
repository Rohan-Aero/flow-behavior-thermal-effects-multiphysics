# -*- coding: utf-8 -*-
"""Section 6B - F-029 isothermal diagnostic, post-processing. Same friction-factor definition as the
heated runs: f = 8 tau_w rho_b / G^2 with slab-averaged |axial wall shear|, fully developed window
x/D 18-29 (exact-window mean by linear interpolation, the definition used in the three-mesh study).
RE-ANALYSIS 2026."""
import os, re, json, math, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                                   # 06_Fluent_CFD/Diagnostics/F029_Isothermal
CFD = os.path.dirname(os.path.dirname(BASE))                   # 06_Fluent_CFD
L, D, NZ = 0.600, 0.020, 90
dz = L / NZ


def read_ascii(p):
    with open(p) as fh:
        cols = [c.strip() for c in fh.readline().strip().split(",")]
        a = np.loadtxt(fh, delimiter=",")
    return {c: a[:, i] for i, c in enumerate(cols[:a.shape[1]])}


def read_report(p):
    hdr, rows = None, []
    for l in open(p, errors="ignore"):
        s = l.strip()
        if s.startswith('("Iteration"'):
            hdr = re.findall(r'"([^"]+)"', s)
        elif hdr and re.match(r"^\d+\s", s):
            rows.append([float(x) for x in s.split()])
    return hdr, np.array(rows)


WI = read_ascii(os.path.join(BASE, "Exports", "wall_interface.csv"))
BI = read_ascii(os.path.join(BASE, "Exports", "boundary_inlet.csv"))
BO = read_ascii(os.path.join(BASE, "Exports", "boundary_outlet.csv"))
hdr, MON = read_report(os.path.join(BASE, "Monitors", "iso_monitors.out"))
mc = {n: i for i, n in enumerate(hdr)}
last = MON[-1]
mdot = float(last[mc["mdot_in"]])
A_in = float(BI["face-area-magnitude"].sum())
G = mdot / A_in
rho = float(np.sum(BI["density"] * BI["face-area-magnitude"]) / A_in)
Tmax_all = float(max(WI["temperature"].max(), BO["temperature"].max()))
Tmin_all = float(min(WI["temperature"].min(), BO["temperature"].min()))
mu300 = 1.846e-5
Re = G * D / mu300
k = np.clip((WI["z-coordinate"] / dz).astype(int), 0, NZ - 1)
zc = (np.arange(NZ) + 0.5) * dz
tau = np.array([np.sum(np.abs(WI["z-wall-shear"][k == i]) * WI["face-area-magnitude"][k == i]) /
                WI["face-area-magnitude"][k == i].sum() for i in range(NZ)])
yp = np.array([np.sum(WI["y-plus"][k == i] * WI["face-area-magnitude"][k == i]) /
               WI["face-area-magnitude"][k == i].sum() for i in range(NZ)])
f_loc = 8 * tau * rho / G ** 2
xD = zc / D


def window_mean(x, y, a=18.0, b=29.0):
    xs = np.linspace(a, b, 2201)
    return float(np.trapz(np.interp(xs, x, y), xs) / (b - a))


f_fd = window_mean(xD, f_loc)
f_slab = float(np.mean(f_loc[(xD > 18) & (xD < 29)]))
f_pet = (0.790 * math.log(Re) - 1.64) ** -2
f_blasius = 0.316 * Re ** -0.25
dp = float(last[mc["p_in_area"]] - last[mc["p_out_area"]])
F_wall = float(last[mc["F_wall_z"]])
# heated medium, same exact-window definition
med = {}
with open(os.path.join(CFD, "Profiles", "axial_profiles_cfd.csv")) as fh:
    fh.readline()
    h_ = fh.readline().strip().split(",")
    a_ = np.loadtxt(fh, delimiter=",")
for i, c in enumerate(h_):
    med[c] = a_[:, i]
f_heated = window_mean(med["x_over_D"], med["f_shear"])
Re_heated = window_mean(med["x_over_D"], med["Re"])
TwTb = window_mean(med["x_over_D"], med["Twi"] / med["Tb_mass"])
f_pet_heatedRe = (0.790 * math.log(Re_heated) - 1.64) ** -2
# heating exponent implied by the CFD: f_heated/f_iso = [f_Pet(Re_h)/f_Pet(Re_iso)] * (Tw/Tb)^m
m_implied = math.log((f_heated / f_fd) / (f_pet_heatedRe / f_pet)) / math.log(TwTb)
RES = dict(mdot_kg_s=mdot, A_in=A_in, G=G, rho=rho, Re=Re, dp_Pa=dp, F_wall_N=F_wall,
           T_range_K=[Tmin_all, Tmax_all], f_fd_exact_window=f_fd, f_fd_slab_mean=f_slab,
           f_petukhov=f_pet, f_blasius=f_blasius, f_vs_petukhov_pct=100 * (f_fd / f_pet - 1),
           f_vs_blasius_pct=100 * (f_fd / f_blasius - 1), yplus_fd_mean=window_mean(xD, yp),
           f_local_xD18=float(np.interp(18, xD, f_loc)), f_local_xD29=float(np.interp(29, xD, f_loc)),
           heated_medium=dict(f_fd_exact_window=f_heated, Re_window=Re_heated, Tw_over_Tb=TwTb,
                              f_petukhov_at_Re=f_pet_heatedRe,
                              f_petukhov_heating_m_minus0p1=f_pet_heatedRe * TwTb ** -0.1),
           heating_ratio_cfd=f_heated / f_fd, heating_ratio_petukhov_m_minus0p1=(f_pet_heatedRe / f_pet) * TwTb ** -0.1,
           heating_exponent_m_implied=m_implied,
           run=json.load(open(os.path.join(BASE, "Audit", "iso_run_summary.json"))))
json.dump(RES, open(os.path.join(BASE, "iso_results.json"), "w"), indent=2, default=float)
with open(os.path.join(BASE, "iso_f_profile.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# isothermal diagnostic, medium mesh: slab-averaged wall shear and Darcy f. RE-ANALYSIS 2026."])
    w.writerow(["z", "x_over_D", "tau_w", "f", "yplus_avg"])
    for i in range(NZ):
        w.writerow(["%.6g" % zc[i], "%.6g" % xD[i], "%.8g" % tau[i], "%.8g" % f_loc[i], "%.6g" % yp[i]])
fig, ax = plt.subplots(1, 1, figsize=(11, 5))
ax.plot(xD, f_loc, color="#2a78d6", lw=1.6, label="CFD isothermal (energy off), medium mesh")
ax.plot(med["x_over_D"], med["f_shear"], color="#eb6834", lw=1.4, ls="--", label="CFD heated baseline, medium mesh")
ax.axhline(f_pet, color="k", lw=1.0, ls=":", label="Petukhov at Re = %.0f (isothermal)" % Re)
ax.axvspan(18, 29, color="#eeeeee", lw=0)
ax.set_ylim(0.015, 0.035); ax.set_xlabel("x/D"); ax.set_ylabel("Darcy f = 8 tau_w rho / G^2"); ax.legend(fontsize=8.5)
ax.set_title("F-029 diagnostic: friction factor, isothermal vs heated (grey = window x/D 18-29)", fontsize=10.5)
fig.text(0.5, -0.02, "Isothermal window mean f = %.5f (%.1f %% vs Petukhov %.5f); heated %.5f. ANSYS Fluent 2026 R1, "
         "matplotlib render of exported data. RE-ANALYSIS 2026." % (f_fd, 100 * (f_fd / f_pet - 1), f_pet, f_heated),
         ha="center", fontsize=7.5, color="#5a5a5a")
fig.savefig(os.path.join(BASE, "Figures", "iso_friction_factor.png"), dpi=160, bbox_inches="tight", facecolor="white")
print(json.dumps({k_: v for k_, v in RES.items() if k_ != "run"}, indent=1, default=float))
print("ISO-POST-DONE")
