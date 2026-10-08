# Section 7A: structural model set-up (one-way CFD → thermal → mechanical). NOT SOLVED

> **RE-ANALYSIS 2026.** A newly built Workbench/Mechanical model based on the re-analysed CFD of Sections 5–6.
>
> - Nothing here is a recovered internship file or result, and no experimental data exists or is used.
> - **LC1 and LC2 are prepared but not solved.** No stress or deformation has been computed, and no parametric study has been run.

## 1. Workbench project

`08_Structural_Analysis/Workbench/Flow_Behavior_Thermal_Effects_Structural.wbpj`, built by `Workbench/Scripts/wb_build_7A.wbjn` + `mech_build_7A.py` (run 5 is the production build; see §7).

It is **the Section 4 project, opened and saved as** this file, with the structural systems added:

```
[Geom] Geometry (Geom.scdocx = the Section 4 copy of heated_duct.scdocx) ──► [SYS] Mesh (CFD mesh, Section 4) ──► [FLU] Fluent (Section 4 placeholder, never solved in WB)
   │
   ├──────────────► [SYS 2] Static Structural  "LC1 Free Expansion"      (Engineering Data, Geometry, Model, Setup)
   │                               │ shares ED, Geometry, Model
   │                               ▼
   │                [SYS 3] Static Structural  "LC2 Axially Restrained"
   │
[SYS 1] External Data "CFD solid T (baseline_medium_final)" ──► Setup of LC1 and Setup of LC2
        file 1 fluent_solid_mesh.cdb (MAPDL CDB, Master) + file 2 fluent_solid_node_temperature.csv (Node ID, T [K])
```

- **Section 4 original unchanged.** The Section 4 project (`05_Meshing/Workbench/...Multiphysics.wbpj`, 7 files) is **content-identical** before and after all builds (SHA-256, `Workbench/Audit/section4_project_hashes_*.json`). Workbench only touched the modification time of its `.project_cache` on opening.
- **Fluent baseline untouched.** The official case and data (`06_Fluent_CFD/Case|Data/baseline_medium_final.*`) are SHA-identical before and after (`Workbench/Audit/cfd_*_hashes_*.json`). They were never overwritten, re-solved or copied into a Workbench Fluent system.
- **Why External Data and not the FLUENT → Static Structural link.** The CFD was solved in standalone Fluent (Section 5). The Workbench FLUENT system cannot hold that converged solution without re-running Fluent (evidence in the mapping audit). The CFD temperature therefore enters through External Data, with a mesh-based master.

## 2. Coupling

One-way. Rationale in `07_Thermal_Analysis/THERMAL_MAPPING_NOTES.md` §2: the deformation is too small to change the flow or heat transfer, and there is no structural feedback path. **No two-way coupling is performed or claimed.**

## 3. Analysis type choice

**Direct import into Static Structural** (brief item 13). A Steady-State Thermal system was **not** added, because it would re-solve conduction that Fluent's conjugate solution already contains, and would duplicate the thermal physics. The CFD solid temperature is applied directly as the body temperature.

## 4. Temperature source and transfer

- **Source.** `baseline_medium_final` (converged, second order, Inconel `solid_domain`, no limiting, inside the property range; 19/19 checks). Source range: 423.21–562.58 K (cells and faces), 423.84–562.54 K (Fluent nodes).
- **Transfer.** Mesh-based External Data → Imported Body Temperature (Bucket Volume + Shape Functions). Outside option set to Nearest Node, but the 9,408 chord-gap nodes actually receive shape-function values of the adjacent source element (verified).
- **Mapped range.** 423.84–562.56 K on 108,252 / 108,252 nodes. 0 unmapped.
- **Error.** ≤ 0.09 K vs the source node field. ≤ 0.25 K vs the FV solution over 14–586 mm. In the first 11 mm at the inlet: up to 2.6 K at the bore and > 0.5 K through the wall (source-resolution limit, flagged).
- **Details.** `CFD_TO_MECHANICAL_MAPPING_AUDIT.md`.

## 5. Model definition

| Item | Definition | Document |
|---|---|---|
| Mesh | M36: SOLID186, 36 × 5 × 130 (bias 4), **108,252 nodes / 23,400 elements** | `Mesh/MESH_7A.md` |
| Licence | Student MAPDL limit **128,000 nodes** (measured); element limit not binding | `Licence_Check/LICENCE_CHECK_7A.md` |
| Material | Inconel_718_Re_analysis: E(T), secant α(T) from 70 °F, ν = 0.294 **[ASSUMED]**, ρ 8190, S_y scalar 1020 MPa (table kept), k(T) information only | `Materials/MATERIAL_MODEL_7A.md` |
| Reference temperature | **T_ref = 300 K**; ΔT = T(x,y,z) − 300 K | `Loads/LOADS_7A.md` |
| LC1 | 3 inlet-end outer nodes (0/120/240°): U_θ = 0, U_z = 0. Everything else free | `Boundary_Conditions/BOUNDARY_CONDITIONS_7A.md` |
| LC2 | U_z = 0 on both end faces; 3 mid-span outer nodes U_θ = 0; radial free everywhere | same |
| Pressure | gauge wall pressure prepared, **suppressed**: uniform 443.41 Pa bound, and linear fit 407.36 − 681.55·z Pa | `Loads/LOADS_7A.md` |
| Solver input files (no solve) | `Mechanical_Setup/Input_Files/LC1_Free_Expansion_ds.dat`, `LC2_Axially_Restrained_ds.dat` | this file |

## 6. What the input files prove (read back, not assumed)

