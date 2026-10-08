# Edit Audit — LS-DYNA Integration into the Existing Final Presentation (Section 13)

**Type of change:** controlled edit of the existing deck. No second presentation was created; the file name is unchanged.

**Deck:** `14_Presentation/Final/Flow_Behavior_Thermal_Effects_Multiphysics_Presentation.pptx`. It has 21 slides (previously 18), 16:9, with speaker notes on every slide.

**Audit date:** 2026-10-07.

**Framing**

- The new slides present the LS-DYNA work as an **additional analysis, a follow-on extension of the project**. Their footer reads "Additional LS-DYNA analysis (follow-on extension of the project)".
- The banner on slide 14 reads "An additional analysis, not part of the original internship work programme. The Mechanical result λ₁ = 1.108 remains the reference."
- No internship activity, supervisor, task, meeting, experimental result or company instruction involving LS-DYNA was added.

**Unchanged**

- Eleation, February–May 2025, the title slide, the existing footers and the internship context.
- "2026": 0 occurrences before and after. "Re-analyse": 0 occurrences before and after.

---

## 1. Files modified

All 11 files are SHA-256-identical on the device after commit. The exception is that the three PNGs carry the transfer bridge's `caBX` metadata chunk; their IDAT data and decoded pixels are identical.

| File (under `14_Presentation/`) | Status | SHA-256 before (prefix) | SHA-256 after (final) |
|---|---|---|---|
| `Final/Flow_Behavior_Thermal_Effects_Multiphysics_Presentation.pptx` | changed | `02EAB433F600` | `C9ED0C49FC7EAAB61E338FB799654AC4358611FE111371BAEBDB36837ADA5D70` |
| `Speaker_Notes/SPEAKER_NOTES.md` | re-exported | `C25C23152C13` | `4938794E8785F48BD69D1E4DEEB079BD160D13399109B3DB724B9011610DAAFA` |
| `Source/build_deck.js` | changed (3 slide blocks; `newSlide` footer parameter; slide-17 strings) | `11D52A869BC8` | `3493B35D6687CE8FA181ECA1A49EB3E067C22443BA602DE3ACA84D914AA18A5F` |
| `Source/notes.js` | changed (notes 13a–13c; one sentence in note 17) | `59D48BE8E209` | `E7919BD1F3790BEE4060903527FC07340C17C3876827B07744C2F66B3EA6032D` |
| `Source/scripts/export_notes.py` | changed (slide count and last-slide index no longer hard-coded to 18) | `AEA2F238E58F` | `96E8F5E583351615A5A5220428BEAA2A83A7A8AC7119384EC25816A9F29C8E61` |
| `Source/scripts/section13_edit_deck.py` | **new** (merge into the existing package) | — | `03A5E954C344325CDF0106600637A53E0209D168C0706768A60088AB2C0C0E87` |
| `Source/scripts/section13_deck_edits_log.json` | **new** (3 inserted slides, 9 text edits) | — | `9A2CBAA2EA83D9D6C7C846938D241978BEFE97136AC276404D5C16F5A168D895` |
| `Figures/LSD_deformed_shape_C5_nt.png` | **new** | — | `29586E0B433734A856BBA3F5135E72A5058CFBDDFC69329A76E44C2F74E99898` |
| `Figures/LSD_load_lateral_nt.png` | **new** | — | `2215AC37CF6B1320FC56C6452CAA196A0FA42D9510C1AAFF931616B497FD1758` |
| `Figures/LSD_mechanical_vs_nonlinear_nt.png` | **new** | — | `541BC20463BBBB088EF1CD04FA6C67427C76A6575664B36FD804914867EA5B87` |
| `Figures/figure_manifest.json` | changed (3 entries; 18 total) | `904743463F65` | `09513B3DD2B893D9EFAF7679EFEC0EA0095FE4D2E9D49F4721553BFEFECD66C8` |

**Method.** The edit was made inside the existing pptx package.

- **Existing parts.** Of the 158 existing package parts, 148 are byte-identical. The 10 that changed are:
  - `slide17.xml`: three text runs;
  - `notesSlide17.xml`: one sentence;
  - `slide14`–`slide18.xml`: the cached text of the slide-number field only;
  - `presentation.xml`, its rels, `[Content_Types].xml` and `app.xml`: slide list and slide count.
- **New slides.** The three slides come from a full rebuild with the updated `build_deck.js`. They were copied in as `slide19`–`slide21.xml`, with their notes and the images `image-19-1`, `image-20-1` and `image-21-1.png`, and inserted after slide 13 (Support Sensitivity).
- **Check.** The merged deck's text equals the full rebuild.

## 2. Slides changed

