# -*- coding: utf-8 -*-
# =====================================================================================================
# SECTION 8A - Mechanical LINEAR (EIGENVALUE) BUCKLING of the LC2 state (runs inside Mechanical via Workbench
# SendCommand from wb_buckling_8A.wbjn). RE-ANALYSIS 2026 - newly generated results, not recovered originals.
#
#  Works on the SaveAs copy Buckling/Workbench/Flow_Behavior_Thermal_Effects_Buckling_8A.wbpj (7B stays untouched).
#  1. PRE-SOLVE AUDIT (gate). Mesh/licence, CS, BC node ids, LC2 temperature import (byte-compare with the 7A export),
#     LC2 solver input vs the exact input solved in 7B (nodes, elements, BFBLOCK, material, resolved constraints),
#     the buckling analysis: pre-stress environment = LC2, no loads of its own, constraints inherited, settings.
#  2. Sensitivity pair LC2NS (NOT the LC2 definition): same import; U_z = 0 and U_theta = 0 on both end faces in
#     CS_DUCT_CYL (radial free, no lateral sway at the ends); + its buckling analysis.
#  3. LC2 is re-solved in this copy (the buckling link switches its Future Analysis to pre-stressed, which needs the
#     .esav/.emat files); the re-solved maxima and reactions are compared with 7B (must be identical).
#  4. Buckling: 6 modes; load multipliers; total/directional deformation per mode; APDL snippet (load factors +
#     corner-node mode shapes at full precision); images.
# Helper functions (logging, ds.dat parsing) are copied unchanged from mech_solve_7B.py (Section 7B).
# =====================================================================================================
import os, json, math, shutil, time, re
import System

BASE = r"<PROJECT_ROOT>"
S8 = os.path.join(BASE, "08_Structural_Analysis")
BK = os.path.join(S8, "Buckling")
AUD = os.path.join(BK, "Audits")
PRE_IN = os.path.join(AUD, "Presolve_Inputs")
MDIR = os.path.join(BK, "Mechanical")
FIG = os.path.join(BK, "figures", "Mechanical")
SNIP_B = os.path.join(BK, "Workbench", "Scripts", "s8a_buckle_snippet.inp")
REF7B_LC2 = os.path.join(S8, "LC2_Restrained", "Solver_Output", "LC2_solve_input_ds.dat")
MAPX = os.path.join(BASE, "07_Thermal_Analysis", "Mapping", "Mechanical_Export")
REF7B_VM = 605160873.3807464        # LC2 max von Mises (Mechanical, 7B)
REF7B_RZ = 548936.6137530317        # LC2 inlet-face reaction (7B)
for d in [AUD, PRE_IN, MDIR, FIG] + [os.path.join(MDIR, k) for k in ("LC2_prestress_resolve", "LC2_Linear_Buckling",
                                                                      "LC2NS_NoSway_Static", "LC2NS_Linear_Buckling")]:
    if not os.path.isdir(d):
        os.makedirs(d)
LOG = os.path.join(AUD, "mech_buckling_8A_log.txt")
PREF = os.path.join(AUD, "presolve_audit_8A.json")
SUMF = os.path.join(AUD, "mech_buckling_8A_summary.json")
lines = []
PRE = {"gate": "NOT RUN", "checks": [], "note": "RE-ANALYSIS 2026 - pre-solve audit of the 8A buckling model"}
S = {"cases": {}, "note": "RE-ANALYSIS 2026 - newly generated linear buckling results (not recovered originals)"}


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


def ptype(a):
    return str(a.AnalysisType)


def prestress_env(a):
    """name of the pre-stress environment of a buckling analysis (several API spellings tried)"""
    found = []
    try:
        for ic in a.InitialConditions:
            for attr in ("PreStressICEnvironment", "PreStressEnvironment", "Environment"):
                try:
                    v = getattr(ic, attr)
                    if v is not None:
                        found.append((attr, str(v.Name)))
                except Exception:
                    pass
            found.append(("ic_name", str(ic.Name)))
    except Exception as e:
        found.append(("error", str(e)[:200]))
    return found


