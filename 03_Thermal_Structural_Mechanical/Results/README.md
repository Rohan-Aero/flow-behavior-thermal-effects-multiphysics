# Results (Section 7B, RE-ANALYSIS 2026)

All files here are computed from the solved 7B model by the scripts in `Scripts/`. Nothing is typed in by hand.

| File | Content |
|---|---|
| `post_7B_results.json` | everything used in STRUCTURAL_RESULTS / AUDIT: temperature check, extremes and locations, native vs table cross-check, reactions and moments, section forces, LC1 expansion checks, Timoshenko comparison, LC2 analytical force, pressure and Lamé check, utilisation with S_y(T), 6B sensitivities, structural error, near-end and ring data |
| `results_summary_7B.csv` / `.md` | summary table LC1 / LC2 / LC2P |
| `critical_locations_7B.csv` / `.md` | critical location table (Case / Quantity / Value / Location / Temperature / Yield basis) |
| `axial_profile_LC1.csv`, `_LC2.csv`, `_LC2P.csv` | 131 corner planes: T (bore, outer, mean), u_z, u_r, von Mises, σ_z, σ_θ, section force, thermal strain, E(T) |
| `hand_checks_7B.json` | indicative hand checks used only for interpretation (Section 2 factor decomposition, LC2/LC1 ratio, F-035 bound, buckling estimate). **Not FE results** |
| `run_stdout.txt` | console output of `post_7B.py` |

**Re-running.**

1. Set `S7B_PROJECT_ROOT` to the project folder, and `S7B_OUT` / `S7B_FIG` to output folders.
2. Run in this order: `post_7B.py` → `hand_checks_7B.py` → `tables_7B.py` → `plots_7B.py`.
3. Requirements: Python 3 with numpy and matplotlib.
