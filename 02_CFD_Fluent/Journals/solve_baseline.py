# ============================================================================
# Section 5B - OFFICIAL BASELINE SOLVE, medium mesh (159,840 cells)
# Project : Flow Behavior and Thermal Effects in Multiphysics Systems
#           RE-ANALYSIS 2026 - no original internship artefact is reproduced here.
#
# Run from 06_Fluent_CFD:   fluent 3ddp -g -py -t4 -i Journals/solve_baseline.py
#
# Sequence
#   0. read the Section 5A setup case (configured, never iterated)
#   1. mandatory corrections, each verified by READING BACK from Fluent
#   2. pre-solve setup audit  -> any mismatch STOPS the run before a single iteration
#   3. stage 1: flow + turbulence only, first order         (startup stabilisation)
#   4. stage 2: energy switched on, first order              (thermal field develops)
#   5. stage 3: ONE switch to second-order upwind, audited, iterate to convergence
#   6. convergence = NR-03 residuals AND physical plateau AND conservation, confirmed
#      again after a further 100 iterations
#   7. write case/data, Fluent's own flux reports, ASCII exports of the solution
#
# Nothing in this file tunes geometry, heat flux, inlet velocity, material
# properties, outlet pressure or the turbulence model toward the analytical answer.
# ============================================================================
import os, sys, math, re, json
sys.path.insert(0, "Journals")
from s5_common import *
from s5_common import _close   # underscore names are not exported by import *

TAG = os.environ.get("BASE_TAG", "baseline")
STDOUT = "Logs/%s_stdout.txt" % TAG
TRN = "Logs/%s_transcript.trn" % TAG
MON = "Monitors/baseline_monitors.out"

FLOW_IT = 150
ENERGY_IT = 150
CHUNK = 100
MAX_STAGE3 = 3000
WINDOW = 200

# ---- frozen baseline (02_Engineering_Calculations/baseline_parameters.json)
P_OP, T_IN, V_IN, QPP = 101325.0, 300.0, 23.5, 8000.0
INC_RHO = 8190.0
AIR_T = [250.0, 300.0, 350.0, 400.0, 450.0, 500.0, 550.0, 600.0]
AIR_CP = [1006.0, 1007.0, 1009.0, 1014.0, 1021.0, 1030.0, 1040.0, 1051.0]
AIR_MU = [1.596e-5, 1.846e-5, 2.082e-5, 2.301e-5, 2.507e-5, 2.701e-5, 2.884e-5, 3.058e-5]
AIR_K = [0.02227, 0.02624, 0.03003, 0.03365, 0.03707, 0.04038, 0.04360, 0.04659]
INC_T = [293.15, 373.15, 473.15, 573.15, 673.15]
INC_CP = [460.0, 458.0, 468.0, 485.0, 501.0]
INC_K = [11.5, 12.1, 13.5, 15.2, 17.1]
TI = 0.16 * 29957.0 ** (-0.125)

# ---- NR-03 / NR-04 and the additional engineering plateau criteria
RES_TARGET = {"continuity": 1e-4, "x-velocity": 1e-4, "y-velocity": 1e-4, "z-velocity": 1e-4,
              "k": 1e-4, "omega": 1e-4, "energy": 1e-6}
ABS_DRIFT_K = {"T_out_bulk": 0.1, "T_solid_max": 0.1, "T_wall_max": 0.1, "T_outer_max": 0.1}
REL_DRIFT = {"dp_area": 1e-3, "q_interface": 1e-3, "mdot_out": 1e-4}
MASS_TOL = 1e-4      # |mdot_in - mdot_out| / mdot_in
ENERGY_TOL = 5e-3    # |sum of boundary heat flows| / Q_wall  (EXPECTED_RESULTS: < 0.5 %)

log("=" * 80)
log("SECTION 5B OFFICIAL BASELINE SOLVE - RE-ANALYSIS 2026")
log("=" * 80)
solver.file.batch_options.confirm_overwrite = False
step("transcript", lambda: solver.file.start_transcript(file_name=TRN), critical=False)

# ---------------------------------------------------------------------------
# 0. read the setup case
# ---------------------------------------------------------------------------
step("read Section 5A setup case", lambda: solver.file.read_case(file_name="Baseline_Setup/baseline_setup.cas.h5"))
step("mesh check", lambda: solver.mesh.check())

