# -*- coding: utf-8 -*-
# =====================================================================================================
# SECTION 9B-2 - PARAMETRIC MECHANICAL ANALYSIS, one design case per call (runs inside Mechanical, sent by
# wb_param_9B2_<run>.wbjn). RE-ANALYSIS 2026 - newly generated models and results, not recovered originals.
#
# Works on a SAVE-AS copy of the solved 7B project (the 7B project and the official baseline results stay untouched).
# Methodology frozen from 7A / 7B / 8A / 8B:
#   material tables, T_ref 300 K, LC1 and LC2 support definitions (the node-based support sets are re-located on the
#   case mesh at the SAME positions: outer radius, z = 0 (LC1) / z = L/2 (LC2), 0/120/240 deg), the Imported Body
#   Temperature settings (Manual / Bucket Volume / Shape Functions / Nearest Node outside), the solver (sparse direct,
#   small deflection), the linear-buckling set-up of 8A (LC2 pre-stress, 6 modes, positive multipliers only).
# What changes per case:
#   - the temperature SOURCE: the External Data system points at the case's OWN Fluent solid mesh (CDB) + node
#     temperatures (9B-1 CFD result of that case); set and read back by the Workbench driver
#   - for T01 / T03 only: the geometry (9B-1 SpaceClaim model) and the through-wall division count (4 / 6, same
#     2.0 mm radial element size as mesh B); 36 circumferential x 130 axial, bias 4 are unchanged
#   - V / Q / C00: the 7B mesh B is kept as it is (checked node-for-node against the 7B solver input)
# Steps: 1 geometry / mesh -> 2 support nodes -> 3 temperature import -> 4 object states + solver input decks
#        (PRE-SOLVE GATE) -> 5 buckling set-up -> 6 solve LC1, LC2, buckling; read maxima; copy APDL tables; images.
# LC2P (thermal + pressure) is NOT solved here (Part N: the 7B pressure result is used); its copied 7B results are
# cleared so that the case project cannot be mistaken for a case pressure result.
# Helper functions (logging, ds.dat parsing) are copied unchanged from mech_meshstudy_8B.py (Section 8B).
# =====================================================================================================
import os, json, math, shutil, time, re
import System

BASE = r"<PROJECT_ROOT>"
S8 = os.path.join(BASE, "08_Structural_Analysis")
SC = os.path.join(BASE, "10_Parametric_Study", "Structural_Cases")
try:
    CFG = json.load(open(os.path.join(SC, "Audits", "current_case.json"), "r"))
except Exception as _e:    # nothing else can be logged before the case folder is known (C00 run 1)
    _f = open(os.path.join(SC, "Audits", "mech_bootstrap_error.txt"), "w")
    _f.write("current_case.json could not be read: %s" % _e)
    _f.close()
    raise
TAG = CFG["tag"]
NC, NR, NA, BIAS = int(CFG["nc"]), int(CFG["nr"]), int(CFG["na"]), float(CFG["bias"])
DO, DI, LL = float(CFG["Do"]), float(CFG["Di"]), float(CFG["L"])
RO, RI = DO / 2.0, DI / 2.0
GEO_CHANGED = bool(CFG["geometry"])
DO_B = bool(CFG["buckling"])
SRC_LO, SRC_HI = [float(x) for x in CFG["source_T_range_K"]]
SRC_NODE_LO, SRC_NODE_HI = [float(x) for x in CFG["source_node_T_K"]]
CD = os.path.join(SC, TAG)
AUD = os.path.join(CD, "Audits")
PRE_IN = os.path.join(AUD, "Presolve_Inputs")
SOLV = os.path.join(CD, "Solver_Output")
FIG = os.path.join(CD, "Figures")
SNIP_B = os.path.join(S8, "Buckling", "Workbench", "Scripts", "s8a_buckle_snippet.inp")
REF7B_LC2 = os.path.join(S8, "LC2_Restrained", "Solver_Output", "LC2_solve_input_ds.dat")
MESH_B_SUPPORT_IDS = {"LC1": [18870, 18882, 18894], "LC2": [25862, 25874, 25886]}     # 7B / 8B variant B
for d in [AUD, PRE_IN, SOLV, FIG] + [os.path.join(SOLV, k) for k in ("LC1", "LC2", "BUCKLING")]:
    if not os.path.isdir(d):
        os.makedirs(d)
LOG = os.path.join(AUD, "mech_%s_log.txt" % TAG)
PREF = os.path.join(AUD, "presolve_audit_%s.json" % TAG)
SUMF = os.path.join(AUD, "summary_%s.json" % TAG)
lines = []
PRE = {"gate": "NOT RUN", "checks": [], "case": CFG, "note": "RE-ANALYSIS 2026 - Section 9B-2 pre-solve audit"}
S = {"case": CFG, "cases": {}, "note": "RE-ANALYSIS 2026 - Section 9B-2 parametric structural solution (not recovered)"}


def W(s):
    lines.append(time.strftime("%H:%M:%S ") + str(s))
    f = open(LOG, "w")
    f.write("\n".join(lines))
    f.close()


def T(label, fn, critical=False):
    try:
        r = fn()
        W("OK   %s %s" % (label, "" if r is None else str(r)[:300]))
        return r
    except Exception as e:
        W("FAIL %s: %s" % (label, str(e)[:400]))
        if critical:
            raise
        return None


def dump():
    for path, obj in ((PREF, PRE), (SUMF, S)):
        f = open(path, "w")
        f.write(json.dumps(obj, indent=1, default=str))
        f.close()


def chk(name, ok, expected, found):
    PRE["checks"].append({"check": name, "pass": bool(ok), "expected": str(expected), "found": str(found)[:600]})
    W("%s  %s | expected %s | found %s" % ("PASS" if ok else "**FAIL**", name, expected, str(found)[:300]))
    return ok


