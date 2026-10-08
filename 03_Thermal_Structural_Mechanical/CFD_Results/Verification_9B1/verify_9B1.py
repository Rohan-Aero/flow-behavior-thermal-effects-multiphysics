# -*- coding: utf-8 -*-
"""Section 9B-1 - INDEPENDENT verification of the CFD parametric cases, from the raw files only.

RE-ANALYSIS 2026. This script does not import extract_case.py, post_9B1.py, param_cases.py or any
Fluent journal. It re-parses Fluent's own reports, the ASCII face exports, the monitor histories, the settings
snapshots and the CAD / mesh records, recomputes every reported quantity by a second route where one exists, and
compares with the published PARAMETRIC_CFD_RESULTS.csv and PARAMETRIC_CFD_TABLE.md.
Run with the ANSYS-bundled CPython 3.10:  python verify_9B1.py
"""
import os, sys, re, csv, json, math, hashlib

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"<PROJECT_ROOT>"
PS = os.path.join(ROOT, "10_Parametric_Study")
CFD = os.path.join(PS, "CFD_Cases")
RES = os.path.join(PS, "CFD_Results")
P00D = os.path.join(ROOT, "06_Fluent_CFD")
CASES = ["C00_PIPELINE_CHECK", "V01_LOW", "V03_HIGH", "Q01_LOW", "Q03_HIGH", "T01_THIN", "T03_THICK"]
# independent restatement of the approved matrix (PARAMETRIC_CASE_MATRIX.csv) and the frozen baseline
V0, Q0, DO0, DI, L, D = 23.5, 8000.0, 0.040, 0.020, 0.600, 0.020
EXPECT = {"C00_PIPELINE_CHECK": dict(V=23.5, q=8000.0, Do=0.040, cells=159840, paths=set()),
          "V01_LOW": dict(V=21.15, q=8000.0, Do=0.040, cells=159840, paths={"vel", "ti"}),
          "V03_HIGH": dict(V=25.85, q=8000.0, Do=0.040, cells=159840, paths={"vel", "ti"}),
          "Q01_LOW": dict(V=23.5, q=7200.0, Do=0.040, cells=159840, paths={"q"}),
          "Q03_HIGH": dict(V=23.5, q=8800.0, Do=0.040, cells=159840, paths={"q"}),
          "T01_THIN": dict(V=23.5, q=8000.0 * 40 / 36, Do=0.036, cells=12 * 12 * 90 + 24 * 48 * 90 + 9 * 48 * 90, paths={"q"}),
          "T03_THICK": dict(V=23.5, q=8000.0 * 40 / 44, Do=0.044, cells=12 * 12 * 90 + 24 * 48 * 90 + 12 * 48 * 90, paths={"q"})}
PATHS = {"vel": "/setup/boundary_conditions/velocity_inlet/fluid_inlet/momentum/velocity_magnitude/value",
         "ti": "/setup/boundary_conditions/velocity_inlet/fluid_inlet/turbulence/turbulent_intensity",
         "q": "/setup/boundary_conditions/wall/heated_outer_wall/thermal/heat_flux/value"}
AT = [250.0, 300.0, 350.0, 400.0, 450.0, 500.0, 550.0, 600.0]
AMU = [1.596e-5, 1.846e-5, 2.082e-5, 2.301e-5, 2.507e-5, 2.701e-5, 2.884e-5, 3.058e-5]
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append({"check": name, "ok": bool(ok), "detail": detail})
    print("%-4s %s  %s" % ("PASS" if ok else "FAIL", name, detail))


def mu(T):
    for i in range(len(AT) - 1):
        if AT[i] <= T <= AT[i + 1]:
            return AMU[i] + (AMU[i + 1] - AMU[i]) * (T - AT[i]) / (AT[i + 1] - AT[i])
    raise ValueError(T)


def rep(path):
    d = {}
    for l in open(path, errors="ignore"):
        t = l.split()
        if len(t) == 2:
            try:
                d[t[0]] = float(t[1])
            except ValueError:
                pass
    return d


