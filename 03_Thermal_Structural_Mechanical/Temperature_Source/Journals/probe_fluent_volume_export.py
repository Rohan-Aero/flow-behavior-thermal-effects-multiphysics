# Section 7A - Fluent probe (read-only): which native exporters write the SOLID cell-zone volume mesh with NODE
# temperatures (Tecplot / VTK / EnSight Gold)? Outputs go to 07_Thermal_Analysis/Temperature_Source/Probe only.
import os, sys
sys.path.insert(0, "Journals")
from s5_common import *
solver.file.batch_options.confirm_overwrite = False
step("read case", lambda: solver.file.read_case(file_name="../../06_Fluent_CFD/Case/baseline_medium_final.cas.h5"))
step("read data", lambda: solver.file.read_data(file_name="../../06_Fluent_CFD/Data/baseline_medium_final.dat.h5"))
EX = solver.file.export
for nm in ("tecplot", "vtk", "ensight_gold"):
    try:
        cmd = getattr(EX, nm)
        args = list(cmd.argument_names)
        log("%s args: %s" % (nm, args))
        kw = {}
        for a in args:
            arg = getattr(cmd, a)
            try:
                av = arg.allowed_values()
            except Exception:
                av = None
            log("   arg %s allowed=%s" % (a, str(av)[:300]))
            if a == "file_name":
                kw[a] = "Probe/probe_solid_%s" % nm
            elif av and "solid_domain" in av:
                kw[a] = ["solid_domain"]
            elif av and "temperature" in av:
                kw[a] = ["temperature"]
        log("%s call kwargs %s" % (nm, kw))
        step("export %s" % nm, lambda c=cmd, k=kw: c(**k), critical=False)
    except Exception as e:
        log("%s not usable: %s" % (nm, e))
for fn in sorted(os.listdir("Probe")):
    log("Probe file %s %d" % (fn, os.path.getsize(os.path.join("Probe", fn))))
flush_log("Probe/probe_volume_export_log.txt")
print("PROBE-VOLUME-EXPORT-DONE")
exit()
