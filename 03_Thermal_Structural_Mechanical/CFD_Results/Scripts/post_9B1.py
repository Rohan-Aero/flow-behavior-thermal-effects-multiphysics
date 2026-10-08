# -*- coding: utf-8 -*-
"""Section 9B-1 - post-processing of the CFD parametric cases (C00, V01, V03, Q01, Q03, T01, T03).

RE-ANALYSIS 2026 - every number comes from newly generated Fluent outputs of this project. No recovered
internship value and no experimental measurement exists or is used.

For every case folder 10_Parametric_Study/CFD_Cases/<CASE> this script
  1. extracts the outputs with extract_case.py (the P00 definitions, unchanged),
  2. re-checks from the raw files: run status, frozen-physics gate, the three setup audits, the convergence
     evaluations, the property-table history, the solver-message scan, y+ policy, heat input, exports,
  3. writes <CASE>/CASE_RESULTS.md and <CASE>/CASE_AUDIT.md,
and then writes CFD_Results/PARAMETRIC_CFD_RESULTS.csv, parametric_cfd_results.json, PARAMETRIC_CFD_TABLE.md and
screening_comparison.json (CFD against the 9A anchored screening; no agreement is forced).
Run with the ANSYS-bundled CPython 3.10:  python post_9B1.py
"""
import os, sys, json, csv, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[1] if len(sys.argv) > 1 else r"<PROJECT_ROOT>"
PS = os.path.join(ROOT, "10_Parametric_Study")
CFD = os.path.join(PS, "CFD_Cases")
RES = os.path.join(PS, "CFD_Results")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(CFD, "Journals"))
from extract_case import extract
import param_cases as PC

AIR = (250.0, 600.0)
INC = (293.15, 673.15)
YP_MAX, YP_MEAN = 1.0, 0.5
C00_V1 = {"solve_param.py": "9A4754C62249D708239D1A08C6738BCB7DDBC982DE1092B91FB6083D22B78802 (archived v1)",
          "param_cases.py": "A8B865F57E6186CE33AD7312FA2E78FE00C7C2384D8049DB0365E5B7E889B7BD (archived v1)"}
MAIN = [("dp_Pa", "Δp [Pa]", "rel"), ("T_out_K", "T_out [K]", "abs"), ("T_solid_max_K", "T_max solid [K]", "abs"),
        ("Q_heated_wall_W", "Q [W]", "rel"), ("Re_in", "Re_in [-]", "rel"), ("yplus_max", "y+ max [-]", "rel")]


def sha256(p):
    import hashlib
    h = hashlib.sha256()
    try:
        with open(p, "rb") as fh:
            for blk in iter(lambda: fh.read(1 << 20), b""):
                h.update(blk)
        return h.hexdigest().upper()
    except Exception as e:
        return "ERROR %s" % e


def jload(p, default=None):
    try:
        return json.load(open(p))
    except Exception:
        return default


def pct(a, b):
    return (a - b) / abs(b) * 100.0


def fmt(v, n=4):
    if v is None:
        return "—"
    if isinstance(v, float):
        if v != 0 and (abs(v) < 1e-3 or abs(v) >= 1e6):
            return "%.3e" % v
        if abs(v) < 1:
            return ("%." + str(n) + "g") % v
        return "%.4f" % v if abs(v) < 100 else ("%.3f" % v if abs(v) < 1e4 else "%.0f" % v)
    return str(v)


