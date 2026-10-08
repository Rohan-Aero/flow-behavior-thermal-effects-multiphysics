# CAD_NOTES.md — Section 3 Geometry

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems
**Original internship:** Eleation, February – May 2025
**Date:** 2026-09-18
**CAD software:** ANSYS SpaceClaim 2026 R1 (v261), driven by IronPython script in batch mode

> ### ⚠ RE-ANALYSIS
> This geometry was **created from scratch in 2026**. It is not a recovered original file.
> Every dimension comes from the frozen Section 2 baseline, which is itself a set of
> re-analysed engineering choices. No original CAD survives.

---

## 1. Modelling procedure

The model was built **entirely by script**, not by interactive clicking, so the whole
geometry is reproducible by re-running one file. Scripts live in `03_CAD_Geometry/Scripts/`.

| Step | Operation | Result |
|------|-----------|--------|
| 1 | `ViewHelper.SetSketchPlane(Plane.PlaneXY)` | sketch plane at z = 0 |
| 2 | `SketchCircle` R = 20 mm, then `SketchCircle` R = 10 mm, concentric | SpaceClaim resolves the two concentric circles into **one annular face** (the inner circle becomes a hole, not a separate region) |
| 3 | `ExtrudeFaces` 600 mm, `ExtrudeType.ForceIndependent` | **SOLID_DOMAIN** — annular solid |
| 4 | Second sketch on the same plane, `SketchCircle` R = 10 mm | a new planar disc surface body |
| 5 | `ExtrudeFaces` 600 mm, `ForceIndependent` | **FLUID_DOMAIN** — solid cylinder occupying the bore |
| 6 | `Body.SetName` on both bodies | named bodies |
| 7 | Faces classified by area + bounding box, `NamedSelection.Create` ×11 | all named selections |
| 8 | `ShareTopology.FindAndFix` | conformal interface (**returned True**) |
| 9 | `DocumentSave.Execute` | native, STEP and STL exports |

### A finding worth recording

Sketching **both** concentric circles in one sketch produces a **single annular face**, not
two regions. The first build attempt therefore extruded only the annulus and produced one
body instead of two. The fluid passage requires its **own second sketch and extrude**. This
is a genuine SpaceClaim behaviour, it was caught by an assertion on body count, and the fix
is step 4 above.

## 2. Final dimensions (frozen Section 2 baseline — unchanged)

| Parameter | Value |
|---|---|
| Inner (bore) diameter Dᵢ | **20 mm** |
| Outer diameter Dₒ | **40 mm** |
| Wall thickness t | **10 mm** |
| Total length L | **600 mm** |
| L/D | 30 |
| Fluid cross-sectional area | 314.159 mm² |
| Hydraulic diameter | 20.000 mm (= Dᵢ exactly, circular duct) |

**No baseline value was changed.** No geometric inconsistency was found that would have
required one.

## 3. Fluid-domain creation

The fluid is a **real solid body occupying the bore**, not a void. This matters: a hole in
the solid would give nothing to mesh and no cell zone for Fluent.

- Body: **FLUID_DOMAIN**, 3 faces — 2 planar end discs + 1 cylindrical wall
- Volume: **1.884956 × 10⁻⁴ m³**
- Faces named: `FLUID_INLET` (z = 0), `FLUID_OUTLET` (z = 600 mm), `FLUID_WALL` (Ø20 cylinder)
- Verified present as a usable body: `total_bodies = 2`, volume > 0, closed

## 4. Solid-domain creation

- Body: **SOLID_DOMAIN**, 4 faces — outer cylinder, inner cylinder, 2 annular ends
- Volume: **5.654867 × 10⁻⁴ m³** (mass 4.631 kg at 8190 kg/m³)
- Faces named: `HEATED_OUTER_WALL` (Ø40), `SOLID_INNER_INTERFACE` (Ø20),
  `SOLID_INLET_END`, `SOLID_OUTLET_END`

## 5. Interface definition

The fluid and solid meet on the Ø20 cylindrical surface. Verification:

| Check | Result |
|---|---|
| Same diameter | both faces at r = 10.000 mm |
| Coincident surfaces | `A_fluid_wall` = 3.7699111843077518 × 10⁻² m², `A_solid_inner` = **identical to all 17 digits** |
| Area difference | **0.000 × 10⁺⁰ m²** |
| No gap, no overlap | fluid + solid volume = 7.539822369 × 10⁻⁴ m³ = **exactly** the full Ø40 × 600 cylinder |
| Duplicate interface | one face per body, paired — not duplicated within a body |
| Shared topology | `ShareTopology.FindAndFix` → **True** |
| Suitable for CHT | yes — conformal, so Fluent creates a coupled wall / wall-shadow pair automatically |

