# -*- coding: utf-8 -*-
"""SECTION 8B - independent verification of the structural mesh study (RE-ANALYSIS 2026).
Written separately from post_8B.py / mesh_geometry_8B.py / mech_meshstudy_8B.py. Reads ONLY raw files:
solver input decks (NBLOCK/EBLOCK/BFBLOCK/D-commands), solver tables (s7b_nodal.csv, s7b_react.csv, s8a_*.csv),
solve.out / file0.err, the Mechanical summaries (for Mechanical's own values) and the device hash comparison.
Every check prints PASS/FAIL and the numbers it compared.
Usage: python verify_8B.py <project_root> <out_json> [post_results_json]"""
import os, sys, json, re, math
import numpy as np

ROOT = sys.argv[1]
OUTJ = sys.argv[2]
POST = sys.argv[3] if len(sys.argv) > 3 else None
S8 = os.path.join(ROOT, "08_Structural_Analysis")
V = os.path.join(S8, "Mesh_Study", "Variants")
DIV = {"XC": (21, 3, 76), "C": (27, 4, 98), "B": (36, 5, 130), "FR": (36, 6, 130), "FA": (36, 5, 152), "FC": (42, 5, 130), "IL": (36, 5, 130)}
BUCK = ("XC", "C", "B", "FR", "FA", "FC")
res = {"checks": []}


def chk(name, ok, detail):
    res["checks"].append({"check": name, "pass": bool(ok), "detail": detail})
    print("PASS" if ok else "FAIL", name, "|", detail)


def nodal(path):
    a = np.loadtxt(path, delimiter=",", skiprows=1)
    return a


def nblock_count(ds):
    n = 0
    with open(ds, errors="ignore") as fh:
        on = False
        for ln in fh:
            if ln.lower().startswith("nblock"):
                on = True; next(fh); continue
            if on:
                if ln.strip().startswith("-1"):
                    break
                n += 1
    return n


def eblock_corners(ds):
    with open(ds, errors="ignore") as fh:
        L = fh.read().split("\n")
    i = [k for k, l in enumerate(L) if l.lower().startswith("eblock,21,compact")][0] + 2
    cs = set(); ne = 0
    while not L[i].strip().startswith("-1"):
        f = L[i].split()
        cs.update(int(x) for x in f[1:9]); ne += 1; i += 1
    return cs, ne


def bf_range(ds):
    vals = []
    with open(ds, errors="ignore") as fh:
        on = False
        for ln in fh:
            l = ln.lower()
            if l.startswith("bfblock"):
                on = True; next(fh); continue
            if on:
                if ln.strip().startswith("-1") or l.startswith("bf,end"):
                    break
                p = ln.split()
                if len(p) >= 2:
                    vals.append(float(p[1]))
    return len(vals), min(vals), max(vals)


def formula(nc, nr, na):
    return nc * ((nr + 1) * (na + 1) * 2 + nr * (na + 1) + (nr + 1) * na)


