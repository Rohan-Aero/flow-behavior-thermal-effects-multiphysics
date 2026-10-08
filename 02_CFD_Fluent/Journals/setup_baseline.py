# ============================================================================
# Section 5A - ANSYS Fluent baseline setup + short diagnostic test solve
# Project : Flow Behavior and Thermal Effects in Multiphysics Systems
#           RE-ANALYSIS 2026 - no original internship artefact is reproduced here.
#
# Run with:  fluent 3ddp -g -py -t4 -i Journals/setup_baseline.py
# Working directory must be 06_Fluent_CFD.
#
# Every value below traces to 02_Engineering_Calculations/baseline_parameters.json
# (the frozen Section 2 baseline) or to a Section 1 decision recorded in
# PROJECT_STATE.md. Nothing is tuned to make the CFD agree with Section 2.
# ============================================================================
import os, math, json, traceback

LOG = []
FAIL = []


def log(msg):
    LOG.append(str(msg))
    print("S5A " + str(msg))


def step(label, fn, critical=True):
    """Run one setup action, record what happened, never die silently."""
    try:
        r = fn()
        log("OK    %-52s %s" % (label, "" if r is None else repr(r)[:90]))
        return r
    except Exception as e:
        msg = "%s: %s: %s" % (label, type(e).__name__, e)
        FAIL.append(("CRITICAL " if critical else "minor ") + msg)
        log("%-5s %-52s %s: %s" % ("FAIL" if critical else "warn", label,
                                   type(e).__name__, str(e)[:120]))
        if critical:
            log("      " + traceback.format_exc().splitlines()[-3].strip())
        return None


def setv(parent, name, val, label=None):
    """Set a settings leaf. Some are compound objects carrying .value, some are plain
    reals. Try both, then verify by reading back."""
    node = getattr(parent, name)
    errs = []
    for how, fn in (("value", lambda: setattr(node, "value", val)),
                    ("direct", lambda: setattr(parent, name, val)),
                    ("set_state", lambda: node.set_state(val))):
        try:
            fn()
            got = readv(parent, name)
            if got is None or _close(got, val):
                return "%s <- %s (%s, read back %s)" % (name, val, how, got)
            errs.append("%s gave %r" % (how, got))
        except Exception as e:
            errs.append("%s: %s" % (how, type(e).__name__))
    raise RuntimeError("; ".join(errs))


def readv(parent, name):
    node = getattr(parent, name)
    for fn in (lambda: node.value(), lambda: node()):
        try:
            v = fn()
            if isinstance(v, dict) and "value" in v:
                return v["value"]
            if isinstance(v, (int, float, str, bool)):
                return v
        except Exception:
            continue
    return None


def _close(a, b):
    try:
        return abs(float(a) - float(b)) <= 1e-9 + 1e-6 * abs(float(b))
    except Exception:
        return a == b


def first_allowed(obj, candidates, label):
    """Pick the first candidate the build actually accepts; log the menu."""
    try:
        allowed = obj.allowed_values()
    except Exception:
        allowed = None
    if allowed:
        log("      %s allowed=%s" % (label, allowed))
        for c in candidates:
            if c in allowed:
                return c
        for c in candidates:
            for a in allowed:
                if c.lower().replace("-", "").replace(" ", "") == \
                   a.lower().replace("-", "").replace(" ", ""):
                    return a
    return candidates[0]


# ---------------------------------------------------------------------------
# Frozen baseline (02_Engineering_Calculations/baseline_parameters.json)
# ---------------------------------------------------------------------------
Di, Do, L = 0.020, 0.040, 0.600
T_IN, V_IN, P_OP = 300.0, 23.5, 101325.0
P_OUT_GAUGE = 0.0
QPP_OUTER = 8000.0
A_C = math.pi * Di ** 2 / 4.0
RE_IN = 29957.0                      # Section 2, inlet Reynolds number
TI = 0.16 * RE_IN ** (-0.125)        # fully-developed pipe correlation
D_H = Di

AIR_T = [250.0, 300.0, 350.0, 400.0, 450.0, 500.0, 550.0, 600.0]
AIR_CP = [1006.0, 1007.0, 1009.0, 1014.0, 1021.0, 1030.0, 1040.0, 1051.0]
AIR_MU = [1.596e-5, 1.846e-5, 2.082e-5, 2.301e-5, 2.507e-5, 2.701e-5, 2.884e-5, 3.058e-5]
AIR_K = [0.02227, 0.02624, 0.03003, 0.03365, 0.03707, 0.04038, 0.04360, 0.04659]
AIR_MW = 28.966                      # standard dry air; verified against rho below

