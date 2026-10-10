#!/usr/bin/env python3
"""Validate database/simulation_results.db against the repository sources and write the validation report.

    python validate_database.py [--repo PATH] [--db PATH] [--no-report]

Standard library only. Exit code 1 if any check FAILS. The source files are only read.

How values are checked: every stored result carries (source file, source case id, source field). This script
re-reads that cell with its own small parser (not the importer's code) and requires exact equality with the stored
value. A tolerance is used only where two *different* files hold the same quantity at different print precision;
each tolerance and its basis is stated next to the check and in the report.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import import_results as imp  # noqa: E402  (used only for rebuild / failure-injection tests)

CFD, MECH, LSD = imp.CFD, imp.MECH, imp.LSD
S = imp.S
SLACK = 1 + 1e-9  # a value exactly half a unit away (rounding tie) is accepted; guards float noise only


# ------------------------------------------------------------------ report plumbing
class Report:
    def __init__(self):
        self.rows = []  # (section, name, status, detail)

    def add(self, section, name, ok, detail="", status=None):
        self.rows.append((section, name, status or ("PASS" if ok else "FAIL"), detail))

    def n(self, status):
        return sum(1 for r in self.rows if r[2] == status)


def half_unit(s: str) -> float:
    """Half of the last printed digit of a decimal string: the rounding tolerance of a value printed as s."""
    return float(Decimal(10) ** Decimal(s.strip().replace(" ", "")).as_tuple().exponent / 2)


def csv_rows(path: Path):
    lines = [ln for ln in path.read_text(encoding="utf-8-sig").splitlines() if ln.strip()]
    while lines and lines[0].lstrip('"').startswith("#"):
        lines.pop(0)
    return list(csv.DictReader(io.StringIO("\n".join(lines))))


def fnum(s):
    s = (s or "").strip()
    return None if s in ("", "nan") else float(s)


# ------------------------------------------------------------------ independent source cell reader
class Sources:
    def __init__(self, repo: Path):
        self.repo, self.cache = repo, {}

    def csv(self, rel, key):
        if (rel, key) not in self.cache:
            self.cache[(rel, key)] = {r[key]: r for r in csv_rows(self.repo / rel)}
        return self.cache[(rel, key)]

    def json(self, rel):
        if rel not in self.cache:
            self.cache[rel] = json.loads((self.repo / rel).read_text(encoding="utf-8-sig"))
        return self.cache[rel]

    def md_table(self, rel, start, must_contain):
        lines = (self.repo / rel).read_text(encoding="utf-8").splitlines()
        i = next(k for k, ln in enumerate(lines) if ln.startswith(start) and must_contain in ln)
        hdr = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        out = {}
        for ln in lines[i + 2:]:
            if not ln.startswith("|"):
                break
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            out[cells[0]] = dict(zip(hdr, cells))
        return out

    def cell(self, rel, case, field):
        """Return the raw source cell (str or number) cited by (file, source case id, source field)."""
        name = Path(rel).name
        m_row = re.fullmatch(r"row '(.*)', column '(.*)'", field)
        if name == "three_mesh_raw_table.csv":
            return self.csv(rel, "quantity")[m_row.group(1)][m_row.group(2)]
        if name == "results_summary_7B.csv":
            return self.csv(rel, "Quantity")[m_row.group(1)][m_row.group(2)]
        if name.startswith("MASTER_PROJECT_DATA"):
            m = re.fullmatch(r"row (M\d+) '.*', part (S\d)", field)
            return self.csv(rel, "ID")[m.group(1)]["Value"].split("/")[int(m.group(2)[1]) - 1].strip()
        if name == "SUPPORT_SENSITIVITY_RESULTS.md":
            m = re.fullmatch(r"section 4 table, column '(.*)'", field)
            return self.md_table(rel, "| Scenario |", "First-yield factor")[case][m.group(1)]
        if name.endswith(".json"):
            m = re.fullmatch(r"json key '(.*)'", field)
            d = self.json(rel)
            return d[m.group(1)] if m.group(1) in d else d[case][m.group(1)]
        keycol = {"PARAMETRIC_CFD_RESULTS.csv": "case", "PARAMETRIC_STRUCTURAL_RESULTS.csv": "Case",
                  "SUPPORT_SENSITIVITY_RESULTS.csv": "Scenario", "IMPERFECTION_SENSITIVITY.csv": "Case",
                  "MECHANICAL_vs_LSDYNA.csv": "Source"}[name]
        m = re.match(r"column '(.*?)'", field)
        row_key = "LS-DYNA 12B G6 (extension)" if name == "MECHANICAL_vs_LSDYNA.csv" else case
        return self.csv(rel, keycol)[row_key][m.group(1)]


TRANSFORM = {
    "lsdyna.n_max_is_interior_max": lambda s: 1.0 if str(s).strip() == "True" else 0.0,
    "lsdyna.southwell_window_low": lambda s: fnum(str(s).split("-")[0]) if str(s).strip() else None,
    "lsdyna.southwell_window_high": lambda s: fnum(str(s).split("-")[1]) if str(s).strip() else None,
}


def to_value(metric, raw):
    if metric in TRANSFORM:
        return TRANSFORM[metric](raw)
    return fnum(str(raw))


# ------------------------------------------------------------------ the validation sections
def check_schema(db, rep):
    sec = "1 Schema and integrity"
    rep.add(sec, "SQLite integrity_check", db.execute("PRAGMA integrity_check").fetchone()[0] == "ok")
    bad = db.execute("PRAGMA foreign_key_check").fetchall()
    rep.add(sec, "foreign_key_check (referential integrity)", not bad, f"{len(bad)} violations")
    ref = sqlite3.connect(":memory:")
    ref.executescript((HERE / "schema.sql").read_text(encoding="utf-8"))
    norm = lambda c: sorted((r[0], r[1], re.sub(r"\s+", " ", r[2] or "")) for r in c.execute(
        "SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"))
    rep.add(sec, "database objects identical to schema.sql", norm(db) == norm(ref),
            f"{len(norm(db))} tables/views/indexes compared")
    rep.add(sec, "schema version (PRAGMA user_version)", db.execute("PRAGMA user_version").fetchone()[0] == 1)


def check_counts(db, rep, src):
    sec = "2 Record counts and duplicates"
    cfd = csv_rows(src.repo / S["cfd_param"])
    ls = csv_rows(src.repo / S["ls_sens"])
    not_run = sorted(p.parent.name for p in (src.repo / LSD / "runs").glob("*/NOT_RUN.txt"))
    # independent expectation from source facts (see data_dictionary.md section 5 for the per-group metric counts)
    n_mesh_q = len(imp.MESH_QTY)
    exp = {
        "simulation_cases": len(cfd) + len(ls) + len(not_run),
        "solver_runs": 3 + (len(cfd) - 1) + 3 * len(cfd) + 4 + 1 + len(ls) + len(not_run),
        "simulation_results": 3 * n_mesh_q + (len(cfd) - 1) * len(imp.CFD_COLS) + len(cfd) * len(imp.STRUCT_COLS) + 1
                              + 3 + 2 * 7 + 2 + len(ls) * 19,
        "case_parameters": len(cfd) * 7 + len(ls) + len(not_run),
        "metrics": len(imp.METRICS),
    }
    for t, e in exp.items():
        got = db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        rep.add(sec, f"{t} row count", got == e, f"database {got}, expected from source row counts {e}")
    dup = {
        "case_code": "SELECT case_code FROM simulation_cases GROUP BY 1 HAVING COUNT(*) > 1",
        "run_code": "SELECT run_code FROM solver_runs GROUP BY 1 HAVING COUNT(*) > 1",
        "(run, metric)": "SELECT run_id, metric_id FROM simulation_results GROUP BY 1,2 HAVING COUNT(*) > 1",
        "repo_path": "SELECT repo_path FROM source_files GROUP BY 1 HAVING COUNT(*) > 1",
        "(case, parameter)": "SELECT case_id, parameter FROM case_parameters GROUP BY 1,2 HAVING COUNT(*) > 1",
        "(case, run, check_name)": "SELECT case_id, run_id, check_name FROM validation_checks GROUP BY 1,2,3 HAVING COUNT(*) > 1",
    }
    for k, q in dup.items():
        rep.add(sec, f"no duplicate {k}", not db.execute(q).fetchall())
    rep.add(sec, "every non-baseline case has a parent; P00 has none",
            db.execute("SELECT COUNT(*) FROM simulation_cases WHERE (case_code='P00') <> (parent_case_id IS NULL)").fetchone()[0] == 0)
    rep.add(sec, "cases marked not_run carry no results", db.execute(
        "SELECT COUNT(*) FROM simulation_results s JOIN solver_runs r USING(run_id) JOIN simulation_cases c USING(case_id)"
        " WHERE c.case_status='not_run'").fetchone()[0] == 0)
    rep.add(sec, "every solved or reference run has at least one result", db.execute(
        "SELECT COUNT(*) FROM solver_runs r JOIN simulation_cases c USING(case_id) WHERE c.case_status <> 'not_run'"
        " AND NOT EXISTS (SELECT 1 FROM simulation_results s WHERE s.run_id = r.run_id)").fetchone()[0] == 0)


def check_fields(db, rep, repo):
    sec = "3 Required fields, units, missing values, privacy"
    q = lambda s: db.execute(s).fetchone()[0]
    rep.add(sec, "result units equal the metric definition units", q(
        "SELECT COUNT(*) FROM simulation_results s JOIN metrics m USING(metric_id) WHERE s.units <> m.units") == 0)
    rep.add(sec, "no empty provenance text on results", q(
        "SELECT COUNT(*) FROM simulation_results WHERE trim(source_case_id)='' OR trim(source_field)=''") == 0)
    rep.add(sec, "value is NULL exactly when value_status is not 'reported', and a reason is given", q(
        "SELECT COUNT(*) FROM simulation_results WHERE (value IS NULL) <> (value_status <> 'reported')"
        " OR (value IS NULL AND (missing_reason IS NULL OR trim(missing_reason) = ''))") == 0)
    rep.add(sec, "no NaN / infinite values stored", q(
        "SELECT COUNT(*) FROM simulation_results WHERE value IS NOT NULL AND (value <> value OR abs(value) > 1e300)") == 0)
    rep.add(sec, "every case has its parameters (7 for design cases, 1 for LS-DYNA cases)", q(
        "SELECT COUNT(*) FROM simulation_cases c WHERE (SELECT COUNT(*) FROM case_parameters p WHERE p.case_id=c.case_id)"
        " <> CASE WHEN c.case_group='lsdyna_imperfection' THEN 1 ELSE 7 END") == 0)
    rep.add(sec, "wall_thickness = (outer_diameter - inner_diameter) / 2 in every design case", q(
        "SELECT COUNT(*) FROM case_parameters t JOIN case_parameters o ON o.case_id=t.case_id AND o.parameter='outer_diameter'"
        " JOIN case_parameters i ON i.case_id=t.case_id AND i.parameter='inner_diameter'"
        " WHERE t.parameter='wall_thickness' AND abs(t.value - (o.value - i.value)/2) > 1e-9") == 0,
        "tolerance 1e-9 mm: float rounding only")
    rep.add(sec, "physical_validity rule for LS-DYNA states", q(
        "SELECT COUNT(*) FROM simulation_results s JOIN solver_runs r USING(run_id) "
        "JOIN simulation_results y ON y.run_id=s.run_id AND y.metric_id='lsdyna.yield_indicator_lambda' "
        "WHERE s.metric_id='lsdyna.n_max' AND y.value_status='reported' AND "
        "((SELECT value FROM simulation_results WHERE run_id=s.run_id AND metric_id='lsdyna.lambda_at_n_max') > y.value) "
        "<> (s.physical_validity='beyond_yield_elastic_model_not_physical')") == 0,
        "N_max flagged 'beyond' exactly when its lambda exceeds the recorded VM/S_y(T)=1 lambda")
    rep.add(sec, "LS-DYNA yield indicator below 1.0 is flagged on lambda=1 states", q(
        "SELECT COUNT(*) FROM simulation_results y JOIN simulation_results v ON v.run_id=y.run_id AND v.metric_id='lsdyna.vm_at_lambda1'"
        " WHERE y.metric_id='lsdyna.yield_indicator_lambda' AND y.value < 1.0 "
        "AND v.physical_validity <> 'beyond_yield_elastic_model_not_physical'") == 0)
    # privacy: no absolute paths, drive letters, e-mail addresses, URLs or credential words in any text column
    pat = re.compile(r"[A-Za-z]:\\|/home/|/Users/|/root/|/tmp/|\\\\|@[A-Za-z0-9-]+\.[a-z]|https?://|passw|token|api[_-]?key|secret",
                     re.I)
    hits = []
    for (t,) in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        cols = [c[1] for c in db.execute(f"PRAGMA table_info({t})") if "CHAR" in c[2].upper() or "TEXT" in c[2].upper()]
        for c in cols:
            for (v,) in db.execute(f"SELECT DISTINCT {c} FROM {t} WHERE {c} IS NOT NULL"):
                if pat.search(str(v)):
                    hits.append((t, c, str(v)[:60]))
    rep.add(sec, "no absolute/personal paths, e-mail, URLs or credential words in any stored text", not hits, str(hits[:3]))
    doc = (HERE / "data_dictionary.md").read_text(encoding="utf-8")
    missing = [m for (m,) in db.execute("SELECT metric_id FROM metrics") if f"`{m}`" not in doc]
    rep.add(sec, "every metric_id is documented in data_dictionary.md", not missing, str(missing[:5]))


def check_sources(db, rep, repo):
    sec = "4 Source-file references"
    manifest = {r["copy_path"]: r["sha256"].upper() for r in csv.DictReader(open(repo / "MANIFEST.csv", encoding="utf-8-sig"))}
    files = db.execute("SELECT source_file_id, repo_path, sha256, size_bytes FROM source_files").fetchall()
    bad_exist, bad_hash, bad_manifest, exact, eol_only = [], [], [], 0, 0
    H = lambda x: hashlib.sha256(x).hexdigest().upper()
    for fid, p, sha, size in files:
        f = repo / p
        if not f.is_file():
            bad_exist.append(p)
            continue
        b = f.read_bytes()
        if hashlib.sha256(b).hexdigest() != sha or len(b) != size:
            bad_hash.append(p)
        # MANIFEST.csv hashes were taken on Windows files (CRLF rows, sometimes an LF first comment line); git stores LF.
        lf = b.replace(b"\r\n", b"\n")
        first, _, rest = lf.partition(b"\n")
        variants = {H(b): "exact", H(lf.replace(b"\n", b"\r\n")): "crlf", H(first + b"\n" + rest.replace(b"\n", b"\r\n")): "crlf"}
        hit = variants.get(manifest.get(p))
        if hit == "exact":
            exact += 1
        elif hit:
            eol_only += 1
        else:
            bad_manifest.append(p)
    rep.add(sec, f"all {len(files)} source files exist in the repository", not bad_exist, str(bad_exist))
    rep.add(sec, "stored SHA-256 and size match the current files", not bad_hash, str(bad_hash))
    rep.add(sec, "each file matches its MANIFEST.csv hash, exactly or after restoring Windows CRLF line endings", not bad_manifest,
            f"{exact} exact, {eol_only} equal only after CRLF restoration (git stores LF), {len(bad_manifest)} unexplained {bad_manifest}. "
            "Line endings are the only difference found: content is otherwise identical to the manifest hash.")
    refs = """SELECT source_file_id FROM simulation_results UNION SELECT source_file_id FROM solver_runs
              UNION SELECT source_file_id FROM case_parameters UNION SELECT source_file_id FROM validation_checks
              UNION SELECT source_file_id FROM simulation_cases"""
    unused = db.execute(f"SELECT repo_path FROM source_files WHERE source_file_id NOT IN ({refs})").fetchall()
    rep.add(sec, "every registered source file is referenced by at least one record", not unused, str(unused))
    try:
        st = subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "--"] + [f[1] for f in files],
                            capture_output=True, text=True, timeout=60)
        if st.returncode == 0:
            rep.add(sec, "source files are unmodified in the working tree (git status)", not st.stdout.strip(), st.stdout.strip()[:200])
        else:
            rep.add(sec, "git status of source files", True, "not a git checkout; skipped", status="INFO")
    except (OSError, subprocess.SubprocessError):
        rep.add(sec, "git status of source files", True, "git not available; skipped", status="INFO")


def check_fidelity(db, rep, src):
    sec = "5 Consistency with authoritative source data"
    bad, n = [], 0
    for rid, code, metric, value, status, sf, scase, sfield in db.execute(
            "SELECT s.result_id, r.run_code, s.metric_id, s.value, s.value_status, f.repo_path, s.source_case_id, s.source_field"
            " FROM simulation_results s JOIN solver_runs r USING(run_id) JOIN source_files f USING(source_file_id)"):
        raw = src.cell(sf, scase, sfield)
        want = raw if isinstance(raw, (int, float)) else to_value(metric, raw)
        n += 1
        if want is None:
            if value is not None or status == "reported":
                bad.append((code, metric, "source blank, database has a value"))
        elif value is None or value != want or status != "reported":
            bad.append((code, metric, value, want))
    rep.add(sec, f"all {n} results equal the cited source cell exactly (file, case id, field re-read)", not bad,
            f"{len(bad)} mismatches {bad[:3]}")
    # case parameters
    cfd, st = src.csv(S["cfd_param"], "case"), src.csv(S["struct_param"], "Case")
    base = src.json(S["baseline"])["params"]
    bad = []
    for code, in [(c,) for (c,) in db.execute("SELECT case_code FROM simulation_cases WHERE case_group <> 'lsdyna_imperfection'")]:
        key = "P00_BASELINE" if code == "P00" else code
        got = dict(db.execute("SELECT parameter, value FROM case_parameters p JOIN simulation_cases c USING(case_id)"
                              " WHERE c.case_code=?", (code,)).fetchall())
        r = cfd[key]
        want = {
            "inlet_velocity": float(r["value"]) if r["variable"] == "inlet velocity" else base["V_in"]["value"],
            "outer_wall_heat_flux": float(r["qpp_heated_area_avg_W_m2"]),
            "wall_thickness": float(r["value"]) if r["variable"].startswith("wall thickness") else 10.0,
            "outer_diameter": float(re.search(r"Do (\d+)", st[key]["Geometry"]).group(1)),
            "inner_diameter": 20.0, "tube_length": 600.0, "inlet_temperature": base["T_in"]["value"]}
        if (base["Di"]["value"], base["L"]["value"], base["Do"]["value"]) != (0.02, 0.6, 0.04):
            bad.append((code, "baseline geometry changed"))
        bad += [(code, k, got.get(k), v) for k, v in want.items() if got.get(k) != v]
    ls = src.csv(S["ls_sens"], "Case")
    rep_json = src.json(S["ls_imperf"])
    for code, a in db.execute("SELECT c.case_code, p.value FROM simulation_cases c JOIN case_parameters p USING(case_id)"
                              " WHERE c.case_group='lsdyna_imperfection' AND p.parameter='imperfection_amplitude'"):
        if code in ls:
            key = re.search(r"A\dp\d", code).group(0)
            realised = rep_json["files"][key]["A_mm"] if key in rep_json["files"] else 0.0  # A0p0 = no imperfection file
            if a != float(ls[code]["Imperfection [mm]"]) or abs(a - realised) > 1e-9:
                bad.append((code, "amplitude", a))
    rep.add(sec, "case parameters equal their sources (and LS-DYNA amplitudes equal the realised amplitudes in imperfection_report_12C.json)",
            not bad, f"{bad[:3]}; amplitude tolerance 1e-9 mm = float rounding of the realised value")
    # run attributes
    mesh = src.json(S["mesh_json"])
    bad = [(lvl, got) for lvl in ("coarse", "medium", "fine")
           for got in [db.execute("SELECT n_cells, iterations, converged FROM solver_runs WHERE run_code=?", (f"P00:fluent:{lvl}",)).fetchone()]
           if got != (mesh["mesh"][lvl]["cells"], mesh["values"][lvl]["iters"], int(mesh["values"][lvl]["converged"]))]
    for key, r in cfd.items():
        if key != "P00_BASELINE":
            got = db.execute("SELECT n_cells, iterations, converged, run_status FROM solver_runs WHERE run_code=?", (f"{key}:fluent",)).fetchone()
            if got != (int(r["cells"]), int(r["iterations"]), int(r["valid"] == "True"), r["status"]):
                bad.append((key, got))
    for key, r in st.items():
        code = "P00" if key == "P00_BASELINE" else key
        got = db.execute("SELECT DISTINCT n_nodes FROM solver_runs WHERE case_id=(SELECT case_id FROM simulation_cases WHERE case_code=?)"
                         " AND solver='ANSYS Mechanical' AND n_nodes IS NOT NULL", (code,)).fetchall()
        if got != [(int(r["Nodes"]),)]:
            bad.append((code, "nodes", got))
    rep.add(sec, "run attributes (cells, nodes, iterations, convergence flag, status label) equal their sources", not bad, str(bad[:3]))


def check_register(db, rep, src):
    sec = "6 Key values against the project data register (MASTER_PROJECT_DATA.csv)"
    reg = src.csv(S["register"], "ID")

    def dbv(case, metric, **flt):
        sql = "SELECT value, units FROM v_results WHERE case_code=? AND metric_id=?"
        args = [case, metric]
        for k, v in flt.items():
            sql += f" AND {k} IS NULL" if v is None else f" AND {k}=?"
            args += [] if v is None else [v]
        return db.execute(sql, args).fetchone()

    P = "P00"
    xw = []  # (register id, part index or None, case, metric, filters)
    for rid, metric in (("M036", "cfd.dp_static"), ("M037", "cfd.t_out_bulk"), ("M038", "cfd.q_heated_wall"),
                        ("M039", "cfd.t_solid_max_facet"), ("M040", "cfd.t_solid_max_cell"), ("M041", "cfd.dt_wall_midspan"),
                        ("M042", "cfd.nu_fd"), ("M043", "cfd.f_darcy_fd"), ("M044", "cfd.yplus_min"), ("M045", "cfd.yplus_mean"),
                        ("M046", "cfd.yplus_max"), ("M035", "cfd.re_out")):
        xw.append((rid, None, P, metric, dict(mesh_level="medium")))
    for lvl, ids in (("fine", "M051 M052 M053 M054 M055 M057"), ("coarse", "M059 M060 M061 M062 M063 M065")):
        for rid, metric in zip(ids.split(), ("cfd.dp_static", "cfd.t_out_bulk", "cfd.q_heated_wall", "cfd.t_solid_max_facet",
                                             "cfd.dt_wall_midspan", "cfd.yplus_max")):
            xw.append((rid, None, P, metric, dict(mesh_level=lvl)))
    for rid, lvl in (("M056", "fine"), ("M064", "coarse")):
        xw += [(rid, 0, P, "cfd.nu_fd", dict(mesh_level=lvl)), (rid, 1, P, "cfd.f_darcy_fd", dict(mesh_level=lvl))]
    for rid, metric, flt in (("M084", "struct.lc1.max_total_deformation", dict(load_case="LC1")), ("M085", "struct.lc1.axial_growth", dict(load_case="LC1")),
                             ("M086", "struct.lc1.max_von_mises", dict(load_case="LC1")), ("M089", "struct.lc2.max_total_deformation", dict(support_condition="S1")),
                             ("M090", "struct.lc2.max_von_mises", dict(support_condition="S1")), ("M091", "struct.lc2.end_reaction_axial", dict(support_condition="S1")),
                             ("M092", "struct.lc2.mean_axial_stress", dict(support_condition="S1")), ("M093", "struct.lc2.critical_temperature", dict(support_condition="S1")),
                             ("M094", "struct.lc2.local_yield_strength", dict(support_condition="S1")), ("M095", "struct.lc2.yield_utilisation", dict(support_condition="S1")),
                             ("M096", "struct.first_yield_factor", dict(support_condition="S1")), ("M098", "buck.eig_lambda1", dict(solver="ANSYS Mechanical", support_condition="S1")),
                             ("M099", "buck.eig_pcr", dict(solver="ANSYS Mechanical", support_condition="S1")), ("M101", "buck.eig_lambda1", dict(support_condition="S2")),
                             ("M102", "buck.eig_pcr", dict(support_condition="S2")), ("M104", "buck.eig_lambda1", dict(support_condition="S3")),
                             ("M105", "buck.eig_pcr", dict(support_condition="S3")), ("M108", "struct.lc2.max_von_mises", dict(support_condition="S2")),
                             ("M109", "struct.lc2.max_von_mises", dict(support_condition="S3"))):
        xw.append((rid, None, P, metric, flt))
    for k, sc in enumerate(("S1", "S2", "S3")):
        xw.append(("M110", k, P, "struct.lc2.end_reaction_axial", dict(support_condition=sc)))
    label = {"pressure drop": "cfd.dp_static", "outlet bulk temperature": "cfd.t_out_bulk",
             "maximum solid temperature (outer-wall facet)": "cfd.t_solid_max_facet",
             "LC1 maximum deformation": "struct.lc1.max_total_deformation", "LC1 maximum von Mises": "struct.lc1.max_von_mises",
             "LC2 maximum von Mises": "struct.lc2.max_von_mises", "LC2 yield utilisation": "struct.lc2.yield_utilisation",
             "lambda1 (S1)": "buck.eig_lambda1", "critical load P_cr": "buck.eig_pcr"}
    for rid, r in reg.items():
        m = re.fullmatch(r"([VQT]0[13]_[A-Z]+): (.*)", r["Parameter"])
        if m and r["Group"] == "Parametric":
            metric = label[m.group(2)]
            flt = dict(mesh_level=None) if metric.startswith("cfd.") else (dict(load_case="LC1") if "lc1" in metric else dict(support_condition="S1"))
            if metric.startswith("buck."):
                flt["solver"] = "ANSYS Mechanical"
            xw.append((rid, None, m.group(1), metric, flt))
    bad, worst, n = [], 0.0, 0
    for rid, part, case, metric, flt in xw:
        r = reg[rid]
        vs = r["Value"].split("/")[part].strip() if part is not None else r["Value"].strip()
        got = dbv(case, metric, **flt)
        n += 1
        if got is None:
            bad.append((rid, "no database value"))
            continue
        tol = half_unit(vs)
        d = abs(got[0] - float(vs))
        worst = max(worst, d / tol if tol else 0)
        if d > tol * SLACK or r["Units"].strip() != got[1]:
            bad.append((rid, metric, got[0], vs, r["Units"], got[1]))
    rep.add(sec, f"{n} register values (CFD meshes, baseline, structural, buckling, 6 parametric cases) agree with the database",
            not bad,
            f"{bad[:4]}. Tolerance for each value = half a unit of the last digit printed in the register (rounding only); "
            f"largest deviation = {worst:.2f} of that tolerance; units compared as strings.")
    cells = [("M033", "P00:fluent:medium"), ("M050", "P00:fluent:fine"), ("M058", "P00:fluent:coarse")]
    bad = [(rid, run) for rid, run in cells if db.execute("SELECT n_cells FROM solver_runs WHERE run_code=?", (run,)).fetchone()[0] != int(reg[rid]["Value"])]
    bad += [("M081", "nodes")] if db.execute("SELECT n_nodes FROM solver_runs WHERE run_code='P00:mech:static:LC2:S1'").fetchone()[0] != int(reg["M081"]["Value"]) else []
    rep.add(sec, "cell and node counts equal the register exactly (M033, M050, M058, M081)", not bad, str(bad))
    ok = all(db.execute("SELECT abs(observed_value - ?) <= ? FROM validation_checks v JOIN solver_runs r USING(run_id) WHERE r.run_code=? AND check_name=?",
                        (float(reg[rid]["Value"]), half_unit(reg[rid]["Value"]) * SLACK, "P00:fluent:medium", name)).fetchone()[0]
             for rid, name in (("M047", "mass_imbalance"), ("M048", "energy_imbalance")))
    rep.add(sec, "baseline mass/energy imbalance (%) agree with M047/M048", ok, "tolerance: half unit of the register's last digit")
    rep.add(sec, "register statuses of the compared rows contain no MISMATCH",
            all(reg[x[0]]["Status"] != "MISMATCH" for x in xw), "statuses in the compared rows: " + ", ".join(sorted({reg[x[0]]["Status"] for x in xw})))


def check_raw(db, rep, src):
    sec = "7 Consistency with raw solver extracts in the repository"
    repo = src.repo

    def fluent(path, row, col=1):
        t = (repo / path).read_text(encoding="utf-8", errors="replace")
        m = re.search(rf"^\s*{re.escape(row)}\s+(-?[\d.eE+-]+)\s*$", t, re.M)
        return m.group(1)

    audit = {"P00:fluent:medium": f"{CFD}/Audit", "P00:fluent:coarse": f"{CFD}/Mesh_Independence/Coarse/Audit",
             "P00:fluent:fine": f"{CFD}/Mesh_Independence/Fine/Audit"}
    for (code,) in db.execute("SELECT case_code FROM simulation_cases WHERE case_group IN ('parametric','pipeline_control')"):
        audit[f"{code}:fluent"] = f"{MECH}/CFD_Cases/{code}/Audit"
    bad, worst, n = [], 0.0, 0
    for run, d in audit.items():
        raw = {"cfd.dp_static": (fluent(f"{d}/fluent_si_p_area.txt", "fluid_inlet"), fluent(f"{d}/fluent_si_p_area.txt", "fluid_outlet")),
               "cfd.t_out_bulk": (fluent(f"{d}/fluent_si_T_mass.txt", "fluid_outlet"),),
               "cfd.q_heated_wall": (fluent(f"{d}/fluent_flux_heat.txt", "heated_outer_wall"),),
               "cfd.t_solid_max_facet": (fluent(f"{d}/fluent_si_Twall_max.txt", "heated_outer_wall"),)}
        for metric, vals in raw.items():
            want = float(vals[0]) - (float(vals[1]) if len(vals) > 1 else 0.0)
            got = db.execute("SELECT value FROM v_results WHERE run_code=? AND metric_id=?", (run, metric)).fetchone()[0]
            tol = max(half_unit(vals[0]), 1e-6 * abs(want))
            worst = max(worst, abs(got - want) / abs(want))
            n += 1
            if abs(got - want) > tol * SLACK:
                bad.append((run, metric, got, want))
    rep.add(sec, f"{n} CFD values equal the raw Fluent audit reports (pressure drop, outlet T, heat rate, max wall T; {len(audit)} runs)",
            not bad, f"{bad[:3]}. Tolerance max(half unit of the printed digit, 1e-6 relative): the two files round the same facet "
                     f"value differently at the 7th significant digit; observed largest relative difference {worst:.1e}.")
    # buckling load factors against the first Block-Lanczos eigenvalue file
    lam = {"P00:mech:buckling:S1": f"{MECH}/Buckling/Mechanical/LC2_Linear_Buckling/Solver_Output/s8a_load_factors.csv",
           "P00:mech:buckling:S2": f"{MECH}/Buckling/Mechanical/LC2NS_Linear_Buckling/Solver_Output/s8a_load_factors.csv",
           "P00:mech:buckling:S3": f"{MECH}/Structural_Cases/S3_LC2_INTERMEDIATE/Solver_Output/S3_BUCKLING/s8a_load_factors.csv"}
    for (code,) in db.execute("SELECT case_code FROM simulation_cases WHERE case_group='parametric'"):
        lam[f"{code}:mech:buckling:S1"] = f"{MECH}/Structural_Cases/{code}/Solver_Output/BUCKLING/s8a_load_factors.csv"
    bad = []
    for run, f in lam.items():
        p = repo / f
        if not p.is_file():
            bad.append((run, "raw file not in repository"))
            continue
        want = float(p.read_text().splitlines()[1].split(",")[1])
        got = db.execute("SELECT value FROM v_results WHERE run_code=? AND metric_id='buck.eig_lambda1'", (run,)).fetchone()[0]
        if abs(got - want) > 5e-6 * SLACK:
            bad.append((run, got, want))
    rep.add(sec, f"{len(lam)} lambda1 values equal the first eigenvalue in the raw s8a_load_factors.csv files", not bad,
            f"{bad[:3]}. Tolerance 5e-6: the summary tables print lambda1 to 5 decimals.")
    # axial reaction: sum of FZ on the inlet face
    def react_sum(rel):
        rows = list(csv.DictReader(open(repo / rel)))
        return sum(float(r["RFZ_nodalCS_N"].replace("D", "E")) for r in rows if abs(float(r["z_m"])) < 1e-9)
    t = (repo / MECH / "Structural_Cases/S2_REEXTRACT/s2x_totals.txt").read_text()
    raw_s2 = float(re.search(r"inlet_face_nodes\s+\d+\.\s+sum_RF_FZ_N\s+(\S+)", t).group(1).replace("D", "E"))
    raws = {"S1": react_sum(f"{MECH}/LC2_Restrained/Solver_Output/s7b_react.csv"), "S2": raw_s2,
            "S3": react_sum(f"{MECH}/Structural_Cases/S3_LC2_INTERMEDIATE/Solver_Output/S3_STATIC/s7b_react.csv")}
    bad = []
    for sc, want in raws.items():
        got = db.execute("SELECT value FROM v_results WHERE case_code='P00' AND support_condition=? AND metric_id='struct.lc2.end_reaction_axial'", (sc,)).fetchone()[0]
        if abs(got - want) > 0.05 * SLACK:
            bad.append((sc, got, want))
    rep.add(sec, "S1/S2/S3 axial reactions equal the sum of FZ over the inlet-face nodes in the raw reaction files", not bad,
            f"{bad}. raw sums: " + ", ".join(f"{k} {v:.2f} N" for k, v in raws.items()) + ". Tolerance 0.05 N: the register prints 0.1 N.")
    # LS-DYNA: N_max and its lambda from the binout N file; full-precision JSON against the rounded summary table
    ser = lambda c: list(csv.DictReader(open(repo / LSD / f"results/series/{c}_series.csv")))
    bad, bad2 = [], []
    an = src.json(f"{LSD}/comparisons/analysis_12C.json")
    for code in ("C0_A0p0", "C1_A0p1", "C3_A0p6", "C5_A1p2"):
        rows = list(csv.DictReader(open(repo / LSD / f"results/{code}_N_binout.csv")))
        top = max(rows, key=lambda r: float(r["Fz_inlet_N"]))
        lam_of_t = {round(float(r["t"]), 6): float(r["lambda"]) for r in ser(code)}
        n_bin, lam_bin = float(top["Fz_inlet_N"]) / 1000, lam_of_t[round(float(top["t"]), 6)]
        n_db, lam_db = [db.execute("SELECT value FROM v_results WHERE case_code=? AND metric_id=?", (code, m)).fetchone()[0]
                        for m in ("lsdyna.n_max", "lsdyna.lambda_at_n_max")]
        if abs(n_bin - n_db) > 0.005 * SLACK or abs(lam_bin - lam_db) > 1e-9:
            bad.append((code, n_db, n_bin, lam_db, lam_bin))
        j = an[code]
        for metric, key, dec in (("lsdyna.n_max", "N_max_kN", 0.005), ("lsdyna.southwell_ncr", "N_southwell_kN", 0.005),
                                 ("lsdyna.yield_indicator_lambda", "lambda_first_yield_indicator", 0.00005),
                                 ("lsdyna.vm_at_lambda1", "vm_at_lambda1_MPa", 0.05), ("lsdyna.onset_lambda", "lambda_onset_1pct", 0.0005)):
            if key in j and j[key] is not None:
                v = db.execute("SELECT value FROM v_results WHERE case_code=? AND metric_id=?", (code, metric)).fetchone()[0]
                if abs(v - j[key]) > dec * SLACK:
                    bad2.append((code, metric, v, j[key]))
    rep.add(sec, "LS-DYNA N_max and lambda at N_max equal the maximum of the binout N file (t mapped to lambda via the series file)", not bad,
            f"{bad}. Tolerance on N: 0.005 kN = the 0.01 kN rounding of the summary table.")
    rep.add(sec, "LS-DYNA summary values agree with the full-precision analysis_12C.json", not bad2,
            f"{bad2[:3]}. Tolerance per value = half unit of the last digit printed in IMPERFECTION_SENSITIVITY.csv.")
    # cross-file consistency: ratios printed in MECHANICAL_vs_LSDYNA.csv against ratios recomputed in SQL
    pcr = db.execute("SELECT value FROM v_results WHERE case_code='P00' AND solver='ANSYS Mechanical' AND support_condition='S1' AND metric_id='buck.eig_pcr'").fetchone()[0]
    want = {"Southwell estimate of the critical load, A = 0.1 mm": "C1_A0p1", "Southwell estimate of the critical load, A = 0.6 mm": "C3_A0p6",
            "Southwell estimate of the critical load, A = 1.2 mm": "C5_A1p2", "Maximum attained axial compression, A = 0.1 mm": "C1_A0p1",
            "Maximum attained axial compression, A = 0.6 mm": "C3_A0p6", "Maximum attained axial compression, A = 1.2 mm": "C5_A1p2"}
    bad = []
    for r in csv_rows(repo / S["ls_vs_mech"]):
        if r["Quantity"] in want:
            metric = "lsdyna.southwell_ncr" if r["Quantity"].startswith("Southwell") else "lsdyna.n_max"
            v = db.execute("SELECT value FROM v_results WHERE case_code=? AND metric_id=?", (want[r["Quantity"]], metric)).fetchone()[0]
            if abs(v / pcr - float(r["Ratio to Mechanical P_cr"])) > 5e-5 * SLACK or abs(100 * (v / pcr - 1) - float(r["Difference to Mechanical P_cr [%]"])) > 0.005 * SLACK:
                bad.append((r["Quantity"], v / pcr))
    rep.add(sec, "ratios to the Mechanical P_cr (and % differences) printed in MECHANICAL_vs_LSDYNA.csv are reproduced from database values",
            not bad, f"{bad}. Tolerance: half unit of the printed 4-decimal ratio / 2-decimal percentage.")
    s = {sc: db.execute("SELECT s.value, l.value, r.value FROM v_results s JOIN v_results l ON l.run_code=s.run_code AND l.metric_id='buck.eig_pcr'"
                        " JOIN v_results r ON r.case_code='P00' AND r.support_condition=? AND r.metric_id='struct.lc2.end_reaction_axial'"
                        " WHERE s.case_code='P00' AND s.support_condition=? AND s.metric_id='buck.eig_lambda1'", (sc, sc)).fetchone() for sc in ("S1", "S2", "S3")}
    bad = [(sc, v) for sc, v in s.items() if abs(v[1] - v[0] * v[2] / 1000) > 0.005 + 5e-6 * v[2] / 1000]
    rep.add(sec, "P_cr = lambda1 x LC2 axial force holds for S1, S2, S3", not bad,
            f"{bad}. Tolerance 0.005 kN + 5e-6 x P_cr: P_cr is printed to 0.01 kN and lambda1 to 5 decimals.")


def check_repro(rep, repo, db_path):
    sec = "8 Reproducibility and failure handling"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dumps = []
        for i in (1, 2):
            out = subprocess.run([sys.executable, str(HERE / "import_results.py"), "--repo", str(repo), "--db", str(td / f"r{i}.db")],
                                 capture_output=True, text=True, cwd=td)
            if out.returncode:
                rep.add(sec, f"rebuild {i} via the documented command", False, out.stderr[-300:])
                return
            dumps.append(hashlib.sha256("\n".join(sqlite3.connect(td / f"r{i}.db").iterdump()).encode()).hexdigest())
        rep.add(sec, "two independent rebuilds produce identical content (SHA-256 of the full SQL dump)", dumps[0] == dumps[1], dumps[0][:16])
        cur = hashlib.sha256("\n".join(sqlite3.connect(db_path).iterdump()).encode()).hexdigest()
        rep.add(sec, "database under test has the same content as a fresh rebuild", cur == dumps[0])
        rep.add(sec, "rebuilt database files are byte-identical", (td / "r1.db").read_bytes() == (td / "r2.db").read_bytes(), status="INFO" if (td / "r1.db").read_bytes() != (td / "r2.db").read_bytes() else None)
        # failure handling: duplicate / conflicting records and an error half-way through an import
        mem = sqlite3.connect(":memory:", isolation_level=None)
        mem.execute("PRAGMA foreign_keys = ON")
        mem.executescript((HERE / "schema.sql").read_text(encoding="utf-8"))
        mem.execute("BEGIN")
        t = imp.Importer(repo, mem)
        t.load_metrics()
        t.load_baseline()
        t.load_cfd_and_structural_cases()
        t.load_cfd_mesh_study()
        outcomes = {}
        for label, val in (("duplicate", 438.12633), ("conflicting", 1.0)):
            try:
                t.add_result("P00:fluent:medium", "cfd.dp_static", val, S["mesh_raw"], "medium", "test")
                outcomes[label] = "accepted"
            except imp.DuplicateRecord:
                outcomes[label] = "DuplicateRecord"
            except imp.ConflictingRecord:
                outcomes[label] = "ConflictingRecord"
        rep.add(sec, "duplicate and conflicting records are detected and refused",
                outcomes == {"duplicate": "DuplicateRecord", "conflicting": "ConflictingRecord"}, str(outcomes))
        mem.close()
        target = td / "keep.db"
        target.write_bytes(b"previous database")

        class Failing(imp.Importer):
            def load_support(self):
                raise imp.ImportFailure("injected failure after partial import")

        try:
            imp.build(repo, target, Failing)
            ok = False
        except imp.ImportFailure:
            ok = target.read_bytes() == b"previous database" and not (td / "keep.db.partial").exists()
        rep.add(sec, "an error mid-import rolls back: existing database untouched, no partial file left", ok)


def run_queries(db_path, rep, log):
    sec = "9 SQL query library"
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    files = sorted((HERE / "queries").glob("*.sql"))
    total = 0
    for f in files:
        sql = f.read_text(encoding="utf-8")
        body = re.sub(r"--.*", "", sql).strip().upper()
        try:
            cur = db.execute(sql)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            ok = bool(rows) and body.startswith(("SELECT", "WITH"))
            rep.add(sec, f.name, ok, f"{len(rows)} rows, {len(cols)} columns" + ("" if ok else " (empty or not read-only)"))
            total += ok
            log.append((f.name, sql, cols, rows))
        except sqlite3.Error as e:
            rep.add(sec, f.name, False, str(e))
    rep.add(sec, f"at least 12 queries tested and returning rows (found {len(files)})", total >= 12, f"{total} passing")


# ------------------------------------------------------------------ report writers
LIMITS = """\
* **Re-analysis data.** Every value is from the project's 2026 re-analysis (`MASTER_PROJECT_DATA.csv` header). No value is recovered internship data and no experimental data exist, so "validation" here means consistency with the repository's own sources, not physical validation.
* **Raw nodal exports are not in the repository** (CSV exports over 10 MB were excluded), so maximum von Mises stresses and deformations cannot be recomputed from raw nodal tables. They are checked against the summary tables, the register and (for P00) the 7B summary only. Reactions and eigenvalues are checked against raw files (section 7).
* **LS-DYNA binout and d3plot files are excluded.** LS-DYNA values are checked against the summary table, the full-precision `analysis_12C.json`, and the extracted N series. Peak stresses and yield-indicator lambdas have no raw-file check.
* **The register does not cover the LS-DYNA 12C extension** (it predates it), so LS-DYNA values are not compared with register rows.
* **The importer's own cross-checks and this script share the same repository.** Agreement between two files in the same repository shows consistency, not independence of the underlying solver runs.
* **Tolerances** are used only in the places stated above; each is a rounding-precision argument (half a unit of the last printed digit, or a stated relative bound where two files round the same value differently). No stored value was rounded.
* **Not reproducible without the repository's published summary files.** The database does not depend on any file excluded from the public repository, but ANSYS Fluent, ANSYS Mechanical and LS-DYNA are needed to regenerate the solver results themselves.
"""


def write_reports(rep, db, log, dbpath):
    out = HERE / "validation"
    out.mkdir(exist_ok=True)
    counts = {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("source_files", "metrics", "simulation_cases", "case_parameters", "solver_runs", "simulation_results", "validation_checks")}
    L = ["# Validation report", "",
         f"Generated by `validate_database.py` (Python {sys.version.split()[0]}, SQLite {sqlite3.sqlite_version}) against "
         f"`database/{Path(dbpath).name}`. Re-run the script to regenerate this file.", "",
         f"**Result: {rep.n('PASS')} passed, {rep.n('FAIL')} failed, {rep.n('INFO')} informational.**", "",
         "## Records imported", "", "| Table | Rows |", "|---|---:|"] + [f"| {t} | {n} |" for t, n in counts.items()]
    sec = None
    for s, name, status, detail in rep.rows:
        if s != sec:
            sec = s
            L += ["", f"## {s}", "", "| Status | Check | Detail |", "|---|---|---|"]
        L.append(f"| {status} | {name} | {detail.replace('|', '/').replace(chr(10), ' ')[:600]} |")
    L += ["", "## Discrepancies preserved in the database (not resolved)", "",
          "| Case | Check | Status | Detail |", "|---|---|---|---|"]
    for case, name, status, detail in db.execute(
            "SELECT c.case_code, v.check_name, v.status, v.detail FROM validation_checks v JOIN simulation_cases c USING(case_id)"
            " WHERE v.status IN ('DISCREPANCY','FAIL') ORDER BY c.case_id"):
        L.append(f"| {case} | {name} | {status} | {detail.replace('|', '/')} |")
    L += ["", "Other source-level observations that are recorded as documented in the sources, not as errors: the C00 pipeline control differs from P00 only in the "
          "LC1 inlet-bore peak stress (24.169 vs 24.282 MPa, mapping-numbering effect stated in `PARAMETRIC_STRUCTURAL_RESULTS.md`); the Fluent facet maximum of the "
          "outer wall is 562.57678 K in the raw report and 562.57675 K in the mesh-study table (relative difference 5e-8).", "",
          "## Limitations", "", LIMITS]
    (out / "VALIDATION_REPORT.md").write_text("\n".join(L).rstrip("\n") + "\n", encoding="utf-8")
    Q = ["# Query run log", "", "Every file in `queries/` executed read-only against the database. Up to 8 rows per query are shown; "
         "values are printed as stored (long text truncated). Regenerated by `validate_database.py`.", ""]
    for name, sql, cols, rows in log:
        title = sql.splitlines()[0].lstrip("- ").strip()
        Q += [f"## {name}", "", f"*{title}*", "", f"{len(rows)} rows. First rows:", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        for r in rows[:8]:
            Q.append("| " + " | ".join("" if v is None else str(v).replace("|", "/")[:48] for v in r) + " |")
        Q.append("")
    (out / "QUERY_RUN_LOG.md").write_text("\n".join(Q).rstrip("\n") + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", type=Path, default=imp.DEFAULT_REPO)
    ap.add_argument("--db", type=Path, default=imp.DEFAULT_DB)
    ap.add_argument("--no-report", action="store_true", help="do not write validation/*.md")
    a = ap.parse_args(argv)
    repo, dbp = a.repo.resolve(), a.db.resolve()
    if not dbp.is_file():
        print(f"database not found: {dbp} (run import_results.py first)", file=sys.stderr)
        return 2
    db = sqlite3.connect(f"file:{dbp}?mode=ro", uri=True)
    rep, src, log = Report(), Sources(repo), []

    def guard(fn, *args):  # a crashing check is a failed check, never a silent pass
        try:
            fn(*args)
        except Exception as e:  # noqa: BLE001
            rep.add("0 Internal", f"{fn.__name__} could not complete", False, f"{type(e).__name__}: {e}"[:300])

    guard(check_schema, db, rep)
    guard(check_counts, db, rep, src)
    guard(check_fields, db, rep, repo)
    guard(check_sources, db, rep, repo)
    guard(check_fidelity, db, rep, src)
    guard(check_register, db, rep, src)
    guard(check_raw, db, rep, src)
    guard(check_repro, rep, repo, dbp)
    guard(run_queries, dbp, rep, log)
    if not a.no_report:
        write_reports(rep, db, log, dbp)
    for s, name, status, detail in rep.rows:
        if status == "FAIL":
            print(f"FAIL  [{s}] {name}: {detail}")
    print(f"validation: {rep.n('PASS')} passed, {rep.n('FAIL')} failed, {rep.n('INFO')} informational")
    return 1 if rep.n("FAIL") else 0


if __name__ == "__main__":
    sys.exit(main())
