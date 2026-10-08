# -*- coding: utf-8 -*-
"""Section 10C-1 - figures for the final presentation (RE-ANALYSIS 2026).
Every image is a 2026 project file that was hash-verified in Section 10B (13_Report/Figures/figure_sources.json,
SHA-256 against the Section 10A manifest). For the slides an image is either copied unchanged or CROPPED
(a rectangle of the original pixels: panel selection, removal of the source-document title/footnote, or trimming
of empty white margin). No pixel value is changed, nothing is drawn onto an image, no image is generated.
Writes Figures/<name>.png and Figures/figure_manifest.json (source path, source SHA-256, crop box, output SHA-256).
Usage: python prepare_slide_figures.py <13_Report/Figures> <14_Presentation/Figures>"""
import os, sys, json, hashlib
import numpy as np
from PIL import Image

SRC, OUT = sys.argv[1:3]
meta = {d["file"]: d for d in json.load(open(os.path.join(SRC, "figure_sources.json"), encoding="utf-8"))}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


def trim_box(im, pad=12, thr=245):
    a = np.asarray(im.convert("L"))
    ys, xs = np.where(a < thr)
    return (max(int(xs.min()) - pad, 0), max(int(ys.min()) - pad, 0),
            min(int(xs.max()) + pad + 1, im.width), min(int(ys.max()) + pad + 1, im.height))


# name, source file in 13_Report/Figures, crop ("trim" | None | (x0, y0, x1, y1)), purpose / slide
FIGS = [
    ("cad_3d_interface", "05_fluid_solid_interface.png", (140, 195, 630, 370), "S1 title: SpaceClaim CAD, fluid body inside the solid annulus (title/footnote removed)"),
    ("drawing_longitudinal", "ENGINEERING_DRAWING.png", (110, 160, 2330, 896), "S3/S5: Section 3 drawing, longitudinal section (sheet frame, cross-section and title block removed)"),
    ("cad_cross_section", "02b_cross_section_end_on.png", (80, 100, 800, 815), "S5: end face drawn from the SpaceClaim tessellation (title/footnote removed)"),
    ("mesh_family", "mesh_08_refinement_comparison.png", (0, 178, 1790, 755), "S7: coarse / medium / fine CFD mesh cross-sections (title/footnote removed)"),
    ("convergence_residuals", "fig16_convergence_nt.png", (0, 40, 705, 742), "S7: panel (a) scaled residuals of the baseline run"),
    ("mapping_fluent_vs_mechanical", "F7A_03_side_by_side_and_difference_nt.png", (0, 0, 1760, 800), "S10: Fluent cell temperatures vs mapped Mechanical nodal temperatures (difference panel omitted)"),
    ("mech_imported_temperature", "LC1_00_Imported_Temperature_iso.png", "trim", "S10: imported body temperature in Mechanical (deg C legend as exported)"),
    ("mech_LC1_deformation", "LC1_Total_Deformation_iso.png", "trim", "S11: LC1 total deformation"),
    ("mech_LC1_vonmises", "LC1_Equivalent_Stress_averaged_iso.png", "trim", "S11: LC1 von Mises stress"),
    ("mech_LC2_deformation", "LC2_Total_Deformation_iso.png", "trim", "S11: LC2 total deformation"),
    ("mech_LC2_vonmises", "LC2_Equivalent_Stress_averaged_iso.png", "trim", "S11: LC2 von Mises stress"),
    ("mech_S1_mode1_side", "LC2_Linear_Buckling_Mode_1_Total_Deformation_side_YZ.png", "trim", "S12: S1 buckling mode 1, side view"),
    ("mech_S1_mode1_iso", "LC2_Linear_Buckling_Mode_1_Total_Deformation_iso.png", "trim", "S12/S13: S1 buckling mode 1, isometric"),
    ("mech_S3_mode1_iso", "S3_BK_Mode_1_iso.png", "trim", "S13: S3 buckling mode 1"),
    ("mech_S2_mode1_iso", "LC2NS_Linear_Buckling_Mode_1_Total_Deformation_iso.png", "trim", "S13: S2 (8A LC2NS) buckling mode 1"),
]

man = []
for name, f, crop, purpose in FIGS:
    p = os.path.join(SRC, f)
    im = Image.open(p)
    box = trim_box(im) if crop == "trim" else crop
    out = im.crop(box) if box else im
    op = os.path.join(OUT, name + ".png")
    out.save(op, optimize=True)
    m = meta[f]
    man.append({"slide_figure": name + ".png", "report_figure": f, "project_path": m["project_path"],
                "project_sha256": m["source_sha256"], "matches_10A_manifest": m["source_matches_project"],
                "report_copy_sha256": sha(p), "title_strip_removed_in_10B_px": m["title_strip_cropped_px"],
                "crop_box_px": list(box) if box else None, "size_px": list(out.size), "output_sha256": sha(op),
                "provenance": m["provenance"], "purpose": purpose})
    print("%-32s %-58s crop=%s -> %s" % (name, f, box, out.size))
json.dump(man, open(os.path.join(OUT, "figure_manifest.json"), "w", encoding="utf-8"), indent=1)
print("figures:", len(man), "all project files verified:", all(x["matches_10A_manifest"] for x in man))
