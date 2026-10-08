# -*- coding: utf-8 -*-
"""
SECTION 9A - ANALYTICAL SCREENING OF THE PROPOSED PARAMETRIC CASES (RE-ANALYSIS 2026)

This is a SCREENING calculation. It is NOT CFD and NOT Mechanical data.
It is used only to reject bad parameter ranges before any expensive simulation.

Two layers of estimate are produced for every case:
  1. ANALYTICAL: the frozen Section 2 1-D model (same equations, same property tables as
     02_Engineering_Calculations/baseline_calculations.py): Petukhov friction, Gnielinski Nu with the
     Kays & Crawford (Tb/Tw)^0.5 property correction, 1-D radial conduction, Timoshenko thick cylinder,
     sigma = -E alpha dT for full axial restraint, Euler scaling for buckling.
  2. ANCHORED: the analytical CHANGE relative to the analytical baseline, applied to the solved
     project baseline (CFD Section 5B, FE Sections 7B / 8A):  X_case = X_base,solved * (X_case / X_base)_analytical
     (for temperatures: the RISE above 300 K is scaled).  This removes most of the known offset of the
     1-D model (e.g. T_max 19 K high, F-027 mean-temperature basis) but it is still an estimate.

Flags raised (any case):
  - air property table 250-600 K exceeded (interface/near-wall air temperature)   -> INVALID
  - Inconel E/k/cp/S_y table 20-400 C (293-673 K) exceeded                         -> INVALID
  - flow not fully turbulent (Re_min < 10,000) or below Gnielinski range (3,000)   -> FLAG / INVALID
  - pressure loss > 1 % of p_op (incompressible-ideal-gas assumption) or Mach > 0.3 -> FLAG
  - y+ (wall-resolved SST, same first cell) > 1                                     -> FLAG (re-mesh)
  - unrealistic thermal expansion: thermal strain > 0.5 % or flow-area change > 1 % (one-way coupling) -> FLAG
  - LC2 peak utilisation >= 1 (linear-elastic model invalid)                        -> INVALID
  - lambda_1 (current support S1) < 1 -> NOTE (the ideal straight column would bifurcate below this load)

Usage: python parametric_screening.py [baseline_parameters.json] [out_dir]
"""
import os, sys, json, math, csv, copy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PJSON = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "02_Engineering_Calculations", "baseline_parameters.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else HERE
D0 = json.load(open(PJSON))

# ------------------------------------------------------------------------------------------------
# Solved project baseline (P00_BASELINE) - the anchor. Values copied from the solved result files:
#   CFD: 06_Fluent_CFD/Baseline/cfd_baseline_results.json (medium mesh, Section 5B)
#   FE : 08_Structural_Analysis (7B) and 08_Structural_Analysis/Buckling (8A); mesh-converged (8B)
# ------------------------------------------------------------------------------------------------
P00 = {
    "mdot_kg_s": 0.0086622, "dp_Pa": 438.13, "T_out_K": 368.93, "Q_W": 602.76,
    "T_solid_max_K": 562.13, "T_outer_wall_max_K": 562.58, "T_interface_max_K": 555.27, "T_fluid_max_K": 553.41,
    "T_solid_min_K": 423.97, "T_solid_mean_K": 525.48, "yplus_max": 0.58484, "yplus_mean": 0.24096,
    "LC1_dL_mm": 1.840860, "LC1_utot_mm": 1.844307, "LC1_vm_max_MPa": 24.282, "LC1_vm_midspan_bore_MPa": 18.197,
    "LC2_vm_max_MPa": 605.161, "LC2_T_at_peak_K": 437.99, "LC2_mean_axial_MPa": -582.440, "LC2_N_N": 548936.6,
    "LC2_utot_mm": 0.134884, "LC2_ur_max_mm": 0.089734, "LC2_utilisation": 0.578,
    "lambda1_S1": 1.108047, "lambda1_S2": 4.29995, "Pcr_S1_kN": 608.25,
    "euler_fixed_pinned_hand": 2.286, "euler_fixed_pinned_shear_hand": 2.221,
}
LIM = {"air_T": (250.0, 600.0), "air_margin_K": 10.0, "solid_T": (293.15, 673.15), "solid_margin_K": 10.0,
       "Re_turb": 1.0e4, "Re_gniel": 3.0e3, "dp_frac": 0.01, "Mach": 0.3, "yplus": 1.0,
       "eps_th": 5.0e-3, "area_change_pct": 1.0}


