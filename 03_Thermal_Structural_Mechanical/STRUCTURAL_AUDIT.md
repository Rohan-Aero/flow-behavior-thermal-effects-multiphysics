# Section 7B: structural audit (LC1, LC2, LC2P)

> **RE-ANALYSIS 2026.** This is an audit of new solutions of the newly built 7A model. Nothing is a recovered original, and there are no experimental data.
>
> Every "found" value is read from:
>
> - `Audits/presolve_audit_7B.json` (61 checks, run inside Mechanical before any solve);
> - the solved model (`Audits/mech_solve_7B_summary.json`);
> - the solver output (`*/Solver_Output/solve.out`);
> - `Results/post_7B_results.json`.
>
> Results are summarised in `STRUCTURAL_RESULTS.md`.

## 1. Verdict

| Area | Status |
|---|---|
| Model definition vs 7A | **Unchanged.** Temperature field, geometry, mesh, material and restraints are identical to 7A, proven section by section in the written solver inputs |
| Pre-solve gate | **PASS, 61/61** (run 2). Run 1 stopped at the gate; see §2 |
| Solutions | LC1, LC2 and LC2P **Solved** (Solution status Done). All Workbench cells Up to Date. No solver error |
| Equilibrium | LC1 reactions ≈ 0 (≤ 6.6 × 10⁻⁶ N). LC2 end reactions ±548,936.6 N, balanced to 1.8 × 10⁻⁸ N and equal to the analytical restrained force to 1 × 10⁻⁵ |
| Temperature in the solver | = mapped CFD field (≤ 1.6 × 10⁻⁵ K from the input BFBLOCK) on all 108,252 nodes |
| Singularities | None found. Peaks are smooth, and averaged vs unaveraged von Mises differ by ≤ 0.3 % |
| Open items | F-039 stability of LC2 (not assessed); F-040 peaks inside the F-035 inlet zone; mesh sensitivity prepared, not run |

## 2. Run history (nothing deleted)

| Run | What happened | Evidence |
|---|---|---|
| APDL snippet syntax test | The post-processing snippet (`s7b_post_snippet.inp`) was first run on a **toy** hollow cylinder in MAPDL. It showed that every command runs with 0 errors, and that FSUM needs element nodal forces, which Mechanical's OUTRES does not store. FSUM was removed. The toy numbers are not project results | `Audits/APDL_snippet_test/` |
| Solve run 1 | The gate **failed** on "LC2P input vs LC2 input: identical EBLOCK". The check compared *all* element blocks, but LC2P correctly carries an extra block of 4,680 SURF154 elements for the pressure. **Nothing was solved.** The check was corrected: the solid block must be identical, and the extra block must be exactly 4,680 SURF154 elements on r = 10 mm. The load was not changed | `Audits/Gate_Run1_FAIL/` (log, JSON, the three presolve inputs, the run-1 script) |
| Solve run 2 | Gate 61/61. Solved LC1 → LC2 → LC2P; evaluated, exported and imaged | `Audits/mech_solve_7B_log.txt` |
| Image runs | Read-only reopen of the solved project for end-centred views; exited **without saving**. The first attempt used the wrong camera attribute; the second ran a stale copy of the script (a device-commit caching issue, caught by the hash check); the third worked. The camera zoom itself was ignored in batch mode (F-042) | `Audits/mech_zoom_images_7B_log*.txt` |

## 3. Mesh validity

| Check | Found |
|---|---|
| Nodes / elements | 108,252 / 23,400 SOLID186 (`et,1,186`, full integration). Identical to 7A: NBLOCK and EBLOCK text match the 7A inputs line for line |
| Licence | 108,252 < 128,000 nodes (measured limit) |
| Jacobian ratio | 1.115–1.205 |
| Element quality | 0.237–0.991 (avg 0.688) |
| Aspect ratio | 1.14–4.88 |
| Warping | ~0 |
| Skewness | 0.056 |
| Parallel deviation | 10° (the circumferential faceting of 36 divisions) |
| MAPDL shape checking during the solve | inactive (Mechanical default `SHPP,OFF`). Shape quality is covered by the metrics above; no invalid element |
| Pivots (sparse direct) | LC1 min 3.5 × 10⁵ / max 7.7 × 10⁹; LC2P min 1.2 × 10⁷ / max 7.7 × 10⁹. **All positive**: no mechanism, no singular stiffness |
| Geometry | solid volume = π(r_o² − r_i²)L to < 0.1 %; mesh extents r 10.000–20.000 mm, z 0–600.000 mm; FLUID_DOMAIN suppressed |