G = solver.setup.general
M = solver.setup.models
air = solver.setup.materials.fluid["air"]
inc = solver.setup.materials.solid["inconel-718"]
BC = solver.setup.boundary_conditions
W = BC.wall
inl = BC.velocity_inlet["fluid_inlet"]
out = BC.pressure_outlet["fluid_outlet"]
S = solver.solution
ds = S.methods.spatial_discretization.discretization_scheme
RD = S.report_definitions

# ---------------------------------------------------------------------------
# 1. mandatory corrections
# ---------------------------------------------------------------------------
# 1A. Inconel density. The Section 5A first dry run wrote option "constant" (not a valid
# name here; the valid name is "value") and the material silently kept aluminium's
# 2719 kg/m3. That was corrected before the 5A test solve. It is re-asserted here and
# proven by read-back regardless, because an assignment that raises nothing is not proof.
def fix_density():
    inc.density.option = "value"
    inc.density.value = INC_RHO
    got_opt = inc.density.option()
    got = inc.density.value()
    if got_opt != "value" or not _close(got, INC_RHO):
        raise RuntimeError("Inconel density read back as %r / %r" % (got_opt, got))
    return {"option": got_opt, "value_kg_m3": got}


step("1A Inconel 718 density = 8190 kg/m3 (read back)", fix_density)

# 1C. Startup stabilisation. Section 5A started flow and energy together from a uniform
# field: the solid overshot to 761 K before the fluid thermal field could carry the heat
# away. The startup study (Monitors/trial_A.out) showed that simply solving flow +
# turbulence first, then switching energy on, removes the overshoot entirely - the solid
# then approaches its steady temperature monotonically from below. That is the smallest
# intervention available: it changes the ORDER in which equations are switched on and
# nothing else. No relaxation factor, pseudo-time scale, limiter or boundary condition
# is altered. It is applied in stage 1 below.

# ---------------------------------------------------------------------------
# monitors
# ---------------------------------------------------------------------------
def mk(container, name, rtype, **kw):
    c = getattr(RD, container)
    try:
        c.create(name)
    except Exception:
        c[name] = {}
    o = c[name]
    if rtype is not None:
        o.report_type = rtype
    for k, v in kw.items():
        setattr(o, k, v)
    return name


NEW = []
for args in [
    ("surface", "p_in_area", "surface-areaavg", dict(field="pressure", surface_names=["fluid_inlet"])),
    ("surface", "p_out_area", "surface-areaavg", dict(field="pressure", surface_names=["fluid_outlet"])),
    ("surface", "T_in_bulk", "surface-massavg", dict(field="temperature", surface_names=["fluid_inlet"])),
    ("surface", "T_outer_max", "surface-facetmax", dict(field="temperature", surface_names=["heated_outer_wall"])),
    ("surface", "T_outer_avg", "surface-areaavg", dict(field="temperature", surface_names=["heated_outer_wall"])),
    ("surface", "T_inner_avg", "surface-areaavg", dict(field="temperature", surface_names=["fluid_solid_interface"])),
    ("surface", "yplus_min", "surface-facetmin", dict(field="y-plus", surface_names=["fluid_solid_interface"])),
    ("surface", "yplus_avg", "surface-areaavg", dict(field="y-plus", surface_names=["fluid_solid_interface"])),
    ("surface", "area_in", "surface-area", dict(surface_names=["fluid_inlet"])),
    ("volume", "T_fluid_max", "volume-max", dict(field="temperature", cell_zones=["fluid_domain"])),
    ("volume", "T_fluid_min", "volume-min", dict(field="temperature", cell_zones=["fluid_domain"])),
    ("volume", "T_solid_min", "volume-min", dict(field="temperature", cell_zones=["solid_domain"])),
    ("flux", "q_ends", "flux-heattransfer", dict(boundaries=["solid_inlet_end", "solid_outlet_end"])),
    ("flux", "q_net_all", "flux-heattransfer",
     dict(boundaries=["fluid_inlet", "fluid_outlet", "heated_outer_wall", "solid_inlet_end", "solid_outlet_end"])),
]:
    r = step("report %s" % args[1], (lambda a=args: mk(a[0], a[1], a[2], **a[3])), critical=False)
    if r:
        NEW.append(r)


