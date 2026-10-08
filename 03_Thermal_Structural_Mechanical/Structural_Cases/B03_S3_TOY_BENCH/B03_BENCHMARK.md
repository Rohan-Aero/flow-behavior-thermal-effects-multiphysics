# B03 — toy benchmark of the S3 support implementation (Section 9B-2, Part L)

> **RE-ANALYSIS 2026.** Method check only. The toy tube has constant properties and a uniform temperature rise, so
> its answers are known in closed form. Nothing here is a project result, a recovered internship value or a measurement.

## Purpose

S3 (inlet clamped, outlet pinned) is the first support in this project that uses a Mechanical *remote point*.
Before the real S3 case was solved, the exact formulation that Mechanical wrote into the S3 solver input
(`../S3_LC2_INTERMEDIATE/Audits/Presolve_Inputs/S3_presolve_ds.dat`, deck mode, not solved) was copied into the 8A toy tube.
The real case was solved only after B03 passed.

## Toy model

- Tube Di 20 / Do 40 / L 600 mm, SOLID186.
- E 190 GPa, ν 0.294, α 13.6 × 10⁻⁶ /K (constant), uniform ΔT = 225 K.
- Exact answers: restrained force N = E·α·ΔT·A; axial stress −E·α·ΔT; free radial growth (1 + ν)·α·ΔT·r_o; clamped–pinned
  Euler load π²EI/(0.6992 L)², with and without the Cowper shear correction.

## Copied support formulation (from the real deck)

| End | Formulation |
|---|---|
| Inlet, z = 0 | every face node rotated into the cylindrical CS (x = r, y = θ, z = axial); U_θ = U_z = 0; radial free |
| Outlet, z = 0.6 m | pilot node on the axis with a TARGE170 element; CONTA174 elements on the outlet element faces (ESURF) |
| Key options (as in the real deck) | `keyo,tid,2,1` (pilot BCs user-defined), `keyo,tid,4,111111` (all 6 pilot DOFs active), `keyo,cid,2,2` (MPC), `keyo,cid,4,1` (force-distributed / deformable), `keyo,cid,12,5` (bonded always) |
| Pilot constraint | U_x = U_y = U_z = 0; rotations free |

**Note on `b03_main.inp`.** Its header comment (line 10) still says "CONTA175 on every outlet-face node". It was written before
the real deck was inspected. The element type actually defined and used is CONTA174 (`et,2,174` + `esurf`), as in the real
deck. The comment was left unchanged because the file is the one that ran.

## Runs

| Run | Mesh | Files |
|---|---|---|
| 1 | free 8A toy mesh, esize 5 mm (37,911 nodes; 62 outlet contact faces) | `b03_main.inp`, `b03_main.out`, `b03_results_run1_original_checks.json` (checks as first formulated), `b03_results.json` (re-evaluated with the reformulated checks) |
| 2 | structured: 36 equal circumferential sectors like the real model (82,585 nodes; 144 outlet contact faces) | `Structured/b03_main.inp`, `Structured/b03_results.json` |

Check script: `b03_check.py` (reformulated checks); `b03_check_v1_original_checks.py` (as first written).

## Result

**PASS (both runs).** No rigid-body motion. The inlet and pilot axial reactions equal E·α·ΔT·A and balance each other.
The static state is uniform. λ₁ lies between the plain and the shear-corrected clamped–pinned Euler values. Mode 1 is the
fixed–pinned column shape with its maximum at 0.6 L from the clamped end.

Two checks failed in run 1 as first formulated. They were reformulated without touching the model: node-mean lateral offset →
least-squares rigid translation, and an absolute lateral-reaction limit → a limit relative to N. Run 2 passes even the
original limits.

The full check table and the numbers are in `../../Results/SUPPORT_SENSITIVITY_RESULTS.md` §2.
