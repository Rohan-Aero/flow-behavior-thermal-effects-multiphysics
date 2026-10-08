# ============================================================================
# Section 9B-1 - PARAMETRIC CFD SOLVE (one case per Fluent session)
# Project : Flow Behavior and Thermal Effects in Multiphysics Systems
#           RE-ANALYSIS 2026 - no original internship artefact is reproduced here.
#
# Run from 10_Parametric_Study/CFD_Cases/<CASE>  (the driver run_param.ps1 does this):
#     set PARAM_CASE=<CASE>
#     fluent 3ddp -g -py -t4 -i ../Journals/solve_param.py
# Every relative path therefore lands inside the case folder. The official medium baseline
# (06_Fluent_CFD) is READ ONLY: its case file is read for its settings (never its data).
#
# Derived from 06_Fluent_CFD/Mesh_Independence/Fine/Journals/solve_fine.py (Section 6B), which was
# derived from Journals/solve_baseline.py (Section 5B). Identical numerics:
#   * physics source   : the converged P00 medium case's settings; the case mesh is loaded by Fluent's
#                        own mesh.replace (the medium mesh itself for C00/V/Q, the new mesh for T);
#                        the settings diff after replace must be ZERO
#   * ONE change       : the case's intended variable (param_cases.py) is then applied and read back;
#                        a second full settings diff must contain ONLY the allowed paths of that case,
#                        and every intended change must be present. Anything else STOPS the run
#   * same audit       : ~70 read-back rows, every common row compared with P00's own audit; rows of the
#                        intended variable must differ from P00 by exactly the intended value
#   * same strategy    : staged start 150 flow-only + 150 energy (first order), one switch to second
#                        order, identical convergence criteria and 100-iteration confirmation
#   * NEW validity gate: after every iterate call, every monitored fluid/solid temperature of every
#                        iteration so far must lie inside its property table (air 250-600 K, Inconel
#                        293.15-673.15 K) and the solver output must contain no limiter / reversed-flow
#                        message. A violation STOPS THE CASE; physics is never changed to rescue it
#   * extra export     : EnSight Gold solid node temperatures (the 7A mapping source) for 9B-2
# Nothing here tunes geometry, heat flux, inlet velocity, material properties, outlet pressure or
# the turbulence model toward P00, the screening estimate or any analytical answer.
# ============================================================================
import os, sys, math, re, json
sys.path.insert(0, "../Journals")
from s5_common import *
from s5_common import _close   # underscore names are not exported by import *
import param_cases as PC

CASE = os.environ.get("PARAM_CASE", "")
if CASE not in PC.CASES:
    print("S5B UNKNOWN CASE %r - STOP" % CASE)
    exit()
CDEF = PC.CASES[CASE]
P = PC.resolved(CASE)
TAG = CASE
STDOUT = "Logs/%s_stdout.txt" % TAG
TRN = "Logs/%s_transcript.trn" % TAG
MON = "Monitors/%s_monitors.out" % CASE
MED_CASE = "../../../06_Fluent_CFD/Case/baseline_medium_final.cas.h5"
MED_AUDIT = "../../../06_Fluent_CFD/Audit/setup_audit_%s.json"
MESH = P["MESH"]
EXPECT_CELLS, EXPECT_FLUID, EXPECT_SOLID = P["COUNTS"]
NZ, LEN = PC.NZ, PC.L
EXPECT_ZONES = {"cell_fluid": ["fluid_domain"], "cell_solid": ["solid_domain"],
                "velocity_inlet": ["fluid_inlet"], "pressure_outlet": ["fluid_outlet"],
                "wall": sorted(["fluid_solid_interface", "fluid_solid_interface-shadow", "heated_outer_wall",
                                "solid_inlet_end", "solid_outlet_end"]),
                "interior": []}

FLOW_IT = 150
ENERGY_IT = 150
CHUNK = 100
MAX_STAGE3 = 3000
WINDOW = 200

# ---- frozen baseline (02_Engineering_Calculations/baseline_parameters.json)
P_OP, T_IN = 101325.0, 300.0
V_IN, TI, INIT_W, QPP = P["V_IN"], P["TI"], P["INIT_W"], P["QPP"]
INC_RHO = 8190.0
AIR_T = [250.0, 300.0, 350.0, 400.0, 450.0, 500.0, 550.0, 600.0]
AIR_CP = [1006.0, 1007.0, 1009.0, 1014.0, 1021.0, 1030.0, 1040.0, 1051.0]
AIR_MU = [1.596e-5, 1.846e-5, 2.082e-5, 2.301e-5, 2.507e-5, 2.701e-5, 2.884e-5, 3.058e-5]
AIR_K = [0.02227, 0.02624, 0.03003, 0.03365, 0.03707, 0.04038, 0.04360, 0.04659]
INC_T = [293.15, 373.15, 473.15, 573.15, 673.15]
INC_CP = [460.0, 458.0, 468.0, 485.0, 501.0]
INC_K = [11.5, 12.1, 13.5, 15.2, 17.1]
AIR_RANGE = (AIR_T[0], AIR_T[-1])
INC_RANGE = (INC_T[0], INC_T[-1])

# ---- NR-03 / NR-04 and the additional engineering plateau criteria (unchanged from 5B)
RES_TARGET = {"continuity": 1e-4, "x-velocity": 1e-4, "y-velocity": 1e-4, "z-velocity": 1e-4,
              "k": 1e-4, "omega": 1e-4, "energy": 1e-6}
ABS_DRIFT_K = {"T_out_bulk": 0.1, "T_solid_max": 0.1, "T_wall_max": 0.1, "T_outer_max": 0.1}
REL_DRIFT = {"dp_area": 1e-3, "q_interface": 1e-3, "mdot_out": 1e-4}
MASS_TOL = 1e-4
ENERGY_TOL = 5e-3

log("=" * 80)
log("SECTION 9B-1 PARAMETRIC CFD SOLVE  case %s - RE-ANALYSIS 2026" % CASE)
log("variable: %s = %s %s" % (CDEF["variable"], CDEF["value"], CDEF["units"]))
log("resolved: V %.6f  TI %.9f  init w %.6f  q'' %.9f  mesh %s" % (V_IN, TI, INIT_W, QPP, MESH))
log("=" * 80)
solver.file.batch_options.confirm_overwrite = False
step("transcript", lambda: solver.file.start_transcript(file_name=TRN), critical=False)
STATUS = ["RUNNING"]


