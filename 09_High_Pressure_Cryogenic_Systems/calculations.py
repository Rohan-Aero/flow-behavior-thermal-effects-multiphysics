#!/usr/bin/env python3
"""Preliminary screening calculations for the conceptual GN2 pressure-control and LN2 transfer study.

CONCEPTUAL, EDUCATIONAL. NOT APPROVED FOR CONSTRUCTION. These are screening calculations only: they do not
validate pressure-vessel or piping integrity, relief-device sizing, or code compliance, and they are not
a design. Standard library only (Python 3.9+). Deterministic: same inputs give byte-identical output.

    python calculations.py                  # regenerate the committed CSV outputs
    python calculations.py --outdir DIR     # write somewhere else (e.g. a temporary directory)
    python calculations.py --headlines      # print the headline values quoted in the documents

Four kinds of number are kept apart (the class column of design_parameters.csv):
  EXISTING     a value already in this repository (register ID Mnnn in 05_Data/MASTER_PROJECT_DATA.csv)
  VERIFIED     a value read from an authoritative public source (verified_constants.csv, verified_properties.csv)
  ASSUMED / ILLUSTRATIVE
               an assumption (AS-nn) or an explicitly illustrative study case (IL-nn) made in this study
  UNRESOLVED   a required input nobody has provided. It has NO value. Any calculation that needs one
               raises MissingInputError instead of using a default.
  CALCULATED   a result of an equation written out in CALCULATION_METHOD.md
Nothing is substituted silently: a missing key raises KeyError, an invalid value raises ValueError.
"""
import argparse
import bisect
import csv
import math
import sys
from pathlib import Path

EXT_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXT_DIR.parent
BANNER = "CONCEPTUAL - NOT APPROVED FOR CONSTRUCTION"


class MissingInputError(RuntimeError):
    """Raised when a calculation needs an input that is registered as UNRESOLVED."""


# ======================================================================================
# 1. LOADERS FOR VERIFIED DATA
# ======================================================================================
def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fnum(s):
    return float(s) if s not in ("", None) else None


def load_constants(base=None):
    base = Path(base or EXT_DIR)
    return {r["id"]: r for r in read_csv(base / "verified_constants.csv")}


def load_props(base=None):
    base = Path(base or EXT_DIR)
    sets = {}
    for r in read_csv(base / "verified_properties.csv"):
        row = {k: (fnum(v) if k not in ("dataset_id", "row_kind", "phase") else v) for k, v in r.items()}
        sets.setdefault(r["dataset_id"], []).append(row)
    return sets


def interp(xs, ys, x):
    """Linear interpolation on ascending xs; raises ValueError outside the table (no extrapolation).

    A tolerance of 1e-6 of the table magnitude absorbs the 7-digit rounding of tabulated pressures.
    """
    tol = 1e-6 * max(abs(xs[0]), abs(xs[-1]), 1.0)
    if x < xs[0] - tol or x > xs[-1] + tol:
        raise ValueError(f"{x} outside table range {xs[0]} to {xs[-1]}")
    i = min(max(bisect.bisect_right(xs, x) - 1, 0), len(xs) - 2)
    t = (x - xs[i]) / (xs[i + 1] - xs[i])
    return ys[i] + t * (ys[i + 1] - ys[i])


def simpson(f, a, b, n=2000):
    h = (b - a) / n
    s = f(a) + f(b)
    for i in range(1, n):
        s += (4 if i % 2 else 2) * f(a + i * h)
    return s * h / 3.0


class Props:
    """Verified nitrogen property tables with interpolation. No extrapolation is ever done."""

    ISOBAR_PG = (0, 1, 2, 5, 10)   # gauge MPa for which isobars are tabulated
    P_ATM = 0.101325               # MPa

    def __init__(self, sets):
        self.sets = sets
        iso = sorted(sets["N2_GAS_300K_ISOTHERM"], key=lambda r: r["p_MPa_abs"])
        self.iso_p = [r["p_MPa_abs"] for r in iso]
        self.iso = iso
        self.isobars = {}
        for pg in self.ISOBAR_PG:
            rows = [r for r in sets[f"N2_GAS_ISOBAR_{pg}MPAG"] if r["phase"] != "liquid" and (pg > 0 or r["T_K"] >= 80)]
            rows.sort(key=lambda r: r["T_K"])
            self.isobars[pg] = rows

    def gas300(self, p_abs_MPa):
        """Gas at 300 K as a function of absolute pressure (MPa): rho, h, cp, cv, jt, mu, k."""
        out = {}
        for key in ("rho_kg_m3", "h_kJ_kg", "cp_kJ_kgK", "cv_kJ_kgK", "jt_K_per_MPa", "mu_uPa_s", "k_W_mK"):
            out[key] = interp(self.iso_p, [r[key] for r in self.iso], p_abs_MPa)
        return out

    def h_gas(self, T, pg):
        """Enthalpy (kJ/kg) of gas at temperature T and gauge pressure pg, from the tabulated isobars."""
        rows = self.isobars[pg]
        return interp([r["T_K"] for r in rows], [r["h_kJ_kg"] for r in rows], T)

    def T_from_h(self, h, pg):
        rows = self.isobars[pg]
        return interp([r["h_kJ_kg"] for r in rows], [r["T_K"] for r in rows], h)

    def isenthalpic(self, T_in, pg_in, pg_out):
        """Outlet temperature of an isenthalpic (Joule-Thomson) expansion between two gauge pressures.

        Inlet enthalpy comes from the 300 K isotherm table (any integer MPa gauge) when T_in is 300 K,
        otherwise from a tabulated isobar. The outlet must be on a tabulated isobar.
        """
        if abs(T_in - 300.0) < 1e-9:
            h_in = self.gas300(self.P_ATM + pg_in)["h_kJ_kg"]
        elif pg_in in self.isobars:
            h_in = self.h_gas(T_in, pg_in)
        else:
            raise ValueError("inlet state is not on a tabulated 300 K isotherm or isobar")
        return self.T_from_h(h_in, pg_out)

    def sat(self, name):
        """(liquid, vapour) rows at the boiling temperature for dataset N2_SAT_<name>MPAG."""
        rows = [r for r in self.sets[f"N2_SAT_{name}MPAG"] if r["T_K"] not in (70.0, 110.0)]
        liq = [r for r in rows if r["phase"] == "liquid"]
        vap = [r for r in rows if r["phase"] == "vapor"]
        if len(liq) != 1 or len(vap) != 1:
            raise ValueError(f"saturation rows for {name} not unique")
        return liq[0], vap[0]

    def k_vapor_1atm(self):
        """(T, k) pairs for N2 at 1 atm from the saturated-vapour point up to 320 K."""
        liq, vap = self.sat("0")
        pairs = [(vap["T_K"], vap["k_W_mK"])]
        pairs += [(r["T_K"], r["k_W_mK"]) for r in sorted(self.sets["N2_GAS_ISOBAR_0MPAG"], key=lambda r: r["T_K"])
                  if r["phase"] == "vapor" and r["T_K"] >= 80]
        return pairs


# ======================================================================================
# 2. PARAMETER REGISTER  (the single source of every number used below)
# ======================================================================================
REG = []   # rows of design_parameters.csv
PAR = {}   # param_id -> value (None for UNRESOLVED)
BP = "01_Project_Documentation/BASELINE_PARAMETERS.md"


def add(pid, system, group, name, value, unit, cls, source, bmin=None, bmax=None, aid="", note=""):
    if pid in PAR:
        raise ValueError(f"duplicate parameter id {pid}")
    if cls == "UNRESOLVED" and value is not None:
        raise ValueError(f"{pid} is UNRESOLVED and must not carry a value")
    if cls != "UNRESOLVED" and value is None:
        raise ValueError(f"{pid} has no value but class {cls}")
    PAR[pid] = value
    REG.append({"param_id": pid, "system": system, "group": group, "name": name, "value": value, "unit": unit, "class": cls,
                "source_ref": source, "bound_min": bmin, "bound_max": bmax, "assumption_id": aid, "note": note})
    return value


def P(pid):
    """Value of a registered parameter. Raises MissingInputError for an UNRESOLVED input."""
    if pid not in PAR:
        raise KeyError(pid)
    if PAR[pid] is None:
        raise MissingInputError(f"{pid} is UNRESOLVED: {next(r["name"] for r in REG if r["param_id"] == pid)}")
    return PAR[pid]


