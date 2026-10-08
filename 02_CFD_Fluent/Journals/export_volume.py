# Section 5B - export the converged VOLUME solution cell by cell.
#
# Why this exists: a cell-zone "surface" in Fluent is the zone's enclosing boundary, not
# its volume (the first export produced 6,912 fluid rows = inlet + outlet + interface faces,
# instead of 116,640 cells). Here every axial slab of cells is cut by an iso-z plane
# through its centre. A plane parallel to the hex faces cuts each cell exactly once, so
# the cut facets carry, at cell-centre location, the values of every cell in the slab
# with no interpolation. Row counts are checked against the mesh.
import os, sys, json
sys.path.insert(0, "Journals")
from s5_common import *

NZ, L = 90, 0.600
dz = L / NZ
solver.file.batch_options.confirm_overwrite = False
step("read final case", lambda: solver.file.read_case(file_name="Case/baseline_medium_final.cas.h5"))
step("read final data", lambda: solver.file.read_data(file_name="Data/baseline_medium_final.dat.h5"))

ISO = solver.results.surfaces.iso_surface
step("create probe iso surface", lambda: ISO.create("zprobe"))
kids = list(ISO["zprobe"].child_names)
log("iso_surface children = %s" % kids)
step("iso probe state", lambda: ISO["zprobe"]())
for c in kids:
    try:
        log("   %s allowed=%s" % (c, getattr(ISO["zprobe"], c).allowed_values()[:12]))
    except Exception:
        pass


def make_iso(name, zval, zone):
    try:
        ISO.create(name)
    except Exception:
        ISO[name] = {}
    o = ISO[name]
    o.field = "z-coordinate"
    if "zones" in kids:
        o.zones = [zone]
    o.iso_values = [zval]
    return o()


names = {"fluid_domain": [], "solid_domain": []}
for zone, tag in (("fluid_domain", "f"), ("solid_domain", "s")):
    for k in range(NZ):
        nm = "z%s%02d" % (tag, k)
        r = step("iso %s z=%.6f" % (nm, (k + 0.5) * dz), (lambda n=nm, z=(k + 0.5) * dz, zz=zone: make_iso(n, z, zz)),
                 critical=(k == 0))
        if r is not None:
            names[zone].append(nm)
log("iso surfaces: fluid %d, solid %d" % (len(names["fluid_domain"]), len(names["solid_domain"])))

EXP = solver.file.export.ascii
FQ = ["cell-zone", "cell-volume", "radial-coordinate", "pressure", "total-pressure", "density", "temperature",
      "enthalpy", "velocity-magnitude", "x-velocity", "y-velocity", "z-velocity", "viscosity-lam", "viscosity-turb",
      "specific-heat-cp", "thermal-conductivity-lam", "turb-kinetic-energy", "specific-diss-rate",
      "cell-wall-distance", "face-area-magnitude"]
SQ = ["cell-zone", "cell-volume", "radial-coordinate", "temperature", "thermal-conductivity-lam",
      "specific-heat-cp", "density", "face-area-magnitude"]
step("export fluid volume", lambda: EXP(file_name="Exports/cells_fluid.csv", surface_name_list=names["fluid_domain"],
                                        delimiter="comma", quantities=FQ, location="cell-center"))
step("export solid volume", lambda: EXP(file_name="Exports/cells_solid.csv", surface_name_list=names["solid_domain"],
                                        delimiter="comma", quantities=SQ, location="cell-center"))


def count(path):
    n = 0
    with open(path) as fh:
        fh.readline()
        for _ in fh:
            n += 1
    return n


res = {}
for p, expect in (("Exports/cells_fluid.csv", 116640), ("Exports/cells_solid.csv", 43200)):
    try:
        n = count(p)
        res[p] = {"rows": n, "expected_cells": expect, "ok": n == expect}
        log("ROWS %s = %d (expected %d cells) %s" % (p, n, expect, "OK" if n == expect else "MISMATCH"))
    except Exception as e:
        res[p] = {"error": str(e)}
write_json("Audit/volume_export_check.json", res)
flush_log("Logs/export_volume_log.txt")
print("EXPORT-DONE")
exit()
