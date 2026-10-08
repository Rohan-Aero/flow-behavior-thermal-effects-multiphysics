# Mesh-Independence Audit — Section 6B

**RE-ANALYSIS 2026 — newly generated analysis of newly generated CFD runs, not recovered originals.**
This file records what the three-mesh study read, what it wrote, which checks it passed, and every
judgement that was revised during the work. Results: `Mesh_Independence_Report.md`.

## 1. Inputs (read only) and outputs

| Input | Used for |
|---|---|
| `06_Fluent_CFD/Baseline/cfd_baseline_results.json`, `06_Fluent_CFD/Profiles/axial_profiles_cfd.csv`, `06_Fluent_CFD/Exports/wall_interface.csv` | medium (Section 5B, frozen) |
| `06_Fluent_CFD/Mesh_Independence/Coarse/…` (same three files) | coarse (Section 6A, frozen) |
| `06_Fluent_CFD/Mesh_Independence/Fine/…` (same three files) | fine (this section) |
| `02_Engineering_Calculations/baseline_results.csv` | frozen Section 2 values (friction factor, peak wall temperature, structural sensitivities) |
| `06_Fluent_CFD/Diagnostics/F029_Isothermal/iso_results.json`, `iso_f_profile.csv` | F-029 diagnostic |

All outputs are written inside `09_Mesh_Independence/` by `Scripts/mesh_study.py`. The script
never writes to `06_Fluent_CFD/` or `02_Engineering_Calculations/`.

## 2. The three solutions being compared

| | Coarse | Medium | Fine |
|---|---|---|---|
| Section | 6A | 5B | 6B |
| Physics carried by | `mesh.replace` on the medium case | original setup (5A/5B audits) | `mesh.replace` on the medium case |
| Settings diff vs medium | 0 entries | — | 0 entries |
| Setup audit (3 stages) | 130/130 each | 59/59 each | 132/132 each; 177/177 items equal to medium, machine-readable |
| Initialisation | fresh standard | fresh standard | fresh standard |
| Converged / confirmed | 600 / 700 | 600 / 700 | 600 / 700 |
| Final continuity / energy residual | 1.2e-10 / 5.0e-14 | 9.0e-11 / 1.6e-14 | 1.9e-10 / 8.6e-15 |
| Mass / energy imbalance | 1.2e-13 % / 2.0e-11 % | 7.0e-13 % / 3.1e-11 % | 3.9e-12 % / 6.2e-11 % |
| Solve wall clock | 9.0 min | 13.0 min | 43.9 min |

All three are converged to round-off, so iteration error is negligible against discretisation
error (≤ 6 × 10⁻⁵ K on temperatures and ≤ 10⁻⁹ relative on Δp; §4).

## 3. Identical definitions

Every quantity is computed by the same code on all three meshes:
- **Δp:** area-weighted static gauge pressure, inlet face minus outlet face (D-031).
- **T_out:** mass-weighted outlet temperature from the Fluent surface integral.
- **Q:** heated-wall heat rate from the Fluent flux report.
- **T_max:** outer-wall facet maximum; the cell-centre maximum is also tabulated.
- **Through-wall ΔT:** circumferential mean of the outer wall minus that of the inner wall.
  - Interpolated linearly between slab centres to **exactly z = 300 mm** and z = 570 mm on every mesh (D-033).
  - The first-slab values (5.0 / 3.3 / 2.2 mm from the inlet) are never compared.
- **Nu_fd and f_fd:** mean over **exactly x/D 18–29**, from local slab values interpolated onto a
  common 2201-point grid.
  - The slab-centre means used in earlier sections cover slightly different windows (x/D 18.25–28.75 coarse, 18.17–28.83 medium, 18.11–29.00 fine).
  - The exact window removes that difference; it changes the values by < 0.03 %.
- **f** = 8 τ_w ρ_b / G². **Nu** = h D / k(T_b) with D = 20 mm.
- **y⁺:** Fluent's wall y⁺ on the conjugate interface faces; area-weighted statistics.

## 4. Checks on the analysis itself

| Check | Result |
|---|---|
| Exact geometric corrections collapse ṁ and Q | ṁ/planar = 8.68694 g/s and Q/lateral = 603.186 W on all three meshes (spread ~10⁻¹² %) |
| Average heat flux on outer wall / bore | 8000.0000 / 16 000.0000 W/m² on every mesh |
| Richardson procedure recovers a known limit | raw ṁ, Q, T_out extrapolate (p = 2.18–2.20) to within 0.004 %, 0.001 %, 0.004 K of the exact circle values |
| Apparent-order solver | converged fixed-point iteration for every monotonic quantity; unequal r handled explicitly |
| Temperatures judged on the rise | GCI on φ − 300 K; extrapolated values shifted back by 300 K |
| Iteration error vs discretisation error | drifts over the last 200 iterations are ≤ 6 × 10⁻⁵ K on every monitored temperature and ≤ 1 × 10⁻⁹ relative on Δp. That is at least 250 times smaller than the smallest mesh change compared (0.016 K on ΔT_wall) and about 10⁴ times smaller than the T_max changes |
| Heated medium f from the profiles equals the value used in the diagnostic | ratio 1.000000 (`f029_decomposition.csv`, `heated_medium_consistency`) |
| F-029 decomposition closes | product of the three factors = 0.896119 = medium f / Section 2 f (exact) |

