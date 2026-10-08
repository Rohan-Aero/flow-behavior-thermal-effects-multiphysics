import traceback
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    OUT.append(s)
    print("P3 " + s)


def attempt(label, fn):
    try:
        r = fn()
        say("PASS  %-46s -> %s" % (label, repr(r)[:100]))
        return True
    except Exception as e:
        say("fail  %-46s -> %s: %s" % (label, type(e).__name__, str(e)[:110]))
        return False


solver.file.read_case(file_name="../05_Meshing/Mesh_Medium/medium.msh")
solver.setup.models.energy.enabled = True
solver.setup.models.viscous.model = "k-omega"
solver.setup.models.viscous.k_omega_model = "sst"
say("energy on, sst on")

# ---------------- gravity ----------------
oc = solver.setup.general.operating_conditions
say("gravity children: %s" % list(getattr(oc.gravity, "child_names", [])))
try:
    say("gravity state: %s" % oc.gravity())
except Exception as e:
    say("gravity get failed: %s" % e)
attempt("gravity.enable=False", lambda: setattr(oc.gravity, "enable", False))
attempt("gravity.set_state({'enable':False})", lambda: oc.gravity.set_state({"enable": False}))
try:
    say("gravity state after: %s" % oc.gravity())
except Exception as e:
    say("gravity get2 failed: %s" % e)

# ---------------- density option ----------------
air = solver.setup.materials.fluid["air"]
say("air state keys: %s" % sorted(air.get_state().keys()))
try:
    say("air.density state: %s" % air.density())
except Exception as e:
    say("air.density get failed: %s" % e)
try:
    say("air.density.option state: %s" % air.density.option())
except Exception as e:
    say("air.density.option get failed: %s" % e)
try:
    say("air.density.option is_active: %s" % air.density.option.is_active())
except Exception as e:
    say("is_active failed: %s" % e)

ok = attempt("air.density.option = 'incompressible-ideal-gas'",
             lambda: setattr(air.density, "option", "incompressible-ideal-gas"))
if not ok:
    ok = attempt("air.density.set_state({'option':...})",
                 lambda: air.density.set_state({"option": "incompressible-ideal-gas"}))
if not ok:
    ok = attempt("air.density = {'option':...}",
                 lambda: setattr(air, "density", {"option": "incompressible-ideal-gas"}))
if not ok:
    ok = attempt("air.set_state({'density':{'option':...}})",
                 lambda: air.set_state({"density": {"option": "incompressible-ideal-gas"}}))
if not ok:
    ok = attempt("TUI define/materials change-create",
                 lambda: solver.tui.define.materials.change_create(
                     "air", "air", "yes", "incompressible-ideal-gas", "no", "no", "no", "no",
                     "no", "no"))
try:
    say("air.density state now: %s" % air.density())
except Exception as e:
    say("air.density get2 failed: %s" % e)

# ---------------- piecewise linear ----------------
T = [250.0, 300.0, 350.0, 400.0]
V = [1006.0, 1007.0, 1009.0, 1014.0]
cp = air.specific_heat
try:
    say("cp children: %s" % list(cp.child_names))
    say("cp state: %s" % cp())
except Exception as e:
    say("cp probe failed: %s" % e)
attempt("cp.option='piecewise-linear'", lambda: setattr(cp, "option", "piecewise-linear"))
try:
    say("cp.piecewise_linear children: %s" % list(cp.piecewise_linear.child_names))
    say("cp.piecewise_linear state: %s" % cp.piecewise_linear())
except Exception as e:
    say("pwl probe failed: %s" % e)
try:
    dp = cp.piecewise_linear.data_points
    say("data_points type: %s" % type(dp))
    say("data_points state: %s" % dp())
    say("data_points children: %s" % list(getattr(dp, "child_names", [])))
    try:
        say("data_points child_object_type children: %s" %
            list(dp.child_object_type.child_names))
    except Exception as e2:
        say("data_points cot: %s" % e2)
except Exception as e:
    say("data_points probe failed: %s" % e)

