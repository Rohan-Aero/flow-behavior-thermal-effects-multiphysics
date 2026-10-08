# -*- coding: utf-8 -*-
"""
Section 5B post-processing - OFFICIAL BASELINE, medium mesh.

Operates ONLY on data exported by ANSYS Fluent 2026 R1 from the converged solution:
  Exports/cells_fluid.csv, cells_solid.csv      cell-centre values (no interpolation)
  Exports/wall_interface.csv, wall_outer.csv,   face-centroid values on walls
  Exports/wall_solid_ends.csv, boundary_*.csv
  Monitors/baseline_monitors.out                Fluent report file, every iteration
  Logs/baseline_stdout.txt                      Fluent solver output (residual history)
  Audit/fluent_*.txt                            Fluent's own flux / surface-integral reports
and on the frozen Section 2 analytical files for comparison.

RE-ANALYSIS 2026 - nothing here is an original internship result.
"""
from __future__ import print_function
import os, re, io, json, math, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from scipy.interpolate import griddata

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                               # 06_Fluent_CFD
ROOT = os.path.dirname(BASE)                               # project root
EXP = os.path.join(BASE, "Exports")
FIG = os.path.join(BASE, "Figures")
PRO = os.path.join(BASE, "Profiles")
MONd = os.path.join(BASE, "Monitors")
AUD = os.path.join(BASE, "Audit")
BL = os.path.join(BASE, "Baseline")
for d in (FIG, PRO, MONd, AUD, BL):
    if not os.path.isdir(d):
        os.makedirs(d)

C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GREY = "#5a5a5a"
PROV = ("ANSYS Fluent 2026 R1 converged baseline (medium mesh, 159,840 cells), exported and plotted "
        "with matplotlib. RE-ANALYSIS 2026 - not an original internship result.")

# geometry, frozen baseline
RI, RO, L, D = 0.010, 0.020, 0.600, 0.020
NT = 48
QPP_O = 8000.0
AIR_T = np.array([250., 300., 350., 400., 450., 500., 550., 600.])
AIR_CP = np.array([1006., 1007., 1009., 1014., 1021., 1030., 1040., 1051.])
AIR_MU = np.array([1.596e-5, 1.846e-5, 2.082e-5, 2.301e-5, 2.507e-5, 2.701e-5, 2.884e-5, 3.058e-5])
AIR_K = np.array([0.02227, 0.02624, 0.03003, 0.03365, 0.03707, 0.04038, 0.04360, 0.04659])
AIR_PR = np.array([0.720, 0.707, 0.700, 0.690, 0.686, 0.684, 0.683, 0.685])
INC_T = np.array([293.15, 373.15, 473.15, 573.15, 673.15])
INC_K = np.array([11.5, 12.1, 13.5, 15.2, 17.1])
kair = lambda T: np.interp(T, AIR_T, AIR_K)
muair = lambda T: np.interp(T, AIR_T, AIR_MU)
cpair = lambda T: np.interp(T, AIR_T, AIR_CP)
prair = lambda T: np.interp(T, AIR_T, AIR_PR)
kinc = lambda T: np.interp(T, INC_T, INC_K)

# faceting of the 48-gon
AREA48 = (NT / (2 * math.pi)) * math.sin(2 * math.pi / NT)        # planar
LAT48 = math.sin(math.pi / NT) / (math.pi / NT)                   # lateral
DH48 = D * math.cos(math.pi / NT)                                 # hydraulic diameter of the 48-gon


