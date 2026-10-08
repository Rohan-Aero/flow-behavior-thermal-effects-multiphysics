import traceback
solver.file.batch_options.confirm_overwrite = False
solver.file.read_case(file_name="Baseline_Setup/baseline_setup.cas.h5")
out = solver.setup.boundary_conditions.pressure_outlet["fluid_outlet"]
for label, fn in [
    ("outlet full state", lambda: out()),
    ("thermal state", lambda: out.thermal()),
    ("thermal children", lambda: list(out.thermal.child_names)),
    ("bftt is_active", lambda: out.thermal.backflow_total_temperature.is_active()),
    ("bftt children", lambda: list(getattr(out.thermal.backflow_total_temperature, "child_names", []))),
    ("bftt get", lambda: out.thermal.backflow_total_temperature()),
    ("bftt value", lambda: out.thermal.backflow_total_temperature.value()),
    ("prevent reverse flow", lambda: out.momentum.prevent_reverse_flow()),
]:
    try:
        print("PB %-22s %s" % (label, repr(fn())[:700]))
    except Exception as e:
        print("PB %-22s ERR %s: %s" % (label, type(e).__name__, str(e)[:300]))
print("PB-DONE")
exit()
