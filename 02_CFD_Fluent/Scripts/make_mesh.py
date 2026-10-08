#!/usr/bin/env python3
"""
STRUCTURED CONFORMAL HEX MESH GENERATOR
Project : Flow Behavior and Thermal Effects in Multiphysics Systems (RE-ANALYSIS 2026)
Phase   : Section 4 - CFD mesh

Builds a single conformal mesh containing TWO cell zones:
    fluid_domain  - butterfly (O-grid) core + graded annulus, Di = 20 mm
    solid_domain  - graded annulus, Di = 20 mm to Do = 40 mm
extruded 600 mm.

The fluid wall nodes and the solid inner nodes are THE SAME NODES, so the
fluid-solid interface is conformal by construction - not by tolerance matching.

Writes an ASCII ANSYS Fluent .msh which Fluent itself then validates.
Geometry is frozen from Section 2/3: Di 20, Do 40, L 600 mm.
"""
import numpy as np, math, json, sys, os

DI, DO, LZ = 0.020, 0.040, 0.600
RI, RO = DI / 2.0, DO / 2.0
SUPER_N = 4.0                      # super-ellipse exponent for the O-grid core boundary


# ----------------------------------------------------------------------------
def geometric_ratio(h1, total, n):
    """growth g such that h1*(g^n - 1)/(g-1) = total"""
    if abs(h1 * n - total) < 1e-15:
        return 1.0
    lo, hi = 1.0000001, 3.0
    for _ in range(200):
        g = 0.5 * (lo + hi)
        s = h1 * (g ** n - 1.0) / (g - 1.0)
        if s < total:
            lo = g
        else:
            hi = g
    return 0.5 * (lo + hi)


def geometric_nodes(r_wall, r_inner, h1, n):
    """node radii from r_inner..r_wall, fine (h1) at the WALL. returns ascending array len n+1"""
    total = r_wall - r_inner
    g = geometric_ratio(h1, total, n)
    h = h1 * g ** np.arange(n)          # h[0] at wall, growing inward
    r = np.empty(n + 1)
    r[n] = r_wall
    for i in range(n - 1, -1, -1):
        r[i] = r[i + 1] - h[n - 1 - i]
    r[0] = r_inner
    return r, g, h


