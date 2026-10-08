# -*- coding: utf-8 -*-
"""Section 9B-1 - C00_PIPELINE_CHECK: does the parametric automation reproduce P00_BASELINE?

RE-ANALYSIS 2026. Compares the C00 run (10_Parametric_Study/CFD_Cases/C00_PIPELINE_CHECK) with the solved
Section 5B baseline (06_Fluent_CFD), both extracted by extract_case.py with identical definitions.

TOLERANCES - fixed here BEFORE C00 was solved (the file is committed before the C00 run is launched):
  * Delta p 0.1 % and temperatures 0.1 K: PARAMETRIC_CASE_MATRIX.csv, row C00 ("T 0.1 K, dp 0.1 %").
  * Q 0.1 % and mdot 0.01 %: the 5B plateau criteria for q_interface and mdot_out (REL_DRIFT in the journals),
    i.e. the numerical tolerance to which P00 itself is converged.
  * y+ 0.1 %: the same relative tolerance as Q and Delta p (y+ is a derived wall quantity of the same solution).
  * mass and energy balance: C00 must itself satisfy the 5B acceptance (mass < 1e-4, energy < 5e-3).
If any comparison fails, C00 FAILS and, per the 9B-1 brief, no parametric case may proceed.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_case import extract

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"<PROJECT_ROOT>"
P00_DIR = os.path.join(ROOT, "06_Fluent_CFD")
C00_DIR = os.path.join(ROOT, "10_Parametric_Study", "CFD_Cases", "C00_PIPELINE_CHECK")

TOL = [  # (key, kind, tolerance, source)
    ("dp_Pa", "rel", 1e-3, "case matrix C00: dp 0.1 %"),
    ("T_out_K", "abs", 0.1, "case matrix C00: T 0.1 K"),
    ("T_solid_max_K", "abs", 0.1, "case matrix C00: T 0.1 K"),
    ("T_solid_cell_max_K", "abs", 0.1, "case matrix C00: T 0.1 K"),
    ("T_interface_max_K", "abs", 0.1, "case matrix C00: T 0.1 K"),
    ("T_fluid_max_K", "abs", 0.1, "case matrix C00: T 0.1 K"),
    ("T_solid_mean_K", "abs", 0.1, "case matrix C00: T 0.1 K"),
    ("T_outer_avg_K", "abs", 0.1, "case matrix C00: T 0.1 K"),
    ("Q_heated_wall_W", "rel", 1e-3, "5B plateau criterion q_interface 0.1 %"),
    ("Q_interface_W", "rel", 1e-3, "5B plateau criterion q_interface 0.1 %"),
    ("mdot_in_kg_s", "rel", 1e-4, "5B plateau criterion mdot 0.01 %"),
    ("mdot_out_kg_s", "rel", 1e-4, "5B plateau criterion mdot 0.01 %"),
    ("yplus_max", "rel", 1e-3, "same relative tolerance as Q / dp"),
    ("yplus_mean", "rel", 1e-3, "same relative tolerance as Q / dp"),
    ("yplus_min", "rel", 1e-3, "same relative tolerance as Q / dp"),
    ("Re_in", "rel", 1e-4, "follows mdot"),
    ("Re_out", "rel", 1e-3, "follows mdot and T_out"),
]
ACCEPT = [("mass_error_monitor", 1e-4, "5B acceptance |in-out|/in < 1e-4"),
          ("energy_error_monitor", 5e-3, "5B acceptance |sum Q|/Q_wall < 5e-3")]


def main():
    p = extract(P00_DIR, "Monitors/baseline_monitors.out")
    c = extract(C00_DIR, "Monitors/C00_PIPELINE_CHECK_monitors.out")
    rows, ok_all = [], True
    for k, kind, tol, src in TOL:
        d = c[k] - p[k]
        e = abs(d) / abs(p[k]) if kind == "rel" else abs(d)
        ok = e <= tol
        ok_all &= ok
        rows.append(dict(quantity=k, P00=p[k], C00=c[k], difference=d, error=e, kind=kind, tolerance=tol,
                         ok=ok, source=src))
    for k, tol, src in ACCEPT:
        ok = c[k] < tol
        ok_all &= ok
        rows.append(dict(quantity=k, P00=p[k], C00=c[k], difference=c[k] - p[k], error=c[k], kind="acceptance",
                         tolerance=tol, ok=ok, source=src))
    try:
        rs = json.load(open(os.path.join(C00_DIR, "Audit", "run_summary.json")))
    except Exception as e:
        rs = {"error": str(e)}
    conv = rs.get("status") == "CONVERGED"
    ok_all &= conv
    res = {"case": "C00_PIPELINE_CHECK", "reference": "P00_BASELINE (06_Fluent_CFD, Section 5B)",
           "C00_status": rs.get("status"), "C00_iterations": c["iterations"], "P00_iterations": p["iterations"],
           "rows": rows, "PASS": bool(ok_all)}
    out = os.path.join(C00_DIR, "C00_REPRODUCTION.json")
    json.dump(res, open(out, "w"), indent=2)
    print("C00 status %s, iterations C00 %d / P00 %d" % (rs.get("status"), c["iterations"], p["iterations"]))
    for r in rows:
        print("%-4s %-22s P00 %-18.10g C00 %-18.10g err %.3e (tol %.1e %s)" %
              ("ok" if r["ok"] else "FAIL", r["quantity"], r["P00"], r["C00"], r["error"], r["tolerance"], r["kind"]))
    print("C00 REPRODUCTION: %s" % ("PASS" if ok_all else "FAIL - STOP: no parametric case may proceed"))


if __name__ == "__main__":
    main()