def finish(fig, name, caption=""):
    txt = (caption + "  " if caption else "") + PROV
    fig.text(0.5, -0.02, wrap(txt, 150), ha="center", va="top", fontsize=7.4, color=GREY, linespacing=1.45)
    p = os.path.join(FIG, name)
    fig.savefig(p, dpi=165, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("   figure", name)


def wrap(t, w):
    out, line = [], ""
    for word in t.split():
        if len(line) + len(word) + 1 > w:
            out.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    out.append(line)
    return "\n".join(out)


def read_fluent_ascii(path):
    with open(path, "r", errors="ignore") as fh:
        head = fh.readline()
        cols = [c.strip() for c in head.strip().split(",")]
        data = np.loadtxt(fh, delimiter=",")
    if data.ndim == 1:
        data = data[None, :]
    if data.shape[1] != len(cols):
        cols = cols[:data.shape[1]]
    return {c: data[:, i] for i, c in enumerate(cols)}


def read_report_file(path):
    hdr, rows = None, []
    with open(path, "r", errors="ignore") as fh:
        for l in fh:
            s = l.strip()
            if s.startswith('("Iteration"'):
                hdr = re.findall(r'"([^"]+)"', s)
                continue
            if hdr and re.match(r"^\d+\s", s):
                rows.append([float(x) for x in s.split()])
    return hdr, np.array(rows)


def read_residuals(path):
    hdr, rows, hdrs = None, [], {}
    with open(path, "r", errors="ignore") as fh:
        for l in fh:
            if "iter" in l and "continuity" in l and not l.lstrip().startswith(">>>"):
                hdr = l.split()
                continue
            if hdr is None:
                continue
            if re.match(r"^\s*(\d+)\s+\d\.\d{4}e[-+]\d\d", l):
                tok = l.split()
                n = len(hdr) - 2
                try:
                    vals = [float(x) for x in tok[1:1 + n]]
                except ValueError:
                    continue
                d = dict(zip(hdr[1:1 + n], vals))
                d["iter"] = int(tok[0])
                rows.append(d)
    return rows


# ============================================================================
# load
# ============================================================================
print("loading Fluent exports ...")
F = read_fluent_ascii(os.path.join(EXP, "cells_fluid.csv"))
Sd = read_fluent_ascii(os.path.join(EXP, "cells_solid.csv"))
WI = read_fluent_ascii(os.path.join(EXP, "wall_interface.csv"))
WO = read_fluent_ascii(os.path.join(EXP, "wall_outer.csv"))
WE = read_fluent_ascii(os.path.join(EXP, "wall_solid_ends.csv"))
BI = read_fluent_ascii(os.path.join(EXP, "boundary_inlet.csv"))
BO = read_fluent_ascii(os.path.join(EXP, "boundary_outlet.csv"))
for nm, d in (("fluid cells", F), ("solid cells", Sd), ("interface faces", WI), ("outer faces", WO),
              ("end faces", WE), ("inlet faces", BI), ("outlet faces", BO)):
    print("   %-16s %7d rows, columns: %s" % (nm, len(next(iter(d.values()))), list(d.keys())))

hdrM, MONr = read_report_file(os.path.join(MONd, "baseline_monitors.out"))
mc = {n: i for i, n in enumerate(hdrM)}
RES = read_residuals(os.path.join(BASE, "Logs", "baseline_stdout.txt"))
runsum = json.load(open(os.path.join(AUD, "run_summary.json")))

# analytical, frozen Section 2
ana = {}
with open(os.path.join(ROOT, "02_Engineering_Calculations", "baseline_results.csv")) as fh:
    for r in csv.reader(fh):
        if len(r) == 4 and r[0] and not r[0].startswith("#") and r[0] != "section":
            try:
                ana[r[1]] = float(r[2])
            except ValueError:
                pass
AP = np.genfromtxt(os.path.join(ROOT, "02_Engineering_Calculations", "axial_profiles.csv"), delimiter=",",
                   names=True)

# ============================================================================
# derived cell quantities
# ============================================================================
def cyl(d):
    x, y = d["x-coordinate"], d["y-coordinate"]
    return np.hypot(x, y), np.degrees(np.arctan2(y, x)) % 360.0


F["r"], F["th"] = cyl(F)
Sd["r"], Sd["th"] = cyl(Sd)
WI["r"], WI["th"] = cyl(WI)
WO["r"], WO["th"] = cyl(WO)
F["vr"] = (F["x-coordinate"] * F["x-velocity"] + F["y-coordinate"] * F["y-velocity"]) / np.maximum(F["r"], 1e-12)
F["vt"] = (F["x-coordinate"] * F["y-velocity"] - F["y-coordinate"] * F["x-velocity"]) / np.maximum(F["r"], 1e-12)

NZ = 90
dz = L / NZ
zc = (np.arange(NZ) + 0.5) * dz
kF = np.clip((F["z-coordinate"] / dz).astype(int), 0, NZ - 1)
kS = np.clip((Sd["z-coordinate"] / dz).astype(int), 0, NZ - 1)
kI = np.clip((WI["z-coordinate"] / dz).astype(int), 0, NZ - 1)
kO = np.clip((WO["z-coordinate"] / dz).astype(int), 0, NZ - 1)

# sign convention of Fluent's wall heat flux, fixed by comparison with Fluent's own flux report
last = MONr[-1]
q_if_report = last[mc["q_interface"]]
q_if_faces = np.sum(WI["heat-flux"] * WI["face-area-magnitude"])
SIGN_I = 1.0 if q_if_faces * q_if_report >= 0 else -1.0
q_o_report = last[mc["q_heated_wall"]]
q_o_faces = np.sum(WO["heat-flux"] * WO["face-area-magnitude"])
SIGN_O = 1.0 if q_o_faces * q_o_report >= 0 else -1.0
print("   heat-flux sign: interface %+d (faces %.4f W vs report %.4f W); outer %+d (faces %.4f vs %.4f)"
      % (SIGN_I, q_if_faces, q_if_report, SIGN_O, q_o_faces, q_o_report))
WI["q"] = SIGN_I * WI["heat-flux"]
WO["q"] = SIGN_O * WO["heat-flux"]

# ============================================================================
# axial profiles, slab by slab (every slab has identical dz, so volume weighting
# is area weighting)
# ============================================================================
V = F["cell-volume"]
mflux = F["density"] * F["z-velocity"] * V
prof = {k: np.zeros(NZ) for k in ("z", "mdot", "p_area", "p_mass", "Tb_mass", "hb", "rho_b", "w_b",
                                  "w_max", "Twi", "Two", "qi", "qo", "yplus_avg", "yplus_min", "yplus_max",
                                  "tau_w", "Tsolid_mean", "Tsolid_max", "Tfluid_max")}
for k in range(NZ):
    m = kF == k
    vol = V[m].sum()
    prof["z"][k] = zc[k]
    prof["mdot"][k] = mflux[m].sum() / dz
    prof["p_area"][k] = np.sum(F["pressure"][m] * V[m]) / vol
    prof["p_mass"][k] = np.sum(F["pressure"][m] * mflux[m]) / mflux[m].sum()
    prof["Tb_mass"][k] = np.sum(F["temperature"][m] * mflux[m]) / mflux[m].sum()
    prof["hb"][k] = np.sum(F["enthalpy"][m] * mflux[m]) / mflux[m].sum()
    prof["rho_b"][k] = np.sum(F["density"][m] * V[m]) / vol
    prof["w_b"][k] = np.sum(F["z-velocity"][m] * V[m]) / vol
    prof["w_max"][k] = F["z-velocity"][m].max()
    prof["Tfluid_max"][k] = F["temperature"][m].max()
    mi = kI == k
    ai = WI["face-area-magnitude"][mi]
    prof["Twi"][k] = np.sum(WI["temperature"][mi] * ai) / ai.sum()
    prof["qi"][k] = np.sum(WI["q"][mi] * ai) / ai.sum()
    prof["yplus_avg"][k] = np.sum(WI["y-plus"][mi] * ai) / ai.sum()
    prof["yplus_min"][k] = WI["y-plus"][mi].min()
    prof["yplus_max"][k] = WI["y-plus"][mi].max()
    prof["tau_w"][k] = np.sum(np.abs(WI["z-wall-shear"][mi]) * ai) / ai.sum()
    mo = kO == k
    ao = WO["face-area-magnitude"][mo]
    prof["Two"][k] = np.sum(WO["temperature"][mo] * ao) / ao.sum()
    prof["qo"][k] = np.sum(WO["q"][mo] * ao) / ao.sum()
    ms = kS == k
    prof["Tsolid_mean"][k] = np.sum(Sd["temperature"][ms] * Sd["cell-volume"][ms]) / Sd["cell-volume"][ms].sum()
    prof["Tsolid_max"][k] = Sd["temperature"][ms].max()

A_poly = math.pi * RI ** 2 * AREA48
# mass flux from Fluent's conservative flux report and Fluent's own inlet face area (authoritative);
# the cell-data reconstruction sum(rho w V)/dz agrees to ~0.01 % and is kept only as a check (prof["mdot"])
G = float(last[mc["mdot_in"]]) / float(BI["face-area-magnitude"].sum())
# incompressible ideal gas: rho = p_op / (R T). Recover Fluent's R from the inlet faces so the
# bulk density is evaluated exactly as the solver evaluates it, at the mixing-cup temperature.
_mi = np.sum(BI["density"] * BI["z-velocity"] * BI["face-area-magnitude"])
_Ti = np.sum(BI["temperature"] * BI["density"] * BI["z-velocity"] * BI["face-area-magnitude"]) / _mi
R_FLUENT = 101325.0 / (float(np.mean(BI["density"])) * _Ti)
prof["rho_b_volavg"] = prof["rho_b"].copy()
prof["rho_b"] = 101325.0 / (R_FLUENT * prof["Tb_mass"])
prof["dTwall"] = prof["Two"] - prof["Twi"]
prof["h"] = prof["qi"] / (prof["Twi"] - prof["Tb_mass"])
prof["Nu"] = prof["h"] * D / kair(prof["Tb_mass"])
prof["Nu_Dh48"] = prof["h"] * DH48 / kair(prof["Tb_mass"])
prof["Re"] = G * D / muair(prof["Tb_mass"])
prof["f_shear"] = 8.0 * prof["tau_w"] * prof["rho_b"] / G ** 2
prof["x_over_D"] = prof["z"] / D
# analytical through-wall dT using k at the CFD's own local mean solid temperature
prof["dTwall_1D_localk"] = QPP_O * RO * math.log(RO / RI) / kinc(prof["Tsolid_mean"])

keys = ["z", "x_over_D", "mdot", "p_area", "p_mass", "Tb_mass", "hb", "rho_b", "rho_b_volavg", "w_b", "w_max", "Twi", "Two",
        "dTwall", "dTwall_1D_localk", "qi", "qo", "h", "Nu", "Nu_Dh48", "Re", "tau_w", "f_shear",
        "yplus_avg", "yplus_min", "yplus_max", "Tsolid_mean", "Tsolid_max", "Tfluid_max"]
with open(os.path.join(PRO, "axial_profiles_cfd.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# CFD axial profiles, slab averages over the 90 axial slabs of the medium mesh. "
                "Source: Fluent cell/face exports of the converged baseline. RE-ANALYSIS 2026."])
    w.writerow(keys)
    for k in range(NZ):
        w.writerow(["%.8g" % prof[c][k] for c in keys])
print("   wrote Profiles/axial_profiles_cfd.csv")

# fully developed window, A-017: x/D > 18, and clear of the outlet end (x/D < 29)
fd = (prof["x_over_D"] > 18.0) & (prof["x_over_D"] < 29.0)


def gnielinski(Re, Pr):
    f = (0.790 * np.log(Re) - 1.64) ** -2
    return (f / 8) * (Re - 1000) * Pr / (1 + 12.7 * np.sqrt(f / 8) * (Pr ** (2. / 3) - 1)), f


Nu_gn, f_pet = gnielinski(prof["Re"], prair(prof["Tb_mass"]))
f_pet_heat = f_pet * (prof["Twi"] / prof["Tb_mass"]) ** (-0.1)
Nu_db = 0.023 * prof["Re"] ** 0.8 * prair(prof["Tb_mass"]) ** 0.4
Nu_corr = Nu_gn * (prof["Tb_mass"] / prof["Twi"]) ** 0.5
n_implied = np.log(prof["Nu"] / Nu_gn) / np.log(prof["Tb_mass"] / prof["Twi"])
FD = dict(Nu_cfd=float(np.mean(prof["Nu"][fd])), Nu_gn=float(np.mean(Nu_gn[fd])), Nu_db=float(np.mean(Nu_db[fd])),
          Nu_corr_n05=float(np.mean(Nu_corr[fd])), n_implied=float(np.mean(n_implied[fd])),
          f_cfd=float(np.mean(prof["f_shear"][fd])), f_petukhov=float(np.mean(f_pet[fd])),
          f_petukhov_heating_m_minus0p1=float(np.mean(f_pet_heat[fd])), R_fluent=R_FLUENT,
          Tw_over_Tb_fd=float(np.mean(prof["Twi"][fd] / prof["Tb_mass"][fd])),
          h_cfd_end_of_window=float(prof["h"][fd][-1]), Nu_cfd_end_of_window=float(prof["Nu"][fd][-1]),
          h_cfd_last_slab=float(prof["h"][-1]), Nu_cfd_last_slab=float(prof["Nu"][-1]),
          x_over_D_window=[float(prof["x_over_D"][fd][0]), float(prof["x_over_D"][fd][-1])])
print("   fully developed (x/D 18-29):", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in FD.items()})

# ============================================================================
# global quantities from the exports
# ============================================================================
A_in = BI["face-area-magnitude"].sum()
A_out = BO["face-area-magnitude"].sum()
mdot_in_faces = np.sum(BI["density"] * BI["z-velocity"] * BI["face-area-magnitude"])
mdot_out_faces = np.sum(BO["density"] * BO["z-velocity"] * BO["face-area-magnitude"])
M_in = np.sum(BI["density"] * BI["z-velocity"] ** 2 * BI["face-area-magnitude"])
M_out = np.sum(BO["density"] * BO["z-velocity"] ** 2 * BO["face-area-magnitude"])
p_in_a = np.sum(BI["pressure"] * BI["face-area-magnitude"]) / A_in
p_out_a = np.sum(BO["pressure"] * BO["face-area-magnitude"]) / A_out
F_wall = np.sum(WI["z-wall-shear"] * WI["face-area-magnitude"])
rho_in_b = mdot_in_faces / np.sum(BI["z-velocity"] * BI["face-area-magnitude"])
rho_out_b = mdot_out_faces / np.sum(BO["z-velocity"] * BO["face-area-magnitude"])
Gi = mdot_in_faces / A_in
beta_in = M_in / (mdot_in_faces ** 2 / (rho_in_b * A_in))
beta_out = M_out / (mdot_out_faces ** 2 / (rho_out_b * A_out))
dp_total = p_in_a - p_out_a
dp_wall = abs(F_wall) / A_in
dp_momentum = (M_out - M_in) / A_in
dp_accel_1D = Gi ** 2 * (1.0 / rho_out_b - 1.0 / rho_in_b)
dp_profile = dp_momentum - dp_accel_1D
mom_closure = dp_total - dp_wall - dp_momentum
PD = dict(dp_total_area=dp_total, dp_total_mass=float(last[mc["p_in"]] - last[mc["p_out"]]),
          dp_wall_shear=dp_wall, dp_momentum_flux=dp_momentum, dp_accel_1D_cfd_densities=dp_accel_1D,
          dp_profile_development=dp_profile, momentum_balance_residual=mom_closure,
          momentum_balance_residual_pct=100 * mom_closure / dp_total, F_wall_N=F_wall,
          F_wall_monitor_N=float(last[mc["F_wall_z"]]), beta_in=beta_in, beta_out=beta_out,
          rho_in_b=rho_in_b, rho_out_b=rho_out_b, A_in=A_in, A_out=A_out)