try:
    W("=== SECTION 8A MECHANICAL LINEAR BUCKLING (RE-ANALYSIS 2026) ===")
    ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS
    NS = dict((n.Name, n) for n in Model.NamedSelections.Children)
    cs = [c for c in Model.CoordinateSystems.Children if c.Name == "CS_DUCT_CYL"][0]
    ALL = list(Model.Analyses)
    S["analyses_on_open"] = [(a.Name, ptype(a)) for a in ALL]
    W("analyses %s" % S["analyses_on_open"])
    an2 = [a for a in ALL if a.Name == "LC2_Axially_Restrained"][0]
    known = ("LC1_Free_Expansion", "LC2_Axially_Restrained", "LC2P_Restrained_Thermal_Plus_Pressure")
    new = [a for a in ALL if a.Name not in known]
    bucks = [a for a in new if "Buckl" in ptype(a)]
    statics = [a for a in new if "Static" in ptype(a)]
    W("new analyses: buckling %s static %s" % ([a.Name for a in bucks], [a.Name for a in statics]))
    if len(bucks) < 1:
        raise Exception("no buckling analysis found - Workbench link not created")
    # order of creation in the journal: LC2 buckling first, then the NS static, then the NS buckling
    bk2 = bucks[0]
    ns = statics[0] if statics else None
    bkn = bucks[1] if len(bucks) > 1 else None
    bk2.Name = "LC2_Linear_Buckling"
    if ns is not None:
        ns.Name = "LC2NS_NoSway_Static_SENSITIVITY"
    if bkn is not None:
        bkn.Name = "LC2NS_Linear_Buckling_SENSITIVITY"
    S["prestress_links"] = {"LC2_Linear_Buckling": prestress_env(bk2),
                            "LC2NS_Linear_Buckling": prestress_env(bkn) if bkn is not None else None}
    W("prestress links %s" % S["prestress_links"])

    # ======================================================================================== 1. PRE-SOLVE AUDIT
    mesh = Model.Mesh
    chk("mesh: 108,252 nodes / 23,400 elements (unchanged since 7A)", int(mesh.Nodes) == 108252 and int(mesh.Elements) == 23400,
        "108252 / 23400", "%s / %s" % (mesh.Nodes, mesh.Elements))
    chk("licence: below the measured Student MAPDL limit (128,000 nodes)", int(mesh.Nodes) < 128000, "< 128,000", mesh.Nodes)
    chk("CS_DUCT_CYL fully defined, cylindrical, origin 0,0,0",
        "FullyDefined" in str(cs.ObjectState) and "Cylindrical" in str(cs.CoordinateSystemType)
        and all(abs(qval(getattr(cs, k))) < 1e-12 for k in ("OriginX", "OriginY", "OriginZ")),
        "FullyDefined / Cylindrical / (0,0,0)", "%s / %s" % (cs.ObjectState, cs.CoordinateSystemType))
    md = ExtAPI.DataModel.MeshDataByName(ExtAPI.DataModel.MeshDataNames[0])
    ids = sorted(list(NS["NS_LC2_HOOP_3NODES_MIDSPAN_OUTER"].Location.Ids))
    pos = [(i, round(math.hypot(md.NodeById(i).X, md.NodeById(i).Y), 9), round(md.NodeById(i).Z, 9)) for i in ids]
    chk("LC2 hoop nodes = 7A ids 25862/25874/25886 at r 20 mm, z 0.3 m", ids == [25862, 25874, 25886]
        and all(abs(p[1] - 0.02) < 1e-8 and abs(p[2] - 0.3) < 1e-8 for p in pos), [25862, 25874, 25886], pos)
    # LC2 temperature import unchanged
    ref7a = open(os.path.join(MAPX, "LC1_imported_body_temperature.txt"), "r").read()
    objs2 = walk(an2)
    ibt2 = [o for o in objs2 if o.Name == "Imported_Body_Temperature_CFD"][0]
    st0 = str(ibt2.ObjectState)
    if "Solved" not in st0 or "Not" in st0:
        T("LC2 re-import (same source and settings)", lambda: ibt2.ImportLoad(), critical=True)
    px = os.path.join(AUD, "presolve_LC2_imported_body_temperature_8A.txt")
    ibt2.ExportToTextFile(px)
    now = open(px, "r").read()
    chk("LC2: mapped temperature identical to the 7A export (thermal field unchanged)", now == ref7a, "byte-identical",
        "identical" if now == ref7a else "DIFFERENT")
    chk("LC2: environment (stress-free reference) temperature 300 K", abs(qK(an2.EnvironmentTemperature) - 300) < 1e-6,
        "300 K", an2.EnvironmentTemperature)
    bad = [(o.Name, str(o.ObjectState)) for o in objs2
           if any(b in str(o.ObjectState) for b in ("UnderDefined", "Error", "SolveFailed", "LicenseConflict"))
           and not getattr(o, "Suppressed", False)]
    chk("LC2: no under-defined / error objects", not bad, "none", bad)
    prs = [(o.Name, bool(o.Suppressed)) for o in objs2 if o.GetType().Name == "Pressure"]
    chk("LC2: pressure objects suppressed (thermal-only pre-stress)", all(s for (_, s) in prs), "all suppressed", prs)
    st2 = an2.AnalysisSettings
    info2 = {}
    for k in ("LargeDeflection", "SolverType", "WeakSprings", "InertiaRelief", "FutureAnalysis"):
        info2[k] = str(T("LC2 " + k, lambda kk=k: getattr(st2, kk)))
    S["LC2_settings"] = info2
    chk("LC2: small deflection, direct solver (as solved in 7B)", info2["LargeDeflection"] in ("False", "Off")
        and "Direct" in info2["SolverType"], "LargeDeflection off, Direct", info2)
    # LC2 solver input vs the input actually solved in 7B
    DS = {}
    p2 = os.path.join(PRE_IN, "LC2_presolve_8A_ds.dat")
    an2.WriteInputFile(p2)
    a = scan_ds(p2)
    b = scan_ds(REF7B_LC2)
    DS["LC2"] = a
    S["presolve_input_LC2"] = public(a)
    for key in ("nblock", "eblock", "bf", "material"):
        chk("LC2 input vs 7B solved LC2 input: identical %s section" % key, same(a, b, key), "identical",
            "identical" if same(a, b, key) else "DIFFERENT")
    chk("LC2 input vs 7B solved LC2 input: identical resolved constraints", a["constraint_set"] == b["constraint_set"],
        b["constraint_set"], a["constraint_set"])
    chk("LC2 input: U_z = 0 on 1,224 end-face nodes + 3 rotated mid-span nodes U_theta = 0, nothing else",
        [c[:4] for c in a["constraint_set"]] == sorted([("D", "uz", 0.0, 1224), ("D", "uy", 0.0, 3), ("NROT_csys12", "", 0.0, 3)]),
        "d uz (1224) + nrot csys12 (3) + d uy (3)", a["constraint_set"])
    chk("LC2 input: no weak springs, no extra elements, no pressure", not a["wsprings"] and not a["extra_eblocks"]
        and not a["has_443.41"], "none", (a["wsprings"], a["extra_eblocks"], a["has_443.41"]))
    S["LC2_input_misc"] = a["misc"]
    # buckling analysis (LC2 pre-stress)
    sb = bk2.AnalysisSettings
    T("LC2 buckling: 6 modes", lambda: setattr(sb, "MaximumModesToFind", 6), critical=True)
    T("LC2 buckling: exclude negative load multipliers",
      lambda: setattr(sb, "IncludeNegativeLoadMultiplier", System.Enum.Parse(IncludeNegativeLoadMultiplier, "No")))
    infob = {}
    for k in ("MaximumModesToFind", "IncludeNegativeLoadMultiplier", "SolverType", "KeepPreStressLoadPattern"):
        infob[k] = str(T("LC2 buckling " + k, lambda kk=k: getattr(sb, kk)))
    S["LC2_buckling_settings"] = infob
    objsb = walk(bk2)
    S["LC2_buckling_objects"] = [(o.Name, o.GetType().Name, str(o.ObjectState)) for o in objsb]
    loads_b = [o.Name for o in objsb if o.GetType().Name in ("Displacement", "FixedSupport", "Pressure", "Force",
                                                             "NodalDisplacement", "ThermalCondition", "ImportedBodyTemperature",
                                                             "RemoteDisplacement", "FrictionlessSupport", "CylindricalSupport")]
    chk("LC2 buckling: no loads or supports of its own (it inherits the LC2 pre-stress state and supports)", not loads_b,
        "none", loads_b)
    pl = S["prestress_links"]["LC2_Linear_Buckling"]
    chk("LC2 buckling: pre-stress environment = LC2_Axially_Restrained",
        any("LC2_Axially_Restrained" in v for (_, v) in pl) or any("LC2 Axially Restrained" in v for (_, v) in pl), "LC2", pl)
    badb = [(o.Name, str(o.ObjectState)) for o in objsb
            if any(x in str(o.ObjectState) for x in ("UnderDefined", "Error", "LicenseConflict"))]
    chk("LC2 buckling: no under-defined / error objects", not badb, "none", badb)
    dump()

    # ======================================================================================== 2. LC2NS sensitivity
    IBT = {"LC2": ibt2}
    if ns is not None:
        ns.EnvironmentTemperature = Quantity(300, "K")
        grp = [c for c in ns.Children if c.GetType().Name == "ImportedLoadGroup"]
        chk("LC2NS: External Data linked", len(grp) == 1, 1, len(grp))
        ibn = grp[0].AddImportedBodyTemperature()
        ibn.Name = "Imported_Body_Temperature_CFD"
        ibn.Location = NS["SOLID_DOMAIN"]
        ibn.MappingControl = MappingControlType.Manual
        ibn.Algorithm = System.Enum.Parse(MappingAlgorithm, "BucketVolume")
        ibn.Weighting = System.Enum.Parse(WeightingType, "ShapeFunctions")
        ibn.OutsideOption = System.Enum.Parse(MappingOutsideOption, "NearestNode")
        T("LC2NS import", lambda: ibn.ImportLoad(), critical=True)
        IBT["LC2NS"] = ibn
        pxn = os.path.join(AUD, "presolve_LC2NS_imported_body_temperature_8A.txt")
        ibn.ExportToTextFile(pxn)
        chk("LC2NS: mapped temperature identical to the 7A export", open(pxn, "r").read() == ref7a, "byte-identical",
            "identical" if open(pxn, "r").read() == ref7a else "DIFFERENT")
        dN = []
        for nm, loc in (("LC2NS_INLET_END_Uz0_Utheta0_CS_DUCT_CYL", NS["SOLID_INLET_END"]),
                        ("LC2NS_OUTLET_END_Uz0_Utheta0_CS_DUCT_CYL", NS["SOLID_OUTLET_END"])):
            d = ns.AddDisplacement()
            d.Name = nm
            d.Location = loc
            d.CoordinateSystem = cs
            d.YComponent.Output.DiscreteValues = [Quantity("0 [m]")]
            d.ZComponent.Output.DiscreteValues = [Quantity("0 [m]")]
            dN.append(d)
        T("LC2NS solver type -> Direct", lambda: setattr(ns.AnalysisSettings, "SolverType", SolverType.Direct))
        badn = [(o.Name, str(o.ObjectState)) for o in walk(ns)
                if any(x in str(o.ObjectState) for x in ("UnderDefined", "Error", "LicenseConflict"))]
        chk("LC2NS: no under-defined / error objects", not badn, "none", badn)
        pn = os.path.join(PRE_IN, "LC2NS_presolve_8A_ds.dat")
        ns.WriteInputFile(pn)
        c = scan_ds(pn)
        DS["LC2NS"] = c
        S["presolve_input_LC2NS"] = public(c)
        for key in ("nblock", "eblock", "bf", "material"):
            chk("LC2NS input vs LC2 input: identical %s section" % key, same(c, a, key), "identical",
                "identical" if same(c, a, key) else "DIFFERENT")
        tot = {}
        for e in c["constraint_set"]:
            k = (e[0], e[1])
            tot[k] = (tot.get(k, (0, 0))[0] + e[3], tot.get(k, (0, 0))[1] + e[4])
        uz_lc2 = [e for e in a["constraint_set"] if e[0] == "D" and e[1] == "uz"][0]
        chk("LC2NS input: the 1,224 end-face nodes rotated to csys 12 with U_theta = 0 and U_z = 0; nothing else",
            sorted(tot.keys()) == sorted([("D", "uy"), ("D", "uz"), ("NROT_csys12", "")])
            and all(v == (1224, uz_lc2[4]) for v in tot.values()),
            "uy, uz, nrot each on the 1224 LC2 end-face nodes (id sum %d)" % uz_lc2[4], c["constraint_set"])
        sbn = bkn.AnalysisSettings
        T("LC2NS buckling: 6 modes", lambda: setattr(sbn, "MaximumModesToFind", 6))
        T("LC2NS buckling: exclude negative load multipliers",
          lambda: setattr(sbn, "IncludeNegativeLoadMultiplier", System.Enum.Parse(IncludeNegativeLoadMultiplier, "No")))
        chk("LC2NS buckling: pre-stress environment = LC2NS",
            any("LC2NS" in v or "No-Sway" in v for (_, v) in S["prestress_links"]["LC2NS_Linear_Buckling"] or []), "LC2NS",
            S["prestress_links"]["LC2NS_Linear_Buckling"])
        dump()
    failed = [x for x in PRE["checks"] if not x["pass"]]
    PRE["gate"] = "PASS" if not failed else "FAIL (%d)" % len(failed)
    dump()
    if failed:
        raise Exception("PRE-SOLVE GATE FAILED - nothing solved: %s" % [x["check"] for x in failed])
    W("PRE-SOLVE GATE PASS (%d checks)" % len(PRE["checks"]))

    # ======================================================================================== 3. result objects
    snip = open(SNIP_B, "r").read()
    RES = {}

    def add_modes(tag, an):
        sol = an.Solution
        out = []
        for n in range(1, 7):
            o = T("%s mode %d total deformation" % (tag, n), lambda: sol.AddTotalDeformation())
            if o is None:
                continue
            o.Name = "%s_Mode_%d_Total_Deformation" % (tag, n)
            T("%s mode %d set" % (tag, n), lambda oo=o, nn=n: setattr(oo, "Mode", nn))
            out.append(("tot", n, o))
            if n <= 2:
                for ax, ori in (("X", NormalOrientationType.XAxis), ("Y", NormalOrientationType.YAxis)):
                    oo = T("%s mode %d dir %s" % (tag, n, ax), lambda: sol.AddDirectionalDeformation())
                    if oo is None:
                        continue
                    oo.Name = "%s_Mode_%d_Deformation_%s_global" % (tag, n, ax)
                    oo.NormalOrientation = ori
                    T("%s mode %d dir set" % (tag, n), lambda o3=oo, nn=n: setattr(o3, "Mode", nn))
                    out.append(("dir" + ax, n, oo))
        sn = T("%s snippet" % tag, lambda: sol.AddCommandSnippet())
        if sn is not None:
            sn.Name = "%s_S8A_POST_APDL_load_factors_mode_shapes" % tag
            T("%s snippet input" % tag, lambda: setattr(sn, "Input", snip), critical=True)
        return out

    RES["LC2_Linear_Buckling"] = add_modes("LC2BK", bk2)
    if bkn is not None:
        RES["LC2NS_Linear_Buckling"] = add_modes("LC2NSBK", bkn)
    # the buckling solver input (record of what MAPDL receives)
    for tag, an in (("LC2_Linear_Buckling", bk2), ("LC2NS_Linear_Buckling", bkn)):
        if an is None:
            continue
        pb = os.path.join(PRE_IN, "%s_presolve_8A_ds.dat" % tag)
        if T("%s write input" % tag, lambda aa=an, pp=pb: aa.WriteInputFile(pp)) is not None or os.path.isfile(pb):
            try:
                sc = scan_ds(pb)
                S.setdefault("buckling_input", {})[tag] = {
                    "n_nodes": sc["n_nodes"], "n_bf": sc["n_bf"], "constraint_set": sc["constraint_set"],
                    "misc": sc["misc"], "wsprings": sc["wsprings"],
                    "buckle_cmds": [l.strip() for l in read_lines(pb) if l.strip().lower().startswith(
                        ("antype", "bucopt", "mxpand", "pstres", "/solu", "solve", "resume", "file,", "eqsl"))][:40]}
            except Exception as e:
                S.setdefault("buckling_input", {})[tag] = "scan failed %s" % e
    dump()

    # ======================================================================================== 4. solve + post
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

    def image(obj, fname, views=(("iso", "Iso"), ("side_YZ", "Right"), ("top_XZ", "Top"))):
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
        if mode == "true":
            T("graphics true scale", lambda: setattr(Graphics.ViewOptions.ResultPreference, "DeformationScaling",
                                                     System.Enum.Parse(DeformationScaling, "True")))
            T("graphics multiplier 1", lambda: setattr(Graphics.ViewOptions.ResultPreference, "DeformationScaleMultiplier", 1.0))
        else:
            names = list(System.Enum.GetNames(DeformationScaling))
            W("DeformationScaling members %s" % names)
            pick = [n for n in names if n.lower().startswith("auto")]
            if pick:
                T("graphics %s scale (mode shapes)" % pick[0],
                  lambda: setattr(Graphics.ViewOptions.ResultPreference, "DeformationScaling", System.Enum.Parse(DeformationScaling, pick[0])))
        S.setdefault("graphics_scaling", []).append(str(T("scaling readback", lambda: (
            Graphics.ViewOptions.ResultPreference.DeformationScaling, Graphics.ViewOptions.ResultPreference.DeformationScaleMultiplier))))

    def copy_files(tag, an, prefixes):
        wd = str(an.WorkingDir)
        dst = os.path.join(MDIR, tag, "Solver_Output")
        if not os.path.isdir(dst):
            os.makedirs(dst)
        names = os.listdir(wd) if os.path.isdir(wd) else []
        got = []
        for n in names:
            if n.startswith(prefixes) or n in ("solve.out", "file0.err", "file.err", "ds.dat", "file.mntr"):
                shutil.copy2(os.path.join(wd, n), os.path.join(dst, n))
                got.append(n)
        C = S["cases"].setdefault(tag, {})
        C["working_dir"] = wd
        C["working_dir_files"] = sorted(names)
        C["copied"] = got
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
        C["messages"] = [(str(m.Severity), m.DisplayString[:800]) for m in list(ExtAPI.Application.Messages)[n0:]]
        W("%s: state %s status %s %.0f s messages %s" % (tag, C["solution_state"], C["solution_status"], C["solve_wall_s"],
                                                         C["messages"]))
        dump()
        return C["solution_state"] == "Solved" or "Done" in C["solution_status"]

    def check_static(tag, an, vm_name, fr_name):
        """compare the re-solved static state with 7B"""
        C = S["cases"][tag]
        T("%s evaluate" % tag, lambda: an.Solution.EvaluateAllResults())
        objs = walk(an.Solution)
        vm = [o for o in objs if o.Name == vm_name]
        fr = [o for o in objs if o.Name == fr_name]
        vmax = qval(vm[0].Maximum) if vm else None
        rz = qval(fr[0].ZAxis) if fr else None
        C["max_von_mises_Pa"] = vmax
        C["inlet_reaction_Z_N"] = rz
        return vmax, rz

    def buckling_post(tag, an):
        C = S["cases"][tag]
        T("%s evaluate" % tag, lambda: an.Solution.EvaluateAllResults())
        modes = []
        for kind, n, o in RES[tag]:
            e = {"kind": kind, "mode": n, "state": str(o.ObjectState)}
            for k in ("LoadMultiplier", "Maximum", "Minimum"):
                q = T("%s mode %d %s %s" % (tag, n, kind, k), lambda kk=k: getattr(o, kk))
                e[k] = str(q)
                e[k + "_value"] = qval(q) if hasattr(q, "Value") else (float(q) if q is not None and not hasattr(q, "Value") else None)
            modes.append(e)
        C["modes"] = modes
        copy_files(tag, an, ("s8a_",))
        dump()
        scaling("auto")
        C["images"] = []
        for kind, n, o in RES[tag]:
            if kind == "tot" and n <= 4:
                C["images"] += image(o, "%s_Mode_%d_Total_Deformation" % (tag, n))
            elif kind.startswith("dir") and n <= 2:
                C["images"] += image(o, "%s_Mode_%d_Deformation_%s" % (tag, n, kind[3:]), views=(("iso", "Iso"),))
        scaling("true")
        dump()

    # ---- LC2 pre-stress (re-solve in this copy) ----
    if not solve("LC2_prestress_resolve", an2):
        copy_files("LC2_prestress_resolve", an2, ("s7b_",))
        raise Exception("LC2 pre-stress solve failed - STOP")
    vmax, rz = check_static("LC2_prestress_resolve", an2, "LC2_Equivalent_Stress_averaged", "LC2_Force_Reaction_LC2_INLET_END")
    copy_files("LC2_prestress_resolve", an2, ("s7b_",))
    ok_same = vmax is not None and rz is not None and abs(vmax / REF7B_VM - 1) < 1e-7 and abs(rz / REF7B_RZ - 1) < 1e-7
    S["cases"]["LC2_prestress_resolve"]["identical_to_7B"] = {"vm": [vmax, REF7B_VM], "rz": [rz, REF7B_RZ], "pass": ok_same}
    W("LC2 re-solve vs 7B: vm %s vs %s, Rz %s vs %s -> %s" % (vmax, REF7B_VM, rz, REF7B_RZ, ok_same))
    dump()
    if not ok_same:
        raise Exception("re-solved LC2 differs from 7B - STOP (setup changed?)")
    # ---- LC2 linear buckling ----
    if not solve("LC2_Linear_Buckling", bk2):
        copy_files("LC2_Linear_Buckling", bk2, ("s8a_",))
        raise Exception("LC2 buckling solve failed - STOP (see messages)")
    buckling_post("LC2_Linear_Buckling", bk2)
    # ---- sensitivity pair ----
    if ns is not None and bkn is not None:
        if solve("LC2NS_NoSway_Static", ns):
            T("LC2NS evaluate", lambda: ns.Solution.EvaluateAllResults())
            sol = ns.Solution
            vmn = T("LC2NS add VM", lambda: sol.AddEquivalentStress())
            frn = T("LC2NS add reaction", lambda: sol.AddForceReaction())
            if frn is not None:
                T("LC2NS reaction scope", lambda: setattr(frn, "BoundaryConditionSelection", dN[0]))
            T("LC2NS evaluate 2", lambda: sol.EvaluateAllResults())
            S["cases"]["LC2NS_NoSway_Static"]["max_von_mises_Pa"] = qval(vmn.Maximum) if vmn is not None else None
            S["cases"]["LC2NS_NoSway_Static"]["inlet_reaction"] = [str(T("r", lambda: frn.XAxis)), str(T("r", lambda: frn.YAxis)),
                                                                  str(T("r", lambda: frn.ZAxis))] if frn is not None else None
            copy_files("LC2NS_NoSway_Static", ns, ("s7b_",))
            dump()
            if solve("LC2NS_Linear_Buckling", bkn):
                buckling_post("LC2NS_Linear_Buckling", bkn)
    S["all_messages_end"] = [(str(m.Severity), m.DisplayString[:500]) for m in ExtAPI.Application.Messages]
    S["final_states"] = [(a.Name, ptype(a), str(a.Solution.ObjectState)) for a in Model.Analyses]
    dump()
    W("MECH-BUCKLING-8A-DONE")
except Exception as e:
    import traceback
    W("FATAL %s" % e)
    W(traceback.format_exc())
    S["FATAL"] = str(e)
    dump()
