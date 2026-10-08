# Section 12B - characterise LS-DYNA buckling modes from d3eigv (read-only). Usage: python mode_check_12B.py <d3eigv> [mech_mode_csv]
import sys, json, math
import numpy as np
from lasso.dyna import D3plot
d = D3plot(sys.argv[1])
X = d.arrays['node_coordinates']; ids = d.arrays['node_ids']
U = d.arrays['node_displacement'] - X[None, :, :]
L = X[:, 2].max() - X[:, 2].min(); z0 = X[:, 2].min()
zs = np.round(X[:, 2], 9); zu = np.unique(zs)
out = {'timesteps': d.arrays['timesteps'].tolist(), 'n_nodes': int(len(ids)), 'L_m': float(L), 'modes': []}
for m in range(U.shape[0]):
    u = U[m]
    # rigid-section motion per axial station: u = t + w x (r - c), fitted by least squares (6 dof per section)
    T = np.zeros((len(zu), 2)); rigid = np.zeros_like(u)
    for k, z in enumerate(zu):
        msk = zs == z; r = X[msk] - X[msk].mean(axis=0); n = len(r)
        A = np.zeros((3 * n, 6)); A[0::3, 0] = 1; A[1::3, 1] = 1; A[2::3, 2] = 1
        # w x r = (wy rz - wz ry, wz rx - wx rz, wx ry - wy rx)
        A[0::3, 4] = r[:, 2]; A[0::3, 5] = -r[:, 1]
        A[1::3, 5] = r[:, 0]; A[1::3, 3] = -r[:, 2]
        A[2::3, 3] = r[:, 1]; A[2::3, 4] = -r[:, 0]
        c, *_ = np.linalg.lstsq(A, u[msk].ravel(), rcond=None)
        rigid[msk] = (A @ c).reshape(-1, 3); T[k] = c[:2]
    frac_rigid_lat = float((rigid ** 2).sum() / (u ** 2).sum())
    resid = u - rigid
    # dominant lateral direction
    w, v = np.linalg.eigh(T.T @ T); dirv = v[:, -1]
    t = T @ dirv
    amp = np.abs(t).max()
    c1 = np.cos(np.pi * (zu - z0) / L); c2 = np.cos(2 * np.pi * (zu - z0) / L); c3 = np.cos(3 * np.pi * (zu - z0) / L)
    corr = lambda a, b: float(np.dot(a - a.mean(), b - b.mean()) / np.linalg.norm(a - a.mean()) / np.linalg.norm(b - b.mean()))
    kz = int(np.argmax(np.abs(t)))
    imid = int(np.argmin(np.abs(zu - (z0 + L / 2))))
    ends = (T[0], T[-1])
    cos_ends = float(np.dot(ends[0], ends[1]) / (np.linalg.norm(ends[0]) * np.linalg.norm(ends[1]) + 1e-300))
    out['modes'].append({
        'mode': m + 1, 'eigen_or_time': float(d.arrays['timesteps'][m]),
        'rigid_section_energy_fraction': frac_rigid_lat,
        'max_section_deformation_over_max_lateral': float(np.linalg.norm(resid, axis=1).max() / amp),
        'max_axial_over_max_lateral': float(np.abs(u[:, 2]).max() / amp),
        'z_of_max_lateral_m': float(zu[kz]), 'midspan_over_max_lateral': float(abs(t[imid]) / amp),
        'cos_inlet_outlet_translation': cos_ends,
        'corr_cos_pi_z_L': corr(t, c1), 'corr_cos_2pi_z_L': corr(t, c2), 'corr_cos_3pi_z_L': corr(t, c3),
        'lateral_direction_deg': float(math.degrees(math.atan2(dirv[1], dirv[0]))),
    })
if len(sys.argv) > 2:
    import csv
    rows = list(csv.reader(open(sys.argv[2])))
    hdr = rows[0]; out['mech_csv_header'] = hdr
    idx = {int(i): k for k, i in enumerate(ids)}
    data = np.array([[float(x) for x in r] for r in rows[1:]])
    nid = data[:, 0].astype(int)
    out['mech_csv_rows'] = int(len(nid))
    sel = np.array([idx[n] for n in nid])
    out['mech_vs_LS_node_coordinate_max_abs_diff_m'] = float(np.abs(data[:, 1:4] - X[sel]).max())
    # columns with displacement components
    cu = [hdr.index(c) for c in hdr if c.lower() in ('ux', 'uy', 'uz', 'ux_m', 'uy_m', 'uz_m', 'u_x', 'u_y', 'u_z')]
    out['mech_disp_cols'] = [hdr[c] for c in cu]
    if len(cu) == 3:
        phi = data[:, cu].ravel()
        A = np.stack([U[0][sel].ravel(), U[1][sel].ravel()], axis=1)
        coef, *_ = np.linalg.lstsq(A, phi, rcond=None)
        proj = A @ coef
        out['mech_mode1_captured_by_LS_pair'] = float(np.dot(proj, phi) ** 2 / (np.dot(proj, proj) * np.dot(phi, phi)))
        out['mac_mode1_vs_LS1'] = float(np.dot(A[:, 0], phi) ** 2 / (np.dot(A[:, 0], A[:, 0]) * np.dot(phi, phi)))
        out['mac_mode1_vs_LS2'] = float(np.dot(A[:, 1], phi) ** 2 / (np.dot(A[:, 1], A[:, 1]) * np.dot(phi, phi)))
print(json.dumps(out, indent=1))