print("   pressure decomposition:", {k: round(v, 5) for k, v in PD.items()})

mdot_in = last[mc["mdot_in"]]
mdot_out = -last[mc["mdot_out"]]
Q_wall = last[mc["q_heated_wall"]]
Q_if = last[mc["q_interface"]]
Q_fluid = -last[mc["q_fluid_net"]]
Q_ends = last[mc["q_ends"]]
Q_net = last[mc["q_net_all"]]
A_outer = WO["face-area-magnitude"].sum()
A_inner = WI["face-area-magnitude"].sum()
CONS = dict(mdot_in=mdot_in, mdot_out=mdot_out,
            mass_imbalance_pct=100 * abs(mdot_in - mdot_out) / mdot_in,
            mdot_from_faces_in=mdot_in_faces, mdot_from_faces_out=mdot_out_faces,
            Q_wall=Q_wall, Q_interface=Q_if, Q_fluid=Q_fluid, Q_ends=Q_ends, Q_net_all=Q_net,
            energy_imbalance_W=Q_wall - Q_fluid, energy_imbalance_pct=100 * (Q_wall - Q_fluid) / Q_wall,
            net_all_boundaries_pct=100 * Q_net / Q_wall,
            interface_vs_wall_pct=100 * (Q_if - Q_wall) / Q_wall,
            A_outer_mesh=A_outer, A_outer_exact=2 * math.pi * RO * L, lateral_ratio_mesh=A_outer / (2 * math.pi * RO * L),
            lateral_ratio_48gon=LAT48, Q_wall_expected_from_area=QPP_O * A_outer,
            Q_analytical=ana.get("Q_total"), Q_wall_vs_analytical_pct=100 * (Q_wall / ana["Q_total"] - 1),
            A_in_mesh=A_in, A_in_exact=math.pi * RI ** 2, planar_ratio_mesh=A_in / (math.pi * RI ** 2),
            planar_ratio_48gon=AREA48)
# independent check of Q_fluid: mdot * (h_out - h_in) from Fluent's own enthalpy field
h_in_b = np.sum(BI["enthalpy"] * BI["density"] * BI["z-velocity"] * BI["face-area-magnitude"]) / mdot_in_faces
h_out_b = np.sum(BO["enthalpy"] * BO["density"] * BO["z-velocity"] * BO["face-area-magnitude"]) / mdot_out_faces
CONS["Q_fluid_from_enthalpy_faces"] = mdot_in_faces * (h_out_b - h_in_b)
print("   conservation:", {k: (round(v, 7) if isinstance(v, float) else v) for k, v in CONS.items()})

# mixing-cup temperatures from Fluent's sensible enthalpy (reference 298.15 K), inverted with the
# same piecewise-linear cp the solver uses
_Tg = np.linspace(250.0, 600.0, 70001)
_cp = cpair(_Tg)
_hg = np.concatenate([[0.0], np.cumsum(0.5 * (_cp[1:] + _cp[:-1]) * np.diff(_Tg))])
_hg -= np.interp(298.15, _Tg, _hg)
T_of_h = lambda h: float(np.interp(h, _hg, _Tg))
h_of_T = lambda T: float(np.interp(T, _Tg, _hg))
MC = dict(h_in_b=h_in_b, h_out_b=h_out_b, T_in_mixing_cup=T_of_h(h_in_b), T_out_mixing_cup=T_of_h(h_out_b),
          T_out_from_cfd_energy_balance=T_of_h(h_of_T(300.0) + Q_wall / mdot_in),
          T_out_from_analytical_energy_balance=T_of_h(h_of_T(300.0) + ana["Q_total"] / ana["m_dot"]))
MC["faceting_shift_K"] = MC["T_out_from_cfd_energy_balance"] - MC["T_out_from_analytical_energy_balance"]
print("   mixing-cup:", MC)
# temperatures
T_in_b = np.sum(BI["temperature"] * BI["density"] * BI["z-velocity"] * BI["face-area-magnitude"]) / mdot_in_faces
T_out_b = np.sum(BO["temperature"] * BO["density"] * BO["z-velocity"] * BO["face-area-magnitude"]) / mdot_out_faces
iSmax = int(np.argmax(Sd["temperature"]))
TEMP = dict(T_in_bulk=T_in_b, T_out_bulk=T_out_b, T_out_bulk_monitor=float(last[mc["T_out_bulk"]]),
            T_fluid_min=float(F["temperature"].min()), T_fluid_max=float(F["temperature"].max()),
            T_solid_min=float(Sd["temperature"].min()), T_solid_max=float(Sd["temperature"].max()),
            T_solid_max_location_mm=dict(r=1e3 * float(Sd["r"][iSmax]), z=1e3 * float(Sd["z-coordinate"][iSmax]),
                                         theta_deg=float(Sd["th"][iSmax])),
            T_solid_mean_volume=float(np.sum(Sd["temperature"] * Sd["cell-volume"]) / Sd["cell-volume"].sum()),
            T_inner_wall_min=float(WI["temperature"].min()), T_inner_wall_max=float(WI["temperature"].max()),
            T_outer_wall_min=float(WO["temperature"].min()), T_outer_wall_max=float(WO["temperature"].max()),
            T_inner_wall_area_avg=float(np.sum(WI["temperature"] * WI["face-area-magnitude"]) / A_inner),
            T_outer_wall_area_avg=float(np.sum(WO["temperature"] * WO["face-area-magnitude"]) / A_outer),
            T_end_faces_max=float(WE["temperature"].max()))
# through-wall dT at the exit station clear of the end face, and at mid length
def at_z(arr, zq):
    return float(np.interp(zq, prof["z"], arr))


TW = dict(dT_wall_z300=at_z(prof["dTwall"], 0.300), dT_wall_z570=at_z(prof["dTwall"], 0.570),
          dT_wall_last_slab=float(prof["dTwall"][-1]), dT_wall_max=float(prof["dTwall"].max()),
          dT_wall_min=float(prof["dTwall"].min()),
          dT_1D_localk_z570=at_z(prof["dTwall_1D_localk"], 0.570),
          Twi_z570=at_z(prof["Twi"], 0.570), Two_z570=at_z(prof["Two"], 0.570),
          Tb_z570=at_z(prof["Tb_mass"], 0.570),
          Twi_last_slab=float(prof["Twi"][-1]), Two_last_slab=float(prof["Two"][-1]))
print("   through-wall:", {k: round(v, 4) for k, v in TW.items()})

# y+
yp, ya = WI["y-plus"], WI["face-area-magnitude"]
YP = dict(min=float(yp.min()), max=float(yp.max()), area_mean=float(np.sum(yp * ya) / ya.sum()),
          median=float(np.median(yp)), p05=float(np.percentile(yp, 5)), p95=float(np.percentile(yp, 95)),
          p99=float(np.percentile(yp, 99)), frac_area_le_1=float(np.sum(ya[yp <= 1.0]) / ya.sum()),
          frac_area_le_0p5=float(np.sum(ya[yp <= 0.5]) / ya.sum()),
          fd_mean=float(np.mean(prof["yplus_avg"][fd])),
          location_of_max_mm=dict(z=1e3 * float(WI["z-coordinate"][np.argmax(yp)]),
                                  theta_deg=float(WI["th"][np.argmax(yp)])),
          location_of_min_mm=dict(z=1e3 * float(WI["z-coordinate"][np.argmin(yp)]),
                                  theta_deg=float(WI["th"][np.argmin(yp)])),
          first_cell_centre_distance_um=dict(min=1e6 * float(WI["cell-wall-distance"].min()),
                                             max=1e6 * float(WI["cell-wall-distance"].max())))
print("   y+:", YP)
k300 = int(np.argmin(abs(zc - 0.3)))
m300 = kI == k300
yw = WI["cell-wall-distance"][m300] * 1e6
tw = np.abs(WI["z-wall-shear"][m300])
th300 = WI["th"][m300]
NW = dict(slab_z_mm=float(zc[k300] * 1e3), ywall_min_um=float(yw.min()), ywall_max_um=float(yw.max()),
          first_layer_equiv_min_um=float(2 * yw.min()), first_layer_equiv_max_um=float(2 * yw.max()),
          theta_of_min_ywall=float(th300[np.argmin(yw)]), theta_of_max_ywall=float(th300[np.argmax(yw)]),
          tau_ptp_pct=float(100 * np.ptp(tw) / tw.mean()),
          yplus_ptp_pct=float(100 * np.ptp(WI["y-plus"][m300]) / WI["y-plus"][m300].mean()),
          superellipse_prediction_ratio=float((RI - 0.45 * RI / (2 * (0.5 ** 0.5) ** 4) ** 0.25) / (RI - 0.45 * RI)))
print("   near-wall geometry at z=300 mm:", NW)
hist, edges = np.histogram(yp, bins=np.linspace(0, max(1.2, yp.max() * 1.02), 49), weights=ya)
with open(os.path.join(PRO, "yplus_distribution.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# area-weighted y+ distribution on FLUID_SOLID_INTERFACE, converged baseline"])
    w.writerow(["yplus_lo", "yplus_hi", "area_m2", "area_fraction"])
    for i in range(len(hist)):
        w.writerow(["%.5f" % edges[i], "%.5f" % edges[i + 1], "%.6e" % hist[i], "%.6f" % (hist[i] / ya.sum())])

