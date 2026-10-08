# FINAL ENGINEERING AUDIT — Section 10A (gatekeeping audit before any report)

> **RE-ANALYSIS 2026 — Re-analysed / Assumed / Simulated 2026.** The original Eleation internship files (Feb–May 2025) were lost.
> Every value audited here is a 2026 re-analysis: an input chosen in 2026, a 2026 hand calculation, or a 2026 ANSYS Student
> 2026 R1 simulation. No value is recovered internship data, and no experimental or measured data exist.

## 0. Verdict

| Item | Result |
|---|---|
| Master dataset | `MASTER_PROJECT_DATA.csv`: **182 rows**. 156 result values were checked by independent recomputation in 10A: **124 VERIFIED, 3 CROSS-CHECKED, 29 REPORTED, 0 MISMATCH**. The other rows are 20 re-analysed inputs, 2 model decisions and 4 interpretation rows |
| File integrity | every earlier hash record matches (1,927 / 1,927 files of `08_Structural_Analysis`; baseline CFD case/data; 7B project 58 / 58). The only changed file is the living `PROJECT_STATE.md` (`FILE_INTEGRITY_AUDIT.md`) |
| Cross-document numbers | 884 occurrences of the 19 key numbers reviewed: **no value conflict and no mislabelled modelling level** (`MASTER_TRACEABILITY.md` §2) |
| Documentation inconsistencies | 15 found (§7): stale status records, superseded Section 1 assumptions, wording that needs care. No computed result is wrong |
| Corrections made | root `README.md` status block; `Claude outputs` not-authoritative note; final assumption, requirement and uncertainty status recorded in `11_Final_Audit`; `PROJECT_STATE.md` §20. No earlier deliverable was deleted or rewritten |
| Findings A–L of the brief | **all 12 supported by the evidence**, 5 of them with a stated qualification (§8) |
| New simulations | none. No integrity problem required one |
| Independent verification | `Scripts/verify_10A.py` on the device: **11 / 11 PASS** (§17) |

## 1. How the audit was done

1. **Raw-file recomputation** (`Scripts/master_data_10A.py`, run with the ANSYS-bundled CPython on the device). The script was written for 10A and imports no earlier post-processing script. From the rawest files it reads:
   - Fluent flux and surface-integral report text files;
   - MAPDL nodal (`s7b_nodal.csv`), reaction (`s7b_react.csv`) and load-factor (`s8a_load_factors.csv`) tables, with corner nodes taken from each solver input's EBLOCK;
   - the CAD measurement file;
   - the solver inputs (TREF, EBLOCK counts).

   Each value is compared with the one documented in the section result file. Section 2 and 6B derived values are marked REPORTED with the reason.
2. **Cross-document search** (`Scripts/crossdoc_10A.py`). Every occurrence of the brief's 19 numbers, with their usual roundings, in 181 documents and summary tables. Each occurrence was classified by modelling level.
3. **Wording scan** (`Scripts/wording_10A.py`). Every use in the `.md` documents of "safe", "safety", "margin", "best", "worst", "optimal", "recovered", "measured", "experimental" and "original internship", checked for correct qualification.
4. **Integrity** (`Scripts/manifest_10A.py`, `Scripts/integrity_10A.py`). A full SHA-256 manifest of 4,856 files, compared with all 13 earlier hash records.
5. **Document review.** Each master document listed below was checked for its headline values against the recomputed data, and for statements that later sections superseded. Documents written in the same phase share one generator (build script) with the data, so their tables were checked through the generator's data files.

