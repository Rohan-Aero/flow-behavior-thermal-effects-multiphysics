#!/usr/bin/env python3
"""Validation of the conceptual heated-duct test-rig design.

Standard library only. Read-only on the repository except for VALIDATION_REPORT.md, which it
rewrites (to --outdir, default this folder). The report has no timestamps, so it is reproducible.

    python validate_design.py                 # run all checks, rewrite VALIDATION_REPORT.md
    python validate_design.py --outdir DIR    # write the report somewhere else
    python validate_design.py --no-rerun      # skip the clean-directory reproduction (V-G01, V-G02)

Exit code 1 if any check fails. A failed check is investigated, never relaxed to pass.
Independent re-calculations here deliberately use different formulations from calculations.py
(Haaland instead of Colebrook-White, the ISO loss-coefficient form for the orifice, the momentum
balance for the expansion) so that a shared mistake is less likely.
"""
import argparse
import csv
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path

EXT = Path(__file__).resolve().parent
REPO = EXT.parent
REGISTER = REPO / "05_Data" / "MASTER_PROJECT_DATA.csv"

RESULTS = []      # (id, group, description, status, expected, actual, note)
REGISTERED = {}   # id -> description (every check id, for the traceability cross-check)


def rec(cid, group, desc, ok, expected="", actual="", note="", skip=False):
    status = "SKIP" if skip else ("PASS" if ok else "FAIL")
    RESULTS.append((cid, group, desc, status, str(expected), str(actual), note))
    REGISTERED[cid] = desc