def mk_force():
    c = RD.force
    try:
        c.create("F_wall_z")
    except Exception:
        c["F_wall_z"] = {}
    o = c["F_wall_z"]
    o.force_vector = [0, 0, 1]
    o.zones = ["fluid_solid_interface"]
    return o()


if step("report F_wall_z (axial wall force)", mk_force, critical=False):
    NEW.append("F_wall_z")

OLD = ["mdot_in", "mdot_out", "mass_imbalance", "q_heated_wall", "q_interface", "q_fluid_net",
       "p_in", "p_out", "T_out_bulk", "T_wall_max", "T_solid_max", "T_solid_mean", "v_out_max", "yplus_max"]
ALLDEFS = OLD + NEW
rf = S.monitor.report_files["s5a_monitors"]
step("monitor file -> %s" % MON, lambda: setattr(rf, "file_name", MON))
step("monitor file report list (%d)" % len(ALLDEFS), lambda: setattr(rf, "report_defs", ALLDEFS))
step("monitor file state", lambda: rf())

# ---------------------------------------------------------------------------
# 2. SETUP AUDIT - read everything back; a single mismatch stops the run
# ---------------------------------------------------------------------------
def pw_state(prop):
    return [(d["item"], d["value"]) for d in prop.piecewise_linear.data_points()]


def curve_ok(got, T, V):
    return len(got) == len(T) and all(_close(a, t, 1e-9) and _close(b, v, 1e-9)
                                      for (a, b), t, v in zip(got, T, V))