# velocity statistics
w_out = BO["z-velocity"]
VEL = dict(w_in_min=float(BI["z-velocity"].min()), w_in_max=float(BI["z-velocity"].max()),
           w_out_area_mean=float(np.sum(w_out * BO["face-area-magnitude"]) / A_out),
           w_out_min=float(w_out.min()), w_out_max=float(w_out.max()),
           w_domain_max=float(F["z-velocity"].max()), w_domain_min=float(F["z-velocity"].min()),
           vmag_max=float(F["velocity-magnitude"].max()),
           reverse_flow_cells=int(np.sum(F["z-velocity"] < 0)),
           max_abs_radial_velocity=float(np.abs(F["vr"]).max()),
           max_abs_swirl_velocity=float(np.abs(F["vt"]).max()),
           centreline_to_bulk_exit=float(prof["w_max"][-1] / prof["w_b"][-1]),
           mach_at_max_velocity_outlet_bulkT=float(F["velocity-magnitude"].max() / math.sqrt(1.4 * 287.058 * T_out_b)))
print("   velocity:", VEL)

# Reynolds numbers - G as above (Fluent flux report / Fluent inlet face area)
RE = dict(Re_in_nominalD=G * D / float(muair(T_in_b)), Re_in_Dh48=G * DH48 / float(muair(T_in_b)),
          Re_out_nominalD=G * D / float(muair(T_out_b)), Re_out_Dh48=G * DH48 / float(muair(T_out_b)), G=G)

