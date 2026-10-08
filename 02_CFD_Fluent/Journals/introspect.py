# Introspection of the Fluent 2026 R1 settings tree, run against the real medium mesh.
# Purpose: write the Section 5A setup against the API that actually exists in this build,
# rather than against remembered attribute names.
import traceback

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    OUT.append(s)
    print("INTRO " + s)


def names(obj, label):
    try:
        cn = list(getattr(obj, "child_names", []) or [])
    except Exception as e:
        cn = ["<child_names failed: %s>" % e]
    try:
        cmd = list(getattr(obj, "command_names", []) or [])
    except Exception as e:
        cmd = ["<command_names failed: %s>" % e]
    say("[%s] children: %s" % (label, cn))
    if cmd:
        say("[%s] commands: %s" % (label, cmd))


def objnames(obj, label):
    for meth in ("get_object_names", "keys"):
        try:
            say("[%s] %s(): %s" % (label, meth, list(getattr(obj, meth)())))
            return
        except Exception:
            pass
    say("[%s] no object-name accessor" % label)


try:
    say("=== reading medium mesh ===")
    solver.file.read_case(file_name="../05_Meshing/Mesh_Medium/medium.msh")
    say("read_case OK")
except Exception:
    say("read_case(file_name=...) failed:\n" + traceback.format_exc())
    try:
        solver.file.read(file_type="case", file_name="../05_Meshing/Mesh_Medium/medium.msh")
        say("file.read(file_type='case') OK")
    except Exception:
        say("file.read failed:\n" + traceback.format_exc())

for label, path in [
    ("setup", "solver.setup"),
    ("general", "solver.setup.general"),
    ("gen.solver", "solver.setup.general.solver"),
    ("gen.opcond", "solver.setup.general.operating_conditions"),
    ("models", "solver.setup.models"),
    ("energy", "solver.setup.models.energy"),
    ("viscous", "solver.setup.models.viscous"),
    ("materials", "solver.setup.materials"),
    ("cellzones", "solver.setup.cell_zone_conditions"),
    ("bcs", "solver.setup.boundary_conditions"),
    ("solution", "solver.solution"),
    ("methods", "solver.solution.methods"),
    ("controls", "solver.solution.controls"),
    ("monitor", "solver.solution.monitor"),
    ("report_defs", "solver.solution.report_definitions"),
    ("init", "solver.solution.initialization"),
    ("runcalc", "solver.solution.run_calculation"),
    ("results", "solver.results"),
]:
    try:
        names(eval(path), label)
    except Exception as e:
        say("[%s] UNAVAILABLE (%s): %s" % (label, path, e))

for label, path in [
    ("materials.fluid", "solver.setup.materials.fluid"),
    ("materials.solid", "solver.setup.materials.solid"),
    ("cellzones.fluid", "solver.setup.cell_zone_conditions.fluid"),
    ("cellzones.solid", "solver.setup.cell_zone_conditions.solid"),
    ("bc.velocity_inlet", "solver.setup.boundary_conditions.velocity_inlet"),
    ("bc.pressure_outlet", "solver.setup.boundary_conditions.pressure_outlet"),
    ("bc.wall", "solver.setup.boundary_conditions.wall"),
    ("bc.interior", "solver.setup.boundary_conditions.interior"),
]:
    try:
        objnames(eval(path), label)
    except Exception as e:
        say("[%s] UNAVAILABLE: %s" % (label, e))

# --- detail on one object of each kind we must configure
probes = [
    ("air", "solver.setup.materials.fluid['air']"),
    ("fluid zone", "solver.setup.cell_zone_conditions.fluid['fluid_domain']"),
    ("solid zone", "solver.setup.cell_zone_conditions.solid['solid_domain']"),
    ("inlet", "solver.setup.boundary_conditions.velocity_inlet['fluid_inlet']"),
    ("outlet", "solver.setup.boundary_conditions.pressure_outlet['fluid_outlet']"),
    ("wall heated", "solver.setup.boundary_conditions.wall['heated_outer_wall']"),
    ("wall interface", "solver.setup.boundary_conditions.wall['fluid_solid_interface']"),
]
for label, path in probes:
    try:
        o = eval(path)
        names(o, label)
    except Exception as e:
        say("[%s] probe failed: %s" % (label, e))

# --- thermal sub-branch of a wall (the CHT-critical one)
for label, path in [
    ("wall.thermal(heated)", "solver.setup.boundary_conditions.wall['heated_outer_wall'].thermal"),
    ("wall.thermal(interface)", "solver.setup.boundary_conditions.wall['fluid_solid_interface'].thermal"),
    ("inlet.turbulence", "solver.setup.boundary_conditions.velocity_inlet['fluid_inlet'].turbulence"),
    ("inlet.momentum", "solver.setup.boundary_conditions.velocity_inlet['fluid_inlet'].momentum"),
    ("inlet.thermal", "solver.setup.boundary_conditions.velocity_inlet['fluid_inlet'].thermal"),
    ("outlet.momentum", "solver.setup.boundary_conditions.pressure_outlet['fluid_outlet'].momentum"),
    ("outlet.turbulence", "solver.setup.boundary_conditions.pressure_outlet['fluid_outlet'].turbulence"),
    ("outlet.thermal", "solver.setup.boundary_conditions.pressure_outlet['fluid_outlet'].thermal"),
    ("air.density", "solver.setup.materials.fluid['air'].density"),
    ("air.viscosity", "solver.setup.materials.fluid['air'].viscosity"),
]:
    try:
        names(eval(path), label)
    except Exception as e:
        say("[%s] UNAVAILABLE: %s" % (label, e))

try:
    say("air state keys: %s" % sorted(solver.setup.materials.fluid['air'].get_state().keys()))
except Exception as e:
    say("air get_state failed: %s" % e)

try:
    say("mesh info:")
    solver.mesh.check()
except Exception as e:
    say("mesh.check failed: %s" % e)

try:
    with open("Logs/introspect_dump.txt", "w") as fh:
        fh.write("\n".join(OUT))
    say("dump written")
except Exception as e:
    say("dump write failed: %s" % e)

print("INTRO-DONE")
exit()
