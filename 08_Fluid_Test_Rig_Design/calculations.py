#!/usr/bin/env python3
"""Preliminary fluid-system calculations for the conceptual heated-duct test rig.

CONCEPTUAL, EDUCATIONAL. Not a construction-ready or certified pressure-system design.
Standard library only (Python 3.9+). Deterministic: same inputs give byte-identical output.
Writes only under --outdir (default: this folder); it never touches any other repository file.

    python calculations.py                  # regenerate the committed CSV/JSON outputs
    python calculations.py --outdir DIR     # write somewhere else (e.g. a temp dir)

Conventions (details: CALCULATION_METHOD.md)
  * Inputs from the existing project are in INPUTS, each with its source. Anything else is an
    assumption AS-nn (register in DESIGN_BASIS.md). Nothing is substituted silently: a missing
    key raises KeyError, an invalid value raises ValueError.
  * Every budget row is a TOTAL-pressure loss (Pa) between two stations, so the blower duty is
    the fan total pressure (FTP) = sum of the rows. The CFD static drop is converted once, in
    ta_points(), and appears in exactly one row (TA-101).
  * Gauge pressures are relative to ambient. Air is dry and ideal (AS-02).
"""
import argparse
import csv
import json
import math
from pathlib import Path

EXT_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXT_DIR.parent

# ======================================================================================
# 1. INPUTS FROM THE EXISTING PROJECT  (value, unit, source)
#    M### = ID in 05_Data/MASTER_PROJECT_DATA.csv. validate_design.py re-checks every one.
# ======================================================================================
BP = "01_Project_Documentation/BASELINE_PARAMETERS.md"
CR = "02_CFD_Fluent/Baseline/CFD_BASELINE_RESULTS.md"
CM = "03_Thermal_Structural_Mechanical/Case_Matrix/PARAMETRIC_CASE_MATRIX.csv"
INPUTS = {
    # geometry and boundary conditions of the test article
    "D_i": (0.020, "m", "M023"),
    "D_o": (0.040, "m", "M024"),
    "t_wall": (0.010, "m", "M025"),
    "L": (0.600, "m", "M026"),
    "T_in": (300.0, "K", "M002"),
    "V_in": (23.5, "m/s", "M003"),
    "p_op": (101325.0, "Pa", "M005"),
    "q_wall": (8000.0, "W/m2", "M006"),
    "R_air": (287.058, "J/(kg K)", BP),
    "gamma": (1.4, "-", BP),
    # existing CFD baseline (medium mesh)
    "dp_cfd": (438.13, "Pa", "M036"),
    "Q_heat_cfd": (602.755, "W", "M038"),
    "T_out_cfd": (368.93, "K", "M037"),
    "T_solid_max_cfd": (562.58, "K", "M039"),
    "Re_in_cfd": (29958.0, "-", "M034"),
    "Re_out_cfd": (25545.0, "-", "M035"),
    "mdot_cfd": (8.662155e-3, "kg/s", CR),
    "V_out_cfd": (28.894, "m/s", CR),
    "dp_accel_cfd": (149.31, "Pa", CR),
    "p0_in_cfd": (759.77091, "Pa", "02_CFD_Fluent/Audit/fluent_si_p0_area.txt"),
    "p0_out_cfd": (425.1597, "Pa", "02_CFD_Fluent/Audit/fluent_si_p0_area.txt"),
    "dp_cfd_coarse": (437.09, "Pa", "M059"),
    "dp_cfd_fine": (439.12, "Pa", "M051"),
    "dp_cfd_rich": (441.81, "Pa", "M070"),
    # existing velocity parametric cases (heat flux unchanged)
    "V_low": (21.15, "m/s", CM),
    "dp_low": (379.93, "Pa", "M125"),
    "T_out_low": (376.56, "K", "M126"),
    "V_high": (25.85, "m/s", CM),
    "dp_high": (499.69, "Pa", "M134"),
    "T_out_high": (362.69, "K", "M135"),
    "T_solid_max_env": (591.13, "K", "M154"),
    "defl_min_env": (1.6284, "mm", "M146"),
    "defl_max_env": (2.0680, "mm", "M155"),
    # existing Mechanical / material values
    "dL_LC1": (1.8409, "mm", "M085"),
    "F_LC2": (548936.6, "N", "M091"),
    "E_hot": (188.1e9, "Pa", BP),
    "alpha": (13.72e-6, "1/K", BP),
    "rho_s": (8190.0, "kg/m3", "M008"),
    "cp_s": (481.0, "J/(kg K)", BP),
    "T_solid_mean": (525.48, "K", CR),
    "T_ref": (300.0, "K", "M083"),
    # values quoted by the frozen baseline documents (cross-check references only)
    "Qv_frozen": (7.383e-3, "m3/s", BP),
    "mdot_frozen": (8.686e-3, "kg/s", BP),
    "Ma_in_frozen": (0.0677, "-", "01_Project_Documentation/FLUID_CALCULATIONS.md"),
    "q_in_frozen": (324.9, "Pa", "01_Project_Documentation/FLUID_CALCULATIONS.md"),
    "q_out_frozen": (399.5, "Pa", "01_Project_Documentation/FLUID_CALCULATIONS.md"),
}


def inp(name):
    return INPUTS[name][0]


# ======================================================================================
# 2. ASSUMPTIONS (register with rationale: DESIGN_BASIS.md section 5)
# ======================================================================================
T_AMB_DESIGN = 300.0                      # AS-01 K   rig ambient = CFD inlet reference
T_AMB_WARM = 313.0                        # AS-13 K   warm-day bound
SUTHERLAND = (1.716e-5, 273.15, 110.4)    # AS-02 (mu0 Pa s, T0 K, S K)
CP_AIR = 1008.0                           # AS-03 J/(kg K), 300-370 K mean, cross-check only
ROUGH = {"low": 1.5e-6, "nom": 4.5e-5, "high": 1.5e-4}   # AS-04 m
LEN_FACTOR = {"low": 0.75, "nom": 1.0, "high": 1.5}      # AS-05
ROUTE = {"L-102": (1.0, 1), "L-103": (2.0, 2),           # AS-05 (length m, 90-degree bends)
         "L-104": (0.5, 1), "L-107": (2.0, 2)}      # L-104: route after the 10 D downstream run
