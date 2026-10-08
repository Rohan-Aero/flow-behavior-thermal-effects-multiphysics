# Section 12B Gates 2/3 - restrained-bar check of ELFORM 23 + MAT_004 thermo-elastic + MAT_ADD_THERMAL_EXPANSION.
# One 20-node hex (10 x 10 x 20 mm), U_z = 0 on both end faces, lateral expansion free, uniform T: 300 K -> 562.56 K.
# Closed form (total-form elasticity, as in MAPDL): sigma_z(T) = -E(T) * eps_th(T); sigma_x = sigma_y = 0.
import os
HERE = os.path.dirname(os.path.abspath(__file__))
MAT = os.path.join(HERE, '..', 'G4_import', 'model', 'mat_inconel_thermoelastic.k')
a, b, c = 0.01, 0.01, 0.02
corn = [(0, 0, 0), (a, 0, 0), (a, b, 0), (0, b, 0), (0, 0, c), (a, 0, c), (a, b, c), (0, b, c)]
mid = [(a/2, 0, 0), (a, b/2, 0), (a/2, b, 0), (0, b/2, 0), (a/2, 0, c), (a, b/2, c), (a/2, b, c), (0, b/2, c),
       (0, 0, c/2), (a, 0, c/2), (a, b, c/2), (0, b, c/2)]
X = corn + mid                                              # node i+1 = position i (LS-DYNA H20 order)
VARIANTS = {'B1_lin_1step': (1, 1), 'B2_lin_10step': (1, 10), 'B3_lin_40step': (1, 40),
            'B4_nl_10step': (12, 10), 'B5_nl_40step': (12, 40)}
TMAX = 562.5576399
for name, (nsolvr, nstep) in VARIANTS.items():
    d = os.path.join(HERE, 'bar', name); os.makedirs(d, exist_ok=True)
    k = ['*KEYWORD', '*TITLE', f'G3 restrained bar {name} (12B; checks element/material only, not project geometry)',
         '*CONTROL_SOLUTION', '0,0,0,10000',
         '*CONTROL_TERMINATION', '1.0', '*CONTROL_IMPLICIT_GENERAL', f'1,{1.0/nstep:.6g}',
         '*CONTROL_IMPLICIT_SOLUTION', f'{nsolvr}', '*CONTROL_IMPLICIT_AUTO', '0',
         '*DATABASE_BINARY_D3PLOT', f'{1.0/nstep:.6g}', '*DATABASE_ELOUT', f'{1.0/nstep:.6g}',
         '*DATABASE_EXTENT_BINARY', '0,0,0,0,0,0,0,0', '0,0,0,0,0,0,0,0', '0,0,0,0,0,0,STRESS,STRESS_GL',
         '*DATABASE_HISTORY_SOLID', '1', '*DATABASE_NODOUT', f'{1.0/nstep:.6g}', '*DATABASE_HISTORY_NODE', '2,3,6,7',
         '*PART', 'bar', '1,1,1', '*SECTION_SOLID', '1,23', '*INCLUDE', 'mat_inconel_thermoelastic.k', '*NODE']
    k += [f'{i + 1},{x:.9e},{y:.9e},{z:.9e}' for i, (x, y, z) in enumerate(X)]
    k += ['*ELEMENT_SOLID_H20', '1,1', ','.join(str(i) for i in range(1, 11)), ','.join(str(i) for i in range(11, 21))]
    bot = [i + 1 for i, p in enumerate(X) if p[2] == 0]; top = [i + 1 for i, p in enumerate(X) if p[2] == c]
    k += ['*SET_NODE_LIST', '1'] + [','.join(map(str, (bot + top)[j:j + 8])) for j in range(0, len(bot + top), 8)]
    k += ['*BOUNDARY_SPC_SET', '1,0,0,0,1,0,0,0', '*BOUNDARY_SPC_NODE', '1,0,1,1,0,0,0,0', '2,0,0,1,0,0,0,0']
    k += ['*LOAD_THERMAL_VARIABLE_NODE'] + [f'{i + 1},{TMAX - 300.0:.6f},300.0,10' for i in range(20)]
    k += ['*DEFINE_CURVE', '10', '0.0,0.0', '1.0,1.0', '*END']
    open(os.path.join(d, 'bar.k'), 'w', newline='\n').write('\n'.join(k) + '\n'); import shutil; shutil.copy(MAT, d)
    print(name)