INC_T = [293.15, 373.15, 473.15, 573.15, 673.15]     # VDM 4127, 20-400 C
INC_CP = [460.0, 458.0, 468.0, 485.0, 501.0]
INC_K = [11.5, 12.1, 13.5, 15.2, 17.1]
INC_RHO = 8190.0

MESH = "../05_Meshing/Mesh_Medium/medium.msh"
TEST_ITERS = int(os.environ.get("S5A_ITERS", "150"))   # 0 = setup-only dry run

log("=" * 78)
log("Section 5A baseline setup - RE-ANALYSIS 2026")
log("turbulence intensity from 0.16*Re^-0.125 at Re=%.0f  ->  %.3f %%" % (RE_IN, TI * 100))
log("=" * 78)

# Batch runs must never stop at an "OK to overwrite?" prompt - a blocked prompt looks
# exactly like a hung solver. Belt and braces: the driver deletes the outputs first and
# Fluent is told not to confirm.
def no_confirm():
    bo = solver.file.batch_options
    names = list(getattr(bo, "child_names", []))
    log("      file.batch_options children = %s" % names)
    done = []
    for n in names:
        if "confirm" in n or "overwrite" in n or "exit" in n or "hang" in n or "question" in n:
            try:
                setattr(bo, n, False if "confirm" in n or "question" in n else True)
                done.append(n)
            except Exception as e:
                log("      batch_options.%s -> %s" % (n, e))
    return done


step("disable batch overwrite prompts", no_confirm, critical=False)
step("transcript", lambda: solver.file.start_transcript(
    file_name="Logs/setup_transcript_%d.trn" % TEST_ITERS), critical=False)

# ---------------------------------------------------------------------------
# 1. Mesh
# ---------------------------------------------------------------------------
step("read medium mesh", lambda: solver.file.read_case(file_name=MESH))
step("mesh check", lambda: solver.mesh.check())
step("mesh quality", lambda: solver.mesh.quality())
step("check before solve", lambda: setattr(solver.mesh, "check_before_solve", True), critical=False)

zones = {}
for kind in ("fluid", "solid"):
    try:
        zones["cell_" + kind] = list(getattr(solver.setup.cell_zone_conditions, kind).get_object_names())
    except Exception as e:
        zones["cell_" + kind] = ["<%s>" % e]
for kind in ("velocity_inlet", "pressure_outlet", "wall", "interior"):
    try:
        zones[kind] = list(getattr(solver.setup.boundary_conditions, kind).get_object_names())
    except Exception as e:
        zones[kind] = ["<%s>" % e]
log("ZONES " + json.dumps(zones))

# ---------------------------------------------------------------------------
# 2. General - solver type, time, operating conditions
# ---------------------------------------------------------------------------
gs = solver.setup.general.solver
step("solver type = pressure-based", lambda: setattr(gs, "type", "pressure-based"))
step("time = steady (A-004)", lambda: setattr(gs, "time", "steady"))
step("velocity formulation = absolute", lambda: setattr(gs, "velocity_formulation", "absolute"))

oc = solver.setup.general.operating_conditions
step("operating pressure = 101325 Pa", lambda: setattr(oc, "operating_pressure", P_OP))
step("gravity OFF (A-007, Gr/Re2 = 4.3e-5)",
     lambda: setattr(oc.gravity, "enable", False))
step("verify gravity state", lambda: oc.gravity(), critical=False)

# ---------------------------------------------------------------------------
# 3. Models - energy FIRST (it activates the thermal branches), then turbulence
# ---------------------------------------------------------------------------
step("energy equation ON", lambda: setattr(solver.setup.models.energy, "enabled", True))
vis = solver.setup.models.viscous
step("viscous model = k-omega", lambda: setattr(vis, "model", "k-omega"))
step("k-omega variant = SST (D-011)", lambda: setattr(vis, "k_omega_model", "sst"))
try:
    log("      near-wall-treatment children = %s" % list(vis.near_wall_treatment.child_names))
    log("      wall_omega_treatment = %s" % vis.near_wall_treatment.wall_omega_treatment())
except Exception as e:
    log("      near-wall probe: %s" % e)

# ---------------------------------------------------------------------------
# 4. Materials
# ---------------------------------------------------------------------------
air = solver.setup.materials.fluid["air"]


