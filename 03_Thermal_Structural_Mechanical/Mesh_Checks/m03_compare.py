# -*- coding: utf-8 -*-
"""Section 9B-2 Part A - M03 CFD mesh-adequacy comparison: T03_THICK (12 solid layers) vs M03_T03_CFD_SOLID18 (18).

RE-ANALYSIS 2026 - compares two newly generated Fluent solutions; nothing is recovered or measured.

Both runs: same journal (solve_param.py), same physics (T03 geometry, q'' 7272.73 W/m2, V 23.5 m/s), same fluid mesh
(bitwise identical), same convergence criteria. Only the number of radial solid layers differs (x1.5 everywhere).
Compared:
  1. Fluent reports (P00 output definitions, extract_case.py): dp, T_out, Q, T max solid (facet / cell), interface
     max (near-wall air), fluid max, outer / interface area means, solid volume mean and minimum, y+ min/mean/max,
     mass and energy balance.
  2. The solid NODE temperature field that Mechanical maps (EnSight export): both meshes share the same 48 angular
     node lines and 91 axial node planes, only the radial node positions differ, so the T03 field is interpolated
     radially (linear, on the same angular line and axial plane) onto every M03 node and the difference is taken
     over all 82,992 M03 solid nodes. Also: through-wall dT and section mean at z = 0 / 0.3 / 0.6 m.
Acceptance (Section 9A, PARAMETRIC_CASE_MATRIX.csv row M03): T_max, through-wall dT, Q and volume-mean T change
<= 0.5 K / 1 %; re-map T03 only if T_max changes by more than 0.5 K.
Usage: python m03_compare.py [project_root]
"""
import os, sys, json, math
import numpy as np

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"<PROJECT_ROOT>"
PS = os.path.join(ROOT, "10_Parametric_Study")
sys.path.insert(0, os.path.join(PS, "CFD_Results", "Scripts"))
from extract_case import extract

A_CASE, B_CASE = "T03_THICK", "M03_T03_CFD_SOLID18"
RI, RO, L = 0.010, 0.022, 0.600


def read_ensight(geo, scl, part_name="solid_domain"):
    """EnSight Gold C-binary reader (same logic as 7A build_mesh_based_source.read_ensight_part; numpy only)."""
    b = open(geo, "rb").read()
    p = [0]

    def s80():
        t = b[p[0]:p[0] + 80].decode(errors="ignore").strip("\x00 ").strip(); p[0] += 80; return t

    def i4(n=1):
        a = np.frombuffer(b, np.int32, n, p[0]); p[0] += 4 * n; return a

    def f4(n):
        a = np.frombuffer(b, np.float32, n, p[0]); p[0] += 4 * n; return a
    hdr = [s80() for _ in range(5)]
    parts = {}
    while p[0] < len(b):
        assert s80() == "part"
        pn = int(i4()[0]); desc = s80(); assert s80() == "coordinates"
        nn = int(i4()[0]); X = np.c_[f4(nn), f4(nn), f4(nn)]
        while p[0] < len(b):
            et = b[p[0]:p[0] + 80].decode(errors="ignore").strip("\x00 ").strip()
            if et == "part":
                break
            p[0] += 80; ne = int(i4()[0])
            npe = {"hexa8": 8, "penta6": 6, "tetra4": 4, "pyramid5": 5, "quad4": 4, "tria3": 3}[et]
            i4(ne * npe)
        parts[desc] = (pn, X)
    pn, X = parts[part_name]
    v = open(scl, "rb").read(); q = 80
    T = None
    while q < len(v):
        q += 80
        vpn = int(np.frombuffer(v, np.int32, 1, q)[0]); q += 4
        q += 80
        n = [pp[1].shape[0] for pp in parts.values() if pp[0] == vpn][0]
        a = np.frombuffer(v, np.float32, n, q); q += 4 * n
        if vpn == pn:
            T = a.astype(np.float64)
    return X.astype(np.float64), T


def lattice(X, T):
    """group nodes by (angular line, axial plane); returns dict key -> (r sorted, T)"""
    r = np.hypot(X[:, 0], X[:, 1])
    th = np.round(np.degrees(np.arctan2(X[:, 1], X[:, 0])) / 7.5).astype(int) % 48
    kz = np.round(X[:, 2] / (L / 90)).astype(int)
    out = {}
    order = np.lexsort((r, kz, th))
    th, kz, r, T = th[order], kz[order], r[order], T[order]
    keys = th * 1000 + kz
    idx = np.flatnonzero(np.r_[True, keys[1:] != keys[:-1], True])
    for a, b in zip(idx[:-1], idx[1:]):
        out[(int(th[a]), int(kz[a]))] = (r[a:b], T[a:b])
    return out


def trap(f, x):
    """trapezoidal integral (numpy-version independent)"""
    return float(np.sum(0.5 * (f[1:] + f[:-1]) * (x[1:] - x[:-1])))


def section(lat, k):
    """through-wall dT (outer minus inner, mean over the 48 lines) and radially area-weighted mean at plane k"""
    dts, means = [], []
    for j in range(48):
        r, T = lat[(j, k)]
        dts.append(T[-1] - T[0])
        means.append(trap(T * r, r) / trap(r, r))
    return float(np.mean(dts)), float(np.mean(means))


