# -*- coding: utf-8 -*-
"""SECTION 10A - independent verification of the 11_Final_Audit deliverables (RE-ANALYSIS 2026).
Standard library only; reads files, writes nothing outside 11_Final_Audit/Verification.
Usage: python -B verify_10A.py <project_root>"""
import os, sys, csv, json, re, glob, hashlib, datetime, collections
sys.dont_write_bytecode = True
ROOT = sys.argv[1]
FA = os.path.join(ROOT, "11_Final_Audit")
DOCS = ["MASTER_PROJECT_DATA.csv", "MASTER_PROJECT_DATA.md", "MASTER_ASSUMPTIONS.md", "MASTER_UNCERTAINTIES.md", "MASTER_TRACEABILITY.md",
        "FILE_INTEGRITY_AUDIT.md", "FINAL_ENGINEERING_AUDIT.md", "FINAL_ENGINEERING_SYNTHESIS.md"]
RES = []


def check(cid, name, ok, detail):
    RES.append({"id": cid, "check": name, "result": "PASS" if ok else "FAIL", "detail": detail})


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- V1 deliverables exist
missing = [d for d in DOCS if not os.path.isfile(os.path.join(FA, d))]
check("V1", "the eight 10A deliverables exist in 11_Final_Audit", not missing, {"missing": missing})
TXT = {d: read(os.path.join(FA, d)) for d in DOCS if d not in missing}

# ---------------------------------------------------------------- V2 re-analysis notice
no_notice = [d for d, s in TXT.items() if not re.search(r"RE-ANALYSIS 2026", s[:1500])]
check("V2", "re-analysis notice at the top of every deliverable", not no_notice, {"without_notice": no_notice})

# ---------------------------------------------------------------- V3 judgement words
FORB = re.compile(r"(?i)\bsafe\b|\bbest\b|\boptimal\b|failure[- ]proof")
QUOTED = re.compile(r"\"[^\"\n]*\"|“[^”\n]*”")
extra = os.path.join(ROOT, "Claude outputs", "README_NOT_AUTHORITATIVE.md")
hits = []
for d, s in list(TXT.items()) + ([("Claude outputs/README_NOT_AUTHORITATIVE.md", read(extra))] if os.path.isfile(extra) else []):
    for i, line in enumerate(s.splitlines(), 1):
        for m in FORB.finditer(QUOTED.sub("", line)):
            hits.append({"file": d, "line": i, "word": m.group(0)})
check("V3", "no judgement words (safe / best / optimal / failure-proof) outside quoted scan-term lists", not hits, {"hits": hits})

# ---------------------------------------------------------------- V4 CSV structure
with open(os.path.join(FA, "MASTER_PROJECT_DATA.csv"), encoding="utf-8") as fh:
    head = fh.readline()
    R = list(csv.DictReader(fh))
ids = [r["ID"] for r in R]
seq_ok = ids == ["M%03d" % i for i in range(1, len(R) + 1)]
ALLOWED = {"VERIFIED", "CROSS-CHECKED", "REPORTED", "INPUT", "DECISION", "INTERPRETATION"}
bad_status = sorted({r["Status"] for r in R} - ALLOWED)
cnt = collections.Counter(r["Status"] for r in R)
check("V4", "master CSV: header notice, sequential unique IDs, allowed statuses, no MISMATCH",
      head.startswith("# RE-ANALYSIS 2026") and seq_ok and not bad_status and len(set(ids)) == len(ids),
      {"rows": len(R), "sequential": seq_ok, "unexpected_status": bad_status, "status_counts": dict(cnt)})

# ---------------------------------------------------------------- V5 CSV values = recomputed master data
M = json.load(open(os.path.join(FA, "Data", "master_data_10A.json"), encoding="utf-8"))
byk = {(r["Group"], r["Parameter"]): r for r in R}


