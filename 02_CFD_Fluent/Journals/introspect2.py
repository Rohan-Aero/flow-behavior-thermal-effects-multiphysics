# Second introspection pass: the allowed values and sub-trees needed to write the
# Section 5A setup without guessing any string literal.
import traceback
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    OUT.append(s)
    print("INTRO2 " + s)


def av(path):
    try:
        o = eval(path)
    except Exception as e:
        say("%-62s UNAVAILABLE %s" % (path, e))
        return
    try:
        say("%-62s allowed=%s" % (path, o.allowed_values()))
    except Exception:
        try:
            say("%-62s children=%s" % (path, list(getattr(o, "child_names", []))))
        except Exception as e:
            say("%-62s no allowed/children (%s)" % (path, e))


def kids(path):
    try:
        o = eval(path)
        say("%-62s children=%s" % (path, list(getattr(o, "child_names", []))))
        cm = list(getattr(o, "command_names", []) or [])
        if cm:
            say("%-62s commands=%s" % (path, cm))
    except Exception as e:
        say("%-62s UNAVAILABLE %s" % (path, e))


solver.file.read_case(file_name="../05_Meshing/Mesh_Medium/medium.msh")
say("mesh read")

for p in [
    "solver.setup.general.solver.type",
    "solver.setup.general.solver.time",
    "solver.setup.general.solver.velocity_formulation",
    "solver.setup.models.viscous.model",
    "solver.setup.models.viscous.k_omega_model",
    "solver.setup.models.viscous.near_wall_treatment",
    "solver.setup.materials.fluid['air'].density.option",
    "solver.setup.materials.fluid['air'].viscosity.option",
    "solver.setup.materials.fluid['air'].specific_heat.option",
    "solver.setup.materials.fluid['air'].thermal_conductivity.option",
    "solver.setup.boundary_conditions.wall['heated_outer_wall'].thermal.thermal_condition",
    "solver.setup.boundary_conditions.wall['fluid_solid_interface'].thermal.thermal_condition",
    "solver.setup.boundary_conditions.velocity_inlet['fluid_inlet'].turbulence.turbulence_specification",
    "solver.setup.boundary_conditions.velocity_inlet['fluid_inlet'].momentum.velocity_specification_method",
    "solver.setup.boundary_conditions.pressure_outlet['fluid_outlet'].turbulence.turbulence_specification",
    "solver.setup.cell_zone_conditions.fluid['fluid_domain'].general",
    "solver.setup.cell_zone_conditions.solid['solid_domain'].general",
]:
    av(p)

for p in [
    "solver.setup.cell_zone_conditions.fluid['fluid_domain'].general",
    "solver.setup.cell_zone_conditions.solid['solid_domain'].general",
    "solver.setup.materials.fluid['air'].specific_heat",
    "solver.setup.materials.fluid['air'].thermal_conductivity",
    "solver.setup.materials.fluid['air'].density.piecewise_linear",
    "solver.setup.solution" if False else "solver.solution.methods.p_v_coupling",
    "solver.solution.methods.spatial_discretization",
    "solver.solution.monitor.residual",
    "solver.solution.monitor.report_files",
    "solver.solution.monitor.report_plots",
    "solver.solution.report_definitions.surface",
    "solver.solution.report_definitions.volume",
    "solver.solution.report_definitions.flux",
    "solver.solution.initialization.defaults",
    "solver.solution.run_calculation.parameters",
    "solver.results.surfaces",
    "solver.file",
    "solver.mesh",
    "solver.setup.reference_values",
]:
    kids(p)

for p in [
    "solver.solution.methods.p_v_coupling.flow_scheme",
    "solver.solution.methods.spatial_discretization.gradient_scheme",
    "solver.solution.methods.spatial_discretization.pressure_scheme",
    "solver.solution.methods.spatial_discretization.mom_scheme",
    "solver.solution.methods.spatial_discretization.energy_scheme",
    "solver.solution.methods.spatial_discretization.k_scheme",
    "solver.solution.methods.spatial_discretization.omega_scheme",
    "solver.solution.initialization.initialization_type",
]:
    av(p)

try:
    say("residual children: %s" % list(solver.solution.monitor.residual.child_names))
    say("residual equations: %s" % list(solver.solution.monitor.residual.equations.get_object_names()))
except Exception:
    say("residual probe:\n" + traceback.format_exc())

try:
    say("flux report children: %s" % list(solver.solution.report_definitions.flux.child_object_type.child_names))
except Exception as e:
    say("flux child_object_type failed: %s" % e)
try:
    say("surface report children: %s" % list(solver.solution.report_definitions.surface.child_object_type.child_names))
except Exception as e:
    say("surface child_object_type failed: %s" % e)
try:
    say("volume report children: %s" % list(solver.solution.report_definitions.volume.child_object_type.child_names))
except Exception as e:
    say("volume child_object_type failed: %s" % e)
try:
    say("report_files children: %s" % list(solver.solution.monitor.report_files.child_object_type.child_names))
except Exception as e:
    say("report_files child_object_type failed: %s" % e)

try:
    say("air MW = %s" % solver.setup.materials.fluid['air'].molecular_weight.value())
except Exception as e:
    say("MW read failed: %s" % e)

try:
    say("database list (solid, inconel search):")
    say(str(solver.setup.materials.database.list_materials(type="solid")))
except Exception as e:
    say("db list failed: %s" % e)

with open("Logs/introspect2_dump.txt", "w") as fh:
    fh.write("\n".join(OUT))
print("INTRO2-DONE")
exit()