def audit(label, schemes_expected):
    rows = []

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
        rows.append({"item": name, "value": got,
                     "expected": ("(recorded)" if info else (expect if not callable(expect) else "see check")),
                     "ok": ok})

    chk("fluent version", lambda: solver.get_fluent_version(), info=True)
    chk("solver type", lambda: G.solver.type(), "pressure-based")
    chk("time", lambda: G.solver.time(), "steady")
    chk("velocity formulation", lambda: G.solver.velocity_formulation(), "absolute")
    chk("operating pressure [Pa]", lambda: G.operating_conditions.operating_pressure(), P_OP)
    chk("gravity enabled", lambda: G.operating_conditions.gravity()["enable"], False)
    chk("energy equation", lambda: M.energy.enabled(), True)
    chk("energy: viscous dissipation", lambda: M.energy.viscous_dissipation(), info=True)
    chk("energy: pressure work", lambda: M.energy.pressure_work(), info=True)
    chk("energy: kinetic energy", lambda: M.energy.kinetic_energy(), info=True)
    chk("viscous model", lambda: M.viscous.model(), "k-omega")
    chk("k-omega variant", lambda: M.viscous.k_omega_model(), "sst")
    chk("SST wall omega treatment", lambda: M.viscous.near_wall_treatment.wall_omega_treatment(), info=True)
    chk("SST low-Re correction", lambda: M.viscous.k_omega.k_omega_low_re_correction(), info=True)
    chk("radiation model", lambda: M.radiation.model(), "none")
    chk("air density model", lambda: air.density.option(), "incompressible-ideal-gas")
    chk("air molecular weight", lambda: air.molecular_weight.value(), 28.966)
    chk("air cp model", lambda: air.specific_heat.option(), "piecewise-linear")
    chk("air cp curve = Incropera A.4", lambda: curve_ok(pw_state(air.specific_heat), AIR_T, AIR_CP), True)
    chk("air mu model", lambda: air.viscosity.option(), "piecewise-linear")
    chk("air mu curve = Incropera A.4", lambda: curve_ok(pw_state(air.viscosity), AIR_T, AIR_MU), True)
    chk("air k model", lambda: air.thermal_conductivity.option(), "piecewise-linear")
    chk("air k curve = Incropera A.4", lambda: curve_ok(pw_state(air.thermal_conductivity), AIR_T, AIR_K), True)
    chk("Inconel density option", lambda: inc.density.option(), "value")
    chk("Inconel density [kg/m3]", lambda: inc.density.value(), INC_RHO)
    chk("Inconel k model", lambda: inc.thermal_conductivity.option(), "piecewise-linear")
    chk("Inconel k curve = VDM 4127", lambda: curve_ok(pw_state(inc.thermal_conductivity), INC_T, INC_K), True)
    chk("Inconel cp model", lambda: inc.specific_heat.option(), "piecewise-linear")
    chk("Inconel cp curve = VDM 4127", lambda: curve_ok(pw_state(inc.specific_heat), INC_T, INC_CP), True)
    chk("fluid zone material", lambda: solver.setup.cell_zone_conditions.fluid["fluid_domain"].general.material(), "air")
    chk("solid zone material", lambda: solver.setup.cell_zone_conditions.solid["solid_domain"].general.material(), "inconel-718")
    chk("inlet velocity spec", lambda: inl.momentum.velocity_specification_method(), "Magnitude, Normal to Boundary")
    chk("inlet velocity [m/s]", lambda: inl.momentum.velocity_magnitude.value(), V_IN)
    chk("inlet temperature [K]", lambda: inl.thermal.temperature.value(), T_IN)
    chk("inlet turbulence spec", lambda: inl.turbulence.turbulence_specification(), "Intensity and Hydraulic Diameter")
    chk("inlet turbulent intensity [-]", lambda: readv(inl.turbulence, "turbulent_intensity"), TI)
    chk("inlet hydraulic diameter [m]", lambda: readv(inl.turbulence, "hydraulic_diameter"), 0.02)
    chk("outlet gauge pressure [Pa]", lambda: out.momentum.gauge_pressure.value(), 0.0)
    # With prevent_reverse_flow on, Fluent deactivates the backflow temperature and backflow
    # turbulence entirely (read back in the 5B probe): they cannot act unless reverse flow
    # occurs, and reverse flow is suppressed. Audit the switch that governs them instead.
    chk("outlet prevent reverse flow", lambda: out.momentum.prevent_reverse_flow(), True)
    chk("outlet backflow T branch active", lambda: out.thermal.backflow_total_temperature.is_active(), info=True)
    chk("heated wall condition", lambda: W["heated_outer_wall"].thermal.thermal_condition(), "Heat Flux")
    chk("heated wall flux [W/m2]", lambda: W["heated_outer_wall"].thermal.heat_flux.value(), QPP)
    chk("solid inlet end", lambda: (W["solid_inlet_end"].thermal.thermal_condition(),
                                    W["solid_inlet_end"].thermal.heat_flux.value()), ("Heat Flux", 0))
    chk("solid outlet end", lambda: (W["solid_outlet_end"].thermal.thermal_condition(),
                                     W["solid_outlet_end"].thermal.heat_flux.value()), ("Heat Flux", 0))
    chk("interface thermal coupling", lambda: W["fluid_solid_interface"].thermal.thermal_condition(), "Coupled")
    chk("interface shadow coupling", lambda: W["fluid_solid_interface-shadow"].thermal.thermal_condition(), "Coupled")
    chk("p-v coupling", lambda: S.methods.p_v_coupling.flow_scheme(), "Coupled")
    chk("gradient scheme", lambda: S.methods.spatial_discretization.gradient_scheme(), "least-square-cell-based")
    for k, v in schemes_expected.items():
        chk("scheme %s" % k, (lambda kk=k: ds[kk]()), v)
    chk("pseudo-time formulation", lambda: S.methods.pseudo_time_method.formulation.coupled_solver(), "global-time-step")
    chk("pseudo-time step settings", lambda: S.run_calculation.pseudo_time_settings.time_step_method(), info=True)
    chk("explicit pseudo relaxation", lambda: S.controls.pseudo_time_explicit_relaxation_factor(), info=True)
    chk("explicit p/mom under-relaxation", lambda: S.controls.p_v_controls(), info=True)
    chk("solution limits", lambda: S.controls.limits(), info=True)
    chk("equations solved", lambda: S.controls.equations(), info=True)

    bad = [r for r in rows if not r["ok"]]
    write_json("Audit/setup_audit_%s.json" % label, {"label": label, "n_items": len(rows),
                                                     "n_failed": len(bad), "rows": rows})
    with open("Audit/setup_audit_%s.txt" % label, "w") as fh:
        fh.write("SETUP AUDIT - %s - values READ BACK from Fluent\n" % label)
        fh.write("%d items, %d failed\n\n" % (len(rows), len(bad)))
        for r in rows:
            fh.write("%-4s %-34s %s\n" % ("ok" if r["ok"] else "FAIL", r["item"], repr(r["value"])[:150]))
    for r in rows:
        log("AUDIT %-4s %-34s %s" % ("ok" if r["ok"] else "FAIL", r["item"], repr(r["value"])[:100]))
    log("AUDIT %s: %d items, %d failed" % (label, len(rows), len(bad)))
    return bad


