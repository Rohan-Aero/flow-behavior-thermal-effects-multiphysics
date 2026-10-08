# Section 5B API map - run against the Section 5A test case+data.
import traceback
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    OUT.append(s)
    print("I3 " + s)


def kids(label, fn):
    try:
        o = fn()
        say("%-44s children=%s" % (label, list(getattr(o, "child_names", []))))
        cm = list(getattr(o, "command_names", []) or [])
        if cm:
            say("%-44s commands=%s" % (label, cm))
        return o
    except Exception as e:
        say("%-44s UNAVAILABLE %s: %s" % (label, type(e).__name__, str(e)[:120]))


def state(label, fn):
    try:
        say("%-44s state=%s" % (label, repr(fn())[:600]))
    except Exception as e:
        say("%-44s state ERR %s: %s" % (label, type(e).__name__, str(e)[:120]))


def allowed(label, fn):
    try:
        say("%-44s allowed=%s" % (label, fn().allowed_values()))
    except Exception as e:
        say("%-44s allowed ERR %s" % (label, str(e)[:120]))


def args(label, fn):
    try:
        o = fn()
        a = getattr(o, "argument_names", None)
        say("%-44s args=%s" % (label, a))
        if a:
            for n in a:
                try:
                    sub = getattr(o, n)
                    extra = ""
                    try:
                        extra = " allowed=%s" % sub.allowed_values()
                    except Exception:
                        pass
                    say("      arg %-30s %s%s" % (n, type(sub).__name__, extra))
                except Exception as e:
                    say("      arg %-30s ? %s" % (n, e))
    except Exception as e:
        say("%-44s args ERR %s" % (label, str(e)[:120]))


solver.file.batch_options.confirm_overwrite = False
solver.file.read_case_data(file_name="Test_Run/test_150iters.cas.h5")
say("read test_150iters case+data OK")

S = solver.solution
# --- pseudo time
kids("methods.pseudo_time_method", lambda: S.methods.pseudo_time_method)
state("methods.pseudo_time_method", lambda: S.methods.pseudo_time_method())
kids("methods.pseudo_time_method.formulation", lambda: S.methods.pseudo_time_method.formulation)
allowed("formulation.coupled_solver", lambda: S.methods.pseudo_time_method.formulation.coupled_solver)
kids("run_calculation.pseudo_time_settings", lambda: S.run_calculation.pseudo_time_settings)
state("run_calculation.pseudo_time_settings", lambda: S.run_calculation.pseudo_time_settings())
try:
    pts = S.run_calculation.pseudo_time_settings
    for c in pts.child_names:
        kids("pts." + c, lambda c=c: getattr(pts, c))
        state("pts." + c, lambda c=c: getattr(pts, c)())
except Exception as e:
    say("pts walk failed %s" % e)
kids("controls.pseudo_time_method_local_time_step", lambda: S.controls.pseudo_time_method_local_time_step)
state("controls.pseudo_time_method_local_time_step", lambda: S.controls.pseudo_time_method_local_time_step())
kids("controls.pseudo_time_explicit_relaxation_factor", lambda: S.controls.pseudo_time_explicit_relaxation_factor)
state("controls.pseudo_time_explicit_relaxation_factor", lambda: S.controls.pseudo_time_explicit_relaxation_factor())
state("controls.under_relaxation", lambda: S.controls.under_relaxation())
state("controls.relaxation_factor", lambda: S.controls.relaxation_factor())
state("controls.p_v_controls", lambda: S.controls.p_v_controls())
kids("controls.equations", lambda: S.controls.equations)
state("controls.equations", lambda: S.controls.equations())
state("controls.limits", lambda: S.controls.limits())
kids("controls.advanced", lambda: S.controls.advanced)

# --- residual
kids("monitor.residual.equations['energy']", lambda: S.monitor.residual.equations["energy"])
state("monitor.residual.equations['energy']", lambda: S.monitor.residual.equations["energy"]())
state("monitor.residual.options", lambda: S.monitor.residual.options())
allowed("residual.options.criterion_type", lambda: S.monitor.residual.options.criterion_type)
args("monitor.residual.write", lambda: S.monitor.residual.write)
kids("monitor.convergence_conditions", lambda: S.monitor.convergence_conditions)
state("monitor.convergence_conditions", lambda: S.monitor.convergence_conditions())