def close(a, b, rel=1e-6, ab=1e-9):
    return abs(a - b) <= max(ab, rel * abs(b))


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def text(path):
    return Path(path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------------------
def load_calc():
    """Execute calculations.py from source. No import machinery, so no bytecode cache is read or written."""
    mod = types.ModuleType("calculations")
    mod.__file__ = str(EXT / "calculations.py")
    exec(compile(text(EXT / "calculations.py"), mod.__file__, "exec"), mod.__dict__)
    return mod


def read_register():
    with open(REGISTER, newline="", encoding="utf-8") as fh:
        fh.readline()                       # first line is a comment
        return {r["ID"]: r for r in csv.DictReader(fh)}


def first_float(s):
    m = re.search(r"[-+]?\d[\d,]*\.?\d*(?:[eE][-+]?\d+)?", s)
    return float(m.group(0).replace(",", "")) if m else None


# needle checks for inputs whose source is a file, not a register ID
NEEDLES = {
    "R_air": ("01_Project_Documentation/BASELINE_PARAMETERS.md", "287.058"),
    "gamma": ("01_Project_Documentation/BASELINE_PARAMETERS.md", "1.4"),
    "E_hot": ("01_Project_Documentation/BASELINE_PARAMETERS.md", "188.1"),
    "alpha": ("01_Project_Documentation/BASELINE_PARAMETERS.md", "13.72"),
    "cp_s": ("01_Project_Documentation/BASELINE_PARAMETERS.md", "481"),
    "Qv_frozen": ("01_Project_Documentation/BASELINE_PARAMETERS.md", "7.383"),
    "mdot_frozen": ("01_Project_Documentation/BASELINE_PARAMETERS.md", "8.686"),
    "T_solid_mean": ("02_CFD_Fluent/Baseline/CFD_BASELINE_RESULTS.md", "525.48"),
    "mdot_cfd": ("02_CFD_Fluent/Baseline/CFD_BASELINE_RESULTS.md", "8.662155"),
    "V_out_cfd": ("02_CFD_Fluent/Baseline/CFD_BASELINE_RESULTS.md", "28.894"),
    "dp_accel_cfd": ("02_CFD_Fluent/Baseline/CFD_BASELINE_RESULTS.md", "149.31"),
    "p0_in_cfd": ("02_CFD_Fluent/Audit/fluent_si_p0_area.txt", "759.77091"),
    "p0_out_cfd": ("02_CFD_Fluent/Audit/fluent_si_p0_area.txt", "425.1597"),
    "V_low": ("03_Thermal_Structural_Mechanical/Case_Matrix/PARAMETRIC_CASE_MATRIX.csv", "V01_LOW,inlet velocity,21.15"),
    "V_high": ("03_Thermal_Structural_Mechanical/Case_Matrix/PARAMETRIC_CASE_MATRIX.csv", "V03_HIGH,inlet velocity,25.85"),
    "Ma_in_frozen": ("01_Project_Documentation/FLUID_CALCULATIONS.md", "0.0677"),
    "q_in_frozen": ("01_Project_Documentation/FLUID_CALCULATIONS.md", "324.9"),
    "q_out_frozen": ("01_Project_Documentation/FLUID_CALCULATIONS.md", "399.5"),
}


def haaland(re_, rel):
    return (-1.8 * math.log10((rel / 3.7) ** 1.11 + 6.9 / re_)) ** -2


def check_group_a(calc, reg):
    # V-A01 register-sourced inputs equal the master data register
    bad, n = [], 0
    for name, (val, unit, src) in calc.INPUTS.items():
        if not re.fullmatch(r"M\d{3}", src):
            continue
        n += 1
        row = reg.get(src)
        if row is None:
            bad.append("%s: %s not in register" % (name, src))
            continue
        if src == "M005":
            ok = "101,325" in row["Value"] and val == 101325.0
        else:
            rv = first_float(row["Value"])
            if row["Units"].strip() == "mm" and unit == "m":
                rv *= 1e-3
            ok = rv is not None and close(val, rv, 1e-9)
        if not ok:
            bad.append("%s != %s (%s)" % (name, src, row["Value"][:30]))
    rec("V-A01", "Inputs", "Every input with a master-register ID equals the register value (%d inputs)" % n,
        not bad, "0 mismatches", "%d mismatches" % len(bad), "; ".join(bad))
    # V-A02 file-sourced inputs found in their source file
    bad, n = [], 0
    for name, (val, unit, src) in calc.INPUTS.items():
        if name in NEEDLES:
            n += 1
            f, needle = NEEDLES[name]
            p = REPO / f
            if not p.exists() or needle not in text(p):
                bad.append("%s: %r not in %s" % (name, needle, f))
    rec("V-A02", "Inputs", "Every file-sourced input appears in its cited source file (%d inputs)" % n, not bad,
        "0 missing", "%d missing" % len(bad), "; ".join(bad))
    # V-A03 every input is classified (register ID, or a needle, or the cited file) - no orphan
    orphan = [k for k, (v, u, s) in calc.INPUTS.items() if not re.fullmatch(r"M\d{3}", s) and k not in NEEDLES
              and not (REPO / s.split(" s")[0]).exists()]
    rec("V-A03", "Inputs", "Every input has a verifiable source (register ID, or a cited file that exists)",
        not orphan, "0 orphans", "%d" % len(orphan), ", ".join(orphan))
    # V-A04 instrument-index wall temperatures reproduce the CFD axial profile
    with open(REPO / "02_CFD_Fluent/Profiles/axial_profiles_cfd.csv", newline="", encoding="utf-8") as fh:
        fh.readline()
        prof = list(csv.DictReader(fh))
    two = {round(float(r["z"]), 6): float(r["Two"]) for r in prof}
    zs = sorted(two)
    z50 = two[min(zs, key=lambda z: abs(z - 0.05))]
    z300 = 0.5 * (two[min(zs, key=lambda z: abs(z - 0.29666667))] + two[min(zs, key=lambda z: abs(z - 0.30333333))])
    z550 = two[min(zs, key=lambda z: abs(z - 0.55))]
    ins = {r["tag"]: r for r in read_csv(EXT / "instrument_index.csv")}
    got = {"TE-111": z50, "TE-112": z300, "TE-113": z550}
    bad = []
    for tag, v in got.items():
        m = re.match(r"([\d.]+) K", ins[tag]["design_basis"])
        if not (m and abs(float(m.group(1)) - v) <= 0.06):
            bad.append("%s: %s vs %.2f" % (tag, ins[tag]["design_basis"][:12], v))
    rec("V-A04", "Inputs", "Wall-temperature expectations for TE-111/112/113 reproduce the CFD axial profile",
        not bad, "within 0.06 K", "%.2f / %.2f / %.2f K" % (z50, z300, z550), "; ".join(bad))


def check_group_b(calc, res):
    # V-B01 independent volumetric flow, written out without the script's helpers
    Q = 23.5 * math.pi * (20.0 / 1000.0) ** 2 / 4.0
    ok = close(res["flow.Qv"], Q, 1e-9) and abs(Q * 1e3 - 7.38) / 7.38 < 1e-3
    rec("V-B01", "Flow", "Volumetric flow reproduced independently and matches the quoted 7.38 L/s",
        ok, "%.5f L/s" % (Q * 1e3), "%.5f L/s" % (res["flow.Qv"] * 1e3))
    # V-B02 independent mass flow
    rho = 101325.0 / (287.058 * 300.0)
    md = rho * Q
    rec("V-B02", "Flow", "Mass flow reproduced independently (rho = p/(R T))", close(res["flow.mdot"], md, 1e-9),
        "%.6f g/s" % (md * 1e3), "%.6f g/s" % (res["flow.mdot"] * 1e3))
    # V-B03 continuity: same mass flow at inlet and outlet of the test article
    rho_out = 101325.0 / (287.058 * 368.93)
    A = math.pi * 0.02 ** 2 / 4
    v_out = md / (rho_out * A)
    c1 = close(rho_out * v_out * A, rho * 23.5 * A, 1e-12)
    c2 = close(res["flow.V_out"], v_out, 1e-6)
    c3 = close(res["ta.1.V_out"], v_out, 1e-6)
    rec("V-B03", "Flow", "Flow continuity: rho_in V_in A = rho_out V_out A, with V_out matching the script",
        c1 and c2 and c3, "V_out %.4f m/s" % v_out, "%.4f / %.4f" % (res["flow.V_out"], res["ta.1.V_out"]))
    # V-B04 Reynolds number and velocity are sensible and close to the CFD
    re_in = res["flow.Re_in"]
    ok = 1e4 < re_in < 1e5 and abs(re_in / 29958 - 1) < 2e-3 and res["flow.Ma_in"] < 0.1 and res["flow.Ma_out"] < 0.1
    rec("V-B04", "Flow", "Reynolds number is turbulent and within 0.2 % of the CFD; Mach numbers below 0.1",
        ok, "29958 (CFD), Ma < 0.1", "Re %.0f, Ma %.4f / %.4f" % (re_in, res["flow.Ma_in"], res["flow.Ma_out"]))
    # V-B05 cross-check table all PASS
    rows = read_csv(EXT / "flow_basis.csv")
    notes = [r["quantity"] for r in rows if r["status"] != "PASS"]
    rec("V-B05", "Flow", "All %d flow cross-checks against the CFD and frozen baseline are within tolerance" % len(rows),
        not notes, "0 outside tolerance", "%d" % len(notes), ", ".join(notes))
    # V-B06 heating acceleration reproduced from the momentum balance without the script's helper
    G = md / A
    acc = G * G * (1 / rho_out - 1 / rho)
    rec("V-B06", "Flow", "Heating acceleration term G^2(1/rho_out - 1/rho_in) reproduced and within 1 % of the CFD value",
        close(acc, res["flow.dp_accel"], 1e-9) and abs(acc / 149.31 - 1) < 1e-2, "149.31 Pa (CFD)", "%.3f Pa" % acc)
    # V-B07 flow envelope factors are exactly the CFD velocity cases
    f_lo, f_hi = res["input.V_low"] / res["input.V_in"], res["input.V_high"] / res["input.V_in"]
    ok = abs(f_lo - 0.9) < 1e-9 and abs(f_hi - 1.1) < 1e-9 and abs(res["ta.0.f"] - 0.9) < 1e-9 and abs(res["ta.2.f"] - 1.1) < 1e-9
    rec("V-B07", "Flow", "The 0.9 and 1.1 flow factors of the duty envelope are the CFD velocity cases (21.15 and 25.85 m/s)",
        ok, "0.9 / 1.1", "%.6f / %.6f" % (f_lo, f_hi))
    # V-B08 free growth estimate against Mechanical LC1
    ok = abs(res["interface.free_growth_diff_pct"]) < 1.0
    rec("V-B08", "Interface", "Simple free-growth estimate agrees with the Mechanical LC1 free growth (M085) within 1 %",
        ok, "within 1 %", "%.2f %%" % res["interface.free_growth_diff_pct"])
    # V-B09 full-restraint force estimate against the LC2 reaction
    ok = abs(res["interface.F_full_diff_pct"]) < 1.0
    rec("V-B09", "Interface", "E A alpha dT estimate of the full-restraint force agrees with the LC2 reaction (M091) within 1 %",
        ok, "within 1 %", "%.2f %%" % res["interface.F_full_diff_pct"])


def budget_rows():
    return read_csv(EXT / "pressure_drop_budget.csv")


def check_group_c(calc, res, reg):
    rows = budget_rows()
    cands = sorted({r["candidate_bore_mm"] for r in rows}, key=float)
    # V-C01 sums
    bad = []
    for c in cands:
        items = [r for r in rows if r["candidate_bore_mm"] == c and r["item_id"] != "TOTAL"]
        tot = [r for r in rows if r["candidate_bore_mm"] == c and r["item_id"] == "TOTAL"][0]
        for k in ("low", "nom", "high"):
            s = sum(float(r["dp_%s_Pa" % k]) for r in items)
            if abs(s - float(tot["dp_%s_Pa" % k])) > 0.011 * len(items) ** 0.5 + 0.02:
                bad.append("%s mm %s: %.2f vs %s" % (c, k, s, tot["dp_%s_Pa" % k]))
    rec("V-C01", "Budget", "Budget rows sum to the TOTAL row for every candidate and every case (low, nominal, high)",
        not bad, "sums agree to rounding", "%d disagreements" % len(bad), "; ".join(bad))
    # V-C02 ordering
    bad = [r["item_id"] + "@" + r["candidate_bore_mm"] for r in rows if r["item_id"] != "TOTAL"
           and not (float(r["dp_low_Pa"]) <= float(r["dp_nom_Pa"]) + 1e-9 <= float(r["dp_high_Pa"]) + 2e-9)]
    rec("V-C02", "Budget", "low <= nominal <= high for every budget row", not bad, "0 violations", "%d" % len(bad), ", ".join(bad))
    # V-C03 candidate summary equals budget; group columns add up
    cl = read_csv(EXT / "candidate_line_sizes.csv")
    bad = []
    for r in cl:
        tot = [x for x in rows if x["candidate_bore_mm"] == r["line_bore_mm"] and x["item_id"] == "TOTAL"][0]
        for k in ("low", "nom", "high"):
            if abs(float(r["total_%s_Pa" % k]) - float(tot["dp_%s_Pa" % k])) > 0.011:
                bad.append("%s %s total" % (r["line_bore_mm"], k))
        parts = sum(float(r[k]) for k in ("friction_Pa", "fittings_Pa", "filter_Pa", "flow_element_Pa", "isolation_valve_Pa",
                                           "adapters_Pa", "test_article_Pa", "discharge_Pa"))
        if abs(parts - float(r["total_nom_Pa"])) > 0.05:
            bad.append("%s groups %.2f vs %s" % (r["line_bore_mm"], parts, r["total_nom_Pa"]))
    rec("V-C03", "Budget", "Candidate summary totals equal the budget and its group columns add up to the nominal total",
        not bad, "0 disagreements", "%d" % len(bad), "; ".join(bad))
    # V-C04 station closure
    st = {r["station"]: r for r in read_csv(EXT / "stream_table.csv")}
    p = lambda s: float(st[s]["p_static_gauge_Pa"])
    p0 = lambda s: float(st[s]["P0_gauge_Pa"])
    ftp = float(st["S4"]["P0_gauge_Pa"]) - float(st["S3"]["P0_gauge_Pa"])
    items = [r for r in rows if r["candidate_bore_mm"] == "50" and r["item_id"] != "TOTAL"]
    total50 = sum(float(r["dp_nom_Pa"]) for r in items)
    ok = (abs(p("S10") - p("S11") - 438.13) < 0.011 and abs(p("S14")) < 0.011 and abs(ftp - total50) < 0.05
          and abs(p0("S14") - float([r for r in items if r["item_id"] == "B21"][0]["dp_nom_Pa"])) < 0.011)
    rec("V-C04", "Budget", "Stream-table closure: test-article static drop = 438.13 Pa, exit static = 0, blower rise = sum of losses",
        ok, "438.13 / 0 / %.2f" % total50, "%.2f / %.2f / %.2f" % (p("S10") - p("S11"), p("S14"), ftp))
    # V-C05 test-article row: reproduced from the register without the script, counted once
    r = reg
    dp_s = first_float(r["M036"]["Value"]); V = first_float(r["M003"]["Value"]); T = first_float(r["M037"]["Value"])
    rho_i = 101325.0 / (287.058 * 300.0); rho_o = 101325.0 / (287.058 * T)
    loss = dp_s + 0.5 * rho_i * V * V - 0.5 * rho_o * (V * rho_i / rho_o) ** 2
    ta = [x for x in rows if x["tag"] == "TA-101" and x["candidate_bore_mm"] == "50"]
    cfd_rows = [x for x in rows if x["in_cfd_domain"] == "YES" and x["candidate_bore_mm"] == "50"]
    area_p0 = 759.77091 - 425.1597
    ok = (len(ta) == 1 and len(cfd_rows) == 1 and abs(float(ta[0]["dp_nom_Pa"]) - loss) < 0.011
          and area_p0 < loss < dp_s)
    rec("V-C05", "Budget", "CFD test-article drop appears exactly once, converted to total pressure, bracketed by CFD p0 loss and static drop",
        ok, "%.2f Pa in (%.2f, %.2f)" % (loss, area_p0, dp_s), ta[0]["dp_nom_Pa"] if ta else "none")
    # V-C06 friction rows reproduced with Haaland from the row's own Re, L and reference pressure
    bad, n = [], 0
    for x in rows:
        if x["item_id"] == "TOTAL" or not x["method"].startswith("Darcy"):
            continue
        n += 1
        D = 0.020 if x["item_id"] in ("B14", "B16") else float(x["candidate_bore_mm"]) * 1e-3
        m = re.match(r"f=([\d.]+); L=([\d.]+) m; Re=(\d+)", x["parameter"])
        f_c, L, Re = float(m.group(1)), float(m.group(2)), float(m.group(3))
        f_h = haaland(Re, 4.5e-5 / D)
        dp_h = f_h * L / D * float(x["q_ref_Pa"])
        if abs(f_h / f_c - 1) > 0.04 or abs(dp_h / float(x["dp_nom_Pa"]) - 1) > 0.05:
            bad.append("%s@%s: f %.5f vs %.5f" % (x["item_id"], x["candidate_bore_mm"], f_c, f_h))
    rec("V-C06", "Budget", "Friction rows (%d) reproduced with the Haaland equation within 4 %% in f and 5 %% in dp" % n,
        not bad, "0 outside", "%d" % len(bad), "; ".join(bad[:4]))
    # V-C06b line-list lengths equal the lengths in the budget (concept bore)
    ll = {x["line_id"]: x for x in read_csv(EXT / "line_list.csv")}
    byline = {}
    for x in items:
        if x["method"].startswith("Darcy"):
            m = re.match(r"f=([\d.]+); L=([\d.]+) m", x["parameter"])
            byline[x["line_id"]] = byline.get(x["line_id"], 0.0) + float(m.group(2))
    bad = [l for l, L in byline.items() if abs(L - float(ll[l]["length_m_assumed"])) > 1e-6]
    rec("V-C06b", "Budget", "Pipe lengths in line_list.csv equal the lengths used by the friction rows (line-loss aggregation)",
        not bad, "all lines agree", "%d disagree" % len(bad), ", ".join(bad))
    # V-C07 orifice: round trip and ISO loss-coefficient form
    rho = 101325.0 / (287.058 * 300.0)
    md = res["flow.mdot"]
    bad = []
    for c in cands:
        beta, dps, ppl = res["cand.%s.beta" % c], res["cand.%s.orifice_signal" % c], res["cand.%s.orifice_ppl" % c]
        D = float(c) * 1e-3
        Ad = math.pi * (beta * D) ** 2 / 4
        md2 = 0.60 * Ad * math.sqrt(2 * rho * dps / (1 - beta ** 4))
        s = math.sqrt(1 - beta ** 4 * (1 - 0.6 ** 2))
        xi = (s / (0.6 * beta ** 2) - 1) ** 2
        v = md / (rho * math.pi * D * D / 4)
        ppl2 = xi * 0.5 * rho * v * v
        if not (close(md2, md, 1e-6) and close(ppl2, ppl, 1e-6)):
            bad.append("%s mm: %.6g/%.6g, %.4g/%.4g" % (c, md2, md, ppl2, ppl))
    rec("V-C07", "Budget", "Orifice sizing round-trips to the design mass flow; permanent loss matches the ISO loss-coefficient form",
        not bad, "agree to 1e-6", "%d disagree" % len(bad), "; ".join(bad))
    # V-C08 expansion: Borda-Carnot loss and the momentum static rise
    rho_h = 101325.0 / (287.058 * 368.93)
    V1 = md / (rho_h * math.pi * 0.02 ** 2 / 4)
    V2 = md / (rho_h * math.pi * 0.05 ** 2 / 4)
    loss_bc = 0.5 * rho_h * (V1 - V2) ** 2
    rise = rho_h * V2 * (V1 - V2)
    b17 = float([x for x in rows if x["candidate_bore_mm"] == "50" and x["item_id"] == "B17"][0]["dp_nom_Pa"])
    st_rise = p("S13") - p("S12")
    ok = abs(loss_bc - b17) < 0.011 and abs(rise - st_rise) < 0.021
    rec("V-C08", "Budget", "Expansion loss equals 0.5 rho (V1 - V2)^2 and the static rise across it equals rho V2 (V1 - V2)",
        ok, "%.2f Pa loss, %.2f Pa rise" % (loss_bc, rise), "%.2f / %.2f" % (b17, st_rise))
    # V-C09 sensitivity
    sens = read_csv(EXT / "pressure_budget_sensitivity.csv")
    g = [x for x in sens if x["kind"] == "GLOBAL"]
    deltas = [float(x["delta_high_Pa"]) for x in g]
    nom_tot = res["cand.50.FTP_nom"]
    ok = (len(g) == 6 and deltas == sorted(deltas) and any(abs(d) < 1e-9 for d in deltas)
          and abs(float(g[0]["dp_nom_Pa"]) - nom_tot) < 0.011)
    unsupported = sum(float(x["dp_nom_Pa"]) for x in items if x["data_class"] in ("ASSUMED_GENERIC", "ALLOCATION"))
    ok = ok and abs(float(g[-1]["delta_high_Pa"]) - 2 * unsupported) < 0.1
    rec("V-C09", "Budget", "Sensitivity table: multiplier scan is monotonic, x1 gives zero change and x3 adds twice the unsupported share",
        ok, "x3 adds %.2f Pa" % (2 * unsupported), g[-1]["delta_high_Pa"])
    # V-C10 duty envelope
    spec_p = res["duty.UPPER_WARM.FTP_high"] / 0.81
    spec_q = res["duty.UPPER_WARM.Q_suction_L_s"] / 0.9
    ok = (close(res["duty.spec.FTP_min_full_speed_Pa"], spec_p, 1e-6) and close(res["duty.spec.Q_min_full_speed_L_s"], spec_q, 1e-6)
          and abs(res["duty.DESIGN.FTP_nom"] - total50) < 0.05)
    rec("V-C10", "Duty", "Blower specification follows the affinity laws (Q/0.9, P/0.81) from the upper warm-ambient high-loss point",
        ok, "%.0f Pa, %.2f L/s" % (spec_p, spec_q),
        "%.0f Pa, %.2f L/s" % (res["duty.spec.FTP_min_full_speed_Pa"], res["duty.spec.Q_min_full_speed_L_s"]))
    # V-C11 screening and recommendation
    ok_list = [c for c in cands if res["cand.%s.screen_ok" % c]]
    iso_ok = all((float(r["line_bore_mm"]) >= 50) == (r["orifice_iso5167_2_scope"] == "yes") for r in cl)
    best = min(ok_list, key=lambda c: res["cand.%s.FTP_nom" % c])
    rec("V-C11", "Duty", "The recommended 50 mm bore has the lowest nominal fan pressure of the candidates that pass the screening",
        best == "50" and res["recommended_bore_mm"] == 50 and iso_ok,
        "50 mm", "%s mm (passing: %s)" % (best, ", ".join(ok_list)))
    # V-C12 candidate velocity and Reynolds number
    mu = 1.716e-5 * (300 / 273.15) ** 1.5 * (273.15 + 110.4) / (300 + 110.4)
    bad = []
    for c in cands:
        D = float(c) * 1e-3
        V = md / (rho * math.pi * D * D / 4)
        Re = 4 * md / (math.pi * D * mu)
        if not (close(V, res["cand.%s.v_cold" % c], 1e-6) and close(Re, res["cand.%s.re_cold" % c], 1e-6)):
            bad.append(c)
    rec("V-C12", "Duty", "Candidate line velocities and Reynolds numbers reproduced independently",
        not bad, "agree to 1e-6", "%d disagree" % len(bad), ", ".join(bad))
    # V-C13 unsupported-data detection
    bad = []
    for x in rows:
        if x["item_id"] == "TOTAL":
            continue
        c, b, a = x["data_class"], x["component_data_basis"], x["assumption_ids"]
        if c in ("ASSUMED_GENERIC", "ALLOCATION"):
            if b == "NONE_REQUIRED" or not a:
                bad.append("%s@%s" % (x["item_id"], x["candidate_bore_mm"]))
        elif c in ("CALC", "CFD_DERIVED"):
            if b != "NONE_REQUIRED" or not a:
                bad.append("%s@%s" % (x["item_id"], x["candidate_bore_mm"]))
        else:
            bad.append("%s@%s class %r" % (x["item_id"], x["candidate_bore_mm"], c))
    share = res["cand.50.unsupported_share"]
    rec("V-C13", "Budget", "Every row relying on generic or vendor-dependent data is flagged with an assumption ID (%.1f %% of the 50 mm nominal budget)" % (100 * share),
        not bad, "all rows classified", "%d unclassified" % len(bad), ", ".join(bad[:4]))


def tags_in(path):
    t = []
    for line in text(path).splitlines():
        s = line.strip()
        if s.startswith("%%") or s.startswith("title:") or s == "---":
            continue
        t.append(s)
    body = "\n".join(t)
    eq = set(re.findall(r"\b[A-Z]{2,5}-\d{3}\b|\bIF-\d\b", body))
    lines = set(re.findall(r"\bL-\d{3}\b", body))
    return eq, lines, body


def check_group_d(calc, res):
    eq = read_csv(EXT / "equipment_schedule.csv")
    ins = read_csv(EXT / "instrument_index.csv")
    ll = read_csv(EXT / "line_list.csv")
    et = [r["tag"] for r in eq]; it = [r["tag"] for r in ins]; lt = [r["line_id"] for r in ll]
    pat = re.compile(r"[A-Z]{2,5}-\d{3}|IF-\d")
    bad = [t for t in et + it if not pat.fullmatch(t)] + [l for l in lt if not re.fullmatch(r"L-\d{3}", l)]
    rec("V-D01", "Tags", "All equipment, instrument and line tags follow the documented tag syntax", not bad, "0 violations", "%d" % len(bad), ", ".join(bad))
    dup = sorted({t for t in et + it if (et + it).count(t) > 1} | {l for l in lt if lt.count(l) > 1})
    rec("V-D02", "Tags", "Tags are unique across the equipment schedule and instrument index; line IDs are unique", not dup, "0 duplicates", "%d" % len(dup), ", ".join(dup))
    known = set(et) | set(it) | set(lt)
    refs = []
    for r in ll:
        for k in ("from_tag", "to_tag", "inline_items"):
            refs += re.findall(r"[A-Z]{2,5}-\d{3}|IF-\d", r[k])
    for r in eq:
        refs += re.findall(r"L-\d{3}", r["lines"])
    for r in ins:
        refs += re.findall(r"L-\d{3}", r["line_id"]) + re.findall(r"[A-Z]{2,5}-\d{3}|IF-\d", r["location_tag"] + " " + r["signal_destination"])
    for r in budget_rows():
        if r["item_id"] != "TOTAL":
            refs += [r["tag"]] if pat.fullmatch(r["tag"]) or re.fullmatch(r"L-\d{3}", r["tag"]) else []
            refs += [r["line_id"]] if r["line_id"] not in ("", "-") else []
    miss = sorted({x for x in refs if x not in known})
    rec("V-D03", "Tags", "Every tag referenced by the line list, schedules and budget exists in a schedule", not miss, "0 unknown", "%d" % len(miss), ", ".join(miss))
    # V-D04 diagrams vs schedules
    flags = {}
    for r in eq:
        flags[r["tag"]] = (r["shown_on_pfd"] == "YES", r["shown_on_pid"] == "YES")
    for r in ins:
        flags[r["tag"]] = (r["shown_on_pfd"] == "YES", r["shown_on_pid"] == "YES")
    pfd_eq, pfd_lines, pfd_body = tags_in(EXT / "PFD.mmd")
    pid_eq, pid_lines, pid_body = tags_in(EXT / "PID.mmd")
    exp_pfd = {t for t, f in flags.items() if f[0]}
    exp_pid = {t for t, f in flags.items() if f[1]}
    exp_lines = {r["line_id"] for r in ll if r["shown_on_pid"] == "YES"}
    d1, d2, d3 = pfd_eq ^ exp_pfd, pid_eq ^ exp_pid, pid_lines ^ exp_lines
    rec("V-D04", "Diagrams", "PFD and P&ID tags and line IDs match the schedules and line list exactly (both directions)",
        not (d1 or d2 or d3), "no differences", "PFD %s; P&ID %s; lines %s" % (sorted(d1), sorted(d2), sorted(d3)))
    # V-D05 PFD stream labels equal the stream table
    st = {r["station"]: r for r in read_csv(EXT / "stream_table.csv")}
    labels = re.findall(r"(S\d+): ([\d.]+) K, (-?\d+) Pa\(g\), ([\d.]+) g/s", pfd_body)
    bad = []
    for s, T, P, m in labels:
        r = st.get(s)
        if r is None or abs(float(T) - float(r["T_K"])) > 0.06 or abs(int(P) - float(r["p_static_gauge_Pa"])) > 0.51 or abs(float(m) - float(r["mdot_g_s"])) > 0.006:
            bad.append(s)
    rec("V-D05", "Diagrams", "PFD stream labels (%d) equal the stream table (T, static gauge pressure, mass flow)" % len(labels),
        labels and not bad, "all labels agree", "%d disagree" % len(bad), ", ".join(bad))
    # V-D06 PFD heat input equals the CFD heat transfer
    ok = "602.755 W" in pfd_body and calc.INPUTS["Q_heat_cfd"][0] == 602.755
    rec("V-D06", "Diagrams", "The heat input quoted on the PFD equals the CFD heat transfer (M038)", ok, "602.755 W", "present" if ok else "missing")
    # V-D07 conceptual labelling and no sizes or ratings on the P&ID
    t1 = text(EXT / "PFD.mmd"); t2 = text(EXT / "PID.mmd")
    lab = ("CONCEPTUAL" in t1 and "CONCEPTUAL" in t2 and "NOT APPROVED FOR CONSTRUCTION" in t2.upper().replace("NOT APPROVED", "NOT APPROVED")
           and "not approved for construction" in t1.lower())
    nodes_only = "\n".join(l for l in t2.splitlines() if not l.strip().startswith("%%"))
    rating = re.findall(r"\b\d+(?:\.\d+)?\s?(?:mm|in|inch|bar|psi|kPa|MPa|DN|NPS|PN|barg)\b|\bclass\s?\d+|\bDN\s?\d+", nodes_only)
    rec("V-D07", "Diagrams", "Diagrams are labelled conceptual and not approved for construction; the P&ID carries no sizes or ratings",
        lab and not rating, "labelled, 0 sizes", "labelled=%s, sizes=%s" % (lab, rating[:3]))
    # V-D08 rendered exports exist, are text SVG, contain every tag
    bad = []
    for n, tags in (("PFD", pfd_eq | pfd_lines), ("PID", pid_eq | pid_lines)):
        svg = EXT / (n + ".svg"); png = EXT / (n + ".png")
        if not svg.exists() or not png.exists():
            bad.append(n + " missing"); continue
        s = text(svg)
        if "foreignObject" in s:
            bad.append(n + ".svg uses foreignObject")
        flat = re.sub(r"<[^>]+>", " ", s)
        miss = sorted(t for t in tags if t not in flat)
        if miss:
            bad.append("%s.svg lacks %s" % (n, miss[:3]))
        if png.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            bad.append(n + ".png is not a PNG")
    rec("V-D08", "Diagrams", "Rendered SVG and PNG exports exist, the SVGs are plain text and contain every tag of their .mmd source",
        not bad, "4 exports valid", "%d problems" % len(bad), "; ".join(bad))
    # V-D09 calc_check pairs agree with the calculation results
    bad, n = [], 0
    for r in eq + ins:
        for pair in filter(None, r.get("calc_check", "").split(";")):
            n += 1
            k, v = pair.split("=")
            if k not in res:
                bad.append("%s: no key %s" % (r["tag"], k)); continue
            v = float(v); a = res[k]
            if not (abs(a - v) <= 0.005 * abs(a) or abs(a - v) < 0.011):
                bad.append("%s: %s=%s vs %.6g" % (r["tag"], k, v, a))
    rec("V-D09", "Tags", "Numbers quoted in the equipment schedule and instrument index (%d) agree with the calculation results" % n,
        not bad, "within 0.5 %", "%d disagree" % len(bad), "; ".join(bad[:4]))
    # V-D10 line-list pressures equal the stream table
    bad = []
    for r in ll:
        if r["station_in"]:
            for sk, pk in (("station_in", "p_in_static_gauge_Pa"), ("station_out", "p_out_static_gauge_Pa")):
                if abs(float(r[pk]) - float(st[r[sk]]["p_static_gauge_Pa"])) > 0.011:
                    bad.append("%s %s" % (r["line_id"], sk))
    rec("V-D10", "Tags", "Line-list pressures equal the stream-table station values", not bad, "0 disagreements", "%d" % len(bad), ", ".join(bad))
    # V-D11 assumptions register
    db = text(EXT / "DESIGN_BASIS.md")
    registered = set(re.findall(r"^\| (AS-\d{2}) \|", db, flags=re.M))
    used = set()
    for f in ("calculations.py", "pressure_drop_budget.csv", "equipment_schedule.csv", "instrument_index.csv", "line_list.csv",
              "thermal_structural_interface.csv", "REQUIREMENTS_TRACEABILITY.csv", "SYSTEM_DESCRIPTION.md", "CALCULATION_METHOD.md"):
        used |= set(re.findall(r"AS-\d{2}", text(EXT / f)))
    miss, orphan = sorted(used - registered), sorted(registered - used)
    rec("V-D11", "Assumptions", "Every assumption ID used is registered in DESIGN_BASIS.md s.5 and every registered one is used (%d IDs)" % len(registered),
        registered and not miss and not orphan, "0 unregistered, 0 unused", "unregistered %s, unused %s" % (miss, orphan))
    # V-D12 no throttling or control valve; nothing in the discharge path
    valve_tags = [t for t in et + it if re.match(r"(FCV|CV|PCV|TCV|XV|HCV|FV)-", t)]
    inline107 = [x for x in re.findall(r"[A-Z]{2,5}-\d{3}", [r for r in ll if r["line_id"] == "L-107"][0]["inline_items"])]
    disch = [t for t in inline107 + ["STK-101"] if re.match(r"(HV|CV|XV|FCV|PSV)-", t)]
    valves_in_pid = re.findall(r"\{\{\"([A-Z]+-\d{3})", pid_body)
    ok = not valve_tags and not disch and valves_in_pid == ["HV-101"]
    rec("V-D12", "Tags", "No control or throttling valve exists, nothing valve-like is in the discharge line, and HV-101 is the only valve on the P&ID",
        ok, "none; HV-101 only", "control valves %s; discharge %s; P&ID valves %s" % (valve_tags, disch, valves_in_pid))


def check_interlocks():
    pid = text(EXT / "PID.mmd")
    ins = {r["tag"]: r for r in read_csv(EXT / "instrument_index.csv")}
    need = ["ZSO101 ==>", "PT101 ==>", "PDSL102 ==>", "TSHH120 ==>", "HS101 ==>"]
    missing = [n for n in need if not re.search(r"^\s*" + re.escape(n) + r".*ES101", pid, flags=re.M)]
    acts = [a for a in ("ES101 ==>|\"stop\"| VFD101", "ES101 ==>|\"heater power off\"| HPWR") if a not in pid]
    # independence: the safety inputs go only to ES-101, and the over-temperature sensor is not a control-system thermocouple
    dest = {t: ins[t]["signal_destination"] for t in ("ZSO-101", "PDSL-102", "TSHH-120", "HS-101")}
    notonly = [t for t, d in dest.items() if d.strip() != "ES-101"]
    shared = ins["TE-120"]["signal_destination"].strip() != "TSHH-120"
    ok = not (missing or acts or notonly or shared)
    rec("V-D13", "Diagrams", "Hardwired trips: ZSO-101, PT-101, PDSL-102, TSHH-120 and HS-101 act on ES-101, ES-101 acts on the drive and heater power, and the independent safety inputs go to ES-101 only",
        ok, "wired as above", "missing %s; actions %s; not ES-101 only %s; TE-120 shared %s" % (missing, acts, notonly, shared))


def check_group_e(calc):
    rq = read_csv(EXT / "REQUIREMENTS_TRACEABILITY.csv")
    reg = read_register()
    eq = {r["tag"] for r in read_csv(EXT / "equipment_schedule.csv")} | {r["tag"] for r in read_csv(EXT / "instrument_index.csv")}
    eq |= {r["line_id"] for r in read_csv(EXT / "line_list.csv")}
    allowed_t = {"PROPOSED REQUIREMENT", "DERIVED CONSTRAINT", "DESIGN DECISION", "SCOPE LIMIT", "DOCUMENTATION REQUIREMENT"}
    bad = []
    ids = [r["req_id"] for r in rq]
    if len(ids) != len(set(ids)):
        bad.append("duplicate req_id")
    for r in rq:
        for k in ("category", "requirement", "type", "source_basis", "implemented_in", "status"):
            if not r[k].strip():
                bad.append("%s empty %s" % (r["req_id"], k))
        if r["type"] not in allowed_t:
            bad.append("%s type" % r["req_id"])
        if not (r["status"].startswith("MET IN CONCEPT") or r["status"].startswith("OPEN")):
            bad.append("%s status" % r["req_id"])
        if r["type"] == "PROPOSED REQUIREMENT" and not r["verification"].strip() and not r["status"].startswith("OPEN"):
            bad.append("%s unverified yet not OPEN" % r["req_id"])
    rec("V-E01", "Traceability", "Requirements (%d) have unique IDs, complete fields, valid types and honest status" % len(rq),
        not bad, "0 problems", "%d" % len(bad), "; ".join(bad[:4]))
    bad = []
    asids = set(re.findall(r"^\| (AS-\d{2}) \|", text(EXT / "DESIGN_BASIS.md"), flags=re.M))
    for r in rq:
        for m in re.findall(r"\bM\d{3}\b", r["source_basis"]):
            if m not in reg:
                bad.append("%s %s" % (r["req_id"], m))
        for a in re.findall(r"AS-\d{2}", r["source_basis"]):
            if a not in asids:
                bad.append("%s %s" % (r["req_id"], a))
        for f in re.findall(r"[\w./]+\.(?:md|csv|py)", r["source_basis"] + " " + r["implemented_in"]):
            if not ((REPO / f).exists() or (EXT / f).exists()):
                bad.append("%s file %s" % (r["req_id"], f))
    rec("V-E02", "Traceability", "Every register ID, assumption ID and file cited as a requirement source exists", not bad, "0 missing", "%d" % len(bad), "; ".join(bad[:4]))
    bad = []
    for r in rq:
        for t in re.findall(r"[A-Z]{2,5}-\d{3}|IF-\d|L-\d{3}", r["implemented_in"]):
            if t not in eq:
                bad.append("%s %s" % (r["req_id"], t))
    rec("V-E03", "Traceability", "Every tag named in 'implemented_in' exists in a schedule", not bad, "0 unknown", "%d" % len(bad), "; ".join(bad[:4]))
    cited = set()
    for r in rq:
        cited |= set(re.findall(r"V-[A-Z]\d{2}b?", r["verification"]))
    miss = sorted(cited - set(REGISTERED))
    rec("V-E04", "Traceability", "Every check ID cited as verification exists in this script (%d IDs cited)" % len(cited), not miss, "0 unknown", "%d" % len(miss), ", ".join(miss))


DOC_VALUES = [   # (file, results key, format) : the formatted number must appear in the document
    ("DESIGN_BASIS.md", "flow.mdot_g_s", "%.3f"), ("DESIGN_BASIS.md", "flow.Qv_L_s", "%.3f"),
    ("CALCULATION_METHOD.md", "flow.Re_in", "%.0f"), ("CALCULATION_METHOD.md", "ta.1.loss", "%.2f"),
    ("CALCULATION_METHOD.md", "cand.50.FTP_nom", "%.0f"), ("CALCULATION_METHOD.md", "cand.50.FTP_low", "%.0f"),
    ("CALCULATION_METHOD.md", "cand.50.FTP_high", "%.0f"), ("CALCULATION_METHOD.md", "cand.25.FTP_nom", "%.0f"),
    ("CALCULATION_METHOD.md", "cand.40.FTP_nom", "%.0f"), ("CALCULATION_METHOD.md", "cand.80.FTP_nom", "%.0f"),
    ("CALCULATION_METHOD.md", "duty.spec.FTP_min_full_speed_Pa", "%.0f"),
    ("CALCULATION_METHOD.md", "duty.spec.Q_min_full_speed_L_s", "%.2f"),
    ("CALCULATION_METHOD.md", "ta.p0_loss_cfd_area_weighted", "%.1f"),
    ("SYSTEM_DESCRIPTION.md", "station.S4.p_static_gauge_Pa", "%.0f"),
    ("SYSTEM_DESCRIPTION.md", "station.S10.p_static_gauge_Pa", "%.0f"),
    ("README.md", "cand.50.FTP_nom", "%.0f"), ("README.md", "flow.mdot_g_s", "%.2f"),
    ("README.md", "interface.F_full_LC2", "%.1f"), ("SYSTEM_DESCRIPTION.md", "interface.F_full_LC2", "%.1f"),
]


def check_group_f(calc, res):
    need = ["README.md", "DESIGN_BASIS.md", "SYSTEM_DESCRIPTION.md", "CALCULATION_METHOD.md", "calculations.py",
            "validate_design.py", "pressure_drop_budget.csv", "candidate_line_sizes.csv", "line_list.csv",
            "equipment_schedule.csv", "instrument_index.csv", "PFD.mmd", "PFD.svg", "PFD.png", "PID.mmd", "PID.svg",
            "PID.png", "PRELIMINARY_HAZARD_REVIEW.md", "REQUIREMENTS_TRACEABILITY.csv", "VALIDATION_REPORT.md",
            "LIMITATIONS_AND_NEXT_STEPS.md", "mermaid-config.json"]
    miss = [f for f in need if not (EXT / f).exists() and f != "VALIDATION_REPORT.md"]
    rec("V-F01", "Documents", "All %d required deliverables are present" % len(need), not miss, "0 missing", "%d" % len(miss), ", ".join(miss))
    bad = []
    for f, key, fmt in DOC_VALUES:
        s = fmt % res[key]
        if s not in text(EXT / f).replace(",", ""):
            bad.append("%s: %s (%s)" % (f, s, key))
    rec("V-F03", "Documents", "Key calculated values quoted in the documents (%d) match the calculation results" % len(DOC_VALUES),
        not bad, "all present", "%d missing" % len(bad), "; ".join(bad[:5]))
    rd = text(EXT / "README.md")
    ok = ("not part of the" in rd and "February" in rd and "2025" in rd and "internship" in rd and "not approved for construction" in rd.lower())
    rec("V-F04", "Documents", "README states the chronology (follow-on, not part of the February to May 2025 internship) and that the design is not approved for construction",
        ok, "present", "present" if ok else "missing")
    disc = [f for f in ("README.md", "DESIGN_BASIS.md", "SYSTEM_DESCRIPTION.md", "CALCULATION_METHOD.md", "PRELIMINARY_HAZARD_REVIEW.md",
                        "LIMITATIONS_AND_NEXT_STEPS.md") if "conceptual" not in text(EXT / f).lower()]
    heater = "not inferred" in text(EXT / "SYSTEM_DESCRIPTION.md").lower() or "not infer" in text(EXT / "SYSTEM_DESCRIPTION.md").lower()
    rec("V-F05", "Documents", "Every narrative document says it is conceptual; the heater subsystem section says nothing is inferred from the heat flux",
        not disc and heater, "all", "missing in %s; heater note %s" % (disc, heater))
    # V-F02 hygiene: private paths, secrets, e-mail addresses, vendor or price words
    pats = {
        "absolute path": re.compile(r"(?:/home/|/root/|/tmp/|/Users/|[A-Z]:\\\\|C:/Users)"),
        "secret": re.compile(r"(?i)(?:api[_-]?key|secret|password|token)\s*[:=]\s*\S{8,}|-----BEGIN|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{12,}"),
        "e-mail": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
        "vendor or price": re.compile(r"(?i)\b(?:siemens|becker|rosemount|endress|emerson|honeywell|swagelok|festo|atlas copco|ebm-papst|kaeser|"
                                       r"gardner denver|busch|omega|usd|eur|gbp|lead time|in stock)\b|\bprices?\s*[:=]\s*[$€£]?\d|[$€£]\s?\d"),
    }
    hits = []
    for p in sorted(EXT.iterdir()):
        if p.suffix in (".md", ".csv", ".py", ".mmd", ".json", ".svg") and p.name != "VALIDATION_REPORT.md":
            s = text(p)
            for name, rx in pats.items():
                if p.name == "validate_design.py" or (p.name == "mermaid-config.json" and name == "absolute path"):
                    continue
                if p.suffix == ".svg" and name != "absolute path" and name != "secret":
                    continue
                m = rx.search(s)
                if m:
                    hits.append("%s: %s %r" % (p.name, name, m.group(0)[:20]))
    rec("V-F02", "Hygiene", "No private paths, secrets, e-mail addresses, vendor names or prices in the new files",
        not hits, "0 hits", "%d" % len(hits), "; ".join(hits[:4]))
    # V-F06 compile
    ok = True
    for f in ("calculations.py", "validate_design.py"):
        try:
            compile(text(EXT / f), f, "exec")
        except SyntaxError:
            ok = False
    rec("V-F06", "Hygiene", "Both scripts compile", ok, "compiles", "ok" if ok else "syntax error")
    # V-F07 repository diff scope
    try:
        base = subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()
        changed = subprocess.run(["git", "diff", "--name-only", base], cwd=REPO, capture_output=True, text=True, check=True).stdout.split()
        untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=REPO, capture_output=True, text=True, check=True).stdout.split()
        outside = [c for c in changed + untracked if not (c.startswith("08_Fluid_Test_Rig_Design/") or c == "README.md")]
        rec("V-F07", "Hygiene", "Only 08_Fluid_Test_Rig_Design/ and README.md differ from origin/main", not outside, "0 other files", "%d: %s" % (len(outside), outside[:3]))
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        rec("V-F07", "Hygiene", "Only 08_Fluid_Test_Rig_Design/ and README.md differ from origin/main", True, note="git or origin/main unavailable", skip=True)