# ============================================================================
# residuals and monitors -> CSV
# ============================================================================
with open(os.path.join(MONd, "baseline_monitors.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(hdrM)
    for r in MONr:
        w.writerow(["%d" % r[0]] + ["%.10g" % v for v in r[1:]])
EQ = ["continuity", "x-velocity", "y-velocity", "z-velocity", "energy", "k", "omega"]
with open(os.path.join(MONd, "residual_history.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["iteration"] + EQ)
    for d in RES:
        w.writerow([d["iter"]] + ["%.5e" % d[e] if e in d else "" for e in EQ])
print("   wrote Monitors/baseline_monitors.csv (%d rows), residual_history.csv (%d rows)" % (len(MONr), len(RES)))
lastres = RES[-1] if RES else {}

# full-history temperature maxima (startup excursion check)
HIST = dict(max_T_solid_history=float(MONr[:, mc["T_solid_max"]].max()),
            iter_of_max_T_solid=int(MONr[np.argmax(MONr[:, mc["T_solid_max"]]), 0]),
            final_T_solid_max_monitor=float(last[mc["T_solid_max"]]),
            max_T_fluid_history=float(MONr[:, mc["T_fluid_max"]].max()),
            min_T_fluid_history=float(MONr[:, mc["T_fluid_min"]].min()),
            min_T_solid_history=float(MONr[:, mc["T_solid_min"]].min()),
            section5A_startup_peak_K=761.0)
HIST["solid_overshoot_above_final_K"] = HIST["max_T_solid_history"] - HIST["final_T_solid_max_monitor"]
RANGE = dict(fluid_table_K=[250.0, 600.0], solid_table_K=[293.15, 673.15],
             final_fluid_within=bool(TEMP["T_fluid_min"] >= 250 and TEMP["T_fluid_max"] <= 600),
             final_solid_within=bool(TEMP["T_solid_min"] >= 293.15 and TEMP["T_solid_max"] <= 673.15),
             history_fluid_within=bool(HIST["min_T_fluid_history"] >= 250 and HIST["max_T_fluid_history"] <= 600),
             history_solid_within=bool(HIST["min_T_solid_history"] >= 293.15 and HIST["max_T_solid_history"] <= 673.15))
lim_hits = []
with open(os.path.join(BASE, "Logs", "baseline_stdout.txt"), "r", errors="ignore") as fh:
    for i, l in enumerate(fh):
        ll = l.lower()
        st = l.strip()
        if st.startswith("#") or st.startswith(">>>") or "license" in ll:
            continue
        if ("temperature limited" in ll or "viscosity limited" in ll or "divergence detected" in ll
                or "floating point" in ll or "reversed flow" in ll or re.search(r"\bnan\b", ll)):
            lim_hits.append("%d: %s" % (i + 1, st[:160]))
RANGE["solver_limit_or_divergence_messages"] = lim_hits[:50]
RANGE["n_limit_messages"] = len(lim_hits)
nan_count = sum(int(np.sum(~np.isfinite(v))) for d in (F, Sd, WI, WO, BI, BO) for v in d.values())
RANGE["nan_or_inf_values_in_exports"] = nan_count
print("   range check:", RANGE)

# ============================================================================
# CFD vs analytical
# ============================================================================
Tsmax_ana = ana["T_wall_outer_exit"]
ANA570 = dict(Twi=float(np.interp(0.570, AP["x_m"], AP["Twi_corrected_K"])),
              dTwall=float(np.interp(0.570, AP["x_m"], AP["Two_corrected_K"] - AP["Twi_corrected_K"])),
              h=float(np.interp(0.570, AP["x_m"], AP["h_corrected"])),
              h_cfd=float(at_z(prof["h"], 0.570)))
TW["h_cfd_z570"] = ANA570["h_cfd"]
TW["analytical_z570"] = dict(ANA570)
rows_cmp = [
    ("Reynolds number, inlet", ana["Re_in"], RE["Re_in_nominalD"], "-",
     "CFD from Fluent mass flux G = mdot/A_poly and mu(T_in) from the same Incropera table; nominal D = 20 mm"),
    ("Reynolds number, outlet", ana["Re_out"], RE["Re_out_nominalD"], "-",
     "mu at the CFD mass-weighted outlet temperature"),
    ("Pressure drop, inlet-to-outlet static (CFD-comparable)", ana["dp_total_CFD_comparable"], dp_total, "Pa",
     "area-weighted static pressure, inlet face minus outlet face; analytical = friction + acceleration + entry"),
    ("Outlet bulk temperature", ana["T_out_bulk"], T_out_b, "K",
     "mass-weighted static temperature over the outlet faces (Fluent's standard bulk measure)"),
    ("Outlet mixing-cup temperature", ana["T_out_bulk"], MC["T_out_mixing_cup"], "K",
     "additional: from Fluent's enthalpy, mass-flux weighted and inverted with the same cp table - the like-for-like "
     "counterpart of the 1-D energy march"),
    ("Heat-transfer rate", ana["Q_total"], Q_wall, "W",
     "Fluent heat flux through HEATED_OUTER_WALL; equals the heat carried out by the air to the stated imbalance"),
    ("Maximum solid temperature", Tsmax_ana, TEMP["T_outer_wall_max"], "K",
     "analytical = outer-wall temperature at the exit station (1-D); CFD = maximum facet temperature of HEATED_OUTER_WALL "
     "(outlet end); the maximum cell-centre value is %.3f K" % TEMP["T_solid_max"]),
    ("Through-wall temperature difference", ana["dT_through_wall"], TW["dT_wall_z570"], "K",
     "analytical = Section 2 headline value (exit; k = 15.22 W/m.K at the 574.4 K inner wall); CFD: outer minus inner "
     "wall, circumferential average, at z = 570 mm (x/D = 28.5, clear of the adiabatic end)"),
    ("Through-wall temperature difference at z = 570 mm (station-matched)", ANA570["dTwall"], TW["dT_wall_z570"], "K",
     "additional: analytical from the Section 2 axial march at the same station (k at the local inner-wall temperature)"),
    ("Peak inner-wall temperature (PR-06)", ana["T_wall_inner_exit"], TEMP["T_inner_wall_max"], "K",
     "additional: analytical peak is at the exit; CFD = maximum facet temperature of the fluid-solid interface "
     "(outlet end)"),
    ("Inner-wall temperature at z = 570 mm (station-matched)", ANA570["Twi"], TW["Twi_z570"], "K",
     "additional: circumferential average; analytical = property-corrected march at the same station"),
    ("Heat-transfer coefficient at z = 570 mm (station-matched)", ANA570["h"], ANA570["h_cfd"], "W/m2K",
     "additional: CFD h = q_inner / (T_inner_wall - T_bulk,mass) per slab; analytical = property-corrected Gnielinski"),
    ("Fully developed Nusselt number (x/D 18-29)", ana["Nu_corrected_exit"], FD["Nu_cfd"], "-",
     "additional (PR-03): CFD mean over the window vs property-corrected Gnielinski at exit"),
    ("Darcy friction factor (x/D 18-29)", ana["f_mean"], FD["f_cfd"], "-",
     "additional (PR-04): CFD from wall shear, f = 8 tau_w rho_b / G^2"),
]
with open(os.path.join(BL, "CFD_vs_Analytical.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# Section 2 ANALYTICAL baseline vs Section 5B CFD (medium mesh, converged). RE-ANALYSIS 2026."])
    w.writerow(["quantity", "analytical_section2", "cfd_section5B", "units", "absolute_difference",
                "percent_difference", "basis"])
    for q, a, c, u, b in rows_cmp:
        w.writerow([q, "%.6g" % a, "%.6g" % c, u, "%.6g" % (c - a), "%.3f" % (100 * (c - a) / a), b])
print("   wrote Baseline/CFD_vs_Analytical.csv")

RESULTS = dict(run=runsum, residuals_final=lastres, conservation=CONS, pressure=PD, temperatures=TEMP, near_wall=NW,
               mixing_cup=MC,
               through_wall=TW, yplus=YP, velocity=VEL, reynolds=RE, fully_developed=FD, history=HIST,
               range_check=RANGE, faceting=dict(planar=AREA48, lateral=LAT48, Dh48=DH48),
               comparison=[dict(quantity=q, analytical=a, cfd=c, units=u, abs_diff=c - a,
                                pct_diff=100 * (c - a) / a, basis=b) for q, a, c, u, b in rows_cmp])
with open(os.path.join(BL, "cfd_baseline_results.json"), "w") as fh:
    json.dump(RESULTS, fh, indent=2, default=float)
print("   wrote Baseline/cfd_baseline_results.json")

# ============================================================================
# FIGURES - every one from the exported Fluent data above
# ============================================================================
def theta_avg(d, fields, rnd=1e-6):
    """Aggregate cells sharing (r, z) to within 1 um - removes the circumferential copies of an
    axisymmetric solution so the (r, z) triangulation is well posed."""
    rk = np.round(d["r"] / rnd).astype(np.int64)
    zk = np.round(d["z-coordinate"] / rnd).astype(np.int64)
    key = rk * 10 ** 7 + zk
    u, inv = np.unique(key, return_inverse=True)
    cnt = np.bincount(inv)
    out = {"r": np.bincount(inv, d["r"]) / cnt, "z": np.bincount(inv, d["z-coordinate"]) / cnt}
    for f in fields:
        out[f] = np.bincount(inv, d[f]) / cnt
    return out


FA = theta_avg(F, ["z-velocity", "vr", "pressure", "temperature", "density", "turb-kinetic-energy"])
SA = theta_avg(Sd, ["temperature"])


def rz_contour(ax, A, field, zlim, rlim, levels, cmap, rscale=1e3, zscale=1e3, mirror=True):
    m = (A["z"] >= zlim[0] - 1e-9) & (A["z"] <= zlim[1] + 1e-9) & (A["r"] >= rlim[0] - 1e-9) & (A["r"] <= rlim[1] + 1e-9)
    z, r, v = A["z"][m], A["r"][m], A[field][m]
    if mirror:
        z, r, v = np.concatenate([z, z]), np.concatenate([r, -r]), np.concatenate([v, v])
    # triangulate in normalised coordinates so thin, long domains triangulate sensibly
    zn = (z - zlim[0]) / (zlim[1] - zlim[0])
    rn = r / (rlim[1] if rlim[1] > 0 else 1.0)
    tri = mtri.Triangulation(zn, rn)
    tri_plot = mtri.Triangulation(z * zscale, r * rscale, tri.triangles)
    return ax.tricontourf(tri_plot, v, levels=levels, cmap=cmap)


# ---- 1 velocity contour
fig, axes = plt.subplots(3, 1, figsize=(12.5, 9.4), gridspec_kw=dict(height_ratios=[1.1, 1, 1], hspace=0.42))
lv = np.linspace(0, float(np.ceil(F["z-velocity"].max())), 29)
cs = rz_contour(axes[0], FA, "z-velocity", (0, L), (0, RI), lv, "viridis")
axes[0].set_title("(a) full 600 mm duct - radial scale strongly exaggerated relative to axial", fontsize=9.5)
cs = rz_contour(axes[1], FA, "z-velocity", (0, 0.06), (0, RI), lv, "viridis")
axes[1].set_title("(b) inlet region 0-60 mm: boundary layer growing from the plug inlet profile", fontsize=9.5)
cs = rz_contour(axes[2], FA, "z-velocity", (0.54, 0.60), (0, RI), lv, "viridis")
axes[2].set_title("(c) outlet region 540-600 mm: developed, heated flow, accelerated by falling density", fontsize=9.5)
for ax in axes:
    ax.set_ylabel("r [mm]")
axes[-1].set_xlabel("z [mm]")
cb = fig.colorbar(cs, ax=axes, shrink=0.9, pad=0.012)
cb.set_label("axial velocity w [m/s]")
fig.suptitle("Figure 1 - Axial velocity, meridional plane (circumferentially averaged cell values)", fontsize=11.5, y=0.995)
finish(fig, "fig01_velocity_contour.png", "Mirrored about the axis for display. Maximum w = %.2f m/s at the outlet centreline; "
       "inlet is a uniform 23.5 m/s." % VEL["w_domain_max"])

# ---- 2 velocity vectors
fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.2), gridspec_kw=dict(width_ratios=[1.9, 1], wspace=0.30))
ax = axes[0]
zg = np.linspace(0.0005, 0.0295, 11)
rg = np.concatenate([np.linspace(0.0003, 0.0085, 9), [0.0092, 0.0096, 0.0099]])
ZZ, RR = np.meshgrid(zg, rg)
pts = np.column_stack([FA["z"], FA["r"]])
WW = griddata(pts, FA["z-velocity"], (ZZ, RR), method="linear")
VR = griddata(pts, FA["vr"], (ZZ, RR), method="linear")
q = ax.quiver(ZZ * 1e3, RR * 1e3, WW, VR, WW, cmap="viridis", scale=420, width=0.0032, pivot="tail")
ax.set_xlim(0, 33); ax.set_ylim(0, 10.4); ax.set_aspect("equal")
ax.axhline(RI * 1e3, color="k", lw=1.2)
ax.set_xlabel("z [mm]"); ax.set_ylabel("r [mm]")
ax.set_title("(a) (w, v_r) vectors, inlet 0-30 mm, true aspect ratio: arrow length ~ speed;\n"
             "the arrows nearest the wall shorten downstream as the boundary layer grows", fontsize=9.5)
fig.colorbar(q, ax=ax, shrink=0.8, label="w [m/s]")
ax = axes[1]
zsel = kF == int(np.argmin(abs(zc - 0.3)))
ux, uy = F["x-velocity"][zsel], F["y-velocity"][zsel]
xs, ys = F["x-coordinate"][zsel] * 1e3, F["y-coordinate"][zsel] * 1e3
sub = np.arange(len(xs)) % 3 == 0
mag = np.hypot(ux, uy)
rsl = np.hypot(xs, ys) / 1e3
vr_s = (xs / 1e3 * ux + ys / 1e3 * uy) / np.maximum(rsl, 1e-12)
vt_s = (xs / 1e3 * uy - ys / 1e3 * ux) / np.maximum(rsl, 1e-12)
SEC = dict(z_mm=float(zc[np.argmin(abs(zc - 0.3))] * 1e3), max_inplane=float(mag.max()),
           max_radial=float(np.abs(vr_s).max()), max_tangential=float(np.abs(vt_s).max()),
           rms_radial=float(np.sqrt(np.mean(vr_s ** 2))), rms_tangential=float(np.sqrt(np.mean(vt_s ** 2))),
           bulk_w=float(prof["w_b"][int(np.argmin(abs(zc - 0.3)))]))
q2 = ax.quiver(xs[sub], ys[sub], ux[sub], uy[sub], mag[sub], cmap="magma", scale=None, width=0.004)
th = np.linspace(0, 2 * np.pi, 200)
ax.plot(10 * np.cos(th), 10 * np.sin(th), "k", lw=1.0)
ax.set_aspect("equal"); ax.set_xlim(-10.8, 10.8); ax.set_ylim(-10.8, 10.8)
ax.set_xlabel("x [mm]"); ax.set_ylabel("y [mm]")
ax.set_title("(b) in-plane velocity, z = %.0f mm\nmax radial %.1e m/s | max swirl %.1e m/s\n(bulk axial %.1f m/s)"
             % (SEC["z_mm"], SEC["max_radial"], SEC["max_tangential"], SEC["bulk_w"]), fontsize=9.0)
fig.colorbar(q2, ax=ax, shrink=0.8, label="|u_inplane| [m/s]")
fig.suptitle("Figure 2 - Velocity vectors", fontsize=11.5, y=1.02)
finish(fig, "fig02_velocity_vectors.png", "Panel (b): the in-plane motion is almost entirely RADIAL, which is "
       "physical and directed toward the axis: heating keeps lowering the near-wall density, the core keeps accelerating, "
       "and by continuity mass flux migrates inward. The swirl component, which an unswirled axisymmetric duct should not have, "
       "is %.1e of the bulk speed: numerical noise from the 48-gon section and the O-grid core."
       % (SEC["max_tangential"] / SEC["bulk_w"]))

# ---- 3 streamlines from the Stokes stream function
zgrid = np.linspace(0, L, 301)
rgrid = np.concatenate([np.linspace(0, 0.0090, 90), RI - np.geomspace(1e-3, 6e-6, 50)])
rgrid = np.unique(np.clip(rgrid, 0, RI))
ZG, RGd = np.meshgrid(zgrid, rgrid)
WG = griddata(np.column_stack([FA["z"] / L, FA["r"] / RI]), FA["z-velocity"], (ZG / L, RGd / RI), method="linear")
DG = griddata(np.column_stack([FA["z"] / L, FA["r"] / RI]), FA["density"], (ZG / L, RGd / RI), method="linear")
WG = np.nan_to_num(WG, nan=0.0); DG = np.nan_to_num(DG, nan=float(np.nanmean(DG)))
integrand = DG * WG * RGd
psi = np.concatenate([np.zeros((1, len(zgrid))),
                      np.cumsum(0.5 * (integrand[1:] + integrand[:-1]) * np.diff(rgrid)[:, None], axis=0)])
psi_n = psi / psi[-1][None, :]
fig, axes = plt.subplots(2, 1, figsize=(12.5, 7.0), gridspec_kw=dict(hspace=0.38))
for ax, zl in zip(axes, [(0, 0.6), (0, 0.06)]):
    sel = (zgrid >= zl[0]) & (zgrid <= zl[1])
    ax.contour(zgrid[sel] * 1e3, rgrid * 1e3, psi_n[:, sel], levels=np.linspace(0.1, 0.9, 9), colors=C1, linewidths=1.1)
    ax.contour(zgrid[sel] * 1e3, -rgrid * 1e3, psi_n[:, sel], levels=np.linspace(0.1, 0.9, 9), colors=C1, linewidths=1.1)
    ax.axhline(10, color="k", lw=1.2); ax.axhline(-10, color="k", lw=1.2)
    ax.set_ylabel("r [mm]"); ax.set_ylim(-10.5, 10.5)
axes[0].set_title("(a) full length - each line bounds a further 10 % of the mass flow", fontsize=9.5)
axes[1].set_title("(b) inlet 0-60 mm - lines bend towards the axis as the wall boundary layer displaces the flow", fontsize=9.5)
axes[1].set_xlabel("z [mm]")
fig.suptitle("Figure 3 - Streamlines of the mean flow (contours of the Stokes stream function "
             "psi = integral of rho w r dr)", fontsize=11.5, y=1.0)
finish(fig, "fig03_streamlines.png", "Stream function built from Fluent's density and axial velocity, "
       "circumferentially averaged. A straight duct's streamlines are straight except where the "
       "boundary layer thickens; the radial scale is stretched to make that visible.")

# ---- 4 pressure contour
fig, ax = plt.subplots(1, 1, figsize=(12.5, 3.6))
lv = np.linspace(float(FA["pressure"].min()), float(FA["pressure"].max()), 30)
cs = rz_contour(ax, FA, "pressure", (0, L), (0, RI), lv, "coolwarm")
ax.set_xlabel("z [mm]"); ax.set_ylabel("r [mm]")
fig.colorbar(cs, ax=ax, pad=0.01, label="static gauge pressure [Pa]")
ax.set_title("Figure 4 - Static pressure, meridional plane (radial scale exaggerated)", fontsize=11)
finish(fig, "fig04_pressure_contour.png", "Pressure is almost uniform across each section and falls "
       "monotonically along the duct, from %.1f Pa (area-average at the inlet) to 0 Pa gauge at the outlet." % p_in_a)

# ---- 5 fluid temperature contour
fig, axes = plt.subplots(2, 1, figsize=(12.5, 7.0), gridspec_kw=dict(hspace=0.38))
lv = np.linspace(300, float(np.ceil(F["temperature"].max())), 30)
cs = rz_contour(axes[0], FA, "temperature", (0, L), (0, RI), lv, "inferno")
axes[0].set_title("(a) full length", fontsize=9.5)
cs = rz_contour(axes[1], FA, "temperature", (0.54, 0.60), (0, RI), lv, "inferno")
axes[1].set_title("(b) outlet region 540-600 mm: a hot, thin wall layer over a core that is still near bulk temperature", fontsize=9.5)
for ax in axes:
    ax.set_ylabel("r [mm]")
axes[1].set_xlabel("z [mm]")
fig.colorbar(cs, ax=axes, shrink=0.9, pad=0.012, label="air temperature [K]")
fig.suptitle("Figure 5 - Air temperature, meridional plane", fontsize=11.5, y=0.995)
finish(fig, "fig05_fluid_temperature_contour.png", "Air range %.2f - %.2f K; outlet bulk (mass-weighted) %.3f K."
       % (TEMP["T_fluid_min"], TEMP["T_fluid_max"], T_out_b))

# ---- 6 solid temperature contour
fig = plt.figure(figsize=(13.0, 6.0))
ax = fig.add_axes([0.06, 0.55, 0.86, 0.36])
lv = np.linspace(float(np.floor(Sd["temperature"].min())), float(np.ceil(Sd["temperature"].max())), 30)
cs = rz_contour(ax, SA, "temperature", (0, L), (RI, RO), lv, "inferno", mirror=False)
ax.set_ylabel("r [mm]"); ax.set_xlabel("z [mm]")
ax.set_title("(a) Inconel 718 wall, r = 10-20 mm, full length", fontsize=9.5)
cax = fig.add_axes([0.93, 0.55, 0.012, 0.36]); fig.colorbar(cs, cax=cax, label="T [K]")
for i, zq in enumerate([0.05, 0.30, 0.57]):
    ax2 = fig.add_axes([0.06 + i * 0.30, 0.04, 0.24, 0.40])
    ks = int(np.argmin(abs(zc - zq)))
    msk = kS == ks
    tri = mtri.Triangulation(Sd["x-coordinate"][msk] * 1e3, Sd["y-coordinate"][msk] * 1e3)
    xm = Sd["x-coordinate"][msk][tri.triangles].mean(axis=1); ym = Sd["y-coordinate"][msk][tri.triangles].mean(axis=1)
    tri.set_mask(np.hypot(xm, ym) < RI * 1.02)
    loc = Sd["temperature"][msk]
    c2 = ax2.tricontourf(tri, loc, levels=np.linspace(loc.min() - 1e-6, loc.max() + 1e-6, 20), cmap="inferno")
    ax2.set_aspect("equal"); ax2.set_title("(%s) cross-section z = %.0f mm: %.2f - %.2f K" % ("bcd"[i], zc[ks] * 1e3, loc.min(), loc.max()), fontsize=8.8)
    ax2.set_xticks([]); ax2.set_yticks([])
    fig.colorbar(c2, ax=ax2, shrink=0.8)
fig.suptitle("Figure 6 - Solid (Inconel 718) temperature", fontsize=11.5, y=0.99)
finish(fig, "fig06_solid_temperature_contour.png", "Maximum solid temperature %.2f K at r = %.2f mm, z = %.1f mm. "
       "The wall is hottest at its outer surface at the downstream end, as it must be with heat entering "
       "from outside and air warming along the duct." % (TEMP["T_solid_max"], TEMP["T_solid_max_location_mm"]["r"],
                                                        TEMP["T_solid_max_location_mm"]["z"]))


def unwrap(ax, D_, field, label, cmap, levels=24):
    tri = mtri.Triangulation(D_["th"], D_["z-coordinate"] * 1e3)
    lv = np.linspace(D_[field].min() - 1e-9, D_[field].max() + 1e-9, levels)
    c = ax.tricontourf(tri, D_[field], levels=lv, cmap=cmap)
    ax.set_xlabel("theta [deg]"); ax.set_ylabel("z [mm]"); ax.set_xlim(0, 360)
    return c


# ---- 7 outer-wall temperature
fig, axes = plt.subplots(1, 2, figsize=(13, 5.0), gridspec_kw=dict(width_ratios=[1, 1.35]))
c = unwrap(axes[0], WO, "temperature", "T", "inferno")
fig.colorbar(c, ax=axes[0], label="T outer wall [K]")
axes[0].set_title("(a) HEATED_OUTER_WALL unwrapped", fontsize=9.5)
ax = axes[1]
ax.plot(AP["x_m"] * 1e3, AP["Two_corrected_K"], color=GREY, ls="--", lw=1.4, label="analytical outer wall (Section 2, corrected h)")
ax.plot(prof["z"] * 1e3, prof["Two"], color=C2, lw=2.0, label="CFD outer wall (circumferential average)")
ax.set_xlabel("z [mm]"); ax.set_ylabel("temperature [K]"); ax.grid(alpha=0.25); ax.legend(fontsize=8, frameon=False)
ax.set_title("(b) outer-wall temperature along the duct", fontsize=9.5)
fig.suptitle("Figure 7 - Outer-wall temperature", fontsize=11.5, y=1.02)
finish(fig, "fig07_outer_wall_temperature.png", "Circumferential variation on the outer wall: %.3f K peak-to-peak "
       "at most (faceting). Max %.2f K." % (max(np.ptp(WO["temperature"][kO == k]) for k in range(NZ)), TEMP["T_outer_wall_max"]))

# ---- 8 wall heat flux
fig, axes = plt.subplots(1, 2, figsize=(14, 5.2), gridspec_kw=dict(width_ratios=[1, 1.35], wspace=0.42))
tri_q = mtri.Triangulation(WI["th"], WI["z-coordinate"] * 1e3)
c = axes[0].tricontourf(tri_q, np.clip(WI["q"], 14500, 17000), levels=np.linspace(14500, 17000, 26),
                        cmap="plasma", extend="max")
axes[0].set_xlabel("theta [deg]"); axes[0].set_ylabel("z [mm]"); axes[0].set_xlim(0, 360)
fig.colorbar(c, ax=axes[0], label="heat flux into the air [W/m2] (colour range clipped)")
axes[0].set_title("(a) FLUID_SOLID_INTERFACE unwrapped\n(first slab reaches %.0f W/m2, off the colour scale)"
                  % prof["qi"][0], fontsize=9.5)
ax = axes[1]
ax.axhline(ana["qpp_inner"], color=GREY, ls="--", lw=1.3, label="1-D assumption: uniform 16 000 W/m2 at the bore")
ax.plot(prof["z"] * 1e3, prof["qi"], color=C2, lw=2.0, label="CFD heat flux into the air (bore)")
ax.plot(prof["z"] * 1e3, prof["qo"], color=C1, lw=1.6, label="CFD heat flux into the solid (outer wall)")
ax.set_xlabel("z [mm]"); ax.set_ylabel("heat flux [W/m2]"); ax.grid(alpha=0.25); ax.legend(fontsize=8, frameon=False)
ax.set_title("(b) wall heat flux along the duct", fontsize=9.5)
fig.suptitle("Figure 8 - Wall heat flux", fontsize=11.5, y=1.02)
_rec = prof["z"][np.argmax((np.abs(prof["qi"] / ana["qpp_inner"] - 1) < 0.01) & (prof["z"] > 0.03))] * 1e3
finish(fig, "fig08_wall_heat_flux.png", "The heat enters uniformly at 8000 W/m2 on the outside, but does NOT leave "
       "uniformly at the bore. In the first slab the bore flux is %.0f W/m2 (%.1f x the 1-D value): the air there is "
       "coldest and its thermal boundary layer thinnest, so h is very high, and heat conducts axially through the "
       "Inconel toward the inlet end to feed it. Just downstream the flux dips to %.0f W/m2, and it is back within 1 %% "
       "of 16 000 W/m2 by z = %.0f mm. At the outlet end it falls to %.0f W/m2."
       % (prof["qi"][0], prof["qi"][0] / ana["qpp_inner"], prof["qi"].min(), _rec, prof["qi"][-1]))

# ---- 9 y+
fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.9), gridspec_kw=dict(width_ratios=[1, 1.25, 1], wspace=0.38))
c = unwrap(axes[0], WI, "y-plus", "y+", "viridis")
fig.colorbar(c, ax=axes[0], label="y+")
axes[0].set_title("(a) y+ on the interface, unwrapped", fontsize=9.5)
ax = axes[1]
ax.fill_between(prof["z"] * 1e3, prof["yplus_min"], prof["yplus_max"], color=C1, alpha=0.2, label="min-max round the circumference")
ax.plot(prof["z"] * 1e3, prof["yplus_avg"], color=C1, lw=2, label="circumferential average")
ax.axhline(1.0, color="#b3261e", ls="--", lw=1.1, label="y+ = 1")
ax.set_xlabel("z [mm]"); ax.set_ylabel("y+"); ax.set_ylim(0, max(1.15, YP["max"] * 1.1)); ax.grid(alpha=0.25)
ax.legend(fontsize=8, frameon=False)
ax.set_title("(b) y+ along the duct", fontsize=9.5)
ax = axes[2]
ax.bar(edges[:-1], hist / ya.sum() * 100, width=np.diff(edges), align="edge", color=C3, edgecolor="white")
ax.axvline(1.0, color="#b3261e", ls="--", lw=1.1)
ax.set_xlabel("y+"); ax.set_ylabel("% of interface area"); ax.grid(alpha=0.25)
ax.set_title("(c) area-weighted distribution", fontsize=9.5)
fig.suptitle("Figure 9 - Wall y+ on FLUID_SOLID_INTERFACE, converged second-order solution", fontsize=11.5, y=1.02)
finish(fig, "fig09_yplus.png", "y+: min %.3f, area-mean %.3f, max %.3f (at z = %.1f mm, the inlet leading edge); "
       "%.1f %% of the area has y+ <= 1. The four-fold circumferential pattern in (a) is geometric: the first fluid "
       "cell is thinner at the O-grid diagonals than at 0/90/180/270 deg - cell-centre wall distance %.2f-%.2f um - "
       "while wall shear varies by only %.1f %% round the circumference (see F-028)."
       % (YP["min"], YP["area_mean"], YP["max"], YP["location_of_max_mm"]["z"], 100 * YP["frac_area_le_1"],
          NW["ywall_min_um"], NW["ywall_max_um"], NW["tau_ptp_pct"]))

