# Section 7A - Fluent export probe (read-only on the official medium case/data).
# Writes Fluent's native "Mechanical APDL" solution-data export of the SOLID cell zone into
# 07_Thermal_Analysis/Temperature_Source/Probe so its format (mesh + nodal values) can be inspected.
import os, sys
sys.path.insert(0, "Journals")
from s5_common import *
solver.file.batch_options.confirm_overwrite = False
step("read case", lambda: solver.file.read_case(file_name="../../06_Fluent_CFD/Case/baseline_medium_final.cas.h5"))
step("read data", lambda: solver.file.read_data(file_name="../../06_Fluent_CFD/Data/baseline_medium_final.dat.h5"))
EX = solver.file.export
step("export mechanical_apdl solid_domain",
     lambda: EX.mechanical_apdl(file_name="Probe/probe_solid_domain_mapdl", thread_name_list=["solid_domain"]))
for fn in sorted(os.listdir("Probe")):
    log("Probe file %s %d" % (fn, os.path.getsize(os.path.join("Probe", fn))))
flush_log("Probe/probe_mapdl_export_log.txt")
print("PROBE-MAPDL-EXPORT-DONE")
exit()
