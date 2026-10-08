# -*- coding: utf-8 -*-
"""Section 9B-1 - the approved CFD parametric cases, defined ONCE and imported by every script.

RE-ANALYSIS 2026. Source of every value: 10_Parametric_Study/Case_Matrix/PARAMETRIC_CASE_MATRIX.csv
(Section 9A, approved) and the frozen baseline (02_Engineering_Calculations/baseline_parameters.json).
Nothing here is a recovered internship value.

Each case differs from P00_BASELINE in exactly ONE design variable. The only other settings that
change are the ones the baseline itself DERIVES from that variable, by the baseline's own rule, exactly as
approved in 9A (PARAMETRIC_PLAN.md s.2 and the frozen-physics gate row of its s.6):
  * V cases: inlet turbulence intensity I = 0.16 Re^-1/8 (baseline formula, "the definition is kept, not
    the number"). The INITIAL field is NOT changed: every case starts from P00's own standard initialisation
    (300 K, w = 23.5 m/s, k and omega as stored in the P00 case, 0 Pa). A converged steady solution does not
    depend on its starting field, and keeping it identical keeps the settings diff to the approved paths only.
  * T cases: the heat flux q'' is DERIVED so that the total heat input equals P00's (D-060):
    q'' = Q_P00 / A_heated,actual = q''_P00 * Do_P00 / Do_case (the heated area is pi*Do*L on the CAD and
    the 48-gon facet area on the CFD mesh; the ratio is the same for both, so Q is held on both).
"""
import math

# ---- frozen baseline
V0, Q0, DO0, DI, L, T_IN = 23.5, 8000.0, 0.040, 0.020, 0.600, 300.0
RE0 = 29957.0                              # baseline Re used by the baseline TI formula
TI_FORMULA = lambda re: 0.16 * re ** (-0.125)
TI0 = TI_FORMULA(RE0)                      # 0.044113... (identical expression to solve_baseline.py)

MED_MESH = "../../../06_Fluent_CFD/Case/medium_mesh_used_for_baseline.msh"
MED_COUNTS = (159840, 116640, 43200)       # total / fluid / solid (Section 4 MESH_QUALITY_TABLE)
NT, NZ = 48, 90                            # circumferential facets, axial slabs (unchanged in every case)


def _v(v):
    return dict(V_IN=v, TI=TI_FORMULA(RE0 * v / V0))


def _q(q):
    return dict(QPP=q)


def _t(t_mm):
    do = DI + 2.0 * t_mm * 1e-3
    return dict(QPP=Q0 * DO0 / do, DO=do, T_WALL=t_mm * 1e-3)


# Allowed settings-tree paths (regex on the snapshot diff). Every other path must be identical to P00.
P_VEL = r"^/setup/boundary_conditions/velocity_inlet/fluid_inlet/momentum/velocity_magnitude(/value)?$"
P_TI = r"^/setup/boundary_conditions/velocity_inlet/fluid_inlet/turbulence/turbulent_intensity(/value)?$"
P_QPP = r"^/setup/boundary_conditions/wall/heated_outer_wall/thermal/heat_flux(/value)?$"

BASE = dict(V_IN=V0, TI=TI0, INIT_W=V0, QPP=Q0, DO=DO0, T_WALL=0.010, MESH=MED_MESH, COUNTS=MED_COUNTS)

CASES = {
    "C00_PIPELINE_CHECK": dict(variable="none (pipeline control)", value="identical to P00", units="-",
                               intended={}, allowed=[], derived=[]),
    "V01_LOW": dict(variable="inlet velocity", value=21.15, units="m/s", intended=_v(21.15),
                    allowed=[P_VEL, P_TI], derived=["TI"]),
    "V03_HIGH": dict(variable="inlet velocity", value=25.85, units="m/s", intended=_v(25.85),
                     allowed=[P_VEL, P_TI], derived=["TI"]),
    "Q01_LOW": dict(variable="outer-wall heat flux", value=7200.0, units="W/m2", intended=_q(7200.0),
                    allowed=[P_QPP], derived=[]),
    "Q03_HIGH": dict(variable="outer-wall heat flux", value=8800.0, units="W/m2", intended=_q(8800.0),
                     allowed=[P_QPP], derived=[]),
    "T01_THIN": dict(variable="wall thickness (Q held constant)", value=8.0, units="mm", intended=_t(8.0),
                     allowed=[P_QPP], derived=["QPP"],
                     mesh="../../Mesh_Checks/Mesh_T01_THIN/T01_THIN.msh", counts=(155520, 116640, 38880)),
    "T03_THICK": dict(variable="wall thickness (Q held constant)", value=12.0, units="mm", intended=_t(12.0),
                      allowed=[P_QPP], derived=["QPP"],
                      mesh="../../Mesh_Checks/Mesh_T03_THICK/T03_THICK.msh", counts=(168480, 116640, 51840)),
}
ORDER = ["C00_PIPELINE_CHECK", "V01_LOW", "V03_HIGH", "Q01_LOW", "Q03_HIGH", "T01_THIN", "T03_THICK"]


def resolved(case):
    """Full parameter set of a case = baseline values overridden by the case's intended values."""
    c = CASES[case]
    r = dict(BASE)
    r.update(c["intended"])
    r["MESH"] = c.get("mesh", MED_MESH)
    r["COUNTS"] = tuple(c.get("counts", MED_COUNTS))
    return r


if __name__ == "__main__":
    import json
    out = {}
    for k in ORDER:
        r = resolved(k)
        out[k] = dict(CASES[k], resolved=r,
                      changed_vs_P00={p: r[p] for p in r if r[p] != BASE[p]})
        print("%-20s V %-6s TI %.6f initw %-6s q'' %.6f Do %.3f mesh %s" %
              (k, r["V_IN"], r["TI"], r["INIT_W"], r["QPP"], r["DO"], r["MESH"]))
    with open("param_cases.json", "w") as fh:
        json.dump(out, fh, indent=2, default=str)