STARTUP_SCHEMES = {"pressure": "second-order", "mom": "first-order-upwind", "k": "first-order-upwind",
                   "omega": "first-order-upwind", "temperature": "first-order-upwind"}
FINAL_SCHEMES = {"pressure": "second-order", "mom": "second-order-upwind", "k": "second-order-upwind",
                 "omega": "second-order-upwind", "temperature": "second-order-upwind"}

bad = audit("1_presolve", STARTUP_SCHEMES)
if bad or [f for f in FAIL if f.startswith("CRITICAL")]:
    log("PRE-SOLVE AUDIT FAILED - STOPPING BEFORE ANY ITERATION")
    for f in FAIL:
        log("   " + f)
    flush_log("Logs/%s_log.txt" % TAG)
    exit()

if os.environ.get("S5B_AUDIT_ONLY", "0") == "1":
    log("AUDIT-ONLY MODE: pre-solve audit passed, exiting without iterating")
    flush_log("Logs/%s_log.txt" % TAG)
    exit()

# ---------------------------------------------------------------------------
# 3. initialisation - RE-INITIALISED from the verified setup case
# ---------------------------------------------------------------------------
# Decision B (re-initialise), not A (continue from the 5A test data): the official
# result must be reproducible from the audited setup case and this journal alone,
# and the 5A data carries a first-order history that includes the overshoot.
ini = S.initialization
step("initialization type standard", lambda: setattr(ini, "initialization_type", "standard"))
step("standard initialize (300 K, w = 23.5 m/s, 0 Pa gauge)", lambda: ini.standard_initialize())


# ---------------------------------------------------------------------------
# convergence machinery
# ---------------------------------------------------------------------------
def last_residuals():
    """Latest scaled residuals, parsed from the live solver output."""
    best = (None, None)
    for path in (STDOUT, TRN):
        if not os.path.isfile(path):
            continue
        hdr, it_res = None, None
        with open(path, "r", errors="ignore") as fh:
            for l in fh:
                if "iter" in l and "continuity" in l and not l.lstrip().startswith(">>>"):
                    hdr = l.split()
                    continue
                if hdr is None:
                    continue
                m = re.match(r"^\s*(\d+)\s+(\d\.\d{4}e[-+]\d\d)", l)
                if m:
                    tok = l.split()
                    n = len(hdr) - 2
                    try:
                        vals = [float(x) for x in tok[1:1 + n]]
                    except ValueError:
                        continue
                    it_res = (int(tok[0]), dict(zip(hdr[1:1 + n], vals)))
        if it_res and (best[0] is None or it_res[0] > best[0]):
            best = it_res
    return best


STAGE3_START = [None]   # first iteration number solved with the final schemes


