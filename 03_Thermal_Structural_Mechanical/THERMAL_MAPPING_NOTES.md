# Section 7A: Fluent solid temperature to Mechanical (thermal mapping notes)

> **RE-ANALYSIS 2026.** Everything here was newly generated in 2026 from the re-analysed CFD model of
> Sections 5–6. It is not a recovered internship result, and no experimental measurement is involved.
> All figures are post-processed simulation data (Python/matplotlib), **not ANSYS screenshots**.

## 1. Source: frozen CFD solution

| Item | Value |
|---|---|
| Case | `06_Fluent_CFD/Case/baseline_medium_final.cas.h5`. SHA-256 `84D6511B…8204`, 5,000,324 B |
| Data | `06_Fluent_CFD/Data/baseline_medium_final.dat.h5`. SHA-256 `F05837C5…352F`, 8,546,549 B |
| Status | Converged medium solution of Section 5B (700 iterations). Mesh-independence status in Section 6B |
| Not used as the load | Section 2 analytical field, Section 5A field, coarse and fine solutions (the fine solution is reference only) |
| Integrity | Case and data SHA-256 checked before and after **every** Fluent export run and the Workbench build. All identical (`Temperature_Source/Audit/`, `08_Structural_Analysis/Workbench/Audit/`) |

### Source verification

Read back from the loaded case by `Temperature_Source/Journals/export_solid_temperature.py`. Result: **19/19 checks pass** (`Audit/source_verification.json`).

- **Solver and models.** Fluent 2026 R1, steady, energy on, k-ω SST.
- **Discretisation.** Second order on all five equations: pressure second-order; momentum, k, ω and energy second-order upwind.
- **Solid zone.** A single solid zone, `solid_domain`, material `inconel-718`, ρ = 8190 kg/m³. k(T) and cp(T) are piecewise-linear on VDM 4127 over 293.15–673.15 K.
- **Boundary conditions.**
  - Heated outer wall: 8000 W/m².
  - Interface: coupled on both sides.
  - Solid end faces: adiabatic.
- **No temperature limiting.** Solver limits are 1–5000 K. The field spans 423.2–562.6 K, far from both limits.
- **Inside the property tables.** The whole solid field (423.2–562.6 K) lies inside the 293.15–673.15 K range of the k/cp tables. No extrapolation.
- **Fluent's own reports on the loaded data** (no iteration):
  - solid cell T: 423.97–562.13 K; volume mean 525.48 K;
  - heated-wall face maximum: 562.58 K;
  - Q(heated wall) = Q(interface) = 602.755 W; net −1.9×10⁻¹⁰ W.

## 2. Coupling: one-way, no two-way coupling

The chain is Fluent (converged CHT) → solid temperature T(x,y,z) → Mechanical imported body temperature → thermal strain α(T)·(T − T_ref) → stress.

One-way coupling is valid here for three reasons:

1. The structural deformation is expected to be microscopic compared with the 10 mm flow passage. Section 2 estimated about 2 mm of free axial growth over 600 mm, and much less radially. That changes neither the flow path nor the heat-transfer area measurably.
2. The loads fed back from the structure to the fluid (wall motion, gap changes) do not exist in this steady, rigid-duct problem.
3. Mechanical stress does not change the thermal properties.

**A two-way (FSI) solution is therefore neither needed nor performed**, and no two-way result is reported anywhere.

## 3. Transfer method (chosen, and the ones rejected)

### Selected: mesh-based External Data (CDB master + Fluent node temperatures), mapped by Mechanical with shape functions

1. **Native Fluent export of the solid cell zone** (read-only run): `file.export.ensight_gold`. It contains the solid mesh (43,200 hexahedra, 48,048 nodes) and **Fluent's own node temperatures** (`Temperature_Source/EnSight/solid_domain_T.*`, journal `export_solid_ensight.py`).
2. **Source mesh as an MAPDL CDB.**
   - `Mapping/Scripts/fluent_solid_mesh_from_case.py` reads the solid-zone nodes and cells from the case file and assembles each hexahedron from its own faces. No structure is assumed. Fluent node and cell ids are preserved.
   - MAPDL (Student 2026 R1, PREP7 only) reads it and writes the native blocked CDB (`Mapping/MeshBased/fluent_solid_mesh.cdb`).
   - MAPDL shape checks: 43,200 SOLID185 elements, **0 warnings, 0 errors**.