# ------------------------------------------------------------------------------------------------
# Section 2 model (copied unchanged in substance from baseline_calculations.py; property tables from the JSON)
# ------------------------------------------------------------------------------------------------
class Props:
    def __init__(self, D):
        a = D["air_primary"]; s = D["solid_props"]
        self.aT, self.acp, self.amu = np.array(a["T_K"], float), np.array(a["cp"], float), np.array(a["mu"], float)
        self.ak, self.aPr = np.array(a["k"], float), np.array(a["Pr"], float)
        self.sT = np.array(s["T_C"], float) + 273.15
        self.sk, self.sE, self.sSy = np.array(s["k"], float), np.array(s["E_GPa"], float) * 1e9, np.array(s["Sy_MPa"], float) * 1e6
        self.cT, self.cA = np.array(s["cte_T_C"], float) + 273.15, np.array(s["cte"], float)
        self.R, self.p = D["params"]["R_air"]["value"], D["params"]["p_op"]["value"]
    cp = lambda s, T: np.interp(T, s.aT, s.acp)
    mu = lambda s, T: np.interp(T, s.aT, s.amu)
    k = lambda s, T: np.interp(T, s.aT, s.ak)
    Pr = lambda s, T: np.interp(T, s.aT, s.aPr)
    rho = lambda s, T: s.p / (s.R * T)
    ks = lambda s, T: np.interp(T, s.sT, s.sk)
    Es = lambda s, T: np.interp(T, s.sT, s.sE)
    Sy = lambda s, T: np.interp(T, s.sT, s.sSy)
    alpha = lambda s, T: np.interp(T, s.cT, s.cA)


# thermal strain exactly as the solver applies it (MPAMOD: secant table datum 21.11 C -> TREF 26.85 C)
_AT = np.array([93.33, 204.44, 315.56, 426.67, 537.78]); _AV = np.array([12.8, 13.3, 13.9, 14.2, 14.8]) * 1e-6
_T0, _TR = 21.11, 26.85
_AMOD = (_AV * (_AT - _T0) - np.interp(_TR, _AT, _AV) * (_TR - _T0)) / (_AT - _TR)
eps_th = lambda T_K: float(np.interp(T_K - 273.15, _AT, _AMOD) * (T_K - 273.15 - _TR))


def f_petukhov(Re):
    return 1.0 / (0.790 * np.log(Re) - 1.64) ** 2


def nu_gnielinski(Re, Pr):
    f = f_petukhov(Re)
    return ((f / 8) * (Re - 1000) * Pr) / (1 + 12.7 * np.sqrt(f / 8) * (Pr ** (2 / 3) - 1))