## 4. Material

The solver input tables are identical to 7A:

- `MPDATA,EX` 204 / 199 / 193 / 187 / 180 GPa at 20–400 °C: **temperature-dependent, active**.
- `NUXY` 0.294 at all points, **[ASSUMED]**.
- `ALPX` 12.8–14.8 × 10⁻⁶ /K at 93.33–537.78 °C, secant: **temperature-dependent, active**.
- `MPAMOD,1,21.11`.
- `MP,DENS` 8190.
- Material `Inconel_718_Re_analysis` on SOLID_DOMAIN.

**Expected warnings.**

- *"ALPX evaluated at 26.85 °C, below the supplied range"*. T_ref lies below the first CTE point, so the constant extrapolation α(26.85 °C) = α(93.33 °C) is used for the MPAMOD re-referencing only. All loaded temperatures (150.7–289.4 °C) are inside the table.
- Mechanical's *"reference temperature for the thermal expansion coefficient differs…"*. Documented in 7A.

**Independent confirmation.** The free growth computed outside ANSYS from the same tables, using MAPDL's MPAMOD rule, matches the FE to 1.3 × 10⁻⁵ (RESULTS §3.1). This confirms that the material law the solver applied is the intended one.

## 5. Temperature mapping and T_ref

| Check | Found |
|---|---|
| Imported temperature objects | state "Solved" on opening; settings Manual / BucketVolume / ShapeFunctions / NearestNode; no unmapped-node set |
| Re-export vs 7A export | **byte-identical** for LC1, LC2 and LC2P (LC2P was freshly imported with the same settings) |
| BFBLOCK | 108,252 nodal temperatures in all three inputs; identical text to 7A; 423.84–562.56 K |
| T actually used (BFE,TEMP from the solved database) | 423.84–562.56 K; max deviation from BFBLOCK 1.6 × 10⁻⁵ K on every node |
| T_ref | `TREF,26.85` = 300.00 K in all inputs; environment temperature 26.85 °C in all three analyses |
| Replacement fields | none: no uniform, mean, max or analytical T anywhere |

## 6. Constraints (read from the solver inputs, name-independent)

The constraints are resolved to DOF, value and node set.

| Case | Constrained DOFs | Free |
|---|---|---|
| LC1 | nodes 18870, 18882, 18894 rotated to local CS 12 (cylindrical): **U_θ = 0, U_z = 0** (6 DOFs) | U_r at those 3 nodes; all DOFs everywhere else |
| LC2 | **U_z = 0** on 1,224 nodes = both complete end faces (global); nodes 25862, 25874, 25886 rotated to CS 12: **U_θ = 0** | U_x, U_y (so radial and hoop) on the end faces; U_r and U_z at the hoop nodes; all DOFs elsewhere. The barrel is not fixed |
| LC2P | identical to LC2 (same resolved set) | same |

**No over-constraint.**

- LC1 is statically determinate: 3 non-collinear U_z constraints and 3 U_θ constraints at 120° spacing.
- In LC2, U_z = 0 on both faces holds the length and keeps the end planes plane. The 3 hoop constraints only remove x/y translation and z rotation.
- Neither case suppresses radial growth. Proof: LC2 radial growth exceeds LC1 by exactly the Poisson term ν|σ̄_z|r/E (18.1 µm at mid-span).
- There are no weak springs in any input, and no hidden constraints (`d`, `cp`, `ce`) besides those listed.

## 7. Equilibrium, reactions and moments

**LC1.**

- Largest nodal reaction 6.6 × 10⁻⁶ N.
- ΣF magnitude 3.9 × 10⁻⁷ N; ΣM magnitude 2.1 × 10⁻⁷ N·m about (0,0,0).
- These are identical in the Mechanical probes and the APDL table.
- Section force ∫σ_z dA along the duct is ≈ 0 (±125 N). That residual is the 6-point radial trapezoid applied to a through-wall σ_z that changes sign: the tension and compression parts are +3.36 / −3.49 kN at mid-span. The exact resultant is the reaction.

**LC2 and LC2P.**

- End-face reactions: LC2 ±548,936.61 N, LC2P ±548,936.53 N. Each pair balances to ≤ 1.8 × 10⁻⁸ N.
- The hoop nodes carry ≤ 1 × 10⁻⁷ N.
- ΣM ≤ 3.1 × 10⁻⁸ N·m.
- N(z) = −549.06 kN is constant over all 131 sections (±0.1 kN): axial equilibrium through the structure.
- The analytical restrained force for the same field, −∫ε̄_th dz / ∫dz/(Ē A), is −548,931 N. It agrees with the reaction to 1 × 10⁻⁵.