def snapshot():
    snap = {}
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            p = os.path.join(root, f)
            st = os.stat(p)
            snap[p] = (st.st_size, st.st_mtime_ns)
    return snap


OUTPUTS = ["flow_basis.csv", "pressure_drop_budget.csv", "candidate_line_sizes.csv", "pressure_budget_sensitivity.csv",
           "stream_table.csv", "system_curve.csv", "thermal_structural_interface.csv", "calculation_results.json"]


def check_group_g(calc, rerun):
    # V-G03 / V-G04: input validation and no silent substitution (in a throw-away module state)
    fails = []
    def expect(exc, fn, label):
        try:
            fn()
            fails.append(label + " accepted")
        except exc:
            pass
    saved = dict(calc.INPUTS)
    try:
        calc.INPUTS["D_i"] = (-0.02, "m", "M023"); expect(ValueError, calc.check_inputs, "negative diameter")
        calc.INPUTS["D_i"] = saved["D_i"]
        calc.INPUTS["D_o"] = (0.015, "m", "M024"); expect(ValueError, calc.check_inputs, "outer < inner")
        calc.INPUTS["D_o"] = saved["D_o"]
        calc.INPUTS["V_in"] = (float("nan"), "m/s", "M003"); expect(ValueError, calc.check_inputs, "NaN velocity")
        calc.INPUTS["V_in"] = saved["V_in"]
        calc.INPUTS["t_wall"] = (0.02, "m", "M025"); expect(ValueError, calc.check_inputs, "inconsistent wall")
        calc.INPUTS["t_wall"] = saved["t_wall"]
        expect(ValueError, lambda: calc.air(-5.0), "negative temperature")
        expect(ValueError, lambda: calc.colebrook(0.0, 0.0), "zero Reynolds number")
        old = calc.CANDIDATE_BORES
        calc.CANDIDATE_BORES = (0.015,); expect(ValueError, calc.check_inputs, "candidate smaller than test article")
        calc.CANDIDATE_BORES = old
        calc.check_inputs()
    finally:
        calc.INPUTS.clear(); calc.INPUTS.update(saved)
    rec("V-G03", "Reproducibility", "Invalid dimensions and non-physical inputs are rejected (7 negative tests); valid inputs are accepted",
        not fails, "all rejected", "%d accepted wrongly" % len(fails), ", ".join(fails))
    miss = False
    try:
        calc.inp("not_an_input")
    except KeyError:
        miss = True
    rec("V-G04", "Reproducibility", "A missing input raises KeyError instead of being substituted", miss, "KeyError", "KeyError" if miss else "no error")
    if not rerun:
        for cid, d in (("V-G01", "Clean-directory rerun reproduces the committed outputs byte for byte"),
                       ("V-G02", "Two independent runs give identical output")):
            rec(cid, "Reproducibility", d, True, note="skipped by --no-rerun", skip=True)
        return
    tmp = Path(tempfile.mkdtemp(prefix="rig_rerun_"))
    try:
        before = snapshot()
        outs = []
        for i in (1, 2):
            d = tmp / ("run%d" % i)
            subprocess.run([sys.executable, str(EXT / "calculations.py"), "--outdir", str(d)], check=True, capture_output=True)
            outs.append(d)
        after = snapshot()
        diff = [f for f in OUTPUTS if (outs[0] / f).read_bytes() != (EXT / f).read_bytes()]
        rec("V-G01", "Reproducibility", "Clean-directory rerun reproduces the %d committed outputs byte for byte" % len(OUTPUTS),
            not diff, "0 differences", "%d: %s" % (len(diff), ", ".join(diff)))
        diff2 = [f for f in OUTPUTS if (outs[0] / f).read_bytes() != (outs[1] / f).read_bytes()]
        untouched = before == after
        rec("V-G02", "Reproducibility", "Two runs give identical output and the run changes no file anywhere in the repository",
            not diff2 and untouched, "identical, repository unchanged", "diff %s; repository changed=%s" % (diff2, not untouched))
        # the script must refuse to write inside the repository outside its own folder
        r = subprocess.run([sys.executable, str(EXT / "calculations.py"), "--outdir", str(REPO / "05_Data")], capture_output=True, text=True)
        rec("V-G05", "Reproducibility", "calculations.py refuses to write inside the repository outside 08_Fluid_Test_Rig_Design",
            r.returncode != 0 and "refusing" in (r.stderr + r.stdout), "refused", "exit %d" % r.returncode)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


