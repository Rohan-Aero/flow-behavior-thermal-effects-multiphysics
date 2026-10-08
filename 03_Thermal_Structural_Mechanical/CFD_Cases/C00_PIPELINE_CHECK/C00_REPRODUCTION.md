# C00_PIPELINE_CHECK: reproduction of P00_BASELINE by the parametric automation

> **RE-ANALYSIS 2026.** C00 is a new Fluent run of the frozen P00 case. It was made through the Section 9B-1 parametric pipeline (`CFD_Cases/Journals/solve_param.py`). The reference is the Section 5B solution in `06_Fluent_CFD`. Neither run is a recovered internship result.

## 1. What C00 exercises

C00 goes through every step that the six parametric cases go through, in the same order:

1. Read the P00 case for its settings only.
2. `mesh.replace` with the case mesh (for C00, the P00 medium mesh itself).
3. Settings-tree diff after the replace, which must be 0.
4. Apply the case change (none for C00).
5. Frozen-physics gate: the second diff must show only the allowed paths (none for C00).
6. Re-assert the Inconel density.
7. Set the start-up schemes.
8. Move the monitor file.
9. The 133-row read-back audit.
10. Staged start: 150 flow-only iterations, then 150 energy iterations.
11. One switch to second order.
12. Property-table and solver-message check after every iterate call.
13. Convergence evaluations, then the 100-iteration confirmation.
14. Reports, exports, and EnSight export.

## 2. Tolerance, fixed before the run

The tolerances are in `CFD_Results/Scripts/c00_compare.py`, which was committed to the device before the C00 run was launched.

- **Δp:** 0.1 %.
- **Temperatures:** 0.1 K.
- **Q and y⁺:** 0.1 %.
- **ṁ:** 0.01 %.
- **Mass and energy balance:** C00 must itself satisfy the 5B acceptance (< 10⁻⁴ and < 5 × 10⁻³).

The Δp and temperature values come from the C00 row of `PARAMETRIC_CASE_MATRIX.csv`. The Q and ṁ values are the plateau criteria to which P00 itself is converged.

## 3. Result: PASS, with zero difference

| Quantity | P00 (5B) | C00 | Difference | Tolerance |
|---|---|---|---|---|
| Δp, area-weighted static [Pa] | 438.12633 | 438.12633 | 0 | 0.1 % |
| T_out, mass-weighted [K] | 368.93236 | 368.93236 | 0 | 0.1 K |
| Q, heated wall [W] | 602.75524 | 602.75524 | 0 | 0.1 % |
| T max solid, outer-wall facet [K] | 562.57678 | 562.57678 | 0 | 0.1 K |
| T max solid, cell centre [K] | 562.12710 | 562.12710 | 0 | 0.1 K |
| T max interface (near-wall air) [K] | 555.26709 | 555.26709 | 0 | 0.1 K |
| T max fluid [K] | 553.41308 | 553.41308 | 0 | 0.1 K |
| y⁺ min / mean / max | 0.20816 / 0.24096 / 0.58484 | identical | 0 | 0.1 % |
| ṁ in / out [kg/s] | 8.6621551 × 10⁻³ | identical | 0 | 0.01 % |
| Re in / out | 29 958.17 / 25 544.91 | identical | 0 | — |
| Mass imbalance | 7.009 × 10⁻¹⁵ | 7.009 × 10⁻¹⁵ | 0 | < 10⁻⁴ |
| Energy imbalance | 3.078 × 10⁻¹³ | 3.078 × 10⁻¹³ | 0 | < 5 × 10⁻³ |
| Iterations; convergence reached / confirmed | 700; 600 / 700 | 700; 600 / 700 | 0 | — |

**Stronger than the tolerance.** The histories match exactly, not just the final values:

- All 29 monitors at every one of the 700 iterations are **bit-identical** (`C00_monitor_history_comparison.json`: 700 of 700 rows identical, maximum absolute difference 0.0).
- The EnSight Gold solid-temperature export written by C00 is **byte-identical** to the Section 7A export that the structural mapping uses (`07_Thermal_Analysis/Temperature_Source/EnSight`). All five files have the same SHA-256.

The parametric pipeline therefore reproduces P00 exactly, including the temperature source that Section 9B-2 will map. The difference between C00 and P00 is 0, which is below any numerical tolerance.

**Why exact reproduction is expected.**

- It is the same executable, mesh, partition count (4), settings, initial field and iteration sequence.
- Fluent's coupled solver is deterministic under those conditions.
- `mesh.replace` with the identical mesh changed nothing (settings diff 0).

## 4. Journal version

C00 was run with journal version 1: `Journals/Archive/solve_param_v1_used_for_C00.py` (SHA-256 `9A4754C6…78802`).

After C00, two lines of the journal were changed before any parametric case was run:

- The V cases now keep P00's initial field instead of taking the initial z-velocity from the new inlet. This keeps the frozen-physics diff to the two paths approved in 9A.
- Each run now records the SHA-256 of its journal, case table and mesh.

C00 executes neither changed line. The only other change is the text label of one audit row. The full diff is in `Journals/Archive/diff_v1_to_v2_solve_param.txt` and `diff_v1_to_v2_param_cases.txt`.

**Decision: C00 PASSES, so the parametric cases may proceed** (9B-1 brief: "If the control run does not reproduce the baseline … STOP").