def qval(q):
    try:
        return float(q.Value)
    except Exception:
        return None


def qK(q):
    """temperature Quantity -> K"""
    v, u = float(q.Value), str(q.Unit)
    if "K" in u and "C" not in u:
        return v
    if "F" in u:
        return (v - 32.0) / 1.8 + 273.15
    return v + 273.15


def walk(o):
    out = []
    for c in o.Children:
        out.append(c)
        out.extend(walk(c))
    return out


# ------------------------------------------------------------------------------------------------ ds.dat parsing
# (copied unchanged from mech_meshstudy_8B.py)
def read_lines(p):
    f = open(p, "r")
    t = f.read()
    f.close()
    return t.splitlines()


def cmblocks(L):
    cm = {}
    i = 0
    n = len(L)
    while i < n:
        l = L[i]
        if l.upper().startswith("CMBLOCK,"):
            p = [x.strip() for x in l.split(",")]
            name, typ, cnt = p[1].lower(), p[2].upper(), int(p[3].split("!")[0])
            ids = []
            ntok = 0
            j = i + 2
            while ntok < cnt and j < n:
                for tok in L[j].split():
                    v = int(tok)
                    ntok += 1
                    if v < 0 and ids:
                        ids.extend(range(ids[-1] + 1, -v + 1))
                    else:
                        ids.append(v)
                j += 1
            cm[name] = (typ, ids)
            i = j
            continue
        i += 1
    return cm


def scan_ds(p):
    """Extract what the solver will actually receive."""
    L = read_lines(p)
    r = {"file": p, "lines": len(L)}
    low = [l.strip().lower() for l in L]
    sec = {"nblock": [], "eblock": [], "bf": [], "material": [], "constraints": [], "pressure": [], "misc": []}
    i = 0
    n = len(L)
    bfv = []
    p443 = []
    eblocks = []
    while i < n:
        l = low[i]
        if not (l.startswith("/com") or l.startswith("!")):
            for tok in re.split(r"[,\s=()']+", l.split("!")[0]):
                try:
                    if abs(float(tok) - 443.41) < 1e-6:
                        p443.append(L[i].strip())
                        break
                except Exception:
                    pass
        if l.startswith("nblock,"):
            r["nblock_header"] = L[i]
            j = i + 2
            while j < n and low[j] != "-1":
                sec["nblock"].append(L[j])
                j += 1
            i = j
            continue
        if l.startswith("eblock,"):
            blk = {"header": L[i], "lines": []}
            j = i + 2
            while j < n and low[j] != "-1":
                blk["lines"].append(L[j])
                j += 1
            eblocks.append(blk)
            i = j
            continue
        if l.startswith("bfblock,"):
            r["bfblock_header"] = L[i]
            j = i + 2
            while j < n and not low[j].startswith("bf,end"):
                sec["bf"].append(L[j])
                try:
                    bfv.append(float(L[j].split()[1]))
                except Exception:
                    pass
                j += 1
            i = j
            continue
        if l.startswith("mp,") or l.startswith("mpdata,") or l.startswith("mptemp,") or l.startswith("mpamod,") \
                or l.startswith("tref,") or l.startswith("tb,") or l.startswith("tbdata,"):
            if not l.startswith("mp,uvid"):
                sec["material"].append(L[i].split("!")[0].strip())
        if l.startswith("d,") or l.startswith("nrot,") or l.startswith("cmsel,") or l.startswith("csys,") \
                or l.startswith("local,") or l.startswith("nsel,") or l.startswith("dk,") or l.startswith("da,") \
                or l.startswith("cp,") or l.startswith("ce,") or "wspr" in l:
            sec["constraints"].append(L[i].split("!")[0].strip())
        if "pres" in l and not l.startswith("/com") and not l.startswith("!"):
            sec["pressure"].append(L[i].strip())
        if l.startswith("et,") or l.startswith("keyo,") or l.startswith("eqsl,") or l.startswith("antype") \
                or l.startswith("nlgeom") or l.startswith("nsub") or l.startswith("outres") or "wspr" in l \
                or l.startswith("sfe,") or l.startswith("sf,") or l.startswith("esurf"):
            sec["misc"].append(L[i].split("!")[0].strip())
        i += 1
    sec["eblock"] = eblocks[0]["lines"] if eblocks else []
    r["eblock_header"] = eblocks[0]["header"] if eblocks else None
    r["extra_eblocks"] = [{"header": b["header"], "count": len(b["lines"])} for b in eblocks[1:]]
    r["_extra_eblock_lines"] = [b["lines"] for b in eblocks[1:]]
    r["n_nodes"] = len(sec["nblock"])
    r["n_elem_lines"] = len(sec["eblock"])
    r["n_bf"] = len(bfv)
    if bfv:
        r["bf_min_C"], r["bf_max_C"] = min(bfv), max(bfv)
        r["bf_min_K"], r["bf_max_K"] = min(bfv) + 273.15, max(bfv) + 273.15
    r["material"] = sec["material"]
    r["constraints_raw"] = sec["constraints"]
    r["pressure_lines"] = sec["pressure"][:40]
    r["misc"] = sorted(set(sec["misc"]))
    r["has_443.41"] = len(p443) > 0
    r["lines_with_443.41"] = p443[:20]
    r["wsprings"] = any("wspr" in x for x in low)
    cm = cmblocks(L)
    cur = None
    csys = 0
    res = []
    for l in low:
        if l.startswith("cmsel,s,"):
            cur = l.split(",")[2].strip()
        elif l.startswith("nsel,all") or l.startswith("allsel"):
            cur = None
        elif l.startswith("csys,"):
            try:
                csys = int(float(l.split(",")[1].split("!")[0]))
            except Exception:
                pass
        elif l.startswith("d,"):
            p = [x.strip() for x in l.split("!")[0].split(",")]
            tgt = p[1]
            key = cur if tgt == "all" else tgt
            ids = cm.get(key, ("?", []))[1] if key else []
            res.append(("D", p[2], float(p[3] or 0.0), len(ids), sum(ids), min(ids) if ids else -1, max(ids) if ids else -1))
        elif l.startswith("nrot,"):
            key = l.split(",")[1].strip()
            ids = cm.get(key, ("?", []))[1]
            res.append(("NROT_csys%d" % csys, "", 0.0, len(ids), sum(ids), min(ids) if ids else -1, max(ids) if ids else -1))
    r["constraint_set"] = sorted(res)
    r["_sections"] = sec
    return r