def finish_failed(status, why):
    STATUS[0] = status
    log("CASE STOPPED: %s - %s" % (status, why))
    for f in FAIL:
        log("   " + f)
    write_json("Audit/run_summary.json", {"case": CASE, "status": status, "why": why, "failures": FAIL,
                                          "validity_events": VALIDITY})
    flush_log("Logs/%s_log.txt" % TAG)
    step("stop transcript", lambda: solver.file.stop_transcript(), critical=False)
    print("S9B1-DONE %s" % status)
    exit()


VALIDITY = []

# ---------------------------------------------------------------------------
# 0. physics from the P00 medium case, mesh by replace
# ---------------------------------------------------------------------------
step("read P00 medium final CASE for its settings (data NOT read)", lambda: solver.file.read_case(file_name=MED_CASE))


def snap():
    return {"setup": solver.setup(), "solution": solver.solution()}


def sdiff(a, b, path=""):
    d = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                d.append((path + "/" + str(k), str(a.get(k, "<absent>"))[:200], str(b.get(k, "<absent>"))[:200]))
            else:
                d += sdiff(a[k], b[k], path + "/" + str(k))
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            d += sdiff(x, y, "%s[%d]" % (path, i))
    elif a != b:
        d.append((path, str(a)[:200], str(b)[:200]))
    return d


SNAP_MED = step("snapshot P00 settings", snap)
write_json("Audit/settings_state_P00_case.json", SNAP_MED)
step("REPLACE MESH -> %s (settings kept by Fluent)" % MESH, lambda: solver.mesh.replace(file_name=MESH))
step("mesh check", lambda: solver.mesh.check())
step("mesh size_info", lambda: solver.mesh.size_info())
step("mesh quality", lambda: solver.mesh.quality())
SNAP_REP = step("snapshot settings after replace", snap)
DIFF0 = sdiff(SNAP_MED, SNAP_REP) if (SNAP_MED and SNAP_REP) else [("snapshot", "failed", "failed")]
write_json("Audit/settings_diff_P00_vs_case_after_replace.json",
           [{"path": p, "P00": x, "case": y} for p, x, y in DIFF0])
log("SETTINGS DIFF P00 -> case after replace: %d differences" % len(DIFF0))
for p, x, y in DIFF0[:50]:
    log("  DIFF %s : %s -> %s" % (p, x, y))

G = solver.setup.general
M = solver.setup.models
air = solver.setup.materials.fluid["air"]
inc = solver.setup.materials.solid["inconel-718"]
BC = solver.setup.boundary_conditions
W = BC.wall
inl = BC.velocity_inlet["fluid_inlet"]
out = BC.pressure_outlet["fluid_outlet"]
S = solver.solution
ds = S.methods.spatial_discretization.discretization_scheme
RD = S.report_definitions
ini = S.initialization

# ---------------------------------------------------------------------------
# 0B. apply the ONE intended change of this case (read back), then the second diff gate
# ---------------------------------------------------------------------------
def set_velocity():
    inl.momentum.velocity_magnitude.value = V_IN
    got = inl.momentum.velocity_magnitude.value()
    if not _close(got, V_IN, 1e-12):
        raise RuntimeError("inlet velocity read back %r" % got)
    return got


def set_ti():
    return setv(inl.turbulence, "turbulent_intensity", TI)


def set_init_w():
    ini.defaults["z-velocity"] = INIT_W
    d = ini.defaults()
    ks = [k for k in d if "z-velocity" in k]
    if not ks or not _close(d[ks[0]], INIT_W, 1e-12):
        raise RuntimeError("init z-velocity read back %r" % d)
    return d[ks[0]]


def set_qpp():
    W["heated_outer_wall"].thermal.heat_flux.value = QPP
    got = W["heated_outer_wall"].thermal.heat_flux.value()
    if not _close(got, QPP, 1e-12):
        raise RuntimeError("heat flux read back %r" % got)
    return got


APPLIED = {}
if "V_IN" in CDEF["intended"]:
    APPLIED["V_IN"] = step("CASE CHANGE inlet velocity -> %.6f m/s" % V_IN, set_velocity)
    APPLIED["TI"] = step("DERIVED  turbulent intensity 0.16 Re^-1/8 -> %.9f" % TI, set_ti)
if "INIT_W" in CDEF["intended"]:      # not used by any approved case (the initial field is P00's in every case)
    APPLIED["INIT_W"] = step("init z-velocity -> %.6f m/s" % INIT_W, set_init_w)
if "QPP" in CDEF["intended"]:
    APPLIED["QPP"] = step("CASE CHANGE heated-wall heat flux -> %.9f W/m2" % QPP, set_qpp)

SNAP_CASE = step("snapshot case settings after the intended change", snap)
write_json("Audit/settings_state_%s_case.json" % CASE, SNAP_CASE)
DIFF1 = sdiff(SNAP_MED, SNAP_CASE) if (SNAP_MED and SNAP_CASE) else [("snapshot", "failed", "failed")]
UNEXPECTED = [d for d in DIFF1 if not any(re.match(pat, d[0]) for pat in CDEF["allowed"])]
MISSING = [pat for pat in CDEF["allowed"] if not any(re.match(pat, d[0]) for d in DIFF1)]
GATE = {"case": CASE, "intended": CDEF["intended"], "allowed_patterns": CDEF["allowed"],
        "diff_after_replace": len(DIFF0),
        "diff_after_change": [{"path": p, "P00": x, "case": y} for p, x, y in DIFF1],
        "unexpected": [{"path": p, "P00": x, "case": y} for p, x, y in UNEXPECTED],
        "intended_but_absent": MISSING, "applied_read_back": APPLIED,
        "passed": (len(DIFF0) == 0 and not UNEXPECTED and not MISSING)}
write_json("Audit/frozen_physics_gate.json", GATE)
log("FROZEN-PHYSICS GATE: %d diffs after change, %d unexpected, %d intended-but-absent -> %s"
    % (len(DIFF1), len(UNEXPECTED), len(MISSING), "PASS" if GATE["passed"] else "FAIL"))
for p, x, y in DIFF1[:20]:
    log("  CHANGE %s : %s -> %s" % (p, x, y))


