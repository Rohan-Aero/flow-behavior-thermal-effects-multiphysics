# Exports (Section 7B, RE-ANALYSIS 2026)

Mechanical `ExportToTextFile` output of every result object of the solved 7B project, one folder per case (LC1, LC2, LC2P).

- **Columns.** Node Number (or Element Number for Structural_Error), then the value in SI units: Pa, m, J, or strain.
- **Precision.** Mechanical writes 5 significant digits. The full-precision values are in `<case>/Solver_Output/s7b_nodal.csv`. The two agree to ≤ 5 × 10⁻⁵ at the corner nodes.
- **What is not exported.** The unaveraged von Mises (element-nodal) is not exported; its maximum is in `Audits/mech_solve_7B_summary.json`.