STATIC_INTRO = """# Validation report

Conceptual educational design. This report is written by `validate_design.py`; do not edit it by hand.
It has no timestamps, so a rerun on unchanged inputs reproduces it exactly.

**What is validated.** Arithmetic, internal consistency, traceability of sourced values, consistency between the
diagrams and the schedules, and reproducibility of the calculation script. Independent re-calculations use different
formulations from `calculations.py` (Haaland instead of Colebrook-White for friction, the ISO loss-coefficient form for the
orifice permanent loss, the momentum balance for the expansion, hand arithmetic for the flow basis).

**What is not validated.** No physical test, vendor datasheet or qualified-engineer review was available. The
generic loss coefficients, the filter and flow-element allocations and the routing are assumptions (register:
DESIGN_BASIS.md section 5). A passing check here shows the document set is self-consistent and reproducible, not that the
design is correct for a real facility. A check that failed would have been investigated, not relaxed.

"""

STATIC_OUTRO = """
## Preserved observations (not failures)

- **Mass flow against the CFD.** The circular-tube mass flow (8.686 g/s) is 0.28 % above the CFD flux (8.662 g/s). The CFD
  mesh is a 48-sided facetted bore with 0.285 % less flow area, as documented in the CFD results. The design uses the
  circular-tube value, because the rig has a round bore.
- **Outlet Reynolds number.** The Sutherland viscosity gives 25,657 at the outlet against the CFD value of 25,545 (0.44 %),
  because the CFD uses tabulated viscosity. Within the 1 % tolerance of the check.
- **Test-article loss bookkeeping.** The budget converts the CFD static drop (438.13 Pa) to a total-pressure loss with
  1-D velocity pressures (363.48 Pa). The CFD area-weighted total-pressure difference is 334.61 Pa. The budget keeps the
  larger value as nominal and brackets the range in the low and high cases (check V-C05). The repository's own note that
  the CFD total pressure is "not combined with or substituted for the static drop" is respected: the static drop remains
  the source and the CFD total pressure is used only as a cross-check bound.
- **Friction-factor method.** Colebrook-White and Haaland differ by up to 4 % by construction. The check tolerance is set
  to that known spread and is not a statement about the CFD friction factor (fully developed f = 0.02163 in the heated duct).
- **Not checked by this script.** Standards were verified against public catalogue listings by web search while writing
  DESIGN_BASIS.md; the standards themselves are paywalled and were not read. Any use of them needs the purchased text.

## How to run

```
python calculations.py             # regenerates the CSV/JSON outputs
python validate_design.py          # runs every check, rewrites this report, exit code 1 on any failure
python validate_design.py --no-rerun
```
"""


