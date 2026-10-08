# -*- coding: utf-8 -*-
"""
SECTION 8A - independent hand buckling estimate for the LC2 (fully axially restrained) heated duct.
RE-ANALYSIS 2026. Newly written; every input is either the frozen geometry, the datasheet material tables used
in Sections 7A/7B, or a value read from the solved 7B LC2 model (reaction forces and nodal temperatures).
Nothing here is a recovered internship value and nothing is a measurement.

What it does
  1. Applied load: the LC2 end reactions, read from the solver reaction table (s7b_react.csv), and the mean axial
     stress N/A. The local von Mises peak is listed for contrast only; it is NOT a column load.
  2. Section properties of the annulus (A, I, r), slenderness KL/r for several end conditions.
  3. Elastic (Euler) critical load with three moduli: hot-end E (lowest), volume-mean E, and a Rayleigh
     (energy) estimate that uses the actual bending stiffness EI(z) of the mapped temperature field with the
     constant-EI mode shape of each end condition.
  4. Shear-deformation (Engesser/Timoshenko) correction, Cowper shear coefficient for a hollow circular section.
  5. Euler applicability: transition slenderness and the Johnson parabola (inelastic estimate).
  6. Local / shell buckling screen: compactness (D/t) and the classical thin-shell formula (outside its validity).
  7. Load factors = critical load / applied load, and the equivalent temperature-rise factor.
Outputs: buckling_hand_results.json (+ printed tables).
Usage: python buckling_calculations.py [project_root]   (default: the cloud mirror used in this re-analysis)
"""
import json, math, os, sys
import numpy as np

ROOT = sys.argv[1] if len(sys.argv) > 1 else "<PROJECT_ROOT>"
S8 = os.path.join(ROOT, "08_Structural_Analysis")
OUT = os.environ.get("S8A_OUT", os.path.dirname(os.path.abspath(__file__)))

# ---------------- frozen geometry (Section 1/2) ----------------
DO, DI, L = 0.040, 0.020, 0.600
RO, RI = DO / 2, DI / 2
A = math.pi / 4 * (DO**2 - DI**2)
I = math.pi / 64 * (DO**4 - DI**4)
R_GYR = math.sqrt(I / A)
T_WALL = RO - RI
R_MEAN = (RO + RI) / 2

# ---------------- material tables (as in the 7A/7B solver input) ----------------
NU = 0.294                                   # [ASSUMED], T-014
T_E = np.array([20, 100, 200, 300, 400.0])   # degC
E_T = np.array([204, 199, 193, 187, 180.0]) * 1e9
T_A = np.array([93.33, 204.44, 315.56, 426.67, 537.78])
A_SEC = np.array([12.8, 13.3, 13.9, 14.2, 14.8]) * 1e-6
T0, TREF = 21.11, 26.85
A_ADJ = (A_SEC * (T_A - T0) - 12.8e-6 * (TREF - T0)) / (T_A - TREF)   # MAPDL MPAMOD re-referencing
SY_T = np.array([1030, 1060, 1040, 1020, 1000.0]) * 1e6              # VDM 4127 age-hardened, 20..400 degC


def E_of(tc):
    return np.interp(tc, T_E, E_T)


def Sy_of(tc):
    return np.interp(tc, T_E, SY_T)


def eps_th(tc):
    return np.interp(tc, T_A, A_ADJ) * (tc - TREF)


# ---------------- 1. applied load from the solved LC2 model ----------------
def read_csv(path):
    return np.loadtxt(path, delimiter=",", skiprows=1)


react = read_csv(os.path.join(S8, "LC2_Restrained", "Solver_Output", "s7b_react.csv"))
z_r = react[:, 3]
inlet = z_r < 1e-9
outlet = z_r > L - 1e-9
N_in = float(react[inlet, 6].sum())
N_out = float(react[outlet, 6].sum())
N_APPLIED = 0.5 * (abs(N_in) + abs(N_out))
SIG_MEAN = N_APPLIED / A
nod = read_csv(os.path.join(S8, "LC2_Restrained", "Solver_Output", "s7b_nodal.csv"))
x, y, z, T_C, seqv = nod[:, 1], nod[:, 2], nod[:, 3], nod[:, 14], nod[:, 12]
r = np.hypot(x, y)
load = {
    "reaction_inlet_face_N": N_in, "reaction_outlet_face_N": N_out,
    "applied_axial_compression_N": N_APPLIED,
    "mean_axial_stress_Pa": -SIG_MEAN,
    "local_von_mises_peak_Pa": float(seqv.max()),
    "note": "The column load is the axial force N (the end reaction). N/A is the mean axial stress. The 605 MPa von Mises "
            "peak is a local combined-stress value at the inlet outer edge and is not a column load.",
}