forms = [
    ("list of dict t/v", lambda: setattr(cp.piecewise_linear, "data_points",
                                         [{"t": a, "v": b} for a, b in zip(T, V)])),
    ("list of dict x/y", lambda: setattr(cp.piecewise_linear, "data_points",
                                         [{"x": a, "y": b} for a, b in zip(T, V)])),
    ("list of pairs", lambda: setattr(cp.piecewise_linear, "data_points",
                                      [[a, b] for a, b in zip(T, V)])),
    ("list of tuples", lambda: setattr(cp.piecewise_linear, "data_points",
                                       [(a, b) for a, b in zip(T, V)])),
    ("flat list", lambda: setattr(cp.piecewise_linear, "data_points",
                                  [x for pair in zip(T, V) for x in pair])),
    ("dict of lists", lambda: setattr(cp.piecewise_linear, "data_points",
                                      {"t": T, "v": V})),
    ("set_state pairs", lambda: cp.piecewise_linear.set_state(
        {"data_points": [[a, b] for a, b in zip(T, V)]})),
    ("set_state t/v dicts", lambda: cp.piecewise_linear.set_state(
        {"data_points": [{"t": a, "v": b} for a, b in zip(T, V)]})),
]
for label, fn in forms:
    if attempt("pwl " + label, fn):
        try:
            say("      -> resulting state: %s" % cp.piecewise_linear())
        except Exception:
            pass
        break

# ---------------- solid material creation ----------------
sol = solver.setup.materials.solid
say("solid objects: %s" % list(sol.get_object_names()))
ok = attempt("sol['inconel-718'] = {}", lambda: sol.__setitem__("inconel-718", {}))
if not ok:
    ok = attempt("sol.create('inconel-718')", lambda: sol.create("inconel-718"))
if not ok:
    ok = attempt("TUI copy aluminum", lambda: solver.tui.define.materials.change_create(
        "aluminum", "inconel-718", "yes", "constant", "8190", "yes", "constant", "460",
        "yes", "constant", "15.2", "no"))
say("solid objects now: %s" % list(sol.get_object_names()))

# ---------------- wall thermal conditions ----------------
W = solver.setup.boundary_conditions.wall
for z in ("heated_outer_wall", "fluid_solid_interface", "fluid_solid_interface-shadow",
          "solid_inlet_end"):
    try:
        say("%s thermal_condition = %s  allowed=%s"
            % (z, W[z].thermal.thermal_condition(),
               W[z].thermal.thermal_condition.allowed_values()))
    except Exception as e:
        say("%s thermal probe failed: %s" % (z, e))

# ---------------- report type allowed values ----------------
RD = solver.solution.report_definitions
for cont in ("flux", "surface", "volume"):
    try:
        c = getattr(RD, cont)
        c.create("probe_" + cont)
        say("%s report_type allowed=%s" % (cont, c["probe_" + cont].report_type.allowed_values()))
    except Exception as e:
        say("%s report probe failed: %s" % (cont, e))

# ---------------- discretization keys ----------------
ds = solver.solution.methods.spatial_discretization.discretization_scheme
try:
    say("ds state: %s" % ds())
except Exception as e:
    say("ds state failed: %s" % e)
try:
    say("ds object names: %s" % list(ds.get_object_names()))
except Exception as e:
    say("ds names failed: %s" % e)
try:
    k0 = list(ds())[0]
    say("ds['%s'] allowed=%s" % (k0, ds[k0].allowed_values()))
except Exception as e:
    say("ds allowed failed: %s" % e)

# ---------------- initialization defaults ----------------
ini = solver.solution.initialization
attempt("compute_defaults(from_zone_name=...)",
        lambda: ini.compute_defaults(from_zone_name="fluid_inlet",
                                     from_zone_type="velocity-inlet"))
try:
    say("init defaults objects: %s" % list(ini.defaults.get_object_names()))
except Exception as e:
    say("init defaults names failed: %s" % e)
try:
    say("init defaults state: %s" % ini.defaults())
except Exception as e:
    say("init defaults state failed: %s" % e)

# ---------------- residual options ----------------
try:
    say("residual.options children: %s" % list(solver.solution.monitor.residual.options.child_names))
except Exception as e:
    say("residual options failed: %s" % e)

with open("Logs/probe3_dump.txt", "w") as fh:
    fh.write("\n".join(OUT))
print("P3-DONE")
exit()
