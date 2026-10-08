# -*- coding: utf-8 -*-
"""Section 9B-1 - CFD meshes for the thickness cases T01_THIN (t 8 mm) and T03_THICK (t 12 mm).

RE-ANALYSIS 2026 - newly generated meshes, not recovered files.

Uses the UNCHANGED Section 4 generator 05_Meshing/Scripts/make_mesh.py (imported, never edited). Only the
outer radius and the number of solid layers change, per rule M-1 of
10_Parametric_Study/Planning/MESH_YPLUS_MATERIAL_POLICY.md:
    fluid     : NC 12 (48 facets), NR 24, NZ 90, first cell 12.2 um  -> IDENTICAL to the P00 medium mesh
    solid     : first layer 0.5 mm, growth <= 1.147 (P00 value 1.1469), smallest layer count that meets it
                t = 8 mm -> 9 layers (g 1.1388);  t = 12 mm -> 12 layers (g 1.1191)
make_mesh.py reads the module globals RO (and DO) inside build(), extract_faces() and generate(), so they are
overridden on a FRESH import of the module for each geometry (no state carried from one geometry to the next).

Step 0 proves the wrapper changes nothing else: it regenerates the P00 medium mesh (DO 40 mm, NRS 10) and
requires a byte-identical file (SHA-256) to 06_Fluent_CFD/Case/medium_mesh_used_for_baseline.msh.

Run with the ANSYS-bundled CPython 3.10 (the interpreter that generated the Section 4 meshes):
    python param_mesh.py
"""
import os, sys, json, math, hashlib, importlib.util, time
import numpy as np

ROOT = r"<PROJECT_ROOT>"
MM_PATH = os.path.join(ROOT, "05_Meshing", "Scripts", "make_mesh.py")
OUT = os.path.join(ROOT, "10_Parametric_Study", "Mesh_Checks")
BASE_MESH = os.path.join(ROOT, "06_Fluent_CFD", "Case", "medium_mesh_used_for_baseline.msh")
NC, NR, NZ, H1F, H1S = 12, 24, 90, 12.2e-6, 0.5e-3
DI, L, G_MAX = 0.020, 0.600, 1.147
CASES = [("T01_THIN", 0.036, 9), ("T03_THICK", 0.044, 12)]
LOG = []


def log(s):
    LOG.append(str(s))
    print(s, flush=True)


def load_mm():
    spec = importlib.util.spec_from_file_location("make_mesh_9b1_%d" % len(LOG), MM_PATH)
    mm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mm)
    mm._selftest()
    return mm


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest().upper()


def quad_area(P):
    """area of planar/near-planar quads, P (n,4,3), by the two-triangle split"""
    a = 0.5 * np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
    b = 0.5 * np.linalg.norm(np.cross(P[:, 2] - P[:, 0], P[:, 3] - P[:, 0]), axis=1)
    return a + b


def smallest_layers(t):
    mm = load_mm()
    for n in range(2, 40):
        if mm.geometric_ratio(H1S, t, n) <= G_MAX:
            return n, mm.geometric_ratio(H1S, t, n)