# ---------------- 2. bending stiffness EI(z) of the actual field ----------------
zr = np.round(z, 7)
rr = np.round(r, 7)
planes = np.unique(zr)
EI_z, EA_z, Tm_z = [], [], []
for q in planes:
    m = zr == q
    R, TT = rr[m], T_C[m]
    rad = np.unique(R)
    Tr = np.array([TT[R == v].mean() for v in rad])       # theta-mean temperature at each radius
    Er = E_of(Tr)
    trap = np.trapezoid
    EI_z.append(math.pi * trap(Er * rad**3, rad))          # integral of E y^2 dA for an axisymmetric E(r)
    EA_z.append(2 * math.pi * trap(Er * rad, rad))
    Tm_z.append(2 * math.pi * trap(Tr * rad, rad) / (math.pi * (rad[-1]**2 - rad[0]**2)))
EI_z, EA_z, Tm_z = map(np.array, (EI_z, EA_z, Tm_z))
# the trapezoid over only 6 radii on midside planes slightly misestimates I: normalise by the exact geometric I
I_num = np.array([math.pi * np.trapezoid(np.unique(rr[zr == q])**3, np.unique(rr[zr == q])) for q in planes])
EI_z = EI_z * I / I_num
E_bend_z = EI_z / I                                        # bending-effective modulus of each section
# volume-weighted means (a plain nodal average would be biased by the end-refined mesh)
EA_num = np.array([2 * math.pi * np.trapezoid(np.unique(rr[zr == q]), np.unique(rr[zr == q])) for q in planes])
E_vol = float(np.trapezoid(EA_z * A / EA_num, planes) / (A * L))
T_vol_C = float(np.trapezoid(Tm_z, planes) / L)
T_hot_C = float(T_C.max())
T_cold_C = float(T_C.min())
E_hot = float(E_of(T_hot_C))
E_cold = float(E_of(T_cold_C))
E_mean_len = float(np.trapezoid(E_bend_z, planes) / L)

# ---------------- 3. end conditions and mode shapes (constant-EI eigenfunctions) ----------------
kl_fp = 4.493409457909064     # tan(kL) = kL, clamped-pinned


def shapes(case, zz):
    s = zz / L
    if case == "pinned-pinned":
        return np.sin(math.pi * s), (math.pi / L) * np.cos(math.pi * s), -(math.pi / L)**2 * np.sin(math.pi * s)
    if case == "fixed-fixed":
        k = 2 * math.pi / L
        return 1 - np.cos(k * zz), k * np.sin(k * zz), k**2 * np.cos(k * zz)
    if case == "guided (fixed-fixed, sway free)":
        k = math.pi / L
        return np.cos(k * zz), -k * np.sin(k * zz), -k**2 * np.cos(k * zz)
    if case.startswith("fixed-pinned"):
        k = kl_fp / L
        zz2 = zz if "cold end fixed" in case else (L - zz)   # measure from the fixed end
        Acoef = -math.cos(kl_fp) / math.sin(kl_fp)
        w = Acoef * np.sin(k * zz2) + np.cos(k * zz2) - Acoef * k * zz2 - 1
        dw = Acoef * k * np.cos(k * zz2) - k * np.sin(k * zz2) - Acoef * k
        d2 = -k**2 * (Acoef * np.sin(k * zz2) + np.cos(k * zz2))
        if "hot end fixed" in case:
            dw = -dw
        return w, dw, d2
    raise ValueError(case)


CASES = [  # name, theoretical K, typical design K (AISC 360 Commentary, Table C-A-7.1), what it represents
    ("guided (fixed-fixed, sway free)", 1.0, 1.2,
     "end planes cannot rotate but may translate laterally: THIS IS WHAT THE LC2 FE MODEL IMPOSES"),
    ("pinned-pinned", 1.0, 1.0, "ends held laterally, free to rotate"),
    ("fixed-pinned (cold end fixed)", 0.6992, 0.8, "inlet clamped, outlet pinned, no sway"),
    ("fixed-pinned (hot end fixed)", 0.6992, 0.8, "outlet clamped, inlet pinned, no sway"),
    ("fixed-fixed", 0.5, 0.65, "both ends clamped against rotation and lateral translation (rigid flanges)"),
]

