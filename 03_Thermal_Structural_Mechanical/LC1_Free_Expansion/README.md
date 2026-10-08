# LC1_Free_Expansion (Section 7B, RE-ANALYSIS 2026)

LC1 free thermal expansion, **thermal only**. This is a new solution of the 7A model; it is not a recovered original.

**Restraint.** 3 inlet-end outer nodes (0/120/240°) with U_θ = U_z = 0 in `CS_DUCT_CYL`. Nothing else is restrained.

**Load.** The mapped CFD temperature field (`baseline_medium_final`), with T_ref = 300 K.

`Solver_Output/`, copied from the solver working directory of the solved 7B project:

| File | Content |
|---|---|
| `LC1_solve_input_ds.dat` | exact solver input (sparse direct; includes the post snippet) |
| `solve.out`, `file0.err` | MAPDL output and warnings |
| `s7b_nodal.csv` | full-precision nodal table in CS_DUCT_CYL: node, x, y, z, u_r, u_θ, u_z, σ_r, σ_θ, σ_z, σ1, σ3, σ_vm, ε_el,eqv, T_used (°C). **Stresses and strains are valid at corner nodes only**: MAPDL writes 0 at SOLID186 midside nodes |
| `s7b_react.csv`, `s7b_prrsol.txt`, `s7b_totals.txt` | reactions of the 3 constrained nodes (nodal CS; PRRSOL in global) and their sums |
| `file.DSP`, `file.mntr` | solver diagnostics |

Results: `../STRUCTURAL_RESULTS.md` §3. Audit: `../STRUCTURAL_AUDIT.md`.
