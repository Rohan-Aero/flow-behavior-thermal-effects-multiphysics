# -*- coding: utf-8 -*-
# =====================================================================================================
# SECTION 7B - Mechanical SOLVE script (runs inside Mechanical via Workbench SendCommand from wb_solve_7B.wbjn).
# RE-ANALYSIS 2026 - newly generated solutions of the newly built 7A model. Nothing here is a recovered original.
#
#  0. Opens nothing new: works on the SaveAs copy ..._Structural_7B.wbpj (the 7A project stays unsolved).
#  1. PRE-SOLVE AUDIT (gate). Geometry, material, mesh, CS, NS node ids, T_ref, imported temperature (re-exported
#     and compared byte-for-byte with the 7A export), object states, and the solver input files written BEFORE any
#     change, compared section by section with the 7A input files. Any failure -> no solve.
#  2. LC2P = LC2 + active uniform internal gauge pressure 443.41 Pa (the CFD wall maximum; upper bound of the CFD
#     distribution). Same temperature import, same restraints. Its input file is compared with the LC2 one.
#  3. Numerical setting only: sparse DIRECT solver in all three cases (the 7A default was PCG 1e-8; a direct solve
#     makes the ~1e-6 relative pressure effect resolvable). No physics is changed.
#  4. Result objects + APDL post snippet (s7b_post_snippet.inp: reactions, full-precision nodal table in CS_DUCT_CYL).
#  5. Solve LC1 -> (check) -> LC2 -> (check) -> LC2P. Evaluate, export text, export images, copy solver output.
# The temperature field, geometry, material and restraints of LC1/LC2 are NOT modified.
# =====================================================================================================
import os, json, math, shutil, time, re
import System

BASE = r"<PROJECT_ROOT>"
S8 = os.path.join(BASE, "08_Structural_Analysis")
AUD = os.path.join(S8, "Audits")
PRE_IN = os.path.join(AUD, "Presolve_Inputs")
EXP = os.path.join(S8, "Exports")
FIG = os.path.join(S8, "Figures", "Mechanical")
SNIP = os.path.join(S8, "Workbench", "Scripts", "s7b_post_snippet.inp")
INP7A = os.path.join(S8, "Mechanical_Setup", "Input_Files")
MAPX = os.path.join(BASE, "07_Thermal_Analysis", "Mapping", "Mechanical_Export")
CASEDIR = {"LC1": os.path.join(S8, "LC1_Free_Expansion"), "LC2": os.path.join(S8, "LC2_Restrained"),
           "LC2P": os.path.join(S8, "Pressure_Check")}
for d in [AUD, PRE_IN, FIG] + [os.path.join(EXP, k) for k in CASEDIR] + list(CASEDIR.values()) + \
         [os.path.join(v, "Solver_Output") for v in CASEDIR.values()]:
    if not os.path.isdir(d):
        os.makedirs(d)
LOG = os.path.join(AUD, "mech_solve_7B_log.txt")
PREF = os.path.join(AUD, "presolve_audit_7B.json")
SUMF = os.path.join(AUD, "mech_solve_7B_summary.json")
lines = []
PRE = {"gate": "NOT RUN", "checks": [], "note": "RE-ANALYSIS 2026 - pre-solve audit of the newly built 7A model"}
S = {"cases": {}, "note": "RE-ANALYSIS 2026 - newly generated structural solutions (not recovered originals)"}


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
            r["eblock_header"] = L[i]
            j = i + 2
            while j < n and low[j] != "-1":
                sec["eblock"].append(L[j])
                j += 1
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


