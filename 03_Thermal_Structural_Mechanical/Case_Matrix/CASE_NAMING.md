# Section 9A: parametric case naming convention (deterministic)

> **RE-ANALYSIS 2026.** Case names are fixed here and used unchanged in every folder, script, table and figure of Sections 9B onward.

## 1. Pattern

`<SERIES><NN>_<LABEL>`

- **SERIES** is one capital letter giving the question and the variable (table below).
- **NN** is a two-digit level index. Within a design series, 01 is the low level, 02 the baseline level (an alias of P00, never re-run) and 03 the high level.
- **LABEL** is a fixed uppercase word: LOW / BASELINE / HIGH / THIN / THICK, or a short description for checks and supports.

| Series | Meaning | Question | Cases |
|---|---|---|---|
| **P** | project baseline (frozen, solved) | reference | P00_BASELINE |
| **C** | pipeline control: P00 re-run through the parametric automation | reference / QA | C00_PIPELINE_CHECK |
| **V** | inlet velocity | A (design / operating) | V01_LOW, V02_BASELINE (= P00), V03_HIGH |
| **Q** | outer-wall heat flux | A | Q01_LOW, Q02_BASELINE (= P00), Q03_HIGH |
| **T** | wall thickness (total heat input held constant) | A | T01_THIN, T02_BASELINE (= P00), T03_THICK |
| **M** | mesh-adequacy check at a geometry extreme | QA | M01_T01_STRUCT_NR5, M02_T03_STRUCT_NR5, M03_T03_CFD_SOLID18 |
| **S** | support / end-restraint scenario at P00 | B (support sensitivity) | S1_LC2_CURRENT, S2_LC2_LATERALLY_GUIDED, S3_LC2_INTERMEDIATE |
| **B** | method benchmark (toy model, not a project result) | QA | B03_S3_TOY_BENCH |

## 2. Analysis suffixes (inside a case folder)

| Suffix | Analysis |
|---|---|
| `_CFD` | Fluent conjugate heat-transfer solution |
| `_LC1` | free thermal expansion (thermal only) |
| `_LC2` | fully axially restrained thermal expansion, with the S1 support unless the case is an S-case |
| `_BK` | linear buckling linked to the case's own LC2 |

Example: `V03_HIGH_LC2`, `S3_LC2_INTERMEDIATE_BK`.

## 3. Folder mapping

```
10_Parametric_Study/
  CFD_Cases/<CASE>/           Case, Data, Audit, Logs, Exports, Profiles, run_summary.json
  Structural_Cases/<CASE>/    Workbench save-as project, Audits (gate, presolve inputs), Solver_Output/<LC1|LC2|BK>/
  Support_Sensitivity/<S-CASE>/   (S3 and B03 only; S1/S2 point to the 8A files)
  Results/                    parametric_results.json, PARAMETRIC_RESULTS.csv (every row with its change from P00)
```

**Rules.**

- Aliases (V02, Q02, T02) have no folder; their rows point to P00.
- A case name never changes after a run. A re-run of a failed case keeps its name and archives the failed attempt as `<CASE>/Attempt_<n>_FAIL/`.