def case_checks(case, P00):
    d = os.path.join(CFD, case)
    A = os.path.join(d, "Audit")
    rs = jload(os.path.join(A, "run_summary.json"), {})
    gate = jload(os.path.join(A, "frozen_physics_gate.json"), {})
    au = {k: jload(os.path.join(A, "setup_audit_%s.json" % k), {}) for k in ("1_presolve", "2_final_schemes", "3_final")}
    ev = jload(os.path.join(A, "convergence_evaluations.json"), [])
    va = jload(os.path.join(A, "validity_checks.json"), {})
    mz = jload(os.path.join(A, "case_mesh_zones.json"), {})
    vx = jload(os.path.join(A, "volume_export_check.json"), {})
    en = jload(os.path.join(A, "ensight_export_verification.json"), {})
    out = {"case": case, "folder": d, "run_summary": rs}
    status = rs.get("status", "NOT_RUN")
    out["journal_status"] = status
    if status != "CONVERGED":
        out["valid"] = False
        out["status"] = status
        out["why"] = rs.get("why", "run did not converge")
        return out, None
    x = extract(d, "Monitors/%s_monitors.out" % case)
    r = PC.resolved(case)
    C = {}
    # 1. frozen-physics gate: intended vs actual changed settings
    C["gate"] = {"ok": bool(gate.get("passed")) and gate.get("diff_after_replace") == 0,
                 "diff_after_replace": gate.get("diff_after_replace"),
                 "changed_paths": [(g["path"], g["P00"], g["case"]) for g in gate.get("diff_after_change", [])],
                 "unexpected": gate.get("unexpected"), "intended_but_absent": gate.get("intended_but_absent")}
    # 2. audits
    C["audits"] = {k: {"items": v.get("n_items"), "failed": v.get("n_failed"),
                       "same_as_P00": sum(1 for row in v.get("rows", []) if row["item"].startswith("SAME AS P00")),
                       "changed_intended": [row["item"] for row in v.get("rows", [])
                                            if row["item"].startswith("CHANGED FROM P00")]}
                   for k, v in au.items()}
    C["audits_ok"] = all(v.get("n_failed") == 0 for v in au.values())
    ver = [row for row in au["1_presolve"].get("rows", []) if row["item"] == "fluent version"]
    C["fluent_version"] = ver[0]["value"] if ver else None
    # 3. convergence
    last = ev[-1] if ev else {}
    C["convergence"] = {"ok": bool(last.get("converged")) and last.get("tag", "").startswith("confirmation"),
                        "n_evaluations": len(ev), "final": last,
                        "first_converged": next((e["tag"] for e in ev if e.get("converged")), None)}
    # 4. property tables over every iteration (raw monitor history, re-read here) + solver messages
    h = x["temperature_history_extremes"]
    air_max = max(h["T_fluid_max"]["max"], h["T_wall_max"]["max"], h["T_out_bulk"]["max"])
    air_min = min(h["T_fluid_min"]["min"], h["T_in_bulk"]["min"])
    sol_max = max(h["T_outer_max"]["max"], h["T_solid_max"]["max"], h["T_wall_max"]["max"])
    sol_min = min(h["T_solid_min"]["min"], h["T_inner_avg"]["min"])
    msgs = [m for c in va.get("checks", []) for m in c.get("messages", [])]
    C["property_tables"] = {
        "air_max_K": air_max, "air_min_K": air_min, "air_table": AIR, "air_margin_K": AIR[1] - air_max,
        "solid_max_K": sol_max, "solid_min_K": sol_min, "inconel_table": INC, "solid_margin_K": INC[1] - sol_max,
        "solid_low_margin_K": sol_min - INC[0],
        "ok": AIR[0] <= air_min and air_max <= AIR[1] and INC[0] <= sol_min and sol_max <= INC[1],
        "journal_checks": len(va.get("checks", [])), "journal_checks_ok": all(c.get("ok") for c in va.get("checks", [])),
        "solver_messages": msgs}
    # 5. start-up excursion: history maximum above the converged value
    C["startup"] = {n: {"history_max_K": h[n]["max"], "final_K": h[n]["final"], "overshoot_K": h[n]["max"] - h[n]["final"],
                        "iteration_of_max": h[n]["iteration_of_max"]}
                    for n in ("T_outer_max", "T_wall_max", "T_fluid_max", "T_solid_max", "T_out_bulk")}
    # 6. y+ policy
    C["yplus"] = {"min": x["yplus_min"], "mean": x["yplus_mean"], "max": x["yplus_max"],
                  "ok": x["yplus_max"] <= YP_MAX and x["yplus_mean"] <= YP_MEAN}
    # 7. heat input: Q = q'' x Fluent heated area; T cases must equal P00's Q
    q_expect = r["QPP"] * x["A_heated_m2"]
    C["heat_input"] = {"qpp_set_W_m2": r["QPP"], "A_heated_Fluent_m2": x["A_heated_m2"], "Q_expected_W": q_expect,
                       "Q_Fluent_W": x["Q_heated_wall_W"], "rel": x["Q_heated_wall_W"] / q_expect - 1.0,
                       "Q_vs_P00_rel": x["Q_heated_wall_W"] / P00["Q_heated_wall_W"] - 1.0,
                       "qpp_area_avg_W_m2": x["qpp_heated_area_avg_W_m2"]}
    C["heat_input"]["ok"] = abs(C["heat_input"]["rel"]) < 1e-6 and (
        not case.startswith("T") or abs(C["heat_input"]["Q_vs_P00_rel"]) < 1e-6)
    # 8. exports
    C["exports"] = {"volume": vx, "ensight": en.get("files"),
                    "ok": all(v.get("ok") for v in vx.values()) and bool(en.get("files")) and
                    all(sz > 0 for sz in (en.get("files") or {}).values())}
    C["mesh"] = mz.get("mesh", {})
    C["mesh"]["file"] = r["MESH"]
    C["mesh"]["expected_cells"] = r["COUNTS"]
    C["mesh"]["sha256"] = sha256(os.path.normpath(os.path.join(d, r["MESH"])))
    C["mesh"]["sha256_recorded_by_run"] = rs.get("mesh_sha256")
    C["mesh"]["sha_consistent"] = rs.get("mesh_sha256") in (None, C["mesh"]["sha256"])
    C["mesh"]["ok"] = C["mesh"].get("cells") == r["COUNTS"][0] and (C["mesh"].get("min_orthogonal_quality") or 0) > 0.1 \
        and not C["mesh"].get("mesh_check_warnings")
    C["balances"] = {"mass_error": x["mass_error_monitor"], "energy_error": x["energy_error_monitor"],
                     "ok": x["mass_error_monitor"] < 1e-4 and x["energy_error_monitor"] < 5e-3}
    keys = ["gate", "convergence", "property_tables", "yplus", "heat_input", "exports", "mesh", "balances"]
    fails = [k for k in keys if not C[k]["ok"]] + ([] if C["audits_ok"] else ["audits"])
    out.update(checks=C, valid=not fails, failed_checks=fails,
               status="CONVERGED_VALID" if not fails else "INVALID (%s)" % ", ".join(fails))
    return out, x


