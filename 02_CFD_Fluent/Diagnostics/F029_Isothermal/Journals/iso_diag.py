# ============================================================================
# Section 6B - F-029 DIAGNOSTIC: isothermal flow on the MEDIUM mesh (not part of the mesh study,
# not a parametric study, not used for any design result).
# Question: does SST on this mesh under-predict the friction factor even WITHOUT heating?
# The only intended difference from the official medium case: the energy equation is not solved,
# so the air stays at the uniform 300 K initial field (constant density 1.1767 kg/m3).
# Run from 06_Fluent_CFD/Diagnostics/F029_Isothermal:  fluent 3ddp -g -py -t4 -i Journals/iso_diag.py
# The medium case is READ ONLY (settings only; its data is never read); nothing is written outside
# this folder. RE-ANALYSIS 2026.
# ============================================================================
import os, sys, re, json
sys.path.insert(0, "Journals")
from s5_common import *
from s5_common import _close

TAG = os.environ.get("BASE_TAG", "iso")
STDOUT = "Logs/%s_stdout.txt" % TAG
TRN = "Logs/%s_transcript.trn" % TAG
MON = "Monitors/iso_monitors.out"
MED_CASE = "../../Case/baseline_medium_final.cas.h5"
FLOW_IT, CHUNK, MAX_IT, WINDOW = 150, 100, 3000, 200
RES_TARGET = {"continuity": 1e-4, "x-velocity": 1e-4, "y-velocity": 1e-4, "z-velocity": 1e-4, "k": 1e-4, "omega": 1e-4}

log("=" * 80)
log("SECTION 6B F-029 DIAGNOSTIC - ISOTHERMAL FLOW, MEDIUM MESH - RE-ANALYSIS 2026")
log("=" * 80)
solver.file.batch_options.confirm_overwrite = False
step("transcript", lambda: solver.file.start_transcript(file_name=TRN), critical=False)
step("read medium final CASE (settings only, data NOT read)", lambda: solver.file.read_case(file_name=MED_CASE))
step("mesh size_info", lambda: solver.mesh.size_info())
S = solver.solution
ds = S.methods.spatial_discretization.discretization_scheme
eq = S.controls.equations
M = solver.setup.models
inl = solver.setup.boundary_conditions.velocity_inlet["fluid_inlet"]
out = solver.setup.boundary_conditions.pressure_outlet["fluid_outlet"]
rf = S.monitor.report_files["s5a_monitors"]
step("monitor file -> %s" % MON, lambda: setattr(rf, "file_name", MON))
STARTUP = {"pressure": "second-order", "mom": "first-order-upwind", "k": "first-order-upwind",
           "omega": "first-order-upwind", "temperature": "first-order-upwind"}
FINAL = {"pressure": "second-order", "mom": "second-order-upwind", "k": "second-order-upwind",
         "omega": "second-order-upwind", "temperature": "second-order-upwind"}
for k, v in STARTUP.items():
    step("startup scheme %s -> %s" % (k, v), (lambda kk=k, vv=v: set_scheme(ds, kk, vv)))
step("energy equation NOT solved (isothermal diagnostic)", lambda: eq.__setitem__("temperature", False))

AUD = {}
for name, fn, exp in [
    ("viscous model", lambda: (M.viscous.model(), M.viscous.k_omega_model()), ("k-omega", "sst")),
    ("wall omega treatment", lambda: M.viscous.near_wall_treatment.wall_omega_treatment(), "correlation"),
    ("inlet velocity [m/s]", lambda: inl.momentum.velocity_magnitude.value(), 23.5),
    ("inlet temperature [K]", lambda: inl.thermal.temperature.value(), 300.0),
    ("inlet intensity [-]", lambda: readv(inl.turbulence, "turbulent_intensity"), 0.16 * 29957.0 ** (-0.125)),
    ("outlet gauge pressure [Pa]", lambda: out.momentum.gauge_pressure.value(), 0.0),
    ("equations solved", lambda: eq(), {"flow": True, "kw": True, "temperature": False}),
    ("p-v coupling", lambda: S.methods.p_v_coupling.flow_scheme(), "Coupled"),
    ("scheme mom (startup)", lambda: ds["mom"](), "first-order-upwind"),
]:
    try:
        got = fn()
        ok = _close(got, exp) if isinstance(exp, float) else (got == exp)
    except Exception as e:
        got, ok = "ERROR %s" % e, False
    AUD[name] = {"value": got, "expected": exp, "ok": bool(ok)}
    log("AUDIT %-4s %-30s %s" % ("ok" if ok else "FAIL", name, repr(got)[:90]))
write_json("Audit/iso_setup_audit.json", AUD)
if not all(v["ok"] for v in AUD.values()) or [f for f in FAIL if f.startswith("CRITICAL")]:
    log("ISO AUDIT FAILED - STOPPING")
    flush_log("Logs/%s_log.txt" % TAG)
    exit()

ini = S.initialization
step("standard initialize (300 K, w 23.5 m/s, 0 Pa)", lambda: ini.standard_initialize())


def last_residuals():
    best = (None, None)
    for path in (STDOUT, TRN):
        if not os.path.isfile(path):
            continue
        hdr, it_res = None, None
        with open(path, "r", errors="ignore") as fh:
            for l in fh:
                if "iter" in l and "continuity" in l and not l.lstrip().startswith(">>>"):
                    hdr = l.split()
                    continue
                if hdr is None:
                    continue
                m = re.match(r"^\s*(\d+)\s+(\d\.\d{4}e[-+]\d\d)", l)
                if m:
                    tok = l.split()
                    n = len(hdr) - 2
                    try:
                        vals = [float(x) for x in tok[1:1 + n]]
                    except ValueError:
                        continue
                    it_res = (int(tok[0]), dict(zip(hdr[1:1 + n], vals)))
        if it_res and (best[0] is None or it_res[0] > best[0]):
            best = it_res
    return best


