# -*- coding: utf-8 -*-
# =====================================================================================================
# SECTION 8B - STRUCTURAL MESH STUDY, one mesh variant per call (runs inside Mechanical, sent by wb_meshstudy_8B.wbjn).
# RE-ANALYSIS 2026 - newly generated results, not recovered originals.
#
# Works on a SAVE-AS copy of the solved 7B project (the 7B project and the official LC1/LC2 baseline stay untouched).
# Physics frozen: geometry, the same External Data temperature source (baseline_medium_final, mesh-based CDB + node
# CSV) re-mapped with the SAME settings, material tables, T_ref 300 K, LC1/LC2 supports (same definitions; the
# node-based support sets are re-located on the new mesh at the SAME positions), pressure definition, solver types.
# ONLY the structural mesh counts change: circumferential divisions (edge sizing), through-wall divisions (mapped face
# meshing) and axial divisions / bias (sweep). The variant is read from Mesh_Study/Audits/current_variant.json.
#  1. remesh -> gate (counts vs formula, quality, extents, support-node positions, temperature re-import, object
#     states, solver input decks: material identical to 7B, constraint sets resolved on the new mesh)
#  2. solve LC1, LC2, (LC2P), (LC2 linear buckling); read Mechanical maxima; copy the APDL snippet tables; images.
# Helper functions (logging, ds.dat parsing) are copied unchanged from mech_solve_7B.py (Section 7B).
# =====================================================================================================
import os, json, math, shutil, time, re
import System

BASE = r"<PROJECT_ROOT>"
S8 = os.path.join(BASE, "08_Structural_Analysis")
MS = os.path.join(S8, "Mesh_Study")
CFG = json.load(open(os.path.join(MS, "Audits", "current_variant.json"), "r"))
TAG = CFG["tag"]
NC, NR, NA, BIAS = int(CFG["nc"]), int(CFG["nr"]), int(CFG["na"]), float(CFG["bias"])
DO_P, DO_B = bool(CFG["pressure"]), bool(CFG["buckling"])
VD = os.path.join(MS, "Variants", TAG)
AUD = os.path.join(VD, "Audits")
PRE_IN = os.path.join(AUD, "Presolve_Inputs")
SOLV = os.path.join(VD, "Solver_Output")
FIG = os.path.join(MS, "figures", "Mechanical")
SNIP_B = os.path.join(S8, "Buckling", "Workbench", "Scripts", "s8a_buckle_snippet.inp")
REF7B_LC2 = os.path.join(S8, "LC2_Restrained", "Solver_Output", "LC2_solve_input_ds.dat")
MAPX = os.path.join(BASE, "07_Thermal_Analysis", "Mapping", "Mechanical_Export")
for d in [AUD, PRE_IN, SOLV, FIG] + [os.path.join(SOLV, k) for k in ("LC1", "LC2", "LC2P", "BUCKLING")]:
    if not os.path.isdir(d):
        os.makedirs(d)
LOG = os.path.join(AUD, "mech_%s_log.txt" % TAG)
PREF = os.path.join(AUD, "presolve_audit_%s.json" % TAG)
SUMF = os.path.join(AUD, "summary_%s.json" % TAG)
lines = []
PRE = {"gate": "NOT RUN", "checks": [], "variant": CFG, "note": "RE-ANALYSIS 2026 - Section 8B pre-solve audit"}
S = {"variant": CFG, "cases": {}, "note": "RE-ANALYSIS 2026 - Section 8B mesh-study solution (not recovered)"}


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
    # first EBLOCK = the 23,400 SOLID186 elements; further EBLOCKs = load-carrying surface elements (e.g. SURF154 for a
    # pressure). Run 1 of 7B compared ALL element blocks and stopped at the gate because LC2P correctly carries 4,680
    # SURF154 pressure elements that LC2 does not have (Audits/Gate_Run1_FAIL).
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
    # resolved constraint set: (dof, value, frozenset(node ids)) - independent of Mechanical's component names
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


def public(r):
    return dict((k, v) for k, v in r.items() if not k.startswith("_"))


def expected_nodes(nc, nr, na):
    return nc * ((nr + 1) * (na + 1) * 2 + nr * (na + 1) + (nr + 1) * na)


