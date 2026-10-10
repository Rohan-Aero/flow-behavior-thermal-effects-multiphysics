# Data dictionary

Database: `database/simulation_results.db` (SQLite 3), built by `import_results.py` from `schema.sql`.

## 1. What the data is

* Results of the project's **2026 re-analysis** of a heated Inconel 718 tube (ID 20 mm, OD 40 mm, L 600 mm): ANSYS Fluent CFD, ANSYS Mechanical thermal-structural and linear-buckling analyses, and the follow-on LS-DYNA 12C nonlinear buckling study. The repository states that no value is recovered internship data and that no experimental data exist.
* The SQL layer is a **separate follow-on extension**. It is not part of the February to May 2025 internship, and it adds no new simulation: every number is copied from a summary file that is already in this repository.
* Values are stored **exactly as parsed** from the source (no rounding, no unit conversion except the exact metre-to-millimetre scaling of baseline geometry, done in decimal arithmetic).

## 2. Tables

```
source_files 1──* simulation_cases 1──* solver_runs 1──* simulation_results *──1 metrics
                          │  └─* case_parameters           │
                          └────* validation_checks *───────┘ (run optional)
```

| Table | One row is | Key columns |
|---|---|---|
| `source_files` | a repository file the importer read, with SHA-256 and size at import | `repo_path` (unique, repository-relative), `file_role` |
| `simulation_cases` | an engineering case: the baseline design point P00, the C00 pipeline control, a parametric design point, or an LS-DYNA imperfection case | `case_code` (unique), `case_group`, `parent_case_id`, `case_status` (`reference`, `solved`, `not_run`) |
| `case_parameters` | one input parameter of a case (numeric `value` or `value_text`, never both) with `units` | PK (`case_id`, `parameter`) |
| `solver_runs` | one solver run of a case: CFD mesh level, structural load case and support, eigenvalue run, or LS-DYNA run | `run_code` (unique), `solver`, `analysis_type`, `load_case`, `support_condition`, `mesh_level`, `n_cells` / `n_nodes`, `run_status` (source's label), `converged`, `iterations`, `model_limitation` |
| `metrics` | the definition of one quantity: unit, family, meaning, caveat | `metric_id` (PK) |
| `simulation_results` | one scalar result of a run | UNIQUE (`run_id`, `metric_id`); FK (`metric_id`, `units`) to `metrics` so a unit cannot differ from the definition |
| `validation_checks` | a check or status attached to a case/run | `check_origin`, `check_name`, `status`, `source_status`, `observed_value`, `reference_value`, `tolerance`, `detail` |

Views: `v_results` (one flat row per result with case, run and metric context) and `v_lsdyna_case_summary` (the distinct LS-DYNA load metrics side by side).

### Columns that need explanation

* `simulation_results.source_file_id`, `source_case_id`, `source_field`: the file, the case identifier used **in that file** (for example `V01_LOW`, `S2`, `coarse`, `C3_A0p6`), and the column / row / key the value came from. `validate_database.py` re-reads that cell for every result.
* `simulation_results.value_status`: `reported` (a value exists) or an explicit reason it does not: `not_identifiable` (the source says it cannot be identified), `not_reached` (a threshold was never reached), `not_available` (blank in the source). When `value` is NULL a `missing_reason` is always present.
* `simulation_results.physical_validity` (default `not_assessed`): `within_elastic_range` or `beyond_yield_elastic_model_not_physical`. See section 6.
* `solver_runs.model_limitation`: the standing limit of the model that produced the run (for example "elastic-only, no plasticity").
* `validation_checks.check_origin`: `source_recorded` (a status or quality figure the project itself recorded), `import_crosscheck` (two repository files compared during import), `data_gap` (data the sources do not provide). `source_status` keeps the source's own label verbatim (mesh status A to E, "SOLVED - VALID ...", ...). `status` is `PASS`, `FAIL`, `DISCREPANCY` (two sources disagree; both kept), `INFO` (recorded, no pass/fail meaning) or `NOT_AVAILABLE`.

## 3. Case and run naming

| Case code | Meaning | Source identifier |
|---|---|---|
| `P00` | baseline: V 23.5 m/s, q'' 8000 W/m2, t 10 mm | `P00_BASELINE` |
| `C00_PIPELINE_CHECK` | baseline re-run through the parametric pipeline (control) | same |
| `V01_LOW`, `V03_HIGH` | inlet velocity 21.15 / 25.85 m/s | same |
| `Q01_LOW`, `Q03_HIGH` | outer-wall heat flux 7200 / 8800 W/m2 | same |
| `T01_THIN`, `T03_THICK` | wall thickness 8 / 12 mm with the total heat input held constant (q'' = 8888.9 / 7272.7 W/m2) | same |
| `C0_A0p0` | LS-DYNA perfect-geometry reference path | same |
| `C1_A0p1`, `C3_A0p6`, `C5_A1p2` | LS-DYNA imperfection amplitude A = 0.1 / 0.6 / 1.2 mm | same |
| `C2_A0p3`, `C4_A0p9`, `N1_A0p1_halfstep`, `C0b_A0p0_negev1_bifurcation_detect` | planned, **not run** (scope reduction); stored with `case_status = 'not_run'` and no results | folder name under `runs/` |

Run codes read `<case>:<solver>:<analysis>[:<detail>]`, for example `P00:fluent:coarse`, `V01_LOW:mech:static:LC1`, `P00:mech:buckling:S2`, `C1_A0p1:lsdyna:nonlinear`.
The CFD mesh study is three **runs of the same case P00** (`mesh_level` coarse, medium, fine); the medium run is the baseline CFD solution. Support scenarios S1, S2, S3 are runs of P00 with different `support_condition`. S1 is the baseline LC2 support.
Imperfection amplitude A is the numerical sensitivity amplitude (maximum lateral nodal value of the imposed buckling mode); the source states the imposed end offset as 2A. It is not a manufacturing tolerance.

## 4. Controlled vocabularies

| Column | Values |
|---|---|
| `solver_runs.analysis_type` | `cfd_conjugate_steady`, `static_structural_thermal`, `linear_eigenvalue_buckling`, `nonlinear_implicit_thermal_buckling` |
| `solver_runs.load_case` | `LC1` free thermal expansion; `LC2` axially restrained; NULL for CFD |
| `solver_runs.support_condition` | `S1` guided column (baseline LC2 support), `S2` clamped-clamped, `S3` clamped-pinned |
| `metrics.quantity_family` | `cfd_flow`, `cfd_thermal`, `cfd_quality`, `structural_response`, `buckling_eigenvalue`, `nonlinear_load`, `nonlinear_response`, `yield_onset` |

## 5. Metrics

Unlike quantities have different `metric_id`s and are never merged. In particular these four are distinct:

* `buck.eig_pcr`: a **linear eigenvalue** critical load of an ideal structure (Mechanical, and the LS-DYNA 12B G6 cross-check).
* `lsdyna.southwell_ncr`: a **Southwell characteristic-load estimate** extrapolated from the nonlinear imperfect run. Not a load reached in the run.
* `lsdyna.n_max`: the **maximum load reached** in the run within lambda <= 1.3. It is an instability point only if `lsdyna.n_max_is_interior_max = 1`.
* `struct.first_yield_factor` and `lsdyna.yield_indicator_lambda`: two different **yield-onset load factors** (linear scaling of the LC2 state versus the first lambda at which nodal VM/S_y(T) = 1 on the nonlinear elastic path).

Results per run type (used by `validate_database.py` to check record counts): P00 mesh runs 15 each; parametric CFD runs 11 each; LC1 / LC2-S1 / buckling-S1 runs 10 per case in total (3 + 5 + 2), plus 1 LC1 utilisation for P00; S1 adds deformation, reaction and first-yield factor; S2 and S3 7 each; LS-DYNA linear cross-check 2; each LS-DYNA nonlinear case 19.

| metric_id | Units | Family | Meaning | Caveat |
|---|---|---|---|---|
| `cfd.dp_static` | Pa | cfd_flow | Area-weighted static pressure drop, inlet minus outlet |  |
| `cfd.t_out_bulk` | K | cfd_thermal | Mass-weighted static temperature at the outlet |  |
| `cfd.q_heated_wall` | W | cfd_thermal | Heat-transfer rate through the heated outer wall |  |
| `cfd.t_solid_max_facet` | K | cfd_thermal | Maximum solid temperature, outer-wall facet maximum |  |
| `cfd.t_solid_max_cell` | K | cfd_thermal | Maximum solid temperature, cell-centre value |  |
| `cfd.t_solid_min_cell` | K | cfd_thermal | Minimum solid temperature, cell-centre value |  |
| `cfd.t_solid_mean` | K | cfd_thermal | Volume-mean solid temperature |  |
| `cfd.dt_wall_midspan` | K | cfd_thermal | Through-wall temperature difference at z = 300 mm |  |
| `cfd.h_midspan` | W/m2K | cfd_thermal | Heat-transfer coefficient at mid-span |  |
| `cfd.nu_fd` | - | cfd_thermal | Fully developed Nusselt number (x/D 18-29 window) |  |
| `cfd.f_darcy_fd` | - | cfd_flow | Fully developed Darcy friction factor (x/D 18-29 window) |  |
| `cfd.re_out` | - | cfd_flow | Reynolds number at the outlet |  |
| `cfd.yplus_min` | - | cfd_quality | Minimum wall y+ (conjugate wall) |  |
| `cfd.yplus_mean` | - | cfd_quality | Area-mean wall y+ |  |
| `cfd.yplus_max` | - | cfd_quality | Maximum wall y+ | Not a convergence metric: the maximum sits in the first slab, whose centre moves with mesh size (source status E). |
| `struct.lc1.max_total_deformation` | mm | structural_response | LC1 (free expansion) maximum total deformation |  |
| `struct.lc1.axial_growth` | mm | structural_response | LC1 face-mean free axial growth |  |
| `struct.lc1.max_von_mises` | MPa | structural_response | LC1 maximum von Mises stress | Near-end value; sensitive to temperature-mapping node numbering (source F-035). |
| `struct.lc1.yield_utilisation` | - | structural_response | LC1 von Mises / S_y(T) at the maximum-stress node |  |
| `struct.lc2.max_von_mises` | MPa | structural_response | LC2 (axially restrained) maximum von Mises stress |  |
| `struct.lc2.mean_axial_stress` | MPa | structural_response | LC2 mean axial stress (negative = compression) |  |
| `struct.lc2.critical_temperature` | K | structural_response | Temperature at the LC2 node of maximum vm / S_y(T) |  |
| `struct.lc2.local_yield_strength` | MPa | structural_response | S_y(T) at that node |  |
| `struct.lc2.yield_utilisation` | - | structural_response | LC2 maximum vm / S_y(T) |  |
| `struct.lc2.max_total_deformation` | mm | structural_response | LC2 maximum total deformation |  |
| `struct.lc2.end_reaction_axial` | N | structural_response | LC2 axial end-face reaction (sum of FZ on the inlet face) |  |
| `struct.first_yield_factor` | - | yield_onset | Mechanical first-yield load factor = 1 / utilisation at the critical node (linear scaling of the LC2 state) | Linear-elastic scaling only. Not comparable with lsdyna.yield_indicator_lambda (nonlinear path, bending included). |
| `buck.eig_lambda1` | - | buckling_eigenvalue | First linear eigenvalue buckling load factor (multiplies the LC2 state) | Linear eigenvalue of an ideal straight tube with idealised supports: no imperfection, no plasticity, no large deflection. Not a collapse load and not a factor of safety (register M179). |
| `buck.eig_pcr` | kN | buckling_eigenvalue | Linear eigenvalue critical load = lambda1 x LC2 axial end force | Linear eigenvalue of an ideal straight tube with idealised supports: no imperfection, no plasticity, no large deflection. Not a collapse load and not a factor of safety (register M179). |
| `lsdyna.n_max` | kN | nonlinear_load | Largest axial compression N reached within lambda <= 1.3 in the nonlinear run | A value reached in a run, not a capacity. It is an instability point only if lsdyna.n_max_is_interior_max = 1. |
| `lsdyna.lambda_at_n_max` | - | nonlinear_load | Load factor lambda at which lsdyna.n_max occurs |  |
| `lsdyna.n_max_is_interior_max` | flag | nonlinear_load | 1 = N_max is an interior maximum (N later drops > 0.1 %); 0 = N still rising at the end of the analysis |  |
| `lsdyna.southwell_ncr` | kN | nonlinear_load | Southwell-plot characteristic (critical) load estimate, fit over N in [0.5, 0.95] N_max | Extrapolated estimate, not a load reached in the run. Not a linear eigenvalue and not a maximum load. |
| `lsdyna.southwell_r2` | - | nonlinear_response | R-squared of the Southwell fit |  |
| `lsdyna.southwell_window_low` | kN | nonlinear_load | Lowest Southwell N_cr over 5 fit-window variants |  |
| `lsdyna.southwell_window_high` | kN | nonlinear_load | Highest Southwell N_cr over 5 fit-window variants |  |
| `lsdyna.southwell_w0` | mm | nonlinear_response | Southwell intercept estimate of the initial end offset (source compares with imposed 2A) |  |
| `lsdyna.onset_lambda` | - | nonlinear_response | First lambda at which N is more than 1 % below the perfect-geometry path |  |
| `lsdyna.onset_n` | kN | nonlinear_load | N at lsdyna.onset_lambda |  |
| `lsdyna.n_at_lambda1` | kN | nonlinear_load | Axial compression at the design load factor lambda = 1 |  |
| `lsdyna.n_at_lambda1p3` | kN | nonlinear_load | Axial compression at the end of the analysis, lambda = 1.3 |  |
| `lsdyna.lateral_max_at_lambda1p3` | mm | nonlinear_response | Maximum section lateral translation at lambda = 1.3 |  |
| `lsdyna.end_sway_at_lambda1p3` | mm | nonlinear_response | Additional relative end sway at lambda = 1.3 |  |
| `lsdyna.vm_at_lambda1` | MPa | nonlinear_response | Peak nodal von Mises stress at lambda = 1 (end regions) | Elastic model: a value above S_y(T) is an indicator, not a physical stress. |
| `lsdyna.vm_max_end_region` | MPa | nonlinear_response | Peak nodal von Mises stress, end regions, lambda <= 1.3 | Elastic model: a value above S_y(T) is an indicator, not a physical stress. |
| `lsdyna.util_max` | - | nonlinear_response | Maximum VM / S_y(T) over lambda <= 1.3 (elastic-validity indicator) |  |
| `lsdyna.yield_indicator_lambda` | - | yield_onset | First lambda at which nodal VM / S_y(T) = 1 in the elastic nonlinear run | Indicator only; plasticity is not modelled. Not comparable with struct.first_yield_factor. |
| `lsdyna.yield_indicator_n` | kN | yield_onset | Axial compression N at lsdyna.yield_indicator_lambda |  |

## 6. Rules applied by the importer

1. **Exact storage.** `value = float(source text)`. Missing source cells become explicit non-`reported` rows.
2. **Units.** Taken from the source (column header or units column) and checked against `metrics.units`; the importer stops on a mismatch. Imbalances are stored in `validation_checks` with the source's unit (`%` in the mesh table, `fraction` in the parametric table).
3. **Not imported on purpose.** Geometry-corrected and "adjusted" estimate rows of the mesh study (they are estimates, not solver results), Richardson extrapolations and GCI values (only the GCI percentage and the status letter are kept as a check), the structural mesh-sensitivity variants (XC, C, FR, FA, FC, IL), Mechanical modes 2-6, mass flow, field profiles and all raw solver output.
4. **Duplicate or conflicting records stop the import** (`DuplicateRecord`, `ConflictingRecord`); any error rolls back the whole transaction.
5. **`physical_validity`.** For the Mechanical stress results: `within_elastic_range` when the source's yield utilisation (or first-yield factor) is at most 1. For LS-DYNA, using the source's own indicator lambda `yl` (first lambda with VM/S_y(T) = 1): a state at load factor lambda is `within_elastic_range` if lambda <= `yl` and `beyond_yield_elastic_model_not_physical` if lambda > `yl`; when the indicator was never reached, the state is within range if the source's maximum VM/S_y(T) is at most 1. Stress maxima use the source's maximum VM/S_y(T). Southwell and fit-quality metrics stay `not_assessed`. `beyond_yield_elastic_model_not_physical` means the elastic-only model (MAT_004) produced the number past first-yield indication; it is **not** validated physical behaviour.
6. **No inference.** Case parameters not varied in a case come from `baseline_parameters.json` and say so in `source_field`. Reaction forces for S1/S2/S3 come from register row M110 (status REPORTED).

## 7. Source-to-table mapping

| Source (repository path) | Loaded into |
|---|---|
| `02_CFD_Fluent/Comparison_Tables/three_mesh_raw_table.csv` | `simulation_results` for the three P00 CFD runs; imbalances to `validation_checks` |
| `02_CFD_Fluent/mesh_study_results.json` | `solver_runs` (cells, iterations, converged flag) for the mesh runs |
| `02_CFD_Fluent/MESH_INDEPENDENCE_RESULTS.csv` | `validation_checks` (`mesh_independence:<quantity>`: status A-E, GCI %, basis text) |
| `03_Thermal_Structural_Mechanical/CFD_Results/PARAMETRIC_CFD_RESULTS.csv` | cases, parameters, parametric CFD runs and results |
| `03_Thermal_Structural_Mechanical/Results/PARAMETRIC_STRUCTURAL_RESULTS.csv` | structural and buckling runs and results for P00, C00 and the six design cases; outer diameter; node counts |
| `03_Thermal_Structural_Mechanical/Results/results_summary_7B.csv` | P00 LC1 yield utilisation |
| `03_Thermal_Structural_Mechanical/Results/SUPPORT_SENSITIVITY_RESULTS.csv` and `.md` (section 4 table) | S2/S3 runs; S1/S2/S3 deformation; first-yield factor; governing-mechanism label |
| `05_Data/MASTER_PROJECT_DATA.csv` (row M110) | S1/S2/S3 axial reaction. Also the main validation target. |
| `01_Project_Documentation/baseline_parameters.json` | unvaried baseline parameters |
| `04_LS_DYNA_Extension/12C_Nonlinear_Buckling/IMPERFECTION_SENSITIVITY.csv` | LS-DYNA cases, amplitudes and nonlinear results |
| `.../comparisons/qc_12C.json`, `.../audit/imperfection_report_12C.json`, `.../MECHANICAL_vs_LSDYNA.csv` | run status, N at lambda = 1, LS-DYNA linear eigenvalue cross-check |
| `.../results/series/<case>_series.csv` | import-time cross-check of N_max and its lambda |
| `.../runs/<case>/NOT_RUN.txt` | the four not-run cases and their stated reason |

## 8. Known source observations (preserved, not resolved)

* **C1 lambda at N_max.** The summary table, `analysis_12C.json` and the binout N file place the C1 maximum at lambda 1.185; the extracted series file places it at 1.19 (and `RESULTS_AUDIT_12C.md` calls the point at 1.19 "the maximum"). The maximum is flat (N within 3 N), one 0.005 load step apart. Stored as a `DISCREPANCY` check; the reported value stays 1.185.
* **C00 pipeline control.** Equal to P00 except the LC1 inlet-bore peak stress (24.169 vs 24.282 MPa), which the source attributes to Fluent's re-numbered node ids in the temperature mapping.
* **Fluent facet maximum.** 562.57678 K in the raw Fluent report, 562.57675 K in the mesh-study table (relative difference 5e-8). Both are inside the stated validation tolerance.
* **Mesh-study status.** Several quantities are status D (affected by polygon geometry) or E (inconclusive); raw coarse/medium/fine changes are therefore not pure discretisation error.
* **Lambda1 below 1.** Q03_HIGH (0.98834) and T01_THIN (0.94497): the source notes that the linear stability criterion indicates loss of stability before the applied load level.
* **Stale documents.** `GITHUB_CONTENT_AUDIT.md` still says "NOT-PUBLIC-READY / nothing published" and `REPOSITORY_STRUCTURE.md` says "there is no 06 folder". Neither was changed.