def main():
    ra = extract(os.path.join(PS, "CFD_Cases", A_CASE), "Monitors/%s_monitors.out" % A_CASE)
    rb = extract(os.path.join(PS, "CFD_Cases", B_CASE), "Monitors/%s_monitors.out" % B_CASE)
    keys = [("dp_Pa", "rel"), ("T_out_K", "abs"), ("Q_heated_wall_W", "rel"), ("Q_interface_W", "rel"),
            ("T_solid_max_K", "abs"), ("T_solid_cell_max_K", "abs"), ("T_interface_max_K", "abs"), ("T_fluid_max_K", "abs"),
            ("T_outer_avg_K", "abs"), ("T_interface_avg_K", "abs"), ("T_solid_mean_K", "abs"), ("T_solid_cell_min_K", "abs"),
            ("T_outer_min_K", "abs"), ("T_interface_min_K", "abs"), ("yplus_min", "rel"), ("yplus_mean", "rel"), ("yplus_max", "rel"),
            ("mass_error_monitor", "info"), ("energy_error_monitor", "info"), ("iterations", "info")]
    rep = []
    for k, kind in keys:
        a, b = ra[k], rb[k]
        d = b - a
        rep.append({"quantity": k, "T03_12_layers": a, "M03_18_layers": b, "difference": d,
                    "relative": (d / abs(a) if a else None) if kind == "rel" else None, "kind": kind})
    EA = read_ensight(*[os.path.join(PS, "CFD_Cases", A_CASE, "EnSight", "solid_domain_T." + e) for e in ("geo", "scl1")])
    EB = read_ensight(*[os.path.join(PS, "CFD_Cases", B_CASE, "EnSight", "solid_domain_T." + e) for e in ("geo", "scl1")])
    la, lb = lattice(*EA), lattice(*EB)
    assert set(la) == set(lb) and len(la) == 48 * 91, (len(la), len(lb))
    worst = (0.0, None)
    diffs = []
    for key in lb:
        ra_, ta = la[key]
        rb_, tb = lb[key]
        ti = np.interp(rb_, ra_, ta)
        dd = tb - ti
        diffs.append(dd)
        i = int(np.argmax(np.abs(dd)))
        if abs(dd[i]) > abs(worst[0]):
            worst = (float(dd[i]), {"theta_deg": key[0] * 7.5, "z_m": key[1] * L / 90, "r_mm": float(rb_[i] * 1e3),
                                    "T_M03_K": float(tb[i]), "T_T03_interp_K": float(ti[i])})
    alld = np.concatenate(diffs)
    field = {"nodes_compared": int(alld.size), "max_abs_K": float(np.abs(alld).max()), "mean_K": float(alld.mean()),
             "rms_K": float(np.sqrt((alld ** 2).mean())), "worst": {"dT_K": worst[0], **worst[1]},
             "node_T_range_T03": [float(EA[1].min()), float(EA[1].max())], "node_T_range_M03": [float(EB[1].min()), float(EB[1].max())]}
    sect = {}
    for k, lab in ((0, "inlet_z0"), (45, "midspan_z0.3"), (90, "outlet_z0.6")):
        dta, ma = section(la, k)
        dtb, mb = section(lb, k)
        sect[lab] = {"through_wall_dT_T03_K": dta, "through_wall_dT_M03_K": dtb, "dT_change_K": dtb - dta,
                     "section_mean_T03_K": ma, "section_mean_M03_K": mb, "mean_change_K": mb - ma}
    R = {k["quantity"]: k for k in rep}
    crit = {
        "T_max solid (facet) change <= 0.5 K": abs(R["T_solid_max_K"]["difference"]) <= 0.5,
        "T_max solid (cell) change <= 0.5 K": abs(R["T_solid_cell_max_K"]["difference"]) <= 0.5,
        "through-wall dT change at mid-span <= 0.5 K and <= 1 %": abs(sect["midspan_z0.3"]["dT_change_K"]) <= 0.5 and
        abs(sect["midspan_z0.3"]["dT_change_K"]) <= 0.01 * abs(sect["midspan_z0.3"]["through_wall_dT_T03_K"]),
        "Q change <= 1 %": abs(R["Q_heated_wall_W"]["relative"]) <= 0.01,
        "solid volume-mean T change <= 0.5 K": abs(R["T_solid_mean_K"]["difference"]) <= 0.5,
        "node field: max |difference| <= 0.5 K anywhere": field["max_abs_K"] <= 0.5,
        "y+ max change <= 1 % (same fluid mesh)": abs(R["yplus_max"]["relative"]) <= 0.01,
    }
    out = {"note": "RE-ANALYSIS 2026 - M03 CFD mesh-adequacy check of T03 (9B-2 Part A)",
           "reports": rep, "node_field": field, "sections": sect, "criteria": crit, "T03_ADEQUATE": bool(all(crit.values())),
           "remap_required": bool(abs(R["T_solid_max_K"]["difference"]) > 0.5)}
    json.dump(out, open(os.path.join(PS, "Mesh_Checks", "m03_comparison.json"), "w"), indent=2)
    for r in rep:
        print("%-22s T03 %-16.9g M03 %-16.9g diff %+.4g%s" % (r["quantity"], r["T03_12_layers"], r["M03_18_layers"], r["difference"],
                                                             "" if r["relative"] is None else " (%+.3e rel)" % r["relative"]))
    print("node field:", json.dumps(field))
    print("sections:", json.dumps(sect))
    for k, v in crit.items():
        print("%-4s %s" % ("PASS" if v else "FAIL", k))
    print("T03 ADEQUATE: %s" % out["T03_ADEQUATE"])


if __name__ == "__main__":
    main()
