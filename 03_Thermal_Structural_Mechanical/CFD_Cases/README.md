# 10_Parametric_Study/CFD_Cases

> **RE-ANALYSIS 2026 — Section 9B-1.** This folder holds the Fluent runs of the approved CFD parametric cases. They are newly generated solutions, not recovered results.

| Folder | Case | Status |
|---|---|---|
| `C00_PIPELINE_CHECK/` | P00 re-run through the parametric automation (control) | converged; reproduces P00 **bit-identically** (see `C00_REPRODUCTION.md`) |
| `V01_LOW/`, `V03_HIGH/` | inlet velocity 21.15 / 25.85 m/s | converged, valid |
| `Q01_LOW/`, `Q03_HIGH/` | outer-wall heat flux 7,200 / 8,800 W/m² | converged, valid |
| `T01_THIN/`, `T03_THICK/` | wall thickness 8 / 12 mm, total heat input held (q″ 8,888.9 / 7,272.7 W/m²) | converged, valid |
| `Journals/` | `solve_param.py` (the single parametric journal), `param_cases.py` (case definitions), `s5_common.py`, `run_param.ps1` / `launch_param.ps1` (drivers), and `Archive/` (the journal version used for C00, plus the diff to the final version) | — |

**Layout of each case folder.**

| Folder or file | Content |
|---|---|
| `Case/`, `Data/` | case and data files: final, end-of-stage-2, and checkpoint |
| `Monitors/` | the 29 monitor reports at every iteration |
| `Audit/` | frozen-physics gate, three setup audits, convergence evaluations, validity checks, Fluent flux and surface-integral reports, run summary |
| `Exports/` | wall, boundary and volume exports |
| `EnSight/` | solid node temperatures (the 7A mapping source for 9B-2) |
| `Logs/` | Fluent stdout, transcript, driver log |
| `CASE_RESULTS.md` | results with the change from P00, validity, screening comparison, output locations |
| `CASE_AUDIT.md` | automation-integrity record: intended vs actual change, unchanged settings, mesh, solver version, convergence, property tables |

The combined tables are in `../CFD_Results/`.
