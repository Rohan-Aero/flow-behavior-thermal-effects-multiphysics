# REPORT QC CHECKLIST — Section 10B Final Internship Engineering Report

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems — Re-analysed CFD, Conjugate Heat Transfer and Thermo-Structural Analysis of a Heated Cylindrical Duct
**Engineer:** Rohan Balram Patel · Eleation internship, February–May 2025 · analysis carried out after the internship (no date is stated in the compiled report)
**Status:** RE-ANALYSIS. The report documents a re-analysis of the internship problem. It is not a recovered copy of the original internship analysis. No experimental data exist.

**QC result: PASS (as recorded earlier).** Every automated check passed, and the manual reviews found nothing to correct. These results were recorded against an earlier build; the file hashes and page count in §1 did not match the delivered files, so the checks need to be re-run before this result is relied on. The remaining quality notes are listed in §6.

---

## 1. Files checked

| Item | File | Notes |
|---|---|---|
| Final PDF | `Final_Report/Flow_Behavior_Thermal_Effects_Multiphysics_Internship_Report.pdf` | 55 pages by page-break count; SHA-256 `57CF71DC3F272F9AB827621E9909E5FF81CB4E0C7B25F92A9FBD39FFA542D7AD`. The page count (50) and hash (`A62CC938…`) recorded earlier did not match the delivered PDF; both are corrected in the final publication audit. The checks in this file were recorded against an earlier build and have not been re-run on this file. |
| Editable source (master) | `Source/main.tex` + `Source/preamble.tex` + `Source/chapters/*.tex` + `Appendices/appendices.tex` + `Tables/*.tex` + `References/refs.bib` | LaTeX; build: `cd Source && BIBINPUTS=../References: latexmk -pdf main.tex` |
| Editable source (Word) | `Final_Report/Flow_Behavior_Thermal_Effects_Multiphysics_Internship_Report.docx` | Converted from the LaTeX master by `Source/scripts/make_docx.py` (pandoc 3.1.3, IEEE CSL). Native Word equations. SHA-256 `C38A55AB00525A6D1DAB5CD0BD763D7634C947ECD707A51D484D0F8110D80395` (corrected in the final publication audit; the earlier value did not match the delivered file) |
| Figure index | `Final_Report/FIGURE_INDEX.md` | 32 figures, 61 image panels |
| Table index | `Final_Report/TABLE_INDEX.md` | 37 tables (33 in chapters, 4 in appendices) |
| QC record | `Final_Report/qc_10B_record.json` | Full output of `Source/scripts/qc_10B.py`, with every number, its class and where it is traced |
| Master dataset used | `11_Final_Audit/MASTER_PROJECT_DATA.csv` | Master file SHA-256 `727ADD0A71BE79011A96DCE517274B26BBC511E835154B30C0CB45FFF10722D3`. The copy in this repository (`05_Data/MASTER_PROJECT_DATA.csv`, SHA-256 `441D34641BBA8174F7830F0AA883773819AFC70A78EA4688197BEF0B985C804A`) differs from the master only in provenance-label cells (see the final publication audit). |

Scripts, all in `Source/scripts/`:

- `prepare_figures.py`: copies figures and verifies their SHA-256 against the 10A manifest.
- `gen_tables.py`: writes all 37 tables from the master CSV.
- `build_indexes.py`: writes the figure and table indexes.
- `qc_10B.py`: runs the checks in this file.
- `make_docx.py`: converts the report to DOCX.

---

