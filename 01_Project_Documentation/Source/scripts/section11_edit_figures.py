# -*- coding: utf-8 -*-
"""Section 11 - remove the burned-in 'RE-ANALYSIS 2026 ...' provenance phrases from the report copies of the figures.
Two operations only: (1) crop a single-line provenance footer off the bottom of the image (no pixel changed);
(2) mask only the framing phrase inside a multi-line explanatory note with the surrounding background colour, then trim the
blank rows this leaves at the bottom. Plot areas, axes, labels, legends and data are not touched. Every operation is recorded."""
import sys, os, re, csv, io, json, hashlib, subprocess
import numpy as np
from PIL import Image

FIG, OUT = sys.argv[1:3]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest().upper()
CROP = ["01_axial_temperatures.png", "F14_support_vs_lambda1.png", "F15_support_vs_LC2_stress.png", "F7A_03_side_by_side_and_difference_nt.png",
        "F7A_05_through_wall_midspan_nt.png", "F7B_01_LC1_axial_profiles.png", "F7B_02_LC2_axial_profiles.png", "F8A_03_critical_load_summary.png",
        "F8A_04_load_factor_comparison.png", "F8B_01_structural_mesh_comparison.png", "F8B_02_LC2_stress_vs_mesh.png"]
MASK = ["MI01_cells_vs_pressure_drop.png", "MI04_cells_vs_max_solid_temperature.png", "MI06_cells_vs_nusselt.png", "MI07_cells_vs_friction_factor.png",
        "MI11_F029_friction_evidence_nt.png", "fig01_velocity_contour_nt.png", "fig04_pressure_contour_nt.png", "fig05_fluid_temperature_contour_nt.png",
        "fig06_solid_temperature_contour_nt.png", "fig08_wall_heat_flux_nt.png", "fig09_yplus_nt.png", "fig10_pressure_axial_nt.png",
        "fig11_bulk_temperature_axial_nt.png", "fig12_through_wall_temperature_nt.png", "fig13_velocity_profiles_nt.png",
        "fig14_radial_temperature_nt.png", "fig15_nusselt_friction_nt.png", "fig16_convergence_nt.png", "ENGINEERING_DRAWING.png", "PHYSICS_SCHEMATIC.png"]


def words(path):
    tsv = subprocess.run(["tesseract", path, "-", "--psm", "3", "tsv"], capture_output=True, text=True).stdout
    out = []
    for r in csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE):
        if r["level"] == "5" and r["text"].strip():
            out.append({"t": r["text"], "x": int(r["left"]), "y": int(r["top"]), "w": int(r["width"]), "h": int(r["height"]),
                        "line": (int(r["block_num"]), int(r["par_num"]), int(r["line_num"]))})
    return out


def bg_of(a, box, pad=6):
    x0, y0, x1, y1 = box
    H, W = a.shape[:2]
    ring = np.concatenate([a[max(y0 - pad, 0):y0, x0:x1].reshape(-1, a.shape[2]), a[y1:min(y1 + pad, H), x0:x1].reshape(-1, a.shape[2]),
                           a[y0:y1, max(x0 - pad, 0):x0].reshape(-1, a.shape[2]), a[y0:y1, x1:min(x1 + pad, W)].reshape(-1, a.shape[2])])
    return np.median(ring, axis=0).astype(a.dtype)


def trim_bottom(a, keep):
    """remove blank rows at the bottom, keeping `keep` px of margin (the original bottom margin)"""
    g = a[..., :3].mean(axis=2) if a.ndim == 3 else a
    ink = np.where((g < 235).any(axis=1))[0]
    last = int(ink.max()) if len(ink) else a.shape[0] - 1
    return a[:min(last + 1 + keep, a.shape[0])]