## 5. Frozen solutions not modified

SHA-256 of 24 files was recorded before the first fine-mesh Fluent launch
(`06_Fluent_CFD/Mesh_Independence/Fine/Audit/frozen_solutions_hashes_before.json`). The files are:
- the medium case, data, results, monitors, profiles, exports and journal;
- the coarse case, data, results, documents, monitors, profiles, exports and journal;
- all three `.msh` files;
- `PROJECT_STATE.md`.

They were re-hashed after the fine run, the isothermal diagnostic and all `mesh_study.py` runs
(`…/frozen_solutions_hashes_after.json`): **24 / 24 identical**. After that check, `PROJECT_STATE.md`
changed in two ways only: its three header status lines were updated and the Section 6B block was
appended. Every other original line is unchanged (`…/project_state_append_check.json`).

The independent number check found that a cloud-side copy of the medium profile
(`06_Fluent_CFD/Profiles/axial_profiles_cfd.csv`, staged on 2026-09-23 during Section 5B) differs
slightly from the file in the project folder. The project-folder file hashes to the recorded
pre-run value `FB851BA9…A7FC`, and so does its copy in `Raw_Data/`. The stale item was the
temporary cloud snapshot, not the frozen file; every number here uses the frozen file.

## 6. Judgements revised during the study (recorded, not hidden)

The first complete run of `mesh_study.py` was reviewed before anything was written up. Five
changes followed. None altered a single CFD number; they change how numbers are judged or shown.

1. **Temperatures judged on their rise above 300 K.** The first run expressed temperature changes as
   % of the absolute temperature. That makes a 1.75 K change look like 0.31 % instead of 0.66 % of
   the rise the CFD actually computes, and it would have flattered the thermal convergence. GCI
   and status now use the rise.
2. **Through-wall ΔT capped at B** (was A). Its changes are small and monotonic (p = 1.37). But the
   apothem estimate attributes about 76 % of the coarse→medium change to geometry. The
   resolution-only steps (+0.006, +0.007 K) do not show a clean trend, so A would have rested on a
   small percentage alone, which the brief forbids.
3. **Geometry-adjusted Δp capped at B** (was A), because the adjustment is itself an estimate.
4. **Outlet Re reclassified D** (was A). It moves only through μ(T_out), which is geometric.
5. **No GCI quoted for geometric quantities (status D).** A GCI on ṁ, Q and T_out would present
   convergence toward the circle as discretisation uncertainty. Their Richardson limits are instead
   compared with the exact circle values, as a check of the procedure.

After the independent number check (a separate reviewer recomputed about 780 figures in the Section 6B
documents against the data files):

6. **Peak-temperature bias for Mechanical now compares raw with raw.** Before, the bulk-corrected
   medium value was compared with the bulk-corrected extrapolation (4.37 K). Mechanical will receive
   the raw medium field, so the raw medium is now compared with the raw extrapolation: 4.44 K, i.e.
   11.5 MPa. Against the bulk-corrected (circle) extrapolation, the raw medium is 4.52 K above. Both
   values are in `downstream_impact.csv`.
7. **F-027 basis corrected.** Section 2's 554.7 K turned out to be a length-averaged mid-wall
   temperature, not an exit-station value (report §8.1).
8. Sixteen further corrections (ten wording or value corrections and six last-digit roundings), none
   affecting a status or the decision:
   - a sign in the fine-results table;
   - the fine solid-node estimate for the Student structural limit;
   - the medium f relative to its limit (2.2 %, not 2.3 %);
   - the range of apparent orders;
   - last-digit rounding.

Presentation fixes (no effect on numbers): captions wrapped to the figure width; the Δp plot's
corrected series relabelled "geometry-adjusted (ESTIMATE)"; mass- and energy-imbalance rows show
no % change (round-off ratios are meaningless).

## 7. Execution record

- `mesh_study.py` runs with the ANSYS-bundled CPython 3.10 from `09_Mesh_Independence/`; the log is
  `mesh_study_log.txt`.
- It was edited in the cloud workspace and copied to the project folder. Four times the copy
  arrived stale (the previous version was still in place).
  - The first time, the hash was printed by the same command that ran the script, so one run used
    the previous version. Its outputs were overwritten by an immediate rerun with the verified file.
  - After that, every run was made conditional on the SHA-256 matching; the other three stale
    copies were caught and **not** run.
- Every output kept in `09_Mesh_Independence/` comes from the final script, SHA-256
  `D2FD8040BDFBE05F68DD6557A567D044004DE54D861B3901706625DED137541B` (51,528 bytes).
- The isothermal diagnostic ran as its own Fluent job (`06_Fluent_CFD/Diagnostics/F029_Isothermal/`)
  with its own audit. It reads the medium case for settings only and writes nothing outside its
  folder.

## 8. How to reproduce

1. Open a PowerShell prompt in `09_Mesh_Independence/`.
2. Run `"C:\Program Files\ANSYS Inc\ANSYS Student\v261\commonfiles\CPython\3_10\winx64\Release\python\python.exe" Scripts\mesh_study.py`.
3. The script rewrites every CSV, JSON and plot in `09_Mesh_Independence/` from the saved CFD
   results. It needs no Fluent licence and runs in under 10 s.

## 9. Not done in this phase, by instruction

- No Mechanical, structural analysis, parametric study or final report.
- Coarse and medium were not rerun; their results are unchanged.