def model(D, pr, N=600):
    g = lambda k: D["params"][k]["value"]
    n_corr = g("n_corr")
    Di, Do, L = g("Di"), g("Do"), g("L")
    ri, ro = Di / 2, Do / 2
    A_c = math.pi * ri ** 2; P_wet = math.pi * Di; Dh = 4 * A_c / P_wet
    rho_in = pr.rho(g("T_in")); mdot = rho_in * g("V_in") * A_c; G = mdot / A_c
    A_i, A_o = math.pi * Di * L, math.pi * Do * L
    Q = g("qpp_o") * A_o; qpp_i = Q / A_i; qprime = Q / L
    x = np.linspace(0, L, N + 1); dx = L / N
    Tb = np.zeros(N + 1); Tb[0] = g("T_in")
    for i in range(1, N + 1):
        Tb[i] = Tb[i - 1] + qpp_i * P_wet * dx / (mdot * pr.cp(Tb[i - 1]))
    Re = G * Dh / pr.mu(Tb); f = f_petukhov(Re)
    h_cp = nu_gnielinski(Re, pr.Pr(Tb)) * pr.k(Tb) / Dh
    Twi = Tb + qpp_i / h_cp
    for _ in range(300):
        Twn = Tb + qpp_i / (h_cp * (Tb / Twi) ** n_corr)
        if np.max(np.abs(Twn - Twi)) < 1e-9:
            Twi = Twn; break
        Twi = 0.5 * (Twi + Twn)
    h = h_cp * (Tb / Twi) ** n_corr
    dTw = qprime * np.log(ro / ri) / (2 * math.pi * pr.ks(Twi)); Two = Twi + dTw
    rho = pr.rho(Tb); V = G / rho; Mach = V / np.sqrt(g("gamma") * g("R_air") * Tb)
    # pressure drop (CFD-comparable: friction + acceleration + developing-flow increment)
    f_m, rho_m, V_m = float(np.mean(f)), float(np.mean(rho)), float(np.mean(V))
    dp_fric = f_m * (L / Dh) * 0.5 * rho_m * V_m ** 2
    dp_acc = G ** 2 * (1 / rho[-1] - 1 / rho[0])
    dp_dev = g("K_dev") * 0.5 * rho_in * g("V_in") ** 2
    # wall shear velocity at the inlet (location of the baseline y+ maximum), air at the inlet temperature
    tau_in = f[0] / 8 * rho_in * g("V_in") ** 2
    u_tau_in = math.sqrt(tau_in / rho_in); nu_in = pr.mu(g("T_in")) / rho_in
    return dict(Di=Di, Do=Do, L=L, ri=ri, ro=ro, mdot=mdot, Q=Q, qpp_i=qpp_i, qprime=qprime, Tb=Tb, Re=Re, f=f, h=h,
                Twi=Twi, Two=Two, dTw=dTw, Mach=Mach, dp=dp_fric + dp_acc + dp_dev, dp_fric=dp_fric, dp_acc=dp_acc,
                u_tau_over_nu=u_tau_in / nu_in, x=x)


def cyl_bore_hoop(dT, a, b, E, al, nu):
    """Timoshenko: bore hoop stress magnitude for a log radial profile, free ends."""
    C = al * E * dT / (2 * (1 - nu) * np.log(b / a))
    lba, k2 = np.log(b / a), a ** 2 / (b ** 2 - a ** 2)
    return abs(C * (1 - np.log(b / a) - k2 * (1 + b ** 2 / a ** 2) * lba))


def section(Di, Do):
    A = math.pi / 4 * (Do ** 2 - Di ** 2); I = math.pi / 64 * (Do ** 4 - Di ** 4)
    return A, I


