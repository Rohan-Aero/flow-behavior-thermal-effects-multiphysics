# -*- coding: utf-8 -*-
# =====================================================================================================
# SECTION 9B-2 Parts K-M - S3 SUPPORT SENSITIVITY at the baseline design (runs inside Mechanical, sent by
# wb_s3_9B2_<mode>.wbjn). RE-ANALYSIS 2026 - newly generated model and results, not recovered originals.
#
# S3 (Section 9A SUPPORT_SCENARIOS.md): inlet end face U_z = U_theta = 0 on every node (CS_DUCT_CYL, radial free);
# outlet end face Remote Displacement, DEFORMABLE, pilot on the axis at z = 0.6 m, Ux = Uy = Uz = 0, rotations FREE;
# no mid-span hoop nodes. Same model as S1 (= LC2) and S2 otherwise: mesh B, P00 temperature field (same External Data,
# same Imported Body Temperature settings), T_ref 300 K, material, sparse direct solver; buckling as 8A (6 modes,
# positive multipliers, LC2-type pre-stress = the S3 static state).
# mode 'deck' : build the S3 static + buckling set-up, run the gate, write the solver input deck. NOTHING IS SOLVED.
# mode 'solve': repeat the gate (the deck must be unchanged), solve S3 static and S3 buckling, extract, copy tables.
# The copied LC1 / LC2 / LC2P analyses of the 7B project are not touched (they are the S1 baseline, solved in 7B).
# Helper functions copied unchanged from mech_param_9B2.py / mech_meshstudy_8B.py.
# =====================================================================================================
import os, json, math, shutil, time, re
import System

BASE = r"<PROJECT_ROOT>"
S8 = os.path.join(BASE, "08_Structural_Analysis")
SC = os.path.join(BASE, "10_Parametric_Study", "Structural_Cases")
try:
    CFG = json.load(open(os.path.join(SC, "Audits", "current_s3.json"), "r"))
except Exception as _e:
    _f = open(os.path.join(SC, "Audits", "mech_s3_bootstrap_error.txt"), "w")
    _f.write("current_s3.json could not be read: %s" % _e)
    _f.close()
    raise
MODE = CFG["mode"]
TAG = "S3_LC2_INTERMEDIATE"
CD = os.path.join(SC, TAG)
AUD = os.path.join(CD, "Audits")
PRE_IN = os.path.join(AUD, "Presolve_Inputs")
SOLV = os.path.join(CD, "Solver_Output")
FIG = os.path.join(CD, "Figures")
SNIP_S = os.path.join(S8, "Workbench", "Scripts", "s7b_post_snippet.inp")
SNIP_B = os.path.join(S8, "Buckling", "Workbench", "Scripts", "s8a_buckle_snippet.inp")
REF7B_LC2 = os.path.join(S8, "LC2_Restrained", "Solver_Output", "LC2_solve_input_ds.dat")
DECK = os.path.join(PRE_IN, "S3_presolve_ds.dat")
for d in [AUD, PRE_IN, SOLV, FIG, os.path.join(SOLV, "S3_STATIC"), os.path.join(SOLV, "S3_BUCKLING")]:
    if not os.path.isdir(d):
        os.makedirs(d)
LOG = os.path.join(AUD, "mech_S3_%s_log.txt" % MODE)
PREF = os.path.join(AUD, "presolve_audit_S3_%s.json" % MODE)
SUMF = os.path.join(AUD, "summary_S3_%s.json" % MODE)
lines = []
PRE = {"gate": "NOT RUN", "checks": [], "mode": MODE, "note": "RE-ANALYSIS 2026 - Section 9B-2 S3 pre-solve audit"}
S = {"mode": MODE, "cases": {}, "note": "RE-ANALYSIS 2026 - Section 9B-2 S3 support sensitivity (not recovered)"}
N_S1 = 548936.6138   # LC2 (= S1) end reaction of 7B [N]


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
    PRE["checks"].append({"check": name, "pass": bool(ok), "expected": str(expected), "found": str(found)[:900]})
    W("%s  %s | expected %s | found %s" % ("PASS" if ok else "**FAIL**", name, expected, str(found)[:300]))
    return ok