K_BEND = {"low": 0.15, "nom": 0.30, "high": 0.90}        # AS-06
K_VALVE = {"low": 0.05, "nom": 0.10, "high": 0.30}       # AS-06 open full-bore isolation valve
K_FLEX = {"low": 0.10, "nom": 0.30, "high": 1.00}        # AS-06 flexible connector
K_ENTR = {"low": 0.05, "nom": 0.50, "high": 1.00}        # AS-06 line entrance
K_EXIT = {"low": 1.00, "nom": 1.00, "high": 1.10}        # AS-06 free-jet exit
FILTER_DP = {"low": 50.0, "nom": 100.0, "high": 250.0}   # AS-07 Pa allocation at design flow
ORIFICE_C, ORIFICE_TARGET_DP = 0.60, 300.0               # AS-08 (eps = 1 assumed)
ORIFICE_BETA = (0.20, 0.70)                              # AS-08 screening range
FE_ALT_LOW, FE_HIGH_FACTOR = 50.0, 1.25                  # AS-08 Pa non-obstructive alternative
CONTR_ANGLE_DEG, CONTR_HIGH = 30.0, 1.25                 # AS-09
EXPAN_ANGLE_DEG, EXPAN_HIGH = 14.0, 1.10                 # AS-09
TA_LOW_FACTOR, TA_HIGH_FACTOR = 0.85, 1.15               # AS-10 (project tolerance PR-05)
SPOOL_DIAMETERS = 5                                      # AS-11 unheated 20 mm spools, each 5 D
METER_RUN = (20, 10)                                     # AS-15 straight run, upstream/downstream, in D
CANDIDATE_BORES = (0.025, 0.040, 0.050, 0.080)           # AS-16 internal diameters, m
VELOCITY_LIMIT = 20.0                                    # AS-16 m/s screening limit
ISO5167_MIN_BORE, ISO5167_MIN_RE = 0.050, 5000.0         # ISO 5167-2 scope (checked, see DESIGN_BASIS)
SPEED_HEADROOM = 0.10                                    # AS-13
BLOWER_ETA = (0.20, 0.50)                                # AS-14 (heating estimate only)
CASES = {                                                # AS-13 (flow factor, ambient K)
    "DESIGN": (1.00, T_AMB_DESIGN),
    "UPPER": (1.10, T_AMB_DESIGN),
    "UPPER_WARM": (1.10, T_AMB_WARM),
}
RECOMMENDED_BORE = 0.050                                 # selected in SYSTEM_DESCRIPTION.md


# ======================================================================================
# 3. VALIDATION OF INPUTS
# ======================================================================================
def check_inputs():
    for k, (v, _, _) in INPUTS.items():
        if not (isinstance(v, float) and math.isfinite(v) and v > 0):
            raise ValueError("input %s must be a positive finite number, got %r" % (k, v))
    if not inp("D_o") > inp("D_i"):
        raise ValueError("outer diameter must exceed inner diameter")
    if abs((inp("D_o") - inp("D_i")) / 2 - inp("t_wall")) > 1e-9:
        raise ValueError("wall thickness inconsistent with diameters")
    if not inp("V_low") < inp("V_in") < inp("V_high"):
        raise ValueError("velocity cases must bracket the baseline")
    for d in CANDIDATE_BORES:
        if not d > inp("D_i"):
            raise ValueError("candidate line bore %.3f m must exceed the test-article bore" % d)


# ======================================================================================
# 4. AIR PROPERTIES AND HYDRAULICS
# ======================================================================================
def mu_air(T):
    if not T > 0:
        raise ValueError("temperature must be positive")
    mu0, T0, S = SUTHERLAND
    return mu0 * (T / T0) ** 1.5 * (T0 + S) / (T + S)


def air(T):
    """Dry ideal-gas state at the operating pressure. AS-17: density is not corrected for the gauge
    pressure outside the test article (largest gauge pressure about 1.2 kPa, about 1.1 % of p_op)."""
    if not T > 0:
        raise ValueError("temperature must be positive")
    return {"T": T, "rho": inp("p_op") / (inp("R_air") * T), "mu": mu_air(T)}


def regime(re):
    return "laminar" if re < 2300 else ("transitional" if re < 4000 else "turbulent")


def colebrook(re, rel):
    """Darcy friction factor, Colebrook-White solved by fixed-point iteration."""
    if not (re > 0 and rel >= 0):
        raise ValueError("invalid Reynolds number or relative roughness")
    if re < 2300:
        return 64.0 / re
    f = 0.25 / math.log10(rel / 3.7 + 5.74 / re ** 0.9) ** 2
    for _ in range(200):
        f_new = (-2.0 * math.log10(rel / 3.7 + 2.51 / (re * math.sqrt(f)))) ** -2
        if abs(f_new - f) < 1e-15:
            return f_new
        f = f_new
    return f


def hyd(D, mdot, st):
    A = math.pi * D * D / 4.0
    V = mdot / (st["rho"] * A)
    return {"D": D, "A": A, "V": V, "q": 0.5 * st["rho"] * V * V,
            "Re": 4.0 * mdot / (math.pi * D * st["mu"])}


# ======================================================================================
# 5. FLOW BASIS (Phase 4A)
# ======================================================================================
D_I = inp("D_i")
A_I = math.pi * D_I ** 2 / 4.0
AIR_IN = air(inp("T_in"))
MDOT0 = AIR_IN["rho"] * inp("V_in") * A_I        # design mass flow, kg/s


def flow_basis():
    r = {}
    r["A_i"] = A_I
    r["Qv"] = inp("V_in") * A_I
    r["rho_in"] = AIR_IN["rho"]
    r["mdot"] = MDOT0
    r["G"] = MDOT0 / A_I
    r["mu_in"] = AIR_IN["mu"]
    r["Re_in"] = 4 * MDOT0 / (math.pi * D_I * AIR_IN["mu"])
    r["q_in"] = 0.5 * AIR_IN["rho"] * inp("V_in") ** 2
    r["a_in"] = math.sqrt(inp("gamma") * inp("R_air") * inp("T_in"))
    r["Ma_in"] = inp("V_in") / r["a_in"]
    # outlet state: bulk temperature from the CFD result, velocity from continuity
    out = air(inp("T_out_cfd"))
    r["rho_out"] = out["rho"]
    r["V_out"] = MDOT0 / (out["rho"] * A_I)
    r["Re_out"] = 4 * MDOT0 / (math.pi * D_I * out["mu"])
    r["q_out"] = 0.5 * out["rho"] * r["V_out"] ** 2
    r["Ma_out"] = r["V_out"] / math.sqrt(inp("gamma") * inp("R_air") * inp("T_out_cfd"))
    r["dp_accel"] = MDOT0 ** 2 / A_I ** 2 * (1 / out["rho"] - 1 / AIR_IN["rho"])
    # independent outlet-temperature estimate: energy balance on the model heat input
    A_o = math.pi * inp("D_o") * inp("L")
    r["Q_heat_model"] = inp("q_wall") * A_o
    r["T_out_est"] = inp("T_in") + r["Q_heat_model"] / (MDOT0 * CP_AIR)
    r["f_colebrook_smooth"] = colebrook(r["Re_in"], 0.0)
    r["f_petukhov"] = (0.790 * math.log(r["Re_in"]) - 1.64) ** -2
    r["regime_in"] = regime(r["Re_in"])
    r["dp_over_pop"] = inp("dp_cfd") / inp("p_op")
    return r


