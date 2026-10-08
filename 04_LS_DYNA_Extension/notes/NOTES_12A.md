# Section 12A — Notes, Decisions and Open Items

## 1. Constraints honoured in 12A

- The final report, final presentation, Fluent results and Mechanical results were not modified, and the baseline CFD
  was not rerun. The project files read are hash-recorded in `inputs/input_probe_12A.json`.
- LS-DYNA was not run, installed or downloaded.
- No plasticity data, imperfection magnitude, support stiffness or experimental validation was invented.
- The LC2 support definition was not changed.
- The existing Mechanical conclusion is unchanged: S1 λ₁ = 1.108 stays a linear eigenvalue buckling factor of a perfect
  tube with idealised supports.

## 2. Decisions (PROJECT_STATE §25)

| ID | Decision | Reason |
|---|---|---|
| D-094 | LS-DYNA is an **additional** nonlinear analysis; the Mechanical results stay the baseline; report and deck untouched | brief |
| D-095 | **Material nonlinearity UNAVAILABLE.** Thermo-elastic only (MAT_004 without SIGY/ETAN); no bilinear or perfectly plastic substitute | no temperature-dependent stress–strain data (F-045, T-036); ETAN = 0 would be an invented curve |
| D-096 | Model source = direct conversion of `LC2_solve_input_ds.dat`: nodes, elements, materials, T_ref, 108,252 BF temperatures, LC2 SPCs. No re-mesh, no re-map, no Workbench LS-DYNA system | exact traceability to the solved baseline |
| D-097 | Imperfection shape = S1 mode 1 (from the converted model's own buckle run, cross-checked with `s8a_mode1.csv`). Amplitude = **sensitivity sweep** w₀/L = 0, 10⁻⁵, 10⁻⁴, 5 × 10⁻⁴, 10⁻³, 2 × 10⁻³, plus a mode-2 orientation check | no project tolerance; t-fraction irrelevant for a global mode; code values not applicable or verified |
| D-098 | Load parameter λ scales (T − 300 K) via `*LOAD_THERMAL_VARIABLE_NODE`; λ_max ≤ 1.42 (end of the E table at 400 °C); no displacement-controlled variant without approval | same load definition as 8A; no property extrapolation |
| D-099 | Gates G0–G4 must pass, with tolerances frozen before running, before any nonlinear result is reported. G4 (λ₁ ≈ 1.108 ± 1 %) is a hard stop. G5 (= P0, perfect geometry) is a diagnostic. G0 includes a temperature-dependent-E restrained-bar test of the material formulation | the translation is new modelling; it must reproduce the baseline first |

## 3. Findings and tasks (PROJECT_STATE §25)

| ID | Item |
|---|---|
| **F-060** (new, High for 12B) | LS-DYNA solver, LS-PrePost and LS-Run are **not installed**. The Student 2026 R1 installation did not include LS-DYNA. Only the Workbench LS-DYNA ACT extension and the R16 manuals are present |
| **F-061** (new, Medium) | **Unverified:** the implicit / double-precision capability of Ansys LS-DYNA Student; solid ELFORM 23 support in implicit buckling; and how the "128K nodes/elements" limit is counted (model: 108,252 nodes, 23,400 elements, 131,652 combined) |
| **F-062** (new, Low) | `s8a_mode1.csv` holds corner nodes only. A mode for all nodes must come from the LS-DYNA buckle run or by mid-side interpolation |
| **F-063** (new, Info) | An Ansys License Manager (FlexNet) was installed on 2026-10-01 from another product's media, with no licence file and the CVD service stopped. It is not used by this project. Machine variable `LSTC_LICENSE=Ansys` exists |
| **T-041** (new) | **User action:** download and install Ansys LS-DYNA Student (separate `.msi`; admin; accept the terms), then re-run `audit/machine_audit_12A.ps1` |
| **T-042** (new) | 12B, when instructed: gates G0–G4, then P0 (= G5 diagnostic), the I1–I5 sweep and the I4-m2 orientation check (`proposed_model/PROPOSED_MODEL_12A.md`) |
| T-035 | open; the 12A plan is the route. It runs on the idealised S1 supports, before T-034 is resolved |
| T-036 | open; the only route to material nonlinearity |
| T-034 | open; dominates every stability statement, including any LS-DYNA result |

## 4. Wording rules for any later LS-DYNA result

- Call it a "geometrically nonlinear, thermo-elastic response of the idealised LC2 (S1) model with a sensitivity
  imperfection".
- Never a factor of safety. Never "safe", "adequate", "optimal" or "best".
- Never equate a nonlinear instability load with λ₁.
- "First-yield load factor of the imperfect elastic model" is an elastic indicator, not a capacity.
- No support ranking. No combined uncertainty percentage.

## 5. External references used (read 2026-10-02)

- Ansys, *Ansys LS-DYNA Student* product page (limits, licence, use terms):
  https://ansys.synopsys.com/academic/students/ansys-ls-dyna-student
- Ansys Innovation Space, *LS-DYNA Implicit single precision/double precision error* (implicit requires double precision):
  https://innovationspace.ansys.com/forum/forums/topic/ls-dyna-implicit-single-precision-double-precision-error/
- *LS-DYNA Keyword User's Manual R16*, Vol I and II, as installed in `ANSYS Student\v261\ansys\docu`. Page numbers in
  `proposed_model/` refer to these PDFs.
