# -*- coding: utf-8 -*-
"""SECTION 10A - full-project file manifest (RE-ANALYSIS 2026). Read-only: walks the project, hashes every file
(SHA-256, 4 MiB chunks) and writes path, bytes, mtime (local ISO), sha256. The 11_Final_Audit folder itself is excluded.
Usage: python manifest_10A.py <project_root> <out_csv>"""
import os, sys, csv, hashlib, datetime, time
sys.dont_write_bytecode = True
ROOT, OUT = sys.argv[1], sys.argv[2]
t0 = time.time(); n = 0; tot = 0
rows = []
for d, dirs, fs in os.walk(ROOT):
    dirs.sort()
    rel_d = os.path.relpath(d, ROOT)
    if rel_d.split(os.sep)[0] == "11_Final_Audit":
        dirs[:] = []
        continue
    for f in sorted(fs):
        p = os.path.join(d, f)
        try:
            st = os.stat(p)
            h = hashlib.sha256()
            with open(p, "rb") as fh:
                for blk in iter(lambda: fh.read(1 << 22), b""):
                    h.update(blk)
            rows.append((os.path.relpath(p, ROOT), st.st_size, datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"), h.hexdigest().upper()))
            n += 1; tot += st.st_size
        except Exception as e:
            rows.append((os.path.relpath(p, ROOT), -1, "", "ERROR " + repr(e)))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["path", "bytes", "mtime", "sha256"]); w.writerows(rows)
print("files %d  bytes %d  seconds %.1f  -> %s" % (n, tot, time.time() - t0, OUT))
