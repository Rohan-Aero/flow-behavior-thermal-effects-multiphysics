# 08_Structural_Analysis/Workbench (Section 7A)

> RE-ANALYSIS 2026.

| Path | Content |
|---|---|
| `Flow_Behavior_Thermal_Effects_Structural.wbpj` (+ `_files`) | **Production project.** Section 4 schematic (Geometry → Mesh → Fluent placeholder) + External Data (CFD solid T) + LC1 Free Expansion + LC2 Axially Restrained. Not solved |
| `Scripts/wb_build_7A.wbjn`, `Scripts/mech_build_7A.py` | the build (IronPython journal + Mechanical script). Run with `Scripts/run_wb.ps1` / `launch_wb.ps1` (`runwb2 -B -R`) |
| `Scripts/hash_tree.ps1` | SHA-256 inventory used for the before/after integrity checks |
| `Scripts/wb_probe*.wbjn`, `mech_probe*.py` | API probes and method trials (throwaway) |
| `Audit/` | before/after hashes of the Section 4 project and the official Fluent case/data (content identical), plus `section7A_key_file_hashes.json` |
| `Logs/` | production build logs; `Superseded_run1/`, `Superseded_run2/` |
| `probe`, `probe2`, `probe5`, `probe6`, `probe7`, `probe9` | throwaway probe projects: point-cloud trials, the Workbench FLUENT-system trial, mesh-based trials. **Not part of the model**; kept as evidence for the method choice |

- **Section 4 project unchanged.** It was opened and immediately saved as the production project. Its files are unchanged apart from Workbench's `.project_cache` timestamp (content identical).