def pw(points_t, points_v):
    """Fluent 2026 R1 stores piecewise-linear data as [{'item': x, 'value': y}, ...].
    Confirmed by reading back the default state, not assumed."""
    return [{"item": float(t), "value": float(v)} for t, v in zip(points_t, points_v)]


def set_option(o, opt):
    """Fluent 2026 R1 sometimes raises 'api-set-var: the object is not active' on an
    option assignment that in fact succeeded. Trust the read-back, not the exception."""
    err = None
    try:
        o.option()                       # refresh the cached state first
    except Exception:
        pass
    try:
        o.option = opt
    except Exception as e:
        err = e
    got = None
    try:
        got = o.option()
    except Exception:
        pass
    if got == opt:
        return opt
    try:
        o.set_state({"option": opt})
        got = o.option()
    except Exception as e2:
        err = err or e2
    if got != opt:
        raise RuntimeError("option is %r, wanted %r (%s)" % (got, opt, err))
    return opt


def set_prop(mat, prop, option, value=None, t=None, v=None, label=""):
    o = getattr(mat, prop)
    opt = first_allowed(o.option, [option], label + "." + prop)
    set_option(o, opt)
    if option == "piecewise-linear":
        o.piecewise_linear.function_of = "temperature"
        o.piecewise_linear.data_points = pw(t, v)
        got = o.piecewise_linear.data_points()
        if len(got) != len(t):
            raise RuntimeError("wrote %d points, read back %d" % (len(t), len(got)))
        for (a, b), g in zip(zip(t, v), got):
            if abs(g["item"] - a) > 1e-9 * max(1.0, abs(a)) or \
               abs(g["value"] - b) > 1e-9 * max(1.0, abs(b)):
                raise RuntimeError("read-back mismatch: wrote (%g,%g) got %s" % (a, b, g))
        return "piecewise-linear, %d points verified %g..%g K" % (len(t), t[0], t[-1])
    elif value is not None:
        o.value = value
        got = readv(mat, prop)
        if not _close(got, value):
            raise RuntimeError("wrote %s=%s, read back %s" % (prop, value, got))
        return "%s = %s (verified)" % (opt, got)
    else:
        # e.g. incompressible-ideal-gas: the option IS the model, there is no scalar
        # value to write, and writing one raises 'the object is not active'.
        return "%s (no scalar value)" % opt


step("air density = incompressible-ideal-gas (D-009/D-021)",
     lambda: set_prop(air, "density", "incompressible-ideal-gas", label="air"))
step("air molecular weight = %.3f" % AIR_MW,
     lambda: setattr(air.molecular_weight, "value", AIR_MW))
step("air cp = piecewise-linear (Incropera A.4)",
     lambda: set_prop(air, "specific_heat", "piecewise-linear", t=AIR_T, v=AIR_CP, label="air"))
step("air mu = piecewise-linear (Incropera A.4)",
     lambda: set_prop(air, "viscosity", "piecewise-linear", t=AIR_T, v=AIR_MU, label="air"))
step("air k = piecewise-linear (Incropera A.4)",
     lambda: set_prop(air, "thermal_conductivity", "piecewise-linear", t=AIR_T, v=AIR_K, label="air"))

# --- Inconel 718 as a new solid material
def make_inconel():
    sol = solver.setup.materials.solid
    try:
        sol["inconel-718"] = {}
    except Exception:
        sol.create("inconel-718")
    return list(sol.get_object_names())


step("create solid material inconel-718", make_inconel)
inc = None
try:
    inc = solver.setup.materials.solid["inconel-718"]
except Exception as e:
    log("FAIL  cannot access inconel-718: %s" % e)

if inc is not None:
    step("inconel rho = 8190 kg/m3",
         lambda: set_prop(inc, "density", "value", value=INC_RHO, label="inconel"))
    step("inconel cp = piecewise-linear (VDM 4127)",
         lambda: set_prop(inc, "specific_heat", "piecewise-linear", t=INC_T, v=INC_CP, label="inconel"))
    step("inconel k = piecewise-linear (VDM 4127)",
         lambda: set_prop(inc, "thermal_conductivity", "piecewise-linear", t=INC_T, v=INC_K,
                          label="inconel"))

# ---------------------------------------------------------------------------
# 5. Cell zones
# ---------------------------------------------------------------------------
step("FLUID_DOMAIN -> air",
     lambda: setattr(solver.setup.cell_zone_conditions.fluid["fluid_domain"].general,
                     "material", "air"))
step("SOLID_DOMAIN -> inconel-718",
     lambda: setattr(solver.setup.cell_zone_conditions.solid["solid_domain"].general,
                     "material", "inconel-718"))

