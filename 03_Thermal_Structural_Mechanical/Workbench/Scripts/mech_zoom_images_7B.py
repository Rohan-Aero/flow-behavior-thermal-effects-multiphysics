# -*- coding: utf-8 -*-
# SECTION 7B - close-up images of the SOLVED 7B Mechanical results at the critical locations (RE-ANALYSIS 2026).
# Read-only use of the solved project: activates existing result objects, moves the camera, exports PNG. Nothing is
# solved, changed or saved (the Workbench journal exits without saving).
import os, time
BASE = r"<PROJECT_ROOT>"
FIG = os.path.join(BASE, "08_Structural_Analysis", "Figures", "Mechanical", "Zoom")
LOG = os.path.join(BASE, "08_Structural_Analysis", "Audits", "mech_zoom_images_7B_log.txt")
if not os.path.isdir(FIG):
    os.makedirs(FIG)
lines = []


def W(s):
    lines.append(time.strftime("%H:%M:%S ") + str(s))
    f = open(LOG, "w")
    f.write("\n".join(lines))
    f.close()


def T(label, fn):
    try:
        r = fn()
        W("OK   %s %s" % (label, "" if r is None else str(r)[:200]))
        return r
    except Exception as e:
        W("FAIL %s: %s" % (label, str(e)[:300]))
        return None


def walk(o):
    out = []
    for c in o.Children:
        out.append(c)
        out.extend(walk(c))
    return out


try:
    ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS
    objs = {}
    for a in Model.Analyses:
        for o in walk(a):
            objs[(a.Name, o.Name)] = o
        W("analysis %s state %s" % (a.Name, a.Solution.ObjectState))
    st = Ansys.Mechanical.Graphics.GraphicsImageExportSettings()
    st.CurrentGraphicsDisplay = False
    st.Resolution = GraphicsResolutionType.EnhancedResolution
    st.Background = GraphicsBackgroundType.White
    st.Capture = GraphicsCaptureType.ImageAndLegend
    st.Width = 1600
    st.Height = 900
    W("camera members %s" % [m for m in dir(Graphics.Camera) if not m.startswith("_")])
    VIEWATTR = "ViewVector" if hasattr(Graphics.Camera, "ViewVector") else "ViewDirection"
    W("view attribute used: %s" % VIEWATTR)
    A1, A2, A3 = "LC1_Free_Expansion", "LC2_Axially_Restrained", "LC2P_Restrained_Thermal_Plus_Pressure"
    # (analysis, object, file tag, focal z [m], view direction, scene height [m])
    INLET = (0.0, (-0.45, -0.35, 1.0))     # camera looks towards +z: sees the inlet end face and the first ~30 mm
    OUTLET = (0.6, (-0.45, -0.35, -1.0))   # camera looks towards -z: sees the outlet end face
    jobs = [(A1, "Imported_Body_Temperature_CFD", "LC1_Z_inlet_Imported_Temperature", INLET, 0.07),
            (A1, "LC1_Equivalent_Stress_averaged", "LC1_Z_inlet_Equivalent_Stress", INLET, 0.07),
            (A1, "LC1_Maximum_Principal_Stress", "LC1_Z_inlet_Max_Principal", INLET, 0.07),
            (A1, "LC1_Hoop_Stress_Stheta_CS_DUCT_CYL", "LC1_Z_inlet_Hoop_Stress", INLET, 0.07),
            (A1, "LC1_Total_Deformation", "LC1_Z_outlet_Total_Deformation", OUTLET, 0.07),
            (A2, "LC2_Equivalent_Stress_averaged", "LC2_Z_inlet_Equivalent_Stress", INLET, 0.07),
            (A2, "LC2_Equivalent_Stress_UNaveraged", "LC2_Z_inlet_Equivalent_Stress_UNaveraged", INLET, 0.07),
            (A2, "LC2_Minimum_Principal_Stress", "LC2_Z_inlet_Min_Principal", INLET, 0.07),
            (A2, "LC2_Equivalent_Stress_averaged", "LC2_Z_outlet_Equivalent_Stress", OUTLET, 0.07),
            (A2, "LC2_Equivalent_Elastic_Strain", "LC2_Z_outlet_Equivalent_Elastic_Strain", OUTLET, 0.07),
            (A3, "LC2P_Equivalent_Stress_averaged", "LC2P_Z_inlet_Equivalent_Stress", INLET, 0.07)]
    for an, name, tag, (zf, vd), h in jobs:
        o = objs.get((an, name))
        if o is None:
            W("missing %s / %s" % (an, name))
            continue
        p = os.path.join(FIG, tag + ".png")
        T(tag, lambda: (o.Activate(),
                        Graphics.Camera.SetSpecificViewOrientation(ViewOrientationType.Iso),
                        setattr(Graphics.Camera, VIEWATTR, Vector3D(vd[0], vd[1], vd[2])),
                        setattr(Graphics.Camera, "UpVector", Vector3D(0, 1, 0)),
                        setattr(Graphics.Camera, "FocalPoint", Point([0.0, 0.0, zf], "m")),
                        setattr(Graphics.Camera, "SceneHeight", Quantity(h, "m")),
                        Graphics.ExportImage(p, GraphicsImageExportFormat.PNG, st)))
        W("%s exists %s" % (p, os.path.isfile(p)))
    W("ZOOM-IMAGES-DONE")
except Exception as e:
    import traceback
    W("FATAL %s" % e)
    W(traceback.format_exc())