VAL = {}
for t, (nc, nr, na) in DIV.items():
    ds = os.path.join(V, t, "Audits", "Presolve_Inputs", "%s_LC2_presolve_ds.dat" % t)
    if not os.path.isfile(ds):
        chk("%s: solver input present" % t, False, ds); continue
    nn = nblock_count(ds); cs, ne = eblock_corners(ds)
    chk("%s: nodes = swept formula and < 128,000" % t, nn == formula(nc, nr, na) and nn < 128000, "%d vs %d" % (nn, formula(nc, nr, na)))
    chk("%s: elements = nc*nr*na" % t, ne == nc * nr * na, "%d" % ne)
    n_bf, tmin, tmax = bf_range(ds)
    chk("%s: temperature on every node, range 150.69-289.41 C (source 423.84-562.56 K)" % t,
        n_bf == nn and 150.6 < tmin < 150.8 and 289.3 < tmax < 289.5, "%d values, %.3f-%.3f C" % (n_bf, tmin, tmax))
    ga = json.load(open(os.path.join(V, t, "Audits", "presolve_audit_%s.json" % t)))
    chk("%s: pre-solve gate" % t, ga["gate"] == "PASS" and all(c["pass"] for c in ga["checks"]), "%d/%d" % (sum(c["pass"] for c in ga["checks"]), len(ga["checks"])))
    S = json.load(open(os.path.join(V, t, "Audits", "summary_%s.json" % t)))
    E = {"nodes": nn}
    cases = ("LC1", "LC2", "LC2P") if t != "IL" else ("LC1", "LC2")
    for c in cases:
        so = os.path.join(V, t, "Solver_Output", c)
        ef = os.path.join(so, "file0.err") if os.path.isfile(os.path.join(so, "file0.err")) else os.path.join(so, "solve.out")
        err = open(ef, errors="ignore").read()
        chk("%s %s: no solver errors (%s)" % (t, c, os.path.basename(ef)), "*** ERROR" not in err, "errors %d" % err.count("*** ERROR"))
        a = nodal(os.path.join(so, "s7b_nodal.csv"))
        idx = np.array(sorted(cs)) - 1 if a[-1, 0] == len(a) else None
        ids = a[:, 0].astype(int)
        m = np.isin(ids, np.array(sorted(cs)))
        seqv = a[m, 12]
        mech = S["cases"][c]["results"]["%s_Equivalent_Stress_averaged" % c]["Maximum"]
        chk("%s %s: max von Mises (corner nodes, raw table) = Mechanical averaged maximum" % (t, c), abs(seqv.max() - mech) / mech < 2e-7,
            "%.6f vs %.6f MPa" % (seqv.max() / 1e6, mech / 1e6))
        E[c + "_max_vm"] = float(seqv.max())
        ut = np.sqrt(a[:, 4]**2 + a[:, 5]**2 + a[:, 6]**2)
        E[c + "_max_utot"] = float(ut.max())
        z = a[:, 3]
        if c == "LC1":
            dl = a[np.abs(z - 0.6) < 1e-9, 6].mean() - a[np.abs(z) < 1e-9, 6].mean()
            E["LC1_dL_nodemean"] = float(dl)
        rr = np.loadtxt(os.path.join(so, "s7b_react.csv"), delimiter=",", skiprows=1)
        rr = np.atleast_2d(rr)
        if c != "LC1":
            fin = rr[np.abs(rr[:, 3]) < 1e-9, 6].sum(); fout = rr[np.abs(rr[:, 3] - 0.6) < 1e-9, 6].sum()
            E[c + "_N"] = float(fin)
            chk("%s %s: end reactions balance" % (t, c), abs(fin + fout) < 1e-4, "%.4f / %.4f N" % (fin, fout))
        else:
            chk("%s LC1: support reactions ~ 0" % t, np.abs(rr[:, 4:7]).max() < 1e-4, "max %.2e N" % np.abs(rr[:, 4:7]).max())
    if t in BUCK:
        so = os.path.join(V, t, "Solver_Output", "BUCKLING")
        out = open(os.path.join(so, "solve.out"), errors="ignore").read()
        blk = out[out.index("LOAD MULTIPLIERS FOR BUCKLING"):]
        lm = [float(x) for x in re.findall(r"^\s+\d\s+([0-9.E+-]+)\s*$", blk[:1200], re.M)][:6]
        csv = np.loadtxt(os.path.join(so, "s8a_load_factors.csv"), delimiter=",", skiprows=1)[:, 1]
        mech = [float(m["LoadMultiplier"]) for m in S["cases"]["BUCKLING"]["modes"]]
        chk("%s: 6 load multipliers identical in solve.out, snippet CSV and Mechanical" % t,
            len(lm) == 6 and np.allclose(lm, csv, rtol=1e-7) and np.allclose(mech, csv, rtol=1e-9), "lambda1 %.7f / %.9f / %.9f" % (lm[0], csv[0], mech[0]))
        chk("%s: buckling solver errors" % t, "*** ERROR" not in open(os.path.join(so, "file0.err"), errors="ignore").read(), "")
        E["lambda"] = csv.tolist(); E["Pcr"] = float(csv[0] * E["LC2_N"])
        # mode 1 directly from the raw eigenvector: lateral displacement of the section centroid at z = 0, 300, 600 mm
        md = np.loadtxt(os.path.join(so, "s8a_mode1.csv"), delimiter=",", skiprows=1)
        zz = md[:, 3]
        cen = {}
        for zq in (0.0, 0.3, 0.6):
            s = np.abs(zz - zq) < 1e-7
            cen[zq] = md[s, 4:6].mean(axis=0)
        ref = cen[0.6] / np.linalg.norm(cen[0.6])
        w0, w3, w6 = (float(cen[q] @ ref) for q in (0.0, 0.3, 0.6))
        # cross-section distortion: Fourier harmonics n = 2 (ovalisation) and n = 3 (lobes) of the radial displacement of the
        # outer ring at the outlet plane, relative to the lateral amplitude (n = 1 is translation + Poisson effect of bending)
        s = (np.abs(zz - 0.6) < 1e-7) & (np.abs(np.hypot(md[:, 1], md[:, 2]) - 0.02) < 1e-7)
        th = np.arctan2(md[s, 2], md[s, 1])
        ur = md[s, 4] * np.cos(th) + md[s, 5] * np.sin(th)
        A = np.c_[np.ones_like(th), np.cos(th), np.sin(th), np.cos(2 * th), np.sin(2 * th), np.cos(3 * th), np.sin(3 * th)]
        co = np.linalg.lstsq(A, ur, rcond=None)[0]
        amp = np.linalg.norm(cen[0.6])
        ov, lo = math.hypot(co[3], co[4]) / amp, math.hypot(co[5], co[6]) / amp
        chk("%s: mode 1 = guided sway (ends opposite, mid-span ~0, no ovalisation / lobes)" % t,
            w0 / w6 < -0.95 and abs(w3 / w6) < 1e-3 and ov < 1e-4 and lo < 1e-4,
            "inlet/outlet %.4f, mid/outlet %.1e, n=2 %.1e, n=3 %.1e" % (w0 / w6, w3 / w6, ov, lo))
    VAL[t] = E

