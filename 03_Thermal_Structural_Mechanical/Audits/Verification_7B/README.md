# Verification_7B (Section 7B, RE-ANALYSIS 2026)

This is an independent re-computation of the 7B key results, written separately from `Results/Scripts/post_7B.py`. It uses the raw solver tables only:

- `*/Solver_Output/s7b_nodal.csv`, `s7b_react.csv`, `s7b_prrsol.txt`, `s7b_totals.txt`;
- the EBLOCK and BFBLOCK of `Mechanical_Setup/Input_Files/LC2_Axially_Restrained_ds.dat`;
- the 7A mapped-temperature export;
- `Audits/presolve_audit_7B.json` and `mech_solve_7B_summary.json`.

It was run in the cloud workspace (Python 3, numpy, scipy). The paths inside the scripts point to that workspace's copy of the project; change `B` to run them elsewhere.

**Run order:** `ver1.py` first (it writes `corner_mask.npy`), then `ver2.py` … `ver8.py`.

| Script | Checks |
|---|---|
| ver1 | corner/midside split; maxima, minima and locations for LC1, LC2 and LC2P; T_used vs the 7A export |
| ver2 | reactions: nodal-CS transformation, force and moment sums, end-face forces, PRRSOL totals; solve states |
| ver3 | free growth, restrained force (6-radius rule), pressure difference and Lamé, utilisation, mid-span values |
| ver4, ver5 | the free-growth and restrained-force integrals with finer quadrature rules (the quadrature sensitivity) |
| ver6 | 6B sensitivities, uniform-shift utilisation, Timoshenko check in the ε_th(T) form |
| ver7 | remaining location claims, outlet-end profiles, BFBLOCK vs T_used, the pre-solve gate, reaction probes |
| ver8 | windowed maxima (50–550 mm); Mechanical result maxima vs the snippet table |

**Outcome.** Everything was confirmed except four rounding or wording items, which were corrected. Nothing changed in the results. See `STRUCTURAL_AUDIT.md` §15.
