# Section 8B: structural mesh-study audit

> **RE-ANALYSIS 2026.** This audits the new structural mesh-sensitivity study (static LC1 / LC2 / LC2P and LC2 linear buckling).
>
> - Nothing here is a recovered original, and there are no experimental data.
> - Every "found" value comes from one of these:
>   - the per-variant pre-solve gate (`Variants/<tag>/Audits/presolve_audit_<tag>.json`);
>   - the solver files (`Variants/<tag>/Solver_Output/`);
>   - the post-processing JSON (`Post/out/`);
>   - the independent verification (`Audits/Verification_8B/verify_8B_result.json`, **120/120 PASS**);
>   - the device hash comparison (`Audits/hash_compare_7B_pre_post_8B.json`).

## 1. Answers to the audit questions

| Question | Answer | Evidence |
|---|---|---|
| **Is the static solution mesh-converged?** | **LC2: yes (class A).** Peak von Mises within 1 × 10⁻⁴, mean axial stress and reaction within 7 × 10⁻⁶, deformation within 5 × 10⁻⁵ across C, B and the three licence-limited fine meshes. **LC1 deformation: yes (A).** **LC1 stresses: approximately.** The inlet peak is class B (±1.1 %, non-monotonic). The mid-span bore stress is class C at a small absolute level: the baseline is 2.1 % (0.39 MPa) below a 1-D exact solution because of surface-stress recovery | `STRUCTURAL_MESH_COMPARISON.md` §6, §7, §9 |
| **Is buckling mesh-converged?** | **Yes (class A).** λ₁ = 1.10799–1.10805 on all six meshes. Fine meshes vs B ≤ 6 × 10⁻⁶; GCI_fine 5.6 × 10⁻⁶; P_cr = 608.25 kN to 2 × 10⁻⁶ | `BUCKLING_MESH_COMPARISON.md` §3, §5 |
| **Is the critical location stable?** | **Yes.** LC2: outer edge of the inlet face (r 20 mm, z 0, 437.98–437.99 K) on every mesh. The θ position is not meaningful, because the edge stress is uniform to ≤ 0.025 MPa. LC1: bore, z 6.5–8.7 mm (the node plane nearest the true peak) on every mesh | T3, T4 |
| **Is the dominant buckling mode stable?** | **Yes.** Global guided sway on every mesh: corr 0.999997 with cos(πz/L), identical mode order, no local, ovalisation or wrinkling mode, perpendicular pair at 90.0° | `BUCKLING_MESH_COMPARISON.md` §4 |
| **Is the inlet peak stable?** | **LC2: yes.** ≤ 0.01 % under through-wall, axial, circumferential and local (IL, first element 1.36 mm) refinement. Not a singularity: symmetry-type face support, no growth with local refinement, unaveraged − averaged = 4 × 10⁻⁵. **LC1: stable to about 1 %.** Refinement raises it 0.9–1.1 %; it is bounded and not called a singularity | `STRUCTURAL_MESH_COMPARISON.md` §11, F8B_09 |
| **Is the selected mesh within the Student limit?** | **Yes.** B has 108,252 nodes (84.6 % of 128,000). All seven meshes (up to 127,080 nodes) and all buckling runs solved with no licence message | T1; `solve.out` of every run |
| **Remaining mesh uncertainty** | Governing results (LC2, λ₁): ≤ 1 × 10⁻⁴, negligible. LC1 bore stresses: about −2 % bias at mid-span and about −1 to −2 % at the inlet peak (non-conservative, small in absolute terms: ≤ 0.6 MPa) | §7 below |
| **Remaining mapping uncertainty** | Unchanged from 7A and identical on every mesh. Interpolation ≤ 0.09 K (≤ 0.14 K at chord-gap nodes). Node-reconstruction difference up to 2.6 K in the first ~11 mm (F-035: ±9.8 MPa local bound), ≤ 0.28 K elsewhere | T2 |
| **Remaining support-stiffness uncertainty** | **Unchanged, and the dominant one.** λ₁ = 1.108 (sway free) vs 4.300 (ends held laterally). The real flange restraint is undefined (T-034). No mesh refinement affects this | `BUCKLING_MESH_COMPARISON.md` §6 |

## 2. Run history (nothing deleted, no failed run)

| Run | Variants | Journal (SHA-256, first 12) | Result |
|---|---|---|---|
| A (ended 12:35) | XC, C, IL | `wb_meshstudy_8B_A.wbjn` (AFD06F095C71) | all gates PASS (43 / 43 / 31 checks), all solved |
| B (12:35–13:07) | B (baseline control), FR, FA | `wb_meshstudy_8B_B.wbjn` (CD50E1589DB6) | all gates PASS (43 each), all solved |
| C (13:09–13:18) | FC | `wb_meshstudy_8B_C.wbjn` (C3421FED76E8) | gate PASS (43), solved |