3. **Node temperatures keyed by node id.**
   - `Mapping/Scripts/build_mesh_based_source.py` writes `fluent_solid_node_temperature.csv` (node_id, T_K).
   - No value is interpolated or created: the EnSight node values are only re-keyed.
4. **Workbench External Data.** The CDB is the **Master**, and the CSV provides `Node ID` and `Temperature [K]` → Static Structural (LC1, LC2) → **Imported Body Temperature**:
   - Mapping Control: Manual, **Bucket Volume + Shape Functions**. The target nodes are located inside the Fluent hexahedra and interpolated with their trilinear shape functions.
   - Outside option set to **Nearest Node**. In the written input file, however, the chord-gap nodes (§4) carry **shape-function values of the adjacent source element**, i.e. a projection, not nearest-node values. Verified: 0 of the 9,408 gap nodes equal their nearest source-node value, and all agree with the clamped shape-function evaluation to ≤ 0.092 K (§5).

**Why this is technically valid.** It is Mechanical's own mesh-to-mesh mapping. The source field is Fluent's own nodal reconstruction, the same values Fluent and CFD-Post display as node values. No temperature is fabricated or hand-interpolated.

### Rejected methods, with evidence (`Validation/rejected_methods_evidence.json`)

| Method tried | Result | Why rejected |
|---|---|---|
| Point cloud (cell and face centroids, 52,800 points), Triangulation, outside = Projection | Mechanical flagged **77,088 / 111,216 nodes as "outside"**; 27,696 nodes got no temperature; max error 3.6 K; 2.3 K away from the ends | The 3-D Delaunay triangulation of the structured CFD lattice (points on 92 planes, graded rings) is degenerate. The failure appears in the interior, not only at the surfaces |
| Same, outside = Nearest Node | all nodes mapped; max error 4.0 K; mean 0.27 K | same triangulation failure, hidden by nearest-node filling |
| Same, "Bucket Volume" requested | identical to the first row | the point cloud has no elements for the bucket algorithm |
| Kriging / radial basis functions on the point cloud (probe 8) | import failed ("Object reference not set…") | not usable in batch; also isotropic neighbour search on an anisotropic lattice |
| Workbench FLUENT system (case imported with `FileType="CffCase"`, converged data as initial data or read in the editor) → Solution → Static Structural | Solution cell stayed **Out of Date**. The data held by the Workbench system was the **initialised** field (T = 300 K uniform), not the converged data (HDF5 comparison, probe 6). No imported-load group was created | Making it usable would need a Workbench Solution Update, which re-iterates Fluent and creates a new solution instead of the frozen one. Mark-Up-To-Date without data would be a false status |
| Fluent `export.mechanical_apdl` (volume mesh + data) | "currently inactive" in this case | not available |
| Mesh-based, Program Controlled (outside property shown as Weighted Average) | interior exact, but **2.35 K error** on the 9,408 outer-surface chord-gap nodes | the written file gives those nodes **exactly the nearest source-node value** (checked: all 9,408 equal it). The nearest node can lie a whole source cell away along the surface, so the value is off by up to 2.35 K |

## 4. Structural target mesh (M36; details in `08_Structural_Analysis/Mesh`)