def build_register(consts, props):
    REG.clear()
    PAR.clear()
    cv = lambda i: float(consts[i]["value"])
    # ---- EXISTING (checked against 05_Data/MASTER_PROJECT_DATA.csv by validate_design.py) ----
    add("EX-01", "BOTH", "existing", "Ambient / gas reference temperature (CFD inlet temperature)", 300.0, "K", "EXISTING", "M002", 250, 350)
    add("EX-02", "BOTH", "existing", "Operating (ambient) absolute pressure", 101325.0, "Pa", "EXISTING", "M005", 90000, 110000)
    add("EX-03", "HP", "existing", "Air inlet velocity of the heated-duct CFD baseline", 23.5, "m/s", "EXISTING", "M003", 1, 100)
    add("EX-04", "HP", "existing", "Heated-duct inner diameter", 0.020, "m", "EXISTING", "M023", 0.001, 0.5)
    add("EX-05", "HP", "existing", "Specific gas constant of dry air", 287.058, "J/(kg K)", "EXISTING", BP, 280, 295)
    # ---- VERIFIED constants ----
    add("VC-01", "BOTH", "verified constant", "Molar gas constant", cv("VC-01"), "J/(mol K)", "VERIFIED", "VC-01", 8.3, 8.4)
    add("VC-02", "BOTH", "verified constant", "Molar mass of nitrogen", cv("VC-02"), "g/mol", "VERIFIED", "VC-02", 28.0, 28.1)
    add("VC-03", "CRYO", "verified constant", "Stefan-Boltzmann constant", cv("VC-03"), "W/(m2 K4)", "VERIFIED", "VC-03", 5.6e-8, 5.7e-8)
    add("VC-04", "BOTH", "verified constant", "Oxygen volume fraction of dry air", cv("VC-04"), "percent", "VERIFIED", "VC-04", 20, 21)
    add("VC-05", "BOTH", "verified constant", "Oxygen-deficient atmosphere threshold (29 CFR 1910.146(b))", cv("VC-05"), "percent", "VERIFIED", "VC-05", 19, 20)
    add("VC-06", "CRYO", "verified constant", "Boiling temperature of oxygen at 0.101325 MPa (context only: oxygen condenses above the nitrogen boiling temperature)", cv("VC-06"), "K", "VERIFIED", "VC-06", 89, 91)
    liq0, vap0 = props.sat("0")
    add("VP-01", "CRYO", "verified property", "Boiling temperature of N2 at 0.101325 MPa", liq0["T_K"], "K", "VERIFIED", "VP:N2_SAT_0MPAG", 77, 78)
    add("VP-02", "CRYO", "verified property", "Saturated liquid density at 0.101325 MPa", liq0["rho_kg_m3"], "kg/m3", "VERIFIED", "VP:N2_SAT_0MPAG", 800, 810)
    add("VP-03", "CRYO", "verified property", "Saturated vapour density at 0.101325 MPa", vap0["rho_kg_m3"], "kg/m3", "VERIFIED", "VP:N2_SAT_0MPAG", 4, 5)
    add("VP-04", "CRYO", "verified property", "Saturated liquid enthalpy at 0.101325 MPa", liq0["h_kJ_kg"], "kJ/kg", "VERIFIED", "VP:N2_SAT_0MPAG", -125, -120)
    add("VP-05", "CRYO", "verified property", "Saturated vapour enthalpy at 0.101325 MPa", vap0["h_kJ_kg"], "kJ/kg", "VERIFIED", "VP:N2_SAT_0MPAG", 75, 80)
    add("VP-06", "CRYO", "verified property", "Saturated liquid cv at 0.101325 MPa", liq0["cv_kJ_kgK"], "kJ/(kg K)", "VERIFIED", "VP:N2_SAT_0MPAG", 1.0, 1.2)
    g300 = props.gas300(Props.P_ATM)
    add("VP-07", "HP", "verified property", "Gas density at 300 K and 0.101325 MPa", g300["rho_kg_m3"], "kg/m3", "VERIFIED", "VP:N2_GAS_300K_ISOTHERM", 1.0, 1.3)
    gamma = g300["cp_kJ_kgK"] / g300["cv_kJ_kgK"]
    add("VP-08", "HP", "verified property", "cp/cv of N2 at 300 K and 0.101325 MPa (used as the isentropic exponent in screening)", gamma, "-", "VERIFIED", "VP:N2_GAS_300K_ISOTHERM", 1.3, 1.5)
    # ---- ASSUMPTIONS (AS-nn): registered in DESIGN_BASIS.md section 5 ----
    for lab, v in (("low", 0.0015), ("nom", 0.045), ("high", 0.15)):
        add(f"AS-02-{lab}", "HP", "assumption", f"Pipe wall roughness, {lab} case", v, "mm", "ASSUMED", "AS-02", 0.001, 0.5, "AS-02", "same set as 08_Fluid_Test_Rig_Design AS-04; material TBD")
    for key, nm, vals in (("bend", "Bend / elbow", (0.15, 0.30, 0.90)), ("valve", "Open full-bore isolation valve", (0.05, 0.10, 0.30)),
                          ("check", "Check valve, fully open", (1.0, 2.0, 5.0))):
        for lab, v in zip(("low", "nom", "high"), vals):
            add(f"AS-03-{key}-{lab}", "HP", "assumption", f"Generic loss coefficient K, {nm}, {lab}", v, "-", "ASSUMED", "AS-03", 0, 20, "AS-03", "on line velocity pressure; generic, not vendor data")
    for key, nm, vals in (("filter", "Filter pressure-drop allocation", (0.0010, 0.0025, 0.0050)), ("fe", "Flow element pressure-drop allocation", (0.0020, 0.0050, 0.0100))):
        for lab, v in zip(("low", "nom", "high"), vals):
            add(f"AS-04-{key}-{lab}", "HP", "assumption", f"{nm}, {lab}, fraction of local absolute pressure", v, "-", "ASSUMED", "AS-04", 0, 0.1, "AS-04", "design allocation to be met by a vendor, not a datasheet value")
    for lab, v in zip(("low", "nom", "high"), (0.75, 1.0, 1.5)):
        add(f"AS-05-lf-{lab}", "HP", "assumption", f"Route length factor, {lab}", v, "-", "ASSUMED", "AS-05", 0.5, 3.0, "AS-05", "covers a layout different from the conceptual one")
    for line, L, n in (("L-301", 2.0, 2), ("L-302", 0.5, 0), ("L-303", 3.0, 3), ("L-304", 2.0, 2), ("L-305", 6.0, 5)):
        add(f"AS-05-len-{line}", "HP", "assumption", f"Conceptual route length of {line}", L, "m", "ASSUMED", "AS-05", 0.1, 100, "AS-05", "no layout drawing exists")
        add(f"AS-05-bends-{line}", "HP", "assumption", f"Conceptual number of bends in {line}", n, "-", "ASSUMED", "AS-05", 0, 50, "AS-05")
    add("AS-06", "HP", "assumption", "Discharge coefficient of the regulator seat, screening only", 0.8, "-", "ASSUMED", "AS-06", 0.3, 1.0, "AS-06", "replace with vendor flow-coefficient data")
    # cryogenic assumptions
    for lab, v in zip(("low", "nom", "high"), (0.001, 0.003, 0.010)):
        add(f"AS-10-{lab}", "CRYO", "assumption", f"Effective emissivity of the MLI blanket (equivalent value), {lab}", v, "-", "ASSUMED", "AS-10", 1e-4, 0.1, "AS-10", "placeholder; vendor or test data required")
    for lab, v in zip(("low", "nom", "high"), (0.05, 0.10, 0.30)):
        add(f"AS-11-{lab}", "CRYO", "assumption", f"Emissivity of bare metal surfaces (both surfaces), {lab}", v, "-", "ASSUMED", "AS-11", 0.01, 1.0, "AS-11", "surface finish unknown")
    for lab, v in zip(("low", "nom", "high"), (0.7, 0.9, 1.0)):
        add(f"AS-12-{lab}", "CRYO", "assumption", f"Overall thermal accommodation coefficient, {lab}", v, "-", "ASSUMED", "AS-12", 0.1, 1.0, "AS-12")
    add("AS-13-design", "CRYO", "assumption", "Annulus gas pressure, design vacuum", 1e-3, "Pa", "ASSUMED", "AS-13", 1e-6, 10, "AS-13", "placeholder; the vacuum level of a real jacket is a vendor figure")
    add("AS-13-degraded", "CRYO", "assumption", "Annulus gas pressure, degraded vacuum", 1.0, "Pa", "ASSUMED", "AS-13", 1e-3, 1e3, "AS-13")
    add("AS-13-lost", "CRYO", "assumption", "Annulus gas pressure, vacuum lost", 101325.0, "Pa", "ASSUMED", "AS-13", 1e4, 2e5, "AS-13")
    for lab, v in zip(("low", "nom", "high"), (1e-5, 2e-5, 1e-4)):
        add(f"AS-14-AL-{lab}", "CRYO", "assumption", f"Cross-section over length of one stainless support path, {lab}", v, "m", "ASSUMED", "AS-14", 1e-7, 1e-2, "AS-14")
    for lab, v in zip(("low", "nom", "high"), (0.5, 1.0, 2.0)):
        add(f"AS-14-n-{lab}", "CRYO", "assumption", f"Number of support paths per metre of line, {lab}", v, "1/m", "ASSUMED", "AS-14", 0, 10, "AS-14")
    add("AS-15-hot-high", "CRYO", "assumption", "Warm-side (jacket) temperature, high case", 313.0, "K", "ASSUMED", "AS-15", 300, 340, "AS-15", "same warm-day bound as 08_Fluid_Test_Rig_Design AS-13")
    add("AS-16", "CRYO", "assumption", "Density of 304 stainless steel", 8000.0, "kg/m3", "ASSUMED", "AS-16", 7500, 8500, "AS-16", "typical handbook magnitude, not verified")
    # ---- ILLUSTRATIVE study cases (IL-nn): none is a requirement ----
    A = math.pi * P("EX-04") ** 2 / 4.0
    rho_air = P("EX-02") / (P("EX-05") * P("EX-01"))
    mdot = rho_air * P("EX-03") * A
    add("IL-01", "HP", "illustrative", "Illustrative nitrogen mass flow (set equal to the heated-duct air design flow)", mdot, "kg/s", "ILLUSTRATIVE", "CALC from EX-01..EX-05", 1e-3, 1e-1, "IL-01", "NOT a nitrogen flow requirement; gives the study a repository-traceable magnitude")
    add("IL-02", "HP", "illustrative", "Illustrative source pressure", 20.0, "MPa(g)", "ILLUSTRATIVE", "IL-02", 0.5, 45, "IL-02", "NOT a source specification")
    add("IL-03", "HP", "illustrative", "Illustrative stage-1 outlet (intermediate) set pressure", 5.0, "MPa(g)", "ILLUSTRATIVE", "IL-03", 0.5, 45, "IL-03")
    add("IL-04", "HP", "illustrative", "Illustrative stage-2 outlet (delivery) set pressure", 1.0, "MPa(g)", "ILLUSTRATIVE", "IL-04", 0.1, 45, "IL-04", "NOT a downstream requirement")
    add("IL-05", "HP", "illustrative", "Illustrative gas temperature at the source", 300.0, "K", "ILLUSTRATIVE", "EX-01", 250, 350, "IL-05")
    add("IL-06", "HP", "illustrative", "Illustrative uniform line inner diameter for the reference budget", 10.0, "mm", "ILLUSTRATIVE", "IL-06", 2, 100, "IL-06", "not a pipe or tube size")
    add("IL-07", "HP", "illustrative", "Line inner-diameter sweep for the sensitivity study", "6;8;10;12;16;20", "mm", "ILLUSTRATIVE", "IL-07", None, None, "IL-07")
    add("IL-08", "HP", "illustrative", "Component-loss multiplier sweep for the sensitivity study", "0.5;1;2;4", "-", "ILLUSTRATIVE", "IL-08", None, None, "IL-08")
    add("IL-09", "HP", "illustrative", "Illustrative limit on passive loss downstream of stage 2, fraction of the delivery set pressure", 0.05, "-", "ILLUSTRATIVE", "IL-09", 0.001, 0.5, "IL-09", "stands in for the unresolved downstream limit UI-04")
    add("IL-10", "HP", "illustrative", "Stage-1 inlet pressure sweep (source depletion and over-supply)", "30;25;20;15;10;7;6", "MPa(g)", "ILLUSTRATIVE", "IL-10", None, None, "IL-10")
    add("IL-11", "HP", "illustrative", "Stage-2 inlet pressure sweep (including stage 1 failed open)", "20;15;10;7;5;3;2", "MPa(g)", "ILLUSTRATIVE", "IL-11", None, None, "IL-11")
    add("IL-12", "CRYO", "illustrative", "Illustrative inner line outside diameter", 25.0, "mm", "ILLUSTRATIVE", "IL-12", 5, 200, "IL-12", "not a pipe size")
    add("IL-13", "CRYO", "illustrative", "Illustrative inner line wall thickness", 2.0, "mm", "ILLUSTRATIVE", "IL-13", 0.5, 20, "IL-13", "not a pressure-design thickness")
    add("IL-14", "CRYO", "illustrative", "Illustrative vacuum-jacket inner diameter", 50.0, "mm", "ILLUSTRATIVE", "IL-14", 10, 400, "IL-14")
    add("IL-15", "CRYO", "illustrative", "Illustrative straight-run lengths for totals", "5;10;20", "m", "ILLUSTRATIVE", "IL-15", None, None, "IL-15", "NOT a routing")
    add("IL-16", "CRYO", "illustrative", "Trapped-liquid screening pressure levels", "0.5;1;5;10", "MPa(g)", "ILLUSTRATIVE", "IL-16", None, None, "IL-16", "screening thresholds, NOT allowable pressures or relief settings")
    add("IL-17", "BOTH", "illustrative", "Illustrative well-mixed room volumes for oxygen-deficiency screening", "10;100;1000", "m3", "ILLUSTRATIVE", "IL-17", None, None, "IL-17")
    add("IL-18", "CRYO", "illustrative", "Closed-volume fill densities for the trapped-liquid isochores", "806.0844;760;700", "kg/m3", "ILLUSTRATIVE", "IL-18", None, None, "IL-18", "806.0844 is the saturated liquid density at 0.101325 MPa (VP-02)")
    # ---- UNRESOLVED inputs: no value, ever, until someone supplies a traceable one ----
    for uid, system, name in UNRESOLVED_INPUTS_SHORT:
        add(uid, system, "unresolved", name, None, "-", "UNRESOLVED", f"UNRESOLVED:{uid}")


