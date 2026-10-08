# -*- coding: utf-8 -*-
"""SECTION 10A - integrity comparison (RE-ANALYSIS 2026). Compares the 10A full-project manifest with every hash
record written in earlier sections, and lists duplicates, superseded/archived material and image files.
Usage: python integrity_10A.py <folder holding the staged project layout> <out_json>"""
import os, sys, csv, json, re, collections
sys.dont_write_bytecode = True
B, OUT = sys.argv[1], sys.argv[2]
P = os.path.join
import ntpath
def norm(p): return ntpath.normpath(p.replace("/", "\\").lstrip("\\")).lower()
MAN = {}
with open(P(B, "11_Final_Audit", "Integrity", "manifest_10A.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        MAN[norm(r["path"])] = r
ROOT_ABS = "<PROJECT_ROOT>\\"
def rel_abs(p):
    p = p.lower()
    return p[len(ROOT_ABS):] if p.startswith(ROOT_ABS) else p
def J(*p):
    return json.load(open(P(B, *p), encoding="utf-8-sig"))
records = []
def add(name, recfile, entries):   # entries: list of (project-relative path, sha)
    same, changed, missing = [], [], []
    for path, sha in entries:
        m = MAN.get(norm(path))
        if m is None:
            missing.append(path)
        elif m["sha256"].upper() == sha.upper():
            same.append(path)
        else:
            changed.append({"path": path, "record": sha[:16], "now": m["sha256"][:16], "mtime_now": m["mtime"]})
    records.append({"record": name, "file": recfile, "n": len(entries), "identical": len(same), "changed": changed, "missing": missing})
# 6B frozen solutions (paths relative to the project root)
f = ("06_Fluent_CFD", "Mesh_Independence", "Fine", "Audit", "frozen_solutions_hashes_after.json")
add("6B frozen medium/coarse/mesh/state files", "\\".join(f), [(e["file"], e["sha256"]) for e in J(*f)])
# 6A medium baseline (paths relative to 06_Fluent_CFD)
f = ("06_Fluent_CFD", "Mesh_Independence", "Coarse", "Audit", "medium_baseline_hashes_after.json")
add("6A medium baseline files", "\\".join(f), [("06_Fluent_CFD\\" + e["file"], e["sha256_after"]) for e in J(*f)])
# 7A source case/data
f = ("07_Thermal_Analysis", "Temperature_Source", "Audit", "source_case_data_hashes.json")
d = J(*f); add("7A CFD source case/data", "\\".join(f), [(e["file"], e["sha256"]) for e in d.get("after", d.get("before", []))])
# rooted records
for f, name in ((("08_Structural_Analysis", "Audits", "post7B_solve_7B_project_files_hashes.json"), "7B solved project files (post-7B)"),
                (("08_Structural_Analysis", "Audits", "post7B_7A_project_files_hashes.json"), "7A project files (post-7B)"),
                (("08_Structural_Analysis", "Workbench", "Audit", "cfd_case_hashes_after.json"), "baseline CFD case files (7A)"),
                (("08_Structural_Analysis", "Workbench", "Audit", "cfd_data_hashes_after.json"), "baseline CFD data files (7A)"),
                (("08_Structural_Analysis", "Workbench", "Audit", "section4_project_hashes_after.json"), "Section 4 Workbench project (7A)")):
    d = J(*f); root = rel_abs(d["root"])
    add(name, "\\".join(f), [(root + "\\" + e["file"], e["sha256"]) for e in d["files"]])
# 7A key files (paths relative to root)
f = ("08_Structural_Analysis", "Workbench", "Audit", "section7A_key_file_hashes.json")
add("7A key files", "\\".join(f), [(e["file"], e["sha256"]) for e in J(*f)])
# pre-7B key files (absolute paths)
f = ("08_Structural_Analysis", "Audits", "pre7B_key_file_hashes.txt")
ent = []
for l in open(P(B, *f), encoding="utf-8-sig"):
    if l.strip():
        h, p = l.strip().split(None, 1); ent.append((rel_abs(p), h))
add("pre-7B key files", "\\".join(f), ent)
# 7B project dicts (relative to 08_Structural_Analysis\Workbench)
for f, name in ((("08_Structural_Analysis", "Buckling", "Audits", "post8A_7B_project_hashes.json"), "7B project (post-8A)"),
                (("08_Structural_Analysis", "Mesh_Study", "Audits", "post8B_7B_project_hashes.json"), "7B project (post-8B)")):
    add(name, "\\".join(f), [("08_Structural_Analysis\\Workbench" + k, v) for k, v in J(*f).items()])
# pre-9B-2 record of the whole 08 folder
f = ("10_Parametric_Study", "Structural_Cases", "Audits", "pre9B2_08_Structural_Analysis_hashes.csv")
with open(P(B, *f), encoding="utf-8-sig") as fh:
    add("08_Structural_Analysis, all files (pre-9B-2)", "\\".join(f), [("08_Structural_Analysis\\" + r["path"], r["sha256"]) for r in csv.DictReader(fh)])
# files added to 08 since the pre-9B-2 record
with open(P(B, *f), encoding="utf-8-sig") as fh:
    rec08 = set(norm("08_Structural_Analysis\\" + r["path"]) for r in csv.DictReader(fh))
added08 = [MAN[k]["path"] for k in MAN if k.startswith("08_structural_analysis\\") and k not in rec08]
# 9B-1 CFD case folders: last modification per case (no hash record exists)
cfd = collections.defaultdict(list)
for k, r in MAN.items():
    m = re.match(r"10_parametric_study\\cfd_cases\\([^\\]+)\\", k)
    if m:
        cfd[m.group(1)].append(r["mtime"])
cfd_mt = {c: {"files": len(v), "first": min(v), "last": max(v)} for c, v in sorted(cfd.items())}
# baseline folders: newest file per top folder
top = collections.defaultdict(list)
for k, r in MAN.items():
    top[r["path"].split("\\")[0]].append((r["mtime"], r["path"]))
newest = {t: max(v) for t, v in sorted(top.items())}
# duplicates
by = collections.defaultdict(list)
for k, r in MAN.items():
    if int(r["bytes"]) > 1024:
        by[r["sha256"]].append(r["path"])
dups = sorted([(len(v), int(MAN[norm(v[0])]["bytes"]), v) for h, v in by.items() if len(v) > 1], key=lambda x: -x[1] * (x[0] - 1))
dup_bytes = sum(b * (n - 1) for n, b, v in dups)
# superseded / archived / rejected material
pat = re.compile(r"(?i)superseded|_fail|\\run\d|rejected|archive|probe|moved_from|stopped|pointcloud|preflip|section1_sizing|claude outputs|\.src\.md")
sup = collections.Counter()
for k, r in MAN.items():
    m = pat.search(r["path"])
    if m:
        parts = r["path"].split("\\")
        # group by the first path component that matches
        for i in range(len(parts)):
            if pat.search("\\" + "\\".join(parts[:i + 1])):
                sup["\\".join(parts[:i + 1])] += 1; break
# images
img = collections.Counter(); shots = []
for k, r in MAN.items():
    if re.search(r"\.(png|jpe?g|gif|bmp|tif)$", k):
        img["\\".join(r["path"].split("\\")[:-1])] += 1
        if re.search(r"(?i)screen ?shot", r["path"].split("\\")[-1]):
            shots.append(r["path"])
out = {"note": "RE-ANALYSIS 2026 - Section 10A integrity comparison", "manifest_files": len(MAN),
       "manifest_bytes": sum(int(r["bytes"]) for r in MAN.values()), "records": records, "added_to_08_since_pre9B2": added08,
       "cfd_parametric_case_mtimes": cfd_mt, "newest_file_per_top_folder": newest,
       "duplicates": {"groups": len(dups), "redundant_bytes": dup_bytes, "largest": [{"n": n, "bytes": b, "paths": v} for n, b, v in dups[:60]]},
       "superseded_or_archived": dict(sorted(sup.items())), "images_per_folder": dict(sorted(img.items())), "files_named_screenshot": shots}
json.dump(out, open(OUT, "w"), indent=1)
for r in records:
    print("%-48s n %4d identical %4d changed %d missing %d" % (r["record"], r["n"], r["identical"], len(r["changed"]), len(r["missing"])))
print("added to 08 since pre-9B-2:", added08)
print("duplicate groups", len(dups), "redundant MB %.1f" % (dup_bytes / 1e6))