**Rigid-body warning.** Mechanical's warning is its generic check and does not see Direct FE supports. It was **not** used to judge the model. The evidence is:

- zero-level LC1 reactions;
- positive pivots;
- a completed solution with bounded displacements (1.84 mm, as the thermal integral predicts).

**F-036 is closed.**

**Coordinate systems of the reactions.**

- `*VGET RF` returns nodal-CS values. This was checked: PRRSOL (global) matches `*VGET` transformed by θ for node 18870 at 240°.
- The rotated nodes were transformed before summing.

## 8. LC1 behaviour

| Check | Found | Judgement |
|---|---|---|
| Free growth | 1.84086 mm vs independent ∫ε_th dz 1.84084 mm | agrees to 1.3 × 10⁻⁵: kinematics and load correct |
| Radial growth free | bore 32.2 µm at mid-span vs α_sec·ΔT·r 31.5 µm | free radially (the difference is the through-wall gradient) |
| Mid-span stress vs Timoshenko (same wall T) | bore σ_θ 18.31 vs 18.55 MPa; outer −11.69 vs −11.76 MPa | −1.3 % / −0.6 %: T-013 closed |
| Stress at the supports | von Mises at the 3 support nodes = ring mean (21.12 MPa) | supports add no stress |
| Non-zero stress sources | through-wall gradient, inlet end effect (peak 24.28 MPa, z 6.5 mm), outlet free-face relief | physical; see RESULTS §3.2 |

## 9. LC2 behaviour

| Check | Found | Judgement |
|---|---|---|
| Mean axial stress | −582.44 MPa = N/A | equals the analytical value for the same field (1 × 10⁻⁵) and Section 2 rescaled to the CFD mean rise (−581.9 MPa, 0.1 %) |
| Axial displacement | 0 at both faces; interior −0.109 mm | the hot outlet part pushes the cooler inlet part; total length fixed |
| Radial growth not suppressed | LC2 − LC1 = ν|σ̄_z|r/E (18.1 vs 18.1 µm) | radial free as intended |
| Stress near the restraint | outlet: flat (587.2–587.5 MPa); inlet: +18 MPa rise over 25 mm, following the entrance-region through-wall ΔT (14.1 K at z = 0) | restraint is symmetry-type; the peak is thermal, not a restraint singularity |
| Stress distribution | 586–605 MPa (outer), 561–576 MPa (bore) along the whole duct | restraint-dominated, as Section 2 predicted |

## 10. Pressure effect

- **Load definition.** Gauge 443.41 Pa (CFD maximum; a bound). Differential internal − external. No atmospheric absolute pressure. Applied through 4,680 SURF154 elements on the bore only (verified r = 10.000 mm for every element node).
- **Verification.** LC2P − LC2 matches Lamé plane strain: σ_θ at the bore within −0.3 %, u_r at the bore within +0.1 %. The end reactions change by −0.08 N, which equals the Poisson term 86.9 Pa × A.
- **Effect.** Max von Mises +45 Pa (+7.4 × 10⁻⁶ %). Max deformation +1.7 × 10⁻¹¹ m.
- **Numerical resolution.** Both cases use the sparse direct solver. The point-to-point scatter of the von Mises difference is about ±15 Pa (2.5 × 10⁻⁸ relative), so the effect of 45–160 Pa is resolved.
- **Conclusion.** Negligible, **confirmed by calculation** (T-030 closed).

## 11. Critical temperature, yield basis and utilisation

| Case | Critical point | Local T | S_y(T) | Utilisation | Margin |
|---|---|---|---|---|---|
| LC1 | bore, z 6.52 mm (node 19007) | 427.81 K / 154.7 °C | 1049.1 MPa | 0.0231 | 42.2 |
| LC2 | outer edge of the inlet face (node 18865) | 437.99 K / 164.8 °C | 1047.0 MPa | **0.578** | **0.730** |
| LC2 (interior, highest utilisation) | outer, z 562.7 mm (node 24110) | 561.74 K / 288.6 °C | 1022.3 MPa | 0.575 | 0.740 |
| LC2P | node 18865 | 437.99 K | 1047.0 MPa | 0.578 | 0.730 |

- **Yield basis.** VDM 4127 table, linear interpolation. The local temperatures are inside 20–400 °C, so no extrapolation was needed (the post-processing raises an error if one would be). The scalar 1020 MPa is not used (F-037 addressed, T-031 closed).
- **Node-wise check.** Utilisation was scanned node by node (σ_vm / S_y(T_node)) over all corner nodes. The global maximum is at the von Mises maximum; the interior hot-end maximum (0.575) is within 0.6 % of it (0.578).