| Document (brief name) | File | Check |
|---|---|---|
| PROJECT_STATE | `PROJECT_STATE.md` | header, §§2–19 headline values; stale parts listed in §7 |
| PROJECT_CONCEPT, PARAMETERS, ASSUMPTIONS | `01_Requirements/PROJECT_CONCEPT.md`, `PARAMETERS.xlsx`, `ASSUMPTIONS.md` | historical facts; assumption status (→ `MASTER_ASSUMPTIONS.md`) |
| ENGINEERING_THEORY / CALCULATIONS / EXPECTED_RESULTS | `02_Engineering_Calculations/*.md`, `baseline_results.csv` | analytical values kept as the ANALYTICAL level; expected bands vs final results (§10) |
| CAD_NOTES | `03_CAD_Geometry/CAD_NOTES.md` | geometry recomputed from `cad_measurements.json` (M023–M031) |
| MESH_NOTES, MESH_QUALITY_TABLE | `05_Meshing/MESH_NOTES.md`, `Mesh_Quality/MESH_QUALITY_TABLE.md` | cells (M033), quality limits (NR-05) |
| CFD_BASELINE_RESULTS / AUDIT | `06_Fluent_CFD/Baseline/*.md` | every baseline CFD value re-read from the Fluent reports (M034–M049) |
| MESH_INDEPENDENCE_REPORT | `09_Mesh_Independence/Mesh_Independence_Report.md` | fine and coarse values from their Fluent reports (M050–M065); GCI values REPORTED (M066–M070) |
| STRUCTURAL_RESULTS / AUDIT | `08_Structural_Analysis/STRUCTURAL_RESULTS.md`, `STRUCTURAL_AUDIT.md` | all LC1 / LC2 / LC2P values recomputed from the MAPDL tables (M081–M097) |
| BUCKLING_RESULTS / AUDIT | `08_Structural_Analysis/Buckling/*.md` | λ₁, P_cr for S1 / S2 recomputed (M098–M103) |
| STRUCTURAL_ / BUCKLING_MESH_COMPARISON | `08_Structural_Analysis/Mesh_Study/*.md` | LC2 peak and λ₁ of all 8B variants recomputed (M111–M124) |
| PARAMETRIC_PLAN, CASE_MATRIX | `10_Parametric_Study/Planning/PARAMETRIC_PLAN.md`, `Case_Matrix/PARAMETRIC_CASE_MATRIX.csv` | screening marked as estimates; superseded by FE (L-12) |
| PARAMETRIC_CFD_TABLE | `10_Parametric_Study/CFD_Results/PARAMETRIC_CFD_TABLE.md` | Δp, T_out, T_max re-read from each case's Fluent reports |
| PARAMETRIC_STRUCTURAL_RESULTS, SUPPORT_SENSITIVITY_RESULTS, FINAL_PARAMETRIC_AUDIT | `10_Parametric_Study/Results/*` | all parametric FE values and S2 / S3 recomputed (M108–M110, parametric rows) |

**One difference was found and resolved by definition, not by changing a number.** The first recomputation of the LC1 free growth used a plain node mean over the end faces and gave 1.84057 mm against the documented 1.8409 mm. The documented value is the **area-weighted** face mean; recomputed that way it is 1.84086 mm (VERIFIED, M085).

## 2. Official baseline definition (the only one to be used)

| Item | Definition |
|---|---|
| Geometry | D_i 20 mm, D_o 40 mm, L 600 mm, t 10 mm; D_h 20 mm; fluid area 314.159 mm²; solid volume 5.654867 × 10⁻⁴ m³; heated area 0.0753982 m² (true cylinder), 0.0753444 m² (CFD 48-facet mesh) |
| Fluid | air, incompressible ideal gas; T_in 300 K; V_in 23.5 m/s; outlet 0 Pa gauge at an operating pressure of 101,325 Pa |
| Thermal | q″ = 8000 W/m² on the outer wall; end faces adiabatic |
| Solid | Inconel 718 (VDM 4127 / Special Metals datasheet properties) |
| CFD | **medium mesh, 159,840 cells** (the official baseline); the fine mesh (500,580 cells) is the verification reference only |
| Structural | mapped medium CFD field; mesh B, **108,252 nodes / 23,400 SOLID186 quadratic hexahedra**; E(T), secant α(T); ν = 0.294 [ASSUMED]; T_ref = 300 K |
| Support | **S1 = the LC2 support** (both end faces U_z = 0, 3 mid-span hoop nodes; ends free to sway, end rotation held) |

**Consistency check.** Every section document from 7A onwards states this baseline; no document calls the fine mesh the
baseline. Differences exist only in documents written before a later decision, and those are historical by construction:

- the Section 3 planning figure of ≈ 48,000 solid nodes (L-13);
- the Section 1 / 2 constant-property material values (L-03, L-14).

