# Section 7A - Mechanical probe 9 (throwaway project probe9): mesh-based External Data (CDB master + node-id data)
# -> Imported Body Temperature on the structural mesh candidate M36. Mapped values + solver INPUT files only.
import os
OUT = r"<PROJECT_ROOT>\08_Structural_Analysis\Workbench\probe9"
LOG = os.path.join(OUT, "mech_probe9_log.txt")
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


try:
    import System
    ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS
    bodies = Model.Geometry.GetChildren(DataModelObjectCategory.Body, True)
    solid = [b for b in bodies if b.Name == "SOLID_DOMAIN"][0]
    fluid = [b for b in bodies if b.Name == "FLUID_DOMAIN"][0]
    fluid.Suppressed = True
    NS = dict((n.Name, n) for n in Model.NamedSelections.Children)
    edges = [e for e in solid.GetGeoBody().Edges]
    mesh = Model.Mesh
    for c in list(mesh.Children):
        c.Delete()
    mesh.ElementOrder = ElementOrder.Quadratic
    sw = mesh.AddAutomaticMethod()
    sw.Location = NS["SOLID_DOMAIN"]
    sw.Method = MethodType.Sweep
    sw.SweepNumberDivisions = 130
    sw.SweepBiasType = System.Enum.Parse(BiasType, "o_ooo_ooooo_ooo_o")
    sw.SweepBiasValue = 4.0
    fm = mesh.AddFaceMeshing()
    fm.Location = NS["SOLID_INLET_END"]
    fm.MappedMesh = True
    fm.InternalNumberOfDivisions = 5
    sel = ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
    sel.Ids = [e.Id for e in edges]
    sz = mesh.AddSizing()
    sz.Location = sel
    sz.Type = SizingType.NumberOfDivisions
    sz.NumberOfDivisions = 36
    sz.Behavior = SizingBehavior.Hard
    T("generate mesh", lambda: mesh.GenerateMesh())
    T("nodes/elements", lambda: (mesh.Nodes, mesh.Elements))
    an = Model.Analyses[0]
    an.EnvironmentTemperature = Quantity(300, "K")
    W("analysis children %s" % [(c.Name, c.GetType().Name) for c in an.Children])
    grp = [c for c in an.Children if c.GetType().Name == "ImportedLoadGroup"][0]
    variants = [("P0_ProgramControlled", None),
                ("P1_Bucket_ShapeFn_Projection", ("BucketVolume", "ShapeFunctions", "Projection")),
                ("P2_Bucket_ShapeFn_Nearest", ("BucketVolume", "ShapeFunctions", "NearestNode"))]
    for tag, opt in variants:
        for n in list(Model.NamedSelections.Children):
            if n.Name in ("Unmapped Nodes", "Outside Nodes", "Mapped Nodes"):
                n.Delete()
        ibt = grp.AddImportedBodyTemperature()
        ibt.Location = NS["SOLID_DOMAIN"]
        if opt is not None:
            T(tag + " manual", lambda: setattr(ibt, "MappingControl", MappingControlType.Manual))
            T(tag + " algorithm", lambda: setattr(ibt, "Algorithm", System.Enum.Parse(MappingAlgorithm, opt[0])))
            T(tag + " weighting", lambda: setattr(ibt, "Weighting", System.Enum.Parse(WeightingType, opt[1])))
            T(tag + " outside", lambda: setattr(ibt, "OutsideOption", System.Enum.Parse(MappingOutsideOption, opt[2])))
        ibt.CreateNameSelectionForOutsideNodes = True
        ibt.CreateNameSelectionForUnmappedNodes = True
        W("%s before import: id=%s control=%s alg=%s method=%s wt=%s out=%s" % (
            tag, ibt.ExternalDataIdentifier, ibt.MappingControl, ibt.Algorithm, ibt.Method, ibt.Weighting, ibt.OutsideOption))
        T(tag + " import", lambda: ibt.ImportLoad())
        W("%s after import: state=%s control=%s alg=%s method=%s wt=%s out=%s" % (
            tag, ibt.ObjectState, ibt.MappingControl, ibt.Algorithm, ibt.Method, ibt.Weighting, ibt.OutsideOption))
        T(tag + " source min/max", lambda: (ibt.SourceMinimum, ibt.SourceMaximum))
        W("%s NS %s" % (tag, [(n.Name, n.Location.Ids.Count if hasattr(n.Location, "Ids") else "?")
                              for n in Model.NamedSelections.Children if "Nodes" in n.Name]))
        T(tag + " export", lambda: ibt.ExportToTextFile(os.path.join(OUT, "probe9_%s_mapped.txt" % tag)))
        T(tag + " write input", lambda: an.WriteInputFile(os.path.join(OUT, "probe9_%s_ds.dat" % tag)))
        ibt.Suppressed = True
    W("messages %s" % [(str(m.Severity), m.DisplayString[:300]) for m in ExtAPI.Application.Messages])
    W("PROBE9-DONE")
except Exception as e:
    import traceback
    W("FATAL %s" % e)
    W(traceback.format_exc())