# B (re-meshed) vs the official 7B / 8A solution
off = {"LC1": os.path.join(S8, "LC1_Free_Expansion", "Solver_Output", "s7b_nodal.csv"), "LC2": os.path.join(S8, "LC2_Restrained", "Solver_Output", "s7b_nodal.csv"),
       "LC2P": os.path.join(S8, "Pressure_Check", "Solver_Output", "s7b_nodal.csv")}
for c, p in off.items():
    if os.path.isfile(p) and "B" in VAL:
        a = nodal(p); b = nodal(os.path.join(V, "B", "Solver_Output", c, "s7b_nodal.csv"))
        same_nodes = a.shape == b.shape and np.array_equal(a[:, 0], b[:, 0]) and np.allclose(a[:, 1:4], b[:, 1:4], atol=1e-12)
        d = np.abs(a[:, 4:] - b[:, 4:]).max(axis=0)
        chk("B vs official 7B %s: identical mesh and nodal results" % c, same_nodes and np.all(d[3:9] <= 1.0) and np.all(d[:3] <= 1e-12),
            "max |diff| stress %.3e Pa, displacement %.3e m" % (d[3:9].max(), d[:3].max()))
lf8a = os.path.join(S8, "Buckling", "Mechanical", "LC2_Linear_Buckling", "Solver_Output", "s8a_load_factors.csv")
if os.path.isfile(lf8a) and "B" in VAL:
    l8 = np.loadtxt(lf8a, delimiter=",", skiprows=1)[:, 1]
    chk("B vs official 8A buckling: lambda identical within Lanczos tolerance", np.allclose(l8, VAL["B"]["lambda"], rtol=1e-5),
        "8A %.8f vs B %.8f" % (l8[0], VAL["B"]["lambda"][0]))
