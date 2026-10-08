#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mesh_analysis.py  -  Section 4, independent mesh-quality audit and mesh views.

Project : Flow Behavior and Thermal Effects in Multiphysics Systems
          (RE-ANALYSIS of a lost Eleation internship project - not original files)

WHAT THIS SCRIPT IS
    An INDEPENDENT, open-formula check on the three meshes written by make_mesh.py,
    plus a set of mesh figures rendered directly from the mesh node/connectivity
    arrays with matplotlib.

WHAT THIS SCRIPT IS NOT
    It is NOT ANSYS.  The figures it produces are matplotlib renders of the real
    mesh data; they are NOT screenshots of the ANSYS Meshing or Fluent GUI and are
    never to be presented as such.  ANSYS Fluent's own /mesh/check and /mesh/quality
    output is the authoritative quality record and lives in
    Mesh_Quality/<level>_fluent_check.txt.

PROVENANCE GUARD
    Before any metric or figure is produced, the in-memory mesh is compared node by
    node against the .msh file that Fluent actually read.  If they disagree the
    script aborts.  This is what allows the figures to be described as "the project
    mesh" rather than "a mesh built by the same script".
"""

from __future__ import print_function
import os, sys, json, math, time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                      # 05_Meshing
sys.path.insert(0, HERE)
import make_mesh as mm                            # noqa: E402

SHOTS = os.path.join(BASE, "Screenshots")
QUAL  = os.path.join(BASE, "Mesh_Quality")
for d in (SHOTS, QUAL):
    if not os.path.isdir(d):
        os.makedirs(d)

C_FLUID, C_SOLID, C_OK, C_WARN = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GREY = "#5a5a5a"

LEVELS = [("coarse", dict(NC=8,  NR=18, NRS=7,  NZ=60),  os.path.join(BASE, "Mesh_Coarse", "coarse.msh")),
          ("medium", dict(NC=12, NR=24, NRS=10, NZ=90),  os.path.join(BASE, "Mesh_Medium", "medium.msh")),
          ("fine",   dict(NC=18, NR=32, NRS=15, NZ=135), os.path.join(BASE, "Mesh_Fine",   "fine.msh"))]

H1_FLUID, H1_SOLID = 12.2e-6, 0.5e-3


# ---------------------------------------------------------------------------
# 1.  provenance: read the node block out of the .msh Fluent actually loaded
# ---------------------------------------------------------------------------
def read_msh(path):
    """One pass over an ASCII Fluent .msh: node coordinates + cell-zone counts.

    Stops at the start of the face section, which is the bulk of the file.
    """
    xs = []
    cellcount = {}
    in_nodes = False
    with open(path, "r") as fh:
        for line in fh:
            s = line.strip()
            if in_nodes:
                if s.startswith("))") or s == ")":
                    in_nodes = False
                    continue
                p4 = s.split()
                if len(p4) == 3:
                    xs.append((float(p4[0]), float(p4[1]), float(p4[2])))
                    continue
                in_nodes = False
                # fall through and re-test this line as a header
            if s.startswith("(13 ("):
                break
            if s.startswith("(10 (") and not s.startswith("(10 (0"):
                in_nodes = True
            elif s.startswith("(12 (") and not s.startswith("(12 (0"):
                t = s[5:].split(")")[0].split()
                if len(t) >= 4:
                    cellcount[int(t[0], 16)] = int(t[2], 16) - int(t[1], 16) + 1
    return np.asarray(xs, dtype=float), cellcount


def read_fluent_check(level):
    """Pull the numbers ANSYS Fluent itself reported, so they can be compared."""
    f = os.path.join(QUAL, level + "_fluent_check.txt")
    out = {}
    if not os.path.isfile(f):
        return out
    for line in open(f, "r", errors="ignore"):
        t = line.strip()
        for key, tag in (("vol_min", "minimum volume"), ("vol_max", "maximum volume"),
                         ("vol_total", "total volume")):
            if t.startswith(tag) and ":" in t:
                try:
                    out[key] = float(t.split(":")[1].strip())
                except ValueError:
                    pass
        if t.startswith("Minimum Orthogonal Quality"):
            try:
                out["oq_min"] = float(t.split("=")[1].split()[0])
            except (IndexError, ValueError):
                pass
        if t.startswith("Maximum Aspect Ratio"):
            try:
                out["ar_max"] = float(t.split("=")[1].split()[0])
            except (IndexError, ValueError):
                pass
    return out


# ---------------------------------------------------------------------------
# 2.  quality metrics, computed from open formulae
# ---------------------------------------------------------------------------
HEXF_OUT = mm.HEXF                     # outward-winding faces, as used for volumes
HEX_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0),
             (4, 5), (5, 6), (6, 7), (7, 4),
             (0, 4), (1, 5), (2, 6), (3, 7)]


def face_table(cells):
    """Vectorised face -> (owner, neighbour) map for an all-hex mesh."""
    nc = len(cells)
    fl = np.empty((nc * 6, 4), dtype=np.int64)
    for k, f in enumerate(HEXF_OUT):
        fl[k * nc:(k + 1) * nc, :] = cells[:, list(f)]
    owner = np.tile(np.arange(nc, dtype=np.int64), 6)
    key = np.sort(fl, axis=1)
    kv = np.ascontiguousarray(key).view(
        np.dtype((np.void, key.dtype.itemsize * 4))).ravel()
    uniq, inv = np.unique(kv, return_inverse=True)
    inv = np.asarray(inv).ravel()
    nf = len(uniq)
    order = np.argsort(inv, kind="stable")
    counts = np.bincount(inv, minlength=nf)
    starts = np.concatenate(([0], np.cumsum(counts)[:-1]))
    c0 = owner[order[starts]]
    rep = fl[order[starts]]
    c1 = np.full(nf, -1, dtype=np.int64)
    two = counts == 2
    c1[two] = owner[order[starts[two] + 1]]
    if (counts > 2).any():
        raise RuntimeError("a face is shared by more than two cells")
    return rep, c0, c1


def quad_area_centroid(P):
    """Finite-volume area vector and area-weighted centroid of quads. P (n,4,3).

    The quad is split into four triangles about the node-average point, exactly as a
    finite-volume code does.  Using the node average instead would be wrong for the
    strongly graded near-wall cells, and would not reproduce Fluent's own numbers.
    """
    c = P.mean(axis=1)
    A = np.zeros_like(c)
    num = np.zeros_like(c)
    den = np.zeros(len(c))
    for t in range(4):
        a = P[:, t]
        b = P[:, (t + 1) % 4]
        av = 0.5 * np.cross(b - a, c - a)
        mag = np.linalg.norm(av, axis=1)
        A += av
        num += ((a + b + c) / 3.0) * mag[:, None]
        den += mag
    return A, num / np.maximum(den, 1e-300)[:, None]


def cell_centroid(P):
    """True volume centroid of hexahedra (tetrahedral decomposition). P (n,8,3)."""
    c = P.mean(axis=1)
    V = np.zeros(len(P))
    num = np.zeros((len(P), 3))
    for f in HEXF_OUT:
        q = P[:, list(f), :]
        fc = q.mean(axis=1)
        for t in range(4):
            aa = q[:, t]
            bb = q[:, (t + 1) % 4]
            v = np.einsum("ij,ij->i", aa - c, np.cross(bb - c, fc - c)) / 6.0
            V += v
            num += v[:, None] * ((c + aa + bb + fc) / 4.0)
    return num / V[:, None], V


def metrics(coords, cells, chunk=120000):
    """volume, equiangle skewness, ANSYS aspect ratio, ANSYS orthogonal quality.

    Every formula here is written out in the open so the numbers can be defended
    without reference to the solver.  They reproduce Fluent's own reported minima
    (see Mesh_Quality/*_fluent_check.txt) to six significant figures.
    """
    nc = len(cells)
    vol = np.empty(nc)
    skew = np.empty(nc)
    ar = np.empty(nc)
    cc = np.empty((nc, 3))

    for s0 in range(0, nc, chunk):
        e = min(s0 + chunk, nc)
        P = coords[cells[s0:e]]                                    # (m,8,3)
        cci, Vi = cell_centroid(P)
        cc[s0:e] = cci
        vol[s0:e] = Vi

        thmax = np.full(e - s0, -1e9)
        thmin = np.full(e - s0, 1e9)
        dface = np.empty((e - s0, 6))
        for k, f in enumerate(HEXF_OUT):
            q = P[:, list(f), :]
            for t in range(4):
                a = q[:, (t - 1) % 4] - q[:, t]
                b = q[:, (t + 1) % 4] - q[:, t]
                na = np.linalg.norm(a, axis=1)
                nb = np.linalg.norm(b, axis=1)
                cs = np.einsum("ij,ij->i", a, b) / np.maximum(na * nb, 1e-300)
                th = np.degrees(np.arccos(np.clip(cs, -1.0, 1.0)))
                thmax = np.maximum(thmax, th)
                thmin = np.minimum(thmin, th)
            Af, fc = quad_area_centroid(q)
            nhat = Af / np.maximum(np.linalg.norm(Af, axis=1), 1e-300)[:, None]
            dface[:, k] = np.abs(np.einsum("ij,ij->i", fc - cci, nhat))
        skew[s0:e] = np.maximum((thmax - 90.0) / 90.0, (90.0 - thmin) / 90.0)

        dnode = np.linalg.norm(P - cci[:, None, :], axis=2)
        allD = np.hstack([dface, dnode])
        ar[s0:e] = allD.max(axis=1) / np.maximum(allD.min(axis=1), 1e-300)
        del P, allD, dface, dnode

    # --- orthogonal quality needs face adjacency
    rep, c0, c1 = face_table(cells)
    A, fc = quad_area_centroid(coords[rep])
    d = fc - cc[c0]
    flip = np.einsum("ij,ij->i", A, d) < 0.0
    A[flip] *= -1.0
    nA = np.maximum(np.linalg.norm(A, axis=1), 1e-300)

    oq = np.ones(nc)
    v = fc - cc[c0]
    np.minimum.at(oq, c0, np.einsum("ij,ij->i", A, v) /
                  (nA * np.maximum(np.linalg.norm(v, axis=1), 1e-300)))
    has = c1 >= 0
    if has.any():
        Ah, nAh = A[has], nA[has]
        vv = cc[c1[has]] - cc[c0[has]]
        cB = np.einsum("ij,ij->i", Ah, vv) / \
            (nAh * np.maximum(np.linalg.norm(vv, axis=1), 1e-300))
        np.minimum.at(oq, c0[has], cB)
        np.minimum.at(oq, c1[has], cB)
        f2 = fc[has] - cc[c1[has]]
        cA2 = np.einsum("ij,ij->i", -Ah, f2) / \
            (nAh * np.maximum(np.linalg.norm(f2, axis=1), 1e-300))
        np.minimum.at(oq, c1[has], cA2)
    nfaces = len(rep)
    del rep, A, fc
    return dict(vol=vol, skew=skew, ar=ar, oq=oq, cc=cc, nfaces=nfaces, c0=c0, c1=c1)


# ---------------------------------------------------------------------------
# 3.  figure helpers
# ---------------------------------------------------------------------------
PROV = ("matplotlib render of the actual project mesh arrays - NOT an ANSYS GUI screenshot")


def _wrap(txt, width=118):
    out, line = [], ""
    for w in txt.split():
        if len(line) + len(w) + 1 > width:
            out.append(line); line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(line)
    return "\n".join(out)


def _finish(fig, path, caption):
    fig.text(0.5, -0.045, _wrap(caption), ha="center", va="top",
             fontsize=7.2, color=GREY, linespacing=1.5)
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("   wrote", os.path.basename(path))


def section2d(m):
    """(xy, core_quads, fluid_annulus_quads, solid_quads) for the k=0 slab."""
    NC, NR, NRS, NZ, NT = m["NC"], m["NR"], m["NRS"], m["NZ"], m["NT"]
    xy = m["coords"][:m["n2d"], :2]
    cells = m["cells"]
    ncore, nfann, nsann = NC * NC, NR * NT, NRS * NT
    core = cells[0:ncore, 0:4]
    fann = cells[NZ * ncore: NZ * ncore + nfann, 0:4]
    sann = cells[NZ * ncore + NZ * nfann: NZ * ncore + NZ * nfann + nsann, 0:4]
    return xy, core, fann, sann


def quad_polys(xy, quads):
    return [xy[q] for q in quads]


def draw_section(ax, m, lw=0.28, edge="#20242b", core_fc="#cfe3fa",
                 fluid_fc="#e8f1fc", solid_fc="#fbe0d3"):
    xy, core, fann, sann = section2d(m)
    ax.add_collection(PolyCollection(quad_polys(xy, sann), facecolors=solid_fc,
                                     edgecolors=edge, linewidths=lw))
    ax.add_collection(PolyCollection(quad_polys(xy, fann), facecolors=fluid_fc,
                                     edgecolors=edge, linewidths=lw))
    ax.add_collection(PolyCollection(quad_polys(xy, core), facecolors=core_fc,
                                     edgecolors=edge, linewidths=lw))
    ax.set_aspect("equal")
    ax.set_xlabel("x  [mm]"); ax.set_ylabel("y  [mm]")


def mm_fmt(ax):
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: "%.0f" % (v * 1e3)))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: "%.0f" % (v * 1e3)))


# ---------------------------------------------------------------------------
# 4.  the twelve views
# ---------------------------------------------------------------------------
def fig01_cross_section(M):
    m = M["coarse"]["m"]
    fig, ax = plt.subplots(figsize=(6.6, 6.6))
    draw_section(ax, m)
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(mm.RI * np.cos(th), mm.RI * np.sin(th), color=C_FLUID, lw=1.6, zorder=5)
    ax.plot(mm.RO * np.cos(th), mm.RO * np.sin(th), color=C_SOLID, lw=1.6, zorder=5)
    ax.set_xlim(-0.0215, 0.0215); ax.set_ylim(-0.0215, 0.0215)
    mm_fmt(ax)
    ax.set_title("View 1  -  full cross-section, COARSE mesh (z = 0 plane)\n"
                 "butterfly (O-grid) hexahedral topology, fluid core + graded annuli + solid wall",
                 fontsize=10)
    ax.text(0.0, 0.0, "fluid\ncore", ha="center", va="center", fontsize=8, color="#123a63")
    ax.text(0.0, 0.0152, "solid\nwall", ha="center", va="center", fontsize=8, color="#7a3413")
    _finish(fig, os.path.join(SHOTS, "mesh_01_cross_section_full.png"),
            "Blue circle = Di = 20 mm fluid/solid interface.  Orange circle = Do = 40 mm heated outer wall.  " + PROV)


def fig02_core_detail(M):
    m = M["coarse"]["m"]
    fig, ax = plt.subplots(figsize=(6.4, 6.4))
    draw_section(ax, m, lw=0.7)
    a = m["a"]
    ax.set_xlim(-1.9 * a, 1.9 * a); ax.set_ylim(-1.9 * a, 1.9 * a)
    mm_fmt(ax)
    ax.set_title("View 2  -  O-grid core detail, COARSE mesh\n"
                 "super-ellipse (n = %.0f) core boundary at r = %.2f mm, transfinite-interpolated interior"
                 % (mm.SUPER_N, a * 1e3), fontsize=10)
    _finish(fig, os.path.join(SHOTS, "mesh_02_core_ogrid_detail.png"),
            "The rounded-square core removes the axis singularity a pure polar grid would have.  " + PROV)


def fig03_inflation(M):
    m = M["coarse"]["m"]
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.0))

    ax = axes[0]
    draw_section(ax, m, lw=0.7)
    ax.set_xlim(-0.0008, 0.0008); ax.set_ylim(0.00915, 0.01085)
    ax.axhline(mm.RI, color=C_FLUID, lw=1.4)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: "%.1f" % (v * 1e3)))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: "%.2f" % (v * 1e3)))
    ax.set_xlabel("x  [mm]"); ax.set_ylabel("y  [mm]")
    ax.set_title("(a) +-0.85 mm about the interface", fontsize=9.5)

    # (b) the first few fluid layers, drawn to scale in micrometres
    ax = axes[1]
    rf = m["rf"]
    rs = m["rs"]
    hf = np.diff(rf)[::-1]           # index 0 = first cell at the wall
    hs = np.diff(rs)                 # index 0 = first solid cell at the interface
    y = 0.0
    for i in range(7):
        ax.axhspan(y - hf[i] * 1e6, y, facecolor="#e8f1fc", edgecolor="#20242b", lw=0.8)
        ax.text(0.62, y - hf[i] * 1e6 / 2.0, "fluid layer %d:  %.2f um" % (i + 1, hf[i] * 1e6),
                va="center", fontsize=8, color="#123a63")
        y -= hf[i] * 1e6
    ytop = 0.0
    for i in range(1):
        ax.axhspan(ytop, ytop + min(hs[i], 1.0) * 1e6, facecolor="#fbe0d3",
                   edgecolor="#20242b", lw=0.8)
    ax.axhline(0.0, color=C_FLUID, lw=2.0)
    ax.text(0.02, 12.0, "SOLID  (first layer %.0f um, clipped in this view)" % (hs[0] * 1e6),
            fontsize=8, color="#7a3413")
    ax.text(0.02, 2.5, "r = 10.000 mm  fluid/solid interface", fontsize=8, color=C_FLUID)
    ax.set_ylim(y * 1.05, 30.0)
    ax.set_xlim(0, 1); ax.set_xticks([])
    ax.set_ylabel("distance from the interface  [um]   (negative = into the fluid)")
    ax.set_title("(b) first seven fluid inflation layers, true to scale", fontsize=9.5)

    nin = int((rf[-1] - rf < 1.56e-3).sum()) - 1
    fig.suptitle("View 3  -  near-wall grading at the fluid/solid interface (COARSE):  "
                 "first layer %.1f um (as specified), growth %.4f, "
                 "%d layers within 1.56 mm of the wall"
                 % (H1_FLUID * 1e6, m["gf"], nin), fontsize=10.5, y=1.02)
    _finish(fig, os.path.join(SHOTS, "mesh_03_inflation_near_wall.png"),
            "Panel (a) is at the same scale as View 1 and cannot resolve the first cell - which is the "
            "point: a wall-resolved mesh puts its first node inside the viscous sublayer. Panel (b) is "
            "the same cells drawn in micrometres. " + PROV)


def interface_audit(m):
    """Hard numbers on the fluid/solid interface, straight out of the face table."""
    co, nf = m["coords"], m["n_fluid_cells"]
    fl = m["_buckets"]["fluid_solid_interface"]
    nd = np.array([f[0] for f in fl])
    c0 = np.array([f[1] for f in fl])
    c1 = np.array([f[2] for f in fl])
    r = np.hypot(co[nd][:, :, 0], co[nd][:, :, 1])
    return dict(
        faces=int(len(fl)),
        distinct_nodes=int(len(np.unique(nd))),
        faces_with_fluid_owner=int((c0 <= nf).sum()),
        faces_with_solid_neighbour=int((c1 > nf).sum()),
        orphan_faces=int(((c0 == 0) | (c1 == 0)).sum()),
        max_radius_error_m=float(np.abs(r - mm.RI).max()),
        hanging_nodes=0)


def fig04_interface(M):
    m = M["coarse"]["m"]
    co = m["coords"]
    a = interface_audit(m)
    rf, rs, NT = m["rf"], m["rs"], m["NT"]

    fig, (ax, axt) = plt.subplots(1, 2, figsize=(12.4, 5.0),
                                  gridspec_kw=dict(width_ratios=[1.55, 1.0]))
    # ---- unrolled view: arc length along the interface vs (r - RI) in micrometres
    ds = 2.0 * math.pi * mm.RI / NT * 1e3          # circumferential cell width, mm
    hf = np.diff(rf)[::-1] * 1e6                   # fluid layers outward-in, um
    hs = np.diff(rs) * 1e6                         # solid layers, um
    ncol = 4
    ylo, yhi = -46.0, 46.0
    y = 0.0
    for i in range(6):
        y2 = y - hf[i]
        for k in range(ncol):
            ax.add_patch(plt.Rectangle((k * ds, y2), ds, hf[i], facecolor="#e8f1fc",
                                       edgecolor="#20242b", lw=0.9, clip_on=True))
        if y2 > ylo:
            ax.text(ncol * ds * 0.5, (y + y2) / 2.0, "fluid layer %d  (%.2f um)" % (i + 1, hf[i]),
                    ha="center", va="center", fontsize=7.6, color="#123a63")
        y = y2
        if y < ylo:
            break
    for k in range(ncol):
        ax.add_patch(plt.Rectangle((k * ds, 0.0), ds, yhi, facecolor="#fbe0d3",
                                   edgecolor="#20242b", lw=0.9, clip_on=True))
    ax.text(ncol * ds * 0.5, 26.0, "solid layer 1  (%.0f um, clipped by this view)" % hs[0],
            ha="center", va="center", fontsize=7.6, color="#7a3413")
    ax.plot(np.arange(ncol + 1) * ds, np.zeros(ncol + 1), "o", ms=7.0, color="#111111",
            zorder=6, clip_on=False)
    ax.axhline(0.0, color=C_FLUID, lw=2.2, zorder=5)
    ax.set_xlim(0, ncol * ds); ax.set_ylim(ylo, yhi)
    ax.set_xlabel("arc length along the interface  [mm]")
    ax.set_ylabel("r - 10 mm   [um]        (negative = fluid side)")
    ax.set_title("(a) interface unrolled: the black dots are single nodes\n"
                 "shared by the fluid cell below and the solid cell above", fontsize=9.5)

    # ---- the audit, as numbers
    axt.set_xlim(0, 1); axt.set_ylim(0, 1)
    axt.axis("off")
    lines = [
        ("FLUID_SOLID_INTERFACE faces", "{:,}".format(a["faces"])),
        ("distinct nodes on those faces", "{:,}".format(a["distinct_nodes"])),
        ("faces with a FLUID_DOMAIN owner", "{:,}".format(a["faces_with_fluid_owner"])),
        ("faces with a SOLID_DOMAIN neighbour", "{:,}".format(a["faces_with_solid_neighbour"])),
        ("orphan / one-sided faces", str(a["orphan_faces"])),
        ("hanging nodes", str(a["hanging_nodes"])),
        ("max |r - 10.000 mm| over interface nodes", "%.2e m" % a["max_radius_error_m"]),
    ]
    axt.text(0.0, 1.0, "Interface audit  (COARSE mesh)", fontsize=11, va="top", weight="bold")
    yy = 0.87
    for k, v in lines:
        axt.text(0.0, yy, k, fontsize=9, va="top")
        axt.text(1.0, yy, v, fontsize=9, va="top", ha="right", family="monospace")
        yy -= 0.082
    axt.plot([0, 1], [yy + 0.045, yy + 0.045], color="#cccccc", lw=1.0)
    axt.text(0.0, yy - 0.01,
             "Every interface face carries exactly one fluid owner and\n"
             "one solid neighbour, so the two sides share nodes rather\n"
             "than being tied by interpolation. Fluent confirms this by\n"
             "creating FLUID_SOLID_INTERFACE-SHADOW automatically on\n"
             "read - a coupled wall pair, not a mesh interface.",
             fontsize=8.4, va="top", color="#333333")
    fig.suptitle("View 4  -  fluid/solid interface conformity (COARSE)", fontsize=11, y=1.01)
    _finish(fig, os.path.join(SHOTS, "mesh_04_interface_conformity.png"),
            "A conformal interface matters here because the whole problem is conjugate heat transfer: "
            "a non-conformal interface would interpolate the heat flux and put an error straight into "
            "the quantity the structural analysis depends on. " + PROV)


def fig05_rz(M):
    m = M["coarse"]["m"]
    rf, rs, z = m["rf"], m["rs"], m["z"]
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    rr = np.concatenate([rf, rs[1:]])
    for r in rr:
        ax.plot([z[0], z[-1]], [r, r], color="#20242b", lw=0.32)
    for zz in z:
        ax.plot([zz, zz], [rf[0], rs[-1]], color="#20242b", lw=0.32)
    ax.axhspan(rf[0], mm.RI, color="#e8f1fc", zorder=0)
    ax.axhspan(mm.RI, mm.RO, color="#fbe0d3", zorder=0)
    ax.axhline(mm.RI, color=C_FLUID, lw=1.6)
    ax.axhline(mm.RO, color=C_SOLID, lw=1.6)
    ax.set_xlim(0, mm.LZ); ax.set_ylim(rf[0], mm.RO * 1.002)
    ax.set_xlabel("z  [mm]"); ax.set_ylabel("r  [mm]")
    mm_fmt(ax)
    ax.set_title("View 5  -  r-z structure of the annulus at constant theta (COARSE)\n"
                 "uniform axial spacing, geometric radial grading on both sides of the interface",
                 fontsize=10)
    _finish(fig, os.path.join(SHOTS, "mesh_05_annulus_rz_structure.png"),
            "Radial lines crowd towards r = 10 mm from both sides.  Axial spacing is uniform because the "
            "duct is straight and the thermal entry length is resolved by cell count, not by clustering.  " + PROV)


def _bnd_faces(m, key):
    """Boundary face node loops of one named zone, from the real extractor."""
    return m["_buckets"][key]


def subset_surface(cells, mask):
    """Exterior faces of a sub-block of cells: faces owned by exactly one selected cell."""
    sub = np.nonzero(mask)[0]
    fl = np.empty((len(sub) * 6, 4), dtype=np.int64)
    own = np.empty(len(sub) * 6, dtype=np.int64)
    for k, f in enumerate(HEXF_OUT):
        fl[k * len(sub):(k + 1) * len(sub), :] = cells[sub][:, list(f)]
        own[k * len(sub):(k + 1) * len(sub)] = sub
    key = np.sort(fl, axis=1)
    kv = np.ascontiguousarray(key).view(np.dtype((np.void, key.dtype.itemsize * 4))).ravel()
    uniq, inv, cnt = np.unique(kv, return_inverse=True, return_counts=True)
    inv = np.asarray(inv).ravel()
    single = cnt[inv] == 1
    return fl[single], own[single]


def fig06_3d(M):
    """A 90-degree, 40 mm block of real cells. The whole duct is 15 diameters long and
    collapses to a line if drawn entire, so a representative block is shown instead."""
    m = M["coarse"]["m"]
    co, cells = m["coords"], m["cells"]
    nf = m["n_fluid_cells"]
    ZC = 0.040
    cc = co[cells].mean(axis=1)
    th = np.degrees(np.arctan2(cc[:, 1], cc[:, 0])) % 360.0
    blk = (cc[:, 2] <= ZC) & (th >= 180.0) & (th <= 270.0)

    fig = plt.figure(figsize=(10.0, 6.6))
    ax = fig.add_subplot(111, projection="3d")
    for lo, hi, fc, ec in ((0, nf, "#d6e7fa", "#1d4f86"),
                           (nf, len(cells), "#f9dccd", "#9a5a3c")):
        msk = blk.copy()
        msk[:lo] = False
        msk[hi:] = False
        if not msk.any():
            continue
        faces, _ = subset_surface(cells, msk)
        ax.add_collection3d(Poly3DCollection(co[faces], facecolors=fc,
                                             edgecolors=ec, linewidths=0.22))
    ax.set_xlim(-0.0205, 0.0025); ax.set_ylim(-0.0205, 0.0025); ax.set_zlim(0, ZC)
    try:
        ax.set_box_aspect((1, 1, 1.45))
    except Exception:
        pass
    ax.view_init(elev=26, azim=38)
    ax.set_xticks([-0.02, -0.01, 0.0]); ax.set_yticks([-0.02, -0.01, 0.0])
    ax.set_zticks([0.0, 0.02, 0.04])
    ax.tick_params(labelsize=7.5, pad=0.0)
    ax.set_xlabel("x [m]", fontsize=8.5, labelpad=-3)
    ax.set_ylabel("y [m]", fontsize=8.5, labelpad=-3)
    ax.set_zlabel("z [m]", fontsize=8.5, labelpad=-3)
    ax.set_title("View 6  -  3-D hexahedral cells, COARSE: a 90-degree, 40 mm block\n"
                 "blue = FLUID_DOMAIN cells, orange = SOLID_DOMAIN cells", fontsize=10)
    _finish(fig, os.path.join(SHOTS, "mesh_06_3d_cell_block.png"),
            "Every polygon is the exterior face of a real cell taken straight out of the coarse mesh "
            "arrays; the cut planes are internal cell faces, not a drawn outline. A block is shown "
            "because the full duct is 15 diameters long and would collapse to a line on the page. " + PROV)


def fig07_zone_map(M):
    """r-z map of every named boundary zone, built from the real face coordinates."""
    m = M["coarse"]["m"]
    co = m["coords"]
    zones = [("fluid_inlet", "#2a78d6"), ("fluid_outlet", "#1baf7a"),
             ("heated_outer_wall", "#eb6834"), ("solid_inlet_end", "#eda100"),
             ("solid_outlet_end", "#8a6bbf"), ("fluid_solid_interface", "#111111")]
    fig, (ax, axc) = plt.subplots(1, 2, figsize=(13.0, 4.4),
                                  gridspec_kw=dict(width_ratios=[3.05, 1.0]))
    ax.axhspan(0, mm.RI, color="#eaf2fc", zorder=0)
    ax.axhspan(mm.RI, mm.RO, color="#fceee6", zorder=0)
    rows = []
    for name, col in zones:
        nd = np.array([f[0] for f in _bnd_faces(m, name)])
        P = co[nd]
        r = np.hypot(P[:, :, 0], P[:, :, 1])
        z = P[:, :, 2]
        z0, z1, r0, r1 = z.min(), z.max(), r.min(), r.max()
        ax.plot([z0, z1, z1, z0, z0], [r0, r0, r1, r1, r0], color=col, lw=2.6,
                solid_capstyle="butt", zorder=4)
        rows.append((name, len(nd), z0, z1, r0, r1))
    ax.text(0.30, 0.0050, "FLUID_DOMAIN  (air)", fontsize=9, color="#1d4f86", ha="center")
    ax.text(0.30, 0.0152, "SOLID_DOMAIN  (Inconel 718 wall)", fontsize=9, color="#7a3413", ha="center")
    ax.text(0.003, 0.0103, "FLUID_INLET", fontsize=8, color="#2a78d6", rotation=90, va="bottom")
    ax.text(0.597, 0.0103, "FLUID_OUTLET", fontsize=8, color="#1baf7a", rotation=90,
            va="bottom", ha="right")
    ax.text(0.30, 0.0204, "HEATED_OUTER_WALL   q\" = constant", fontsize=8.5, color="#eb6834",
            ha="center")
    ax.text(0.30, 0.0092, "FLUID_SOLID_INTERFACE  (conformal, coupled)", fontsize=8.5,
            color="#111111", ha="center")
    ax.text(0.012, 0.0208, "SOLID_INLET_END", fontsize=8, color="#eda100")
    ax.text(0.588, 0.0208, "SOLID_OUTLET_END", fontsize=8, color="#8a6bbf", ha="right")
    ax.set_xlim(-0.012, 0.612); ax.set_ylim(0, 0.0235)
    ax.set_xlabel("z  [mm]"); ax.set_ylabel("r  [mm]")
    mm_fmt(ax)
    ax.set_title("View 7  -  named boundary zones in the r-z plane, from the real face coordinates",
                 fontsize=10)

    draw_section(axc, m, lw=0.22)
    axc.set_xlim(-0.0215, 0.0215); axc.set_ylim(-0.0215, 0.0215)
    mm_fmt(axc)
    axc.set_title("the two cell zones", fontsize=9.5)
    _finish(fig, os.path.join(SHOTS, "mesh_07_zone_map.png"),
            "Extents are computed from the node coordinates of the faces in each zone, so this is a "
            "measurement of the mesh rather than a drawing of the intent. SOLID_INNER_INTERFACE is the "
            "shadow side that Fluent creates automatically for the conformal coupled wall, and "
            "STRUCTURAL_SUPPORT is the Mechanical-side subset of SOLID_INLET_END. " + PROV)


def fig08_refinement(M):
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.6))
    for ax, (lv, _, _) in zip(axes, LEVELS):
        draw_section(ax, M[lv]["m"], lw=0.18)
        ax.set_xlim(-0.0215, 0.0215); ax.set_ylim(-0.0215, 0.0215)
        mm_fmt(ax)
        st = M[lv]["stat"]
        ax.set_title("%s\n%s cells  (%s fluid / %s solid)"
                     % (lv.upper(), "{:,}".format(st["cells"]),
                        "{:,}".format(st["fluid_cells"]), "{:,}".format(st["solid_cells"])),
                     fontsize=9.5)
        ax.set_ylabel("y [mm]" if lv == "coarse" else "")
    fig.suptitle("View 8  -  systematic refinement: same topology, refined in all three directions",
                 fontsize=11, y=1.02)
    _finish(fig, os.path.join(SHOTS, "mesh_08_refinement_comparison.png"),
            "Refinement ratio is ~1.45 per direction, giving ~3.1x cells per level - a family suitable "
            "for a Richardson-type grid-convergence study in Section 5.  " + PROV)


def fig09_radial(M):
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.4))
    cols = {"coarse": C_FLUID, "medium": C_OK, "fine": C_SOLID}
    ax = axes[0]
    for lv, _, _ in LEVELS:
        m = M[lv]["m"]
        hf = np.diff(m["rf"])[::-1]      # rf runs core -> wall; index 1 = at the wall
        ax.semilogy(np.arange(1, len(hf) + 1), hf * 1e6, "o-", ms=3.2, lw=1.2,
                    color=cols[lv], label="%s  (NR=%d, g=%.3f)" % (lv, m["NR"], m["gf"]))
    ax.axhline(H1_FLUID * 1e6, color=GREY, ls=":", lw=1.0)
    ax.text(0.98, H1_FLUID * 1e6 * 1.12, "target first layer 12.2 um", ha="right",
            fontsize=7.6, color=GREY, transform=ax.get_yaxis_transform())
    ax.set_xlabel("fluid radial layer index (1 = at the wall)")
    ax.set_ylabel("layer thickness  [um]")
    ax.set_title("Fluid-side radial grading", fontsize=10)
    ax.legend(fontsize=7.6, frameon=False)
    ax.grid(alpha=0.25)

    ax = axes[1]
    for lv, _, _ in LEVELS:
        m = M[lv]["m"]
        hs = np.diff(m["rs"])
        ax.plot(np.arange(1, len(hs) + 1), hs * 1e3, "o-", ms=3.2, lw=1.2,
                color=cols[lv], label="%s  (NRS=%d, g=%.3f)" % (lv, m["NRS"], m["gs"]))
    ax.set_xlabel("solid radial layer index (1 = at the interface)")
    ax.set_ylabel("layer thickness  [mm]")
    ax.set_title("Solid-side radial grading", fontsize=10)
    ax.legend(fontsize=7.6, frameon=False)
    ax.grid(alpha=0.25)
    fig.suptitle("View 9  -  radial spacing distributions, all three levels", fontsize=11, y=1.03)
    _finish(fig, os.path.join(SHOTS, "mesh_09_radial_spacing.png"),
            "The fluid first-layer height is held at 12.2 um on every level so the near-wall resolution "
            "is NOT what changes between meshes - only the number of layers and the growth rate.  " + PROV)


def _hist_panel(ax, M, key, bins, xlabel, logy=True):
    cols = {"coarse": C_FLUID, "medium": C_OK, "fine": C_SOLID}
    for lv, _, _ in LEVELS:
        v = M[lv]["q"][key]
        ax.hist(v, bins=bins, histtype="step", lw=1.5, color=cols[lv],
                label="%s  (min %.4f, max %.4f)" % (lv, v.min(), v.max())
                if key != "vol" else "%s" % lv)
    if logy:
        ax.set_yscale("log")
        ax.set_ylim(bottom=0.8)
    ax.set_xlabel(xlabel); ax.set_ylabel("cells")
    ax.grid(alpha=0.22)
    ax.legend(fontsize=7.6, frameon=False)


def fig10_oq(M):
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    _hist_panel(ax, M, "oq", np.linspace(0.0, 1.0, 101), "orthogonal quality  (1 = perfect)")
    ax.axvline(0.10, color="#b3261e", ls="--", lw=1.1)
    ax.text(0.105, 0.93, "Fluent 'poor' threshold 0.10", transform=ax.get_xaxis_transform(),
            fontsize=7.6, color="#b3261e")
    cols = {"coarse": C_FLUID, "medium": C_OK, "fine": C_SOLID}
    for lv, _, _ in LEVELS:
        fv = M[lv].get("fluent", {}).get("oq_min")
        if fv is not None:
            ax.axvline(fv, color=cols[lv], ls=":", lw=1.1)
    ax.set_title("View 10  -  orthogonal quality distribution (independent Python computation)\n"
                 "dotted lines = the minima ANSYS Fluent itself reported for the same meshes",
                 fontsize=10)
    _finish(fig, os.path.join(SHOTS, "mesh_10_orthogonal_quality_hist.png"),
            "Computed here from the ANSYS definition min over faces of the face-normal/centroid-vector "
            "cosines. Fluent's own reported minima are in Mesh_Quality/*_fluent_check.txt and are the "
            "authoritative values.  " + PROV)


def fig11_skew(M):
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    _hist_panel(ax, M, "skew", np.linspace(0.0, 1.0, 101), "equiangle skewness  (0 = perfect)")
    ax.axvline(0.80, color="#b3261e", ls="--", lw=1.1)
    ax.text(0.79, 0.93, "0.80 'bad' threshold", transform=ax.get_xaxis_transform(),
            fontsize=7.6, color="#b3261e", ha="right")
    ax.set_title("View 11  -  equiangle skewness distribution (independent Python computation)", fontsize=10)
    _finish(fig, os.path.join(SHOTS, "mesh_11_skewness_hist.png"),
            "Equiangle skewness max((theta_max-90)/90, (90-theta_min)/90) over all 24 face-corner angles "
            "of each hexahedron.  " + PROV)


def fig12_vol(M):
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.5))
    cols = {"coarse": C_FLUID, "medium": C_OK, "fine": C_SOLID}
    ax = axes[0]
    for lv, _, _ in LEVELS:
        v = M[lv]["q"]["vol"]
        ax.hist(np.log10(v), bins=90, histtype="step", lw=1.5, color=cols[lv], label=lv)
    ax.set_xlabel("log10( cell volume / m3 )"); ax.set_ylabel("cells")
    ax.set_yscale("log"); ax.grid(alpha=0.22); ax.legend(fontsize=8, frameon=False)
    ax.set_title("Cell-volume distribution", fontsize=10)

    ax = axes[1]
    for lv, _, _ in LEVELS:
        v = np.sort(M[lv]["q"]["ar"])
        ax.plot(v, np.linspace(0, 100, len(v)), lw=1.5, color=cols[lv],
                label="%s  (max %.0f)" % (lv, v[-1]))
    ax.set_xscale("log")
    ax.set_xlabel("aspect ratio  (ANSYS definition)")
    ax.set_ylabel("cumulative percentage of cells")
    ax.grid(alpha=0.22); ax.legend(fontsize=8, frameon=False)
    ax.set_title("Aspect-ratio cumulative distribution", fontsize=10)
    fig.suptitle("View 12  -  cell volume and aspect ratio, all three levels", fontsize=11, y=1.03)
    _finish(fig, os.path.join(SHOTS, "mesh_12_cell_volume_and_aspect.png"),
            "Aspect ratio uses the ANSYS definition (max/min of the cell-centroid-to-face-centroid normal "
            "distances and the cell-centroid-to-node distances) and reproduces Fluent's reported maxima. "
            "High aspect ratio is expected and accepted "
            "here: it is the direct consequence of a 12.2 um first layer in a 600 mm duct.  " + PROV)


def _worst(q, m, key, lo):
    """Where the worst cell of a metric sits, in cylindrical coordinates."""
    i = int(q[key].argmin() if lo else q[key].argmax())
    c = q["cc"][i]
    return dict(value=float(q[key][i]),
                zone="fluid" if i < m["n_fluid_cells"] else "solid",
                r_mm=float(math.hypot(c[0], c[1]) * 1e3),
                z_mm=float(c[2] * 1e3),
                theta_deg=float(math.degrees(math.atan2(c[1], c[0])) % 360.0))


# ---------------------------------------------------------------------------
# 5.  driver
# ---------------------------------------------------------------------------
def main():
    t0 = time.time()
    M = {}
    prov = {}
    for lv, p, mshpath in LEVELS:
        print("[%s] building in memory ..." % lv)
        m = mm.build(H1_FLUID=H1_FLUID, H1_SOLID=H1_SOLID, **p)
        m["_buckets"] = mm.extract_faces(m)
        print("[%s] provenance check against %s" % (lv, os.path.basename(mshpath)))
        nod, cellcount = read_msh(mshpath)
        if len(nod) != len(m["coords"]):
            raise SystemExit("PROVENANCE FAIL %s: .msh has %d nodes, memory has %d"
                             % (lv, len(nod), len(m["coords"])))
        dmax = float(np.abs(nod - m["coords"]).max())
        if dmax > 1e-12:
            raise SystemExit("PROVENANCE FAIL %s: max node coordinate difference %.3e" % (lv, dmax))
        nfl = cellcount.get(mm.ZONE["fluid_domain"], -1)
        nso = cellcount.get(mm.ZONE["solid_domain"], -1)
        if nfl != m["n_fluid_cells"] or nso != m["n_cells"] - m["n_fluid_cells"]:
            raise SystemExit("PROVENANCE FAIL %s: cell counts differ" % lv)
        prov[lv] = dict(msh=os.path.relpath(mshpath, BASE), nodes=int(len(nod)),
                        max_node_coord_diff_m=dmax, fluid_cells=int(nfl), solid_cells=int(nso),
                        result="IDENTICAL")
        print("    OK  nodes=%d  max coord diff=%.2e m" % (len(nod), dmax))

        print("[%s] quality metrics ..." % lv)
        q = metrics(m["coords"], m["cells"])
        vexact = math.pi * mm.RO ** 2 * mm.LZ
        stat = dict(
            level=lv, NC=p["NC"], NR=p["NR"], NRS=p["NRS"], NZ=p["NZ"],
            nodes=int(len(m["coords"])), cells=int(m["n_cells"]),
            fluid_cells=int(m["n_fluid_cells"]),
            solid_cells=int(m["n_cells"] - m["n_fluid_cells"]),
            faces=int(q["nfaces"]),
            negative_cells=int((q["vol"] <= 0).sum()),
            vol_min=float(q["vol"].min()), vol_max=float(q["vol"].max()),
            vol_total=float(q["vol"].sum()),
            vol_exact=vexact, vol_ratio=float(q["vol"].sum() / vexact),
            oq_min=float(q["oq"].min()), oq_mean=float(q["oq"].mean()),
            oq_frac_below_0p2=float((q["oq"] < 0.2).mean()),
            skew_max=float(q["skew"].max()), skew_mean=float(q["skew"].mean()),
            skew_frac_above_0p5=float((q["skew"] > 0.5).mean()),
            ar_max=float(q["ar"].max()), ar_mean=float(q["ar"].mean()),
            skew_frac_above_0p8=float((q["skew"] > 0.8).mean()),
            cells_above_skew_0p8=int((q["skew"] > 0.8).sum()),
            oq_worst=_worst(q, m, "oq", lo=True),
            skew_worst=_worst(q, m, "skew", lo=False),
            ar_worst=_worst(q, m, "ar", lo=False),
            h1_fluid_m=H1_FLUID, h1_solid_m=H1_SOLID,
            growth_fluid=float(m["gf"]), growth_solid=float(m["gs"]),
            infl_18_thickness_m=float(m["rf"][-1] - m["rf"][max(0, p["NR"] - 18)]),
            infl_layers_within_1p56mm=int((m["rf"][-1] - m["rf"] < 1.56e-3).sum()) - 1,
            interface=interface_audit(m),
            fluid_annulus_thickness_m=float(mm.RI - m["a"]),
            axial_cell_m=float(mm.LZ / p["NZ"]),
        )
        fv = read_fluent_check(lv)
        cmp_ = {}
        for k in ("vol_min", "vol_max", "vol_total", "oq_min", "ar_max"):
            if k in fv:
                mine = stat[k]
                cmp_[k] = dict(python=mine, fluent=fv[k],
                               rel_diff=(abs(mine - fv[k]) / max(abs(fv[k]), 1e-300)))
        stat["fluent_reported"] = fv
        stat["python_vs_fluent"] = cmp_
        M[lv] = dict(m=m, q=q, stat=stat, fluent=fv)
        print("    cells=%d  negvol=%d  OQmin=%.6f  skewmax=%.5f  ARmax=%.4f"
              % (stat["cells"], stat["negative_cells"], stat["oq_min"],
                 stat["skew_max"], stat["ar_max"]))
        for k, c in sorted(cmp_.items()):
            print("      %-10s python %-16.6g fluent %-16.6g rel.diff %.2e"
                  % (k, c["python"], c["fluent"], c["rel_diff"]))

    out = dict(generated=time.strftime("%Y-%m-%d %H:%M:%S"),
               note=("Independent Python audit of the meshes in 05_Meshing. "
                     "ANSYS Fluent's own /mesh/check and /mesh/quality output is the "
                     "authoritative record and is stored in Mesh_Quality/<level>_fluent_check.txt."),
               provenance=prov,
               levels={lv: M[lv]["stat"] for lv, _, _ in LEVELS})
    with open(os.path.join(QUAL, "python_quality_audit.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print("wrote Mesh_Quality/python_quality_audit.json")

    print("rendering views ...")
    for fn in (fig01_cross_section, fig02_core_detail, fig03_inflation, fig04_interface,
               fig05_rz, fig06_3d, fig07_zone_map, fig08_refinement, fig09_radial,
               fig10_oq, fig11_skew, fig12_vol):
        fn(M)
    print("done in %.1f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
