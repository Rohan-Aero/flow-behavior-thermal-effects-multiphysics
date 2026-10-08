# -*- coding: utf-8 -*-
"""SECTION 10A - cross-document number search (RE-ANALYSIS 2026). Read-only. Finds every occurrence of the key
numbers of the brief (and their usual roundings) in the project's documents (.md everywhere, plus summary .csv files
< 300 kB), with the line text, so that each occurrence can be classified by modelling level.
Usage: python crossdoc_10A.py <project_root> <out_json>"""
import os, sys, re, json
sys.dont_write_bytecode = True
ROOT, OUT = sys.argv[1], sys.argv[2]
T = [("603.19 W (analytical Q, true cylinder)", r"(?<![\d.])603\.1[89]\d*"),
     ("602.755 W (CFD medium Q, 48-gon)", r"(?<![\d.])602\.7[56]\d*"),
     ("602.994 W (CFD fine Q, 72-gon)", r"(?<![\d.])602\.99\d*"),
     ("581.7 K (analytical T_max)", r"(?<![\d.])581\.7\d*"),
     ("562.58 K (CFD medium T_max facet)", r"(?<![\d.])562\.5[78]\d*"),
     ("560.83 K (CFD fine T_max facet)", r"(?<![\d.])560\.8[23]\d*"),
     ("605.16 MPa (FE LC2 peak von Mises)", r"(?<![\d.])605\.1[56]\d*|(?<![\d.])605\.2(?![\d])"),
     ("657.2 MPa (analytical LC2 axial stress)", r"(?<![\d.])657\.2\d*|(?<![\d.])657(?![\d.,])"),
     ("24.28 MPa (FE LC1 peak von Mises)", r"(?<![\d.])24\.28\d*"),
     ("1.108 (S1 lambda1)", r"(?<![\d.])1\.108\d*"),
     ("1.73 (first-yield factor)", r"(?<![\d.])1\.73(?![\d])|(?<![\d.])1\.730\d*"),
     ("4.30 (S2 lambda1)", r"(?<![\d.])4\.30(?![1-9\d])|(?<![\d.])4\.300\d*|(?<![\d.])4\.2999\d*"),
     ("2.232 (S3 lambda1)", r"(?<![\d.])2\.232\d*"),
     ("548,936.6 N (LC2 end reaction)", r"548[, ]?936(?:\.\d+)?|(?<![\d.])548\.9\d*\s*kN|(?<![\d.])549\s*kN"),
     ("8190 kg/m3 (Inconel density)", r"(?<![\d.,])8[, ]?190(?![\d])"),
     ("1020 MPa (scalar S_y, ED lower bound)", r"(?<![\d.,])1[, ]?020(?:\.\d+)?\s*MPa|(?<![\d.,])1[, ]?020(?![\d.,])"),
     ("1047 MPa (local S_y at LC2 peak)", r"(?<![\d.,])1[, ]?047(?:\.\d+)?"),
     ("2.096 mm (analytical free growth)", r"(?<![\d.])2\.096\d*"),
     ("1.841 mm (FE LC1 free growth)", r"(?<![\d.])1\.84(?:09|1(?![\d])|086|08(?![\d]))\d*")]
CT = [(n, re.compile(p)) for n, p in T]
skip_dirs = re.compile(r"(?i)\\11_Final_Audit(\\|$)|_files(\\|$)|\\Projects(\\|$)|\\Solver_Output(\\|$)|\\Exports(\\|$)|\\EnSight(\\|$)|\\Case(\\|$)|\\Data(\\|$)|\\Logs(\\|$)|\\Presolve_Inputs(\\|$)|\\probe")
hits = []; nfiles = 0
for d, dirs, fs in os.walk(ROOT):
    if skip_dirs.search("\\" + os.path.relpath(d, ROOT)):
        dirs[:] = []; continue
    for f in fs:
        p = os.path.join(d, f); ext = f.lower().rsplit(".", 1)[-1]
        if ext == "md" or (ext == "csv" and os.path.getsize(p) < 300000):
            nfiles += 1
            try:
                L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
            except Exception:
                continue
            for i, l in enumerate(L):
                for n, c in CT:
                    for m in c.finditer(l):
                        s = max(0, m.start() - 150); e = min(len(l), m.end() + 110)
                        hits.append({"target": n, "file": os.path.relpath(p, ROOT), "line": i + 1, "match": m.group(0), "context": l[s:e].strip()})
json.dump({"files_searched": nfiles, "targets": [n for n, _ in T], "hits": hits}, open(OUT, "w"), indent=1)
from collections import Counter
c = Counter(h["target"] for h in hits)
print("files", nfiles, "hits", len(hits))
for n, _ in T:
    print("%5d  %s" % (c[n], n))