# unresolved inputs (id, system, name). Full wording, reason and blocked calculations: MISSING_INPUTS below.
UNRESOLVED_INPUTS_SHORT = [
    ("UI-01", "HP", "Required downstream operating pressure and tolerance"),
    ("UI-02", "HP", "Nitrogen source type, pressure range, temperature range and depletion profile"),
    ("UI-03", "HP", "Required mass-flow range and duty cycle"),
    ("UI-04", "HP", "Downstream minimum and maximum pressure limits"),
    ("UI-05", "BOTH", "Pressure-system classification, governing design code and jurisdiction"),
    ("UI-06", "HP", "Design pressure and design temperature of each pressure zone"),
    ("UI-07", "HP", "Relief-device set pressures, required capacities and discharge locations"),
    ("UI-08", "HP", "Regulator characteristics: supply-pressure effect, droop, lock-up, minimum differential, flow curves"),
    ("UI-09", "HP", "Component specifications and ratings (valves, filter, flow element, check valve cracking pressure, hoses)"),
    ("UI-10", "BOTH", "Materials, seals, cleaning level and compatibility for the service temperature range"),
    ("UI-11", "HP", "Vent routing, discharge location, stack height, noise and silencing"),
    ("UI-12", "BOTH", "Room or area volume, ventilation rate and oxygen-deficiency classification"),
    ("UI-13", "BOTH", "Power and instrument-air failure positions and electrical area classification"),
    ("UI-20", "CRYO", "Source vessel capacity, maximum allowable working pressure, relief and vent capacity"),
    ("UI-21", "CRYO", "Transfer-line length, routing, elevation and bore"),
    ("UI-22", "CRYO", "Allowable pressures, relief set pressures, relief capacities and vent sizes"),
    ("UI-23", "CRYO", "Insulation system data: vacuum level, MLI specification, vendor heat-leak figures"),
    ("UI-24", "CRYO", "Support and spacer design, bellows or loop movement capacity"),
    ("UI-25", "CRYO", "Material grades, low-temperature toughness requirements and allowable stresses"),
    ("UI-26", "CRYO", "Receiving vessel or user, fill rate and pressure"),
    ("UI-27", "CRYO", "Required transfer rate, duration and driving pressure difference"),
    ("UI-28", "CRYO", "Cooldown time limit, valve and flange thermal masses"),
    ("UI-29", "CRYO", "Phase separator and cold vent sizing, vent dispersion and ground-level cold-vapour behaviour"),
    ("UI-30", "CRYO", "Installation environment: indoor or outdoor, drainage, spill containment, personnel exposure"),
    ("UI-31", "CRYO", "Cryogenic-qualified instrument ranges and accuracy"),
    ("UI-32", "CRYO", "Measured emissivity and MLI performance"),
    ("UI-33", "CRYO", "Two-phase pressure drop, flow regime and hydraulic-transient data"),
]


# ======================================================================================
# 3. HIGH-PRESSURE GN2: gas model, pressure budget, sensitivity, regulator envelope
# ======================================================================================
class HP:
    def __init__(self, props):
        self.props = props
        self.R_s = P("VC-01") / (P("VC-02") / 1000.0)          # J/(kg K)
        self.T = P("IL-05")
        self.gamma = P("VP-08")
        self.mdot = P("IL-01")
        self.p_atm_MPa = P("EX-02") / 1e6
        self.p_sup = P("IL-02") + self.p_atm_MPa                # MPa abs
        self.p_int = P("IL-03") + self.p_atm_MPa
        self.p_del = P("IL-04") + self.p_atm_MPa

    # gas state at 300 K ------------------------------------------------------------
    def state(self, p_Pa):
        g = self.props.gas300(p_Pa / 1e6)
        return dict(rho=g["rho_kg_m3"], zrt=p_Pa / g["rho_kg_m3"], mu=g["mu_uPa_s"] * 1e-6,
                    Z=p_Pa / (g["rho_kg_m3"] * self.R_s * self.T))

    @staticmethod
    def colebrook(Re, rr):
        if Re < 2300:
            return 64.0 / Re
        f = 0.02
        for _ in range(200):
            f_new = (-2.0 * math.log10(rr / 3.7 + 2.51 / (Re * math.sqrt(f)))) ** -2
            if abs(f_new - f) < 1e-13:
                f = f_new
                break
            f = f_new
        return f

    def pipe_dp(self, p1, D, L, eps):
        """Isothermal compressible pipe flow, p1 in Pa. Returns (dp, v_in, Re, f).

        p1^2 - p2^2 = G^2 (Z R T) (f L/D + 2 ln(p1/p2)),  Z R T = p/rho taken at the segment inlet.
        """
        A = math.pi * D * D / 4.0
        G = self.mdot / A
        st = self.state(p1)
        Re = G * D / st["mu"]
        f = self.colebrook(Re, eps / D)
        B = G * G * st["zrt"]
        fl = f * L / D
        F = lambda p2: p1 * p1 - p2 * p2 - B * (fl + 2.0 * math.log(p1 / p2))
        lo, hi = p1 * 1e-6, p1
        if F(lo) < 0:
            raise ValueError("flow exceeds the isothermal capacity of the pipe segment")
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if F(mid) > 0:
                lo = mid
            else:
                hi = mid
        p2 = 0.5 * (lo + hi)
        return p1 - p2, G / st["rho"], Re, f

    def k_dp(self, p1, D, K):
        A = math.pi * D * D / 4.0
        G = self.mdot / A
        st = self.state(p1)
        return K * G * G / (2.0 * st["rho"]), G / st["rho"]

    def mach(self, v, p):
        return v / math.sqrt(self.gamma * self.state(p)["zrt"])

    # row specification of the reference budget --------------------------------------
    ROWS = [
        # item, zone, line, tag, group, description, kind, arg
        ("B01", "HP", "L-301", "SRC-301", "pipe", "Source interface piping, friction", "pipe", "L-301"),
        ("B02", "HP", "L-301", "L-301", "fittings", "Bends in L-301", "bends", "L-301"),
        ("B03", "HP", "L-301", "HV-301", "valve", "Source isolation valve (block 1), fully open", "K", "valve"),
        ("B04", "HP", "L-302", "HV-302", "valve", "Second isolation valve (block 2), fully open", "K", "valve"),
        ("B05", "HP", "L-302", "L-302", "pipe", "Piping between the two isolation valves, friction", "pipe", "L-302"),
        ("B06", "HP", "L-303", "FLT-301", "filter", "High-pressure particulate filter, allocation", "alloc", "filter"),
        ("B07", "HP", "L-303", "L-303", "pipe", "Piping to stage-1 regulator, friction", "pipe", "L-303"),
        ("B08", "HP", "L-303", "L-303", "fittings", "Bends in L-303", "bends", "L-303"),
        ("B09", "HP", "L-303", "PCV-301", "regulation", "Stage-1 regulation: controlled drop to the intermediate set pressure (not a loss)", "ctrl", "int"),
        ("B10", "INT", "L-304", "L-304", "pipe", "Intermediate piping, friction", "pipe", "L-304"),
        ("B11", "INT", "L-304", "L-304", "fittings", "Bends in L-304", "bends", "L-304"),
        ("B12", "INT", "L-304", "PCV-302", "regulation", "Stage-2 regulation: controlled drop to the delivery set pressure (not a loss)", "ctrl", "del"),
        ("B13", "DEL", "L-305", "FE-301", "flow element", "Flow element, allocation", "alloc", "fe"),
        ("B14", "DEL", "L-305", "FCV-301", "flow control", "Downstream flow control valve: drop depends on unresolved UI-01/UI-04", "unres", "UI-04"),
        ("B15", "DEL", "L-305", "CV-301", "check valve", "Conditional check valve, fully open (K only)", "K", "check"),
        ("B16", "DEL", "L-305", "CV-301", "check valve", "Conditional check valve cracking pressure: vendor datasheet value", "unres", "UI-09"),
        ("B17", "DEL", "L-305", "XV-301", "valve", "Remote shutoff valve, fully open", "K", "valve"),
        ("B18", "DEL", "L-305", "HV-304", "valve", "Manual delivery block valve, fully open", "K", "valve"),
        ("B19", "DEL", "L-305", "L-305", "pipe", "Delivery piping, friction", "pipe", "L-305"),
        ("B20", "DEL", "L-305", "L-305", "fittings", "Bends in L-305", "bends", "L-305"),
        ("B21", "VENT", "L-307", "PSV-301", "vent", "Relief discharge back-pressure, stage-1 relief: needs relief flow (UI-07)", "unres", "UI-07"),
        ("B22", "VENT", "L-308", "PSV-302", "vent", "Relief discharge back-pressure, delivery relief: needs relief flow (UI-07)", "unres", "UI-07"),
        ("B23", "VENT", "L-309", "VS-301", "vent", "Vent header and stack back-pressure: needs vent flow and routing (UI-11)", "unres", "UI-11"),
    ]

    def chain(self, case, D=None, kmult=1.0):
        """Run the budget chain for case 'low' | 'nom' | 'high'. Returns a list of row dicts (Pa)."""
        D = (D if D is not None else P("IL-06")) / 1000.0
        eps = P(f"AS-02-{case}") / 1000.0
        lf = P(f"AS-05-lf-{case}")
        K = {k: P(f"AS-03-{k}-{case}") * kmult for k in ("bend", "valve", "check")}
        alloc = {k: P(f"AS-04-{k}-{case}") * kmult for k in ("filter", "fe")}
        setp = {"int": self.p_int * 1e6, "del": self.p_del * 1e6}
        p = self.p_sup * 1e6
        out = []
        for item, zone, line, tag, group, desc, kind, arg in self.ROWS:
            r = dict(item=item, zone=zone, line=line, tag=tag, group=group, desc=desc, kind=kind, p_in=p, dp=None, v=None, method="")
            if kind == "pipe":
                dp, v, Re, f = self.pipe_dp(p, D, P(f"AS-05-len-{arg}") * lf, eps)
                r.update(dp=dp, v=v, method=f"isothermal compressible pipe flow, Colebrook f={f:.4f}, Re={Re:.4g}")
            elif kind == "bends":
                n = P(f"AS-05-bends-{arg}")
                dp, v = self.k_dp(p, D, n * K["bend"])
                r.update(dp=dp, v=v, method=f"K x G^2/(2 rho), {n} bends")
            elif kind == "K":
                dp, v = self.k_dp(p, D, K[arg])
                r.update(dp=dp, v=v, method="K x G^2/(2 rho)")
            elif kind == "alloc":
                r.update(dp=alloc[arg] * p, v=self.mdot / (math.pi * D * D / 4.0) / self.state(p)["rho"], method="allocation: fraction x local absolute pressure")
            elif kind == "ctrl":
                if p <= setp[arg]:
                    raise ValueError("regulator inlet is not above its set pressure")
                r.update(dp=p - setp[arg], v=self.mdot / (math.pi * D * D / 4.0) / self.state(p)["rho"], method="p_in - set pressure")
                r["ctrl_set"] = setp[arg]
            elif kind == "unres":
                r.update(method=f"not calculated: needs {arg}")
                r["unres"] = arg
            if r["dp"] is not None and kind != "ctrl":
                p -= r["dp"]
            elif kind == "ctrl":
                p = setp[arg]
            r["p_out"] = p
            out.append(r)
        return out

    @staticmethod
    def zone_sum(rows, zone=None):
        return sum(r["dp"] for r in rows if r["dp"] is not None and r["kind"] != "ctrl" and (zone is None or r["zone"] == zone))

    # regulator envelope ----------------------------------------------------------------
    def rho_at(self, T, pg):
        """Real-gas density (kg/m3) at temperature T and gauge pressure pg (MPa), from the verified tables."""
        if abs(T - 300.0) < 1e-9:
            return self.props.gas300(self.p_atm_MPa + pg)["rho_kg_m3"]
        rows = self.props.isobars[int(pg)]
        return interp([r["T_K"] for r in rows], [r["rho_kg_m3"] for r in rows], T)

    def choked_flux(self, p0_Pa, rho0):
        """Choked mass flux through a unit area with discharge coefficient AS-06 (kg/(m2 s)): real density at p0, ideal exponent."""
        g, cd = self.gamma, P("AS-06")
        return cd * math.sqrt(g * rho0 * p0_Pa) * (2.0 / (g + 1.0)) ** ((g + 1.0) / (2.0 * (g - 1.0)))

    def flux(self, p0_Pa, p1_Pa, rho0):
        """Mass flux (kg/(m2 s)) through a restriction from p0 to p1: subsonic isentropic or choked."""
        g, cd = self.gamma, P("AS-06")
        r = p1_Pa / p0_Pa
        r_crit = (2.0 / (g + 1.0)) ** (g / (g - 1.0))
        if r <= r_crit:
            return self.choked_flux(p0_Pa, rho0), True, r, r_crit
        G = cd * math.sqrt(2.0 * rho0 * p0_Pa * g / (g - 1.0) * (r ** (2.0 / g) - r ** ((g + 1.0) / g)))
        return G, False, r, r_crit

    def reg_row(self, label, stage, T_in, pg_in, pg_out):
        p0 = (pg_in + self.p_atm_MPa) * 1e6
        p1 = (pg_out + self.p_atm_MPa) * 1e6
        rho0 = self.rho_at(T_in, pg_in)
        G, choked, r, rc = self.flux(p0, p1, rho0)
        T_out = self.props.isenthalpic(T_in, pg_in, pg_out)
        A_req_mm2 = self.mdot / G * 1e6 if pg_out > 0 else None     # not meaningful for a bleed to ambient
        return dict(case=label, stage=stage, p_in_MPa_g=pg_in, p_out_MPa_g=pg_out, T_in_K=T_in, ratio=r, ratio_crit=rc,
                    choked="TRUE" if choked else "FALSE", Z_in=p0 / (rho0 * self.R_s * T_in), rho_in=rho0, T_out_K=T_out, dT_K=T_out - T_in,
                    below_273K="TRUE" if T_out < 273.15 else "FALSE", G_kg_m2s=G, flux_g_s_mm2=G * 1e-6 * 1e3,
                    A_req_mm2=A_req_mm2, multiple=G * 1e-6 / self.mdot)

    def envelope(self):
        rows = []
        T_a = self.props.isenthalpic(300.0, int(P("IL-02")), int(P("IL-03")))   # gas leaving stage 1 in the design case
        for s in P("IL-10").split(";"):
            rows.append(self.reg_row("stage 1, inlet sweep to the intermediate set pressure", "PCV-301", 300.0, int(s), int(P("IL-03"))))
        rows.append(self.reg_row("stage 2, normal (inlet is the cold stage-1 outlet gas)", "PCV-302", T_a, int(P("IL-03")), int(P("IL-04"))))
        for s in P("IL-11").split(";"):
            rows.append(self.reg_row("stage 2, inlet sweep at 300 K (stage 1 failed open, full source pressure possible)", "PCV-302", 300.0, int(s), int(P("IL-04"))))
        rows.append(self.reg_row("single stage, source to delivery set pressure", "PCV-301/302 alternative", 300.0, int(P("IL-02")), int(P("IL-04"))))
        rows.append(self.reg_row("controlled depressurization, delivery set pressure to ambient (JT only; expansion cooling of the remaining gas not modelled)", "HV-305", 300.0, int(P("IL-04")), 0))
        return rows


