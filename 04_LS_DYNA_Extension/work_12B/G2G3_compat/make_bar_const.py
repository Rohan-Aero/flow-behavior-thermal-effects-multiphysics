# Section 12B - diagnostic: restrained bar with CONSTANT E, nu, alpha (8A benchmark values), uniform dT = 225.
# Closed form: sigma_z = -E*alpha*dT = -581.4 MPa, sigma_x = sigma_y = 0. Isolates solver treatment of thermal strain.
import os
HERE = os.path.dirname(os.path.abspath(__file__))
a, b, c = 0.01, 0.01, 0.02
X = [(0,0,0),(a,0,0),(a,b,0),(0,b,0),(0,0,c),(a,0,c),(a,b,c),(0,b,c),(a/2,0,0),(a,b/2,0),(a/2,b,0),(0,b/2,0),
     (a/2,0,c),(a,b/2,c),(a/2,b,c),(0,b/2,c),(0,0,c/2),(a,0,c/2),(a,b,c/2),(0,b,c/2)]
V = {'C1_lin_1step': (1, 1), 'C2_nl_1step': (12, 1), 'C3_nl_10step': (12, 10), 'C4_lin_10step': (1, 10)}
for name, (ns, nst) in V.items():
    d = os.path.join(HERE, 'bar_const', name); os.makedirs(d, exist_ok=True)
    k = ['*KEYWORD', '*TITLE', f'diagnostic constant-property restrained bar {name}', '*CONTROL_TERMINATION', '1.0',
         '*CONTROL_IMPLICIT_GENERAL', f'1,{1.0/nst:.6g}', '*CONTROL_IMPLICIT_SOLUTION', f'{ns}', '*CONTROL_IMPLICIT_AUTO', '0',
         '*DATABASE_ELOUT', f'{1.0/nst:.6g}', '*DATABASE_HISTORY_SOLID', '1', '*DATABASE_SPCFORC', f'{1.0/nst:.6g}',
         '*PART', 'bar', '1,1,1', '*SECTION_SOLID', '1,23', '*MAT_ELASTIC', '1,8190.0,1.9e11,0.294', '*MAT_ADD_THERMAL_EXPANSION', '1,0,1.36e-5', '*NODE']
    k += [f'{i+1},{x:.9e},{y:.9e},{z:.9e}' for i, (x, y, z) in enumerate(X)]
    k += ['*ELEMENT_SOLID_H20', '1,1', ','.join(str(i) for i in range(1, 11)), ','.join(str(i) for i in range(11, 21))]
    ends = [i+1 for i, p in enumerate(X) if p[2] in (0, c)]
    k += ['*SET_NODE_LIST', '1'] + [','.join(map(str, ends[j:j+8])) for j in range(0, len(ends), 8)]
    k += ['*BOUNDARY_SPC_SET', '1,0,0,0,1,0,0,0', '*BOUNDARY_SPC_NODE', '1,0,1,1,0,0,0,0', '2,0,0,1,0,0,0,0']
    k += ['*LOAD_THERMAL_VARIABLE_NODE'] + [f'{i+1},225.0,0.0,10' for i in range(20)]
    k += ['*DEFINE_CURVE', '10', '0.0,0.0', '1.0,1.0', '*END']
    open(os.path.join(d, 'bar.k'), 'w', newline='\n').write('\n'.join(k) + '\n')
