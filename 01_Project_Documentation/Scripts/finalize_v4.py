# Python Script, API Version = V21
# v4: open saved model, resolve share topology + Parasolid export, render views
import os, json, traceback
BASE = r"<PROJECT_ROOT>\03_CAD_Geometry"
GC = os.path.join(BASE, "Geometry_Check")
msgs = []
def L(s): msgs.append(str(s))
res = {}
try:
    DocumentOpen.Execute(os.path.join(BASE, "Native_CAD", "heated_duct.scdocx"))
    part = GetRootPart()
    L("opened; bodies=%d groups=%d" % (len(part.Bodies), len(list(part.Groups))))
    L("groups: %s" % str([g.Name for g in part.Groups]))

    L("-- globals containing 'hare' or 'opolog' --")
    L(str(sorted([g for g in globals().keys() if ("hare" in g.lower() or "opolog" in g.lower())])))
    try:
        doc = GetActiveWindow().Document
        L("Document attrs with 'hare': %s" % str([a for a in dir(doc) if "hare" in a.lower()]))
        L("Part attrs with 'hare': %s" % str([a for a in dir(part) if "hare" in a.lower()]))
    except Exception as e:
        L("doc probe failed: %s" % e)
    try:
        L("ShareTopology globals: %s" % str([a for a in dir(ShareTopology) if not a.startswith("_")]))
    except Exception as e:
        L("no ShareTopology global: %s" % e)

    st = "unresolved"
    try:
        o = ShareTopologyOptions()
        r = ShareTopology.FindAndFix(Selection.Create(part.Bodies), o)
        st = "ShareTopology.FindAndFix OK: %s" % r
    except Exception as e1:
        try:
            o = ShareTopologyOptions()
            r = ShareTopology.Fix(Selection.Create(part.Bodies), o)
            st = "ShareTopology.Fix OK: %s" % r
        except Exception as e2:
            st = "FindAndFix:%s | Fix:%s" % (e1, e2)
    L("share topology attempt: %s" % st)
    res["share_topology"] = st

    L("-- exports --")
    exp = {}
    for sub, fn in [("Parasolid","heated_duct.x_t"),("Parasolid","heated_duct.x_b"),
                    ("Parasolid","heated_duct.xmt_txt"),("STEP","heated_duct.stp"),
                    ("Screenshots","reference_mesh_preview.stl")]:
        p = os.path.join(BASE, sub, fn)
        try:
            DocumentSave.Execute(p)
            exp[fn] = os.path.exists(p)
            L("  %-28s -> %s" % (fn, exp[fn]))
        except Exception as e:
            exp[fn] = "ERR: %s" % e
            L("  %-28s -> ERROR %s" % (fn, e))
    res["exports"] = exp
    DocumentSave.Execute(os.path.join(BASE, "Native_CAD", "heated_duct.scdocx"))
    L("=== v4 DONE ===")
except Exception as e:
    L("FATAL: %s" % e); L(traceback.format_exc())
f=open(os.path.join(GC,"v4_log.txt"),"w"); f.write("\n".join(msgs)); f.close()
f=open(os.path.join(GC,"v4_result.json"),"w"); f.write(json.dumps(res, indent=2)); f.close()
