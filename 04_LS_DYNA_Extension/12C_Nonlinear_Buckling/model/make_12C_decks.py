# Section 12C - case decks: validated 12B G5 physics + imperfection + lambda schedule beyond 1 (time t -> lambda via LCID 10).
import os
OUT = "<OUTPUT_ROOT>/S12C/15_LS_DYNA_Extension/12C_Nonlinear_Buckling/runs"
cases = {'C0_A0p0': ('0.0', r'..\..\model\nodes.k'), 'C1_A0p1': ('0.1', r'..\..\imperfection\nodes_A0p1.k'),
         'C2_A0p3': ('0.3', r'..\..\imperfection\nodes_A0p3.k'), 'C3_A0p6': ('0.6', r'..\..\imperfection\nodes_A0p6.k'),
         'C4_A0p9': ('0.9', r'..\..\imperfection\nodes_A0p9.k'), 'C5_A1p2': ('1.2', r'..\..\imperfection\nodes_A1p2.k'),
         'N1_A0p1_halfstep': ('0.1', r'..\..\imperfection\nodes_A0p1.k')}
def deck(name, amp, nodes):
    half = name.startswith('N1')
    L = ['*KEYWORD', '*TITLE',
         f'12C {name}: nonlinear thermo-elastic LC2, mode-1 imperfection A = {amp} mm, lambda 0-1.3' + (' (half steps lambda>1)' if half else ''),
         '*CONTROL_SOLUTION', '0,0,0,10000',
         '*CONTROL_TERMINATION', '0.9',
         '*CONTROL_IMPLICIT_GENERAL', '1,0.01',
         '*CONTROL_IMPLICIT_SOLUTION', '12,11,15,1.0e-4,1.0e-3,1.0e-4', '2,1,1,2',
         '*CONTROL_IMPLICIT_AUTO', ('1,11,5,1.0e-4,-30' if half else '1,11,5,1.0e-4,0.01'),
         '*DATABASE_BINARY_D3PLOT', '0.05',
         '*DATABASE_NODOUT', '0.01',
         '*DATABASE_HISTORY_NODE_SET', '21',
         '*DATABASE_ELOUT', '0.02',
         '*DATABASE_HISTORY_SOLID_SET', '2',
         '*DATABASE_EXTENT_BINARY', '0,0,0,0,0,0,0,0', '0,0,0,0,0,0,0,0', '0,0,0,0,0,0,,STRESS_GL',
         '*DATABASE_SPCFORC', '0.01,3',
         '*DATABASE_GLSTAT', '0.01',
         '*PART', 'duct_solid_domain', '1,1,1',
         '*SECTION_SOLID', '1,23']
    for inc in [r'..\..\model\mat_inconel_thermoelastic.k', nodes, r'..\..\model\elements_h20.k', r'..\..\model\sets.k',
                r'..\..\model\csys_hoop.k', r'..\..\model\spc_lc2.k', r'..\..\model\temps_lc2.k', r'..\..\model\monitor_sets_12C.k']:
        assert len(inc) <= 80
        L += ['*INCLUDE', inc]
    L += ['*DEFINE_CURVE_TITLE', 'lambda(t): scales (T - 300 K); 40 steps to 1.0, 0.005 to 1.2, 0.01 to 1.3', '10',
          '0.0,0.0', '0.4,1.0', '0.8,1.2', '0.9,1.3']
    if half:
        L += ['*DEFINE_CURVE_TITLE', 'max step vs time: 0.01 to t=0.4, then 0.005', '30', '0.0,0.01', '0.399999,0.01', '0.4,0.005', '0.9,0.005']
    L += ['*END']
    return '\n'.join(L) + '\n'
for name, (amp, nodes) in cases.items():
    os.makedirs(f'{OUT}/{name}', exist_ok=True)
    open(f'{OUT}/{name}/case.k', 'w', newline='\n').write(deck(name, amp, nodes))
print(open(f'{OUT}/C3_A0p6/case.k').read())