def rounding_ok(s, v):
    s = s.strip()
    try:
        x = float(s)
    except ValueError:
        return None
    mant = s.lower().split("e")[0]
    dec = len(mant.split(".")[1]) if "." in mant else 0
    exp = int(s.lower().split("e")[1]) if "e" in s.lower() else 0
    return abs(x - v) <= 0.5 * 10 ** (exp - dec) * (1 + 1e-9) + 1e-15


prob = []
for it in M["items"]:
    r = byk.get((it["group"], it["parameter"]))
    if r is None:
        prob.append({"item": it["parameter"], "issue": "not in CSV"}); continue
    if r["Status"] != it["status"]:
        prob.append({"item": it["parameter"], "issue": "status %s vs %s" % (r["Status"], it["status"])})
    if isinstance(it["value"], (int, float)) and not isinstance(it["value"], bool):
        ok = rounding_ok(r["Value"], float(it["value"]))
        if ok is False or ok is None:
            prob.append({"item": it["parameter"], "issue": "CSV %s vs recomputed %r" % (r["Value"], it["value"])})
mcnt = collections.Counter(it["status"] for it in M["items"])
check("V5", "every recomputed item is in the CSV with the same status and a correctly rounded value",
      not prob and all(cnt[k] == v for k, v in mcnt.items()), {"items": len(M["items"]), "recomputed_status_counts": dict(mcnt), "problems": prob})

# ---------------------------------------------------------------- V6 source files exist
NONFILE = {"master rows S1 lambda1 and first-yield factor", "master rows S2/S3 lambda1 and first-yield factor",
           "reaction tables (7B LC2, 8A LC2NS, 9B-2 S3)", "recomputed above"}
TOP = re.compile(r"^(\d\d_[A-Za-z_]+|PROJECT_STATE\.md)")


def paths_of(src):
    s = re.sub(r"\s*\([^)]*\)\s*$", "", src.strip())
    parts = [p.strip() for p in s.split(" + ")]
    out, first = [], parts[0]
    out.append(first)
    for p in parts[1:]:
        out.append(p if TOP.match(p) else os.path.dirname(first) + "/" + p)   # "<dir>/a.csv + b.csv" -> b.csv beside a.csv
    return out


nf, bad, checked = [], [], 0
for src in sorted({r["Source file"] for r in R}):
    if src in NONFILE:
        nf.append(src); continue
    for p in paths_of(src):
        checked += 1
        full = os.path.join(ROOT, *p.split("/"))
        if not (glob.glob(full) if "*" in p else os.path.isfile(full)):
            bad.append(p)
check("V6", "every file named in the 'Source file' column exists in the project", not bad,
      {"paths_checked": checked, "missing": bad, "non_file_references": nf})

# ---------------------------------------------------------------- V7 hand-typed parametric tables = CSV
cases = {"P00": None, "V01": "V01_LOW", "V03": "V03_HIGH", "Q01": "Q01_LOW", "Q03": "Q03_HIGH", "T01": "T01_THIN", "T03": "T03_THICK"}
qs = ["pressure drop", "outlet bulk temperature", "maximum solid temperature (outer-wall facet)", "LC1 maximum deformation",
      "LC1 maximum von Mises", "LC2 maximum von Mises", "lambda1 (S1)", "critical load P_cr", "LC2 yield utilisation"]
p00 = ["Pressure drop (area-weighted static, inlet - outlet)", "Outlet bulk temperature (mass-weighted)", "Maximum solid temperature (outer-wall facet)",
       "LC1 maximum total deformation", "LC1 maximum von Mises stress", "LC2 maximum von Mises stress", "S1 lambda1",
       "S1 critical load P_cr = lambda1 x N", "LC2 yield utilisation (max vm / S_y(T))"]
