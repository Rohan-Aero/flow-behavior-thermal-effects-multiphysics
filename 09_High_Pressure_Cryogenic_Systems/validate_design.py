#!/usr/bin/env python3
"""Validation of the conceptual GN2 and LN2 study (CONCEPTUAL - NOT APPROVED FOR CONSTRUCTION).

Standard library only. Read-only on the repository except for VALIDATION_REPORT.md, which it rewrites
(to --outdir, default this folder). The report has no timestamps, so it is reproducible.

    python validate_design.py                 # all checks and the mutation tests; rewrite VALIDATION_REPORT.md
    python validate_design.py --online        # also re-check the verified data against the live NIST, NASA and CFR pages and, if CoolProp is installed, regenerate the nitrogen table
    python validate_design.py --no-mutation   # skip the mutation tests (about a minute)
    python validate_design.py --outdir DIR    # write the report somewhere else

Exit code 1 if any check or mutation test fails. A failed check is investigated, never relaxed to pass.
The independent re-calculations here deliberately use different formulations from calculations.py
(a bisection solution of Colebrook-White and the Haaland formula for friction, direct summation of the
fit polynomials, trapezoid sums for Simpson integrals, constants derived from exact SI definitions) so
that a shared mistake is less likely. Every tolerance has a stated reason; none was loosened to pass.

Mutation tests copy this folder (and the few repository files it reads) to a temporary directory,
corrupt a source value or an important output on purpose, run the same checks and require the
expected checks to FAIL.
"""
import argparse
import csv
import hashlib
import html
import importlib.util
import io
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.dont_write_bytecode = True   # importing the code under test must not leave __pycache__ in the folder

HERE = Path(__file__).resolve().parent
BANNER = "CONCEPTUAL — NOT APPROVED FOR CONSTRUCTION."
OUTPUTS = ["design_parameters.csv", "boundary_conditions.csv", "pressure_budget.csv", "pressure_sensitivity.csv", "regulator_envelope.csv",
           "cryogenic_heat_leak.csv", "cryogenic_uncertainty.csv", "cryogenic_cooldown.csv", "thermal_contraction.csv", "trapped_liquid.csv",
           "cryogenic_property_screening.csv", "oxygen_deficiency_screening.csv", "missing_inputs_register.csv"]
DOCS = ["README.md", "DESIGN_BASIS.md", "HIGH_PRESSURE_SYSTEM.md", "CRYOGENIC_SYSTEM.md", "CALCULATION_METHOD.md",
        "HAZARD_REVIEW_HIGH_PRESSURE.md", "HAZARD_REVIEW_CRYOGENIC.md", "LIMITATIONS_AND_NEXT_STEPS.md"]
DIAGRAMS = {"PFD_HIGH_PRESSURE": ("HP", "pfd"), "PID_HIGH_PRESSURE": ("HP", "pid"), "PFD_CRYOGENIC": ("CRYO", "pfd"), "PID_CRYOGENIC": ("CRYO", "pid")}
TAG_RE = re.compile(r"\b[A-Z]{1,5}-\d{3}\b")
NON_EQUIPMENT_PREFIX = {"L", "SB", "SC"}          # lines and stations share the tag pattern
GROUPS = {"A": "A. Source and verified data", "B": "B. Units and formulas", "C": "C. Mass flow and pressure budget", "D": "D. Parameter bounds and output sanity",
          "E": "E. Tags, diagrams and schedules", "F": "F. Requirement traceability", "G": "G. Assumptions", "H": "H. Missing inputs and scope guards",
          "I": "I. Deterministic regeneration", "J": "J. Hygiene and claims", "K": "K. Repository integrity", "L": "L. Numbers quoted in documents"}


# ======================================================================================
# helpers
# ======================================================================================
def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def text(path):
    return Path(path).read_text(encoding="utf-8")


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def close(a, b, rel=1e-6, ab=1e-12):
    return abs(a - b) <= max(ab, rel * abs(b))


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Acc:
    """Collects the sub-conditions of one check; records one result."""

    def __init__(self, ctx, cid, desc):
        self.ctx, self.cid, self.desc, self.n, self.fails = ctx, cid, desc, 0, []

    def ok(self, cond, msg):
        self.n += 1
        if not cond:
            self.fails.append(msg)

    def done(self, expected="", note=""):
        ok = not self.fails
        actual = f"{self.n} conditions, all hold" if ok else f"{len(self.fails)} of {self.n} fail: " + " | ".join(self.fails[:4])
        self.ctx.rec(self.cid, self.desc, ok, expected or "all conditions hold", actual, note)


class Ctx:
    def __init__(self, ext, repo, online=False, rerun_twice=True):
        self.ext, self.repo, self.online, self.rerun_twice = Path(ext), Path(repo), online, rerun_twice
        self.results = []
        self._cache = {}

    def rec(self, cid, desc, ok, expected="", actual="", note="", skip=False):
        status = "SKIP" if skip else ("PASS" if ok else "FAIL")
        self.results.append((cid, desc, status, str(expected), str(actual), note))

    def acc(self, cid, desc):
        return Acc(self, cid, desc)

    def csv(self, name):
        key = ("csv", name)
        if key not in self._cache:
            self._cache[key] = read_csv(self.ext / name)
        return self._cache[key]

    def calc(self):
        if "calc" not in self._cache:
            mod = load_module(self.ext / "calculations.py", f"calc_{id(self)}")
            consts = mod.load_constants(self.ext)
            props = mod.Props(mod.load_props(self.ext))
            mod.build_register(consts, props)
            hp, cy = mod.HP(props), mod.Cryo(props, consts)
            self._cache["calc"] = (mod, consts, props, hp, cy)
        return self._cache["calc"]

    def reg(self):
        return {r["param_id"]: r for r in self.csv("design_parameters.csv")}

    def master(self):
        lines = text(self.repo / "05_Data" / "MASTER_PROJECT_DATA.csv").split("\n", 1)[1]
        return {r["ID"]: r for r in csv.DictReader(io.StringIO(lines))}

    def schedules(self):
        eq, ins = self.csv("equipment_schedule.csv"), self.csv("instrument_index.csv")
        return eq, ins, {r["tag"] for r in eq}, {r["tag"] for r in ins}

    def lines(self):
        return {"HP": self.csv("line_list_high_pressure.csv"), "CRYO": self.csv("line_list_cryogenic.csv")}

    def all_ids(self):
        return {r[0] for r in self.results}


def strip_comments(t):
    return "\n".join(ln for ln in t.splitlines() if not ln.strip().startswith("%%"))


def tags_in(t):
    return {m for m in TAG_RE.findall(t) if m.split("-")[0] not in NON_EQUIPMENT_PREFIX}


def lines_in(t):
    return set(re.findall(r"\bL-\d{3}\b", t))


def stations_in(t):
    return set(re.findall(r"\b(?:SB|SC)-\d{3}\b", t))


