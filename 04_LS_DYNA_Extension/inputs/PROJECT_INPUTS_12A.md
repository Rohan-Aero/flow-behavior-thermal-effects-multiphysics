# Section 12A — Project Inputs for the LS-DYNA Model (inventory)

> Every value below was read from the actual project files on 2026-10-02 by `input_probe_12A.py`. That is a read-only
> probe; its output is `input_probe_12A.json`, with SHA-256 and size of 29 key files.
>
> **Nothing was copied, re-meshed, re-mapped or modified.** The hashes record the baseline that a later LS-DYNA phase must
> leave untouched.

## 1. Single source of truth

The model is fully contained in the deck that Mechanical actually solved for LC2:

`08_Structural_Analysis/LC2_Restrained/Solver_Output/LC2_solve_input_ds.dat`
(240,298 lines, 15,527,234 B, SHA-256 `51d806783abc26ac2a6f89e47e3a19f079c59acb53d3655a90e21ecf6ae15b09`)

| Deck block | Lines | Content (verified) | LS-DYNA target |
|---|---|---|---|
| `/units,MKS`, `toffst,273.15` | 21, 131700 | SI units; temperatures in °C | SI (kg, m, s, N, Pa); temperatures converted to K (+273.15) |
| `local,12,1,0,0,0` | 31 | `CS_DUCT_CYL`: cylindrical, origin at the inlet centre, z = duct axis | Three node-local `*DEFINE_COORDINATE_SYSTEM` (r, θ, z) for the hoop SPCs |
| `nblock,3,,119077` | 34–108288 | **108,252** node records counted, IDs 1–108,252; z 0–0.600 m; r 0.010–0.020 m. The header value 119,077 is the MAPDL maximum-node field written by Workbench (an upper bound), not the node count | `*NODE` (IDs and coordinates kept) |
| `et,1,186`; `keyo,1,2,1`; `eblock,21,COMPACT,,23400` | 108291–108294… | **23,400 SOLID186**, 20 nodes each, full integration | `*ELEMENT_SOLID` (20-node), `*SECTION_SOLID` ELFORM 23; node order converted (gate G1) |
| `tref,26.85` | 131702 | Stress-free reference **300 K** [M014, M083] | TB = 300 K in `*LOAD_THERMAL_VARIABLE_NODE` |
| `MP`/`MPTEMP`/`MPDATA` | 131706–131740 | DENS 8190. EX 204 / 199 / 193 / 187 / 180 GPa at 20 / 100 / 200 / 300 / 400 °C. NUXY 0.294. ALPX 12.8 / 13.3 / 13.9 / 14.2 / 14.8 ×10⁻⁶ at 93.33 / 204.44 / 315.56 / 426.67 / 537.78 °C. `MPAMOD,1,21.11`. KXX (not needed) | `*MAT_004` thermo-elastic + `*MAT_ADD_THERMAL_EXPANSION` (see `material_data/`) |
| `CMBLOCK` (node components) | 131762–131814 | SOLID_INLET_END **612**, SOLID_OUTLET_END **612**, STRUCTURAL_SUPPORT (= inlet end), HEATED_OUTER_WALL, FLUID_WALL / FLUID_SOLID_INTERFACE / SOLID_INNER_INTERFACE (bore surface), NS_LC1_SUPPORT_3NODES_INLET_OUTE (18870, 18882, 18894), NS_LC2_HOOP_3NODES_MIDSPAN_OUTER (25862, 25874, 25886); element component SOLID_DOMAIN | `*SET_NODE_LIST` with the same names and members |
| `_DISPZEROUZ` + `d,all,uz,0` | 131825–131840 | **1,224** nodes, all at z = 0 or z = 0.6 m (both full end faces) | `*BOUNDARY_SPC_SET`, DOFZ = 1 (global) |
| `_CM92` `nrot` in csys 12 (131818–131822) + `_CM93U` (131843–131845) with `d,_CM93U,uy,0.` (131880) | as listed | Nodes 25862 (−120°), 25874 (0°), 25886 (+120°), at r = 20 mm, z = 0.300 m: **U_θ = 0 only** | `*BOUNDARY_SPC_NODE`, CID = local (r, θ, z) system of that node, DOFY = 1 |
| `bfblock,2,temp,108252` | 131884–240138 | **108,252** nodal temperatures, 150.687–289.408 °C = **423.84–562.56 K** (the mapped Fluent field actually solved) | `*LOAD_THERMAL_VARIABLE_NODE`: NID, TS = T_i − 300 K, TB = 300 K, LCID = λ(t) |
| `antype,0`, `nsub,1,1,1`, no NLGEOM | 131868, 240141 | Linear static, small deflection (the Mechanical baseline) | Replaced by an implicit nonlinear solution. This is the intended extension, not a change to the baseline |

## 2. Inventory by item requested in the brief

