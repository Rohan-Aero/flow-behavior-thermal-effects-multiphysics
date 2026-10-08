# -*- coding: utf-8 -*-
"""Section 9B-1 - analytical geometry checks of the T01_THIN / T03_THICK CAD and the DERIVED heat flux.

RE-ANALYSIS 2026. Inputs (all newly generated):
  Geometry_Checks/<CASE>/cad_measurements.json     SpaceClaim measurements of the new CAD (build_geometry_<CASE>.py)
  Mesh_Checks/mesh_checks_9B1.json                 closed-form checks of the new CFD meshes (param_mesh.py)
  03_CAD_Geometry/Geometry_Check/cad_measurements.json and 06_Fluent_CFD/Audit/fluent_si_areas.txt,
  fluent_flux_heat.txt                             P00 CAD and P00 CFD (read only)
Outputs:
  Geometry_Checks/<CASE>/geometry_verification.csv (same layout as the P00 file, plus the thickness-case rows)
  Geometry_Checks/geometry_checks_9B1.json, Geometry_Checks/derived_heat_flux_9B1.json

Derived flux (D-060, total heat input held at the P00 value):
    q''_case = Q_P00 / A_heated,case(actual)
with the ACTUAL heated area of each geometry: pi*Do*L on the CAD (measured by SpaceClaim), and the 48-facet area
on the CFD mesh. Because both areas scale with Do by the same factor, q''_case = q''_P00 * Do_P00 / Do_case and the
CFD heat input equals the P00 CFD heat input (602.755 W) exactly; the check below proves it numerically.
"""
import os, sys, json, math, re, csv

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"<PROJECT_ROOT>"
PS = os.path.join(ROOT, "10_Parametric_Study")
GC = os.path.join(PS, "Geometry_Checks")
DI, L, QPP0, DO0 = 0.020, 0.600, 8000.0, 0.040
CASES = [("T01_THIN", 0.036), ("T03_THICK", 0.044)]
NUM = re.compile(r"^\s*(\S+)\s+([-+]?[0-9.]+(?:[eE][-+]?\d+)?)\s*$")


def report(path):
    out = {}
    for l in open(path, "r", errors="ignore"):
        m = NUM.match(l)
        if m:
            out[m.group(1)] = float(m.group(2))
    return out


def status(a, c):
    rel = abs(c - a) / abs(a) if a else abs(c - a)
    return rel, ("EXACT" if rel < 1e-9 else ("OK" if rel < 1e-6 else "MISMATCH"))