def scan_mesh_text():
    """Cell count, minimum cell volume, orthogonal quality and mesh-check warnings, as printed by Fluent."""
    cells = minvol = None
    oq = None
    warn = []
    for path in (STDOUT, TRN):
        if not os.path.isfile(path):
            continue
        txt = open(path, "r", errors="ignore").read()
        q = re.findall(r"Minimum Orthogonal Quality\s*=\s*([-+0-9.eE]+)", txt)
        if q:
            oq = float(q[-1])
        blk = txt[txt.rfind("Checking mesh"):]
        blk = blk[:blk.find("Done.") + 5] if "Done." in blk else blk[:4000]
        warn = [l.strip() for l in blk.splitlines()
                if re.search(r"warning|error|invalid|negative|left-handed|skewed|degenerate", l, re.I)]
        if oq is not None:
            break
    for path in (STDOUT, TRN):
        if not os.path.isfile(path):
            continue
        txt = open(path, "r", errors="ignore").read()
        m = re.findall(r"Level\s+Cells\s+Faces\s+Nodes\s+Partitions\s*\n\s*0\s+(\d+)\s+(\d+)\s+(\d+)", txt)
        if m:
            cells = int(m[-1][0])
        v = re.findall(r"minimum volume \(m3\):\s*([-+0-9.eE]+)", txt)
        if v:
            minvol = float(v[-1])
        if cells is not None and minvol is not None:
            break
    return {"cells": cells, "min_volume_m3": minvol, "min_orthogonal_quality": oq, "mesh_check_warnings": warn}


MESHINFO = step("mesh size/volume as printed by Fluent", scan_mesh_text)


def scan_zone_ids():
    for path in (STDOUT, TRN):
        if os.path.isfile(path):
            ids = re.findall(r"Setting zone id of (\S+) to (\d+)\.", open(path, "r", errors="ignore").read())
            if ids:
                return {n: int(i) for n, i in ids}
    return {}


ZONE_IDS = step("zone ids as printed by Fluent's replace", scan_zone_ids, critical=False)
ZONES = {}
for kind in ("fluid", "solid"):
    ZONES["cell_" + kind] = sorted(getattr(solver.setup.cell_zone_conditions, kind).get_object_names())
for kind in ("velocity_inlet", "pressure_outlet", "wall", "interior"):
    ZONES[kind] = sorted(getattr(solver.setup.boundary_conditions, kind).get_object_names())
log("ZONES " + json.dumps(ZONES))
write_json("Audit/case_mesh_zones.json", {"zones": ZONES, "zone_ids_from_replace": ZONE_IDS,
                                          "mesh": MESHINFO, "mesh_file": MESH})

# ---------------------------------------------------------------------------
# 1. mandatory corrections (identical to 5B/6A/6B)
# ---------------------------------------------------------------------------
def fix_density():
    inc.density.option = "value"
    inc.density.value = INC_RHO
    got_opt = inc.density.option()
    got = inc.density.value()
    if got_opt != "value" or not _close(got, INC_RHO):
        raise RuntimeError("Inconel density read back as %r / %r" % (got_opt, got))
    return {"option": got_opt, "value_kg_m3": got}


step("1A Inconel 718 density = 8190 kg/m3 (read back)", fix_density)

STARTUP_SCHEMES = {"pressure": "second-order", "mom": "first-order-upwind", "k": "first-order-upwind",
                   "omega": "first-order-upwind", "temperature": "first-order-upwind"}
FINAL_SCHEMES = {"pressure": "second-order", "mom": "second-order-upwind", "k": "second-order-upwind",
                 "omega": "second-order-upwind", "temperature": "second-order-upwind"}
for k, v in STARTUP_SCHEMES.items():
    step("startup scheme %-12s -> %s" % (k, v), (lambda kk=k, vv=v: set_scheme(ds, kk, vv)))

# ---------------------------------------------------------------------------
# monitors - the 29 report definitions already exist in the P00 case; only the file moves
# ---------------------------------------------------------------------------
OLD = ["mdot_in", "mdot_out", "mass_imbalance", "q_heated_wall", "q_interface", "q_fluid_net",
       "p_in", "p_out", "T_out_bulk", "T_wall_max", "T_solid_max", "T_solid_mean", "v_out_max", "yplus_max"]
NEW = ["p_in_area", "p_out_area", "T_in_bulk", "T_outer_max", "T_outer_avg", "T_inner_avg", "yplus_min",
       "yplus_avg", "area_in", "T_fluid_max", "T_fluid_min", "T_solid_min", "q_ends", "q_net_all", "F_wall_z"]
ALLDEFS = OLD + NEW
rf = S.monitor.report_files["s5a_monitors"]
step("monitor file -> %s" % MON, lambda: setattr(rf, "file_name", MON))
step("monitor file report list (%d)" % len(ALLDEFS), lambda: setattr(rf, "report_defs", ALLDEFS))
step("monitor file state", lambda: rf())

# ---------------------------------------------------------------------------
# 2. SETUP AUDIT - read everything back; a single mismatch stops the run
# ---------------------------------------------------------------------------
INTENDED_ROWS = {}
if "V_IN" in CDEF["intended"]:
    INTENDED_ROWS = {"inlet velocity [m/s]": V_IN, "inlet turbulent intensity [-]": TI}
if "QPP" in CDEF["intended"]:
    INTENDED_ROWS = {"heated wall flux [W/m2]": QPP}


def pw_state(prop):
    return [(d["item"], d["value"]) for d in prop.piecewise_linear.data_points()]


def curve_ok(got, T, V):
    return len(got) == len(T) and all(_close(a, t, 1e-9) and _close(b, v, 1e-9)
                                      for (a, b), t, v in zip(got, T, V))