# ---- 10 pressure vs z
fig, ax = plt.subplots(figsize=(10.5, 4.8))
ax.plot(prof["z"] * 1e3, prof["p_area"], color=C1, lw=2.0, label="CFD area-averaged static pressure, per slab")
ax.plot([0, L * 1e3], [p_in_a, p_out_a], "o", color=C2, ms=6, label="CFD inlet / outlet faces")
ax.set_xlabel("z [mm]"); ax.set_ylabel("static gauge pressure [Pa]"); ax.grid(alpha=0.25)
ax.axvline(18 * D * 1e3, color=GREY, ls=":", lw=1)
ax.text(18 * D * 1e3 + 4, p_in_a * 0.95, "x/D = 18\n(entry length, A-017)", fontsize=8, color=GREY, va="top")
ax.legend(fontsize=8.5, frameon=False)
ax.set_title("Figure 10 - Static pressure along the duct: inlet-to-outlet drop %.2f Pa" % dp_total, fontsize=11)
finish(fig, "fig10_pressure_axial.png", "Steeper at the inlet (thin boundary layer, high wall shear, profile "
       "development) and steepening again downstream as heating lowers density and accelerates the flow.")

# ---- 11 bulk / wall temperature vs z, with the analytical march
fig, ax = plt.subplots(figsize=(11, 5.4))
ax.plot(AP["x_m"] * 1e3, AP["Tb_K"], color=GREY, ls="--", lw=1.4, label="analytical bulk (Section 2 energy march)")
ax.plot(AP["x_m"] * 1e3, AP["Twi_corrected_K"], color=GREY, ls="-.", lw=1.3, label="analytical inner wall, property-corrected h")
ax.plot(AP["x_m"] * 1e3, AP["Twi_constprop_K"], color=GREY, ls=":", lw=1.3, label="analytical inner wall, constant-property h")
ax.plot(prof["z"] * 1e3, prof["Tb_mass"], color=C1, lw=2.2, label="CFD bulk (mass-weighted)")
ax.plot(prof["z"] * 1e3, prof["Twi"], color=C2, lw=2.2, label="CFD inner wall")
ax.plot(prof["z"] * 1e3, prof["Two"], color=C4, lw=1.8, label="CFD outer wall")
ax.set_xlabel("z [mm]"); ax.set_ylabel("temperature [K]"); ax.grid(alpha=0.25); ax.legend(fontsize=8, frameon=False, ncol=2)
ax.set_title("Figure 11 - Bulk and wall temperature along the duct, CFD vs Section 2 analytical", fontsize=11)
finish(fig, "fig11_bulk_temperature_axial.png", "CFD bulk temperature is linear in z, as a uniform imposed flux requires, "
       "and lies on the analytical energy march. The walls differ: upstream of about 80 mm the CFD inner wall is BELOW both "
       "analytical curves, because the 1-D march applies a fully developed h from z = 0 and has no thermal entrance region, "
       "where the real h is far higher. Downstream the CFD wall lies between the constant-property and property-corrected "
       "curves, finishing %.1f K below the corrected one at the exit." % (float(AP["Twi_corrected_K"][-1]) - prof["Twi"][-1]))