## 3. CFD final reference

| Check | Result |
|---|---|
| Medium convergence | converged at iteration 600 and confirmed at 700 (D-030). Continuity residual 9.0 × 10⁻¹¹; T_out drift 2.3 × 10⁻⁶ K over the last 200 iterations; mass imbalance 7.0 × 10⁻¹³ %, energy 3.1 × 10⁻¹¹ % (VERIFIED, M047 / M048) |
| Fine convergence | converged at 600 and confirmed at 700; mass / energy imbalance 3.9 × 10⁻¹² % / 6.2 × 10⁻¹¹ % (6B) |
| Coarse convergence | converged at 600 and confirmed at 700 (6A) |
| Mesh-independence study | three meshes, r ≈ 1.46; status **B (approximately convergent)** for Δp, T_max, ΔT_wall, Nu, f. Geometric (faceting) changes are separated exactly and not called mesh error (D-035). Strict mesh independence is **not** claimed |
| Decision | **medium = official baseline** (D-034). Its error is small and conservative for the structural phase: T_max +4.4 K above the extrapolated 558.13 K; volume mean +3.1 K; mid-span ΔT_wall 0.04 K low |
| CFD uncertainty | register entries U1 (mesh) and U2 (model form) in `MASTER_UNCERTAINTIES.md` |

## 4. Structural final reference

| Element | Final setting | Stated consistently in |
|---|---|---|
| Temperature field | medium CFD solution `baseline_medium_final` (hash-verified, unchanged) | 7A, 7B, 8A, 8B, 9B-2 |
| Mapping | mesh-based External Data (Manual / Bucket Volume / Shape Functions / Nearest Node): 0 unmapped nodes; mapping error ≤ 0.081 K inside the source mesh; mapped range 423.84–562.56 K | 7A, 8B (per mesh), 9B-2 (per case) |
| Mesh | B: 36 × 5 × 130, bias 4 — 108,252 nodes / 23,400 SOLID186 (VERIFIED M081 / M082) | 7A, 7B, 8B (D-056), 9B-2 |
| Material | E(T), secant α(T) (MPAMOD re-referencing), ν 0.294 [ASSUMED], S_y(T) VDM table for assessment | 7A (D-036), 7B (D-050), all later |
| T_ref | 300 K (TREF 26.85 °C read from the solver input, VERIFIED M083) | all |

## 5. Support scenarios (kept distinct; no ranking)

| Scenario | Physical definition | λ₁ | P_cr | Governing mechanism in the idealised model |
|---|---|---|---|---|
| **S1** (current LC2) | ends restrained axially; ends can move sideways (end rotation held by U_z = 0 on the full face) | **1.108** | 608.25 kN | elastic bifurcation before first yield (1.108 < 1.730) |
| **S3** | inlet clamped; outlet held in position but free to rotate | **2.232** | 1,225.36 kN | first yield before elastic bifurcation (1.730 < 2.232) |
| **S2** | both ends laterally held and rotation held | **4.300** | 2,360.40 kN | first yield before elastic bifurcation (1.730 < 4.300) |

- **Physical effect:** greater lateral and rotational restraint of the ends gives a higher idealised buckling load factor. The mode changes accordingly: guided sway → fixed–pinned → clamped.
- The static stress state is the same in all three (peak 605.16 MPa, mean −582.44 MPa, end force 548.94 kN).
- This describes the model's response to an undefined boundary condition (T-034). It is **not** a recommendation of a support.

## 6. Buckling interpretation (checked in every document)

- λ₁ is a **linear eigenvalue buckling indicator**. It assumes an ideal, perfectly straight tube with idealised supports. It includes no imperfection, no nonlinear material response and no large-deflection effect, and it is **not** a guaranteed physical collapse load.
- **S1: λ₁ = 1.108.** The idealised S1 model is close to instability. λ₁ is **not a real-world factor of safety**. 8A and 8B state this explicitly (`BUCKLING_RESULTS.md` §7: "A factor of 1.108 does not mean …").
- The wording scan found no document that presents λ₁ or the first-yield factor as a factor of safety. The judgement word appears only in negated statements (8A, 8B, 9A).

## 7. Inconsistencies found and corrections made

