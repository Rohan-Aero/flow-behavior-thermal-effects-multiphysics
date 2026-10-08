# -*- coding: utf-8 -*-
"""SECTION 10A - wording scan (RE-ANALYSIS 2026). Read-only. Lists every line of the project's .md documents
that uses judgement words (safe, safety factor, margin, best, worst, optimal, failure-proof, recovered, original,
measured, experimental) so that each can be checked for correct qualification.
Usage: python wording_10A.py <project_root> <out_json>"""
import os, sys, re, json
sys.dont_write_bytecode = True
ROOT, OUT = sys.argv[1], sys.argv[2]
W = re.compile(r"(?i)\bsafe(ty)?\b|factor of safety|safety factor|\bFoS\b|\bmargins?\b|\bbest\b|\bworst\b|\boptimal\b|\boptimum\b|failure-proof|"
               r"\brecovered\b|\bmeasured\b|\bexperiment(al|s)?\b|\boriginal internship\b|\bhistorical\b")
skip = re.compile(r"(?i)\\11_Final_Audit(\\|$)|_files(\\|$)|\\Projects(\\|$)|\\Solver_Output(\\|$)|\\probe")
hits = []
for d, dirs, fs in os.walk(ROOT):
    if skip.search("\\" + os.path.relpath(d, ROOT)):
        dirs[:] = []; continue
    for f in fs:
        if f.lower().endswith(".md"):
            p = os.path.join(d, f)
            for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")):
                for m in W.finditer(l):
                    s = max(0, m.start() - 140); e = min(len(l), m.end() + 140)
                    hits.append({"file": os.path.relpath(p, ROOT), "line": i + 1, "word": m.group(0).lower(), "context": l[s:e].strip()})
json.dump({"hits": hits}, open(OUT, "w"), indent=1)
from collections import Counter
print(len(hits), Counter(h["word"] for h in hits).most_common())
