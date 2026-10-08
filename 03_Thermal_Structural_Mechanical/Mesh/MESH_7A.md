# Section 7A: structural mesh M36 (production)

> RE-ANALYSIS 2026. Newly generated mesh. The statistics come from Mechanical (`Mechanical_Setup/Logs/mech_build_7A_summary.json`) and from the written solver input file (`LC1_Free_Expansion_ds.dat`).

## Definition (script `Workbench/Scripts/mech_build_7A.py`)

| Item | Setting |
|---|---|
| Body | SOLID_DOMAIN only; FLUID_DOMAIN suppressed |
| Element | **SOLID186**: 20-node quadratic hexahedron (`et,1,186`), element order Quadratic |
| Method | Sweep along the axis, **130 divisions**, bias type "fine at both ends", **bias factor 4** |
| End face | Face meshing, mapped, **5 internal (radial) divisions** |
| Edges | the four circular edges: **36 divisions**, hard |

## Resulting mesh

| Quantity | Value |
|---|---|
| Nodes | **108,252** (28,296 corner + 79,956 mid-side) = **84.6 % of the measured 128,000-node limit** |
| Elements | **23,400** SOLID186 |
| Through-wall (radial) | 5 elements × 2.000 mm. Quadratic, so 11 nodes through the 10 mm wall |
| Circumferential | 36 elements × 10°. Mid-side nodes every 5°; arc 1.745 mm (bore) to 3.491 mm (outer) |
| Axial | 130 elements, 2.128 mm at each end growing to 8.510 mm at mid-length (ratio 4.00). 4 / 8 / 12 elements within 10 / 20 / 30 mm of each end |
| Node plane at mid-span | yes (z = 300 mm), used for the checks |
| Surfaces | true circles r = 10 and 20 mm (quadratic edges). Volume 5.65486×10⁻⁴ m³ (π(r_o² − r_i²)L = 5.65487×10⁻⁴) |

## Quality (Mechanical mesh metrics, whole mesh)

| Metric | Min | Max | Average |
|---|---|---|---|
| Element quality | 0.237 | 0.991 | 0.688 |
| Aspect ratio | 1.137 | **4.882** | 2.413 |
| Jacobian ratio | 1.115 | 1.205 | 1.153 |
| Warping factor | 0 | 1.4×10⁻¹³ | — |
| Parallel deviation | 10° | 10° | 10° (the 10° sector) |
| Maximum corner angle | 95° | 95° | 95° |
| Skewness | 0.056 | 0.056 | 0.056 |

**Minimum element quality 0.237.** This occurs in the longest mid-length elements (8.5 mm axial × 1.75 mm bore arc). It is an aspect-ratio effect in a region of mild axial gradient. The hexahedra have no distortion: Jacobian ratio ≤ 1.21, warping 0. A maximum aspect ratio below 5 is well inside normal practice for quadratic solids.

## Why this mesh

- **Through-wall resolution.** The LC1 (free-expansion) stress comes from the radial temperature gradient; the through-wall ΔT at mid-span is 7.6 K. Five quadratic elements give a quadratic displacement and linear strain variation per element, so 10 linear stress segments across the wall.
- **Axial refinement at the ends.** The end-effect decay length of the shell, √(R·t)/[3(1−ν²)]^¼ ≈ 9.5 mm for R = 15 mm and t = 10 mm, is resolved by 4 elements per 10 mm. This matters for LC2, whose free and restrained edges carry the steepest gradients.
- **Circumferential.** The load is axisymmetric: the CFD circumferential temperature spread is ≤ 0.0053 K. Quadratic 10° elements represent the circle exactly enough, and the rigid-body supports need nodes at 0°, 120° and 240°, which exist.
- **Licence.** 108,252 nodes leave 15 % margin below the 128,000-node limit (see `Licence_Check/LICENCE_CHECK_7A.md`).

## Candidates considered (probe projects, not used)

| Candidate | Nodes | Max aspect ratio | Min element quality | Reason not chosen |
|---|---|---|---|---|
| 48 × 5 × 100, bias 5 | 111,216 | 9.19 | 0.097 | worse aspect ratio and quality for more nodes |
| CFD solid mesh 1:1 (48 × 10 graded × 90, linear hex) | 48,048 | about 13 at the bore | — | linear elements; uniform 6.67 mm axial cells cannot be refined at the ends. As quadratic it would have 187,296 nodes, over the limit |

## Mesh sensitivity

No structural mesh-sensitivity study has been run yet (nothing is solved in 7A).

- A coarser level (for example 24 × 4 × 100, 45,936 nodes) fits easily.
- A finer level must stay below 128,000 nodes. For example, 36 × 6 × 120 has 117,360 nodes; the refinement would go into the wall, not into more axial elements.
- This is an item for Section 7B if convergence evidence is wanted.
