# Section 7A - Fluent API probe (read-only): what does file.export offer for Mechanical?
# Reads the official medium case+data; writes only inside 07_Thermal_Analysis/Temperature_Source/Probe.
import os, sys, json
sys.path.insert(0, "Journals")
from s5_common import *
solver.file.batch_options.confirm_overwrite = False
step("read case", lambda: solver.file.read_case(file_name="../../06_Fluent_CFD/Case/baseline_medium_final.cas.h5"))
step("read data", lambda: solver.file.read_data(file_name="../../06_Fluent_CFD/Data/baseline_medium_final.dat.h5"))
EX = solver.file.export
log("export children: %s" % (list(EX.child_names) if hasattr(EX, "child_names") else "n/a"))
log("export commands: %s" % (list(EX.command_names) if hasattr(EX, "command_names") else "n/a"))
for nm in ("mechanical_apdl_input", "mechanical_apdl"):
    try:
        cmd = getattr(EX, nm)
        log("%s args: %s" % (nm, cmd.argument_names))
        for a in cmd.argument_names:
            try:
                arg = getattr(cmd, a)
                av = None
                try:
                    av = arg.allowed_values()
                except Exception:
                    pass
                log("   arg %s allowed=%s" % (a, av))
            except Exception as e:
                log("   arg %s err %s" % (a, e))
    except Exception as e:
        log("%s not available: %s" % (nm, e))
flush_log("Probe/probe_export_api_log.txt")
print("PROBE-EXPORT-API-DONE")
exit()
