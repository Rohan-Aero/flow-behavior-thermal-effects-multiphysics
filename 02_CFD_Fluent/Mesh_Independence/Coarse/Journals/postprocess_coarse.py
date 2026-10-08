# -*- coding: utf-8 -*-
"""
Section 6A post-processing - COARSE MESH (51,840 cells), mesh-independence point.
Derived from 06_Fluent_CFD/Journals/postprocess_baseline.py (Section 5B, untouched): the same
definitions, applied to the coarse exports, plus a like-for-like comparison with the medium result.

Operates ONLY on data exported by ANSYS Fluent 2026 R1 from the converged solution:
  Exports/cells_fluid.csv, cells_solid.csv      cell-centre values (no interpolation)
  Exports/wall_interface.csv, wall_outer.csv,   face-centroid values on walls
  Exports/wall_solid_ends.csv, boundary_*.csv
  Monitors/coarse_monitors.out                  Fluent report file, every iteration
  Logs/coarse_stdout.txt                        Fluent solver output (residual history)
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
BASE = os.path.dirname(HERE)                               # 06_Fluent_CFD/Mesh_Independence/Coarse
MED = os.path.dirname(os.path.dirname(BASE))               # 06_Fluent_CFD (medium baseline, READ ONLY)
ROOT = os.path.dirname(MED)                                # project root
EXP = os.path.join(BASE, "Exports")
FIG = os.path.join(BASE, "Figures")
PRO = os.path.join(BASE, "Profiles")
MONd = os.path.join(BASE, "Monitors")
AUD = os.path.join(BASE, "Audit")
BL = BASE
for d in (FIG, PRO, MONd, AUD, BL):
    if not os.path.isdir(d):
        os.makedirs(d)

C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GREY = "#5a5a5a"
PROV = ("ANSYS Fluent 2026 R1 converged COARSE-mesh solution (51,840 cells, mesh-independence point), exported and plotted "
        "with matplotlib. RE-ANALYSIS 2026 - not an original internship result.")

# geometry, frozen baseline
RI, RO, L, D = 0.010, 0.020, 0.600, 0.020
NT = 32                      # coarse mesh: 32-sided polygon (medium 48, fine 72)
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

# faceting of the NT-gon
AREA_P = (NT / (2 * math.pi)) * math.sin(2 * math.pi / NT)        # planar
LAT_P = math.sin(math.pi / NT) / (math.pi / NT)                   # lateral
DH_P = D * math.cos(math.pi / NT)                                 # hydraulic diameter of the NT-gon


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

hdrM, MONr = read_report_file(os.path.join(MONd, "coarse_monitors.out"))
mc = {n: i for i, n in enumerate(hdrM)}
RES = read_residuals(os.path.join(BASE, "Logs", "coarse_stdout.txt"))
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

NZ = 60
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

A_poly = math.pi * RI ** 2 * AREA_P
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
prof["Nu_Dh_poly"] = prof["h"] * DH_P / kair(prof["Tb_mass"])
prof["Re"] = G * D / muair(prof["Tb_mass"])
prof["f_shear"] = 8.0 * prof["tau_w"] * prof["rho_b"] / G ** 2
prof["x_over_D"] = prof["z"] / D
# analytical through-wall dT using k at the CFD's own local mean solid temperature
prof["dTwall_1D_localk"] = QPP_O * RO * math.log(RO / RI) / kinc(prof["Tsolid_mean"])

keys = ["z", "x_over_D", "mdot", "p_area", "p_mass", "Tb_mass", "hb", "rho_b", "rho_b_volavg", "w_b", "w_max", "Twi", "Two",
        "dTwall", "dTwall_1D_localk", "qi", "qo", "h", "Nu", "Nu_Dh_poly", "Re", "tau_w", "f_shear",
        "yplus_avg", "yplus_min", "yplus_max", "Tsolid_mean", "Tsolid_max", "Tfluid_max"]
with open(os.path.join(PRO, "axial_profiles_cfd.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# CFD axial profiles, slab averages over the 60 axial slabs of the COARSE mesh. "
                "Source: Fluent cell/face exports of the converged coarse solution. RE-ANALYSIS 2026."])
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
            lateral_ratio_polygon=LAT_P, Q_wall_expected_from_area=QPP_O * A_outer,
            Q_analytical=ana.get("Q_total"), Q_wall_vs_analytical_pct=100 * (Q_wall / ana["Q_total"] - 1),
            A_in_mesh=A_in, A_in_exact=math.pi * RI ** 2, planar_ratio_mesh=A_in / (math.pi * RI ** 2),
            planar_ratio_polygon=AREA_P)
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
    w.writerow(["# area-weighted y+ distribution on FLUID_SOLID_INTERFACE, converged COARSE solution"])
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
RE = dict(Re_in_nominalD=G * D / float(muair(T_in_b)), Re_in_Dh_poly=G * DH_P / float(muair(T_in_b)),
          Re_out_nominalD=G * D / float(muair(T_out_b)), Re_out_Dh_poly=G * DH_P / float(muair(T_out_b)), G=G)

# ============================================================================
# residuals and monitors -> CSV
# ============================================================================
with open(os.path.join(MONd, "coarse_monitors.csv"), "w", newline="") as fh:
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
print("   wrote Monitors/coarse_monitors.csv (%d rows), residual_history.csv (%d rows)" % (len(MONr), len(RES)))
lastres = RES[-1] if RES else {}

# full-history temperature maxima (startup excursion check)
HIST = dict(max_T_solid_history=float(MONr[:, mc["T_solid_max"]].max()),
            iter_of_max_T_solid=int(MONr[np.argmax(MONr[:, mc["T_solid_max"]]), 0]),
            final_T_solid_max_monitor=float(last[mc["T_solid_max"]]),
            max_T_fluid_history=float(MONr[:, mc["T_fluid_max"]].max()),
            min_T_fluid_history=float(MONr[:, mc["T_fluid_min"]].min()),
            min_T_solid_history=float(MONr[:, mc["T_solid_min"]].min()),
            section5A_startup_peak_K_other_run=761.0)
HIST["solid_overshoot_above_final_K"] = HIST["max_T_solid_history"] - HIST["final_T_solid_max_monitor"]
RANGE = dict(fluid_table_K=[250.0, 600.0], solid_table_K=[293.15, 673.15],
             final_fluid_within=bool(TEMP["T_fluid_min"] >= 250 and TEMP["T_fluid_max"] <= 600),
             final_solid_within=bool(TEMP["T_solid_min"] >= 293.15 and TEMP["T_solid_max"] <= 673.15),
             history_fluid_within=bool(HIST["min_T_fluid_history"] >= 250 and HIST["max_T_fluid_history"] <= 600),
             history_solid_within=bool(HIST["min_T_solid_history"] >= 293.15 and HIST["max_T_solid_history"] <= 673.15))
lim_hits = []
with open(os.path.join(BASE, "Logs", "coarse_stdout.txt"), "r", errors="ignore") as fh:
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
# SECTION 6A - load the MEDIUM result (read only) and compare like with like
# ============================================================================
MEDJ = json.load(open(os.path.join(MED, "Baseline", "cfd_baseline_results.json")))


def read_profile_csv(path):
    with open(path) as fh:
        fh.readline()                      # quoted provenance comment
        hdr = fh.readline().strip().split(",")
        arr = np.loadtxt(fh, delimiter=",")
    return {h: arr[:, i] for i, h in enumerate(hdr)}


PM = read_profile_csv(os.path.join(MED, "Profiles", "axial_profiles_cfd.csv"))
WIM = read_fluent_ascii(os.path.join(MED, "Exports", "wall_interface.csv"))
WIM["r"], WIM["th"] = cyl(WIM)
at_zm = lambda arr, zq: float(np.interp(zq, PM["z"], arr))
NT_MED = 48
AREA_MED = (NT_MED / (2 * math.pi)) * math.sin(2 * math.pi / NT_MED)
LAT_MED = math.sin(math.pi / NT_MED) / (math.pi / NT_MED)
GEO = dict(mdot_ratio=AREA_P / AREA_MED, Q_ratio=LAT_P / LAT_MED)
print("   geometric (faceting) ratios coarse/medium:", GEO)

# matched-location quantities, both meshes, identical definition (linear interpolation between slab centres)
MID = {}
for zq, tag in ((0.300, "z300"), (0.570, "z570")):
    MID[tag] = dict(
        coarse=dict(dTwall=at_z(prof["dTwall"], zq), Twi=at_z(prof["Twi"], zq), Two=at_z(prof["Two"], zq),
                    Tb=at_z(prof["Tb_mass"], zq), h=at_z(prof["h"], zq), qi=at_z(prof["qi"], zq),
                    p=at_z(prof["p_area"], zq), yplus=at_z(prof["yplus_avg"], zq)),
        medium=dict(dTwall=at_zm(PM["dTwall"], zq), Twi=at_zm(PM["Twi"], zq), Two=at_zm(PM["Two"], zq),
                    Tb=at_zm(PM["Tb_mass"], zq), h=at_zm(PM["h"], zq), qi=at_zm(PM["qi"], zq),
                    p=at_zm(PM["p_area"], zq), yplus=at_zm(PM["yplus_avg"], zq)))
TW["Twi_z300"], TW["Two_z300"], TW["Tb_z300"] = MID["z300"]["coarse"]["Twi"], MID["z300"]["coarse"]["Two"], MID["z300"]["coarse"]["Tb"]
TW["h_z300"], TW["h_z570"] = MID["z300"]["coarse"]["h"], MID["z570"]["coarse"]["h"]

mc_ = MEDJ["conservation"]; mp_ = MEDJ["pressure"]; mt_ = MEDJ["temperatures"]; my_ = MEDJ["yplus"]
mfd_ = MEDJ["fully_developed"]; mre_ = MEDJ["reynolds"]; mmc_ = MEDJ["mixing_cup"]; mtw_ = MEDJ["through_wall"]
ROWS = [
    # quantity, units, coarse, medium, geometric expectation (coarse/medium - 1, %), note
    ("cells", "-", 51840, 159840, None, "mesh"),
    ("polygon sides (circumferential cells)", "-", NT, NT_MED, None, "mesh"),
    ("axial slabs", "-", NZ, 90, None, "mesh"),
    ("inlet mass flow (Fluent flux report)", "g/s", 1e3 * mdot_in, 1e3 * mc_["mdot_in"], 100 * (GEO["mdot_ratio"] - 1),
     "planar area of the inscribed polygon"),
    ("outlet mass flow (Fluent flux report)", "g/s", 1e3 * mdot_out, 1e3 * mc_["mdot_out"], 100 * (GEO["mdot_ratio"] - 1), ""),
    ("Reynolds number, inlet (D = 20 mm)", "-", RE["Re_in_nominalD"], mre_["Re_in_nominalD"], 0.0,
     "G = mdot/A is unchanged by faceting"),
    ("Reynolds number, outlet (D = 20 mm)", "-", RE["Re_out_nominalD"], mre_["Re_out_nominalD"], None, ""),
    ("pressure drop, static, area-weighted inlet - outlet", "Pa", PD["dp_total_area"], mp_["dp_total_area"], None,
     "identical definition to Section 5B"),
    ("  - wall shear, F_wall/A", "Pa", PD["dp_wall_shear"], mp_["dp_wall_shear"], None, "momentum balance"),
    ("  - 1-D acceleration", "Pa", PD["dp_accel_1D_cfd_densities"], mp_["dp_accel_1D_cfd_densities"], None, ""),
    ("  - profile development", "Pa", PD["dp_profile_development"], mp_["dp_profile_development"], None, ""),
    ("outlet temperature, mass-weighted", "K", T_out_b, mt_["T_out_bulk"], None, ""),
    ("outlet mixing-cup temperature (enthalpy)", "K", MC["T_out_mixing_cup"], mmc_["T_out_mixing_cup"], None, ""),
    ("outlet T predicted by energy balance on the mesh's own Q and mdot", "K", MC["T_out_from_cfd_energy_balance"],
     mmc_["T_out_from_cfd_energy_balance"], None, "isolates the faceting effect on T_out"),
    ("heat-transfer rate (heated wall)", "W", Q_wall, mc_["Q_wall"], 100 * (GEO["Q_ratio"] - 1),
     "lateral area of the inscribed polygon"),
    ("maximum solid temperature (outer-wall facet max)", "K", TEMP["T_outer_wall_max"], mt_["T_outer_wall_max"], None, ""),
    ("maximum solid temperature (cell centre)", "K", TEMP["T_solid_max"], mt_["T_solid_max"], None, ""),
    ("peak inner-wall temperature (facet max)", "K", TEMP["T_inner_wall_max"], mt_["T_inner_wall_max"], None, ""),
    ("volume-mean solid temperature", "K", TEMP["T_solid_mean_volume"], mt_["T_solid_mean_volume"], None, ""),
    ("through-wall dT, MID-SPAN z = 300 mm", "K", MID["z300"]["coarse"]["dTwall"], MID["z300"]["medium"]["dTwall"], None,
     "matched location (both interpolated between slab centres)"),
    ("through-wall dT, z = 570 mm", "K", MID["z570"]["coarse"]["dTwall"], MID["z570"]["medium"]["dTwall"], None, "5B reported station"),
    ("inner-wall T, mid-span", "K", MID["z300"]["coarse"]["Twi"], MID["z300"]["medium"]["Twi"], None, ""),
    ("outer-wall T, mid-span", "K", MID["z300"]["coarse"]["Two"], MID["z300"]["medium"]["Two"], None, ""),
    ("bulk T, mid-span", "K", MID["z300"]["coarse"]["Tb"], MID["z300"]["medium"]["Tb"], None, ""),
    ("h, mid-span", "W/m2K", MID["z300"]["coarse"]["h"], MID["z300"]["medium"]["h"], None, ""),
    ("fully developed Nu (x/D 18-29)", "-", FD["Nu_cfd"], mfd_["Nu_cfd"], None, ""),
    ("fully developed Darcy f (x/D 18-29)", "-", FD["f_cfd"], mfd_["f_cfd"], None, ""),
    ("y+ minimum", "-", YP["min"], my_["min"], None, ""),
    ("y+ area mean", "-", YP["area_mean"], my_["area_mean"], None, ""),
    ("y+ maximum", "-", YP["max"], my_["max"], None, ""),
    ("y+ mean, fully developed window", "-", YP["fd_mean"], my_["fd_mean"], None, ""),
    ("mass imbalance", "%", CONS["mass_imbalance_pct"], mc_["mass_imbalance_pct"], None, "|in-out|/in"),
    ("energy imbalance (net over all boundaries / Q_wall)", "%", CONS["net_all_boundaries_pct"],
     mc_["net_all_boundaries_pct"], None, ""),
]
CMP = []
with open(os.path.join(BL, "Coarse_vs_Medium.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# Section 6A COARSE vs Section 5B MEDIUM, identical definitions. Raw comparison only - "
                "NOT a mesh-independence conclusion (fine mesh not yet solved). RE-ANALYSIS 2026."])
    w.writerow(["quantity", "units", "coarse", "medium", "coarse_minus_medium", "percent_of_medium",
                "geometric_faceting_expectation_percent", "note"])
    for q, u, c, m, g, note in ROWS:
        d = c - m
        pc = 100.0 * d / m if m not in (0, 0.0) else float("nan")
        CMP.append(dict(quantity=q, units=u, coarse=c, medium=m, diff=d, pct=pc, geometric_pct=g, note=note))
        w.writerow([q, u, "%.8g" % c, "%.8g" % m, "%.6g" % d, "%.4f" % pc, "" if g is None else "%.4f" % g, note])
print("   wrote Coarse_vs_Medium.csv")

RESULTS = dict(mesh=dict(level="coarse", cells=51840, fluid_cells=38400, solid_cells=13440, polygon_sides=NT,
                         axial_slabs=NZ, msh="05_Meshing/Mesh_Coarse/coarse.msh"),
               run=runsum, residuals_final=lastres, conservation=CONS, pressure=PD, temperatures=TEMP,
               near_wall=NW, mixing_cup=MC, through_wall=TW, matched_locations=MID, yplus=YP, velocity=VEL,
               reynolds=RE, fully_developed=FD, history=HIST, range_check=RANGE,
               faceting=dict(planar=AREA_P, lateral=LAT_P, Dh_poly=DH_P, ratios_vs_medium=GEO),
               comparison_vs_medium=CMP)
with open(os.path.join(BL, "coarse_cfd_results.json"), "w") as fh:
    json.dump(RESULTS, fh, indent=2, default=float)
print("   wrote coarse_cfd_results.json")

# ============================================================================
# FIGURES (coarse; medium overlaid where the comparison is the point)
# ============================================================================
CC, CM = C2, C1          # coarse orange, medium blue
PROV = ("ANSYS Fluent 2026 R1: coarse mesh 51,840 cells (Section 6A) vs medium 159,840 cells (Section 5B), both "
        "converged, identical physics; plotted with matplotlib from exported Fluent data. Raw comparison, "
        "NOT a mesh-independence conclusion. RE-ANALYSIS 2026 - not an original internship result.")


def mark(ax, zmm):
    ax.axvline(zmm, color=GREY, lw=0.8, ls=":")


# ---- c01 convergence history
it = MONr[:, 0]
fig, axes = plt.subplots(2, 2, figsize=(14, 8.4), gridspec_kw=dict(hspace=0.36, wspace=0.26))
ax = axes[0, 0]
ri = np.array([d["iter"] for d in RES])
for e, col in zip(EQ, [C1, C2, C3, C4, "#8a3ffc", GREY, "#d12771"]):
    v = np.array([d.get(e, np.nan) for d in RES], dtype=float)
    ax.semilogy(ri, np.where(v > 0, v, np.nan), lw=1.1, color=col, label=e)
ax.axhline(1e-4, color="k", lw=0.8, ls="--"); ax.axhline(1e-6, color="k", lw=0.8, ls=":")
ax.set_title("(a) scaled residuals (dashed 1e-4, dotted 1e-6 energy)", fontsize=9.5)
ax.legend(fontsize=7, ncol=2); ax.set_xlabel("iteration")
s3 = runsum.get("stage3_first_iteration") or 301
for a_ in axes.flat:
    a_.axvspan(0, 150, color="#e8e8e8", alpha=0.6, lw=0)
    a_.axvline(s3 - 0.5, color="k", lw=0.8)
ax = axes[0, 1]
ax.plot(it, MONr[:, mc["T_out_bulk"]], color=C1, lw=1.3, label="T_out bulk")
ax.set_ylabel("T_out [K]", color=C1); ax.set_xlabel("iteration")
ax2 = ax.twinx(); ax2.plot(it, MONr[:, mc["T_solid_max"]], color=C2, lw=1.3, label="T_solid max")
ax2.set_ylabel("T_solid max [K]", color=C2)
ax.set_title("(b) outlet bulk and maximum solid temperature", fontsize=9.5)
ax = axes[1, 0]
ax.plot(it, MONr[:, mc["p_in_area"]] - MONr[:, mc["p_out_area"]], color=C3, lw=1.3)
ax.set_ylabel("dp [Pa]"); ax.set_xlabel("iteration"); ax.set_title("(c) static pressure drop (area-weighted)", fontsize=9.5)
ax = axes[1, 1]
ax.plot(it, MONr[:, mc["q_heated_wall"]], color=C4, lw=1.3, label="heated wall")
ax.plot(it, MONr[:, mc["q_interface"]], color=C1, lw=1.0, ls="--", label="fluid-solid interface")
ax.plot(it, 1e5 * (MONr[:, mc["mdot_in"]] + MONr[:, mc["mdot_out"]]), color=GREY, lw=0.8, label="mass imbalance x 1e5 [kg/s]")
ax.set_xlabel("iteration"); ax.set_ylabel("W"); ax.legend(fontsize=7.5)
ax.set_title("(d) heat rates", fontsize=9.5)
fig.suptitle("Figure C1 - Coarse mesh: convergence history (grey band = stage 1, energy off; vertical line = switch to second order)",
             fontsize=11.5, y=0.995)
finish(fig, "figC01_coarse_convergence.png", "Converged at iteration %s and confirmed %d iterations later; final T_out drift over "
       "the last 200 iterations %.1e K." % (runsum["final_eval"]["iteration"] - 100 if runsum.get("final_eval") else "?", 100,
                                              runsum["final_eval"]["checks"]["drift T_out_bulk over 200 it [K]"]["value"]
                                              if runsum.get("final_eval") else float("nan")))

# ---- c02 axial temperatures, coarse vs medium
fig, axes = plt.subplots(2, 1, figsize=(12.5, 8.6), gridspec_kw=dict(height_ratios=[2, 1], hspace=0.3))
ax = axes[0]
for arr_c, arr_m, lab in ((prof["Two"], PM["Two"], "outer wall"), (prof["Twi"], PM["Twi"], "inner wall"),
                          (prof["Tb_mass"], PM["Tb_mass"], "bulk air")):
    ax.plot(prof["z"] * 1e3, arr_c, color=CC, lw=1.6, label="coarse " + lab if lab == "outer wall" else None)
    ax.plot(PM["z"] * 1e3, arr_m, color=CM, lw=1.2, ls="--", label="medium " + lab if lab == "outer wall" else None)
    ax.text(603, arr_c[-1], lab, fontsize=8, va="center")
ax.set_ylabel("T [K]"); ax.legend(["coarse", "medium"], fontsize=8.5, loc="upper left"); ax.set_xlim(0, 640)
mark(ax, 300); ax.set_title("(a) slab-averaged temperatures", fontsize=9.5)
ax = axes[1]
for arr_c, arr_m, lab, col in ((prof["Two"], PM["Two"], "outer wall", C4), (prof["Twi"], PM["Twi"], "inner wall", C3),
                               (prof["Tb_mass"], PM["Tb_mass"], "bulk", GREY)):
    ax.plot(prof["z"] * 1e3, arr_c - np.interp(prof["z"], PM["z"], arr_m), color=col, lw=1.4, label=lab)
ax.axhline(0, color="k", lw=0.6); mark(ax, 300); ax.set_xlim(0, 640)
ax.set_xlabel("z [mm]"); ax.set_ylabel("coarse - medium [K]"); ax.legend(fontsize=8)
ax.set_title("(b) difference at the coarse slab centres (medium linearly interpolated)", fontsize=9.5)
fig.suptitle("Figure C2 - Axial temperature profiles, coarse vs medium", fontsize=11.5, y=0.995)
finish(fig, "figC02_axial_temperatures_vs_medium.png", "Mid-span (dotted line): inner wall %.2f vs %.2f K, outer wall %.2f vs "
       "%.2f K, bulk %.2f vs %.2f K (coarse vs medium). The last point of the bulk curve in (b) is not a like-for-like "
       "difference: at the outflow boundary Fluent's outlet face temperature equals the adjacent cell's, so the last cell "
       "layer carries the outlet temperature on both meshes, and those layers sit at different z (595 vs 596.7 mm)." % (MID["z300"]["coarse"]["Twi"], MID["z300"]["medium"]["Twi"],
                                                           MID["z300"]["coarse"]["Two"], MID["z300"]["medium"]["Two"],
                                                           MID["z300"]["coarse"]["Tb"], MID["z300"]["medium"]["Tb"]))

# ---- c03 through-wall dT
fig, ax = plt.subplots(1, 1, figsize=(12.5, 5.0))
ax.plot(prof["z"] * 1e3, prof["dTwall"], "o-", color=CC, ms=3, lw=1.4, label="coarse (60 slabs)")
ax.plot(PM["z"] * 1e3, PM["dTwall"], "s--", color=CM, ms=2.5, lw=1.1, label="medium (90 slabs)")
for zq in (300, 570):
    mark(ax, zq)
ax.set_ylim(6.5, max(16.0, float(prof["dTwall"].max()) + 0.5))
ax.set_xlabel("z [mm]"); ax.set_ylabel("T_outer - T_inner [K]"); ax.legend(fontsize=9)
ax.set_title("Figure C3 - Through-wall temperature difference (circumferential average) - coarse vs medium", fontsize=11)
finish(fig, "figC03_through_wall_dT_vs_medium.png", "Matched stations: mid-span z = 300 mm %.3f K (coarse) vs %.3f K (medium); "
       "z = 570 mm %.3f vs %.3f K. First slab: %.2f K (coarse, centre z = %.0f mm) vs %.2f K (medium, centre z = %.1f mm) - "
       "different slab centres, not a matched location." % (MID["z300"]["coarse"]["dTwall"], MID["z300"]["medium"]["dTwall"],
                                                          MID["z570"]["coarse"]["dTwall"], MID["z570"]["medium"]["dTwall"],
                                                          prof["dTwall"][0], prof["z"][0] * 1e3, PM["dTwall"][0], PM["z"][0] * 1e3))

# ---- c04 pressure
fig, ax = plt.subplots(1, 1, figsize=(12.5, 4.8))
ax.plot(prof["z"] * 1e3, prof["p_area"], color=CC, lw=1.6, label="coarse")
ax.plot(PM["z"] * 1e3, PM["p_area"], color=CM, lw=1.2, ls="--", label="medium")
ax.set_xlabel("z [mm]"); ax.set_ylabel("slab-average static gauge pressure [Pa]"); ax.legend()
ax.set_title("Figure C4 - Axial static pressure, coarse vs medium", fontsize=11)
finish(fig, "figC04_pressure_vs_medium.png", "Inlet-to-outlet static drop (area-weighted faces, the Section 5B definition): "
       "%.2f Pa coarse vs %.2f Pa medium." % (PD["dp_total_area"], mp_["dp_total_area"]))

# ---- c05 bore heat flux and h
fig, axes = plt.subplots(2, 1, figsize=(12.5, 8.0), gridspec_kw=dict(hspace=0.32))
ax = axes[0]
ax.plot(prof["z"] * 1e3, prof["qi"], color=CC, lw=1.5, label="coarse")
ax.plot(PM["z"] * 1e3, PM["qi"], color=CM, lw=1.1, ls="--", label="medium")
ax.axhline(16000, color=GREY, lw=0.8, ls=":")
ax.set_ylim(13000, 20000); ax.set_ylabel("bore heat flux [W/m2]"); ax.legend(fontsize=8.5)
ax.set_title("(a) heat flux into the air at the bore (1-D value 16 000 W/m2 dotted; inlet peaks clipped)", fontsize=9.5)
ax = axes[1]
ax.plot(prof["z"] * 1e3, prof["h"], color=CC, lw=1.5, label="coarse")
ax.plot(PM["z"] * 1e3, PM["h"], color=CM, lw=1.1, ls="--", label="medium")
ax.set_ylim(60, 140); ax.set_xlabel("z [mm]"); ax.set_ylabel("h [W/m2K]"); ax.legend(fontsize=8.5)
ax.set_title("(b) local heat-transfer coefficient h = q_inner / (T_inner - T_bulk)", fontsize=9.5)
fig.suptitle("Figure C5 - Wall heat flux and heat-transfer coefficient, coarse vs medium", fontsize=11.5, y=0.995)
finish(fig, "figC05_heat_flux_h_vs_medium.png", "First slab: q = %.0f W/m2 (coarse) vs %.0f (medium); h at mid-span %.2f vs "
       "%.2f W/m2K." % (prof["qi"][0], PM["qi"][0], MID["z300"]["coarse"]["h"], MID["z300"]["medium"]["h"]))

# ---- c06 y+
fig, axes = plt.subplots(1, 2, figsize=(15, 5.2), gridspec_kw=dict(wspace=0.25))
ax = axes[0]
ax.plot(prof["z"] * 1e3, prof["yplus_avg"], color=CC, lw=1.5, label="coarse, slab mean")
ax.plot(prof["z"] * 1e3, prof["yplus_max"], color=CC, lw=0.9, ls=":", label="coarse, slab max")
ax.plot(PM["z"] * 1e3, PM["yplus_avg"], color=CM, lw=1.1, ls="--", label="medium, slab mean")
ax.plot(PM["z"] * 1e3, PM["yplus_max"], color=CM, lw=0.8, ls="-.", label="medium, slab max")
ax.axhline(1.0, color="k", lw=0.8)
ax.set_xlabel("z [mm]"); ax.set_ylabel("y+"); ax.set_ylim(0, 1.1); ax.legend(fontsize=8)
ax.set_title("(a) along the duct", fontsize=9.5)
ax = axes[1]
kc = int(np.argmin(abs(zc - 0.3)))
mcs = kI == kc
km = np.clip((WIM["z-coordinate"] / (L / 90)).astype(int), 0, 89)
kmm = int(np.argmin(abs((np.arange(90) + 0.5) * L / 90 - 0.3)))
mms = km == kmm
o1 = np.argsort(WI["th"][mcs]); o2 = np.argsort(WIM["th"][mms])
ax.plot(WI["th"][mcs][o1], WI["y-plus"][mcs][o1], "o-", color=CC, ms=3, lw=1.2, label="coarse, slab z = %.1f mm" % (zc[kc] * 1e3))
ax.plot(WIM["th"][mms][o2], WIM["y-plus"][mms][o2], "s--", color=CM, ms=2.5, lw=1.0,
        label="medium, slab z = %.1f mm" % ((kmm + 0.5) * L / 90 * 1e3))
ax.set_xlabel("theta [deg]"); ax.set_ylabel("y+"); ax.legend(fontsize=8)
ax.set_title("(b) around the circumference near mid-span (O-grid pattern)", fontsize=9.5)
fig.suptitle("Figure C6 - y+ on the conjugate wall, coarse vs medium (Fluent cell-centre y+)", fontsize=11.5, y=1.0)
finish(fig, "figC06_yplus_vs_medium.png", "Coarse: min %.3f, area mean %.3f, max %.3f; medium: min %.3f, mean %.3f, max %.3f."
       % (YP["min"], YP["area_mean"], YP["max"], my_["min"], my_["area_mean"], my_["max"]))

# ---- c07 Nu and f vs x/D
fig, axes = plt.subplots(1, 2, figsize=(15, 5.2), gridspec_kw=dict(wspace=0.25))
for ax, key, lab, lim in ((axes[0], "Nu", "local Nu", (40, 110)), (axes[1], "f_shear", "local Darcy f", (0.015, 0.04))):
    ax.plot(prof["x_over_D"], prof[key], color=CC, lw=1.5, label="coarse")
    ax.plot(PM["x_over_D"], PM[key], color=CM, lw=1.1, ls="--", label="medium")
    ax.axvspan(18, 29, color="#e8e8e8", alpha=0.7, lw=0)
    ax.set_ylim(*lim); ax.set_xlabel("x/D"); ax.set_ylabel(lab); ax.legend(fontsize=8.5)
axes[0].set_title("(a) Nu; window mean %.2f coarse vs %.2f medium" % (FD["Nu_cfd"], mfd_["Nu_cfd"]), fontsize=9.5)
axes[1].set_title("(b) f = 8 tau_w rho_b / G^2; window mean %.5f vs %.5f" % (FD["f_cfd"], mfd_["f_cfd"]), fontsize=9.5)
fig.suptitle("Figure C7 - Local Nusselt number and friction factor (grey = fully developed window x/D 18-29)", fontsize=11.5, y=1.0)
finish(fig, "figC07_nu_f_vs_medium.png", "")


# ---- c08 coarse temperature fields (meridional, circumferentially averaged cell values)
def theta_avg(d, fields, rnd=1e-6):
    rk = np.round(d["r"] / rnd).astype(np.int64)
    zk = np.round(d["z-coordinate"] / rnd).astype(np.int64)
    key = rk * 10 ** 7 + zk
    u, inv = np.unique(key, return_inverse=True)
    cnt = np.bincount(inv)
    out = {"r": np.bincount(inv, d["r"]) / cnt, "z": np.bincount(inv, d["z-coordinate"]) / cnt}
    for f_ in fields:
        out[f_] = np.bincount(inv, d[f_]) / cnt
    return out


def rz_contour(ax, A, field, zlim, rlim, levels, cmap):
    m = (A["z"] >= zlim[0] - 1e-9) & (A["z"] <= zlim[1] + 1e-9) & (A["r"] >= rlim[0] - 1e-9) & (A["r"] <= rlim[1] + 1e-9)
    z, r, v = A["z"][m], A["r"][m], A[field][m]
    zn = (z - zlim[0]) / (zlim[1] - zlim[0]); rn = (r - rlim[0]) / (rlim[1] - rlim[0])
    tri = mtri.Triangulation(zn, rn)
    return ax.tricontourf(mtri.Triangulation(z * 1e3, r * 1e3, tri.triangles), v, levels=levels, cmap=cmap)


FA = theta_avg(F, ["temperature", "z-velocity"])
SA = theta_avg(Sd, ["temperature"])
fig, axes = plt.subplots(3, 1, figsize=(12.5, 9.6), gridspec_kw=dict(hspace=0.45))
lv = np.linspace(300, float(np.ceil(max(F["temperature"].max(), Sd["temperature"].max()))), 30)
cs = rz_contour(axes[0], FA, "temperature", (0, L), (0, RI), lv, "inferno")
axes[0].set_title("(a) air, r = 0-10 mm", fontsize=9.5)
lvs = np.linspace(float(np.floor(Sd["temperature"].min())), float(np.ceil(Sd["temperature"].max())), 30)
cs2 = rz_contour(axes[1], SA, "temperature", (0, L), (RI, RO), lvs, "inferno")
axes[1].set_title("(b) Inconel wall, r = 10-20 mm", fontsize=9.5)
lvw = np.linspace(0, float(np.ceil(F["z-velocity"].max())), 29)
cs3 = rz_contour(axes[2], FA, "z-velocity", (0, L), (0, RI), lvw, "viridis")
axes[2].set_title("(c) axial velocity", fontsize=9.5)
for a_ in axes:
    a_.set_ylabel("r [mm]")
axes[-1].set_xlabel("z [mm]")
fig.colorbar(cs, ax=axes[0], pad=0.01, label="T [K]"); fig.colorbar(cs2, ax=axes[1], pad=0.01, label="T [K]")
fig.colorbar(cs3, ax=axes[2], pad=0.01, label="w [m/s]")
fig.suptitle("Figure C8 - Coarse mesh: temperature and axial velocity, meridional plane (radial scale exaggerated)",
             fontsize=11.5, y=0.995)
finish(fig, "figC08_coarse_fields.png", "Circumferentially averaged cell-centre values. Solid %.2f-%.2f K; air %.2f-%.2f K; "
       "max w %.2f m/s." % (Sd["temperature"].min(), Sd["temperature"].max(), F["temperature"].min(),
                            F["temperature"].max(), F["z-velocity"].max()))

# ---- c09 mid-span cross-section, coarse cell centres
fig, axes = plt.subplots(1, 2, figsize=(14, 6.4), gridspec_kw=dict(wspace=0.2))
kf = kF == kc; ks = kS == kc
for ax, pts, ttl in ((axes[0], None, "(a) cell centres of the mid-span slab, coloured by T"),
                     (axes[1], None, "(b) near-wall detail (first fluid cells and solid)")):
    sc = ax.scatter(np.concatenate([F["x-coordinate"][kf], Sd["x-coordinate"][ks]]) * 1e3,
                    np.concatenate([F["y-coordinate"][kf], Sd["y-coordinate"][ks]]) * 1e3,
                    c=np.concatenate([F["temperature"][kf], Sd["temperature"][ks]]), s=6, cmap="inferno")
    thp = np.linspace(0, 2 * np.pi, NT + 1)
    for rr in (RI, RO):
        ax.plot(rr * 1e3 * np.cos(thp), rr * 1e3 * np.sin(thp), color=C3, lw=0.9)
    ax.set_aspect("equal"); ax.set_title(ttl, fontsize=9.5); ax.set_xlabel("x [mm]"); ax.set_ylabel("y [mm]")
axes[1].set_xlim(6, 14); axes[1].set_ylim(-3, 3)
fig.colorbar(sc, ax=axes, shrink=0.8, label="T [K]")
fig.suptitle("Figure C9 - Coarse mesh at mid-span (slab centre z = %.0f mm): %d-sided polygon, %d fluid + %d solid cells per slab"
             % (zc[kc] * 1e3, NT, int(kf.sum()), int(ks.sum())), fontsize=11, y=0.98)
finish(fig, "figC09_coarse_midspan_section.png", "Green: the inscribed %d-gon at r = 10 and 20 mm." % NT)

# ---- c10 raw differences coarse vs medium
sel = ["inlet mass flow (Fluent flux report)", "heat-transfer rate (heated wall)", "pressure drop, static, area-weighted inlet - outlet",
       "outlet temperature, mass-weighted", "maximum solid temperature (outer-wall facet max)",
       "peak inner-wall temperature (facet max)", "through-wall dT, MID-SPAN z = 300 mm", "h, mid-span",
       "fully developed Nu (x/D 18-29)", "fully developed Darcy f (x/D 18-29)", "y+ area mean"]
rows_ = [c for c in CMP if c["quantity"] in sel]
fig, ax = plt.subplots(1, 1, figsize=(12.5, 6.0))
y_ = np.arange(len(rows_))
ax.barh(y_, [r["pct"] for r in rows_], color=CC, height=0.55, label="coarse vs medium")
for i, r in enumerate(rows_):
    if r["geometric_pct"] not in (None,):
        ax.plot([r["geometric_pct"]], [i], "k|", ms=16, mew=2, label="faceting alone" if i == 0 else None)
    ax.text(r["pct"] + (0.05 if r["pct"] >= 0 else -0.05), i, "%+.3f %%" % r["pct"], va="center",
            ha="left" if r["pct"] >= 0 else "right", fontsize=8)
ax.set_yticks(y_); ax.set_yticklabels([r["quantity"] for r in rows_], fontsize=8.5); ax.invert_yaxis()
ax.axvline(0, color="k", lw=0.8); ax.set_xlabel("(coarse - medium) / medium [%]"); ax.legend(fontsize=8.5, loc="lower right")
_lo = min(r["pct"] for r in rows_); _hi = max(r["pct"] for r in rows_)
ax.set_xlim(_lo - 0.45 * (_hi - _lo), _hi + 0.3 * (_hi - _lo))
ax.set_title("Figure C10 - Raw differences, coarse vs medium (black tick = difference expected from polygon faceting alone)",
             fontsize=10.5)
finish(fig, "figC10_differences_vs_medium.png", "Two points only; no extrapolation, no GCI and no independence verdict until the "
       "fine mesh is solved.")
print("DONE")