def pressure_budget_rows(hp):
    low, nom, high = hp.chain("low"), hp.chain("nom"), hp.chain("high")
    out = []
    Ai = math.pi * (P("IL-06") / 1000.0) ** 2 / 4.0
    for a, b, c in zip(low, nom, high):
        flag = "FALSE" if b["kind"] in ("ctrl", "unres") else "TRUE"
        if b["kind"] == "ctrl":
            cls, basis = "CONTROLLED", "set by the regulator, not a loss"
        elif b["kind"] == "unres":
            cls, basis = "UNRESOLVED", f"VENDOR_OR_DESIGN_DATA_REQUIRED ({b['unres']})"
        elif b["kind"] == "alloc":
            cls, basis = "ALLOCATION", "VENDOR_DATA_REQUIRED"
        elif b["kind"] == "pipe":
            cls, basis = "CALCULATED_ASSUMED_ROUTE", "route and material TBD"
        else:
            cls, basis = "CALCULATED_GENERIC", "VENDOR_DATA_REQUIRED"
        aids = {"pipe": "AS-02;AS-05", "bends": "AS-03;AS-05", "K": "AS-03", "alloc": "AS-04", "ctrl": "IL-02;IL-03;IL-04", "unres": ""}[b["kind"]]
        out.append(dict(
            case_id="ILL-REF", item_id=b["item"], zone=b["zone"], line_id=b["line"], tag=b["tag"], group=b["group"],
            description=b["desc"], method=b["method"], data_class=cls, data_basis=basis, assumption_ids=aids,
            included_in_total=flag, p_in_MPa_g=(b["p_in"] / 1e6 - hp.p_atm_MPa), v_in_m_s=b["v"],
            dp_low_kPa=None if a["dp"] is None else a["dp"] / 1e3, dp_nom_kPa=None if b["dp"] is None else b["dp"] / 1e3,
            dp_high_kPa=None if c["dp"] is None else c["dp"] / 1e3, p_out_MPa_g=(b["p_out"] / 1e6 - hp.p_atm_MPa)))
    for zone, label in (("HP", "total passive loss, high-pressure zone (source to stage 1)"), ("INT", "total passive loss, intermediate zone"),
                        ("DEL", "total passive loss, delivery zone (downstream of stage 2)"), (None, "total passive loss, all zones")):
        vals = [hp.zone_sum(ch, zone) / 1e3 for ch in (low, nom, high)]
        out.append(dict(case_id="ILL-REF", item_id=f"T-{zone or 'ALL'}", zone=zone or "ALL", line_id="", tag="TOTAL", group="total",
                        description=label, method="sum of included rows", data_class="TOTAL", data_basis="", assumption_ids="",
                        included_in_total="FALSE", p_in_MPa_g=None, v_in_m_s=None, dp_low_kPa=vals[0], dp_nom_kPa=vals[1], dp_high_kPa=vals[2], p_out_MPa_g=None))
    lim = P("IL-09") * P("IL-04") * 1e3
    dd = [hp.zone_sum(ch, "DEL") / 1e3 for ch in (low, nom, high)]
    out.append(dict(case_id="ILL-REF", item_id="LIMIT", zone="DEL", line_id="", tag="IL-09", group="illustrative limit",
                    description="Illustrative limit on delivery-zone passive loss (IL-09 x delivery set pressure); the real limit is UI-04",
                    method="IL-09 x set pressure", data_class="ILLUSTRATIVE", data_basis="", assumption_ids="IL-09", included_in_total="FALSE",
                    p_in_MPa_g=None, v_in_m_s=None, dp_low_kPa=lim, dp_nom_kPa=lim, dp_high_kPa=lim, p_out_MPa_g=None))
    out.append(dict(case_id="ILL-REF", item_id="MARGIN", zone="DEL", line_id="", tag="IL-09", group="illustrative limit",
                    description="Margin to the illustrative limit (limit minus delivery-zone loss); positive means within the illustrative limit",
                    method="LIMIT - T-DEL", data_class="CALCULATED", data_basis="", assumption_ids="IL-09", included_in_total="FALSE",
                    p_in_MPa_g=None, v_in_m_s=None, dp_low_kPa=lim - dd[0], dp_nom_kPa=lim - dd[1], dp_high_kPa=lim - dd[2], p_out_MPa_g=None))
    return out


def sensitivity_rows(hp):
    rows = []
    for ids in P("IL-07").split(";"):
        for km in P("IL-08").split(";"):
            ch = hp.chain("nom", D=float(ids), kmult=float(km))
            dp_del = hp.zone_sum(ch, "DEL")
            first_del = next(r for r in ch if r["zone"] == "DEL")
            D = float(ids) / 1000.0
            Re = 4.0 * hp.mdot / (math.pi * D * hp.state(first_del["p_in"])["mu"])
            v = max(r["v"] for r in ch if r["zone"] == "DEL" and r["v"])
            rows.append(dict(id_mm=float(ids), k_mult=float(km), dp_HP_kPa=hp.zone_sum(ch, "HP") / 1e3, dp_INT_kPa=hp.zone_sum(ch, "INT") / 1e3,
                             dp_DEL_kPa=dp_del / 1e3, dp_ALL_kPa=hp.zone_sum(ch) / 1e3, DEL_loss_pct_of_set=100.0 * dp_del / (P("IL-04") * 1e6),
                             v_DEL_max_m_s=v, Mach_DEL_max=hp.mach(v, first_del["p_out"]), Re_DEL=Re,
                             within_IL09="TRUE" if dp_del <= P("IL-09") * P("IL-04") * 1e6 else "FALSE"))
    return rows


# ======================================================================================
# 4. CRYOGENIC LN2: heat leak, boil-off, cooldown, contraction, trapped liquid
# ======================================================================================
def log_poly(coefs, T):
    x = math.log10(T)
    return 10.0 ** sum(c * x ** n for n, c in enumerate(coefs))


