# -*- coding: utf-8 -*-
"""Section 7A - READ-ONLY export of the static GAUGE pressure on the fluid side of the inner wall
(face zone fluid_solid_interface) of the official medium solution, for the pressure-load preparation.
Fluent pressures are gauge values relative to the operating pressure (101325 Pa); the outside of the duct is
ambient, so the wall load for the structure is the gauge value itself (no absolute pressure is used anywhere).
Outputs: fluent_interface_wall_pressure.csv (face centroid x,y,z, pressure [Pa gauge], face area),
         Audit/wall_pressure_export.json
RE-ANALYSIS 2026 - newly generated export of a newly generated CFD solution.
"""
import os, sys
sys.path.insert(0, "Journals")
from s5_common import *

CASE = "../../06_Fluent_CFD/Case/baseline_medium_final.cas.h5"
DATA = "../../06_Fluent_CFD/Data/baseline_medium_final.dat.h5"
solver.file.batch_options.confirm_overwrite = False
step("read case  " + CASE, lambda: solver.file.read_case(file_name=CASE))
step("read data  " + DATA, lambda: solver.file.read_data(file_name=DATA))
info = {"case": CASE, "data": DATA}
try:
    info["operating_pressure_Pa"] = solver.setup.general.operating_conditions.operating_pressure()
except Exception as e:
    info["operating_pressure_Pa"] = "n/a %s" % e
log("operating pressure %s" % info["operating_pressure_Pa"])
step("export wall pressure", lambda: solver.file.export.ascii(
    file_name="fluent_interface_wall_pressure.csv", surface_name_list=["fluid_solid_interface"], delimiter="comma",
    quantities=["pressure", "face-area-magnitude"], location="cell-center"))
info["failures"] = FAIL
write_json("Audit/wall_pressure_export.json", info)
flush_log("Logs/wall_pressure_export_log.txt")
print("S7A-WALL-PRESSURE-DONE")
exit()
