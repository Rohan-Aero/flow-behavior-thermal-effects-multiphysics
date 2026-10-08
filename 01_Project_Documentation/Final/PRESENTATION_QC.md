# PRESENTATION QC — Section 10C-1 Final Technical Presentation

**Deck:** `Final/Flow_Behavior_Thermal_Effects_Multiphysics_Presentation.pptx` — 18 slides, 16:9 (13.33 × 7.5 in), speaker notes on every slide
**SHA-256:** `54DD1C9ED3DAC633136CE5591DE5167084B433569569E64C1A5702F29029AE6A`
**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems — Rohan Balram Patel, Eleation internship (Feb–May 2025)
**Status:** RE-ANALYSIS 2026. The deck presents re-analysed engineering work. It is not a recovered copy of the original internship presentation. No simulation was run in 10C-1. No new data or engineering conclusions were introduced.

**QC result: PASS.** Every check in brief §10 passed. The remaining presentation issues are listed in §6.

---

## 1. Sources and method

| Item | Source |
|---|---|
| Numbers on slides, tables and charts | `11_Final_Audit/MASTER_PROJECT_DATA.csv`, read by row ID in `Source/scripts/build_slide_data.py`. SHA-256 of the master file: `727ADD0A…10722D3` |
| Findings and interpretation | `FINAL_ENGINEERING_AUDIT.md` §8 (findings A–L) and §15; final report Chapters 8–18 |
| Slide-8 CFD profiles | `06_Fluent_CFD/Profiles/axial_profiles_cfd.csv` (medium mesh); its SHA-256 is checked against the 10A manifest before use |
| Figures | 15 project images, hash-verified in 10B against the 10A manifest (`Figures/figure_manifest.json`) |
| QC | `Source/scripts/qc_10C1.py` reads the finished .pptx (slides, tables, chart XML, notes). The full record is `Final/qc_10C1_record.json` |
| Visual check | Every slide was rendered with LibreOffice (Carlito, the metric-compatible Calibri) and inspected, before and after every fix |

---

## 2. Checklist of brief §10

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | **Every number matches MASTER_PROJECT_DATA** | ✅ PASS | 328 numbers were checked (229 on slides, tables and charts; 99 in the speaker notes): 283 trace to the master dataset and 45 to exact values in project documents, with 0 untraced. For numbers with ≥ 3 significant digits: 172 master, 35 document. The document-traced values are not master rows; they are listed in §3. The chart series were compared too: all 9 parametric series equal the master values exactly, and all 6 slide-8 profile series equal the project CSV exactly. |
| 2 | **Every figure exists** | ✅ PASS | 15 pictures, 15 distinct. All are files of `Figures/` (matched by SHA-256), and each is tied by the manifest to a hash-verified project file. There are no unknown pictures, and every file in `Figures/` is used. |
| 3 | **Every chart is readable** | ✅ PASS | All 12 charts are native, editable PowerPoint charts. The smallest chart text is 10 pt (axis ticks). Data labels are 12 pt bold, and titles are 12–14 pt. |
| 4 | **No unsupported claim** | ✅ PASS | Every finding on slides 16 and 18 is an audit statement: A, D, F, G, H, I, J, K, L and §15. No new conclusion was added. |
| 5 | **No fake screenshot** | ✅ PASS | No image was generated or edited. The ANSYS images are Mechanical `Graphics.ExportImage` renders. The CFD, mesh and CAD images are project matplotlib renders of solver or geometry data, labelled as such in their captions. The drawing is the Section 3 project drawing. Crops are recorded in the manifest (§4). |
| 6 | **No factor-of-safety wording for λ₁** | ✅ PASS | Both occurrences (slide 12 and its notes) say λ₁ is "not a factor of safety". |
| 7 | **No "safe" / "optimal" claim** | ✅ PASS | There are 0 occurrences of safe, optimal, best or worst, apart from the negated "not a factor of safety". Supports S1/S3/S2 are "not ranked" (slide 13). |
| 8 | **No experimental-validation claim** | ✅ PASS | Every "validation" is negated (slides 9, 17 and 18, and the notes), or is the future-work item "Experimental validation" (slide 17). |
| 9 | **Re-analysis note present** | ✅ PASS | The brief §7 text appears verbatim on slide 2. A compact version is on slide 1, and there is a re-analysis footer on slides 2–17. The wording states facts and does not apologise. |
| 10 | **Slide numbers sequential** | ✅ PASS | 18 slides, each with a slide-number field (1–18). |
| 11 | **No text clipped** | ✅ PASS | An estimated text fit (Carlito metrics) flagged 0 text boxes. The visual inspection of all 18 renders found no clipped or overflowing text. |
| 12 | **No table overflowing** | ✅ PASS | The two tables (slides 9 and 14) lie inside the slide. The visual check found no cell overflow. |
| 13 | **No tiny unreadable labels** | ✅ PASS for slide-built content | Slide text is ≥ 10 pt; the only 9 pt text is the footer line. Chart text is ≥ 10 pt. Limitation: labels *inside* some project images are small at slide scale (see §6.1); their key values are repeated as native text. |
| 14 | **Shapes inside the slide** | ✅ PASS | 0 shapes out of bounds. The file passes the pptx validator ("All validations PASSED"). |