## 12. Singularities, under-resolution and mesh-sensitivity preparation

**Nothing was refined and no mesh study was run, by instruction.** This section only inspects the solution.

### 12.1 Singularity check

| Candidate | Evidence | Conclusion |
|---|---|---|
| LC1 point supports (3 nodes) | reactions ≈ 10⁻⁶ N; support-node von Mises = ring mean | no concentrated load, so **no singularity** |
| LC2 end faces (U_z = 0, in-plane free) | symmetry-type condition; outlet end shows no stress rise at all | **no geometric singularity** |
| LC2 hoop nodes | reactions ≈ 10⁻⁷ N | none |
| Peak locations | averaged vs unaveraged von Mises max: LC1 24.282 vs 24.356 MPa (+0.30 %); LC2 605.161 vs 605.185 MPa (+0.004 %). Peaks decay smoothly over several element planes (F7B_03) | resolved; not mesh-driven spikes |

### 12.2 Where the mesh is weakest (structural error, energy norm)

| | LC1 | LC2 |
|---|---|---|
| Total structural error | 7.44 × 10⁻⁶ J | 7.15 × 10⁻⁶ J |
| Strain energy (from the nodal stresses) | 0.154 J | 505.6 J |
| Energy-norm error estimate √(e / (U + e)) | **0.70 %** | **0.012 %** |
| Share of the error in the first 15 mm (5.4 % of the elements) | 12.7 % | 12.9 % |
| Highest element errors | bore-side elements, z ≈ 1–3 mm | bore-side elements, z ≈ 3 mm |
| Error per element ring: first ring vs mid-span ring | 2.36 × 10⁻⁷ vs 9.3 × 10⁻⁸ J (2.5×) | 2.16 × 10⁻⁷ vs 9.1 × 10⁻⁸ J (2.4×) |

The inlet end region is the least resolved part of the model. It is also where both peaks sit and where the transferred temperature is least certain (F-035). The kinks visible in the bore curves at z ≈ 5–10 mm (F7B_03) follow the piecewise gradient of the transferred temperature on the 6.67 mm Fluent axial cells.

**The inlet-zone temperature uncertainty is the larger effect.**

- Up to 2.57 K at the bore. The bound E α ΔT/(1 − ν) is ±9.8 MPa. This is a bound, not a computed value.
- That is ≈ 40 % of the LC1 peak and 1.6 % of the LC2 peak.
- A finer *structural* mesh cannot remove it. The CFD entrance region would need finer axial cells.

### 12.3 Prepared sensitivity study (T-029 / T-033, not run)

- **Keep:** the temperature field, material, restraints and T_ref.
- **Change only the structural mesh, within 128,000 nodes:**
  - (a) axial refinement of the first 30 mm (stronger end bias, or more divisions there);
  - (b) 5 → 7 through-wall elements;
  - (c) one coarser reference (for example 24 × 4 × 100) to give a three-level trend.
- **Monitor:**
  - LC1 peak (bore, z ≈ 6.5 mm);
  - LC2 peak (outer inlet edge);
  - LC1 mid-span bore stress;
  - LC2 mean stress;
  - free growth;
  - end reactions;
  - structural error in the first 15 mm.
- **Expectation, from the evidence above:**
  - LC2 and the interior values change by well under 1 %;
  - the LC1 inlet peak is the quantity most likely to move;
  - the LC1 inlet peak remains limited by F-035 in any case.

## 13. Post-processing integrity

- **Full-precision data.** A post-solve APDL snippet in each Solution writes `s7b_nodal.csv` (E17.9) and `s7b_react.csv` (E22.14). Mechanical's own maxima agree with it to ≤ 6 × 10⁻⁸ for von Mises, principal stresses and deformations, and to 6 × 10⁻⁵ for the LC1 equivalent elastic strain (a different effective-Poisson convention). Mechanical's text exports (5 significant digits) agree to ≤ 5 × 10⁻⁵.
- **Corner nodes only for stress (F-041).** MAPDL stores averaged nodal stresses of SOLID186 at the corner nodes only; `*VGET` returns 0 at the 79,956 midside nodes.
  - The first post-processing pass averaged those zeros and produced an LC2 section force of −91.5 kN against a reaction of −549 kN.
  - The equilibrium check exposed the error.
  - All stress and strain statistics now use the 28,296 corner nodes. Displacements and temperatures use all nodes.