class Cryo:
    def __init__(self, props, consts):
        self.props = props
        self.cv = lambda i: float(consts[i]["value"])
        self.k_ss_c = [self.cv(f"VC-{n}") for n in range(10, 19)]
        self.cp_ss_c = [self.cv(f"VC-{n}") for n in range(20, 29)]
        self.E_ss_c = [self.cv(f"VC-{n}") for n in range(30, 35)]
        self.ex_ss = ([self.cv(f"VC-{n}") for n in range(40, 45)], self.cv("VC-45"), self.cv("VC-46"))
        self.ex_al = ([self.cv(f"VC-{n}") for n in range(50, 55)], self.cv("VC-55"), self.cv("VC-56"))
        self.E_al_c = [self.cv(f"VC-{n}") for n in range(60, 65)]
        self.sigma = P("VC-03")
        self.Ru = P("VC-01")
        self.M = P("VC-02") / 1000.0
        self.Tc = P("VP-01")
        self.Do = P("IL-12") / 1000.0
        self.t = P("IL-13") / 1000.0
        self.Dj = P("IL-14") / 1000.0
        self.Di_bore = self.Do - 2 * self.t
        self.liq, self.vap = props.sat("0")
        self.hfg = (self.vap["h_kJ_kg"] - self.liq["h_kJ_kg"]) * 1e3          # J/kg
        self.kv = props.k_vapor_1atm()

    # material fits ------------------------------------------------------------------
    def k_ss(self, T):
        return log_poly(self.k_ss_c, T)

    def cp_ss(self, T):
        return log_poly(self.cp_ss_c, T)

    @staticmethod
    def poly(c, T):
        return sum(ci * T ** n for n, ci in enumerate(c))

    def strain_y(self, mat, T):
        """(L - L293)/L293 x 1e5 from the NIST fit."""
        c, tlow, f = self.ex_ss if mat == "SS304" else self.ex_al
        return f if T < tlow else self.poly(c, T)

    def dy_dT(self, mat, T):
        c, tlow, f = self.ex_ss if mat == "SS304" else self.ex_al
        if T < tlow:
            return 0.0
        return sum(n * ci * T ** (n - 1) for n, ci in enumerate(c) if n)

    def E_GPa(self, mat, T):
        return self.poly(self.E_ss_c if mat == "SS304" else self.E_al_c, T)

    def contraction(self, mat, T1, T2):
        """Fractional length change (L(T2) - L(T1)) / L(T1) between two temperatures."""
        y1, y2 = self.strain_y(mat, T1) * 1e-5, self.strain_y(mat, T2) * 1e-5
        return (y2 - y1) / (1.0 + y1)

    def restrained_stress_MPa(self, mat, T_hi, T_lo):
        """Thermal stress (MPa, tensile positive) of a fully restrained bar cooled from T_hi to T_lo: integral of E(T) alpha(T) dT."""
        f = lambda T: self.E_GPa(mat, T) * 1e3 * self.dy_dT(mat, T) * 1e-5
        return simpson(f, T_lo, T_hi)

    # heat transfer ------------------------------------------------------------------
    def rad_bare(self, Th, Tc, e1, e2):
        """Bare concentric cylinders, W per metre: sigma pi D1 (Th^4-Tc^4) / (1/e1 + (D1/D2)(1/e2 - 1))."""
        return self.sigma * math.pi * self.Do * (Th ** 4 - Tc ** 4) / (1.0 / e1 + (self.Do / self.Dj) * (1.0 / e2 - 1.0))

    def rad_mli(self, Th, Tc, e_eff):
        return self.sigma * math.pi * self.Do * e_eff * (Th ** 4 - Tc ** 4)

    def gas_fm(self, Th, Tc, p, alpha, gamma=1.4):
        """Free-molecular gas conduction, W per metre: alpha (g+1)/(g-1) sqrt(Ru/(8 pi M Tm)) p (Th-Tc) pi D1."""
        Tm = 0.5 * (Th + Tc)
        lam = (gamma + 1.0) / (gamma - 1.0) * math.sqrt(self.Ru / (8.0 * math.pi * self.M * Tm))
        return alpha * lam * p * (Th - Tc) * math.pi * self.Do

    def kint_gas(self, Th):
        """Integral of the N2 conductivity from the boiling temperature to Th (W/m)."""
        T = [a for a, _ in self.kv]
        k = [b for _, b in self.kv]
        n = 4000
        h = (Th - T[0]) / n
        return sum(0.5 * (interp(T, k, T[0] + i * h) + interp(T, k, T[0] + (i + 1) * h)) * h for i in range(n))

    def gas_cont(self, Th, Tc):
        """Continuum conduction across the annulus (lower bound: no convection), W per metre."""
        return 2.0 * math.pi * self.kint_gas(Th) / math.log(self.Dj / self.Do)

    def gas_bridge(self, Th, Tc, p, alpha):
        qfm, qc = self.gas_fm(Th, Tc, p, alpha), self.gas_cont(Th, Tc)
        return 1.0 / (1.0 / qfm + 1.0 / qc)

    def supports(self, Th, AL, n):
        return n * AL * simpson(self.k_ss, self.Tc, min(Th, 300.0))

    def rayleigh_annulus(self, Th):
        """Rayleigh number on the annulus gap at the mean gas temperature, vapour properties at 1 atm."""
        Tm = 0.5 * (Th + self.Tc)
        rows = sorted((r for r in self.props.sets["N2_GAS_ISOBAR_0MPAG"] if r["phase"] == "vapor" and r["T_K"] >= 80), key=lambda r: r["T_K"])
        T = [r["T_K"] for r in rows]
        g = lambda key: interp(T, [r[key] for r in rows], Tm)
        rho, mu, k, cp = g("rho_kg_m3"), g("mu_uPa_s") * 1e-6, g("k_W_mK"), g("cp_kJ_kgK") * 1e3
        nu, alpha = mu / rho, k / (rho * cp)
        delta = 0.5 * (self.Dj - self.Do)
        return 9.80665 * (1.0 / Tm) * (Th - self.Tc) * delta ** 3 / (nu * alpha)

    SCEN = (
        ("S1", "VJ line with MLI, design vacuum", "mli", "design"),
        ("S2", "VJ line without MLI (bare surfaces), design vacuum", "bare", "design"),
        ("S3", "VJ line with MLI, degraded vacuum (transitional-regime estimate, low confidence)", "mli", "degraded"),
        ("S4", "VJ line with MLI, vacuum lost (annulus at ambient pressure, conduction only: lower bound)", "mli", "lost"),
    )

    def params(self, lab):
        Th = 300.0 if lab != "high" else P("AS-15-hot-high")
        return dict(Th=Th, e_mli=P(f"AS-10-{lab}"), e_bare=P(f"AS-11-{lab}"), alpha=P(f"AS-12-{lab}"),
                    AL=P(f"AS-14-AL-{lab}"), n=P(f"AS-14-n-{lab}"))

    def leak(self, scen, par, override=None):
        sid, _, rad, vac = next(s for s in self.SCEN if s[0] == scen)
        q = dict(par)
        if override:
            q.update(override)
        Th = q["Th"]
        q_rad = self.rad_mli(Th, self.Tc, q["e_mli"]) if rad == "mli" else self.rad_bare(Th, self.Tc, q["e_bare"], q["e_bare"])
        p = P(f"AS-13-{vac}")
        if vac == "design":
            q_gas = self.gas_fm(Th, self.Tc, p, q["alpha"])
        elif vac == "degraded":
            q_gas = self.gas_bridge(Th, self.Tc, p, q["alpha"])
        else:
            q_gas = self.gas_cont(Th, self.Tc)
        q_sup = self.supports(Th, q["AL"], q["n"])
        return q_rad, q_gas, q_sup

    def boil(self, Q):
        """Boil-off for a heat load Q (W): mass flow, liquid volume rate, vapour volume flows."""
        m = Q / self.hfg
        rho_amb = self.props.gas300(Props.P_ATM)["rho_kg_m3"]
        return dict(g_s=m * 1e3, L_h=m / self.liq["rho_kg_m3"] * 1e3 * 3600.0, vap_L_s_77K=m / self.vap["rho_kg_m3"] * 1e3,
                    vap_L_s_300K=m / rho_amb * 1e3)


def heat_leak_rows(cy):
    rows = []
    for sid, desc, rad, vac in cy.SCEN:
        for lab in ("low", "nom", "high"):
            par = cy.params(lab)
            qr, qg, qs = cy.leak(sid, par)
            Q = qr + qg + qs
            b = cy.boil(Q)
            Lref = float(P("IL-15").split(";")[1])
            rows.append(dict(scenario=sid, description=desc, case=lab, T_hot_K=par["Th"], T_cold_K=cy.Tc, annulus_p_Pa=P(f"AS-13-{vac}"),
                             Q_rad_W_m=qr, Q_gas_W_m=qg, Q_support_W_m=qs, Q_total_W_m=Q,
                             share_rad_pct=100 * qr / Q, share_gas_pct=100 * qg / Q, share_support_pct=100 * qs / Q,
                             boil_g_s_m=b["g_s"] / 1.0, boil_L_h_m=b["L_h"], Q_ref_length_W=Q * Lref, boil_ref_length_L_h=b["L_h"] * Lref,
                             ref_length_m=Lref, Ra_gap=cy.rayleigh_annulus(par["Th"]) if vac == "lost" else None,
                             confidence={"design": "MEDIUM-LOW (placeholders)", "degraded": "LOW (transitional regime, bridged)", "lost": "LOWER BOUND (convection ignored)"}[vac],
                             data_class="CALCULATED from ASSUMED inputs",
                             assumption_ids="AS-10;AS-12;AS-13;AS-14;AS-15;IL-12;IL-14" if rad == "mli" else "AS-11;AS-12;AS-13;AS-14;AS-15;IL-12;IL-14"))
    rows.append(dict(scenario="VESSEL", description="Source vessel evaporation (normal evaporation rate)", case="-", T_hot_K=None, T_cold_K=None, annulus_p_Pa=None,
                     Q_rad_W_m=None, Q_gas_W_m=None, Q_support_W_m=None, Q_total_W_m=None, share_rad_pct=None, share_gas_pct=None, share_support_pct=None,
                     boil_g_s_m=None, boil_L_h_m=None, Q_ref_length_W=None, boil_ref_length_L_h=None, ref_length_m=None, Ra_gap=None,
                     confidence="NOT CALCULATED", data_class="UNRESOLVED", assumption_ids="UI-20;UI-23"))
    rows.append(dict(scenario="ENDS", description="Terminations, valves, flanges and bayonet joints", case="-", T_hot_K=None, T_cold_K=None, annulus_p_Pa=None,
                     Q_rad_W_m=None, Q_gas_W_m=None, Q_support_W_m=None, Q_total_W_m=None, share_rad_pct=None, share_gas_pct=None, share_support_pct=None,
                     boil_g_s_m=None, boil_L_h_m=None, Q_ref_length_W=None, boil_ref_length_L_h=None, ref_length_m=None, Ra_gap=None,
                     confidence="NOT CALCULATED", data_class="UNRESOLVED", assumption_ids="UI-21;UI-23;UI-24"))
    return rows


def uncertainty_rows(cy):
    """One-at-a-time sensitivity of the S1 and S2 totals: each parameter at its low and high value, others nominal."""
    rows = []
    nom = cy.params("nom")
    for sid, keys in (("S1", ("e_mli", "alpha", "AL", "n", "Th")), ("S2", ("e_bare", "alpha", "AL", "n", "Th"))):
        base = sum(cy.leak(sid, nom))
        for key in keys:
            vals = {}
            for lab in ("low", "high"):
                ov = {key: cy.params(lab)[key]}
                vals[lab] = sum(cy.leak(sid, nom, ov))
            rows.append(dict(scenario=sid, parameter=key, nominal_value=nom[key], low_value=cy.params("low")[key], high_value=cy.params("high")[key],
                             Q_nominal_W_m=base, Q_at_low_W_m=vals["low"], Q_at_high_W_m=vals["high"],
                             swing_W_m=abs(vals["high"] - vals["low"]), swing_pct_of_nominal=100.0 * abs(vals["high"] - vals["low"]) / base))
    return rows


def cooldown_rows(cy):
    rows = []
    Am = math.pi / 4.0 * (cy.Do ** 2 - cy.Di_bore ** 2)
    m_per_m = P("AS-16") * Am
    dh_metal = simpson(cy.cp_ss, cy.Tc, 300.0)                     # J/kg, 300 K down to the boiling temperature
    rho_amb_h = cy.props.h_gas(300.0, 0)                           # kJ/kg gas at 300 K, 1 atm
    dh_full = (rho_amb_h - cy.liq["h_kJ_kg"]) * 1e3                # J per kg LN2 if the vapour leaves at 300 K
    for L in (1.0,) + tuple(float(x) for x in P("IL-15").split(";")):
        E = m_per_m * L * dh_metal
        rows.append(dict(length_m=L, metal_mass_kg=m_per_m * L, metal_dh_kJ_kg=dh_metal / 1e3, energy_to_remove_kJ=E / 1e3,
                         LN2_kg_latent_only=E / cy.hfg, LN2_L_latent_only=E / cy.hfg / cy.liq["rho_kg_m3"] * 1e3,
                         LN2_kg_full_sensible=E / dh_full, LN2_L_full_sensible=E / dh_full / cy.liq["rho_kg_m3"] * 1e3,
                         hfg_kJ_kg=cy.hfg / 1e3, dh_full_kJ_kg=dh_full / 1e3, data_class="CALCULATED from VERIFIED (cp fit) and ASSUMED (density, geometry)",
                         scope="inner line metal only; valves, flanges, supports, receiver and jacket thermal masses excluded (UI-28)",
                         assumption_ids="AS-16;IL-12;IL-13"))
    return rows


def contraction_rows(cy):
    rows = []
    Am = math.pi / 4.0 * (cy.Do ** 2 - cy.Di_bore ** 2)
    for mat in ("SS304", "AL6061T6"):
        eps = -cy.contraction(mat, 300.0, cy.Tc)          # positive = shortening on cooling
        sig = cy.restrained_stress_MPa(mat, 293.0, cy.Tc)
        for L in (float(x) for x in P("IL-15").split(";")):
            rows.append(dict(material=mat, install_T_K=300.0, cold_T_K=cy.Tc, length_m=L, contraction_strain_pct=eps * 100.0, dL_mm=eps * L * 1e3,
                             restrained_stress_MPa=sig, restrained_force_kN=sig * Am * 1e3, section_area_mm2=Am * 1e6,
                             E_293K_GPa=cy.E_GPa(mat, 293.0), E_cold_GPa=cy.E_GPa(mat, cy.Tc),
                             fit_error_pct=5 if mat == "SS304" else 4, data_class="CALCULATED from VERIFIED (NIST fits)",
                             note="stress is the fully restrained bound from 293 K (upper end of the E fit); no allowable stress is compared because none is available (UI-25)"))
    return rows