Additional brief requirements:

| Requirement | Result |
|---|---|
| 15–18 slides, 10–15 min | 18 slides. The speaker-note plan totals 14.7 min, and every slide falls between 30 and 90 s (35–65 s). |
| Story order | Problem → geometry → CFD → heat transfer → verification → thermal mapping → structure → buckling → supports → parametric → findings → limitations → conclusion (slides 3–18). |
| Speaker notes on every slide | 18 of 18. Each note gives what the audience sees, the engineering point, the number that matters and the transition. They are also exported to `Speaker_Notes/SPEAKER_NOTES.md`. |
| Modelling levels kept distinct | All 27 occurrences of 562.58 / 581.71 / 605.16 / 1.108 carry their level: 23 in the same sentence or box, and 4 through the card label, column header or table header. Slide 9 separates "Analytical (Section 2)" from "CFD (medium mesh)". |
| Screening ≠ simulation | Slide 14: "Every case, not an estimate". The notes state that no screening estimate enters the results. |
| One-way coupling, not FSI | Slide 10: "Not a two-way FSI model …". |
| λ₁ interpretation | Slide 12 covers the idealised elastic model; no imperfections, plasticity or post-buckling; and "not a collapse load and not a factor of safety". |
| No adequacy / certification claim | Slide 18 and its notes state that the results "do not show that a real component is structurally adequate". There are 0 occurrences of "certif". |
| No supervisor names, no stock photos, no animation | None used. |

---

## 3. Numbers that are not master-dataset rows

These are all quoted from project result documents, exactly as in the final report:

| Slide | Value | Project source |
|---|---|---|
| 7 | Medium → fine −1.75 K, fine solid ≈ 157 k nodes, 128,000-node limit, apparent order 1.2–1.6 | `PROJECT_STATE.md` §12, `FINAL_ENGINEERING_SYNTHESIS.md`, `FINAL_ENGINEERING_AUDIT.md` §8 C. The −1.75 K is also M039 − M054 |
| 9 | Analytical Re 29,957 | `02_Engineering_Calculations/baseline_results.csv` (Re_in = 29,956.55) |
| 9 | Differences −0.77 %, −0.071 %, −19.1 K, and −15.0 / −4.2 K split | `CFD_VS_ANALYTICAL.md`, `PROJECT_STATE.md` §5b (arithmetic on M036–M039 and M071–M074) |
| 10 | Mapped range 423.84–562.56 K (source 423.84–562.54 K), ≤ 0.081 K, 108,252 nodes, 0.70 % flow-area change | `THERMAL_MAPPING_NOTES.md`, `PROJECT_STATE.md` §13.1. Nodes also M081; 0.70 % is the M015 note |
| 11 | 32× at mid-span | `STRUCTURAL_RESULTS.md` / `PROJECT_STATE.md` §14 |
| 14–15 | Case values 21.15 / 25.85 m/s, 7200 / 8800 W/m², Dₒ 36 / 44 mm | `PARAMETRIC_STUDY_NOTES.md`, `PROJECT_STATE.md` §17 |
| 15–16 | Parametric changes (−13.3 / +14.1 %, −28.1 / +28.6 K, −11.0 / +11.2 %, −36.6 / +49.3 %, −0.61 / +0.50 K) | `FINAL_ENGINEERING_AUDIT.md` §8 J–L (arithmetic on M125–M178) |

Display rounding follows the report:

- 1.8443 → 1.844 mm
- 0.1349 → 0.135 mm
- 605.161 → 605.16 MPa
- λ₁ to 3 decimals

The chart data labels use 1 decimal (e.g. 438.1 Pa) or, for P_cr, integer kN.

---

## 4. Figures used

| Slide | Figure (`Figures/`) | Project file | Treatment |
|---|---|---|---|
| 1 | `cad_3d_interface.png` | `03_CAD_Geometry/Screenshots/05_fluid_solid_interface.png` | crop: source title and footnote removed |
| 5 | `drawing_longitudinal.png` | `03_CAD_Geometry/Drawings/ENGINEERING_DRAWING.png` | crop: View 1 only |
| 5 | `cad_cross_section.png` | `03_CAD_Geometry/Screenshots/02b_cross_section_end_on.png` | crop: title and footnote removed |
| 7 | `mesh_family.png` | `05_Meshing/Screenshots/mesh_08_refinement_comparison.png` | crop: title, panel labels and footnote removed; replaced by slide labels |
| 7 | `convergence_residuals.png` | `06_Fluent_CFD/Figures/fig16_convergence.png` | crop: panel (a) residuals |
| 10 | `mapping_fluent_vs_mechanical.png` | `07_Thermal_Analysis/Figures/F7A_03_side_by_side_and_difference.png` | crop: Fluent and Mechanical panels (difference panel omitted) |
| 10 | `mech_imported_temperature.png` | `08_Structural_Analysis/Figures/Mechanical/LC1_00_Imported_Temperature_iso.png` | white-margin trim only |
| 11 | `mech_LC1_deformation.png`, `mech_LC1_vonmises.png`, `mech_LC2_deformation.png`, `mech_LC2_vonmises.png` | `08_Structural_Analysis/Figures/Mechanical/LC1_/LC2_…_iso.png` | white-margin trim only |
| 12 | `mech_S1_mode1_side.png` | `08_Structural_Analysis/Buckling/figures/Mechanical/LC2_Linear_Buckling_Mode_1_Total_Deformation_side_YZ.png` | white-margin trim only |
| 13 | `mech_S1_mode1_iso.png`, `mech_S3_mode1_iso.png`, `mech_S2_mode1_iso.png` | `…/LC2_Linear_Buckling_Mode_1_…_iso.png`, `10_Parametric_Study/…/S3_BK_Mode_1_iso.png`, `…/LC2NS_Linear_Buckling_Mode_1_…_iso.png` | white-margin trim only |