def build(NC, NR, NRS, NZ, H1_FLUID, H1_SOLID, core_frac=0.45):
    """NC: core-square divisions per side (Ntheta = 4*NC)"""
    NT = 4 * NC
    a = core_frac * RI
    th = 225.0 * math.pi / 180.0 + 2.0 * math.pi * np.arange(NT) / NT
    ct, st = np.cos(th), np.sin(th)
    rho = a / (np.abs(ct) ** SUPER_N + np.abs(st) ** SUPER_N) ** (1.0 / SUPER_N)

    # ---- core block via transfinite interpolation of the rounded-square boundary
    B = np.column_stack([rho * ct, rho * st])                 # (NT,2)
    def Bp(j):
        return B[j % NT]
    C0, C1, C2, C3 = Bp(0), Bp(NC), Bp(2 * NC), Bp(3 * NC)
    core = np.zeros((NC + 1, NC + 1, 2))
    for p in range(NC + 1):
        for q in range(NC + 1):
            u, v = p / NC, q / NC
            bot, rig = Bp(p), Bp(NC + q)
            top, lef = Bp(3 * NC - p), Bp(4 * NC - q)
            core[p, q] = ((1 - v) * bot + v * top + (1 - u) * lef + u * rig
                          - ((1 - u) * (1 - v) * C0 + u * (1 - v) * C1
                             + u * v * C2 + (1 - u) * v * C3))

    # ---- radial distributions
    rf, gf, hf = geometric_nodes(RI, a, H1_FLUID, NR)          # fluid annulus
    rs, gs, hs = geometric_nodes(RO, RI, H1_SOLID, NRS)        # solid annulus (h1 at RI)
    rs = RI + (RO - rs[::-1] + RI - RI)                        # placeholder, replaced below
    # solid: fine at the INNER radius -> build outward
    gs2 = geometric_ratio(H1_SOLID, RO - RI, NRS)
    hs2 = H1_SOLID * gs2 ** np.arange(NRS)
    rs = np.concatenate([[RI], RI + np.cumsum(hs2)])
    rs[-1] = RO

    # ---- 2D node table
    n_core = (NC + 1) * (NC + 1)
    n_fann = NR * NT
    n_sann = NRS * NT
    n2d = n_core + n_fann + n_sann
    xy = np.zeros((n2d, 2))
    for p in range(NC + 1):
        for q in range(NC + 1):
            xy[q * (NC + 1) + p] = core[p, q]
    for i in range(1, NR + 1):
        R = rho + (rf[i] - a) * (RI - rho) / (RI - a)
        xy[n_core + (i - 1) * NT: n_core + i * NT] = np.column_stack([R * ct, R * st])
    for i in range(1, NRS + 1):
        xy[n_core + n_fann + (i - 1) * NT: n_core + n_fann + i * NT] = \
            np.column_stack([rs[i] * ct, rs[i] * st])

    def perim(j):
        j %= NT
        if j <= NC:              return 0 * (NC + 1) + j           # bottom q=0
        if j <= 2 * NC:          return (j - NC) * (NC + 1) + NC   # right p=NC
        if j <= 3 * NC:          return NC * (NC + 1) + (3 * NC - j)
        return (4 * NC - j) * (NC + 1) + 0
    PER = np.array([perim(j) for j in range(NT)])

    def fann(i, j):
        j %= NT
        return PER[j] if i == 0 else n_core + (i - 1) * NT + j
    def sann(i, j):
        j %= NT
        return fann(NR, j) if i == 0 else n_core + n_fann + (i - 1) * NT + j

    # ---- 3D nodes
    z = np.linspace(0.0, LZ, NZ + 1)
    coords = np.zeros((n2d * (NZ + 1), 3))
    for k in range(NZ + 1):
        coords[k * n2d:(k + 1) * n2d, 0:2] = xy
        coords[k * n2d:(k + 1) * n2d, 2] = z[k]
    N3 = lambda m, k: k * n2d + m

    # ---- cells (fluid first, then solid), each as 8 nodes bottom-CCW then top
    cells = []
    for k in range(NZ):
        for q in range(NC):
            for p in range(NC):
                b = [q * (NC + 1) + p, q * (NC + 1) + p + 1,
                     (q + 1) * (NC + 1) + p + 1, (q + 1) * (NC + 1) + p]
                cells.append([N3(m, k) for m in b] + [N3(m, k + 1) for m in b])
    for k in range(NZ):
        for i in range(NR):
            for j in range(NT):
                b = [fann(i, j), fann(i + 1, j), fann(i + 1, j + 1), fann(i, j + 1)]
                cells.append([N3(m, k) for m in b] + [N3(m, k + 1) for m in b])
    n_fluid_cells = len(cells)
    for k in range(NZ):
        for i in range(NRS):
            for j in range(NT):
                b = [sann(i, j), sann(i + 1, j), sann(i + 1, j + 1), sann(i, j + 1)]
                cells.append([N3(m, k) for m in b] + [N3(m, k + 1) for m in b])
    cells = np.array(cells, dtype=np.int64)
    n_cells = len(cells)
    return dict(coords=coords, cells=cells, n_fluid_cells=n_fluid_cells, n_cells=n_cells,
                n2d=n2d, NT=NT, NC=NC, NR=NR, NRS=NRS, NZ=NZ, a=a,
                rf=rf, gf=gf, hf=hf, rs=rs, gs=gs2, hs=hs2, z=z)


HEXF = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def hex_volumes(coords, cn):
    P = coords[cn]
    c = P.mean(axis=1)
    V = np.zeros(len(cn))
    for f in HEXF:
        q = P[:, f, :]
        fc = q.mean(axis=1)
        for t in range(4):
            aa = q[:, t, :]; bb = q[:, (t + 1) % 4, :]
            nrm = 0.5 * np.cross(bb - aa, fc - aa)
            V += np.einsum('ij,ij->i', (aa + bb + fc) / 3.0 - c, nrm)
    return V / 3.0


def _selftest():
    cube = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
                     [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], float)
    v = hex_volumes(cube, np.array([[0, 1, 2, 3, 4, 5, 6, 7]]))[0]
    assert abs(v - 1.0) < 1e-12, "unit cube volume wrong: %r" % v
    return True


# ----------------------------------------------------------------------------
# face extraction and ANSYS Fluent .msh writer
# ----------------------------------------------------------------------------
ZONE = dict(fluid_domain=2, solid_domain=3, interior_fluid=4, interior_solid=5,
            fluid_inlet=6, fluid_outlet=7, fluid_solid_interface=8,
            heated_outer_wall=9, solid_inlet_end=10, solid_outlet_end=11)
BC = dict(interior=2, wall=3, pressure_outlet=5, velocity_inlet=10)


