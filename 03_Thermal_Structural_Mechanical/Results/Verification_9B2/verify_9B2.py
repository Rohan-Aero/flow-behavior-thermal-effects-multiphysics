# -*- coding: utf-8 -*-
"""SECTION 9B-2 - independent verification of the parametric structural deliverables (RE-ANALYSIS 2026).

Written separately from post_9B2.py / tables_plots_9B2.py and does NOT import them. From the RAW solver tables it
recomputes, with its own code, the headline numbers of every case and compares them with the published CSV tables;
then it checks the gates, the rules of the brief and the integrity of the baseline folders.
Checks:
  V1  per case, from s7b_nodal.csv / s7b_react.csv / s8a_load_factors.csv + the LC2 input deck (corner nodes):
      LC2 max von Mises (corner nodes), LC2 end reaction and mean axial stress, LC1 max von Mises and max total
      deformation, max utilisation with S_y(T) (own interpolation), lambda1, P_cr = lambda1 x |F_inlet|;
      values must equal PARAMETRIC_STRUCTURAL_RESULTS.csv to its printed rounding
  V2  node counts < 128,000; gate PASS; 0 unmapped nodes (Mechanical summary); temperatures inside the tables
  V3  Part I label present for every lambda1 < 1 case (CSV status) and in PARAMETRIC_STRUCTURAL_RESULTS.md
  V4  support table: the same recomputation for S1 / S2 / S3; no 'best' / 'worst' word in the support deliverables;
      S2 re-extraction: the S1 re-extraction equals the 8A in-session table in every column, and the S2 table has
      u_theta = 0 at its NMOD-rotated (U_theta-constrained) end-face nodes
  V5  C00 control vs 7B/8A within the declared tolerances; M01/M02 vs T01/T03; B03 PASS; M03 criteria
  V6  15 figures exist and are PNG files; all six Results files exist
  V7  integrity: 08_Structural_Analysis file hashes equal the pre-9B-2 record (Audits/pre9B2_08_Structural_Analysis_hashes.csv)
Usage: python verify_9B2.py <project_root>"""
import os, sys, csv, json, hashlib, math, re
import numpy as np

ROOT = sys.argv[1]
PS = os.path.join(ROOT, "10_Parametric_Study")
SC = os.path.join(PS, "Structural_Cases")
RES = os.path.join(PS, "Results")
S8 = os.path.join(ROOT, "08_Structural_Analysis")
out = {"note": "RE-ANALYSIS 2026 - Section 9B-2 independent verification", "checks": []}


def check(name, ok, detail=""):
    out["checks"].append({"check": name, "pass": bool(ok), "detail": str(detail)[:400]})
    print("%s  %s  %s" % ("PASS" if ok else "FAIL", name, str(detail)[:160]))


def corners(ds):
    L = open(ds, errors="ignore").read().split("\n")
    i = next(k for k, l in enumerate(L) if l.lower().startswith("eblock")) + 2
    s = set()
    while not L[i].strip().startswith("-1"):
        s.update(int(L[i][k:k + 9]) for k in range(9, 81, 9))
        i += 1
    return s


def sy(tc):
    T = [20, 100, 200, 300, 400]; V = [1030e6, 1060e6, 1040e6, 1020e6, 1000e6]
    for a in range(4):
        if T[a] <= tc <= T[a + 1]:
            return V[a] + (V[a + 1] - V[a]) * (tc - T[a]) / (T[a + 1] - T[a])
    raise ValueError(tc)


def nodal(p, cs):
    a = np.loadtxt(p, delimiter=",", skiprows=1)
    a = a[np.hypot(a[:, 1], a[:, 2]) > 1e-6]
    c = np.array([int(n) in cs for n in a[:, 0]])
    vm = a[c, 12]; T = a[c, 14]
    u = np.array([v / sy(t) for v, t in zip(vm, T)])
    ut = np.sqrt(a[:, 4] ** 2 + a[:, 5] ** 2 + a[:, 6] ** 2)
    return {"vm": vm.max(), "util": u.max(), "utot": ut.max(), "Tmin": a[:, 14].min(), "Tmax": a[:, 14].max()}


def inlet_fz(p):
    a = np.atleast_2d(np.loadtxt(p, delimiter=",", skiprows=1))
    return a[np.abs(a[:, 3]) < 1e-9, 6].sum()


def lam1(d):
    return float(np.atleast_2d(np.loadtxt(os.path.join(d, "s8a_load_factors.csv"), delimiter=",", skiprows=1))[0, 1])


