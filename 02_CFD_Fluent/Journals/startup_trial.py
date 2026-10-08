# Section 5B startup study - WHICH stabilisation is the smallest one that works?
# Not the production run. Reads the Section 5A setup case (configured, pre-iteration)
# and runs: flow-only startup, then energy switched on at first order, recording the
# peak solid temperature. Parameterised by environment variables.
import os, sys, math
sys.path.insert(0, "Journals")
from s5_common import *

TAG = os.environ.get("TRIAL_TAG", "A")
FLOW_IT = int(os.environ.get("TRIAL_FLOW_ITERS", "120"))
ENER_IT = int(os.environ.get("TRIAL_ENERGY_ITERS", "150"))
SOLID_F = float(os.environ.get("TRIAL_SOLID_FACTOR", "1.0"))
log("startup trial %s: flow-only %d it, then energy %d it, time_solid_scale_factor=%g"
    % (TAG, FLOW_IT, ENER_IT, SOLID_F))

solver.file.batch_options.confirm_overwrite = False
step("read setup case", lambda: solver.file.read_case(file_name="Baseline_Setup/baseline_setup.cas.h5"))
inc = solver.setup.materials.solid["inconel-718"]
step("Inconel density read-back", lambda: readv(inc, "density"))

S = solver.solution
tsm = S.run_calculation.pseudo_time_settings.time_step_method
step("pseudo-time settings before", lambda: tsm())
if abs(SOLID_F - 1.0) > 1e-12:
    step("time_solid_scale_factor = %g" % SOLID_F, lambda: setv(tsm, "time_solid_scale_factor", SOLID_F))
step("pseudo-time settings in force", lambda: tsm())

rf = S.monitor.report_files["s5a_monitors"]
mon = "Monitors/trial_%s.out" % TAG
step("redirect monitor file", lambda: setattr(rf, "file_name", mon))

ini = S.initialization
step("standard initialize", lambda: ini.standard_initialize())

# Stage 1: flow and turbulence only. The energy equation is not solved, so the whole
# domain stays at the 300 K initial temperature while the velocity field develops.
eq = S.controls.equations
step("energy equation OFF for flow-only startup", lambda: eq.__setitem__("temperature", False))
step("equations state", lambda: eq())
step("iterate flow-only %d" % FLOW_IT, lambda: S.run_calculation.iterate(iter_count=FLOW_IT))

# Stage 2: energy on, still first order.
step("energy equation ON", lambda: eq.__setitem__("temperature", True))
step("equations state", lambda: eq())
step("iterate with energy %d" % ENER_IT, lambda: S.run_calculation.iterate(iter_count=ENER_IT))

hdr, rows = read_report_file(mon)
res = {"tag": TAG, "flow_iters": FLOW_IT, "energy_iters": ENER_IT, "solid_factor": SOLID_F}
if hdr and rows:
    c = {n: i for i, n in enumerate(hdr)}
    Ts = [r[c["T_solid_max"]] for r in rows]
    Tw = [r[c["T_wall_max"]] for r in rows]
    qi = [r[c["q_interface"]] for r in rows]
    To = [r[c["T_out_bulk"]] for r in rows]
    ipk = max(range(len(Ts)), key=lambda i: Ts[i])
    res.update(peak_T_solid=Ts[ipk], peak_iter=rows[ipk][0], final_T_solid=Ts[-1],
               final_T_wall=Tw[-1], peak_q_interface=max(qi), final_q_interface=qi[-1],
               final_T_out=To[-1], rows=len(rows))
    log("TRIAL %s RESULT peak T_solid_max = %.2f K at iter %d; final %.2f K; "
        "overshoot %.2f K; peak q_interface %.1f W; final T_out %.3f K"
        % (TAG, Ts[ipk], rows[ipk][0], Ts[-1], Ts[ipk] - Ts[-1], max(qi), To[-1]))
else:
    log("TRIAL %s: monitor file unreadable (%s)" % (TAG, mon))

# --- cheap probe for the post-processing path: can cell zones become export surfaces?
step("create cell-zone surface fluid", lambda: solver.setup.cell_zone_conditions.fluid["fluid_domain"].create_surface(),
     critical=False)
step("create cell-zone surface solid", lambda: solver.setup.cell_zone_conditions.solid["solid_domain"].create_surface(),
     critical=False)
step("ascii export surfaces now", lambda: solver.file.export.ascii.surface_name_list.allowed_values(), critical=False)
step("residual.write probe", lambda: S.monitor.residual.write(file_name="Monitors/trial_%s_residuals.txt" % TAG),
     critical=False)

write_json("Monitors/trial_%s_result.json" % TAG, res)
flush_log("Logs/trial_%s_log.txt" % TAG)
print("TRIAL-DONE")
exit()