byp = {r["Parameter"]: r["Value"] for r in R}
ref = {c: [byp[p] for p in p00] if k is None else [byp["%s: %s" % (k, q)] for q in qs] for c, k in cases.items()}
tab_prob = {}
for d in ("FINAL_ENGINEERING_SYNTHESIS.md", "MASTER_PROJECT_DATA.md"):
    found = set()
    for line in TXT.get(d, "").splitlines():
        m = re.match(r"^\|\s*\**(P00|V01|V03|Q01|Q03|T01|T03)\b[^|]*\|(.*)\|\s*$", line)
        if not m:
            continue
        cells = [c.strip().replace("*", "") for c in m.group(2).split("|")]
        if len(cells) != 9 or not all(re.fullmatch(r"-?[\d.]+", c) for c in cells):
            continue
        found.add(m.group(1))
        for c, rv, q in zip(cells, ref[m.group(1)], qs):
            if abs(float(c) - float(rv)) > 1e-9:
                tab_prob.setdefault(d, []).append({"case": m.group(1), "quantity": q, "doc": c, "csv": rv})
    if found != set(cases):
        tab_prob.setdefault(d, []).append({"rows_found": sorted(found)})
check("V7", "parametric tables in the synthesis and in MASTER_PROJECT_DATA.md equal the CSV cell by cell", not tab_prob, tab_prob)

# ---------------------------------------------------------------- V8 brief key numbers carry their modelling level
KEY = [("603.19", "M071", "heat-transfer rate", "ANALYTICAL", 2), ("602.755", "M038", "Heat-transfer rate", "CFD-MEDIUM", 3),
       ("602.994", "M053", "fine: heat-transfer rate", "CFD-FINE", 3), ("581.7", "M074", "maximum solid temperature", "ANALYTICAL", 1),
       ("562.58", "M039", "Maximum solid temperature", "CFD-MEDIUM", 2), ("560.83", "M054", "fine: maximum solid temperature", "CFD-FINE", 2),
       ("605.16", "M090", "LC2 maximum von Mises", "FE-STATIC", 2), ("-657.2", "M078", "LC2 axial stress", "ANALYTICAL", 1),
       ("24.28", "M086", "LC1 maximum von Mises", "FE-STATIC", 2), ("1.108", "M098", "S1 lambda1", "FE-BUCKLING", 3),
       ("1.73", "M096", "First-yield load factor", "FE-STATIC", 2), ("4.30", "M101", "S2 lambda1", "FE-BUCKLING", 2),
       ("2.232", "M104", "S3 lambda1", "FE-BUCKLING", 3), ("548936.6", "M091", "LC2 end reaction", "FE-STATIC", 1),
       ("8190", "M008", "Solid density", "INPUT", 0), ("1047", "M094", "Local yield strength", "FE-STATIC", 0),
       ("2.096", "M076", "free axial growth", "ANALYTICAL", 3), ("1.841", "M085", "LC1 free axial growth", "FE-STATIC", 3)]
rid = {r["ID"]: r for r in R}
kp = []
for num, i, par, lev, nd in KEY:
    r = rid[i]
    ok = par.lower() in r["Parameter"].lower() and lev in r["Modelling level"] and round(float(r["Value"]), nd) == float(num)
    if not ok:
        kp.append({"number": num, "id": i, "row": [r["Parameter"], r["Value"], r["Modelling level"]]})
r13 = rid["M013"]
if not ("1020 MPa" in r13["Note"] and "NOT used for utilisation" in r13["Note"]):
    kp.append({"number": "1020", "id": "M013", "issue": "Engineering Data scalar not labelled"})
check("V8", "the brief's key numbers exist in the master data with their modelling level", not kp, {"checked": len(KEY) + 1, "problems": kp})