# ---- 12 temperature through the wall
fig, axes = plt.subplots(1, 2, figsize=(13, 5.0))
ax = axes[0]
cols = [C1, C3, C4, C2]
for zq, col in zip([0.05, 0.20, 0.40, 0.57], cols):
    ks = int(np.argmin(abs(zc - zq)))
    m = kS == ks
    rr, tt = Sd["r"][m], Sd["temperature"][m]
    o = np.argsort(rr)
    rb = np.unique(np.round(rr[o], 7))
    tb = np.array([tt[np.abs(rr - v) < 5e-8].mean() for v in rb])
    ax.plot(rb * 1e3, tb - tb[0], "o", color=col, ms=4, label="CFD z = %.0f mm" % (zc[ks] * 1e3))
    Tm = np.mean(tb)
    rl = np.linspace(rb[0], RO, 50)
    ax.plot(rl * 1e3, QPP_O * RO * np.log(rl / rb[0]) / float(kinc(Tm)), color=col, lw=1.0, ls="--")
ax.set_xlabel("r [mm]"); ax.set_ylabel("T(r) - T(first solid cell) [K]"); ax.grid(alpha=0.25)
ax.legend(fontsize=8, frameon=False)
ax.set_title("(a) radial profile in the Inconel wall\ndashed = 1-D log law with k at that station's mean wall T", fontsize=9.5)
ax = axes[1]
ax.plot(prof["z"] * 1e3, prof["dTwall"], color=C2, lw=2, label="CFD: T_outer - T_inner")
ax.plot(prof["z"] * 1e3, prof["dTwall_1D_localk"], color=GREY, ls="--", lw=1.4, label="1-D Fourier with k at local T")
ax.axhline(ana["dT_through_wall"], color=GREY, ls=":", lw=1.2, label="Section 2: 7.28 K (k = 15.22 at exit)")
ax.set_xlabel("z [mm]"); ax.set_ylabel("through-wall dT [K]"); ax.grid(alpha=0.25); ax.legend(fontsize=8, frameon=False)
ax.set_title("(b) through-wall temperature difference along the duct", fontsize=9.5)
fig.suptitle("Figure 12 - Temperature through the solid wall", fontsize=11.5, y=1.02)
finish(fig, "fig12_through_wall_temperature.png", "The profile is logarithmic, as cylindrical conduction requires. From "
       "z = 100 mm onward the CFD follows the 1-D Fourier law (with k at the local temperature) to within about 1 %%, and "
       "it grows toward the inlet because Inconel's conductivity falls at lower temperature. In the first slab it jumps to "
       "%.1f K: that is where the bore flux is %.1f x nominal (Figure 8), fed by axial conduction - a 2-D effect a 1-D "
       "model cannot represent." % (prof["dTwall"][0], prof["qi"][0] / ana["qpp_inner"]))

# ---- 13 velocity profiles
fig, ax = plt.subplots(figsize=(10, 5.2))
for zq, col in zip([0.0033, 0.02, 0.06, 0.15, 0.36, 0.597], [GREY, C4, C3, C1, "#7a3413", C2]):
    ks = int(np.argmin(abs(zc - zq)))
    m = np.abs(FA["z"] - zc[ks]) < 0.25 * dz
    o = np.argsort(FA["r"][m])
    ax.plot(FA["r"][m][o] / RI, FA["z-velocity"][m][o] / prof["w_b"][ks], color=col, lw=1.6,
            label="z = %.1f mm (x/D = %.1f)" % (zc[ks] * 1e3, zc[ks] / D))
