# 06 Simulation Data SQL

A SQLite database, a Python importer, a query library and a validation script built on the **results that are already in this repository** (Fluent CFD, Mechanical thermal-structural and buckling, LS-DYNA 12C nonlinear buckling).

**Status of this folder.** It is a separate follow-on extension, added after the internship period and after the LS-DYNA study. It is not part of the February to May 2025 internship. It runs no solver and adds no new simulation or result: every number is copied from a summary file already published here. As the repository states, all values are from the project's 2026 re-analysis; none is recovered internship data and no experimental data exist.

## Quick start

Needs Python 3.9 or later and SQLite 3.25 or later (window functions). No packages to install: standard library only, so there is no `requirements.txt`. Tested with Python 3.13 and SQLite 3.45.

```bash
cd 06_Simulation_Data_SQL
python import_results.py          # builds database/simulation_results.db (about 230 KB, a few seconds)
python validate_database.py       # 68 checks, rewrites validation/*.md, exit code 1 on any failure
```

Run one query (the Python route is the tested one; the `sqlite3` command-line route was not available to test here):

```bash
python -c "import sqlite3,sys; c=sqlite3.connect('database/simulation_results.db'); cur=c.execute(open(sys.argv[1]).read()); print([d[0] for d in cur.description]); [print(r) for r in cur]" queries/11_yield_onset_below_one.sql
sqlite3 -header -column database/simulation_results.db < queries/11_yield_onset_below_one.sql    # if the sqlite3 CLI is installed
```

The importer reads only repository files and never modifies them. It builds in a temporary file inside one transaction and replaces the database only if everything succeeded, so running it twice gives a byte-identical file and a failed run leaves an existing database untouched. Use `--repo PATH` and `--db PATH` to change the locations.

## Contents

| Path | Purpose |
|---|---|
| `schema.sql` | tables, constraints, indexes and two views |
| `import_results.py` | repeatable importer (transaction, rollback, duplicate/conflict detection, explicit missing values) |
| `validate_database.py` | independent validation and report writer |
| `data_dictionary.md` | tables, columns, every metric with units and caveat, naming, rules, source-to-table mapping, known source observations |
| `queries/` | 15 SQL files (index below) |
| `validation/VALIDATION_REPORT.md` | passed/failed checks, preserved discrepancies, limitations |
| `validation/QUERY_RUN_LOG.md` | every query executed against the database, with its first result rows |
| `database/` | the generated `.db` goes here; it is not committed (see below) |

## What is in the database

| Table | Rows | Content |
|---|---:|---|
| `source_files` | 22 | repository files read, with SHA-256 |
| `simulation_cases` | 16 | P00 baseline, C00 pipeline control, 6 parametric cases (V/Q/T), LS-DYNA C0 reference and C1/C3/C5, plus 4 planned LS-DYNA cases that were not run |
| `case_parameters` | 64 | velocity, heat flux, wall thickness, diameters, length, inlet temperature; LS-DYNA imperfection amplitude |
| `solver_runs` | 47 | CFD coarse/medium/fine and parametric runs, Mechanical LC1 / LC2 / buckling runs (support S1, S2, S3), LS-DYNA linear cross-check and nonlinear runs |
| `metrics` | 48 | definition, unit and caveat of every stored quantity |
| `simulation_results` | 298 | scalar results, each with unit, source file, source case id and source field |
| `validation_checks` | 116 | convergence and solution statuses recorded by the project, mesh-independence status A to E, import cross-checks, data gaps |

Design points that matter when reading results:

* **Unlike quantities are never mixed.** A linear eigenvalue load (`buck.eig_pcr`), a Southwell characteristic-load estimate (`lsdyna.southwell_ncr`), the maximum load reached in a run (`lsdyna.n_max`) and two different yield-onset factors (`struct.first_yield_factor`, `lsdyna.yield_indicator_lambda`) each have their own `metric_id`. A composite foreign key stops a result's unit from differing from its metric definition.
* **Missing values are explicit.** A result with no value has `value_status` `not_identifiable`, `not_reached` or `not_available` and a reason (for example the C0 Southwell load). Metrics the sources do not provide for a run are listed as `data_gap` checks.
* **Elastic-only results past first-yield indication are flagged.** The LS-DYNA model has no plasticity. Each LS-DYNA state beyond the source's own VM/S_y(T) = 1 indicator carries `physical_validity = 'beyond_yield_elastic_model_not_physical'`. That is a model output, not validated physical behaviour. Rule: `data_dictionary.md` section 6.
* **Source discrepancies are preserved, not resolved** (one found: below).

## Query library

