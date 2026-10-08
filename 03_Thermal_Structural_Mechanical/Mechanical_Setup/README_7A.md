# 08_Structural_Analysis/Mechanical_Setup (Section 7A)

> RE-ANALYSIS 2026. **Nothing in this folder is a solved result.**

| Path | Content |
|---|---|
| `Input_Files/LC1_Free_Expansion_ds.dat` | MAPDL solver input written by Mechanical (*Write Input File*) for LC1. Mesh, material, TREF, the 3-node Direct FE support, and the mapped nodal temperatures (BFBLOCK, °C) |
| `Input_Files/LC2_Axially_Restrained_ds.dat` | the same for LC2: end faces U_z = 0 plus the 3 mid-span hoop constraints |
| `Logs/mech_build_7A_log.txt`, `mech_build_7A_summary.json` | log and machine-readable summary of the production build (run 3): mesh metrics, support nodes, mapping settings, BC objects, analysis settings, Mechanical messages |
| `Superseded_run1/`, `Superseded_run2/` | earlier build runs, kept as evidence. Run 1: truncated LC2 input (DOF conflict). Run 2: stopped after the LC1 import |

- **About `solve`.** Both input files end with `solve`, because Write Input File always writes a complete deck. They have **not** been run.
- **Section 7B.** 7B will solve LC1/LC2 from the Workbench project, not by hand-editing these files.
