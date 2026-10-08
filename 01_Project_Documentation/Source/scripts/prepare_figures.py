# -*- coding: utf-8 -*-
"""Section 10B - copies the ACTUAL project figures used in the report into 13_Report/Figures.
RE-ANALYSIS 2026. No figure is generated or edited except that, where marked crop=True, the
image's own title strip (which carries the source document's figure number, e.g. "Figure 11 -")
is cropped off (or, where the title shares rows with an axis label, blanked within the title's own
columns) so it does not conflict with the report's numbering. All other pixel content is unchanged. Writes Figures/figure_sources.json (report key -> source path, SHA-256 of
the source and of the copy, crop flag, provenance class).
Usage: python prepare_figures.py <staged project root> <S9B2 figure dir> <13_Report root> <manifest csv>"""
import os, sys, json, hashlib, csv, shutil
import numpy as np
from PIL import Image
SRC, S9, OUT, MAN = sys.argv[1:5]
FIG = os.path.join(OUT, "Figures")
man = {}
with open(MAN, encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        man[r["path"].replace("\\", "/")] = r["sha256"]
F = [  # key, project-relative path, crop, provenance class
 ("drawing", "03_CAD_Geometry/Drawings/ENGINEERING_DRAWING.png", False, "drawing"),
 ("physics", "03_CAD_Geometry/Drawings/PHYSICS_SCHEMATIC.png", False, "drawing"),
 ("cad_full", "03_CAD_Geometry/Screenshots/01_full_cad_model.png", False, "cad_render"),
 ("cad_xsec", "03_CAD_Geometry/Screenshots/02b_cross_section_end_on.png", False, "cad_render"),
 ("cad_iface", "03_CAD_Geometry/Screenshots/05_fluid_solid_interface.png", False, "cad_render"),
 ("mesh_xsec", "05_Meshing/Screenshots/mesh_01_cross_section_full.png", False, "mesh_render"),
 ("mesh_infl", "05_Meshing/Screenshots/mesh_03_inflation_near_wall.png", False, "mesh_render"),
 ("mesh_iface", "05_Meshing/Screenshots/mesh_04_interface_conformity.png", False, "mesh_render"),
 ("mesh_refine", "05_Meshing/Screenshots/mesh_08_refinement_comparison.png", False, "mesh_render"),
 ("mesh_oq", "05_Meshing/Screenshots/mesh_10_orthogonal_quality_hist.png", False, "mesh_render"),
 ("cfd_vel", "06_Fluent_CFD/Figures/fig01_velocity_contour.png", True, "cfd_plot"),
 ("cfd_press", "06_Fluent_CFD/Figures/fig04_pressure_contour.png", True, "cfd_plot"),
 ("cfd_tfluid", "06_Fluent_CFD/Figures/fig05_fluid_temperature_contour.png", True, "cfd_plot"),
 ("cfd_tsolid", "06_Fluent_CFD/Figures/fig06_solid_temperature_contour.png", True, "cfd_plot"),
 ("cfd_touter", "06_Fluent_CFD/Figures/fig07_outer_wall_temperature.png", True, "cfd_plot"),
 ("cfd_flux", "06_Fluent_CFD/Figures/fig08_wall_heat_flux.png", True, "cfd_plot"),
 ("cfd_yplus", "06_Fluent_CFD/Figures/fig09_yplus.png", True, "cfd_plot"),
 ("cfd_paxial", "06_Fluent_CFD/Figures/fig10_pressure_axial.png", True, "cfd_plot"),
 ("cfd_taxial", "06_Fluent_CFD/Figures/fig11_bulk_temperature_axial.png", True, "cfd_plot"),
 ("cfd_twall", "06_Fluent_CFD/Figures/fig12_through_wall_temperature.png", True, "cfd_plot"),
 ("cfd_vprof", "06_Fluent_CFD/Figures/fig13_velocity_profiles.png", True, "cfd_plot"),
 ("cfd_trad", "06_Fluent_CFD/Figures/fig14_radial_temperature.png", True, "cfd_plot"),
 ("cfd_nuf", "06_Fluent_CFD/Figures/fig15_nusselt_friction.png", True, "cfd_plot"),
 ("cfd_conv", "06_Fluent_CFD/Figures/fig16_convergence.png", True, "cfd_plot"),
 ("cfd_pdecomp", "06_Fluent_CFD/Figures/fig17_pressure_decomposition.png", True, "cfd_plot"),
 ("mi_dp", "09_Mesh_Independence/Plots/MI01_cells_vs_pressure_drop.png", False, "cfd_plot"),
 ("mi_tout", "09_Mesh_Independence/Plots/MI02_cells_vs_outlet_temperature.png", False, "cfd_plot"),
 ("mi_q", "09_Mesh_Independence/Plots/MI03_cells_vs_heat_transfer_rate.png", False, "cfd_plot"),
 ("mi_tmax", "09_Mesh_Independence/Plots/MI04_cells_vs_max_solid_temperature.png", False, "cfd_plot"),
 ("mi_dtw", "09_Mesh_Independence/Plots/MI05_cells_vs_midspan_through_wall_dT.png", False, "cfd_plot"),
 ("mi_nu", "09_Mesh_Independence/Plots/MI06_cells_vs_nusselt.png", False, "cfd_plot"),
 ("mi_f", "09_Mesh_Independence/Plots/MI07_cells_vs_friction_factor.png", False, "cfd_plot"),
 ("mi_yplus", "09_Mesh_Independence/Plots/MI08_yplus_statistics_vs_mesh.png", True, "cfd_plot"),
 ("mi_prof", "09_Mesh_Independence/Plots/MI09_profiles_three_meshes.png", True, "cfd_plot"),
 ("mi_geom", "09_Mesh_Independence/Plots/MI10_geometry_vs_resolution.png", True, "cfd_plot"),
 ("mi_fric", "09_Mesh_Independence/Plots/MI11_F029_friction_evidence.png", True, "cfd_plot"),
 ("map_side", "07_Thermal_Analysis/Figures/F7A_03_side_by_side_and_difference.png", True, "data_plot"),
 ("map_axial", "07_Thermal_Analysis/Figures/F7A_04_axial_wall_temperature.png", True, "data_plot"),
 ("map_mid", "07_Thermal_Analysis/Figures/F7A_05_through_wall_midspan.png", True, "data_plot"),
 ("mech_temp", "08_Structural_Analysis/Figures/Mechanical/LC1_00_Imported_Temperature_iso.png", False, "mechanical"),
 ("lc1_def", "08_Structural_Analysis/Figures/Mechanical/LC1_Total_Deformation_iso.png", False, "mechanical"),
 ("lc1_vm", "08_Structural_Analysis/Figures/Mechanical/LC1_Equivalent_Stress_averaged_iso.png", False, "mechanical"),
 ("lc2_def", "08_Structural_Analysis/Figures/Mechanical/LC2_Total_Deformation_iso.png", False, "mechanical"),
 ("lc2_vm", "08_Structural_Analysis/Figures/Mechanical/LC2_Equivalent_Stress_averaged_iso.png", False, "mechanical"),
 ("lc2_sz", "08_Structural_Analysis/Figures/Mechanical/LC2_Axial_Stress_Sz_global_iso.png", False, "mechanical"),
 ("lc1_prof", "08_Structural_Analysis/Figures/F7B_01_LC1_axial_profiles.png", False, "data_plot"),
 ("lc2_prof", "08_Structural_Analysis/Figures/F7B_02_LC2_axial_profiles.png", False, "data_plot"),
 ("inlet_zone", "08_Structural_Analysis/Figures/F7B_03_inlet_zone_detail.png", False, "data_plot"),
 ("press_eff", "08_Structural_Analysis/Figures/F7B_04_pressure_effect.png", False, "data_plot"),
 ("exp_comp", "08_Structural_Analysis/Figures/F7B_05_expansion_comparison.png", False, "data_plot"),
 ("sec_force", "08_Structural_Analysis/Figures/F7B_06_section_force_equilibrium.png", False, "data_plot"),
 ("smesh_fam", "08_Structural_Analysis/Mesh_Study/figures/F8B_01_structural_mesh_comparison.png", False, "data_plot"),
 ("smesh_lc2", "08_Structural_Analysis/Mesh_Study/figures/F8B_02_LC2_stress_vs_mesh.png", False, "data_plot"),
 ("smesh_lc1", "08_Structural_Analysis/Mesh_Study/figures/F8B_04_LC1_stress_vs_mesh.png", False, "data_plot"),
 ("smesh_lam", "08_Structural_Analysis/Mesh_Study/figures/F8B_06_lambda1_vs_mesh.png", False, "data_plot"),
 ("smesh_inlet", "08_Structural_Analysis/Mesh_Study/figures/F8B_09_inlet_region_stress.png", False, "data_plot"),
 ("smesh_iso", "08_Structural_Analysis/Mesh_Study/figures/Mechanical/B_mesh_iso.png", False, "mechanical"),
 ("smesh_end", "08_Structural_Analysis/Mesh_Study/figures/Mechanical/B_mesh_end_face.png", False, "mechanical"),
 ("bk_iso", "08_Structural_Analysis/Buckling/figures/Mechanical/LC2_Linear_Buckling_Mode_1_Total_Deformation_iso.png", False, "mechanical"),
 ("bk_side", "08_Structural_Analysis/Buckling/figures/Mechanical/LC2_Linear_Buckling_Mode_1_Total_Deformation_side_YZ.png", False, "mechanical"),
 ("bk_s2", "08_Structural_Analysis/Buckling/figures/Mechanical/LC2NS_Linear_Buckling_Mode_1_Total_Deformation_iso.png", False, "mechanical"),
 ("bk_shape", "08_Structural_Analysis/Buckling/figures/F8A_01_buckling_mode_1_shape.png", False, "data_plot"),
 ("bk_pcr", "08_Structural_Analysis/Buckling/figures/F8A_03_critical_load_summary.png", False, "data_plot"),
 ("bk_lf", "08_Structural_Analysis/Buckling/figures/F8A_04_load_factor_comparison.png", False, "data_plot"),
 ("bk_s3", "10_Parametric_Study/Structural_Cases/S3_LC2_INTERMEDIATE/Figures/S3_BK_Mode_1_iso.png", False, "mechanical"),
 ("bk_s3side", "10_Parametric_Study/Structural_Cases/S3_LC2_INTERMEDIATE/Figures/S3_BK_Mode_1_side_YZ.png", False, "mechanical"),
 ("t01_mesh", "10_Parametric_Study/Structural_Cases/T01_THIN/Figures/T01_THIN_mesh_end_face.png", False, "mechanical"),
 ("t03_mesh", "10_Parametric_Study/Structural_Cases/T03_THICK/Figures/T03_THICK_mesh_end_face.png", False, "mechanical"),
 ("an_axial", "02_Engineering_Calculations/calculation_plots/01_axial_temperatures.png", False, "analytical_plot"),
 ("an_radial", "02_Engineering_Calculations/calculation_plots/03_radial_wall_temperature.png", False, "analytical_plot"),
 ("an_press", "02_Engineering_Calculations/calculation_plots/05_pressure_breakdown.png", False, "analytical_plot"),
]
for k in range(1, 16):
    n = [f for f in os.listdir(S9) if f.startswith("F%02d_" % k)][0]
    F.append(("par%02d" % k, "10_Parametric_Study/Results/Figures/" + n, False, "data_plot"))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


def crop_title(im):
    for need in (4, 2):
        out, cut = _crop(im, need)
        if cut:
            return out, cut
    # fallback: title line shares rows with an axis tick label; restrict the gap search to the title's columns
    a = np.asarray(im.convert("L"), dtype=float) < 140
    r0 = int(np.argmax(a.any(axis=1)))
    cols = a[r0:r0 + 12].any(axis=0)
    lo, hi = np.where(cols)[0][[0, -1]]
    sub = a[:, lo:hi + 1].any(axis=1)
    r, run = r0, 0
    while r < a.shape[0] and run < 3:
        run = 0 if sub[r] else run + 1
        r += 1
    if r - r0 > 0.08 * a.shape[0]:
        return im, 0
    im = im.convert("RGB").copy()                     # blank the title strip only (its own columns), keep the tick labels
    from PIL import ImageDraw
    ImageDraw.Draw(im).rectangle((max(lo - 3, 0), max(r0 - 3, 0), min(hi + 3, im.size[0] - 1), r - 3), fill="white")
    return im, r - 3


def _crop(im, need):
    a = np.asarray(im.convert("L"), dtype=float)
    dark = (a < 140).any(axis=1)
    r0 = int(np.argmax(dark))
    r, run = r0, 0
    while r < a.shape[0]:
        if dark[r]:
            run = 0
        else:
            run += 1
            if run >= need:
                break
        r += 1
    if r - r0 > 0.08 * a.shape[0]:      # no clean single title line found: leave the image unchanged
        return im, 0
    cut = r - 2
    return im.crop((0, cut, im.size[0], im.size[1])), cut


rec = []
for key, rel, crop, prov in F:
    src = os.path.join(S9, os.path.basename(rel)) if rel.startswith("10_Parametric_Study/Results/Figures/") else os.path.join(SRC, *rel.split("/"))
    h = sha(src)
    base = os.path.basename(rel)
    if crop:
        im = Image.open(src)
        out, cut = crop_title(im)
        dst = base.replace(".png", "_nt.png")
        out.save(os.path.join(FIG, dst))
    else:
        dst, cut = base, 0
        shutil.copyfile(src, os.path.join(FIG, dst))
    rec.append({"key": key, "project_path": rel, "file": dst, "source_sha256": h, "manifest_sha256": man.get(rel),
                "source_matches_project": man.get(rel) == h, "title_strip_cropped_px": cut, "provenance": prov,
                "copy_sha256": sha(os.path.join(FIG, dst))})
json.dump(rec, open(os.path.join(FIG, "figure_sources.json"), "w"), indent=1)
bad = [r["key"] for r in rec if not r["source_matches_project"]]
print("figures", len(rec), "cropped", sum(1 for r in rec if r["title_strip_cropped_px"]), "not matching manifest:", bad)
