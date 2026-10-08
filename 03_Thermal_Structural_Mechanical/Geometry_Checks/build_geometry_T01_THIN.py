# Python Script, API Version = V21
# RE-ANALYSIS 2026 - Section 9B-1 thickness-case CAD (T01_THIN, Do = 36.0 mm).
# Generated from build_geometry_param_TEMPLATE.py; the same modelling procedure as the P00 CAD
# (03_CAD_Geometry/Scripts/build_geometry_v3.py + finalize_v4.py), with ONLY the outer diameter changed.
# Writes ONLY into 10_Parametric_Study/Geometry_Checks/T01_THIN/. The P00 CAD is never opened or written.
import os, json, traceback

CASE = "T01_THIN"
DO_MM = 36.0
DI_MM, L_MM = 20.0, 600.0
OUT = os.path.join(r"<PROJECT_ROOT>\10_Parametric_Study\Geometry_Checks", CASE)
if not os.path.isdir(OUT):
    os.makedirs(OUT)
msgs = []


def L(s):
    msgs.append(str(s))


def dump(extra):
    f = open(os.path.join(OUT, "build_log.txt"), "w"); f.write("\n".join(msgs)); f.close()
    f = open(os.path.join(OUT, "cad_measurements.json"), "w"); f.write(json.dumps(extra, indent=2)); f.close()


def bbox(shape):
    try:
        b = shape.GetBoundingBox(Matrix.Identity)
        return [b.MinCorner.X, b.MinCorner.Y, b.MinCorner.Z, b.MaxCorner.X, b.MaxCorner.Y, b.MaxCorner.Z]
    except Exception:
        return None


