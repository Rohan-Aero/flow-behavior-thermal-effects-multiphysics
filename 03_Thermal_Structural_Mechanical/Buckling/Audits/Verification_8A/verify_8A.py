# -*- coding: utf-8 -*-
"""SECTION 8A - independent verification (RE-ANALYSIS 2026). Written separately from buckling_calculations.py,
mode_shapes.py and mech_buckling_8A.py; reads raw solver files only. Prints a check list; exits non-zero on failure."""
import os, re, sys, json, math
import numpy as np
ROOT = sys.argv[1] if len(sys.argv) > 1 else "<PROJECT_ROOT>"
B = os.path.join(ROOT, "08_Structural_Analysis")
BK = os.path.join(B, "Buckling")
ok_all = True
out = []


def check(name, cond, detail):
    global ok_all
    ok_all &= bool(cond)
    out.append(("PASS" if cond else "FAIL", name, detail))


# 1. applied load from the raw 8A LC2 re-solve reaction table (and equality with 7B)
def fz_faces(path):
    a = np.loadtxt(path, delimiter=",", skiprows=1)
    return a[a[:, 3] < 1e-9, 6].sum(), a[a[:, 3] > 0.6 - 1e-9, 6].sum()
i8, o8 = fz_faces(os.path.join(BK, "Mechanical", "LC2_prestress_resolve", "Solver_Output", "s7b_react.csv"))
i7, o7 = fz_faces(os.path.join(B, "LC2_Restrained", "Solver_Output", "s7b_react.csv"))
N = abs(i8)
check("applied force: 8A LC2 re-solve inlet/outlet reactions balance and equal 7B", abs(i8 + o8) < 1e-6 and abs(i8 - i7) < 1e-6,
      "inlet %.4f N, outlet %.4f N, 7B inlet %.4f N" % (i8, o8, i7))
A = math.pi / 4 * (0.04**2 - 0.02**2)
I = math.pi / 64 * (0.04**4 - 0.02**4)
check("mean axial stress N/A = 582.44 MPa", abs(N / A / 1e6 - 582.44) < 0.005, "%.4f MPa" % (N / A / 1e6))
r = math.sqrt(I / A)
check("r = 11.180 mm, L/r = 53.67", abs(r * 1e3 - 11.1803) < 1e-3 and abs(0.6 / r - 53.666) < 1e-2, "r %.5f mm, L/r %.4f" % (r * 1e3, 0.6 / r))

# 2. load factors: solve.out table = snippet csv = Mechanical summary LoadMultiplier
S = json.load(open(os.path.join(BK, "Audits", "mech_buckling_8A_summary.json")))
for case in ("LC2_Linear_Buckling", "LC2NS_Linear_Buckling"):
    so = open(os.path.join(BK, "Mechanical", case, "Solver_Output", "solve.out"), errors="replace").read()
    blk = so[so.index("LOAD MULTIPLIERS FOR BUCKLING"):]
    lam_so = [float(x) for x in re.findall(r"^\s+\d\s+([0-9.]+)\s*$", blk[:800], re.M)][:6]
    csv = np.loadtxt(os.path.join(BK, "Mechanical", case, "Solver_Output", "s8a_load_factors.csv"), delimiter=",", skiprows=1)
    mech = [m["LoadMultiplier_value"] if m.get("LoadMultiplier_value") is not None else float(m["LoadMultiplier"])
            for m in S["cases"][case]["modes"] if m["kind"] == "tot"]
    check("%s: 6 load factors agree (solve.out / snippet / Mechanical)" % case,
          len(lam_so) == 6 and np.allclose(lam_so, csv[:, 1], rtol=1e-7) and np.allclose(mech, csv[:, 1], rtol=1e-9),
          "solve.out %s | csv %s | mech %s" % (lam_so, np.round(csv[:, 1], 7).tolist(), np.round(mech, 7).tolist()))
    check("%s: 0 solver errors, solution Solved" % case, "NUMBER OF ERROR   MESSAGES ENCOUNTERED=          0" in so
          and S["cases"][case]["solution_state"] == "Solved", S["cases"][case]["solution_state"])