# ------------------------------------------------------------------------------------------------
def evaluate(case, pr, base_ana=None):
    D = copy.deepcopy(D0)
    for k, v in case["set"].items():
        D["params"][k]["value"] = v
    M = model(D, pr)
    nu = D["params"]["nu_s"]["value"]
    Tsm = float(np.mean(0.5 * (M["Twi"] + M["Two"])))            # Section 2 mean-solid basis
    r = dict(case=case["name"], group=case["group"], parameter=case["parameter"], value=case["value"], units=case["units"])
    r.update(Re_in=float(M["Re"][0]), Re_out=float(M["Re"][-1]), Re_min=float(M["Re"].min()), Mach_max=float(M["Mach"].max()),
             mdot_g_s=M["mdot"] * 1e3, Q_W=M["Q"], qpp_bore=M["qpp_i"], dp_Pa=M["dp"], dp_fric_Pa=M["dp_fric"], dp_acc_Pa=M["dp_acc"],
             h_exit=float(M["h"][-1]), h_mean=float(np.mean(M["h"])), T_out_K=float(M["Tb"][-1]),
             Twi_max_K=float(M["Twi"].max()), Two_max_K=float(M["Two"].max()), dTwall_exit_K=float(M["dTw"][-1]),
             Tsm_K=Tsm, u_tau_over_nu=M["u_tau_over_nu"])
    A, I = section(M["Di"], M["Do"])
    E_m = float(pr.Es(Tsm)); Sy_m = float(pr.Sy(Tsm))
    r.update(A_mm2=A * 1e6, I_mm4=I * 1e12, r_g_mm=math.sqrt(I / A) * 1e3,
             eps_th_mean=eps_th(Tsm), dL_mm=eps_th(Tsm) * M["L"] * 1e3,
             sig_LC2_MPa=-E_m * eps_th(Tsm) / 1e6, N_LC2_kN=E_m * eps_th(Tsm) * A / 1e3,
             sig_LC1_bore_MPa=cyl_bore_hoop(float(M["dTw"][-1]), M["ri"], M["ro"], float(pr.Es(M["Two"][-1] - M["dTw"][-1] / 2)),
                                            float(pr.alpha(M["Two"][-1] - M["dTw"][-1] / 2)), nu) / 1e6,
             EI_over_L2=E_m * I / M["L"] ** 2)
    if base_ana is None:
        return r, M
    b = base_ana
    rise = lambda key, P: 300.0 + (P - 300.0) * (r[key] - 300.0) / (b[key] - 300.0)
    s_mean = (r["Tsm_K"] - 300.0) / (b["Tsm_K"] - 300.0)
    a = {}
    a["dp_Pa"] = P00["dp_Pa"] * r["dp_Pa"] / b["dp_Pa"]
    a["T_out_K"] = rise("T_out_K", P00["T_out_K"])
    a["Q_W"] = P00["Q_W"] * r["Q_W"] / b["Q_W"]
    a["mdot_g_s"] = P00["mdot_kg_s"] * 1e3 * r["mdot_g_s"] / b["mdot_g_s"]
    a["T_interface_max_K"] = rise("Twi_max_K", P00["T_interface_max_K"])
    a["T_fluid_max_K"] = rise("Twi_max_K", P00["T_fluid_max_K"])
    a["T_solid_max_K"] = rise("Two_max_K", P00["T_solid_max_K"])
    a["T_solid_mean_K"] = rise("Tsm_K", P00["T_solid_mean_K"])
    a["T_solid_min_K"] = 300.0 + (P00["T_solid_min_K"] - 300.0) * s_mean       # inlet-end solid follows the heat input / flow
    a["yplus_max"] = P00["yplus_max"] * r["u_tau_over_nu"] / b["u_tau_over_nu"]
    # structural: solver thermal strain and E at the anchored volume-mean temperature
    Tm_c, Tm_b = a["T_solid_mean_K"], P00["T_solid_mean_K"]
    eE = lambda T: float(pr.Es(T)) * eps_th(T)
    a["LC1_dL_mm"] = P00["LC1_dL_mm"] * eps_th(Tm_c) / eps_th(Tm_b)
    a["LC1_vm_max_MPa"] = P00["LC1_vm_max_MPa"] * r["sig_LC1_bore_MPa"] / b["sig_LC1_bore_MPa"]
    a["LC2_mean_axial_MPa"] = P00["LC2_mean_axial_MPa"] * eE(Tm_c) / eE(Tm_b)
    a["LC2_vm_max_MPa"] = P00["LC2_vm_max_MPa"] * eE(Tm_c) / eE(Tm_b)       # trend only (peak follows the restrained part)
    a["LC2_N_kN"] = abs(a["LC2_mean_axial_MPa"]) * r["A_mm2"] / 1e3
    T_pk = 300.0 + (P00["LC2_T_at_peak_K"] - 300.0) * s_mean
    a["LC2_T_at_peak_K"] = T_pk
    a["LC2_utilisation"] = a["LC2_vm_max_MPa"] * 1e6 / float(pr.Sy(T_pk))
    a["first_yield_factor"] = 1.0 / a["LC2_utilisation"]
    stiff = (float(pr.Es(Tm_c)) * r["I_mm4"]) / (float(pr.Es(Tm_b)) * b["I_mm4"])
    a["lambda1_S1"] = P00["lambda1_S1"] * stiff * (P00["LC2_N_N"] / 1e3) / a["LC2_N_kN"]
    a["lambda1_S2"] = P00["lambda1_S2"] * stiff * (P00["LC2_N_N"] / 1e3) / a["LC2_N_kN"]
    a["lambda1_S3_hand"] = P00["euler_fixed_pinned_shear_hand"] * stiff * (P00["LC2_N_N"] / 1e3) / a["LC2_N_kN"]
    a["Pcr_S1_kN"] = a["lambda1_S1"] * a["LC2_N_kN"]
    a["area_change_pct"] = ((1 + eps_th(Tm_c)) ** 2 - 1) * 100
    r.update({"anch_" + k: v for k, v in a.items()})
    # ---------------- flags ----------------
    fl = []
    lo, hi = LIM["air_T"]
    if a["T_interface_max_K"] > hi:
        fl.append("INVALID: near-wall air %.0f K above the 600 K air-property table" % a["T_interface_max_K"])
    elif a["T_interface_max_K"] > hi - LIM["air_margin_K"]:
        fl.append("MARGINAL: near-wall air %.0f K within 10 K of the 600 K air table" % a["T_interface_max_K"])
    if a["T_solid_max_K"] > LIM["solid_T"][1]:
        fl.append("INVALID: solid %.0f K above the 673 K Inconel E/k/S_y tables" % a["T_solid_max_K"])
    elif a["T_solid_max_K"] > LIM["solid_T"][1] - LIM["solid_margin_K"]:
        fl.append("MARGINAL: solid within 10 K of the 673 K Inconel tables")
    if r["Re_min"] < LIM["Re_gniel"]:
        fl.append("INVALID: Re below the Gnielinski range")
    elif r["Re_min"] < LIM["Re_turb"]:
        fl.append("FLAG: transitional Re (< 10,000)")
    if r["dp_Pa"] / D0["params"]["p_op"]["value"] > LIM["dp_frac"]:
        fl.append("FLAG: dp > 1 % of p_op (incompressible-ideal-gas assumption)")
    if r["Mach_max"] > LIM["Mach"]:
        fl.append("FLAG: Mach > 0.3")
    if a["yplus_max"] > LIM["yplus"]:
        fl.append("FLAG: y+ > 1 with the baseline first cell (re-mesh inflation layer)")
    if a["LC1_dL_mm"] / (r.get("L", 0.6) * 1e3) > LIM["eps_th"] or a["area_change_pct"] > LIM["area_change_pct"]:
        fl.append("FLAG: thermal expansion outside the small-strain / one-way-coupling basis")
    if a["LC2_utilisation"] >= 1:
        fl.append("INVALID: LC2 peak at or above yield (linear-elastic model invalid)")
    if a["lambda1_S1"] < 1:
        fl.append("NOTE: lambda_1(S1) < 1 - the ideal straight column would bifurcate below this load")
    r["flags"] = "; ".join(fl) if fl else "OK"
    r["valid"] = bool(not any(x.startswith("INVALID") for x in fl))
    return r, M