def audit(label, schemes_expected):
    rows = []

    def chk(name, fn, expect=None, info=False):
        try:
            got = fn()
            if info:
                ok = True
            elif isinstance(expect, float):
                ok = _close(got, expect)
            elif callable(expect):
                ok = bool(expect(got))
            else:
                ok = (got == expect)
        except Exception as e:
            got, ok = "ERROR %s" % e, False
        rows.append({"item": name, "value": got,
                     "expected": ("(recorded)" if info else (expect if not callable(expect) else "see check")),
                     "ok": ok})

    chk("fluent version", lambda: solver.get_fluent_version(), info=True)
    chk("solver type", lambda: G.solver.type(), "pressure-based")
    chk("time", lambda: G.solver.time(), "steady")
    chk("velocity formulation", lambda: G.solver.velocity_formulation(), "absolute")
    chk("operating pressure [Pa]", lambda: G.operating_conditions.operating_pressure(), P_OP)
    chk("gravity enabled", lambda: G.operating_conditions.gravity()["enable"], False)
    chk("energy equation", lambda: M.energy.enabled(), True)
    chk("energy: viscous dissipation", lambda: M.energy.viscous_dissipation(), info=True)
    chk("energy: pressure work", lambda: M.energy.pressure_work(), info=True)
    chk("energy: kinetic energy", lambda: M.energy.kinetic_energy(), info=True)
    chk("viscous model", lambda: M.viscous.model(), "k-omega")
    chk("k-omega variant", lambda: M.viscous.k_omega_model(), "sst")
    chk("SST wall omega treatment", lambda: M.viscous.near_wall_treatment.wall_omega_treatment(), info=True)
    chk("SST low-Re correction", lambda: M.viscous.k_omega.k_omega_low_re_correction(), info=True)
    chk("radiation model", lambda: M.radiation.model(), "none")
    chk("air density model", lambda: air.density.option(), "incompressible-ideal-gas")
    chk("air molecular weight", lambda: air.molecular_weight.value(), 28.966)
    chk("air cp model", lambda: air.specific_heat.option(), "piecewise-linear")
    chk("air cp curve = Incropera A.4", lambda: curve_ok(pw_state(air.specific_heat), AIR_T, AIR_CP), True)
    chk("air mu model", lambda: air.viscosity.option(), "piecewise-linear")
    chk("air mu curve = Incropera A.4", lambda: curve_ok(pw_state(air.viscosity), AIR_T, AIR_MU), True)
    chk("air k model", lambda: air.thermal_conductivity.option(), "piecewise-linear")
    chk("air k curve = Incropera A.4", lambda: curve_ok(pw_state(air.thermal_conductivity), AIR_T, AIR_K), True)
    chk("Inconel density option", lambda: inc.density.option(), "value")
    chk("Inconel density [kg/m3]", lambda: inc.density.value(), INC_RHO)
    chk("Inconel k model", lambda: inc.thermal_conductivity.option(), "piecewise-linear")
    chk("Inconel k curve = VDM 4127", lambda: curve_ok(pw_state(inc.thermal_conductivity), INC_T, INC_K), True)
    chk("Inconel cp model", lambda: inc.specific_heat.option(), "piecewise-linear")
    chk("Inconel cp curve = VDM 4127", lambda: curve_ok(pw_state(inc.specific_heat), INC_T, INC_CP), True)
    chk("fluid zone material", lambda: solver.setup.cell_zone_conditions.fluid["fluid_domain"].general.material(), "air")
    chk("solid zone material", lambda: solver.setup.cell_zone_conditions.solid["solid_domain"].general.material(), "inconel-718")
    chk("inlet velocity spec", lambda: inl.momentum.velocity_specification_method(), "Magnitude, Normal to Boundary")
    chk("inlet velocity [m/s]", lambda: inl.momentum.velocity_magnitude.value(), V_IN)
    chk("inlet temperature [K]", lambda: inl.thermal.temperature.value(), T_IN)
    chk("inlet turbulence spec", lambda: inl.turbulence.turbulence_specification(), "Intensity and Hydraulic Diameter")
    chk("inlet turbulent intensity [-]", lambda: readv(inl.turbulence, "turbulent_intensity"), TI)
    chk("inlet hydraulic diameter [m]", lambda: readv(inl.turbulence, "hydraulic_diameter"), 0.02)
    chk("outlet gauge pressure [Pa]", lambda: out.momentum.gauge_pressure.value(), 0.0)
    chk("outlet prevent reverse flow", lambda: out.momentum.prevent_reverse_flow(), True)
    chk("outlet backflow T branch active", lambda: out.thermal.backflow_total_temperature.is_active(), info=True)
    chk("heated wall condition", lambda: W["heated_outer_wall"].thermal.thermal_condition(), "Heat Flux")
    chk("heated wall flux [W/m2]", lambda: W["heated_outer_wall"].thermal.heat_flux.value(), QPP)
    chk("solid inlet end", lambda: (W["solid_inlet_end"].thermal.thermal_condition(),
                                    W["solid_inlet_end"].thermal.heat_flux.value()), ("Heat Flux", 0))
    chk("solid outlet end", lambda: (W["solid_outlet_end"].thermal.thermal_condition(),
                                     W["solid_outlet_end"].thermal.heat_flux.value()), ("Heat Flux", 0))
    chk("interface thermal coupling", lambda: W["fluid_solid_interface"].thermal.thermal_condition(), "Coupled")
    chk("interface shadow coupling", lambda: W["fluid_solid_interface-shadow"].thermal.thermal_condition(), "Coupled")
    chk("p-v coupling", lambda: S.methods.p_v_coupling.flow_scheme(), "Coupled")
    chk("gradient scheme", lambda: S.methods.spatial_discretization.gradient_scheme(), "least-square-cell-based")
    for k, v in schemes_expected.items():
        chk("scheme %s" % k, (lambda kk=k: ds[kk]()), v)
    chk("pseudo-time formulation", lambda: S.methods.pseudo_time_method.formulation.coupled_solver(), "global-time-step")
    chk("pseudo-time step settings", lambda: S.run_calculation.pseudo_time_settings.time_step_method(), info=True)
    chk("explicit pseudo relaxation", lambda: S.controls.pseudo_time_explicit_relaxation_factor(), info=True)
    chk("explicit p/mom under-relaxation", lambda: S.controls.p_v_controls(), info=True)
    chk("solution limits", lambda: S.controls.limits(), info=True)
    chk("equations solved", lambda: S.controls.equations(), info=True)
    n_common = len(rows)

    # --- Section 6A/6B additions (explicit expectations)
    chk("6A turbulence model = SST k-omega", lambda: (M.viscous.model(), M.viscous.k_omega_model()), ("k-omega", "sst"))
    chk("6A wall omega treatment = correlation", lambda: M.viscous.near_wall_treatment.wall_omega_treatment(),
        "correlation")
    chk("6A low-Re correction off", lambda: M.viscous.k_omega.k_omega_low_re_correction(), False)
    chk("6A energy extra terms off", lambda: (M.energy.viscous_dissipation(), M.energy.pressure_work(),
                                              M.energy.kinetic_energy()), (False, False, False))
    chk("6A mesh cells (printed by Fluent)", lambda: MESHINFO["cells"], EXPECT_CELLS)
    chk("6A minimum cell volume > 0 [m3]", lambda: MESHINFO["min_volume_m3"], lambda v: v is not None and v > 0)
    chk("6B minimum orthogonal quality > 0.1 (Fluent)", lambda: MESHINFO["min_orthogonal_quality"],
        lambda v: v is not None and v > 0.1)
    chk("6B mesh-check warnings / malformed cells", lambda: MESHINFO["mesh_check_warnings"], [])
    chk("6A zone names", lambda: ZONES, EXPECT_ZONES)
    chk("6A zone ids (Fluent replace output)", lambda: ZONE_IDS,
        {"fluid_domain": 2, "solid_domain": 3, "interior-fluid": 4, "interior-solid": 5, "fluid_inlet": 6,
         "fluid_outlet": 7, "fluid_solid_interface": 8, "heated_outer_wall": 9, "solid_inlet_end": 10,
         "solid_outlet_end": 11, "fluid_solid_interface-shadow": 12})
    chk("6A settings diff vs P00 after replace", lambda: len(DIFF0), 0)
    chk("9B frozen-physics gate (only the intended variable changed)", lambda: GATE["passed"], True)
    chk("6A monitor file name", lambda: rf.file_name(),
        lambda v: re.sub(r"[\\/]+", "/", v).endswith(MON))
    chk("6A monitor report list", lambda: list(rf.report_defs()), ALLDEFS)

    def init_ok(d):
        def pick(sub):
            ks = [k for k in d if sub in k]
            return float(d[ks[0]]) if ks else None
        return (_close(pick("temperature"), T_IN) and _close(pick("z-velocity"), INIT_W) and
                abs(pick("x-velocity")) < 1e-12 and abs(pick("y-velocity")) < 1e-12 and abs(pick("pressure")) < 1e-9)

    chk("6A init defaults (T 300 K, w 23.5 m/s = P00, u = v = 0, p 0 Pa)",
        lambda: {k: v for k, v in S.initialization.defaults().items() if isinstance(v, (int, float))}, init_ok)

    # --- every common row must equal P00's own audit of the same stage, except the intended rows,
    #     which must differ from P00 and equal the case value
    try:
        med = json.load(open(MED_AUDIT % label))
        medv = {r["item"]: r["value"] for r in med["rows"]}
        for r in rows[:n_common]:
            mine = json.loads(json.dumps(r["value"], default=str))
            if r["item"] in INTENDED_ROWS:
                tgt = INTENDED_ROWS[r["item"]]
                ok = (r["item"] in medv) and _close(mine, tgt, 1e-12) and not _close(mine, medv[r["item"]], 1e-12)
                rows.append({"item": "CHANGED FROM P00 (intended): " + r["item"], "value": mine,
                             "expected": "%r (P00 %r)" % (tgt, medv.get(r["item"])), "ok": bool(ok)})
                continue
            same = (r["item"] in medv) and (mine == medv[r["item"]] or _close(mine, medv[r["item"]], 1e-12))
            rows.append({"item": "SAME AS P00: " + r["item"], "value": mine,
                         "expected": medv.get(r["item"], "<not in P00 audit>"), "ok": bool(same)})
    except Exception as e:
        rows.append({"item": "SAME AS P00: audit file", "value": "ERROR %s" % e, "expected": MED_AUDIT % label,
                     "ok": False})

    bad = [r for r in rows if not r["ok"]]
    write_json("Audit/setup_audit_%s.json" % label, {"label": label, "case": CASE, "n_items": len(rows),
                                                     "n_failed": len(bad), "rows": rows})
    with open("Audit/setup_audit_%s.txt" % label, "w") as fh:
        fh.write("SETUP AUDIT - %s - %s - values READ BACK from Fluent\n" % (CASE, label))
        fh.write("%d items, %d failed\n\n" % (len(rows), len(bad)))
        for r in rows:
            fh.write("%-4s %-60s %s%s\n" % ("ok" if r["ok"] else "FAIL", r["item"], repr(r["value"])[:150],
                                           "" if r["ok"] else "   EXPECTED %r" % (r["expected"],)))
    for r in rows:
        log("AUDIT %-4s %-60s %s" % ("ok" if r["ok"] else "FAIL", r["item"], repr(r["value"])[:100]))
    log("AUDIT %s: %d items, %d failed" % (label, len(rows), len(bad)))
    return bad


