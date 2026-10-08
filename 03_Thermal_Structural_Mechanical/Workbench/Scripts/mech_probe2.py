# Section 7A - Mechanical API probe 2 (runs inside Mechanical via Workbench SendCommand/execfile).
# Throwaway: writes only into 08_Structural_Analysis/Workbench/probe2. Nothing is solved.
import os
OUT = r"<PROJECT_ROOT>\08_Structural_Analysis\Workbench\probe2"
LOG = os.path.join(OUT, "mech_probe2_log.txt")
lines = []


def W(s):
    lines.append(str(s))
    f = open(LOG, "w")
    f.write("\n".join(lines))
    f.close()


def T(label, fn):
    try:
        r = fn()
        W("OK   %s %s" % (label, "" if r is None else str(r)[:400]))
        return r
    except Exception as e:
        W("FAIL %s: %s" % (label, e))
        return None


def DD(n, o):
    try:
        W("DIR %s: %s" % (n, [a for a in dir(o) if not a.startswith("_")]))
    except Exception as e:
        W("DIR %s failed %s" % (n, e))


def PROPS(n, o, keys):
    for k in keys:
        try:
            W("   %s.%s = %s" % (n, k, getattr(o, k)))
        except Exception as e:
            W("   %s.%s -> %s" % (n, k, e))


try:
    import Ansys
    en = Ansys.Mechanical.DataModel.Enums
    for nm in dir(en):
        if any(k in nm for k in ("Outside", "Weight", "Mapping", "SweepBias", "Bias", "SizingType", "SizingBehavior",
                                 "ElementOrder", "MeshMetric", "MethodType", "SweepSource", "Transfer", "Validation",
                                 "ReferenceTemperature", "Interpolation", "ShapeFunction", "Algorithm")):
            try:
                W("ENUM %s: %s" % (nm, [m for m in dir(getattr(en, nm)) if not m.startswith("_") and m[0].isupper()][:40]))
            except Exception as e:
                W("ENUM %s err %s" % (nm, e))
    T("unit system before", lambda: ExtAPI.Application.ActiveUnitSystem)
    T("set StandardMKS", lambda: setattr(ExtAPI.Application, "ActiveUnitSystem", MechanicalUnitSystem.StandardMKS))
    bodies = Model.Geometry.GetChildren(DataModelObjectCategory.Body, True)
    for b in bodies:
        W("BODY %s material=%s suppressed=%s" % (b.Name, b.Material, b.Suppressed))
    solid = [b for b in bodies if b.Name == "SOLID_DOMAIN"][0]
    fluid = [b for b in bodies if b.Name == "FLUID_DOMAIN"][0]
    DD("body", solid)
    T("suppress fluid", lambda: setattr(fluid, "Suppressed", True))
    T("assign material", lambda: setattr(solid, "Material", "Inconel_718_Re_analysis"))
    T("material now", lambda: solid.Material)
    NS = dict((n.Name, n) for n in Model.NamedSelections.Children)
    W("NS %s" % sorted(NS.keys()))
    ge = solid.GetGeoBody()
    T("geo body faces/edges", lambda: (len(ge.Faces), len(ge.Edges), [f.SurfaceType for f in ge.Faces], [e.CurveType for e in ge.Edges]))
    mesh = Model.Mesh
    DD("mesh", mesh)
    T("element order quadratic", lambda: setattr(mesh, "ElementOrder", ElementOrder.Quadratic))
    sw = mesh.AddAutomaticMethod()
    DD("automethod", sw)
    T("sweep location", lambda: setattr(sw, "Location", NS["SOLID_DOMAIN"]))
    T("method sweep", lambda: setattr(sw, "Method", MethodType.Sweep))
    PROPS("sweep", sw, ["Method", "SourceTargetSelection", "SweepNumberDivisions", "SweepBiasType", "SweepBias",
                        "SweepElementSize", "SweepSizeBehavior", "FreeFaceMeshType", "Algorithm", "ElementOrder"])
    fm = mesh.AddFaceMeshing()
    DD("facemeshing", fm)
    sz = mesh.AddSizing()
    DD("sizing", sz)
    PROPS("sizing", sz, ["Type", "NumberOfDivisions", "Behavior", "BiasType", "BiasFactor", "BiasGrowthRate"])
    fm.Delete()
    sz.Delete()
    sw.Delete()
    an = Model.Analyses[0]
    DD("analysis", an)
    PROPS("analysis", an, ["EnvironmentTemperature", "PhysicsType", "AnalysisType"])
    W("analysis children %s" % [(c.Name, c.GetType().Name) for c in an.Children])
    grp = [c for c in an.Children if "Imported" in c.GetType().Name]
    if grp:
        g = grp[0]
        DD("imported group", g)
        ibt = g.AddImportedBodyTemperature()
        DD("ibt", ibt)
        props = [a for a in dir(ibt) if not a.startswith("_")]
        for a in props:
            try:
                v = getattr(ibt, a)
                if not callable(v):
                    W("   ibt.%s = %s" % (a, str(v)[:150]))
            except Exception as e:
                W("   ibt.%s -> %s" % (a, e))
        try:
            t = ibt.GetTableByName("")
            W("table type %s count %s" % (type(t), t.Count))
            DD("table", t)
            r0 = t[0]
            DD("row", r0)
            for k in ("Source Temperature", "Analysis Load Step", "Scale", "Offset"):
                try:
                    W("   row[%s] = %s" % (k, r0[k]))
                except Exception as e:
                    W("   row[%s] -> %s" % (k, e))
        except Exception as e:
            W("table failed %s" % e)
        ibt.Delete()
    W("PROBE2-DONE")
except Exception as e:
    import traceback
    W("FATAL %s" % e)
    W(traceback.format_exc())