No computed value was found wrong. The items are documentation-level; nothing was deleted.

| ID | Where | Finding | Correction / action |
|---|---|---|---|
| L-01 | root `README.md` | still showed "Section 0 — no results exist" and the planned folder map (`01_problem_definition` … `10_logs`) | status block added at the top pointing to `PROJECT_STATE.md` and `11_Final_Audit`, with the real folder map; original text kept |
| L-02 | `01_Requirements/ENGINEERING_REQUIREMENTS.md` | every FR / PR / NR requirement still "OPEN" (never updated after Section 1) | closure table with evidence in §9. The Section 1 file is left as the historical requirement record |
| L-03 | `01_Requirements/ASSUMPTIONS.md` | A-003 (limits unverified), A-013 (constant properties) and the A-012 justification ("ample elastic margin") superseded by later sections | final status of every assumption in `MASTER_ASSUMPTIONS.md` §3 |
| L-04 | `PROJECT_STATE.md` §9, `FLUENT_SETUP_NOTES.md` vs `ASSUMPTIONS.md` | **ID collision:** "A-020" means inlet turbulence intensity in the CFD documents and perfect thermal contact in the register | TI assumption renamed **A-020b** in `MASTER_ASSUMPTIONS.md` |
| L-05 | Sections 1–2 ("margin of safety" 0.59 / 0.56; PR-10), 7B ("margin 0.730") | these are **first-yield margins** (S_y/σ − 1) of a static state, not structural safety margins; 8A found S1 stability-limited (F-043) | clarification recorded here and in `PROJECT_STATE.md` §20. In the report use "first-yield margin" and state that stability governs under S1 |
| L-06 | `02_Engineering_Calculations/EXPECTED_RESULTS.md` | six final values lie outside the Section 2 bands (§10) | explained deviations (F-027 mean-rise basis, F-029 gas-heating friction). Not errors; bands kept as the historical record |
| L-07 | `PROJECT_STATE.md` §18.3 | attributes the slightly more-than-proportional temperature response to q″ to air / Inconel property variation *as a fact*; 9B-2 found the cause not isolated | clarification in §20: the cause is not isolated |
| L-08 | `PROJECT_STATE.md` §8 (file tree up to 5B), §9 / §10 (task and flag tables of 5B) | superseded by the per-section file lists and flag / task tables appended later (append-only convention) | noted in §20; `FILE_INTEGRITY_AUDIT.md` gives the current folder status |
| L-09 | `Claude outputs/` | 7 stale copies of earlier drafts | not-authoritative note added; not deleted; no document cites the folder |
| L-10 | `03_CAD_Geometry/Screenshots`, `05_Meshing/Screenshots` | folder names say "Screenshots", but the images are captioned renders | wording note: call them renders; no fake screenshot exists |
| L-11 | `09_Mesh_Independence/Mesh_Independence_Report.md` | the wording "on the … side" for the medium-mesh temperature bias | means *conservative*; use "conservative" in the report |
| L-12 | 9A (`PARAMETRIC_PLAN.md`, `SCREENING_RESULTS.md`, F-048) | the screening put V01 at λ₁ ≈ 1.00 (≤ 1); the FE gives 1.0031 | superseded by the FE result (F-051); the report must cite the FE values only |
| L-13 | `PROJECT_STATE.md` §6b (Section 3) | "≈ 48,000 solid nodes for Mechanical" | Section 3 planning estimate; the final mesh B has 108,252 nodes |
| L-14 | S_y values 1023.7 (Section 2), 1020 (7A Engineering Data scalar), 1047.0 MPa (7B local) | three different quantities | kept distinct in the master data; only S_y(T) at the local node is used for utilisation |
| L-15 | PR-09 target −668 MPa (Section 1) vs −657.2 MPa (Section 2) | Section 1 target superseded by the corrected Section 2 value (D-020) | recorded in the §9 closure table |

## 8. Findings A–L of the brief: verified against the evidence

