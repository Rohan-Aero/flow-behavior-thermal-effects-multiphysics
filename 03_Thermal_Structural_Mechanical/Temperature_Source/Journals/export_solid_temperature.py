# -*- coding: utf-8 -*-
"""Section 7A - READ-ONLY export of the converged medium-mesh solid temperature field.

Runs inside Fluent (fluent 3ddp -g -py -i ...) with the working directory
07_Thermal_Analysis/Temperature_Source. It READS the Section 5B official case and data and never writes to
06_Fluent_CFD (no write_case, no write_data, no iterate). The case/data SHA-256 are recorded by the driver
before and after the run.

Outputs (all in 07_Thermal_Analysis/Temperature_Source):
  Audit/source_verification.json        read-back of the settings that define the field + Fluent's own reports
  fluent_solid_cells.csv                every solid cell (43,200): centre x,y,z and cell temperature
  fluent_solid_face_<zone>.csv          solid boundary faces: face-centroid x,y,z, face temperature, heat flux
  fluent_solid_node_<zone>.csv          same boundaries, Fluent node values (validation only)
RE-ANALYSIS 2026 - newly generated export of a newly generated CFD solution.
"""
import os, sys, json
sys.path.insert(0, "Journals")
from s5_common import *
from s5_common import _close

CASE = "../../06_Fluent_CFD/Case/baseline_medium_final.cas.h5"
DATA = "../../06_Fluent_CFD/Data/baseline_medium_final.dat.h5"
NZ, LEN, EXPECT_SOLID = 90, 0.600, 43200
FINAL_SCHEMES = {"pressure": "second-order", "mom": "second-order-upwind", "k": "second-order-upwind",
                 "omega": "second-order-upwind", "temperature": "second-order-upwind"}
INC_T = [293.15, 373.15, 473.15, 573.15, 673.15]
INC_K = [11.5, 12.1, 13.5, 15.2, 17.1]
INC_CP = [460.0, 458.0, 468.0, 485.0, 501.0]

log("=" * 80)
log("SECTION 7A - READ-ONLY EXPORT OF THE MEDIUM SOLID TEMPERATURE FIELD - RE-ANALYSIS 2026")
log("=" * 80)
solver.file.batch_options.confirm_overwrite = False
step("transcript", lambda: solver.file.start_transcript(file_name="Logs/source_transcript.trn"), critical=False)
step("read case  " + CASE, lambda: solver.file.read_case(file_name=CASE))
step("read data  " + DATA, lambda: solver.file.read_data(file_name=DATA))

G = solver.setup.general
M = solver.setup.models
inc = solver.setup.materials.solid["inconel-718"]
W = solver.setup.boundary_conditions.wall
S = solver.solution
ds = S.methods.spatial_discretization.discretization_scheme
ROWS = []


def chk(name, fn, expect=None, info=False):
    try:
        got = fn()
        if info:
            ok = True
        elif isinstance(expect, float):
            ok = _close(got, expect)
        elif callable(expect):
            ok = bool(expect(got))
        else:
            ok = (got == expect)
    except Exception as e:
        got, ok = "ERROR %s" % e, False
    ROWS.append({"item": name, "value": got, "expected": "(recorded)" if info else (
        expect if not callable(expect) else "see check"), "ok": ok})
    log("CHECK %-4s %-46s %s" % ("ok" if ok else "FAIL", name, repr(got)[:100]))


def pw(prop):
    return [(d["item"], d["value"]) for d in prop.piecewise_linear.data_points()]


chk("fluent version", lambda: solver.get_fluent_version(), info=True)
chk("solver time", lambda: G.solver.time(), "steady")
chk("energy equation", lambda: M.energy.enabled(), True)
chk("viscous model", lambda: (M.viscous.model(), M.viscous.k_omega_model()), ("k-omega", "sst"))
chk("solid cell zones", lambda: sorted(solver.setup.cell_zone_conditions.solid.get_object_names()), ["solid_domain"])
chk("solid zone material", lambda: solver.setup.cell_zone_conditions.solid["solid_domain"].general.material(),
    "inconel-718")
chk("Inconel density [kg/m3]", lambda: (inc.density.option(), inc.density.value()), ("value", 8190.0))
chk("Inconel k piecewise-linear = VDM 4127", lambda: pw(inc.thermal_conductivity),
    lambda g: len(g) == 5 and all(_close(a, t, 1e-9) and _close(b, v, 1e-9) for (a, b), t, v in zip(g, INC_T, INC_K)))
chk("Inconel cp piecewise-linear = VDM 4127", lambda: pw(inc.specific_heat),
    lambda g: len(g) == 5 and all(_close(a, t, 1e-9) and _close(b, v, 1e-9) for (a, b), t, v in zip(g, INC_T, INC_CP)))