**Both files:**

- 108,252 nodes, 23,400 elements, `et,1,186`.
- `TREF,26.85`.
- Material: `MPDATA,EX` (5 points), `NUXY` 0.294, `ALPX` (5 points) + `MPAMOD,1,21.11`.
- The same BF block, 108,252 nodal temperatures (423.84–562.56 K).

**LC1 file:**

- `local,12,1` (the cylindrical CS).
- `nrot` on nodes {18870, 18882, 18894}.
- `d,…,uy,0` and `d,…,uz,0` on those three nodes.
- Nothing else is constrained.

**LC2 file:**

- `nrot` on nodes {25862, 25874, 25886} and `d,…,uy,0` on them.
- `d,all,uz,0` on component `_DISPZEROUZ` = exactly the 1,224 inlet and outlet end-face nodes.

Pressure objects are suppressed, so they are absent from both files.

- **The solve command.** Write Input File always produces a complete deck: a `solve` command behind an interactive `/eof` guard, followed by Workbench post-processing commands. These decks were **not** submitted to the solver.
- **Truncated names.** Component names in the decks are cut to 32 characters, e.g. `NS_LC1_SUPPORT_3NODES_INLET_OUTE`.

## 7. Build history (nothing deleted)

| Run | Outcome | Kept in |
|---|---|---|
| 1 | LC1 correct. LC2 input truncated: Direct FE hoop constraints on inlet-face nodes that also carried U_z = 0 → "conflicting DOF constraints". Also, Tensile Yield Strength would not accept a Temperature column | `Mechanical_Setup/Superseded_run1/`, `Workbench/Logs/Superseded_run1/` |
| 2 | Crashed while probing the native MappingValidation object (protected API member) after the LC1 import | `.../Superseded_run2/` |
| 3 | Complete input files, but `CS_DUCT_CYL` was **Under-defined**: no origin definition, so Mechanical kept its placeholder geometry scoping. Both Solution objects were therefore "Underdefined" and the Workbench Setup cells "Incomplete" (found by the independent verification; diagnosed with the read-only probe 11) | `.../Superseded_run3/` |
| 4 | Stopped at the CS fix: the origin-define-by property takes a `CoordinateSystemAlignmentType`, not a `GeometryDefineByType` | `.../Superseded_run4/` |
| 5 | **Production.** CS origin defined by global coordinates (0,0,0). Otherwise identical to run 3 | current folders |

**Throwaway probe projects** (`Workbench/probe`, `probe2`, `probe5`, `probe6`, `probe7`, `probe9`) hold the API probes and the rejected-method evidence. They are not part of the model.

## 8. Remaining issues for 7B

1. **Inlet-end temperature uncertainty** within about 11 mm of the inlet end: up to 2.6 K at the bore, > 0.5 K through the full thickness. It is a CFD axial-resolution limit, not a mapping error. Treat stresses there with care; they are also dominated by the end restraint.
2. **Poisson's ratio [ASSUMED]** (T-014).
3. **No structural mesh-sensitivity study yet.** A finer level must stay below 128,000 nodes.
4. **Rigid-body check.** Mechanical warns "not enough constraints" because its check ignores Direct FE supports. 7B must confirm near-zero reaction forces in LC1 and in the LC2 hoop constraints.
5. **Yield.** Use S_y(T) at the local temperature for margins; the Engineering Data scalar of 1020 MPa is a lower bound.
6. **Pressure.** Show negligibility with the suppressed 443 Pa bound. It is excluded from the primary solutions.
7. **Geometry.** The structural mesh has true circular surfaces; the CFD solid is a 48-gon (+0.29 % volume, F-031). 9,408 outer-surface nodes lie ≤ 0.038 mm outside the source mesh. Accounted for in the mapping check.
8. **Workbench cell states.** Fixed in run 5 (see §9). Re-check that the Solution cells are ready (not Underdefined) when 7B opens the project.

## 9. Model readiness (production run 5)

- **Mechanical objects.** All objects are Fully Defined. `CS_DUCT_CYL` is Fully Defined: cylindrical, origin "Fixed" (global coordinates 0,0,0). Both imported temperatures are "Solved" (mapped). Both Solution objects are **"Not Solved"**: ready to solve, and not solved.
- **What went wrong in run 3.** `CS_DUCT_CYL` was left Under-defined (no origin definition). That propagated to "Underdefined" Solution objects and "Attention required" Model cells. It was found by the independent verification and diagnosed read-only with probe 11 (`Workbench/Scripts/wb_probe11_states.wbjn`, which opens the project and does not save it).
- **Workbench cells after run 5.**

  | Cell | State |
  |---|---|
  | Geometry | Up to Date |
  | LC1 / LC2 Model | Up to Date |
  | External Data | Up to Date |
  | LC1 / LC2 Setup and Solution | "Incomplete" (quick-help key `wb2qh_Mech_ur`) |
  | Section 4 Mesh cell | Incomplete; unchanged from Section 4 |
  | Section 4 Fluent placeholder | Unfulfilled; never used |

- **Why the Setup and Solution cells are left incomplete.** No Workbench Update was run on them, deliberately: an Update of the Solution cell would solve, which 7A forbids. The input files were written from Mechanical instead.
- **First step of 7B.** Update the LC1/LC2 Solution and confirm the cells reach Up to Date without errors.
- **Input files unchanged by the fix.** The run-5 files are identical to run 3 except for the material GUID comment and UVID lines. The BF blocks, BCs and mesh are unchanged, so the verification results are unchanged; they were re-run and are byte-identical.