| # | Statement | Supported? | Evidence (master IDs) | Qualification |
|---|---|---|---|---|
| A | Baseline CFD is converged and conserves mass and energy | **Yes** | converged at 600, confirmed at 700; imbalances 7.0 × 10⁻¹³ % / 3.1 × 10⁻¹¹ % (M047–M049) | — |
| B | The medium mesh is adequate for the downstream structural analysis | **Yes** | D-034; medium T_max +4.4 K above extrapolated; structural effect LC2 −10.1 / +2.8 MPa, λ₁ +1.8 / −0.5 % | adequate with a quantified, slightly conservative error |
| C | Fine-mesh CFD confirms that the key thermal / flow quantities are approximately converged | **Yes** | medium → fine: Δp +0.23 %, T_max −1.75 K (−0.66 % of the rise), Nu +0.91 %, f +0.85 %, ΔT_wall +0.21 % (M050–M057) | status **B**, approximately convergent. Apparent order 1.2–1.6, below the formal 2 (F-032). Not strict mesh independence |
| D | Structural LC2 stress is approximately 605 MPa | **Yes** | LC2 peak von Mises 605.161 MPa (M090) | this is the **local peak** at the inlet-face outer edge. The column load measure is the mean axial stress −582.44 MPa (M092) |
| E | The structural result is not materially sensitive to the structural mesh | **Yes** for LC2 and λ₁ | largest change against B: 4.9 × 10⁻⁴ (LC2 peak), 5.4 × 10⁻⁵ (λ₁) (M124) | LC1 surface stresses carry a −2.1 % bias (F-046) |
| F | The linear buckling factor for S1 is approximately 1.108 | **Yes** | 1.10805 (M098); fine meshes within 6 × 10⁻⁶ | — |
| G | For S1, buckling is the limiting idealised instability mode before first yield | **Yes** | λ₁ 1.108 < first-yield factor 1.730 (M096, M098) | idealised linear model; the conventional inelastic (Johnson) estimate is lower still (1.058, 8A) |
| H | The end-support definition changes the idealised buckling factor substantially | **Yes** | S1 1.108 · S3 2.232 · S2 4.300 (M098 / M104 / M101): factor 3.9 | — |
| I | Pressure loading is negligible compared with thermal loading | **Yes** | LC2P − LC2 = +45 Pa on 605.16 MPa (7.4 × 10⁻⁶ %) at the CFD maximum wall pressure (M097) | shown for P00; the design cases have Δp of the same order (not re-run, D-071) |
| J | Velocity mainly changes cooling and pressure drop, and affects the structural response indirectly | **Yes** | V −10 / +10 %: Δp −13.3 / +14.1 %; T_max +24.9 / −20.5 K; the structural response follows the temperature (end force +9.7 / −8.0 %, λ₁ 1.003 / 1.211); P_cr changes < 0.7 % | — |
| K | Heat flux directly drives temperature and thermal stress | **Yes** | q″ −10 / +10 %: T_max −28.1 / +28.6 K; end force and LC2 VM −11.0 / +11.2 %; λ₁ 1.255 / 0.988; Δp only ±4.2 % | — |
| L | Wall thickness strongly affects axial stiffness and buckling capacity, with a relatively small temperature effect at constant total heat input | **Yes** | t 8 / 12 mm: T_max −0.61 / +0.50 K; A −25.3 / +28.0 %; I −36.7 / +49.5 %; end force −25.6 / +28.5 %; P_cr −36.6 / +49.3 %; λ₁ 0.945 / 1.287 | the LC2 stress level barely changes (−0.47 / +0.43 %): thickness changes the force and the capacity, not the stress |

## 9. Requirements closure (the Section 1 requirements, evaluated with the final results)