GEO = {"P00_BASELINE": (0.010, 0.020), "C00_PIPELINE_CHECK": (0.010, 0.020), "V01_LOW": (0.010, 0.020), "V03_HIGH": (0.010, 0.020),
       "Q01_LOW": (0.010, 0.020), "Q03_HIGH": (0.010, 0.020), "T01_THIN": (0.010, 0.018), "T03_THICK": (0.010, 0.022)}
rows = {}
with open(os.path.join(RES, "PARAMETRIC_STRUCTURAL_RESULTS.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(l for l in fh if not l.startswith("#")):
        rows[r["Case"]] = r


def close(a, b, nd):
    return abs(float(a) - round(b, nd)) <= 1.01 * 10 ** (-nd)


REC = {}
for tag, (ri, ro) in GEO.items():
    if tag == "P00_BASELINE":
        d1, d2 = os.path.join(S8, "LC1_Free_Expansion", "Solver_Output"), os.path.join(S8, "LC2_Restrained", "Solver_Output")
        db, ds = os.path.join(S8, "Buckling", "Mechanical", "LC2_Linear_Buckling", "Solver_Output"), os.path.join(d2, "LC2_solve_input_ds.dat")
    else:
        c = os.path.join(SC, tag)
        d1, d2, db = [os.path.join(c, "Solver_Output", k) for k in ("LC1", "LC2", "BUCKLING")]
        ds = os.path.join(c, "Audits", "Presolve_Inputs", "%s_LC2_presolve_ds.dat" % tag)
    if not os.path.isfile(os.path.join(d2, "s7b_nodal.csv")):
        check("V1 %s raw tables present" % tag, False, "missing")
        continue
    cs = corners(ds)
    n1, n2 = nodal(os.path.join(d1, "s7b_nodal.csv"), cs), nodal(os.path.join(d2, "s7b_nodal.csv"), cs)
    F = inlet_fz(os.path.join(d2, "s7b_react.csv")); A = math.pi * (ro ** 2 - ri ** 2); l1 = lam1(db)
    REC[tag] = {"LC1_vm": n1["vm"], "LC1_utot": n1["utot"], "LC2_vm": n2["vm"], "F": F, "sig": -abs(F) / A, "util": n2["util"], "lam": l1,
                "Pcr": l1 * abs(F), "T": [n2["Tmin"], n2["Tmax"]]}
    r = rows.get(tag, {})
    ok = bool(r) and close(r["LC2 max stress [MPa]"], n2["vm"] / 1e6, 3) and close(r["LC2 mean axial stress [MPa]"], -abs(F) / A / 1e6, 3) \
        and close(r["LC1 max stress [MPa]"], n1["vm"] / 1e6, 3) and close(r["Max deformation [mm]"], n1["utot"] * 1e3, 5) \
        and close(r["Yield utilization [-]"], n2["util"], 4) and close(r["Lambda1 [-]"], l1, 5) and close(r["Critical buckling load [kN]"], l1 * abs(F) / 1e3, 2)
    check("V1 %s: recomputed LC1/LC2/utilisation/lambda1/P_cr = CSV" % tag, ok,
          "LC2 %.3f MPa, sig %.3f, util %.4f, lam %.5f, Pcr %.2f kN" % (n2["vm"] / 1e6, -abs(F) / A / 1e6, n2["util"], l1, l1 * abs(F) / 1e3))
    check("V2 %s: temperatures inside the E/S_y tables (20-400 degC)" % tag, 20 <= n2["Tmin"] and n2["Tmax"] <= 400, REC[tag]["T"])
    if tag != "P00_BASELINE":
        S = json.load(open(os.path.join(SC, tag, "Audits", "summary_%s.json" % tag)))
        P = json.load(open(os.path.join(SC, tag, "Audits", "presolve_audit_%s.json" % tag)))
        unm = [c for c in P["checks"] if c["check"] == "no unmapped nodes"]
        check("V2 %s: gate PASS, 0 unmapped, nodes < 128,000, no FATAL" % tag,
              P["gate"] == "PASS" and unm and unm[0]["pass"] and S["mesh"]["nodes"] < 128000 and "FATAL" not in S,
              "%s, %d nodes" % (P["gate"], S["mesh"]["nodes"]))
    lam_ok = l1 >= 1 or ("pre-buckling equilibrium result" in r.get("Status", ""))
    check("V3 %s: Part I label present when lambda1 < 1" % tag, lam_ok, "lambda1 %.5f" % l1)
md = open(os.path.join(RES, "PARAMETRIC_STRUCTURAL_RESULTS.md"), encoding="utf-8").read() if os.path.isfile(os.path.join(RES, "PARAMETRIC_STRUCTURAL_RESULTS.md")) else ""
check("V3 PARAMETRIC_STRUCTURAL_RESULTS.md carries the Part I wording",
      "pre-buckling equilibrium result; linear stability criterion indicates loss of stability before the applied load level" in md)
# V4 support scenarios
srows = {}
with open(os.path.join(RES, "SUPPORT_SENSITIVITY_RESULTS.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(l for l in fh if not l.startswith("#")):
        srows[r["Scenario"]] = r
cs_b = corners(os.path.join(S8, "LC2_Restrained", "Solver_Output", "LC2_solve_input_ds.dat"))
x = os.path.join(SC, "S2_REEXTRACT")
s2 = nodal(os.path.join(x, "s2x_nodal.csv"), cs_b) if os.path.isfile(os.path.join(x, "s2x_nodal.csv")) else None
s3d = os.path.join(SC, "S3_LC2_INTERMEDIATE", "Solver_Output")
s3 = nodal(os.path.join(s3d, "S3_STATIC", "s7b_nodal.csv"), cs_b) if os.path.isfile(os.path.join(s3d, "S3_STATIC", "s7b_nodal.csv")) else None
sup = {"S1": (REC.get("P00_BASELINE", {}).get("LC2_vm"), REC.get("P00_BASELINE", {}).get("lam")),
       "S2": (s2["vm"] if s2 else None, lam1(os.path.join(S8, "Buckling", "Mechanical", "LC2NS_Linear_Buckling", "Solver_Output"))),
       "S3": (s3["vm"] if s3 else None, lam1(os.path.join(s3d, "S3_BUCKLING")) if s3 else None)}
for k, (vm, lm) in sup.items():
    r = srows.get(k, {})
    check("V4 %s: recomputed max stress and lambda1 = support CSV" % k, vm is not None and lm is not None and r
          and close(r["Max stress [MPa]"], vm / 1e6, 3) and close(r["Lambda1 [-]"], lm, 5), "vm %s lam %s" % (vm, lm))
v1p = os.path.join(x, "s1x_nodal.csv")
v0p = os.path.join(S8, "Buckling", "Mechanical", "LC2_prestress_resolve", "Solver_Output", "s7b_nodal.csv")
if os.path.isfile(v1p) and os.path.isfile(v0p):
    A1, A0 = np.loadtxt(v1p, delimiter=",", skiprows=1), np.loadtxt(v0p, delimiter=",", skiprows=1)
    same = A1.shape == A0.shape and np.array_equal(A1[:, 0], A0[:, 0])
    dmax = float(np.abs(A1 - A0).max()) if same else None
    check("V4 S2 re-extraction method: S1 re-extraction = 8A in-session table (all 15 columns identical)", same and dmax == 0.0, "max |diff| %s" % dmax)
else:
    check("V4 S2 re-extraction method: S1 re-extraction = 8A in-session table (all 15 columns identical)", False, "files missing")
if os.path.isfile(os.path.join(x, "s2x_nodal.csv")):
    dsn = os.path.join(S8, "Buckling", "Mechanical", "LC2NS_NoSway_Static", "Solver_Output", "ds.dat")
    nm = set(int(l.split(",")[1]) for l in open(dsn, errors="ignore") if l.lower().startswith("nmod,"))
    A2 = np.loadtxt(os.path.join(x, "s2x_nodal.csv"), delimiter=",", skiprows=1)
    m = np.isin(A2[:, 0].astype(int), list(nm))
    check("V4 S2 table: |u_theta| < 1e-9 m at every NMOD-rotated end-face node (U_theta = 0 support)", m.sum() > 0 and np.abs(A2[m, 5]).max() < 1e-9,
          "%d nodes, max |u_theta| %.2e m" % (m.sum(), np.abs(A2[m, 5]).max() if m.any() else float("nan")))
bad = []
for f in ("SUPPORT_SENSITIVITY_RESULTS.csv", "SUPPORT_SENSITIVITY_RESULTS.md", "PARAMETRIC_STRUCTURAL_RESULTS.md", "PARAMETRIC_TRENDS.md",
          "FINAL_PARAMETRIC_AUDIT.md", "PARAMETRIC_STRUCTURAL_RESULTS.csv"):
    p = os.path.join(RES, f)
    if os.path.isfile(p) and re.search(r"(?i)\b(best|worst)\b", open(p, encoding="utf-8").read()):
        bad.append(f)
check("V4 no 'best' / 'worst' label in the Results deliverables", not bad, bad)
# V5 controls
p0, c0 = REC.get("P00_BASELINE"), REC.get("C00_PIPELINE_CHECK")
if p0 and c0:
    check("V5 C00 vs 7B/8A: LC2 max vm, lambda1 and end reaction within 1e-5 (relative)",
          abs(c0["LC2_vm"] / p0["LC2_vm"] - 1) <= 1e-5 and abs(c0["lam"] / p0["lam"] - 1) <= 1e-5 and abs(c0["F"] / p0["F"] - 1) <= 1e-5,
          "vm %.2e, lam %.2e, F %.2e" % (c0["LC2_vm"] / p0["LC2_vm"] - 1, c0["lam"] / p0["lam"] - 1, c0["F"] / p0["F"] - 1))
pj = os.path.join(RES, "Data", "post_9B2_results.json")
if os.path.isfile(pj):
    MM = json.load(open(pj)).get("structural_mesh_checks_M01_M02", {})
    for k, v in MM.items():
        check("V5 %s: LC2 max vm, mean axial stress and lambda1 within 1e-4 of %s" % (k, v["reference"]), v["class_A_LC2_lambda1_le_1e-4"],
              {q: round(v["changes"][q]["rel"], 7) for q in ("LC2 max vm", "LC2 mean axial stress", "lambda1")})
b3 = os.path.join(SC, "B03_S3_TOY_BENCH", "b03_results.json")
check("V5 B03 toy benchmark PASS before the S3 solve", os.path.isfile(b3) and json.load(open(b3)).get("B03_PASS") is True)
m3 = os.path.join(PS, "Mesh_Checks", "m03_comparison.json")
check("V5 M03: all criteria PASS", os.path.isfile(m3) and json.load(open(m3)).get("T03_ADEQUATE") is True)
# V6 files
figs = [f for f in os.listdir(os.path.join(RES, "Figures")) if f.lower().endswith(".png")] if os.path.isdir(os.path.join(RES, "Figures")) else []
okf = len([f for f in figs if re.match(r"F(0[1-9]|1[0-5])_", f)]) == 15 and all(open(os.path.join(RES, "Figures", f), "rb").read(8) == b"\x89PNG\r\n\x1a\n" for f in figs)
check("V6 15 figures F01..F15 present, valid PNG", okf, len(figs))
need = ["PARAMETRIC_STRUCTURAL_RESULTS.csv", "SUPPORT_SENSITIVITY_RESULTS.csv", "PARAMETRIC_STRUCTURAL_RESULTS.md", "SUPPORT_SENSITIVITY_RESULTS.md",
        "PARAMETRIC_TRENDS.md", "FINAL_PARAMETRIC_AUDIT.md"]
check("V6 the six Part Y files exist", all(os.path.isfile(os.path.join(RES, f)) for f in need), [f for f in need if not os.path.isfile(os.path.join(RES, f))])
# V7 integrity of 08_Structural_Analysis
pre = os.path.join(SC, "Audits", "pre9B2_08_Structural_Analysis_hashes.csv")
if os.path.isfile(pre):
    ref = {}
    with open(pre, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            ref[r[list(r.keys())[0]]] = r
    keys = list(next(iter(ref.values())).keys())
    kh = "sha256"
    diff, miss = [], []
    for rel, r in ref.items():
        p = rel if os.path.isabs(rel) else os.path.join(S8, rel)
        if not os.path.isfile(p):
            miss.append(rel); continue
        hh = hashlib.sha256()
        with open(p, "rb") as fh:
            for blk in iter(lambda: fh.read(1 << 22), b""):
                hh.update(blk)
        h = hh.hexdigest().upper()
        if h != r[kh].upper():
            diff.append(rel)
    refn = set(os.path.normcase(rel if os.path.isabs(rel) else os.path.join(S8, rel)) for rel in ref)
    added = [os.path.relpath(os.path.join(d, f), S8) for d, _, fs in os.walk(S8) for f in fs if os.path.normcase(os.path.join(d, f)) not in refn]
    check("V7 08_Structural_Analysis unchanged (all %d pre-9B-2 files identical, none missing, none added)" % len(ref),
          not diff and not miss and not added, "changed %d %s, missing %d %s, added %d %s" % (len(diff), diff[:3], len(miss), miss[:3], len(added), added[:3]))
out["n_pass"] = sum(c["pass"] for c in out["checks"]); out["n_total"] = len(out["checks"])
json.dump(out, open(os.path.join(RES, "Verification_9B2", "verify_9B2_result.json"), "w"), indent=1)
print("TOTAL %d / %d PASS" % (out["n_pass"], out["n_total"]))