S2 = [None]


def evaluate(tag):
    it, res = last_residuals()
    hdr, rows = read_report_file(MON)
    rows = [r for r in rows if S2[0] is None or r[0] >= S2[0]]
    ev = {"tag": tag, "iteration": it, "residuals": res, "checks": {}}
    if res is None or not hdr or len(rows) < WINDOW:
        ev["ready"] = False
        return False, ev
    c = {n: i for i, n in enumerate(hdr)}
    win = rows[-WINDOW:]
    ok = True
    for e_, t_ in RES_TARGET.items():
        v = res.get(e_)
        o = v is not None and v < t_
        ev["checks"]["residual " + e_] = {"value": v, "target": t_, "ok": o}
        ok &= o
    for name, vals, tol in (("rel drift dp_area", [r[c["p_in_area"]] - r[c["p_out_area"]] for r in win], 1e-3),
                            ("rel drift F_wall_z", [r[c["F_wall_z"]] for r in win], 1e-3),
                            ("rel drift mdot_out", [abs(r[c["mdot_out"]]) for r in win], 1e-4)):
        d = (max(vals) - min(vals)) / max(abs(sum(vals) / len(vals)), 1e-30)
        ev["checks"][name] = {"value": d, "target": tol, "ok": d < tol}
        ok &= d < tol
    lr = rows[-1]
    mi = abs(lr[c["mdot_in"]] + lr[c["mdot_out"]]) / lr[c["mdot_in"]]
    ev["checks"]["mass imbalance"] = {"value": mi, "target": 1e-4, "ok": mi < 1e-4}
    ok &= mi < 1e-4
    ev["ready"] = True
    ev["converged"] = bool(ok)
    return ok, ev


step("stage 1 first-order: iterate %d" % FLOW_IT, lambda: S.run_calculation.iterate(iter_count=FLOW_IT))
_h, _r = read_report_file(MON)
S2[0] = (_r[-1][0] + 1) if _r else None
for k, v in FINAL.items():
    step("final scheme %s -> %s" % (k, v), (lambda kk=k, vv=v: set_scheme(ds, kk, vv)))
EV = []
done, conv = 0, False
while done < MAX_IT:
    step("second-order: iterate %d" % CHUNK, lambda: S.run_calculation.iterate(iter_count=CHUNK))
    done += CHUNK
    ok, ev = evaluate("so+%d" % done)
    EV.append(ev)
    log("EVAL iter %s: %s" % (ev.get("iteration"), "CONVERGED" if ok else ("not yet" if ev.get("ready") else "not evaluable")))
    write_json("Audit/iso_convergence_evaluations.json", EV)
    if ok:
        step("confirmation: iterate %d" % CHUNK, lambda: S.run_calculation.iterate(iter_count=CHUNK))
        done += CHUNK
        ok2, ev2 = evaluate("confirm+%d" % done)
        EV.append(ev2)
        log("CONFIRM iter %s: %s" % (ev2.get("iteration"), "HOLDS" if ok2 else "LOST"))
        if ok2:
            conv = True
            break
write_json("Audit/iso_convergence_evaluations.json", EV)
sfx = "final" if conv else "NOT_CONVERGED"
step("write case", lambda: solver.file.write_case(file_name="Case/iso_medium_%s.cas.h5" % sfx))
step("write data", lambda: solver.file.write_data(file_name="Data/iso_medium_%s.dat.h5" % sfx))
FR = solver.results.report.fluxes
step("flux report mass", lambda: FR.mass_flow(zones=["fluid_inlet", "fluid_outlet"], write_to_file=True,
                                              file_name="Audit/fluent_flux_mass.txt"), critical=False)
SI = solver.results.report.surface_integrals
step("SI p_area", lambda: SI.area_weighted_avg(surface_names=["fluid_inlet", "fluid_outlet"], report_of="pressure",
                                               write_to_file=True, file_name="Audit/fluent_si_p_area.txt"), critical=False)
step("SI T_mass", lambda: SI.mass_weighted_avg(surface_names=["fluid_inlet", "fluid_outlet"], report_of="temperature",
                                               write_to_file=True, file_name="Audit/fluent_si_T_mass.txt"), critical=False)
EXP = solver.file.export.ascii
WALLQ = ["x-coordinate", "y-coordinate", "z-coordinate", "face-area-magnitude", "temperature", "y-plus",
         "wall-shear", "z-wall-shear", "cell-wall-distance"]
BNDQ = ["x-coordinate", "y-coordinate", "z-coordinate", "face-area-magnitude", "pressure", "temperature", "density",
        "z-velocity"]
for fname, surfs, q in (("Exports/wall_interface.csv", ["fluid_solid_interface"], WALLQ),
                        ("Exports/boundary_inlet.csv", ["fluid_inlet"], BNDQ),
                        ("Exports/boundary_outlet.csv", ["fluid_outlet"], BNDQ)):
    step("export %s" % fname, (lambda f=fname, s_=surfs, qq=q: EXP(file_name=f, surface_name_list=s_, delimiter="comma",
                                                                  quantities=qq, location="cell-center")), critical=False)
write_json("Audit/iso_run_summary.json", {"converged": conv, "stage1_iters": FLOW_IT, "second_order_iters": done,
                                          "total_iters": FLOW_IT + done, "failures": FAIL,
                                          "final_eval": EV[-1] if EV else None})
log("ISO RUN COMPLETE converged=%s total=%d" % (conv, FLOW_IT + done))
flush_log("Logs/%s_log.txt" % TAG)
step("stop transcript", lambda: solver.file.stop_transcript(), critical=False)
print("ISO-DONE")
exit()