**Common to all runs.**

- The Mechanical script is `mech_meshstudy_8B.py` (D55E893BF51B) for every variant.
- No `FAIL` line appears in any Mechanical log, and no variant stopped at its gate.

**Why FC was added after runs A and B.** It was not in the first plan. It was added so that **each of the three mesh directions** of the baseline is refined once at the licence limit. The circumferential direction would otherwise have been refined only inside the coarsening family.

**Cosmetic defect in run C's log.** The final line of `wb_meshstudy_8B_C_log.txt` reads "WB MESH STUDY B DONE", because the journal was derived from run B's. Its first line and variant block correctly read C / FC. No result is affected.

**IL is static only.** It solves LC1 and LC2, with no pressure and no buckling, by design: it is a local inlet check, not part of the family.

## 3. Pre-solve gate per variant (all checks run inside Mechanical before any solve)

| Check group | XC | C | B | FR | FA | FC | IL |
|---|---|---|---|---|---|---|---|
| Start mesh = 7B baseline controls (36/5/130, bias 4) before re-meshing | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Nodes = swept-hex formula; elements = nc·nr·na; < 128,000; quadratic | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| No invalid elements (Jacobian ratio < 40, quality > 0); aspect ratio < 20 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Geometry extents unchanged; end-face node count = 2 nc(3 nr + 2) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| LC1 and LC2 support nodes re-located at r 20 mm, 0/120/240° (z 0 and z 300 mm) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Temperature import settings unchanged; every node mapped; export identical for all cases | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Solver input: material identical to 7B; temperature on every node; sparse solver; no weak springs | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Constraint sets exactly as intended (LC1: 3 nodes; LC2/LC2P: all end-face nodes + 3 hoop nodes) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Pressure only in LC2P (443.41 Pa on nc·na SURF154) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | n/a |
| Buckling: pre-stress = LC2_Axially_Restrained; no own loads or supports | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | n/a |
| **Total** | 43/43 | 43/43 | 43/43 | 43/43 | 43/43 | 43/43 | 31/31 |

## 4. Frozen physics (the only change is the mesh)

- **Material.** Identical, section by section, to the 7B solved input on all seven meshes.
- **Temperature source.** The same (baseline_medium_final), with the same import settings. No re-mapping from another CFD case. Mapped range 423.837–562.560 K on every mesh.
- **Constraints.** Re-generated on each mesh from the same named-selection definitions, and checked in the written input: DOF, value, node count and node positions.
- **Control.** The re-meshed baseline B is **bit-identical** to the official 7B solution: LC1, LC2 and LC2P nodal tables differ by 0 Pa and 0 m at all 108,252 nodes, and the BFBLOCK is byte-identical. B's λ₁ matches 8A to 1.1 × 10⁻⁷.
- **What this proves.** The re-mesh pipeline itself introduces nothing; differences between meshes are mesh effects only.

## 5. Independent checks

| Check | Script | Result |
|---|---|---|
| Mesh validity and connectivity from the solver input decks: 20 distinct nodes per element, no coincident or unreferenced nodes, every internal face shared by exactly 2 elements, free faces = 2·nc·na + 2·nc·nr, corner Jacobians > 0 | `Post/mesh_geometry_8B.py` | PASS on all 8 inputs (7 meshes + 7B official) |
| Temperature mapping per mesh vs (A) the exact source-node-field value and (B) the Fluent FV field | `Post/mapping_check_8B.py` (7A modules unchanged) | B reproduces the 7A values exactly (0.081 / 0.092 / 2.57 K); 0 unmapped on all meshes |
| Exact reference for the LC1 mid-span bore stress | `Post/ref1d_lc1_8B.py` (1-D generalised plane strain, 2,000 elements; solver check vs closed-form Timoshenko: 0.06 %) | 18.698 MPa. FE: B −2.08 %, FR −1.46 % |
| Temperature representation vs stress recovery | `Post/ref1d_split_8B.py` | the mesh-interpolated temperature gives 18.69–18.71 MPa on every mesh (within 0.1 %), so the 2 % is surface-stress recovery |
| Independent verification from raw files only | `Audits/Verification_8B/verify_8B.py` | **120/120 PASS** |

**What the independent verification covers.** It was written separately from the post-processing and reads only raw files:

- node and element counts from the NBLOCK / EBLOCK;
- BFBLOCK range;
- gate results;
- 0 solver errors in every run;
- maximum von Mises from the raw nodal tables = Mechanical's maximum, every mesh and case;
- end-reaction balance;
- LC1 reactions ≈ 0;
- the six load multipliers identical in solve.out, the snippet CSV and Mechanical;
- mode 1 recomputed from the raw eigenvector (ends opposite, mid-span ≈ 0, n = 2 and n = 3 harmonics < 10⁻⁴);
- B = official 7B / 8A;
- Richardson p and extrapolation recomputed for the LC2 peak and λ₁;
- pressure effect positive and tiny on every mesh;
- the 7B project hashes.