def write_case_docs(case, info, x, P00, scr):
    d = os.path.join(CFD, case)
    if not os.path.isdir(d):
        return
    cd = PC.CASES[case]
    r = PC.resolved(case)
    rs = info["run_summary"]
    L = ["# %s — CFD case results (Section 9B-1)" % case, "",
         "> **RE-ANALYSIS 2026 — newly generated results, not recovered originals. No measured data exists or is used.**",
         "> Generated by `CFD_Results/Scripts/post_9B1.py` from the raw Fluent outputs in this folder.", ""]
    if x is None:
        L += ["**Status: %s** — %s" % (info["status"], info.get("why", "")), "",
              "No result of this case is reported. The case was not modified to rescue it."]
        open(os.path.join(d, "CASE_RESULTS.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
        open(os.path.join(d, "CASE_AUDIT.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
        return
    C = info["checks"]
    L += ["## 1. Case definition", "",
          "| Item | Value |", "|---|---|",
          "| Case ID | `%s` |" % case,
          "| Variable | %s |" % cd["variable"],
          "| Value | %s %s |" % (cd["value"], cd["units"] if cd["units"] != "-" else ""),
          "| Inlet velocity | %.4f m/s |" % r["V_IN"],
          "| Inlet turbulence intensity | %.6f (0.16 Re^-1/8 with Re scaled by V/23.5) |" % r["TI"],
          "| Heated-wall flux | %.6f W/m² |" % r["QPP"],
          "| Geometry | Di 20 / Do %.0f / L 600 mm (t = %.0f mm) |" % (r["DO"] * 1e3, r["T_WALL"] * 1e3),
          "| Mesh | `%s` — %s cells (%s fluid / %s solid) |" % (r["MESH"], r["COUNTS"][0], r["COUNTS"][1], r["COUNTS"][2]),
          "| Solver | %s, 3ddp, 4 processes, pressure-based coupled, steady, SST k-ω |" % C["fluent_version"],
          "| Status | **%s** |" % info["status"], ""]
    L += ["## 2. Results (definitions identical to P00, `Planning/OUTPUT_DEFINITIONS.md`)", "",
          "| Output | P00 | %s | Change |" % case, "|---|---|---|---|"]
    rows = [("Mass flow in [g/s]", "mdot_in_kg_s", 1e3, "rel"), ("Re inlet", "Re_in", 1, "rel"),
            ("Re outlet", "Re_out", 1, "rel"), ("Δp static, area-weighted [Pa]", "dp_Pa", 1, "rel"),
            ("T_out, mass-weighted [K]", "T_out_K", 1, "abs"), ("Q heated wall [W]", "Q_heated_wall_W", 1, "rel"),
            ("Q interface [W]", "Q_interface_W", 1, "rel"),
            ("T max solid (outer-wall facet) [K]", "T_solid_max_K", 1, "abs"),
            ("T max solid (cell centre) [K]", "T_solid_cell_max_K", 1, "abs"),
            ("T max interface (near-wall air) [K]", "T_interface_max_K", 1, "abs"),
            ("T max fluid (cell) [K]", "T_fluid_max_K", 1, "abs"),
            ("Outer wall T, area mean [K]", "T_outer_avg_K", 1, "abs"),
            ("Interface T, area mean [K]", "T_interface_avg_K", 1, "abs"),
            ("Solid T, volume mean [K]", "T_solid_mean_K", 1, "abs"),
            ("Solid T min (cell) [K]", "T_solid_cell_min_K", 1, "abs"),
            ("y+ min / mean / max", None, None, None),
            ("Mass imbalance, abs(in + out) / in", "mass_error_monitor", 1, None),
            ("Energy imbalance, abs(ΣQ) / Q_wall", "energy_error_monitor", 1, None),
            ("Iterations (total)", "iterations", 1, None)]
    for lab, k, s, kind in rows:
        if k is None:
            L.append("| %s | %.4f / %.4f / %.4f | %.4f / %.4f / %.4f | max %+.2f %% |" %
                     (lab, P00["yplus_min"], P00["yplus_mean"], P00["yplus_max"], x["yplus_min"], x["yplus_mean"],
                      x["yplus_max"], pct(x["yplus_max"], P00["yplus_max"])))
            continue
        a, b = P00[k] * s, x[k] * s
        ch = "" if kind is None else ("%+.3f %%" % pct(b, a) if kind == "rel" else "%+.2f K" % (b - a))
        fa = ("%.3e" % a) if k.endswith("error_monitor") else fmt(a, 6)
        fb = ("%.3e" % b) if k.endswith("error_monitor") else fmt(b, 6)
        L.append("| %s | %s | %s | %s |" % (lab, fa, fb, ch))
    L += ["", "## 3. Validity", "",
          "| Check | Result |", "|---|---|",
          "| Converged (residuals + 200-it plateau + mass + energy, then 100-it confirmation) | %s (first met at %s; %d evaluations) |"
          % ("yes" if C["convergence"]["ok"] else "**NO**", C["convergence"]["first_converged"], C["convergence"]["n_evaluations"]),
          "| Air table 250–600 K, every iteration | min %.2f K, max %.2f K (margin %.1f K) — %s |"
          % (C["property_tables"]["air_min_K"], C["property_tables"]["air_max_K"], C["property_tables"]["air_margin_K"],
             "inside" if C["property_tables"]["ok"] else "**OUTSIDE**"),
          "| Inconel table 293.15–673.15 K, every iteration | min %.2f K, max %.2f K (margin %.1f K) — %s |"
          % (C["property_tables"]["solid_min_K"], C["property_tables"]["solid_max_K"], C["property_tables"]["solid_margin_K"],
             "inside" if C["property_tables"]["ok"] else "**OUTSIDE**"),
          "| Solver limiter / reversed-flow / divergence messages | %d |" % len(C["property_tables"]["solver_messages"]),
          "| Start-up excursion (history max − converged), outer-wall max | %+.3f K at iteration %d |"
          % (C["startup"]["T_outer_max"]["overshoot_K"], C["startup"]["T_outer_max"]["iteration_of_max"]),
          "| y+ (max ≤ 1.0, mean ≤ 0.5) | max %.4f, mean %.4f — %s |" % (C["yplus"]["max"], C["yplus"]["mean"],
                                                                       "met" if C["yplus"]["ok"] else "**NOT MET**"),
          "| Heat input Q = q″ × A_heated(Fluent) | %.6f W vs %.6f W (rel %.1e) |" % (C["heat_input"]["Q_Fluent_W"],
                                                                                C["heat_input"]["Q_expected_W"], C["heat_input"]["rel"]),
          ""]
    if scr:
        L += ["## 4. Against the 9A anchored screening (no agreement forced)", "",
              "| Output | Screening | CFD | CFD − screening |", "|---|---|---|---|"]
        for lab, sv, cv, kind in scr["rows"]:
            L.append("| %s | %s | %s | %s |" % (lab, fmt(sv, 6), fmt(cv, 6),
                                               ("%+.2f K" % (cv - sv)) if kind == "abs" else ("%+.2f %%" % pct(cv, sv))))
        L += ["", "The attribution of each difference is in `CFD_Results/SCREENING_COMPARISON.md`.", ""]
    if case == "C00_PIPELINE_CHECK":
        L += ["## 4. Reproduction of P00", "", "See `C00_REPRODUCTION.md` (comparison with the Section 5B solution, tolerances "
              "fixed before the run) and `C00_monitor_history_comparison.json` (all 29 monitors at every iteration).", ""]
    L += ["## 5. Output locations (this folder)", "",
          "| What | Where |", "|---|---|",
          "| Case / data | `Case/%s_final.cas.h5`, `Data/%s_final.dat.h5` |" % (case, case),
          "| Monitors (29 reports, every iteration) | `Monitors/%s_monitors.out` |" % case,
          "| Fluent flux and surface-integral reports | `Audit/fluent_flux_*.txt`, `Audit/fluent_si_*.txt` |",
          "| Wall / boundary / volume exports | `Exports/*.csv` |",
          "| Solid node temperatures for 9B-2 mapping (EnSight Gold) | `EnSight/solid_domain_T.*` |",
          "| Audits, gate, convergence, validity | `Audit/` (see CASE_AUDIT.md) |",
          "| Logs and transcript | `Logs/` |", ""]
    open(os.path.join(d, "CASE_RESULTS.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

    A = ["# %s — CFD case audit (Section 9B-1)" % case, "",
         "> **RE-ANALYSIS 2026.** Automation-integrity record of this case, generated from the raw audit files.", "",
         "## 1. Intended vs actual change", "",
         "Intended change (param_cases.py): `%s`" % json.dumps(cd["intended"]), "",
         "Settings diff after mesh replace: **%s** differences (must be 0)." % C["gate"]["diff_after_replace"], ""]
    gp = C["gate"]["changed_paths"]
    A += ["Settings diff after the intended change (full settings tree, `Audit/frozen_physics_gate.json`): **%d** paths" % len(gp), ""]
    if gp:
        A += ["| Path | P00 | Case |", "|---|---|---|"] + ["| `%s` | %s | %s |" % (p, a, b) for p, a, b in gp] + [""]
    A += ["Unexpected paths: %s · intended-but-absent: %s · gate: **%s**" %
          (len(C["gate"]["unexpected"] or []), len(C["gate"]["intended_but_absent"] or []), "PASS" if C["gate"]["ok"] else "FAIL"), "",
          "## 2. Unchanged settings (read back from Fluent and compared with P00's own audit)", "",
          "| Audit stage | Items | Failed | Rows identical to P00 | Rows changed as intended |", "|---|---|---|---|---|"]
    for k, v in C["audits"].items():
        A.append("| %s | %s | %s | %s | %s |" % (k, v["items"], v["failed"], v["same_as_P00"],
                                               ", ".join(i.replace("CHANGED FROM P00 (intended): ", "") for i in v["changed_intended"]) or "—"))
    A += ["", "The common rows cover solver, models, materials (all six property curves), cell-zone materials, every boundary "
          "condition, schemes, pseudo-time controls, limits and equations.", "",
          "## 3. Mesh", "",
          "| Item | Value |", "|---|---|",
          "| File | `%s` |" % C["mesh"]["file"],
          "| SHA-256 | `%s` |" % C["mesh"].get("sha256"),
          "| Cells (printed by Fluent) / expected | %s / %s |" % (C["mesh"].get("cells"), C["mesh"]["expected_cells"][0]),
          "| Minimum cell volume [m³] | %s |" % C["mesh"].get("min_volume_m3"),
          "| Minimum orthogonal quality (Fluent) | %s |" % C["mesh"].get("min_orthogonal_quality"),
          "| Mesh-check warnings | %s |" % (C["mesh"].get("mesh_check_warnings") or "none"), "",
          "## 4. Convergence", "", "| Evaluation | Converged | Failing checks |", "|---|---|---|"]
    for e in jload(os.path.join(d, "Audit", "convergence_evaluations.json"), []):
        if not e.get("ready"):
            A.append("| %s (iter %s) | not evaluable | %s |" % (e["tag"], e.get("iteration"), e.get("why")))
        else:
            A.append("| %s (iter %s) | %s | %s |" % (e["tag"], e.get("iteration"), "yes" if e.get("converged") else "no",
                                                   ", ".join(k for k, v in e["checks"].items() if not v["ok"]) or "none"))
    fe = C["convergence"]["final"]
    A += ["", "Final evaluation values:", "", "| Criterion | Value | Target |", "|---|---|---|"]
    for k, v in (fe.get("checks") or {}).items():
        A.append("| %s | %.3e | %.1e |" % (k.replace("|", "\\|"), v["value"], v["target"]))
    pt = C["property_tables"]
    A += ["", "## 5. Property tables and solver messages (every iteration of every stage)", "",
          "Checked by the journal after every iterate call (%d checks, all ok: %s) and re-checked here from the raw monitor file." %
          (pt["journal_checks"], pt["journal_checks_ok"]), "",
          "| Monitor | History min [K] | History max [K] | Iteration of max | Converged [K] |", "|---|---|---|---|---|"]
    for n, v in x["temperature_history_extremes"].items():
        A.append("| %s | %.3f | %.3f | %d | %.3f |" % (n, v["min"], v["max"], v["iteration_of_max"], v["final"]))
    A += ["", "Solver messages matching limiter / reversed-flow / divergence formats: %s" % (pt["solver_messages"] or "none"), "",
          "## 6. Heat input, balances, exports", "",
          "| Check | Value |", "|---|---|",
          "| q″ set / area-average read back [W/m²] | %.6f / %.6f |" % (C["heat_input"]["qpp_set_W_m2"], C["heat_input"]["qpp_area_avg_W_m2"]),
          "| Heated area (Fluent) [m²] | %.9e |" % C["heat_input"]["A_heated_Fluent_m2"],
          "| Q Fluent / q″·A [W] | %.6f / %.6f |" % (C["heat_input"]["Q_Fluent_W"], C["heat_input"]["Q_expected_W"]),
          "| Q vs P00 | %+.4e (relative) |" % C["heat_input"]["Q_vs_P00_rel"],
          "| Mass imbalance | %.3e (target < 1e-4) |" % C["balances"]["mass_error"],
          "| Energy imbalance | %.3e (target < 5e-3) |" % C["balances"]["energy_error"],
          "| Volume export rows | %s |" % json.dumps({k.split("/")[-1]: v.get("rows") for k, v in C["exports"]["volume"].items()}),
          "| EnSight files | %s |" % json.dumps(C["exports"]["ensight"]), "",
          "## 7. Versions", "",
          "| Item | Value |", "|---|---|",
          "| Fluent | %s |" % C["fluent_version"],
          "| Journal `solve_param.py` SHA-256 | `%s` |" % rs.get("journal_sha256", C00_V1["solve_param.py"] if case == "C00_PIPELINE_CHECK" else "(not recorded)"),
          "| `param_cases.py` SHA-256 | `%s` |" % rs.get("param_cases_sha256", C00_V1["param_cases.py"] if case == "C00_PIPELINE_CHECK" else "(not recorded)"),
          ""]
    if case == "C00_PIPELINE_CHECK":
        A += ["C00 was solved with journal version 1 (archived as `Journals/Archive/solve_param_v1_used_for_C00.py` and "
              "`param_cases_v1_used_for_C00.py`; the version-1 journal did not yet record its own hash, so the archived file hashes are "
              "given above). Version 2, used for every parametric case, differs only in lines that C00 does not execute (the V-case "
              "initial-field rule and the hash record) and one audit-row label; the diff is `Journals/Archive/diff_v1_to_v2_*.txt`.", ""]
    A += ["**Overall: %s**" % info["status"], ""]
    open(os.path.join(d, "CASE_AUDIT.md"), "w", encoding="utf-8").write("\n".join(A) + "\n")


def main():
    P00 = extract(os.path.join(ROOT, "06_Fluent_CFD"), "Monitors/baseline_monitors.out")
    scrj = jload(os.path.join(PS, "Analytical_Screening", "screening_results.json"), {})
    smat = {m["case"]: m for m in scrj.get("matrix", [])}
    allinfo, table = {}, []
    base_row = dict(case="P00_BASELINE", variable="baseline", value="V 23.5; q'' 8000; t 10", units="-",
                    cells=159840, status="SOLVED (Section 5B reference)", valid=True, **{k: v for k, v in P00.items()
                                                                                             if not isinstance(v, dict)})
    table.append(base_row)
    for case in PC.ORDER:
        info, x = case_checks(case, P00)
        scr = None
        if x is not None and case in smat:
            s = smat[case]
            scr = {"rows": [("Re inlet", s["Re_in"], x["Re_in"], "rel"), ("Δp [Pa]", s["anch_dp_Pa"], x["dp_Pa"], "rel"),
                            ("T_out [K]", s["anch_T_out_K"], x["T_out_K"], "abs"),
                            ("T max interface [K]", s["anch_T_interface_max_K"], x["T_interface_max_K"], "abs"),
                            ("T max fluid [K]", s["anch_T_fluid_max_K"], x["T_fluid_max_K"], "abs"),
                            ("T max solid, cell [K]", s["anch_T_solid_max_K"], x["T_solid_cell_max_K"], "abs"),
                            ("T solid mean [K]", s["anch_T_solid_mean_K"], x["T_solid_mean_K"], "abs"),
                            ("T solid min [K]", s["anch_T_solid_min_K"], x["T_solid_cell_min_K"], "abs"),
                            ("Q [W]", s["anch_Q_W"], x["Q_heated_wall_W"], "rel"),
                            ("y+ max", s["anch_yplus_max"], x["yplus_max"], "rel")],
                   # changes from P00: screening change vs CFD change (both relative to their own P00 value)
                   "delta_vs_P00": {
                       "dp_pct": {"screening": pct(s["anch_dp_Pa"], 438.13), "cfd": pct(x["dp_Pa"], P00["dp_Pa"])},
                       "T_out_K": {"screening": s["anch_T_out_K"] - 368.93, "cfd": x["T_out_K"] - P00["T_out_K"]},
                       "T_interface_max_K": {"screening": s["anch_T_interface_max_K"] - 555.27,
                                             "cfd": x["T_interface_max_K"] - P00["T_interface_max_K"]},
                       "T_solid_cell_max_K": {"screening": s["anch_T_solid_max_K"] - 562.13,
                                              "cfd": x["T_solid_cell_max_K"] - P00["T_solid_cell_max_K"]},
                       "T_solid_mean_K": {"screening": s["anch_T_solid_mean_K"] - 525.48,
                                          "cfd": x["T_solid_mean_K"] - P00["T_solid_mean_K"]},
                       "Re_in_pct": {"screening": pct(s["Re_in"], smat["P00_BASELINE"]["Re_in"]),
                                     "cfd": pct(x["Re_in"], P00["Re_in"])},
                       "yplus_max_pct": {"screening": pct(s["anch_yplus_max"], 0.58484),
                                         "cfd": pct(x["yplus_max"], P00["yplus_max"])}}}
        info["screening"] = scr
        info["extracted"] = x
        allinfo[case] = info
        write_case_docs(case, info, x, P00, scr)
        cd, rr = PC.CASES[case], PC.resolved(case)
        row = dict(case=case, variable=cd["variable"], value=cd["value"], units=cd["units"], cells=rr["COUNTS"][0],
                   status=info["status"], valid=info.get("valid"))
        if x is not None:
            row.update({k: v for k, v in x.items() if not isinstance(v, dict)})
        table.append(row)
    # machine-readable table with % / K change from P00
    cols = ["case", "variable", "value", "units", "cells", "status", "valid", "iterations", "mdot_in_kg_s", "mdot_out_kg_s",
            "Re_in", "Re_out", "dp_Pa", "T_in_bulk_K", "T_out_K", "Q_heated_wall_W", "Q_interface_W", "T_solid_max_K",
            "T_solid_cell_max_K", "T_interface_max_K", "T_fluid_max_K", "T_outer_avg_K", "T_interface_avg_K",
            "T_solid_mean_K", "T_solid_cell_min_K", "yplus_min", "yplus_mean", "yplus_max", "mass_error_monitor",
            "energy_error_monitor", "A_heated_m2", "qpp_heated_area_avg_W_m2"]
    chg = [("dp_Pa", "rel"), ("T_out_K", "abs"), ("T_solid_max_K", "abs"), ("T_interface_max_K", "abs"),
           ("T_solid_mean_K", "abs"), ("Q_heated_wall_W", "rel"), ("Re_in", "rel"), ("yplus_max", "rel"), ("mdot_in_kg_s", "rel")]
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "PARAMETRIC_CFD_RESULTS.csv"), "w", newline="") as fh:
        fh.write("# RE-ANALYSIS 2026 - Section 9B-1 CFD parametric results (newly generated Fluent solutions, not recovered data). "
                 "Changes are vs P00_BASELINE: *_pct = relative %, *_dK = kelvin.\n")
        w = csv.writer(fh)
        w.writerow(cols + [k + ("_pct" if kind == "rel" else "_dK") for k, kind in chg])
        for row in table:
            vals = [row.get(c, "") for c in cols]
            for k, kind in chg:
                if row.get(k) in (None, ""):
                    vals.append("")
                else:
                    vals.append("%.6g" % (pct(row[k], P00[k]) if kind == "rel" else row[k] - P00[k]))
            w.writerow(["%.10g" % v if isinstance(v, float) else v for v in vals])
    json.dump({"P00": P00, "cases": allinfo}, open(os.path.join(RES, "parametric_cfd_results.json"), "w"), indent=2, default=str)
    json.dump({c: allinfo[c]["screening"] for c in allinfo}, open(os.path.join(RES, "screening_comparison.json"), "w"), indent=2)
    # final table
    T = ["# Section 9B-1 — CFD parametric results table", "",
         "> **RE-ANALYSIS 2026 — newly generated Fluent results, not recovered originals. No measured data exists or is used.**",
         "> Generated by `Scripts/post_9B1.py` from the raw case outputs. Definitions identical to P00 (`Planning/OUTPUT_DEFINITIONS.md`).", "",
         "## 1. Results", "",
         "| Case | Variable | Value | Cells | Δp [Pa] | T_out [K] | Tmax solid [K] | Q [W] | Re_in | y+ max | Mass error | Energy error | Status |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for row in table:
        if row.get("dp_Pa") in (None, ""):
            T.append("| %s | %s | %s %s | %s | — | — | — | — | — | — | — | — | %s |" % (row["case"], row["variable"], row["value"],
                                                                                 row["units"], row["cells"], row["status"]))
            continue
        me = row.get("mass_error_monitor", row.get("mass_error"))
        ee = row.get("energy_error_monitor", row.get("energy_error"))
        T.append("| %s | %s | %s %s | %s | %.2f | %.2f | %.2f | %.2f | %.0f | %.4f | %.1e | %.1e | %s |" %
                 (row["case"], row["variable"], row["value"], row["units"] if row["units"] != "-" else "", row["cells"],
                  row["dp_Pa"], row["T_out_K"], row["T_solid_max_K"], row["Q_heated_wall_W"], row["Re_in"], row["yplus_max"],
                  me, ee, row["status"]))
    T += ["", "Tmax solid = maximum over the solid including its boundary facets (outer-wall facet maximum). Mass error = "
          "|ṁ_in + ṁ_out| / ṁ_in; energy error = |Σ boundary heat rates| / Q_wall (monitor precision).", "",
          "## 2. Change from P00", "",
          "| Case | Δp | T_out | Tmax solid | T interface max | T solid mean | Q | Re_in | y+ max |",
          "|---|---|---|---|---|---|---|---|---|"]
    for row in table[1:]:
        if row.get("dp_Pa") in (None, ""):
            T.append("| %s | — | — | — | — | — | — | — | — |" % row["case"])
            continue
        T.append("| %s | %+.2f %% | %+.2f K | %+.2f K | %+.2f K | %+.2f K | %+.2f %% | %+.2f %% | %+.2f %% |" %
                 (row["case"], pct(row["dp_Pa"], P00["dp_Pa"]), row["T_out_K"] - P00["T_out_K"],
                  row["T_solid_max_K"] - P00["T_solid_max_K"], row["T_interface_max_K"] - P00["T_interface_max_K"],
                  row["T_solid_mean_K"] - P00["T_solid_mean_K"], pct(row["Q_heated_wall_W"], P00["Q_heated_wall_W"]),
                  pct(row["Re_in"], P00["Re_in"]), pct(row["yplus_max"], P00["yplus_max"])))
    open(os.path.join(RES, "PARAMETRIC_CFD_TABLE.md"), "w", encoding="utf-8").write("\n".join(T) + "\n")
    for c, i in allinfo.items():
        print("%-20s %-28s %s" % (c, i["status"], "" if i.get("valid") else i.get("why", i.get("failed_checks"))))
    print("POST-9B1-DONE")


if __name__ == "__main__":
    main()
