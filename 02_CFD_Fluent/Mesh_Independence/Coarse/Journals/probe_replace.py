# Section 6A - PROBE (no iterations, no case written).
# Question: can the audited Section 5B medium-mesh case settings be carried onto the coarse
# mesh by Fluent's own replace-mesh, and does every setting survive unchanged?
# Run from 06_Fluent_CFD/Mesh_Independence/Coarse. Reads the medium FINAL case (settings only,
# never its data) and never writes anywhere outside this folder.
import os, sys, json
sys.path.insert(0, "Journals")
from s5_common import *

MED_CASE = "../../Case/baseline_medium_final.cas.h5"
MESH = "../../../05_Meshing/Mesh_Coarse/coarse.msh"
solver.file.batch_options.confirm_overwrite = False
step("transcript", lambda: solver.file.start_transcript(file_name="Logs/probe_transcript.trn"), critical=False)
step("read medium final CASE (settings only, no data)", lambda: solver.file.read_case(file_name=MED_CASE))


def snap():
    out = {}
    for k in ("setup", "solution"):
        try:
            out[k] = getattr(solver, k)()
        except Exception as e:
            out[k] = "ERROR %s" % e
    return out


A = step("snapshot settings (medium case)", snap)
write_json("Audit/probe_state_medium_case.json", A)
for obj, nm in ((solver.mesh, "mesh"), (solver.file, "file")):
    for attr in ("child_names", "command_names"):
        try:
            log("%s.%s = %s" % (nm, attr, list(getattr(obj, attr))))
        except Exception as e:
            log("%s.%s unreadable: %s" % (nm, attr, e))
try:
    log("mesh.replace arguments = %s" % list(solver.mesh.replace.argument_names))
except Exception as e:
    log("mesh.replace argument probe: %s" % e)


def do_replace():
    if "replace" in list(solver.mesh.command_names):
        return solver.mesh.replace(file_name=MESH)
    raise RuntimeError("no settings-API mesh.replace")


r = step("replace mesh via settings API", do_replace, critical=False)
if r is None and any("replace mesh via settings" in f for f in FAIL):
    step("replace mesh via TUI", lambda: solver.execute_tui('/mesh/replace "%s"' % MESH), critical=False)
step("mesh check", lambda: solver.mesh.check())
for cmd in ("size_info", "info"):
    step("mesh.%s" % cmd, (lambda c=cmd: getattr(solver.mesh, c)()), critical=False)

zones = {}
for kind in ("fluid", "solid"):
    try:
        zones["cell_" + kind] = list(getattr(solver.setup.cell_zone_conditions, kind).get_object_names())
    except Exception as e:
        zones["cell_" + kind] = ["<%s>" % e]
for kind in ("velocity_inlet", "pressure_outlet", "wall", "interior"):
    try:
        zones[kind] = list(getattr(solver.setup.boundary_conditions, kind).get_object_names())
    except Exception as e:
        zones[kind] = ["<%s>" % e]
log("ZONES " + json.dumps(zones))

B = step("snapshot settings (after replace)", snap)
write_json("Audit/probe_state_after_replace.json", B)


def diff(a, b, path=""):
    d = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                d.append((path + "/" + str(k), "<absent>", str(b[k])[:200]))
            elif k not in b:
                d.append((path + "/" + str(k), str(a[k])[:200], "<absent>"))
            else:
                d += diff(a[k], b[k], path + "/" + str(k))
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            d += diff(x, y, "%s[%d]" % (path, i))
    elif a != b:
        d.append((path, str(a)[:200], str(b)[:200]))
    return d


D = diff(A, B) if isinstance(A, dict) and isinstance(B, dict) else [("snapshot", "failed", "failed")]
log("SETTINGS DIFF medium case -> after replace: %d differences" % len(D))
for p, x, y in D[:80]:
    log("  DIFF %s : %s -> %s" % (p, x, y))
write_json("Audit/probe_state_diff.json", [{"path": p, "medium": x, "coarse": y} for p, x, y in D])
write_json("Audit/probe_zones.json", zones)
flush_log("Logs/probe_log.txt")
step("stop transcript", lambda: solver.file.stop_transcript(), critical=False)
print("PROBE-DONE")
exit()
