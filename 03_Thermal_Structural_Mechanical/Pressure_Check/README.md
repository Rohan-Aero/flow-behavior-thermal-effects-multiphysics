# Pressure_Check (Section 7B, RE-ANALYSIS 2026)

**LC2P = LC2 + internal pressure.** Thermal + pressure. This is a new solution; it is not a recovered original.

**Load.**

- Uniform **443.41 Pa gauge** normal to the bore (outward).
- 443.41 Pa is the CFD wall static pressure at the first station, the maximum of the CFD distribution, so it is a bound.
- It is a differential internal − external pressure. The 101,325 Pa operating pressure is **not** applied.
- In the solver it is carried by 4,680 SURF154 elements on the bore.

**Unchanged from LC2.** Restraints and temperature field are identical to LC2, verified in the solver input.

**Result.**

- Max von Mises 605.160918 MPa, against 605.160873 MPa for LC2: **+45 Pa (+7.4 × 10⁻⁶ %)**.
- Lamé check of LC2P − LC2 at mid-span: σ_θ at the bore within −0.3 %.
- The pressure is negligible, and this is confirmed by calculation.

`Solver_Output/` has the same file set as LC2.

Details: `../STRUCTURAL_RESULTS.md` §5 and `../Figures/F7B_04_pressure_effect.png`.
