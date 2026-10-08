# Section 7A - Mechanical probe 4 (throwaway project probe2): biased sweep + mapping-algorithm variants.
import os
OUT = r"<PROJECT_ROOT>\08_Structural_Analysis\Workbench\probe2"
LOG = os.path.join(OUT, "mech_probe4_log.txt")
lines = []
def W(s):
    lines.append(str(s)); f = open(LOG, "w"); f.write("\n".join(lines)); f.close()
def T(label, fn):
    try:
        r = fn(); W("OK   %s %s" % (label, "" if r is None else str(r)[:300])); return r
    except Exception as e:
        W("FAIL %s: %s" % (label, str(e)[:300])); return None
try:
    import System
    ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS
    NS = dict((n.Name, n) for n in Model.NamedSelections.Children)
    mesh = Model.Mesh
    sw = [c for c in mesh.Children if c.GetType().Name == "AutomaticMethod"][0]
    names = list(System.Enum.GetNames(BiasType))
    W("bias names %s" % names)
    T("bias type both-ends-fine", lambda: setattr(sw, "SweepBiasType", System.Enum.Parse(BiasType, "o_ooo_ooooo_ooo_o")))
    T("bias value 5", lambda: setattr(sw, "SweepBiasValue", 5.0))
    W("sweep: divs=%s biastype=%s biasvalue=%s" % (sw.SweepNumberDivisions, sw.SweepBiasType, sw.SweepBiasValue))
    T("generate mesh", lambda: mesh.GenerateMesh())
    T("nodes/elements", lambda: (mesh.Nodes, mesh.Elements))
    for mt in ("ElementQuality", "AspectRatio", "JacobianRatio", "Skewness", "MaximumCornerAngle", "WarpingFactor", "ParallelDeviation"):
        try:
            mesh.MeshMetric = getattr(MeshMetricType, mt)
            W("METRIC %s min=%s max=%s avg=%s sd=%s" % (mt, mesh.Minimum, mesh.Maximum, mesh.Average, mesh.StandardDeviation))
        except Exception as e:
            W("metric %s failed %s" % (mt, e))
    an = Model.Analyses[0]
    grp = [c for c in an.Children if c.GetType().Name == "ImportedLoadGroup"][0]
    for c in list(grp.Children):
        c.Delete()
    for n in list(Model.NamedSelections.Children):
        if n.Name in ("Unmapped Nodes", "Outside Nodes", "Mapped Nodes"):
            n.Delete()
    variants = [("V1_PointCloud_Tri_Projection", "PointCloud", "Triangulation", "Projection"),
                ("V2_PointCloud_Tri_Nearest", "PointCloud", "Triangulation", "NearestNode"),
                ("V3_Bucket_Tri_Projection", "BucketVolume", "Triangulation", "Projection")]
    for tag, alg, wt, oo in variants:
        ibt = grp.AddImportedBodyTemperature()
        ibt.Location = NS["SOLID_DOMAIN"]
        T(tag + " control manual", lambda: setattr(ibt, "MappingControl", MappingControlType.Manual))
        T(tag + " algorithm", lambda: setattr(ibt, "Algorithm", System.Enum.Parse(MappingAlgorithm, alg)))
        T(tag + " weighting", lambda: setattr(ibt, "Weighting", System.Enum.Parse(WeightingType, wt)))
        T(tag + " outside", lambda: setattr(ibt, "OutsideOption", System.Enum.Parse(MappingOutsideOption, oo)))
        ibt.CreateNameSelectionForOutsideNodes = True
        ibt.CreateNameSelectionForUnmappedNodes = True
        T(tag + " import", lambda: ibt.ImportLoad())
        W("%s state=%s alg=%s method=%s wt=%s out=%s" % (tag, ibt.ObjectState, ibt.Algorithm, ibt.Method, ibt.Weighting, ibt.OutsideOption))
        W("%s NS %s" % (tag, [(n.Name, n.Location.Ids.Count if hasattr(n.Location, "Ids") else "?") for n in Model.NamedSelections.Children if "Nodes" in n.Name]))
        T(tag + " export", lambda: ibt.ExportToTextFile(os.path.join(OUT, "probe4_%s_mapped.txt" % tag)))
        T(tag + " write input", lambda: an.WriteInputFile(os.path.join(OUT, "probe4_%s_ds.dat" % tag)))
        ibt.Suppressed = True
        for n in list(Model.NamedSelections.Children):
            if n.Name in ("Unmapped Nodes", "Outside Nodes", "Mapped Nodes"):
                n.Delete()
    W("PROBE4-DONE")
except Exception as e:
    import traceback
    W("FATAL %s" % e); W(traceback.format_exc())