def evaluate(tag):
    it, res = last_residuals()
    hdr, rows = read_report_file(MON)
    ev = {"tag": tag, "iteration": it, "residuals": res, "checks": {}}
    ok_all = True
    # the plateau window must lie ENTIRELY inside the final-scheme stage
    if STAGE3_START[0] is not None:
        rows = [r for r in rows if r[0] >= STAGE3_START[0]]
    if res is None or not hdr or len(rows) < WINDOW:
        ev["ready"] = False
        ev["why"] = "residuals %s, stage-3 rows %d < %d" % ("ok" if res else "unreadable", len(rows), WINDOW)
        return False, ev
    c = {n: i for i, n in enumerate(hdr)}
    need = ["p_in_area", "p_out_area", "q_net_all", "T_outer_max", "mdot_in", "mdot_out",
            "q_heated_wall", "q_interface", "T_out_bulk", "T_solid_max", "T_wall_max"]
    missing = [n for n in need if n not in c]
    if missing:
        ev["ready"] = False
        ev["why"] = "monitor columns missing: %s" % missing
        return False, ev
    win = rows[-WINDOW:]
    lastr = rows[-1]

    for eq, tgt in RES_TARGET.items():
        v = res.get(eq)
        ok = v is not None and v < tgt
        ev["checks"]["residual %s" % eq] = {"value": v, "target": tgt, "ok": ok}
        ok_all &= ok

    def col(name):
        return [r[c[name]] for r in win]

    dp_win = [r[c["p_in_area"]] - r[c["p_out_area"]] for r in win]
    for name, tol in ABS_DRIFT_K.items():
        v = col(name)
        d = max(v) - min(v)
        ok = d < tol
        ev["checks"]["drift %s over %d it [K]" % (name, WINDOW)] = {"value": d, "target": tol, "ok": ok}
        ok_all &= ok
    for name, tol in REL_DRIFT.items():
        v = dp_win if name == "dp_area" else [abs(x) for x in col(name)]
        d = (max(v) - min(v)) / max(abs(sum(v) / len(v)), 1e-30)
        ok = d < tol
        ev["checks"]["rel drift %s over %d it" % (name, WINDOW)] = {"value": d, "target": tol, "ok": ok}
        ok_all &= ok

    mi = abs(lastr[c["mdot_in"]] + lastr[c["mdot_out"]]) / lastr[c["mdot_in"]]
    ev["checks"]["mass imbalance |in-out|/in"] = {"value": mi, "target": MASS_TOL, "ok": mi < MASS_TOL}
    ok_all &= mi < MASS_TOL
    qw = lastr[c["q_heated_wall"]]
    ei = abs(lastr[c["q_net_all"]]) / qw
    ev["checks"]["energy imbalance |sum Q|/Q_wall"] = {"value": ei, "target": ENERGY_TOL, "ok": ei < ENERGY_TOL}
    ok_all &= ei < ENERGY_TOL
    ev["ready"] = True
    ev["converged"] = bool(ok_all)
    return ok_all, ev


def iterate(n, label):
    return step("%s: iterate %d" % (label, n), lambda: S.run_calculation.iterate(iter_count=n))


def checkpoint(label):
    step("checkpoint %s" % label, lambda: solver.file.write_case_data(file_name="Case/checkpoint.cas.h5"),
         critical=False)


# ---------------------------------------------------------------------------
# 4. STAGE 1 - flow + turbulence only (energy equation not solved)
# ---------------------------------------------------------------------------
eq = S.controls.equations
step("STAGE 1: energy equation OFF", lambda: eq.__setitem__("temperature", False))
step("equations", lambda: eq())
iterate(FLOW_IT, "stage 1 flow-only")

# ---------------------------------------------------------------------------
# 5. STAGE 2 - energy ON, still first order
# ---------------------------------------------------------------------------
step("STAGE 2: energy equation ON", lambda: eq.__setitem__("temperature", True))
step("equations", lambda: eq())
iterate(ENERGY_IT, "stage 2 energy first-order")
checkpoint("end of stage 2")

# ---------------------------------------------------------------------------
# 6. STAGE 3 - the ONE switch to the final second-order schemes, then converge
# ---------------------------------------------------------------------------
_h, _r = read_report_file(MON)
STAGE3_START[0] = (_r[-1][0] + 1) if _r else None
log("stage 3 starts at iteration %s" % STAGE3_START[0])
for k, v in FINAL_SCHEMES.items():
    step("STAGE 3 scheme %-12s -> %s" % (k, v), (lambda kk=k, vv=v: set_scheme(ds, kk, vv)))
bad = audit("2_final_schemes", FINAL_SCHEMES)
if bad:
    log("FINAL-SCHEME AUDIT FAILED - STOPPING")
    flush_log("Logs/%s_log.txt" % TAG)
    exit()

