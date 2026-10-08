# -*- coding: utf-8 -*-
"""Section 7A - independent re-evaluation of the Fluent NODE field with the source hexahedra's trilinear shape
functions at arbitrary target points (what a mesh-based / shape-function mapping should return).

Used only to CHECK Mechanical's mapping (the load itself is mapped by Mechanical). Target points inside a source hex
are located by Newton inversion of the isoparametric map; points between the 48-gon chords and the true circle
(outside the source mesh by <= the sagitta) are evaluated at the clamped local coordinate (= projection onto the
source boundary face), mirroring Mechanical's 'Projection' outside option.
RE-ANALYSIS 2026 helper.
"""
import numpy as np

SIGN = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                 [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)


def shape(xi):
    """xi (n,3) -> N (n,8), dN/dxi (n,8,3)"""
    a = 1 + xi[:, None, :] * SIGN[None, :, :]          # (n,8,3)
    N = a.prod(axis=2) / 8.0
    dN = np.empty(a.shape)
    for k in range(3):
        o = [j for j in range(3) if j != k]
        dN[:, :, k] = SIGN[None, :, k] * a[:, :, o[0]] * a[:, :, o[1]] / 8.0
    return N, dN


class HexField:
    def __init__(self, node_xyz_by_id, conn, T_by_id, n_theta=48, dz=0.6 / 90, n_z=90):
        self.X = node_xyz_by_id           # indexable by node id
        self.T = T_by_id
        self.conn = conn
        P = node_xyz_by_id[conn]          # (ne,8,3)
        c = P.mean(axis=1)
        th = np.mod(np.arctan2(c[:, 1], c[:, 0]), 2 * np.pi)
        self.dth = 2 * np.pi / n_theta
        # angular offset of the lattice from any vertex
        v0 = P[0, 0]
        self.th0 = np.mod(np.arctan2(v0[1], v0[0]), self.dth)
        i = np.floor(np.mod(th - self.th0, 2 * np.pi) / self.dth).astype(int) % n_theta
        nodes = np.unique(conn)
        self.r_edges = np.unique(np.round(np.hypot(node_xyz_by_id[nodes, 0], node_xyz_by_id[nodes, 1]), 9))
        n_r = len(self.r_edges) - 1                        # graded radial layers of the CFD solid mesh
        rc = np.hypot(c[:, 0], c[:, 1]) / np.cos(np.pi / n_theta)   # vertex-average radius -> nominal radius
        j = np.clip(np.searchsorted(self.r_edges, rc) - 1, 0, n_r - 1)
        k = np.clip(np.floor(c[:, 2] / dz).astype(int), 0, n_z - 1)
        self.lut = -np.ones((n_theta, n_r, n_z), int)
        self.lut[i, j, k] = np.arange(len(conn))
        assert (self.lut >= 0).all(), 'lattice lookup incomplete'
        self.n = (n_theta, n_r, n_z); self.dz = dz

    def _invert(self, e, p, it=30):
        P = self.X[self.conn[e]]                          # (n,8,3)
        xi = np.zeros((len(p), 3))
        for _ in range(it):
            N, dN = shape(xi)
            x = np.einsum('ni,nij->nj', N, P)
            J = np.einsum('nik,nij->njk', dN, P)          # dx_j/dxi_k
            d = np.linalg.solve(J, (p - x)[:, :, None])[:, :, 0]
            xi += d
            if np.abs(d).max() < 1e-13:
                break
        return xi

    def evaluate(self, p):
        th = np.mod(np.arctan2(p[:, 1], p[:, 0]), 2 * np.pi)
        r = np.hypot(p[:, 0], p[:, 1])
        i = np.floor(np.mod(th - self.th0, 2 * np.pi) / self.dth).astype(int) % self.n[0]
        j = np.clip(np.searchsorted(self.r_edges, r) - 1, 0, self.n[1] - 1)
        k = np.clip(np.floor(p[:, 2] / self.dz).astype(int), 0, self.n[2] - 1)
        out_T = np.full(len(p), np.nan); out_d = np.full(len(p), np.inf); out_e = np.full(len(p), -1)
        cand = [(0, 0, 0)] + [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1) if (a, b, c) != (0, 0, 0)]
        for di, dj, dk in cand:
            todo = np.where(out_d > 1e-10)[0]               # not yet located strictly inside a source hex
            if len(todo) == 0:
                break
            e = self.lut[(i[todo] + di) % self.n[0], np.clip(j[todo] + dj, 0, self.n[1] - 1),
                         np.clip(k[todo] + dk, 0, self.n[2] - 1)]
            xi = self._invert(e, p[todo])
            dev = np.abs(xi).max(axis=1) - 1.0             # <= 0 inside
            N, _ = shape(np.clip(xi, -1, 1))
            Tv = (N * self.T[self.conn[e]]).sum(axis=1)
            b = dev < out_d[todo]
            out_T[todo[b]] = Tv[b]; out_d[todo[b]] = dev[b]; out_e[todo[b]] = e[b]
        return out_T, out_d                               # out_d > 0: outside the source mesh (clamped/projected)
