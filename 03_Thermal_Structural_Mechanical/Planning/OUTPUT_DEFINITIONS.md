# Section 9A: output definitions for every parametric case (identical to the baseline)

> **RE-ANALYSIS 2026.** Every quantity is defined exactly as it was for P00_BASELINE and extracted by the same scripts or APDL snippets. Nothing is re-defined for the parametric study.
>
> - Every case result is reported as its value **and** its change from P00 (% or K).
> - No case is compared with another case without P00 shown alongside.

## 1. CFD outputs (Fluent, one per design case)

| Output | Definition (as in Section 5B) | Source in the baseline workflow | P00 value |
|---|---|---|---|
| Mass flow ṁ | Fluent conservative mass-flux report at the inlet (and outlet, for the imbalance check) | `fluent_flux_mass.txt`, report `mdot_in/out` | 8.6622 g/s |
| Pressure drop Δp | **area-weighted static gauge pressure, inlet face minus outlet face** (D-031); total pressure never mixed in | `fluent_si_p_area.txt`, report `p_in_area` − `p_out_area` | 438.13 Pa |
| Outlet temperature T_out | **mass-weighted** static temperature on the outlet face | `fluent_si_T_mass.txt`, report `T_out_bulk` | 368.93 K |
| Heat-transfer rate Q | total heat rate through `heated_outer_wall` (= interface heat, energy closure checked) | `fluent_flux_heat.txt`, reports `q_heated_wall`, `q_interface` | 602.76 W |
| Maximum solid temperature | maximum over the solid zone including its boundary facets = outer-wall facet maximum; the cell-centre maximum is also recorded | reports `T_outer_max` / `T_solid_max` | 562.58 K / 562.13 K |
| Validity monitors (not design outputs) | interface facet maximum; fluid-cell maximum; solid minimum; y⁺ max/mean/min on the conjugate wall; all at every iteration | reports `T_wall_max`, `T_fluid_max`, `T_solid_min`, `yplus_*` | 555.27 / 553.41 / 423.97 K; y⁺ 0.585 / 0.241 |
| Volume-mean solid temperature (structural consistency) | volume-weighted mean over the solid cells | report `T_solid_mean` | 525.48 K |

**Convergence acceptance per case** (D-030 unchanged):

- NR-03 residual targets met;
- a 200-iteration plateau taken from second-order iterations only;
- mass and energy imbalance below target;
- confirmation over a further 100 iterations.

## 2. Structural outputs (Mechanical / MAPDL, same APDL post-snippets as 7B/8A/8B)

| Case | Output | Definition | Script | P00 value |
|---|---|---|---|---|
| LC1 | Axial expansion ΔL | face-mean u_z(outlet) − face-mean u_z(inlet) (area-weighted over the end faces) | `post_8B.py` (`dL_face_mean`) from `s7b_nodal.csv` | 1.8409 mm |
| LC1 | Maximum deformation | maximum total displacement over all nodes | `s7b_nodal.csv` / Mechanical Total Deformation | 1.8443 mm |
| LC1 | Maximum von Mises stress | maximum corner-node SEQV (= Mechanical averaged maximum); location (r, z, θ, T) recorded; unaveraged maximum also recorded | same | 24.28 MPa (bore, z 6.5 mm) |
| LC2 | Maximum von Mises stress | as LC1 | same | 605.16 MPa (outer edge of the inlet face, 437.99 K) |
| LC2 | Mean axial stress | −\|inlet-face reaction\| / A, with A = π/4 (D_o² − D_i²) **of the case geometry** | `s7b_react.csv` | −582.44 MPa |
| LC2 | Deformation | maximum total displacement | `s7b_nodal.csv` | 0.1349 mm |
| LC2 | Radial deformation | maximum u_r in the cylindrical CS (`CS_DUCT_CYL`) | same | 0.0897 mm |
| LC2 | Local yield utilisation | σ_vm / S_y(T) at the location of the maximum σ_vm, with S_y(T) interpolated in the VDM 4127 table (D-050). The **maximum of σ_vm / S_y(T) over all corner nodes** is also reported (governing location) | `post_7B.py` utilisation block | 0.578 |
| Stability | λ₁ | first eigenvalue of the linear buckling linked to the case's own LC2 (perturbation, all LC2 boundary conditions kept, 6 modes) | `s8a_load_factors.csv` = solve.out = Mechanical LoadMultiplier | 1.1080 |
| Stability | Critical buckling load | P_cr = λ₁ × N, with N the case's own LC2 end reaction | as above | 608.2 kN |
| Stability | Mode classification | `mode_shapes.py` (8A, unchanged): beam-type share, ovalisation, lobes, correlation with the guided / clamped / pinned shapes, location of the maximum lateral deflection, perpendicular pair | `s8a_mode1..6.csv` | global guided sway |

## 3. Derived comparison quantities

| Quantity | Definition | Use |
|---|---|---|
| Change from P00 | (X_case − X_P00) / \|X_P00\| × 100 %; temperatures in K | every table and plot |
| First-yield factor | 1 / utilisation | compared with λ₁ to state whether stability or yield governs, per case and support |
| Screening vs solved | solved value against the anchored screening estimate | checks the screening model; not a validation |
