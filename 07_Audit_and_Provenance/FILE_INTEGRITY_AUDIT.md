# FILE INTEGRITY AUDIT — Section 10A

> **RE-ANALYSIS 2026 — Re-analysed / Assumed / Simulated 2026.** Every file in this project was created in 2026. None is a
> recovered file of the Eleation internship (Feb–May 2025), whose files were lost. This audit checks the 2026 files against the
> hash records written during the re-analysis.

**Nothing was deleted, moved or overwritten by this audit.** It reads files and writes only inside `11_Final_Audit/`. The one
exception is two new, clearly named notes (§8).

## 1. Method

| Step | Tool | Output |
|---|---|---|
| Full manifest: every file hashed with SHA-256 (4 MiB chunks); `11_Final_Audit` excluded | `Scripts/manifest_10A.py` | `Integrity/manifest_10A.csv`: **4,856 files, 14.64 GB**, 52.5 s |
| Comparison with every earlier hash record, list of duplicates, archives and images | `Scripts/integrity_10A.py` | `Data/integrity_10A.json` |
| Figure timestamps against their data files; spot checks of image content | manifest + visual check | this document §6 |

The manifest is the integrity reference for any later phase. It includes the first complete record of the 9B-1 and 9B-2 folders.

## 2. Earlier hash records compared with the files on disk today

| Record (section) | Record file | Files | Identical | Changed | Missing |
|---|---|---|---|---|---|
| 6B frozen medium / coarse / mesh / state files | `06_Fluent_CFD/Mesh_Independence/Fine/Audit/frozen_solutions_hashes_after.json` | 24 | 23 | 1 (`PROJECT_STATE.md`) | 0 |
| 6A medium baseline files | `06_Fluent_CFD/Mesh_Independence/Coarse/Audit/medium_baseline_hashes_after.json` | 21 | 20 | 1 (`PROJECT_STATE.md`) | 0 |
| 7A CFD source case / data | `07_Thermal_Analysis/Temperature_Source/Audit/source_case_data_hashes.json` | 2 | 2 | 0 | 0 |
| Baseline CFD case files (7A) | `08_Structural_Analysis/Workbench/Audit/cfd_case_hashes_after.json` | 3 | 3 | 0 | 0 |
| Baseline CFD data files (7A) | `08_Structural_Analysis/Workbench/Audit/cfd_data_hashes_after.json` | 2 | 2 | 0 | 0 |
| Section 4 Workbench project (7A) | `08_Structural_Analysis/Workbench/Audit/section4_project_hashes_after.json` | 7 | 7 | 0 | 0 |
| 7A key files | `08_Structural_Analysis/Workbench/Audit/section7A_key_file_hashes.json` | 22 | 21 | 1 (`PROJECT_STATE.md`) | 0 |
| pre-7B key files | `08_Structural_Analysis/Audits/pre7B_key_file_hashes.txt` | 5 | 5 | 0 | 0 |
| 7A project files (post-7B) | `08_Structural_Analysis/Audits/post7B_7A_project_files_hashes.json` | 20 | 20 | 0 | 0 |
| 7B solved project files (post-7B) | `08_Structural_Analysis/Audits/post7B_solve_7B_project_files_hashes.json` | 57 | 57 | 0 | 0 |
| 7B project (post-8A) | `08_Structural_Analysis/Buckling/Audits/post8A_7B_project_hashes.json` | 58 | 58 | 0 | 0 |
| 7B project (post-8B) | `08_Structural_Analysis/Mesh_Study/Audits/post8B_7B_project_hashes.json` | 58 | 58 | 0 | 0 |
| **All of `08_Structural_Analysis` (pre-9B-2)** | `10_Parametric_Study/Structural_Cases/Audits/pre9B2_08_Structural_Analysis_hashes.csv` | **1,927** | **1,927** | 0 | 0 (**0 added**) |

- `PROJECT_STATE.md` is the living project record. It is updated at the end of every phase by design, so the only "changed" entries are expected.
- **Baseline CFD** (`06_Fluent_CFD/Case`, `Data`) is unchanged: `baseline_medium_final.cas.h5` is SHA `84D6511B…` and `.dat.h5` is `F05837C5…`, as recorded in 5B, 6A, 6B and 7A.
- **Official structural 7B files**: the solved 7B project (57/58 files) and all 7B solver outputs are unchanged.
- **8A buckling files** are unchanged (inside the 1,927-file record of `08_Structural_Analysis`).
- In 9B-2 a Python cache file had been added to `08_Structural_Analysis/Buckling/__pycache__/`. It was moved (not deleted) to `10_Parametric_Study/Results/Verification_9B2/Moved_from_08/`. The empty `__pycache__` folder remains; it holds no file.
- Only the timestamp of `08_Structural_Analysis/Workbench/Flow_Behavior_Thermal_Effects_Structural_7B_files/.project_cache` moved (2026-09-27 15:00, when the project was opened for a save-as copy). Its content hash is unchanged.