def flow_basis_rows(r):
    rows = []

    def add(name, unit, calc, ref, src, tol, note):
        d = (calc - ref) / ref * 100.0 if ref else float("nan")
        rows.append([name, unit, "%.6g" % calc, "%.6g" % ref, src, "%.3f" % d, "%.2f" % tol,
                     "PASS" if abs(d) <= tol else "NOTE", note])

    add("volumetric flow", "m3/s", r["Qv"], inp("Qv_frozen"), "BASELINE_PARAMETERS.md", 0.1,
        "A*V with A = pi*Di^2/4")
    add("mass flow (circular tube)", "kg/s", r["mdot"], inp("mdot_frozen"), "BASELINE_PARAMETERS.md", 0.1,
        "rho_in*V*A, rho = p/(R T)")
    add("mass flow vs CFD", "kg/s", r["mdot"], inp("mdot_cfd"), "CFD_BASELINE_RESULTS.md s4", 0.5,
        "CFD uses a 48-sided facetted bore: -0.285 % flow area (documented in the CFD results)")
    add("inlet Reynolds number", "-", r["Re_in"], inp("Re_in_cfd"), "M034", 0.2,
        "4 mdot/(pi D mu), Sutherland mu")
    add("outlet Reynolds number", "-", r["Re_out"], inp("Re_out_cfd"), "M035", 1.0,
        "CFD uses tabulated mu(T); Sutherland differs slightly")
    add("inlet Mach number", "-", r["Ma_in"], inp("Ma_in_frozen"), "FLUID_CALCULATIONS.md", 0.5,
        "V/sqrt(gamma R T)")
    add("inlet dynamic pressure", "Pa", r["q_in"], inp("q_in_frozen"), "FLUID_CALCULATIONS.md", 0.2, "0.5 rho V^2")
    add("outlet dynamic pressure", "Pa", r["q_out"], inp("q_out_frozen"), "FLUID_CALCULATIONS.md", 0.3,
        "1-D value at the CFD outlet bulk temperature")
    add("outlet velocity (continuity)", "m/s", r["V_out"], inp("V_out_cfd"), "CFD_BASELINE_RESULTS.md s4", 0.2,
        "mdot/(rho_out A) with CFD bulk outlet T")
    add("outlet temperature (energy balance)", "K", r["T_out_est"], inp("T_out_cfd"), "M037", 0.1,
        "T_in + q'' A_o/(mdot cp), cp = 1008 J/(kg K) assumed (AS-03)")
    add("heating acceleration term", "Pa", r["dp_accel"], inp("dp_accel_cfd"), "CFD_BASELINE_RESULTS.md s4", 1.0,
        "G^2 (1/rho_out - 1/rho_in)")
    add("friction factor (smooth Colebrook vs Petukhov)", "-", r["f_colebrook_smooth"], r["f_petukhov"],
        "FLUID_CALCULATIONS.md (Petukhov)", 2.0, "method cross-check at Re_in; CFD fully developed f = 0.02163 (M043)")
    return rows


# ======================================================================================
# 6. TEST ARTICLE: CFD static drop -> total-pressure loss (the only CFD row in the budget)
# ======================================================================================
def ta_points():
    """CFD cases at flow factor 0.9 / 1.0 / 1.1 with the static drop converted to a total-pressure loss.

    loss = dp_static + q_in - q_out   (1-D velocity pressures; q_out at the CFD outlet bulk temperature)
    """
    pts = []
    for f, V, dps, Tout in ((V_ / inp("V_in"), V_, dp_, T_) for V_, dp_, T_ in (
            (inp("V_low"), inp("dp_low"), inp("T_out_low")),
            (inp("V_in"), inp("dp_cfd"), inp("T_out_cfd")),
            (inp("V_high"), inp("dp_high"), inp("T_out_high")))):
        out = air(Tout)
        q_in = 0.5 * AIR_IN["rho"] * V * V
        V_out = V * AIR_IN["rho"] / out["rho"]
        q_out = 0.5 * out["rho"] * V_out ** 2
        pts.append({"f": f, "V_in": V, "dp_static": dps, "T_out": Tout, "q_in": q_in,
                    "V_out": V_out, "q_out": q_out, "loss": dps + q_in - q_out})
    return pts


def _interp(f, key, pts):
    """Piecewise log-log interpolation; the end segments extrapolate (flagged by cfd_supported)."""
    if f <= pts[1]["f"]:
        a, b = pts[0], pts[1]
    else:
        a, b = pts[1], pts[2]
    if key == "T_out":
        return a[key] + (b[key] - a[key]) * (f - a["f"]) / (b["f"] - a["f"])
    n = math.log(b[key] / a[key]) / math.log(b["f"] / a["f"])
    return a[key] * (f / a["f"]) ** n


def cfd_supported(f):
    return 0.9 - 1e-9 <= f <= 1.1 + 1e-9


# ======================================================================================
# 7. FLOW ELEMENT (orifice, generic) AND FITTING LOSS FORMS
# ======================================================================================
def orifice_dp(beta, D, mdot, rho):
    Ad = math.pi * (beta * D) ** 2 / 4.0
    return (mdot / (ORIFICE_C * Ad)) ** 2 * (1 - beta ** 4) / (2 * rho)


def orifice_ppl_fraction(beta):
    s = math.sqrt(1 - beta ** 4 * (1 - ORIFICE_C ** 2))
    return (s - ORIFICE_C * beta ** 2) / (s + ORIFICE_C * beta ** 2)


def size_orifice(D):
    """beta giving ORIFICE_TARGET_DP at design flow, clamped to ORIFICE_BETA. Bisection, 80 steps."""
    cold = air(T_AMB_DESIGN)
    lo, hi = ORIFICE_BETA
    clamp = ""
    if orifice_dp(hi, D, MDOT0, cold["rho"]) >= ORIFICE_TARGET_DP:
        beta, clamp = hi, "beta clamped at upper limit; signal above target"
    elif orifice_dp(lo, D, MDOT0, cold["rho"]) <= ORIFICE_TARGET_DP:
        beta, clamp = lo, "beta clamped at lower limit; signal below target"
    else:
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if orifice_dp(mid, D, MDOT0, cold["rho"]) > ORIFICE_TARGET_DP:
                lo = mid
            else:
                hi = mid
        beta = 0.5 * (lo + hi)
    dp = orifice_dp(beta, D, MDOT0, cold["rho"])
    return {"beta": beta, "d": beta * D, "dp_signal": dp, "ppl_fraction": orifice_ppl_fraction(beta),
            "ppl": orifice_ppl_fraction(beta) * dp, "clamp": clamp,
            "iso_scope": D >= ISO5167_MIN_BORE - 1e-12}


def k_contraction(sigma, gradual):
    """Handbook-form loss coefficient on small-end velocity pressure; sigma = A_small/A_large."""
    if gradual:
        return 0.8 * math.sin(math.radians(CONTR_ANGLE_DEG) / 2) * (1 - sigma)
    return 0.5 * (1 - sigma)


def k_expansion(sigma, gradual):
    """Loss coefficient on small-end velocity pressure; sigma = A_small/A_large."""
    if gradual:
        return 2.6 * math.sin(math.radians(EXPAN_ANGLE_DEG) / 2) * (1 - sigma) ** 2
    return (1 - sigma) ** 2          # Borda-Carnot: 0.5 rho (V1 - V2)^2