| ID | Requirement (short) | Final result | Status |
|---|---|---|---|
| FR-01 … FR-05 | turbulent internal flow; conjugate HT; through-wall field; FE from CFD field; two load cases on one field | Re 29,958 / 25,545; coupled interface; 10 solid cell layers; mapped field; LC1 + LC2 | **MET** |
| FR-06 | linear-elastic regime or declared | max utilisation 0.645 (all cases) < 1; nonlinear buckling declared out of scope | **MET** |
| PR-01 | energy balance within 0.5 % of 603.2 W | 602.755 W (−0.071 %, entirely 48-gon faceting); imbalance 3.1 × 10⁻¹¹ % | **MET** |
| PR-02 | T_out within 3 % | 368.93 K vs 368.85 K (+0.08 K) | **MET** |
| PR-03 | Nu_fd within 44–67 | 54.17 | **MET** |
| PR-04 | f within 10 % of Petukhov 0.0241 | 0.02163: −10.4 % (fine −9.6 %, extrapolated −8.4 %) | **NOT MET (marginal)**, explained as a gas-heating effect (F-029); not re-interpreted |
| PR-05 | Δp within 15 % of 412 Pa (Section 1) | 438.13 Pa (+6.3 %; −0.77 % vs the Section 2 441.5 Pa) | **MET** |
| PR-06 | peak inner-wall T within 5 % of 574.3 K | 555.27 K (−3.3 %) | **MET** |
| PR-07 | through-wall ΔT within 10 % of 7.2 K | 7.36 K at z = 570 mm (+2.2 %); 7.58 K at mid-span | **MET** |
| PR-08 | LC1 peak VM within 15 % of 16.5 MPa (thick-cylinder closed form) | mid-span bore 18.20 MPa (+10.3 %); −1.9 % vs the closed form evaluated on the CFD field (18.55 MPa). The 24.28 MPa inlet-end peak is outside the closed-form scope (T-013) | **MET** (mid-span, as specified) |
| PR-09 | LC2 axial stress within 10 % of −668 MPa | mean −582.44 MPa: −12.8 % vs −668 (−11.4 % vs the Section 2 −657.2); +0.1 % vs the same closed form on the CFD mean rise (−581.9 MPa) | **NOT MET as written**; the gap is the analytical vs CFD mean temperature rise (254.7 vs 225.5 K, F-027), not a model error |
| PR-10 | margin vs hot yield reported for both load cases | LC1 utilisation 0.023; LC2 0.578 (first-yield margin 0.730) | **MET** (reported). Interpretation superseded: S1 is stability-limited |
| PR-11 | LC2 / LC1 ratio quantified (≈ 40×, order of magnitude) | 32× at mid-span, 25× peak to peak | **MET** |
| NR-01 | y⁺ ≤ 1 | max 0.585, 100 % ≤ 1 | **MET** |
| NR-02 | mesh independence: < 3 % change in Nu and peak solid T | Nu 1.48 / 0.91 %; T_max 1.07 / 0.66 % of the rise | **MET** in the stated sense (status B) |
| NR-03, NR-04, NR-06 | residuals; physical-monitor plateau < 0.1 K; second order | 9.0 × 10⁻¹¹; 2.3 × 10⁻⁶ K; second-order upwind from iteration 301 | **MET** |
| NR-05 | orthogonal quality > 0.1, skewness < 0.95 | medium 0.446 / 0.760; fine 0.314 / 0.836 | **MET** |
| NR-07 | mapped min / max within 1 K of the source | 423.84–562.56 K vs 423.84–562.54 K; 0 unmapped | **MET** |
| CR-03, CR-04 | mesh size; node limit | 159,840 cells; 108,252 nodes < 128,000 (measured) | **MET** |

## 10. Section 2 expected bands against the final results

| Quantity | Band | Final | In band | Reason if outside |
|---|---|---|---|---|
| Re inlet / outlet | 29,400–30,500 / 25,000–26,100 | 29,958 / 25,545 | yes / yes | |
| Darcy f | 0.022–0.027 | 0.02163 | **no** | gas-heating reduction (F-029) |
| Δp | 375–510 Pa | 438.13 Pa | yes | |
| Q | 600–606 W | 602.755 W | yes | |
| T_out | 365–373 K | 368.93 K | yes | |
| Nu_fd | 44–67 | 54.17 | yes | |
| Peak inner-wall T | 534–583 K | 555.27 K | yes | |
| Through-wall ΔT | 6.6–8.0 K | 7.581 K (mid-span) | yes | |
| Max solid T | 541–591 K | 562.58 K | yes | |
| y⁺ | ≤ 1 | 0.585 | yes | |
| Volume-mean solid T | 542–566 K | 525.48 K | **no** | the band rests on the Section 2 length-averaged mid-wall temperature; CFD mean rise is 225.5 vs 254.7 K (F-027) |
| Free axial growth | 1.95–2.25 mm | 1.8409 mm | **no** | same cause; the FE equals ∫ε_th dz of the CFD field to 1.3 × 10⁻⁵ |
| LC1 peak VM (mid-span) | 13–20 MPa | 18.20 MPa | yes | the 24.28 MPa peak is an inlet end effect |
| LC2 axial stress (mid-span) | 600–700 MPa compressive | mean 582.44; mid-span outer 593.4 / bore 564.9 MPa | **no** | same cause (F-027) |
| LC2 utilisation | 0.60–0.70 | 0.578 | **no** | lower temperatures, and S_y(T) at the local node (1047.0 vs 1023.7 MPa) |
| LC2 margin (S_y/σ − 1) | 0.43–0.67 | 0.730 | **no** | same |
| LC2 / LC1 ratio | 30–50× | 32× (mid-span) | yes | |