def extract_faces(m, tol=1e-9):
    coords, cells, nf = m["coords"], m["cells"], m["n_fluid_cells"]
    seen = {}
    for ci in range(len(cells)):
        cn = cells[ci]
        for f in HEXF:
            # Fluent's face normal (right-hand rule on the node loop) points from
            # c1 TOWARD c0, i.e. INTO c0 - the opposite of the outward convention used
            # by HEXF. Verified empirically: the outward winding gave Fluent negative
            # cell volumes on every cell. The loop is therefore reversed here.
            nd = (int(cn[f[3]]), int(cn[f[2]]), int(cn[f[1]]), int(cn[f[0]]))
            key = tuple(sorted(nd))
            e = seen.get(key)
            if e is None:
                seen[key] = [nd, ci + 1, 0]
            else:
                e[2] = ci + 1
    buckets = {k: [] for k in ZONE if k not in ("fluid_domain", "solid_domain")}
    zl, zh = 0.0 + tol, LZ - tol
    for nd, c0, c1 in seen.values():
        if c1 == 0:
            p = coords[list(nd)]
            zc = p[:, 2].mean()
            rc = np.sqrt(p[:, 0] ** 2 + p[:, 1] ** 2).mean()
            fluid = c0 <= nf
            if zc < zl:
                buckets["fluid_inlet" if fluid else "solid_inlet_end"].append((nd, c0, 0))
            elif zc > zh:
                buckets["fluid_outlet" if fluid else "solid_outlet_end"].append((nd, c0, 0))
            elif rc > 0.5 * (RI + RO):
                buckets["heated_outer_wall"].append((nd, c0, 0))
            else:
                raise RuntimeError("unclassified boundary face at z=%.4f r=%.4f" % (zc, rc))
        else:
            f0, f1 = c0 <= nf, c1 <= nf
            if f0 and f1:
                buckets["interior_fluid"].append((nd, c0, c1))
            elif (not f0) and (not f1):
                buckets["interior_solid"].append((nd, c0, c1))
            else:
                if f0:
                    buckets["fluid_solid_interface"].append((nd, c0, c1))
                else:
                    buckets["fluid_solid_interface"].append((nd[::-1], c1, c0))
    return buckets


def write_msh(path, m, buckets, title):
    coords, cells, nf, nc = m["coords"], m["cells"], m["n_fluid_cells"], m["n_cells"]
    nn = len(coords)
    order = ["interior_fluid", "interior_solid", "fluid_inlet", "fluid_outlet",
             "fluid_solid_interface", "heated_outer_wall", "solid_inlet_end", "solid_outlet_end"]
    bctype = dict(interior_fluid="interior", interior_solid="interior",
                  fluid_inlet="velocity_inlet", fluid_outlet="pressure_outlet",
                  fluid_solid_interface="wall", heated_outer_wall="wall",
                  solid_inlet_end="wall", solid_outlet_end="wall")
    zname = dict(interior_fluid="interior-fluid", interior_solid="interior-solid",
                 fluid_inlet="fluid_inlet", fluid_outlet="fluid_outlet",
                 fluid_solid_interface="fluid_solid_interface",
                 heated_outer_wall="heated_outer_wall",
                 solid_inlet_end="solid_inlet_end", solid_outlet_end="solid_outlet_end")
    ztype = dict(interior_fluid="interior", interior_solid="interior",
                 fluid_inlet="velocity-inlet", fluid_outlet="pressure-outlet",
                 fluid_solid_interface="wall", heated_outer_wall="wall",
                 solid_inlet_end="wall", solid_outlet_end="wall")
    nfaces = sum(len(buckets[k]) for k in order)
    hx = lambda v: format(int(v), "x")
    w = open(path, "w")
    w.write('(0 "%s")\n' % title)
    w.write('(0 "RE-ANALYSIS 2026 - structured conformal hex mesh, not an original file")\n')
    w.write("(2 3)\n")
    w.write('(0 "Nodes")\n(10 (0 1 %s 0 3))\n(10 (1 1 %s 1 3)(\n' % (hx(nn), hx(nn)))
    for p in coords:
        w.write("%.12e %.12e %.12e\n" % (p[0], p[1], p[2]))
    w.write("))\n")
    w.write('(0 "Cells")\n(12 (0 1 %s 0 0))\n' % hx(nc))
    w.write("(12 (%s 1 %s 1 4))\n" % (hx(ZONE["fluid_domain"]), hx(nf)))
    w.write("(12 (%s %s %s %s 4))\n" % (hx(ZONE["solid_domain"]), hx(nf + 1), hx(nc), hx(17)))
    w.write('(0 "Faces")\n(13 (0 1 %s 0 0))\n' % hx(nfaces))
    start = 1
    for k in order:
        fl = buckets[k]
        if not fl:
            continue
        end = start + len(fl) - 1
        w.write("(13 (%s %s %s %s 4)(\n" % (hx(ZONE[k]), hx(start), hx(end), hx(BC[bctype[k]])))
        for nd, c0, c1 in fl:
            w.write("%s %s %s %s %s %s\n" % (hx(nd[0] + 1), hx(nd[1] + 1), hx(nd[2] + 1),
                                             hx(nd[3] + 1), hx(c0), hx(c1)))
        w.write("))\n")
        start = end + 1
    w.write('(0 "Zones")\n')
    w.write("(45 (%d fluid fluid_domain)())\n" % ZONE["fluid_domain"])
    w.write("(45 (%d solid solid_domain)())\n" % ZONE["solid_domain"])
    for k in order:
        if buckets[k]:
            w.write("(45 (%d %s %s)())\n" % (ZONE[k], ztype[k], zname[k]))
    w.close()
    return nfaces