try:
    W("=== SECTION 7B MECHANICAL SOLVE (RE-ANALYSIS 2026) ===")
    ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS
    S["unit_system"] = str(ExtAPI.Application.ActiveUnitSystem)
    # ------------------------------------------------------------------------------------------ objects
    bodies = Model.Geometry.GetChildren(DataModelObjectCategory.Body, True)
    solid = [b for b in bodies if b.Name == "SOLID_DOMAIN"][0]
    fluid = [b for b in bodies if b.Name == "FLUID_DOMAIN"][0]
    NS = dict((n.Name, n) for n in Model.NamedSelections.Children)
    cs = [c for c in Model.CoordinateSystems.Children if c.Name == "CS_DUCT_CYL"][0]
    AN = dict((a.Name, a) for a in Model.Analyses)
    W("analyses %s" % [a.Name for a in Model.Analyses])
    an1 = AN["LC1_Free_Expansion"]
    an2 = AN["LC2_Axially_Restrained"]
    others = [a for a in Model.Analyses if a.Name not in ("LC1_Free_Expansion", "LC2_Axially_Restrained")]
    an3 = others[0] if others else None
    if an3 is not None:
        an3.Name = "LC2P_Restrained_Thermal_Plus_Pressure"
    CASES = [("LC1", an1), ("LC2", an2)] + ([("LC2P", an3)] if an3 is not None else [])

    # ========================================================================================== 1. PRE-SOLVE AUDIT
    # geometry / material
    chk("geometry: SOLID_DOMAIN active", not solid.Suppressed, "not suppressed", solid.Suppressed)
    chk("geometry: FLUID_DOMAIN suppressed (structural model = solid only)", bool(fluid.Suppressed), True, fluid.Suppressed)
    vol = qval(solid.Volume)
    vth = math.pi * (0.020 ** 2 - 0.010 ** 2) * 0.600
    chk("geometry: solid volume = pi(ro^2-ri^2)L (Di 20, Do 40, L 600 mm)", vol is not None and abs(vol / vth - 1) < 1e-3,
        "%.6e m3 (+/-0.1%%)" % vth, vol)
    chk("material: SOLID_DOMAIN = Inconel_718_Re_analysis", str(solid.Material) == "Inconel_718_Re_analysis",
        "Inconel_718_Re_analysis", solid.Material)
    # mesh
    mesh = Model.Mesh
    chk("mesh: node count", int(mesh.Nodes) == 108252, 108252, mesh.Nodes)
    chk("mesh: element count", int(mesh.Elements) == 23400, 23400, mesh.Elements)
    chk("mesh: quadratic elements", "Quadratic" in str(mesh.ElementOrder), "Quadratic", mesh.ElementOrder)
    chk("mesh: below measured Student MAPDL limit", int(mesh.Nodes) < 128000, "< 128,000 nodes", mesh.Nodes)
    met = {}
    for mt in ("ElementQuality", "AspectRatio", "JacobianRatio", "WarpingFactor", "ParallelDeviation",
               "MaximumCornerAngle", "Skewness", "OrthogonalQuality"):
        try:
            mesh.MeshMetric = getattr(MeshMetricType, mt)
            met[mt] = {"min": qval(mesh.Minimum) if hasattr(mesh.Minimum, "Value") else float(mesh.Minimum),
                       "max": qval(mesh.Maximum) if hasattr(mesh.Maximum, "Value") else float(mesh.Maximum),
                       "avg": qval(mesh.Average) if hasattr(mesh.Average, "Value") else float(mesh.Average)}
        except Exception as e:
            met[mt] = "n/a %s" % str(e)[:120]
    S["mesh_metrics"] = met
    jr = met.get("JacobianRatio")
    eq = met.get("ElementQuality")
    chk("mesh: no invalid elements (Jacobian ratio finite, < 40; element quality > 0)",
        isinstance(jr, dict) and 0 < jr["max"] < 40 and isinstance(eq, dict) and eq["min"] > 0,
        "JR max < 40, EQ min > 0", "JR %s / EQ %s" % (jr, eq))
    md = ExtAPI.DataModel.MeshDataByName(ExtAPI.DataModel.MeshDataNames[0])
    rmin, rmax, zmin, zmax, nn = 1e9, -1e9, 1e9, -1e9, 0
    for nd in md.Nodes:
        r = math.hypot(nd.X, nd.Y)
        rmin, rmax, zmin, zmax = min(rmin, r), max(rmax, r), min(zmin, nd.Z), max(zmax, nd.Z)
        nn += 1
    chk("geometry: mesh extents r 10-20 mm, z 0-600 mm",
        abs(rmin - 0.010) < 1e-7 and abs(rmax - 0.020) < 1e-7 and abs(zmin) < 1e-7 and abs(zmax - 0.6) < 1e-7,
        "r 0.010-0.020 m, z 0-0.600 m", "r %.9f-%.9f z %.9f-%.9f (%d nodes)" % (rmin, rmax, zmin, zmax, nn))
    # support node sets must be the 7A ones (same numbering = same mesh)
    for nsname, zz, ids7a in (("NS_LC1_SUPPORT_3NODES_INLET_OUTER", 0.0, [18870, 18882, 18894]),
                              ("NS_LC2_HOOP_3NODES_MIDSPAN_OUTER", 0.3, [25862, 25874, 25886])):
        ids = sorted(list(NS[nsname].Location.Ids))
        pos = []
        for i in ids:
            nd = md.NodeById(i)
            pos.append((i, round(math.hypot(nd.X, nd.Y), 9), round(nd.Z, 9), round(math.degrees(math.atan2(nd.Y, nd.X)), 4)))
        chk("BC nodes: %s = 7A ids at r 20 mm, z %.1f m, 0/120/240 deg" % (nsname, zz),
            ids == ids7a and all(abs(p[1] - 0.02) < 1e-8 and abs(p[2] - zz) < 1e-8 for p in pos), ids7a, pos)
    # coordinate system
    chk("CS_DUCT_CYL fully defined, cylindrical, origin 0,0,0",
        "FullyDefined" in str(cs.ObjectState) and "Cylindrical" in str(cs.CoordinateSystemType)
        and all(abs(qval(getattr(cs, k))) < 1e-12 for k in ("OriginX", "OriginY", "OriginZ")),
        "FullyDefined / Cylindrical / (0,0,0)",
        "%s / %s / (%s,%s,%s)" % (cs.ObjectState, cs.CoordinateSystemType, cs.OriginX, cs.OriginY, cs.OriginZ))
    # analyses LC1, LC2 as built in 7A
    ref7a = open(os.path.join(MAPX, "LC1_imported_body_temperature.txt"), "r").read()
    IBT = {}
    for tag, an in (("LC1", an1), ("LC2", an2)):
        chk("%s: environment (stress-free reference) temperature = 300 K" % tag,
            abs(qK(an.EnvironmentTemperature) - 300.0) < 1e-6, "300 K", an.EnvironmentTemperature)
        objs = walk(an)
        ibt = [o for o in objs if o.Name == "Imported_Body_Temperature_CFD"][0]
        IBT[tag] = ibt
        st0 = str(ibt.ObjectState)
        W("%s imported temperature state on open: %s" % (tag, st0))
        if "Solved" not in st0 or "Not" in st0:
            T("%s re-import (same External Data source and settings as 7A)" % tag, lambda b=ibt: b.ImportLoad(), critical=True)
        px = os.path.join(AUD, "presolve_%s_imported_body_temperature_7B.txt" % tag)
        ibt.ExportToTextFile(px)
        now = open(px, "r").read()
        chk("%s: mapped temperature identical to the 7A export (field unchanged)" % tag, now == ref7a,
            "byte-identical to 07_Thermal_Analysis/Mapping/Mechanical_Export/LC1_imported_body_temperature.txt",
            "identical" if now == ref7a else "DIFFERENT (%d vs %d chars)" % (len(now), len(ref7a)))
        chk("%s: imported temperature settings" % tag,
            "Manual" in str(ibt.MappingControl) and "BucketVolume" in str(ibt.Algorithm)
            and "ShapeFunctions" in str(ibt.Weighting) and "NearestNode" in str(ibt.OutsideOption),
            "Manual / BucketVolume / ShapeFunctions / NearestNode",
            "%s / %s / %s / %s (state on open %s, now %s)" % (ibt.MappingControl, ibt.Algorithm, ibt.Weighting,
                                                           ibt.OutsideOption, st0, ibt.ObjectState))
        unm = [(n.Name, n.Location.Ids.Count) for n in Model.NamedSelections.Children
               if "UNMAPPED" in n.Name.upper() and n.Name.upper().startswith(tag)]
        chk("%s: no unmapped nodes" % tag, all(c == 0 for (_, c) in unm), "0 unmapped", unm if unm else "no unmapped-node NS created (0 unmapped)")
        bad = [(o.Name, str(o.ObjectState)) for o in objs
               if any(b in str(o.ObjectState) for b in ("UnderDefined", "Error", "SolveFailed", "LicenseConflict"))
               and not getattr(o, "Suppressed", False)]
        chk("%s: no under-defined / error objects" % tag, not bad, "none", bad)
        prs = [(o.Name, bool(o.Suppressed)) for o in objs if o.GetType().Name == "Pressure"]
        chk("%s: pressure objects suppressed (thermal-only case)" % tag, all(s for (_, s) in prs) and len(prs) == 2,
            "2 pressure objects, both suppressed", prs)
        stt = an.AnalysisSettings
        info = {}
        for k in ("LargeDeflection", "NumberOfSteps", "SolverType", "WeakSprings", "InertiaRelief"):
            info[k] = str(T("%s %s" % (tag, k), lambda kk=k: getattr(stt, kk)))
        chk("%s: analysis settings (small deflection, 1 step, no inertia relief)" % tag,
            info["LargeDeflection"] in ("False", "Off") and info["NumberOfSteps"] == "1" and info["InertiaRelief"] in ("False", "Off"),
            "LargeDeflection off, 1 step, InertiaRelief off", info)
        S.setdefault("settings_before", {})[tag] = info
        W("%s solution state before solve: %s" % (tag, an.Solution.ObjectState))
    dump()
    # solver input files written BEFORE any 7B change, compared with the 7A files
    DS = {}
    for tag, an, f7a in (("LC1", an1, "LC1_Free_Expansion_ds.dat"), ("LC2", an2, "LC2_Axially_Restrained_ds.dat")):
        p = os.path.join(PRE_IN, "%s_presolve_ds.dat" % tag)
        an.WriteInputFile(p)
        a = scan_ds(p)
        b = scan_ds(os.path.join(INP7A, f7a))
        DS[tag] = a
        S.setdefault("presolve_input", {})[tag] = public(a)
        for key in ("nblock", "eblock", "bf", "material"):
            chk("%s input vs 7A input: identical %s section" % (tag, key), same(a, b, key), "identical",
                "identical" if same(a, b, key) else "DIFFERENT")
        chk("%s input vs 7A input: identical resolved constraints (DOF, value, node set)" % tag,
            a["constraint_set"] == b["constraint_set"], b["constraint_set"], a["constraint_set"])
        S.setdefault("presolve_input_raw_constraints_identical_to_7A", {})[tag] = same(a, b, "constraints")
        chk("%s input: 108,252 nodes, 23,400 SOLID186, BF on all nodes" % tag,
            a["n_nodes"] == 108252 and a["n_elem_lines"] == 23400 and a["n_bf"] == 108252 and "et,1,186" in a["misc"],
            "108252 / 23400 / 108252 / et,1,186", "%s / %s / %s / %s" % (a["n_nodes"], a["n_elem_lines"], a["n_bf"],
                                                                        [x for x in a["misc"] if x.startswith("et,")]))
        chk("%s input: mapped T range 423.84-562.56 K" % tag,
            abs(a["bf_min_K"] - 423.84) < 0.05 and abs(a["bf_max_K"] - 562.56) < 0.05, "423.84-562.56 K",
            "%.3f-%.3f K" % (a["bf_min_K"], a["bf_max_K"]))
        mat = a["material"]
        chk("%s input: T_ref, density, E(T) table, nu 0.294 [ASSUMED], secant alpha(T) table, MPAMOD 21.11" % tag,
            "tref,26.85" in [x.lower() for x in mat]
            and any(x.upper().startswith("MP,DENS,1,8190") for x in mat)
            and any(x.upper().startswith("MPDATA,EX,1") and "204000000000,199000000000,193000000000,187000000000,180000000000" in x for x in mat)
            and any(x.upper().startswith("MPDATA,NUXY,1") and x.count("0.294") == 5 for x in mat)
            and any(x.upper().startswith("MPDATA,ALPX,1") and "1.28e-05,1.33e-05,1.39e-05,1.42e-05,1.48e-05" in x for x in mat)
            and any(x.upper().startswith("MPAMOD,1,21.11") for x in mat),
            "tref 26.85 C; DENS 8190; EX 204/199/193/187/180 GPa @20-400 C; NUXY 0.294; ALPX 12.8-14.8e-6 @93.33-537.78 C; MPAMOD 21.11",
            [x for x in mat if not x.upper().startswith("MPTEMP,,")])
        chk("%s input: no weak springs" % tag, not a["wsprings"], "no wsprings", a["wsprings"])
    chk("LC1 constraints: 3 rotated nodes (csys 12), U_theta = 0 and U_z = 0 only",
        [c[:4] for c in DS["LC1"]["constraint_set"]] == sorted([("D", "uy", 0.0, 3), ("D", "uz", 0.0, 3), ("NROT_csys12", "", 0.0, 3)]),
        "nrot(3, csys 12) + d uy + d uz on the same 3 nodes", DS["LC1"]["constraint_set"])
    chk("LC2 constraints: U_z = 0 on 1,224 end-face nodes + 3 rotated mid-span nodes U_theta = 0",
        [c[:4] for c in DS["LC2"]["constraint_set"]] == sorted([("D", "uz", 0.0, 1224), ("D", "uy", 0.0, 3), ("NROT_csys12", "", 0.0, 3)]),
        "d uz (1224 nodes) + nrot(3, csys 12) + d uy (3)", DS["LC2"]["constraint_set"])
    dump()

    # ========================================================================================== 2. LC2P set-up
    if an3 is None:
        raise Exception("third analysis (LC2P) not found - Workbench system was not created")
    an3.EnvironmentTemperature = Quantity(300, "K")
    grp = [c for c in an3.Children if c.GetType().Name == "ImportedLoadGroup"]
    chk("LC2P: External Data linked (imported load group present)", len(grp) == 1, 1, len(grp))
    ibt3 = grp[0].AddImportedBodyTemperature()
    ibt3.Name = "Imported_Body_Temperature_CFD"
    ibt3.Location = NS["SOLID_DOMAIN"]
    ibt3.MappingControl = MappingControlType.Manual
    ibt3.Algorithm = System.Enum.Parse(MappingAlgorithm, "BucketVolume")
    ibt3.Weighting = System.Enum.Parse(WeightingType, "ShapeFunctions")
    ibt3.OutsideOption = System.Enum.Parse(MappingOutsideOption, "NearestNode")
    T("LC2P import", lambda: ibt3.ImportLoad(), critical=True)
    IBT["LC2P"] = ibt3
    px = os.path.join(AUD, "presolve_LC2P_imported_body_temperature_7B.txt")
    ibt3.ExportToTextFile(px)
    now = open(px, "r").read()
    chk("LC2P: mapped temperature identical to the 7A export", now == ref7a, "byte-identical", "identical" if now == ref7a else "DIFFERENT")

    def disp(an, name, loc):
        d = an.AddDisplacement()
        d.Name = name
        d.Location = loc
        d.ZComponent.Output.DiscreteValues = [Quantity("0 [m]")]
        return d

    dA = disp(an3, "LC2P_INLET_END_Uz0", NS["SOLID_INLET_END"])
    dB = disp(an3, "LC2P_OUTLET_END_Uz0", NS["SOLID_OUTLET_END"])
    no3 = an3.AddNodalOrientation()
    no3.Name = "LC2P_HOOP_3NODES_MIDSPAN_Utheta0_orientation_CS_DUCT_CYL"
    no3.Location = NS["NS_LC2_HOOP_3NODES_MIDSPAN_OUTER"]
    no3.CoordinateSystem = cs
    nd3 = an3.AddNodalDisplacement()
    nd3.Name = "LC2P_HOOP_3NODES_MIDSPAN_Utheta0"
    nd3.Location = NS["NS_LC2_HOOP_3NODES_MIDSPAN_OUTER"]
    nd3.YComponent.Output.DiscreteValues = [Quantity("0 [m]")]
    pr = an3.AddPressure()
    pr.Name = "LC2P_P_uniform_443.41Pa_gauge_ACTIVE"
    pr.Location = NS["SOLID_INNER_INTERFACE"]
    pr.Magnitude.Output.DiscreteValues = [Quantity("443.41 [Pa]")]
    S["LC2P_definition"] = {
        "pressure": "uniform 443.41 Pa gauge (= CFD wall static pressure at the first station, maximum of the CFD wall distribution) "
                    "on SOLID_INNER_INTERFACE, normal to the bore (pushes outward). Differential internal-external pressure: the "
                    "outlet is at 0 Pa gauge and the outside of the duct at ambient, so no atmospheric absolute pressure is applied.",
        "why_uniform": "upper bound of the CFD distribution p(z) = 407.36-681.55 z <= 443.41 Pa; the model is linear, so the "
                       "pressure contribution scales with p and the uniform maximum bounds the effect of the real distribution",
        "restraints": "identical to LC2", "temperature": "identical CFD import", "states": {
            "pressure": str(pr.ObjectState), "inlet": str(dA.ObjectState), "outlet": str(dB.ObjectState),
            "hoop": str(nd3.ObjectState), "orientation": str(no3.ObjectState), "import": str(ibt3.ObjectState)}}
    stt = an3.AnalysisSettings
    S.setdefault("settings_before", {})["LC2P"] = dict((k, str(T("LC2P " + k, lambda kk=k: getattr(stt, kk))))
                                                       for k in ("LargeDeflection", "NumberOfSteps", "SolverType", "WeakSprings", "InertiaRelief"))
    bad = [(o.Name, str(o.ObjectState)) for o in walk(an3)
           if any(b in str(o.ObjectState) for b in ("UnderDefined", "Error", "SolveFailed", "LicenseConflict"))]
    chk("LC2P: no under-defined / error objects", not bad, "none", bad)
    p3 = os.path.join(PRE_IN, "LC2P_presolve_ds.dat")
    an3.WriteInputFile(p3)
    c3 = scan_ds(p3)
    DS["LC2P"] = c3
    S.setdefault("presolve_input", {})["LC2P"] = public(c3)
    for key in ("nblock", "eblock", "bf", "material"):
        chk("LC2P input vs LC2 input: identical %s section" % key, same(c3, DS["LC2"], key), "identical",
            "identical" if same(c3, DS["LC2"], key) else "DIFFERENT")
    chk("LC2P input: same resolved constraints as LC2", [c[:7] for c in c3["constraint_set"]] == [c[:7] for c in DS["LC2"]["constraint_set"]],
        DS["LC2"]["constraint_set"], c3["constraint_set"])
    chk("LC2P input: pressure 443.41 Pa present", c3["has_443.41"], "443.41 in input", c3["pressure_lines"][:12])
    chk("LC2 input: no pressure (thermal only)", not DS["LC2"]["has_443.41"], "no 443.41", DS["LC2"]["has_443.41"])
    chk("LC1 input: no pressure (thermal only)", not DS["LC1"]["has_443.41"], "no 443.41", DS["LC1"]["has_443.41"])
    dump()
    failed = [c for c in PRE["checks"] if not c["pass"]]
    PRE["gate"] = "PASS" if not failed else "FAIL (%d)" % len(failed)
    dump()
    if failed:
        raise Exception("PRE-SOLVE GATE FAILED - nothing solved: %s" % [c["check"] for c in failed])
    W("PRE-SOLVE GATE PASS (%d checks)" % len(PRE["checks"]))

    # ========================================================================================== 3. solver setting
    for tag, an in CASES:
        T("%s solver type -> Direct" % tag, lambda aa=an: setattr(aa.AnalysisSettings, "SolverType", SolverType.Direct), critical=True)
        S.setdefault("solver_setting", {})[tag] = str(an.AnalysisSettings.SolverType)

    # ========================================================================================== 4. results objects
    snip_txt = open(SNIP, "r").read()
    RES = {}

    def add_results(tag, an, bcs):
        sol = an.Solution
        R = []

        def add(kind, name, fn):
            o = T("%s add %s" % (tag, name), fn)
            if o is not None:
                o.Name = "%s_%s" % (tag, name)
                R.append((kind, name, o))
            return o

        add("res", "Total_Deformation", lambda: sol.AddTotalDeformation())
        o = add("res", "Axial_Deformation_Uz_global", lambda: sol.AddDirectionalDeformation())
        if o is not None:
            o.NormalOrientation = NormalOrientationType.ZAxis
        o = add("res", "Radial_Deformation_Ur_CS_DUCT_CYL", lambda: sol.AddDirectionalDeformation())
        if o is not None:
            o.CoordinateSystem = cs
            o.NormalOrientation = NormalOrientationType.XAxis
        add("res", "Equivalent_Stress_averaged", lambda: sol.AddEquivalentStress())
        o = add("res", "Equivalent_Stress_UNaveraged", lambda: sol.AddEquivalentStress())
        if o is not None:
            T(tag + " unaveraged", lambda: setattr(o, "DisplayOption", ResultAveragingType.Unaveraged))
        add("res", "Maximum_Principal_Stress", lambda: sol.AddMaximumPrincipalStress())
        add("res", "Minimum_Principal_Stress", lambda: sol.AddMinimumPrincipalStress())
        o = add("res", "Axial_Stress_Sz_global", lambda: sol.AddNormalStress())
        if o is not None:
            o.NormalOrientation = NormalOrientationType.ZAxis
        o = add("res", "Hoop_Stress_Stheta_CS_DUCT_CYL", lambda: sol.AddNormalStress())
        if o is not None:
            o.CoordinateSystem = cs
            o.NormalOrientation = NormalOrientationType.YAxis
        o = add("res", "Radial_Stress_Sr_CS_DUCT_CYL", lambda: sol.AddNormalStress())
        if o is not None:
            o.CoordinateSystem = cs
            o.NormalOrientation = NormalOrientationType.XAxis
        add("res", "Equivalent_Elastic_Strain", lambda: sol.AddEquivalentElasticStrain())
        add("res", "Structural_Error", lambda: sol.AddStructuralError())
        add("res", "Structural_Temperature", lambda: sol.AddStructuralTemperature())
        for bname, bobj in bcs:
            for kind, lab, adder in (("fr", "Force_Reaction_", lambda: sol.AddForceReaction()),
                                     ("mr", "Moment_Reaction_", lambda: sol.AddMomentReaction())):
                pb = add(kind, lab + bname, adder)
                if pb is None:
                    continue
                ok = True
                try:
                    pb.BoundaryConditionSelection = bobj
                    W("OK   %s %s%s scoped to %s" % (tag, lab, bname, bobj.Name))
                except Exception as e:
                    ok = False
                    W("NOTE %s %s%s cannot be scoped to %s (%s) - probe deleted; reactions from the APDL snippet"
                      % (tag, lab, bname, bobj.Name, str(e)[:200]))
                if ok and "UnderDefined" in str(pb.ObjectState):
                    ok = False
                    W("NOTE %s %s%s under-defined after scoping - probe deleted" % (tag, lab, bname))
                if not ok:
                    R.pop()
                    pb.Delete()
                    S.setdefault("probes_not_possible", []).append("%s %s%s" % (tag, lab, bname))
                    continue
                if kind == "mr":
                    T("%s MR summation about CS origin" % tag,
                      lambda: setattr(pb, "Summation", System.Enum.Parse(MomentsAtSummationPointType, "OrientationSystem")))
        sn = T("%s add APDL snippet" % tag, lambda: sol.AddCommandSnippet())
        if sn is not None:
            sn.Name = "%s_S7B_POST_APDL_reactions_nodal_table" % tag
            T("%s snippet input" % tag, lambda: setattr(sn, "Input", snip_txt), critical=True)
        return R

    def bc(an, name):
        return [o for o in walk(an) if o.Name == name][0]

    RES["LC1"] = add_results("LC1", an1, [("LC1_SUPPORT_3NODES_DirectFE", bc(an1, "LC1_SUPPORT_3NODES_Utheta0_Uz0"))])
    RES["LC2"] = add_results("LC2", an2, [("LC2_INLET_END", bc(an2, "LC2_INLET_END_Uz0")),
                                          ("LC2_OUTLET_END", bc(an2, "LC2_OUTLET_END_Uz0")),
                                          ("LC2_HOOP_3NODES_DirectFE", bc(an2, "LC2_HOOP_3NODES_MIDSPAN_Utheta0"))])
    RES["LC2P"] = add_results("LC2P", an3, [("LC2P_INLET_END", dA), ("LC2P_OUTLET_END", dB),
                                            ("LC2P_HOOP_3NODES_DirectFE", nd3)])
    # record of the exact solver input (after the solver-type change and the snippets)
    for tag, an in CASES:
        p = os.path.join(CASEDIR[tag], "Solver_Output", "%s_solve_input_ds.dat" % tag)
        T("%s write final input" % tag, lambda aa=an, pp=p: aa.WriteInputFile(pp))
        try:
            fin = scan_ds(p)
            S.setdefault("final_input", {})[tag] = {"eqsl": [x for x in fin["misc"] if x.startswith("eqsl")],
                                                    "same_bf_as_presolve": same(fin, DS[tag], "bf"),
                                                    "same_constraints_as_presolve": fin["constraint_set"] == DS[tag]["constraint_set"],
                                                    "same_material_as_presolve": same(fin, DS[tag], "material")}
        except Exception as e:
            S.setdefault("final_input", {})[tag] = "scan failed %s" % e
    dump()

    # ========================================================================================== 5. solve + post
    def graphics_setup():
        for lab, fn in (("true scale", lambda: setattr(Graphics.ViewOptions.ResultPreference, "DeformationScaling",
                                                       System.Enum.Parse(DeformationScaling, "True"))),
                        ("scale 1", lambda: setattr(Graphics.ViewOptions.ResultPreference, "DeformationScaleMultiplier", 1.0))):
            T("graphics " + lab, fn)
        S["graphics_deformation_scaling"] = str(T("graphics readback", lambda: (
            Graphics.ViewOptions.ResultPreference.DeformationScaling,
            Graphics.ViewOptions.ResultPreference.DeformationScaleMultiplier)))

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

    def image(obj, fname):
        out = []
        for view, fn in (("iso", lambda: Graphics.Camera.SetSpecificViewOrientation(ViewOrientationType.Iso)),
                         ("side", lambda: Graphics.Camera.SetSpecificViewOrientation(ViewOrientationType.Right))):
            p = os.path.join(FIG, "%s_%s.png" % (fname, view))
            ok = T("image %s %s" % (fname, view), lambda: (obj.Activate(), fn(), Graphics.Camera.SetFit(),
                                                             Graphics.ExportImage(p, GraphicsImageExportFormat.PNG, IMG)
                                                             if IMG is not None else Graphics.ExportImage(p, GraphicsImageExportFormat.PNG)))
            if ok is not None and os.path.isfile(p):
                out.append(p)
        return out

    def copy_solver_files(tag, an):
        wd = str(an.WorkingDir)
        dst = os.path.join(CASEDIR[tag], "Solver_Output")
        got = []
        names = os.listdir(wd) if os.path.isdir(wd) else []
        S["cases"][tag]["working_dir"] = wd
        S["cases"][tag]["working_dir_files"] = sorted(names)
        for n in names:
            if n.startswith("s7b_") or n in ("solve.out", "file.err", "file.mntr", "file.BCS", "file.DSP"):
                shutil.copy2(os.path.join(wd, n), os.path.join(dst, n))
                got.append(n)
        if not any(g.startswith("s7b_") for g in got):
            root = os.path.dirname(os.path.dirname(os.path.dirname(wd.rstrip("\\/"))))
            for dp, dn, fn in os.walk(root):
                if "s7b_totals.txt" in fn and (time.time() - os.path.getmtime(os.path.join(dp, "s7b_totals.txt"))) < 1800 \
                        and os.path.normcase(dp) != os.path.normcase(wd.rstrip("\\/")):
                    for n in fn:
                        if n.startswith("s7b_"):
                            shutil.copy2(os.path.join(dp, n), os.path.join(dst, n))
                            got.append(dp + "|" + n)
                    break
        S["cases"][tag]["solver_files_copied"] = got
        return got

    def solve_case(tag, an):
        C = S["cases"].setdefault(tag, {})
        n0 = len(list(ExtAPI.Application.Messages))
        t0 = time.time()
        W("SOLVING %s ..." % tag)
        T("%s solve" % tag, lambda: an.Solve(True))
        C["solve_wall_s"] = round(time.time() - t0, 1)
        C["solution_status"] = str(an.Solution.Status)
        C["solution_state"] = str(an.Solution.ObjectState)
        msgs = list(ExtAPI.Application.Messages)
        C["messages"] = [(str(m.Severity), m.DisplayString[:600]) for m in msgs[n0:]]
        W("%s solved: state %s status %s in %.0f s; messages %s" % (tag, C["solution_state"], C["solution_status"],
                                                                     C["solve_wall_s"], C["messages"]))
        dump()
        if C["solution_state"] in ("SolveFailed", "NotSolved", "UnderDefined", "Error", "Obsolete") or \
                (C["solution_state"] != "Solved" and "Done" not in C["solution_status"]):
            copy_solver_files(tag, an)
            dump()
            raise Exception("%s did not solve (state %s) - STOP" % (tag, C["solution_state"]))
        T("%s evaluate all results" % tag, lambda: an.Solution.EvaluateAllResults())
        C["results"] = {}
        for kind, name, o in RES[tag]:
            e = {"state": str(o.ObjectState)}
            if kind == "res":
                for k in ("Maximum", "Minimum", "Average"):
                    q = T("%s %s %s" % (tag, name, k), lambda kk=k: getattr(o, kk))
                    e[k] = str(q)
                    e[k + "_value"] = qval(q) if q is not None else None
                px = os.path.join(EXP, tag, "%s_%s.txt" % (tag, name))
                if "UNaveraged" in name:
                    pass
                elif T("%s export %s" % (tag, name), lambda: o.ExportToTextFile(px)) is not None or os.path.isfile(px):
                    e["export"] = px
            else:
                for k in ("XAxis", "YAxis", "ZAxis", "Total", "BoundaryConditionSelection", "LocationMethod", "Summation",
                          "SummationPoint"):
                    q = T("%s %s %s" % (tag, name, k), lambda kk=k: getattr(o, kk))
                    if q is not None:
                        e[k] = str(q)
                        e[k + "_value"] = qval(q) if hasattr(q, "Value") else None
            C["results"][name] = e
        dump()
        copy_solver_files(tag, an)
        dump()
        # images (from the solved Mechanical model)
        graphics_setup()
        C["images"] = []
        C["images"] += image(IBT[tag], "%s_00_Imported_Temperature" % tag)
        for kind, name, o in RES[tag]:
            if kind in ("res", "fr") and name not in ("Structural_Error",):
                C["images"] += image(o, "%s_%s" % (tag, name))
        dump()
        return C

    graphics_setup()
    solve_case("LC1", an1)
    solve_case("LC2", an2)
    solve_case("LC2P", an3)
    S["all_messages_end"] = [(str(m.Severity), m.DisplayString[:600]) for m in ExtAPI.Application.Messages]
    S["final_states"] = dict((tag, str(an.Solution.ObjectState)) for tag, an in CASES)
    dump()
    W("MECH-SOLVE-7B-DONE")
except Exception as e:
    import traceback
    W("FATAL %s" % e)
    W(traceback.format_exc())
    S["FATAL"] = str(e)
    dump()
