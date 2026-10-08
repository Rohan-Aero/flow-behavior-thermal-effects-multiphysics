# Python Script, API Version = V21
# RE-ANALYSIS (2026) - Section 3 CAD build, v3 (groups + share topology + exports)
import os, json, traceback

BASE = r"<PROJECT_ROOT>\03_CAD_Geometry"
GC   = os.path.join(BASE, "Geometry_Check")
msgs = []
def L(s):
    msgs.append(str(s))
def dump(extra=None):
    f = open(os.path.join(GC, "build_log.txt"), "w"); f.write("\n".join(msgs)); f.close()
    if extra is not None:
        f = open(os.path.join(GC, "cad_measurements.json"), "w"); f.write(json.dumps(extra, indent=2)); f.close()
def bbox(shape):
    try:
        b = shape.GetBoundingBox(Matrix.Identity)
        return [b.MinCorner.X, b.MinCorner.Y, b.MinCorner.Z, b.MaxCorner.X, b.MaxCorner.Y, b.MaxCorner.Z]
    except Exception:
        return None

data = {}
try:
    Di, Do, Lz = 0.020, 0.040, 0.600
    L("=== SPACECLAIM BUILD v3 ===")

    # ---------- 1. annulus -> SOLID ----------
    ViewHelper.SetSketchPlane(Plane.PlaneXY, None)
    SketchCircle.Create(Point2D.Create(MM(0), MM(0)), MM(20))
    SketchCircle.Create(Point2D.Create(MM(0), MM(0)), MM(10))
    ViewHelper.SetViewMode(InteractionMode.Solid, None)
    part = GetRootPart()
    ann = [f for b in part.Bodies for f in b.Faces]
    o = ExtrudeFaceOptions(); o.ExtrudeType = ExtrudeType.ForceIndependent
    ExtrudeFaces.Execute(FaceSelection.Create(ann), MM(600), o)

    # ---------- 2. inner disc -> FLUID ----------
    ViewHelper.SetSketchPlane(Plane.PlaneXY, None)
    SketchCircle.Create(Point2D.Create(MM(0), MM(0)), MM(10))
    ViewHelper.SetViewMode(InteractionMode.Solid, None)
    part = GetRootPart()
    disc = []
    for b in part.Bodies:
        try: v = b.Shape.Volume
        except Exception: v = 0.0
        if v < 1e-12 and len(b.Faces) == 1:
            disc.append(b.Faces[0])
    o2 = ExtrudeFaceOptions(); o2.ExtrudeType = ExtrudeType.ForceIndependent
    ExtrudeFaces.Execute(FaceSelection.Create(disc), MM(600), o2)
    part = GetRootPart()

    bl = sorted([(b.Shape.Volume, b) for b in part.Bodies])
    fluid_v, fluid_b = bl[0]
    solid_v, solid_b = bl[1]
    fluid_b.SetName("FLUID_DOMAIN"); solid_b.SetName("SOLID_DOMAIN")
    L("FLUID %.10e m3 (%d faces) | SOLID %.10e m3 (%d faces)"
      % (fluid_v, len(fluid_b.Faces), solid_v, len(solid_b.Faces)))

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
    F_IN  = pick(fF, True,  z=0.0)
    F_OUT = pick(fF, True,  z=Lz)
    F_WALL= pick(fF, False, r=Di/2)
    S_IN  = pick(sF, True,  z=0.0)
    S_OUT = pick(sF, True,  z=Lz)
    S_INNER = pick(sF, False, r=Di/2)
    S_OUTER = pick(sF, False, r=Do/2)

    # ---------- 3. PROBE the group + share-topology APIs ----------
    L("-- API PROBE --")
    L("part attrs with 'roup': %s" % str([a for a in dir(part) if "roup" in a.lower()]))
    try:
        L("ShareTopologyOptions members: %s" % str([a for a in dir(ShareTopologyOptions) if not a.startswith("_")]))
    except Exception as e:
        L("ShareTopologyOptions missing: %s" % e)
    try:
        probe_res = NamedSelection.Create(FaceSelection.Create(F_IN), Selection.Empty())
        L("NamedSelection.Create result attrs: %s" % str([a for a in dir(probe_res) if not a.startswith("_")]))
        try:
            L("  result.CreatedNamedSelection = %s" % str(probe_res.CreatedNamedSelection))
        except Exception as e:
            L("  no CreatedNamedSelection: %s" % e)
        try:
            L("  part.Groups -> %s" % str([g.Name for g in part.Groups]))
        except Exception as e:
            L("  part.Groups failed: %s" % e)
    except Exception as e:
        L("probe NS failed: %s" % e)

    # ---------- 4. named selections ----------
    def group_names():
        try:    return [g.Name for g in part.Groups]
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

    for g in list(group_names()):
        try: NamedSelection.Delete(g)
        except Exception: pass

    L("-- named selections --")
    made = []
    for nm, s in [("FLUID_DOMAIN",          BodySelection.Create(fluid_b)),
                  ("SOLID_DOMAIN",          BodySelection.Create(solid_b)),
                  ("FLUID_INLET",           FaceSelection.Create(F_IN)),
                  ("FLUID_OUTLET",          FaceSelection.Create(F_OUT)),
                  ("FLUID_WALL",            FaceSelection.Create(F_WALL)),
                  ("FLUID_SOLID_INTERFACE", FaceSelection.Create([F_WALL, S_INNER])),
                  ("SOLID_INNER_INTERFACE", FaceSelection.Create(S_INNER)),
                  ("HEATED_OUTER_WALL",     FaceSelection.Create(S_OUTER)),
                  ("SOLID_INLET_END",       FaceSelection.Create(S_IN)),
                  ("SOLID_OUTLET_END",      FaceSelection.Create(S_OUT)),
                  ("STRUCTURAL_SUPPORT",    FaceSelection.Create(S_IN))]:
        if ns(nm, s): made.append(nm)
    L("created %d named selections: %s" % (len(made), str(made)))
    L("final group list: %s" % str(group_names()))

    # ---------- 5. share topology ----------
    st = "not set"
    try:
        opts = [a for a in dir(ShareTopologyOptions) if not a.startswith("_")]
        pref = None
        for want in ["Share", "Merge", "Auto", "On", "ShareTopology"]:
            if want in opts: pref = getattr(ShareTopologyOptions, want); st_name = want; break
        if pref is not None:
            for m in range(3):
                try:
                    if m == 0: ComponentHelper.SetShareTopology(Selection.Create(part), pref, None)
                    elif m == 1: part.SetShareTopology(pref)
                    else: part.ShareTopology = pref
                    st = "%s via method %d" % (st_name, m); break
                except Exception as e:
                    st = "FAILED(%s): %s" % (st_name, e)
        else:
            st = "no suitable enum member in %s" % str(opts)
    except Exception as e:
        st = "FAILED: %s" % e
    L("share topology: %s" % st)

    # ---------- 6. exports (all at the end, then verified) ----------
    exports = {}
    targets = [("Native_CAD", "heated_duct.scdoc"), ("STEP", "heated_duct.step"),
               ("Parasolid", "heated_duct.x_t"), ("Parasolid", "heated_duct.xmt_txt")]
    for sub, fn in targets:
        p = os.path.join(BASE, sub, fn)
        try:
            DocumentSave.Execute(p)
            L("DocumentSave.Execute ok for %s" % fn)
        except Exception as e:
            L("DocumentSave FAILED %s : %s" % (fn, e))
    for sub, fn in targets:
        p = os.path.join(BASE, sub, fn)
        exports[fn] = (os.path.exists(p), os.path.getsize(p) if os.path.exists(p) else 0)
    for sub in ["Native_CAD", "STEP", "Parasolid"]:
        L("dir %s -> %s" % (sub, str(os.listdir(os.path.join(BASE, sub)))))

    data = dict(fluid_volume_m3=fluid_v, solid_volume_m3=solid_v,
                fluid_faces=len(fluid_b.Faces), solid_faces=len(solid_b.Faces),
                area_fluid_inlet=F_IN.Area, area_fluid_outlet=F_OUT.Area,
                area_fluid_wall=F_WALL.Area, area_solid_inner=S_INNER.Area,
                area_heated_outer=S_OUTER.Area, area_solid_inlet_end=S_IN.Area,
                area_solid_outlet_end=S_OUT.Area,
                bbox_fluid=bbox(fluid_b.Shape), bbox_solid=bbox(solid_b.Shape),
                named_selections=made, final_groups=group_names(),
                share_topology=st, exports=exports, total_bodies=len(part.Bodies))
    L("=== BUILD COMPLETE ===")
except Exception as e:
    L("FATAL: %s" % e); L(traceback.format_exc())
dump(data)