def generate(name, outdir, NC, NR, NRS, NZ, H1_FLUID=12.2e-6, H1_SOLID=0.5e-3):
    m = build(NC, NR, NRS, NZ, H1_FLUID, H1_SOLID)
    V = hex_volumes(m["coords"], m["cells"])
    nf = m["n_fluid_cells"]
    b = extract_faces(m)
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "%s.msh" % name)
    nfaces = write_msh(path, m, b, "%s mesh - heated thick-walled duct" % name)

    # Euler / consistency checks
    per_cell = {}
    for k, fl in b.items():
        for nd, c0, c1 in fl:
            per_cell[c0] = per_cell.get(c0, 0) + 1
            if c1:
                per_cell[c1] = per_cell.get(c1, 0) + 1
    bad = [c for c in range(1, m["n_cells"] + 1) if per_cell.get(c, 0) != 6]
    used = set()
    for fl in b.values():
        for nd, c0, c1 in fl:
            used.update(nd)
    stat = dict(
        name=name, file=path, file_MB=round(os.path.getsize(path) / 1e6, 2),
        NC=NC, Ntheta=4 * NC, NR=NR, NRS=NRS, NZ=NZ,
        nodes=int(len(m["coords"])), cells=int(m["n_cells"]),
        fluid_cells=int(nf), solid_cells=int(m["n_cells"] - nf), faces=int(nfaces),
        faces_by_zone={k: len(v) for k, v in b.items() if v},
        min_cell_volume=float(V.min()), max_cell_volume=float(V.max()),
        negative_cells=int((V <= 0).sum()),
        fluid_volume=float(V[:nf].sum()), solid_volume=float(V[nf:].sum()),
        fluid_volume_exact=math.pi * RI ** 2 * LZ,
        solid_volume_exact=math.pi * (RO ** 2 - RI ** 2) * LZ,
        polygon_area_ratio=float((4 * NC) / (2 * math.pi) * math.sin(2 * math.pi / (4 * NC))),
        first_layer_m=float(H1_FLUID), fluid_growth=float(m["gf"]),
        infl_18_thickness_m=float(m["rf"][-1] - m["rf"][max(0, NR - 18)]),
        fluid_annulus_thickness_m=float(RI - m["a"]), core_radius_m=float(m["a"]),
        solid_first_layer_m=float(H1_SOLID), solid_growth=float(m["gs"]),
        axial_cell_m=float(LZ / NZ),
        max_aspect_ratio_est=float((LZ / NZ) / H1_FLUID),
        cells_with_wrong_face_count=len(bad),
        all_nodes_used=bool(len(used) == len(m["coords"])))
    return stat


if __name__ == "__main__":
    _selftest()
    outroot = sys.argv[1] if len(sys.argv) > 1 else "."
    levels = [("coarse", dict(NC=8,  NR=18, NRS=7,  NZ=60)),
              ("medium", dict(NC=12, NR=24, NRS=10, NZ=90)),
              ("fine",   dict(NC=18, NR=32, NRS=15, NZ=135))]
    only = sys.argv[2] if len(sys.argv) > 2 else None
    allstat = []
    for nm, kw in levels:
        if only and only != nm:
            continue
        d = os.path.join(outroot, "Mesh_" + nm.capitalize())
        s = generate(nm, d, **kw)
        allstat.append(s)
        print("%-7s cells=%-8d nodes=%-8d faces=%-9d neg=%d  file=%.1f MB"
              % (nm, s["cells"], s["nodes"], s["faces"], s["negative_cells"], s["file_MB"]))
        print("        fluid vol %.8e (exact %.8e, ratio %.6f)"
              % (s["fluid_volume"], s["fluid_volume_exact"], s["fluid_volume"] / s["fluid_volume_exact"]))
        print("        solid vol %.8e (exact %.8e, ratio %.6f)"
              % (s["solid_volume"], s["solid_volume_exact"], s["solid_volume"] / s["solid_volume_exact"]))
        print("        polygon area ratio %.6f | growth f=%.4f s=%.4f | bad-face-count cells=%d | all nodes used=%s"
              % (s["polygon_area_ratio"], s["fluid_growth"], s["solid_growth"],
                 s["cells_with_wrong_face_count"], s["all_nodes_used"]))
    with open(os.path.join(outroot, "Mesh_Quality", "mesh_generation_stats.json"), "w") as fh:
        json.dump(allstat, fh, indent=2)
    print("wrote mesh_generation_stats.json")