def ptype(a):
    return str(a.AnalysisType)


try:
    W("=== SECTION 8B MESH VARIANT %s: %d circ x %d wall x %d axial, bias %.1f (RE-ANALYSIS 2026) ===" % (TAG, NC, NR, NA, BIAS))
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

    # ------------------------------------------------------------------ 1. mesh controls -> variant
    mesh = Model.Mesh
    ctrls = list(mesh.Children)
    S["mesh_controls_before"] = [(c.Name, c.GetType().Name) for c in ctrls]
    sw = [c for c in ctrls if c.GetType().Name == "AutomaticMethod"][0]
    fm = [c for c in ctrls if c.GetType().Name == "FaceMeshing"][0]
    sz = [c for c in ctrls if "Sizing" in c.GetType().Name][0]
    before = {"sweep_divisions": str(sw.SweepNumberDivisions), "bias_type": str(sw.SweepBiasType), "bias": str(sw.SweepBiasValue),
              "radial": str(fm.InternalNumberOfDivisions), "circumferential": str(sz.NumberOfDivisions)}
    S["mesh_settings_before"] = before
    chk("starting point is the 7B baseline mesh (36 circ, 5 wall, 130 axial, bias 4)",
        before["sweep_divisions"] == "130" and before["radial"] == "5" and before["circumferential"] == "36"
        and abs(float(before["bias"]) - 4.0) < 1e-9, "36/5/130/4", before)
    T("circumferential divisions", lambda: setattr(sz, "NumberOfDivisions", NC), critical=True)
    T("through-wall divisions", lambda: setattr(fm, "InternalNumberOfDivisions", NR), critical=True)
    T("axial divisions", lambda: setattr(sw, "SweepNumberDivisions", NA), critical=True)
    T("axial bias", lambda: setattr(sw, "SweepBiasValue", BIAS), critical=True)
    sw.Name = "MS8B_%s_Sweep_%d_axial_bias%g" % (TAG, NA, BIAS)
    fm.Name = "MS8B_%s_Mapped_End_%d_wall" % (TAG, NR)
    sz.Name = "MS8B_%s_%d_circumferential" % (TAG, NC)
    S["mesh_settings_after"] = {"sweep_divisions": str(sw.SweepNumberDivisions), "bias_type": str(sw.SweepBiasType),
                                "bias": str(sw.SweepBiasValue), "radial": str(fm.InternalNumberOfDivisions),
                                "circumferential": str(sz.NumberOfDivisions), "element_order": str(mesh.ElementOrder)}
    T("clear mesh", lambda: mesh.ClearGeneratedData())
    t0 = time.time()
    T("generate mesh", lambda: mesh.GenerateMesh(), critical=True)
    S["mesh_time_s"] = round(time.time() - t0, 1)
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
    chk("geometry: mesh extents r 10-20 mm, z 0-600 mm (geometry unchanged)",
        abs(min(rs) - 0.010) < 1e-7 and abs(max(rs) - 0.020) < 1e-7 and abs(min(zsn)) < 1e-7 and abs(max(zsn) - 0.6) < 1e-7,
        "r 0.010-0.020, z 0-0.6", "r %.9f-%.9f z %.9f-%.9f" % (min(rs), max(rs), min(zsn), max(zsn)))
    endset = set(i for (i, x, y, z) in allnodes if abs(z) < 1e-7 or abs(z - 0.6) < 1e-7)
    chk("mesh: end-face node count = 2 nc (3 nr + 2)", len(endset) == 2 * NC * (3 * NR + 2), 2 * NC * (3 * NR + 2), len(endset))

    # ------------------------------------------------------------------ 2. support-node sets at the same positions
    def three_nodes(zz, nsname):
        ring = [(i, x, y, z, math.degrees(math.atan2(y, x))) for (i, x, y, z) in allnodes
                if abs(z - zz) < 1e-7 and abs(math.hypot(x, y) - 0.02) < 1e-7]
        picks = []
        for target in (0.0, 120.0, -120.0):
            best = min(ring, key=lambda t: abs(((t[4] - target) + 180.0) % 360.0 - 180.0))
            if abs(((best[4] - target) + 180.0) % 360.0 - 180.0) > 0.01:
                raise Exception("no node at %s deg on the outer ring z=%s" % (target, zz))
            picks.append(best)
        sel = ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.MeshNodes)
        sel.Ids = [p[0] for p in picks]
        NS[nsname].Location = sel
        got = sorted(list(NS[nsname].Location.Ids))
        info = [(p[0], round(math.hypot(p[1], p[2]), 9), round(p[3], 9), round(p[4], 4)) for p in picks]
        chk("support nodes %s re-located at r 20 mm, z %.1f m, 0/120/240 deg" % (nsname, zz),
            got == sorted([p[0] for p in picks]) and len(got) == 3, "3 nodes at the 7A positions", info)
        return info

    S["support_nodes"] = {"LC1": three_nodes(0.0, "NS_LC1_SUPPORT_3NODES_INLET_OUTER"),
                          "LC2": three_nodes(0.3, "NS_LC2_HOOP_3NODES_MIDSPAN_OUTER")}
    dump()

    # ------------------------------------------------------------------ 3. temperature re-mapped (same source, same settings)
    ref_settings = ("Manual", "BucketVolume", "ShapeFunctions", "NearestNode")
    CASES = [("LC1", an1), ("LC2", an2)] + ([("LC2P", an3)] if (DO_P and an3 is not None) else [])
    IBT = {}
    exports = {}
    for tag, an in CASES:
        ibt = [o for o in walk(an) if o.Name == "Imported_Body_Temperature_CFD"][0]
        IBT[tag] = ibt
        chk("%s: import settings unchanged" % tag,
            all(s in str(v) for s, v in zip(ref_settings, (ibt.MappingControl, ibt.Algorithm, ibt.Weighting, ibt.OutsideOption))),
            "Manual / BucketVolume / ShapeFunctions / NearestNode",
            "%s / %s / %s / %s" % (ibt.MappingControl, ibt.Algorithm, ibt.Weighting, ibt.OutsideOption))
        T("%s re-import onto the %s mesh" % (tag, TAG), lambda b=ibt: b.ImportLoad(), critical=True)
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
                                           "min_K": min(vals) + 273.15, "max_K": max(vals) + 273.15}
        chk("%s: mapped temperature on every node, range inside the CFD source range 423.21-562.58 K" % tag,
            len(vals) == nn and min(vals) + 273.15 >= 423.21 - 0.01 and max(vals) + 273.15 <= 562.58 + 0.01,
            "%d values in [423.21, 562.58] K" % nn, S["mapping"][tag])
    chk("temperature export identical for all cases on this mesh", all(exports[k] == exports["LC1"] for k in exports), "identical",
        [k for k in exports if exports[k] != exports["LC1"]])
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
                                                   "eqsl": [x for x in a["misc"] if x.startswith("eqsl")], "has_443.41": a["has_443.41"]}
        chk("%s input: material section identical to the 7B solved input (E(T), alpha(T), nu 0.294, TREF 26.85, MPAMOD)" % tag,
            same(a, ref, "material"), "identical", "identical" if same(a, ref, "material") else "DIFFERENT")
        chk("%s input: %d nodes, %d SOLID186, temperature on every node" % (tag, nn, ne),
            a["n_nodes"] == nn and a["n_elem_lines"] == ne and a["n_bf"] == nn and "et,1,186" in a["misc"],
            "%d / %d / %d / et,1,186" % (nn, ne, nn), "%s / %s / %s" % (a["n_nodes"], a["n_elem_lines"], a["n_bf"]))
        chk("%s input: sparse direct solver (same as 7B)" % tag, any(x.startswith("eqsl,sparse") for x in a["misc"]),
            "eqsl,sparse", [x for x in a["misc"] if x.startswith("eqsl")])
        chk("%s input: no weak springs" % tag, not a["wsprings"], "none", a["wsprings"])
    lc1ids = sorted(p[0] for p in S["support_nodes"]["LC1"])
    lc2ids = sorted(p[0] for p in S["support_nodes"]["LC2"])
    c1 = [(c[0], c[1], c[3], c[5], c[6]) for c in DS["LC1"]["constraint_set"]]
    chk("LC1 constraints: the 3 re-located support nodes rotated to csys 12, U_theta = 0 and U_z = 0; nothing else",
        sorted([x[:3] for x in c1]) == sorted([("D", "uy", 3), ("D", "uz", 3), ("NROT_csys12", "", 3)])
        and all(x[3] == lc1ids[0] and x[4] == lc1ids[2] for x in c1), "uy, uz, nrot on %s" % lc1ids, DS["LC1"]["constraint_set"])
    for tag in [t for (t, _) in CASES if t != "LC1"]:
        c2 = DS[tag]["constraint_set"]
        uz = [c for c in c2 if c[0] == "D" and c[1] == "uz"]
        others = sorted([(c[0], c[1], c[3], c[5], c[6]) for c in c2 if not (c[0] == "D" and c[1] == "uz")])
        chk("%s constraints: U_z = 0 on all %d end-face nodes + 3 re-located mid-span nodes U_theta = 0 (csys 12); nothing else"
            % (tag, len(endset)),
            len(uz) == 1 and uz[0][3] == len(endset) and uz[0][4] == sum(endset)
            and others == sorted([("D", "uy", 3, lc2ids[0], lc2ids[2]), ("NROT_csys12", "", 3, lc2ids[0], lc2ids[2])]),
            "uz on the end faces, uy + nrot on %s" % lc2ids, c2)
    chk("LC1/LC2 inputs: no pressure (thermal only)", not DS["LC1"]["has_443.41"] and not DS["LC2"]["has_443.41"], "none",
        (DS["LC1"]["has_443.41"], DS["LC2"]["has_443.41"]))
    if "LC2P" in DS:
        c3 = DS["LC2P"]
        chk("LC2P input: 443.41 Pa on %d SURF154 bore faces (nc x na)" % (NC * NA),
            c3["has_443.41"] and len(c3["extra_eblocks"]) == 1 and c3["extra_eblocks"][0]["count"] == NC * NA,
            "%d SURF154" % (NC * NA), c3["extra_eblocks"])
    if bk is not None:
        pl = []
        for ic in bk.InitialConditions:
            try:
                pl.append(str(ic.PreStressICEnvironment.Name))
            except Exception as e:
                pl.append("? %s" % str(e)[:80])
        chk("buckling: pre-stress environment = LC2_Axially_Restrained", "LC2_Axially_Restrained" in pl, "LC2", pl)
        own = [o.Name for o in walk(bk) if o.GetType().Name in ("Displacement", "FixedSupport", "Pressure", "Force",
                                                              "NodalDisplacement", "ImportedBodyTemperature")]
        chk("buckling: no loads or supports of its own", not own, "none", own)
    failed = [c for c in PRE["checks"] if not c["pass"]]
    PRE["gate"] = "PASS" if not failed else "FAIL (%d)" % len(failed)
    dump()
    if failed:
        raise Exception("PRE-SOLVE GATE FAILED - nothing solved: %s" % [c["check"] for c in failed])
    W("PRE-SOLVE GATE PASS (%d checks)" % len(PRE["checks"]))

    # ------------------------------------------------------------------ 5. buckling set-up (identical to 8A)
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
    if "LC2P" in DS:
        solve("LC2P", an3)
        extract("LC2P", an3)
        copy_files("LC2P", an3, ("s7b_",), "LC2P")
    if bk is not None:
        solve("BUCKLING", bk)
        T("buckling evaluate", lambda: bk.Solution.EvaluateAllResults())
        S["cases"]["BUCKLING"]["modes"] = [{"mode": n, "LoadMultiplier": str(T("LM %d" % n, lambda oo=o: oo.LoadMultiplier)),
                                            "state": str(o.ObjectState)} for (n, o) in BRES]
        copy_files("BUCKLING", bk, ("s8a_",), "BUCKLING")
        W("load multipliers %s" % [m["LoadMultiplier"] for m in S["cases"]["BUCKLING"]["modes"]])
    dump()
    # images (actual solved model)
    imgs = []
    scaling("true")
    imgs += image(mesh, "%s_mesh" % TAG, (("end_face", "Front"), ("side", "Right"), ("iso", "Iso")))
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
    W("MECH-MESHSTUDY-8B-%s-DONE" % TAG)
except Exception as e:
    import traceback
    W("FATAL %s" % e)
    W(traceback.format_exc())
    S["FATAL"] = str(e)
    dump()
