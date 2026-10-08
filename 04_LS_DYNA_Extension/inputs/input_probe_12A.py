import os, io, json, hashlib, math
P = r'<PROJECT_ROOT>'
S = os.path.join(P, '08_Structural_Analysis')
res = {}
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()
files = [
 r'03_CAD_Geometry\STEP\heated_duct.step', r'03_CAD_Geometry\Native_CAD\heated_duct.scdocx', r'03_CAD_Geometry\Geometry_Check\cad_measurements.json',
 r'07_Thermal_Analysis\Mapping\MeshBased\fluent_solid_mesh.cdb', r'07_Thermal_Analysis\Mapping\MeshBased\fluent_solid_node_temperature.csv',
 r'07_Thermal_Analysis\Mapping\Mechanical_Export\LC2_imported_body_temperature.txt', r'07_Thermal_Analysis\Temperature_Source\fluent_interface_wall_pressure.csv',
 r'07_Thermal_Analysis\Validation\mapping_validation_7A.json',
 r'08_Structural_Analysis\LC2_Restrained\Solver_Output\LC2_solve_input_ds.dat', r'08_Structural_Analysis\LC2_Restrained\Solver_Output\s7b_nodal.csv',
 r'08_Structural_Analysis\LC2_Restrained\Solver_Output\s7b_react.csv', r'08_Structural_Analysis\LC1_Free_Expansion\Solver_Output\LC1_solve_input_ds.dat',
 r'08_Structural_Analysis\Pressure_Check\Solver_Output\LC2P_solve_input_ds.dat', r'08_Structural_Analysis\Loads\wall_pressure_profile_7A.csv',
 r'08_Structural_Analysis\Materials\materials_7A.csv', r'08_Structural_Analysis\Materials\MATERIAL_MODEL_7A.md',
 r'08_Structural_Analysis\Boundary_Conditions\BOUNDARY_CONDITIONS_7A.md', r'08_Structural_Analysis\Mesh\MESH_7A.md', r'08_Structural_Analysis\Mesh\mesh_stats_7A.json',
 r'08_Structural_Analysis\Buckling\Mechanical\LC2_Linear_Buckling\Solver_Output\s8a_mode1.csv', r'08_Structural_Analysis\Buckling\Mechanical\LC2_Linear_Buckling\Solver_Output\s8a_mode2.csv',
 r'08_Structural_Analysis\Buckling\Mechanical\LC2_Linear_Buckling\Solver_Output\s8a_load_factors.csv', r'08_Structural_Analysis\Buckling\Mechanical\LC2_Linear_Buckling\Solver_Output\ds.dat',
 r'08_Structural_Analysis\Buckling\Mechanical\LC2_prestress_resolve\Solver_Output\ds.dat', r'08_Structural_Analysis\Buckling\fe_modes_8A.json',
 r'08_Structural_Analysis\Buckling\BUCKLING_RESULTS.md', r'08_Structural_Analysis\Buckling\Workbench\Flow_Behavior_Thermal_Effects_Buckling_8A.wbpj',
 r'08_Structural_Analysis\Workbench\Flow_Behavior_Thermal_Effects_Structural_7B.wbpj', r'11_Final_Audit\MASTER_PROJECT_DATA.csv',
]
res['hashes'] = {}
for f in files:
    p = os.path.join(P, f)
    res['hashes'][f] = {'sha256': sha(p), 'bytes': os.path.getsize(p)} if os.path.exists(p) else 'MISSING'
# parse LC2 deck
ds = os.path.join(S, r'LC2_Restrained\Solver_Output\LC2_solve_input_ds.dat')
L = io.open(ds, encoding='utf-8', errors='replace').read().splitlines()
nodes = {}; i = 0
while not L[i].lower().startswith('nblock'): i += 1
i += 2
while L[i].strip() != '-1':
    t = L[i].split(); nodes[int(t[0])] = tuple(float(x) for x in t[1:4]); i += 1
