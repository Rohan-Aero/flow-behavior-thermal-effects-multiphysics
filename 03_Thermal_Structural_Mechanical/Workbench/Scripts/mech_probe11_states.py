# Section 7A probe 11 - dump object states (read-only; nothing changed, nothing solved)
import os
LOG = r"<PROJECT_ROOT>\08_Structural_Analysis\Workbench\Logs\mech_probe11_states_log.txt"
lines = []
def W(s):
    lines.append(str(s)); f = open(LOG, "w"); f.write("\n".join(lines)); f.close()
def walk(o, depth=0):
    try:
        st = o.ObjectState
    except Exception:
        st = "?"
    try:
        sup = o.Suppressed
    except Exception:
        sup = ""
    W("%s%s | %s | state=%s | suppressed=%s" % ("  " * depth, o.Name, o.GetType().Name, st, sup))
    try:
        for c in o.Children:
            walk(c, depth + 1)
    except Exception:
        pass
try:
    walk(Model)
    W("messages:")
    for m in ExtAPI.Application.Messages:
        W("  %s | %s" % (m.Severity, m.DisplayString[:400]))
    W("PROBE11-DONE")
except Exception as e:
    import traceback
    W("FATAL %s" % e); W(traceback.format_exc())