EVALS = []
done = 0
converged = False
while done < MAX_STAGE3:
    iterate(CHUNK, "stage 3 second-order")
    done += CHUNK
    ok, ev = evaluate("stage3+%d" % done)
    EVALS.append(ev)
    if ev.get("ready"):
        failing = [k for k, v in ev["checks"].items() if not v["ok"]]
        log("EVAL iter %s: %s  (failing: %s)" % (ev["iteration"], "CONVERGED" if ok else "not yet",
                                               ", ".join(failing) if failing else "none"))
    else:
        log("EVAL iter %s: not evaluable yet (%s)" % (ev.get("iteration"), ev.get("why")))
    write_json("Audit/convergence_evaluations.json", EVALS)
    if done % 500 == 0:
        checkpoint("stage 3 +%d" % done)
    if ok:
        # confirmation: another CHUNK iterations must leave every criterion satisfied
        iterate(CHUNK, "confirmation")
        done += CHUNK
        ok2, ev2 = evaluate("confirmation+%d" % done)
        EVALS.append(ev2)
        failing = [k for k, v in ev2["checks"].items() if not v["ok"]]
        log("CONFIRM iter %s: %s  (failing: %s)" % (ev2["iteration"], "HOLDS" if ok2 else "LOST",
                                                    ", ".join(failing) if failing else "none"))
        if ok2:
            converged = True
            break

write_json("Audit/convergence_evaluations.json", EVALS)
log("STAGE 3 finished after %d second-order iterations; converged=%s" % (done, converged))

bad = audit("3_final", FINAL_SCHEMES)

# ---------------------------------------------------------------------------
# 7. outputs
# ---------------------------------------------------------------------------
sfx = "final" if converged else "NOT_CONVERGED"
step("write case", lambda: solver.file.write_case(file_name="Case/baseline_medium_%s.cas.h5" % sfx))
step("write data", lambda: solver.file.write_data(file_name="Data/baseline_medium_%s.dat.h5" % sfx))

FLUXZ = ["fluid_inlet", "fluid_outlet", "heated_outer_wall", "solid_inlet_end", "solid_outlet_end",
         "fluid_solid_interface", "fluid_solid_interface-shadow"]
FR = solver.results.report.fluxes
step("Fluent flux report: mass", lambda: FR.mass_flow(zones=["fluid_inlet", "fluid_outlet"],
                                                     write_to_file=True, file_name="Audit/fluent_flux_mass.txt"),
     critical=False)
step("Fluent flux report: heat", lambda: FR.heat_transfer(zones=FLUXZ, write_to_file=True,
                                                         file_name="Audit/fluent_flux_heat.txt"), critical=False)
SI = solver.results.report.surface_integrals
for fn, surfs, fld, f in [
    ("area_weighted_avg", ["fluid_inlet", "fluid_outlet"], "pressure", "p_area"),
    ("mass_weighted_avg", ["fluid_inlet", "fluid_outlet"], "pressure", "p_mass"),
    ("area_weighted_avg", ["fluid_inlet", "fluid_outlet"], "total-pressure", "p0_area"),
    ("mass_weighted_avg", ["fluid_inlet", "fluid_outlet"], "temperature", "T_mass"),
    ("mass_weighted_avg", ["fluid_inlet", "fluid_outlet"], "enthalpy", "h_mass"),
    ("area_weighted_avg", ["fluid_inlet", "fluid_outlet"], "density", "rho_area"),
    ("area_weighted_avg", ["fluid_inlet", "fluid_outlet"], "z-velocity", "w_area"),
    ("area", ["fluid_inlet", "fluid_outlet", "heated_outer_wall", "fluid_solid_interface"], None, "areas"),
    ("area_weighted_avg", ["heated_outer_wall", "fluid_solid_interface"], "temperature", "Twall_area"),
    ("facet_max", ["heated_outer_wall", "fluid_solid_interface"], "temperature", "Twall_max"),
    ("facet_min", ["heated_outer_wall", "fluid_solid_interface"], "temperature", "Twall_min"),
    ("area_weighted_avg", ["fluid_solid_interface"], "y-plus", "yplus_area"),
    ("facet_max", ["fluid_solid_interface"], "y-plus", "yplus_max"),
    ("facet_min", ["fluid_solid_interface"], "y-plus", "yplus_min"),
    ("area_weighted_avg", ["fluid_solid_interface", "heated_outer_wall"], "heat-flux", "qpp_area"),
]:
    kw = dict(surface_names=surfs, write_to_file=True, file_name="Audit/fluent_si_%s.txt" % f)
    if fld:
        kw["report_of"] = fld
    step("Fluent surface integral %s" % f, (lambda fn=fn, kw=kw: getattr(SI, fn)(**kw)), critical=False)