## 6. Integrity of the official results

| Item | Status |
|---|---|
| Official 7B project (`Workbench/Flow_Behavior_Thermal_Effects_Structural_7B.wbpj` + files) | opened read-only by the journals and immediately saved *as* `Mesh_Study/Projects/MS8B_<tag>.wbpj`. **58/58 files SHA-256 identical** before run A and after run C (`pre8B_7B_project_hashes.json` vs `post8B_7B_project_hashes.json`) |
| Official 7B result folders (`LC1_Free_Expansion/`, `LC2_Restrained/`, `Pressure_Check/`) and the 8A `Buckling/` folder | not written by any 8B script. All 8B output goes to `Mesh_Study/`. The 8A project was not opened |
| Official LC1/LC2 values | unchanged. The baseline results reported in 7B and 8A remain the project values. 8B adds a mesh-uncertainty statement to them; it does not replace them |
| Figures | data plots from the solver tables, plus unedited Mechanical exports (`Graphics.ExportImage`). No image is edited or fabricated. The PNG copies written to the device carry an extra 5.8 kB `caBX` metadata chunk added by the cloud-to-device file transfer. Their pixel data were verified identical to the generated files (F8B_09 decoded and compared), so their SHA-256 differs from the cloud copies for that reason only |

## 7. Remaining uncertainty after 8B (kept separate, not combined)

| Type | LC2 stress | LC2 / LC1 deformation | LC1 stress | λ₁ |
|---|---|---|---|---|
| A. CFD mesh (6B) | −2.3 / +0.7 % (peak); −1.7 / +0.5 % (mean) | −1.7 / +0.5 % | −0.2 / +0.6 % (mid-span) | +1.8 / −0.5 % |
| B. Mapping / transfer (7A) | ±9.8 MPa local bound at the inlet (1.6 %); interior ≤ 1 MPa | negligible | ±9.8 MPa at the inlet (40 % of the peak) | about −0.02 % |
| C. Structural mesh (8B) | ≤ 1 × 10⁻⁴ | ≤ 5 × 10⁻⁵ | −2 % (mid-span, known sign); about −1 to −2 % (inlet peak) | ≤ 6 × 10⁻⁶ |
| Supports (T-034) | the LC2 idealisation itself | — | — | factor 3.9 (1.108 vs 4.300) |

## 8. Observations and limitations

1. **No uniformly refined fine level exists.** It cannot fit the licence, which is shown by exact node counts. Convergence rests on the coarsening family plus one licence-limited refinement per direction. This is weaker than a three-level study with a finer uniform level. For the governing quantities it is conclusive anyway, because the changes are at 10⁻⁵–10⁻⁴.
2. **The Richardson extrapolation of the LC1 mid-span stress under-shoots the exact value (18.39 vs 18.70 MPa).** The family changes all directions at once, and the error is dominated by the through-wall direction. It is reported, not hidden: family-based extrapolation should not be trusted for through-wall surface stresses on this mesh topology.
3. **The 1-D reference neglects the axial temperature variation at mid-span** (about 0.2 K/mm). It is a reference for the through-wall discretisation only.
4. **The energy-norm estimate is Mechanical's structural-error heuristic,** normalised with the 7B strain energy. It is used only as a trend indicator.
5. **The θ position of discrete maxima differs between meshes.** It has no physical meaning because the fields are nearly axisymmetric (edge variation ≤ 0.025 MPa).
6. **The Workbench variant projects (`Mesh_Study/Projects/`) are solved copies, kept for traceability.** They are not official results.

## 9. Final structural-credibility status (neutral)

**The linear-elastic results are not limited by the structural mesh.**

- **LC2** (yield utilisation 0.578 at the inlet edge; mean axial stress −582.44 MPa) and **LC2 linear buckling** (λ₁ = 1.108, P_cr = 608.2 kN, global sway mode) are mesh-converged on the baseline mesh within 10⁻⁴.
- **LC1 deformation** is mesh-converged. LC1 stresses carry a small known under-prediction of about 2 %.

**The outcome remains stability-controlled for the LC2 idealisation.** λ₁ = 1.108 is below the first-yield factor of about 1.73. That conclusion does not depend on the mesh.

**The primary remaining uncertainty is the end-restraint definition (T-034).** After it come the temperature basis and CFD model, the inelastic and imperfection behaviour (F-044/F-045) and the material data. The structural discretisation is not among them.

This audit does **not** state that the component is safe.
