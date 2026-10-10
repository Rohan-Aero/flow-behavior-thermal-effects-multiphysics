-- Simulation results database for the flow-behaviour / thermal-effects multiphysics project.
-- SQLite 3. Created by import_results.py (executed with PRAGMA foreign_keys = ON).
--
-- Grain:  simulation_cases  1 engineering case (design point or LS-DYNA imperfection variant)
--         solver_runs       1 solver run of a case (CFD mesh level / structural load case + support / LS-DYNA run)
--         simulation_results 1 scalar result of a run, identified by a metric_id with fixed units
-- Every result keeps its source file, source case identifier and source field.

PRAGMA user_version = 1;

CREATE TABLE source_files (
    source_file_id INTEGER PRIMARY KEY,
    repo_path      TEXT NOT NULL UNIQUE
                   CHECK (repo_path NOT LIKE '/%' AND repo_path NOT LIKE '%\%' AND repo_path NOT LIKE '%:%'),
    file_role      TEXT NOT NULL
                   CHECK (file_role IN ('result_summary','case_definition','run_record','master_register','documentation')),
    sha256         TEXT NOT NULL CHECK (length(sha256) = 64),
    size_bytes     INTEGER NOT NULL CHECK (size_bytes >= 0)
);

CREATE TABLE simulation_cases (
    case_id        INTEGER PRIMARY KEY,
    case_code      TEXT NOT NULL UNIQUE,
    case_group     TEXT NOT NULL
                   CHECK (case_group IN ('baseline','pipeline_control','parametric','lsdyna_imperfection')),
    parent_case_id INTEGER REFERENCES simulation_cases (case_id),
    description    TEXT NOT NULL,
    case_status    TEXT NOT NULL CHECK (case_status IN ('reference','solved','not_run')),
    source_file_id INTEGER NOT NULL REFERENCES source_files (source_file_id),
    source_case_id TEXT NOT NULL
);

CREATE TABLE case_parameters (
    case_id        INTEGER NOT NULL REFERENCES simulation_cases (case_id),
    parameter      TEXT NOT NULL,
    value          REAL,
    value_text     TEXT,
    units          TEXT NOT NULL,
    source_file_id INTEGER NOT NULL REFERENCES source_files (source_file_id),
    source_field   TEXT NOT NULL,
    PRIMARY KEY (case_id, parameter),
    CHECK ((value IS NULL) <> (value_text IS NULL))
) WITHOUT ROWID;

CREATE TABLE solver_runs (
    run_id            INTEGER PRIMARY KEY,
    case_id           INTEGER NOT NULL REFERENCES simulation_cases (case_id),
    run_code          TEXT NOT NULL UNIQUE,
    solver            TEXT NOT NULL CHECK (solver IN ('ANSYS Fluent','ANSYS Mechanical','LS-DYNA')),
    solver_version    TEXT NOT NULL,
    analysis_type     TEXT NOT NULL
                      CHECK (analysis_type IN ('cfd_conjugate_steady','static_structural_thermal',
                                               'linear_eigenvalue_buckling','nonlinear_implicit_thermal_buckling')),
    load_case         TEXT CHECK (load_case IN ('LC1','LC2')),
    support_condition TEXT CHECK (support_condition IN ('S1','S2','S3')),
    mesh_level        TEXT CHECK (mesh_level IN ('coarse','medium','fine')),   -- CFD mesh study only
    n_cells           INTEGER CHECK (n_cells > 0),
    n_nodes           INTEGER CHECK (n_nodes > 0),
    run_status        TEXT NOT NULL,         -- source's own label, or 'not_run'
    converged         INTEGER CHECK (converged IN (0,1)),
    iterations        INTEGER CHECK (iterations > 0),
    model_limitation  TEXT,
    source_file_id    INTEGER NOT NULL REFERENCES source_files (source_file_id),
    source_case_id    TEXT NOT NULL
);
CREATE UNIQUE INDEX ux_solver_runs_identity ON solver_runs
    (case_id, solver, analysis_type, COALESCE(load_case,''), COALESCE(support_condition,''), COALESCE(mesh_level,''));

-- One row per quantity definition. Unlike quantities (a linear eigenvalue load, a Southwell estimate, a maximum
-- load reached, a yield-onset factor, ...) have different metric_ids and are never stored under a shared one.
CREATE TABLE metrics (
    metric_id       TEXT PRIMARY KEY,
    units           TEXT NOT NULL,
    quantity_family TEXT NOT NULL
                    CHECK (quantity_family IN ('cfd_flow','cfd_thermal','cfd_quality','structural_response',
                                               'buckling_eigenvalue','nonlinear_load','nonlinear_response',
                                               'yield_onset')),
    description     TEXT NOT NULL,
    caveat          TEXT,
    UNIQUE (metric_id, units)
);

