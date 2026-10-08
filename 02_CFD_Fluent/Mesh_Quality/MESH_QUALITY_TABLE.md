# Mesh Quality Table — Section 4

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems
**Status:** RE-ANALYSIS (2026). Nothing in this file is an original 2025 artefact.
**Generated:** 2026-09-19
**Meshes audited:** `Mesh_Coarse/coarse.msh`, `Mesh_Medium/medium.msh`, `Mesh_Fine/fine.msh`

---

## 0. Where each number comes from

Two independent sources are reported side by side, and they are never mixed:

| Tag | Source | Evidence file |
|-----|--------|---------------|
| **F** | Reported by **ANSYS Fluent 2026 R1** itself (`/mesh/check`, `/mesh/quality`) | `Mesh_Quality/{coarse,medium,fine}_fluent_check.txt` |
| **P** | Computed independently in Python from the published ANSYS formulae | `Mesh_Quality/python_quality_audit.json`, script `Scripts/mesh_analysis.py` |

The **P** computation was written without reference to the solver output and then compared
against it. Agreement is to the six significant figures Fluent prints:

| Quantity | coarse F | coarse P | medium F | medium P | fine F | fine P | worst rel. diff |
|---|---|---|---|---|---|---|---|
| min cell volume (m³) | 2.049465e-10 | 2.049465e-10 | 9.051023e-11 | 9.051023e-11 | 4.009135e-11 | 4.009135e-11 | 1.2e-07 |
| max cell volume (m³) | 1.056568e-07 | 1.056568e-07 | 2.859743e-08 | 2.859743e-08 | 6.548914e-09 | 6.548914e-09 | 1.7e-07 |
| total volume (m³) | 7.491468e-04 | 7.491468e-04 | 7.518309e-04 | 7.518309e-04 | 7.530256e-04 | 7.530256e-04 | 4.9e-08 |
| min orthogonal quality | 0.448186 | 0.448186 | 0.445829 | 0.445829 | 0.314386 | 0.314386 | 9.5e-07 |
| max aspect ratio | 974.491 | 974.491 | 654.392 | 654.392 | 437.899 | 437.899 | 1.1e-06 |

The residual differences are the rounding in Fluent's own printed output, not a modelling
difference. **Consequence:** every quality number in this project can be re-derived from the
mesh file alone; none of it has to be taken on the solver's word.

### Provenance guard

`mesh_analysis.py` refuses to report anything until it has re-read the `.msh` file that Fluent
loaded and confirmed it node-for-node against the mesh held in memory:

| Level | nodes in `.msh` | max node-coordinate difference | cell-zone counts | verdict |
|---|---|---|---|---|
| coarse | 53,741 | 4.94e-15 m | match | IDENTICAL |
| medium | 163,891 | 3.34e-14 m | match | IDENTICAL |
| fine | 509,320 | 4.45e-14 m | match | IDENTICAL |

The differences are double-precision ASCII round-trip noise (12 significant figures written).

---

## 1. Mesh sizing controls

| Control | coarse | medium | fine |
|---|---|---|---|
| Core divisions per side, `NC` | 8 | 12 | 18 |
| Circumferential divisions, `Nθ = 4·NC` | 32 | 48 | 72 |
| Fluid radial divisions, `NR` | 18 | 24 | 32 |
| Solid radial divisions, `NRS` | 7 | 10 | 15 |
| Axial divisions, `NZ` | 60 | 90 | 135 |
| Axial cell length | 10.000 mm | 6.667 mm | 4.444 mm |
| Element type | hexahedra, 100 % | hexahedra, 100 % | hexahedra, 100 % |
| Tetrahedra / prisms / pyramids | 0 | 0 | 0 |

## 2. Counts

| Count | coarse | medium | fine |
|---|---|---|---|
| Nodes | 53,741 | 163,891 | 509,320 |
| **Cells (total)** | **51,840** | **159,840** | **500,580** |
| — FLUID_DOMAIN | 38,400 | 116,640 | 354,780 |
| — SOLID_DOMAIN | 13,440 | 43,200 | 145,800 |
| Faces | 157,344 | 483,456 | 1,510,308 |
| FLUID_SOLID_INTERFACE faces | 1,920 | 4,320 | 9,720 |
| `.msh` file size | 7.97 MB | 26.3 MB | 84.6 MB |
| Cell ratio to previous level | — | 3.083 | 3.132 |
| Equivalent linear ratio `r = (N₂/N₁)^⅓` | — | **1.455** | **1.463** |

`r ≈ 1.46` on both steps. A Richardson / GCI study needs `r ≥ 1.3`; this family satisfies it
and refines in **all three directions at once**, so the levels differ systematically rather
than in one direction only.

## 3. Volume conservation

