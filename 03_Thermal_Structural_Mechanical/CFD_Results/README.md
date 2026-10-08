# 10_Parametric_Study/CFD_Results: Section 9B-1 CFD parametric results

> **RE-ANALYSIS 2026.** These are newly generated Fluent results of the re-analysed duct. They are not recovered internship results, and no experimental data exist.

| File | Content |
|---|---|
| `PARAMETRIC_CFD_TABLE.md` | the final table (Case, Variable, Value, Cells, Δp, T_out, Tmax solid, Q, Re, y⁺ max, mass error, energy error, status), plus the change of each case from P00 |
| `PARAMETRIC_CFD_RESULTS.csv` | machine-readable: one row per case (P00 and the 7 cases), every extracted output, and its change from P00 (`*_pct`, `*_dK`) |
| `parametric_cfd_results.json` | full record per case: extracted values, every re-check (gate, audits, convergence, property tables, start-up excursion, y⁺, heat input, exports, mesh) |
| `SCREENING_COMPARISON.md` · `screening_comparison.json` | CFD against the 9A anchored screening. Agreement is not forced; each difference is attributed |
| `Scripts/extract_case.py` | the P00 output definitions, applied identically to P00 and every case |
| `Scripts/c00_compare.py` · `c00_history_compare.py` | C00 reproduction test (tolerances fixed before the run) and full monitor-history comparison |
| `Scripts/post_9B1.py` | builds the tables above and every case's `CASE_RESULTS.md` / `CASE_AUDIT.md` |
| `Verification_9B1/verify_9B1.py` · `verify_9B1_result.json` · `verify_9B1_stdout.txt` | independent verification from the raw files only. It uses a second route (face exports) for every reported quantity, re-diffs the settings snapshots, re-checks the property tables at every iteration, and checks the CSV and table |

Case folders: `../CFD_Cases/<CASE>/`, each with `CASE_RESULTS.md` and `CASE_AUDIT.md`. Geometry: `../Geometry_Checks/`. Meshes: `../Mesh_Checks/`. Driver logs: `../Logs/`.