# shear coefficient (Cowper, hollow circular section)
m_ = DI / DO
K_SHEAR = 6 * (1 + NU) * (1 + m_**2)**2 / ((7 + 6 * NU) * (1 + m_**2)**2 + (20 + 12 * NU) * m_**2)


def euler(E, K):
    return math.pi**2 * E * I / (K * L)**2


def shear_corr(P, E):
    G = E / (2 * (1 + NU))
    return P / (1 + P / (K_SHEAR * G * A))


def johnson(Sy, E, slender):
    cc = math.sqrt(2 * math.pi**2 * E / Sy)
    if slender >= cc:
        return math.pi**2 * E / slender**2, cc, "Euler (elastic) range"
    return Sy - (Sy**2 / (4 * math.pi**2 * E)) * slender**2, cc, "intermediate (inelastic) range"


zfine = np.linspace(0, L, 4001)
EIfine = np.interp(zfine, planes, EI_z)
rows = []
for name, K, Kd, meaning in CASES:
    w, dw, d2 = shapes(name, zfine)
    P_ray = float(np.trapezoid(EIfine * d2**2, zfine) / np.trapezoid(dw**2, zfine))
    E_ray = P_ray * (K * L)**2 / (math.pi**2 * I)          # equivalent uniform modulus for this mode
    slender = K * L / R_GYR
    out = {"case": name, "meaning": meaning, "K_theoretical": K, "K_design_typical": Kd,
           "KL_m": K * L, "slenderness_KL_over_r": slender,
           "E_hot_end_Pa": E_hot, "E_volume_mean_Pa": E_vol, "E_rayleigh_mode_weighted_Pa": E_ray}
    for tag, E in (("hot_E", E_hot), ("mean_E", E_vol), ("rayleigh_EIz", E_ray)):
        P = euler(E, K)
        Ps = shear_corr(P, E)
        out["Pcr_euler_" + tag + "_N"] = P
        out["sigma_euler_" + tag + "_Pa"] = P / A
        out["LF_euler_" + tag] = P / N_APPLIED
        out["Pcr_euler_shear_" + tag + "_N"] = Ps
        out["LF_euler_shear_" + tag] = Ps / N_APPLIED
    # design K (information: how a design code would treat imperfect end fixity)
    out["LF_euler_rayleigh_designK"] = euler(E_ray, Kd) / N_APPLIED
    # Johnson with the hot-end yield (lowest S_y and E: conservative) and with the section-mean yield
    for tag, Sy, E in (("hot", float(Sy_of(T_hot_C)), E_hot), ("volmean", float(Sy_of(T_vol_C)), E_vol)):
        sj, cc, regime = johnson(Sy, E, slender)
        out["johnson_" + tag] = {"Sy_Pa": Sy, "E_Pa": E, "transition_slenderness_Cc": cc, "regime": regime,
                                 "sigma_cr_Pa": sj, "Pcr_N": sj * A, "LF": sj * A / N_APPLIED}
    rows.append(out)

# ---------------- 5/6. applicability and local / shell buckling screen ----------------
Sy_hot = float(Sy_of(T_hot_C))
Sy_min_field = float(Sy_of(np.array([T_cold_C, T_hot_C])).min())
squash = {"Sy_hot_Pa": Sy_hot, "P_squash_hot_N": Sy_hot * A, "LF_squash_hot": Sy_hot * A / N_APPLIED,
          "note": "first-yield ceiling for any column mode: the whole section at S_y of the hottest point"}