# --- export
kids("file.export", lambda: solver.file.export)
args("file.export.ascii", lambda: solver.file.export.ascii)
args("file.export.cgns", lambda: solver.file.export.cgns)

# --- results / report
kids("results.report", lambda: solver.results.report)
kids("results.report.fluxes", lambda: solver.results.report.fluxes)
args("report.fluxes.mass_flow", lambda: solver.results.report.fluxes.mass_flow)
kids("results.report.surface_integrals", lambda: solver.results.report.surface_integrals)
args("report.surface_integrals.area_weighted_avg",
     lambda: solver.results.report.surface_integrals.area_weighted_avg)
kids("results.report.forces", lambda: solver.results.report.forces)
args("results.report.forces.wall_forces", lambda: solver.results.report.forces.wall_forces)

# --- force report definition children
RD = S.report_definitions
try:
    RD.force.create("probe_force")
    kids("report_definitions.force[probe]", lambda: RD.force["probe_force"])
    state("report_definitions.force[probe]", lambda: RD.force["probe_force"]())
except Exception as e:
    say("force probe failed: %s" % e)

# --- field names: use a surface report's field allowed values
try:
    RD.surface.create("probe_field")
    fl = RD.surface["probe_field"].field.allowed_values()
    say("SURFACE FIELD COUNT %d" % len(fl))
    say("SURFACE FIELDS %s" % fl)
except Exception as e:
    say("field probe failed: %s" % e)
try:
    RD.volume.create("probe_vfield")
    fl = RD.volume["probe_vfield"].field.allowed_values()
    say("VOLUME FIELD COUNT %d" % len(fl))
    say("VOLUME FIELDS %s" % fl)
except Exception as e:
    say("vfield probe failed: %s" % e)

# --- surfaces
kids("results.surfaces.line_surface", lambda: solver.results.surfaces.line_surface)
try:
    solver.results.surfaces.line_surface.create("probe_line")
    kids("line_surface[probe]", lambda: solver.results.surfaces.line_surface["probe_line"])
    state("line_surface[probe]", lambda: solver.results.surfaces.line_surface["probe_line"]())
except Exception as e:
    say("line surface probe: %s" % e)
try:
    solver.results.surfaces.plane_surface.create("probe_plane")
    kids("plane_surface[probe]", lambda: solver.results.surfaces.plane_surface["probe_plane"])
    state("plane_surface[probe]", lambda: solver.results.surfaces.plane_surface["probe_plane"]())
except Exception as e:
    say("plane surface probe: %s" % e)
args("cell zone create_surface", lambda: solver.setup.cell_zone_conditions.fluid["fluid_domain"].create_surface)
kids("results.plot", lambda: solver.results.plot)
kids("results.plot.xy_plot", lambda: solver.results.plot.xy_plot)

# --- radiation / models audit
state("models.radiation", lambda: solver.setup.models.radiation())
state("models.viscous", lambda: solver.setup.models.viscous())
state("models.energy", lambda: solver.setup.models.energy())

# --- does a fields accessor exist in the built-in console?
say("solver attrs: %s" % [a for a in dir(solver) if not a.startswith("_")][:80])
try:
    fd = solver.fields.field_data
    say("solver.fields.field_data available: %s" % type(fd))
except Exception as e:
    say("solver.fields.field_data NOT available: %s" % e)

# --- current iteration accessor
for p in ("solver.solution.run_calculation.iter_count",
          "solver.rp_vars", "solver.scheme"):
    try:
        say("%s -> %s" % (p, eval(p)))
    except Exception as e:
        say("%s -> ERR %s" % (p, e))
try:
    say("scheme iter: %s" % solver.scheme.eval("(%iterate-count)"))
except Exception as e:
    say("scheme iter failed: %s" % e)
try:
    say("rp iteration: %s" % solver.scheme.eval("(rpgetvar 'number-of-iterations)"))
except Exception as e:
    say("rp iteration failed: %s" % e)

with open("Logs/introspect3_dump.txt", "w") as fh:
    fh.write("\n".join(OUT))
print("I3-DONE")
exit()