lam1 = float(np.loadtxt(os.path.join(BK, "Mechanical", "LC2_Linear_Buckling", "Solver_Output", "s8a_load_factors.csv"), delimiter=",", skiprows=1)[0, 1])

# 3. independent Euler check with a plain trapezoid E(z) from the 7B nodal temperatures
nod = np.loadtxt(os.path.join(B, "LC2_Restrained", "Solver_Output", "s7b_nodal.csv"), delimiter=",", skiprows=1)
T = nod[:, 14]; z = np.round(nod[:, 3], 6)
E_of = lambda t: np.interp(t, [20, 100, 200, 300, 400], [204e9, 199e9, 193e9, 187e9, 180e9])
zs = np.unique(z)
Ez = np.array([E_of(T[z == q]).mean() for q in zs])      # node-average E per plane (a different, cruder weighting)
w2 = np.cos(np.pi * zs / 0.6)**2                         # guided-mode curvature weight
E_g = np.trapezoid(Ez * w2, zs) / np.trapezoid(w2, zs)
P_g = math.pi**2 * E_g * I / 0.6**2
check("guided Euler with an independent E weighting within 0.5 % of the documented 1.119", abs(P_g / N / 1.1194 - 1) < 5e-3,
      "E_g %.2f GPa, LF %.4f" % (E_g / 1e9, P_g / N))
check("FE lambda_1 between Euler + shear (1.1036) and Euler (1.1194)", 1.1036 < lam1 < 1.1194, "lambda_1 %.6f" % lam1)
Sy = 1022.118e6; Eh = 187.6355e9
for K, lfj in ((1.0, 1.058), (0.5, 1.581)):
    lam = K * 0.6 / r
    sj = Sy - Sy**2 / (4 * math.pi**2 * Eh) * lam**2
    check("Johnson K=%.1f (hot-end S_y, E) = %.3f" % (K, lfj), abs(sj * A / N - lfj) < 1e-3, "%.4f" % (sj * A / N))

# 4. constraints read independently from the LC2 buckling pre-stress input
def constraints(path):
    L = open(path, errors="replace").read().splitlines()
    cm, cur, d, rot, nmod = {}, None, [], [], {}
    i = 0
    while i < len(L):
        l = L[i].strip()
        if l.upper().startswith("CMBLOCK,"):
            p = [x.strip() for x in l.split(",")]
            name, cnt = p[1].lower(), int(p[3].split("!")[0])
            ids, j, ntok = [], i + 2, 0
            while ntok < cnt and j < len(L):       # cnt = number of ENTRIES (a negative entry closes a range)
                for t in (int(x) for x in L[j].split()):
                    ntok += 1
                    if t < 0:
                        ids.extend(range(ids[-1] + 1, -t + 1))
                    else:
                        ids.append(t)
                j += 1
            cm[name] = set(ids)
            i = j
            continue
        ll = l.lower()
        if ll.startswith("cmsel,s,"):
            cur = ll.split(",")[2]
        elif ll.startswith("nsel,all"):
            cur = None
        elif ll.startswith("d,"):
            p = ll.split(",")
            tgt = cur if p[1] == "all" else p[1]
            d.append((p[2], tgt))
        elif ll.startswith("nrot,"):
            rot.append(ll.split(",")[1])
        elif ll.startswith("nmod,"):
            q = ll.split(",")
            nmod[int(q[1])] = float(q[5] or 0)
        i += 1
    return cm, d, rot, nmod
cm, d, rot, _ = constraints(os.path.join(BK, "Audits", "Presolve_Inputs", "LC2_presolve_8A_ds.dat"))
uz = [cm[t] for (dof, t) in d if dof == "uz"]
uy = [cm[t] for (dof, t) in d if dof == "uy"]
ends = set(np.round(nod[np.abs(nod[:, 3]) < 1e-9, 0]).astype(int)) | set(np.round(nod[np.abs(nod[:, 3] - 0.6) < 1e-9, 0]).astype(int))
check("LC2 (pre-stress of the buckling): U_z = 0 on exactly the nodes with z = 0 or z = 0.6 m (1,224)",
      len(uz) == 1 and uz[0] == ends and len(ends) == 1224, "uz set %d nodes, end-face nodes %d, equal %s" % (len(uz[0]), len(ends), uz[0] == ends))