A crop keeps a rectangle of original pixels. No pixel value was changed and nothing was drawn onto an image. Every crop box and output hash is in `Figures/figure_manifest.json`.

**Native slide graphics** (built in PowerPoint from verified data, editable):

- 12 charts:
  - slide 8: velocity, pressure and temperature profiles from the project CSV;
  - slide 15: nine parametric charts from the master dataset.
- 2 tables: slide 9 (analytical vs CFD) and slide 14 (parametric design).
- Schematic diagrams:
  - slide 3: duct and physics chain, labelled "schematic, not to scale";
  - slides 2, 6, 10 and 12: tool chain and process flows;
  - slide 14: one-factor-at-a-time diagram.

---

## 5. Wording review

17 sensitive-word occurrences were found; 16 are negated. The one not negated is "Experimental validation" as a **future-work** item on slide 17, which is correct.

The negated occurrences:

- "not experimental validation" (slide 9 and notes);
- "verified, not validated" (slide 17 and notes);
- "not validated against measurement" (slide 18);
- "Not a two-way FSI model" (slide 10 and notes);
- "Not a collapse load and not a factor of safety" (slide 12 and notes);
- "do not show that a real component is structurally adequate" (slide 18 and notes).

---

## 6. Remaining presentation issues (not failures)

1. **Labels inside some project images are small at slide scale.**
   - The ANSYS Mechanical legends and scale bars on slides 10, 11 and 13 fall to about 3–5 pt.
   - The embedded axis labels of the drawing (slide 5), mesh plots and residual plot (slide 7) and mapping plot (slide 10) are about 5–8 pt.
   - These images are reproduced as exported, without redrawing. Every value that matters is also given as native slide text (≥ 12 pt): stat cards, captions and λ₁ values. Slide 12's buckling render is shown large, so its legend is legible.
2. **Timing is at the upper end of the target.** The note plan is 14.7 min, and the notes hold 2,363 words. Speaking them in full at an unhurried pace can exceed 15 min. They are guidance, so trimming slides 9, 12 and 15 is the easiest way to stay near 12–13 min.
3. **Fonts.** The deck uses Calibri. The QC renders used Carlito, which has identical metrics. On a machine without Calibri, PowerPoint substitutes a font and line breaks may shift slightly.
4. **Chart style in PowerPoint versus LibreOffice.** The charts were checked in LibreOffice renders. PowerPoint may place data labels a few points differently; nothing depends on exact label positions.

---

## 7. Reproduce

```bash
cd 14_Presentation/Source
python scripts/build_slide_data.py <MASTER_PROJECT_DATA.csv> <06_Fluent_CFD/Profiles/axial_profiles_cfd.csv> ../Tables
python scripts/prepare_slide_figures.py <13_Report/Figures> ../Figures
node build_deck.js                                   # needs pptxgenjs; notes in notes.js
python scripts/postprocess_pptx.py ../Final/Flow_Behavior_Thermal_Effects_Multiphysics_Presentation.pptx
python scripts/export_notes.py ../Final/Flow_Behavior_Thermal_Effects_Multiphysics_Presentation.pptx ../Speaker_Notes
python scripts/qc_10C1.py ../Final/Flow_Behavior_Thermal_Effects_Multiphysics_Presentation.pptx .. <MASTER_PROJECT_DATA.csv> <out.json> <project folder> [<section outputs>]
```

---

## 8. Copy in the project folder

All 33 files of `14_Presentation` were written to `<PROJECT_ROOT>\14_Presentation\` and verified there on 2026-09-30:

- **Non-image files are byte-identical** to the working copies (SHA-256 per file). These are the deck, the QC files, the notes, the tables and the scripts. The deck is `54DD1C9E…29AE6A` on both sides.
- **The 15 PNG figures carry one extra chunk.** The file-transfer bridge inserted a C2PA content-credentials chunk (`caBX`, 5,758 bytes) into each PNG. Their image chunks (IHDR, IDAT, IEND) are byte-identical to the working copies, so no pixel differs. Only the whole-file SHA-256 differs from the `output_sha256` recorded in `Figures/figure_manifest.json`. The pictures embedded in the .pptx are the unmodified working copies.