- **Elements:** SOLID186, swept. 36 circumferential × 5 through-wall (2.0 mm each) × 130 axial, bias 4, fine at both ends (2.13 → 8.51 mm).
- **Size:** 108,252 nodes (84.6 % of the measured 128,000-node Student limit), 23,400 elements.
- **Geometry difference.** The target surfaces are **true circles** (r = 10 and 20 mm). The Fluent solid is a 48-sided polygon with its vertices on those circles.
  - Volume: 5.6549×10⁻⁴ m³ (target) vs 5.6387×10⁻⁴ m³ (Fluent): +0.29 %, the known faceting of F-031.
  - Consequence: **9,408 target nodes**, all on the **outer** surface between polygon vertices, lie outside the source mesh by at most **0.038 mm** (the sagitta bound is 0.043 mm).
  - The inner-surface arc nodes lie *inside* the source solid, because the chord is nearer the axis. A further 3,136 outer nodes at the vertex angles coincide with the polygon to round-off.
  - Mechanical's own outside flag in the identical program-controlled probe is also 9,408.

## 5. Mapping verification (Section 7A production files)

Independent check with `Validation/validate_mapping_7A.py`. It reads the **solver input files written by Mechanical** (`LC1_Free_Expansion_ds.dat`, `LC2_Axially_Restrained_ds.dat`, NBLOCK/EBLOCK/BFBLOCK in °C) and compares them with the Fluent exports.

- **Coverage.** Mapped nodes: **108,252 / 108,252**. **Unmapped: 0.**
- **Identical in both load cases.** The BF blocks of LC1 and LC2 are identical, and so are Mechanical's two exported text files (same SHA-256).
- **Reference temperature.** `TREF,26.85` °C, i.e. 300 K, in both files.

### Two independent error measures

| Measure | What it tests | Max | Mean |
|---|---|---|---|
| **(A)** mapped vs Fluent node field evaluated with the source hexahedra's own trilinear shape functions at every target node | Mechanical's mapping implementation | **0.081 K** inside the source mesh; **0.092 K** on the chord-gap nodes, against clamped local coordinates (conservative: an unclamped linear projection gives about 0.05 K) | **0.0022 K** |
| **(B)** mapped vs an independent finite-volume reference (tensor grid of cell-centre and boundary-face values, linear in r and z) | total transfer vs Fluent's FV solution, including Fluent's own node reconstruction | **2.57 K** at the inner edge of the inlet end (z = 3.2 mm) | **0.039 K** (RMS 0.14 K, p99 0.74 K) |

### Error (B) by axial band

| Band | Max | Mean |
|---|---|---|
| z < 7 mm | 2.57 K | 0.58 K |
| 7–14 mm | 0.80 K | 0.14 K |
| 14–30 mm | 0.25 K | 0.036 K |
| 30–586 mm | **≤ 0.092 K** | 0.017–0.022 K |
| last 6.6 mm (outlet end) | 0.39 K | 0.049 K |

- Nodes with |B| > 0.5 K: 1,764 (1.6 %), all within 11.1 mm of the inlet end.
- Nodes with |B| > 1 K: 576, all between z = 1.1 and 4.3 mm.
- The reference's own uncertainty there (linear vs cubic interpolation) is up to 0.66 K.

### Engineering quantities (`Validation/MAPPING_ERROR_TABLE.md`)

| Quantity | Fluent Source | Mechanical Mapped | Difference |
|---|---|---|---|
| Solid T minimum | 423.837 K (node); 423.211 K (face) | 423.837 K | +0.00003 K |
| Solid T maximum | 562.544 K (node); 562.127 K (cell); 562.577 K (face) | 562.558 K | +0.014 K (shape-function extrapolation across the ≤ 0.038 mm chord gap) |
| Mid-span inner wall T (z = 300 mm) | 531.672 K | 531.687 K | +0.015 K |
| Mid-span outer wall T (z = 300 mm) | 539.253 K | 539.266 K | +0.014 K |
| Mid-span through-wall ΔT | 7.581 K | 7.580 K | −0.001 K |
| Inlet end, inner edge | 423.838 K (node) | 423.860 K | +0.022 K |
| Outlet end, outer edge | 562.263 K (node) | 562.272 K | +0.009 K |
| Volume-mean solid T | 525.483 K (cell-volume weighted) | 525.520 K (SOLID186 Gauss integration) | +0.037 K |
| Temperature range | 423.21–562.58 K (cells and faces); 423.84–562.54 K (nodes) | 423.84–562.56 K | — |