def write_report(outdir):
    n_pass = sum(1 for r in RESULTS if r[3] == "PASS")
    n_fail = sum(1 for r in RESULTS if r[3] == "FAIL")
    n_skip = sum(1 for r in RESULTS if r[3] == "SKIP")
    lines = [STATIC_INTRO, "## Summary\n", "| Result | Checks |", "|---|---:|", "| PASS | %d |" % n_pass, "| FAIL | %d |" % n_fail,
             "| SKIP | %d |" % n_skip, "", "## Checks\n", "| ID | Group | Check | Result | Expected | Actual | Note |", "|---|---|---|---|---|---|---|"]
    esc = lambda s: s.replace("|", "/").replace("\n", " ")
    for cid, grp, desc, st, ex, ac, note in sorted(RESULTS, key=lambda r: r[0]):
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (cid, grp, esc(desc), st, esc(ex), esc(ac), esc(note)))
    lines.append(STATIC_OUTRO)
    (Path(outdir) / "VALIDATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return n_pass, n_fail, n_skip


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--outdir", help="where to write VALIDATION_REPORT.md (default: this folder)")
    ap.add_argument("--no-rerun", action="store_true", help="skip the clean-directory reproduction")
    a = ap.parse_args()
    calc = load_calc()
    res = json.loads(text(EXT / "calculation_results.json"))
    reg = read_register()
    check_group_a(calc, reg)
    check_group_b(calc, res)
    check_group_c(calc, res, reg)
    check_group_d(calc, res)
    check_interlocks()
    check_group_g(calc, not a.no_rerun)
    check_group_f(calc, res)
    check_group_e(calc)          # last: it cross-checks the check IDs registered above
    out = Path(a.outdir).resolve() if a.outdir else EXT
    out.mkdir(parents=True, exist_ok=True)
    p, f, s = write_report(out)
    for r in RESULTS:
        if r[3] == "FAIL":
            print("FAIL %s %s | expected %s | actual %s | %s" % (r[0], r[2], r[4], r[5], r[6]))
    print("checks: %d pass, %d fail, %d skip -> %s" % (p, f, s, out / "VALIDATION_REPORT.md"))
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(main())