# BFBLOCK identical between B and the official 7B input (same field on the same mesh)
dsB = os.path.join(V, "B", "Audits", "Presolve_Inputs", "B_LC2_presolve_ds.dat")
ds7 = os.path.join(S8, "Mechanical_Setup", "Input_Files", "LC2_Axially_Restrained_ds.dat")
if os.path.isfile(ds7):
    def bf(ds):
        out = []
        with open(ds, errors="ignore") as fh:
            on = False
            for ln in fh:
                if ln.lower().startswith("bfblock"):
                    on = True; next(fh); continue
                if on:
                    if ln.strip().startswith("-1") or ln.lower().startswith("bf,end"):
                        break
                    out.append(ln.strip())
        return out
    chk("B vs 7B: BFBLOCK (mapped temperature) byte-identical", bf(dsB) == bf(ds7), "%d lines" % len(bf(dsB)))


# independent Richardson on the family XC -> C -> B for three governing quantities
def rich(f3, f2, f1, r):
    e32, e21 = f2 - f3, f1 - f2
    if e32 == 0 or e21 / e32 <= 0 or e21 / e32 >= 1:
        return None
    p = math.log(e32 / e21) / math.log(r)
    return {"p": p, "ext": f1 + e21 / (r**p - 1), "gci": 1.25 * abs(e21 / f1) / (r**p - 1)}


r = (23400 / 10584) ** (1 / 3)
for q in ("LC2_max_vm", "lambda1"):
    g = lambda t: VAL[t]["LC2_max_vm"] if q == "LC2_max_vm" else VAL[t]["lambda"][0]
    rr_ = rich(g("XC"), g("C"), g("B"), r)
    res.setdefault("richardson", {})[q] = rr_
    if POST:
        P = json.load(open(POST))
        key = {"LC2_max_vm": "LC2 max von Mises [Pa]", "lambda1": "lambda_1"}[q]
        fa = P["family_assessment"][key]
        chk("Richardson %s recomputed independently = post_8B" % q, rr_ and abs(rr_["p"] - fa["p"]) < 1e-6 and abs(rr_["ext"] / fa["extrapolated"] - 1) < 1e-9,
            "p %.3f ext %.8g GCI %.2e" % (rr_["p"], rr_["ext"], rr_["gci"]))
# largest relative change of the fine variants vs B (governing quantities)
fine = [t for t in ("FR", "FA", "FC") if t in VAL]
for q, fn in (("LC2 max VM", lambda t: VAL[t]["LC2_max_vm"]), ("LC2 end force", lambda t: VAL[t]["LC2_N"]),
              ("lambda1", lambda t: VAL[t]["lambda"][0]), ("P_cr", lambda t: VAL[t]["Pcr"]), ("LC1 max VM", lambda t: VAL[t]["LC1_max_vm"]),
              ("LC1 dL", lambda t: VAL[t]["LC1_dL_nodemean"])):
    ch = {t: fn(t) / fn("B") - 1 for t in fine}
    res.setdefault("fine_vs_B", {})[q] = ch
    print("   fine vs B", q, {k: "%+.2e" % v for k, v in ch.items()})
# pressure effect on every mesh
for t in VAL:
    if "LC2P_max_vm" in VAL[t]:
        d = VAL[t]["LC2P_max_vm"] - VAL[t]["LC2_max_vm"]
        chk("%s: pressure effect on max VM tiny and positive (no anomaly)" % t, 0 < d < 500, "%+.0f Pa (%.1e relative)" % (d, d / VAL[t]["LC2_max_vm"]))
# 7B project integrity
hc = os.path.join(S8, "Mesh_Study", "Audits", "hash_compare_7B_pre_post_8B.json")
if os.path.isfile(hc):
    h = json.load(open(hc, encoding="utf-8-sig"))
    chk("official 7B project unchanged by the mesh study (SHA-256)", h["verdict"] == "IDENTICAL" and not h["changed"] and not h["missing"],
        "%d files before, %d after, changed %d" % (h["pre_files"], h["post_files"], len(h["changed"])))
res["values"] = VAL
res["summary"] = "%d/%d PASS" % (sum(c["pass"] for c in res["checks"]), len(res["checks"]))
print(res["summary"])
json.dump(res, open(OUTJ, "w"), indent=1)