def main():
    p00cad = json.load(open(os.path.join(ROOT, "03_CAD_Geometry", "Geometry_Check", "cad_measurements.json")))
    p00area = report(os.path.join(ROOT, "06_Fluent_CFD", "Audit", "fluent_si_areas.txt"))
    p00heat = report(os.path.join(ROOT, "06_Fluent_CFD", "Audit", "fluent_flux_heat.txt"))
    mesh = json.load(open(os.path.join(PS, "Mesh_Checks", "mesh_checks_9B1.json")))
    Q_P00_ana = QPP0 * math.pi * DO0 * L
    Q_P00_cad = QPP0 * p00cad["area_heated_outer"]
    Q_P00_cfd = p00heat["heated_outer_wall"]
    A_P00_cfd = p00area["heated_outer_wall"]
    out = {"P00": {"Do_m": DO0, "qpp_W_m2": QPP0, "A_heated_analytic_m2": math.pi * DO0 * L,
                   "A_heated_CAD_m2": p00cad["area_heated_outer"], "A_heated_CFD_Fluent_m2": A_P00_cfd,
                   "Q_analytic_W": Q_P00_ana, "Q_CAD_W": Q_P00_cad, "Q_CFD_Fluent_W": Q_P00_cfd,
                   "Q_CFD_qpp_x_Fluent_area_W": QPP0 * A_P00_cfd}, "cases": {}}
    all_ok = True
    for case, DO in CASES:
        m = json.load(open(os.path.join(GC, case, "cad_measurements.json")))
        bs, bf = m["bbox_solid"], m["bbox_fluid"]
        do_cad = bs[3] - bs[0]
        di_cad = bf[3] - bf[0]
        l_cad = bs[5] - bs[2]
        a_fl = m["area_fluid_inlet"]
        per = m["area_fluid_wall"] / l_cad
        rows = [
            ("Outer diameter", "mm", DO * 1e3, do_cad * 1e3),
            ("Inner (bore) diameter", "mm", DI * 1e3, di_cad * 1e3),
            ("Wall thickness", "mm", (DO - DI) / 2 * 1e3, (do_cad - di_cad) / 2 * 1e3),
            ("Total length", "mm", L * 1e3, l_cad * 1e3),
            ("Fluid cross-sectional area", "mm^2", math.pi / 4 * DI ** 2 * 1e6, a_fl * 1e6),
            ("Hydraulic diameter", "mm", DI * 1e3, 4 * a_fl / per * 1e3),
            ("FLUID_DOMAIN volume", "m^3", math.pi / 4 * DI ** 2 * L, m["fluid_volume_m3"]),
            ("SOLID_DOMAIN volume", "m^3", math.pi / 4 * (DO ** 2 - DI ** 2) * L, m["solid_volume_m3"]),
            ("FLUID_INLET area", "m^2", math.pi / 4 * DI ** 2, m["area_fluid_inlet"]),
            ("FLUID_OUTLET area", "m^2", math.pi / 4 * DI ** 2, m["area_fluid_outlet"]),
            ("FLUID_WALL area", "m^2", math.pi * DI * L, m["area_fluid_wall"]),
            ("SOLID_INNER_INTERFACE area", "m^2", math.pi * DI * L, m["area_solid_inner"]),
            ("HEATED_OUTER_WALL area", "m^2", math.pi * DO * L, m["area_heated_outer"]),
            ("SOLID_INLET_END area", "m^2", math.pi / 4 * (DO ** 2 - DI ** 2), m["area_solid_inlet_end"]),
            ("SOLID_OUTLET_END area", "m^2", math.pi / 4 * (DO ** 2 - DI ** 2), m["area_solid_outlet_end"]),
        ]
        ver = []
        for q, u, a, c in rows:
            rel, st = status(a, c)
            all_ok &= st != "MISMATCH"
            ver.append(dict(quantity=q, unit=u, analytical=a, cad=c, difference=c - a, relative_pct=rel * 100, status=st))
        extra = dict(bodies=m["total_bodies"], fluid_faces=m["fluid_faces"], solid_faces=m["solid_faces"],
                     named_selections=len(m["named_selections"]), share_topology=m["share_topology"],
                     exports=m["exports"], cad_status=m["status"])
        extra_ok = (m["total_bodies"] == 2 and m["fluid_faces"] == 3 and m["solid_faces"] == 4 and
                    len(m["named_selections"]) == 11 and "OK: True" in m["share_topology"] and m["status"] == "complete")
        all_ok &= extra_ok
        with open(os.path.join(GC, case, "geometry_verification.csv"), "w", newline="") as fh:
            fh.write("# RE-ANALYSIS 2026 - Section 9B-1 geometry verification of %s (Di 20 / Do %.0f / L 600 mm). "
                     "CAD from ANSYS SpaceClaim 2026 R1. Not an original file.\n" % (case, DO * 1e3))
            w = csv.writer(fh)
            w.writerow(["quantity", "unit", "analytical", "cad", "difference", "relative_pct", "status"])
            for r in ver:
                w.writerow([r["quantity"], r["unit"], "%.12g" % r["analytical"], "%.12g" % r["cad"],
                            "%.6e" % r["difference"], "%.6e" % r["relative_pct"], r["status"]])
        # derived flux
        mc = mesh["cases"][case]
        A_cad = m["area_heated_outer"]
        A_mesh = mc["closed_form"]["heated_outer_wall"]["mesh"]
        qpp = Q_P00_ana / A_cad
        qpp_formula = QPP0 * DO0 / DO
        flux = dict(A_heated_analytic_m2=math.pi * DO * L, A_heated_CAD_m2=A_cad, A_heated_CFD_mesh_m2=A_mesh,
                    qpp_derived_W_m2=qpp, qpp_formula_qpp0_Do0_over_Do=qpp_formula,
                    qpp_derived_vs_formula_rel=qpp / qpp_formula - 1.0,
                    Q_CAD_W=qpp * A_cad, Q_CAD_vs_P00_analytic_rel=qpp * A_cad / Q_P00_ana - 1.0,
                    Q_CFD_mesh_W=qpp_formula * A_mesh,
                    Q_CFD_mesh_vs_P00_CFD_rel=qpp_formula * A_mesh / Q_P00_cfd - 1.0,
                    qpp_change_vs_P00_pct=(qpp_formula / QPP0 - 1.0) * 100.0)
        flux_ok = (abs(flux["qpp_derived_vs_formula_rel"]) < 1e-9 and abs(flux["Q_CAD_vs_P00_analytic_rel"]) < 1e-9
                   and abs(flux["Q_CFD_mesh_vs_P00_CFD_rel"]) < 1e-6)
        all_ok &= flux_ok
        out["cases"][case] = {"verification": ver, "cad_structure": extra, "cad_structure_ok": extra_ok,
                              "derived_heat_flux": flux, "derived_heat_flux_ok": flux_ok,
                              "mesh_counts": mc["counts"], "mesh_sha256": mc["file"]["sha256"]}
        print("%s: %d/%d rows EXACT/OK, structure %s; A_heated CAD %.9e m2, mesh %.9e m2; q'' %.6f W/m2 "
              "(formula %.6f); Q CAD %.6f W, Q CFD %.6f W (P00 CFD %.6f)"
              % (case, sum(r["status"] != "MISMATCH" for r in ver), len(ver), extra_ok, A_cad, A_mesh, qpp,
                 qpp_formula, flux["Q_CAD_W"], flux["Q_CFD_mesh_W"], Q_P00_cfd))
    out["ALL_OK"] = bool(all_ok)
    json.dump(out, open(os.path.join(GC, "geometry_checks_9B1.json"), "w"), indent=2)
    json.dump({"P00": out["P00"], "cases": {k: v["derived_heat_flux"] for k, v in out["cases"].items()}},
              open(os.path.join(GC, "derived_heat_flux_9B1.json"), "w"), indent=2)
    print("GEOMETRY CHECKS 9B-1: %s" % ("ALL OK" if all_ok else "FAILED"))


if __name__ == "__main__":
    main()