| Slide (new number) | Previously | Change |
|---|---|---|
| 1–13 | 1–13 | none (byte-identical parts) |
| **14 LS-DYNA Nonlinear Buckling Extension** | — | **new** |
| **15 Imperfection Sensitivity** | — | **new** |
| **16 Mechanical vs LS-DYNA Buckling** | — | **new** |
| 17–19 (Parametric Study, Parametric Results, Key Engineering Findings) | 14–16 | moved; cached slide-number text only |
| **20 Limitations and Future Work** | 17 | "No geometric imperfections" → "No measured geometric imperfections"; "No nonlinear (post-)buckling analysis" → "Nonlinear buckling: elastic LS-DYNA extension only"; future item 3 description → "elastic–plastic, with tolerance-based imperfections"; note: one sentence added ("The additional LS-DYNA extension covers only the elastic, geometrically nonlinear part, with numerical imperfections.") |
| 21 Conclusion / Questions | 18 | moved; cached slide-number text only |

**Text check, old vs new (python-pptx).**

- Old slides 1–13 are identical to new slides 1–13.
- The only other differences are on old slides 14–18 (now 17–21): the slide-number field (14/15/16 → 17/18/19 etc.) and the slide-20 wording above.
- No other number on an existing slide changed.

## 3. New LS-DYNA content

| Slide | Content |
|---|---|
| 14 | "What was added": same LC2 model (mapped Fluent field, S1 supports, 108,252-node mesh); LS-DYNA verified first (605.160 vs 605.161 MPa; λ₁ = 1.1095, +0.13 %); geometrically nonlinear, elastic temperature-dependent material; λ up to 1.3; mode-1 imperfection 0.1 / 0.6 / 1.2 mm as numerical sensitivity values plus a perfect reference. Image: C5 deformed shape (12C F5). Case card: C1 / C3 / C5 + C0, all runs terminated normally. Banner: additional analysis; Mechanical λ₁ = 1.108 remains the reference |
| 15 | Image: load vs lateral end sway and normalised curves (12C F3). "At a glance" table: 1 % drop λ, N at λ = 1, VM at λ = 1, yield λ for C1 / C3 / C5. Takeaways: earlier departure with larger amplitude (1.070 → 0.825 → 0.375); at λ = 1 lower N (552.2 → 503.5 kN) and higher stress (690 → 1104 MPa); the normalised curves collapse onto one curve (single global mode) |
| 16 | Image: Mechanical vs nonlinear bar chart (12C F7). Stats: Southwell 607.7–612.3 kN (−0.1 % to +0.7 % of P_cr); Mechanical P_cr 608.25 kN (λ₁ = 1.108, linear, perfect elastic tube); maximum load 601.0 kN for the 0.1 mm case at λ = 1.185, with C3 and C5 still rising at λ = 1.3. Banner: "Elastic model only: first local yield at λ = 0.974–1.109, so the later curves lie outside the elastic range. The perfect-geometry run gives no bifurcation load. Not a factor of safety, not experimental validation." |

The images are the actual 12C plots. Only the title strip was cropped, the same files as report Figures 14.3–14.5. Each picture has alt text.

**Speaker notes (slides 14–16)**

| Slide | Planned time | Words | Covers |
|---|---|---|---|
| 14 | 55 s | 164 | why LS-DYNA (λ₁ is for a perfectly straight elastic tube; add geometric nonlinearity with an initial out-of-straightness); follow-on extension, not internship work; 12B verification; the three cases as sensitivity values |
| 15 | 55 s | 130 | onset λ, N and stress at λ = 1 for the three cases; single global mode |
| 16 | 60 s | 191 | 607.7–612.3 kN vs 608.25 kN; the characteristic load is insensitive while deformation and stress are imperfection-sensitive; "not a factor of safety, and it is not experimental validation"; the elastic limitation (no defensible plastic curve for Inconel 718; yield at λ 1.109 / 1.031 / 0.974, C5 before λ = 1; later curves outside the elastic range, not a collapse prediction); C0 gives no bifurcation load, so the Mechanical eigenvalue stays the reference |

`SPEAKER_NOTES.md` was re-exported from the deck: **21 slides, all with notes, 1,050 s (17.5 min), 2,869 words.** Before the edit it was 18 slides and 880 s.

## 4. Numbers added and their sources

The number trace (`trace_numbers.py`) covers slide text, tables and notes of slides 14–16. **105 numbers were found and all are traced**, except the slide-number field "15", which is structural.