# ======================================================================================
# 8. PRESSURE BUDGET
# ======================================================================================
def build_budget(D, case, ori):
    """Rows for line bore D under a case ('DESIGN', ...). All dp are total-pressure losses in Pa."""
    f, T_amb = CASES[case] if isinstance(case, str) else case
    mdot = MDOT0 * f
    pts = ta_points()
    cold, hot = air(T_amb), air(_interp(f, "T_out", pts))
    lc, lh = hyd(D, mdot, cold), hyd(D, mdot, hot)       # candidate line, cold / hot side
    bi, bo = hyd(D_I, mdot, cold), hyd(D_I, mdot, hot)   # test-article bore, inlet / outlet side
    sig = (D_I / D) ** 2
    rows = []

    def add(rid, line, tag, group, desc, method, h, param, trip, cls, basis, ass, src, cfd="NO"):
        rows.append({"item_id": rid, "line_id": line, "tag": tag, "group": group, "description": desc,
                     "method": method, "v_ref_m_s": h["V"] if h else "", "q_ref_Pa": h["q"] if h else "",
                     "parameter": param, "dp_low_Pa": trip[0], "dp_nom_Pa": trip[1], "dp_high_Pa": trip[2],
                     "data_class": cls, "component_data_basis": basis, "assumption_ids": ass,
                     "source": src, "in_cfd_domain": cfd})

    def kloss(h, kd):
        return tuple(kd[k] * h["q"] for k in ("low", "nom", "high"))

    def fric(h, length):
        trip, fnom = [], None
        for k in ("low", "nom", "high"):
            fk = colebrook(h["Re"], ROUGH[k] / h["D"])
            trip.append(fk * (length * LEN_FACTOR[k] / h["D"]) * h["q"])
            if k == "nom":
                fnom = fk
        return tuple(trip), "f=%.5f; L=%.3f m; Re=%.0f" % (fnom, length, h["Re"])

    G_C, G_P = "CALC", "NONE_REQUIRED"
    G_G, G_V = "ASSUMED_GENERIC", "GENERIC_HANDBOOK_FORM"
    G_A, G_AV = "ALLOCATION", "VENDOR_DATA_REQUIRED"
    DW = "Darcy-Weisbach, Colebrook-White f"

    # --- intake (ambient to blower suction) ---
    add("B01", "L-102", "FLT-101", "fittings", "Line entrance from filter plenum to blower suction line",
        "K x q", lc, "K=%.2f" % K_ENTR["nom"], kloss(lc, K_ENTR), G_G, G_V, "AS-06", "generic K, handbook form")
    add("B02", "L-102", "FLT-101", "filter", "Intake filter, clean-to-loaded allocation (linear in flow)",
        "allocation", None, "allocation at design flow", tuple(FILTER_DP[k] * f for k in ("low", "nom", "high")),
        G_A, G_AV, "AS-07", "design allocation; filter data to be supplied by vendor")
    trip, par = fric(lc, ROUTE["L-102"][0])
    add("B03", "L-102", "L-102", "straight pipe", "Straight pipe, filter to blower suction", DW, lc, par, trip,
        G_C, G_P, "AS-04;AS-05", "Colebrook-White; assumed roughness and routing")
    add("B04", "L-102", "L-102", "fittings", "90-degree bends x%d, filter to blower suction" % ROUTE["L-102"][1],
        "n x K x q", lc, "n=%d; K=%.2f" % (ROUTE["L-102"][1], K_BEND["nom"]),
        tuple(ROUTE["L-102"][1] * x for x in kloss(lc, K_BEND)), G_G, G_V, "AS-06;AS-05", "generic K, handbook form")
    # --- discharge side, upstream of the test article (cold) ---
    add("B05", "L-103", "FC-101", "fittings", "Flexible connector at blower discharge", "K x q", lc,
        "K=%.2f" % K_FLEX["nom"], kloss(lc, K_FLEX), G_G, G_V, "AS-06", "generic K; convolution data needs vendor")
    trip, par = fric(lc, ROUTE["L-103"][0])
    add("B06", "L-103", "L-103", "straight pipe", "Straight pipe, blower discharge to metering run", DW, lc, par,
        trip, G_C, G_P, "AS-04;AS-05", "Colebrook-White; assumed roughness and routing")
    add("B07", "L-103", "L-103", "fittings", "90-degree bends x%d, blower discharge" % ROUTE["L-103"][1],
        "n x K x q", lc, "n=%d; K=%.2f" % (ROUTE["L-103"][1], K_BEND["nom"]),
        tuple(ROUTE["L-103"][1] * x for x in kloss(lc, K_BEND)), G_G, G_V, "AS-06;AS-05", "generic K, handbook form")
    add("B08", "L-103", "HV-101", "isolation valve", "Isolation valve, full-bore, fully open", "K x q", lc,
        "K=%.2f" % K_VALVE["nom"], kloss(lc, K_VALVE), G_G, G_V, "AS-06", "generic K; valve data needs vendor")
    trip, par = fric(lc, METER_RUN[0] * D)
    add("B09", "L-104", "L-104", "straight pipe", "Metering run, %d D straight upstream of FE-101" % METER_RUN[0],
        DW, lc, par, trip, G_C, G_P, "AS-04;AS-15", "Colebrook-White; run length scales with bore")
    d_fe = orifice_dp(ori["beta"], D, mdot, cold["rho"])
    ppl = ori["ppl_fraction"] * d_fe
    add("B10", "L-104", "FE-101", "flow element",
        "Orifice-type flow element, permanent pressure loss (signal %.0f Pa at this flow)" % d_fe,
        "orifice equation x permanent-loss fraction", lc,
        "beta=%.3f; C=%.2f; ISO 5167-2 scope %s" % (ori["beta"], ORIFICE_C, "yes" if ori["iso_scope"] else "NO"),
        (FE_ALT_LOW * f * f, ppl, FE_HIGH_FACTOR * ppl), G_G, G_V, "AS-08",
        "generic orifice model; low = non-obstructive alternative allocation")
    trip, par = fric(lc, METER_RUN[1] * D + ROUTE["L-104"][0])
    add("B11", "L-104", "L-104", "straight pipe",
        "Straight pipe: %d D downstream of FE-101 plus route to the test-article adapter" % METER_RUN[1], DW, lc,
        par, trip, G_C, G_P, "AS-04;AS-05;AS-15", "Colebrook-White; assumed roughness and routing")
    add("B12", "L-104", "L-104", "fittings", "90-degree bends x%d, to test-article adapter" % ROUTE["L-104"][1],
        "n x K x q", lc, "n=%d; K=%.2f" % (ROUTE["L-104"][1], K_BEND["nom"]),
        tuple(ROUTE["L-104"][1] * x for x in kloss(lc, K_BEND)), G_G, G_V, "AS-06;AS-05", "generic K, handbook form")
    kc_nom, kc_low = k_contraction(sig, False), k_contraction(sig, True)
    add("B13", "-", "ADP-101", "adapter", "Contraction, line bore to 20 mm test-article bore (outside CFD)",
        "K x q(20 mm bore)", bi, "sigma=%.4f; K_abrupt=%.3f; K_conical=%.3f" % (sig, kc_nom, kc_low),
        (kc_low * bi["q"], kc_nom * bi["q"], CONTR_HIGH * kc_nom * bi["q"]), G_G, G_V, "AS-09",
        "handbook form; nominal = abrupt, low = %.0f-degree cone" % CONTR_ANGLE_DEG)
    spool = SPOOL_DIAMETERS * D_I
    trip, par = fric(bi, spool)
    add("B14", "L-105", "L-105", "adapter", "Unheated 20 mm inlet instrument spool (outside CFD)", DW, bi, par, trip,
        G_C, G_P, "AS-04;AS-11", "Colebrook-White at 20 mm bore")
    # --- test article: the only row that uses the CFD result ---
    ta_loss = _interp(f, "loss", pts)
    ta_static = _interp(f, "dp_static", pts)
    ta_qin = 0.5 * AIR_IN["rho"] * (inp("V_in") * f) ** 2
    ta_qout = _interp(f, "q_out", pts)
    add("B15", "-", "TA-101", "test article",
        "Heated duct, CFD static drop converted to total-pressure loss",
        "dp_static + q_in - q_out", None,
        "dp_static=%.2f Pa; q_in=%.2f Pa; q_out=%.2f Pa%s" % (
            ta_static, ta_qin, ta_qout, "" if cfd_supported(f) else "; EXTRAPOLATED beyond CFD cases"),
        (TA_LOW_FACTOR * ta_loss, ta_loss, TA_HIGH_FACTOR * ta_static), "CFD_DERIVED", G_P, "AS-10",
        "M036 (+M125/M134 for other flows); high = static drop + 15 %", cfd="YES")
    # --- test-article outlet (hot) ---
    trip, par = fric(bo, spool)
    add("B16", "L-106", "L-106", "adapter", "Unheated 20 mm outlet instrument spool (outside CFD)", DW, bo, par,
        trip, G_C, G_P, "AS-04;AS-11", "Colebrook-White at 20 mm bore, hot air")
    be_nom, be_low = k_expansion(sig, False), k_expansion(sig, True)
    add("B17", "-", "ADP-102", "adapter", "Expansion, 20 mm bore to line bore (outside CFD)",
        "K x q(20 mm bore, hot)", bo, "sigma=%.4f; K_sudden=%.3f; K_conical=%.3f" % (sig, be_nom, be_low),
        (be_low * bo["q"], be_nom * bo["q"], EXPAN_HIGH * be_nom * bo["q"]), G_C, G_P, "AS-09",
        "Borda-Carnot momentum balance (nominal); low = %.0f-degree diffuser" % EXPAN_ANGLE_DEG)
    # --- discharge (hot) ---
    trip, par = fric(lh, ROUTE["L-107"][0])
    add("B18", "L-107", "L-107", "straight pipe", "Straight pipe, mixing section and discharge line (hot air)", DW, lh,
        par, trip, G_C, G_P, "AS-04;AS-05;AS-12", "Colebrook-White; hot properties, no heat loss")
    add("B19", "L-107", "FC-102", "fittings", "Flexible connection (thermal-growth accommodation), hot", "K x q", lh,
        "K=%.2f" % K_FLEX["nom"], kloss(lh, K_FLEX), G_G, G_V, "AS-06", "generic K; convolution data needs vendor")
    add("B20", "L-107", "L-107", "fittings", "90-degree bends x%d, discharge line" % ROUTE["L-107"][1],
        "n x K x q", lh, "n=%d; K=%.2f" % (ROUTE["L-107"][1], K_BEND["nom"]),
        tuple(ROUTE["L-107"][1] * x for x in kloss(lh, K_BEND)), G_G, G_V, "AS-06;AS-05", "generic K, handbook form")
    add("B21", "L-107", "STK-101", "discharge", "Free-jet discharge to atmosphere (velocity pressure dumped)",
        "K x q", lh, "K=%.2f" % K_EXIT["nom"], kloss(lh, K_EXIT), G_C, G_P, "AS-12",
        "static pressure at exit = ambient; kinetic energy lost")
    ctx = {"cold": cold, "hot": hot, "lc": lc, "lh": lh, "bi": bi, "bo": bo, "mdot": mdot, "f": f, "T_amb": T_amb,
           "ta_qin": ta_qin, "ta_qout": ta_qout}
    return rows, ctx


