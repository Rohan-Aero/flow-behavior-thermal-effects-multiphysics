# S2 re-extraction - Run 1 (archived, not deleted) - RE-ANALYSIS 2026

**What ran:** `run_s2x.inp` (Run 1 version, copied here as `run_s2x_run1.inp`) read the COPY of the 8A S2 result
file (`s2.rst`, 8A SYS-6 "LC2NS No-Sway Static") and then, in the SAME MAPDL session, the COPY of the 8A S1 LC2 re-solve
(`s1.rst`, 8A SYS-3) with `s2_reextract.inp` (/POST1 only, nothing solved).

**Finding:** the S1 validation table (`s1x_nodal.csv`) disagreed with the 8A in-session table in u_r / u_theta at
1,204 nodes (max |diff| 1.79e-4 m in u_r, 8.97e-5 m in u_theta); stresses, temperatures and u_z agreed exactly.

**Cause (diagnosed with `diag_s1x.py` / `diag_s2x.py`, outputs in the conversation log and summarised here):**
MAPDL keeps the model geometry of the first result file in the database when `FILE`/`SET` switch to a second file
in the same session. The S2 solve rotated its 1,202 end-face nodes (NMOD, THXY = node angle, for the
U_z = U_theta = 0 supports in CS_DUCT_CYL); the S1 solve did not rotate them, but did rotate the 3 mid-span hoop nodes
(NROT on _CM92). Reading S1 with the S2 nodal rotations still in the database gives, per node,
u_out = R(theta - beta + alpha) u_global with beta = S2 rotation, alpha = S1 rotation:
- end-face nodes (beta = theta, alpha = 0): u_out = global (u_x, u_y) instead of (u_r, u_theta) - matches every mismatched end-face node;
- 3 mid-span nodes (beta = 0, alpha = theta): u_out = R(theta) (u_r, u_theta) - matches nodes 25862 / 25886.

**Consequence for S2:** the S2 table itself was read first, with its own geometry, and is correct. Check on the S2
data alone: max |u_theta| at the 1,202 U_theta-constrained end-face nodes = 1.24e-12 m; u_r is uniform around the
outer ring at z = 0 (5.29960e-5 to 5.29968e-5 m) and z = 0.6 m (8.97310e-5 to 8.97316e-5 m) and continuous with the
first interior node level (5.3015e-5 m).

**Earlier wrong hypothesis (not used):** a rotation correction of the S2 table (`fix_rotated`, post_9B2.py
a0bf225e / 3dfd3d7a) was written on the assumption that /POST1 had ignored the S2 rotations. It did not change the S1
comparison and is withdrawn; no reported number used it.

**Fix (Run 2):** `/clear,nostart` between the two re-extractions so each result file is read with its own geometry;
the S1 validation must then reproduce the 8A table in every column, and the S2 table must be identical to Run 1.