# ---------------------------------------------------------------------------
# 6. Boundary conditions
# ---------------------------------------------------------------------------
inl = solver.setup.boundary_conditions.velocity_inlet["fluid_inlet"]
step("inlet velocity spec = normal to boundary",
     lambda: setattr(inl.momentum, "velocity_specification_method",
                     first_allowed(inl.momentum.velocity_specification_method,
                                   ["Magnitude, Normal to Boundary"], "inlet.vspec")))
step("inlet velocity = 23.5 m/s", lambda: setattr(inl.momentum.velocity_magnitude, "value", V_IN))
step("inlet temperature = 300 K", lambda: setattr(inl.thermal.temperature, "value", T_IN))
step("inlet turbulence spec = I and Dh",
     lambda: setattr(inl.turbulence, "turbulence_specification",
                     first_allowed(inl.turbulence.turbulence_specification,
                                   ["Intensity and Hydraulic Diameter"], "inlet.tspec")))
# Fluent has historically stored turbulent intensity as a percentage in the TUI and as
# a fraction in the settings API. Read the shipped default and match its scale rather
# than guessing: a factor-of-100 error here would be invisible and would poison the
# whole near-wall solution.
TI_DEFAULT = readv(inl.turbulence, "turbulent_intensity")
TI_IS_PERCENT = (TI_DEFAULT is not None and float(TI_DEFAULT) > 1.0)
TI_SET = TI * 100.0 if TI_IS_PERCENT else TI
log("      turbulent_intensity default = %s -> treating as %s, writing %.6g"
    % (TI_DEFAULT, "PERCENT" if TI_IS_PERCENT else "FRACTION", TI_SET))
step("inlet I = %.3f %% (written as %.6g)" % (TI * 100, TI_SET),
     lambda: setv(inl.turbulence, "turbulent_intensity", TI_SET))
step("inlet Dh = 0.020 m",
     lambda: setv(inl.turbulence, "hydraulic_diameter", D_H))

out = solver.setup.boundary_conditions.pressure_outlet["fluid_outlet"]
step("outlet gauge pressure = 0 Pa", lambda: setattr(out.momentum.gauge_pressure, "value", P_OUT_GAUGE))
step("outlet backflow total temperature = 300 K",
     lambda: setattr(out.thermal.backflow_total_temperature, "value", T_IN))
step("outlet backflow turbulence spec = I and Dh",
     lambda: setattr(out.turbulence, "turbulence_specification",
                     first_allowed(out.turbulence.turbulence_specification,
                                   ["Intensity and Hydraulic Diameter"], "outlet.tspec")))
step("outlet backflow I",
     lambda: setv(out.turbulence, "backflow_turbulent_intensity", TI_SET), critical=False)
step("outlet backflow Dh",
     lambda: setv(out.turbulence, "backflow_hydraulic_diameter", D_H), critical=False)
step("outlet prevent reverse flow = on",
     lambda: setattr(out.momentum, "prevent_reverse_flow", True), critical=False)

W = solver.setup.boundary_conditions.wall


def wall_thermal(zone, condition, flux=None):
    t = W[zone].thermal
    cond = first_allowed(t.thermal_condition, [condition], zone + ".thermal_condition")
    t.thermal_condition = cond
    if flux is not None:
        t.heat_flux.value = flux
    return "%s -> %s%s" % (zone, cond, "" if flux is None else " q=%g W/m2" % flux)


step("HEATED_OUTER_WALL: heat flux 8000 W/m2",
     lambda: wall_thermal("heated_outer_wall", "Heat Flux", QPP_OUTER))
step("SOLID_INLET_END: adiabatic (A-011)",
     lambda: wall_thermal("solid_inlet_end", "Heat Flux", 0.0))
step("SOLID_OUTLET_END: adiabatic (A-011)",
     lambda: wall_thermal("solid_outlet_end", "Heat Flux", 0.0))

# The fluid/solid interface must be COUPLED - Fluent should set this itself because
# the zone separates two cell zones and has a shadow. Verify, never impose.
for z in ("fluid_solid_interface", "fluid_solid_interface-shadow"):
    try:
        log("      %s thermal_condition = %s" % (z, W[z].thermal.thermal_condition()))
    except Exception as e:
        log("      %s thermal_condition unreadable: %s" % (z, e))