CREATE TABLE simulation_results (
    result_id         INTEGER PRIMARY KEY,
    run_id            INTEGER NOT NULL REFERENCES solver_runs (run_id),
    metric_id         TEXT NOT NULL,
    units             TEXT NOT NULL,
    value             REAL,
    value_status      TEXT NOT NULL
                      CHECK (value_status IN ('reported','not_identifiable','not_reached','not_available')),
    missing_reason    TEXT,
    physical_validity TEXT NOT NULL DEFAULT 'not_assessed'
                      CHECK (physical_validity IN ('not_assessed','within_elastic_range',
                                                   'beyond_yield_elastic_model_not_physical')),
    source_file_id    INTEGER NOT NULL REFERENCES source_files (source_file_id),
    source_case_id    TEXT NOT NULL,
    source_field      TEXT NOT NULL,
    note              TEXT,
    UNIQUE (run_id, metric_id),
    FOREIGN KEY (metric_id, units) REFERENCES metrics (metric_id, units),   -- units cannot drift from the definition
    CHECK ((value_status = 'reported' AND value IS NOT NULL)
        OR (value_status <> 'reported' AND value IS NULL AND missing_reason IS NOT NULL))
);

CREATE TABLE validation_checks (
    check_id        INTEGER PRIMARY KEY,
    case_id         INTEGER NOT NULL REFERENCES simulation_cases (case_id),
    run_id          INTEGER REFERENCES solver_runs (run_id),
    check_origin    TEXT NOT NULL CHECK (check_origin IN ('source_recorded','import_crosscheck','data_gap')),
    check_name      TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('PASS','FAIL','DISCREPANCY','INFO','NOT_AVAILABLE')),
    source_status   TEXT,          -- the source's own label (e.g. mesh status A-E, 'SOLVED - VALID'), kept verbatim
    observed_value  REAL,
    reference_value REAL,
    tolerance       REAL,
    units           TEXT,
    detail          TEXT NOT NULL,
    source_file_id  INTEGER NOT NULL REFERENCES source_files (source_file_id)
);
CREATE UNIQUE INDEX ux_validation_checks_identity ON validation_checks (case_id, COALESCE(run_id,0), check_name);

CREATE INDEX ix_case_parameters_name   ON case_parameters (parameter, value);
CREATE INDEX ix_runs_case              ON solver_runs (case_id);
CREATE INDEX ix_runs_type              ON solver_runs (solver, analysis_type);
CREATE INDEX ix_results_metric_value   ON simulation_results (metric_id, value);
CREATE INDEX ix_results_status         ON simulation_results (value_status);
CREATE INDEX ix_checks_status          ON validation_checks (status, check_origin);

-- Flat view used by most queries: one row per result with case, run and metric context.
CREATE VIEW v_results AS
SELECT c.case_code, c.case_group, r.run_code, r.solver, r.analysis_type, r.load_case, r.support_condition,
       r.mesh_level, m.metric_id, m.quantity_family, s.value, s.units, s.value_status, s.missing_reason,
       s.physical_validity, sf.repo_path AS source_file, s.source_case_id, s.source_field, s.note
FROM simulation_results s
JOIN solver_runs  r  ON r.run_id = s.run_id
JOIN simulation_cases c ON c.case_id = r.case_id
JOIN metrics      m  ON m.metric_id = s.metric_id
JOIN source_files sf ON sf.source_file_id = s.source_file_id;

-- One row per LS-DYNA nonlinear case with the distinct load metrics side by side (never merged into one column).
CREATE VIEW v_lsdyna_case_summary AS
SELECT c.case_code,
       MAX(CASE WHEN p.parameter = 'imperfection_amplitude' THEN p.value END) AS amplitude_mm,
       c.case_status,
       MAX(CASE WHEN s.metric_id = 'lsdyna.southwell_ncr'          THEN s.value END) AS southwell_ncr_kn,
       MAX(CASE WHEN s.metric_id = 'lsdyna.southwell_ncr'          THEN s.value_status END) AS southwell_status,
       MAX(CASE WHEN s.metric_id = 'lsdyna.n_max'                  THEN s.value END) AS n_max_kn,
       MAX(CASE WHEN s.metric_id = 'lsdyna.lambda_at_n_max'        THEN s.value END) AS lambda_at_n_max,
       MAX(CASE WHEN s.metric_id = 'lsdyna.n_max_is_interior_max'  THEN s.value END) AS n_max_is_interior,
       MAX(CASE WHEN s.metric_id = 'lsdyna.n_max'                  THEN s.physical_validity END) AS n_max_validity,
       MAX(CASE WHEN s.metric_id = 'lsdyna.yield_indicator_lambda' THEN s.value END) AS yield_indicator_lambda,
       MAX(CASE WHEN s.metric_id = 'lsdyna.yield_indicator_lambda' THEN s.value_status END) AS yield_indicator_status,
       MAX(CASE WHEN s.metric_id = 'lsdyna.yield_indicator_n'      THEN s.value END) AS yield_indicator_n_kn
FROM simulation_cases c
LEFT JOIN case_parameters p ON p.case_id = c.case_id
LEFT JOIN solver_runs r ON r.case_id = c.case_id AND r.solver = 'LS-DYNA'
                       AND r.analysis_type = 'nonlinear_implicit_thermal_buckling'
LEFT JOIN simulation_results s ON s.run_id = r.run_id
WHERE c.case_group = 'lsdyna_imperfection'
GROUP BY c.case_id;