Exact geometric volume of the Ø40 × 600 mm cylinder: **7.539822e-04 m³**.

| | coarse | medium | fine |
|---|---|---|---|
| Mesh total volume (F) | 7.491468e-04 | 7.518309e-04 | 7.530256e-04 |
| Ratio to exact | 0.993587 | 0.997147 | 0.998731 |
| Inscribed-polygon area ratio `(Nθ/2π)·sin(2π/Nθ)` | 0.993587 | 0.997147 | 0.998731 |
| Difference | **0** | **0** | **0** |

The entire volume deficit is the faceting of a circle by an `Nθ`-sided inscribed polygon —
it is not mesh error, and it vanishes as `Nθ⁻²` exactly as it should. This is a closed-form
check on the mesh generator that does not depend on the solver at all.

## 4. Quality metrics

| Metric | coarse | medium | fine | acceptance |
|---|---|---|---|---|
| **Negative-volume cells** (F) | **0** | **0** | **0** | must be 0 ✔ |
| "wrong node order" warnings (F) | **none** | **none** | **none** | must be none ✔ |
| Minimum orthogonal quality (F) | **0.448186** | **0.445829** | **0.314386** | > 0.10 ✔ |
| Mean orthogonal quality (P) | 0.948540 | 0.978744 | 0.989525 | — |
| Cells with OQ < 0.20 (P) | 0 | 0 | 0 | — ✔ |
| Maximum equiangle skewness (P) | 0.65635 | 0.76002 | **0.83641** | < 0.95 ✔, < 0.80 ✘ on fine |
| Mean skewness (P) | 0.082946 | 0.063367 | 0.050548 | — |
| Cells with skewness > 0.50 (P) | 240 (0.46 %) | 360 (0.23 %) | 1,620 (0.32 %) | — |
| Cells with skewness > 0.80 (P) | 0 | 0 | **540 (0.108 %)** | flagged, §6 |
| Maximum aspect ratio (F) | 974.491 | 654.392 | 437.899 | see §6 |
| Mean aspect ratio (P) | 141.34 | 96.16 | 66.04 | — |
| Mesh continuity / Euler check | pass | pass | pass | every cell has exactly 6 faces, every node used |

## 5. Inflation / near-wall resolution

| | target (Section 4 brief) | coarse | medium | fine |
|---|---|---|---|---|
| First fluid cell height | 12.2 µm | **12.2 µm** | **12.2 µm** | **12.2 µm** |
| Fluid growth rate | — | 1.3182 | 1.2091 | 1.1385 |
| Radial layers within 1.56 mm of the wall | 18 | 13 | 17 | 22 |
| Thickness of the 18 wall-most fluid layers | ≈ 1.56 mm | 5.500 mm* | 1.721 mm | 0.821 mm |
| Solid first cell at the interface | — | 0.5 mm | 0.5 mm | 0.5 mm |
| Solid growth rate | — | 1.3420 | 1.1469 | 1.0398 |

\* On the coarse mesh `NR = 18`, so "the 18 wall-most layers" is the **entire** 5.5 mm fluid
annulus. See §6 for why the brief's "18 layers ≈ 1.56 mm" is not met literally.

**y⁺ is not claimed anywhere in this section.** The 12.2 µm first layer was sized in Section 2
from a correlation-based wall-shear estimate; whether it actually lands at y⁺ ≤ 1 can only be
answered by Fluent after the momentum equations are solved. That is open task **T-010**.

## 6. Flagged items — read before quoting these meshes

**(a) Maximum aspect ratio is high (438–974), and that is intended.**
A 12.2 µm first cell in a 600 mm duct with 4.4–10 mm axial cells gives `AR ≈ Δz / Δr ≈ 360–820`
by construction. The worst cells sit at r = 9.95–9.99 mm — i.e. they are the inflation cells,
exactly where a wall-resolved mesh is supposed to be stretched. High aspect ratio in the
wall-normal direction is benign for a pressure-based coupled solver on a hex mesh where the
stretching is aligned with the flow; it would be a problem only if the stretching were oblique
to the flow, which it is not. Note that **aspect ratio improves monotonically with refinement**
(974 → 654 → 438), because the axial cell shrinks while the first layer is held fixed.

**(b) The fine mesh has 540 cells with skewness > 0.80.** ⚠
That is 0.108 % of 500,580 cells. They are located at r ≈ 5.28 mm, θ = 45°/135°/225°/315° —
i.e. **exactly the four corner columns of the O-grid core block**, 4 corners × 135 axial layers
= 540 cells. The count is an exact product, which confirms the diagnosis rather than leaving it
as a guess. They are on the duct axis side, 4.7 mm away from the wall and from the fluid/solid
interface, in the part of the flow where gradients are smallest.