# ---------------------------------------------------------------------------
# 7. Reference values
# ---------------------------------------------------------------------------
# Reference values affect only the non-dimensional reports (Cf, Nu); they change no
# equation. Set explicitly from the frozen baseline rather than auto-computed.
rv = solver.setup.reference_values
RHO_IN = P_OP / (287.058 * T_IN)
for nm, val in (("area", A_C), ("length", D_H), ("temperature", T_IN),
                ("velocity", V_IN), ("density", RHO_IN), ("pressure", 0.0),
                ("viscosity", 1.846e-5)):
    step("reference %-12s = %-12.6g" % (nm, val),
         (lambda n=nm, x=val: setv(rv, n, x)), critical=False)

# ---------------------------------------------------------------------------
# 8. Numerical methods - CONSERVATIVE STARTUP (first order)
# ---------------------------------------------------------------------------
me = solver.solution.methods
step("p-v coupling = Coupled",
     lambda: setattr(me.p_v_coupling, "flow_scheme",
                     first_allowed(me.p_v_coupling.flow_scheme, ["Coupled"], "flow_scheme")))
step("gradient = least-squares cell based",
     lambda: setattr(me.spatial_discretization, "gradient_scheme",
                     first_allowed(me.spatial_discretization.gradient_scheme,
                                   ["least-square-cell-based"], "gradient")))

ds = me.spatial_discretization.discretization_scheme
try:
    log("      discretization_scheme keys = %s" % list(ds.get_object_names()))
except Exception:
    try:
        log("      discretization_scheme state = %s" % ds())
    except Exception as e:
        log("      discretization_scheme unreadable: %s" % e)

# Conservative first-order startup on the transported equations; pressure stays
# second-order. NR-06 requires second-order everywhere for the FINAL solution - that
# switch belongs to Section 5B, not to this diagnostic run.
STARTUP = {"pressure": ["second-order", "standard"],
           "mom": ["first-order-upwind"],
           "k": ["first-order-upwind"],
           "omega": ["first-order-upwind"],
           "temperature": ["first-order-upwind"]}


def set_scheme(key, cands):
    o = ds[key]
    val = first_allowed(o, cands, "scheme." + key)
    ds[key] = val
    return val


try:
    keys = list(ds.get_object_names())
except Exception:
    keys = []
for k, cands in STARTUP.items():
    match = [kk for kk in keys if kk.lower() == k or kk.lower().startswith(k)]
    target = match[0] if match else k
    step("startup scheme %-12s" % target, (lambda t=target, c=cands: set_scheme(t, c)),
         critical=False)

ct = solver.solution.controls
step("log pseudo-time method state",
     lambda: me.pseudo_time_method(), critical=False)
step("log pseudo-time children",
     lambda: list(me.pseudo_time_method.child_names), critical=False)
step("log run_calculation pseudo-time settings",
     lambda: solver.solution.run_calculation.pseudo_time_settings(), critical=False)
# With the Coupled scheme Fluent uses the pseudo-time method, where the explicit
# Courant number is inactive by design; the pseudo-time time-scale factor governs
# instead. Record what is actually in force rather than forcing a number that is not
# being used.
step("courant number (inactive under pseudo-time - expected)",
     lambda: setv(ct, "courant_number", 50.0), critical=False)


def relax_conservative():
    """Conservative explicit relaxation for the coupled/pseudo-time startup."""
    out_ = {}
    for holder in ("pseudo_time_explicit_relaxation_factor", "under_relaxation",
                   "relaxation_factor"):
        try:
            h = getattr(ct, holder)
            keys = list(h.get_object_names())
            out_[holder] = keys
        except Exception as e:
            out_[holder] = "n/a (%s)" % type(e).__name__
    return out_


step("log relaxation containers", relax_conservative, critical=False)

# ---------------------------------------------------------------------------
# 9. Report definitions  (Section 5A item 12)
# ---------------------------------------------------------------------------
RD = solver.solution.report_definitions
made = []


def mk(container, name, rtype_cands, **kw):
    c = getattr(RD, container)
    try:
        c.create(name)
    except Exception:
        c[name] = {}
    o = c[name]
    rt = first_allowed(o.report_type, rtype_cands, name + ".report_type")
    o.report_type = rt
    for k, v in kw.items():
        setattr(o, k, v)
    made.append(name)
    return "%s (%s)" % (name, rt)


step("rep mdot_in", lambda: mk("flux", "mdot_in", ["flux-massflow"], boundaries=["fluid_inlet"]))
step("rep mdot_out", lambda: mk("flux", "mdot_out", ["flux-massflow"], boundaries=["fluid_outlet"]))
step("rep mass_imbalance", lambda: mk("flux", "mass_imbalance", ["flux-massflow"],
                                      boundaries=["fluid_inlet", "fluid_outlet"]))