def totals(rows):
    return {k: sum(r["dp_%s_Pa" % k] for r in rows) for k in ("low", "nom", "high")}


def unsupported_share(rows):
    t = sum(r["dp_nom_Pa"] for r in rows)
    u = sum(r["dp_nom_Pa"] for r in rows if r["data_class"] in ("ASSUMED_GENERIC", "ALLOCATION"))
    return u / t


# ======================================================================================
# 9. STATIONS / STREAM TABLE (recommended bore, design case, nominal losses)
# ======================================================================================
def stream_table(rows, ctx, D):
    nom = {r["item_id"]: r["dp_nom_Pa"] for r in rows}
    ftp = sum(nom.values())
    lc, lh, bi, bo = ctx["lc"], ctx["lh"], ctx["bi"], ctx["bo"]
    cold, hot = ctx["cold"], ctx["hot"]

    def s(ids):
        return sum(nom[i] for i in ids)

    p0 = {}
    p0["S2"] = -s(["B01", "B02"])
    p0["S3"] = -s(["B01", "B02", "B03", "B04"])
    p0["S4"] = p0["S3"] + ftp
    p0["S5"] = p0["S4"] - s(["B05", "B06", "B07", "B08"])
    p0["S6"] = p0["S5"] - nom["B09"]
    p0["S7"] = p0["S6"] - nom["B10"]
    p0["S8"] = p0["S7"] - s(["B11", "B12"])
    p0["S9"] = p0["S8"] - nom["B13"]
    p0["S10"] = p0["S9"] - nom["B14"]
    p0["S11"] = p0["S10"] - nom["B15"]
    p0["S12"] = p0["S11"] - nom["B16"]
    p0["S13"] = p0["S12"] - nom["B17"]
    p0["S14"] = p0["S13"] - s(["B18", "B19", "B20"])
    spec = [
        ("S1", "INL-101", "L-101", "Ambient air at intake", cold, None, 0.0),
        ("S2", "FLT-101", "L-102", "Start of L-102: after filter and line entrance", cold, lc, p0["S2"]),
        ("S3", "BLW-101", "L-102", "End of L-102: blower suction flange", cold, lc, p0["S3"]),
        ("S4", "BLW-101", "L-103", "Start of L-103: blower discharge flange", cold, lc, p0["S4"]),
        ("S5", "HV-101", "L-103", "End of L-103: after HV-101, start of the metering run", cold, lc, p0["S5"]),
        ("S6", "FE-101", "L-104", "Flow element upstream (after 20 D straight run)", cold, lc, p0["S6"]),
        ("S7", "FE-101", "L-104", "Flow element downstream (after permanent loss)", cold, lc, p0["S7"]),
        ("S8", "ADP-101", "L-104", "End of L-104: contraction adapter inlet", cold, lc, p0["S8"]),
        ("S9", "ADP-101", "L-105", "Start of L-105: after contraction", cold, bi, p0["S9"]),
        ("S10", "TA-101", "L-105", "End of L-105: test-article inlet plane IF-1", cold, bi, p0["S10"]),
        ("S11", "TA-101", "L-106", "Start of L-106: test-article outlet plane IF-2", hot, bo, p0["S11"]),
        ("S12", "ADP-102", "L-106", "End of L-106: before expansion", hot, bo, p0["S12"]),
        ("S13", "ADP-102", "L-107", "Start of L-107: after expansion", hot, lh, p0["S13"]),
        ("S14", "STK-101", "L-107", "End of L-107: discharge exit plane, before exit loss", hot, lh, p0["S14"]),
    ]
    out = []
    for sid, tag, line, desc, st, h, p0v in spec:
        V = h["V"] if h else 0.0
        q = h["q"] if h else 0.0
        out.append({"station": sid, "tag": tag, "line_id": line, "description": desc, "T_K": st["T"],
                    "mdot_g_s": ctx["mdot"] * 1e3, "rho_kg_m3": st["rho"], "V_m_s": V,
                    "P0_gauge_Pa": p0v, "p_static_gauge_Pa": p0v - q})
    return out, ftp