def trapped_rows(cy):
    rows = []
    iso = {}
    for key, rho in zip(("806", "760", "700"), (float(x) for x in P("IL-18").split(";"))):
        sel = sorted(cy.props.sets[f"N2_ISOCHORE_{key}"], key=lambda r: r["T_K"])
        iso[key] = sel
        for r in sel:
            rows.append(dict(section="ISOCHORE", fill_density_kg_m3=rho, T_K=r["T_K"], p_MPa_g=round(r["p_MPa_abs"] - Props.P_ATM, 6), phase=r["phase"],
                             heat_case="", Q_W_m="", target_p_MPa_g="", dT_K="", time_min="", note="closed volume warmed at constant density: verified equation-of-state table"))
    sel = iso["806"]
    Ts, ps = [r["T_K"] for r in sel], [round(r["p_MPa_abs"] - Props.P_ATM, 6) for r in sel]
    mass = cy.liq["rho_kg_m3"] * math.pi / 4.0 * cy.Di_bore ** 2     # kg per metre of bore, full of saturated liquid
    cv = P("VP-06") * 1e3
    for sid in ("S1", "S2", "S4"):
        for lab in ("nom", "high"):
            Q = sum(cy.leak(sid, cy.params(lab)))
            for tp in (float(x) for x in P("IL-16").split(";")):
                Tt = interp(ps, Ts, tp)
                dT = Tt - cy.Tc
                t = mass * cv * dT / Q
                rows.append(dict(section="TIME_TO_PRESSURE", fill_density_kg_m3=cy.liq["rho_kg_m3"], T_K=Tt, p_MPa_g=tp, phase="single_phase",
                                 heat_case=f"{sid} {lab}", Q_W_m=Q, target_p_MPa_g=tp, dT_K=dT, time_min=t / 60.0,
                                 note=f"liquid only ({mass:.4g} kg per metre of bore), cv at 77.355 K, metal and support thermal mass ignored (shortest time); pressure threshold is a screening level, not an allowable"))
    return rows


def property_screening_rows(cy):
    rows = []
    rho_amb = cy.props.gas300(Props.P_ATM)["rho_kg_m3"]
    for name, pg in (("0", 0.0), ("0P2", 0.2), ("0P5", 0.5), ("1", 1.0)):
        liq, vap = cy.props.sat(name)
        hfg = vap["h_kJ_kg"] - liq["h_kJ_kg"]
        rows.append(dict(p_MPa_g=pg, T_sat_K=liq["T_K"], rho_liquid_kg_m3=liq["rho_kg_m3"], rho_vapour_kg_m3=vap["rho_kg_m3"],
                         h_fg_kJ_kg=hfg, liquid_to_sat_vapour_volume_ratio=liq["rho_kg_m3"] / vap["rho_kg_m3"],
                         liquid_to_ambient_gas_volume_ratio=liq["rho_kg_m3"] / rho_amb, data_class="CALCULATED from VERIFIED",
                         note="saturated liquid; ambient gas is 300 K and 0.101325 MPa"))
    return rows


def oxygen_rows(hp, cy):
    x0, thr = P("VC-04") / 100.0, P("VC-05") / 100.0
    rho_amb = hp.props.gas300(Props.P_ATM)["rho_kg_m3"]
    rows = []
    sources = [("LN2", "1 L of liquid nitrogen vaporised to ambient gas", cy.liq["rho_kg_m3"] / rho_amb * 1e-3)]
    for pg in (1, 5, 20):
        g = hp.props.gas300(Props.P_ATM + pg)
        sources.append((f"GN2 {pg} MPa(g)", f"1 L of GN2 at {pg} MPa(g), 300 K, released to ambient", g["rho_kg_m3"] / rho_amb * 1e-3))
    for tag, desc, m3_per_L in sources:
        for V in (float(x) for x in P("IL-17").split(";")):
            Vadd = -V * math.log(thr / x0)
            rows.append(dict(source=tag, description=desc, ambient_gas_m3_per_litre=m3_per_L, room_volume_m3=V,
                             max_added_gas_m3_to_reach_threshold=Vadd, litres_to_reach_threshold=Vadd / m3_per_L,
                             O2_threshold_pct=thr * 100.0, O2_start_pct=x0 * 100.0,
                             model="well mixed room, displaced mixture leaves: x = x0 exp(-Vadd/V)",
                             caveat="local concentrations near a release, in pits or at floor level (cold dense vapour) can be far lower than the room average",
                             data_class="CALCULATED from VERIFIED"))
    return rows


# ======================================================================================
# 5. MISSING INPUTS REGISTER
# ======================================================================================
MISSING_INPUTS = {
    # id: (why needed, calculations or decisions blocked, who must supply, effect if wrong, workaround used in this study)
    "UI-01": ("Defines what pressure the delivery side must hold", "Delivery set pressure, pressure-budget acceptance, regulator range", "Downstream user / test owner", "Whole pressure architecture", "IL-04 illustrative 1 MPa(g)"),
    "UI-02": ("Source pressure, temperature and depletion fix regulator inlet range and JT cooling", "Regulator envelope, relief load, source-side design pressure", "Gas supplier / facility", "Stage count, ratings, relief load", "IL-02 illustrative 20 MPa(g), sweep IL-10"),
    "UI-03": ("Flow range and duty cycle fix regulator capacity, line size and vent loads", "Line sizing, regulator capacity, flow element range", "Downstream user / test owner", "Pressure budget, noise, JT", "IL-01 reuses the heated-duct air mass flow"),
    "UI-04": ("Downstream limits turn a pressure budget into a pass or fail", "Pressure-budget acceptance, flow-control valve authority", "Downstream user / test owner", "Margin cannot be claimed", "IL-09 illustrative 5 percent"),
    "UI-05": ("Classification and code select the design rules, tests, stamping and approvals", "All ratings, wall thickness, tests, relief rules", "Responsible pressure-systems engineer / authority having jurisdiction", "Every rating and the legal basis of the design", "none: no rating is given"),
    "UI-06": ("Design pressure and temperature of each zone are the basis of all ratings", "Component ratings, wall thickness, test pressure, relief set pressure", "Responsible engineer", "Every rating", "none: no rating is given"),
    "UI-07": ("Relief set pressure and capacity depend on credible failures and component data", "Relief sizing, vent line back-pressure", "Responsible engineer with vendor data", "Overpressure protection", "choked flux per mm2 shown for scale only"),
    "UI-08": ("Regulators droop, drift with supply pressure and need a minimum differential", "Regulator selection, set-point accuracy, depletion behaviour", "Regulator vendor datasheets", "Downstream pressure accuracy and stability", "capacity screened with generic Cd (AS-06)"),
    "UI-09": ("Specifications and ratings of every component", "Component selection, cracking pressure, Cv, leak rate", "Vendor data", "Budget rows marked ALLOCATION or UNRESOLVED", "generic K and allocations (AS-03, AS-04)"),
    "UI-10": ("Materials, seals and cleaning level must suit service temperature, pressure and compatibility", "Material selection, JT-cold seal limits, cleaning", "Materials engineer", "Embrittlement, seal failure, contamination", "none"),
    "UI-11": ("Vent location and routing govern exposure, noise and back-pressure", "Vent sizing, back-pressure budget, dispersion", "Responsible engineer / facility", "Exposure of personnel and equipment", "none"),
    "UI-12": ("Room volume and ventilation govern the oxygen-deficiency risk", "Oxygen-deficiency classification, monitor placement, ventilation", "Facility / safety engineer", "Asphyxiation risk", "IL-17 illustrative well-mixed volumes"),
    "UI-13": ("Failure positions of valves on loss of power or air decide the safe state", "Actuator selection, interlock design, trip logic", "Controls engineer / safety review", "Behaviour on power loss", "none: positions shown TBD"),
    "UI-20": ("Source vessel data fix transfer pressure, evaporation rate and relief arrangement", "Source normal evaporation rate, driving pressure, vessel relief and vent", "Vessel vendor / facility", "Boil-off, transfer pressure", "not calculated"),
    "UI-21": ("Length, routing and bore set total heat leak, contraction and pressure drop", "Totals of heat leak, boil-off, contraction, cooldown, trapped volume", "Responsible engineer", "All totals", "IL-15 illustrative straight runs and per-metre results"),
    "UI-22": ("Allowable pressures and relief arrangement protect against trapped-liquid and boil-off overpressure", "Relief sizing for trapped liquid, boil-off and vacuum-jacket failure; vent sizes", "Responsible engineer with vendor data", "Overpressure protection", "none: only the pressure-rise physics is shown"),
    "UI-23": ("Real insulation performance replaces placeholder emissivities and vacuum levels", "Heat leak and boil-off of the real line", "Insulation vendor / test", "Heat leak and boil-off by an unknown factor", "AS-10, AS-11, AS-13 placeholders with low and high cases"),
    "UI-24": ("Supports, spacers and bellows set conduction paths and movement allowance", "Support heat leak, restraint loads, movement allowance", "Responsible engineer / vendor", "Heat leak, stress", "AS-14 placeholders"),
    "UI-25": ("Material grades, toughness and allowable stresses decide pass or fail", "Stress compared with allowable, material selection", "Materials engineer / code", "Cannot state any stress margin", "stress magnitude only, no allowable"),
    "UI-26": ("The receiver defines fill rate, back-pressure and venting", "Transfer rate, receiver relief, vent routing", "Receiver owner", "Transfer duty", "none"),
    "UI-27": ("Transfer rate and duration set the flow regime and two-phase length", "Hydraulic pressure drop, flashing, cooldown vent flow", "Responsible engineer", "Two-phase behaviour, vent loads", "none"),
    "UI-28": ("Valves, flanges and receiver thermal mass dominate real cooldown", "Cooldown liquid use and time", "Responsible engineer / vendor", "Cooldown consumption by a large factor", "line-metal-only lower bound"),
    "UI-29": ("Cold vent behaviour (dense cold vapour) decides exposure and the vent design", "Phase separator, vent sizing, dispersion", "Responsible engineer / safety engineer", "Exposure at ground level", "none"),
    "UI-30": ("Indoor or outdoor, drainage and spill containment change hazards", "Spill and exposure assessment", "Facility", "Exposure and embrittlement of nearby structure", "none"),
    "UI-31": ("Instruments must work at 77 K and meet accuracy needs", "Instrument selection", "Controls engineer / vendor", "False readings", "none"),
    "UI-32": ("Measured emissivity and MLI performance replace placeholders", "Heat leak", "Vendor / test", "Heat leak", "AS-10, AS-11"),
    "UI-33": ("Two-phase pressure drop and hydraulic transients are needed for chilldown and valve closure", "Pressure-surge and cooldown assessment", "Responsible engineer", "Surge pressures, damage", "identified qualitatively only"),
}


def missing_rows():
    names = {u: (s, n) for u, s, n in UNRESOLVED_INPUTS_SHORT}
    rows = []
    for uid, (why, blocked, who, eff, work) in MISSING_INPUTS.items():
        s, n = names[uid]
        rows.append(dict(id=uid, system=s, missing_input=n, why_needed=why, blocked_calculations_or_decisions=blocked, to_be_supplied_by=who,
                         effect_if_wrong=eff, workaround_in_this_study=work, status="OPEN"))
    return rows


def relief_sizing(*_):
    """Relief-device sizing is intentionally not implemented: it needs UI-07 and UI-22. Raises MissingInputError."""
    for uid in ("UI-06", "UI-07", "UI-22"):
        P(uid)
    raise AssertionError("unreachable: the inputs above are unresolved")


# ======================================================================================
# 6. OUTPUT
# ======================================================================================
def fmt(x, digits=6):
    if x is None or x == "":
        return ""
    if isinstance(x, bool):
        return "TRUE" if x else "FALSE"
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float):
        s = f"{x:.{digits}g}"
        return "0" if s in ("-0", "0") else s
    return str(x)