bad = audit("1_presolve", STARTUP_SCHEMES)
if bad or [f for f in FAIL if f.startswith("CRITICAL")] or not GATE["passed"]:
    finish_failed("FAILED_PRESOLVE_AUDIT", "pre-solve audit or frozen-physics gate failed; no iteration run")

if os.environ.get("PARAM_AUDIT_ONLY", "0") == "1":
    log("AUDIT-ONLY MODE: pre-solve audit and frozen-physics gate passed, exiting without iterating")
    write_json("Audit/run_summary.json", {"case": CASE, "status": "AUDIT_ONLY_PASSED", "failures": FAIL})
    flush_log("Logs/%s_log.txt" % TAG)
    print("S9B1-DONE AUDIT_ONLY")
    exit()

# ---------------------------------------------------------------------------
# 3. initialisation - fresh standard initialisation from P00's own defaults (300 K, w = 23.5 m/s, 0 Pa)
# ---------------------------------------------------------------------------
step("initialization type standard", lambda: setattr(ini, "initialization_type", "standard"))
step("standard initialize (300 K, w = %.4f m/s, 0 Pa gauge)" % INIT_W, lambda: ini.standard_initialize())


# ---------------------------------------------------------------------------
# validity gate: property tables and solver limiters, checked after EVERY iterate call
# ---------------------------------------------------------------------------
FLUID_T = ["T_fluid_max", "T_fluid_min", "T_wall_max", "T_out_bulk", "T_in_bulk"]
SOLID_T = ["T_solid_max", "T_solid_min", "T_outer_max", "T_outer_avg", "T_inner_avg", "T_wall_max"]
# Fluent's own message formats only (the journal source is echoed into stdout, so a bare keyword search could
# match journal text): "<quantity> limited to <number> in <n> cells", "reversed flow in <n> faces ...",
# the AMG divergence message, and a floating-point exception (character classes keep this source line from
# matching its own pattern when it is echoed)
MSG_PAT = re.compile(r"limited to .{0,60}?\bin\s+\d+\s+(cells|faces)|reversed flow (in|on)\s+\d+|"
                     r"diverg[e]nce detected in|floating[ ]point exception", re.I)
SCAN_FROM = {}


def mark_scan_start():
    for pth in (STDOUT, TRN):
        SCAN_FROM[pth] = os.path.getsize(pth) if os.path.isfile(pth) else 0