# ======================================================================================
# A. source and verified data
# ======================================================================================
def check_A(c):
    reg, master = c.reg(), c.master()
    a = c.acc("V-A01", "EXISTING parameters equal the master register and the baseline sheet")
    for pid, r in reg.items():
        if r["class"] != "EXISTING":
            continue
        val, src = float(r["value"]), r["source_ref"]
        if re.fullmatch(r"M\d{3}", src):
            row = master.get(src)
            if row is None:
                a.ok(False, f"{pid}: {src} not in the register")
                continue
            nums = [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*\.?\d*", row["Value"] + " " + row["Units"])]
            scale = 1000.0 if row["Units"].strip() == "mm" and r["unit"] == "m" else 1.0
            a.ok(any(close(n, val * scale, 1e-9) for n in nums), f"{pid}={val} not in {src} ({row['Value']} {row['Units']})")
        else:
            a.ok(f"{val:g}" in text(c.repo / src), f"{pid}: {val:g} not found in {src}")
    a.done("each EXISTING value is in its source", "M002, M003, M005, M023 and the air gas constant of BASELINE_PARAMETERS.md")

    mod, consts, props, hp, cy = c.calc()
    a = c.acc("V-A02", "Illustrative mass flow equals the existing rig design flow (independent recomputation and 08 flow_basis.csv)")
    p, R, T, V, D = (float(reg[k]["value"]) for k in ("EX-02", "EX-05", "EX-01", "EX-03", "EX-04"))
    ind = p / (R * T) * V * math.pi * D * D / 4.0
    il01 = float(reg["IL-01"]["value"])
    a.ok(close(il01, ind, 1e-9), f"IL-01 {il01} vs independent {ind}")
    fb = [r for r in read_csv(c.repo / "08_Fluid_Test_Rig_Design" / "flow_basis.csv") if r["quantity"] == "mass flow (circular tube)"]
    a.ok(len(fb) == 1 and close(il01, float(fb[0]["calculated"]), 2e-6), f"08 flow_basis {fb[0]['calculated'] if fb else None}")
    a.done("equal within 2e-6 (the 08 file holds 6 digits)", "IL-01 is reused only for its magnitude")

    a = c.acc("V-A03", "Verified constants satisfy exact SI relations and register copies match the file")
    VC = lambda i: float(consts[i]["value"])
    NA, kB, h, cl = 6.02214076e23, 1.380649e-23, 6.62607015e-34, 299792458.0
    a.ok(close(VC("VC-01"), NA * kB, 1e-9), "R_u = N_A k_B")
    a.ok(close(VC("VC-03"), 2 * math.pi ** 5 * kB ** 4 / (15 * h ** 3 * cl ** 2), 1e-8), "sigma from k, h, c")
    a.ok(close(VC("VC-02"), 2 * 14.007, 1e-4), "M(N2) vs 2 x 14.007")
    a.ok(20.0 < VC("VC-04") < 21.5 and 19.0 < VC("VC-05") < VC("VC-04"), "oxygen fractions")
    a.ok(VC("VC-06") > float(reg["VP-01"]["value"]), "O2 boils above N2")
    for k, row in consts.items():
        a.ok(row["source_url"].startswith("https://") and row["retrieved"], f"{k} has no URL or date")
    for pid, r in reg.items():
        if r["class"] == "VERIFIED" and r["source_ref"].startswith("VC-"):
            a.ok(close(float(r["value"]), VC(r["source_ref"]), 1e-9), f"{pid} differs from {r['source_ref']}")
    a.done("exact SI relations hold; every row has a URL and date", "CODATA exact values and the standard atomic weight")

    a = c.acc("V-A04", "Verified nitrogen tables are internally consistent")
    S = props.sets
    row = lambda ds, **kw: next(r for r in S[ds] if all(abs(r[k] - v) < 1e-9 for k, v in kw.items()))
    g0 = props.gas300(props.P_ATM)
    Rs = VC("VC-01") / (VC("VC-02") / 1000.0)
    rho_ig = 101325.0 / (Rs * 300.0)
    a.ok(abs(g0["rho_kg_m3"] / rho_ig - 1) < 0.0015, f"ideal-gas density {rho_ig:.5f} vs table {g0['rho_kg_m3']}")
    a.ok(abs(g0["cp_kJ_kgK"] / g0["cv_kJ_kgK"] - 1.4) < 0.003, "cp/cv near 7/5 for a diatomic gas at low pressure")
    sat = {n: props.sat(n) for n in ("0", "0P2", "0P5", "1")}
    # Clapeyron: dp/dT = h_fg / (T (1/rho_v - 1/rho_l)) at the middle state, against a central difference over the neighbours
    (l0, v0), (l1, v1), (l2, v2) = sat["0"], sat["0P2"], sat["0P5"]
    fd = (l2["p_MPa_abs"] - l0["p_MPa_abs"]) * 1e6 / (l2["T_K"] - l0["T_K"])
    cl_ = (v1["h_kJ_kg"] - l1["h_kJ_kg"]) * 1e3 / (l1["T_K"] * (1 / v1["rho_kg_m3"] - 1 / l1["rho_kg_m3"]))
    a.ok(abs(fd / cl_ - 1) < 0.05, f"Clapeyron {cl_:.0f} vs finite difference {fd:.0f} Pa/K")
    for pg in (1, 2, 5, 10):
        h_iso = props.gas300(props.P_ATM + pg)["h_kJ_kg"]
        h_bar = props.h_gas(300.0, pg)
        a.ok(close(h_iso, h_bar, 1e-5), f"h(300 K, {pg} MPa(g)) differs between isotherm {h_iso} and isobar {h_bar}")
    for key in ("806", "760", "700"):
        rows = sorted(S[f"N2_ISOCHORE_{key}"], key=lambda r: r["T_K"])
        a.ok(all(b["p_MPa_abs"] >= x["p_MPa_abs"] for x, b in zip(rows, rows[1:])), f"isochore {key} not monotonic")
    iso806 = sorted(S["N2_ISOCHORE_806"], key=lambda r: r["T_K"])
    a.ok(abs(iso806[0]["p_MPa_abs"] - props.P_ATM) < 1e-3, "806 kg/m3 isochore starts at 0.101325 MPa")
    a.ok(abs(sat["0"][0]["T_K"] - 77.355) < 0.01 and abs(sat["0"][0]["rho_kg_m3"] - 806.08) < 0.1, "boiling point and liquid density at 1 atm")
    hfg = (sat["0"][1]["h_kJ_kg"] - sat["0"][0]["h_kJ_kg"])
    a.ok(abs(hfg - 199.18) < 0.05, f"latent heat {hfg}")
    a.done("tolerances: 0.15 percent for the ideal-gas density (Z = 0.9998), 5 percent for Clapeyron (central difference over a 19 K interval carries a curvature error of a few percent)", "equation-of-state tables")

    a = c.acc("V-A05", "NIST material fits: independent evaluation, reference points and sanity windows")
    co = lambda r: [VC(f"VC-{n}") for n in r]
    ex_ss, ex_al = co(range(40, 45)), co(range(50, 55))
    horner = lambda cf, T: sum(ci * T ** n for n, ci in enumerate(cf))
    a.ok(abs(horner(ex_ss, 293.0)) < 1.0 and abs(horner(ex_al, 293.0)) < 1.0, "expansion is referenced to 293 K: y(293) must be near zero (units 1e-5; fit errors are 5 and 4 percent of about 280 and 400)")
    a.ok(-295 < horner(ex_ss, 77.355) < -265, f"304 expansion at 77 K: {horner(ex_ss, 77.355):.1f}")
    a.ok(-420 < horner(ex_al, 77.355) < -385, f"6061 expansion at 77 K: {horner(ex_al, 77.355):.1f}")
    a.ok(close(cy.strain_y("SS304", 150.0), horner(ex_ss, 150.0), 1e-12) and close(cy.strain_y("AL6061T6", 150.0), horner(ex_al, 150.0), 1e-12), "code matches direct summation")
    kss = lambda T: 10 ** sum(cf * math.log10(T) ** n for n, cf in enumerate(co(range(10, 19))))
    cpss = lambda T: 10 ** sum(cf * math.log10(T) ** n for n, cf in enumerate(co(range(20, 29))))
    a.ok(close(cy.k_ss(100.0), kss(100.0), 1e-12) and close(cy.cp_ss(100.0), cpss(100.0), 1e-12), "log-polynomial fits match direct summation")
    a.ok(12.0 < kss(300.0) < 17.0 and 440 < cpss(300.0) < 520, f"304 at 300 K: k {kss(300.0):.2f} W/(m K), cp {cpss(300.0):.0f} J/(kg K)")
    a.ok(195 < horner(co(range(30, 35)), 293.0) < 205 and 68 < horner(co(range(60, 65)), 293.0) < 72, "Young's modulus at 293 K near 200 and 70 GPa")
    a.done("windows are broad physical magnitudes consistent with the NIST fit errors of 1 to 5 percent", "NIST cryogenic materials")

    a = c.acc("V-A06", "Online: verified constants, material coefficients and property values match the live public pages")
    if not c.online:
        c.rec("V-A06", a.desc, True, skip=True, note="needs network access; run with --online (performed at authoring, see the report header)")
    else:
        page_cache = {}

        def page(u):
            if u not in page_cache:
                req = urllib.request.Request(u, headers={"User-Agent": "curl/8 (validate_design.py; educational project)"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    page_cache[u] = r.read().decode("utf-8", "replace")
            return page_cache[u]
        flat = lambda s: re.sub(r"\s+", "", html.unescape(re.sub(r"<[^>]+>", " ", s)))
        for k, row in consts.items():
            v = row["value"]
            if v == "0" or k == "VC-07":
                continue
            try:
                body = flat(page(row["source_url"]))
            except Exception as e:                                       # network or HTTP failure counts as a failed check
                a.ok(False, f"{k}: {type(e).__name__}")
                continue
            probe = v.replace("e-8", "") if k == "VC-03" else v
            a.ok(probe in body, f"{k}: {v} not on the page")
        # spot checks of the generated nitrogen table against the NIST WebBook (values are read, never stored)
        base = ("https://webbook.nist.gov/cgi/fluid.cgi?Action=Data&Wide=on&ID=C7727379&Digits=7&RefState=DEF&TUnit=K&PUnit=MPa"
                "&DUnit=kg/m3&HUnit=kJ/kg&WUnit=m/s&VisUnit=uPa*s&STUnit=N/m")
        spots = [("&Type=IsoTherm&T=300&PLow=0.101325&PHigh=20.101325&PInc=20", "N2_GAS_300K_ISOTHERM"), ("&Type=IsoBar&P=0.101325&TLow=100&THigh=300&TInc=100", "N2_GAS_ISOBAR_0MPAG"),
                 ("&Type=IsoBar&P=5.101325&TLow=240&THigh=300&TInc=60", "N2_GAS_ISOBAR_5MPAG")]
        cols = {"rho_kg_m3": "Density (kg/m3)", "cp_kJ_kgK": "Cp (J/g*K)", "cv_kJ_kgK": "Cv (J/g*K)", "jt_K_per_MPa": "Joule-Thomson (K/MPa)", "mu_uPa_s": "Viscosity (uPa*s)", "k_W_mK": "Therm. Cond. (W/m*K)"}
        compared = 0
        for suffix, ds in spots:
            try:
                lines_ = [ln for ln in page(base + suffix).splitlines() if ln.strip()]
            except Exception as e:
                a.ok(False, f"NIST spot check {ds}: {type(e).__name__}")
                continue
            head = lines_[0].split("\t")
            ix = {h: i for i, h in enumerate(head)}
            for ln in lines_[1:]:
                f = ln.split("\t")
                T, p = float(f[ix["Temperature (K)"]]), float(f[ix["Pressure (MPa)"]])
                mine = min(S[ds], key=lambda r: abs(r["T_K"] - T) + abs(r["p_MPa_abs"] - p))
                if abs(mine["T_K"] - T) > 1e-3 or abs(mine["p_MPa_abs"] - p) > 1e-5:
                    a.ok(False, f"{ds}: no row at {T} K, {p} MPa")
                    continue
                compared += 1
                for k, nm in cols.items():
                    a.ok(close(mine[k], float(f[ix[nm]]), 5e-6), f"{ds} {T} K {p:.4g} MPa {k}: {mine[k]} vs NIST {f[ix[nm]]}")
                a.ok(abs(mine["h_kJ_kg"] - float(f[ix["Enthalpy (kJ/kg)"]])) < 5e-4, f"{ds} {T} K {p:.4g} MPa enthalpy")
        a.ok(compared >= 7, f"only {compared} spot states compared")
        try:
            lines_ = [ln for ln in page(base + "&Type=IsoBar&P=0.101325&TLow=70&THigh=110&TInc=40").splitlines() if ln.strip()]
            ix = {h: i for i, h in enumerate(lines_[0].split("\t"))}
            liq, vap = props.sat("0")
            for ln in lines_[1:]:
                f = ln.split("\t")
                if f[ix["Phase"]] in ("liquid", "vapor") and abs(float(f[ix["Temperature (K)"]]) - liq["T_K"]) < 0.01:
                    ref = liq if f[ix["Phase"]] == "liquid" else vap
                    a.ok(close(ref["rho_kg_m3"], float(f[ix["Density (kg/m3)"]]), 2e-5) and abs(ref["h_kJ_kg"] - float(f[ix["Enthalpy (kJ/kg)"]])) < 2e-3, f"saturation state {f[ix['Phase']]}")
        except Exception as e:
            a.ok(False, f"saturation spot check: {type(e).__name__}")
        gen = load_module(c.ext / "generate_verified_properties.py", "gen_mod")
        try:
            import CoolProp  # noqa: F401
            fresh = gen.to_csv_text(gen.build())
            a.ok(gen.compare(text(c.ext / "verified_properties.csv"), fresh, 1e-6), "verified_properties.csv differs from a fresh CoolProp generation (relative 1e-6)")
            note_cp = "table regenerated with CoolProp and compared"
        except ImportError:
            note_cp = "CoolProp not installed here: the table was not regenerated"
        a.done("every transcribed value is on its page; spot states agree with the NIST WebBook within 5e-6 relative (observed agreement at authoring: about 1e-6)", f"NIST CODATA, NIST WebBook, NIST cryogenic materials, NASA, Cornell LII; {note_cp}")


# ======================================================================================
# B. units and formulas
# ======================================================================================
def haaland(Re, rr):
    return (-1.8 * math.log10((rr / 3.7) ** 1.11 + 6.9 / Re)) ** -2


def colebrook_bisect(Re, rr):
    f = lambda x: 1.0 / math.sqrt(x) + 2.0 * math.log10(rr / 3.7 + 2.51 / (Re * math.sqrt(x)))
    lo, hi = 1e-4, 0.5
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
    return 0.5 * (lo + hi)


def check_B(c):
    mod, consts, props, hp, cy = c.calc()
    reg = c.reg()
    P = lambda k: float(reg[k]["value"])
    ALLOWED = {"K", "Pa", "MPa(g)", "m", "mm", "kg/s", "g/s", "kg/m3", "-", "percent", "J/(mol K)", "g/mol", "W/(m2 K4)", "m/s", "J/(kg K)", "kJ/kg",
               "kJ/(kg K)", "1/m", "m3", "L/s", "W/m", "L/h", "MPa", "kPa", "kg/m", "kg/m2", "W", "kN", "MPa/K", "min", "s", "L", "g/(s mm2)", "mm2", "W/(m K)"}
    a = c.acc("V-B01", "Units: allowed unit strings, and unit conversions in the CSV outputs agree with independent recomputation")
    for pid, r in reg.items():
        a.ok(r["unit"] in ALLOWED, f"{pid}: unit '{r['unit']}'")
    bud = c.csv("pressure_budget.csv")
    atm = P("EX-02") / 1e6
    for r in bud:
        if r["tag"] == "FE-301" and r["data_class"] == "ALLOCATION":
            for col, key in (("dp_low_kPa", "low"), ("dp_nom_kPa", "nom"), ("dp_high_kPa", "high")):
                exp = P(f"AS-04-fe-{key}") * (float(r["p_in_MPa_g"]) + atm) * 1e3
                a.ok(close(float(r[col]), exp, 2e-5), f"FE-301 {col} {r[col]} vs {exp:.5g} kPa (Pa, kPa and MPa mixed up?)")
    heat = c.csv("cryogenic_heat_leak.csv")
    rho_l = P("VP-02")
    for r in heat:
        if r["Q_total_W_m"]:
            gs = float(r["Q_total_W_m"]) / (cy.hfg) * 1e3
            a.ok(close(float(r["boil_g_s_m"]), gs, 2e-5), f"{r['scenario']} {r['case']} boil g/s")
            a.ok(close(float(r["boil_L_h_m"]), gs * 1e-3 / rho_l * 1e3 * 3600, 2e-5), f"{r['scenario']} {r['case']} boil L/h")
    for r in c.csv("thermal_contraction.csv"):
        a.ok(close(float(r["dL_mm"]), float(r["contraction_strain_pct"]) / 100 * float(r["length_m"]) * 1e3, 2e-5), f"{r['material']} {r['length_m']} m dL_mm")
        a.ok(close(float(r["restrained_force_kN"]), float(r["restrained_stress_MPa"]) * float(r["section_area_mm2"]) * 1e-3, 2e-5), f"{r['material']} force kN")
    for r in c.csv("trapped_liquid.csv"):
        if r["section"] == "TIME_TO_PRESSURE":
            m = rho_l * math.pi / 4 * cy.Di_bore ** 2
            exp = m * P("VP-06") * 1e3 * float(r["dT_K"]) / float(r["Q_W_m"]) / 60.0
            a.ok(close(float(r["time_min"]), exp, 3e-5), f"trapped {r['heat_case']} {r['target_p_MPa_g']} time")
    a.done("conversion factors agree to 2e-5 (CSV values carry 6 significant digits)", "kPa, MPa, g/s, L/h, mm, kN, min")

    a = c.acc("V-B02", "Pipe pressure loss: isothermal compressible formula against independent Colebrook (bisection) and Haaland")
    p1, D, eps = 1.101325e6, 0.010, 4.5e-5
    st = hp.state(p1)
    for L, tol in ((0.05, 1e-3), (6.0, 2e-2)):
        dp, v, Re, f = hp.pipe_dp(p1, D, L, eps)
        G = hp.mdot / (math.pi * D * D / 4)
        fc = colebrook_bisect(Re, eps / D)
        a.ok(close(f, fc, 1e-6), f"Colebrook f {f} vs {fc}")
        a.ok(abs(f / haaland(Re, eps / D) - 1) < 0.03, "Colebrook vs Haaland within 3 percent (Haaland is itself an approximation, stated error about 2 percent)")
        dp_dw = fc * L / D * G * G / (2 * st["rho"])
        a.ok(abs(dp / dp_dw - 1) < tol, f"L {L} m: dp {dp:.4f} vs Darcy-Weisbach {dp_dw:.4f} Pa (relative {dp / dp_dw - 1:.2e})")
    a.done("0.1 percent for a 0.05 m segment (pressure drop about 0.007 percent of the pressure, so the compressible and Darcy-Weisbach formulas must coincide); 2 percent for 6 m (compressibility changes the result by about half the relative pressure drop, here under 1 percent)", "")

    a = c.acc("V-B03", "Choked and subsonic flux formulas")
    g, cd = hp.gamma, P("AS-06")
    for p0 in (1.1e6, 5.1e6, 20.1e6):
        rho0 = hp.state(p0)["rho"]
        zrt = p0 / rho0
        closed = cd * p0 * math.sqrt(g / zrt) * (2 / (g + 1)) ** ((g + 1) / (2 * (g - 1)))
        a.ok(close(hp.choked_flux(p0, rho0), closed, 1e-12), f"choked flux at {p0:.3g} Pa")
        rc = (2 / (g + 1)) ** (g / (g - 1))
        sub = cd * math.sqrt(2 * rho0 * p0 * g / (g - 1) * (rc ** (2 / g) - rc ** ((g + 1) / g)))
        a.ok(close(sub, closed, 1e-12), "subsonic branch meets the choked value at the critical ratio")
        G1, ch, r, rc2 = hp.flux(p0, 0.9 * p0, rho0)
        a.ok(not ch and G1 < closed, "subsonic flux is below the choked flux")
        G2, ch2, _, _ = hp.flux(p0, 0.1 * p0, rho0)
        a.ok(ch2 and close(G2, closed, 1e-12), "flux is choked below the critical ratio")
    a.ok(abs((2 / (1.4 + 1)) ** (1.4 / 0.4) - 0.5283) < 1e-4, "critical ratio 0.5283 for gamma 1.4")
    a.done("equal to 1e-12 (same equations, written independently)", "")

    a = c.acc("V-B04", "Radiation, gas conduction and support formulas against limiting cases")
    Th, Tc = 300.0, cy.Tc
    save = cy.Dj
    cy.Dj = cy.Do * (1 + 1e-9)
    plane = cy.sigma * (Th ** 4 - Tc ** 4) / (1 / 0.2 + 1 / 0.2 - 1) * math.pi * cy.Do
    a.ok(close(cy.rad_bare(Th, Tc, 0.2, 0.2), plane, 1e-6), "concentric cylinders tend to parallel plates when the gap closes")
    cy.Dj = save
    a.ok(close(cy.rad_mli(Th, Tc, 0.003), 5.670374419e-8 * math.pi * cy.Do * 0.003 * (Th ** 4 - Tc ** 4), 1e-8), "MLI radiation")
    Tm = 0.5 * (Th + Tc)
    lam = (1.4 + 1) / (1.4 - 1) * math.sqrt(8.314462618 / (8 * math.pi * 0.0280134 * Tm))
    a.ok(1.3 < lam < 1.7, f"free-molecular coefficient {lam:.3f} W/(m2 K Pa)")
    a.ok(close(cy.gas_fm(Th, Tc, 1e-3, 0.9), 0.9 * lam * 1e-3 * (Th - Tc) * math.pi * cy.Do, 1e-8), "free-molecular heat flow")
    kv0 = cy.kv
    cy.kv = [(Tc, 0.02), (320.0, 0.02)]
    a.ok(close(cy.gas_cont(Th, Tc), 2 * math.pi * 0.02 * (Th - Tc) / math.log(cy.Dj / cy.Do), 1e-9), "continuum conduction for a constant conductivity")
    cy.kv = kv0
    ks0 = cy.k_ss
    cy.k_ss = lambda T: 10.0
    a.ok(close(cy.supports(300.0, 2e-5, 1.0), 2e-5 * 10.0 * (300.0 - cy.Tc), 1e-9), "support conduction for a constant conductivity")
    cy.k_ss = ks0
    qfm, qc = cy.gas_fm(Th, Tc, 1.0, 0.9), cy.gas_cont(Th, Tc)
    br = cy.gas_bridge(Th, Tc, 1.0, 0.9)
    a.ok(br < min(qfm, qc) and close(br, 1 / (1 / qfm + 1 / qc), 1e-12), "bridged value is below both limits")
    a.done("limiting cases to 1e-6 to 1e-12 (closed-form identities)", "")

    a = c.acc("V-B05", "Cooldown energy and boil-off arithmetic")
    n = 4000
    Ts = [cy.Tc + i * (300.0 - cy.Tc) / n for i in range(n + 1)]
    trap = sum(0.5 * (cy.cp_ss(x) + cy.cp_ss(y)) * (y - x) for x, y in zip(Ts, Ts[1:]))
    cool = {float(r["length_m"]): r for r in c.csv("cryogenic_cooldown.csv")}
    a.ok(close(float(cool[1.0]["metal_dh_kJ_kg"]) * 1e3, trap, 1e-5), "integral of cp against a trapezoid sum")
    Am = math.pi / 4 * (cy.Do ** 2 - cy.Di_bore ** 2)
    a.ok(close(float(cool[10.0]["metal_mass_kg"]), P("AS-16") * Am * 10.0, 1e-5), "metal mass")
    a.ok(close(float(cool[10.0]["LN2_kg_latent_only"]), float(cool[10.0]["energy_to_remove_kJ"]) / float(cool[10.0]["hfg_kJ_kg"]), 1e-5), "LN2 mass = energy / latent heat")
    a.ok(float(cool[10.0]["LN2_kg_full_sensible"]) < float(cool[10.0]["LN2_kg_latent_only"]), "using the vapour sensible heat needs less liquid than latent heat only")
    a.ok(close(float(cool[10.0]["hfg_kJ_kg"]), (cy.vap["h_kJ_kg"] - cy.liq["h_kJ_kg"]), 1e-5), "latent heat from the table")
    a.done("to 1e-5; trapezoid sum with 4000 intervals against Simpson with 2000", "")

    a = c.acc("V-B06", "Thermal contraction and restrained stress bounds")
    tc = {(r["material"], r["length_m"]): r for r in c.csv("thermal_contraction.csv")}
    for mat, key in (("SS304", "SS304"), ("AL6061T6", "AL6061T6")):
        cf = [float(consts[f"VC-{n}"]["value"]) for n in (range(40, 45) if mat == "SS304" else range(50, 55))]
        y = lambda T: sum(ci * T ** k for k, ci in enumerate(cf)) * 1e-5
        eps_ind = -(y(cy.Tc) - y(300.0)) / (1 + y(300.0))
        r10 = tc[(key, "10")]
        a.ok(close(float(r10["contraction_strain_pct"]) / 100, eps_ind, 2e-5), f"{mat} strain")
        e293 = float(r10["E_293K_GPa"]) * 1e3
        ecold = float(r10["E_cold_GPa"]) * 1e3
        eps_293 = -(y(cy.Tc) - y(293.0)) / (1 + y(293.0))
        sig = float(r10["restrained_stress_MPa"])
        a.ok(e293 * eps_293 * 0.999 <= sig <= ecold * eps_293 * 1.001, f"{mat} stress {sig:.1f} MPa outside [E(293) eps, E(cold) eps]")
    a.ok(float(tc[("AL6061T6", "10")]["dL_mm"]) > float(tc[("SS304", "10")]["dL_mm"]), "aluminium shortens more than stainless steel")
    a.done("to 2e-5; stress bounded by the moduli at the two ends", "")

    a = c.acc("V-B07", "Joule-Thomson drop consistent with the integral of the tabulated coefficient")
    env = {(r["stage"], r["p_in_MPa_g"], r["p_out_MPa_g"], r["T_in_K"]): r for r in c.csv("regulator_envelope.csv")}
    ps = [(r["p_MPa_abs"], r["jt_K_per_MPa"]) for r in props.iso]
    s1 = next(r for r in c.csv("regulator_envelope.csv") if r["stage"] == "PCV-301" and r["p_in_MPa_g"] == "20")
    lo, hi = 5 + props.P_ATM, 20 + props.P_ATM
    xs = [x for x, _ in ps if lo - 1e-3 <= x <= hi + 1e-3]
    ys = [y for x, y in ps if lo - 1e-3 <= x <= hi + 1e-3]
    integral = sum(0.5 * (ys[i] + ys[i + 1]) * (xs[i + 1] - xs[i]) for i in range(len(xs) - 1))
    ratio = -float(s1["dT_K"]) / integral
    a.ok(0.98 < ratio < 1.15, f"|dT| / integral of mu_JT at 300 K = {ratio:.3f}")
    a.done("ratio between 0.98 and 1.15: the 300 K coefficient integral neglects that mu_JT rises as the gas cools, so the true drop is slightly larger; a ratio below 1 or far above would indicate an error", "")

    a = c.acc("V-B08", "Trapped-liquid pressure rise and time to threshold")
    tl = c.csv("trapped_liquid.csv")
    iso = sorted((r for r in tl if r["section"] == "ISOCHORE" and abs(float(r["fill_density_kg_m3"]) - 806.0844) < 1e-3), key=lambda r: float(r["T_K"]))
    a.ok(len(iso) >= 5 and all(float(y["p_MPa_g"]) > float(x["p_MPa_g"]) for x, y in zip(iso, iso[1:])), "liquid-full isochore rises monotonically")
    slopes = [(float(y["p_MPa_g"]) - float(x["p_MPa_g"])) / (float(y["T_K"]) - float(x["T_K"])) for x, y in zip(iso, iso[1:])]
    a.ok(all(1.0 < s < 2.5 for s in slopes), f"slopes {min(slopes):.2f} to {max(slopes):.2f} MPa/K")
    tt = [r for r in tl if r["section"] == "TIME_TO_PRESSURE"]
    a.ok(all(float(r["time_min"]) > 0 for r in tt), "times are positive")
    for hc in {r["heat_case"] for r in tt}:
        seq = [float(r["time_min"]) for r in sorted((r for r in tt if r["heat_case"] == hc), key=lambda r: float(r["target_p_MPa_g"]))]
        a.ok(all(y > x for x, y in zip(seq, seq[1:])), f"{hc}: higher pressure threshold takes longer")
    a.done("slopes between 1.0 and 2.5 MPa/K (the isochore is nearly linear at about 1.7 MPa/K)", "")

    a = c.acc("V-B09", "Oxygen-deficiency formula")
    x0, thr = P("VC-04") / 100, P("VC-05") / 100
    for r in c.csv("oxygen_deficiency_screening.csv"):
        V, Vadd = float(r["room_volume_m3"]), float(r["max_added_gas_m3_to_reach_threshold"])
        a.ok(close(x0 * math.exp(-Vadd / V), thr, 1e-5), f"{r['source']} {V:g} m3: exp relation")
        a.ok(close(float(r["litres_to_reach_threshold"]) * float(r["ambient_gas_m3_per_litre"]), Vadd, 2e-5), f"{r['source']} {V:g} m3: litres")
    ln2 = next(r for r in c.csv("oxygen_deficiency_screening.csv") if r["source"] == "LN2")
    a.ok(close(float(ln2["ambient_gas_m3_per_litre"]), P("VP-02") / P("VP-07") * 1e-3, 1e-4), "gas per litre of liquid (the 300 K, 0.101325 MPa gas density)")
    a.done("to 1e-5", "")


# ======================================================================================
# C. mass flow and pressure budget
# ======================================================================================
def check_C(c):
    mod, consts, props, hp, cy = c.calc()
    reg = c.reg()
    P = lambda k: float(reg[k]["value"])
    bud = c.csv("pressure_budget.csv")
    atm = P("EX-02") / 1e6
    rows = [r for r in bud if r["item_id"].startswith("B")]
    D = P("IL-06") / 1000.0
    A = math.pi * D * D / 4
    a = c.acc("V-C01", "Mass-flow continuity in the budget rows (v rho A equals the illustrative flow)")
    for r in rows:
        if r["v_in_m_s"]:
            rho = hp.state((float(r["p_in_MPa_g"]) + atm) * 1e6)["rho"]
            a.ok(close(float(r["v_in_m_s"]) * rho * A, P("IL-01"), 3e-5), f"{r['item_id']}: v rho A = {float(r['v_in_m_s']) * rho * A:.6g}")
    a.done("equal to 3e-5 (6-digit CSV values)", "")

    a = c.acc("V-C02", "Pressure chain arithmetic: pressure after each row equals pressure before minus loss; regulators land on their set pressures")
    p = P("IL-02")
    for r in rows:
        if r["data_class"] == "UNRESOLVED":
            a.ok(r["dp_nom_kPa"] == "" and abs(float(r["p_in_MPa_g"]) - p) < 2e-4, f"{r['item_id']} unresolved row must not change the pressure")
            continue
        a.ok(abs(float(r["p_in_MPa_g"]) - p) < 2e-4, f"{r['item_id']}: p_in {r['p_in_MPa_g']} vs chain {p:.6f}")
        if r["data_class"] == "CONTROLLED":
            setp = P("IL-03") if r["tag"] == "PCV-301" else P("IL-04")
            a.ok(abs(float(r["p_out_MPa_g"]) - setp) < 1e-9, f"{r['item_id']}: set pressure {r['p_out_MPa_g']}")
            a.ok(abs(float(r["dp_nom_kPa"]) / 1e3 - (p - setp)) < 2e-4, f"{r['item_id']}: controlled drop")
            p = setp
        else:
            p -= float(r["dp_nom_kPa"]) / 1e3
            a.ok(abs(float(r["p_out_MPa_g"]) - p) < 2e-4, f"{r['item_id']}: p_out {r['p_out_MPa_g']} vs {p:.6f}")
    a.done("each row to within 2e-4 MPa (the CSV prints 6 significant digits of a 20 MPa value)", "")

    a = c.acc("V-C03", "Zone totals equal the sum of the included rows, and all-zone equals the sum of the zones")
    for col in ("dp_low_kPa", "dp_nom_kPa", "dp_high_kPa"):
        tot = {}
        for z in ("HP", "INT", "DEL"):
            tot[z] = sum(float(r[col]) for r in rows if r["zone"] == z and r["included_in_total"] == "TRUE")
            row = next(r for r in bud if r["item_id"] == f"T-{z}")
            a.ok(close(float(row[col]), tot[z], 2e-5), f"T-{z} {col}: {row[col]} vs {tot[z]:.6g}")
        row = next(r for r in bud if r["item_id"] == "T-ALL")
        a.ok(close(float(row[col]), sum(tot.values()), 2e-5), f"T-ALL {col}")
    lim = next(r for r in bud if r["item_id"] == "LIMIT")
    mar = next(r for r in bud if r["item_id"] == "MARGIN")
    tdel = next(r for r in bud if r["item_id"] == "T-DEL")
    a.ok(close(float(lim["dp_nom_kPa"]), P("IL-09") * P("IL-04") * 1e3, 1e-9), "illustrative limit")
    a.ok(close(float(mar["dp_nom_kPa"]), float(lim["dp_nom_kPa"]) - float(tdel["dp_nom_kPa"]), 1e-5), "margin")
    a.done("to 2e-5", "")

    a = c.acc("V-C04", "Low, nominal and high cases are ordered for every included passive row")
    for r in rows:
        if r["included_in_total"] == "TRUE":
            lo, no, hi = float(r["dp_low_kPa"]), float(r["dp_nom_kPa"]), float(r["dp_high_kPa"])
            a.ok(lo <= no <= hi and no >= 0, f"{r['item_id']}: {lo} {no} {hi}")
    a.done("low <= nominal <= high", "controlled rows are excluded: their drop falls as upstream losses rise")

    a = c.acc("V-C05", "Unresolved rows carry no value and are excluded from totals; included rows have a value")
    for r in rows:
        if r["data_class"] == "UNRESOLVED":
            a.ok(r["included_in_total"] == "FALSE" and not (r["dp_low_kPa"] or r["dp_nom_kPa"] or r["dp_high_kPa"]), f"{r['item_id']}")
        elif r["data_class"] != "CONTROLLED":
            a.ok(r["included_in_total"] == "TRUE" and r["dp_nom_kPa"] != "", f"{r['item_id']}")
    ids = {r["item_id"] for r in rows}
    a.ok({"B14", "B16", "B21", "B22", "B23"} <= {r["item_id"] for r in rows if r["data_class"] == "UNRESOLVED"}, "flow-control valve, cracking pressure and the three vent rows stay unresolved")
    a.done("", "")

    a = c.acc("V-C06", "Sensitivity table reproduces the reference budget and moves in the expected direction")
    sens = c.csv("pressure_sensitivity.csv")
    ref = next(r for r in sens if r["id_mm"] == "10" and r["k_mult"] == "1")
    a.ok(close(float(ref["dp_DEL_kPa"]), float(tdel["dp_nom_kPa"]), 2e-5) and close(float(ref["dp_ALL_kPa"]), float(next(r for r in bud if r["item_id"] == "T-ALL")["dp_nom_kPa"]), 2e-5), "10 mm and multiplier 1 equals the reference budget")
    for km in {r["k_mult"] for r in sens}:
        seq = [float(r["dp_DEL_kPa"]) for r in sorted((r for r in sens if r["k_mult"] == km), key=lambda r: float(r["id_mm"]))]
        a.ok(all(x > y for x, y in zip(seq, seq[1:])), f"multiplier {km}: loss falls as the bore grows")
    for ids_ in {r["id_mm"] for r in sens}:
        seq = [float(r["dp_DEL_kPa"]) for r in sorted((r for r in sens if r["id_mm"] == ids_), key=lambda r: float(r["k_mult"]))]
        a.ok(all(y > x for x, y in zip(seq, seq[1:])), f"bore {ids_}: loss rises with the component multiplier")
    for r in sens:
        a.ok((float(r["dp_DEL_kPa"]) <= P("IL-09") * P("IL-04") * 1e3) == (r["within_IL09"] == "TRUE"), f"{r['id_mm']} {r['k_mult']}: limit flag")
    a.done("", "")

    a = c.acc("V-C07", "Regulator envelope: choked flag, flux and required area are consistent")
    gam = P("VP-08")
    rcrit = (2 / (gam + 1)) ** (gam / (gam - 1))
    for r in c.csv("regulator_envelope.csv"):
        ratio = (float(r["p_out_MPa_g"]) + atm) / (float(r["p_in_MPa_g"]) + atm)
        a.ok(close(float(r["ratio"]), ratio, 2e-5) and close(float(r["ratio_crit"]), rcrit, 1e-4), f"{r['stage']} {r['p_in_MPa_g']}: ratio")
        a.ok((ratio <= rcrit) == (r["choked"] == "TRUE"), f"{r['stage']} {r['p_in_MPa_g']}: choked flag")
        a.ok(float(r["T_out_K"]) < float(r["T_in_K"]) and abs(float(r["dT_K"]) - (float(r["T_out_K"]) - float(r["T_in_K"]))) < 2e-3, f"{r['stage']} {r['p_in_MPa_g']}: expansion cools the gas (dT to 2e-3 K: the CSV rounds 300 K values to 6 digits)")
        if r["A_req_mm2"]:
            a.ok(close(float(r["A_req_mm2"]) * float(r["G_kg_m2s"]) * 1e-6, P("IL-01"), 3e-5), f"{r['stage']} {r['p_in_MPa_g']}: A x G = flow")
        a.ok(0 < float(r["Z_in"]) < 1.5, "compressibility factor plausible")
    st1 = sorted((r for r in c.csv("regulator_envelope.csv") if r["stage"] == "PCV-301"), key=lambda r: float(r["p_in_MPa_g"]))
    a.ok(all(float(y["A_req_mm2"]) < float(x["A_req_mm2"]) for x, y in zip(st1, st1[1:])), "required area falls as the inlet pressure rises")
    a.done("", "")


# ======================================================================================
# D. parameter bounds and output sanity
# ======================================================================================
def check_D(c):
    reg = c.reg()
    a = c.acc("V-D01", "Every numeric parameter lies within its stated bounds; bounds are ordered; sweeps parse")
    for pid, r in reg.items():
        v = num(r["value"])
        lo, hi = num(r["bound_min"]), num(r["bound_max"])
        if lo is not None and hi is not None:
            a.ok(lo < hi, f"{pid}: bounds {lo} {hi}")
            a.ok(v is not None and lo <= v <= hi, f"{pid}={r['value']} outside [{lo}, {hi}]")
        if v is None and r["class"] not in ("UNRESOLVED",) and ";" in r["value"]:
            a.ok(all(num(x) is not None for x in r["value"].split(";")), f"{pid}: sweep does not parse")
        if r["class"] in ("ASSUMED", "ILLUSTRATIVE", "VERIFIED", "EXISTING") and ";" not in r["value"]:
            a.ok(v is not None and (v >= 0 or r["unit"] == "kJ/kg"), f"{pid}: not a non-negative number")
    for pid in reg:
        if pid.startswith(("AS-10", "AS-11", "AS-12")):
            a.ok(0 < float(reg[pid]["value"]) <= 1.0, f"{pid}: an emissivity or accommodation coefficient must be in (0, 1]")
    a.done("each value within [bound_min, bound_max]; emissivities and accommodation in (0, 1]", "bounds are physical limits, not tuned to the results")

    a = c.acc("V-D02", "Output sanity: totals equal their parts, scenario order, shares, signs")
    heat = [r for r in c.csv("cryogenic_heat_leak.csv") if r["Q_total_W_m"]]
    for r in heat:
        parts = float(r["Q_rad_W_m"]) + float(r["Q_gas_W_m"]) + float(r["Q_support_W_m"])
        a.ok(close(float(r["Q_total_W_m"]), parts, 2e-5), f"{r['scenario']} {r['case']}: total {r['Q_total_W_m']} vs parts {parts:.6g}")
        a.ok(abs(float(r["share_rad_pct"]) + float(r["share_gas_pct"]) + float(r["share_support_pct"]) - 100) < 1e-3, f"{r['scenario']} {r['case']}: shares")
    q = {(r["scenario"], r["case"]): float(r["Q_total_W_m"]) for r in heat}
    a.ok(q[("S1", "nom")] < q[("S2", "nom")] < q[("S3", "nom")] < q[("S4", "nom")], "S1 < S2 < S3 < S4")
    for s in ("S1", "S2", "S3", "S4"):
        a.ok(q[(s, "low")] <= q[(s, "nom")] <= q[(s, "high")], f"{s}: low <= nominal <= high")
    for r in c.csv("cryogenic_uncertainty.csv"):
        a.ok(float(r["Q_at_high_W_m"]) >= float(r["Q_at_low_W_m"]) and close(float(r["swing_W_m"]), abs(float(r["Q_at_high_W_m"]) - float(r["Q_at_low_W_m"])), 1e-9, 1e-5 * max(1.0, float(r["Q_nominal_W_m"]))), f"{r['scenario']} {r['parameter']}")
    a.ok(any(r["scenario"] == "VESSEL" and r["confidence"] == "NOT CALCULATED" for r in c.csv("cryogenic_heat_leak.csv")), "vessel evaporation is marked NOT CALCULATED")
    for r in c.csv("pressure_budget.csv"):
        if r["included_in_total"] == "TRUE":
            a.ok(float(r["dp_nom_kPa"]) >= 0, f"{r['item_id']}: negative loss")
    for r in c.csv("thermal_contraction.csv"):
        a.ok(float(r["contraction_strain_pct"]) > 0 and float(r["restrained_stress_MPa"]) > 0, f"{r['material']}: contraction and stress positive")
    for r in c.csv("cryogenic_property_screening.csv"):
        a.ok(float(r["liquid_to_sat_vapour_volume_ratio"]) > 1 and float(r["h_fg_kJ_kg"]) > 0, f"p {r['p_MPa_g']}")
    a.done("", "")


# ======================================================================================
# E. tags, diagrams, schedules
# ======================================================================================
def check_E(c):
    eq, ins, eqt, int_ = c.schedules()
    lines = c.lines()
    allt = eqt | int_
    reg_lines = {s: {r["line_id"] for r in rows} for s, rows in lines.items()}
    a = c.acc("V-E01", "Tags are unique, well formed and in the right area; schedules do not overlap")
    for name, rows in (("equipment", eq), ("instrument", ins)):
        tags = [r["tag"] for r in rows]
        a.ok(len(tags) == len(set(tags)), f"{name} tags not unique")
        for r in rows:
            a.ok(bool(re.fullmatch(r"[A-Z]{1,5}-\d{3}", r["tag"])), f"{r['tag']} format")
            area = {"HP": "3", "CRYO": "4"}[r["system"]]
            a.ok(r["tag"].split("-")[1][0] == area, f"{r['tag']} is in the wrong area for system {r['system']}")
    a.ok(not (eqt & int_), "a tag is in both schedules")
    for s, rows in lines.items():
        ids = [r["line_id"] for r in rows]
        a.ok(len(ids) == len(set(ids)) and all(i.startswith("L-3" if s == "HP" else "L-4") for i in ids), f"{s} line IDs")
    a.done("", "")

    a = c.acc("V-E02", "Diagram tags equal the schedule flags in both directions, by system and drawing")
    flags = {}
    for rows in (eq, ins):
        for r in rows:
            flags.setdefault((r["system"], "pfd"), set()).update([r["tag"]] if r["shown_on_pfd"] == "YES" else [])
            flags.setdefault((r["system"], "pid"), set()).update([r["tag"]] if r["shown_on_pid"] == "YES" else [])
    system_tags = {s: {r["tag"] for rows in (eq, ins) for r in rows if r["system"] == s} for s in ("HP", "CRYO")}
    for name, (sysm, kind) in DIAGRAMS.items():
        body = strip_comments(text(c.ext / f"{name}.mmd"))
        got = tags_in(body)
        want = flags[(sysm, kind)]
        a.ok(got == want, f"{name}: missing {sorted(want - got)[:5]} extra {sorted(got - want)[:5]}")
        a.ok(got <= system_tags[sysm], f"{name}: tags of the other system or unknown {sorted(got - system_tags[sysm])[:5]}")
    a.done("diagram tags == flagged tags of the system", "")

    a = c.acc("V-E03", "Diagram line IDs equal the line-list flags in both directions")
    for name, (sysm, kind) in DIAGRAMS.items():
        body = strip_comments(text(c.ext / f"{name}.mmd"))
        want = {r["line_id"] for r in lines[sysm] if r[f"shown_on_{kind}"] == "YES"}
        got = lines_in(body)
        a.ok(got == want, f"{name}: missing {sorted(want - got)} extra {sorted(got - want)}")
    a.done("", "")

    a = c.acc("V-E04", "Every diagram has the banner in its title and body, and current SVG and PNG renders exist")
    for name in DIAGRAMS:
        src = text(c.ext / f"{name}.mmd")
        a.ok(src.count(BANNER) >= 2, f"{name}.mmd: banner count {src.count(BANNER)} (title and node needed)")
        a.ok("title:" in src and BANNER in src.split("---")[1], f"{name}.mmd: banner missing from the title")
        svg, png = c.ext / f"{name}.svg", c.ext / f"{name}.png"
        a.ok(svg.exists() and png.exists(), f"{name}: render missing")
        if svg.exists():
            s = text(svg)
            a.ok(BANNER in s or BANNER.replace("—", "&#8212;") in s, f"{name}.svg: banner text missing")
            body = strip_comments(src)
            for t in sorted(tags_in(body) | lines_in(body)):
                a.ok(t in s, f"{name}.svg is stale: {t} missing")
            for k, v in re.findall(r"^%% CALC (\w+)=(\S+)$", src, re.M):
                a.ok(v in s, f"{name}.svg is stale: {v} missing")
        if png.exists():
            b = png.read_bytes()
            a.ok(b[:8] == b"\x89PNG\r\n\x1a\n" and len(b) > 20000, f"{name}.png is not a plausible PNG")
    a.done("", "SVG and PNG were rendered with @mermaid-js/mermaid-cli 11.4.2")

    a = c.acc("V-E05", "Numbers in the diagrams equal the calculated values")
    mod, consts, props, hp, cy = c.calc()
    ctx_ = [c.csv(n) for n in OUTPUTS]
    H = c_headlines(c)
    for name in DIAGRAMS:
        src = text(c.ext / f"{name}.mmd")
        marks = re.findall(r"^%% CALC (\w+)=(\S+)$", src, re.M)
        body = strip_comments(src)
        for k, v in marks:
            a.ok(k in H and H[k] == v, f"{name}: CALC {k}={v} but calculated {H.get(k)}")
            a.ok(v in body, f"{name}: label does not show {v}")
    a.ok(sum(len(re.findall(r"^%% CALC", text(c.ext / f"{n}.mmd"), re.M)) for n in DIAGRAMS) >= 8, "at least 8 numbers are tied")
    bc = {r["station"]: r for r in c.csv("boundary_conditions.csv")}
    pfd = strip_comments(text(c.ext / "PFD_HIGH_PRESSURE.mmd"))
    a.ok(f"{float(bc['SB-301']['p_MPa_g']):g} MPa(g)" in pfd and f"{float(bc['SB-302']['p_MPa_g']):g} MPa(g)" in pfd and f"{float(bc['SB-303']['p_MPa_g']):g} MPa(g)" in pfd, "illustrative pressures on the GN2 PFD equal the boundary register")
    a.done("each marked value equals the formatted calculated value and appears in the drawing text", "")

    a = c.acc("V-E06", "Line lists agree with the calculations and the budget")
    bud = {r["item_id"]: r for r in c.csv("pressure_budget.csv")}
    reg = c.reg()
    for r in lines["HP"]:
        lid = r["line_id"]
        if f"AS-05-len-{lid}" in reg:
            a.ok(close(float(r["length_m_assumed"]), float(reg[f"AS-05-len-{lid}"]["value"]), 1e-9) and float(r["bends_assumed"]) == float(reg[f"AS-05-bends-{lid}"]["value"]), f"{lid}: length or bends differ from AS-05")
        listed = {x.strip() for x in r["budget_rows"].split(";") if x.strip()}
        owned = {i for i, b in bud.items() if b["line_id"] == lid and i.startswith("B")}
        a.ok(listed == owned, f"{lid}: budget rows listed {sorted(listed)} vs budget {sorted(owned)}")
        for t in re.findall(r"(\d+\.\d) K", r["illustrative_pressure_case"]):
            a.ok(any(abs(float(t) - float(b["T_K"])) < 0.051 for b in c.csv("boundary_conditions.csv") if b["T_K"]), f"{lid}: {t} K not in the boundary register")
    a.done("", "")

    a = c.acc("V-E07", "Schedules, instruments and line lists reference each other correctly")
    for r in ins:
        a.ok(r["location_tag"] in eqt, f"{r['tag']}: location {r['location_tag']}")
        s = r["system"]
        a.ok(not r["line_id"] or r["line_id"] in reg_lines[s], f"{r['tag']}: line {r['line_id']}")
        d = r["signal_destination"]
        a.ok(d == "none (local)" or d in eqt or d in int_, f"{r['tag']}: destination {d}")
        a.ok(bool(r["instrument_type"]) and bool(r["measured_variable"]), f"{r['tag']}: type")
    for r in eq:
        for ln in [x for x in r["lines"].split(";") if x]:
            a.ok(ln in reg_lines[r["system"]], f"{r['tag']}: line {ln}")
    for s, rows in lines.items():
        for r in rows:
            for t in (r["from_tag"], r["to_tag"]):
                a.ok(t in eqt or t in reg_lines[s], f"{r['line_id']}: end {t}")
            for t in tags_in(r["inline_items"]):
                a.ok(t in allt, f"{r['line_id']}: inline {t}")
    a.done("", "")

    a = c.acc("V-E08", "Every tag, line and station in the documents exists")
    known_lines = set().union(*reg_lines.values())
    stations = {r["station"] for r in c.csv("boundary_conditions.csv")}
    for d in DOCS:                                   # the generated report quotes failures, so it is not scanned
        p = c.ext / d
        t = text(p)
        a.ok(tags_in(t) <= allt, f"{d}: unknown tags {sorted(tags_in(t) - allt)[:5]}")
        a.ok(lines_in(t) <= known_lines, f"{d}: unknown lines {sorted(lines_in(t) - known_lines)[:5]}")
        a.ok(stations_in(t) <= stations, f"{d}: unknown stations {sorted(stations_in(t) - stations)[:5]}")
    for d, area in (("HIGH_PRESSURE_SYSTEM.md", "3"), ("HAZARD_REVIEW_HIGH_PRESSURE.md", "3"), ("CRYOGENIC_SYSTEM.md", "4"), ("HAZARD_REVIEW_CRYOGENIC.md", "4")):
        t = text(c.ext / d)
        other = [x for x in tags_in(t) if x.split("-")[1][0] != area]
        a.ok(not other, f"{d}: tags of the other system {other[:4]}")
    a.done("", "")

    a = c.acc("V-E09", "Boundary-condition and station tags exist")
    for r in c.csv("boundary_conditions.csv"):
        for t in tags_in(r["tag"].replace(";", " ")):
            a.ok(t in allt, f"{r['station']}: {t}")
        for t in re.findall(r"L-\d{3}", r["tag"]):
            a.ok(t in known_lines, f"{r['station']}: {t}")
    for name in ("PFD_HIGH_PRESSURE", "PID_HIGH_PRESSURE", "PFD_CRYOGENIC", "PID_CRYOGENIC"):
        a.ok(stations_in(strip_comments(text(c.ext / f"{name}.mmd"))) <= stations, f"{name}: unknown station")
    a.done("", "")

    a = c.acc("V-E10", "No size, rating or model is given in the schedules")
    unit = re.compile(r"\b\d+(\.\d+)?\s?(mm|cm|inch|in|NPS|DN|psi|psig|bar|barg|kPa|MPa|gal|L/min|kW|hp)\b")
    for r in eq:
        a.ok(r["rating_and_model"].startswith("Not selected"), f"{r['tag']}: rating_and_model must be 'Not selected...'")
        for col in ("name", "generic_type"):
            a.ok(not unit.search(r[col]), f"{r['tag']}: {col} contains a size or rating: {unit.search(r[col]).group(0) if unit.search(r[col]) else ''}")
        for col in ("function_and_rationale", "design_basis"):
            m = unit.search(r[col])
            a.ok(not m or re.search(r"IL-|AS-|illustrative|NASA-STD|UI-", r[col]), f"{r['tag']}: {col} has an unqualified size or rating {m.group(0) if m else ''}")
    for r in ins:
        for col in ("instrument_type", "range_and_accuracy_basis"):
            m = unit.search(r[col])
            a.ok(not m, f"{r['tag']}: {col} {m.group(0) if m else ''}")
    for s, rows in lines.items():
        for r in rows:
            a.ok(r["design_pressure"].startswith("UNRESOLVED") and r["design_temperature"].startswith("UNRESOLVED"), f"{r['line_id']}: design pressure or temperature is given")
            a.ok(r["bore_basis"].startswith("TBD"), f"{r['line_id']}: bore must be TBD")
    a.done("", "")


def c_headlines(c):
    mod, consts, props, hp, cy = c.calc()
    budget = mod.pressure_budget_rows(hp)
    sens = mod.sensitivity_rows(hp)
    heat = mod.heat_leak_rows(cy)
    cool = mod.cooldown_rows(cy)
    contr = mod.contraction_rows(cy)
    trapped = mod.trapped_rows(cy)
    oxy = mod.oxygen_rows(hp, cy)
    H = mod.HEADLINES(hp, cy, heat, contr, trapped, sens, budget, cool, oxy)
    return {k: format(v[0], v[1]) for k, v in H.items()}


# ======================================================================================
# F. traceability  G. assumptions  H. missing inputs
# ======================================================================================
REQ_STATUS = {"MET IN CONCEPT", "OPEN", "NOT APPLICABLE"}


def check_F(c):
    eq, ins, eqt, int_ = c.schedules()
    lines = c.lines()
    known_lines = set().union(*({r["line_id"] for r in rows} for rows in lines.values()))
    req = c.csv("REQUIREMENTS_TRACEABILITY.csv")
    registered = c.registered_ids if hasattr(c, "registered_ids") else set()
    a = c.acc("V-F01", "Traceability matrix is well formed: unique IDs, real tags and files, registered verification IDs")
    cols = {"req_id", "category", "requirement", "type", "source_basis", "implemented_in", "verification", "hazard_ids", "status", "open_items", "review_discipline"}
    a.ok(bool(req) and cols <= set(req[0].keys()), "columns")
    ids = [r["req_id"] for r in req]
    a.ok(len(ids) == len(set(ids)) and all(re.fullmatch(r"REQ-(HP|CR|GN)-\d\d", i) for i in ids), "requirement IDs")
    for r in req:
        a.ok(r["status"] in REQ_STATUS, f"{r['req_id']}: status {r['status']}")
        a.ok(len(r["requirement"]) > 20, f"{r['req_id']}: requirement text")
        for tok in [t.strip() for t in r["implemented_in"].split(";") if t.strip()]:
            first = tok.split(" ")[0]
            if TAG_RE.fullmatch(first):
                a.ok(first in eqt | int_ or first in known_lines, f"{r['req_id']}: tag {first}")
            elif re.fullmatch(r"L-\d{3}", first):
                a.ok(first in known_lines, f"{r['req_id']}: line {first}")
            else:
                a.ok((c.ext / first).exists(), f"{r['req_id']}: file {first}")
        for v in [t.strip() for t in r["verification"].split(";") if t.strip()]:
            a.ok(v in registered, f"{r['req_id']}: verification {v} is not a check of this script")
    a.done("", "")

    a = c.acc("V-F02", "Hazards and requirements cross-reference in both directions")
    hz = {}
    for d in ("HAZARD_REVIEW_HIGH_PRESSURE.md", "HAZARD_REVIEW_CRYOGENIC.md"):
        t = text(c.ext / d)
        for m in re.finditer(r"^\| (HAZ-(?:HP|CR)-\d\d) \|.*$", t, re.M):
            hz[m.group(1)] = m.group(0)
    a.ok(len(hz) >= 30, f"{len(hz)} hazards found")
    in_matrix = set()
    for r in req:
        for h in [t.strip() for t in r["hazard_ids"].split(";") if t.strip()]:
            a.ok(h in hz, f"{r['req_id']}: hazard {h} not in the reviews")
            in_matrix.add(h)
    a.ok(set(hz) <= in_matrix, f"hazards not traced to a requirement: {sorted(set(hz) - in_matrix)[:6]}")
    for h, row in hz.items():
        refs = set(re.findall(r"REQ-(?:HP|CR|GN)-\d\d", row))
        a.ok(bool(refs) and refs <= set(ids), f"{h}: requirement references {sorted(refs)}")
        for rr in refs:
            tr = next((x for x in req if x["req_id"] == rr), None)
            a.ok(tr is not None and h in tr["hazard_ids"], f"{h} cites {rr}, which does not list it")
    for d in DOCS:
        for rr in set(re.findall(r"REQ-(?:HP|CR|GN)-\d\d", text(c.ext / d))):
            a.ok(rr in ids, f"{d}: {rr} unknown")
    a.done("", "")

    a = c.acc("V-F03", "Unresolved inputs: register, missing-inputs file and design basis agree; every UI reference exists")
    reg = c.reg()
    ui_reg = {k for k, r in reg.items() if r["class"] == "UNRESOLVED"}
    ui_miss = {r["id"] for r in c.csv("missing_inputs_register.csv")}
    ui_doc = set(re.findall(r"^\| (UI-\d\d) \|", text(c.ext / "DESIGN_BASIS.md"), re.M))
    a.ok(ui_reg == ui_miss == ui_doc, f"register {len(ui_reg)}, file {len(ui_miss)}, doc {len(ui_doc)}")
    for r in c.csv("missing_inputs_register.csv"):
        a.ok(all(r[k] for k in ("why_needed", "blocked_calculations_or_decisions", "to_be_supplied_by", "effect_if_wrong", "workaround_in_this_study")), f"{r['id']}: empty field")
    used = set()
    for p in c.ext.iterdir():
        if p.suffix in (".md", ".csv", ".mmd"):
            used |= set(re.findall(r"\bUI-\d\d\b", text(p)))
    a.ok(used <= ui_reg, f"unknown UI references {sorted(used - ui_reg)}")
    a.done("", "")

    a = c.acc("V-F04", "Status rules: MET IN CONCEPT has verification; OPEN names unresolved inputs or decisions")
    for r in req:
        if r["status"] == "MET IN CONCEPT":
            a.ok(bool(r["verification"].strip()), f"{r['req_id']}: no verification")
        if r["status"] == "OPEN":
            oi = r["open_items"]
            a.ok(bool(re.findall(r"UI-\d\d|HAZ-\w+-\d\d", oi)), f"{r['req_id']}: OPEN without open items")
            a.ok(set(re.findall(r"UI-\d\d", oi)) <= ui_reg, f"{r['req_id']}: unknown UI")
    a.ok(sum(r["status"] == "OPEN" for r in req) >= 5, "open requirements are not hidden")
    a.done("", "")


def check_G(c):
    reg = c.reg()
    basis = text(c.ext / "DESIGN_BASIS.md")
    sec5 = basis.split("## 5.")[1].split("## 6.")[0]
    registered = set(re.findall(r"^\| ((?:AS|IL)-\d\d) \|", sec5, re.M))
    a = c.acc("V-G01", "Every AS and IL ID used is registered in DESIGN_BASIS.md section 5, and every registered ID is used")
    used = set()
    for p in c.ext.iterdir():
        if p.suffix in (".csv", ".mmd", ".py") and p.name != "validate_design.py":
            used |= set(re.findall(r"\b(?:AS|IL)-\d\d\b", text(p)))
        if p.suffix == ".md" and p.name not in ("VALIDATION_REPORT.md",):
            used |= set(re.findall(r"\b(?:AS|IL)-\d\d\b", text(p)))
    a.ok(used <= registered, f"used but not registered: {sorted(used - registered)}")
    method = text(c.ext / "CALCULATION_METHOD.md") + text(c.ext / "calculations.py")
    for i in sorted(registered):
        a.ok(i in method, f"{i} is registered but never used in the method or the code")
    for pid, r in reg.items():
        if r["class"] in ("ASSUMED", "ILLUSTRATIVE"):
            a.ok(r["assumption_id"] in registered, f"{pid}: assumption_id {r['assumption_id']}")
    a.ok(len(registered) >= 35, f"{len(registered)} registered IDs")
    a.done("", "")

    a = c.acc("V-G02", "Class labelling: each register row has a class, a source and the right kind of source")
    for pid, r in reg.items():
        cl, src = r["class"], r["source_ref"]
        a.ok(cl in ("EXISTING", "VERIFIED", "ASSUMED", "ILLUSTRATIVE", "UNRESOLVED", "CALCULATED"), f"{pid}: class {cl}")
        a.ok(bool(src), f"{pid}: no source")
        if cl == "EXISTING":
            a.ok(bool(re.match(r"M\d{3}$|01_Project", src)), f"{pid}: source {src}")
        if cl == "VERIFIED":
            a.ok(src.startswith(("VC-", "VP:")), f"{pid}: source {src}")
        if cl == "UNRESOLVED":
            a.ok(r["value"] == "" and src.startswith("UNRESOLVED:"), f"{pid}: an unresolved input carries a value")
        if cl == "CALCULATED":
            a.ok(src == "calculations.py", f"{pid}: source {src}")
    for r in c.csv("verified_properties.csv"):
        pass
    a.done("", "")


def check_H(c):
    reg = c.reg()
    mod, consts, props, hp, cy = c.calc()
    a = c.acc("V-H01", "Unresolved inputs have no value, are registered once, and have a missing-inputs entry")
    ui = {k for k, r in reg.items() if r["class"] == "UNRESOLVED"}
    a.ok(len(ui) >= 20, f"{len(ui)} unresolved inputs")
    for k in ui:
        a.ok(reg[k]["value"] == "" and reg[k]["bound_min"] == "" and reg[k]["bound_max"] == "", f"{k}: carries a value or bound")
    miss = {r["id"] for r in c.csv("missing_inputs_register.csv")}
    a.ok(ui == miss, f"register vs missing-inputs file: {sorted(ui ^ miss)}")
    a.ok(all(reg[k]["name"] for k in ui), "names")
    a.done("", "")

    a = c.acc("V-H02", "Calculations refuse unresolved inputs and invalid registrations")
    for fn, label in ((lambda: mod.P("UI-01"), "P(UI-01)"), (lambda: mod.relief_sizing(), "relief_sizing()")):
        try:
            fn()
            a.ok(False, f"{label} did not raise")
        except mod.MissingInputError:
            a.ok(True, "")
    try:
        mod.add("UI-TEST", "HP", "unresolved", "test", 5.0, "-", "UNRESOLVED", "x")
        a.ok(False, "an UNRESOLVED parameter with a value was accepted")
    except ValueError:
        a.ok(True, "")
    try:
        mod.P("NOT-A-PARAMETER")
        a.ok(False, "unknown key did not raise")
    except KeyError:
        a.ok(True, "")
    try:
        props.gas300(50.0)
        a.ok(False, "extrapolation was allowed")
    except ValueError:
        a.ok(True, "")
    a.done("MissingInputError, ValueError and KeyError are raised", "")

    a = c.acc("V-H03", "Outputs for unresolved quantities are blank or flagged, never numbers")
    heat = c.csv("cryogenic_heat_leak.csv")
    for sid in ("VESSEL", "ENDS"):
        r = next(x for x in heat if x["scenario"] == sid)
        a.ok(r["confidence"] == "NOT CALCULATED" and r["Q_total_W_m"] == "" and r["boil_L_h_m"] == "", f"{sid} row")
    for r in c.csv("boundary_conditions.csv"):
        if r["data_class"] == "UNRESOLVED":
            a.ok(r["p_MPa_g"] == "" and r["T_K"] == "", f"{r['station']} has a value")
    for r in c.csv("pressure_budget.csv"):
        if r["data_class"] == "UNRESOLVED":
            a.ok(r["dp_nom_kPa"] == "", f"{r['item_id']} has a value")
    a.done("", "")

    a = c.acc("V-H04", "Scope and claim guards: out-of-scope fluids only as exclusions; no compliance, certification or approval claims")
    neg = re.compile(r"\b(no|not|never|without|cannot|nor|neither|none)\b|exclud|out of scope|NOT", re.I)
    claims = re.compile(r"complies with|in compliance with|compliant with|meets the requirements|certified to|is approved|validated relief|is sized to|has been certified", re.I)
    scope = re.compile(r"liquid oxygen|\bLOX\b|liquid hydrogen|\bLH2\b|propellant|combustion", re.I)
    for p in list(c.ext.glob("*.md")) + list(c.ext.glob("*.csv")) + list(c.ext.glob("*.mmd")):
        if p.name in ("VALIDATION_REPORT.md", "verified_properties.csv"):
            continue
        for i, ln in enumerate(text(p).splitlines(), 1):
            if claims.search(ln):
                a.ok(bool(neg.search(ln)), f"{p.name}:{i}: possible claim '{claims.search(ln).group(0)}'")
            if scope.search(ln):
                a.ok(bool(neg.search(ln)) or "Out of scope" in ln, f"{p.name}:{i}: out-of-scope fluid mentioned as if in scope")
    for d in ("DESIGN_BASIS.md", "README.md"):
        a.ok(re.search(r"no compliance is claimed|does not claim compliance|No compliance is claimed", text(c.ext / d)) is not None, f"{d}: explicit no-compliance statement")
    a.done("", "")


# ======================================================================================
# I. determinism   J. hygiene   K. repository   L. documents
# ======================================================================================
def run_calc(ext, outdir, hashseed):
    env = dict(os.environ, PYTHONHASHSEED=str(hashseed))
    r = subprocess.run([sys.executable, "-I", str(Path(ext) / "calculations.py"), "--outdir", str(outdir)], capture_output=True, text=True, env=env, cwd=str(outdir))
    return r.returncode, r.stdout + r.stderr


def check_I(c):
    a = c.acc("V-I01", "Regeneration in clean directories is byte-identical to the committed outputs and to itself")
    with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
        rc1, o1 = run_calc(c.ext, t1, 0)
        a.ok(rc1 == 0, f"calculations.py failed: {o1[-200:]}")
        runs = [t1]
        if c.rerun_twice:
            rc2, o2 = run_calc(c.ext, t2, 12345)
            a.ok(rc2 == 0, "second run failed")
            runs.append(t2)
        if rc1 == 0:
            for name in OUTPUTS:
                h = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                a.ok((Path(t1) / name).exists() and h(Path(t1) / name) == h(c.ext / name), f"{name}: committed file differs from a fresh run")
                if c.rerun_twice and (Path(t2) / name).exists():
                    a.ok(h(Path(t1) / name) == h(Path(t2) / name), f"{name}: differs between runs with different hash seeds")
    a.done("13 files identical (SHA256 digest); two runs with different PYTHONHASHSEED", "")

    a = c.acc("V-I02", "verified_properties.csv covers every dataset of generate_verified_properties.py and nothing else")
    fetch = load_module(c.ext / "generate_verified_properties.py", "gen_mod2")
    have = {}
    for r in c.csv("verified_properties.csv"):
        have[r["dataset_id"]] = have.get(r["dataset_id"], 0) + 1
    a.ok(set(have) == set(fetch.DATASETS), f"datasets differ: {sorted(set(have) ^ set(fetch.DATASETS))}")
    a.ok(all(v >= 4 for v in have.values()), "a dataset has too few rows")
    for r in c.csv("verified_properties.csv"):
        a.ok(r["T_K"] != "" and r["p_MPa_abs"] != "", f"{r['dataset_id']}: empty T or p")
    a.done("", "")


def check_J(c):
    PATTERNS = [r"/ho" + r"me/", r"/ro" + r"ot/", r"/tm" + r"p/", r"claude-" + r"0", r"\bsk-[A-Za-z0-9]{10,}", r"(?i)api[_-]?key", r"(?i)password\s*[:=]",
                r"BEGIN (RSA|OPENSSH|PRIVATE)", r"gh[pousr]_[A-Za-z0-9]{20,}", r"[\w.+-]+@[\w-]+\.[\w.-]+", r"[A-Za-z]:\\\\Users", r"(?i)secret\s*[:=]"]
    a = c.acc("V-J01", "No private paths, secrets or e-mail addresses in any file of the folder")
    for p in sorted(c.ext.iterdir()):
        if p.is_dir() or p.suffix in (".png",) or p.name in ("validate_design.py",):
            continue
        t = text(p)
        for pat in PATTERNS:
            m = re.search(pat, t)
            a.ok(not m, f"{p.name}: matches '{pat}' ({m.group(0)[:30] if m else ''})")
    a.done("", "validate_design.py holds the patterns and is skipped")

    a = c.acc("V-J02", "Every document carries the status banner near its top")
    for d in DOCS:
        head = "\n".join(text(c.ext / d).splitlines()[:14])
        a.ok("NOT APPROVED FOR CONSTRUCTION" in head, f"{d}: banner missing near the top")
    a.done("", "")

    a = c.acc("V-J03", "Only expected file types; no standard, PDF or archive is stored")
    ok_ext = {".md", ".csv", ".py", ".mmd", ".svg", ".png", ".json"}
    for p in c.ext.iterdir():
        a.ok(p.is_file() and p.suffix in ok_ext, f"unexpected file or folder {p.name}")
    a.ok(max((len(text(c.ext / d).splitlines()) for d in DOCS)) < 400, "a document is suspiciously long (a pasted standard?)")
    a.done("", "")


def git(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


def check_K(c):
    repo = c.repo
    r = git(["rev-parse", "--is-inside-work-tree"], repo) if (repo / ".git").exists() else None
    if r is None or r.returncode != 0:
        for cid, d in (("V-K01", "Existing repository files are unchanged (only the root README link may change)"), ("V-K02", "The root README change is an added link only")):
            c.rec(cid, d, True, skip=True, note="not a git checkout (mutation copy or unpacked archive)")
        return
    base = next((b for b in ("origin/main", "main") if git(["rev-parse", "--verify", "-q", b], repo).returncode == 0), None)
    if base is None:
        for cid, d in (("V-K01", "Existing repository files are unchanged (only the root README link may change)"), ("V-K02", "The root README change is an added link only")):
            c.rec(cid, d, True, skip=True, note="no main branch to compare with")
        return
    a = c.acc("V-K01", "Existing repository files are unchanged (only the root README link may change)")
    d = git(["diff", "--name-status", base], repo).stdout.splitlines()
    new = git(["ls-files", "--others", "--exclude-standard"], repo).stdout.splitlines()
    for ln in d:
        st, path = ln.split("\t", 1)
        a.ok(path == "README.md" and st == "M" or (st == "A" and path.startswith("09_High_Pressure_Cryogenic_Systems/")), f"{st} {path}")
    for path in new:
        a.ok(path.startswith("09_High_Pressure_Cryogenic_Systems/"), f"untracked {path}")
    a.done(f"only README.md modified; new files only under 09_High_Pressure_Cryogenic_Systems/ (compared with {base})", "08_Fluid_Test_Rig_Design, the CFD, Mechanical, LS-DYNA, SQL, report and presentation files are unchanged")
    a = c.acc("V-K02", "The root README change is an added link only")
    dd = git(["diff", "-U0", base, "--", "README.md"], repo).stdout.splitlines()
    removed = [ln for ln in dd if ln.startswith("-") and not ln.startswith("---")]
    added = [ln for ln in dd if ln.startswith("+") and not ln.startswith("+++")]
    a.ok(not removed, f"{len(removed)} lines removed from README.md")
    a.ok(len(added) == 0 or any("09_High_Pressure_Cryogenic_Systems/README.md" in ln for ln in added), "the added text links to the new folder")
    a.ok(len(added) <= 6, f"{len(added)} lines added")
    a.done("", "")


def check_L(c):
    H = c_headlines(c)
    a = c.acc("V-L01", "Numbers quoted in the documents equal the calculated values")
    minimum = {"README.md": 10, "HIGH_PRESSURE_SYSTEM.md": 12, "CRYOGENIC_SYSTEM.md": 20, "HAZARD_REVIEW_HIGH_PRESSURE.md": 5, "HAZARD_REVIEW_CRYOGENIC.md": 10, "LIMITATIONS_AND_NEXT_STEPS.md": 3}
    for d in DOCS:
        t = text(c.ext / d)
        marks = re.findall(r"<!--h:(\w+)-->(.*?)<!--/h-->", t)
        a.ok(len(marks) >= minimum.get(d, 0), f"{d}: {len(marks)} marked numbers, at least {minimum.get(d, 0)} expected")
        for k, v in marks:
            a.ok(k in H and H[k] == v, f"{d}: {k} is {v} but the calculation gives {H.get(k)}")
        a.ok(t.count("<!--h:") == t.count("<!--/h-->"), f"{d}: unbalanced markers")
    a.done("each marked number equals the formatted headline value", "")


# ======================================================================================
# registry, runner, mutation tests, report
# ======================================================================================
CHECKS = [check_A, check_B, check_C, check_D, check_E, check_F, check_G, check_H, check_I, check_J, check_K, check_L]
ALL_IDS = ["V-A01", "V-A02", "V-A03", "V-A04", "V-A05", "V-A06", "V-B01", "V-B02", "V-B03", "V-B04", "V-B05", "V-B06", "V-B07", "V-B08", "V-B09",
           "V-C01", "V-C02", "V-C03", "V-C04", "V-C05", "V-C06", "V-C07", "V-D01", "V-D02", "V-E01", "V-E02", "V-E03", "V-E04", "V-E05", "V-E06", "V-E07",
           "V-E08", "V-E09", "V-E10", "V-F01", "V-F02", "V-F03", "V-F04", "V-G01", "V-G02", "V-H01", "V-H02", "V-H03", "V-H04", "V-I01", "V-I02",
           "V-J01", "V-J02", "V-J03", "V-K01", "V-K02", "V-L01"]


def run_checks(ext, repo, online=False, rerun_twice=True):
    c = Ctx(ext, repo, online, rerun_twice)
    c.registered_ids = set(ALL_IDS)
    for fn in CHECKS:
        try:
            fn(c)
        except Exception as e:                                           # a crash is a failed check, never a silent pass
            c.rec(f"V-{fn.__name__[-1]}XX", f"{fn.__name__} crashed", False, "no exception", f"{type(e).__name__}: {e}")
    missing = [i for i in ALL_IDS if i not in c.all_ids()]
    if missing:
        c.rec("V-ZZZ", "Every registered check ran", False, "all ran", f"not run: {missing}")
    return c.results


def mutate_replace(path, old, new, count=1):
    def f(ext, repo):
        p = Path(ext) / path if not str(path).startswith("@repo/") else Path(repo) / str(path)[6:]
        s = p.read_text(encoding="utf-8")
        assert old in s, f"mutation target not found in {path}: {old[:40]}"
        p.write_text(s.replace(old, new, count), encoding="utf-8")
    return f


def mutate_csv_cell(path, key_col, key, col, newval):
    def f(ext, repo):
        p = Path(ext) / path if not str(path).startswith("@repo/") else Path(repo) / str(path)[6:]
        rows = read_csv(p)
        hdr = list(rows[0].keys())
        hit = [r for r in rows if all(r[k] == v for k, v in zip(key_col, key))]
        assert hit, f"row not found in {path}: {key}"
        hit[0][col] = newval
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=hdr, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    return f


def mutate_delete_row(path, key_col, key):
    def f(ext, repo):
        p = Path(ext) / path
        rows = read_csv(p)
        hdr = list(rows[0].keys())
        rows2 = [r for r in rows if r[key_col] != key]
        assert len(rows2) == len(rows) - 1
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=hdr, lineterminator="\n")
            w.writeheader()
            w.writerows(rows2)
    return f


def master_mutation(ext, repo):
    p = Path(repo) / "05_Data" / "MASTER_PROJECT_DATA.csv"
    lines = p.read_text(encoding="utf-8").split("\n")
    i = next(k for k, ln in enumerate(lines) if ln.startswith("M002,"))
    parts = lines[i].split(",")
    assert parts[3] == "300"
    parts[3] = "310"
    lines[i] = ",".join(parts)
    p.write_text("\n".join(lines), encoding="utf-8")


def props_density_mutation(ext, repo):
    p = Path(ext) / "verified_properties.csv"
    rows = read_csv(p)
    hdr = list(rows[0].keys())
    hit = [r for r in rows if r["dataset_id"] == "N2_GAS_300K_ISOTHERM" and abs(float(r["p_MPa_abs"]) - 0.101325) < 1e-6]
    assert len(hit) == 1
    hit[0]["rho_kg_m3"] = f"{float(hit[0]['rho_kg_m3']) * 1.05:.7g}"
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=hdr, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


MUTATIONS = [
    ("Change the CFD inlet temperature M002 in the master register copy (300 K to 310 K)", master_mutation, ["V-A01"]),
    ("Raise the tabulated N2 density at 300 K and 1 atm by 5 percent", props_density_mutation, ["V-A04"]),
    ("Set the molar gas constant to 8.4", mutate_replace("verified_constants.csv", "VC-01,Molar gas constant,8.314462618", "VC-01,Molar gas constant,8.4"), ["V-A03"]),
    ("Corrupt a NIST expansion coefficient (a: -2.9554E2 to -2.7554E2)", mutate_replace("verified_constants.csv", "-2.9554E2", "-2.7554E2"), ["V-A05"]),
    ("Multiply one nominal budget loss (B19 delivery pipe friction) by 1.5 in pressure_budget.csv", mutate_csv_cell("pressure_budget.csv", ("item_id",), ("B19",), "dp_nom_kPa", "13.9"), ["V-C03", "V-I01"]),
    ("Multiply a thermal-contraction length change by 1.1", mutate_csv_cell("thermal_contraction.csv", ("material", "length_m"), ("SS304", "10"), "dL_mm", "31.95"), ["V-B01", "V-I01"]),
    ("Double the S1 nominal heat-leak total", mutate_csv_cell("cryogenic_heat_leak.csv", ("scenario", "case"), ("S1", "nom"), "Q_total_W_m", "0.37"), ["V-D02", "V-I01"]),
    ("Change the K of a bend in calculations.py without regenerating the outputs", mutate_replace("calculations.py", "(0.15, 0.30, 0.90)", "(0.15, 0.60, 0.90)"), ["V-I01"]),
    ("Delete the FLT-301 row from the equipment schedule", mutate_delete_row("equipment_schedule.csv", "tag", "FLT-301"), ["V-E02"]),
    ("Remove the banner from the cryogenic P&ID source", mutate_replace("PID_CRYOGENIC.mmd", "CONCEPTUAL — NOT APPROVED FOR CONSTRUCTION.", "DRAFT", 2), ["V-E04"]),
    ("Change a calculated temperature shown on the GN2 PFD label (271.7 K to 281.7 K)", mutate_replace("PFD_HIGH_PRESSURE.mmd", "1 MPa(g) (IL-04), 271.7 K (calc)", "1 MPa(g) (IL-04), 281.7 K (calc)"), ["V-E05"]),
    ("Put a value into the unresolved input UI-01", mutate_csv_cell("design_parameters.csv", ("param_id",), ("UI-01",), "value", "1.5"), ["V-H01"]),
    ("Remove an unresolved input from the missing-inputs register", mutate_delete_row("missing_inputs_register.csv", "id", "UI-27"), ["V-H01", "V-F03"]),
    ("Point a requirement at a verification check that does not exist", mutate_replace("REQUIREMENTS_TRACEABILITY.csv", "V-C03", "V-Z99"), ["V-F01"]),
    ("Use an unregistered assumption ID in a CSV", mutate_replace("pressure_budget.csv", "AS-02;AS-05", "AS-02;AS-99", 1), ["V-G01"]),
    ("Push an emissivity outside (0, 1]", mutate_csv_cell("design_parameters.csv", ("param_id",), ("AS-11-nom",), "value", "1.5"), ["V-D01"]),
    ("Edit a number quoted in a document", mutate_replace("CRYOGENIC_SYSTEM.md", "<!--h:T_sat_K-->77.355<!--/h-->", "<!--h:T_sat_K-->78.355<!--/h-->"), ["V-L01"]),
    ("Put a private path in a document", mutate_replace("LIMITATIONS_AND_NEXT_STEPS.md", "## 6. Reuse", "## 6. Reuse\n\nSee /ho" + "me/someone/notes.", 1), ["V-J01"]),
    ("Add a size and rating to an equipment schedule row", mutate_csv_cell("equipment_schedule.csv", ("tag",), ("PCV-301",), "rating_and_model", "DN25 PN400 model X"), ["V-E10"]),
    ("Add a compliance claim to a document", mutate_replace("HIGH_PRESSURE_SYSTEM.md", "## 7. Test and maintenance interfaces", "## 7. Test and maintenance interfaces\n\nThis design complies with ASME B31.3.", 1), ["V-H04"]),
]


def run_mutations(online=False):
    out = []
    keep = ("05_Data/MASTER_PROJECT_DATA.csv", "01_Project_Documentation/BASELINE_PARAMETERS.md", "08_Fluid_Test_Rig_Design/flow_basis.csv")
    for name, fn, expected in MUTATIONS:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            ext = repo / "09_High_Pressure_Cryogenic_Systems"
            shutil.copytree(HERE, ext, ignore=shutil.ignore_patterns("__pycache__", "VALIDATION_REPORT.md.tmp"))
            for rel in keep:
                (repo / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(HERE.parent / rel, repo / rel)
            try:
                fn(ext, repo)
                res = run_checks(ext, repo, False, rerun_twice=False)
                failed = sorted({r[0] for r in res if r[2] == "FAIL"})
                ok = all(e in failed for e in expected)
                out.append((name, expected, failed, ok, ""))
            except Exception as e:
                out.append((name, expected, [], False, f"{type(e).__name__}: {e}"))
    return out


def write_report(path, results, mutations, online):
    ids = {r[0]: r for r in results}
    by_group = {}
    for r in results:
        by_group.setdefault(r[0].split("-")[1][0], []).append(r)
    n = {s: sum(1 for r in results if r[2] == s) for s in ("PASS", "FAIL", "SKIP")}
    L = ["# Validation report", "",
         "**CONCEPTUAL — NOT APPROVED FOR CONSTRUCTION.** Result of `validate_design.py` on this folder. Generated: do not edit by hand. The report has no timestamps; re-running reproduces it.", "",
         f"Mode: {'offline checks plus online re-check of the verified data (`--online`)' if online else 'offline checks only (the online re-check V-A06 is skipped)'}. "
         f"{len(results)} checks: {n['PASS']} pass, {n['FAIL']} fail, {n['SKIP']} skipped. Mutation tests: {sum(1 for m in mutations if m[3])} of {len(mutations)} detected." if mutations is not None else "",
         "", "These checks validate the arithmetic, the data traceability and the internal consistency of the study. They do **not** validate pressure-vessel or piping integrity, relief-device sizing or code compliance, which this study does not attempt.", ""]
    for g in sorted(by_group):
        L += [f"## {GROUPS.get(g, "Checks that could not run")}", "", "| ID | Check | Result | Expected | Actual | Note |", "| --- | --- | --- | --- | --- | --- |"]
        for r in sorted(by_group[g]):
            esc = lambda s: str(s).replace("|", "/").replace("\n", " ")
            L.append(f"| {r[0]} | {esc(r[1])} | {r[2]} | {esc(r[3])} | {esc(r[4])} | {esc(r[5])} |")
        L.append("")
    if mutations is not None:
        L += ["## Mutation tests: do the checks fail when a source value or an important output is corrupted?", "",
              "Each test copies this folder and the three repository files it reads to a temporary directory, corrupts one thing on purpose, runs every check, and requires the listed checks to FAIL. Nothing in the real folder is touched.", "",
              "| # | Corruption | Must fail | Failed | Detected |", "| --- | --- | --- | --- | --- |"]
        for i, (name, exp, failed, ok, err) in enumerate(mutations, 1):
            L.append(f"| {i} | {name} | {', '.join(exp)} | {', '.join(failed) if failed else err} | {'YES' if ok else 'NO'} |")
        L.append("")
    skips = [r for r in results if r[2] == "SKIP"]
    L += ["## Tests not performed, and why", ""]
    if skips:
        for r in skips:
            L.append(f"- **{r[0]}** {r[1]}: {r[5]}.")
    L += ["- **Solver runs.** Fluent, Mechanical, LS-DYNA and the SQL import were not run, by design. No CFD or finite-element result is reused: the existing models cover air below 1 atm and Inconel 718 at 293 to 673 K only.",
          "- **Independent verification of the NIST values.** The data are checked for internal consistency (ideal-gas limit, Clapeyron relation, isotherm against isobars, monotonic isochores) and, with `--online`, against the live pages. They were not checked against a second independent equation of state or against measurements.",
          "- **Fit accuracy.** The NIST material fits carry their own stated errors (1 to 5 percent); no measured data were used.",
          "- **Validation against experiment or a real system.** None exists. The numbers are screening values for placeholder assumptions.",
          "- **Relief-device sizing, vessel and piping integrity, stress margins, two-phase and transient behaviour, plume dispersion.** Not calculated (`CALCULATION_METHOD.md` section 7); there is nothing to test.",
          "- **Standards compliance.** Not claimed, so not tested. The standards were read in part or only as listings (`DESIGN_BASIS.md` section 7).",
          "- **Python 3.9 to 3.12.** The code was written for Python 3.9 or later and run with Python 3.13 only; no other interpreter was available.",
          "- **Mermaid rendering from a clean machine.** The SVG and PNG files were rendered once with mermaid-cli 11.4.2; validation checks that they exist, carry the banner and show the current tags and numbers, but does not re-render them.", ""]
    Path(path).write_text("\n".join(x for x in L if x is not None) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--outdir", default=str(HERE))
    ap.add_argument("--online", action="store_true")
    ap.add_argument("--no-mutation", action="store_true")
    args = ap.parse_args()
    results = run_checks(HERE, HERE.parent, args.online, True)
    mutations = None if args.no_mutation else run_mutations()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    write_report(out / "VALIDATION_REPORT.md", results, mutations, args.online)
    fails = [r for r in results if r[2] == "FAIL"]
    for r in fails:
        print(f"FAIL {r[0]} {r[1]}\n     {r[4]}")
    bad = [m for m in (mutations or []) if not m[3]]
    for m in bad:
        print(f"MUTATION NOT DETECTED: {m[0]} (expected {m[1]}, failed {m[2]} {m[4]})")
    n = {s: sum(1 for r in results if r[2] == s) for s in ("PASS", "FAIL", "SKIP")}
    print(f"{len(results)} checks: {n['PASS']} pass, {n['FAIL']} fail, {n['SKIP']} skip; mutation tests detected: "
          f"{'not run' if mutations is None else f'{len(mutations) - len(bad)} of {len(mutations)}'}")
    return 1 if fails or bad else 0


if __name__ == "__main__":
    sys.exit(main())
