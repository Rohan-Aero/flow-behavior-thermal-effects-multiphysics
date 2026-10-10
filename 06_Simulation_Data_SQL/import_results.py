#!/usr/bin/env python3
"""Rebuild the SQLite results database from summary files that already exist in this repository.

    python import_results.py [--repo PATH] [--db PATH]

* Standard library only. Source files are only read, never modified.
* Idempotent: the database is rebuilt from scratch in one transaction in a temporary file and moved into
  place only if every step succeeded. Any error rolls back, removes the temporary file and leaves an
  existing database untouched.
* Duplicate or conflicting records stop the import (DuplicateRecord / ConflictingRecord).
* Values are stored exactly as parsed from the source (no rounding). Missing values are explicit rows with a
  value_status and a reason, never silent NULLs.
* No ANSYS or LS-DYNA run is needed: only the published summary tables and small run records are read.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sqlite3
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_REPO = HERE.parent
DEFAULT_DB = HERE / "database" / "simulation_results.db"

# ---------------------------------------------------------------- source files (repo-relative)
CFD = "02_CFD_Fluent"
MECH = "03_Thermal_Structural_Mechanical"
LSD = "04_LS_DYNA_Extension/12C_Nonlinear_Buckling"
S = {
    "mesh_raw": f"{CFD}/Comparison_Tables/three_mesh_raw_table.csv",
    "mesh_status": f"{CFD}/MESH_INDEPENDENCE_RESULTS.csv",
    "mesh_json": f"{CFD}/mesh_study_results.json",
    "cfd_param": f"{MECH}/CFD_Results/PARAMETRIC_CFD_RESULTS.csv",
    "struct_param": f"{MECH}/Results/PARAMETRIC_STRUCTURAL_RESULTS.csv",
    "summary_7b": f"{MECH}/Results/results_summary_7B.csv",
    "support_csv": f"{MECH}/Results/SUPPORT_SENSITIVITY_RESULTS.csv",
    "support_md": f"{MECH}/Results/SUPPORT_SENSITIVITY_RESULTS.md",
    "baseline": "01_Project_Documentation/baseline_parameters.json",
    "register": "05_Data/MASTER_PROJECT_DATA.csv",
    "ls_sens": f"{LSD}/IMPERFECTION_SENSITIVITY.csv",
    "ls_vs_mech": f"{LSD}/MECHANICAL_vs_LSDYNA.csv",
    "ls_qc": f"{LSD}/comparisons/qc_12C.json",
    "ls_imperf": f"{LSD}/audit/imperfection_report_12C.json",
}
LS_SERIES = LSD + "/results/series/{case}_series.csv"
LS_NOT_RUN = LSD + "/runs/{case}/NOT_RUN.txt"

# Solver versions: root README.md "Stages and tools" table.
V_FLUENT, V_MECH, V_LSDYNA = "Fluent 2026 R1", "ANSYS 2026 R1 (Student)", "LS-DYNA R16.1 (Student)"
NO_LABEL = "no status label in source"

LIM_CFD = ("Re-analysis 2026 (original internship data not retained); CFD only, no experimental data. "
           "Medium mesh is the project reference; see mesh_independence checks for per-quantity status.")
LIM_STATIC = "Linear-elastic one-way thermal-structural solution; no plasticity. Re-analysis 2026."
LIM_EIGEN = ("Linear eigenvalue of an ideal straight tube with idealised supports: no imperfection, no plasticity, "
             "no large deflection. Not a collapse load and not a factor of safety (register M179).")
LIM_NONLIN = ("Elastic-only thermo-elastic material (MAT_004, no plasticity). Where VM/S_y(T) > 1 the model is outside "
              "its range of validity: stresses above S_y(T) are indicators, not predicted physical stresses. "
              "Imperfection amplitudes are numerical sensitivity values, not tolerances. Not experimental validation "
              "(FINAL_12C_RESULTS.md).")

# ---------------------------------------------------------------- metric catalogue
# (metric_id, units, family, description, caveat)
METRICS = [
    ("cfd.dp_static", "Pa", "cfd_flow", "Area-weighted static pressure drop, inlet minus outlet", None),
    ("cfd.t_out_bulk", "K", "cfd_thermal", "Mass-weighted static temperature at the outlet", None),
    ("cfd.q_heated_wall", "W", "cfd_thermal", "Heat-transfer rate through the heated outer wall", None),
    ("cfd.t_solid_max_facet", "K", "cfd_thermal", "Maximum solid temperature, outer-wall facet maximum", None),
    ("cfd.t_solid_max_cell", "K", "cfd_thermal", "Maximum solid temperature, cell-centre value", None),
    ("cfd.t_solid_min_cell", "K", "cfd_thermal", "Minimum solid temperature, cell-centre value", None),
    ("cfd.t_solid_mean", "K", "cfd_thermal", "Volume-mean solid temperature", None),
    ("cfd.dt_wall_midspan", "K", "cfd_thermal", "Through-wall temperature difference at z = 300 mm", None),
    ("cfd.h_midspan", "W/m2K", "cfd_thermal", "Heat-transfer coefficient at mid-span", None),
    ("cfd.nu_fd", "-", "cfd_thermal", "Fully developed Nusselt number (x/D 18-29 window)", None),
    ("cfd.f_darcy_fd", "-", "cfd_flow", "Fully developed Darcy friction factor (x/D 18-29 window)", None),
    ("cfd.re_out", "-", "cfd_flow", "Reynolds number at the outlet", None),
    ("cfd.yplus_min", "-", "cfd_quality", "Minimum wall y+ (conjugate wall)", None),
    ("cfd.yplus_mean", "-", "cfd_quality", "Area-mean wall y+", None),
    ("cfd.yplus_max", "-", "cfd_quality", "Maximum wall y+",
     "Not a convergence metric: the maximum sits in the first slab, whose centre moves with mesh size (source status E)."),
    ("struct.lc1.max_total_deformation", "mm", "structural_response", "LC1 (free expansion) maximum total deformation", None),
    ("struct.lc1.axial_growth", "mm", "structural_response", "LC1 face-mean free axial growth", None),
    ("struct.lc1.max_von_mises", "MPa", "structural_response", "LC1 maximum von Mises stress",
     "Near-end value; sensitive to temperature-mapping node numbering (source F-035)."),
    ("struct.lc1.yield_utilisation", "-", "structural_response", "LC1 von Mises / S_y(T) at the maximum-stress node", None),
    ("struct.lc2.max_von_mises", "MPa", "structural_response", "LC2 (axially restrained) maximum von Mises stress", None),
    ("struct.lc2.mean_axial_stress", "MPa", "structural_response", "LC2 mean axial stress (negative = compression)", None),
    ("struct.lc2.critical_temperature", "K", "structural_response", "Temperature at the LC2 node of maximum vm / S_y(T)", None),
    ("struct.lc2.local_yield_strength", "MPa", "structural_response", "S_y(T) at that node", None),
    ("struct.lc2.yield_utilisation", "-", "structural_response", "LC2 maximum vm / S_y(T)", None),
    ("struct.lc2.max_total_deformation", "mm", "structural_response", "LC2 maximum total deformation", None),
    ("struct.lc2.end_reaction_axial", "N", "structural_response", "LC2 axial end-face reaction (sum of FZ on the inlet face)", None),
    ("struct.first_yield_factor", "-", "yield_onset",
     "Mechanical first-yield load factor = 1 / utilisation at the critical node (linear scaling of the LC2 state)",
     "Linear-elastic scaling only. Not comparable with lsdyna.yield_indicator_lambda (nonlinear path, bending included)."),
    ("buck.eig_lambda1", "-", "buckling_eigenvalue", "First linear eigenvalue buckling load factor (multiplies the LC2 state)", LIM_EIGEN),
    ("buck.eig_pcr", "kN", "buckling_eigenvalue", "Linear eigenvalue critical load = lambda1 x LC2 axial end force", LIM_EIGEN),
    ("lsdyna.n_max", "kN", "nonlinear_load",
     "Largest axial compression N reached within lambda <= 1.3 in the nonlinear run",
     "A value reached in a run, not a capacity. It is an instability point only if lsdyna.n_max_is_interior_max = 1."),
    ("lsdyna.lambda_at_n_max", "-", "nonlinear_load", "Load factor lambda at which lsdyna.n_max occurs", None),
    ("lsdyna.n_max_is_interior_max", "flag", "nonlinear_load",
     "1 = N_max is an interior maximum (N later drops > 0.1 %); 0 = N still rising at the end of the analysis", None),
    ("lsdyna.southwell_ncr", "kN", "nonlinear_load",
     "Southwell-plot characteristic (critical) load estimate, fit over N in [0.5, 0.95] N_max",
     "Extrapolated estimate, not a load reached in the run. Not a linear eigenvalue and not a maximum load."),
    ("lsdyna.southwell_r2", "-", "nonlinear_response", "R-squared of the Southwell fit", None),
    ("lsdyna.southwell_window_low", "kN", "nonlinear_load", "Lowest Southwell N_cr over 5 fit-window variants", None),
    ("lsdyna.southwell_window_high", "kN", "nonlinear_load", "Highest Southwell N_cr over 5 fit-window variants", None),
    ("lsdyna.southwell_w0", "mm", "nonlinear_response", "Southwell intercept estimate of the initial end offset (source compares with imposed 2A)", None),
    ("lsdyna.onset_lambda", "-", "nonlinear_response", "First lambda at which N is more than 1 % below the perfect-geometry path", None),
    ("lsdyna.onset_n", "kN", "nonlinear_load", "N at lsdyna.onset_lambda", None),
    ("lsdyna.n_at_lambda1", "kN", "nonlinear_load", "Axial compression at the design load factor lambda = 1", None),
    ("lsdyna.n_at_lambda1p3", "kN", "nonlinear_load", "Axial compression at the end of the analysis, lambda = 1.3", None),
    ("lsdyna.lateral_max_at_lambda1p3", "mm", "nonlinear_response", "Maximum section lateral translation at lambda = 1.3", None),
    ("lsdyna.end_sway_at_lambda1p3", "mm", "nonlinear_response", "Additional relative end sway at lambda = 1.3", None),
    ("lsdyna.vm_at_lambda1", "MPa", "nonlinear_response", "Peak nodal von Mises stress at lambda = 1 (end regions)",
     "Elastic model: a value above S_y(T) is an indicator, not a physical stress."),
    ("lsdyna.vm_max_end_region", "MPa", "nonlinear_response", "Peak nodal von Mises stress, end regions, lambda <= 1.3",
     "Elastic model: a value above S_y(T) is an indicator, not a physical stress."),
    ("lsdyna.util_max", "-", "nonlinear_response", "Maximum VM / S_y(T) over lambda <= 1.3 (elastic-validity indicator)", None),
    ("lsdyna.yield_indicator_lambda", "-", "yield_onset",
     "First lambda at which nodal VM / S_y(T) = 1 in the elastic nonlinear run",
     "Indicator only; plasticity is not modelled. Not comparable with struct.first_yield_factor."),
    ("lsdyna.yield_indicator_n", "kN", "yield_onset", "Axial compression N at lsdyna.yield_indicator_lambda", None),
]
M = {m[0]: m for m in METRICS}

# three_mesh_raw_table.csv quantity -> metric (derived/geometry-corrected rows are intentionally not imported)
MESH_QTY = {
    "Pressure drop, static (area-wtd, inlet - outlet)": "cfd.dp_static",
    "Outlet temperature, mass-weighted": "cfd.t_out_bulk",
    "Heat-transfer rate": "cfd.q_heated_wall",
    "Maximum solid temperature (outer-wall facet max)": "cfd.t_solid_max_facet",
    "Maximum solid temperature (cell centre)": "cfd.t_solid_max_cell",
    "Minimum solid temperature (cell centre)": "cfd.t_solid_min_cell",
    "Volume-mean solid temperature": "cfd.t_solid_mean",
    "Through-wall dT, MID-SPAN z = 300 mm": "cfd.dt_wall_midspan",
    "h, mid-span": "cfd.h_midspan",
    "Fully developed Nu (exact window x/D 18-29)": "cfd.nu_fd",
    "Fully developed Darcy f (exact window x/D 18-29)": "cfd.f_darcy_fd",
    "Reynolds number, outlet": "cfd.re_out",
    "y+ minimum": "cfd.yplus_min",
    "y+ area mean": "cfd.yplus_mean",
    "y+ maximum": "cfd.yplus_max",
}
# PARAMETRIC_CFD_RESULTS.csv column -> (metric, unit token expected in the column name)
CFD_COLS = [
    ("dp_Pa", "cfd.dp_static", "Pa"), ("T_out_K", "cfd.t_out_bulk", "K"),
    ("Q_heated_wall_W", "cfd.q_heated_wall", "W"), ("T_solid_max_K", "cfd.t_solid_max_facet", "K"),
    ("T_solid_cell_max_K", "cfd.t_solid_max_cell", "K"), ("T_solid_cell_min_K", "cfd.t_solid_min_cell", "K"),
    ("T_solid_mean_K", "cfd.t_solid_mean", "K"), ("Re_out", "cfd.re_out", "-"),
    ("yplus_min", "cfd.yplus_min", "-"), ("yplus_mean", "cfd.yplus_mean", "-"), ("yplus_max", "cfd.yplus_max", "-"),
]
# PARAMETRIC_STRUCTURAL_RESULTS.csv column -> (metric, run key)
STRUCT_COLS = [
    ("Max deformation [mm]", "struct.lc1.max_total_deformation", "lc1"),
    ("Axial growth [mm]", "struct.lc1.axial_growth", "lc1"),
    ("LC1 max stress [MPa]", "struct.lc1.max_von_mises", "lc1"),
    ("LC2 max stress [MPa]", "struct.lc2.max_von_mises", "lc2"),
    ("LC2 mean axial stress [MPa]", "struct.lc2.mean_axial_stress", "lc2"),
    ("Critical temperature [K]", "struct.lc2.critical_temperature", "lc2"),
    ("Yield strength [MPa]", "struct.lc2.local_yield_strength", "lc2"),
    ("Yield utilization [-]", "struct.lc2.yield_utilisation", "lc2"),
    ("Lambda1 [-]", "buck.eig_lambda1", "buck"),
    ("Critical buckling load [kN]", "buck.eig_pcr", "buck"),
]
# IMPERFECTION_SENSITIVITY.csv columns
LC = {
    "case": "Case", "role": "Study role", "amp": "Imperfection [mm]", "char": "Instability/Characteristic Load",
    "lat13": "Max Lateral Displacement [mm] (max section translation at lambda=1.3)",
    "sway13": "Additional relative end sway at lambda=1.3 [mm]",
    "vm_max": "Max von Mises [MPa] (nodal, end-region monitored elements, lambda<=1.3; elastic model)",
    "vm_l1": "Max von Mises at lambda=1 [MPa]", "nmax": "N_max [kN]", "lam_nmax": "lambda at N_max",
    "interior": "Interior peak", "n13": "N at lambda=1.3 [kN]", "sw": "Southwell N_cr [kN]", "sw_r2": "Southwell R2",
    "sw_rng": "Southwell range over 5 fit-window variants [kN]",
    "sw_w0": "Southwell w0 estimate [mm] (imposed 2A)", "on_l": "Onset lambda (N 1% below perfect path)",
    "on_n": "Onset N [kN]", "yl": "lambda at VM/S_y(T)=1", "yn": "N at VM/S_y(T)=1 [kN]", "util": "max VM/S_y(T)",
}


class ImportFailure(Exception):
    pass


class DuplicateRecord(ImportFailure):
    pass


class ConflictingRecord(ImportFailure):
    pass


def num(s):
    s = (s or "").strip()
    return None if s in ("", "nan", "NaN") else float(s)


def mm(x_m):  # exact decimal metre -> millimetre
    return float(Decimal(str(x_m)) * 1000)


class Importer:
    def __init__(self, repo: Path, con: sqlite3.Connection):
        self.repo, self.con = repo, con
        self._bytes, self.fid, self.case_id, self.run_id = {}, {}, {}, {}
        self.results, self.n = {}, {}

    # ------------------------------------------------------------ source access
    def _read(self, rel, role):
        if rel not in self._bytes:
            p = (self.repo / rel).resolve()
            if not p.is_file() or self.repo.resolve() not in p.parents:
                raise ImportFailure(f"required source file missing: {rel}")
            b = p.read_bytes()
            self._bytes[rel] = b
            cur = self.con.execute(
                "INSERT INTO source_files (repo_path, file_role, sha256, size_bytes) VALUES (?,?,?,?)",
                (rel, role, hashlib.sha256(b).hexdigest(), len(b)))
            self.fid[rel] = cur.lastrowid
        return self._bytes[rel]

    def text(self, rel, role):
        b = self._read(rel, role)
        for enc in ("utf-8-sig", "utf-16"):
            try:
                return b.decode(enc)
            except UnicodeDecodeError:
                continue
        raise ImportFailure(f"cannot decode {rel}")

    def rows(self, rel, role="result_summary", key=None):
        lines = [ln for ln in self.text(rel, role).splitlines() if ln.strip()]
        while lines and lines[0].lstrip('"').startswith("#"):
            lines.pop(0)
        out = list(csv.DictReader(io.StringIO("\n".join(lines))))
        if key:
            seen = set()
            for r in out:
                if r[key] in seen:
                    raise DuplicateRecord(f"{rel}: duplicate {key} = {r[key]!r}")
                seen.add(r[key])
        return out

    def json(self, rel, role="run_record"):
        return json.loads(self.text(rel, role))

    # ------------------------------------------------------------ inserts
    def _count(self, t):
        self.n[t] = self.n.get(t, 0) + 1

    def add_case(self, code, group, desc, status, src, src_case, parent=None):
        if code in self.case_id:
            return self.case_id[code]
        if parent and parent not in self.case_id:
            raise ImportFailure(f"case {code}: parent case {parent} has not been loaded")
        cur = self.con.execute(
            "INSERT INTO simulation_cases (case_code, case_group, parent_case_id, description, case_status,"
            " source_file_id, source_case_id) VALUES (?,?,?,?,?,?,?)",
            (code, group, self.case_id.get(parent), desc, status, self.fid[src], src_case))
        self.case_id[code] = cur.lastrowid
        self._count("simulation_cases")
        return cur.lastrowid

    def add_param(self, case, name, value, units, src, field):
        v, t = (None, value) if isinstance(value, str) else (value, None)
        self.con.execute(
            "INSERT INTO case_parameters (case_id, parameter, value, value_text, units, source_file_id, source_field)"
            " VALUES (?,?,?,?,?,?,?)", (self.case_id[case], name, v, t, units, self.fid[src], field))
        self._count("case_parameters")

    def add_run(self, code, case, solver, version, atype, status, src, src_case, limitation, *, load_case=None,
                support=None, mesh=None, cells=None, nodes=None, converged=None, iters=None):
        if code in self.run_id:
            raise DuplicateRecord(f"duplicate solver run {code}")
        cur = self.con.execute(
            "INSERT INTO solver_runs (case_id, run_code, solver, solver_version, analysis_type, load_case,"
            " support_condition, mesh_level, n_cells, n_nodes, run_status, converged, iterations, model_limitation,"
            " source_file_id, source_case_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (self.case_id[case], code, solver, version, atype, load_case, support, mesh, cells, nodes, status,
             converged, iters, limitation, self.fid[src], src_case))
        self.run_id[code] = cur.lastrowid
        self._count("solver_runs")

    def add_result(self, run, metric, value, src, src_case, field, *, status="reported", reason=None,
                   validity="not_assessed", note=None):
        if metric not in M:
            raise ImportFailure(f"unknown metric {metric}")
        if status == "reported" and value is None:
            raise ImportFailure(f"{run} {metric}: reported value is empty in {src} ({field})")
        key = (run, metric)
        if key in self.results:
            old = self.results[key]
            kind = DuplicateRecord if old[0] == value else ConflictingRecord
            raise kind(f"{run} {metric}: {old[1]} gives {old[0]!r}, {src} ({field}) gives {value!r}")
        self.results[key] = (value, f"{src} ({field})")
        self.con.execute(
            "INSERT INTO simulation_results (run_id, metric_id, units, value, value_status, missing_reason,"
            " physical_validity, source_file_id, source_case_id, source_field, note) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (self.run_id[run], metric, M[metric][1], value, status, reason, validity, self.fid[src], src_case,
             field, note))
        self._count("simulation_results")

    def add_check(self, case, run, origin, name, status, detail, src, *, source_status=None, observed=None,
                  reference=None, tol=None, units=None):
        self.con.execute(
            "INSERT INTO validation_checks (case_id, run_id, check_origin, check_name, status, source_status,"
            " observed_value, reference_value, tolerance, units, detail, source_file_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (self.case_id[case], self.run_id.get(run), origin, name, status, source_status, observed, reference, tol,
             units, detail, self.fid[src]))
        self._count("validation_checks")

    # ------------------------------------------------------------ loaders
    def load_metrics(self):
        for m in METRICS:
            self.con.execute("INSERT INTO metrics VALUES (?,?,?,?,?)", m)
            self._count("metrics")

    def load_baseline(self):
        p = self.json(S["baseline"], "case_definition")["params"]
        for k, u in (("Di", "m"), ("Do", "m"), ("L", "m"), ("T_in", "K"), ("V_in", "m/s"), ("qpp_o", "W/m2")):
            if p[k]["units"] != u:
                raise ImportFailure(f"baseline_parameters.json: {k} units {p[k]['units']!r}, expected {u!r}")
        self.base = {k: p[k]["value"] for k in ("Di", "Do", "L", "T_in", "V_in", "qpp_o")}

    def load_cfd_and_structural_cases(self):
        cfd = self.rows(S["cfd_param"], key="case")
        st = self.rows(S["struct_param"], key="Case")
        if [r["case"] for r in cfd] != [r["Case"] for r in st]:
            raise ConflictingRecord("case lists differ between PARAMETRIC_CFD_RESULTS.csv and PARAMETRIC_STRUCTURAL_RESULTS.csv")
        self.cfd_rows = {r["case"]: r for r in cfd}
        self.st_rows = {r["Case"]: r for r in st}
        base_t = float((Decimal(str(self.base["Do"])) - Decimal(str(self.base["Di"]))) / 2 * 1000)
        for src_case, r in self.cfd_rows.items():
            code = "P00" if src_case == "P00_BASELINE" else src_case
            group = ("baseline" if code == "P00" else "pipeline_control" if code.startswith("C00") else "parametric")
            desc = ("Baseline design point: " + r["value"] if code == "P00" else
                    "Pipeline control, identical to P00" if group == "pipeline_control" else
                    f"{r['variable']} = {r['value']} {r['units']}")
            self.add_case(code, group, desc, "reference" if code == "P00" else "solved", S["cfd_param"], src_case,
                          parent=None if code == "P00" else "P00")
            f = S["cfd_param"]
            self.add_param(code, "inlet_velocity", float(r["value"]) if r["variable"] == "inlet velocity" else self.base["V_in"],
                           "m/s", f if r["variable"] == "inlet velocity" else S["baseline"],
                           "column 'value'" if r["variable"] == "inlet velocity" else "params.V_in.value (not varied)")
            self.add_param(code, "outer_wall_heat_flux", float(r["qpp_heated_area_avg_W_m2"]), "W/m2", f,
                           "column 'qpp_heated_area_avg_W_m2'")
            thick = r["variable"].startswith("wall thickness")
            self.add_param(code, "wall_thickness", float(r["value"]) if thick else base_t, "mm",
                           f if thick else S["baseline"],
                           "column 'value'" if thick else "derived (Do - Di) / 2 from params.Do, params.Di (not varied)")
            geo = re.search(r"Do (\d+)", self.st_rows[src_case]["Geometry"])
            if not geo:
                raise ImportFailure(f"cannot read outer diameter from Geometry of {src_case}")
            self.add_param(code, "outer_diameter", float(geo.group(1)), "mm", S["struct_param"], "column 'Geometry' (Do ...)")
            self.add_param(code, "inner_diameter", mm(self.base["Di"]), "mm", S["baseline"], "params.Di.value (m converted exactly)")
            self.add_param(code, "tube_length", mm(self.base["L"]), "mm", S["baseline"], "params.L.value (m converted exactly)")
            self.add_param(code, "inlet_temperature", self.base["T_in"], "K", S["baseline"], "params.T_in.value")

    def load_cfd_mesh_study(self):
        js = self.json(S["mesh_json"], "result_summary")
        rows = self.rows(S["mesh_raw"], key="quantity")
        status = {r["quantity"]: r for r in self.rows(S["mesh_status"], key="quantity")}
        for level in ("coarse", "medium", "fine"):
            v = js["values"][level]
            self.add_run(f"P00:fluent:{level}", "P00", "ANSYS Fluent", V_FLUENT, "cfd_conjugate_steady",
                         f"converged={v['converged']}", S["mesh_json"], level, LIM_CFD, mesh=level,
                         cells=js["mesh"][level]["cells"], converged=int(bool(v["converged"])), iters=int(v["iters"]))
            for r in rows:
                q = r["quantity"]
                if q in MESH_QTY:
                    metric = MESH_QTY[q]
                    if r["units"] != M[metric][1]:
                        raise ImportFailure(f"{S['mesh_raw']}: units of {q!r} are {r['units']!r}, expected {M[metric][1]!r}")
                    self.add_result(f"P00:fluent:{level}", metric, num(r[level]), S["mesh_raw"], level,
                                    f"row '{q}', column '{level}'")
                elif q in ("Mass imbalance", "Energy imbalance"):
                    self.add_check("P00", f"P00:fluent:{level}", "source_recorded", q.lower().replace(" ", "_"), "INFO",
                                   "recorded conservation imbalance of the converged solution", S["mesh_raw"],
                                   observed=num(r[level]), units="%")
            self.add_check("P00", f"P00:fluent:{level}", "source_recorded", "convergence",
                           "PASS" if v["converged"] else "FAIL", f"{v['iters']} iterations; converged flag from the run record",
                           S["mesh_json"], source_status=f"converged={v['converged']}", observed=float(v["iters"]), units="iterations")
        for q, r in status.items():
            self.add_check("P00", None, "source_recorded", f"mesh_independence:{q}", "INFO", r["status_basis"],
                           S["mesh_status"], source_status=r["status"], observed=num(r["GCI_fine_pct"]),
                           units="% (GCI, fine mesh)" if r["GCI_fine_pct"].strip() else None)

    def load_cfd_parametric(self):
        for src_case, r in self.cfd_rows.items():
            code = "P00" if src_case == "P00_BASELINE" else src_case
            if code == "P00":
                continue  # P00's CFD run is the medium-mesh run loaded from the mesh study (same solution)
            run = f"{code}:fluent"
            ok = r["valid"].strip() == "True"
            self.add_run(run, code, "ANSYS Fluent", V_FLUENT, "cfd_conjugate_steady", r["status"], S["cfd_param"],
                         src_case, LIM_CFD, cells=int(r["cells"]), converged=int(ok), iters=int(r["iterations"]))
            for col, metric, tok in CFD_COLS:
                if M[metric][1] != tok:
                    raise ImportFailure(f"unit mismatch for {col}")
                self.add_result(run, metric, num(r[col]), S["cfd_param"], src_case, f"column '{col}'")
            self.add_check(code, run, "source_recorded", "convergence", "PASS" if ok else "FAIL",
                           "valid flag and iteration count from the run table", S["cfd_param"], source_status=r["status"],
                           observed=float(r["iterations"]), units="iterations")
            for col, name in (("mass_error_monitor", "mass_imbalance"), ("energy_error_monitor", "energy_imbalance")):
                self.add_check(code, run, "source_recorded", name, "INFO",
                               "recorded conservation imbalance as a fraction (not percent)", S["cfd_param"],
                               observed=num(r[col]), units="fraction")

    def load_structural(self):
        u7 = {r["Quantity"]: r for r in self.rows(S["summary_7b"], key="Quantity")}
        util1 = float(u7["utilisation at max von Mises (S_y(T))"]["LC1 (thermal only)"])
        for src_case, r in self.st_rows.items():
            code = "P00" if src_case == "P00_BASELINE" else src_case
            nodes = int(r["Nodes"])
            status, _, note = r["Status"].partition(";")
            status = status.strip()
            runs = {
                "lc1": (f"{code}:mech:static:LC1", "static_structural_thermal", "LC1", None, LIM_STATIC),
                "lc2": (f"{code}:mech:static:LC2:S1", "static_structural_thermal", "LC2", "S1", LIM_STATIC),
                "buck": (f"{code}:mech:buckling:S1", "linear_eigenvalue_buckling", "LC2", "S1", LIM_EIGEN),
            }
            for rc, atype, lc, sup, lim in runs.values():
                self.add_run(rc, code, "ANSYS Mechanical", V_MECH, atype, status, S["struct_param"], src_case, lim,
                             load_case=lc, support=sup, nodes=nodes)
            util2 = float(r["Yield utilization [-]"])
            for col, metric, k in STRUCT_COLS:
                units = re.search(r"\[(.*?)\]$", col).group(1)
                if units != M[metric][1]:
                    raise ImportFailure(f"unit mismatch for column {col!r}")
                validity = "not_assessed"
                if metric == "struct.lc2.max_von_mises":
                    validity = "within_elastic_range" if util2 <= 1 else "beyond_yield_elastic_model_not_physical"
                elif metric == "struct.lc1.max_von_mises" and code == "P00":  # LC1 utilisation is recorded for P00 only
                    validity = "within_elastic_range" if util1 <= 1 else "beyond_yield_elastic_model_not_physical"
                field = f"column '{col}'" + (" (= LC1 max total deformation per file header)" if col == "Max deformation [mm]" else "")
                self.add_result(runs[k][0], metric, num(r[col]), S["struct_param"], src_case, field, validity=validity)
            if code == "P00":
                self.add_result(runs["lc1"][0], "struct.lc1.yield_utilisation", util1, S["summary_7b"], "LC1",
                                "row 'utilisation at max von Mises (S_y(T))', column 'LC1 (thermal only)'",
                                validity="within_elastic_range")
            self.add_check(code, runs["lc2"][0], "source_recorded", "solution_status",
                           "PASS" if status.startswith(("SOLVED - VALID", "OFFICIAL BASELINE")) else "INFO",
                           note.strip() or "no additional note in source", S["struct_param"], source_status=r["Status"])
            lam = num(r["Lambda1 [-]"])
            if lam < 1:
                self.add_check(code, runs["buck"][0], "source_recorded", "linear_stability_lambda1_below_1", "INFO",
                               "lambda1 < 1: the LC2 static stress is a pre-buckling equilibrium result; the linear "
                               "stability criterion indicates loss of stability before the applied load level (source note)",
                               S["struct_param"], observed=lam, reference=1.0, units="-")

    def load_support(self):
        reg = {r["ID"]: r for r in self.rows(S["register"], "master_register", key="ID")}
        m110 = reg["M110"]
        if m110["Parameter"] != "S1 / S2 / S3 axial reaction" or m110["Units"] != "N":
            raise ImportFailure("MASTER_PROJECT_DATA.csv M110 is not the S1/S2/S3 axial reaction row in N")
        react = dict(zip(("S1", "S2", "S3"), (float(x) for x in m110["Value"].split("/"))))
        md = self.text(S["support_md"], "documentation").splitlines()
        i = next(k for k, ln in enumerate(md) if ln.startswith("| Scenario |") and "First-yield factor" in ln)
        hdr = [c.strip() for c in md[i].strip().strip("|").split("|")]
        tab = {}
        for ln in md[i + 2:]:
            if not ln.startswith("|"):
                break
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            tab[cells[0]] = dict(zip(hdr, cells))
        for r in self.rows(S["support_csv"], key="Scenario"):
            sc = r["Scenario"]
            lc2, bk = f"P00:mech:static:LC2:{sc}", f"P00:mech:buckling:{sc}"
            fy = float(tab[sc]["First-yield factor"])
            if sc != "S1":
                self.add_run(lc2, "P00", "ANSYS Mechanical", V_MECH, "static_structural_thermal", NO_LABEL,
                             S["support_csv"], sc, LIM_STATIC, load_case="LC2", support=sc)
                self.add_run(bk, "P00", "ANSYS Mechanical", V_MECH, "linear_eigenvalue_buckling", NO_LABEL,
                             S["support_csv"], sc, LIM_EIGEN, load_case="LC2", support=sc)
                self.add_result(lc2, "struct.lc2.max_von_mises", num(r["Max stress [MPa]"]), S["support_csv"], sc,
                                "column 'Max stress [MPa]'",
                                validity="within_elastic_range" if fy >= 1 else "beyond_yield_elastic_model_not_physical")
                self.add_result(lc2, "struct.lc2.mean_axial_stress", num(r["Mean axial stress [MPa]"]), S["support_csv"], sc,
                                "column 'Mean axial stress [MPa]'")
                self.add_result(bk, "buck.eig_lambda1", num(r["Lambda1 [-]"]), S["support_csv"], sc, "column 'Lambda1 [-]'")
                self.add_result(bk, "buck.eig_pcr", num(r["Critical load [kN]"]), S["support_csv"], sc, "column 'Critical load [kN]'")
            self.add_result(lc2, "struct.lc2.max_total_deformation", num(r["Deformation [mm]"]), S["support_csv"], sc,
                            "column 'Deformation [mm]'")
            self.add_result(lc2, "struct.lc2.end_reaction_axial", react[sc], S["register"], "M110",
                            f"row M110 'S1 / S2 / S3 axial reaction', part {sc}",
                            note="register status REPORTED; sum of FZ on the inlet face")
            self.add_result(lc2, "struct.first_yield_factor", fy, S["support_md"], sc,
                            "section 4 table, column 'First-yield factor'")
            self.add_check("P00", bk, "source_recorded", "governing_mechanism_idealised", "INFO",
                           "which limit comes first in the idealised model (source classification, not a validation)",
                           S["support_md"], source_status=tab[sc]["Occurs first (idealised)"])

    def load_lsdyna(self):
        qc, imp = self.json(S["ls_qc"]), self.json(S["ls_imperf"])
        # LS-DYNA 12B G6 linear eigenvalue cross-check on the P00 model (extension)
        vs = self.rows(S["ls_vs_mech"])
        g6 = [r for r in vs if r["Source"] == "LS-DYNA 12B G6 (extension)"]
        if len(g6) != 1:
            raise ImportFailure("MECHANICAL_vs_LSDYNA.csv: expected exactly one 'LS-DYNA 12B G6' row")
        run = "P00:lsdyna:linear_eigen"
        self.add_run(run, "P00", "LS-DYNA", V_LSDYNA, "linear_eigenvalue_buckling", NO_LABEL, S["ls_vs_mech"], "12B G6",
                     LIM_EIGEN, load_case="LC2")
        self.add_result(run, "buck.eig_lambda1", imp["lambda_eig"], S["ls_imperf"], "12B G6", "json key 'lambda_eig'")
        self.add_result(run, "buck.eig_pcr", num(g6[0]["Value [kN]"]), S["ls_vs_mech"], "12B G6", "column 'Value [kN]'")

        sens = self.rows(S["ls_sens"], key=LC["case"])
        for r in sens:
            code = r[LC["case"]]
            a = float(r[LC["amp"]])
            ref = r[LC["role"]].startswith("reference")
            self.add_case(code, "lsdyna_imperfection",
                          f"LS-DYNA nonlinear thermal buckling, imperfection amplitude A = {a:g} mm"
                          + (" (perfect-geometry reference path)" if ref else ""),
                          "reference" if ref else "solved", S["ls_sens"], code, parent="P00")
            self.add_param(code, "imperfection_amplitude", a, "mm", S["ls_sens"], f"column '{LC['amp']}'")
            q = qc[code]
            run = f"{code}:lsdyna:nonlinear"
            ok = bool(q["normal"])
            warn = ""
            if q["warnings"]:  # Warning 60120 is documented as a performance-only warning (FINAL_12C_RESULTS.md section 2)
                known = {"60120": "out-of-core factorisation; affects run time only, results reproduced bit-for-bit (FINAL_12C_RESULTS.md section 2)"}
                warn = "; solver warnings in the run record: " + ", ".join(
                    f"{w} ({known[w]})" if w in known else f"{w} (not explained in the source files)" for w in q["warnings"])
            self.add_run(run, code, "LS-DYNA", V_LSDYNA, "nonlinear_implicit_thermal_buckling",
                         "normal termination" if ok else "abnormal termination", S["ls_qc"], code, LIM_NONLIN, load_case="LC2")
            self.add_check(code, run, "source_recorded", "normal_termination", "PASS" if ok else "FAIL",
                           f"{q['steps']} steps; equilibrium iterations per step min {q['iters_min']} / max {q['iters_max']} / "
                           f"mean {q['iters_mean']}{warn}", S["ls_qc"],
                           observed=float(q["steps"]), units="steps")
            self.add_check(code, run, "source_recorded", "reaction_balance_max", "INFO",
                           "largest relative imbalance of inlet and outlet reactions over the run", S["ls_qc"],
                           observed=q["reac_balance_max"], units="fraction of N")
            self.add_check(code, run, "source_recorded", "instability_identification", "INFO", r[LC["char"]], S["ls_sens"],
                           source_status=f"interior_peak={r[LC['interior']]}")
            self.ls_results(code, run, r, q)
            self.series_crosscheck(code, run, r)
        for code in sorted(self.case_id_unrun()):
            self.not_run(code, imp)

    def case_id_unrun(self):
        base = self.repo / LSD / "runs"
        return [p.name for p in base.iterdir() if (p / "NOT_RUN.txt").is_file()]

    def not_run(self, code, imp):
        rel = LS_NOT_RUN.format(case=code)
        reason = " ".join(self.text(rel, "run_record").split())
        key = re.search(r"A(\d)p(\d)", code)
        key = f"A{key.group(1)}p{key.group(2)}" if key else None
        a = imp["files"][key]["A_mm"] if key in imp["files"] else (0.0 if key == "A0p0" else None)
        self.add_case(code, "lsdyna_imperfection", "Planned LS-DYNA case, not run", "not_run", rel, code, parent="P00")
        if a is not None:
            self.add_param(code, "imperfection_amplitude", a, "mm", S["ls_imperf"] if key in imp["files"] else rel,
                           f"json files.{key}.A_mm" if key in imp["files"] else "case name A0p0 (no imperfection)")
        run = f"{code}:lsdyna:nonlinear"
        self.add_run(run, code, "LS-DYNA", V_LSDYNA, "nonlinear_implicit_thermal_buckling", "not_run", rel, code,
                     LIM_NONLIN, load_case="LC2")
        self.add_check(code, run, "data_gap", "case_not_run", "NOT_AVAILABLE", reason, rel)

    def ls_results(self, code, run, r, q):
        f = S["ls_sens"]
        yl, util = num(r[LC["yl"]]), num(r[LC["util"]])

        def validity(lam):  # elastic-model validity of a state at load factor lam, from the source's own indicator
            if yl is None:
                return "within_elastic_range" if util <= 1 else "not_assessed"
            return "within_elastic_range" if lam <= yl else "beyond_yield_elastic_model_not_physical"

        def put(metric, col, v, **kw):
            self.add_result(run, metric, v, f, code, f"column '{LC[col]}'", **kw)

        lam_nmax = num(r[LC["lam_nmax"]])
        put("lsdyna.n_max", "nmax", num(r[LC["nmax"]]), validity=validity(lam_nmax), note=r[LC["char"]])
        put("lsdyna.lambda_at_n_max", "lam_nmax", lam_nmax, validity=validity(lam_nmax))
        put("lsdyna.n_max_is_interior_max", "interior", 1.0 if r[LC["interior"]].strip() == "True" else 0.0,
            validity=validity(lam_nmax))
        put("lsdyna.n_at_lambda1p3", "n13", num(r[LC["n13"]]), validity=validity(1.3))
        put("lsdyna.lateral_max_at_lambda1p3", "lat13", num(r[LC["lat13"]]), validity=validity(1.3))
        put("lsdyna.end_sway_at_lambda1p3", "sway13", num(r[LC["sway13"]]), validity=validity(1.3))
        put("lsdyna.vm_at_lambda1", "vm_l1", num(r[LC["vm_l1"]]), validity=validity(1.0))
        put("lsdyna.vm_max_end_region", "vm_max", num(r[LC["vm_max"]]),
            validity="within_elastic_range" if util <= 1 else "beyond_yield_elastic_model_not_physical")
        put("lsdyna.util_max", "util", util)
        self.add_result(run, "lsdyna.n_at_lambda1", q["N_lam1_kN"], S["ls_qc"], code, "json key 'N_lam1_kN'",
                        validity=validity(1.0))
        # Southwell family and onset: blank in the source for the perfect-geometry reference
        for metric, col in (("lsdyna.southwell_ncr", "sw"), ("lsdyna.southwell_r2", "sw_r2"), ("lsdyna.southwell_w0", "sw_w0")):
            v = num(r[LC[col]])
            if v is None:
                put(metric, col, None, status="not_identifiable" if col == "sw" else "not_available",
                    reason=("no characteristic load identifiable for the perfect-geometry reference (blank in source): "
                            + r[LC["char"]]) if col == "sw" else "blank in source (no Southwell fit for this case)")
            else:
                put(metric, col, v)
        rng = r[LC["sw_rng"]].strip()
        for metric, idx in (("lsdyna.southwell_window_low", 0), ("lsdyna.southwell_window_high", 1)):
            if rng:
                put(metric, "sw_rng", float(rng.split("-")[idx].strip()))
            else:
                put(metric, "sw_rng", None, status="not_available", reason="blank in source (no Southwell fit for this case)")
        for metric, col in (("lsdyna.onset_lambda", "on_l"), ("lsdyna.onset_n", "on_n")):
            v = num(r[LC[col]])
            if v is None:
                put(metric, col, None, status="not_available",
                    reason="defined relative to the perfect-geometry path, which is this case (blank in source)")
            else:
                put(metric, col, v, validity=validity(num(r[LC["on_l"]])))
        for metric, col in (("lsdyna.yield_indicator_lambda", "yl"), ("lsdyna.yield_indicator_n", "yn")):
            v = num(r[LC[col]])
            if v is None:
                put(metric, col, None, status="not_reached",
                    reason=f"VM/S_y(T) never reached 1 within lambda <= 1.3 (max {util:g}); blank in source")
            else:
                put(metric, col, v)

    def series_crosscheck(self, code, run, r):
        """Second extraction of N(lambda) in results/series: compare N_max and its lambda with the summary table."""
        rows = self.rows(LS_SERIES.format(case=code), "run_record")
        best = max(rows, key=lambda x: float(x["Fz_in_N"]))
        n_series, lam_series = float(best["Fz_in_N"]) / 1000, float(best["lambda"])
        n_sum, lam_sum = num(r[LC["nmax"]]), num(r[LC["lam_nmax"]])
        src = LS_SERIES.format(case=code)
        self.add_check(code, run, "import_crosscheck", "n_max_vs_series_extraction",
                       "PASS" if abs(n_series - n_sum) <= 0.007 else "DISCREPANCY",
                       "N_max in the summary table vs the maximum of Fz_in_N in results/series. Tolerance 7 N = the documented "
                       "agreement between ASCII and binout reaction extractions (FINAL_12C_RESULTS.md section 9).",
                       src, observed=n_series, reference=n_sum, tol=0.007, units="kN")
        same = abs(lam_series - lam_sum) < 1e-9
        self.add_check(code, run, "import_crosscheck", "lambda_at_n_max_vs_series_extraction",
                       "PASS" if same else "DISCREPANCY",
                       "lambda at N_max: summary table vs argmax of Fz_in_N in results/series. "
                       + ("Agree." if same else
                          f"Summary and the binout N file place the maximum at lambda {lam_sum:g}; the series extraction at "
                          f"lambda {lam_series:g}, one fine load step (0.005) away, on a flat maximum (N within "
                          f"{abs(n_series - n_sum) * 1000:.1f} N across the two, including the 0.01 kN rounding of the "
                          f"summary table). Both kept; the summary value is the reported one."),
                       src, observed=lam_series, reference=lam_sum, tol=0.0, units="-")

    def add_gaps(self):
        """Per run type, list metrics that other runs of the same type have but this run has not."""
        q = self.con.execute(
            "SELECT r.run_id, r.run_code, r.case_id, r.source_file_id, r.solver, r.analysis_type, COALESCE(r.load_case,'')"
            " FROM solver_runs r ORDER BY r.run_id").fetchall()
        have = {}
        for rid, mid in self.con.execute("SELECT run_id, metric_id FROM simulation_results"):
            have.setdefault(rid, set()).add(mid)
        groups = {}
        for rid, code, cid, sid, solver, at, lc in q:
            if rid in have:
                groups.setdefault((solver, at, lc), set()).update(have[rid])
        for rid, code, cid, sid, solver, at, lc in q:
            if rid not in have:
                continue
            miss = sorted(groups[(solver, at, lc)] - have[rid])
            if miss:
                case = self.con.execute("SELECT case_code FROM simulation_cases WHERE case_id=?", (cid,)).fetchone()[0]
                src = self.con.execute("SELECT repo_path FROM source_files WHERE source_file_id=?", (sid,)).fetchone()[0]
                self.add_check(case, code, "data_gap", "metrics_not_recorded", "NOT_AVAILABLE",
                               "No value in the imported source files for: " + ", ".join(miss), src)

    def run_all(self):
        self.load_metrics()
        self.load_baseline()
        self.load_cfd_and_structural_cases()
        self.load_cfd_mesh_study()
        self.load_cfd_parametric()
        self.load_structural()
        self.load_support()
        self.load_lsdyna()
        self.add_gaps()


def build(repo: Path, db: Path, importer_cls=Importer) -> dict:
    """Build into a temporary file inside one transaction; move into place only on success."""
    db.parent.mkdir(parents=True, exist_ok=True)
    tmp = db.with_name(db.name + ".partial")
    if tmp.exists():
        tmp.unlink()
    con = sqlite3.connect(tmp, isolation_level=None)  # explicit transaction control
    try:
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript((HERE / "schema.sql").read_text(encoding="utf-8"))
        con.execute("BEGIN")
        imp = importer_cls(repo, con)
        imp.run_all()
        bad = con.execute("PRAGMA foreign_key_check").fetchall()
        if bad:
            raise ImportFailure(f"foreign key violations: {bad[:3]}")
        con.execute("COMMIT")
        con.close()
        os.replace(tmp, db)
        return imp.n
    except BaseException:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        con.close()
        if tmp.exists():
            tmp.unlink()
        raise


def v_status(db, case, name):
    return db.execute("SELECT v.status FROM validation_checks v JOIN simulation_cases c USING (case_id)"
                      " WHERE c.case_code = ? AND v.check_name = ?", (case, name)).fetchone()[0]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", type=Path, default=DEFAULT_REPO, help="repository root (default: parent of this folder)")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="output database path")
    a = ap.parse_args(argv)
    try:
        counts = build(a.repo.resolve(), a.db.resolve())
    except (ImportFailure, sqlite3.Error, KeyError, ValueError) as e:
        print(f"IMPORT FAILED, rolled back, no database written: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print(f"Database written: {a.db.name} ({a.db.stat().st_size} bytes)")
    for t, n in counts.items():
        print(f"  {t:<20}{n:>6}")
    db = sqlite3.connect(a.db)
    print(f"  {'source_files':<20}{db.execute('SELECT COUNT(*) FROM source_files').fetchone()[0]:>6}")
    for case, name in db.execute("SELECT c.case_code, v.check_name FROM validation_checks v JOIN simulation_cases c USING (case_id)"
                                 " WHERE v.status IN ('DISCREPANCY','FAIL')"):
        print(f"  note: {v_status(db, case, name)} kept for review: {case} / {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