# ------------------------------------------------------------------------------------------------
BASE_V, BASE_Q, BASE_DO = D0["params"]["V_in"]["value"], D0["params"]["qpp_o"]["value"], D0["params"]["Do"]["value"]
Q_TOTAL_BASE = BASE_Q * BASE_DO          # q''*Do held constant for thickness cases (constant total heat input)


def C(name, group, parameter, value, units, **setp):
    return dict(name=name, group=group, parameter=parameter, value=value, units=units, set=setp)


def t_case(name, t_mm, const="Q"):
    Do = 0.020 + 2 * t_mm / 1e3
    q = Q_TOTAL_BASE / Do if const == "Q" else BASE_Q
    return C(name, "thickness" + ("" if const == "Q" else " (const q'')"), "wall thickness", t_mm, "mm", Do=Do, qpp_o=q)


# candidate sweep (range selection) and the proposed matrix
CANDIDATES = [C("cand_V_%.3f" % s, "velocity sweep", "inlet velocity", round(BASE_V * s, 4), "m/s", V_in=BASE_V * s)
              for s in (0.70, 0.75, 0.80, 0.85, 0.875, 0.90, 1.0, 1.10, 1.125, 1.25, 1.50)] + \
             [C("cand_Q_%d" % q, "heat-flux sweep", "outer heat flux", q, "W/m2", qpp_o=float(q))
              for q in (6000, 7000, 7200, 7500, 8000, 8500, 8800, 9000, 9500, 10000, 12000)] + \
             [t_case("cand_T_%g" % t, t) for t in (6, 8, 10, 12, 14)] + \
             [t_case("cand_Tq_%g" % t, t, const="q") for t in (8, 12)] + \
             [C("corner_Vlow_Qhigh", "factorial corner (not proposed)", "V 0.9x & q 8800", 0, "-", V_in=BASE_V * 0.9, qpp_o=8800.0),
              C("corner_Vhigh_Qlow", "factorial corner (not proposed)", "V 1.1x & q 7200", 0, "-", V_in=BASE_V * 1.1, qpp_o=7200.0),
              C("corner_Vlow_Qlow", "factorial corner (not proposed)", "V 0.9x & q 7200", 0, "-", V_in=BASE_V * 0.9, qpp_o=7200.0),
              C("corner_Vhigh_Qhigh", "factorial corner (not proposed)", "V 1.1x & q 8800", 0, "-", V_in=BASE_V * 1.1, qpp_o=8800.0)]