> The volume-sum identity is the strongest single check here. If the bodies overlapped, the
> sum would exceed the full cylinder; if a gap existed, it would fall short. It matches to
> machine precision.

## 6. Named selections (11 created, all verified in the saved file)

| Name | Type | Entity | Used later in |
|---|---|---|---|
| `FLUID_DOMAIN` | body | air passage | Fluent cell zone |
| `SOLID_DOMAIN` | body | Inconel 718 annulus | Fluent solid zone + Mechanical body |
| `FLUID_INLET` | face | Ø20 disc at z = 0 | velocity inlet |
| `FLUID_OUTLET` | face | Ø20 disc at z = 600 | pressure outlet |
| `FLUID_WALL` | face | Ø20 cylinder, fluid side | inflation layers, y⁺ monitoring |
| `FLUID_SOLID_INTERFACE` | 2 faces | both sides of the Ø20 surface | conjugate coupling |
| `SOLID_INNER_INTERFACE` | face | Ø20 cylinder, solid side | conjugate coupling |
| `HEATED_OUTER_WALL` | face | Ø40 cylinder | q″ = 8000 W/m² (Section 5) |
| `SOLID_INLET_END` | face | annulus at z = 0 | adiabatic |
| `SOLID_OUTLET_END` | face | annulus at z = 600 | adiabatic |
| `STRUCTURAL_SUPPORT` | face | annulus at z = 0 | LC1 / LC2 restraint (Section 6) |

`STRUCTURAL_SUPPORT` is deliberately an **end face only**. Restraining the full cylindrical
wall would suppress the free thermal growth that LC1 exists to measure.

## 7. Geometry verification — analytical vs CAD

| Quantity | Unit | Analytical | CAD | Difference | Relative | Status |
|---|---|---|---|---|---|---|
| Outer diameter | mm | 40 | 40 | 0.000e+00 | 0.00e+00 % | **EXACT** |
| Inner (bore) diameter | mm | 20 | 20 | 0.000e+00 | 0.00e+00 % | **EXACT** |
| Wall thickness | mm | 10 | 10 | 0.000e+00 | 0.00e+00 % | **EXACT** |
| Total length | mm | 600 | 600 | 0.000e+00 | 0.00e+00 % | **EXACT** |
| Fluid cross-sectional area | mm^2 | 314.1592654 | 314.1592654 | 5.684e-14 | 1.81e-14 % | **EXACT** |
| Hydraulic diameter | mm | 20 | 20 | 3.553e-15 | 1.78e-14 % | **EXACT** |
| FLUID_DOMAIN volume | m^3 | 0.0001884955592 | 0.0001884955592 | 2.711e-20 | 1.44e-14 % | **EXACT** |
| SOLID_DOMAIN volume | m^3 | 0.0005654866776 | 0.0005654866776 | 0.000e+00 | 0.00e+00 % | **EXACT** |
| FLUID_INLET area | m^2 | 0.0003141592654 | 0.0003141592654 | 5.421e-20 | 1.73e-14 % | **EXACT** |
| FLUID_OUTLET area | m^2 | 0.0003141592654 | 0.0003141592654 | 5.421e-20 | 1.73e-14 % | **EXACT** |
| FLUID_WALL area | m^2 | 0.03769911184 | 0.03769911184 | 0.000e+00 | 0.00e+00 % | **EXACT** |
| SOLID_INNER_INTERFACE area | m^2 | 0.03769911184 | 0.03769911184 | 0.000e+00 | 0.00e+00 % | **EXACT** |
| HEATED_OUTER_WALL area | m^2 | 0.07539822369 | 0.07539822369 | 0.000e+00 | 0.00e+00 % | **EXACT** |
| SOLID_INLET_END area | m^2 | 0.0009424777961 | 0.0009424777961 | 2.168e-19 | 2.30e-14 % | **EXACT** |
| SOLID_OUTLET_END area | m^2 | 0.0009424777961 | 0.0009424777961 | 2.168e-19 | 2.30e-14 % | **EXACT** |

**Every quantity matches to machine precision.** The largest relative deviation is
1.8 × 10⁻¹⁴ %, which is double-precision round-off, not a geometry error.

## 8. Topology and cleanup