def solver_messages():
    hits = []
    for pth in (STDOUT, TRN):
        if not os.path.isfile(pth):
            continue
        with open(pth, "r", errors="ignore") as fh:
            fh.seek(SCAN_FROM.get(pth, 0))
            for l in fh:
                if "S5B " in l or l.lstrip().startswith(">>>"):
                    continue
                if MSG_PAT.search(l):
                    hits.append("%s: %s" % (os.path.basename(pth), l.strip()[:200]))
    return hits


EXTREMES = {}


def validity(tag, scan_messages=True):
    hdr, rows = read_report_file(MON)
    ev = {"tag": tag, "rows": len(rows), "violations": [], "messages": []}
    if hdr and rows:
        c = {n: i for i, n in enumerate(hdr)}
        for names, (lo, hi), table in ((FLUID_T, AIR_RANGE, "air"), (SOLID_T, INC_RANGE, "Inconel")):
            for n in names:
                if n not in c:
                    ev["violations"].append("monitor %s missing" % n)
                    continue
                vals = [r[c[n]] for r in rows]
                vmin, vmax = min(vals), max(vals)
                e = EXTREMES.setdefault(n, {"min": vmin, "max": vmax})
                e["min"], e["max"] = min(e["min"], vmin), max(e["max"], vmax)
                if vmin < lo or vmax > hi:
                    i = [k for k, v in enumerate(vals) if v < lo or v > hi][0]
                    ev["violations"].append("%s outside %s table [%.2f, %.2f] K: min %.3f max %.3f (first at iteration %d)"
                                            % (n, table, lo, hi, vmin, vmax, int(rows[i][0])))
    else:
        ev["violations"].append("monitor file unreadable")
    # the solver-message scan covers the iteration output only (the final pass re-checks the monitor history;
    # its message scan was already done chunk by chunk, and export chatter is not solver output)
    ev["messages"] = solver_messages() if scan_messages else []
    ev["ok"] = not ev["violations"] and not ev["messages"]
    VALIDITY.append(ev)
    write_json("Audit/validity_checks.json", {"extremes_so_far": EXTREMES, "checks": VALIDITY})
    log("VALIDITY %s: %s (%d monitor rows)%s" % (tag, "ok" if ev["ok"] else "VIOLATION", len(rows),
                                                 "" if ev["ok"] else " " + "; ".join(ev["violations"] + ev["messages"])[:300]))
    if not ev["ok"]:
        st = "FAILED_PROPERTY_RANGE" if ev["violations"] else "FAILED_SOLVER_MESSAGE"
        try:
            solver.file.write_case_data(file_name="Case/%s_FAILED.cas.h5" % CASE)
        except Exception:
            pass
        finish_failed(st, "; ".join(ev["violations"] + ev["messages"]))
    return ev


# ---------------------------------------------------------------------------
# convergence machinery (unchanged from 5B/6A/6B)
# ---------------------------------------------------------------------------
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


STAGE3_START = [None]


def evaluate(tag):
    it, res = last_residuals()
    hdr, rows = read_report_file(MON)
    ev = {"tag": tag, "iteration": it, "residuals": res, "checks": {}}
    ok_all = True
    if STAGE3_START[0] is not None:
        rows = [r for r in rows if r[0] >= STAGE3_START[0]]
    if res is None or not hdr or len(rows) < WINDOW:
        ev["ready"] = False
        ev["why"] = "residuals %s, stage-3 rows %d < %d" % ("ok" if res else "unreadable", len(rows), WINDOW)
        return False, ev
    c = {n: i for i, n in enumerate(hdr)}
    need = ["p_in_area", "p_out_area", "q_net_all", "T_outer_max", "mdot_in", "mdot_out",
            "q_heated_wall", "q_interface", "T_out_bulk", "T_solid_max", "T_wall_max"]
    missing = [n for n in need if n not in c]
    if missing:
        ev["ready"] = False
        ev["why"] = "monitor columns missing: %s" % missing
        return False, ev
    win = rows[-WINDOW:]
    lastr = rows[-1]
    for eq, tgt in RES_TARGET.items():
        v = res.get(eq)
        ok = v is not None and v < tgt
        ev["checks"]["residual %s" % eq] = {"value": v, "target": tgt, "ok": ok}
        ok_all &= ok

    def col(name):
        return [r[c[name]] for r in win]

    dp_win = [r[c["p_in_area"]] - r[c["p_out_area"]] for r in win]
    for name, tol in ABS_DRIFT_K.items():
        v = col(name)
        d = max(v) - min(v)
        ok = d < tol
        ev["checks"]["drift %s over %d it [K]" % (name, WINDOW)] = {"value": d, "target": tol, "ok": ok}
        ok_all &= ok
    for name, tol in REL_DRIFT.items():
        v = dp_win if name == "dp_area" else [abs(x) for x in col(name)]
        d = (max(v) - min(v)) / max(abs(sum(v) / len(v)), 1e-30)
        ok = d < tol
        ev["checks"]["rel drift %s over %d it" % (name, WINDOW)] = {"value": d, "target": tol, "ok": ok}
        ok_all &= ok
    mi = abs(lastr[c["mdot_in"]] + lastr[c["mdot_out"]]) / lastr[c["mdot_in"]]
    ev["checks"]["mass imbalance |in-out|/in"] = {"value": mi, "target": MASS_TOL, "ok": mi < MASS_TOL}
    ok_all &= mi < MASS_TOL
    qw = lastr[c["q_heated_wall"]]
    ei = abs(lastr[c["q_net_all"]]) / qw
    ev["checks"]["energy imbalance |sum Q|/Q_wall"] = {"value": ei, "target": ENERGY_TOL, "ok": ei < ENERGY_TOL}
    ok_all &= ei < ENERGY_TOL
    ev["ready"] = True
    ev["converged"] = bool(ok_all)
    return ok_all, ev


def iterate(n, label):
    r = step("%s: iterate %d" % (label, n), lambda: S.run_calculation.iterate(iter_count=n))
    validity(label)
    return r


def checkpoint(label):
    step("checkpoint %s" % label, lambda: solver.file.write_case_data(file_name="Case/%s_checkpoint.cas.h5" % CASE),
         critical=False)


# ---------------------------------------------------------------------------
# 4. STAGE 1 - flow + turbulence only (energy equation not solved)
# ---------------------------------------------------------------------------
mark_scan_start()
eq = S.controls.equations
step("STAGE 1: energy equation OFF", lambda: eq.__setitem__("temperature", False))
step("equations", lambda: eq())
iterate(FLOW_IT, "stage 1 flow-only")