def write_csv(path, fields, rows, digits=6):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(fields)
        for r in rows:
            w.writerow([fmt(r.get(f), digits) for f in fields])


def boundary_rows(hp, cy):
    nom = hp.chain("nom")
    T_a = hp.props.isenthalpic(300.0, int(P("IL-02")), int(P("IL-03")))
    T_b = hp.props.isenthalpic(T_a, int(P("IL-03")), int(P("IL-04")))
    dp_del = hp.zone_sum(nom, "DEL") / 1e6
    R = []

    def row(sid, sysm, loc, tag, p, T, cls, src, note):
        R.append(dict(station=sid, system=sysm, location=loc, tag=tag, p_MPa_g=p, T_K=T, data_class=cls, source_ref=src, note=note))
    row("SB-301", "HP", "Nitrogen source interface", "SRC-301", P("IL-02"), P("IL-05"), "ILLUSTRATIVE", "IL-02;IL-05", "source range, depletion and temperature variation are UI-02")
    row("SB-302", "HP", "Stage-1 outlet", "PCV-301", P("IL-03"), T_a, "ILLUSTRATIVE;CALCULATED", "IL-03", "temperature is the isenthalpic outlet of the 300 K source gas (no heat gain)")
    row("SB-303", "HP", "Stage-2 outlet", "PCV-302", P("IL-04"), T_b, "ILLUSTRATIVE;CALCULATED", "IL-04", "temperature is the isenthalpic outlet of the stage-1 outlet gas (no heat gain)")
    row("SB-304", "HP", "Delivery interface", "DI-301", P("IL-04") - dp_del, None, "CALCULATED", "pressure_budget.csv T-DEL", "nominal passive loss subtracted; required interface pressure is UI-01/UI-04")
    row("SB-305", "HP", "Vent stack exit", "VS-301", 0.0, None, "ASSUMED", "AS-01", "ambient at the exit; back-pressure during relief is UI-07/UI-11")
    row("SB-306", "HP", "Design pressure, high-pressure zone", "L-301..L-303", None, None, "UNRESOLVED", "UI-06", "no design pressure is assumed")
    row("SB-307", "HP", "Design pressure, intermediate zone", "L-304", None, None, "UNRESOLVED", "UI-06", "")
    row("SB-308", "HP", "Design pressure, delivery zone", "L-305", None, None, "UNRESOLVED", "UI-06", "")
    row("SB-309", "HP", "Set pressure of PSV-301 and PSV-302", "PSV-301;PSV-302", None, None, "UNRESOLVED", "UI-07", "no relief setting is assumed")
    row("SC-401", "CRYO", "Source vessel liquid", "VES-401", 0.0, cy.Tc, "ILLUSTRATIVE;VERIFIED", "VP-01", "0 MPa(g) is used to read properties; the real vessel pressure is UI-20")
    row("SC-402", "CRYO", "Transfer line liquid inlet", "L-401", 0.0, cy.Tc, "ILLUSTRATIVE;VERIFIED", "VP-01", "subcooling or pressure above the boiling pressure is not assumed")
    row("SC-403", "CRYO", "Vacuum annulus", "L-401", None, None, "ASSUMED", "AS-13", "annulus pressure 1e-3 Pa (design), 1 Pa (degraded), 101325 Pa (lost); outer jacket 300 K")
    row("SC-404", "CRYO", "Receiver", "RCV-401", None, None, "UNRESOLVED", "UI-26", "")
    row("SC-405", "CRYO", "Cold vent exit", "VS-401", 0.0, None, "ASSUMED", "AS-01", "ambient at the exit; relief back-pressure and vent temperature are UI-22/UI-29")
    row("SC-406", "CRYO", "Allowable pressure and relief setting", "TRV-401;TRV-402", None, None, "UNRESOLVED", "UI-22", "no allowable pressure or relief setting is assumed")
    return R


def design_rows(hp, cy, heat, contr, trapped, sens, budget, cool, oxy):
    """Append CALCULATED headline results to the register (after the inputs)."""
    rows = list(REG)
    for key, (val, fmt_s, unit, desc, sysm) in HEADLINES(hp, cy, heat, contr, trapped, sens, budget, cool, oxy).items():
        rows.append({"param_id": f"CA-{key}", "system": sysm, "group": "calculated result", "name": desc, "value": val, "unit": unit, "class": "CALCULATED",
                     "source_ref": "calculations.py", "bound_min": None, "bound_max": None, "assumption_id": "", "note": "headline value quoted in the documents"})
    return rows