man = []
os.makedirs(OUT, exist_ok=True)
for f in CROP + MASK:
    p = os.path.join(FIG, f)
    im = Image.open(p)
    mode = im.mode
    a = np.array(im.convert("RGBA" if "A" in mode else "RGB"))
    H, W = a.shape[:2]
    g = a[..., :3].mean(axis=2)
    ink_rows = (g < 235).any(axis=1)
    rows = np.where(ink_rows)[0]
    orig_bottom_margin = H - 1 - int(rows.max())
    rec = {"file": f, "size_before": [W, H], "sha256_before": sha(p)}
    if f in CROP:
        # the footer is the last ink band; cut in the middle of the white gap above it
        last = int(rows.max()); y = last
        while y > 0 and ink_rows[y]:
            y -= 1
        band_top = y + 1
        gap_bot = y
        while y > 0 and not ink_rows[y]:
            y -= 1
        gap_top = y + 1
        cut = (gap_top + gap_bot) // 2 + 1
        new = a[:cut]
        rec.update({"operation": "crop footer line", "crop_box": [0, 0, W, cut], "removed_band_px": [band_top, last]})
    else:
        ws = words(p)
        boxes = []
        if f == "PHYSICS_SCHEMATIC.png":
            ln = [w for w in ws if re.search(r"RE-ANALYSE", w["t"], re.I)][0]["line"]
            boxes = [w for w in ws if w["line"] == ln]
        else:
            idx = [i for i, w in enumerate(ws) if re.search(r"RECONSTRUC", w["t"], re.I)]
            for i0 in idx:
                j = i0
                endpat = r"values$" if f == "ENGINEERING_DRAWING.png" else r"\.$"
                while True:
                    boxes.append(ws[j])
                    if re.search(endpat, ws[j]["t"]) or j + 1 >= len(ws):
                        break
                    if f == "ENGINEERING_DRAWING.png" and not re.search(r"RECONSTRUC|\(2026\)|dimensions|newly|selected|NOT|original|internship|values|-", ws[j + 1]["t"]):
                        break
                    j += 1
        masked = []
        bylines = {}
        for w in boxes:
            bylines.setdefault(w["line"], []).append(w)
        for ln, lw in bylines.items():
            # one rectangle per text line: union of the phrase's words (covers hyphens and spaces) plus trailing punctuation
            x0 = min(w["x"] for w in lw) - 3; x1 = max(w["x"] + w["w"] for w in lw) + 18
            y0 = min(w["y"] for w in lw) - 3; y1 = max(w["y"] + w["h"] for w in lw) + 4
            box = (max(x0, 0), max(y0, 0), min(x1, W), min(y1, H))
            col = bg_of(a, box)
            a[box[1]:box[3], box[0]:box[2]] = col
            masked.append([*box, " ".join(w["t"] for w in lw)])
            # residual specks (detached punctuation) on the same text band, just beyond the rectangle
            band = a[box[1]:box[3], max(box[0] - 25, 0):min(box[2] + 30, W)]
            gb = band[..., :3].mean(axis=2)
            ink = gb < 200
            if ink.any():
                from scipy import ndimage
                lab, n = ndimage.label(ink)
                for k in range(1, n + 1):
                    ys, xs = np.where(lab == k)
                    if len(ys) < 60 and (xs.max() - xs.min()) < 12:
                        X0 = max(box[0] - 25, 0)
                        sub = (X0 + xs.min() - 2, box[1] + ys.min() - 2, X0 + xs.max() + 3, box[1] + ys.max() + 3)
                        # only specks that touch the masked band horizontally adjacent (not other words)
                        if sub[0] >= box[2] - 2:      # right of the phrase only (left of it is the preceding sentence)
                            a[sub[1]:sub[3], sub[0]:sub[2]] = col
                            masked.append([*sub, "speck"])
        new = trim_bottom(a, orig_bottom_margin)
        rec.update({"operation": "mask framing phrase" + (" (whole subtitle line)" if f == "PHYSICS_SCHEMATIC.png" else ""),
                    "masked_words": masked, "trimmed_to_height": int(new.shape[0])})
    out = Image.fromarray(new)
    if out.mode != mode and mode in ("RGB", "RGBA", "L", "P"):
        out = out.convert(mode) if mode != "P" else out
    op = os.path.join(OUT, f)
    out.save(op, optimize=True)
    rec.update({"size_after": list(out.size), "sha256_after": sha(op)})
    man.append(rec)
    print("%-48s %-28s %s -> %s" % (f, rec["operation"][:28], rec["size_before"], rec["size_after"]))
json.dump(man, open(os.path.join(OUT, "figure_edits_section11.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=int)