| File | Question |
|---|---|
| `01_cfd_mesh_comparison` | coarse / medium / fine comparison with % change and the project's mesh-independence status |
| `02_baseline_cfd_summary` | baseline CFD results with run context and provenance |
| `03_pressure_drop_comparison` | pressure drop across all CFD design cases, ranked, vs baseline |
| `04_heat_transfer_outlet_temperature` | heat rate, outlet temperature and bulk rise across cases |
| `05_max_structural_stress_ranking` | maximum von Mises stress ranked within LC1 and LC2 |
| `06_lc1_vs_lc2` | LC1 versus LC2 per case |
| `07_support_condition_buckling` | S1 / S2 / S3 eigenvalue buckling against first yield |
| `08_lsdyna_imperfection_sensitivity` | effect of imperfection amplitude vs the perfect path |
| `09_mechanical_eigenvalue_vs_lsdyna_southwell` | Mechanical eigenvalue load vs LS-DYNA estimates (three different quantities, listed separately) |
| `10_southwell_vs_max_load_reached` | Southwell estimate vs maximum load reached, with the nature of each maximum |
| `11_yield_onset_below_one` | recorded yield-onset factors below 1.0 |
| `12a_validation_check_summary` | validation records by origin, status and family |
| `12b_missing_data_report` | results not reported, data gaps, runs not made |
| `13_buckling_factor_below_one` | eigenvalue buckling factors below 1.0 |
| `14_source_provenance` | which file supports how many records |

Features used: CTEs, window functions (`RANK`), conditional aggregation pivots, correlated subqueries, self-joins, set operations, string functions, and the views `v_results` and `v_lsdyna_case_summary`.

## Results the queries show (from the stored data)

* Baseline mesh study: pressure drop changes by +0.236 % (coarse to medium) and +0.227 % (medium to fine); the source rates it B. Heat rate and outlet temperature are rated D because most of their raw change is polygon geometry.
* Support cases: lambda1 is 1.10805 (S1), 2.23224 (S3), 4.29995 (S2); the first-yield factor is 1.730 in all three, so S1 is stability-limited and S2, S3 yield-limited in the idealised model.
* LS-DYNA Southwell estimates are 612.3, 611.1 and 607.7 kN for A = 0.1, 0.6, 1.2 mm, within +0.7 % and -0.1 % of the Mechanical eigenvalue load 608.25 kN. The maximum loads actually reached are 601.0 kN (C1, an interior maximum at lambda 1.185), 572.4 and 545.3 kN (C3, C5: end of analysis, N still rising). All three occur after the elastic model's own yield indicator, so they are model outputs only.
* The only recorded yield-onset factor below 1.0 is LS-DYNA C5 (0.9738). Eigenvalue factors below 1.0 occur for Q03_HIGH (0.98834) and T01_THIN (0.94497).

## Validation

`validate_database.py` checks schema and referential integrity, record counts and duplicates, units and missing-value rules, a privacy scan of all stored text, source-file existence and hashes (also against `MANIFEST.csv`), every stored result against the source cell it cites (exact equality), 104 key values against `MASTER_PROJECT_DATA.csv`, values against raw Fluent audit reports, raw eigenvalue files and raw reaction files, reproducibility (two rebuilds), rollback on injected failures, and that every query runs. During development it was also run against deliberately altered copies of the database (changed values, units, source rows, validity flags) to confirm that it fails when it should; that test is not part of the committed script. Result: **68 passed, 0 failed**. Details, tolerances and their justification: `validation/VALIDATION_REPORT.md`.

## Limitations and open points

* **Re-analysis data, no experiments.** "Validated" here means consistent with the repository's own sources.
* **Raw nodal exports and LS-DYNA binary files are not in the repository**, so maximum stresses and LS-DYNA peak values cannot be recomputed from raw data; they are checked against summary files, the register and extracts.
* **One source discrepancy is kept for review:** for C1 the maximum load is at lambda 1.185 in the summary table, the full-precision JSON and the binout N file, and at lambda 1.19 in the extracted series file, one 0.005 load step away on a flat maximum (N within 3 N).
* **`MANIFEST.csv` hashes do not match files in a git clone** for text files that had Windows CRLF line endings, because git stores LF. Content is otherwise identical (checked). This folder records the hash of the bytes actually read.
* **Not imported:** geometry-corrected estimate rows, Richardson/GCI values, the structural mesh-variant study, higher buckling modes, and all raw solver data.
* **The database file is not committed.** It is small (about 230 KB) and checked for private paths and credentials, but it is a binary that cannot be reviewed as a diff, is fully reproducible by the commands above, and the repository's `NOTICE.md` (section 3) records that the redistribution terms of solver-derived data have not been confirmed. The query results are in `validation/QUERY_RUN_LOG.md`.
* This folder is not listed in `MANIFEST.csv` or `REPOSITORY_STRUCTURE.md` (which still says there is no 06 folder); those documents were left unchanged.