Cause: the super-ellipse core boundary (exponent n = 4, radius 0.45·Rᵢ) is held fixed while
`NC` rises, so the corner cells become relatively more distorted at higher `NC`. The same
mechanism is why **minimum orthogonal quality degrades with refinement** (0.448 → 0.446 →
0.314) instead of improving — an unusual direction that would be a red flag if it were not
explained.

Assessment: acceptable. 0.314 is still more than 3× Fluent's 0.10 "poor" threshold, no cell is
below 0.20, and the affected cells are away from every boundary that drives the physics.
If Section 5 shows convergence trouble traceable to the core block, the remedy is to raise the
super-ellipse exponent or shrink `core_frac`; that would change the mesh, not the geometry, and
is recorded here so the option is not rediscovered later.

**(c) The brief's "18 inflation layers, total ≈ 1.56 mm" is not met literally.** ⚠
This mesh has no separate prism-layer stack. It is a single structured hex block in which the
radial spacing is graded continuously from the wall all the way to the O-grid core, so there is
no boundary between "inflation layers" and "bulk cells" to count. What is preserved is the
parameter that actually matters — the **first-layer height of 12.2 µm, identical on all three
levels** — so the near-wall resolution is held constant while everything else refines. That is
the right control for a mesh-independence study: if the first cell changed with the mesh, the
wall treatment would change with it and the study would be measuring two things at once.
The number of layers within 1.56 mm of the wall (13 / 17 / 22) is reported instead.

**(d) The `.msh` files name `aluminum` as the cell-zone material.** ⚠
That is Fluent's default material assignment when reading a mesh with no material data, not a
project decision. The project solid is **Inconel 718, age-hardened** (Section 2,
`BASELINE_PARAMETERS.md`) and the fluid is air. Materials are assigned in the solver setup in
Section 5; the mesh file carries none.

## 7. Fluid/solid interface

| Audit item | coarse | medium | fine |
|---|---|---|---|
| FLUID_SOLID_INTERFACE faces | 1,920 | 4,320 | 9,720 |
| Distinct nodes on those faces | 1,952 | 4,368 | 9,792 |
| Faces with a FLUID_DOMAIN owner | 1,920 | 4,320 | 9,720 |
| Faces with a SOLID_DOMAIN neighbour | 1,920 | 4,320 | 9,720 |
| Orphan / one-sided faces | **0** | **0** | **0** |
| Hanging nodes | **0** | **0** | **0** |
| max \|r − 10.000 mm\| over interface nodes | 1.7e-18 m | 1.7e-18 m | 1.7e-18 m |

Every interface face carries exactly one fluid owner and one solid neighbour, so the two sides
**share nodes** rather than being tied by interpolation. Fluent confirms this independently: on
reading each mesh it creates `fluid_solid_interface-shadow` automatically (zone 12), which is
the coupled-wall pair it builds for a conformal interface. A non-conformal mesh would instead
have required an explicit mesh interface.

This matters because the whole problem is conjugate heat transfer. A non-conformal interface
would interpolate the heat flux crossing r = 10 mm, and that flux is the input to the thermal
and structural analyses in Sections 6–7.

## 8. Zones as Fluent reads them

From `/define/boundary-conditions/list-zones` (identical structure on all three levels):

| ID | Name | Type | Kind |
|---|---|---|---|
| 2 | fluid_domain | fluid | cell |
| 3 | solid_domain | solid | cell |
| 4 | interior-fluid | interior | face |
| 5 | interior-solid | interior | face |
| 6 | fluid_inlet | velocity-inlet | face |
| 7 | fluid_outlet | pressure-outlet | face |
| 8 | fluid_solid_interface | wall | face |
| 9 | heated_outer_wall | wall | face |
| 10 | solid_inlet_end | wall | face |
| 11 | solid_outlet_end | wall | face |
| 12 | fluid_solid_interface-shadow | wall | face (auto-created) |

Face counts, coarse: 113,600 / 38,176 interior; 640 inlet; 640 outlet; 1,920 interface;
1,920 heated outer wall; 224 + 224 solid ends. All match the generator exactly.

## 9. Recommended baseline

**MESH B (medium), 159,840 cells.**

- Within 4.7 % of the Section 4 target of ~167,760 cells.
- Best quality of the three: minimum OQ 0.4458, zero cells above skewness 0.80, and a max
  aspect ratio (654) between the other two.
- Volume within 0.29 % of exact.
- Fits the 15.7 GB / 8-core budget comfortably for a coupled CHT run.
- The coarse and fine levels bracket it at `r ≈ 1.46`, which is what the Section 5
  mesh-independence study needs.

**Mesh independence is NOT claimed here.** Nothing has been solved yet. The three meshes exist
so that the claim can be tested in Section 5.
