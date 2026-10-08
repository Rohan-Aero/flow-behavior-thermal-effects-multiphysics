# -*- coding: utf-8 -*-
"""SECTION 8A - classification of eigen-buckling mode shapes from the APDL corner-node tables (s8a_mode<i>.csv).
RE-ANALYSIS 2026. For each axial corner plane: rigid lateral translation of the section (mean u_x, u_y), the
remaining in-plane cross-section deformation (radial displacement minus the rigid part: Fourier n = 2 = ovalisation,
n >= 3 = lobes), and axial displacement. Reports the share of the mode that is beam-type (section moves as a rigid
body) and the lateral deflection curve w(z)."""
import numpy as np


def load_mode(path):
    a = np.loadtxt(path, delimiter=",", skiprows=1)
    return {"node": a[:, 0].astype(int), "x": a[:, 1], "y": a[:, 2], "z": a[:, 3], "ux": a[:, 4], "uy": a[:, 5], "uz": a[:, 6]}


def classify(m, L=0.6):
    x, y, z, ux, uy, uz = m["x"], m["y"], m["z"], m["ux"], m["uy"], m["uz"]
    th = np.arctan2(y, x)
    zr = np.round(z, 7)
    planes = np.unique(zr)
    W = []           # (z, wx, wy)
    res_inplane = 0.0
    tot_inplane = 0.0
    ov = []          # ovalisation amplitude per plane (n=2), lobes n>=3
    lobes = []
    for q in planes:
        k = zr == q
        wx, wy = ux[k].mean(), uy[k].mean()
        W.append((q, wx, wy))
        dx, dy = ux[k] - wx, uy[k] - wy          # in-plane deformation after removing rigid translation
        res_inplane += np.sum(dx**2 + dy**2)
        tot_inplane += np.sum(ux[k]**2 + uy[k]**2)
        ur = dx * np.cos(th[k]) + dy * np.sin(th[k])
        t = th[k]
        def amp(n):
            return 2 * np.hypot(np.mean(ur * np.cos(n * t)), np.mean(ur * np.sin(n * t)))
        ov.append(amp(2))
        lobes.append(max(amp(n) for n in (3, 4, 5, 6)))
    W = np.array(W)
    # principal lateral direction
    M = np.array([[np.sum(W[:, 1]**2), np.sum(W[:, 1] * W[:, 2])], [np.sum(W[:, 1] * W[:, 2]), np.sum(W[:, 2]**2)]])
    ev, evec = np.linalg.eigh(M)
    d = evec[:, np.argmax(ev)]
    w = W[:, 1] * d[0] + W[:, 2] * d[1]
    w_perp = -W[:, 1] * d[1] + W[:, 2] * d[0]
    # remove rigid lateral translation (the model's lateral rigid body is held only at mid-span)
    amax = np.max(np.abs(w))
    wn = w / (w[np.argmax(np.abs(w))] if amax > 0 else 1.0)
    sign_changes = int(np.sum(np.diff(np.sign(np.where(np.abs(wn - wn.mean()) < 1e-12, 0, wn - wn.mean()))) != 0))
    # curvature-based shape comparison with the two guided-column shapes and the clamped shapes
    s = W[:, 0] / L
    refs = {"guided_n1 cos(pi z/L)": np.cos(np.pi * s), "guided_n2 / clamped_n1 cos(2pi z/L)": np.cos(2 * np.pi * s),
            "pinned_n1 sin(pi z/L)": np.sin(np.pi * s)}
    corr = {}
    for k_, r_ in refs.items():
        a1 = wn - wn.mean(); b1 = r_ - r_.mean()
        corr[k_] = float(np.dot(a1, b1) / (np.linalg.norm(a1) * np.linalg.norm(b1) + 1e-30))
    beam_share = 1 - res_inplane / max(tot_inplane, 1e-300)
    return {"planes": int(planes.size), "lateral_direction_deg": float(np.degrees(np.arctan2(d[1], d[0]))),
            "beam_type_share_of_inplane_motion": float(beam_share),
            "max_ovalisation_over_max_lateral": float(np.max(ov) / (amax + 1e-300)),
            "max_lobes_over_max_lateral": float(np.max(lobes) / (amax + 1e-300)),
            "perpendicular_over_main": float(np.max(np.abs(w_perp)) / (amax + 1e-300)),
            "z_of_max_lateral_mm": float(W[np.argmax(np.abs(w)), 0] * 1e3),
            "lateral_at_ends_and_mid": [float(wn[0]), float(np.interp(0.3, W[:, 0], wn)), float(wn[-1])],
            "correlation_with_reference_shapes": corr,
            "_curve": {"z_m": W[:, 0].tolist(), "w_norm": wn.tolist(), "ovalisation_norm": (np.array(ov) / (amax + 1e-300)).tolist()}}


if __name__ == "__main__":
    import sys, json
    for p in sys.argv[1:]:
        c = classify(load_mode(p))
        c.pop("_curve")
        print(p.split("/Benchmark/")[-1] if "/Benchmark/" in p else p, json.dumps(c, indent=None))
