# Section 12B Gate 3 - LS-DYNA thermo-elastic material from the EXISTING project data (no new data).
# E(T), nu: MPDATA EX/NUXY of the LC2 deck. CTE: secant table (ALPX at 93.33..537.78 C, datum 21.11 C, MPAMOD)
# converted EXACTLY to the instantaneous coefficient LS-DYNA integrates (alpha_inst = d eps_th / dT), where eps_th is
# the thermal strain MAPDL applies: eps_th(T) = alpha'(T) * (T - TREF), alpha' = MPAMOD-modified table, linear
# interpolation, constant extrapolation (MAPDL convention). Temperatures in K in the LS-DYNA files.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
TREF = 26.85; TD = 21.11                                   # deg C (TREF from deck; MPAMOD definition temperature)
TA = [93.33, 204.44, 315.56, 426.67, 537.78]               # deg C, ALPX table temperatures
AS = [12.8e-6, 13.3e-6, 13.9e-6, 14.2e-6, 14.8e-6]         # secant CTE from 21.11 C
TE = [20.0, 100.0, 200.0, 300.0, 400.0]                    # deg C, EX table temperatures
EE = [204e9, 199e9, 193e9, 187e9, 180e9]; NU = 0.294; RHO = 8190.0
def lin(x, xs, ys):                                        # MAPDL-style linear interpolation, constant extrapolation
    if x <= xs[0]: return ys[0]
    if x >= xs[-1]: return ys[-1]
    for k in range(len(xs) - 1):
        if xs[k] <= x <= xs[k + 1]:
            return ys[k] + (ys[k + 1] - ys[k]) * (x - xs[k]) / (xs[k + 1] - xs[k])
a_ref = lin(TREF, TA, AS)                                   # = 12.8e-6 (below the first table point)
AP = [(AS[k] * (TA[k] - TD) - a_ref * (TREF - TD)) / (TA[k] - TREF) for k in range(5)]   # MPAMOD-modified table
def eps_th(Tc):  return lin(Tc, TA, AP) * (Tc - TREF)       # thermal strain in MAPDL (deg C input)
def eps_th_continuous(Tc): return lin(Tc, TA, AS) * (Tc - TD) - a_ref * (TREF - TD)   # alternative (12A) reading
def a_inst(Tc, side=0):                                     # derivative of eps_th; side -1/+1 at table points
    if Tc < TA[0] or (Tc == TA[0] and side < 0): return AP[0]
    if Tc > TA[-1] or (Tc == TA[-1] and side > 0): return AP[-1]
    for k in range(4):
        lo, hi = TA[k], TA[k + 1]
        if lo <= Tc <= hi and not (Tc == lo and side < 0) and not (Tc == hi and side > 0):
            s = (AP[k + 1] - AP[k]) / (hi - lo)
            return AP[k] + s * (Tc - lo) + s * (Tc - TREF)
    return AP[-1]
# curve points (K): exact piecewise-linear representation of alpha_inst with 1e-4 K jumps at table points
dlt = 1e-4; pts = [(250.0, AP[0])]
for k, t in enumerate(TA):
    tk = t + 273.15
    pts += [(tk - dlt, a_inst(t, -1)), (tk + dlt, a_inst(t, +1))]
pts.append((900.0, AP[-1]))
lines = ['*KEYWORD', '$ Inconel 718 (project data set) thermo-elastic: MAT_004 without SIGY/ETAN + instantaneous CTE curve 20',
         '$ E(T): VDM 4127 table (LC2 deck MPDATA,EX); nu 0.294 [ASSUMED]; CTE: exact conversion of the MPAMOD secant table',
         '*MAT_ELASTIC_PLASTIC_THERMAL', f'1,{RHO}',
         ','.join(f'{t + 273.15:.2f}' for t in TE), ','.join(f'{e:.4g}' for e in EE), ','.join(f'{NU}' for _ in TE),
         ','.join('0.0' for _ in TE), '', '',
         '*MAT_ADD_THERMAL_EXPANSION', '1,20,1.0', '*DEFINE_CURVE_TITLE', 'alpha_inst(T) [1/K] vs T [K] - exact derivative of MAPDL eps_th', '20']
lines += [f'{x:.6f},{y:.12e}' for x, y in pts] + ['*END']
open(os.path.join(HERE, 'G4_import', 'model', 'mat_inconel_thermoelastic.k'), 'w', newline='\n').write('\n'.join(lines) + '\n')
chk = {'a_ref': a_ref, 'alpha_mpamod_table': AP, 'curve_points_K': pts,
       'eps_th_at_K': {f'{tk:.2f}': eps_th(tk - 273.15) for tk in (300.0, 366.48, 423.84, 437.99, 477.59, 500.0, 525.48, 562.56, 588.71, 640.0, 673.15)},
       'max_rel_diff_mpamod_vs_continuous_423_673K': max(abs(eps_th(t) - eps_th_continuous(t)) / eps_th(t) for t in [150 + 0.5 * i for i in range(500)])}
json.dump(chk, open(os.path.join(HERE, 'G4_import', 'model', 'material_check.json'), 'w'), indent=1)
print('AP', AP); print('eps', chk['eps_th_at_K']); print('max rel diff', chk['max_rel_diff_mpamod_vs_continuous_423_673K'])