def mon(path):
    hdr, rows = None, []
    for l in open(path, errors="ignore"):
        s = l.strip()
        if s.startswith('("Iteration"'):
            hdr = re.findall(r'"([^"]+)"', s)
        elif hdr and s[:1].isdigit():
            rows.append([float(v) for v in s.split()])
    return hdr, rows


def faces(path):
    with open(path) as fh:
        h = [c.strip() for c in fh.readline().split(",")]
        i0 = h.index("face-area-magnitude")
        names = h[i0:]
        cols = {n: [] for n in names}
        for l in fh:
            v = l.split(",")
            for k, n in enumerate(names):
                cols[n].append(float(v[i0 + k]))
    return cols


def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, p + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, "%s[%d]" % (p, i))
    else:
        yield p, o


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest().upper()


def solve_case(d, monfile):
    A = os.path.join(d, "Audit")
    E = os.path.join(d, "Exports")
    fm, fh = rep(os.path.join(A, "fluent_flux_mass.txt")), rep(os.path.join(A, "fluent_flux_heat.txt"))
    pa, tm = rep(os.path.join(A, "fluent_si_p_area.txt")), rep(os.path.join(A, "fluent_si_T_mass.txt"))
    tx, ar = rep(os.path.join(A, "fluent_si_Twall_max.txt")), rep(os.path.join(A, "fluent_si_areas.txt"))
    yx, ya = rep(os.path.join(A, "fluent_si_yplus_max.txt")), rep(os.path.join(A, "fluent_si_yplus_area.txt"))
    bi, bo = faces(os.path.join(E, "boundary_inlet.csv")), faces(os.path.join(E, "boundary_outlet.csv"))
    wi, wo = faces(os.path.join(E, "wall_interface.csv")), faces(os.path.join(E, "wall_outer.csv"))
    hdr, rows = mon(os.path.join(d, monfile))
    c = {n: i for i, n in enumerate(hdr)}
    last = rows[-1]
    r = {}
    # route 1: Fluent's own reports (the published definitions)
    r["dp"] = pa["fluid_inlet"] - pa["fluid_outlet"]
    r["T_out"] = tm["fluid_outlet"]
    r["Q"] = fh["heated_outer_wall"]
    r["Tmax_solid"] = max(tx["heated_outer_wall"], tx["fluid_solid_interface"])
    r["yplus_max"], r["yplus_mean"] = yx["fluid_solid_interface"], ya["fluid_solid_interface"]
    r["mdot_in"], r["A_in"], r["A_heated"] = fm["fluid_inlet"], ar["fluid_inlet"], ar["heated_outer_wall"]
    r["Re_in"] = fm["fluid_inlet"] / ar["fluid_inlet"] * D / mu(tm["fluid_inlet"])
    r["mass_err"] = abs(last[c["mdot_in"]] + last[c["mdot_out"]]) / last[c["mdot_in"]]
    r["energy_err"] = abs(last[c["q_net_all"]]) / last[c["q_heated_wall"]]
    r["iterations"] = int(last[0])
    # route 2: the exported face data
    def aw(cols, f):
        return sum(a * v for a, v in zip(cols["face-area-magnitude"], cols[f])) / sum(cols["face-area-magnitude"])
    def mw(cols):
        m = [a * rho * w for a, rho, w in zip(cols["face-area-magnitude"], cols["density"], cols["z-velocity"])]
        return sum(mi * t for mi, t in zip(m, cols["temperature"])) / sum(m)
    r2 = {"dp": aw(bi, "pressure") - aw(bo, "pressure"), "T_out": mw(bo), "T_in": mw(bi),
          "Q": sum(a * q for a, q in zip(wo["face-area-magnitude"], wo["heat-flux"])),
          "Tmax_solid": max(max(wo["temperature"]), max(wi["temperature"])),
          "yplus_max": max(wi["y-plus"]), "yplus_mean": aw(wi, "y-plus"),
          "A_in": sum(bi["face-area-magnitude"]), "A_heated": sum(wo["face-area-magnitude"]),
          "q_set_faces": (min(wo["heat-flux"]), max(wo["heat-flux"]))}
    r2["Re_in"] = fm["fluid_inlet"] / r2["A_in"] * D / mu(r2["T_in"])
    return r, r2, (hdr, rows)


