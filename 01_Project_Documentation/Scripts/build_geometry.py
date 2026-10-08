# Python Script, API Version = V21
# ---------------------------------------------------------------------------
# RE-ANALYSIS (2026) - heated thick-walled duct, Section 3 CAD build.
# Frozen Section 2 baseline: Di=20 mm, Do=40 mm, L=600 mm.
# Builds TWO coincident bodies: annular SOLID_DOMAIN + internal FLUID_DOMAIN.
# ---------------------------------------------------------------------------
import os, json

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
    except Exception as e:
        return None

data = {}
try:
    Di, Do, Lz = 0.020, 0.040, 0.600
    L("=== SPACECLAIM BUILD: heated thick-walled duct ===")
    L("target Di=%.3f m  Do=%.3f m  L=%.3f m" % (Di, Do, Lz))

    # ---- 1. sketch two concentric circles on XY ----------------------------
    ViewHelper.SetSketchPlane(Plane.PlaneXY, None)
    SketchCircle.Create(Point2D.Create(MM(0), MM(0)), MM(20))
    SketchCircle.Create(Point2D.Create(MM(0), MM(0)), MM(10))
    ViewHelper.SetViewMode(InteractionMode.Solid, None)
    part = GetRootPart()
    L("after sketch: bodies=%d" % len(part.Bodies))
    for i, b in enumerate(part.Bodies):
        L("  body %d faces=%d area=%.8e" % (i, len(b.Faces), sum([f.Area for f in b.Faces])))

    # ---- 2a. extrude the ANNULAR face -> SOLID_DOMAIN -----------------------
    faces = []
    for b in part.Bodies:
        for f in b.Faces:
            faces.append(f)
    L("annular faces to extrude: %d" % len(faces))
    opts = ExtrudeFaceOptions()
    opts.ExtrudeType = ExtrudeType.ForceIndependent
    ExtrudeFaces.Execute(FaceSelection.Create(faces), MM(600), opts)
    part = GetRootPart()
    L("after annulus extrude: bodies=%d" % len(part.Bodies))

    # ---- 2b. second sketch: inner disc -> FLUID_DOMAIN ----------------------
    def surface_faces(p):
        out = []
        for b in p.Bodies:
            try:
                v = b.Shape.Volume
            except Exception:
                v = 0.0
            if v < 1e-12 and len(b.Faces) == 1:
                out.append(b.Faces[0])
        return out

    ViewHelper.SetSketchPlane(Plane.PlaneXY, None)
    SketchCircle.Create(Point2D.Create(MM(0), MM(0)), MM(10))
    ViewHelper.SetViewMode(InteractionMode.Solid, None)
    part = GetRootPart()
    disc = surface_faces(part)
    L("inner-disc surface faces found: %d (bodies now %d)" % (len(disc), len(part.Bodies)))

    if len(disc) > 0:
        opts2 = ExtrudeFaceOptions()
        opts2.ExtrudeType = ExtrudeType.ForceIndependent
        ExtrudeFaces.Execute(FaceSelection.Create(disc), MM(600), opts2)
        part = GetRootPart()
        L("after fluid extrude (sketch route): bodies=%d" % len(part.Bodies))

    if len(part.Bodies) < 2:
        L("sketch route did not yield a second body - trying low-level Body API")
        try:
            frame = Frame.Create(Point.Create(0, 0, 0), Direction.DirX, Direction.DirY)
            circ = CurveSegment.CreateCircle(frame, 0.010)
            fb = Body.ExtrudeProfile([circ], 0.600)
            DesignBody.Create(part, "FLUID_DOMAIN", fb)
            part = GetRootPart()
            L("low-level route: bodies=%d" % len(part.Bodies))
        except Exception as e:
            L("low-level route failed: %s" % e)

    bodies = []
    for i, b in enumerate(part.Bodies):
        v = b.Shape.Volume
        bodies.append((v, b, i))
        L("  body %d faces=%d volume=%.10e m3" % (i, len(b.Faces), v))
    if len(bodies) != 2:
        raise Exception("expected 2 bodies after extrude, got %d" % len(bodies))

    bodies.sort()
    fluid_v, fluid_b, _ = bodies[0]      # smaller volume = internal passage
    solid_v, solid_b, _ = bodies[1]      # larger  volume = annular wall
    fluid_b.SetName("FLUID_DOMAIN")
    solid_b.SetName("SOLID_DOMAIN")
    L("FLUID_DOMAIN volume = %.10e m3 (%d faces)" % (fluid_v, len(fluid_b.Faces)))
    L("SOLID_DOMAIN volume = %.10e m3 (%d faces)" % (solid_v, len(solid_b.Faces)))

    # ---- 3. identify faces by area + bounding box --------------------------
    TOL = 1e-6
    def classify(body, label):
        out = {}
        for f in body.Faces:
            bb = bbox(f.Shape)
            a = f.Area
            zmin, zmax = (bb[2], bb[5]) if bb else (None, None)
            rmax = max(abs(bb[3]), abs(bb[0])) if bb else None
            planar = (bb is not None) and (abs(zmax - zmin) < TOL)
            out[f] = dict(area=a, zmin=zmin, zmax=zmax, rmax=rmax, planar=planar)
            L("  %s face: area=%.8e planar=%s zmin=%.6f zmax=%.6f rmax=%.6f"
              % (label, a, planar, zmin, zmax, rmax))
        return out

    L("-- FLUID faces --"); fF = classify(fluid_b, "fluid")
    L("-- SOLID faces --"); sF = classify(solid_b, "solid")

    def pick(fd, want_planar, z=None, r=None):
        best, bestscore = None, 1e9
        for f, d in fd.items():
            if d["planar"] != want_planar:
                continue
            score = 0.0
            if z is not None:
                score += abs(d["zmin"] - z)
            if r is not None:
                score += abs(d["rmax"] - r)
            if score < bestscore:
                best, bestscore = f, score
        return best

    FLUID_INLET  = pick(fF, True,  z=0.0)
    FLUID_OUTLET = pick(fF, True,  z=Lz)
    FLUID_WALL   = pick(fF, False, r=Di/2)
    SOLID_IN_END = pick(sF, True,  z=0.0)
    SOLID_OUT_END= pick(sF, True,  z=Lz)
    SOLID_INNER  = pick(sF, False, r=Di/2)
    SOLID_OUTER  = pick(sF, False, r=Do/2)

    # ---- 4. named selections ----------------------------------------------
    def ns(name, sel_obj):
        try:
            before = set([g.Name for g in part.GetGroups()])
            NamedSelection.Create(sel_obj, Selection.Empty())
            after = [g for g in part.GetGroups() if g.Name not in before]
            if after:
                try:
                    NamedSelection.Rename(after[0].Name, name)
                except Exception:
                    after[0].SetName(name)
                L("  NS created: %s" % name)
                return True
            L("  NS FAILED (no new group): %s" % name)
        except Exception as e:
            L("  NS ERROR %s : %s" % (name, e))
        return False

    L("-- named selections --")
    made = []
    for nm, s in [("FLUID_DOMAIN",          BodySelection.Create(fluid_b)),
                  ("SOLID_DOMAIN",          BodySelection.Create(solid_b)),
                  ("FLUID_INLET",           FaceSelection.Create(FLUID_INLET)),
                  ("FLUID_OUTLET",          FaceSelection.Create(FLUID_OUTLET)),
                  ("FLUID_WALL",            FaceSelection.Create(FLUID_WALL)),
                  ("FLUID_SOLID_INTERFACE", FaceSelection.Create([FLUID_WALL, SOLID_INNER])),
                  ("SOLID_INNER_INTERFACE", FaceSelection.Create(SOLID_INNER)),
                  ("HEATED_OUTER_WALL",     FaceSelection.Create(SOLID_OUTER)),
                  ("SOLID_INLET_END",       FaceSelection.Create(SOLID_IN_END)),
                  ("SOLID_OUTLET_END",      FaceSelection.Create(SOLID_OUT_END)),
                  ("STRUCTURAL_SUPPORT",    FaceSelection.Create(SOLID_IN_END))]:
        if ns(nm, s):
            made.append(nm)

    # ---- 5. share topology -------------------------------------------------
    st = "not set"
    for attempt in range(3):
        try:
            if attempt == 0:
                ComponentHelper.SetShareTopology(Selection.Create(part), ShareTopologyOptions.Share, None)
            elif attempt == 1:
                part.SetShareTopology(ShareTopologyOptions.Share)
            else:
                part.ShareTopology = ShareTopologyOptions.Share
            st = "Share (method %d)" % attempt
            break
        except Exception as e:
            st = "FAILED: %s" % e
    L("share topology: %s" % st)

    # ---- 6. measurements ---------------------------------------------------
    data = dict(
        fluid_volume_m3=fluid_v, solid_volume_m3=solid_v,
        fluid_faces=len(fluid_b.Faces), solid_faces=len(solid_b.Faces),
        area_fluid_inlet=FLUID_INLET.Area, area_fluid_outlet=FLUID_OUTLET.Area,
        area_fluid_wall=FLUID_WALL.Area, area_solid_inner=SOLID_INNER.Area,
        area_heated_outer=SOLID_OUTER.Area, area_solid_inlet_end=SOLID_IN_END.Area,
        area_solid_outlet_end=SOLID_OUT_END.Area,
        bbox_fluid=bbox(fluid_b.Shape), bbox_solid=bbox(solid_b.Shape),
        named_selections=made, share_topology=st,
        total_bodies=len(part.Bodies))

    # ---- 7. exports --------------------------------------------------------
    exports = {}
    for sub, fn in [("Native_CAD", "heated_duct.scdoc"), ("STEP", "heated_duct.step"),
                    ("Parasolid", "heated_duct.x_t")]:
        p = os.path.join(BASE, sub, fn)
        try:
            DocumentSave.Execute(p)
            exports[fn] = os.path.exists(p)
            L("exported %s -> %s" % (fn, exports[fn]))
        except Exception as e:
            exports[fn] = False
            L("EXPORT FAILED %s : %s" % (fn, e))
    data["exports"] = exports
    L("=== BUILD COMPLETE ===")
except Exception as e:
    L("FATAL: %s" % e)
    import traceback
    L(traceback.format_exc())
dump(data)