step("rep q_heated_wall", lambda: mk("flux", "q_heated_wall", ["flux-heattransfer"],
                                     boundaries=["heated_outer_wall"]))
step("rep q_interface", lambda: mk("flux", "q_interface", ["flux-heattransfer"],
                                   boundaries=["fluid_solid_interface"]))
step("rep q_fluid_net", lambda: mk("flux", "q_fluid_net", ["flux-heattransfer"],
                                   boundaries=["fluid_inlet", "fluid_outlet"]))
step("rep p_in", lambda: mk("surface", "p_in", ["surface-massavg"],
                            field="pressure", surface_names=["fluid_inlet"]))
step("rep p_out", lambda: mk("surface", "p_out", ["surface-massavg"],
                             field="pressure", surface_names=["fluid_outlet"]))
step("rep T_out_bulk", lambda: mk("surface", "T_out_bulk", ["surface-massavg"],
                                  field="temperature", surface_names=["fluid_outlet"]))
step("rep T_wall_max", lambda: mk("surface", "T_wall_max", ["surface-facetmax"],
                                  field="temperature", surface_names=["fluid_solid_interface"]))
step("rep T_solid_max", lambda: mk("volume", "T_solid_max", ["volume-max"],
                                   field="temperature", cell_zones=["solid_domain"]))
step("rep T_solid_mean", lambda: mk("volume", "T_solid_mean", ["volume-average"],
                                    field="temperature", cell_zones=["solid_domain"]))
step("rep v_out_max", lambda: mk("surface", "v_out_max", ["surface-facetmax"],
                                 field="velocity-magnitude", surface_names=["fluid_outlet"]),
     critical=False)
for yf in ("y-plus", "yplus", "wall-yplus"):
    r = step("rep yplus_max (field=%s)" % yf,
             (lambda f=yf: mk("surface", "yplus_max", ["surface-facetmax"],
                              field=f, surface_names=["fluid_solid_interface"])),
             critical=False)
    if r:
        break


def mk_expr(name, definition):
    c = RD.expression
    try:
        c.create(name)
    except Exception:
        c[name] = {}
    o = c[name]
    kids = list(getattr(o, "child_names", []))
    log("      expression report children = %s" % kids)
    for cand in ("definition", "define", "expression", "expr", "report_type"):
        if cand in kids and cand != "report_type":
            setattr(o, cand, definition)
            made.append(name)
            return "%s = %s" % (cand, definition)
    raise RuntimeError("no definition-like child among %s" % kids)


step("rep dp_total (expression)",
     lambda: mk_expr("dp_total",
                     "MassAvg(AbsolutePressure,['fluid_inlet']) - "
                     "MassAvg(AbsolutePressure,['fluid_outlet'])"),
     critical=False)

log("REPORT DEFINITIONS CREATED: %s" % made)

# --- per-iteration monitor file (Section 5A item 12/16)
# The expression report is excluded: it computes empty in this build and one bad entry
# silently suppresses the whole file.
FILE_DEFS = [m for m in made if m != "dp_total"]


def make_report_file():
    rf = solver.solution.monitor.report_files
    try:
        rf.create("s5a_monitors")
    except Exception:
        rf["s5a_monitors"] = {}
    o = rf["s5a_monitors"]
    log("      report_files children = %s" % list(getattr(o, "child_names", [])))
    for k, v in (("report_defs", FILE_DEFS),
                 ("file_name", "Test_Run/s5a_monitors.out"),
                 ("frequency_of", "iteration"),
                 ("frequency", 1),
                 ("print", True),
                 ("active", True)):
        try:
            setattr(o, k, v)
        except Exception as e:
            log("      report_files.%s <- %r failed: %s" % (k, v, e))
    st = o()
    log("      report_files state = %s" % st)
    return st


step("per-iteration monitor file", make_report_file, critical=False)

step("residual: do not use for convergence (NR-04)",
     lambda: setattr(solver.solution.monitor.residual.options, "criterion_type", "none"),
     critical=False)
try:
    log("      residual equations now = %s" %
        list(solver.solution.monitor.residual.equations.get_object_names()))
except Exception as e:
    log("      residual equations unreadable: %s" % e)

