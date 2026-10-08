# Section 7A - Mechanical probe 8 (throwaway project probe2): point-cloud weighting variants that do NOT rely on
# the 3-D triangulation (Kriging, radial basis functions). Mapped values + solver INPUT files only; nothing is solved.
import os
OUT = r"<PROJECT_ROOT>\08_Structural_Analysis\Workbench\probe2"
LOG = os.path.join(OUT, "mech_probe8_log.txt")
lines = []


def W(s):
    lines.append(str(s))
    f = open(LOG, "w")
    f.write("\n".join(lines))
    f.close()


def T(label, fn):
    try:
        r = fn()
        W("OK   %s %s" % (label, "" if r is None else str(r)[:300]))
        return r
    except Exception as e:
        W("FAIL %s: %s" % (label, str(e)[:300]))
        return None


try:
    import System
    ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS
    NS = dict((n.Name, n) for n in Model.NamedSelections.Children)
    mesh = Model.Mesh
    W("mesh nodes/elements %s %s" % (mesh.Nodes, mesh.Elements))
    an = Model.Analyses[0]
    grp = [c for c in an.Children if c.GetType().Name == "ImportedLoadGroup"][0]
    for c in list(grp.Children):
        c.Delete()
    probe = grp.AddImportedBodyTemperature()
    for p in ("KrigingPolynom", "KrigingCorrelationFunction"):
        try:
            W("ENUM %s %s" % (p, list(System.Enum.GetNames(getattr(probe, p).GetType()))))
        except Exception as e:
            W("enum %s failed %s" % (p, e))
    probe.Delete()
    variants = [("K1_Kriging_Linear", "KrigingFunction", {"KrigingPolynom": "PolyLinear"}),
                ("K2_Kriging_Quadratic", "KrigingFunction", {"KrigingPolynom": "PolyQuadratic"}),
                ("R1_RBF", "RadialBasisFunctions", {})]
    for tag, wt, extra in variants:
        for n in list(Model.NamedSelections.Children):
            if n.Name in ("Unmapped Nodes", "Outside Nodes", "Mapped Nodes"):
                n.Delete()
        ibt = grp.AddImportedBodyTemperature()
        ibt.Location = NS["SOLID_DOMAIN"]
        T(tag + " control manual", lambda: setattr(ibt, "MappingControl", MappingControlType.Manual))
        T(tag + " algorithm", lambda: setattr(ibt, "Algorithm", System.Enum.Parse(MappingAlgorithm, "PointCloud")))
        T(tag + " weighting", lambda: setattr(ibt, "Weighting", System.Enum.Parse(WeightingType, wt)))
        for k, v in extra.items():
            T(tag + " " + k, lambda kk=k, vv=v: setattr(ibt, kk, System.Enum.Parse(getattr(ibt, kk).GetType(), vv)))
        T(tag + " outside projection", lambda: setattr(ibt, "OutsideOption", System.Enum.Parse(MappingOutsideOption, "Projection")))
        ibt.CreateNameSelectionForOutsideNodes = True
        ibt.CreateNameSelectionForUnmappedNodes = True
        T(tag + " import", lambda: ibt.ImportLoad())
        W("%s state=%s alg=%s wt=%s poly=%s corr=%s limit=%s out=%s" % (tag, ibt.ObjectState, ibt.Algorithm, ibt.Weighting,
                                                                          ibt.KrigingPolynom, ibt.KrigingCorrelationFunction,
                                                                          ibt.Limit, ibt.OutsideOption))
        W("%s NS %s" % (tag, [(n.Name, n.Location.Ids.Count if hasattr(n.Location, "Ids") else "?")
                              for n in Model.NamedSelections.Children if "Nodes" in n.Name]))
        T(tag + " write input", lambda: an.WriteInputFile(os.path.join(OUT, "probe8_%s_ds.dat" % tag)))
        ibt.Suppressed = True
    W("PROBE8-DONE")
except Exception as e:
    import traceback
    W("FATAL %s" % e)
    W(traceback.format_exc())