# ======================================================================================
# 10. SENSITIVITY, CANDIDATES, DUTY, SYSTEM CURVE
# ======================================================================================
def sensitivity(rows):
    nom_total = sum(r["dp_nom_Pa"] for r in rows)
    out = []
    for r in rows:
        dl, dh = r["dp_low_Pa"] - r["dp_nom_Pa"], r["dp_high_Pa"] - r["dp_nom_Pa"]
        if abs(dl) > 1e-12 or abs(dh) > 1e-12:
            out.append(["OAT", r["item_id"], r["tag"], r["description"], "%.2f" % r["dp_nom_Pa"],
                        "%.2f" % dl, "%.2f" % dh, "%.2f" % (100 * dh / nom_total), r["data_class"]])
    out.sort(key=lambda x: (-max(abs(float(x[5])), abs(float(x[6]))), x[1]))
    for m in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
        t = sum(r["dp_nom_Pa"] * (m if r["data_class"] in ("ASSUMED_GENERIC", "ALLOCATION") else 1.0) for r in rows)
        out.append(["GLOBAL", "x%.2f" % m, "", "All ASSUMED_GENERIC and ALLOCATION rows scaled by %.2f" % m,
                    "%.2f" % nom_total, "", "%.2f" % (t - nom_total), "%.2f" % (100 * (t - nom_total) / nom_total), ""])
    return out


def duty(rows_by_case):
    """Blower duty points for the recommended bore (fan total pressure, Pa; suction volume flow, L/s)."""
    res = {}
    for case, (rows, ctx) in rows_by_case.items():
        t = totals(rows)
        res[case] = {"mdot_g_s": ctx["mdot"] * 1e3, "Q_suction_L_s": ctx["mdot"] / ctx["cold"]["rho"] * 1e3,
                     "FTP_low": t["low"], "FTP_nom": t["nom"], "FTP_high": t["high"],
                     "hyd_power_W": ctx["mdot"] / ctx["cold"]["rho"] * t["nom"]}
    ub = res["UPPER_WARM"]
    res["spec"] = {"Q_min_full_speed_L_s": ub["Q_suction_L_s"] / (1 - SPEED_HEADROOM),
                   "FTP_min_full_speed_Pa": ub["FTP_high"] / (1 - SPEED_HEADROOM) ** 2}
    return res


def candidates():
    out = []
    for D in CANDIDATE_BORES:
        ori = size_orifice(D)
        by = {c: build_budget(D, c, ori) for c in CASES}
        rows, ctx = by["DESIGN"]
        t = totals(rows)
        grp = {}
        for r in rows:
            grp[r["group"]] = grp.get(r["group"], 0.0) + r["dp_nom_Pa"]
        lc, lh = ctx["lc"], ctx["lh"]
        d = duty(by)
        ok = ori["iso_scope"] and lc["Re"] >= ISO5167_MIN_RE and lc["V"] <= VELOCITY_LIMIT
        out.append({"D": D, "ori": ori, "rows": rows, "ctx": ctx, "tot": t, "grp": grp, "duty": d,
                    "share_unsupported": unsupported_share(rows), "screen_ok": ok,
                    "ta_share": rows[14]["dp_nom_Pa"] / t["nom"]})
    return out


def system_curve(D):
    ori = size_orifice(D)
    out = []
    for f in (0.8, 0.9, 1.0, 1.1, 1.2, 1.3):
        rows, ctx = build_budget(D, (f, T_AMB_DESIGN), ori)
        t = totals(rows)
        out.append([f, ctx["mdot"] * 1e3, ctx["mdot"] / ctx["cold"]["rho"] * 1e3, t["low"], t["nom"], t["high"],
                    "YES" if cfd_supported(f) else "EXTRAPOLATED"])
    return out


# ======================================================================================
# 11. THERMAL AND STRUCTURAL INTERFACE SCREENING (Phase 4D)
# ======================================================================================
def interface():
    A_wall = math.pi / 4 * (inp("D_o") ** 2 - inp("D_i") ** 2)
    m = inp("rho_s") * A_wall * inp("L")
    EA = inp("E_hot") * A_wall
    dT = inp("T_solid_mean") - inp("T_ref")
    free = inp("alpha") * inp("L") * dT
    F_full = EA * inp("alpha") * dT
    I = math.pi / 64 * (inp("D_o") ** 4 - inp("D_i") ** 4)
    mu_l = inp("rho_s") * A_wall
    fscale = math.sqrt(inp("E_hot") * I / mu_l) / inp("L") ** 2
    r = {"A_wall": A_wall, "mass": m, "weight": m * 9.80665, "EA": EA, "k_tube": EA / inp("L"),
         "free_growth_est_mm": free * 1e3, "free_growth_LC1_mm": inp("dL_LC1"),
         "free_growth_diff_pct": (free * 1e3 / inp("dL_LC1") - 1) * 100,
         "F_full_est": F_full, "F_full_LC2": inp("F_LC2"), "F_full_diff_pct": (F_full / inp("F_LC2") - 1) * 100,
         "travel_min_mm": inp("defl_max_env"),
         "heating_rate_K_s": inp("Q_heat_cfd") / (m * inp("cp_s")),
         "f_cantilever_Hz": 1.8751 ** 2 / (2 * math.pi) * fscale,
         "f_pinned_Hz": math.pi / 2 * fscale,
         "f_fixed_Hz": 4.7300 ** 2 / (2 * math.pi) * fscale}
    r["time_100K_s"] = 100.0 / r["heating_rate_K_s"]
    r["stiff_table"] = []
    for k in (10.0, 100.0, 1000.0, 10000.0):          # N/mm, placeholders only
        keff = k * 1e3 * r["k_tube"] / (k * 1e3 + r["k_tube"])
        r["stiff_table"].append((k, keff * free))
    return r


def blower_heating(ftp, qsuc_l_s):
    hyd_w = qsuc_l_s * 1e-3 * ftp
    cap = MDOT0 * CP_AIR
    return [hyd_w / eta / cap for eta in BLOWER_ETA]


# ======================================================================================
# 12. OUTPUT
# ======================================================================================
def resolve_outdir(arg):
    out = Path(arg).resolve() if arg else EXT_DIR
    try:
        out.relative_to(REPO_ROOT)
    except ValueError:
        return out                       # outside the repository, e.g. a temp dir
    if out != EXT_DIR and EXT_DIR not in out.parents:
        raise SystemExit("refusing to write inside the repository outside %s" % EXT_DIR.name)
    return out


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def fx(x, nd):
    """Fixed-decimal text without negative zero."""
    return "%.*f" % (nd, round(x, nd) + 0.0)