check("LC2: U_theta = 0 only on 25862/25874/25886, rotated (nrot) to the cylindrical CS; no other D",
      len(uy) == 1 and uy[0] == {25862, 25874, 25886} and len(rot) == 1 and cm[rot[0]] == {25862, 25874, 25886} and len(d) == 2,
      "D entries %s, nrot %s" % ([(a, len(cm[b])) for a, b in d], [sorted(cm[x]) for x in rot]))
cmn, dn, rotn, nmodn = constraints(os.path.join(BK, "Audits", "Presolve_Inputs", "LC2NS_presolve_8A_ds.dat"))
xy = dict(zip(nod[:, 0].astype(int), zip(nod[:, 1], nod[:, 2])))
err = max(abs(((nmodn[n] - math.degrees(math.atan2(xy[n][1], xy[n][0]))) + 180) % 360 - 180) for n in nmodn)
unrot = [n for n in ends if n not in nmodn]
check("LC2NS: uy and uz on the 1,224 end-face nodes; cylindrical nodal systems (NMOD) except at theta = 0",
      all(cmn[t] == ends for (_, t) in dn) and len(dn) == 2 and err < 1e-6 and all(abs(math.atan2(xy[n][1], xy[n][0])) < 1e-9 for n in unrot),
      "%d NMOD, max angle error %.2e deg, %d unrotated at theta 0" % (len(nmodn), err, len(unrot)))

# 5. mode 1 shape directly from the raw eigenvector (no classifier): lateral motion of end planes vs mid-span
m = np.loadtxt(os.path.join(BK, "Mechanical", "LC2_Linear_Buckling", "Solver_Output", "s8a_mode1.csv"), delimiter=",", skiprows=1)
zz = np.round(m[:, 3], 6)
lat = lambda q: np.hypot(m[zz == q, 4].mean(), m[zz == q, 5].mean())
u0, umid, uL = lat(0.0), lat(0.3), lat(0.6)
vec0 = np.array([m[zz == 0.0, 4].mean(), m[zz == 0.0, 5].mean()]); vecL = np.array([m[zz == 0.6, 4].mean(), m[zz == 0.6, 5].mean()])
check("mode 1: both end planes translate laterally in opposite directions, mid-span ~0 (guided sway)",
      umid / max(u0, uL) < 1e-3 and np.dot(vec0, vecL) < 0 and abs(u0 / uL - 1) < 0.02,
      "|u| inlet %.4f, mid %.2e, outlet %.4f, cos(angle) %.4f" % (u0, umid, uL, np.dot(vec0, vecL) / (np.linalg.norm(vec0) * np.linalg.norm(vecL))))
mn = np.loadtxt(os.path.join(BK, "Mechanical", "LC2NS_Linear_Buckling", "Solver_Output", "s8a_mode1.csv"), delimiter=",", skiprows=1)
zn = np.round(mn[:, 3], 6)
latn = lambda q: np.hypot(mn[zn == q, 4].mean(), mn[zn == q, 5].mean())
check("LC2NS mode 1: ends fixed laterally, maximum at mid-span (clamped shape)", latn(0.0) / latn(0.3) < 1e-2 and latn(0.6) / latn(0.3) < 1e-2,
      "inlet %.2e, mid %.4f, outlet %.2e" % (latn(0.0), latn(0.3), latn(0.6)))

# 6. 7B project unchanged
pre = json.load(open(os.path.join(BK, "Audits", "pre8A_7B_project_hashes.json"), encoding="utf-8-sig"))
post = json.load(open(os.path.join(BK, "Audits", "post8A_7B_project_hashes.json"), encoding="utf-8-sig"))
check("7B project files SHA-identical before/after 8A", pre == post and len(pre) == 58, "%d files, identical %s" % (len(pre), pre == post))

for s_, n_, d_ in out:
    print("%s  %s | %s" % (s_, n_, d_))
print("ALL PASS" if ok_all else "SOME CHECKS FAILED")
json.dump([{"status": a, "check": b, "detail": c} for a, b, c in out], open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_8A_result.json"), "w"), indent=1)
sys.exit(0 if ok_all else 1)