### Figures (`07_Thermal_Analysis/Figures`, post-processed data)

1. `F7A_01_fluent_solid_T_rz.png`: Fluent solid temperature (cell values, circumferential mean, r–z).
2. `F7A_02_mechanical_imported_T_rz.png`: Mechanical imported field (mapped nodal values from the input file).
3. `F7A_03_side_by_side_and_difference.png`: side by side, plus the difference against the FV reference.
4. `F7A_04_axial_wall_temperature.png`: inner and outer wall T(z) and through-wall ΔT(z).
5. `F7A_05_through_wall_midspan.png`: T(r) at z = 300 mm (cells, faces, Fluent nodes, mapped nodes).

## 6. Assessment

- **The mapping itself is accurate to ≤ 0.09 K** everywhere (mean 0.002 K).
- **The transferred field matches the CFD finite-volume solution** to ≤ 0.25 K (mean 0.02 K) over 14–586 mm, i.e. 95 % of the length. Mid-span wall temperatures and the through-wall ΔT are reproduced to 0.015 K and 0.001 K. The volume mean is within 0.04 K.
- **Inlet-end limitation (flagged, not hidden).**
  - In the first CFD slab (z < 6.7 mm) the axial temperature profile is strongly curved. The inner wall rises 9.5 K between the first two slab centres, and the adiabatic end forces dT/dz = 0 at z = 0.
  - Fluent's node reconstruction (averages of neighbouring cells) differs there from the cell values by up to about 2.4 K. The mapped field inherits this; it is **not a mapping error** (measure A is 0.08 K there).
  - It is a resolution limit of the 6.67 mm CFD axial cells at the inlet.
  - Effect, within about 11 mm of the inlet end:
    - up to 2.6 K local temperature uncertainty at the bore (errors > 2 K only at the bore, z = 3.2 mm);
    - above 1 K out to r ≈ 16 mm;
    - above 0.5 K through the full wall thickness.
  - **Section 7B must treat stresses within about 15 mm of the inlet end with this uncertainty in mind.** They are also dominated by the end boundary condition.
- **Verdict.** The mapping quality is accepted for Section 7B. The poor point-cloud mapping was replaced, not used.

## 7. Files

- **Temperature_Source/**: Fluent exports and journals.
  - `fluent_solid_cells.csv` (43,200 cells), `fluent_solid_face_*.csv`, `fluent_solid_node_*.csv`.
  - `EnSight/solid_domain_T.*` (**the source used for the mapping**).
  - `fluent_solid_zone_nodes.csv`: boundary nodes, double precision, used to cross-check the EnSight float32 values (max difference 3.0×10⁻⁵ K).
  - `fluent_interface_wall_pressure.csv`: for the pressure load.
  - `Journals/`, `Audit/`, `Logs/`.
  - `Probe/`: API probes.
- **Mapping/**
  - `MeshBased/`: CDB master, node temperature CSV, MAPDL build input and output, `mesh_based_source_report.json` (all checks pass).
  - `Scripts/`.
  - `Mechanical_Export/`: Mechanical's own export of the mapped load.
  - `fluent_solid_temperature_pointcloud.csv`: **the rejected point-cloud source, kept as evidence**.
- **Validation/**: `validate_mapping_7A.py`, `rejected_methods_evidence.py`, helpers, `mapping_validation_7A.json`, `MAPPING_ERROR_TABLE.md`, `axial_profiles_mapped_vs_fluent.csv`, `rejected_methods_evidence.json`.
- **Figures/**: F7A_01 … F7A_05.

**Reproducibility.** Python 3 with numpy, scipy, h5py and matplotlib; the Ansys-bundled CPython lacks h5py. The Section 7A post-processing was run on byte-identical copies of the files above (SHA-256 recorded in `08_Structural_Analysis/Workbench/Audit/section7A_key_file_hashes.json`).
