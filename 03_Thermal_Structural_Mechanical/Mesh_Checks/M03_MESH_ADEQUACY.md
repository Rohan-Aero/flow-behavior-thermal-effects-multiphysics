# M03 — thick-wall CFD mesh adequacy check of T03 (Section 9B-2, Part A)

**RE-ANALYSIS 2026.** Both Fluent solutions compared here were newly generated in Sections 9B-1 and 9B-2. Nothing is
recovered from the lost internship and no measurement is involved.

## Why the check was needed

T03_THICK (Do 44 mm, wall 12 mm) is the only design case where the solid mesh had to be stretched furthest from the P00
mesh (P00: 10 layers over 10 mm). The 9B-1 mesh check only proved that the T03 mesh is valid (counts, volumes,
conformity, no negative cells). It did not prove that 12 radial layers resolve the through-wall temperature field well
enough to be used as the thermal load of a structural model. The brief therefore required a refined comparison before
the T03 field is used structurally.

## What was compared

| Item | T03_THICK (used structurally) | M03_T03_CFD_SOLID18 (refined check) |
|---|---|---|
| Geometry, physics, BCs | T03 (q″ 7272.73 W/m², V 23.5 m/s, 300 K) | identical (same journal `solve_param.py`, same `param_cases.py` entry except mesh) |
| Solid radial layers | 12, first 0.500 mm, growth 1.119, last 1.724 mm | 18, first 0.333 mm, growth 1.076, last 1.157 mm (every layer ≈ ×1.5 finer) |
| Solid cells | 51,840 | 77,760 |
| Fluid mesh | 116,640 cells | bit-identical (same generator settings; fluid node coordinates and connectivity equal) |
| Angular × axial | 48 × 90 | 48 × 90 (unchanged) |
| Fluid–solid interface | 4,320 conformal face pairs | 4,320 conformal face pairs |
| Min orthogonal quality (Fluent) | 0.445829 | 0.445829 (set by the unchanged fluid inflation layer) |
| Convergence | converged 600, confirmed 700 | converged 600, confirmed 700; 133-row audits 0 failed; frozen-physics gate PASS |
| y+ (min / mean / max) | 0.2083 / 0.2408 / 0.5777 | 0.2083 / 0.2408 / 0.5777 |

Script: `Mesh_Checks/m03_compare.py` → `m03_comparison.json`, `m03_compare_stdout.txt`.
Mesh generator: `Mesh_Checks/m03_mesh.py` (mesh SHA-256 C8182CF6525101E8…); `mesh_checks_M03.json`.

## Results (M03 minus T03)

| Quantity | T03 (12 layers) | M03 (18 layers) | Difference |
|---|---|---|---|
| Heat input Q (heated wall = interface) | 602.755 W | 602.755 W | 0 |
| Pressure drop | 438.1428 Pa | 438.1428 Pa | +4e-5 Pa |
| Outlet bulk T | 368.932 K | 368.932 K | 0 |
| Solid T max (facet) | 563.072 K | 563.067 K | −0.005 K |
| Solid T max (cell centre) | 562.662 K | 562.790 K | +0.128 K (cell-centre sampling moves with the finer layers) |
| Solid volume-mean T | 526.384 K | 526.375 K | −0.009 K |
| Solid T min (cell centre) | 428.917 K | 428.672 K | −0.245 K (sampling effect at the inlet bore, see below) |
| Interface T min / max (facet) | 428.134 / 554.775 K | 428.151 / 554.775 K | +0.017 / −0.0001 K |
| y+ max | 0.57774 | 0.57772 | −4.3e-5 (relative) |

Solid **node** field (what Mechanical maps). Both meshes share the same 48 angular lines and 91 axial planes, so the T03
node temperatures were interpolated radially onto all 82,992 M03 solid nodes:

| Node-field measure | Value |
|---|---|
| Max \|ΔT\| | 0.197 K (bore, inlet face z = 0, θ = 22.5°) |
| Mean / RMS | +0.003 K / 0.011 K |
| Mid-span through-wall ΔT | 8.608 → 8.602 K (−0.0055 K, −0.06 %) |
| Mid-span section mean | 536.830 → 536.826 K (−0.004 K) |
| Inlet-face through-wall ΔT | 16.558 → 16.855 K (+0.30 K, +1.8 %) |
| Outlet-face through-wall ΔT | 7.798 → 7.952 K (+0.15 K, +2.0 %) |

## Acceptance (9A case matrix row M03) and decision

| Criterion | Result |
|---|---|
| Solid T max (facet and cell) change ≤ 0.5 K | PASS (−0.005 K, +0.128 K) |
| Mid-span through-wall ΔT change ≤ 0.5 K and ≤ 1 % | PASS (−0.0055 K, 0.06 %) |
| Q change ≤ 1 % | PASS (0) |
| Solid volume-mean T change ≤ 0.5 K | PASS (−0.009 K) |
| Node field: max \|ΔT\| ≤ 0.5 K anywhere | PASS (0.197 K) |
| y+ max change ≤ 1 % | PASS |
| Re-map T03 only if T max changes by more than 0.5 K | not required |

**Decision: the T03 CFD mesh (12 solid layers) is adequate for the structural analysis. No remap and no mesh repair
were needed, and no boundary condition was altered.** The structural T03 case uses the 12-layer T03_THICK field.

## What the check does and does not cover

- It varies only the radial solid resolution, which is the dimension stretched for T03. The axial (90 cells) and
  angular (48) resolution and the fluid mesh are the P00 values; their adequacy rests on the Section 6B three-mesh
  study (GCI) and is inherited, not re-tested here.
- The largest local differences are at the two end faces (through-wall ΔT +0.30 K at the inlet face, +0.15 K at the
  outlet). They are below 0.5 K in absolute terms but 1.8–2.0 % in relative terms, because the end faces are adiabatic
  planes where the radial gradient changes quickly. An order-of-magnitude estimate of their structural effect is
  E·α·ΔT/(2(1−ν)) ≈ 190 GPa × 14e-6 × 0.30 K / 1.41 ≈ 0.6 MPa, about 0.1 % of the LC2 stress level (≈ 600 MPa). This is
  recorded as a local uncertainty of the T03 end-face stress, not as a failed criterion.
- The −0.245 K change of the cell-centre minimum is a sampling effect: the first cell centre sits 0.167 mm from the bore
  in M03 instead of 0.25 mm in T03, so it reads a value closer to the wall minimum. The facet minimum on the interface
  changes by only +0.017 K.