res['n_nodes'] = len(nodes)
while not L[i].lower().startswith('eblock'): i += 1
i += 2; ne = 0
while L[i].strip() != '-1':
    ne += 1; i += 1
res['n_elem_lines'] = ne
def cm(name):
    for k, l in enumerate(L):
        if l.upper().startswith('CMBLOCK,' + name.upper()):
            n = int(l.split(',')[3]); vals = []; j = k + 2
            while len(vals) < n:
                vals += [int(x) for x in L[j].split()]; j += 1
            out = []
            for a, v in enumerate(vals):
                if v < 0:
                    out += list(range(vals[a-1] + 1, -v + 1))
                else:
                    out.append(v)
            return out
ez = cm('_DISPZEROUZ'); res['n_DISPZEROUZ'] = len(ez)
res['DISPZEROUZ_z_values'] = sorted(set(round(nodes[n][2], 6) for n in ez))
for nm in ['SOLID_INLET_END', 'SOLID_OUTLET_END', 'NS_LC2_HOOP_3NODES_MIDSPAN_OUTER', 'NS_LC1_SUPPORT_3NODES_INLET_OUTE']:
    c = cm(nm); res['n_' + nm] = len(c)
hoop = cm('NS_LC2_HOOP_3NODES_MIDSPAN_OUTER')
res['hoop_nodes'] = {n: [round(x, 6) for x in nodes[n]] + [round(math.degrees(math.atan2(nodes[n][1], nodes[n][0])), 3)] for n in hoop}
# BF temperatures
k = [j for j, l in enumerate(L) if l.lower().startswith('bfblock')][0]
T = []; j = k + 2
while not L[j].lower().startswith('bf,end'):
    T.append(float(L[j].split()[1])); j += 1
res['n_BF'] = len(T); res['T_min_C'] = min(T); res['T_max_C'] = max(T)
res['T_min_K'] = min(T) + 273.15; res['T_max_K'] = max(T) + 273.15
zs = [c[2] for c in nodes.values()]; rs = [math.hypot(c[0], c[1]) for c in nodes.values()]
res['z_range'] = [min(zs), max(zs)]; res['r_range'] = [min(rs), max(rs)]
# mode 1 corner-node eigenvector
m1 = os.path.join(S, r'Buckling\Mechanical\LC2_Linear_Buckling\Solver_Output\s8a_mode1.csv')
rows = [l.split(',') for l in io.open(m1).read().splitlines()[1:] if l.strip()]
lat = []; ax = []
for r in rows:
    x, y, z, ux, uy, uz = map(float, r[1:7]); lat.append((math.hypot(ux, uy), z, ux, uy)); ax.append(abs(uz))
mx = max(lat)
res['mode1_n_rows'] = len(rows); res['mode1_max_lateral'] = mx[0]; res['mode1_max_lateral_z'] = mx[1]
res['mode1_lateral_dir_deg'] = round(math.degrees(math.atan2(mx[3], mx[2])), 3)
res['mode1_max_abs_uz_over_max_lat'] = max(ax) / mx[0]
mid = [l for l in lat if abs(l[1] - 0.3) < 1e-6]
res['mode1_midspan_max_lat_over_max'] = max(m[0] for m in mid) / mx[0] if mid else None
# cos(pi z/L) correlation of lateral component along the outer line nearest the max direction (all corner nodes)
num = den1 = den2 = 0.0
for r in rows:
    x, y, z, ux, uy, uz = map(float, r[1:7])
    proj = (ux * mx[2] + uy * mx[3]) / mx[0]
    c = math.cos(math.pi * z / 0.6)
    num += proj * c; den1 += proj * proj; den2 += c * c
res['mode1_corr_cos_pi_z_over_L'] = num / math.sqrt(den1 * den2)
json.dump(res, io.open(os.path.join(os.environ['TEMP'], 'claude_inputs_probe3.json'), 'w', encoding='utf-8'), indent=1)
print('ok')
