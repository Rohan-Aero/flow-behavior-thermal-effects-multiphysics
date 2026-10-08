# 15_LS_DYNA_Extension — Section 12A (feasibility only)

An additional, optional nonlinear buckling analysis in LS-DYNA, planned on top of the unchanged Mechanical baseline
(S1 λ₁ = 1.108, P_cr ≈ 608 kN, N ≈ 548.94 kN). **Nothing has been run.**

| Path | Content |
|---|---|
| `LS_DYNA_FEASIBILITY.md` | **Start here.** Nine-part assessment and verdict |
| `audit/MACHINE_AUDIT_12A.md` | Installation, licence, hardware and Student-limit evidence |
| `audit/machine_audit_12A.ps1`, `audit/machine_audit_12A_output.txt` | Re-runnable read-only audit and its 2026-10-02 output |
| `audit/raw/` | Full-drive executable searches and the list of LS-DYNA-named files in the ANSYS tree |
| `inputs/PROJECT_INPUTS_12A.md` | Where every model input already exists (LC2 solver deck) |
| `inputs/input_probe_12A.py`, `inputs/input_probe_12A.json` | Read-only probe: counts, temperature range, supports, mode-1 checks, SHA-256 of 29 input files |
| `material_data/` | Material availability; decision that material nonlinearity is unavailable |
| `proposed_model/PROPOSED_MODEL_12A.md` | Keyword map, load path, gates G0–G4 (+ G5 diagnostic), imperfection sweep, output definitions |
| `notes/NOTES_12A.md` | Decisions D-094 to D-099, findings F-060 to F-063, tasks T-041 and T-042, wording rules, references |
| `results/` | Empty: no run made |

**Verdict.**

- Not runnable today: LS-DYNA is not installed.
- After the user installs Ansys LS-DYNA Student, a geometrically nonlinear thermo-elastic imperfection-sensitivity study
  is conditionally feasible: only if gates G0–G4 pass.
- An elastic–plastic study is not feasible, because there is no plastic stress–strain data.