## 3. Folders without a hash record: newest-file check

| Folder | Newest file (date, file) | Reading |
|---|---|---|
| `06_Fluent_CFD` (5B baseline, 6A coarse, 6B fine) | 2026-09-24 19:44, `Mesh_Independence/Fine/Audit/project_state_append_check.json` | nothing written after Section 6B |
| `09_Mesh_Independence` | 2026-09-24 19:44, `Mesh_Independence_Report.md` | nothing written after Section 6B |
| `07_Thermal_Analysis` | 2026-09-25 11:11, `THERMAL_MAPPING_NOTES.md` | nothing written after Section 7A |
| `05_Meshing` | 2026-09-25 11:04, Section 4 project `.project_cache` | timestamp only; content hash-identical (Section 4 record) |
| `03_CAD_Geometry` | 2026-09-19 13:57 | nothing written after Section 3 |
| `01_Requirements`, `02_Engineering_Calculations`, `00_admin` | 2026-09-18 | frozen since Sections 0–2 |

**9B-1 CFD parametric cases** (`10_Parametric_Study/CFD_Cases/`; no hash record was written in 9B-1):

| Case | Files | First file | Last file |
|---|---|---|---|
| C00_PIPELINE_CHECK | 63 | 2026-09-26 17:51 | 2026-09-26 20:11 |
| V01_LOW / V03_HIGH | 58 / 58 | 18:21 / 18:37 | 20:06 |
| Q01_LOW / Q03_HIGH | 58 / 58 | 18:55 / 19:12 | 20:06 |
| T01_THIN / T03_THICK | 58 / 58 | 19:30 / 19:47 | 20:06 |
| M03_T03_CFD_SOLID18 (9B-2 Part A) | 56 | 22:38 | 22:49 |

No 9B-1 case file was modified after 9B-1 finished (20:11); 9B-2 only read them. The 9B-2 structural cases are recorded for the
first time in the 10A manifest.

## 4. Duplicate files (identical content, > 1 kB)

**437 groups; 3.35 GB of redundant bytes. All are copies made on purpose; none is deleted.**

| Kind | Groups | Redundant size | Why it exists |
|---|---|---|---|
| Solver files copied out of the Workbench projects (`Solver_Output`, `Presolve_Inputs`, geometry `.scdocx`) | 320 | 2.36 GB | every section archives the exact solver input and output beside its report (D-049) |
| Workbench save-as project copies | 36 | 0.57 GB | each phase solves in a save-as copy so the earlier project stays byte-identical (D-046, D-051, D-054, 9B-2) |
| Scripts / data copied between sections | 68 | 0.38 GB | e.g. Fluent transcripts, `mode_shapes.py` in 8A and 8B, CFD exports reused as the 9B-1 C00 control |
| Mesh / case copies | 2 | 0.03 GB | `*_mesh_used_for_*.msh` beside each CFD case (documented in 5B / 6A) |
| `09_Mesh_Independence/Raw_Data` copies of the CFD result files | 6 | < 0.1 MB | the 6B study keeps its own input copies |
| `Claude outputs` copies | 5 | 0.5 MB | see §5 |

## 5. Superseded, archived and stale material (not deleted)

| Location | Content | Status |
|---|---|---|
| `Claude outputs/` (12 files) | copies of early deliverables made by the app. **7 of 12 differ from the project versions** (older drafts): `FINE_CFD_RESULTS.md`, `FINE_CFD_AUDIT.md`, `GEOMETRY_CORRECTION.md`, `mesh_study.py`, two calculation plots, `ENGINEERING_SCHEMATIC.png`. The other 5 are identical copies | **stale — not a source**. A note `README_NOT_AUTHORITATIVE.md` was added (§8). No project document cites this folder |
| `02_Engineering_Calculations/section1_sizing/` | Section 1 sizing scripts (12 kW/m² era) | superseded by Section 2 (D-015); retained |
| `05_Meshing/Mesh_Quality/SUPERSEDED_preflip_fluent_check.txt` | first Fluent read with reversed face normals (F-016) | superseded; retained |
| `07_Thermal_Analysis/Mapping/fluent_solid_temperature_pointcloud.csv`, `pointcloud_source_tags.csv` | point-cloud transfer that failed validation (7A) | rejected method; retained as evidence (`rejected_methods_evidence.json`) |
| `08_Structural_Analysis/Mechanical_Setup/Superseded_run1…4`, `Workbench/Logs/Superseded_run1…4` | 7A build runs 1–4 | superseded by run 5; retained |
| `08_Structural_Analysis/Audits/Gate_Run1_FAIL`, `Buckling/Audits/Gate_Run1_FAIL`, `Gate_Run2_FAIL`, `Run3_STOPPED_at_images` | gate stops before any solve (7B, 8A) | archived |
| `08_Structural_Analysis/Workbench/probe*`, `Licence_Check/probe_*` | throw-away probe projects, licence-limit probes (7A) | archived evidence (T-026) |
| `08_Structural_Analysis/Mesh_Study/Post/doc_src/*.src.md` | document sources of the 8B reports | generator input; the published reports are the `.md` files one level up |
| `10_Parametric_Study/Structural_Cases/Audits/Run1…Run6_*` | 9B-2 run archives (gate stops, S3 deck failures, shutdown) | archived with READMEs |
| `10_Parametric_Study/Structural_Cases/S2_REEXTRACT/Run1_shared_session/` | S2 re-extraction run 1 (shared MAPDL database) | superseded by run 2; README explains |
| `10_Parametric_Study/CFD_Cases/Journals/Archive/` | 9B-1 journal v1 used for C00 | archived with diff |