data = {"case": CASE, "Do_mm_input": DO_MM, "Di_mm_input": DI_MM, "L_mm_input": L_MM, "status": "started"}
try:
    Di, Do, Lz = DI_MM / 1000.0, DO_MM / 1000.0, L_MM / 1000.0
    L("=== SPACECLAIM BUILD 9B-1 %s  Di %.1f / Do %.1f / L %.1f mm ===" % (CASE, DI_MM, DO_MM, L_MM))

    # ---------- 1. annulus -> SOLID (two concentric circles resolve to ONE annular face)
    ViewHelper.SetSketchPlane(Plane.PlaneXY, None)
    SketchCircle.Create(Point2D.Create(MM(0), MM(0)), MM(DO_MM / 2.0))
    SketchCircle.Create(Point2D.Create(MM(0), MM(0)), MM(DI_MM / 2.0))
    ViewHelper.SetViewMode(InteractionMode.Solid, None)
    part = GetRootPart()
    ann = [f for b in part.Bodies for f in b.Faces]
    o = ExtrudeFaceOptions(); o.ExtrudeType = ExtrudeType.ForceIndependent
    ExtrudeFaces.Execute(FaceSelection.Create(ann), MM(L_MM), o)

    # ---------- 2. inner disc -> FLUID (its own sketch + extrude)
    ViewHelper.SetSketchPlane(Plane.PlaneXY, None)
    SketchCircle.Create(Point2D.Create(MM(0), MM(0)), MM(DI_MM / 2.0))
    ViewHelper.SetViewMode(InteractionMode.Solid, None)
    part = GetRootPart()
    disc = []
    for b in part.Bodies:
        try: v = b.Shape.Volume
        except Exception: v = 0.0
        if v < 1e-12 and len(b.Faces) == 1:
            disc.append(b.Faces[0])
    o2 = ExtrudeFaceOptions(); o2.ExtrudeType = ExtrudeType.ForceIndependent
    ExtrudeFaces.Execute(FaceSelection.Create(disc), MM(L_MM), o2)
    part = GetRootPart()
    if len(part.Bodies) != 2:
        raise RuntimeError("expected 2 bodies, found %d" % len(part.Bodies))

    bl = sorted([(b.Shape.Volume, b) for b in part.Bodies])
    fluid_b, solid_b = bl[0][1], bl[1][1]
    fluid_b.SetName("FLUID_DOMAIN"); solid_b.SetName("SOLID_DOMAIN")

    # ---------- 3. share topology (conformal interface), as finalize_v4.py
    st = "unresolved"
    try:
        r = ShareTopology.FindAndFix(Selection.Create(part.Bodies), ShareTopologyOptions())
        st = "ShareTopology.FindAndFix OK: %s" % r
    except Exception as e1:
        try:
            r = ShareTopology.Fix(Selection.Create(part.Bodies), ShareTopologyOptions())
            st = "ShareTopology.Fix OK: %s" % r
        except Exception as e2:
            st = "FindAndFix:%s | Fix:%s" % (e1, e2)
    L("share topology: %s" % st)
    part = GetRootPart()
    bl = sorted([(b.Shape.Volume, b) for b in part.Bodies])
    fluid_v, fluid_b = bl[0]
    solid_v, solid_b = bl[1]
    L("FLUID %.12e m3 (%d faces) | SOLID %.12e m3 (%d faces)" % (fluid_v, len(fluid_b.Faces), solid_v, len(solid_b.Faces)))

    # ---------- 4. classify faces and create the 11 named selections of the P00 CAD
    TOL = 1e-6
    def classify(body):
        d = {}
        for f in body.Faces:
            bb = bbox(f.Shape)
            d[f] = dict(area=f.Area, zmin=bb[2], zmax=bb[5], rmax=max(abs(bb[3]), abs(bb[0])),
                        planar=abs(bb[5] - bb[2]) < TOL)
        return d
    fF, sF = classify(fluid_b), classify(solid_b)
    def pick(fd, planar, z=None, r=None):
        best, sc = None, 1e9
        for f, d in fd.items():
            if d["planar"] != planar: continue
            s = (abs(d["zmin"] - z) if z is not None else 0) + (abs(d["rmax"] - r) if r is not None else 0)
            if s < sc: best, sc = f, s
        return best
    F_IN, F_OUT, F_WALL = pick(fF, True, z=0.0), pick(fF, True, z=Lz), pick(fF, False, r=Di / 2)
    S_IN, S_OUT = pick(sF, True, z=0.0), pick(sF, True, z=Lz)
    S_INNER, S_OUTER = pick(sF, False, r=Di / 2), pick(sF, False, r=Do / 2)

    def group_names():
        try: return [g.Name for g in part.Groups]
        except Exception: return []
    def ns(name, sel_obj):
        try:
            before = set(group_names())
            res = NamedSelection.Create(sel_obj, Selection.Empty())
            newg = [g for g in part.Groups if g.Name not in before]
            if newg:
                try: newg[0].SetName(name)
                except Exception: NamedSelection.Rename(newg[0].Name, name)
                return True
            try:
                res.CreatedNamedSelection.SetName(name); return True
            except Exception: pass
            L("  NS no-new-group: %s" % name)
        except Exception as e:
            L("  NS ERROR %s : %s" % (name, e))
        return False
    made = []
    for nm, s in [("FLUID_DOMAIN", BodySelection.Create(fluid_b)), ("SOLID_DOMAIN", BodySelection.Create(solid_b)),
                  ("FLUID_INLET", FaceSelection.Create(F_IN)), ("FLUID_OUTLET", FaceSelection.Create(F_OUT)),
                  ("FLUID_WALL", FaceSelection.Create(F_WALL)),
                  ("FLUID_SOLID_INTERFACE", FaceSelection.Create([F_WALL, S_INNER])),
                  ("SOLID_INNER_INTERFACE", FaceSelection.Create(S_INNER)),
                  ("HEATED_OUTER_WALL", FaceSelection.Create(S_OUTER)),
                  ("SOLID_INLET_END", FaceSelection.Create(S_IN)), ("SOLID_OUTLET_END", FaceSelection.Create(S_OUT)),
                  ("STRUCTURAL_SUPPORT", FaceSelection.Create(S_IN))]:
        if ns(nm, s): made.append(nm)
    L("created %d named selections: %s" % (len(made), str(made)))

    # ---------- 5. save native + STEP into the case folder only
    exports = {}
    for fn in ["%s.scdocx" % CASE, "%s.stp" % CASE]:
        p = os.path.join(OUT, fn)
        try:
            DocumentSave.Execute(p)
        except Exception as e:
            L("DocumentSave FAILED %s : %s" % (fn, e))
        exports[fn] = [os.path.exists(p), os.path.getsize(p) if os.path.exists(p) else 0]
    L("exports: %s" % str(exports))

    data.update(dict(status="complete", fluid_volume_m3=fluid_v, solid_volume_m3=solid_v,
                     fluid_faces=len(fluid_b.Faces), solid_faces=len(solid_b.Faces),
                     area_fluid_inlet=F_IN.Area, area_fluid_outlet=F_OUT.Area, area_fluid_wall=F_WALL.Area,
                     area_solid_inner=S_INNER.Area, area_heated_outer=S_OUTER.Area,
                     area_solid_inlet_end=S_IN.Area, area_solid_outlet_end=S_OUT.Area,
                     bbox_fluid=bbox(fluid_b.Shape), bbox_solid=bbox(solid_b.Shape),
                     bbox_heated_outer=bbox(S_OUTER.Shape), bbox_solid_inner=bbox(S_INNER.Shape),
                     named_selections=made, final_groups=group_names(), share_topology=st,
                     exports=exports, total_bodies=len(part.Bodies)))
    L("=== BUILD COMPLETE ===")
except Exception as e:
    data["status"] = "FAILED"
    L("FATAL: %s" % e); L(traceback.format_exc())
dump(data)