## 11. Parametric study: provenance

- Every final parametric number comes from the **actual 9B-1 CFD fields**, the **actual 9B-2 Mechanical LC1 / LC2 solutions** and the **actual linear buckling solutions**.
- 54 parametric values were re-read in 10A from each case's Fluent reports and MAPDL tables: **all VERIFIED**.
- The 9A screening appears only in clearly labelled comparison tables (`PARAMETRIC_TRENDS.md` §5, `SCREENING_COMPARISON.md`). No final conclusion cites a screening value.
- The one screening statement contradicted by the FE is V01 ≤ 1. It is superseded (L-12).

## 12. Cases with λ₁ < 1, and the near-1 case

| Case | λ₁ (S1) | Label in the 9B-2 deliverables | Checked |
|---|---|---|---|
| Q03 (q″ 8,800 W/m²) | 0.98834 | "pre-buckling equilibrium result; linear stability criterion indicates loss of stability before the applied load level" (CSV status, results MD; verify_9B2 V3) | yes |
| T01 (t 8 mm) | 0.94497 | same | yes |
| V01 (V 21.15 m/s) | 1.00307 | marginal, 0.31 % above 1 (`FINAL_PARAMETRIC_AUDIT.md` Q6) | yes |

The Q03 and T01 LC2 static solutions are **idealised pre-buckling equilibrium calculations**. They are not described anywhere as
physically stable operating conditions.

## 13. First yield vs linear buckling (used consistently)

- **Baseline S1:** LC2 yield utilisation 0.578 (first-yield factor 1.730), but λ₁ = 1.108. The idealised S1 case is therefore **stability-limited before first yield**.
- **S2 and S3:** the first-yield factor (1.730) is below λ₁ (4.300, 2.232). In the current analysis first yield comes before the idealised buckling mode.
- **All seven S1 design cases** are stability-first; none is yield-limited (maximum utilisation 0.645).
- The two factors are always reported side by side. No single factor of safety is formed anywhere in the project.

## 14. Items that remain uncertain

1. **Real end restraint** (flange lateral / rotational stiffness): undefined (T-034). It controls λ₁ and which mechanism comes first.
2. **Imperfection-sensitive nonlinear buckling**: not run (T-035). The real capacity is expected below the linear λ₁.
3. **Inelastic material behaviour**: no temperature-dependent stress–strain data (T-036, F-045). The Johnson estimates are conventional only.
4. **Turbulence / property model form**: not quantified by a model-form study (F-029, F-034, F-027). There are no experimental data to validate against.
5. **Radiation** (A-015, T-009) and **ν** (T-014): assumed, not varied.
6. **The side of λ₁ = 1 for V01 and Q03** lies inside the thermal and material uncertainty bands (`MASTER_UNCERTAINTIES.md` §4).
7. **Combined parameter changes**: not studied (one factor at a time; interaction 8–11 %).
8. **Facts about the original internship** (A-001 licence, A-002 scope): unconfirmed (T-002, T-003).

## 15. Final project conclusion supported by the evidence

Within the re-analysed, idealised model (2026 ANSYS Student simulations, not validated against measurement):