| Check | Result |
|---|---|
| Open surfaces | none — both bodies closed, volume computed successfully |
| Gaps / overlaps | none — volume-sum identity exact (§5) |
| Duplicate faces / edges | none — 3 + 4 = 7 faces total, the exact minimum |
| Non-manifold geometry | none |
| Sliver faces | none — smallest face is 9.42478 × 10⁻⁴ m² |
| Tiny edges | none — all edges are full circles or 600 mm generators |
| Fillets, ribs, holes, bosses | none, by design |
| Cleanup required | **none.** `ShareTopology.FindAndFix` was the only repair-class operation run, and it succeeded. |

A 7-face model has essentially no room for topology defects. That is the point of keeping
the benchmark geometry clean.

## 9. Meshability assessment (no mesh generated)

| Question | Assessment |
|---|---|
| Can the fluid domain be meshed? | **Yes — sweepable.** Constant circular cross-section over 600 mm; a hex sweep from `FLUID_INLET` to `FLUID_OUTLET` applies directly. |
| Can the solid domain be meshed? | **Yes — sweepable.** Constant annular cross-section; hex sweep with a mapped face mesh. |
| Can inflation be applied to `FLUID_WALL`? | **Yes.** It is a single clean cylindrical face with no splits, so the prism stack wraps it without a transition. Target first cell **12.2 µm** (y⁺ ≈ 1), 18 layers, growth 1.2 → 1.56 mm stack ≈ 16 % of the bore radius. |
| Can the interface be resolved? | **Yes.** Shared topology makes it conformal, so no non-conformal interface or interpolation error. |
| Unnecessary tiny features? | **None.** |
| Expected mesh size | ≈ **167 760 cells** (fluid ≈ 124 560 + solid ≈ 43 200) at 48 circumferential × 90 axial |
| Memory on 15.7 GB? | **Comfortable.** A 170 k-cell CHT + SST case needs well under 1 GB. |
| Fluent Student 4-core cap | Not limiting at this size. |
| Solid nodes for Mechanical | ≈ 48 000, within the typical 128 k Student node limit |
| Suitable for conjugate heat transfer? | **Yes** — two cell zones, one conformal coupled interface, all boundary faces named. |

**Verdict: the geometry is mesh-ready.** No defeaturing, repair or simplification is needed
before Section 4.

## 10. Files created

| Folder | File | Notes |
|---|---|---|
| `Native_CAD/` | `heated_duct.scdocx` | **primary** — native SpaceClaim, carries bodies + named selections + share topology |
| `STEP/` | `heated_duct.step`, `heated_duct.stp` | neutral interchange (AP214) |
| `Reference_STL/` | `heated_duct_reference.stl` | **reference only** — see limitation below |
| `Drawings/` | `ENGINEERING_DRAWING.png`, `PHYSICS_SCHEMATIC.png` | |
| `Screenshots/` | 9 rendered views | |
| `Geometry_Check/` | `cad_measurements.json`, `geometry_verification.csv`, `build_log.txt`, `v4_log.txt` | raw SpaceClaim output |
| `Scripts/` | `build_geometry_v3.py`, `finalize_v4.py`, `probe.py` | reproducible build |

## 11. Honest limitations

**Parasolid export is not available in this installation.** `DocumentSave.Execute` was
called for `.x_t`, `.x_b` and `.xmt_txt`; all three returned without error but **wrote no
file**, while `.step` and `.stl` from the same loop wrote correctly. Parasolid export
appears not to be licensed in ANSYS Student. This costs nothing here: the native
`.scdocx` transfers losslessly into Workbench (including named selections), and STEP covers
neutral interchange.

**The STL is a coarse tessellation and must not be used for meshing.** It approximates each
circle with **18 facets**, which under-states both volumes by **2.02 %** — visible in the
parse check (554 073 mm³ vs 565 487 mm³ exact). It is retained only for visualisation.
The meshing source is the native file or the STEP.

**The screenshots are renders of the exported geometry, not SpaceClaim UI captures.** A
SpaceClaim **GUI** session was launched to export viewport images; it hung for over 400
seconds without executing the script and was terminated. Rather than fake a UI screenshot,
the views were rendered directly from `heated_duct_reference.stl` — the actual tessellated
CAD output — and each image is captioned with its provenance. The cross-section view is
drawn from the real end-face triangles, which is why the 18-facet polygonal approximation is
visible in it. If a genuine SpaceClaim UI screenshot is wanted, opening
`Native_CAD/heated_duct.scdocx` by hand and capturing the window takes about a minute.

**Share topology was applied via `ShareTopology.FindAndFix`**, which returned True.
`ShareTopologyOptions` in this API version is an options object, not an enum — the
documented `ShareTopologyOptions.Share` member does not exist here. Worth re-confirming in
Workbench that the mesh is conformal across the interface when Section 4 runs.
