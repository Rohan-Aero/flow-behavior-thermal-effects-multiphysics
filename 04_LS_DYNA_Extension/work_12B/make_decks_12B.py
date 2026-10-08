# Section 12B - main decks built from the converted LC2 model (G4_import/model). No physics is tuned to match Mechanical.
import os
W = os.path.dirname(os.path.abspath(__file__))
M = r'..\G4_import\model'
def inc(*names, pre=M):
    out = []
    for n in names: out += ['*INCLUDE', f'{pre}\\{n}']
    return out
OUT_COMMON = ['*DATABASE_BINARY_D3PLOT', '1.0', '*DATABASE_SPCFORC', '0.25', '*DATABASE_NODOUT', '1.0',
              '*DATABASE_HISTORY_NODE_SET', '5', '*DATABASE_ELOUT', '1.0', '*SET_SOLID_GENERAL', '1', 'ALL',
              '*DATABASE_HISTORY_SOLID_SET', '1', '*DATABASE_EXTENT_BINARY', '0,0,0,0,0,0,0,0', '0,0,0,0,0,0,0,0', '0,0,0,0,0,0,,STRESS_GL',
              '*DATABASE_GLSTAT', '0.25']
def write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', newline='\n').write('\n'.join(lines + ['*END']) + '\n')
# ---- G2 benchmark on mesh B: constant properties, uniform dT = 225 (8A toy-benchmark values), LC2 supports ----
d = os.path.join(W, 'G2G3_compat', 'bench_meshB')
os.makedirs(d, exist_ok=True)
nodes = [int(l.split(',')[0]) for l in open(os.path.join(W, 'G4_import', 'model', 'nodes.k')) if l[:1].isdigit()]
open(os.path.join(d, 'temps_uniform225.k'), 'w', newline='\n').write('\n'.join(['*KEYWORD', '*LOAD_THERMAL_VARIABLE_NODE'] + [f'{n},225.0,0.0,10' for n in nodes] + ['*END']) + '\n')
write(os.path.join(d, 'bench.k'), ['*KEYWORD', '*TITLE', 'G2 benchmark mesh B: E=190GPa nu=0.294 a=13.6e-6 dT=225 uniform, LC2 supports, static+buckle (method check)',
      '*CONTROL_SOLUTION', '0,0,0,10000', '*CONTROL_TERMINATION', '1.0', '*CONTROL_IMPLICIT_GENERAL', '1,1.0',
      '*CONTROL_IMPLICIT_SOLUTION', '1', '*CONTROL_IMPLICIT_BUCKLE', '6,1', '*DATABASE_BINARY_D3PLOT', '1.0', '*DATABASE_SPCFORC', '1.0',
      '*PART', 'tube', '1,1,1', '*SECTION_SOLID', '1,23', '*MAT_ELASTIC', '1,8190.0,1.9e11,0.294', '*MAT_ADD_THERMAL_EXPANSION', '1,0,1.36e-5']
      + inc('nodes.k', 'elements_h20.k', 'sets.k', 'csys_hoop.k', 'spc_lc2.k', pre='..\\'+M) + ['*INCLUDE', 'temps_uniform225.k', '*DEFINE_CURVE', '10', '0.0,0.0', '1.0,1.0'])
# ---- G5: LC2 static reproduction (project material, mapped field, LC2 supports, perfect geometry) ----
def lc2(nstep, buckle, title):
    k = ['*KEYWORD', '*TITLE', title, '*CONTROL_SOLUTION', '0,0,0,10000', '*CONTROL_TERMINATION', '1.0',
         '*CONTROL_IMPLICIT_GENERAL', f'1,{1.0/nstep:.6g}', '*CONTROL_IMPLICIT_SOLUTION', '12', '*CONTROL_IMPLICIT_AUTO', '0']
    if buckle: k += ['*CONTROL_IMPLICIT_BUCKLE', '6,1']
    k += OUT_COMMON + ['*PART', 'duct_solid_domain', '1,1,1', '*SECTION_SOLID', '1,23']
    k += inc('mat_inconel_thermoelastic.k', 'nodes.k', 'elements_h20.k', 'sets.k', 'csys_hoop.k', 'spc_lc2.k', 'temps_lc2.k')
    k += ['*DEFINE_CURVE_TITLE', 'lambda(t): scales (T - 300 K)', '10', '0.0,0.0', '1.0,1.0']
    return k
write(os.path.join(W, 'G5_static', 'lc2_static.k'), lc2(40, False, 'G5 LC2 static reproduction: mapped field, T_ref 300 K, LC2 supports, MAT_004 thermo-elastic, 40 steps, NSOLVR 12'))
write(os.path.join(W, 'G6_buckle', 'lc2_buckle.k'), lc2(40, True, 'G6 LC2 linear eigen-buckling check: G5 state at lambda = 1, then *CONTROL_IMPLICIT_BUCKLE (6 modes)'))
print('decks written; nodes', len(nodes))
