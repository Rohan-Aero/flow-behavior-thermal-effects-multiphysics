# -*- coding: utf-8 -*-
# SECTION 9B-2 - Mechanical side of the API probe (throw-away copy; nothing solved). RE-ANALYSIS 2026.
import os, json, math
PD = r"<PROJECT_ROOT>\10_Parametric_Study\Structural_Cases\Probe"
OUT = os.path.join(PD, "mech_probe_9B2.json")
R = {}


def save():
    f = open(OUT, "w")
    f.write(json.dumps(R, indent=1, default=str))
    f.close()


def walk(o):
    out = []
    for c in o.Children:
        out.append(c)
        out.extend(walk(c))
    return out


try:
    ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS
    bodies = Model.Geometry.GetChildren(DataModelObjectCategory.Body, True)
    R["bodies"] = [(b.Name, str(b.Suppressed), str(b.Material), str(b.Volume)) for b in bodies]
    R["named_selections"] = []
    for n in Model.NamedSelections.Children:
        try:
            ids = list(n.Location.Ids)
            R["named_selections"].append((n.Name, str(n.ObjectState), len(ids), str(n.Location.SelectionType)))
        except Exception as e:
            R["named_selections"].append((n.Name, str(n.ObjectState), "err %s" % e))
    R["mesh_controls"] = [(c.Name, c.GetType().Name, str(c.ObjectState)) for c in Model.Mesh.Children]
    R["objects_not_ok"] = [(o.Name, o.GetType().Name, str(o.ObjectState)) for a in Model.Analyses for o in walk(a)
                           if any(k in str(o.ObjectState) for k in ("UnderDefined", "Error", "Suppressed"))]
    R["analyses"] = [(a.Name, str(a.AnalysisType), str(a.Solution.ObjectState)) for a in Model.Analyses]
    solid = [b for b in bodies if b.Name == "SOLID_DOMAIN"]
    if solid:
        gb = solid[0].GetGeoBody()
        R["solid_edges"] = [(e.Id, str(e.CurveType), e.Length) for e in gb.Edges]
        R["solid_faces"] = [(f.Id, str(f.SurfaceType), f.Area) for f in gb.Faces]
    save()
    mesh = Model.Mesh
    fm = [c for c in mesh.Children if c.GetType().Name == "FaceMeshing"][0]
    sz = [c for c in mesh.Children if "Sizing" in c.GetType().Name][0]
    R["sizing_location_count"] = str(sz.Location.Ids.Count) if hasattr(sz.Location, "Ids") else "?"
    fm.InternalNumberOfDivisions = 4
    mesh.ClearGeneratedData()
    mesh.GenerateMesh()
    R["mesh_nodes_elements"] = (int(mesh.Nodes), int(mesh.Elements))
    md = ExtAPI.DataModel.MeshDataByName(ExtAPI.DataModel.MeshDataNames[0])
    rs = [math.hypot(n.X, n.Y) for n in md.Nodes]
    zs = [n.Z for n in md.Nodes]
    R["mesh_extent"] = (min(rs), max(rs), min(zs), max(zs))
    R["objects_not_ok_after_mesh"] = [(o.Name, o.GetType().Name, str(o.ObjectState)) for a in Model.Analyses for o in walk(a)
                                      if any(k in str(o.ObjectState) for k in ("UnderDefined", "Error"))]
    R["messages"] = [(str(m.Severity), m.DisplayString[:300]) for m in ExtAPI.Application.Messages][-30:]
    R["DONE"] = True
    save()
except Exception as e:
    import traceback
    R["FATAL"] = str(e)
    R["tb"] = traceback.format_exc()
    save()