# ---------------------------------------------------------------------------
# 5. STAGE 2 - energy ON, still first order
# ---------------------------------------------------------------------------
step("STAGE 2: energy equation ON", lambda: eq.__setitem__("temperature", True))
step("equations", lambda: eq())
iterate(ENERGY_IT, "stage 2 energy first-order")
step("write end-of-stage-2 case/data",
     lambda: solver.file.write_case_data(file_name="Case/%s_intermediate_end_stage2_firstorder.cas.h5" % CASE),
     critical=False)

# ---------------------------------------------------------------------------
# 6. STAGE 3 - the ONE switch to the final second-order schemes, then converge
# ---------------------------------------------------------------------------
_h, _r = read_report_file(MON)
STAGE3_START[0] = (_r[-1][0] + 1) if _r else None
log("stage 3 starts at iteration %s" % STAGE3_START[0])
for k, v in FINAL_SCHEMES.items():
    step("STAGE 3 scheme %-12s -> %s" % (k, v), (lambda kk=k, vv=v: set_scheme(ds, kk, vv)))
bad = audit("2_final_schemes", FINAL_SCHEMES)
if bad:
    finish_failed("FAILED_FINAL_SCHEME_AUDIT", "audit after the scheme switch failed")

EVALS = []
done = 0
converged = False
while done < MAX_STAGE3:
    iterate(CHUNK, "stage 3 second-order")
    done += CHUNK
    ok, ev = evaluate("stage3+%d" % done)
    EVALS.append(ev)
    if ev.get("ready"):
        failing = [k for k, v in ev["checks"].items() if not v["ok"]]
        log("EVAL iter %s: %s  (failing: %s)" % (ev["iteration"], "CONVERGED" if ok else "not yet",
                                               ", ".join(failing) if failing else "none"))
    else:
        log("EVAL iter %s: not evaluable yet (%s)" % (ev.get("iteration"), ev.get("why")))
    write_json("Audit/convergence_evaluations.json", EVALS)
    if done % 500 == 0:
        checkpoint("stage 3 +%d" % done)
    if ok:
        iterate(CHUNK, "confirmation")
        done += CHUNK
        ok2, ev2 = evaluate("confirmation+%d" % done)
        EVALS.append(ev2)
        failing = [k for k, v in ev2["checks"].items() if not v["ok"]]
        log("CONFIRM iter %s: %s  (failing: %s)" % (ev2["iteration"], "HOLDS" if ok2 else "LOST",
                                                    ", ".join(failing) if failing else "none"))
        if ok2:
            converged = True
            break

write_json("Audit/convergence_evaluations.json", EVALS)
log("STAGE 3 finished after %d second-order iterations; converged=%s" % (done, converged))
STATUS[0] = "CONVERGED" if converged else "NOT_CONVERGED"

bad = audit("3_final", FINAL_SCHEMES)

# ---------------------------------------------------------------------------
# 7. outputs (identical to 6B) + EnSight solid node temperatures (7A mapping source)
# ---------------------------------------------------------------------------
sfx = "final" if converged else "NOT_CONVERGED"
step("write case", lambda: solver.file.write_case(file_name="Case/%s_%s.cas.h5" % (CASE, sfx)))
step("write data", lambda: solver.file.write_data(file_name="Data/%s_%s.dat.h5" % (CASE, sfx)))

FLUXZ = ["fluid_inlet", "fluid_outlet", "heated_outer_wall", "solid_inlet_end", "solid_outlet_end",
         "fluid_solid_interface", "fluid_solid_interface-shadow"]
FR = solver.results.report.fluxes
step("Fluent flux report: mass", lambda: FR.mass_flow(zones=["fluid_inlet", "fluid_outlet"],
                                                     write_to_file=True, file_name="Audit/fluent_flux_mass.txt"),
     critical=False)
step("Fluent flux report: heat", lambda: FR.heat_transfer(zones=FLUXZ, write_to_file=True,
                                                         file_name="Audit/fluent_flux_heat.txt"), critical=False)
SI = solver.results.report.surface_integrals
for fn, surfs, fld, f in [
    ("area_weighted_avg", ["fluid_inlet", "fluid_outlet"], "pressure", "p_area"),
    ("mass_weighted_avg", ["fluid_inlet", "fluid_outlet"], "pressure", "p_mass"),
    ("area_weighted_avg", ["fluid_inlet", "fluid_outlet"], "total-pressure", "p0_area"),
    ("mass_weighted_avg", ["fluid_inlet", "fluid_outlet"], "temperature", "T_mass"),
    ("mass_weighted_avg", ["fluid_inlet", "fluid_outlet"], "enthalpy", "h_mass"),
    ("area_weighted_avg", ["fluid_inlet", "fluid_outlet"], "density", "rho_area"),
    ("area_weighted_avg", ["fluid_inlet", "fluid_outlet"], "z-velocity", "w_area"),
    ("area", ["fluid_inlet", "fluid_outlet", "heated_outer_wall", "fluid_solid_interface"], None, "areas"),
    ("area_weighted_avg", ["heated_outer_wall", "fluid_solid_interface"], "temperature", "Twall_area"),
    ("facet_max", ["heated_outer_wall", "fluid_solid_interface"], "temperature", "Twall_max"),
    ("facet_min", ["heated_outer_wall", "fluid_solid_interface"], "temperature", "Twall_min"),
    ("area_weighted_avg", ["fluid_solid_interface"], "y-plus", "yplus_area"),
    ("facet_max", ["fluid_solid_interface"], "y-plus", "yplus_max"),
    ("facet_min", ["fluid_solid_interface"], "y-plus", "yplus_min"),
    ("area_weighted_avg", ["fluid_solid_interface", "heated_outer_wall"], "heat-flux", "qpp_area"),
]:
    kw = dict(surface_names=surfs, write_to_file=True, file_name="Audit/fluent_si_%s.txt" % f)
    if fld:
        kw["report_of"] = fld
    step("Fluent surface integral %s" % f, (lambda fn=fn, kw=kw: getattr(SI, fn)(**kw)), critical=False)

EXP = solver.file.export.ascii
WALLQ = ["x-coordinate", "y-coordinate", "z-coordinate", "face-area-magnitude", "temperature",
         "heat-flux", "y-plus", "wall-shear", "z-wall-shear", "skin-friction-coef",
         "wall-adjacent-temperature", "cell-wall-distance"]
