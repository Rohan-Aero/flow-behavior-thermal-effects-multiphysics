# -*- coding: utf-8 -*-
# =====================================================================================================
# SECTION 7A - Mechanical build script (runs inside Mechanical via Workbench SendCommand). NOTHING IS SOLVED.
# RE-ANALYSIS 2026 - newly built model.
#   - SOLID_DOMAIN only (FLUID_DOMAIN suppressed), material Inconel_718_Re_analysis
#   - structural mesh M36: SOLID186, swept, 36 circumferential x 5 through-wall x 130 axial (bias 4, fine at both ends)
#   - both analyses: environment (reference) temperature 300 K; Imported Body Temperature from External Data
#     (mesh-based: Bucket Volume + Shape Functions; nodes in the chord/arc gap of the 48-gon source -> Nearest Node)
#   - LC1 free expansion: 3 nodes at the inlet end, outer radius, 0/120/240 deg: U_theta = 0, U_z = 0 (cyl. CS)
#   - LC2 axially restrained: U_z = 0 on both end faces + 3 mid-span outer nodes U_theta = 0 (radial free everywhere)
#   RUN 5: origin-define-by enum is CoordinateSystemAlignmentType (run 4 crashed using GeometryDefineByType).
#   RUN 4: CS_DUCT_CYL origin defined by coordinates (run 3: CS under-defined -> Solution 'UnderDefined').
#   RUN 3: no native MappingValidation object (run 2 crashed while probing it). RUN 2: Direct FE supports only; LC2 hoop nodes at mid-span (run 1 LC2 conflict: face U_z + Direct FE on same nodes)
#   - internal gauge pressure prepared on SOLID_INNER_INTERFACE and SUPPRESSED (two variants)
#   - solver input files written with WriteInputFile (no solve); mapped temperatures exported
# =====================================================================================================
import os, json, math
BASE = r"<PROJECT_ROOT>"
LOGDIR = os.path.join(BASE, "08_Structural_Analysis", "Mechanical_Setup", "Logs")
INP = os.path.join(BASE, "08_Structural_Analysis", "Mechanical_Setup", "Input_Files")
MAPX = os.path.join(BASE, "07_Thermal_Analysis", "Mapping", "Mechanical_Export")
for d in (LOGDIR, INP, MAPX):
    if not os.path.isdir(d):
        os.makedirs(d)
LOG = os.path.join(LOGDIR, "mech_build_7A_log.txt")
SUMMARY = {}
lines = []


def W(s):
    lines.append(str(s))
    f = open(LOG, "w")
    f.write("\n".join(lines))
    f.close()


def T(label, fn, critical=False):
    try:
        r = fn()
        W("OK   %s %s" % (label, "" if r is None else str(r)[:400]))
        return r
    except Exception as e:
        W("FAIL %s: %s" % (label, str(e)[:400]))
        if critical:
            raise
        return None


def dump():
    f = open(os.path.join(LOGDIR, "mech_build_7A_summary.json"), "w")
    f.write(json.dumps(SUMMARY, indent=1, default=str))
    f.close()