# ---------------------------------------------------------------------------
# 9b. VERIFICATION PASS - read every critical setting back out of Fluent
# ---------------------------------------------------------------------------
log("-" * 78)
log("VERIFICATION - values read back from Fluent, not from this script")
CHECKS = [
    ("solver type", lambda: gs.type(), "pressure-based"),
    ("time", lambda: gs.time(), "steady"),
    ("velocity formulation", lambda: gs.velocity_formulation(), "absolute"),
    ("operating pressure", lambda: oc.operating_pressure(), P_OP),
    ("gravity", lambda: oc.gravity()["enable"], False),
    ("energy enabled", lambda: solver.setup.models.energy.enabled(), True),
    ("viscous model", lambda: vis.model(), "k-omega"),
    ("k-omega variant", lambda: vis.k_omega_model(), "sst"),
    ("air density option", lambda: air.density.option(), "incompressible-ideal-gas"),
    ("fluid zone material",
     lambda: solver.setup.cell_zone_conditions.fluid["fluid_domain"].general.material(), "air"),
    ("solid zone material",
     lambda: solver.setup.cell_zone_conditions.solid["solid_domain"].general.material(),
     "inconel-718"),
    ("inlet velocity", lambda: inl.momentum.velocity_magnitude.value(), V_IN),
    ("inlet temperature", lambda: inl.thermal.temperature.value(), T_IN),
    ("inlet intensity", lambda: readv(inl.turbulence, "turbulent_intensity"), TI_SET),
    ("inlet Dh", lambda: readv(inl.turbulence, "hydraulic_diameter"), D_H),
    ("inlet turb spec", lambda: inl.turbulence.turbulence_specification(),
     "Intensity and Hydraulic Diameter"),
    ("air cp is piecewise", lambda: air.specific_heat.option(), "piecewise-linear"),
    ("air mu is piecewise", lambda: air.viscosity.option(), "piecewise-linear"),
    ("air k is piecewise", lambda: air.thermal_conductivity.option(), "piecewise-linear"),
    ("inconel k is piecewise",
     lambda: solver.setup.materials.solid["inconel-718"].thermal_conductivity.option(),
     "piecewise-linear"),
    ("inconel density", lambda: readv(solver.setup.materials.solid["inconel-718"],
                                      "density"), INC_RHO),
    ("outlet gauge pressure", lambda: out.momentum.gauge_pressure.value(), P_OUT_GAUGE),
    ("heated wall condition", lambda: W["heated_outer_wall"].thermal.thermal_condition(),
     "Heat Flux"),
    ("heated wall flux", lambda: W["heated_outer_wall"].thermal.heat_flux.value(), QPP_OUTER),
    ("solid inlet end flux", lambda: W["solid_inlet_end"].thermal.heat_flux.value(), 0.0),
    ("solid outlet end flux", lambda: W["solid_outlet_end"].thermal.heat_flux.value(), 0.0),
    ("INTERFACE is coupled", lambda: W["fluid_solid_interface"].thermal.thermal_condition(),
     "Coupled"),
    ("INTERFACE shadow coupled",
     lambda: W["fluid_solid_interface-shadow"].thermal.thermal_condition(), "Coupled"),
]
VERIFY = {}
for name, fn, expect in CHECKS:
    try:
        got = fn()
        ok = (got == expect) if not isinstance(expect, float) else \
             (abs(float(got) - expect) <= 1e-9 + 1e-9 * abs(expect))
        VERIFY[name] = {"got": got, "expected": expect, "ok": bool(ok)}
        log("%-5s %-28s got=%-26s expected=%s" % ("VER" if ok else "MISMATCH", name,
                                                  repr(got)[:26], repr(expect)))
        if not ok:
            FAIL.append("VERIFY MISMATCH %s: got %r expected %r" % (name, got, expect))
    except Exception as e:
        VERIFY[name] = {"error": str(e)}
        FAIL.append("VERIFY ERROR %s: %s" % (name, e))
        log("VERR  %-28s %s" % (name, e))

# The heat flux must be applied on the OUTER wall only - never twice.
for z in ("fluid_solid_interface", "fluid_solid_interface-shadow", "solid_inlet_end",
          "solid_outlet_end"):
    try:
        cond = W[z].thermal.thermal_condition()
        q = W[z].thermal.heat_flux.value() if cond == "Heat Flux" else None
        log("HEAT-PATH %-32s condition=%-10s flux=%s" % (z, cond, q))
        if cond == "Heat Flux" and q not in (0.0, 0):
            FAIL.append("DOUBLE HEAT INPUT: %s carries %g W/m2" % (z, q))
    except Exception as e:
        log("HEAT-PATH %-32s unreadable: %s" % (z, e))

log("-" * 78)

