# -*- coding: utf-8 -*-
"""Section 7A (mapping fix) - READ-ONLY native Fluent export of the SOLID cell zone as EnSight Gold:
the solid_domain hexahedral mesh (43,200 cells / 48,048 nodes) with Fluent's own NODE temperatures.

Runs inside Fluent (fluent 3ddp -g -py -t4 -i ...) in 07_Thermal_Analysis/Temperature_Source. Reads the official
Section 5B medium case + data, never writes a case/data file, never iterates; the driver hashes the official files
before and after.

Why: the point-cloud (triangulation) mapping failed validation. The replacement is mesh-based: the Fluent solid
mesh + Fluent node temperatures are given to Mechanical External Data as an MAPDL CDB master mesh + node-ID data,
so Mechanical interpolates with the source element shape functions.
Output: EnSight/solid_domain_T.encas/.geo/.scl1 (C binary, node-centred), Audit/ensight_export_verification.json
RE-ANALYSIS 2026 - newly generated export of a newly generated CFD solution.
"""
import os, sys, json
sys.path.insert(0, "Journals")
from s5_common import *

CASE = "../../06_Fluent_CFD/Case/baseline_medium_final.cas.h5"
DATA = "../../06_Fluent_CFD/Data/baseline_medium_final.dat.h5"
solver.file.batch_options.confirm_overwrite = False
os.makedirs("EnSight", exist_ok=True)
step("read case  " + CASE, lambda: solver.file.read_case(file_name=CASE))
step("read data  " + DATA, lambda: solver.file.read_data(file_name=DATA))
EG = solver.file.export.ensight_gold
step("export EnSight Gold solid_domain, node-centred temperature",
     lambda: EG(file_name="EnSight/solid_domain_T", quantities=["temperature"], binary_format=True,
                cellzones=["solid_domain"], cell_centered=False))
info = {"case": CASE, "data": DATA, "exporter": "file.export.ensight_gold",
        "arguments": {"quantities": ["temperature"], "binary_format": True, "cellzones": ["solid_domain"],
                      "cell_centered": False},
        "files": {fn: os.path.getsize(os.path.join("EnSight", fn)) for fn in sorted(os.listdir("EnSight"))},
        "failures": FAIL}
write_json("Audit/ensight_export_verification.json", info)
flush_log("Logs/ensight_export_log.txt")
print("S7A-ENSIGHT-EXPORT-DONE")
exit()
