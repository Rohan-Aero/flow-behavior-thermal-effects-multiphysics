# Section 7A: LC1 and LC2 boundary conditions (prepared, NOT solved)

> RE-ANALYSIS 2026. All BC and load objects of both load cases are defined ("Fully Defined") in the Workbench project
> `08_Structural_Analysis/Workbench/Flow_Behavior_Thermal_Effects_Structural.wbpj`. Their solver input files were written with
> *Write Input File* (`Mechanical_Setup/Input_Files/`). **Neither load case has been solved**: the Solution cells are not up to date.
> The constrained DOFs below are read from the written input files, not only from the script.
> Named-selection names are truncated to 32 characters inside the decks (`NS_LC1_SUPPORT_3NODES_INLET_OUTE`).
> Build run 3 left `CS_DUCT_CYL` under-defined, so both Solution objects were "Underdefined". Run 5 defines its origin by global coordinates (see `STRUCTURAL_SETUP_NOTES.md` §7 and §9).

## Common to both load cases

- **Body.** SOLID_DOMAIN (Inconel_718_Re_analysis), mesh M36. FLUID_DOMAIN suppressed.
- **Stress-free reference temperature.** **T_ref = 300 K**: Environment Temperature 26.85 °C → `TREF,26.85`. The body reference temperature is taken from the environment.
- **Thermal load.** Imported Body Temperature `Imported_Body_Temperature_CFD`: the full 3-D CFD field on all 108,252 nodes (`BFBLOCK,2,TEMP,108252`), identical in LC1 and LC2. Thermal strain = α(T)·(T − 300 K). There is no uniform ΔT and no Section 2 mean value.
- **Analysis settings.** Static structural, 1 step. Large deflection OFF: small strain is appropriate for a thermal strain of at most about 0.36 %. Weak springs OFF. Inertia relief OFF.
- **Cylindrical coordinate system `CS_DUCT_CYL`.** Origin defined by global coordinates (0,0,0) on the duct axis, Z along the axis: x = r, y = θ, z = axial (`local,12,1` in the input file).
- **Rigid-body modes to remove.** 3 translations + 3 rotations. Pure thermal loading has no net external force, so the supports should carry (numerically) zero reaction.

## LC1: free thermal expansion (statically determinate, 6 DOFs)

| Object (Mechanical) | Scope | Constrained DOFs | Free |
|---|---|---|---|
| Nodal Orientation `LC1_SUPPORT_3NODES_Utheta0_Uz0_orientation_CS_DUCT_CYL` | 3 nodes: `NS_LC1_SUPPORT_3NODES_INLET_OUTER` | rotates the 3 nodal coordinate systems to CS_DUCT_CYL (`nrot`) | — |
| Nodal Displacement `LC1_SUPPORT_3NODES_Utheta0_Uz0` | same 3 nodes | **U_θ = 0 (`d,…,uy,0`) and U_z = 0 (`d,…,uz,0`)** | U_r at all 3 nodes; every other node completely free |

**The three support nodes** lie on the inlet end face (= `STRUCTURAL_SUPPORT`, D-025) at the outer radius r = 20 mm, z = 0. They are nodes 18882 (θ = 0°), 18894 (θ = 120°) and 18870 (θ = −120° = 240°).

**Why this is the right LC1 support.**

- **What the six constraints remove.** Three U_z constraints on non-collinear points remove axial translation and the two rotations about the x and y axes. Three U_θ constraints at 120° spacing remove x/y translation and rotation about z.
  - That is exactly 6 independent constraints, so the support is statically determinate.
  - Radial motion is free, so the free radial expansion of the ring is not restrained.
- **Consistency with free expansion.** Pure axisymmetric thermal expansion has U_θ = 0 everywhere and U_z = constant on the z = 0 plane only if that plane stays plane.
  - Only three points of the end face are held in z. Any warping of the end face is not prevented beyond those three points.
  - The axial growth of the tube is not blocked at all: the outlet end is free.
- **What is not done.** No face or barrel is fixed. There is no "Fixed Support", which would destroy the free-expansion case.
- **Mechanical's rigid-body warning.** "Not enough constraints appear to be applied to prevent rigid body motion". This is Mechanical's generic check, which does not recognise Direct FE constraints. The count above shows the model is not under-constrained; 7B should confirm near-zero reactions.

## LC2: axial expansion prevented, radial growth permitted

| Object (Mechanical) | Scope | Constrained DOFs | Free |
|---|---|---|---|
| Displacement `LC2_INLET_END_Uz0` (global CS) | face SOLID_INLET_END (612 nodes) | **U_z = 0** | U_x, U_y (so radial and hoop) |
| Displacement `LC2_OUTLET_END_Uz0` (global CS) | face SOLID_OUTLET_END (612 nodes) | **U_z = 0** | U_x, U_y |
| Nodal Orientation `LC2_HOOP_3NODES_MIDSPAN_Utheta0_orientation_CS_DUCT_CYL` | 3 nodes: `NS_LC2_HOOP_3NODES_MIDSPAN_OUTER` | `nrot` to CS_DUCT_CYL | — |
| Nodal Displacement `LC2_HOOP_3NODES_MIDSPAN_Utheta0` | same 3 nodes | **U_θ = 0** only | U_r, U_z |

- **End faces.** In the input file both end faces are one component, `_DISPZEROUZ`: 1,224 nodes = the inlet plus outlet end-face nodes, with `d,all,uz,0`.
- **Hoop nodes.** 25874 (0°), 25886 (120°) and 25862 (240°), at mid-span z = 300 mm and r = 20 mm.

**Why.**

- **The restraint.** LC2 is the Section 2 "fully restrained axially" case, now with the real field. U_z = 0 on both complete end faces holds the length at 600 mm and keeps the end planes plane. That is the axial restraint of a duct clamped between rigid flanges.
- **Radial and hoop.** Radial (and hoop) motion is free on every node, including the end faces. The barrel is not fixed.
- **What the end-face constraint already removes.** U_z = 0 removes axial translation and the x/y rotations.
- **What the 3 hoop constraints remove.** x/y translation and rotation about z. They add no restraint to the axisymmetric deformation, because U_θ = 0 there anyway.

**Why the hoop nodes are at mid-span (run-1 correction).** In build run 1 they were the inlet-end nodes of LC1. Mechanical refused to write the LC2 input: "conflicting DOF constraints with defined Direct FE loading", because a face Displacement and a Direct FE nodal displacement fell on the same nodes. The run-1 files are kept in `Mechanical_Setup/Superseded_run1/`. Moving the 3 hoop constraints to the mid-span outer ring removes the conflict without changing the physics.

## Why not other supports

- **"Fixed Support" on an end.** It would clamp radial growth at that end. That is not LC1, and not LC2 either: the brief asks for radial deformation to be permitted.
- **"Frictionless Support" on the end faces.** Equivalent to U_normal = 0 for LC2, i.e. identical. The explicit Displacement U_z = 0 was used so that the DOF is visible.
- **Cylindrical Support on the barrel.** It would fix the barrel. Forbidden by the brief and by D-025.

## Pressure load

Prepared in both load cases and **suppressed**. See `Loads/LOADS_7A.md`.