# ---------------------------------------------------------------- V9 document content rules
syn, aud, unc = TXT.get("FINAL_ENGINEERING_SYNTHESIS.md", ""), TXT.get("FINAL_ENGINEERING_AUDIT.md", ""), TXT.get("MASTER_UNCERTAINTIES.md", "")
heads = re.findall(r"^## (\d+)\. ", syn, re.M)
lids = sorted(set(re.findall(r"^\| (L-\d\d) \|", aud, re.M)))
reg = re.findall(r"^\| (\d) \| \*\*", unc, re.M)
rules = {
    "synthesis has parts 1-17 in order": heads == [str(i) for i in range(1, 18)],
    "audit inconsistency table has L-01..L-15": lids == ["L-%02d" % i for i in range(1, 16)],
    "audit findings table has A..L": re.findall(r"^\| ([A-L]) \| ", aud, re.M) == list("ABCDEFGHIJKL"),
    "uncertainty register has 9 separate sources": reg == [str(i) for i in range(1, 10)],
    "no combined uncertainty percentage": "No combined uncertainty percentage is formed" in unc,
    "supports not ranked (synthesis and audit)": "not** ranked" in syn and "no ranking" in aud,
    "lambda1 not called a factor of safety": "not a real-world factor of safety" in syn and "not a real-world factor of safety" in aud,
    "Q03 / T01 labelled pre-buckling equilibrium": syn.count("pre-buckling equilibrium") >= 1 and aud.count("pre-buckling equilibrium") >= 1,
    "support values present in synthesis": all(v in syn for v in ("1.10805", "4.29995", "2.23224", "608.25", "2,360.40", "1,225.36")),
}
check("V9", "content rules of the brief", all(rules.values()), rules)

# ---------------------------------------------------------------- V10 integrity against the 10A manifest
man = {}
with open(os.path.join(FA, "Integrity", "manifest_10A.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        man[r["path"]] = r
cur = {}
for d, dirs, fs in os.walk(ROOT):
    dirs.sort()
    if os.path.relpath(d, ROOT).split(os.sep)[0] == "11_Final_Audit":
        dirs[:] = []; continue
    for f in fs:
        p = os.path.join(d, f)
        st = os.stat(p)
        cur[os.path.relpath(p, ROOT)] = (st.st_size, datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"))


def sha(p):
    h = hashlib.sha256()
    with open(os.path.join(ROOT, p), "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest().upper()


EXP_MOD = {"PROJECT_STATE.md", "README.md"}
EXP_ADD = {os.path.join("Claude outputs", "README_NOT_AUTHORITATIVE.md")}
changed, touched_same = [], []
for p, (sz, mt) in cur.items():
    if p in man and (str(sz) != man[p]["bytes"] or mt != man[p]["mtime"]):
        (changed if sha(p) != man[p]["sha256"] else touched_same).append(p)
added = sorted(set(cur) - set(man))
missing_f = sorted(set(man) - set(cur))
unexp = sorted((set(changed) - EXP_MOD) | (set(added) - EXP_ADD))
check("V10", "project files unchanged since the 10A manifest except the three planned edits",
      not unexp and not missing_f,
      {"manifest_files": len(man), "current_files": len(cur), "changed": sorted(changed), "added": added, "missing": missing_f,
       "mtime_only_same_hash": sorted(touched_same), "unexpected": unexp})

# ---------------------------------------------------------------- V11 no bytecode written into the project by 10A scripts
pyc = [os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(FA, "**", "*.pyc"), recursive=True)]
check("V11", "no Python bytecode written into 11_Final_Audit", not pyc, {"pyc": pyc})

# ---------------------------------------------------------------- report
os.makedirs(os.path.join(FA, "Verification"), exist_ok=True)
out = {"note": "RE-ANALYSIS 2026 - Section 10A verification of 11_Final_Audit", "run": datetime.datetime.now().isoformat(timespec="seconds"),
       "passed": sum(r["result"] == "PASS" for r in RES), "total": len(RES), "checks": RES}
json.dump(out, open(os.path.join(FA, "Verification", "verify_10A_results.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for r in RES:
    print("%-4s %s  %s" % (r["id"], r["result"], r["check"]))
print("PASSED %d / %d" % (out["passed"], out["total"]))
