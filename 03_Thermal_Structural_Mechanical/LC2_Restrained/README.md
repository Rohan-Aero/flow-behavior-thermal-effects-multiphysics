# LC2_Restrained (Section 7B, RE-ANALYSIS 2026)

LC2 axially restrained, **thermal only**. This is a new solution of the 7A model; it is not a recovered original.

**Restraint.**

- U_z = 0 on both complete end faces (1,224 nodes).
- 3 mid-span outer nodes with U_θ = 0.
- Radial motion free everywhere.

**Load.** The mapped CFD temperature field, with T_ref = 300 K.

`Solver_Output/` has the same file set as LC1: exact input, `solve.out`, `file0.err`, `s7b_nodal.csv` (stresses valid at corner nodes only), and the reactions of all 1,227 constrained nodes (`s7b_react.csv`, nodal CS).

Results: `../STRUCTURAL_RESULTS.md` §4. Audit: `../STRUCTURAL_AUDIT.md`.