OUTWQ = ["x-coordinate", "y-coordinate", "z-coordinate", "face-area-magnitude", "temperature", "heat-flux"]
BNDQ = ["x-coordinate", "y-coordinate", "z-coordinate", "face-area-magnitude", "pressure", "total-pressure",
        "temperature", "density", "z-velocity", "velocity-magnitude", "enthalpy"]
for fname, surfs, q in [
    ("Exports/wall_interface.csv", ["fluid_solid_interface"], WALLQ),
    ("Exports/wall_outer.csv", ["heated_outer_wall"], OUTWQ),
    ("Exports/wall_solid_ends.csv", ["solid_inlet_end", "solid_outlet_end"], OUTWQ),
    ("Exports/boundary_inlet.csv", ["fluid_inlet"], BNDQ),
    ("Exports/boundary_outlet.csv", ["fluid_outlet"], BNDQ),
]:
    step("ASCII export %s" % fname,
         (lambda f=fname, s_=surfs, qq=q: EXP(file_name=f, surface_name_list=s_, delimiter="comma",
                                               quantities=qq, location="cell-center")), critical=False)

ISO = solver.results.surfaces.iso_surface
dz = LEN / NZ


def make_iso(name, zval, zone):
    try:
        ISO.create(name)
    except Exception:
        ISO[name] = {}
    o = ISO[name]
    o.field = "z-coordinate"
    o.zones = [zone]
    o.iso_values = [zval]
    return None


ISONAMES = {"fluid_domain": [], "solid_domain": []}
for zone, tg in (("fluid_domain", "f"), ("solid_domain", "s")):
    for k in range(NZ):
        nm = "z%s%02d" % (tg, k)
        if step("iso %s z=%.6f" % (nm, (k + 0.5) * dz), (lambda n=nm, z=(k + 0.5) * dz, zz=zone: make_iso(n, z, zz)),
                critical=False) is None and not any(nm in f for f in FAIL):
            ISONAMES[zone].append(nm)
log("iso surfaces: fluid %d, solid %d" % (len(ISONAMES["fluid_domain"]), len(ISONAMES["solid_domain"])))
FQ = ["cell-zone", "cell-volume", "radial-coordinate", "pressure", "total-pressure", "density", "temperature",
      "enthalpy", "velocity-magnitude", "x-velocity", "y-velocity", "z-velocity", "viscosity-lam", "viscosity-turb",
      "specific-heat-cp", "thermal-conductivity-lam", "turb-kinetic-energy", "specific-diss-rate",
      "cell-wall-distance", "face-area-magnitude"]
SQ = ["cell-zone", "cell-volume", "radial-coordinate", "temperature", "thermal-conductivity-lam",
      "specific-heat-cp", "density", "face-area-magnitude"]
step("export fluid volume", lambda: EXP(file_name="Exports/cells_fluid.csv", surface_name_list=ISONAMES["fluid_domain"],
                                        delimiter="comma", quantities=FQ, location="cell-center"), critical=False)
step("export solid volume", lambda: EXP(file_name="Exports/cells_solid.csv", surface_name_list=ISONAMES["solid_domain"],
                                        delimiter="comma", quantities=SQ, location="cell-center"), critical=False)


def count_rows(path):
    n = 0
    with open(path) as fh:
        fh.readline()
        for _ in fh:
            n += 1
    return n


VEXP = {}
for pth, expect in (("Exports/cells_fluid.csv", EXPECT_FLUID), ("Exports/cells_solid.csv", EXPECT_SOLID)):
    try:
        n = count_rows(pth)
        VEXP[pth] = {"rows": n, "expected_cells": expect, "ok": n == expect}
        log("ROWS %s = %d (expected %d cells) %s" % (pth, n, expect, "OK" if n == expect else "MISMATCH"))
    except Exception as e:
        VEXP[pth] = {"error": str(e)}
write_json("Audit/volume_export_check.json", VEXP)

os.makedirs("EnSight", exist_ok=True)
EG = solver.file.export.ensight_gold
step("export EnSight Gold solid_domain, node-centred temperature (7A mapping source)",
     lambda: EG(file_name="EnSight/solid_domain_T", quantities=["temperature"], binary_format=True,
                cellzones=["solid_domain"], cell_centered=False), critical=False)
try:
    ENS = {fn: os.path.getsize(os.path.join("EnSight", fn)) for fn in sorted(os.listdir("EnSight"))}
except Exception as e:
    ENS = {"error": str(e)}
write_json("Audit/ensight_export_verification.json",
           {"exporter": "file.export.ensight_gold", "arguments": {"quantities": ["temperature"], "binary_format": True,
                                                                 "cellzones": ["solid_domain"], "cell_centered": False},
            "files": ENS})

# final validity pass over the complete history (every iteration of every stage)
validity("final", scan_messages=False)
def _sha(path):
    try:
        import hashlib
        return hashlib.sha256(open(path, "rb").read()).hexdigest().upper()
    except Exception as e:
        return "ERROR %s" % e


write_json("Audit/run_summary.json", {"case": CASE, "status": STATUS[0], "converged": converged,
                                      "journal_sha256": _sha("../Journals/solve_param.py"),
                                      "param_cases_sha256": _sha("../Journals/param_cases.py"),
                                      "s5_common_sha256": _sha("../Journals/s5_common.py"),
                                      "mesh_sha256": _sha(MESH),
                                      "variable": CDEF["variable"], "value": CDEF["value"], "units": CDEF["units"],
                                      "resolved_parameters": P, "applied_read_back": APPLIED,
                                      "frozen_physics_gate_passed": GATE["passed"],
                                      "stage1_iters": FLOW_IT, "stage2_iters": ENERGY_IT, "stage3_iters": done,
                                      "total_iters": FLOW_IT + ENERGY_IT + done,
                                      "stage3_first_iteration": STAGE3_START[0],
                                      "final_audit_failed_rows": len(bad) if bad else 0,
                                      "temperature_extremes_all_iterations": EXTREMES,
                                      "failures": FAIL, "final_eval": EVALS[-1] if EVALS else None})
log("=" * 80)
log("RUN COMPLETE  case %s  status=%s  total iterations=%d" % (CASE, STATUS[0], FLOW_IT + ENERGY_IT + done))
log("FAILURES (%d)" % len(FAIL))
for f in FAIL:
    log("   " + f)
log("=" * 80)
flush_log("Logs/%s_log.txt" % TAG)
step("stop transcript", lambda: solver.file.stop_transcript(), critical=False)
print("S9B1-DONE %s" % STATUS[0])
exit()