def qval(q):
    try:
        return float(q.Value)
    except Exception:
        return None


def qK(q):
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


def read_lines(p):
    f = open(p, "r")
    t = f.read()
    f.close()
    return t.splitlines()


def blocks(p):
    """NBLOCK / EBLOCK / BFBLOCK bodies, material lines, command lines (everything outside the block bodies)"""
    L = read_lines(p)
    low = [l.strip().lower() for l in L]
    out = {"nblock": [], "eblocks": [], "bf": [], "material": [], "commands": []}
    i = 0
    n = len(L)
    while i < n:
        l = low[i]
        if l.startswith("nblock,"):
            out["commands"].append(L[i])
            j = i + 2
            while j < n and low[j] != "-1":
                out["nblock"].append(L[j])
                j += 1
            i = j
            continue
        if l.startswith("eblock,"):
            out["commands"].append(L[i])
            blk = {"header": L[i], "fmt": L[i + 1], "lines": []}
            j = i + 2
            while j < n and low[j] != "-1":
                blk["lines"].append(L[j])
                j += 1
            out["eblocks"].append(blk)
            i = j
            continue
        if l.startswith("bfblock,"):
            out["commands"].append(L[i])
            j = i + 2
            while j < n and not low[j].startswith("bf,end"):
                out["bf"].append(L[j])
                j += 1
            i = j
            continue
        if l.startswith("cmblock,"):
            out["commands"].append(L[i])
            cnt = int(l.split(",")[3].split("!")[0])
            j = i + 2
            got = 0
            while got < cnt and j < n:
                got += len(L[j].split())
                j += 1
            i = j
            continue
        if l.startswith("mp,") or l.startswith("mpdata,") or l.startswith("mptemp,") or l.startswith("mpamod,") \
                or l.startswith("tref,") or l.startswith("tb,") or l.startswith("tbdata,"):
            if not l.startswith("mp,uvid"):
                out["material"].append(L[i].split("!")[0].strip())
        out["commands"].append(L[i])
        i += 1
    return out


def import_s3(ibt):
    """S3 deck runs 1-5 (Audits/Run*_S3_deck_FAIL_import): ImportedBodyTemperature.ImportLoad() raised a .NET
    NullReferenceException in this copy (the diagnostic probe, Structural_Cases/Probe/mech_probe_s3.json, showed it even for
    the unchanged LC1 object), while ImportedLoadGroup.ImportLoad() of the parent group works. The group call imports the
    same object with the same settings; the result is checked (state, exported values identical to the LC2 mapping)."""
    try:
        ibt.ImportLoad()
        W("OK   S3 import (object)")
        S["import_route"] = "ImportedBodyTemperature.ImportLoad"
    except Exception as e:
        W("NOTE object ImportLoad failed (%s); importing through the parent Imported Load group" % str(e)[:200])
        T("S3 import (group)", lambda: ibt.Parent.ImportLoad(), critical=True)
        S["import_route"] = "ImportedLoadGroup.ImportLoad (object call raised NullReferenceException)"
    W("S3 imported body temperature state %s" % ibt.ObjectState)