- **Figures.**
  - Mechanical renders are unedited `Graphics.ExportImage` output of the solved result objects.
  - Deformation scaling reads back as "True", ×1.0.
  - Data plots are labelled as plotted from the solution tables.
  - No screenshot was fabricated.
- **Integrity rule.** Nothing was tuned to approach the Section 2 numbers. Temperature field, geometry, mesh, material and restraints are unchanged from 7A (§3–§6). The 7A project files are content-identical before and after 7B; only `.project_cache` changed, and only its modification time (`Audits/pre7B_*`, `post7B_*` hashes).

## 14. Flags and tasks from this audit

| ID | Item |
|---|---|
| **F-039** (new, **Medium**) | LC2 stability not assessed. An indicative hand estimate gives a critical-to-applied ratio of 1.06 (ends free to sway) to 1.58 (no sway). An eigenvalue buckling analysis with the real end conditions is needed (T-032) |
| **F-040** (new, Medium) | Both peaks lie in the F-035 inlet zone. Local bound ±9.8 MPa (≈ 40 % of the LC1 peak, 1.6 % of LC2). Interior values are robust |
| **F-041** (new, Low) | SOLID186 nodal stresses exist at corner nodes only in MAPDL tables; post-processing must filter them (lesson recorded) |
| **F-042** (new, Low) | Mechanical camera zoom and view-vector commands have no effect in batch; the "Zoom" images are end-centred side views |
| F-036 | **CLOSED**: LC1 reactions ≤ 6.6 × 10⁻⁶ N, positive pivots |
| T-013, T-028, T-030, T-031 | **CLOSED** (mid-span comparison; LC1/LC2 solved with reaction checks; pressure superposition; S_y(T) margins) |
| T-029 → **T-033** | structural mesh sensitivity, prepared (§12.3), **not run** |
| **T-032** (new) | eigenvalue buckling of LC2 with the real end restraint (when instructed) |
| T-014 / F-011 | ν still [ASSUMED] (none on the LC2 mean stress; about 1.4 % on LC1) |

## 15. Independent verification pass

After the documents were written, the key numbers were recomputed from the raw solver tables (`s7b_nodal.csv`, `s7b_react.csv`, `s7b_prrsol.txt`, the ds.dat EBLOCK and BFBLOCK) with separately written code that does not use `post_7B.py`. Scripts and record: `Audits/Verification_7B/`.

- **Confirmed** (to the stated digits): all maxima, minima and their nodes, radii, axial positions and temperatures for LC1, LC2 and LC2P; the corner/midside split (28,296 / 79,956 nodes, no overlap, midside stresses all 0); T_used vs BFBLOCK (1.57 × 10⁻⁵ K) and vs the 7A export (0.005 K); every reaction sum, moment and end-face force, including the nodal-CS transformation (the transformed sum reproduces the PRRSOL global totals, the untransformed one does not); the pressure difference (+45.0 Pa, nodes +14 … +161 Pa) and the Lamé comparison; S_y(T), utilisation and margins, including the node-wise scan; the LC1 and LC2 mid-span values; the buckling hand estimate; the 6B sensitivities; the Section 2 ratios; Mechanical maxima vs the snippet table (≤ 2.8 × 10⁻⁸; LC1 elastic strain 6.4 × 10⁻⁵).
- **Quadrature sensitivity of the two integral checks.** The FE-vs-integral agreement for free growth (1.3 × 10⁻⁵) and for the restrained force (1.0 × 10⁻⁵) was reproduced with the same rule (Simpson over the 11 radii, trapezoid over the 131 corner planes). Other reasonable rules give between −1.5 × 10⁻⁵ and +1.3 × 10⁻⁵ for both, so these agreements are at the 10⁻⁵ level set by the quadrature; they are not exact.
- **Timoshenko hand check.** Written with the thermal strain ε_th(T) itself instead of a tangent-α linearisation, the mid-span bore/outer values become 18.67 / −11.63 MPa (vs 18.55 / −11.76). The FE (18.31 / −11.69) is within 2 % of either form.
- **Corrections made to `STRUCTURAL_RESULTS.md` and this audit.** All were rounding or wording; no result changed:
  1. LC2 max-deformation components: u_z −0.1085 and u_r +0.0801 mm (was "−0.108 and +0.081").
  2. LC1 bore von Mises at the outlet face: 0.27 MPa (was 0.26).
  3. LC2 outlet-end plateau: 587.2–587.5 MPa (was 587.3–587.5), in both documents.
  4. 6B utilisation row: states that S_y is held at the nominal temperature (0.570), and gives 0.569 if S_y is shifted too.