shell = {
    "D_over_t": DO / T_WALL, "R_mean_over_t": R_MEAN / T_WALL,
    "compact_limit_AISC_round_HSS_0.11E_over_Fy": 0.11 * E_hot / Sy_hot,
    "compact": DO / T_WALL < 0.11 * E_hot / Sy_hot,
    "classical_thin_shell_sigma_cl_Pa": E_hot * T_WALL / (R_MEAN * math.sqrt(3 * (1 - NU**2))),
    "classical_formula_valid": False,
    "note": ("R/t = 1.5 is a thick-walled tube, far outside thin-shell theory (which needs R/t of roughly 10 or more). "
             "The classical value is shown only to demonstrate the order of magnitude (tens of GPa, far above S_y): "
             "local shell buckling, ovalisation (Brazier) and circumferential wrinkling cannot precede yielding. "
             "The section is compact by the AISC round-HSS limit D/t < 0.11 E/F_y. No shell-buckling load is claimed."),
}
guided = rows[0]
thermal = {
    "volume_mean_T_K": T_vol_C + 273.15, "mean_temperature_rise_K": T_vol_C + 273.15 - 300.0,
    "note": ("For a fully restrained duct the axial force is proportional to the integrated thermal strain, so a load "
             "factor LF corresponds approximately to LF times the present thermal strain (about LF x the mean rise)."),
    "section2_temperature_basis": {"mean_rise_K": 254.7, "restrained_force_scale": 254.7 / 225.5},
}

R = {"note": "RE-ANALYSIS 2026 - hand estimates, not finite-element results",
     "geometry": {"Do_m": DO, "Di_m": DI, "L_m": L, "A_m2": A, "I_m4": I, "r_gyr_m": R_GYR, "L_over_r": L / R_GYR,
                  "wall_t_m": T_WALL, "L_over_Do": L / DO},
     "material": {"nu_ASSUMED": NU, "E_hot_Pa": E_hot, "E_cold_Pa": E_cold, "E_volume_mean_Pa": E_vol,
                  "E_bending_length_mean_Pa": E_mean_len, "T_hot_K": T_hot_C + 273.15, "T_cold_K": T_cold_C + 273.15,
                  "shear_coefficient_Cowper": K_SHEAR, "Sy_hot_Pa": Sy_hot},
     "applied_load": load, "cases": rows, "squash": squash, "shell_local": shell, "thermal_interpretation": thermal,
     "EI_profile": {"z_m": planes.tolist(), "E_bending_Pa": E_bend_z.tolist(), "T_section_mean_K": (Tm_z + 273.15).tolist()}}
json.dump(R, open(os.path.join(OUT, "buckling_hand_results.json"), "w"), indent=1)

# ---------------- printed summary ----------------
print("A = %.6e m2, I = %.6e m4, r = %.4f mm, L/r = %.2f" % (A, I, R_GYR * 1e3, L / R_GYR))
print("Applied N = %.1f N (inlet %.1f, outlet %.1f); mean stress %.2f MPa; local VM peak %.2f MPa (not a column load)"
      % (N_APPLIED, N_in, N_out, SIG_MEAN / 1e6, seqv.max() / 1e6))
print("E hot %.2f GPa, E cold %.2f, E vol-mean %.2f, shear k %.4f" % (E_hot / 1e9, E_cold / 1e9, E_vol / 1e9, K_SHEAR))
for o in rows:
    print("%-34s K=%.4f KL/r=%6.2f  E_ray=%.2f GPa  Euler P(ray)=%9.0f N LF=%.3f | +shear LF=%.3f | hotE LF=%.3f | "
          "Johnson(hot) %.0f MPa LF=%.3f [%s, Cc=%.1f] | designK LF=%.3f"
          % (o["case"], o["K_theoretical"], o["slenderness_KL_over_r"], o["E_rayleigh_mode_weighted_Pa"] / 1e9,
             o["Pcr_euler_rayleigh_EIz_N"], o["LF_euler_rayleigh_EIz"], o["LF_euler_shear_rayleigh_EIz"], o["LF_euler_hot_E"],
             o["johnson_hot"]["sigma_cr_Pa"] / 1e6, o["johnson_hot"]["LF"], o["johnson_hot"]["regime"],
             o["johnson_hot"]["transition_slenderness_Cc"], o["LF_euler_rayleigh_designK"]))
print("squash LF %.3f ; D/t %.1f vs compact limit %.1f ; thin-shell sigma_cl %.0f MPa (formula not valid)"
      % (squash["LF_squash_hot"], shell["D_over_t"], shell["compact_limit_AISC_round_HSS_0.11E_over_Fy"],
         shell["classical_thin_shell_sigma_cl_Pa"] / 1e6))
