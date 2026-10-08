# -*- coding: utf-8 -*-
"""SECTION 9B-2 Part R - case validity scan (RE-ANALYSIS 2026).
For every structural case: solver output (solve.out, file0.err) of LC1 / LC2 / buckling / S3 -> errors, warnings (text,
de-duplicated), licence messages, pivot / rigid-body messages; Mechanical summary (FATAL, solution states, mesh
metrics, gate result); CFD validity from 9B-1 (parametric_cfd_results.json); temperature range vs the material tables
(E(T) and S_y(T): 20-400 degC; secant alpha(T): 93.33-537.78 degC, held constant below 93.33 degC as in MAPDL).
Usage: python validity_9B2.py <project_root> <out_json>"""
import os, sys, json, re, glob

ROOT, OUTJ = sys.argv[1], sys.argv[2]
PS = os.path.join(ROOT, "10_Parametric_Study")
SC = os.path.join(PS, "Structural_Cases")
CFDJ = json.load(open(os.path.join(PS, "CFD_Results", "parametric_cfd_results.json")))
CASES = ["C00_PIPELINE_CHECK", "V01_LOW", "V03_HIGH", "Q01_LOW", "Q03_HIGH", "T01_THIN", "T03_THICK", "M01_T01_STRUCT_NR5", "M02_T03_STRUCT_NR5", "S3_LC2_INTERMEDIATE"]


KNOWN = [  # warning categories seen and explained in 7B / 8A / 8B (STRUCTURAL_AUDIT.md, BUCKLING_AUDIT.md)
    (r"ALPX of material 1 is evaluated at a temperature of 26.85", "secant-alpha re-referencing to TREF 26.85 degC (MPAMOD) - 7B, expected"),
    (r"Element shape checking is currently inactive", "Mechanical default (SHPP off); mesh quality checked separately - expected"),
    (r"Some entities requested in the \*VGET were undefined", "APDL snippet: SOLID186 mid-side nodes carry no nodal stress - 7B, expected"),
    (r"out-of-core memory", "performance only (sparse solver out-of-core mode)"),
    (r"elapsed time exceeds the CPU time", "performance only"),
    (r"linear perturbation analysis with contact usually requires", "S3 buckling advisory: the only contact pair is the bonded "
     "(KEYOPT(12)=5) MPC force-distributed remote-point constraint, whose status cannot change; every buckling case of the "
     "project (S1, S2, S3, design cases) uses a small-deflection (NLGEOM off) pre-stress by design; the MPC outlet block "
     "reproduced the expected column behaviour in B03 - explained"),
]


def classify_warning(txt):
    for pat, cat in KNOWN:
        if re.search(pat, txt):
            return cat
    return "UNCLASSIFIED - needs explanation"


def scan(path):
    if not os.path.isfile(path):
        return None
    t = open(path, errors="ignore").read()
    L = t.splitlines()
    warns, errs = [], []
    for i, l in enumerate(L):
        if "*** WARNING ***" in l or "*** ERROR ***" in l:
            txt = " ".join(x.strip() for x in L[i + 1:i + 5] if x.strip() and "***" not in x)[:400]
            (warns if "WARNING" in l else errs).append(re.sub(r"\s+", " ", txt))
    cats = {}
    for w in warns:
        k = classify_warning(w)
        cats[k] = cats.get(k, 0) + 1
    return {"file": os.path.basename(path), "warnings": len(warns), "errors": len(errs), "warning_categories": cats,
            "unclassified_warnings": sorted(set(w for w in warns if classify_warning(w).startswith("UNCLASSIFIED"))),
            "warning_texts": sorted(set(warns)), "error_texts": sorted(set(errs)),
            "licence_messages": sorted(set(re.findall(r"(?i)[^\n]*licen[sc]e[^\n]*(?:fail|exceed|limit|denied)[^\n]*", t)))[:10],
            "pivot_or_rigid_body": sorted(set(re.findall(r"(?i)[^\n]*(?:small pivot|negative pivot|zero pivot|rigid body motion|singular)[^\n]*", t)))[:10],
            "solution_done": ("FINISH SOLUTION PROCESSING" in t) and ("RUN COMPLETED" in t)} if path.endswith("solve.out") else {
            "file": os.path.basename(path), "warnings": len(warns), "errors": len(errs)}