for k, v in FINAL_SCHEMES.items():
    chk("scheme %s (final, second order)" % k, (lambda kk=k: ds[kk]()), v)
chk("heated wall", lambda: (W["heated_outer_wall"].thermal.thermal_condition(),
                            W["heated_outer_wall"].thermal.heat_flux.value()), ("Heat Flux", 8000.0))
chk("interface coupling", lambda: (W["fluid_solid_interface"].thermal.thermal_condition(),
                                   W["fluid_solid_interface-shadow"].thermal.thermal_condition()),
    ("Coupled", "Coupled"))
chk("solid ends adiabatic", lambda: (W["solid_inlet_end"].thermal.heat_flux.value(),
                                     W["solid_outlet_end"].thermal.heat_flux.value()), (0.0, 0.0))
chk("solution limits (temperature)", lambda: S.controls.limits(), info=True)
chk("equations solved", lambda: S.controls.equations(), info=True)

# Fluent's own report definitions evaluated on the loaded data (no iteration)
REP = {}


def compute_reports():
    names = ["T_solid_max", "T_solid_min", "T_solid_mean", "T_outer_max", "T_wall_max", "T_inner_avg",
             "T_outer_avg", "q_heated_wall", "q_interface", "q_net_all"]
    out = S.report_definitions.compute(report_defs=names)
    for d in out:
        for k, v in d.items():
            REP[k] = v
    return REP


step("Fluent report definitions on the loaded data", compute_reports, critical=False)

# ---------------------------------------------------------------------------
# exports (cell-centre and face-centroid values carry the solver's own numbers: no interpolation)
# ---------------------------------------------------------------------------
EXP = solver.file.export.ascii
ISO = solver.results.surfaces.iso_surface
dz = LEN / NZ


def make_iso(name, zval):
    try:
        ISO.create(name)
    except Exception:
        ISO[name] = {}
    o = ISO[name]
    o.field = "z-coordinate"
    o.zones = ["solid_domain"]
    o.iso_values = [zval]
    return None


names = []
for k in range(NZ):
    nm = "zs%02d" % k
    if step("iso %s z=%.6f" % (nm, (k + 0.5) * dz), (lambda n=nm, z=(k + 0.5) * dz: make_iso(n, z)),
            critical=(k == 0)) is None:
        names.append(nm)
SQ = ["cell-zone", "cell-volume", "radial-coordinate", "temperature", "thermal-conductivity-lam"]
step("export solid cells", lambda: EXP(file_name="fluent_solid_cells.csv", surface_name_list=names,
                                       delimiter="comma", quantities=SQ, location="cell-center"))
FQ = ["face-area-magnitude", "radial-coordinate", "temperature", "heat-flux"]
for zone in ("heated_outer_wall", "fluid_solid_interface-shadow", "solid_inlet_end", "solid_outlet_end"):
    step("export faces %s" % zone, (lambda z=zone: EXP(file_name="fluent_solid_face_%s.csv" % z,
                                                        surface_name_list=[z], delimiter="comma",
                                                        quantities=FQ, location="cell-center")))
    step("export nodes %s" % zone, (lambda z=zone: EXP(file_name="fluent_solid_node_%s.csv" % z,
                                                        surface_name_list=[z], delimiter="comma",
                                                        quantities=["radial-coordinate", "temperature"],
                                                        location="node")), critical=False)


def count(path):
    n = 0
    with open(path) as fh:
        fh.readline()
        for _ in fh:
            n += 1
    return n


CNT = {}
for p in ["fluent_solid_cells.csv"] + ["fluent_solid_face_%s.csv" % z for z in
                                       ("heated_outer_wall", "fluid_solid_interface-shadow",
                                        "solid_inlet_end", "solid_outlet_end")]:
    try:
        CNT[p] = count(p)
        log("ROWS %-50s %d" % (p, CNT[p]))
    except Exception as e:
        CNT[p] = "ERROR %s" % e
write_json("Audit/source_verification.json", {"case": CASE, "data": DATA, "checks": ROWS, "fluent_reports": REP,
                                              "row_counts": CNT, "expected_solid_cells": EXPECT_SOLID,
                                              "failures": FAIL})
log("CHECKS %d, failed %d; step failures %d" % (len(ROWS), sum(1 for r in ROWS if not r["ok"]), len(FAIL)))
for f in FAIL:
    log("   " + f)
flush_log("Logs/source_log.txt")
step("stop transcript", lambda: solver.file.stop_transcript(), critical=False)
print("S7A-SOURCE-DONE")
exit()
