# -*- coding: utf-8 -*-
"""Section 7A (mapping fix) - READ-ONLY export of Fluent's own NODE temperatures of the solid zone.

Runs inside Fluent (fluent 3ddp -g -py -t4 -i ...) with working directory 07_Thermal_Analysis/Temperature_Source.
Reads the official Section 5B medium case + data; never writes a case/data, never iterates. The driver hashes the
official files before/after.

Why: the point-cloud (triangulation) mapping of cell/face centroids failed validation (Section 7A audit). The
replacement is a MESH-BASED transfer: Fluent's solid-zone mesh (read from the case file) becomes the External Data
master (MAPDL CDB) and Fluent's own node temperatures (exported here) are attached to its nodes, so Mechanical
interpolates with the source element shape functions.

Outputs (07_Thermal_Analysis/Temperature_Source):
  fluent_solid_zone_nodes.csv   every node of cell zone solid_domain: Fluent node number, x, y, z, T (Fluent node value)
  fluent_solid_zone_cells.csv   every solid cell (cell-centre values) - cross-check of the earlier iso-plane export
  Audit/node_export_verification.json
RE-ANALYSIS 2026 - newly generated export of a newly generated CFD solution.
"""
import os, sys, json
sys.path.insert(0, "Journals")
from s5_common import *

CASE = "../../06_Fluent_CFD/Case/baseline_medium_final.cas.h5"
DATA = "../../06_Fluent_CFD/Data/baseline_medium_final.dat.h5"
solver.file.batch_options.confirm_overwrite = False
step("read case  " + CASE, lambda: solver.file.read_case(file_name=CASE))
step("read data  " + DATA, lambda: solver.file.read_data(file_name=DATA))
EXP = solver.file.export.ascii
info = {"case": CASE, "data": DATA}
try:
    info["export_surface_allowed"] = [s for s in EXP.surface_name_list.allowed_values() if "solid" in s]
except Exception as e:
    info["export_surface_allowed"] = "n/a %s" % e
log("allowed surfaces containing 'solid': %s" % info["export_surface_allowed"])
SURF = "solid_domain"
if isinstance(info["export_surface_allowed"], list) and SURF not in info["export_surface_allowed"]:
    # fall back to an explicit zone surface of the solid cell zone (post-processing object only)
    def mk():
        zs = solver.results.surfaces.zone_surface
        zs.create("zs_solid_domain")
        zs["zs_solid_domain"].zone_name = "solid_domain"
    step("zone surface of solid_domain", mk)
    SURF = "zs_solid_domain"
info["surface_used"] = SURF
step("export solid-zone NODE temperatures",
     lambda: EXP(file_name="fluent_solid_zone_nodes.csv", surface_name_list=[SURF], delimiter="comma",
                 quantities=["temperature"], location="node"))
step("export solid-zone CELL temperatures",
     lambda: EXP(file_name="fluent_solid_zone_cells.csv", surface_name_list=[SURF], delimiter="comma",
                 quantities=["temperature", "cell-volume"], location="cell-center"))


def count(path):
    n = 0
    with open(path) as fh:
        head = fh.readline().strip()
        for _ in fh:
            n += 1
    return head, n


for p in ("fluent_solid_zone_nodes.csv", "fluent_solid_zone_cells.csv"):
    try:
        info[p] = count(p)
        log("ROWS %s %s" % (p, info[p]))
    except Exception as e:
        info[p] = "ERROR %s" % e
info["failures"] = FAIL
write_json("Audit/node_export_verification.json", info)
flush_log("Logs/node_export_log.txt")
print("S7A-NODE-EXPORT-DONE")
exit()
