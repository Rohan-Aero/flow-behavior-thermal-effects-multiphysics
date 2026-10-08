# Section 7A - Mechanical probe 10 (throwaway project probe9): mesh-based mapping, handling of the structural nodes
# that lie between the source 48-gon chords and the true circular surfaces (<= 0.044 mm outside the source mesh).
# Variants of the bucket tolerance / outside option. Mapped values + solver INPUT files only; nothing is solved.
import os
OUT = r"<PROJECT_ROOT>\08_Structural_Analysis\Workbench\probe9"
LOG = os.path.join(OUT, "mech_probe10_log.txt")
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
        W("FAIL %s: %s" % (label, str(e)[:400]))
        return None


try:
    import System
    ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS
    NS = dict((n.Name, n) for n in Model.NamedSelections.Children)
    an = Model.Analyses[0]
    grp = [c for c in an.Children if c.GetType().Name == "ImportedLoadGroup"][0]
    for c in list(grp.Children):
        c.Delete()
    W("mesh %s %s" % (Model.Mesh.Nodes, Model.Mesh.Elements))
    variants = [("T1_abs0.1mm_Nearest", "AbsoluteGap", 1.0e-4, "NearestNode"),
                ("T2_abs0.1mm_Ignore", "AbsoluteGap", 1.0e-4, "Ignore"),
                ("T3_rel0.1_Ignore", "RelativeGap", 0.1, "Ignore")]
    for tag, key, val, oo in variants:
        for n in list(Model.NamedSelections.Children):
            if n.Name in ("Unmapped Nodes", "Outside Nodes", "Mapped Nodes"):
                n.Delete()
        ibt = grp.AddImportedBodyTemperature()
        ibt.Location = NS["SOLID_DOMAIN"]
        ibt.MappingControl = MappingControlType.Manual
        ibt.Algorithm = System.Enum.Parse(MappingAlgorithm, "BucketVolume")
        ibt.Weighting = System.Enum.Parse(WeightingType, "ShapeFunctions")
        T(tag + " outside", lambda: setattr(ibt, "OutsideOption", System.Enum.Parse(MappingOutsideOption, oo)))
        T(tag + " tol check on", lambda: setattr(ibt, "BucketToleranceCheck", System.Enum.Parse(ibt.BucketToleranceCheck.GetType(), "On")))
        T(tag + " tol key", lambda: setattr(ibt, "BucketToleranceKey", System.Enum.Parse(MappingToleranceKey, key)))
        if key == "AbsoluteGap":
            T(tag + " tol value", lambda: setattr(ibt, "BucketToleranceValue", Quantity(val, "m")))
        else:
            T(tag + " tol value (relative)", lambda: setattr(ibt, "BucketToleranceValue", Quantity(val, "")))
        ibt.CreateNameSelectionForOutsideNodes = True
        ibt.CreateNameSelectionForUnmappedNodes = True
        T(tag + " import", lambda: ibt.ImportLoad())
        W("%s state=%s alg=%s wt=%s out=%s tolcheck=%s key=%s val=%s" % (tag, ibt.ObjectState, ibt.Algorithm, ibt.Weighting,
                                                                          ibt.OutsideOption, ibt.BucketToleranceCheck,
                                                                          ibt.BucketToleranceKey, ibt.BucketToleranceValue))
        W("%s NS %s" % (tag, [(n.Name, n.Location.Ids.Count if hasattr(n.Location, "Ids") else "?")
                              for n in Model.NamedSelections.Children if "Nodes" in n.Name]))
        T(tag + " write input", lambda: an.WriteInputFile(os.path.join(OUT, "probe10_%s_ds.dat" % tag)))
        ibt.Suppressed = True
    W("PROBE10-DONE")
except Exception as e:
    import traceback
    W("FATAL %s" % e)
    W(traceback.format_exc())
