# Section 7A - Mechanical probe 6 (throwaway project probe6): Fluent-system upstream -> Imported Body Temperature.
# Structural mesh candidate M36 (36 circ x 5 radial x 130 axial, quadratic sweep, bias 4 fine at both ends).
# Writes mapped values + solver INPUT file only. Nothing is solved.
import os
OUT = r"<PROJECT_ROOT>\08_Structural_Analysis\Workbench\probe6"
LOG = os.path.join(OUT, "mech_probe6_log.txt")
lines = []


def W(s):
    lines.append(str(s))
    f = open(LOG, "w")
    f.write("\n".join(lines))
    f.close()


def T(label, fn):
    try:
        r = fn()
        W("OK   %s %s" % (label, "" if r is None else str(r)[:500]))
        return r
    except Exception as e:
        W("FAIL %s: %s" % (label, str(e)[:500]))
        return None


def PROPS(n, o):
    for a in [x for x in dir(o) if not x.startswith("_")]:
        try:
            v = getattr(o, a)
            if not callable(v):
                W("   %s.%s = %s" % (n, a, str(v)[:200]))
        except Exception as e:
            W("   %s.%s -> %s" % (n, a, str(e)[:120]))


try:
    import System
    ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS
    bodies = Model.Geometry.GetChildren(DataModelObjectCategory.Body, True)
    solid = [b for b in bodies if b.Name == "SOLID_DOMAIN"][0]
    fluid = [b for b in bodies if b.Name == "FLUID_DOMAIN"][0]
    fluid.Suppressed = True
    NS = dict((n.Name, n) for n in Model.NamedSelections.Children)
    W("NS %s" % sorted(NS.keys()))
    edges = [e for e in solid.GetGeoBody().Edges]
    W("edges %s" % [(e.Id, str(e.CurveType), round(e.Length, 6)) for e in edges])
    mesh = Model.Mesh
    for c in list(mesh.Children):
        c.Delete()
    mesh.ElementOrder = ElementOrder.Quadratic
    sw = mesh.AddAutomaticMethod()
    sw.Location = NS["SOLID_DOMAIN"]
    sw.Method = MethodType.Sweep
    sw.SweepNumberDivisions = 130
    T("bias type", lambda: setattr(sw, "SweepBiasType", System.Enum.Parse(BiasType, "o_ooo_ooooo_ooo_o")))
    T("bias value", lambda: setattr(sw, "SweepBiasValue", 4.0))
    fm = mesh.AddFaceMeshing()
    fm.Location = NS["SOLID_INLET_END"]
    fm.MappedMesh = True
    fm.InternalNumberOfDivisions = 5
    sel = ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
    sel.Ids = [e.Id for e in edges if str(e.CurveType).lower().find("circ") >= 0] or [e.Id for e in edges]
    sz = mesh.AddSizing()
    sz.Location = sel
    sz.Type = SizingType.NumberOfDivisions
    sz.NumberOfDivisions = 36
    sz.Behavior = SizingBehavior.Hard
    T("generate mesh", lambda: mesh.GenerateMesh())
    T("nodes/elements", lambda: (mesh.Nodes, mesh.Elements))
    for mt in ("ElementQuality", "AspectRatio", "JacobianRatio", "Skewness", "MaximumCornerAngle"):
        try:
            mesh.MeshMetric = getattr(MeshMetricType, mt)
            W("METRIC %s min=%s max=%s avg=%s sd=%s" % (mt, mesh.Minimum, mesh.Maximum, mesh.Average, mesh.StandardDeviation))
        except Exception as e:
            W("metric %s failed %s" % (mt, e))
    an = Model.Analyses[0]
    T("env temp 300 K", lambda: setattr(an, "EnvironmentTemperature", Quantity(300, "K")))
    W("analysis children %s" % [(c.Name, c.GetType().Name) for c in an.Children])
    grps = [c for c in an.Children if "Imported" in c.GetType().Name]
    if not grps:
        W("NO IMPORTED LOAD GROUP - upstream link not effective")
    else:
        grp = grps[0]
        PROPS("group", grp)
        W("group methods %s" % [a for a in dir(grp) if a.startswith("Add")])
        ibt = grp.AddImportedBodyTemperature()
        ibt.Location = NS["SOLID_DOMAIN"]
        PROPS("ibt(before)", ibt)
        t = T("table", lambda: ibt.GetTableByName(""))
        if t is not None:
            W("table dir %s" % [a for a in dir(t) if not a.startswith("_")])
            T("table count", lambda: t.Count)
            for k in ("CFD Body", "CFD Surface", "Source", "Source Body", "Source Temperature", "Cell Zone",
                      "Analysis Load Step", "Scale", "Offset", "Source Time"):
                T("row0[%s]" % k, lambda kk=k: t[0][kk])
        T("import (program controlled)", lambda: ibt.ImportLoad())
        PROPS("ibt(after)", ibt)
        T("export mapped", lambda: ibt.ExportToTextFile(os.path.join(OUT, "probe6_mapped.txt")))
        T("write input", lambda: an.WriteInputFile(os.path.join(OUT, "probe6_ds.dat")))
        W("messages %s" % [(m.Severity, m.DisplayString[:300]) for m in ExtAPI.Application.Messages])
    W("PROBE6-DONE")
except Exception as e:
    import traceback
    W("FATAL %s" % e)
    W(traceback.format_exc())