def geometry_checks(mm, name, DO, NRS):
    """rebuild the mesh object with the same code path and check it against closed-form values"""
    mm.DO, mm.RO = DO, DO / 2.0
    RI, RO = DI / 2.0, DO / 2.0
    m = mm.build(NC, NR, NRS, NZ, H1F, H1S)
    b = mm.extract_faces(m)
    V = mm.hex_volumes(m["coords"], m["cells"])
    nf = m["n_fluid_cells"]
    NT = 4 * NC
    k = NT / (2 * math.pi) * math.sin(2 * math.pi / NT)          # inscribed-polygon area ratio
    per = math.sin(math.pi / NT) / (math.pi / NT)                 # inscribed-polygon perimeter ratio
    A = {z: float(quad_area(m["coords"][np.array([f[0] for f in b[z]])]).sum()) for z in b if b[z]}
    exact = dict(
        fluid_volume=k * math.pi * RI ** 2 * L, solid_volume=k * math.pi * (RO ** 2 - RI ** 2) * L,
        fluid_inlet=k * math.pi * RI ** 2, solid_inlet_end=k * math.pi * (RO ** 2 - RI ** 2),
        fluid_solid_interface=per * math.pi * DI * L, heated_outer_wall=per * math.pi * DO * L)
    got = dict(fluid_volume=float(V[:nf].sum()), solid_volume=float(V[nf:].sum()),
               fluid_inlet=A["fluid_inlet"], solid_inlet_end=A["solid_inlet_end"],
               fluid_solid_interface=A["fluid_solid_interface"], heated_outer_wall=A["heated_outer_wall"])
    rs = m["rs"]
    layers = np.diff(rs)
    chk = {
        "counts": {"cells": int(m["n_cells"]), "fluid_cells": int(nf), "solid_cells": int(m["n_cells"] - nf),
                   "faces_by_zone": {z: len(v) for z, v in b.items() if v}},
        "closed_form": {q: {"mesh": got[q], "exact_polygon": exact[q], "rel_diff": got[q] / exact[q] - 1.0}
                        for q in exact},
        "circle_vs_polygon": {"heated_area_circle_pi_Do_L": math.pi * DO * L, "perimeter_ratio": per,
                              "area_ratio": k},
        "solid_layers": {"n": int(NRS), "first_m": float(layers[0]), "last_m": float(layers[-1]),
                         "growth": float(m["gs"]), "sum_m": float(rs[-1] - rs[0]), "outer_radius_m": float(rs[-1]),
                         "radii_m": [float(x) for x in rs]},
        "fluid_inflation": {"first_cell_m": float(m["hf"][0]), "growth": float(m["gf"]), "NR": NR,
                            "core_radius_m": float(m["a"])},
        "conformity": {
            "interface_faces": len(b["fluid_solid_interface"]), "expected_NT_x_NZ": NT * NZ,
            # every interface face has one fluid cell and one solid cell (conformal by construction: same nodes)
            "interface_faces_fluid_solid_pair": int(sum(1 for nd, c0, c1 in b["fluid_solid_interface"]
                                                        if (c0 <= nf) != (c1 <= nf))),
            "interface_nodes_on_RI": bool(np.allclose(np.hypot(*m["coords"][np.unique(
                np.array([f[0] for f in b["fluid_solid_interface"]]).ravel())][:, :2].T), RI, rtol=0, atol=1e-12)),
            "heated_nodes_on_RO": bool(np.allclose(np.hypot(*m["coords"][np.unique(
                np.array([f[0] for f in b["heated_outer_wall"]]).ravel())][:, :2].T), RO, rtol=0, atol=1e-12))},
        "negative_or_zero_volume_cells": int((V <= 0).sum()),
        "min_cell_volume_m3": float(V.min()),
        "max_aspect_ratio_est": {"fluid_first_cell": (L / NZ) / H1F,
                                 "solid_first_layer": (L / NZ) / float(layers[0]),
                                 "solid_last_layer": max((L / NZ) / float(layers[-1]),
                                                         float(layers[-1]) / ((L / NZ)))},
    }
    return m, chk