try:
    W("=== SECTION 9B-2 S3 SUPPORT SENSITIVITY, MODE %s (RE-ANALYSIS 2026) ===" % MODE)
    ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS
    NS = dict((n.Name, n) for n in Model.NamedSelections.Children)
    cs = [c for c in Model.CoordinateSystems.Children if c.Name == "CS_DUCT_CYL"][0]
    ALL = list(Model.Analyses)
    known = ("LC1_Free_Expansion", "LC2_Axially_Restrained", "LC2P_Restrained_Thermal_Plus_Pressure")
    an2 = [a for a in ALL if a.Name == "LC2_Axially_Restrained"][0]
    st = [a for a in ALL if "Static" in str(a.AnalysisType) and a.Name not in known]
    bks = [a for a in ALL if "Buckl" in str(a.AnalysisType)]
    S["analyses"] = [(a.Name, str(a.AnalysisType)) for a in ALL]
    chk("one new static (S3) and one buckling analysis in the copy", len(st) == 1 and len(bks) == 1, "1 / 1", S["analyses"])
    s3, bk = st[0], bks[0]
    s3.Name = "S3_LC2_Intermediate_Clamped_Pinned"
    bk.Name = "S3_Linear_Buckling"
    mesh = Model.Mesh
    nn, ne = int(mesh.Nodes), int(mesh.Elements)
    chk("mesh B unchanged (108,252 nodes / 23,400 SOLID186)", nn == 108252 and ne == 23400, "108252 / 23400", "%d / %d" % (nn, ne))
    md = ExtAPI.DataModel.MeshDataByName(ExtAPI.DataModel.MeshDataNames[0])
    allnodes = [(nd.Id, nd.X, nd.Y, nd.Z) for nd in md.Nodes]
    inlet = set(i for (i, x, y, z) in allnodes if abs(z) < 1e-7)
    outlet = set(i for (i, x, y, z) in allnodes if abs(z - 0.6) < 1e-7)
    chk("end faces: 612 inlet and 612 outlet nodes", len(inlet) == 612 and len(outlet) == 612, "612 / 612", "%d / %d" % (len(inlet), len(outlet)))

    # ------------------------------------------------------------------ 1. set-up (deck mode) / find (solve mode)
    s3objs = dict((o.Name, o) for o in walk(s3))
    if MODE == "deck":
        s3.EnvironmentTemperature = Quantity(300, "K")
        grp = [c for c in s3.Children if c.GetType().Name == "ImportedLoadGroup"]
        chk("S3: External Data linked (one imported load group)", len(grp) == 1, 1, len(grp))
        ibt = grp[0].AddImportedBodyTemperature()
        ibt.Name = "Imported_Body_Temperature_CFD"
        ibt.Location = NS["SOLID_DOMAIN"]
        ibt.MappingControl = MappingControlType.Manual
        ibt.Algorithm = System.Enum.Parse(MappingAlgorithm, "BucketVolume")
        ibt.Weighting = System.Enum.Parse(WeightingType, "ShapeFunctions")
        ibt.OutsideOption = System.Enum.Parse(MappingOutsideOption, "NearestNode")
        import_s3(ibt)
        d = s3.AddDisplacement()
        d.Name = "S3_INLET_END_Uz0_Utheta0_CS_DUCT_CYL"
        d.Location = NS["SOLID_INLET_END"]
        d.CoordinateSystem = cs
        d.YComponent.Output.DiscreteValues = [Quantity("0 [m]")]
        d.ZComponent.Output.DiscreteValues = [Quantity("0 [m]")]
        rd = s3.AddRemoteDisplacement()
        rd.Name = "S3_OUTLET_PILOT_Ux0_Uy0_Uz0_ROT_FREE_DEFORMABLE"
        rd.Location = NS["SOLID_OUTLET_END"]
        T("remote displacement: deformable", lambda: setattr(rd, "Behavior", LoadBehavior.Deformable), critical=True)
        T("pilot x", lambda: setattr(rd, "XCoordinate", Quantity(0.0, "m")), critical=True)
        T("pilot y", lambda: setattr(rd, "YCoordinate", Quantity(0.0, "m")), critical=True)
        T("pilot z", lambda: setattr(rd, "ZCoordinate", Quantity(0.6, "m")), critical=True)
        for k in ("XComponent", "YComponent", "ZComponent"):
            T("pilot %s = 0" % k, lambda kk=k: setattr(getattr(rd, kk).Output, "DiscreteValues", [Quantity("0 [m]")]), critical=True)
        for k in ("RotationX", "RotationY", "RotationZ"):
            T("pilot %s free" % k, lambda kk=k: setattr(getattr(rd, kk).Output, "DefinitionType", VariableDefinitionType.Free))
        T("S3 solver type -> Direct (sparse, as 7B)", lambda: setattr(s3.AnalysisSettings, "SolverType", SolverType.Direct))
        sol = s3.Solution
        for kind, name in (("AddEquivalentStress", "S3_Equivalent_Stress_averaged"), ("AddTotalDeformation", "S3_Total_Deformation"),
                           ("AddDirectionalDeformation", "S3_Axial_Deformation_Uz_global"),
                           ("AddDirectionalDeformation", "S3_Lateral_Deformation_Ux_global"),
                           ("AddDirectionalDeformation", "S3_Lateral_Deformation_Uy_global"),
                           ("AddNormalStress", "S3_Axial_Stress_Sz_global")):
            o = T("add %s" % name, lambda kk=kind: getattr(sol, kk)())
            if o is not None:
                o.Name = name
                if name.endswith("Uz_global") or name.endswith("Sz_global"):
                    T("%s Z" % name, lambda oo=o: setattr(oo, "NormalOrientation", NormalOrientationType.ZAxis))
                if name.endswith("Ux_global"):
                    T("%s X" % name, lambda oo=o: setattr(oo, "NormalOrientation", NormalOrientationType.XAxis))
                if name.endswith("Uy_global"):
                    T("%s Y" % name, lambda oo=o: setattr(oo, "NormalOrientation", NormalOrientationType.YAxis))
        for bc, nm in ((d, "S3_Force_Reaction_INLET_END"), (rd, "S3_Force_Reaction_OUTLET_PILOT")):
            fr = T("add %s" % nm, lambda: sol.AddForceReaction())
            if fr is not None:
                fr.Name = nm
                T("%s scope" % nm, lambda ff=fr, bb=bc: setattr(ff, "BoundaryConditionSelection", bb))
        for bc, nm in ((d, "S3_Moment_Reaction_INLET_END"), (rd, "S3_Moment_Reaction_OUTLET_PILOT")):
            mr = T("add %s" % nm, lambda: sol.AddMomentReaction())
            if mr is not None:
                mr.Name = nm
                T("%s scope" % nm, lambda mm=mr, bb=bc: setattr(mm, "BoundaryConditionSelection", bb))
        sn = T("S3 APDL post snippet (7B s7b_post_snippet, unchanged)", lambda: sol.AddCommandSnippet())
        if sn is not None:
            sn.Name = "S3_S7B_POST_APDL_nodal_table_reactions"
            T("snippet input", lambda: setattr(sn, "Input", open(SNIP_S, "r").read()), critical=True)
        sb = bk.AnalysisSettings
        T("buckling 6 modes", lambda: setattr(sb, "MaximumModesToFind", 6), critical=True)
        T("buckling positive multipliers only",
          lambda: setattr(sb, "IncludeNegativeLoadMultiplier", System.Enum.Parse(sb.IncludeNegativeLoadMultiplier.GetType(), "No")))
        for n in range(1, 7):
            o = T("mode %d result" % n, lambda: bk.Solution.AddTotalDeformation())
            if o is not None:
                o.Name = "S3_BK_Mode_%d_Total_Deformation" % n
                T("mode %d set" % n, lambda oo=o, nn_=n: setattr(oo, "Mode", nn_))
        snb = T("buckling snippet", lambda: bk.Solution.AddCommandSnippet())
        if snb is not None:
            snb.Name = "S3_S8A_POST_APDL_load_factors_mode_shapes"
            T("buckling snippet input", lambda: setattr(snb, "Input", open(SNIP_B, "r").read()), critical=True)
        s3objs = dict((o.Name, o) for o in walk(s3))
    ibt = s3objs["Imported_Body_Temperature_CFD"]
    d = s3objs["S3_INLET_END_Uz0_Utheta0_CS_DUCT_CYL"]
    rd = s3objs["S3_OUTLET_PILOT_Ux0_Uy0_Uz0_ROT_FREE_DEFORMABLE"]
    S["support_definition"] = {
        "inlet": {"name": d.Name, "scope": str(T("inlet scope", lambda: d.Location.Name)), "cs": str(d.CoordinateSystem.Name),
                  "X_radial": str(d.XComponent.Output.DefinitionType), "Y_theta": str(d.YComponent.Output.DefinitionType),
                  "Z_axial": str(d.ZComponent.Output.DefinitionType)},
        "outlet": {"name": rd.Name, "scope": str(T("outlet scope", lambda: rd.Location.Name)), "behavior": str(rd.Behavior),
                   "pilot_xyz_m": [qval(rd.XCoordinate), qval(rd.YCoordinate), qval(rd.ZCoordinate)],
                   "components": dict((k, str(T(k, lambda kk=k: getattr(rd, kk).Output.DefinitionType)))
                                      for k in ("XComponent", "YComponent", "ZComponent", "RotationX", "RotationY", "RotationZ"))}}
    W("support definition %s" % S["support_definition"])
    so = S["support_definition"]["outlet"]
    chk("S3 outlet: deformable remote displacement, pilot (0, 0, 0.6) m, Ux = Uy = Uz = 0, rotations free",
        "Deformable" in so["behavior"] and None not in so["pilot_xyz_m"]
        and max(abs(u - v) for u, v in zip(so["pilot_xyz_m"], (0.0, 0.0, 0.6))) < 1e-9
        and all("Free" not in so["components"][k] for k in ("XComponent", "YComponent", "ZComponent"))
        and all("Free" in so["components"][k] for k in ("RotationX", "RotationY", "RotationZ")), "as defined in 9A", so)
    si = S["support_definition"]["inlet"]
    chk("S3 inlet: displacement on SOLID_INLET_END in CS_DUCT_CYL, U_theta = U_z = 0, radial free",
        si["cs"] == "CS_DUCT_CYL" and "Free" in si["X_radial"] and "Free" not in si["Y_theta"] and "Free" not in si["Z_axial"],
        "CS_DUCT_CYL; X free, Y = Z = 0", si)
    chk("S3: no mid-span hoop nodes, no other supports",
        sorted(o.Name for o in walk(s3) if o.GetType().Name in ("Displacement", "RemoteDisplacement", "NodalDisplacement",
                                                               "FixedSupport", "NodalOrientation", "Pressure", "Force"))
        == sorted([d.Name, rd.Name]), [d.Name, rd.Name],
        [o.Name for o in walk(s3) if o.GetType().Name in ("Displacement", "RemoteDisplacement", "NodalDisplacement", "FixedSupport",
                                                          "NodalOrientation", "Pressure", "Force")])
    chk("S3: environment (reference) temperature 300 K", abs(qK(s3.EnvironmentTemperature) - 300.0) < 1e-6, "300 K", s3.EnvironmentTemperature)
    ref_settings = ("Manual", "BucketVolume", "ShapeFunctions", "NearestNode")
    chk("S3: import settings = 7A (Manual / BucketVolume / ShapeFunctions / NearestNode)",
        all(s in str(v) for s, v in zip(ref_settings, (ibt.MappingControl, ibt.Algorithm, ibt.Weighting, ibt.OutsideOption))),
        ref_settings, "%s / %s / %s / %s" % (ibt.MappingControl, ibt.Algorithm, ibt.Weighting, ibt.OutsideOption))
    if MODE == "solve":
        import_s3(ibt)
    p3 = os.path.join(AUD, "S3_imported_body_temperature_%s.txt" % MODE)
    p2 = os.path.join(AUD, "LC2_imported_body_temperature_in_S3_copy_%s.txt" % MODE)
    ibt.ExportToTextFile(p3)
    ib2 = [o for o in walk(an2) if o.Name == "Imported_Body_Temperature_CFD"][0]
    ib2.ExportToTextFile(p2)
    chk("S3: mapped temperature identical to the LC2 (S1) mapping", open(p3).read() == open(p2).read(), "identical",
        "identical" if open(p3).read() == open(p2).read() else "DIFFERENT")
    for tag, an in (("S3", s3), ("S3_BUCKLING", bk)):
        bad = [(o.Name, str(o.ObjectState)) for o in walk(an)
               if any(b in str(o.ObjectState) for b in ("UnderDefined", "Error", "LicenseConflict")) and not getattr(o, "Suppressed", False)]
        chk("%s: no under-defined / error objects" % tag, not bad, "none", bad)
    pl = []
    for ic in bk.InitialConditions:
        try:
            pl.append(str(ic.PreStressICEnvironment.Name))
        except Exception as e:
            pl.append("? %s" % str(e)[:80])
    chk("buckling: pre-stress environment = S3 static", s3.Name in pl, s3.Name, pl)
    own = [o.Name for o in walk(bk) if o.GetType().Name in ("Displacement", "FixedSupport", "Pressure", "Force", "RemoteDisplacement",
                                                          "NodalDisplacement", "ImportedBodyTemperature")]
    chk("buckling: no loads or supports of its own", not own, "none", own)

    # ------------------------------------------------------------------ 2. solver input deck
    deck = DECK if MODE == "deck" else os.path.join(PRE_IN, "S3_presolve_ds_solve_mode.dat")
    s3.WriteInputFile(deck)
    B = blocks(deck)
    R = blocks(REF7B_LC2)
    S["deck"] = {"file": deck, "nblock_lines": len(B["nblock"]), "eblocks": [(b["header"], len(b["lines"])) for b in B["eblocks"]],
                 "bf_lines": len(B["bf"]), "commands_file": os.path.join(AUD, "S3_deck_commands_%s.txt" % MODE)}
    f = open(S["deck"]["commands_file"], "w")
    f.write("\n".join(B["commands"]))
    f.close()
    chk("S3 input: SOLID186 element block identical to the 7B LC2 input", B["eblocks"][0]["lines"] == R["eblocks"][0]["lines"],
        "identical", "identical" if B["eblocks"][0]["lines"] == R["eblocks"][0]["lines"] else "DIFFERENT")
    chk("S3 input: all 7B mesh nodes present unchanged (a pilot node may be added)",
        set(R["nblock"]).issubset(set(B["nblock"])) and len(B["nblock"]) - len(R["nblock"]) in (0, 1),
        "7B NBLOCK subset, +0/1 node", "%d vs %d lines" % (len(B["nblock"]), len(R["nblock"])))
    chk("S3 input: nodal temperatures identical to the 7B LC2 input", B["bf"] == R["bf"], "identical",
        "identical" if B["bf"] == R["bf"] else "DIFFERENT")
    it = iter(B["material"])
    chk("S3 input: every 7B material line present, in order (E(T), alpha(T), nu, TREF)", all(any(x == y for y in it) for x in R["material"]),
        "7B material lines in order", "%d vs %d lines" % (len(B["material"]), len(R["material"])))
    kl = [l.split("!")[0].strip().lower().replace(" ", "") for l in B["commands"] if l.strip().lower().startswith("keyo,")]
    S["deck"]["remote_point_keyopts"] = kl
    chk("S3 input: MPC key options = bonded always (12,5), force-distributed / deformable (4,1), MPC (2,2); pilot not fixed (2,1), 6-DOF set",
        all(k in kl for k in ("keyo,cid,12,5", "keyo,cid,4,1", "keyo,cid,2,2", "keyo,tid,2,1", "keyo,tid,4,111111")), "5 key options", kl)
    chk("S3 input: pilot node carries U_x = U_y = U_z = 0 only (rotations free)",
        sorted(l.strip().lower() for l in B["commands"] if re.match(r"^d,\s*108253,", l.strip().lower())) == ["d,108253,ux,0.", "d,108253,uy,0.", "d,108253,uz,0."],
        "d,108253,ux/uy/uz,0.", [l for l in B["commands"] if re.match(r"^d,\s*108253,", l.strip().lower())])
    chk("S3 input: sparse direct solver", any(l.strip().lower().startswith("eqsl,sparse") for l in B["commands"]), "eqsl,sparse",
        [l for l in B["commands"] if l.strip().lower().startswith("eqsl")])
    # deck run 6 showed Mechanical 2026 R1 writes CONTA174 (8-node surface contact on the outlet faces), not CONTA175
    chk("S3 input: remote point written as MPC contact pair (TARGE170 pilot + CONTA174/175 surface elements)",
        any(re.match(r"^et,\s*\w+,\s*170", l.strip().lower()) for l in B["commands"])
        and any(re.match(r"^et,\s*\w+,\s*17[45]", l.strip().lower()) for l in B["commands"]), "et,..,170 and et,..,174/175",
        [l for l in B["commands"] if l.strip().lower().startswith("et,")])
    if MODE == "solve":
        D0 = blocks(DECK)
        same_deck = (D0["nblock"] == B["nblock"] and D0["bf"] == B["bf"] and [b["lines"] for b in D0["eblocks"]] == [b["lines"] for b in B["eblocks"]]
                     and [l for l in D0["commands"] if not l.startswith("/")] == [l for l in B["commands"] if not l.startswith("/")])
        chk("S3 input: identical to the deck written (and used for the B03 benchmark) in deck mode", same_deck, "identical",
            "identical" if same_deck else "DIFFERENT")
    failed = [c for c in PRE["checks"] if not c["pass"]]
    PRE["gate"] = "PASS" if not failed else "FAIL (%d)" % len(failed)
    dump()
    if failed:
        raise Exception("PRE-SOLVE GATE FAILED - nothing solved: %s" % [c["check"] for c in failed])
    W("PRE-SOLVE GATE PASS (%d checks)" % len(PRE["checks"]))
    if MODE == "deck":
        S["result"] = "DECK WRITTEN - NOT SOLVED (B03 toy benchmark next)"
        dump()
        W("MECH-S3-DECK-DONE (nothing solved)")
    else:
        # ------------------------------------------------------------------ 3. solve + extract
        def copy_files(tag, an, prefixes, sub):
            wd = str(an.WorkingDir)
            dst = os.path.join(SOLV, sub)
            got = []
            for n in (os.listdir(wd) if os.path.isdir(wd) else []):
                if n.startswith(prefixes) or n in ("solve.out", "file0.err", "file.err", "ds.dat"):
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
            RR = {}
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
                    if tn == "TotalDeformation" and "BK_Mode" in o.Name:
                        e["LoadMultiplier"] = str(T("LM %s" % o.Name, lambda: o.LoadMultiplier))
                else:
                    continue
                RR[o.Name] = e
            C["results"] = RR
            dump()

        solve("S3_STATIC", s3)
        extract("S3_STATIC", s3)
        copy_files("S3_STATIC", s3, ("s7b_",), "S3_STATIC")
        fr = S["cases"]["S3_STATIC"]["results"]
        rin = fr.get("S3_Force_Reaction_INLET_END", {}).get("ZAxis")
        rout = fr.get("S3_Force_Reaction_OUTLET_PILOT", {}).get("ZAxis")
        S["cases"]["S3_STATIC"]["axial_reaction_check"] = {"inlet_Fz_N": rin, "pilot_Fz_N": rout, "S1_N": N_S1}
        W("S3 axial reactions inlet %s pilot %s (S1 %s)" % (rin, rout, N_S1))
        solve("S3_BUCKLING", bk)
        extract("S3_BUCKLING", bk)
        copy_files("S3_BUCKLING", bk, ("s8a_",), "S3_BUCKLING")
        dump()
        try:
            st_ = Ansys.Mechanical.Graphics.GraphicsImageExportSettings()
            st_.CurrentGraphicsDisplay = False
            st_.Resolution = GraphicsResolutionType.EnhancedResolution
            st_.Background = GraphicsBackgroundType.White
            st_.Capture = GraphicsCaptureType.ImageAndLegend
            st_.Width = 1600
            st_.Height = 900
        except Exception:
            st_ = None
        imgs = []
        for oname, fname in (("S3_Equivalent_Stress_averaged", "S3_Equivalent_Stress_iso"), ("S3_BK_Mode_1_Total_Deformation", "S3_BK_Mode_1_iso"),
                             ("S3_BK_Mode_1_Total_Deformation", "S3_BK_Mode_1_side_YZ")):
            o = [x for x in walk(s3.Solution) + walk(bk.Solution) if x.Name == oname]
            if o:
                p = os.path.join(FIG, fname + ".png")
                view = ViewOrientationType.Right if fname.endswith("YZ") else ViewOrientationType.Iso
                ok = T("image %s" % fname, lambda: (o[0].Activate(), Graphics.Camera.SetSpecificViewOrientation(view), Graphics.Camera.SetFit(),
                                                   Graphics.ExportImage(p, GraphicsImageExportFormat.PNG, st_) if st_ is not None
                                                   else Graphics.ExportImage(p, GraphicsImageExportFormat.PNG)))
                if ok is not None and os.path.isfile(p):
                    imgs.append(p)
        S["images"] = imgs
        S["final_states"] = [(a.Name, str(a.Solution.ObjectState)) for a in Model.Analyses]
        dump()
        W("MECH-S3-SOLVE-DONE")
except Exception as e:
    import traceback
    W("FATAL %s" % e)
    W(traceback.format_exc())
    S["FATAL"] = str(e)
    dump()
