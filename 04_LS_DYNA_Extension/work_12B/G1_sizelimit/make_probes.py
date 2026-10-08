# Section 12B Gate 1 - synthetic size-limit probes (NOT project geometry). Writes P1..P5 decks.
# Each probe: unit-size steel block, free, explicit, terminated after 2 cycles. Only the node/element counts matter.
import os
HERE = os.path.dirname(os.path.abspath(__file__))
PROBES = {  # name: (kind, nx, ny, nz)
    'P1_N127500_E120050': ('hex', 49, 49, 50),
    'P2_N128502_E120640': ('hex', 32, 58, 65),
    'P3_N131502_E123000': ('hex', 30, 41, 100),
    'P4_N29640_E128520_tet': ('tet', 12, 18, 119),
    'P5_N29808_E131495_tet': ('tet', 17, 17, 91),
}
TET5 = [(0, 1, 3, 4), (1, 2, 3, 6), (1, 4, 5, 6), (3, 4, 6, 7), (1, 3, 4, 6)]  # 5-tet split of hex (0..7 corner order)

def vol(p, a, b, c, d):
    ax, ay, az = [p[b][i] - p[a][i] for i in range(3)]
    bx, by, bz = [p[c][i] - p[a][i] for i in range(3)]
    cx, cy, cz = [p[d][i] - p[a][i] for i in range(3)]
    return ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx)

for name, (kind, nx, ny, nz) in PROBES.items():
    d = os.path.join(HERE, name); os.makedirs(d, exist_ok=True)
    nid = lambda i, j, k: 1 + i + (nx + 1) * (j + (ny + 1) * k)
    coords = {}
    lines = ['*KEYWORD', '*TITLE', f'G1 size probe {name} (synthetic block, not project data)',
             '*CONTROL_TERMINATION', '1.0,2', '*DATABASE_BINARY_D3PLOT', '1.0',
             '*PART', 'block', '1,1,1', '*SECTION_SOLID', '1,%d' % (2 if kind == 'hex' else 10),
             '*MAT_ELASTIC', '1,7800.0,2.0e11,0.3', '*NODE']
    for k in range(nz + 1):
        for j in range(ny + 1):
            for i in range(nx + 1):
                n = nid(i, j, k); x, y, z = i / nx, j / ny, k / nz; coords[n] = (x, y, z)
                lines.append(f'{n},{x:.8f},{y:.8f},{z:.8f}')
    lines.append('*ELEMENT_SOLID')
    eid = 0
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                c = [nid(i, j, k), nid(i + 1, j, k), nid(i + 1, j + 1, k), nid(i, j + 1, k),
                     nid(i, j, k + 1), nid(i + 1, j, k + 1), nid(i + 1, j + 1, k + 1), nid(i, j + 1, k + 1)]
                if kind == 'hex':
                    eid += 1; lines += [f'{eid},1', ','.join(map(str, c))]
                else:
                    for t in TET5:
                        a, b, cc, dd = [c[q] for q in t]
                        if vol(coords, a, b, cc, dd) < 0: b, cc = cc, b
                        eid += 1; lines += [f'{eid},1', f'{a},{b},{cc},{dd},{dd},{dd},{dd},{dd}']
    lines.append('*END')
    with open(os.path.join(d, 'probe.k'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(name, 'nodes', len(coords), 'elements', eid)