def main():
    t00 = time.time()
    res = {"generator": MM_PATH, "generator_sha256": sha256(MM_PATH), "python": sys.version,
           "numpy": np.__version__, "settings": dict(NC=NC, NR=NR, NZ=NZ, H1_FLUID=H1F, H1_SOLID=H1S),
           "solid_layer_rule": "first layer 0.5 mm, growth <= %.3f, smallest count" % G_MAX}
    log("9B-1 thickness meshes - RE-ANALYSIS 2026")
    log("generator %s sha256 %s" % (MM_PATH, res["generator_sha256"]))

    # ---- step 0: the wrapper must regenerate the P00 medium mesh byte for byte
    vdir = os.path.join(OUT, "Wrapper_Validation")
    mm = load_mm()
    mm.DO, mm.RO = 0.040, 0.020
    t0 = time.time()
    s0 = mm.generate("medium", vdir, NC=NC, NR=NR, NRS=10, NZ=NZ)
    h_new, h_base = sha256(s0["file"]), sha256(BASE_MESH)
    res["wrapper_validation"] = {"regenerated": s0["file"], "sha256_regenerated": h_new,
                                 "baseline_mesh": BASE_MESH, "sha256_baseline": h_base,
                                 "byte_identical": h_new == h_base, "bytes": os.path.getsize(s0["file"]),
                                 "seconds": round(time.time() - t0, 1), "stats": s0}
    log("STEP 0 wrapper validation: regenerated %s vs baseline %s -> %s"
        % (h_new[:16], h_base[:16], "BYTE-IDENTICAL" if h_new == h_base else "DIFFERENT - STOP"))
    if h_new != h_base:
        json.dump(res, open(os.path.join(OUT, "mesh_checks_9B1.json"), "w"), indent=2, default=str)
        open(os.path.join(OUT, "param_mesh_log.txt"), "w").write("\n".join(LOG))
        sys.exit(1)
    os.remove(s0["file"])          # identical copy of an existing file: only its hash record is kept
    res["wrapper_validation"]["regenerated_copy_removed_after_hash_match"] = True

    # ---- reference (P00) node table for the "fluid mesh unchanged" proof
    mref = load_mm()
    mref.DO, mref.RO = 0.040, 0.020
    ref = mref.build(NC, NR, 10, NZ, H1F, H1S)
    n_fluid_nodes_2d = (NC + 1) ** 2 + NR * 4 * NC

    res["cases"] = {}
    for name, DO, NRS in CASES:
        t = (DO - DI) / 2.0
        n_rule, g_rule = smallest_layers(t)
        mm = load_mm()
        mm.DO, mm.RO = DO, DO / 2.0
        t0 = time.time()
        st = mm.generate(name, os.path.join(OUT, "Mesh_" + name), NC=NC, NR=NR, NRS=NRS, NZ=NZ)
        sec = round(time.time() - t0, 1)
        mchk = load_mm()
        m, chk = geometry_checks(mchk, name, DO, NRS)
        n2d = m["n2d"]
        same_fluid = all(np.array_equal(m["coords"][kz * n2d: kz * n2d + n_fluid_nodes_2d],
                                        ref["coords"][kz * ref["n2d"]: kz * ref["n2d"] + n_fluid_nodes_2d])
                         for kz in range(NZ + 1))
        # global node ids differ (n2d grows with the solid layers), so compare as (axial level, in-plane node)
        cf_, cr_ = m["cells"][:m["n_fluid_cells"]], ref["cells"][:ref["n_fluid_cells"]]
        fluid_cells_same = bool(m["n_fluid_cells"] == ref["n_fluid_cells"] and
                                np.array_equal(cf_ // n2d, cr_ // ref["n2d"]) and
                                np.array_equal(cf_ % n2d, cr_ % ref["n2d"]))
        chk["fluid_mesh_identical_to_P00"] = {"fluid_node_coordinates_bitwise_equal": bool(same_fluid),
                                              "fluid_cell_connectivity_equal": bool(fluid_cells_same)}
        chk["layer_rule"] = {"t_m": t, "smallest_n_meeting_rule": n_rule, "growth_at_that_n": g_rule,
                             "n_used": NRS, "rule_met": bool(n_rule == NRS)}
        chk["file"] = {"path": st["file"], "sha256": sha256(st["file"]), "bytes": os.path.getsize(st["file"]),
                       "generate_seconds": sec}
        chk["generator_stats"] = st
        res["cases"][name] = chk
        cf = chk["closed_form"]
        log("%s: Do %.3f NRS %d cells %d (fluid %d / solid %d) neg %d  sha %s  %.1f s"
            % (name, DO, NRS, st["cells"], st["fluid_cells"], st["solid_cells"], st["negative_cells"],
               chk["file"]["sha256"][:16], sec))
        log("   heated area mesh %.9e exact polygon %.9e (rel %.2e); circle pi*Do*L %.9e"
            % (cf["heated_outer_wall"]["mesh"], cf["heated_outer_wall"]["exact_polygon"],
               cf["heated_outer_wall"]["rel_diff"], math.pi * DO * L))
        log("   solid vol rel %.2e  fluid vol rel %.2e  interface faces %d/%d  fluid mesh identical %s/%s"
            % (cf["solid_volume"]["rel_diff"], cf["fluid_volume"]["rel_diff"],
               chk["conformity"]["interface_faces"], chk["conformity"]["expected_NT_x_NZ"],
               same_fluid, fluid_cells_same))
        log("   solid layers %d first %.4e last %.4e growth %.4f (rule smallest n %d)"
            % (NRS, chk["solid_layers"]["first_m"], chk["solid_layers"]["last_m"], chk["solid_layers"]["growth"], n_rule))
    res["total_seconds"] = round(time.time() - t00, 1)
    json.dump(res, open(os.path.join(OUT, "mesh_checks_9B1.json"), "w"), indent=2, default=str)
    open(os.path.join(OUT, "param_mesh_log.txt"), "w").write("\n".join(LOG))
    log("MESH-9B1-DONE")


if __name__ == "__main__":
    main()
