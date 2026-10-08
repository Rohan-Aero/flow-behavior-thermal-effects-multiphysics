# -*- coding: utf-8 -*-
# SECTION 9B-2 - diagnostic probe of the S3 copy (nothing saved, nothing solved). RE-ANALYSIS 2026.
import os, json
OUT = r"<PROJECT_ROOT>\10_Parametric_Study\Structural_Cases\Probe\mech_probe_s3.json"
R = {"steps": []}


def save():
    f = open(OUT, "w"); f.write(json.dumps(R, indent=1, default=str)); f.close()


def walk(o):
    out = []
    for c in o.Children:
        out.append(c); out.extend(walk(c))
    return out


def step(label, fn):
    try:
        r = fn()
        R["steps"].append([label, "OK", str(r)[:800]])
    except Exception as e:
        det = str(e)
        try:
            det += " | " + str(e.clsException.ToString())[:3000]
        except Exception:
            pass
        R["steps"].append([label, "FAIL", det[:3500]])
    save()


try:
    ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS
    R["analyses"] = [(a.Name, str(a.AnalysisType), str(a.Solution.ObjectState)) for a in Model.Analyses]
    for a in Model.Analyses:
        for o in walk(a):
            if o.GetType().Name in ("ImportedLoadGroup", "ImportedBodyTemperature"):
                R.setdefault("imported", []).append((a.Name, o.Name, o.GetType().Name, str(o.ObjectState)))
    ib1 = [o for o in walk(Model.Analyses[0]) if o.GetType().Name == "ImportedBodyTemperature"][0]
    for p in ("ExternalDataIdentifier", "Location", "MappingControl", "Algorithm", "Weighting", "OutsideOption", "SourceMinimum", "SourceMaximum", "ObjectState"):
        step("LC1 ibt %s" % p, lambda pp=p: getattr(ib1, pp))
    grp = ib1.Parent
    step("LC1 group type", lambda: grp.GetType().Name)
    step("LC1 group dir", lambda: [x for x in dir(grp) if not x.startswith("_")][:120])
    step("LC1 ibt ImportLoad", lambda: ib1.ImportLoad())
    step("LC1 group ImportLoad", lambda: grp.ImportLoad() if hasattr(grp, "ImportLoad") else "no method")
    step("messages", lambda: [(str(m.Severity), m.DisplayString[:400]) for m in ExtAPI.Application.Messages][-20:])
    R["DONE"] = True
    save()
except Exception as e:
    R["FATAL"] = str(e)
    save()