def HEADLINES(hp, cy, heat, contr, trapped, sens, budget, cool, oxy):
    """key -> (value, format spec, unit, description, system). The documents quote these between <!--h:key--> markers."""
    H = {}
    nomchain = hp.chain("nom")
    s1 = next(r for r in hp.envelope() if r["stage"] == "PCV-301" and r["p_in_MPa_g"] == int(P("IL-02")))
    s2 = next(r for r in hp.envelope() if r["stage"] == "PCV-302" and r["case"].startswith("stage 2, normal"))
    fail = next(r for r in hp.envelope() if r["stage"] == "PCV-302" and r["p_in_MPa_g"] == int(P("IL-02")))
    H["mdot_g_s"] = (P("IL-01") * 1e3, ".3f", "g/s", "Illustrative nitrogen mass flow", "HP")
    H["Qstd_L_s"] = (P("IL-01") / P("VP-07") * 1e3, ".2f", "L/s", "Illustrative flow as volume at 300 K and 0.101325 MPa", "HP")
    H["Z_source"] = (s1["Z_in"], ".3f", "-", "Compressibility factor at the illustrative source condition", "HP")
    H["dT_stage1"] = (s1["dT_K"], ".1f", "K", "Isenthalpic temperature change across stage 1 (illustrative case)", "HP")
    H["T_out_stage1"] = (s1["T_out_K"], ".1f", "K", "Gas temperature after stage 1, no heat gain (illustrative case)", "HP")
    H["p_DI_MPa_g"] = (P("IL-04") - hp.zone_sum(nomchain, "DEL") / 1e6, ".3f", "MPa(g)", "Nominal pressure at the delivery interface after passive losses", "HP")
    H["T_boil_O2_K"] = (P("VC-06"), ".3f", "K", "Boiling temperature of oxygen at 0.101325 MPa (context only)", "CRYO")
    H["T_sat_K"] = (cy.Tc, ".3f", "K", "Boiling temperature of N2 at 0.101325 MPa", "CRYO")
    H["T_out_stage2"] = (s2["T_out_K"], ".1f", "K", "Gas temperature after stage 2, no heat gain", "HP")
    H["ratio_stage1"] = (s1["ratio"], ".3f", "-", "Outlet/inlet absolute pressure ratio, stage 1", "HP")
    H["flux_source"] = (s1["flux_g_s_mm2"], ".1f", "g/(s mm2)", "Choked mass flux per mm2 of flow area at the illustrative source pressure (Cd=AS-06)", "HP")
    H["flux_multiple_source"] = (s1["multiple"], ".1f", "-", "Illustrative flow multiples passed by 1 mm2 at the source pressure", "HP")
    H["flux_stage2_fail"] = (fail["flux_g_s_mm2"], ".1f", "g/(s mm2)", "Choked flux per mm2 into stage 2 with stage 1 failed open", "HP")
    H["Areq_stage1"] = (s1["A_req_mm2"], ".3f", "mm2", "Effective flow area needed for the illustrative flow at stage 1 (Cd=AS-06)", "HP")
    tdel = next(r for r in budget if r["item_id"] == "T-DEL")
    tall = next(r for r in budget if r["item_id"] == "T-ALL")
    H["dp_del_nom_kPa"] = (tdel["dp_nom_kPa"], ".2f", "kPa", "Nominal passive loss downstream of stage 2", "HP")
    H["dp_del_pct"] = (100 * tdel["dp_nom_kPa"] / (P("IL-04") * 1e3), ".2f", "percent", "Nominal delivery-zone loss as percent of the delivery set pressure", "HP")
    H["dp_all_nom_kPa"] = (tall["dp_nom_kPa"], ".1f", "kPa", "Nominal passive loss, all zones", "HP")
    H["dp_del_high_kPa"] = (tdel["dp_high_kPa"], ".2f", "kPa", "High-case passive loss downstream of stage 2", "HP")
    vend = sum(r["dp_nom_kPa"] for r in budget if r["zone"] == "DEL" and r["data_basis"] == "VENDOR_DATA_REQUIRED" and r["included_in_total"] == "TRUE")
    H["vendor_share_del_pct"] = (100 * vend / tdel["dp_nom_kPa"], ".0f", "percent", "Share of the nominal delivery-zone loss that rests on generic K or allocations needing vendor data", "HP")
    H["dp_hp_nom_kPa"] = (next(r for r in budget if r["item_id"] == "T-HP")["dp_nom_kPa"], ".1f", "kPa", "Nominal passive loss, high-pressure zone (mostly the filter allocation)", "HP")
    s_ref = next(r for r in sens if r["id_mm"] == 6.0 and r["k_mult"] == 4.0)
    H["sens_worst_pct"] = (s_ref["DEL_loss_pct_of_set"], ".2f", "percent", "Delivery loss, smallest swept bore with 4x component losses, percent of set pressure", "HP")
    H["sens_worst_v"] = (s_ref["v_DEL_max_m_s"], ".1f", "m/s", "Peak delivery velocity at the smallest swept bore", "HP")
    heatd = {(r["scenario"], r["case"]): r for r in heat if r["case"] in ("low", "nom", "high")}
    for sid in ("S1", "S2", "S3", "S4"):
        H[f"Q_{sid}_nom"] = (heatd[(sid, "nom")]["Q_total_W_m"], ".3g", "W/m", f"Heat leak per metre, scenario {sid}, nominal", "CRYO")
    H["Q_S1_low"] = (heatd[("S1", "low")]["Q_total_W_m"], ".3g", "W/m", "Heat leak per metre, S1, low case", "CRYO")
    H["Q_S1_high"] = (heatd[("S1", "high")]["Q_total_W_m"], ".3g", "W/m", "Heat leak per metre, S1, high case", "CRYO")
    H["boil_S1_L_h_10m"] = (heatd[("S1", "nom")]["boil_ref_length_L_h"], ".3g", "L/h", "Boil-off of a 10 m held-cold line, S1 nominal", "CRYO")
    H["boil_S4_L_h_10m"] = (heatd[("S4", "nom")]["boil_ref_length_L_h"], ".3g", "L/h", "Boil-off of a 10 m held-cold line, S4 nominal (lower bound)", "CRYO")
    H["Ra_S4"] = (heatd[("S4", "nom")]["Ra_gap"], ".2e", "-", "Rayleigh number of the annulus gap with vacuum lost", "CRYO")
    H["ratio_S4_S1"] = (heatd[("S4", "nom")]["Q_total_W_m"] / heatd[("S1", "nom")]["Q_total_W_m"], ".0f", "-", "Heat-leak ratio, vacuum lost to design vacuum", "CRYO")
    H["hfg"] = (cy.hfg / 1e3, ".2f", "kJ/kg", "Latent heat of vaporization of N2 at 0.101325 MPa", "CRYO")
    ss = next(r for r in contr if r["material"] == "SS304" and r["length_m"] == 10.0)
    al = next(r for r in contr if r["material"] == "AL6061T6" and r["length_m"] == 10.0)
    H["ss_strain_pct"] = (ss["contraction_strain_pct"], ".3f", "percent", "304 stainless contraction, 300 K to 77.355 K", "CRYO")
    H["ss_dL_10m_mm"] = (ss["dL_mm"], ".1f", "mm", "304 stainless contraction of a 10 m run", "CRYO")
    H["al_dL_10m_mm"] = (al["dL_mm"], ".1f", "mm", "6061-T6 contraction of a 10 m run", "CRYO")
    H["ss_stress_MPa"] = (ss["restrained_stress_MPa"], ".0f", "MPa", "304 stainless fully restrained thermal stress bound, 293 K to 77.355 K", "CRYO")
    H["ss_force_kN"] = (ss["restrained_force_kN"], ".0f", "kN", "Force if the illustrative inner line were fully restrained", "CRYO")
    tr = next(r for r in trapped if r["section"] == "TIME_TO_PRESSURE" and r["heat_case"] == "S1 nom" and r["target_p_MPa_g"] == 1.0)
    H["trap_t_S1_1MPa_min"] = (tr["time_min"], ".0f", "min", "Time for trapped liquid to reach 1 MPa(g), S1 nominal heat leak", "CRYO")
    tr2 = next(r for r in trapped if r["section"] == "TIME_TO_PRESSURE" and r["heat_case"] == "S2 nom" and r["target_p_MPa_g"] == 1.0)
    H["trap_t_S2_1MPa_min"] = (tr2["time_min"], ".0f", "min", "Time for trapped liquid to reach 1 MPa(g), S2 nominal heat leak", "CRYO")
    iso = sorted((r for r in trapped if r["section"] == "ISOCHORE" and r["fill_density_kg_m3"] == 806.0844), key=lambda r: r["T_K"])
    H["dpdT_trap"] = ((iso[2]["p_MPa_g"] - iso[1]["p_MPa_g"]) / (iso[2]["T_K"] - iso[1]["T_K"]), ".2f", "MPa/K", "Pressure rise per kelvin of a liquid-full closed volume (isochore slope near 80 K)", "CRYO")
    c10 = next(r for r in cool if r["length_m"] == 10.0)
    H["cool_LN2_kg_m"] = (next(r for r in cool if r["length_m"] == 1.0)["LN2_kg_latent_only"], ".2f", "kg/m", "LN2 to cool 1 m of inner line, latent heat only (upper bound of this estimate)", "CRYO")
    H["cool_LN2_L_10m_lat"] = (c10["LN2_L_latent_only"], ".1f", "L", "LN2 to cool 10 m of inner line, latent heat only", "CRYO")
    H["cool_LN2_L_10m_full"] = (c10["LN2_L_full_sensible"], ".1f", "L", "LN2 to cool 10 m of inner line, vapour leaves at 300 K", "CRYO")
    o_ln2 = next(r for r in oxy if r["source"] == "LN2" and r["room_volume_m3"] == 10.0)
    H["odh_ln2_L_10m3"] = (o_ln2["litres_to_reach_threshold"], ".2f", "L", "LN2 vaporised in a well-mixed 10 m3 room that lowers oxygen to 19.5 percent", "BOTH")
    H["odh_ratio_ln2"] = (o_ln2["ambient_gas_m3_per_litre"] * 1e3, ".0f", "-", "Gas volume (litres) at 300 K per litre of LN2", "CRYO")
    o_g = next(r for r in oxy if r["source"] == "GN2 20 MPa(g)" and r["room_volume_m3"] == 10.0)
    H["odh_gn2_L_10m3"] = (o_g["litres_to_reach_threshold"], ".1f", "L", "Pressurised volume at 20 MPa(g) whose release lowers a well-mixed 10 m3 room to 19.5 percent", "HP")
    env = hp.envelope()
    H["dT_stage2"] = (s2["dT_K"], ".1f", "K", "Isenthalpic temperature change across stage 2, normal case", "HP")
    single = next(r for r in env if r["stage"] == "PCV-301/302 alternative")
    H["dT_single"] = (single["dT_K"], ".1f", "K", "Isenthalpic temperature change, single stage from source to delivery set pressure", "HP")
    d6 = next(r for r in env if r["stage"] == "PCV-301" and r["p_in_MPa_g"] == 6)
    H["Areq_stage1_6MPa"] = (d6["A_req_mm2"], ".2f", "mm2", "Effective flow area needed at stage 1 with the source depleted to 6 MPa(g)", "HP")
    H["Areq_growth"] = (d6["A_req_mm2"] / s1["A_req_mm2"], ".1f", "-", "Growth of the required stage-1 flow area, source depleted to 6 MPa(g) versus 20 MPa(g)", "HP")
    unc_d = {(r["scenario"], r["parameter"]): r for r in uncertainty_rows(cy)}
    H["unc_mli_pct"] = (unc_d[("S1", "e_mli")]["swing_pct_of_nominal"], ".0f", "percent", "Swing of the S1 heat leak across the MLI emissivity range, percent of nominal", "CRYO")
    H["unc_AL_pct"] = (unc_d[("S1", "AL")]["swing_pct_of_nominal"], ".0f", "percent", "Swing of the S1 heat leak across the support A/L range, percent of nominal", "CRYO")
    H["boil_S1_g_s_m"] = (heatd[("S1", "nom")]["boil_g_s_m"], ".3g", "g/s", "Boil-off per metre of line, S1 nominal", "CRYO")
    trd = {(r["heat_case"], r["target_p_MPa_g"]): r for r in trapped if r["section"] == "TIME_TO_PRESSURE"}
    H["trap_t_S1_5MPa_min"] = (trd[("S1 nom", 5.0)]["time_min"], ".0f", "min", "Time for trapped liquid to reach 5 MPa(g), S1 nominal heat leak", "CRYO")
    H["trap_t_S4_1MPa_s"] = (trd[("S4 nom", 1.0)]["time_min"] * 60.0, ".0f", "s", "Time for trapped liquid to reach 1 MPa(g), S4 nominal heat leak", "CRYO")
    H["ratio_sat_1atm"] = (cy.liq["rho_kg_m3"] / cy.vap["rho_kg_m3"], ".0f", "-", "Saturated liquid to saturated vapour density ratio at 0.101325 MPa", "CRYO")
    for key in ("760", "700"):
        first = min((r for r in trapped if r["section"] == "ISOCHORE" and r["fill_density_kg_m3"] == float(key) and r["phase"] == "single_phase"), key=lambda r: r["T_K"])
        H[f"Tfull_{key}_K"] = (first["T_K"], ".1f", "K", f"First tabulated single-phase temperature of the {key} kg/m3 closed volume", "CRYO")
    return H


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--outdir", default=str(EXT_DIR), help="where to write the CSV outputs")
    ap.add_argument("--headlines", action="store_true", help="print the headline values and exit")
    ap.add_argument("--indir", default=str(EXT_DIR), help="folder holding verified_constants.csv and verified_properties.csv")
    args = ap.parse_args()
    out = Path(args.outdir).resolve()
    if REPO_ROOT in out.parents and not (out == EXT_DIR or EXT_DIR in out.parents):
        sys.exit("refusing to write inside the repository outside 09_High_Pressure_Cryogenic_Systems")
    out.mkdir(parents=True, exist_ok=True)

    consts = load_constants(args.indir)
    props = Props(load_props(args.indir))
    build_register(consts, props)
    hp, cy = HP(props), Cryo(props, consts)

    budget = pressure_budget_rows(hp)
    sens = sensitivity_rows(hp)
    env = hp.envelope()
    heat = heat_leak_rows(cy)
    unc = uncertainty_rows(cy)
    cool = cooldown_rows(cy)
    contr = contraction_rows(cy)
    trapped = trapped_rows(cy)
    prop = property_screening_rows(cy)
    oxy = oxygen_rows(hp, cy)
    bcs = boundary_rows(hp, cy)
    H = HEADLINES(hp, cy, heat, contr, trapped, sens, budget, cool, oxy)
    if args.headlines:
        for k, (v, f, u, d, s) in H.items():
            print(f"{k} = {format(v, f)} {u}  | {d}")
        return 0

    write_csv(out / "design_parameters.csv", ["param_id", "system", "group", "name", "value", "unit", "class", "source_ref", "bound_min", "bound_max", "assumption_id", "note"],
              design_rows(hp, cy, heat, contr, trapped, sens, budget, cool, oxy), digits=10)
    write_csv(out / "boundary_conditions.csv", ["station", "system", "location", "tag", "p_MPa_g", "T_K", "data_class", "source_ref", "note"], bcs)
    write_csv(out / "pressure_budget.csv",
              ["case_id", "item_id", "zone", "line_id", "tag", "group", "description", "method", "data_class", "data_basis", "assumption_ids", "included_in_total",
               "p_in_MPa_g", "v_in_m_s", "dp_low_kPa", "dp_nom_kPa", "dp_high_kPa", "p_out_MPa_g"], budget)
    write_csv(out / "pressure_sensitivity.csv", ["id_mm", "k_mult", "dp_HP_kPa", "dp_INT_kPa", "dp_DEL_kPa", "dp_ALL_kPa", "DEL_loss_pct_of_set", "v_DEL_max_m_s", "Mach_DEL_max", "Re_DEL", "within_IL09"], sens)
    write_csv(out / "regulator_envelope.csv",
              ["case", "stage", "p_in_MPa_g", "p_out_MPa_g", "T_in_K", "ratio", "ratio_crit", "choked", "Z_in", "rho_in", "T_out_K", "dT_K", "below_273K", "G_kg_m2s", "flux_g_s_mm2", "A_req_mm2", "multiple"], env)
    write_csv(out / "cryogenic_heat_leak.csv",
              ["scenario", "description", "case", "T_hot_K", "T_cold_K", "annulus_p_Pa", "Q_rad_W_m", "Q_gas_W_m", "Q_support_W_m", "Q_total_W_m", "share_rad_pct", "share_gas_pct", "share_support_pct",
               "boil_g_s_m", "boil_L_h_m", "ref_length_m", "Q_ref_length_W", "boil_ref_length_L_h", "Ra_gap", "confidence", "data_class", "assumption_ids"], heat)
    write_csv(out / "cryogenic_uncertainty.csv",
              ["scenario", "parameter", "nominal_value", "low_value", "high_value", "Q_nominal_W_m", "Q_at_low_W_m", "Q_at_high_W_m", "swing_W_m", "swing_pct_of_nominal"], unc)
    write_csv(out / "cryogenic_cooldown.csv",
              ["length_m", "metal_mass_kg", "metal_dh_kJ_kg", "energy_to_remove_kJ", "hfg_kJ_kg", "dh_full_kJ_kg", "LN2_kg_latent_only", "LN2_L_latent_only", "LN2_kg_full_sensible", "LN2_L_full_sensible", "data_class", "scope", "assumption_ids"], cool)
    write_csv(out / "thermal_contraction.csv",
              ["material", "install_T_K", "cold_T_K", "length_m", "contraction_strain_pct", "dL_mm", "restrained_stress_MPa", "restrained_force_kN", "section_area_mm2", "E_293K_GPa", "E_cold_GPa", "fit_error_pct", "data_class", "note"], contr)
    write_csv(out / "trapped_liquid.csv", ["section", "fill_density_kg_m3", "T_K", "p_MPa_g", "phase", "heat_case", "Q_W_m", "target_p_MPa_g", "dT_K", "time_min", "note"], trapped)
    write_csv(out / "cryogenic_property_screening.csv",
              ["p_MPa_g", "T_sat_K", "rho_liquid_kg_m3", "rho_vapour_kg_m3", "h_fg_kJ_kg", "liquid_to_sat_vapour_volume_ratio", "liquid_to_ambient_gas_volume_ratio", "data_class", "note"], prop)
    write_csv(out / "oxygen_deficiency_screening.csv",
              ["source", "description", "ambient_gas_m3_per_litre", "room_volume_m3", "max_added_gas_m3_to_reach_threshold", "litres_to_reach_threshold", "O2_threshold_pct", "O2_start_pct", "model", "caveat", "data_class"], oxy)
    write_csv(out / "missing_inputs_register.csv",
              ["id", "system", "missing_input", "why_needed", "blocked_calculations_or_decisions", "to_be_supplied_by", "effect_if_wrong", "workaround_in_this_study", "status"], missing_rows())
    print(f"wrote 13 CSV outputs to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
