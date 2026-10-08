# Python Script, API Version = V21
import os
out = r"<PROJECT_ROOT>\03_CAD_Geometry\Geometry_Check\probe.txt"
msgs = []
def L(s):
    msgs.append(str(s))
try:
    L("SCRIPT STARTED OK")
    try:
        L("API helper MM(10) = %s" % str(MM(10)))
    except Exception as e:
        L("MM() unavailable: %s" % e)
    try:
        p = GetRootPart()
        L("GetRootPart OK, bodies=%d" % len(p.Bodies))
    except Exception as e:
        L("GetRootPart failed: %s" % e)
    for nm in ["ViewHelper","SketchCircle","ExtrudeFaces","Body","Frame","CurveSegment","NamedSelection","DocumentSave","Selection","FaceSelection","BodySelection","ComponentHelper","Point2D","Plane","InteractionMode","ExtrudeFaceOptions","ExtrudeType","Window","WindowExportFormat"]:
        L("%-22s %s" % (nm, "YES" if nm in globals() or nm in dir() else "not-in-globals"))
except Exception as e:
    L("FATAL: %s" % e)
f = open(out, "w"); f.write("\n".join(msgs)); f.close()