MATRIX = [C("P00_BASELINE", "baseline", "baseline", 0, "-"),
          C("V01_LOW", "velocity", "inlet velocity", BASE_V * 0.9, "m/s", V_in=BASE_V * 0.9),
          C("V03_HIGH", "velocity", "inlet velocity", BASE_V * 1.1, "m/s", V_in=BASE_V * 1.1),
          C("Q01_LOW", "heat flux", "outer heat flux", 7200.0, "W/m2", qpp_o=7200.0),
          C("Q03_HIGH", "heat flux", "outer heat flux", 8800.0, "W/m2", qpp_o=8800.0),
          t_case("T01_THIN", 8.0), t_case("T03_THICK", 12.0)]

if __name__ == "__main__":
    pr = Props(D0)
    base, MB = evaluate(MATRIX[0], pr)
    # self-check against the frozen Section 2 results (must reproduce them)
    chk = {"Re_in": (base["Re_in"], 29957, 1), "dp_CFD_comparable": (base["dp_Pa"], 441.5, 0.2), "T_out": (base["T_out_K"], 368.85, 0.02),
           "Q": (base["Q_W"], 603.19, 0.01), "h_exit": (base["h_exit"], 77.83, 0.02), "Twi_exit": (base["Twi_max_K"], 574.43, 0.02),
           "dT_wall_exit": (base["dTwall_exit_K"], 7.28, 0.01), "T_mean_solid": (base["Tsm_K"], 554.7, 0.1)}
    selfcheck = {k: {"value": float(v), "section2": s, "ok": bool(abs(v - s) <= tol)} for k, (v, s, tol) in chk.items()}
    ok_all = all(x["ok"] for x in selfcheck.values())
    print("SELF-CHECK vs Section 2:", "PASS" if ok_all else "FAIL", json.dumps(selfcheck, indent=0)[:600])
    base_full, _ = evaluate(MATRIX[0], pr, base_ana=base)
    rows_m = [evaluate(c, pr, base_ana=base)[0] for c in MATRIX]
    rows_c = [evaluate(c, pr, base_ana=base)[0] for c in CANDIDATES]
    for rows, fn in ((rows_m, "screening_matrix"), (rows_c, "screening_candidates")):
        keys = list(rows[0].keys())
        with open(os.path.join(OUT, fn + ".csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
    b0 = rows_m[0]
    for r in rows_m:
        r["pct_vs_P00"] = {k: (100 * (r[k] - b0[k]) / abs(b0[k]) if isinstance(r[k], float) and b0[k] not in (0,) else None)
                           for k in r if k.startswith("anch_") and isinstance(r[k], float)}
    json.dump({"note": "SCREENING ONLY - analytical and anchored estimates, not CFD or Mechanical results",
               "selfcheck_section2": selfcheck, "anchor_P00": P00, "limits": LIM, "matrix": rows_m, "candidates": rows_c},
              open(os.path.join(OUT, "screening_results.json"), "w"), indent=1, default=float)
    fmt = "%-24s %8s %9s %7s %7s %7s %7s %7s %7s %7s %7s %7s %7s  %s"
    print(fmt % ("case", "value", "Re_in", "dp", "Tout", "Tif", "Tsmax", "Tmean", "LC2", "util", "lamS1", "yplus", "dL", "flags"))
    for r in rows_c + rows_m:
        print(fmt % (r["case"], "%.4g" % r["value"], "%.0f" % r["Re_in"], "%.0f" % r["anch_dp_Pa"], "%.1f" % r["anch_T_out_K"],
                     "%.1f" % r["anch_T_interface_max_K"], "%.1f" % r["anch_T_solid_max_K"], "%.1f" % r["anch_T_solid_mean_K"],
                     "%.0f" % r["anch_LC2_vm_max_MPa"], "%.3f" % r["anch_LC2_utilisation"], "%.3f" % r["anch_lambda1_S1"],
                     "%.3f" % r["anch_yplus_max"], "%.3f" % r["anch_LC1_dL_mm"], r["flags"]))
