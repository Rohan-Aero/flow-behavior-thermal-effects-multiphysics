# Section 9B-1: thickness-case geometry (T01_THIN, T03_THICK) and derived heat flux

> **RE-ANALYSIS 2026.** Both geometries are new CAD models made in 2026 for the parametric study. They are not recovered files. The P00 CAD in `03_CAD_Geometry/` was **not opened, modified or re-exported**.

## 1. What was built

| Item | T01_THIN | P00 (reference, unchanged) | T03_THICK |
|---|---|---|---|
| Wall thickness t | **8 mm** | 10 mm | **12 mm** |
| Outer diameter Do | 36 mm | 40 mm | 44 mm |
| Bore Di, length L | 20 mm, 600 mm | 20 mm, 600 mm | 20 mm, 600 mm |
| Script | `build_geometry_T01_THIN.py` | `03_CAD_Geometry/Scripts/build_geometry_v3.py` + `finalize_v4.py` | `build_geometry_T03_THICK.py` |
| Output folder | `T01_THIN/` | `03_CAD_Geometry/` | `T03_THICK/` |

**How the scripts were made.**

- Both case scripts are generated from one template, `build_geometry_param_TEMPLATE.py`. Only two placeholders change: the case name and Do.
- The modelling procedure is the P00 procedure, step for step:
  1. Sketch the annulus (two concentric circles, which SpaceClaim resolves to one annular face) and extrude it 600 mm to make SOLID_DOMAIN.
  2. Make a separate sketch and extrude for the bore disc, giving FLUID_DOMAIN.
  3. Run `ShareTopology.FindAndFix`.
  4. Create the same 11 named selections.
  5. Save as native `.scdocx` and as STEP.
- SpaceClaim 2026 R1 was run headless in batch (`run_cad.ps1`), one process per case. The driver log is in `run_cad_driver.txt`: exit code 0, 194 s for T01 and 99 s for T03.

## 2. Analytical check (built before any T-case solve)

The checker is `geometry_check_9B1.py`. For each case it writes `<CASE>/geometry_verification.csv`, in the same layout as the P00 file `03_CAD_Geometry/Geometry_Check/geometry_verification.csv`.

| Quantity | Analytical (T01 / T03) | SpaceClaim (T01 / T03) | Status |
|---|---|---|---|
| Do [mm] | 36 / 44 | 36 / 44 | EXACT / EXACT |
| Di [mm] | 20 / 20 | 20 / 20 | EXACT |
| t [mm] | 8 / 12 | 8 / 12 | EXACT |
| L [mm] | 600 / 600 | 600 / 600 | EXACT |
| Fluid cross-section [mm²] | 314.159265 | 314.159265 | EXACT |
| Hydraulic diameter [mm] | 20 | 20 | EXACT |
| Fluid volume [m³] | 1.884956 × 10⁻⁴ | 1.884956 × 10⁻⁴ | EXACT |
| **Solid volume [m³]** | **4.222301 × 10⁻⁴ / 7.238229 × 10⁻⁴** | **4.222301 × 10⁻⁴ / 7.238229 × 10⁻⁴** | EXACT |
| Fluid wall = solid inner area [m²] | 0.0376991 | 0.0376991 | EXACT |
| **Heated outer-wall area [m²]** | **0.0678584 / 0.0829380** | **0.0678584 / 0.0829380** | EXACT |
| Solid end-face area [m²] | 7.037168 × 10⁻⁴ / 1.206372 × 10⁻³ | same | EXACT |

- **Rows.** 15 of 15 rows per case are EXACT, with relative differences ≤ 5 × 10⁻¹⁴ %.
- **Structure.** Each model has 2 bodies (fluid with 3 faces, solid with 4), 11 named selections, share topology `FindAndFix OK: True`, and both exports written.

## 3. Derived heat flux (D-060: total heat input held at P00)

**The flux is a derived parameter.** The design variable is the wall thickness. Keeping q″ = 8000 W/m² on every thickness would change the heat input in proportion to Do. The thickness effect would then be confounded with a ±10 % change in heat load.

The rule is q″_case = Q_P00 / A_heated,case, using the actual heated-wall area of each geometry:

| | P00 | T01_THIN | T03_THICK |
|---|---|---|---|
| Heated area, CAD = π·Do·L [m²] | 0.0753982 | **0.0678584** | **0.0829380** |
| Heated area, CFD mesh (48 facets) [m²] | 0.0753444 (Fluent) | 0.0678100 | 0.0828788 |
| Heat input Q, analytical / CAD [W] | **603.186** | 603.186 | 603.186 |
| Heat input Q, CFD mesh [W] | **602.755** (Fluent, P00) | 602.755 | 602.755 |
| **Required q″ [W/m²]** | 8000 | **8888.889** (+11.11 %) | **7272.727** (−9.09 %) |

Equivalent closed form: q″_case = q″_P00 · Do_P00 / Do_case.

**Why the CAD and CFD values agree.**

- The CAD area (true circle) and the CFD area (inscribed 48-gon) differ by the same factor for every Do: the perimeter ratio sin(π/48)/(π/48) = 0.999286.
- So one q″ holds Q at the P00 value on both.
- Numerically, q″ × A_mesh = 602.755239 W for both cases, against 602.755239 W for the P00 Fluent heat rate. The relative difference is 1.7 × 10⁻⁹, which is the rounding of Fluent's printed report.
- The solved T cases re-check this with Fluent's own heated-area and heat-rate reports (`CFD_Results/`).

Machine-readable records: `geometry_checks_9B1.json` and `derived_heat_flux_9B1.json`.