def same(a, b, key):
    return "\n".join(a["_sections"][key]) == "\n".join(b["_sections"][key])


def bfmap(lines_):
    """BFBLOCK body lines (node id in columns 1-9, temperature in 10-29, degC) -> {node: T}"""
    out = {}
    for l in lines_:
        if l.strip():
            out[int(l[0:9])] = float(l[9:29])
    return out


def expected_nodes(nc, nr, na):
    return nc * ((nr + 1) * (na + 1) * 2 + nr * (na + 1) + (nr + 1) * na)


def ptype(a):
    return str(a.AnalysisType)


try:
    W("=== SECTION 9B-2 PARAMETRIC CASE %s: Do %.0f mm, %d circ x %d wall x %d axial, bias %.1f, geometry %s (RE-ANALYSIS 2026) ==="
      % (TAG, DO * 1e3, NC, NR, NA, BIAS, "REPLACED" if GEO_CHANGED else "baseline"))
    ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS
    NS = dict((n.Name, n) for n in Model.NamedSelections.Children)
    cs = [c for c in Model.CoordinateSystems.Children if c.Name == "CS_DUCT_CYL"][0]
    ALL = list(Model.Analyses)
    AN = dict((a.Name, a) for a in ALL)
    an1, an2 = AN["LC1_Free_Expansion"], AN["LC2_Axially_Restrained"]
    an3 = AN.get("LC2P_Restrained_Thermal_Plus_Pressure")
    bks = [a for a in ALL if "Buckl" in ptype(a)]
    bk = bks[0] if bks else None
    if bk is not None:
        bk.Name = "LC2_Linear_Buckling_%s" % TAG
    S["analyses"] = [(a.Name, ptype(a)) for a in Model.Analyses]
    W("analyses %s" % S["analyses"])
    chk("buckling analysis present as requested", (bk is not None) == DO_B, DO_B, bk is not None)
    if an3 is not None:
        T("LC2P: clear the copied 7B results (LC2P is not part of 9B-2, Part N)", lambda: an3.Solution.ClearGeneratedData())
        S["LC2P"] = {"solved_in_9B2": False, "state_after_clear": str(an3.Solution.ObjectState),
                     "note": "copied from the 7B project; results cleared; not solved for the parametric cases (Part N)"}

    # ------------------------------------------------------------------ 1. geometry / bodies / mesh
    bodies = Model.Geometry.GetChildren(DataModelObjectCategory.Body, True)
    solid = [b for b in bodies if b.Name == "SOLID_DOMAIN"][0]
    fluid = [b for b in bodies if b.Name == "FLUID_DOMAIN"][0]
    if GEO_CHANGED:
        # a replaced geometry file re-creates the bodies: fluid un-suppressed, no material (API probe, 9B-2)
        T("suppress FLUID_DOMAIN (as 7A)", lambda: setattr(fluid, "Suppressed", True), critical=True)
        T("assign Inconel_718_Re_analysis to SOLID_DOMAIN (as 7A)",
          lambda: setattr(solid, "Material", "Inconel_718_Re_analysis"), critical=True)
    vol = qval(solid.Volume)
    vexp = math.pi / 4.0 * (DO ** 2 - DI ** 2) * LL
    S["bodies"] = {"solid_material": str(solid.Material), "fluid_suppressed": bool(fluid.Suppressed), "solid_volume_m3": vol,
                   "expected_volume_m3": vexp}
    chk("bodies: FLUID_DOMAIN suppressed, SOLID_DOMAIN = Inconel_718_Re_analysis",
        bool(fluid.Suppressed) and str(solid.Material) == "Inconel_718_Re_analysis", "suppressed / Inconel_718_Re_analysis",
        "%s / %s" % (fluid.Suppressed, solid.Material))
    chk("geometry: solid volume = pi/4 (Do^2 - Di^2) L for Do %.0f mm" % (DO * 1e3), vol is not None and abs(vol - vexp) < 1e-6 * vexp,
        "%.9e m3" % vexp, vol)
    mesh = Model.Mesh
    ctrls = list(mesh.Children)
    S["mesh_controls_before"] = [(c.Name, c.GetType().Name, str(c.ObjectState)) for c in ctrls]
    sw = [c for c in ctrls if c.GetType().Name == "AutomaticMethod"][0]
    fm = [c for c in ctrls if c.GetType().Name == "FaceMeshing"][0]
    sz = [c for c in ctrls if "Sizing" in c.GetType().Name][0]
    if GEO_CHANGED:
        edges = [e for e in solid.GetGeoBody().Edges]
        S["solid_edges"] = [(e.Id, str(e.CurveType), e.Length) for e in edges]
        circ = sorted(round(e.Length, 9) for e in edges)
        chk("geometry: 4 circular edges, circumferences 2 pi Ri and 2 pi Ro",
            len(edges) == 4 and all("Circle" in str(e.CurveType) for e in edges)
            and abs(circ[0] - 2 * math.pi * RI) < 1e-7 and abs(circ[1] - 2 * math.pi * RI) < 1e-7
            and abs(circ[2] - 2 * math.pi * RO) < 1e-7 and abs(circ[3] - 2 * math.pi * RO) < 1e-7,
            "2x %.6f, 2x %.6f m" % (2 * math.pi * RI, 2 * math.pi * RO), circ)
        sel = ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
        sel.Ids = [e.Id for e in edges]
        T("circumferential sizing re-scoped to the 4 circular solid edges (as 7A)", lambda: setattr(sz, "Location", sel), critical=True)
        T("through-wall divisions %d" % NR, lambda: setattr(fm, "InternalNumberOfDivisions", NR), critical=True)
        fm.Name = "M36_Mapped_End_%d_radial" % NR
    S["mesh_settings"] = {"sweep_divisions": str(sw.SweepNumberDivisions), "bias_type": str(sw.SweepBiasType),
                          "bias": str(sw.SweepBiasValue), "radial": str(fm.InternalNumberOfDivisions),
                          "circumferential": str(sz.NumberOfDivisions), "sizing_edges": str(T("sizing ids", lambda: list(sz.Location.Ids))),
                          "sweep_location": str(T("sweep loc", lambda: sw.Location.Name)),
                          "face_meshing_location": str(T("fm loc", lambda: fm.Location.Name)),
                          "mapped": str(fm.MappedMesh), "element_order": str(mesh.ElementOrder)}
    chk("mesh controls: sweep %d axial / bias %.0f both ends / %d circumferential / %d through-wall / quadratic" % (NA, BIAS, NC, NR),
        S["mesh_settings"]["sweep_divisions"] == str(NA) and abs(float(S["mesh_settings"]["bias"]) - BIAS) < 1e-9
        and S["mesh_settings"]["circumferential"] == str(NC) and S["mesh_settings"]["radial"] == str(NR)
        and "o_ooo_ooooo_ooo_o" in S["mesh_settings"]["bias_type"], "%d / %.0f / %d / %d" % (NA, BIAS, NC, NR), S["mesh_settings"])
    if GEO_CHANGED or int(mesh.Nodes) == 0:
        S["mesh_regenerated"] = True
        T("clear mesh", lambda: mesh.ClearGeneratedData())
        t0 = time.time()
        T("generate mesh", lambda: mesh.GenerateMesh(), critical=True)
        S["mesh_time_s"] = round(time.time() - t0, 1)
    else:
        S["mesh_regenerated"] = False
        W("mesh B kept as in the 7B project (not regenerated)")
    S["mesh_controls_after"] = [(c.Name, c.GetType().Name, str(c.ObjectState)) for c in mesh.Children]
    nn, ne = int(mesh.Nodes), int(mesh.Elements)
    S["mesh"] = {"nodes": nn, "elements": ne, "expected_nodes": expected_nodes(NC, NR, NA), "expected_elements": NC * NR * NA}
    W("mesh %d nodes %d elements" % (nn, ne))
    chk("mesh: node count = swept quadratic-hex formula nc[(nr+1)(na+1)2 + nr(na+1) + (nr+1)na]",
        nn == expected_nodes(NC, NR, NA), expected_nodes(NC, NR, NA), nn)
    chk("mesh: element count = nc x nr x na", ne == NC * NR * NA, NC * NR * NA, ne)
    chk("licence: below the measured Student MAPDL limit (128,000 nodes)", nn < 128000, "< 128,000", nn)
    chk("mesh: quadratic elements", "Quadratic" in str(mesh.ElementOrder), "Quadratic", mesh.ElementOrder)
    met = {}
    for mt in ("ElementQuality", "AspectRatio", "JacobianRatio", "WarpingFactor", "ParallelDeviation",
               "MaximumCornerAngle", "Skewness"):
        try:
            mesh.MeshMetric = getattr(MeshMetricType, mt)
            met[mt] = {"min": qval(mesh.Minimum) if hasattr(mesh.Minimum, "Value") else float(mesh.Minimum),
                       "max": qval(mesh.Maximum) if hasattr(mesh.Maximum, "Value") else float(mesh.Maximum),
                       "avg": qval(mesh.Average) if hasattr(mesh.Average, "Value") else float(mesh.Average)}
        except Exception as e:
            met[mt] = "n/a %s" % str(e)[:120]
    S["mesh_metrics"] = met
    jr, eq, ar = met.get("JacobianRatio"), met.get("ElementQuality"), met.get("AspectRatio")
    chk("mesh: no invalid / inverted elements (Jacobian ratio finite and < 40, element quality > 0)",
        isinstance(jr, dict) and 0 < jr["max"] < 40 and isinstance(eq, dict) and eq["min"] > 0, "JR < 40, EQ > 0",
        "JR %s / EQ %s" % (jr, eq))
    chk("mesh: aspect ratio acceptable (< 20)", isinstance(ar, dict) and ar["max"] < 20, "< 20", ar)
    md = ExtAPI.DataModel.MeshDataByName(ExtAPI.DataModel.MeshDataNames[0])
    allnodes = [(nd.Id, nd.X, nd.Y, nd.Z) for nd in md.Nodes]
    rs = [math.hypot(x, y) for (_, x, y, _) in allnodes]
    zsn = [z for (_, _, _, z) in allnodes]
    chk("geometry: mesh extents r %.0f-%.0f mm, z 0-%.0f mm" % (RI * 1e3, RO * 1e3, LL * 1e3),
        abs(min(rs) - RI) < 1e-7 and abs(max(rs) - RO) < 1e-7 and abs(min(zsn)) < 1e-7 and abs(max(zsn) - LL) < 1e-7,
        "r %.3f-%.3f, z 0-%.1f" % (RI, RO, LL), "r %.9f-%.9f z %.9f-%.9f" % (min(rs), max(rs), min(zsn), max(zsn)))
    endset = set(i for (i, x, y, z) in allnodes if abs(z) < 1e-7 or abs(z - LL) < 1e-7)
    chk("mesh: end-face node count = 2 nc (3 nr + 2)", len(endset) == 2 * NC * (3 * NR + 2), 2 * NC * (3 * NR + 2), len(endset))
    # through-wall node radii at mid-span on theta = 0 (radial resolution record)
    rline = sorted(set(round(math.hypot(x, y), 9) for (i, x, y, z) in allnodes if abs(z - LL / 2) < 1e-7 and abs(y) < 1e-9 and x > 0))
    S["midspan_radial_node_positions_m"] = rline
    chk("mesh: 2 nr + 1 node radii through the wall (quadratic), uniform %.2f mm elements" % ((RO - RI) / NR * 1e3),
        len(rline) == 2 * NR + 1 and max(abs((rline[k + 1] - rline[k]) - (RO - RI) / (2 * NR)) for k in range(len(rline) - 1)) < 1e-7,
        "%d radii, step %.4f mm" % (2 * NR + 1, (RO - RI) / (2 * NR) * 1e3), rline)
    dump()

    # ------------------------------------------------------------------ 2. support-node sets at the same positions
    def three_nodes(zz, nsname):
        ring = [(i, x, y, z, math.degrees(math.atan2(y, x))) for (i, x, y, z) in allnodes
                if abs(z - zz) < 1e-7 and abs(math.hypot(x, y) - RO) < 1e-7]
        picks = []
        for target in (0.0, 120.0, -120.0):
            best = min(ring, key=lambda t: abs(((t[4] - target) + 180.0) % 360.0 - 180.0))
            if abs(((best[4] - target) + 180.0) % 360.0 - 180.0) > 0.01:
                raise Exception("no node at %s deg on the outer ring z=%s" % (target, zz))
            picks.append(best)
        ns = NS[nsname]
        # after a geometry replacement the node-based selection shows 'Suppressed' (its old mesh nodes are gone);
        # 'Suppressed' is read-only for a NamedSelection and clears when the new nodes are assigned (T01 run 1)
        W("%s state before re-location: %s" % (nsname, ns.ObjectState))
        sel =ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.MeshNodes)
        sel.Ids = [p[0] for p in picks]
        ns.Location = sel
        got = sorted(list(ns.Location.Ids))
        info = [(p[0], round(math.hypot(p[1], p[2]), 9), round(p[3], 9), round(p[4], 4)) for p in picks]
        chk("support nodes %s at r %.0f mm (outer), z %.2f m, 0/120/240 deg" % (nsname, RO * 1e3, zz),
            got == sorted([p[0] for p in picks]) and len(got) == 3 and str(ns.ObjectState) != "Suppressed",
            "3 nodes at the 7A positions", "%s state %s" % (info, ns.ObjectState))
        return info

    S["support_nodes"] = {"LC1": three_nodes(0.0, "NS_LC1_SUPPORT_3NODES_INLET_OUTER"),
                          "LC2": three_nodes(LL / 2.0, "NS_LC2_HOOP_3NODES_MIDSPAN_OUTER")}
    if not GEO_CHANGED:
        for k in ("LC1", "LC2"):
            ids = sorted(p[0] for p in S["support_nodes"][k])
            chk("mesh B: %s support nodes are the 7B nodes %s" % (k, MESH_B_SUPPORT_IDS[k]), ids == MESH_B_SUPPORT_IDS[k],
                MESH_B_SUPPORT_IDS[k], ids)
    dump()

    # ------------------------------------------------------------------ 3. temperature import (case source, 7A settings)
    ref_settings = ("Manual", "BucketVolume", "ShapeFunctions", "NearestNode")
    CASES = [("LC1", an1), ("LC2", an2)]
    exports = {}
    for tag, an in CASES:
        ibt = [o for o in walk(an) if o.Name == "Imported_Body_Temperature_CFD"][0]
        if GEO_CHANGED:
            T("%s imported temperature re-scoped to SOLID_DOMAIN (as 7A)" % tag, lambda b=ibt: setattr(b, "Location", NS["SOLID_DOMAIN"]),
              critical=True)
        chk("%s: import settings unchanged" % tag,
            all(s in str(v) for s, v in zip(ref_settings, (ibt.MappingControl, ibt.Algorithm, ibt.Weighting, ibt.OutsideOption))),
            "Manual / BucketVolume / ShapeFunctions / NearestNode",
            "%s / %s / %s / %s" % (ibt.MappingControl, ibt.Algorithm, ibt.Weighting, ibt.OutsideOption))
        chk("%s: environment (reference) temperature 300 K" % tag, abs(qK(an.EnvironmentTemperature) - 300.0) < 1e-6, "300 K",
            an.EnvironmentTemperature)
        T("%s import from the %s source" % (tag, TAG), lambda b=ibt: b.ImportLoad(), critical=True)
        smin = T("%s source minimum" % tag, lambda b=ibt: qK(b.SourceMinimum))
        smax = T("%s source maximum" % tag, lambda b=ibt: qK(b.SourceMaximum))
        px = os.path.join(AUD, "%s_%s_imported_body_temperature.txt" % (TAG, tag))
        ibt.ExportToTextFile(px)
        txt = open(px, "r").read()
        exports[tag] = txt
        vals = []
        for ln in txt.splitlines()[1:]:
            p = ln.split("\t")
            if len(p) >= 2:
                try:
                    vals.append(float(p[1]))
                except Exception:
                    pass
        S.setdefault("mapping", {})[tag] = {"state": str(ibt.ObjectState), "n": len(vals), "min_C": min(vals), "max_C": max(vals),
                                           "min_K": min(vals) + 273.15, "max_K": max(vals) + 273.15,
                                           "source_min_K": smin, "source_max_K": smax}
        if smin is not None and smax is not None:
            chk("%s: Mechanical reads the %s node temperatures (source min/max = case CSV %.3f / %.3f K)" % (tag, TAG, SRC_NODE_LO, SRC_NODE_HI),
                abs(smin - SRC_NODE_LO) < 0.01 and abs(smax - SRC_NODE_HI) < 0.01, "%.3f / %.3f K" % (SRC_NODE_LO, SRC_NODE_HI),
                "%s / %s" % (smin, smax))
        chk("%s: mapped temperature on every node, range inside the %s CFD solid range %.2f-%.2f K" % (tag, TAG, SRC_LO, SRC_HI),
            len(vals) == nn and min(vals) + 273.15 >= SRC_LO - 0.01 and max(vals) + 273.15 <= SRC_HI + 0.01,
            "%d values in [%.2f, %.2f] K" % (nn, SRC_LO, SRC_HI), S["mapping"][tag])
    chk("temperature export identical for LC1 and LC2", all(exports[k] == exports["LC1"] for k in exports), "identical",
        [k for k in exports if exports[k] != exports["LC1"]])
    S["mapping_named_selections"] = [(n.Name, n.Location.Ids.Count if hasattr(n.Location, "Ids") else "?")
                                     for n in Model.NamedSelections.Children if "_MAP_" in n.Name.upper()]
    unm = [(n.Name, n.Location.Ids.Count) for n in Model.NamedSelections.Children if "UNMAPPED" in n.Name.upper()]
    chk("no unmapped nodes", all(c == 0 for (_, c) in unm), "0", unm if unm else "no unmapped-node set created")
    dump()

    # ------------------------------------------------------------------ 4. object states and solver input decks
    for tag, an in CASES + ([("BUCKLING", bk)] if bk is not None else []):
        bad = [(o.Name, str(o.ObjectState)) for o in walk(an)
               if any(b in str(o.ObjectState) for b in ("UnderDefined", "Error", "LicenseConflict")) and not getattr(o, "Suppressed", False)]
        chk("%s: no under-defined / error objects" % tag, not bad, "none", bad)
    ref = scan_ds(REF7B_LC2)
    DS = {}
    for tag, an in CASES:
        p = os.path.join(PRE_IN, "%s_%s_presolve_ds.dat" % (TAG, tag))
        an.WriteInputFile(p)
        a = scan_ds(p)
        DS[tag] = a
        S.setdefault("presolve_input", {})[tag] = {"n_nodes": a["n_nodes"], "n_elem_lines": a["n_elem_lines"], "n_bf": a["n_bf"],
                                                   "bf_min_K": a.get("bf_min_K"), "bf_max_K": a.get("bf_max_K"),
                                                   "constraint_set": a["constraint_set"], "extra_eblocks": a["extra_eblocks"],
                                                   "eqsl": [x for x in a["misc"] if x.startswith("eqsl")], "has_443.41": a["has_443.41"],
                                                   "nblock_identical_to_7B": same(a, ref, "nblock"),
                                                   "eblock_identical_to_7B": same(a, ref, "eblock"),
                                                   "bf_identical_to_7B": same(a, ref, "bf")}
        chk("%s input: material section identical to the 7B solved input (E(T), alpha(T), nu 0.294, TREF 26.85, MPAMOD)" % tag,
            same(a, ref, "material"), "identical", "identical" if same(a, ref, "material") else "DIFFERENT")
        chk("%s input: %d nodes, %d SOLID186, temperature on every node" % (tag, nn, ne),
            a["n_nodes"] == nn and a["n_elem_lines"] == ne and a["n_bf"] == nn and "et,1,186" in a["misc"],
            "%d / %d / %d / et,1,186" % (nn, ne, nn), "%s / %s / %s" % (a["n_nodes"], a["n_elem_lines"], a["n_bf"]))
        chk("%s input: sparse direct solver (same as 7B)" % tag, any(x.startswith("eqsl,sparse") for x in a["misc"]),
            "eqsl,sparse", [x for x in a["misc"] if x.startswith("eqsl")])
        chk("%s input: no weak springs" % tag, not a["wsprings"], "none", a["wsprings"])
        chk("%s input: BF temperatures inside the %s CFD solid range" % (tag, TAG),
            a.get("bf_min_K") is not None and a["bf_min_K"] >= SRC_LO - 0.01 and a["bf_max_K"] <= SRC_HI + 0.01,
            "[%.2f, %.2f] K" % (SRC_LO, SRC_HI), "%s - %s" % (a.get("bf_min_K"), a.get("bf_max_K")))
        if not GEO_CHANGED:
            chk("%s input: mesh B node and element blocks identical to the 7B solved input" % tag,
                same(a, ref, "nblock") and same(a, ref, "eblock"), "identical",
                "nblock %s / eblock %s" % (same(a, ref, "nblock"), same(a, ref, "eblock")))
        if TAG == "C00_PIPELINE_CHECK":
            # C00 run 3 (Audits/Run3_C00_FAIL_bitwise_criterion): the C00 source is the P00 field on the SAME node
            # coordinates but with Fluent's re-numbered node / cell ids; Mechanical's bucket search then interpolates some
            # target nodes in a different (equally valid) source element. Bit-identity is therefore not the right test;
            # two valid mappings of one field may differ by at most twice the accepted 7A mapping error (2 x 0.092 K).
            bm = bfmap(a["_sections"]["bf"]); br = bfmap(ref["_sections"]["bf"])
            dd = [abs(bm[k] - br[k]) for k in br if k in bm]
            nd = sum(1 for x in dd if x > 0.0)
            S.setdefault("C00_bf_vs_7B", {})[tag] = {"nodes": len(dd), "nodes_different": nd, "max_abs_K": max(dd),
                                                    "mean_abs_K": sum(dd) / len(dd), "identical": same(a, ref, "bf")}
            chk("%s input (C00 control): nodal temperatures = 7B solved input within 2 x the 7A mapping error (0.184 K)" % tag,
                len(dd) == len(br) and max(dd) <= 0.184, "all %d nodes, max |dT| <= 0.184 K" % len(br), S["C00_bf_vs_7B"][tag])
        elif not GEO_CHANGED:
            chk("%s input: nodal temperatures differ from P00 (the case source is in use)" % tag, not same(a, ref, "bf"), "different",
                "different" if not same(a, ref, "bf") else "IDENTICAL TO P00")
    lc1ids = sorted(p[0] for p in S["support_nodes"]["LC1"])
    lc2ids = sorted(p[0] for p in S["support_nodes"]["LC2"])
    c1 = [(c[0], c[1], c[3], c[5], c[6]) for c in DS["LC1"]["constraint_set"]]
    chk("LC1 constraints: the 3 support nodes rotated to csys 12, U_theta = 0 and U_z = 0; nothing else",
        sorted([x[:3] for x in c1]) == sorted([("D", "uy", 3), ("D", "uz", 3), ("NROT_csys12", "", 3)])
        and all(x[3] == lc1ids[0] and x[4] == lc1ids[2] for x in c1), "uy, uz, nrot on %s" % lc1ids, DS["LC1"]["constraint_set"])
    c2 = DS["LC2"]["constraint_set"]
    uz = [c for c in c2 if c[0] == "D" and c[1] == "uz"]
    others = sorted([(c[0], c[1], c[3], c[5], c[6]) for c in c2 if not (c[0] == "D" and c[1] == "uz")])
    chk("LC2 constraints: U_z = 0 on all %d end-face nodes + 3 mid-span nodes U_theta = 0 (csys 12); nothing else" % len(endset),
        len(uz) == 1 and uz[0][3] == len(endset) and uz[0][4] == sum(endset)
        and others == sorted([("D", "uy", 3, lc2ids[0], lc2ids[2]), ("NROT_csys12", "", 3, lc2ids[0], lc2ids[2])]),
        "uz on the end faces, uy + nrot on %s" % lc2ids, c2)
    chk("LC1/LC2 inputs: no pressure (thermal only)", not DS["LC1"]["has_443.41"] and not DS["LC2"]["has_443.41"], "none",
        (DS["LC1"]["has_443.41"], DS["LC2"]["has_443.41"]))
    if bk is not None:
        pl = []
        for ic in bk.InitialConditions:
            try:
                pl.append(str(ic.PreStressICEnvironment.Name))
            except Exception as e:
                pl.append("? %s" % str(e)[:80])
        chk("buckling: pre-stress environment = LC2_Axially_Restrained", "LC2_Axially_Restrained" in pl, "LC2", pl)
        own = [o.Name for o in walk(bk) if o.GetType().Name in ("Displacement", "FixedSupport", "Pressure", "Force",
                                                              "NodalDisplacement", "ImportedBodyTemperature", "RemoteDisplacement")]
        chk("buckling: no loads or supports of its own", not own, "none", own)
    failed = [c for c in PRE["checks"] if not c["pass"]]
    PRE["gate"] = "PASS" if not failed else "FAIL (%d)" % len(failed)
    dump()
    if failed:
        raise Exception("PRE-SOLVE GATE FAILED - nothing solved: %s" % [c["check"] for c in failed])
    W("PRE-SOLVE GATE PASS (%d checks)" % len(PRE["checks"]))

    # ------------------------------------------------------------------ 5. buckling set-up (identical to 8A / 8B)
    BRES = []
    if bk is not None:
        sb = bk.AnalysisSettings
        T("buckling 6 modes", lambda: setattr(sb, "MaximumModesToFind", 6), critical=True)
        T("buckling positive multipliers only",
          lambda: setattr(sb, "IncludeNegativeLoadMultiplier", System.Enum.Parse(sb.IncludeNegativeLoadMultiplier.GetType(), "No")))
        S["buckling_settings"] = dict((k, str(T("bk " + k, lambda kk=k: getattr(sb, kk))))
                                      for k in ("MaximumModesToFind", "IncludeNegativeLoadMultiplier", "SolverType"))
        for n in range(1, 7):
            o = T("mode %d result" % n, lambda: bk.Solution.AddTotalDeformation())
            if o is not None:
                o.Name = "%s_BK_Mode_%d_Total_Deformation" % (TAG, n)
                T("mode %d set" % n, lambda oo=o, nn_=n: setattr(oo, "Mode", nn_))
                BRES.append((n, o))
        sn = T("buckling snippet", lambda: bk.Solution.AddCommandSnippet())
        if sn is not None:
            sn.Name = "%s_S8A_POST_APDL_load_factors_mode_shapes" % TAG
            T("buckling snippet input", lambda: setattr(sn, "Input", open(SNIP_B, "r").read()), critical=True)
    dump()

    # ------------------------------------------------------------------ 6. solve + extract
    def img_settings():
        try:
            st = Ansys.Mechanical.Graphics.GraphicsImageExportSettings()
            st.CurrentGraphicsDisplay = False
            st.Resolution = GraphicsResolutionType.EnhancedResolution
            st.Background = GraphicsBackgroundType.White
            st.Capture = GraphicsCaptureType.ImageAndLegend
            st.Width = 1600
            st.Height = 900
            return st
        except Exception as e:
            W("image settings failed %s" % e)
            return None

    IMG = img_settings()

    def image(obj, fname, views):
        got = []
        for lab, vname in views:
            p = os.path.join(FIG, "%s_%s.png" % (fname, lab))
            ok = T("image %s %s" % (fname, lab), lambda: (obj.Activate(),
                                                         Graphics.Camera.SetSpecificViewOrientation(getattr(ViewOrientationType, vname)),
                                                         Graphics.Camera.SetFit(),
                                                         Graphics.ExportImage(p, GraphicsImageExportFormat.PNG, IMG)
                                                         if IMG is not None else Graphics.ExportImage(p, GraphicsImageExportFormat.PNG)))
            if ok is not None and os.path.isfile(p):
                got.append(p)
        return got

    def scaling(mode):
        rp = Graphics.ViewOptions.ResultPreference
        try:
            et = rp.DeformationScaling.GetType()
            names = list(System.Enum.GetNames(et))
            pick = "True" if mode == "true" else [n for n in names if n.lower().startswith("auto")][0]
            T("scaling %s" % pick, lambda: setattr(rp, "DeformationScaling", System.Enum.Parse(et, pick)))
            if mode == "true":
                T("multiplier 1", lambda: setattr(rp, "DeformationScaleMultiplier", 1.0))
        except Exception as e:
            W("scaling failed %s" % str(e)[:200])

    def copy_files(tag, an, prefixes, sub):
        wd = str(an.WorkingDir)
        dst = os.path.join(SOLV, sub)
        names = os.listdir(wd) if os.path.isdir(wd) else []
        got = []
        for n in names:
            if n.startswith(prefixes) or n in ("solve.out", "file0.err", "file.err"):
                shutil.copy2(os.path.join(wd, n), os.path.join(dst, n))
                got.append(n)
        S["cases"].setdefault(tag, {})["copied"] = got
        S["cases"][tag]["working_dir"] = wd
        return got

    def solve(tag, an):
        C = S["cases"].setdefault(tag, {})
        n0 = len(list(ExtAPI.Application.Messages))
        t0 = time.time()
        W("SOLVING %s ..." % tag)
        T("%s solve" % tag, lambda: an.Solve(True))
        C["solve_wall_s"] = round(time.time() - t0, 1)
        C["solution_status"] = str(an.Solution.Status)
        C["solution_state"] = str(an.Solution.ObjectState)
        C["messages"] = [(str(m.Severity), m.DisplayString[:600]) for m in list(ExtAPI.Application.Messages)[n0:]]
        W("%s: state %s status %s %.0f s" % (tag, C["solution_state"], C["solution_status"], C["solve_wall_s"]))
        dump()
        if not (C["solution_state"] == "Solved" or "Done" in C["solution_status"]):
            raise Exception("%s did not solve (%s) - STOP" % (tag, C["solution_state"]))

    def extract(tag, an):
        C = S["cases"][tag]
        T("%s evaluate" % tag, lambda: an.Solution.EvaluateAllResults())
        R = {}
        for o in walk(an.Solution):
            tn = o.GetType().Name
            e = {"type": tn, "state": str(o.ObjectState)}
            if tn in ("ForceReaction", "MomentReaction"):
                for k in ("XAxis", "YAxis", "ZAxis", "Total"):
                    q = T("%s %s %s" % (tag, o.Name, k), lambda kk=k: getattr(o, kk))
                    e[k] = qval(q) if q is not None and hasattr(q, "Value") else str(q)
            elif hasattr(o, "Maximum") and tn not in ("CommandSnippet",):
                for k in ("Maximum", "Minimum"):
                    q = T("%s %s %s" % (tag, o.Name, k), lambda kk=k: getattr(o, kk))
                    e[k] = qval(q) if q is not None and hasattr(q, "Value") else str(q)
                if "Structural_Error" in o.Name:
                    px = os.path.join(SOLV, tag, "%s_%s_Structural_Error.txt" % (TAG, tag))
                    T("%s export structural error" % tag, lambda: o.ExportToTextFile(px))
            else:
                continue
            R[o.Name] = e
        C["results"] = R
        dump()

    solve("LC1", an1)
    extract("LC1", an1)
    copy_files("LC1", an1, ("s7b_",), "LC1")
    solve("LC2", an2)
    extract("LC2", an2)
    copy_files("LC2", an2, ("s7b_",), "LC2")
    if bk is not None:
        solve("BUCKLING", bk)
        T("buckling evaluate", lambda: bk.Solution.EvaluateAllResults())
        S["cases"]["BUCKLING"]["modes"] = [{"mode": n, "LoadMultiplier": str(T("LM %d" % n, lambda oo=o: oo.LoadMultiplier)),
                                            "state": str(o.ObjectState)} for (n, o) in BRES]
        copy_files("BUCKLING", bk, ("s8a_",), "BUCKLING")
        W("load multipliers %s" % [m["LoadMultiplier"] for m in S["cases"]["BUCKLING"]["modes"]])
    dump()
    imgs = []
    scaling("true")
    imgs += image(mesh, "%s_mesh" % TAG, (("end_face", "Front"), ("iso", "Iso")))
    vm1 = [o for o in walk(an1.Solution) if o.Name == "LC1_Equivalent_Stress_averaged"]
    if vm1:
        imgs += image(vm1[0], "%s_LC1_Equivalent_Stress" % TAG, (("iso", "Iso"),))
    vm2 = [o for o in walk(an2.Solution) if o.Name == "LC2_Equivalent_Stress_averaged"]
    if vm2:
        imgs += image(vm2[0], "%s_LC2_Equivalent_Stress" % TAG, (("iso", "Iso"),))
    if BRES:
        scaling("auto")
        imgs += image(BRES[0][1], "%s_BK_Mode_1" % TAG, (("iso", "Iso"), ("side_YZ", "Right")))
        scaling("true")
    S["images"] = imgs
    S["final_states"] = [(a.Name, str(a.Solution.ObjectState)) for a in Model.Analyses]
    dump()
    W("MECH-PARAM-9B2-%s-DONE" % TAG)
except Exception as e:
    import traceback
    W("FATAL %s" % e)
    W(traceback.format_exc())
    S["FATAL"] = str(e)
    dump()