# ASCII exports of the converged solution (cell-centre values: no interpolation)
step("cell-zone surface fluid", lambda: solver.setup.cell_zone_conditions.fluid["fluid_domain"].create_surface(),
     critical=False)
step("cell-zone surface solid", lambda: solver.setup.cell_zone_conditions.solid["solid_domain"].create_surface(),
     critical=False)
surf_list = step("export surface list", lambda: list(solver.file.export.ascii.surface_name_list.allowed_values()),
                 critical=False) or []
log("EXPORT SURFACES (full) = %s" % surf_list)
fz = [s for s in surf_list if "fluid_domain" in s]
sz = [s for s in surf_list if "solid_domain" in s]
EXP = solver.file.export.ascii
CELLQ = ["x-coordinate", "y-coordinate", "z-coordinate", "cell-volume", "pressure", "total-pressure",
         "density", "temperature", "enthalpy", "velocity-magnitude", "x-velocity", "y-velocity",
         "z-velocity", "viscosity-lam", "viscosity-turb", "specific-heat-cp", "thermal-conductivity-lam",
         "turb-kinetic-energy", "specific-diss-rate", "cell-wall-distance"]
SOLQ = ["x-coordinate", "y-coordinate", "z-coordinate", "cell-volume", "temperature",
        "thermal-conductivity-lam", "specific-heat-cp", "density"]
WALLQ = ["x-coordinate", "y-coordinate", "z-coordinate", "face-area-magnitude", "temperature",
         "heat-flux", "y-plus", "wall-shear", "z-wall-shear", "skin-friction-coef",
         "wall-adjacent-temperature", "cell-wall-distance"]
OUTWQ = ["x-coordinate", "y-coordinate", "z-coordinate", "face-area-magnitude", "temperature", "heat-flux"]
BNDQ = ["x-coordinate", "y-coordinate", "z-coordinate", "face-area-magnitude", "pressure", "total-pressure",
        "temperature", "density", "z-velocity", "velocity-magnitude", "enthalpy"]
for fname, surfs, q in [
    ("Exports/cells_fluid.csv", fz, CELLQ),
    ("Exports/cells_solid.csv", sz, SOLQ),
    ("Exports/wall_interface.csv", ["fluid_solid_interface"], WALLQ),
    ("Exports/wall_outer.csv", ["heated_outer_wall"], OUTWQ),
    ("Exports/wall_solid_ends.csv", ["solid_inlet_end", "solid_outlet_end"], OUTWQ),
    ("Exports/boundary_inlet.csv", ["fluid_inlet"], BNDQ),
    ("Exports/boundary_outlet.csv", ["fluid_outlet"], BNDQ),
]:
    if not surfs:
        log("warn  no surface available for %s" % fname)
        continue
    step("ASCII export %s" % fname,
         (lambda f=fname, s=surfs, qq=q: EXP(file_name=f, surface_name_list=s, delimiter="comma",
                                              quantities=qq, location="cell-center")), critical=False)

write_json("Audit/run_summary.json", {"tag": TAG, "converged": converged, "stage1_iters": FLOW_IT,
                                      "stage2_iters": ENERGY_IT, "stage3_iters": done,
                                      "total_iters": FLOW_IT + ENERGY_IT + done,
                                      "stage3_first_iteration": STAGE3_START[0],
                                      "failures": FAIL, "final_eval": EVALS[-1] if EVALS else None})
log("=" * 80)
log("RUN COMPLETE  converged=%s  total iterations=%d" % (converged, FLOW_IT + ENERGY_IT + done))
log("FAILURES (%d)" % len(FAIL))
for f in FAIL:
    log("   " + f)
log("=" * 80)
flush_log("Logs/%s_log.txt" % TAG)
step("stop transcript", lambda: solver.file.stop_transcript(), critical=False)
print("S5B-DONE")
exit()