rr = np.linspace(0, 1, 200)
ax.plot(rr, (1 - rr) ** (1 / 7.) / (98 / 120.), color="k", ls=":", lw=1.2,
        label="1/7 power law (reference shape)")
ax.set_xlabel("r / R"); ax.set_ylabel("w / w_bulk"); ax.grid(alpha=0.25); ax.legend(fontsize=8, frameon=False)
ax.set_title("Figure 13 - Axial-velocity profiles: plug inlet developing to a turbulent profile", fontsize=11)
finish(fig, "fig13_velocity_profiles.png", "The 1/7 power law is a textbook reference shape only (w/w_b = (1-r/R)^(1/7) / 0.8167), "
       "not a Section 2 result.")

# ---- 14 radial temperature through fluid and solid
fig, ax = plt.subplots(figsize=(10.5, 5.2))
for zq, col in zip([0.05, 0.30, 0.57], [C1, C3, C2]):
    ks = int(np.argmin(abs(zc - zq)))
    m = np.abs(FA["z"] - zc[ks]) < 0.25 * dz
    o = np.argsort(FA["r"][m])
    ax.plot(FA["r"][m][o] * 1e3, FA["temperature"][m][o], color=col, lw=1.8, label="air, z = %.0f mm" % (zc[ks] * 1e3))
    ms = np.abs(SA["z"] - zc[ks]) < 0.25 * dz
    o2 = np.argsort(SA["r"][ms])
    ax.plot(SA["r"][ms][o2] * 1e3, SA["temperature"][ms][o2], color=col, lw=1.8, ls="--")
ax.axvline(10, color="k", lw=1.0); ax.text(10.2, ax.get_ylim()[0] + 5, "interface", fontsize=8)
ax.set_xlabel("r [mm]"); ax.set_ylabel("temperature [K]"); ax.grid(alpha=0.25); ax.legend(fontsize=8, frameon=False)
ax.set_title("Figure 14 - Radial temperature: air (solid lines) and Inconel wall (dashed)", fontsize=11)
finish(fig, "fig14_radial_temperature.png", "Almost the whole wall-to-bulk temperature difference sits in the thin air "
       "layer next to the wall; the 10 mm of Inconel carries only a few kelvin. That is the Section 2 finding that the "
       "film carries ~97 % of the thermal resistance, now seen directly.")

# ---- 15 Nu and f
fig, axes = plt.subplots(1, 2, figsize=(13, 4.9))
ax = axes[0]
ax.plot(prof["x_over_D"], prof["Nu"], color=C2, lw=2, label="CFD local Nu")
ax.plot(prof["x_over_D"], Nu_gn, color=GREY, ls="--", lw=1.2, label="Gnielinski (constant property)")
ax.plot(prof["x_over_D"], Nu_db, color=GREY, ls=":", lw=1.2, label="Dittus-Boelter")
ax.plot(prof["x_over_D"], Nu_corr, color=GREY, ls="-.", lw=1.2, label="Gnielinski x (Tb/Tw)^0.5")
ax.axvspan(18, 29, color=C3, alpha=0.08)
ax.set_ylim(0, 200); ax.set_xlabel("x / D"); ax.set_ylabel("Nu"); ax.grid(alpha=0.25); ax.legend(fontsize=8, frameon=False)
ax.set_title("(a) Nusselt number (shaded: fully developed window x/D 18-29)", fontsize=9.5)
ax = axes[1]
ax.plot(prof["x_over_D"], prof["f_shear"], color=C1, lw=2, label="CFD, from wall shear")
ax.plot(prof["x_over_D"], f_pet, color=GREY, ls="--", lw=1.2, label="Petukhov at local Re (constant property)")
ax.plot(prof["x_over_D"], f_pet_heat, color=GREY, ls="-.", lw=1.2, label="Petukhov x (Tw/Tb)^-0.1 (gas heating)")
ax.axhline(ana["f_mean"], color=GREY, ls=":", lw=1.1, label="Section 2 mean 0.0241")
ax.axvspan(18, 29, color=C3, alpha=0.08)
ax.set_ylim(0, 0.06); ax.set_xlabel("x / D"); ax.set_ylabel("Darcy f"); ax.grid(alpha=0.25); ax.legend(fontsize=8, frameon=False)
ax.set_title("(b) Darcy friction factor", fontsize=9.5)
fig.suptitle("Figure 15 - Local Nusselt number and friction factor vs correlations", fontsize=11.5, y=1.02)
finish(fig, "fig15_nusselt_friction.png", "Correlations are evaluated at the CFD's own local Re, Pr and wall/bulk "
       "temperatures. Fully developed means: Nu %.2f (CFD) vs %.2f corrected / %.2f Gnielinski / %.2f Dittus-Boelter; "
       "f %.5f (CFD) vs %.5f Petukhov." % (FD["Nu_cfd"], FD["Nu_corr_n05"], FD["Nu_gn"], FD["Nu_db"], FD["f_cfd"], FD["f_petukhov"]))

# ---- 16 convergence
it_res = np.array([d["iter"] for d in RES])
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
ax = axes[0]
for e, col in zip(EQ, [C1, "#7aa9e0", "#a8c6ec", "#1d4f86", C2, C3, C4]):
    vals = np.array([d.get(e, np.nan) for d in RES])
    ax.semilogy(it_res, vals, lw=1.1, color=col, label=e)
ax.axhline(1e-4, color=GREY, ls=":", lw=1); ax.axhline(1e-6, color=GREY, ls="--", lw=1)
s1 = runsum["stage1_iters"]; s2 = s1 + runsum["stage2_iters"]
for a in axes:
    a.axvline(s1, color="k", lw=0.8, ls=":"); a.axvline(s2, color="k", lw=0.8, ls=":")
ax.set_xlabel("iteration"); ax.set_ylabel("scaled residual"); ax.legend(fontsize=7, frameon=False, ncol=2)
ax.set_title("(a) residuals; dotted: energy ON, then second order", fontsize=9.5); ax.grid(alpha=0.2)
ax = axes[1]
it_m = MONr[:, 0]
ax.plot(it_m, MONr[:, mc["T_solid_max"]], color=C2, lw=1.5, label="max solid T")
ax.plot(it_m, MONr[:, mc["T_wall_max"]], color=C4, lw=1.5, label="max wetted-wall T")
ax.plot(it_m, MONr[:, mc["T_out_bulk"]], color=C1, lw=1.5, label="outlet bulk T")
ax.axhline(673.15, color="#b3261e", ls="--", lw=1); ax.text(10, 676, "top of Inconel property table 673.15 K", fontsize=7, color="#b3261e")
ax.set_ylim(280, 700); ax.set_xlabel("iteration"); ax.set_ylabel("K"); ax.legend(fontsize=8, frameon=False)
ax.set_title("(b) temperatures: monotonic approach, no overshoot", fontsize=9.5); ax.grid(alpha=0.2)
ax = axes[2]
ax.plot(it_m, MONr[:, mc["p_in_area"]] - MONr[:, mc["p_out_area"]], color=C1, lw=1.5, label="dp [Pa]")
ax.plot(it_m, MONr[:, mc["q_interface"]], color=C2, lw=1.5, label="Q across interface [W]")
ax.set_xlabel("iteration"); ax.legend(fontsize=8, frameon=False); ax.grid(alpha=0.2)
ax.set_title("(c) pressure drop and interface heat rate", fontsize=9.5)
fig.suptitle("Figure 16 - Convergence history of the official run", fontsize=11.5, y=1.02)
finish(fig, "fig16_convergence.png", "Stage 1: flow and turbulence only (%d it). Stage 2: energy on, first order (%d it). "
       "Stage 3: second-order upwind on momentum, k, omega and energy (%d it)." % (runsum["stage1_iters"], runsum["stage2_iters"], runsum["stage3_iters"]))

# ---- 17 pressure-drop decomposition
fig, ax = plt.subplots(figsize=(10.5, 4.8))
labels = ["friction", "acceleration", "entry increment", "TOTAL"]
anav = [ana["dp_friction"], ana["dp_acceleration"], ana["dp_entry_increment"], ana["dp_total_CFD_comparable"]]
x = np.arange(4)
ax.bar(x - 0.2, anav, 0.38, color=GREY, label="Section 2 analytical")
cfd_comp = [dp_wall, dp_accel_1D, dp_profile, dp_total]
ax.bar(x + 0.2, cfd_comp, 0.38, color=C1, label="CFD (momentum balance on the exported solution)")
for i in range(4):
    ax.text(x[i] - 0.2, anav[i] + 5, "%.1f" % anav[i], ha="center", fontsize=8)
    ax.text(x[i] + 0.2, cfd_comp[i] + 5, "%.1f" % cfd_comp[i], ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(["wall shear\n(analytical: fully developed friction)", "1-D acceleration\nG^2(1/rho_out - 1/rho_in)",
                                      "profile development\n(analytical: K_dev entry term)", "inlet-to-outlet\nstatic dp"], fontsize=8)
ax.set_ylabel("Pa"); ax.grid(alpha=0.2, axis="y"); ax.legend(fontsize=8.5, frameon=False)
ax.set_title("Figure 17 - What the pressure drop is made of", fontsize=11)
finish(fig, "fig17_pressure_decomposition.png", "CFD components from the axial momentum balance: dp*A = F_wall + (M_out - M_in). "
       "The wall-shear term includes the extra entry-region shear; the analytical 'entry increment' has no one-to-one CFD "
       "counterpart, so only the totals are compared like for like. Momentum-balance residual %.2f Pa (%.2f %%)."
       % (mom_closure, 100 * mom_closure / dp_total))
print("DONE")
