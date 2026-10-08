# Section 9B-2: lists files in 08_Structural_Analysis that are not in the pre-9B-2 hash record (diagnostic, read-only)
import os, csv, sys, datetime
R = sys.argv[1]; S8 = os.path.join(R, "08_Structural_Analysis")
pre = os.path.join(R, "10_Parametric_Study", "Structural_Cases", "Audits", "pre9B2_08_Structural_Analysis_hashes.csv")
with open(pre, encoding="utf-8-sig") as fh:
    rows = list(csv.DictReader(fh))
k0 = list(rows[0].keys())[0]
ref = set(os.path.normcase(r[k0] if os.path.isabs(r[k0]) else os.path.join(S8, r[k0])) for r in rows)
print("header", list(rows[0].keys()), "example", rows[0][k0])
for d, _, fs in os.walk(S8):
    for f in fs:
        p = os.path.join(d, f)
        if os.path.normcase(p) not in ref:
            st = os.stat(p)
            print("ADDED", p, st.st_size, datetime.datetime.fromtimestamp(st.st_mtime), "created", datetime.datetime.fromtimestamp(st.st_ctime))