def sig(x):
    """9 significant digits; magnitudes below 1e-9 are floating-point noise (e.g. closure residuals) and become 0.
    Without this, such residuals differ between Python builds and break byte-identical reproduction."""
    return 0.0 if abs(x) < 1e-9 else float("%.9g" % x)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--outdir", help="output directory (default: the extension folder)")
    args = ap.parse_args()
    out = resolve_outdir(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    check_inputs()

    fb = flow_basis()
    cands = candidates()
    rec = [c for c in cands if abs(c["D"] - RECOMMENDED_BORE) < 1e-9][0]
    rows_rec, ctx_rec = rec["rows"], rec["ctx"]
    stations, ftp = stream_table(rows_rec, ctx_rec, rec["D"])
    ifc = interface()
    pts = ta_points()
    heat = blower_heating(rec["duty"]["DESIGN"]["FTP_nom"], rec["duty"]["DESIGN"]["Q_suction_L_s"])
    n_ta = math.log(pts[2]["loss"] / pts[0]["loss"]) / math.log(pts[2]["f"] / pts[0]["f"])

    # ---- flow_basis.csv
    write_csv(out / "flow_basis.csv",
              ["quantity", "unit", "calculated", "reference", "reference_source", "difference_pct",
               "tolerance_pct", "status", "note"], flow_basis_rows(fb))

    # ---- pressure_drop_budget.csv (all candidate bores, design case)
    hdr = ["candidate_bore_mm", "item_id", "line_id", "tag", "group", "description", "method", "v_ref_m_s",
           "q_ref_Pa", "parameter", "dp_low_Pa", "dp_nom_Pa", "dp_high_Pa", "data_class",
           "component_data_basis", "assumption_ids", "source", "in_cfd_domain"]
    body = []
    for c in cands:
        for r in c["rows"]:
            body.append([("%g" % (c["D"] * 1e3))] + [
                ("%.3f" % r[k] if k == "v_ref_m_s" and r[k] != "" else
                 "%.2f" % r[k] if k in ("q_ref_Pa",) and r[k] != "" else
                 "%.2f" % r[k] if k.startswith("dp_") else r[k]) for k in hdr[1:]])
        t = c["tot"]
        body.append([("%g" % (c["D"] * 1e3)), "TOTAL", "", "", "total", "Fan total pressure required (sum of rows)",
                     "sum", "", "", "", "%.2f" % t["low"], "%.2f" % t["nom"], "%.2f" % t["high"], "", "", "", "", ""])
    write_csv(out / "pressure_drop_budget.csv", hdr, body)

    # ---- candidate_line_sizes.csv
    chdr = ["line_bore_mm", "line_area_mm2", "v_cold_m_s", "re_cold", "v_hot_m_s", "re_hot",
            "orifice_beta", "orifice_signal_Pa", "orifice_iso5167_2_scope", "friction_Pa", "fittings_Pa",
            "filter_Pa", "flow_element_Pa", "isolation_valve_Pa", "adapters_Pa", "test_article_Pa", "discharge_Pa",
            "total_low_Pa", "total_nom_Pa", "total_high_Pa", "ta_share_of_nom_pct",
            "unsupported_data_share_pct", "FTP_upper_warm_high_Pa", "screening_pass", "notes"]
    crow = []
    for c in cands:
        g, o = c["grp"], c["ori"]
        notes = []
        if not o["iso_scope"]:
            notes.append("bore below ISO 5167-2 minimum of 50 mm; orifice not covered by the standard")
        if o["clamp"]:
            notes.append(o["clamp"])
        if c["ctx"]["lc"]["V"] > VELOCITY_LIMIT:
            notes.append("velocity above screening limit")
        crow.append([
            "%g" % (c["D"] * 1e3), "%.1f" % (c["ctx"]["lc"]["A"] * 1e6), "%.3f" % c["ctx"]["lc"]["V"],
            "%.0f" % c["ctx"]["lc"]["Re"], "%.3f" % c["ctx"]["lh"]["V"], "%.0f" % c["ctx"]["lh"]["Re"],
            "%.3f" % o["beta"], "%.1f" % o["dp_signal"], "yes" if o["iso_scope"] else "NO",
            "%.2f" % g["straight pipe"], "%.2f" % g["fittings"], "%.2f" % g["filter"],
            "%.2f" % g["flow element"], "%.2f" % g["isolation valve"], "%.2f" % g["adapter"],
            "%.2f" % g["test article"], "%.2f" % g["discharge"],
            "%.2f" % c["tot"]["low"], "%.2f" % c["tot"]["nom"], "%.2f" % c["tot"]["high"],
            "%.1f" % (100 * c["ta_share"]), "%.1f" % (100 * c["share_unsupported"]),
            "%.2f" % c["duty"]["UPPER_WARM"]["FTP_high"], "yes" if c["screen_ok"] else "NO", "; ".join(notes)])
    write_csv(out / "candidate_line_sizes.csv", chdr, crow)

    # ---- pressure_budget_sensitivity.csv (recommended bore)
    write_csv(out / "pressure_budget_sensitivity.csv",
              ["kind", "item", "tag", "description", "dp_nom_Pa", "delta_low_Pa", "delta_high_Pa",
               "delta_high_pct_of_total", "data_class"], sensitivity(rows_rec))

    # ---- stream_table.csv
    write_csv(out / "stream_table.csv",
              ["station", "tag", "line_id", "description", "T_K", "mdot_g_s", "rho_kg_m3", "V_m_s",
               "P0_gauge_Pa", "p_static_gauge_Pa"],
              [[s["station"], s["tag"], s["line_id"], s["description"], "%.2f" % s["T_K"], "%.3f" % s["mdot_g_s"],
                "%.4f" % s["rho_kg_m3"], "%.3f" % s["V_m_s"], fx(s["P0_gauge_Pa"], 2),
                fx(s["p_static_gauge_Pa"], 2)] for s in stations])

    # ---- system_curve.csv
    write_csv(out / "system_curve.csv",
              ["flow_factor", "mdot_g_s", "Q_suction_L_s", "FTP_low_Pa", "FTP_nom_Pa", "FTP_high_Pa", "cfd_supported"],
              [["%.2f" % r[0], "%.3f" % r[1], "%.3f" % r[2], "%.1f" % r[3], "%.1f" % r[4], "%.1f" % r[5], r[6]]
               for r in system_curve(rec["D"])])

    # ---- thermal_structural_interface.csv
    irows = [
        ["TA-101 tube mass (Inconel 718, no flanges/heater/insulation)", "%.3f" % ifc["mass"], "kg", "DERIVED",
         "rho_s * pi/4 (Do^2 - Di^2) * L; rho_s = M008"],
        ["TA-101 tube weight", "%.2f" % ifc["weight"], "N", "DERIVED", "mass * 9.80665"],
        ["Free axial growth, existing Mechanical LC1", "%.4f" % ifc["free_growth_LC1_mm"], "mm", "EXISTING_RESULT",
         "M085"],
        ["Free axial growth, simple estimate alpha*L*(Tmean-Tref)", "%.4f" % ifc["free_growth_est_mm"], "mm", "DERIVED",
         "alpha 13.72e-6 1/K, Tmean 525.48 K (CFD volume mean), Tref 300 K"],
        ["Difference, estimate vs LC1", "%.2f" % ifc["free_growth_diff_pct"], "%", "DERIVED", "cross-check"],
        ["Largest LC1 maximum deformation in the existing parametric envelope", "%.4f" % ifc["travel_min_mm"], "mm",
         "EXISTING_RESULT", "M155 (Q03_HIGH); lower bound for joint travel, margin to be set at detail design"],
        ["Full-restraint axial force, existing LC2 end reaction", "%.1f" % ifc["F_full_LC2"], "N", "EXISTING_RESULT",
         "M091; bounding case, NOT a rig configuration"],
        ["Full-restraint axial force, simple estimate E*A*alpha*dT", "%.1f" % ifc["F_full_est"], "N", "DERIVED",
         "E = 188.1 GPa at 555 K, A = pi/4 (Do^2-Di^2)"],
        ["Difference, estimate vs LC2", "%.2f" % ifc["F_full_diff_pct"], "%", "DERIVED", "cross-check"],
        ["Tube axial stiffness E*A/L", "%.4g" % ifc["k_tube"], "N/m", "DERIVED", "E*A/L"],
        ["Adiabatic heating rate of the bare tube if flow is lost with heat input on", "%.4f" % ifc["heating_rate_K_s"],
         "K/s", "DERIVED", "Q_cfd/(m*cp_s); ignores heater/insulation mass and losses (AS-18)"],
        ["Time for +100 K at that rate", "%.0f" % ifc["time_100K_s"], "s", "DERIVED", "100/(rate); bare tube only"],
        ["First bending frequency, cantilever bound", "%.1f" % ifc["f_cantilever_Hz"], "Hz", "DERIVED",
         "Euler-Bernoulli, bare tube (AS-18)"],
        ["First bending frequency, pinned-pinned bound", "%.1f" % ifc["f_pinned_Hz"], "Hz", "DERIVED",
         "Euler-Bernoulli, bare tube (AS-18)"],
        ["First bending frequency, fixed-fixed bound", "%.1f" % ifc["f_fixed_Hz"], "Hz", "DERIVED",
         "Euler-Bernoulli, bare tube (AS-18)"],
        ["Test-article inlet static gauge pressure, design case", "%.2f" % stations[9]["p_static_gauge_Pa"], "Pa",
         "DERIVED", "stream_table.csv station S10; negligible against the thermal stresses of M090"],
        ["Existing peak outer-wall temperature, baseline", "%.2f" % inp("T_solid_max_cfd"), "K", "EXISTING_RESULT",
         "M039"],
        ["Existing peak outer-wall temperature, highest of the studied cases", "%.2f" % inp("T_solid_max_env"), "K",
         "EXISTING_RESULT", "M154 (Q03_HIGH)"],
        ["Existing outlet bulk air temperature", "%.2f" % inp("T_out_cfd"), "K", "EXISTING_RESULT", "M037"],
        ["Blower heating of the air, low-efficiency bound", "%.2f" % heat[0], "K", "ASSUMED",
         "all shaft power to the air; eta 0.20 (AS-14)"],
        ["Blower heating of the air, high-efficiency bound", "%.2f" % heat[1], "K", "ASSUMED",
         "all shaft power to the air; eta 0.50 (AS-14)"],
    ]
    for k, F in ifc["stiff_table"]:
        irows.append(["Illustrative end force at placeholder joint stiffness %g N/mm" % k, "%.1f" % F, "N", "ASSUMED",
                      "F = k_series * free growth; stiffness is a placeholder, vendor data required"])
    write_csv(out / "thermal_structural_interface.csv", ["quantity", "value", "unit", "class", "basis"], irows)

    # ---- calculation_results.json (flat, sorted keys; read by validate_design.py)
    res = {}
    for k, v in fb.items():
        res["flow." + k] = sig(v) if isinstance(v, float) else v
    for i, p in enumerate(pts):
        for k, v in p.items():
            res["ta.%d.%s" % (i, k)] = sig(v)
    res["ta.exponent_loss_vs_flow"] = sig(n_ta)
    res["ta.p0_loss_cfd_area_weighted"] = sig(inp("p0_in_cfd") - inp("p0_out_cfd"))
    for c in cands:
        b = "cand.%g." % (c["D"] * 1e3)
        res[b + "FTP_low"], res[b + "FTP_nom"], res[b + "FTP_high"] = (sig(c["tot"][k]) for k in ("low", "nom", "high"))
        res[b + "v_cold"] = sig(c["ctx"]["lc"]["V"])
        res[b + "re_cold"] = sig(c["ctx"]["lc"]["Re"])
        res[b + "beta"] = sig(c["ori"]["beta"])
        res[b + "orifice_signal"] = sig(c["ori"]["dp_signal"])
        res[b + "orifice_ppl"] = sig(c["ori"]["ppl"])
        res[b + "screen_ok"] = c["screen_ok"]
        res[b + "unsupported_share"] = sig(c["share_unsupported"])
        res[b + "FTP_upper_warm_high"] = sig(c["duty"]["UPPER_WARM"]["FTP_high"])
    for case in CASES:
        for k, v in rec["duty"][case].items():
            res["duty.%s.%s" % (case, k)] = sig(v)
    for k, v in rec["duty"]["spec"].items():
        res["duty.spec." + k] = sig(v)
    for s in stations:
        for k in ("T_K", "V_m_s", "P0_gauge_Pa", "p_static_gauge_Pa"):
            res["station.%s.%s" % (s["station"], k)] = sig(s[k])
    res["budget.FTP_nom_recommended"] = sig(ftp)
    res["check.ta_dp_from_stations"] = sig(stations[9]["p_static_gauge_Pa"] - stations[10]["p_static_gauge_Pa"])
    res["check.exit_static_gauge"] = sig(stations[13]["p_static_gauge_Pa"])
    res["flow.mdot_g_s"] = sig(fb["mdot"] * 1e3)
    res["flow.Qv_L_s"] = sig(fb["Qv"] * 1e3)
    for k, (v, _, _) in INPUTS.items():
        res["input." + k] = v
    for k, v in ifc.items():
        if isinstance(v, float):
            res["interface." + k] = sig(v)
    res["interface.blower_heating_K_low"], res["interface.blower_heating_K_high"] = sig(heat[0]), sig(heat[1])
    res["recommended_bore_mm"] = RECOMMENDED_BORE * 1e3
    with open(out / "calculation_results.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
        fh.write("\n")

    # ---- console summary
    print("mdot = %.4f g/s   Qv = %.4f L/s   Re_in = %.0f   Ma_in = %.4f" % (
        fb["mdot"] * 1e3, fb["Qv"] * 1e3, fb["Re_in"], fb["Ma_in"]))
    print("TA total-pressure loss %.2f Pa (CFD static %.2f Pa)" % (pts[1]["loss"], pts[1]["dp_static"]))
    for c in cands:
        print("bore %2g mm: V=%5.2f m/s  FTP low/nom/high = %7.1f / %7.1f / %7.1f Pa  screening=%s" % (
            c["D"] * 1e3, c["ctx"]["lc"]["V"], c["tot"]["low"], c["tot"]["nom"], c["tot"]["high"],
            "pass" if c["screen_ok"] else "FAIL"))
    print("outputs written to", out)


if __name__ == "__main__":
    main()
