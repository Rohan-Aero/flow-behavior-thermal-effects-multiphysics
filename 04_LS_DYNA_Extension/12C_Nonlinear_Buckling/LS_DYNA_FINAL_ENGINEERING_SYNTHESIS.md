# LS-DYNA extension (12A–12C): final engineering synthesis

> **Status.** The LS-DYNA extension is **complete in its reduced final scope**:
> - 12A feasibility audit;
> - 12B installation and baseline gates (decision YELLOW: all gates pass, with quantified offsets);
> - 12C three-point nonlinear imperfection sensitivity study (C1/C3/C5), plus the perfect-geometry reference C0.
>
> **What it is not.** This is additional work performed as an extension of the internship project. It is **not**:
> - part of the original project results;
> - experimental validation;
> - a replacement for the Mechanical eigenvalue result;
> - a statement of real-world structural adequacy.
>
> No number in it is a factor of safety. The final report and presentation have **not** been modified.

## 1. Original project (unchanged)

| Item | Value |
|---|---|
| Method | ANSYS Mechanical, LC2 (restrained thermal expansion) |
| Temperature field | Fluent `baseline_medium_final` (423.84–562.56 K) |
| Linear eigenvalue buckling | λ₁ = 1.10805 on the LC2 thermal-stress state, i.e. P_cr = λ₁ × 548.94 kN = **608.25 kN**, global guided-sway mode |
| Peak von Mises (7B) | 605.16 MPa at the outer edge of the inlet face |

## 2. What the LS-DYNA extension established

1. **The model can be reproduced in a second solver** (12B).
   - LS-DYNA R16.1 Student (implicit, double precision, 20-node solids) reproduces the Mechanical LC2 static state:
     peak VM 605.160 vs 605.161 MPa at the same node.
   - It reproduces the linear buckling result: λ₁ = 1.1095, +0.13 % raw / −0.64 % kinematics-corrected, with the same mode
     (vector agreement 0.9999998).
   - The two offsets are quantified:
     - large-deformation kinematics, about +0.77 %;
     - integration rule, about −0.65 %.
2. **The magnitude of the Mechanical critical load is supported by an independent nonlinear analysis** (12C).
   - The Southwell critical-load estimates of the three imperfect cases are 612.3 / 611.1 / 607.7 kN, i.e. −0.1 % to
     +0.7 % of the Mechanical P_cr.
   - They are almost independent of the imperfection amplitude.
   - The smallest imperfection (0.1 mm) reaches an interior maximum of 601.0 kN (98.8 % of P_cr) at λ = 1.185.
3. **The actual response is gradual, not a sudden bifurcation.**
   - With imperfections in the buckling-mode shape, lateral deflection and bending stress grow from the start of loading.
   - At the LC2 temperature field (λ = 1), the imperfection amplitudes studied give:
     - end lateral translations of 0.85 / 3.71 / 5.32 mm;
     - axial-force reductions of 0.2 / 4.0 / 9.0 % against the perfect path;
     - peak von Mises increases of 14 / 60 / 82 % against the perfect value (605 MPa).
4. **No local or shell-type mode and no snap-through or collapse were found.**
   - The response stays in the single global guided-sway mode.
   - Under the deformation-controlled thermal load, the post-critical state carries an almost constant axial force while
     the sway grows (10–11 mm at λ = 1.3).
   - The C1 maximum and its slow decline follow the falling critical load of the heated tube as E(T) decreases with the
     scaled temperatures.
5. **The critical location is confirmed.**
   - It is the outer edge of the inlet face (437.99 K at λ = 1), as in the original 7B result, in every case.
   - Mid-span carries little bending in this mode and is not critical.

## 3. Limits that control how these results may be used

- **Elastic only.**
  - The elastic-validity indicator VM / S_y(T) reaches 1 at λ = 1.109 / 1.031 / 0.974 (0.1 / 0.6 / 1.2 mm).
  - For the 1.2 mm amplitude it is exceeded slightly at λ = 1 (1.055).
  - Beyond these points the elastic results, including stresses above S_y(T), are not physical.
  - An elastic-plastic analysis was not part of the scope and was not performed.
- **Numerical imperfections.** 0.1 / 0.6 / 1.2 mm are sensitivity values, not manufacturing tolerances. No statement
  about the real component follows from them.
- **Three points only.** C2, C4, the step-size check N1 and the perfect-geometry bifurcation check C0b were not run.
- **Bifurcation of the perfect geometry not identified.** The perfect run did not buckle on its own and the solver's
  default setting ignores negative eigenvalues.
- **Mesh and step size.** Mesh independence of the nonlinear response is not claimed, and step-size sensitivity was not
  quantified in 12C.
- **Load scaling beyond the operating point.** λ scales the temperature rise. Values above λ = 1 are load-scaled
  states, not operating conditions.

## 4. Suggested wording if the user later decides to mention the extension (not applied)

> *An additional geometrically nonlinear LS-DYNA analysis was performed after the internship as an extension. It used
> the same LC2 thermal load with mode-shaped numerical imperfections of 0.1, 0.6 and 1.2 mm. The resulting critical-load
> estimates (607.7–612.3 kN) agree with the Mechanical eigenvalue result (608.2 kN) to within about 1 %. The analysis
> also showed that lateral deflection and bending stress grow progressively below this load and that the elastic model's
> validity limit is reached near λ ≈ 1 for the larger imperfections. The extension does not replace the original
> eigenvalue result and is not an experimental validation.*

Any change to the report or presentation needs a separate instruction.

## 5. Where to find everything

| Topic | Location |
|---|---|
| 12A | `15_LS_DYNA_Extension/` (feasibility audit) |
| 12B | `15_LS_DYNA_Extension/LS_DYNA_GATE_STATUS_12B.md` and gate files; `work_12B/` |
| 12C results | `12C_Nonlinear_Buckling/FINAL_12C_RESULTS.md` |
| 12C tables | `IMPERFECTION_SENSITIVITY.csv`, `MECHANICAL_vs_LSDYNA.csv` |
| 12C audit | `RESULTS_AUDIT_12C.md` |
| 12C figures | `plots/F1–F8` |
| 12C runs | `runs/` |
| 12C data and scripts | `results/`, `comparisons/` |
| 12C protection audit | `audit/` |
| Project log | `PROJECT_STATE.md` §25–§27 |