try:
    import System
    W("=== SECTION 7A MECHANICAL BUILD (no solve) ===")
    ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS
    SUMMARY["unit_system"] = str(ExtAPI.Application.ActiveUnitSystem)
    # ---------------- geometry / material ----------------
    bodies = Model.Geometry.GetChildren(DataModelObjectCategory.Body, True)
    solid = [b for b in bodies if b.Name == "SOLID_DOMAIN"][0]
    fluid = [b for b in bodies if b.Name == "FLUID_DOMAIN"][0]
    fluid.Suppressed = True
    T("assign material", lambda: setattr(solid, "Material", "Inconel_718_Re_analysis"), critical=True)
    SUMMARY["solid_body"] = {"material": str(solid.Material), "fluid_suppressed": bool(fluid.Suppressed)}
    for a in ("ReferenceTemperature", "ReferenceTemperatureType", "StiffnessBehavior", "Volume", "Mass"):
        SUMMARY["solid_body"][a] = str(T("body " + a, lambda aa=a: getattr(solid, aa)))
    NS = dict((n.Name, n) for n in Model.NamedSelections.Children)
    W("geometry NS %s" % sorted(NS.keys()))
    # ---------------- structural mesh M36 ----------------
    mesh = Model.Mesh
    for c in list(mesh.Children):
        c.Delete()
    mesh.ElementOrder = ElementOrder.Quadratic
    sw = mesh.AddAutomaticMethod()
    sw.Name = "M36_Sweep_130_axial_bias4"
    sw.Location = NS["SOLID_DOMAIN"]
    sw.Method = MethodType.Sweep
    sw.SweepNumberDivisions = 130
    T("bias both ends", lambda: setattr(sw, "SweepBiasType", System.Enum.Parse(BiasType, "o_ooo_ooooo_ooo_o")), critical=True)
    T("bias factor 4", lambda: setattr(sw, "SweepBiasValue", 4.0), critical=True)
    fm = mesh.AddFaceMeshing()
    fm.Name = "M36_Mapped_End_5_radial"
    fm.Location = NS["SOLID_INLET_END"]
    fm.MappedMesh = True
    fm.InternalNumberOfDivisions = 5
    edges = [e for e in solid.GetGeoBody().Edges]
    sel = ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
    sel.Ids = [e.Id for e in edges]
    sz = mesh.AddSizing()
    sz.Name = "M36_36_circumferential"
    sz.Location = sel
    sz.Type = SizingType.NumberOfDivisions
    sz.NumberOfDivisions = 36
    sz.Behavior = SizingBehavior.Hard
    T("generate mesh", lambda: mesh.GenerateMesh(), critical=True)
    SUMMARY["mesh"] = {"nodes": int(mesh.Nodes), "elements": int(mesh.Elements), "order": str(mesh.ElementOrder),
                       "edges": [(e.Id, str(e.CurveType), e.Length) for e in edges]}
    W("mesh nodes %s elements %s" % (mesh.Nodes, mesh.Elements))
    if mesh.Nodes >= 128000:
        raise Exception("mesh exceeds the measured MAPDL Student node limit (128,000)")
    met = {}
    for mt in ("ElementQuality", "AspectRatio", "JacobianRatio", "WarpingFactor", "ParallelDeviation",
               "MaximumCornerAngle", "Skewness", "OrthogonalQuality"):
        try:
            mesh.MeshMetric = getattr(MeshMetricType, mt)
            met[mt] = {"min": str(mesh.Minimum), "max": str(mesh.Maximum), "avg": str(mesh.Average),
                       "sd": str(mesh.StandardDeviation)}
        except Exception as e:
            met[mt] = "n/a %s" % str(e)[:120]
    SUMMARY["mesh"]["metrics"] = met
    W("metrics %s" % met)
    dump()
    # ---------------- cylindrical CS and the three support nodes ----------------
    cs = Model.CoordinateSystems.AddCoordinateSystem()
    cs.Name = "CS_DUCT_CYL"
    cs.CoordinateSystemType = CoordinateSystemTypeEnum.Cylindrical
    # RUN 4: origin defined explicitly by global coordinates (run 3 left the CS 'UnderDefined' - no geometry scoping -
    # which made both Solution objects 'UnderDefined' and the Workbench Setup cells 'Incomplete'; probe 11 diagnosis)
    import System
    names = list(System.Enum.GetNames(CoordinateSystemAlignmentType))
    W("CoordinateSystemAlignmentType names %s" % names)
    pick = [n for n in ("Fixed", "GlobalCoordinates", "Global") if n in names]
    if not pick:
        raise Exception("no 'global coordinates' member in CoordinateSystemAlignmentType: %s" % names)
    T("cs origin define by %s (global coordinates)" % pick[0],
      lambda: setattr(cs, "OriginDefineBy", System.Enum.Parse(CoordinateSystemAlignmentType, pick[0])), critical=True)
    for k in ("OriginX", "OriginY", "OriginZ"):
        T("cs " + k, lambda kk=k: setattr(cs, kk, Quantity(0.0, "m")), critical=True)
    T("cs origin", lambda: (cs.OriginX, cs.OriginY, cs.OriginZ))
    SUMMARY["cs_duct_cyl"] = {"state": str(cs.ObjectState), "type": str(cs.CoordinateSystemType),
                              "origin_define_by": str(T("cs define by", lambda: cs.OriginDefineBy))}
    W("CS_DUCT_CYL state %s" % cs.ObjectState)
    if "UnderDefined" in str(cs.ObjectState):
        raise Exception("CS_DUCT_CYL still under-defined")
    md = ExtAPI.DataModel.MeshDataByName(ExtAPI.DataModel.MeshDataNames[0])
    allnodes = [(n.Id, n.X, n.Y, n.Z) for n in md.Nodes]

    def three_nodes(zz, nsname):
        ring = [(i, x, y, z, math.degrees(math.atan2(y, x))) for (i, x, y, z) in allnodes
                if abs(z - zz) < 1e-7 and abs(math.hypot(x, y) - 0.02) < 1e-7]
        picks = []
        for target in (0.0, 120.0, -120.0):
            best = min(ring, key=lambda t: abs(((t[4] - target) + 180.0) % 360.0 - 180.0))
            dev = abs(((best[4] - target) + 180.0) % 360.0 - 180.0)
            if dev > 0.01:
                raise Exception("no mesh node at %s deg on the outer ring z=%s (closest %.4f deg)" % (target, zz, best[4]))
            picks.append(best)
        nsel = ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.MeshNodes)
        nsel.Ids = [p[0] for p in picks]
        ns = Model.AddNamedSelection()
        ns.Name = nsname
        ns.Location = nsel
        info = {"named_selection": nsname, "ring_nodes": len(ring),
                "nodes": [{"id": p[0], "x": p[1], "y": p[2], "z": p[3], "theta_deg": p[4]} for p in picks]}
        W("%s %s" % (nsname, info))
        return ns, info

    # LC1: inlet end (= STRUCTURAL_SUPPORT face, D-025), outer radius. LC2: mid-span, outer radius - the LC2 end faces
    # carry U_z = 0 and Mechanical does not allow Direct FE constraints on nodes that already carry a face constraint
    # (run 1: "conflicting DOF constraints with defined Direct FE loading").
    nsN, SUMMARY["support_nodes_LC1"] = three_nodes(0.0, "NS_LC1_SUPPORT_3NODES_INLET_OUTER")
    nsM, SUMMARY["support_nodes_LC2"] = three_nodes(0.3, "NS_LC2_HOOP_3NODES_MIDSPAN_OUTER")
    # ---------------- analyses ----------------
    an1, an2 = Model.Analyses[0], Model.Analyses[1]
    an1.Name = "LC1_Free_Expansion"
    an2.Name = "LC2_Axially_Restrained"
    SUMMARY["analyses"] = {}

    def imported_temperature(an, tag):
        an.EnvironmentTemperature = Quantity(300, "K")
        grp = [c for c in an.Children if c.GetType().Name == "ImportedLoadGroup"][0]
        ibt = grp.AddImportedBodyTemperature()
        ibt.Name = "Imported_Body_Temperature_CFD"
        ibt.Location = NS["SOLID_DOMAIN"]
        ibt.MappingControl = MappingControlType.Manual
        ibt.Algorithm = System.Enum.Parse(MappingAlgorithm, "BucketVolume")
        ibt.Weighting = System.Enum.Parse(WeightingType, "ShapeFunctions")
        ibt.OutsideOption = System.Enum.Parse(MappingOutsideOption, "NearestNode")
        ibt.CreateNameSelectionForOutsideNodes = True
        ibt.CreateNameSelectionForUnmappedNodes = True
        T(tag + " outside NS name", lambda: setattr(ibt, "OutsideNodesName", tag + "_MAP_OUTSIDE_NODES"))
        T(tag + " unmapped NS name", lambda: setattr(ibt, "UnmappedNodesName", tag + "_MAP_UNMAPPED_NODES"))
        T(tag + " import", lambda: ibt.ImportLoad(), critical=True)
        info = {"state": str(ibt.ObjectState), "identifier": str(ibt.ExternalDataIdentifier),
                "control": str(ibt.MappingControl), "algorithm": str(ibt.Algorithm), "method": str(ibt.Method),
                "weighting": str(ibt.Weighting), "outside": str(ibt.OutsideOption),
                "bucket_tol": [str(ibt.BucketToleranceCheck), str(ibt.BucketToleranceKey), str(ibt.BucketToleranceValue)],
                "source_min": str(T(tag + " src min", lambda: ibt.SourceMinimum)),
                "source_max": str(T(tag + " src max", lambda: ibt.SourceMaximum)),
                "environment_temperature": str(an.EnvironmentTemperature)}
        info["mapping_NS"] = [(n.Name, n.Location.Ids.Count if hasattr(n.Location, "Ids") else "?")
                              for n in Model.NamedSelections.Children if n.Name.startswith(tag + "_MAP")]
        T(tag + " export mapped", lambda: ibt.ExportToTextFile(os.path.join(MAPX, tag + "_imported_body_temperature.txt")))
        info["native_mapping_validation_object"] = "not added: the batch API gives no statistics (run 2 probe crashed on it); verification is external (validate_mapping_7A.py)"
        W("%s imported temperature %s" % (tag, info))
        return ibt, info

    def disp(an, name, loc, cs_obj, comps):
        d = an.AddDisplacement()
        d.Name = name
        d.Location = loc
        if cs_obj is not None:
            d.CoordinateSystem = cs_obj
        for k in comps:
            getattr(d, k + "Component").Output.DiscreteValues = [Quantity("0 [m]")]
        return {"name": name, "cs": (cs_obj.Name if cs_obj is not None else "Global Cartesian"),
                "fixed": comps, "state": str(d.ObjectState),
                "X": str(d.XComponent.Output.DefinitionType), "Y": str(d.YComponent.Output.DefinitionType),
                "Z": str(d.ZComponent.Output.DefinitionType)}

    def support(an, name, ns, comps):
        """Direct FE: nodal orientation to the cylindrical CS (x = r, y = theta, z = axial) + nodal displacement.
        (A standard Displacement scoped to a node-based selection has a read-only coordinate system - run 1.)"""
        no = an.AddNodalOrientation()
        no.Name = name + "_orientation_CS_DUCT_CYL"
        no.Location = ns
        no.CoordinateSystem = cs
        nd = an.AddNodalDisplacement()
        nd.Name = name
        nd.Location = ns
        for k in comps:
            getattr(nd, k + "Component").Output.DiscreteValues = [Quantity("0 [m]")]
        return {"name": name, "type": "Direct FE: NodalOrientation (CS_DUCT_CYL) + NodalDisplacement", "named_selection": ns.Name,
                "fixed_in_cyl_CS": comps, "free": [c for c in ("X", "Y", "Z") if c not in comps],
                "state": str(nd.ObjectState), "orientation_state": str(no.ObjectState)}

    def pressure(an, tag):
        out = []
        p1 = an.AddPressure()
        p1.Name = tag + "_P_equivalent_uniform_443Pa_SUPPRESSED"
        p1.Location = NS["SOLID_INNER_INTERFACE"]
        p1.Magnitude.Output.DiscreteValues = [Quantity("443.41 [Pa]")]
        p1.Suppressed = True
        out.append({"name": p1.Name, "definition": "uniform 443.41 Pa gauge (CFD wall maximum, first station)",
                    "suppressed": bool(p1.Suppressed)})
        p2 = an.AddPressure()
        p2.Name = tag + "_P_CFD_linear_fit_SUPPRESSED"
        p2.Location = NS["SOLID_INNER_INTERFACE"]
        ok = T(tag + " pressure formula", lambda: (setattr(p2.Magnitude.Output, "DefinitionType", VariableDefinitionType.Formula),
                                                  setattr(p2.Magnitude.Output, "Formula", "407.36-681.55*z")))
        p2.Suppressed = True
        out.append({"name": p2.Name, "definition": "p(z) = 407.36 - 681.55 z [Pa gauge, z in m] (least-squares fit of the 90 CFD wall stations)",
                    "formula_set": ok is not None, "formula_readback": str(T(tag + " formula readback", lambda: p2.Magnitude.Output.Formula)),
                    "suppressed": bool(p2.Suppressed)})
        return out

    # LC1
    ibt1, i1 = imported_temperature(an1, "LC1")
    s1 = support(an1, "LC1_SUPPORT_3NODES_Utheta0_Uz0", nsN, ["Y", "Z"])
    SUMMARY["analyses"]["LC1"] = {"name": an1.Name, "imported_temperature": i1, "supports": [s1], "pressure": pressure(an1, "LC1")}
    dump()
    # LC2
    ibt2, i2 = imported_temperature(an2, "LC2")
    e_in = disp(an2, "LC2_INLET_END_Uz0", NS["SOLID_INLET_END"], None, ["Z"])
    e_out = disp(an2, "LC2_OUTLET_END_Uz0", NS["SOLID_OUTLET_END"], None, ["Z"])
    s2 = support(an2, "LC2_HOOP_3NODES_MIDSPAN_Utheta0", nsM, ["Y"])
    SUMMARY["analyses"]["LC2"] = {"name": an2.Name, "imported_temperature": i2, "supports": [e_in, e_out, s2],
                                  "pressure": pressure(an2, "LC2")}
    for an, tag in ((an1, "LC1"), (an2, "LC2")):
        s = an.AnalysisSettings
        SUMMARY["analyses"][tag]["settings"] = {k: str(T(tag + " " + k, lambda kk=k: getattr(s, kk)))
                                                for k in ("LargeDeflection", "NumberOfSteps", "SolverType", "WeakSprings",
                                                          "InertiaRelief")}
    dump()
    # ---------------- solver INPUT files only ----------------
    for an, tag in ((an1, "LC1_Free_Expansion"), (an2, "LC2_Axially_Restrained")):
        p = os.path.join(INP, tag + "_ds.dat")
        T("write input %s" % tag, lambda aa=an, pp=p: aa.WriteInputFile(pp), critical=True)
        SUMMARY["analyses"][tag[:3]]["input_file"] = p
        SUMMARY["analyses"][tag[:3]]["solution_state"] = str(an.Solution.ObjectState)
        W("%s solution state %s (must not be UnderDefined)" % (tag, an.Solution.ObjectState))
    SUMMARY["messages"] = [(str(m.Severity), m.DisplayString[:300]) for m in ExtAPI.Application.Messages]
    SUMMARY["named_selections"] = [(n.Name, n.Location.Ids.Count if hasattr(n.Location, "Ids") else "?")
                                   for n in Model.NamedSelections.Children]
    dump()
    W("MECH-BUILD-7A-DONE (nothing solved)")
except Exception as e:
    import traceback
    W("FATAL %s" % e)
    W(traceback.format_exc())
    SUMMARY["FATAL"] = str(e)
    dump()