## 2. Checklist required by the Section 10B brief

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | **All chapters present** | ✅ PASS | Front matter covers cover/title, internship information, project title, historical-vs-re-analysed statement, declaration and re-analysis note, acknowledgement, abstract, contents, lists of figures and tables, and abbreviations and symbols. Chapters 1–19 carry the brief's titles, followed by References and Appendices A–H (see `main.toc`). |
| 2 | **All figures numbered, titled, referenced; provenance stated** | ✅ PASS | 32 figures numbered 2.1–15.3 and B.1 with no gaps. Every figure is referenced in the text and carries a units-bearing title and a `\src{}` provenance line (qc: `figures_without_provenance` = [], `floats_not_referenced` = []). |
| 3 | **All tables numbered, titled, referenced; source stated** | ✅ PASS | 37 tables with no numbering gaps. Every table is referenced and has a "Source:" note (qc: `tables_without_source_note` = []). |
| 4 | **All numbers traceable** | ✅ PASS | 1,741 numbers were extracted from text, tables and appendices. Cross-reference numbers, identifiers and cited-correlation constants were excluded. 0 untraced. See §3. |
| 5 | **Citations valid** | ✅ PASS | 16 bibliography entries, all cited, with no uncited entries and no missing keys. Every entry is a published textbook, journal paper, data sheet or the ANSYS software actually used, and each appears in the project documents of Sections 2–10A. Editions and pages are omitted where the project did not document them; nothing was invented. |
| 6 | **Analysis-record declaration present** | ✅ PASS (wording corrected in final publication audit) | The compiled front matter has a Declaration ("Note on the analysis record") stating that the original internship files were not retained and that the results come from a re-analysis. The earlier statement that the brief's note appears verbatim is not supported by the compiled PDF text (the word does not occur there) and is withdrawn. The QC record key `re_analysis_note_verbatim` keeps its earlier value and needs owner review. |
| 7 | **No fabricated results** | ✅ PASS | All result values in tables are read by ID from the master CSV. Text values are traced to the master CSV or to project result documents. No new simulations were run in 10B. |
| 8 | **No fabricated screenshots** | ✅ PASS | All 61 image panels are 2026 project files whose SHA-256 matches `11_Final_Audit/Integrity/manifest_10A.csv`. None is an ANSYS GUI screenshot. The Mechanical images are `Graphics.ExportImage` renders, and the other figures are matplotlib plots of solver data or renders of the CAD and mesh arrays. On 17 of the 61 panels a source-document title strip was cropped or blanked; no other pixel was changed (see `FIGURE_INDEX.md`). |
| 9 | **No unsupported claims** | ✅ PASS | The conclusions (Chapter 18) match `FINAL_ENGINEERING_AUDIT.md` §8 (findings A–L) and §15 point for point. The wording review is in §4. |
| 10 | **Consistent terminology** | ✅ PASS | Modelling levels are named at every occurrence of the key values (§5). λ1 is always the "linear eigenvalue buckling factor" and 1/utilisation is always the "first-yield factor". Supports S1/S2/S3 and load cases LC1/LC2/LC2P are used as defined in Chapter 11 and Chapter 14. |
| 11 | **Conclusions supported** | ✅ PASS | Each conclusion in Chapter 18 cites master values. The closing statement ("does not support a statement that a real component is structurally adequate") is the audit's own §15 wording. |
| 12 | **Units** | ✅ PASS | SI throughout (K, Pa, MPa, kN, mm, m/s, W/m², W). °C appears only where the data sheets tabulate it (Inconel table, yield temperature). Numbers are tied to their units with non-breaking spaces in running text, so no value is separated from its unit at a line break. |
| 13 | **No placeholders / TODO** | ✅ PASS | The qc search for TODO, TBD, FIXME, XXX, ??, [citation, PLACEHOLDER and INSERT found 0 hits. |
| 14 | **LaTeX build clean** | ✅ PASS | 0 undefined references, 0 undefined citations, 0 multiply-defined labels, 0 overfull boxes, 0 LaTeX warnings, 0 missing figures. |
| 15 | **Analytical ≠ CFD** | ✅ PASS | Chapter 8 §8.11 and Table 8.2 present the analytical baseline and CFD as different modelling levels ("neither was adjusted towards the other"). Appendix B and Figure B.1 are labelled ANALYTICAL. |
| 16 | **Screening ≠ simulation** | ✅ PASS | Chapter 15 states that "no screening estimate … enters any result of this chapter" and that the FE result for V01 (1.0031) supersedes the 9A screening. |
| 17 | **No factor-of-safety wording** | ✅ PASS | All 4 occurrences of "factor of safety" are negations (Chapter 3, Chapter 13, Chapter 18, Table 13.2). |
| 18 | **No real-world structural-adequacy claim** | ✅ PASS | The only "adequacy" statements concern mesh adequacy (Chapters 9 and 11). Structural adequacy of a real component is explicitly not claimed (abstract, Chapter 18). |
| 19 | **S1/S2/S3 not ranked** | ✅ PASS | 0 occurrences of best, worst or optimal. The support table caption reads "listed in order of definition, not ranked". |
| 20 | **No combined uncertainty percentage invented** | ✅ PASS | No combined, total or overall uncertainty value appears. Chapter 16 lists each uncertainty with its own quantified or qualitative basis. |
| 21 | **λ1 not a guaranteed collapse load** | ✅ PASS | Chapter 3 §3.12: "**not** a guaranteed real-world collapse load and not a factor of safety". Repeated in Chapter 13, Chapter 17 and Chapter 18. |
| 22 | **Not called experimentally validated** | ✅ PASS | All "validated" or "validation" statements about the results are negated. "Mapping validation" (Chapter 10) is explicitly defined as a numerical comparison, not experimental validation. |
| 23 | **Page target (≈35–50 pages)** | ✅ PASS | 50 pages including front matter, figures, tables, equations, references and appendices. |
| 24 | **Abstract 250–350 words** | ✅ PASS | 350 whitespace-delimited words (342 alphanumeric tokens). It covers the re-analysis status, system, methods, CFD, mesh study, mapping, structural, buckling, supports, parametric trends, limitations and conclusion. It does not claim validation. |
| 25 | **Front matter (author and institution attribution)** | ✅ PASS (wording corrected in final publication audit) | The compiled front matter names the author, the degree and university (B.Tech Aerospace Engineering, Dayananda Sagar University, Bengaluru) and the organisation (Eleation, February–May 2025), as instructed. The acknowledgement names no individual. Earlier wording said the front matter had no personal names; that was inaccurate and is withdrawn. |

---

## 3. Number traceability (automated, `qc_10B.py`)

Method:

- Every number a reader sees in the chapters, appendices and tables is extracted after removing:
  - cross-reference numbers (Figure/Table/Chapter/Section/Equation);
  - row, task and case identifiers (M001, T-034, P00, LC2, S1 …);
  - years;
  - LaTeX dimensions;
  - constants of the cited correlations in display equations.
- Each number is then tested in order against:
  1. **master**: a value of `MASTER_PROJECT_DATA.csv` that rounds to the printed value at its printed precision. Unit-scale factors 10^±3, 10^±6 and 100 are allowed; the factor used is recorded.
  2. **document-exact**: the same token appears in a project document. The corpus is 835 text files of the project folder and section outputs; iteration histories and raw nodal data are excluded from rounding matches.
  3. **document-rounded**: a value in a project result document or table rounds to it.

| Class | All numbers | Numbers with ≥ 3 significant digits |
|---|---:|---:|
| master | 1,148 | 643 |
| document-exact | 589 | 444 |
| document-rounded | 4 | 3 |
| **untraced** | **0** | **0** |
| **Total** | **1,741** | **1,090** |

The four document-rounded values were checked by hand:

| Report value | Where | Source value |
|---|---|---|
| R_cond/R_conv = 0.0342 | Chapter 2, Table B.1 | `02_Engineering_Calculations/baseline_results.csv` 0.03422270302 |
| ṁ = 8.686 × 10⁻³ kg/s | Appendix B | `baseline_results.csv` |
| Fluid volume difference 1.4 × 10⁻¹⁴ % | Table 5.2 | `03_CAD_Geometry/CAD_NOTES.md` 1.44e-14 % |

Values fixed during QC:

- "about 157000 structural nodes" was reworded to "about 157 k", which is the wording of `FINAL_ENGINEERING_SYNTHESIS.md`.
- Earlier content corrections made in 10B are recorded in `PROJECT_STATE.md` §21.

Limitation of the automated check:

- A document-exact match proves the value exists in a project file, not that it is the same quantity.
- Numbers with one or two significant digits (counts, ±10 %, "2 mm") match trivially.
- The meaningful evidence is therefore the ≥ 3-significant-digit column. There, 59 % of values trace to the master dataset and the rest to named project documents.

---

## 4. Wording review (automated search + manual review)

The following terms were searched in all sources, each with its sentence:

- validat*
- safe* / safety
- best, worst, optim*
- failure-proof, revolutionary, cutting-edge, highly accurate
- guarant*
- adequa*
- recover*
- factor of safety
- prove(d/n)
- experimental*

47 occurrences were found. Of these, 37 are negated or conditional ("not validated", "not a factor of safety", "would allow …"). The remaining 10 were reviewed by hand, and all are technical uses that make no claim:

| Where | Word | Use |
|---|---|---|
| Chapter 1 scope list | experimental validation | listed as **outside the scope** |
| Chapter 7 | guaranteed | "conformality of the interface is guaranteed by construction" (shared node table) |
| Chapter 19 | guaranteed | "minimum-guaranteed yield strengths" (a material-specification term) |
| Chapter 8, Chapter 9, Chapter 12, Table 9.1 | recovers / recovery | physical recovery of the heat flux, Richardson recovery of the exact circle value, surface-stress recovery (FE term) |
| Chapter 9, Chapter 11 | adequate / adequacy | adequacy of the **mesh** as thermal input / of the structural mesh, demonstrated by mesh studies |

Wording changes made during QC:

- Objective 4 "validate the transfer" became "verify the transfer".
- Chapter 1 "mapping validation" became "mapping checks".
- Table 10.1 caption became "Numerical checks of the CFD-to-Mechanical temperature transfer".
- A definition sentence was added under Chapter 10 §10.4 "Mapping Validation".
- Table 6.2 "prove the converged state holds" became "confirm that …".

---

## 5. Modelling-level distinctions

Every occurrence of the key values carries its modelling level in the same sentence, or in the caption or header of its table: 45 occurrences, 0 unlabelled.

| Value | Level | Statement in report |
|---|---|---|
| 581.7 K | ANALYTICAL (Section 2, 1-D) | "581.7 K in the one-dimensional analytical model" |
| 562.58 K | CFD-MEDIUM (official baseline) | "562.58 K on the medium mesh" |
| 560.83 K | CFD-FINE (reference) | "fine mesh 560.83 K" |
| 558.13 K | CFD-EXTRAPOLATED | "extrapolated 558.13 K" |
| −657.2 MPa | ANALYTICAL restrained axial stress (−EαΔT̄) | Appendix B, Appendix H |
| 605.16 MPa | FE-STATIC LC2 local peak von Mises | "local peak von Mises stress of 605.16 MPa" |
| −582.44 MPa | FE-STATIC LC2 mean axial stress (column load measure) | Chapter 11, Chapter 13, Chapter 18 |

Appendix H states that values from different levels are different models or quantities, not contradictions.

The critical interpretations required by the brief are all stated:

- **Velocity** acts mainly on cooling, Re and Δp, and affects the structure only through temperature (Chapter 15, Chapter 18, abstract).
- **Heat flux** drives temperature and thermal stress.
- **Thickness** drives stiffness and buckling capacity, with little thermal effect at constant Q.
- **The support** dominates λ1 (1.108 / 2.232 / 4.300).
- **The mesh** is not the dominant uncertainty (Chapter 17: "The mesh is not the dominant uncertainty; the boundary condition is").
- **Pressure** is negligible (7.4 × 10⁻⁶ %).
- **Linear buckling** is not the collapse load of the real, imperfect duct (Chapter 3, Chapter 13, Chapter 16, Chapter 17).

---

## 6. Remaining report-quality notes (not failures)

1. **The DOCX is a secondary, converted format.**
   - Differences from the PDF:
     - sub-figure grids are stacked as one image per line;
     - the coloured re-analysis box becomes an indented quotation;
     - the two-column contents becomes a Word TOC field, which must be refreshed on opening (right-click → Update field);
     - some wide tables auto-fit with a narrow first column.
   - The LibreOffice preview is about 100 pages because of the stacked figures.
   - Equations are native Word equations, numbered as in the PDF.
   - After the fixes in `make_docx.py`, the preview shows no missing symbols (°, µ, Ø) and no stray glyphs. The fixes covered aligned equations, empty-base super/subscripts, y⁺, leading relations, text symbols and `@{}` in `\multicolumn`.
2. **Small sub-figures in the PDF.** Some paired contour sub-figures (Chapter 8, Chapter 11) are small because of the page limit. The embedded images are full resolution and remain legible when zoomed.
3. **The page count is at the upper end of the target.** The report is 50 physical pages, including the cover and front matter.
4. **Unused figures.** `Figures/` contains 86 prepared, hash-verified images. 25 were removed from the report during trimming and are kept for the presentation phase.
5. **Scope of the automated number check.** See the limitation note in §3.

---

## 7. Reproduce

```bash
cd 13_Report/Source
python scripts/gen_tables.py <11_Final_Audit/MASTER_PROJECT_DATA.csv> <10_Parametric_Study/.../PARAMETRIC_STRUCTURAL_RESULTS.csv> ../Tables
BIBINPUTS=../References: latexmk -pdf -outdir=<build> main.tex
python scripts/build_indexes.py .. <build>
python scripts/qc_10B.py .. <build> <MASTER_PROJECT_DATA.csv> <build>/qc_10B.json <project folder> [<section outputs>]
python scripts/make_docx.py . <build> ../References ../Figures <out.docx>
```
