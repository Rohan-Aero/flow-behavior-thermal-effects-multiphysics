# Section 7A - Mechanical probe 3 (throwaway project probe2): mesh controls, mesh stats, temperature import,
# export of mapped values and solver input file. Nothing is solved.
import os
OUT = r"<PROJECT_ROOT>\08_Structural_Analysis\Workbench\probe2"
LOG = os.path.join(OUT, "mech_probe3_log.txt")
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


try:
    import System
    for enm in (BiasType, BiasOptionType, MeshMetricType):
        try:
            W("NAMES %s: %s" % (enm, list(System.Enum.GetNames(enm))))
            W("VALUES %s: %s" % (enm, [int(v) for v in System.Enum.GetValues(enm)]))
        except Exception as e:
            W("names failed %s" % e)
    ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS
    NS = dict((n.Name, n) for n in Model.NamedSelections.Children)
    solid = [b for b in Model.Geometry.GetChildren(DataModelObjectCategory.Body, True) if b.Name == "SOLID_DOMAIN"][0]
    ge = solid.GetGeoBody()
    edges = [e for e in ge.Edges]
    W("edges: %s" % [(e.Id, e.CurveType, round(e.Length, 6), [round(c, 5) for c in e.Centroid]) for e in edges])
    mesh = Model.Mesh
    for c in list(mesh.Children):
        c.Delete()
    mesh.ElementOrder = ElementOrder.Quadratic
    sw = mesh.AddAutomaticMethod()
    sw.Location = NS["SOLID_DOMAIN"]
    sw.Method = MethodType.Sweep
    W("sweep attrs: %s" % [a for a in dir(sw) if "Sweep" in a or "Bias" in a or "Source" in a or "Target" in a])
    T("sweep divisions 100", lambda: setattr(sw, "SweepNumberDivisions", 100))
    fm = mesh.AddFaceMeshing()
    fm.Location = NS["SOLID_INLET_END"]
    T("mapped", lambda: setattr(fm, "MappedMesh", True))
    T("internal divisions 5", lambda: setattr(fm, "InternalNumberOfDivisions", 5))
    sel = ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
    sel.Ids = [e.Id for e in edges]
    sz = mesh.AddSizing()
    sz.Location = sel
    sz.Type = SizingType.NumberOfDivisions
    sz.NumberOfDivisions = 48
    sz.Behavior = SizingBehavior.Hard
    T("generate mesh", lambda: mesh.GenerateMesh())
    T("mesh nodes/elements", lambda: (mesh.Nodes, mesh.Elements))
    for mt in ("ElementQuality", "AspectRatio", "JacobianRatio", "Skewness", "OrthogonalQuality", "MaximumCornerAngle"):
        try:
            mesh.MeshMetric = getattr(MeshMetricType, mt)
            W("METRIC %s min=%s max=%s avg=%s sd=%s" % (mt, mesh.Minimum, mesh.Maximum, mesh.Average, mesh.StandardDeviation))
        except Exception as e:
            W("metric %s failed %s" % (mt, e))
    an = Model.Analyses[0]
    T("env temp 300 K", lambda: setattr(an, "EnvironmentTemperature", Quantity(300, "K")))
    grp = [c for c in an.Children if c.GetType().Name == "ImportedLoadGroup"][0]
    ibt = grp.AddImportedBodyTemperature()
    ibt.Location = NS["SOLID_DOMAIN"]
    T("mapping control manual", lambda: setattr(ibt, "MappingControl", MappingControlType.Manual))
    T("weighting triangulation", lambda: setattr(ibt, "Weighting", WeightingType.Triangulation))
    T("outside projection", lambda: setattr(ibt, "OutsideOption", MappingOutsideOption.Projection))
    T("create NS outside", lambda: setattr(ibt, "CreateNameSelectionForOutsideNodes", True))
    T("create NS unmapped", lambda: setattr(ibt, "CreateNameSelectionForUnmappedNodes", True))
    t = ibt.GetTableByName("")
    T("row source", lambda: t[0].__setitem__("Source Temperature", "File1:Temperature1"))
    T("row step", lambda: t[0].__setitem__("Analysis Load Step", "1"))
    W("row now: %s %s %s %s" % (t[0]["Source Temperature"], t[0]["Analysis Load Step"], t[0]["Scale"], t[0]["Offset"]))
    T("import", lambda: ibt.ImportLoad())
    W("ibt state %s; props: Algorithm=%s Method=%s Weighting=%s Outside=%s" % (ibt.ObjectState, ibt.Algorithm, ibt.Method,
                                                                              ibt.Weighting, ibt.OutsideOption))
    for a in ("SourceMinimum", "SourceMaximum"):
        T(a, lambda aa=a: getattr(ibt, aa))
    T("export mapped", lambda: ibt.ExportToTextFile(os.path.join(OUT, "probe3_mapped.txt")))
    T("NS after import", lambda: [(n.Name, n.TotalSelection if hasattr(n, "TotalSelection") else "") for n in Model.NamedSelections.Children])
    T("write input file", lambda: an.WriteInputFile(os.path.join(OUT, "probe3_ds.dat")))
    W("PROBE3-DONE")
except Exception as e:
    import traceback
    W("FATAL %s" % e)
    W(traceback.format_exc())