| Values on the slides / in the notes | Quantity | Source (exact value) |
|---|---|---|
| 0.1 / 0.6 / 1.2 mm | imperfection amplitude C1 / C3 / C5 | `15_LS_DYNA_Extension/12C_Nonlinear_Buckling/FINAL_12C_RESULTS.md` §1–2 |
| 1.070 / 0.825 / 0.375 | λ at onset (N 1 % below the perfect path) | `IMPERFECTION_SENSITIVITY.csv`, `FINAL_12C_RESULTS.md` |
| 552.2 / 531.2 / 503.5 kN | N at λ = 1 | same (552.17 / 531.19 / 503.46) |
| 690 / 966 / 1104 MPa | peak von Mises at λ = 1 | same (689.7 / 966.3 / 1103.7) |
| 1.109 / 1.031 / 0.974; "0.974–1.109" | λ at first local yield (VM / S_y(T) = 1) | same (1.1093 / 1.0315 / 0.9738) |
| 601.0 kN at λ 1.185 | C1 maximum attained N | same (600.997 kN) |
| "still rising at λ = 1.3" | C3 / C5 maximum N (572.4 / 545.3 kN in the chart) | same (572.410 / 545.318) |
| 607.7–612.3 kN | Southwell characteristic load range | same (607.66 / 611.06 / 612.32) |
| −0.1 % to +0.7 % | Southwell vs P_cr | `MECHANICAL_vs_LSDYNA.csv` (−0.10 / +0.46 / +0.67 %) |
| 605.160 vs 605.161 MPa; 1.1095; +0.13 % | 12B verification (G5, G6) | `LS_DYNA_FINAL_ENGINEERING_SYNTHESIS.md` §2; `LS_DYNA_GATE_STATUS_12B.md` |
| 108,252 nodes; λ ≤ 1.3; λ 1.0–1.2 fine steps; λ = 1.15–1.30 | model and load schedule | `FINAL_12C_RESULTS.md` §1 |
| λ₁ = 1.108; P_cr = 608.25 kN | Mechanical reference (unchanged) | `11_Final_Audit/MASTER_PROJECT_DATA.csv` M098 (1.10805), M099 (608.25 kN) |
| chart: 608 / 609 / 601 / 572 / 545 kN bars; 612 / 611 / 608 kN markers | 12C F7 plot | `analysis_12C.json` = the 12C CSVs (checked) |

**Unchanged values.** No existing CFD or Mechanical value changed. The baseline CFD, mesh study, mapping, LC1, LC2, λ₁ = 1.108, support sensitivity and the parametric charts and tables on slides 1–13 and 17–21 are untouched: their XML parts and the native chart data are byte-identical. λ₁ is nowhere called a factor of safety.

**Protected files.** The protected project files were device-checked after commit and are unchanged:

| File | SHA-256 (prefix) |
|---|---|
| `MASTER_PROJECT_DATA.csv` | `727ADD0A…` |
| Fluent case / data | `84D6511B…` / `F05837C5…` |
| LC2 deck | `51D80678…` |
| `s7b_nodal.csv` | `DC650A0C…` |
| `s8a_mode1.csv` | `A5FDC844…` |
| `BUCKLING_RESULTS.md` | `5BABD2DC…` |

## 5. Final hashes (SHA-256)

| File | Before Section 13 | Final |
|---|---|---|
| Presentation PPTX | `02EAB433F6004679345D1BCFC60D38603601EEA63E937040449FC27540CA7157` | `C9ED0C49FC7EAAB61E338FB799654AC4358611FE111371BAEBDB36837ADA5D70` |
| SPEAKER_NOTES.md | `C25C23152C1381F8228DFFC1937EC4B75D15D8AF18C9833673DD7C32A6D31765` | `4938794E8785F48BD69D1E4DEEB079BD160D13399109B3DB724B9011610DAAFA` |

The final PPTX hash was verified on the device after commit and is identical to the cloud build.

## 6. Visual QC, notes and links

| Check | Status |
|---|---|
| Rendering | **PASS.** All 21 slides were rendered (LibreOffice) and inspected: no clipped text, no overflow and no overlap on the new slides or on slide 20. The existing style is kept: title band, cards, stat blocks and caption style. Font sizes on slides 14–16: body text 14–16 pt; table text 11.5–12 pt; captions and stat sub-lines 11 pt; footer 9 pt. These match the 10C-1 limits (≥ 10 pt, footer 9 pt) |
| Bounds | 0 shapes outside the slide on any of the 21 slides (python-pptx) |
| Package | Office XML validator: PASS |
| Speaker notes | present on all 21 slides; slides 14–16 cover every required point (§3) |
| Slide numbers | slide-number fields recompute in PowerPoint; the cached values were also updated to 17–21 on the moved slides |
| Hyperlinks | the deck has no hyperlinks (0 before and after) |
| References | the deck cites no references; none added |

---

*Section 13 presentation edit complete. The final documents were not modified after this hash audit.*
