# Python Script, API Version = V21
# v5 (GUI): render real views of the CAD model
import os, json, traceback
BASE = r"<PROJECT_ROOT>\03_CAD_Geometry"
SS   = os.path.join(BASE, "Screenshots")
GC   = os.path.join(BASE, "Geometry_Check")
msgs = []
def L(s): msgs.append(str(s))

WEF = None
for mod in ["SpaceClaim.Api.V232", "SpaceClaim.Api.V231", "SpaceClaim.Api.V21", "SpaceClaim.Api.V20"]:
    try:
        m = __import__(mod, globals(), locals(), ["WindowExportFormat"])
        WEF = getattr(m, "WindowExportFormat")
        L("WindowExportFormat from %s" % mod); break
    except Exception:
        pass
if WEF is None: L("WindowExportFormat NOT importable")

try:
    DocumentOpen.Execute(os.path.join(BASE, "Native_CAD", "heated_duct.scdocx"))
    part = GetRootPart()
    win = Window.ActiveWindow
    L("opened; bodies=%d groups=%d  window=%s" % (len(part.Bodies), len(list(part.Groups)), win is not None))
    L("Window attrs: %s" % str([a for a in dir(win) if not a.startswith("_")][:60]))
    L("ViewHelper attrs: %s" % str([a for a in dir(ViewHelper) if not a.startswith("_")]))
    b0 = part.Bodies[0]
    L("DesignBody attrs (visibility): %s" % str([a for a in dir(b0) if "isib" in a.lower() or "tyle" in a.lower()]))

    bl = sorted([(b.Shape.Volume, b) for b in part.Bodies])
    fluid_b, solid_b = bl[0][1], bl[1][1]

    def shot(name):
        p = os.path.join(SS, name + ".png")
        ok = False
        try:
            win.Export(WEF.Png, p); ok = os.path.exists(p)
        except Exception as e:
            L("  export(%s) err: %s" % (name, e))
        if not ok:
            try:
                win.Export(WEF.Png, p, True); ok = os.path.exists(p)
            except Exception as e:
                L("  export2(%s) err: %s" % (name, e))
        L("  shot %-34s -> %s" % (name, ok))
        return ok

    def vis(body, state):
        for meth in ["SetVisibility"]:
            try:
                getattr(body, meth)(None, state); return True
            except Exception:
                try:
                    getattr(body, meth)(state); return True
                except Exception: pass
        return False

    def iso():
        for m in ["SetViewIsometric", "SetIsometricView"]:
            try: getattr(ViewHelper, m)(); return m
            except Exception: pass
        try:
            win.SetViewIsometric(); return "win.SetViewIsometric"
        except Exception: pass
        return "none"
    L("iso method: %s" % iso())
    try: win.ZoomExtents()
    except Exception as e: L("ZoomExtents err: %s" % e)

    L("-- rendering --")
    shot("01_full_cad_model")
    vis(fluid_b, False); 
    try: win.ZoomExtents()
    except Exception: pass
    shot("04_solid_body_only")
    vis(fluid_b, True); vis(solid_b, False)
    try: win.ZoomExtents()
    except Exception: pass
    shot("03_fluid_body_only")
    vis(solid_b, True)
    try: win.ZoomExtents()
    except Exception: pass
    shot("09_final_geometry_in_ansys")
    L("=== v5 DONE ===")
except Exception as e:
    L("FATAL: %s" % e); L(traceback.format_exc())
f=open(os.path.join(GC,"v5_log.txt"),"w"); f.write("\n".join(msgs)); f.close()