- **Temperatures.** The air-cooled Inconel 718 duct (D_i 20 / D_o 40 / L 600 mm, 23.5 m/s, 8000 W/m²) reaches a maximum solid temperature of **562.58 K** on the official medium CFD mesh (fine 560.83 K; Richardson-extrapolated 558.13 K). The through-wall temperature difference is only **7.58 K** at mid-span, because the air film carries most of the thermal resistance.
- **LC2 stresses.** With both ends axially restrained (LC2), the prevented thermal growth produces:
  - an end force of **548.94 kN**;
  - a mean axial stress of **−582.44 MPa**;
  - a local peak von Mises stress of **605.16 MPa** at the inlet-face outer edge, i.e. **57.8 %** of the local yield strength.
- **Restraint dominates.** The through-wall gradient alone (LC1, free expansion) produces a peak of only 24.28 MPa. Axial restraint, not the gradient, dominates the thermal stress (32× at mid-span).
- **Stability.** Under the baseline S1 support, the linear eigenvalue buckling factor is **1.108**, below the first-yield factor 1.730. The idealised S1 model is therefore stability-limited and close to instability.
  - In the ±10 % / ±20 % one-factor study, Q03 (λ₁ 0.988) and T01 (λ₁ 0.945) fall below 1, and V01 sits at 1.003.
  - Heat flux and velocity act through the wall temperature; wall thickness acts through the cross-section.
- **What controls the stability conclusion.**
  - The end-support definition: λ₁ 1.108 / 2.232 / 4.300 for S1 / S3 / S2. The real support is not defined.
  - Imperfections and inelastic behaviour, which were not modelled.

**The evidence therefore supports:**

- a quantified characterisation of the thermal-stress mechanism;
- its sensitivity to the operating and design parameters;
- its dependence on the end restraint.

**It does not support** a statement that a real component is structurally adequate.

## 16. Wording rule applied to the 10A documents

The 10A documents avoid the judgement words named in the brief. Where a factor is discussed, it is named for what it is:

- "linear eigenvalue buckling factor λ₁";
- "first-yield factor" (1 / utilisation);
- "first-yield margin" (S_y/σ − 1).

`Scripts/verify_10A.py` checks the eight 10A documents for the judgement words.

## 17. Independent verification of `11_Final_Audit`

`Scripts/verify_10A.py` (standard library only; reads files, writes only `Verification/verify_10A_results.json`), run on the
device with the ANSYS-bundled CPython 3.10 after all 10A files were written: **11 / 11 PASS**.

| ID | Check | Result |
|---|---|---|
| V1 | the eight deliverables exist | PASS |
| V2 | re-analysis notice at the top of each | PASS |
| V3 | no judgement words ("safe", "best", "optimal", "failure-proof") outside quoted scan-term lists; includes the `Claude outputs` note | PASS |
| V4 | master CSV: notice header, IDs M001–M182 sequential and unique, allowed statuses only, no MISMATCH | PASS |
| V5 | each of the 156 recomputed items is in the CSV with the same status and a correctly rounded value | PASS |
| V6 | every file named in the "Source file" column exists (120 paths; 4 rows cite derived comparisons, not files) | PASS |
| V7 | the parametric tables in `FINAL_ENGINEERING_SYNTHESIS.md` and `MASTER_PROJECT_DATA.md` equal the CSV cell by cell | PASS |
| V8 | the brief's key numbers exist in the master data with their modelling level (19 numbers) | PASS |
| V9 | content rules: synthesis parts 1–17; L-01…L-15; findings A–L; 9 separate uncertainty sources and no combined percentage; supports not ranked; λ₁ not called a factor of safety; Q03 / T01 labelled | PASS |
| V10 | project files against the 10A manifest (4,856 files): the only changes are the planned edits (`README.md` changed, `Claude outputs/README_NOT_AUTHORITATIVE.md` added, `PROJECT_STATE.md` §20); nothing missing | PASS |
| V11 | no Python bytecode written into `11_Final_Audit` | PASS |

**One source-column clarification was made during verification.** Two traceability entries used shorthand that the path check
could not resolve:

- the parametric P_cr rows: "…/BUCKLING + LC2/s7b_react.csv";
- the S1 / S2 / S3 P_cr rows: "+ static reaction table".

`master_data_10A.py` was changed to write both full file paths (load-factor table + reaction table) and re-run. All 156 values
and statuses were unchanged; only the 9 source strings differ.