**Empty placeholder folders from Section 0** (planned layout, never used): `03_geometry`, `04_mesh`, `05_cfd_fluent`,
`06_thermal_structural`, `07_workbench`, `08_results`, `09_report`, `10_logs`. The work lives in `01_Requirements` … `10_Parametric_Study`.
The root `README.md` still described the planned layout and "Section 0" status; a status block was added at its top (§8).

**Stale-reference check.** The 10A documents cite only current files. The master data script reads the official folders only (never
`Superseded_*`, `Run*_FAIL*`, `probe*`, `Claude outputs`). No current section report points to a superseded result file.

## 6. Figures and screenshots

| Folder | Images | Provenance | Timestamp vs data |
|---|---|---|---|
| `03_CAD_Geometry/Screenshots` | 9 | matplotlib renders of the STL exported by SpaceClaim; each image is captioned *"rendered from heated_duct.stl exported by ANSYS SpaceClaim 2026 R1"* | — |
| `05_Meshing/Screenshots` | 12 | matplotlib renders of the real mesh arrays; captioned *"NOT an ANSYS GUI screenshot"* (checked) | — |
| `06_Fluent_CFD/Figures`, `Mesh_Independence/Coarse, Fine/Figures`, `09_Mesh_Independence/Plots` | 17 / 10 / 10 / 11 | plots of exported Fluent data | all newer than their result JSON |
| `07_Thermal_Analysis/Figures` | 5 | plots of the mapping validation | newer than `mapping_validation_7A.json` |
| `08_Structural_Analysis/Figures` (F7B), `Buckling/figures` (F8A) | 6 / 4 | plots of the post-processed MAPDL tables | newer than their JSON |
| `08_Structural_Analysis/Mesh_Study/figures` (F8B) | 9 | plots of the 8B tables | 1 min older than `post_8B_results.json`, because the whole `Post/` folder was copied to the device after plotting (every file there carries the 13:36 copy time). Values checked: F8B_06 shows λ₁ 1.10799–1.10805, equal to the recomputed values (M112–M122) |
| `08_Structural_Analysis/Figures/Mechanical` (+ `Zoom`), `Buckling/figures/Mechanical`, `Mesh_Study/figures/Mechanical`, 9B-2 case `Figures/` | 97 / 32 / 40 / 57 | **genuine ANSYS Mechanical image exports**, written by the Mechanical scripts during the solves (legend of `LC2_Z_inlet_Equivalent_Stress.png`: max 6.0516e8 Pa = 605.16 MPa, checked) | written in the solve session, before the post-processing tables |
| `10_Parametric_Study/Results/Figures` | 15 | plots of the 9B-2 data | generated from the data as staged; `post_9B2_results.json` was re-written later with byte-identical content (9B-2 §19.7) |

- **No fake screenshot exists.** No image is named or captioned as a GUI screenshot; the two folders called `Screenshots` hold captioned renders.
- **Wording for the report:** call them "renders" or "figures", not "screenshots" (T-016: a genuine SpaceClaim UI capture would have to be taken by hand).

## 7. Integrity findings

| # | Finding | Severity | Action |
|---|---|---|---|
| I-1 | All baseline, 7B and 8A result files identical to their records | — | none |
| I-2 | `Claude outputs/` holds 7 stale copies | Low | not deleted; not-authoritative note added |
| I-3 | Root `README.md` described the Section 0 plan (folders and status) | Low | status block added at the top; original text kept |
| I-4 | 8 empty placeholder folders | Info | kept (deleting is not needed) |
| I-5 | Folders named `Screenshots` contain renders | Info | wording note for the report |
| I-6 | 3.35 GB of intended duplicates | Info | kept; required for traceability |
| I-7 | 9B-1 / 9B-2 folders had no hash record | Low | covered by the 10A manifest from now on |

## 8. Files written outside `11_Final_Audit` by this audit

- `README.md` (root): a status block added at the top, pointing to `PROJECT_STATE.md` and `11_Final_Audit`, with the real folder map. The original Section 0 text is kept below it unchanged.
- `Claude outputs/README_NOT_AUTHORITATIVE.md`: a new note stating that the folder holds non-authoritative copies.
- `PROJECT_STATE.md`: header lines and an appended §20 (living document).