# ---------------------------------------------------------------------------
# 10. Initialization
# ---------------------------------------------------------------------------
ini = solver.solution.initialization
step("initialization type = standard", lambda: setattr(ini, "initialization_type", "standard"))
step("compute defaults from fluid_inlet",
     lambda: ini.compute_defaults(from_zone_name="fluid_inlet", from_zone_type="velocity-inlet"),
     critical=False)
step("list defaults", lambda: ini.list_defaults(), critical=False)


def force_defaults():
    d = ini.defaults
    out = {}
    for key, val in (("temperature", T_IN), ("x-velocity", 0.0), ("y-velocity", 0.0),
                     ("z-velocity", V_IN), ("gauge-pressure", 0.0)):
        try:
            d[key] = val
            out[key] = val
        except Exception as e:
            out[key] = "skip(%s)" % type(e).__name__
    return out


step("force sensible init values", force_defaults, critical=False)
step("standard initialize", lambda: ini.standard_initialize())

# ---------------------------------------------------------------------------
# 11. Save the SETUP case before any iteration
# ---------------------------------------------------------------------------
step("write setup case",
     lambda: solver.file.write_case(file_name="Baseline_Setup/baseline_setup.cas.h5"))

# ---------------------------------------------------------------------------
# 12. SHORT DIAGNOSTIC TEST SOLVE  - NOT a converged run
# ---------------------------------------------------------------------------
log("-" * 78)
if TEST_ITERS > 0:
    log("STARTING SHORT DIAGNOSTIC SOLVE: %d iterations. This is NOT a converged run." % TEST_ITERS)
    log("-" * 78)
    step("iterate %d" % TEST_ITERS,
         lambda: solver.solution.run_calculation.iterate(iter_count=TEST_ITERS))
else:
    log("DRY RUN: S5A_ITERS=0, setup only, no iterations performed.")
    log("-" * 78)

# ---------------------------------------------------------------------------
# 13. Post-test diagnostics
# ---------------------------------------------------------------------------
results = {}
for nm in made:
    try:
        v = RD.compute(report_defs=[nm])
        results[nm] = v
        log("MONITOR %-16s = %s" % (nm, v))
    except Exception as e:
        results[nm] = "ERROR %s" % e
        log("MONITOR %-16s ERROR %s" % (nm, e))

# Delta p is the difference of two monitors that are written every iteration. The
# expression report is a convenience; this computation is the one that is guaranteed.
def dp_from_monitors():
    def val(nm):
        r = RD.compute(report_defs=[nm])
        return float(r[0][nm][0])
    pi, po = val("p_in"), val("p_out")
    d = pi - po
    log("DERIVED dp_total = p_in - p_out = %.4f - %.4f = %.4f Pa" % (pi, po, d))
    results["dp_total_derived_Pa"] = d
    return d


step("derive dp from p_in - p_out", dp_from_monitors, critical=False)

def check_monitor_file():
    pth = "Test_Run/s5a_monitors.out"
    if not os.path.isfile(pth):
        raise RuntimeError("monitor file was NOT written to %s" % pth)
    n = sum(1 for _ in open(pth))
    return "%s exists, %d lines" % (pth, n)


step("verify monitor file written", check_monitor_file, critical=False)

step("flux balance mass", lambda: solver.results.report.fluxes.mass_flow(write_to_file=False), critical=False)
step("flux balance heat", lambda: solver.results.report.fluxes.heat_transfer(write_to_file=False), critical=False)

if TEST_ITERS > 0:
    step("write test case+data",
         lambda: solver.file.write_case_data(file_name="Test_Run/test_%diters.cas.h5" % TEST_ITERS))

summary = dict(mesh=MESH, iterations=TEST_ITERS, zones=zones,
               turbulent_intensity=TI, ti_written=TI_SET, verification=VERIFY,
               monitors=results, failures=FAIL)
try:
    with open("Logs/setup_summary_%d.json" % TEST_ITERS, "w") as fh:
        json.dump(summary, fh, indent=2, default=str)
    log("summary written")
except Exception as e:
    log("summary write failed: %s" % e)

try:
    with open("Logs/setup_log_%d.txt" % TEST_ITERS, "w") as fh:
        fh.write("\n".join(LOG))
except Exception:
    pass

log("=" * 78)
log("FAILURES (%d):" % len(FAIL))
for f in FAIL:
    log("   " + f)
log("=" * 78)
print("S5A-DONE")
step("stop transcript", lambda: solver.file.stop_transcript(), critical=False)
exit()