out = {"note": "RE-ANALYSIS 2026 - Section 9B-2 case validity scan (Part R)", "cases": {}}
for c in CASES:
    d = os.path.join(SC, c)
    so = os.path.join(d, "Solver_Output")
    E = {"solver": {}}
    for sub in sorted(os.listdir(so)) if os.path.isdir(so) else []:
        E["solver"][sub] = {"solve.out": scan(os.path.join(so, sub, "solve.out")), "file0.err": scan(os.path.join(so, sub, "file0.err"))}
    sf = os.path.join(d, "Audits", "summary_%s.json" % c) if c != "S3_LC2_INTERMEDIATE" else os.path.join(d, "Audits", "summary_S3_solve.json")
    pf = os.path.join(d, "Audits", "presolve_audit_%s.json" % c) if c != "S3_LC2_INTERMEDIATE" else os.path.join(d, "Audits", "presolve_audit_S3_solve.json")
    if os.path.isfile(sf):
        S = json.load(open(sf))
        E["fatal"] = S.get("FATAL")
        E["final_states"] = S.get("final_states")
        E["mesh"] = S.get("mesh")
        mm = S.get("mesh_metrics") or {}
        E["mesh_metrics"] = {k: mm.get(k) for k in ("JacobianRatio", "ElementQuality", "AspectRatio")}
        E["messages"] = {k: v.get("messages") for k, v in S.get("cases", {}).items()}
        E["mapping"] = S.get("mapping")
    if os.path.isfile(pf):
        P = json.load(open(pf))
        E["gate"] = P.get("gate"); E["gate_checks"] = len(P.get("checks", []))
        E["gate_failed"] = [x["check"] for x in P.get("checks", []) if not x["pass"]]
    cfd = CFDJ["cases"].get({"M01_T01_STRUCT_NR5": "T01_THIN", "M02_T03_STRUCT_NR5": "T03_THICK"}.get(c, c))
    if cfd:
        E["cfd"] = {"status": cfd.get("status"), "valid": cfd.get("valid"), "failed_checks": cfd.get("failed_checks")}
    elif c == "S3_LC2_INTERMEDIATE":
        E["cfd"] = {"status": "uses the P00 (Section 5B) CFD field", "valid": True}
    # temperature range vs material tables (mapped range from the Mechanical summary)
    mp = (E.get("mapping") or {}).get("LC2") or {}
    src = "Mechanical imported-load summary (LC2)"
    if not mp and c == "S3_LC2_INTERMEDIATE":   # S3 summary carries no mapping block: T_used column of the S3 static table
        tab = os.path.join(so, "S3_STATIC", "s7b_nodal.csv")
        if os.path.isfile(tab):
            tv, npil = [], 0
            for l in open(tab).readlines()[1:]:
                f = l.split(",")
                if len(f) < 15:
                    continue
                if (float(f[1]) ** 2 + float(f[2]) ** 2) ** 0.5 < 1e-6:   # remote-point pilot node on the axis (no solid node there)
                    npil += 1
                    continue
                tv.append(float(f[14]))
            mp = {"min_C": round(min(tv), 2), "max_C": round(max(tv), 2)}
            src = ("T_used column of Solver_Output/S3_STATIC/s7b_nodal.csv (P00 field, same External Data as 7B); %d solid nodes, "
                   "%d pilot node(s) on the axis excluded" % (len(tv), npil))
    if mp:
        tmin, tmax = mp.get("min_C"), mp.get("max_C")
        E["material_range"] = {"mapped_T_C": [tmin, tmax], "E_and_Sy_table_C": [20, 400], "alpha_table_C": [93.33, 537.78],
                               "inside_E_Sy_table": tmin >= 20 and tmax <= 400, "inside_alpha_table": tmin >= 93.33 and tmax <= 537.78,
                               "source": src}
    out["cases"][c] = E
    tot_w = sum((v["solve.out"] or {}).get("warnings", 0) for v in E["solver"].values())
    tot_e = sum((v["solve.out"] or {}).get("errors", 0) for v in E["solver"].values())
    print(c, "gate", E.get("gate"), "fatal", E.get("fatal"), "solve.out warnings", tot_w, "errors", tot_e,
          "material range ok", (E.get("material_range") or {}).get("inside_E_Sy_table"))
json.dump(out, open(OUTJ, "w"), indent=1)