| Item | Actual file(s) | Status for LS-DYNA |
|---|---|---|
| Geometry | `03_CAD_Geometry/STEP/heated_duct.step` (`0cef81c6…`), `Native_CAD/heated_duct.scdocx`, `Geometry_Check/cad_measurements.json` | Available; **not needed** (the mesh is reused) |
| Structural mesh | LC2 deck (above); description `08_Structural_Analysis/Mesh/MESH_7A.md`, `mesh_stats_7A.json` | Available, mesh B (36 × 5 × 130, bias 4) [M081, M082] |
| Fluent solid temperature field | Mapped: LC2 deck `BFBLOCK` = `07_Thermal_Analysis/Mapping/Mechanical_Export/LC2_imported_body_temperature.txt` (`da7b7af5…`). Source: `Mapping/MeshBased/fluent_solid_mesh.cdb` + `fluent_solid_node_temperature.csv`. Verification record: `Validation/mapping_validation_7A.json` | Available. **Use the mapped nodal values directly**, which reproduces the solved field exactly with no new mapping error |
| Fluent pressure field | `07_Thermal_Analysis/Temperature_Source/fluent_interface_wall_pressure.csv`; `08_Structural_Analysis/Loads/wall_pressure_profile_7A.csv`; `Pressure_Check/…/LC2P_solve_input_ds.dat` | Available. **Not applied**, because LC2 excludes pressure by definition and the LC2P effect on the peak is +45 Pa (M097). An optional sensitivity run could add it later |
| Mechanical material definition | LC2 deck MP block; `08_Structural_Analysis/Materials/materials_7A.csv`, `MATERIAL_MODEL_7A.md` | Available (elastic only); see `material_data/MATERIAL_DATA_CHECK_12A.md` |
| LC2 supports | LC2 deck; `08_Structural_Analysis/Boundary_Conditions/BOUNDARY_CONDITIONS_7A.md` | Available. Translated one-to-one, **no change** |
| Buckling mode shape | `08_Structural_Analysis/Buckling/Mechanical/LC2_Linear_Buckling/Solver_Output/s8a_mode1.csv` … `s8a_mode6.csv` (`a5fdc844…` for mode 1); classification `Buckling/fe_modes_8A.json` | Available, with limits: **corner nodes only** (28,296 rows; mid-side nodes not exported); arbitrary scale; orientation arbitrary within the repeated pair (mode 1 points at −17.4°). Maximum lateral value at z = 0.6 m; mid-span lateral 2.9 × 10⁻⁵ of the maximum; correlation with cos(πz/L) of magnitude 0.999988; axial component ≤ 0.103 of lateral (section rotation). These are the probe's own definitions (`input_probe_12A.py`: all corner nodes, lateral component projected on the maximum-lateral direction). 8A recorded 0.999997 and 1.4 × 10⁻⁵ with its own definitions (`fe_modes_8A.json`, `BUCKLING_RESULTS.md`); both describe the same cos(πz/L) sway |
| Baseline load | `LC2_Restrained/Solver_Output/s7b_react.csv` (N = 548,936.6 N, M091); `s8a_load_factors.csv` (λ₁ = λ₂ = 1.108047, λ₃,₄ = 4.29790, λ₅,₆ = 9.22482) | Available. In LS-DYNA the load is the thermal field itself. N is an **output** to compare with |
| Coordinate system | Global Cartesian, origin at the inlet centre, z axial; `CS_DUCT_CYL` = `local,12` | Available |
| Named selections | LC2 deck `CMBLOCK` | Available (above) |

## 3. Reference results for the translation gates (unchanged baseline)

| Gate quantity | Value | Master ID / file |
|---|---|---|
| LC1 free axial growth ΔL | 1.8409 mm | M085, `LC1_Free_Expansion/Solver_Output/s7b_nodal.csv` |
| LC1 maximum von Mises | 24.282 MPa | M086 |
| LC2 axial reaction | 548,936.6 N | M091, `LC2_Restrained/Solver_Output/s7b_react.csv` |
| LC2 mean axial stress | −582.44 MPa | M092 |
| LC2 maximum von Mises | 605.161 MPa (inlet-face outer edge, 437.99 K) | M090, M093 |
| LC2 maximum total deformation | 0.1349 mm | M089 |
| S1 λ₁ (λ₂) / λ₃ | 1.10805 (repeated) / 4.2979 | M098, M107 |
| S1 P_cr | 608.25 kN | M099 |
| First-yield factor (linear, perfect) | 1.730 | M096 |

The LC1 deck (`LC1_Free_Expansion/Solver_Output/LC1_solve_input_ds.dat`, `6e56fe95…`) is the source for gate G2. Per
`BOUNDARY_CONDITIONS_7A.md` it has the same body, mesh and imported temperature field as LC2; only the LC1 three-node
supports differ. Gate G2 starts by confirming this with a deck-to-deck comparison.