def main():
    out = {}
    p00, p00b, p00m = solve_case(P00D, "Monitors/baseline_monitors.out")
    csvrows = {}
    try:
        with open(os.path.join(RES, "PARAMETRIC_CFD_RESULTS.csv")) as fh:
            fh.readline()
            for row in csv.DictReader(fh):
                csvrows[row["case"]] = row
    except Exception as e:
        check("PARAMETRIC_CFD_RESULTS.csv readable", False, str(e))
    table = open(os.path.join(RES, "PARAMETRIC_CFD_TABLE.md"), encoding="utf-8").read() if os.path.isfile(
        os.path.join(RES, "PARAMETRIC_CFD_TABLE.md")) else ""
    s0 = json.load(open(os.path.join(CFD, "C00_PIPELINE_CHECK", "Audit", "settings_state_P00_case.json")))
    base_state = dict(walk(s0))
    meshj = json.load(open(os.path.join(PS, "Mesh_Checks", "mesh_checks_9B1.json")))
    for case in CASES:
        e = EXPECT[case]
        d = os.path.join(CFD, case)
        A = os.path.join(d, "Audit")
        rs = json.load(open(os.path.join(A, "run_summary.json")))
        check("%s run status CONVERGED" % case, rs.get("status") == "CONVERGED", rs.get("status"))
        if rs.get("status") != "CONVERGED":
            continue
        r, r2, (hdr, rows) = solve_case(d, "Monitors/%s_monitors.out" % case)
        # --- the case differs from P00 ONLY in its intended variable (settings snapshots re-diffed here)
        st = dict(walk(json.load(open(os.path.join(A, "settings_state_%s_case.json" % case)))))
        diff = {p for p in set(st) | set(base_state) if st.get(p, "<absent>") != base_state.get(p, "<absent>")}
        check("%s settings diff = intended paths only" % case, diff == {PATHS[k] for k in e["paths"]}, sorted(diff))
        check("%s inlet velocity read back" % case, abs(st[PATHS["vel"]] - e["V"]) < 1e-12, st[PATHS["vel"]])
        ti_exp = 0.16 * (29957.0 * e["V"] / V0) ** (-0.125)
        check("%s turbulence intensity = 0.16 Re^-1/8" % case, abs(st[PATHS["ti"]] - ti_exp) < 1e-12, st[PATHS["ti"]])
        check("%s heat flux read back" % case, abs(st[PATHS["q"]] - e["q"]) < 1e-9, st[PATHS["q"]])
        check("%s heat flux on every outer face = set value" % case,
              abs(r2["q_set_faces"][0] - e["q"]) < 1e-3 and abs(r2["q_set_faces"][1] - e["q"]) < 1e-3, r2["q_set_faces"])
        # --- audits and convergence
        for k in ("1_presolve", "2_final_schemes", "3_final"):
            a = json.load(open(os.path.join(A, "setup_audit_%s.json" % k)))
            bad = [x for x in a["rows"] if not x["ok"]]
            check("%s audit %s: 0 failed of %d" % (case, k, len(a["rows"])), not bad, [x["item"] for x in bad][:3])
        ev = json.load(open(os.path.join(A, "convergence_evaluations.json")))
        fin = ev[-1]
        check("%s converged and confirmed (final evaluation)" % case,
              fin.get("converged") and fin["tag"].startswith("confirmation") and all(v["ok"] for v in fin["checks"].values()),
              fin["tag"])
        # recompute the plateau from the raw monitor history (last 200 second-order rows)
        c = {n: i for i, n in enumerate(hdr)}
        win = rows[-200:]
        drift = max(max(x[c[n]] for x in win) - min(x[c[n]] for x in win) for n in ("T_out_bulk", "T_solid_max", "T_wall_max", "T_outer_max"))
        dpw = [x[c["p_in_area"]] - x[c["p_out_area"]] for x in win]
        check("%s plateau recomputed: T drift < 0.1 K, dp drift < 0.1 %%" % case,
              drift < 0.1 and (max(dpw) - min(dpw)) / (sum(dpw) / len(dpw)) < 1e-3, "%.2e K" % drift)
        check("%s mass and energy balance" % case, r["mass_err"] < 1e-4 and r["energy_err"] < 5e-3,
              "%.1e / %.1e" % (r["mass_err"], r["energy_err"]))
        # --- property tables at EVERY iteration (own parse of the monitor file)
        fl = [x[c[n]] for x in rows for n in ("T_fluid_max", "T_fluid_min", "T_wall_max", "T_out_bulk", "T_in_bulk")]
        so = [x[c[n]] for x in rows for n in ("T_solid_max", "T_solid_min", "T_outer_max", "T_outer_avg", "T_inner_avg")]
        check("%s air 250-600 K at every iteration" % case, 250 <= min(fl) and max(fl) <= 600, "%.2f-%.2f K" % (min(fl), max(fl)))
        check("%s Inconel 293.15-673.15 K at every iteration" % case, 293.15 <= min(so) and max(so) <= 673.15,
              "%.2f-%.2f K" % (min(so), max(so)))
        msgs = 0
        for fn in os.listdir(os.path.join(d, "Logs")):
            if fn.endswith("_stdout.txt"):
                for l in open(os.path.join(d, "Logs", fn), errors="ignore"):
                    if l.startswith("S5B ") or l.lstrip().startswith(">>>"):
                        continue
                    if re.search(r"limited to .{0,60}?\bin\s+\d+\s+(cells|faces)|reversed flow (in|on)\s+\d+|diverg[e]nce detected", l, re.I):
                        msgs += 1
        check("%s no limiter / reversed-flow / divergence message in the solver output" % case, msgs == 0, msgs)
        # --- second route agrees with Fluent's reports
        for k, tol, kind in (("dp", 1e-6, "rel"), ("T_out", 1e-4, "abs"), ("Q", 1e-6, "rel"), ("Tmax_solid", 1e-4, "abs"),
                             ("yplus_max", 1e-6, "rel"), ("yplus_mean", 1e-6, "rel"), ("Re_in", 1e-6, "rel"), ("A_heated", 1e-7, "rel")):
            err = abs(r2[k] - r[k]) / abs(r[k]) if kind == "rel" else abs(r2[k] - r[k])
            check("%s %s: face-export route = Fluent report" % (case, k), err < tol, "%.3g vs %.3g (err %.1e)" % (r2[k], r[k], err))
        check("%s y+ policy (max <= 1, mean <= 0.5)" % case, r["yplus_max"] <= 1.0 and r["yplus_mean"] <= 0.5,
              "%.4f / %.4f" % (r["yplus_max"], r["yplus_mean"]))
        check("%s Q = q'' x Fluent heated area" % case, abs(r["Q"] / (e["q"] * r["A_heated"]) - 1) < 1e-6, "%.6f W" % r["Q"])
        # --- mesh
        mz = json.load(open(os.path.join(A, "case_mesh_zones.json")))
        check("%s cells printed by Fluent = expected" % case, mz["mesh"]["cells"] == e["cells"], mz["mesh"]["cells"])
        check("%s Fluent min orthogonal quality > 0.1, no mesh warnings" % case,
              mz["mesh"]["min_orthogonal_quality"] > 0.1 and not mz["mesh"]["mesh_check_warnings"], mz["mesh"]["min_orthogonal_quality"])
        if case.startswith("T"):
            mc = meshj["cases"][case]
            mpath = os.path.join(PS, "Mesh_Checks", "Mesh_" + case, case + ".msh")
            check("%s mesh file = generated mesh (SHA-256)" % case, sha(mpath) == mc["file"]["sha256"], mc["file"]["sha256"][:16])
            poly = 48 * 2 * (e["Do"] / 2) * math.sin(math.pi / 48) * L
            check("%s Fluent heated area = 48-facet area of Do" % case, abs(r["A_heated"] / poly - 1) < 1e-7, "%.9e" % r["A_heated"])
            check("%s total heat input = P00 (Q held)" % case, abs(r["Q"] / p00["Q"] - 1) < 1e-6, "%.6f vs %.6f W" % (r["Q"], p00["Q"]))
        else:
            check("%s mesh = P00 medium mesh (SHA-256)" % case,
                  sha(os.path.join(P00D, "Case", "medium_mesh_used_for_baseline.msh")).startswith("2C6FCFB31108654D"), "")
        # --- EnSight export for 9B-2
        ens = os.path.join(d, "EnSight")
        fl_ = sorted(os.listdir(ens)) if os.path.isdir(ens) else []
        check("%s EnSight solid temperature export present" % case,
              all(x in fl_ for x in ("solid_domain_T.encas", "solid_domain_T.geo", "solid_domain_T.scl1")) and
              all(os.path.getsize(os.path.join(ens, x)) > 0 for x in fl_), fl_)
        # --- published CSV and table
        row = csvrows.get(case, {})
        for k, col, tol in (("dp", "dp_Pa", 1e-8), ("T_out", "T_out_K", 1e-6), ("Q", "Q_heated_wall_W", 1e-8),
                            ("Tmax_solid", "T_solid_max_K", 1e-6), ("Re_in", "Re_in", 1e-8), ("yplus_max", "yplus_max", 1e-7)):
            try:
                v = float(row[col])
                ok = abs(v - r[k]) <= tol * max(1.0, abs(r[k]))
            except Exception:
                v, ok = None, False
            check("%s CSV %s = recomputed" % (case, col), ok, v)
        for k, col, kind in (("dp", "dp_Pa_pct", "rel"), ("T_out", "T_out_K_dK", "abs"), ("Tmax_solid", "T_solid_max_K_dK", "abs"),
                             ("Q", "Q_heated_wall_W_pct", "rel"), ("Re_in", "Re_in_pct", "rel")):
            exp = (r[k] - p00[k]) / abs(p00[k]) * 100 if kind == "rel" else r[k] - p00[k]
            try:
                ok = abs(float(row[col]) - exp) < 1e-4 * max(1.0, abs(exp))
            except Exception:
                ok = False
            check("%s CSV %s = recomputed change from P00" % (case, col), ok, "%.4f" % exp)
        line = [l for l in table.splitlines() if l.startswith("| %s |" % case)]
        ok = bool(line) and all(("%.2f" % r[k]) in line[0] for k in ("dp", "T_out", "Tmax_solid", "Q"))
        check("%s table row shows the recomputed dp, T_out, Tmax, Q" % case, ok, line[0][:120] if line else "missing")
        out[case] = {"route1_reports": r, "route2_faces": {k: v for k, v in r2.items() if k != "q_set_faces"}}
    # --- C00 specifics
    h1, a = p00m
    h2, b = mon(os.path.join(CFD, "C00_PIPELINE_CHECK", "Monitors", "C00_PIPELINE_CHECK_monitors.out"))
    check("C00 monitor history bit-identical to P00 (all monitors, all iterations)", h1 == h2 and a == b, "%d rows" % len(b))
    e7 = os.path.join(ROOT, "07_Thermal_Analysis", "Temperature_Source", "EnSight")
    ec = os.path.join(CFD, "C00_PIPELINE_CHECK", "EnSight")
    same = all(sha(os.path.join(e7, f)) == sha(os.path.join(ec, f)) for f in os.listdir(e7))
    check("C00 EnSight export byte-identical to the 7A mapping source", same, sorted(os.listdir(e7)))
    # --- geometry (independent analytic values vs SpaceClaim)
    for case, Do in (("T01_THIN", 0.036), ("T03_THICK", 0.044)):
        m = json.load(open(os.path.join(PS, "Geometry_Checks", case, "cad_measurements.json")))
        pairs = [(m["bbox_solid"][3] - m["bbox_solid"][0], Do), (m["bbox_fluid"][3] - m["bbox_fluid"][0], DI),
                 (m["bbox_solid"][5] - m["bbox_solid"][2], L), (m["area_heated_outer"], math.pi * Do * L),
                 (m["solid_volume_m3"], math.pi / 4 * (Do ** 2 - DI ** 2) * L), (m["fluid_volume_m3"], math.pi / 4 * DI ** 2 * L),
                 (m["area_fluid_inlet"], math.pi / 4 * DI ** 2), (m["area_solid_inlet_end"], math.pi / 4 * (Do ** 2 - DI ** 2))]
        check("%s CAD = analytical (Do, Di, L, heated area, volumes, end areas)" % case,
              all(abs(x / y - 1) < 1e-9 for x, y in pairs), "max rel %.1e" % max(abs(x / y - 1) for x, y in pairs))
        check("%s derived q'' = Q_P00 / A_heated(CAD)" % case,
              abs(Q0 * math.pi * DO0 * L / m["area_heated_outer"] - EXPECT[case]["q"]) < 1e-9, "%.6f" % EXPECT[case]["q"])
    # P00 CAD and P00 CFD solution untouched by 9B-1: no file there was written after the first 9B-1 file
    t9 = os.path.getmtime(os.path.join(PS, "Mesh_Checks", "param_mesh.py"))
    for sub in ("03_CAD_Geometry", os.path.join("06_Fluent_CFD", "Case"), os.path.join("06_Fluent_CFD", "Data"),
                os.path.join("06_Fluent_CFD", "Audit"), os.path.join("06_Fluent_CFD", "Monitors"), os.path.join("06_Fluent_CFD", "Exports"),
                os.path.join("07_Thermal_Analysis", "Temperature_Source", "EnSight")):
        newest = max(os.path.getmtime(os.path.join(dp, f)) for dp, _, fs in os.walk(os.path.join(ROOT, sub)) for f in fs)
        check("%s not modified by 9B-1 (newest file older than the first 9B-1 file)" % sub, newest < t9,
              "newest %.0f s before" % (t9 - newest))
    # --- mesh rule
    def g(n, t):
        lo, hi = 1.0000001, 3.0
        for _ in range(200):
            x = 0.5 * (lo + hi)
            lo, hi = (x, hi) if 0.5e-3 * (x ** n - 1) / (x - 1) < t else (lo, x)
        return 0.5 * (lo + hi)
    gp = g(10, 0.010)
    for case, t, n in (("T01_THIN", 0.008, 9), ("T03_THICK", 0.012, 12)):
        check("%s solid layers = smallest n with growth <= 1.147 (P00 %.4f)" % (case, gp),
              g(n, t) <= 1.147 and g(n - 1, t) > 1.147, "n %d g %.4f; n-1 g %.4f" % (n, g(n, t), g(n - 1, t)))
        mc = meshj["cases"][case]
        check("%s fluid mesh identical to P00 (node coords + connectivity)" % case,
              all(mc["fluid_mesh_identical_to_P00"].values()), mc["fluid_mesh_identical_to_P00"])
    check("mesh wrapper regenerated the P00 medium mesh byte-identically", meshj["wrapper_validation"]["byte_identical"],
          meshj["wrapper_validation"]["sha256_regenerated"][:16])
    n_ok = sum(c["ok"] for c in CHECKS)
    res = {"n_checks": len(CHECKS), "n_pass": n_ok, "all_pass": n_ok == len(CHECKS), "checks": CHECKS, "values": out}
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_9B1_result.json"), "w"), indent=2, default=str)
    print("VERIFY 9B-1: %d/%d PASS" % (n_ok, len(CHECKS)))


if __name__ == "__main__":
    main()
