# -*- coding: utf-8 -*-
"""Section 9B-2 Part A - M03 CFD mesh-adequacy check for T03_THICK: the refined alternative mesh.

RE-ANALYSIS 2026 - newly generated mesh, not a recovered file.

Case M03_T03_CFD_SOLID18 (PARAMETRIC_CASE_MATRIX.csv, approved in 9A): the T03 geometry (Di 20 / Do 44 / L 600 mm)
with the SOLID radially refined by a factor 1.5 everywhere:
    T03 (under test) : 12 solid layers, first 0.500 mm, growth 1.1191, last 1.724 mm
    M03 (refined)    : 18 solid layers, first 0.333 mm, growth 1.0759, last 1.157 mm
Fluid mesh unchanged (bitwise identical to P00/T03: NC 12, NR 24, NZ 90, first cell 12.2 um).
Uses the unchanged Section 4 generator through the 9B-1 wrapper functions (param_mesh.py); nothing else changes.
Run with the ANSYS-bundled CPython 3.10:  python m03_mesh.py
"""
import os, sys, json, math, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import param_mesh as pm            # 9B-1 wrapper (load_mm, geometry_checks, sha256); its main() is not called

NAME, DO, NRS = "M03_T03_CFD_SOLID18", 0.044, 18
H1S = 0.5e-3 / 1.5
OUT = os.path.join(pm.OUT, "Mesh_" + NAME)


def main():
    t0 = time.time()
    pm.H1S = H1S                    # geometry_checks() builds with the module-level first solid layer
    mm = pm.load_mm()
    mm.DO, mm.RO = DO, DO / 2.0
    st = mm.generate(NAME, OUT, NC=pm.NC, NR=pm.NR, NRS=NRS, NZ=pm.NZ, H1_FLUID=pm.H1F, H1_SOLID=H1S)
    m, chk = pm.geometry_checks(pm.load_mm(), NAME, DO, NRS)
    ref = pm.load_mm()
    ref.DO, ref.RO = 0.040, 0.020
    r0 = ref.build(pm.NC, pm.NR, 10, pm.NZ, pm.H1F, 0.5e-3)
    import numpy as np
    nf2d = (pm.NC + 1) ** 2 + pm.NR * 4 * pm.NC
    same = all(np.array_equal(m["coords"][k * m["n2d"]: k * m["n2d"] + nf2d], r0["coords"][k * r0["n2d"]: k * r0["n2d"] + nf2d])
               for k in range(pm.NZ + 1))
    t03 = json.load(open(os.path.join(pm.OUT, "mesh_checks_9B1.json")))["cases"]["T03_THICK"]["solid_layers"]
    res = {"case": NAME, "file": st["file"], "sha256": pm.sha256(st["file"]), "bytes": os.path.getsize(st["file"]),
           "generator_stats": st, "checks": chk, "fluid_node_coordinates_bitwise_equal_P00": bool(same),
           "refinement_vs_T03": {"layers": [12, NRS], "first_m": [t03["first_m"], chk["solid_layers"]["first_m"]],
                                 "last_m": [t03["last_m"], chk["solid_layers"]["last_m"]],
                                 "growth": [t03["growth"], chk["solid_layers"]["growth"]],
                                 "first_ratio": t03["first_m"] / chk["solid_layers"]["first_m"],
                                 "last_ratio": t03["last_m"] / chk["solid_layers"]["last_m"]},
           "seconds": round(time.time() - t0, 1)}
    json.dump(res, open(os.path.join(pm.OUT, "mesh_checks_M03.json"), "w"), indent=2, default=str)
    print("M03: cells %d (fluid %d / solid %d), neg %d, sha %s, fluid identical %s, solid first %.4e last %.4e g %.4f"
          % (st["cells"], st["fluid_cells"], st["solid_cells"], st["negative_cells"], res["sha256"][:16], same,
             chk["solid_layers"]["first_m"], chk["solid_layers"]["last_m"], chk["solid_layers"]["growth"]))
    print("heated area mesh %.9e exact %.9e; solid vol rel %.1e; interface faces %d" % (
        chk["closed_form"]["heated_outer_wall"]["mesh"], chk["closed_form"]["heated_outer_wall"]["exact_polygon"],
        chk["closed_form"]["solid_volume"]["rel_diff"], chk["conformity"]["interface_faces"]))
    print("M03-MESH-DONE")


if __name__ == "__main__":
    main()
