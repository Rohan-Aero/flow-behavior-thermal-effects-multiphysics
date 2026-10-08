# Edit Audit — LS-DYNA Integration into the Existing Final Report (Section 13)

**Type of change:** controlled edit of the existing report. No second report was created; the file names are unchanged.
**Report:** `13_Report/Final_Report/Flow_Behavior_Thermal_Effects_Multiphysics_Internship_Report.pdf` (master) and `.docx` (secondary conversion), both rebuilt from the edited LaTeX source with the unchanged 10B tool chain.
**Audit date:** 2026-10-07.

**Framing:**

- The LS-DYNA work is described as an **"Additional Nonlinear Buckling Analysis Using ANSYS LS-DYNA"**, carried out as a follow-on extension of the thermo-structural analysis.
- The new section states that it "is not part of the internship work programme described in Chapter 1 and does not change any result of the preceding chapters".
- No internship activity, supervisor, task, meeting, experimental result or company instruction involving LS-DYNA was added.

**Unchanged:**

- the title, the cover and its identity, Eleation, the internship period February–May 2025, and the certificate-based Internship Information table;
- the word "re-analysed" was not reintroduced (the three "re-analysis" occurrences before and after are Fluent's technical node-reconstruction term);
- no new "2026" was added (5 occurrences before and after, all solver-version information).

---

## 1. Files modified

The device copies match the cloud build: all 24 files are SHA-256-identical on the device, except that the four PNGs carry the transfer bridge's `caBX` metadata chunk. Their IDAT image data and decoded pixels are identical.

In the table, the "SHA-256 before" column shows the first 12 characters; the "SHA-256 after" column is the full final hash.

| File (under `13_Report/`) | Status | SHA-256 before | SHA-256 after (final) |
|---|---|---|---|
| `Final_Report/Flow_Behavior_Thermal_Effects_Multiphysics_Internship_Report.pdf` | changed | `7F8F32ADB39C` | `57CF71DC3F272F9AB827621E9909E5FF81CB4E0C7B25F92A9FBD39FFA542D7AD` |
| `Final_Report/Flow_Behavior_Thermal_Effects_Multiphysics_Internship_Report.docx` | changed | `2D40820C27BD` | `C38A55AB00525A6D1DAB5CD0BD763D7634C947ECD707A51D484D0F8110D80395` |
| `Final_Report/FIGURE_INDEX.md` | changed (regenerated) | `B7BE6213CB24` | `9C4A20872E8E43A415C4DED71E70474BAC202070F2093EC9358B041277486A6C` |
| `Final_Report/TABLE_INDEX.md` | changed (regenerated) | `8CAB2DBA5C26` | `AD203A76D810874A6B6DA41C01EAE0C46A9D423E78925CC58BE6F337BD3D2D1A` |
| `Source/main.tex` | changed (one `\input` line) | `AF7E4BE40B4C` | `30CCB62DD351F2D5FAFA4F9872113DE9BD1866226CDB79274B854489F12B3949` |
| `Source/chapters/ch14b_lsdyna.tex` | **new** (§14.7) | — | `7020EC1234606072EA29C9F59D3163941E44216BCB6E4A28E38235409A16E9B6` |
| `Source/chapters/frontmatter.tex` | changed (abstract) | `B6489B17B7D4` | `1F3646B8EF1E13A46F02B9C8FE3667C656F5B7257781770D1D93465C2AF23AD7` |
| `Source/chapters/ch01_introduction.tex` | changed | `0C119B2237BB` | `185E4D67CDCBE44B280887E813073107B574C792FC2ABC9AE5B817F56D1A1CC1` |
| `Source/chapters/ch13_buckling.tex` | changed | `3098161C5E79` | `DF385823F73F7152C884696CC20F8CD68B623FC6F8DE1199C5331AB93792080A` |
| `Source/chapters/ch16_uncertainty.tex` | changed | `4E03A12BEE77` | `01BEBBDCF788A372888E0BA985542080B0324EE5D7C7C0778B9D6B3D8B368578` |
| `Source/chapters/ch17_discussion.tex` | changed | `99875644EE6C` | `A27EA22A1ED78C409E9F1EFD17DEF0B9C361FECED9820C92A9E17259331EB257` |
| `Source/chapters/ch18_conclusions.tex` | changed | `AEC4E17A2039` | `6F63F974ABD2BBC23EC2D6F8ABC0869EC76E2BBCB91FA113AC58DC5DBE75ADDE` |
| `Source/chapters/ch19_future.tex` | changed | `347BD5D379B7` | `2E1C9FF3F36DCC97ADD35736C991E9E67629FB38B5CE68EA38AB2EBF8D4D0940` |
| `Tables/tab_lsdyna.tex` | **new** (Table 14.2) | — | `DA9627673FEF9BB119ED310A780BE0CC67875D5EBF8C713EB7D3CDFB5196A819` |
| `Tables/tab_unc.tex` | changed (row 8 wording) | `9A75BA21633B` | `2A07DD820C1D208EF02B334B73A2AAD1A2963A3A7DC2F0D0CC428DC3F2CD212F` |
| `Tables/tables_index.tsv` | changed (one row added) | `5C4DE221A13E` | `11BE2651D63AB134E1392207C53185C88C96245017DC41C42ECBE1DF37429C77` |
| `Figures/LSD_load_lateral_nt.png` | **new** | — | `2215AC37CF6B1320FC56C6452CAA196A0FA42D9510C1AAFF931616B497FD1758` |
| `Figures/LSD_amplitude_vs_characteristic_load_nt.png` | **new** | — | `82C7C709A9E4C3C296BC1D491C9F7A294085E0872BE54E66F57A0057A2E52FE1` |
| `Figures/LSD_mechanical_vs_nonlinear_nt.png` | **new** | — | `541BC20463BBBB088EF1CD04FA6C67427C76A6575664B36FD804914867EA5B87` |
| `Figures/LSD_deformed_shape_C5_nt.png` | **new** | — | `29586E0B433734A856BBA3F5135E72A5058CFBDDFC69329A76E44C2F74E99898` |
| `Figures/figure_sources.json` | changed (4 entries added; 90 total) | `B37153DE039C` | `F0FD2C7042A25EC8D32659A14E4D41741CEFA743DB71A18B8ED76EADE6AC7BCD` |
| `Source/scripts/build_indexes.py` | changed (provenance label `lsdyna_plot`) | `7053DE940987` | `F319370707C1167EED3A4FF1F18D7D0EE0B2D0A510DC69028E34B23B0A10A242` |
| `Source/scripts/section13_edit_report.py` | **new** (exact-once text edits) | — | `4CF363395FB48B0298C0D9FD0E6E3C54556836D754693DCDF03BB90756359A3E` |
| `Source/scripts/section13_report_edits_log.json` | **new** (log of the 12 edits) | — | `BE7D26E515891EEC2314265783AB1397388B027A09FA18D43E87B56C98E74C35` |

Every other file in `13_Report` is unchanged, including `References/refs.bib` and the Appendices. A device scan found exactly 35 files newer than the end of 12C in `13_Report` and `14_Presentation`, and they are the committed files.

## 2. Pages changed (final PDF: 55 pages, previously 50)

The final PDF has a cover, front matter i–vii and 47 numbered pages. Before the edit it had front matter i–vi and 43 numbered pages.

| Physical page | Printed page | Change |
|---|---|---|
| 3 | ii | Abstract: one sentence on the additional LS-DYNA analysis. "geometric imperfections" became "measured geometric imperfections" in the open-uncertainty sentence. The abstract still fits its page |
| 5–7 | iv–vi | Contents and lists of figures and tables: automatic entries for §14.7, Table 14.2 and Figures 14.3–14.5. The abbreviations list moved to page vii |
| 9 | 1 | Ch. 1 scope: one sentence pointing to §14.7 ("does not change the scope or the results of the main study") |
| 39 | 31 | Ch. 13 limitations: one sentence ("an elastic, geometrically nonlinear imperfection-sensitivity extension is reported in Section 14.7; it does not determine a collapse load") |
| **41–44** | **33–36** | **New §14.7 "Additional Nonlinear Buckling Analysis Using ANSYS LS-DYNA"** (after support sensitivity §14.6, before Chapter 15), with Table 14.2 and Figures 14.3, 14.4 and 14.5 |
| 47 | 39 | Uncertainty register (Table 16.1), row 8 "Geometric imperfection": "not modelled in the Mechanical study (numerical amplitudes only in the additional elastic LS-DYNA analysis, Section 14.7)" |
| 48 | 40 | Ch. 16 Geometric Imperfections: one sentence appended |
| 49 | 41 | Ch. 17 Buckling Behaviour: one sentence appended ("Southwell characteristic-load estimates stay within 1 % of the linear critical load") |
| 51 | 43 | Ch. 18: new conclusion item "Additional nonlinear LS-DYNA analysis (extension)"; the Limitations item made precise. Ch. 19: intro note and item 3 sentence ("addressed in part by the additional elastic LS-DYNA analysis") |
| 45–55 | 37–47 | Repaginated only (+4 printed pages); no content change |

## 3. New LS-DYNA content (§14.7, ≈ 3.5 pages)

| Subsection | Content |
|---|---|
| Introduction | Additional analysis, follow-on extension; not part of the internship work programme; changes no earlier result |
| 14.7.1 Purpose and Model | Why: λ₁ is for a perfectly straight elastic tube; LS-DYNA adds geometric nonlinearity with a seeded imperfection. Same LC2 model: 108,252 nodes / 23,400 twenty-node elements, mapped Fluent temperature field (T_ref 300 K), S1 supports, temperature-dependent elastic Inconel 718. 12B verification: peak VM 605.160 vs 605.161 MPa; linear λ₁ 1.1095 (+0.13 %, −0.64 % after the large-deformation correction); mode correlation 0.9999998. Load: temperature rise scaled by λ up to 1.3 (Δλ = 0.005 for λ 1.0–1.2). Imperfection: mode 1 with amplitudes 0.1 / 0.6 / 1.2 mm (C1 / C3 / C5), numerical sensitivity values; perfect reference C0; all four runs terminated normally |
| 14.7.2 Results | Onset λ, N, VM and lateral translation at λ = 1, maximum attained N and Southwell estimates; **Table 14.2**; **Figure 14.3** (load path) |
| 14.7.3 Comparison with the Mechanical Linear Buckling Result | Southwell 607.7–612.3 kN vs P_cr 608.25 kN (λ₁ = 1.108): −0.1 % to +0.7 %. Maximum attained N = 98.8 / 94.1 / 89.7 % of P_cr. The characteristic global buckling load is relatively insensitive to the tested amplitudes, while the onset of lateral deformation, and the deflection and stress at a given load, are strongly imperfection-sensitive. C0 stays straight to 720.7 kN at λ = 1.3, and the solver ignores negative eigenvalues by default, so the perfect-geometry bifurcation load is **not identifiable**; the Mechanical eigenvalue is the perfect-geometry reference. Mode: global guided sway (mid-span lateral < 0.2 % of the end translation, ovalisation ≤ 0.041 mm, no local mode; highest stress at the outer edge of the inlet face). "None of these load values is a factor of safety or a real-world capacity, and the analysis is not an experimental validation." **Figure 14.4** (a, b) and **Figure 14.5** |
| 14.7.4 Limitations of the Elastic Model | No defensible temperature-dependent plastic stress–strain curve for Inconel 718 (T-036), so the model is elastic. Peak stress reaches the local yield estimate at λ = 1.109 / 1.031 / 0.974; C5 reaches it before λ = 1. The later parts of the curves are outside the validated elastic range: not elastic–plastic, not a post-yield collapse and not a collapse load. The Southwell comparison (pre-critical branches) is the meaningful result. Other limitations: numerical amplitudes, three amplitudes only, no mesh or step study, idealised S1 |

**Figures**

The figures are the actual 12C plots, without new curves. Only the plot title strip was cropped (Pillow), to remove the embedded "Fig. N" / "F5" titles. The crop is recorded in `figure_sources.json` with the source and output SHA-256.

| Report figure | 12C source plot (`15_LS_DYNA_Extension/12C_Nonlinear_Buckling/plots/`) | Rows cropped | Source SHA-256 | Output SHA-256 |
|---|---|---|---|---|
| 14.3 | F3 load vs lateral (+ normalised) | 50 | `6AB60A08…` | `2215AC37…` |
| 14.4 (a) | F7 Mechanical vs nonlinear | 49 | `5BFABFB5…` | `541BC204…` |
| 14.4 (b) | F4 amplitude vs characteristic load | 49 | `E02E3E40…` | `82C7C709…` |
| 14.5 | F5 deformed shape C5 | 50 | `11FA90FB…` | `29586E0B…` |

The plot data (`analysis_12C.json`) equal the 12C CSV deliverables. The F7 bars are 608 / 609 / 601 / 572 / 545 kN, with Southwell markers 612 / 611 / 608 kN. The captions explain "8A" (Mechanical) and "12B G6" (LS-DYNA linear check).

## 4. Numbers added and their sources

The number trace (`trace_numbers.py`) covers all numbers in §14.7, Table 14.2 and the inserted cross-reference sentences:

- **126 numbers found; all traced**, except the LaTeX layout parameters 0.155 (column width) and 3.4 (pt column separation), which are not data;
- section, table and figure numbers are excluded as structural.

| Values in the report | Quantity | Source (exact value) |
|---|---|---|
| 0.1 / 0.6 / 1.2 mm | imperfection amplitude C1 / C3 / C5 | `12C_Nonlinear_Buckling/FINAL_12C_RESULTS.md` §1–2 |
| 1.070 / 0.825 / 0.375 | λ at onset (N 1 % below the perfect path) | `IMPERFECTION_SENSITIVITY.csv`, `FINAL_12C_RESULTS.md` |
| 552.2 / 531.2 / 503.5 kN | N at λ = 1 | same (552.17 / 531.19 / 503.46) |
| 690 / 966 / 1104 MPa | peak von Mises at λ = 1 | same (689.7 / 966.3 / 1103.7) |
| 1.109 / 1.031 / 0.974 | λ at VM / S_y(T) = 1 (first local yield) | same (1.1093 / 1.0315 / 0.9738) |
| 601.0 kN at λ 1.185 | C1 maximum attained N (interior maximum) | same (600.997 kN) |
| 572.4 / 545.3 kN at λ 1.3, rising | C3 / C5 maximum attained N | same (572.410 / 545.318) |
| 612.3 / 611.1 / 607.7 kN; range 607.7–612.3 | Southwell characteristic load | same (612.32 / 611.06 / 607.66) |
| +0.7 / +0.5 / −0.1 %; "−0.1 % to +0.7 %" | Southwell vs P_cr | `MECHANICAL_vs_LSDYNA.csv` (+0.67 / +0.46 / −0.10 %) |
| 98.8 / 94.1 / 89.7 % | maximum attained N / P_cr | `MECHANICAL_vs_LSDYNA.csv` (0.9881 / 0.9411 / 0.8965) |
| 0.85 / 3.71 / 5.32 mm | maximum lateral translation at λ = 1 | `FINAL_12C_RESULTS.md` §3 |
| 553.2 kN, 605.2 MPa, 720.7 kN at λ 1.3 | C0 reference: N and VM at λ = 1; N at λ = 1.3 | `FINAL_12C_RESULTS.md` §3 (553.25 / 605.2 / 720.69) |
| +0.79 % | C0 N(λ = 1) vs Mechanical 548.94 kN (large-deformation formulation) | `MECHANICAL_vs_LSDYNA.csv`; 12B D-105 |
| < 0.2 %; ≤ 0.041 mm | mid-span lateral / end translation; ovalisation | `FINAL_12C_RESULTS.md` §5 (0.13–0.18 %; 0.041 mm) |
| λ ≤ 1.3; Δλ 0.005 (λ 1.0–1.2); λ 1.15–1.30 | load schedule; deformed-shape states | `FINAL_12C_RESULTS.md` §1 |
| 108,252 nodes; 23,400 elements; 300 K | model; T_ref | `FINAL_12C_RESULTS.md` §1 (= 7A/7B model) |
| 605.160 vs 605.161 MPa; 1.1095; +0.13 %; −0.64 %; 0.9999998 | 12B verification (G5 static, G6 buckling, mode correlation) | `LS_DYNA_FINAL_ENGINEERING_SYNTHESIS.md` §2; `LS_DYNA_GATE_STATUS_12B.md` |
| λ₁ = 1.108; P_cr = 608.25 kN; N = 548.94 kN | Mechanical reference (unchanged) | `11_Final_Audit/MASTER_PROJECT_DATA.csv` M098 (1.10805), M099 (608.25 kN); LC2 end reaction 548.94 kN |

**Mechanical values re-checked in `MASTER_PROJECT_DATA.csv`:**

| Row | Quantity | Value |
|---|---|---|
| M098 | λ₁ | 1.10805 |
| M099 | P_cr | 608.25 kN |
| M090 | LC2 peak von Mises | 605.161 MPa |
| M093 | critical temperature | 437.99 K |
| M096 | first-yield factor | 1.730 |

No LS-DYNA value conflicts with an existing number. λ₁ is nowhere called a factor of safety.

## 5. Existing CFD and Mechanical results not altered

**Source-level evidence**

- Every edit outside the two new files was made by `section13_edit_report.py`, as an exact-once text replacement. The edits are logged with the old and new text in `section13_report_edits_log.json`, 12 entries (11 text edits and 1 table-index row).
- No existing sentence lost a number. The edits append sentences; the only rewording is the tab_unc row 8 and the Ch. 18 Limitations item, both qualitative.

**Rendered-text evidence**

- **PDF, old vs new:**
  - The only numeric tokens lost are page numbers 33–43, from the contents and list entries, which moved by +4 pages.
  - The only word lost is the roman page label "vi".
  - All baseline CFD, mesh-study, mapping, LC1, LC2, λ₁ = 1.108, support-sensitivity and parametric values are present with unchanged counts.
- **DOCX, old vs new:** 0 numbers lost and 0 words lost.

**Toolchain reproducibility (checked before editing)**

Rebuilding the unedited source reproduced the old PDF and DOCX text exactly: the diff was 0 lines for each.

**Protected project files**

A device SHA-256 check after commit found all of these unchanged:

| File | SHA-256 |
|---|---|
| `MASTER_PROJECT_DATA.csv` | `727ADD0A71BE…` |
| Fluent baseline case | `84D6511B66C3…` |
| Fluent baseline data | `F05837C5C27E…` |
| LC2 solver deck | `51D806783ABC…` |
| `s7b_nodal.csv` | `DC650A0C2532…` |
| `s8a_mode1.csv` | `A5FDC844DDDE…` |
| `BUCKLING_RESULTS.md` | `5BABD2DC6219…` |

**Other folders**

No file outside `13_Report` and `14_Presentation` changed after the 12C final hash audit (2026-10-07 19:38:19). The one exception is that audit's own output file, `changed_outside_12C.txt`, written in the same second. No LS-DYNA analysis was run.

## 6. Final hashes (SHA-256)

| File | Before Section 13 | Final |
|---|---|---|
| Report PDF | `7F8F32ADB39CD260A804CC0D42EB75915A5B37D6DD4D5197E856061584624494` | `57CF71DC3F272F9AB827621E9909E5FF81CB4E0C7B25F92A9FBD39FFA542D7AD` |
| Report DOCX | `2D40820C27BD55255021E0D576DBCA860AE41D9E178230D049322A1E1128CAD3` | `C38A55AB00525A6D1DAB5CD0BD763D7634C947ECD707A51D484D0F8110D80395` |

Both final hashes were verified on the device after commit and are identical to the cloud build.

## 7. Visual QC, references and links

| Check | Status |
|---|---|
| LaTeX build | 0 overfull boxes, 0 undefined references or citations. Table 14.2 fits the text width (tabcolsep 3.4 pt) |
| Rendered pages | **PASS.** Pages with new or changed content were rendered (pdftoppm) and inspected: no clipping, no overflow, no float collision. Figure 14.4 subfigures were stacked (0.78 / 0.62 linewidth) after a side-by-side version proved too small; the captions are readable |
| Cross-references | `sec:lsdyna` → 14.7 (p. 33); `tab:lsdyna` → Table 14.2 (p. 34); `fig:lsdpath` → 14.3 (p. 34); `fig:lsdcomp` / `fig:lsdshape` → 14.4 / 14.5 (p. 35). All seven inserted "Section 14.7" references resolve |
| Hyperlinks | 453 link annotations (previously 428). The +25 are internal hyperref links to the new section, table and figures. External URLs: 5 before and after |
| References | no citation added; `refs.bib` byte-identical |
| Indexes | `FIGURE_INDEX.md` (35 figures, 65 panels) and `TABLE_INDEX.md` (38 tables) regenerated |
| DOCX | secondary conversion (D-079), checked in a LibreOffice render. Table 14.2 header text is plain (no `\makecell`); its narrow columns wrap in Word. Refresh the Word TOC on opening, as before |

---

*Section 13 report edit complete. The final documents were not modified after this hash audit.*
