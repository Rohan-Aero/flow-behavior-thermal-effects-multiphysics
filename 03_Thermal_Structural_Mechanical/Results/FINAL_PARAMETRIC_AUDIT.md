# Final parametric audit and engineering synthesis — Section 9B-2 (Parts R, V, X, Y)

> **RE-ANALYSIS 2026.** Every number in this document is a newly generated ANSYS 2026 R1 Student result of this re-analysis (Fluent CFD of Section 9B-1, Mechanical of Section 9B-2), computed from the solver's own output tables. Nothing is a recovered internship value, and no experimental or measured data exist or are implied.

## 1. Case validity (Part R)

| Case | CFD converged / valid (9B-1) | Mapping valid | Pre-solve gate | LC1 / LC2 / buckling solved | Invalid elements | Licence | Material range (E, S_y: 20–400 °C) | Solver warnings (categories) | Unexplained warnings | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| C00 | CONVERGED_VALID / True | PASS | PASS (49) | yes | 0 (JR max 1.205, EQ min 0.237) | no failure (108,252 nodes) | inside (150.7–289.4 °C) | shape checking off (default) ×3; out-of-core solver (performance) ×1; elapsed > CPU (performance) ×1; secant-α re-referencing (7B) ×2; snippet mid-side-node reads (7B) ×14 | none | **VALID** |
| V01 | CONVERGED_VALID / True | PASS | PASS (49) | yes | 0 (JR max 1.205, EQ min 0.237) | no failure (108,252 nodes) | inside (162.8–314.3 °C) | shape checking off (default) ×3; secant-α re-referencing (7B) ×2; snippet mid-side-node reads (7B) ×14 | none | **VALID** |
| V03 | CONVERGED_VALID / True | PASS | PASS (49) | yes | 0 (JR max 1.205, EQ min 0.237) | no failure (108,252 nodes) | inside (140.7–268.9 °C) | shape checking off (default) ×3; secant-α re-referencing (7B) ×2; snippet mid-side-node reads (7B) ×14 | none | **VALID** |
| Q01 | CONVERGED_VALID / True | PASS | PASS (49) | yes | 0 (JR max 1.205, EQ min 0.237) | no failure (108,252 nodes) | inside (137.4–261.3 °C) | shape checking off (default) ×3; secant-α re-referencing (7B) ×2; snippet mid-side-node reads (7B) ×14 | none | **VALID** |
| Q03 | CONVERGED_VALID / True | PASS | PASS (49) | yes | 0 (JR max 1.205, EQ min 0.237) | no failure (108,252 nodes) | inside (164.1–318.0 °C) | shape checking off (default) ×3; elapsed > CPU (performance) ×1; secant-α re-referencing (7B) ×2; snippet mid-side-node reads (7B) ×14 | none | **VALID** |
| T01 | CONVERGED_VALID / True | PASS | PASS (44) | yes | 0 (JR max 1.205, EQ min 0.237) | no failure (89,424 nodes) | inside (144.8–288.8 °C) | shape checking off (default) ×3; secant-α re-referencing (7B) ×2; snippet mid-side-node reads (7B) ×14 | none | **VALID** |
| T03 | CONVERGED_VALID / True | PASS | PASS (44) | yes | 0 (JR max 1.205, EQ min 0.237) | no failure (127,080 nodes) | inside (155.6–289.9 °C) | shape checking off (default) ×3; out-of-core solver (performance) ×1; elapsed > CPU (performance) ×1; secant-α re-referencing (7B) ×2; snippet mid-side-node reads (7B) ×14 | none | **VALID** |
| M01 | CONVERGED_VALID / True | PASS | PASS (44) | yes | 0 (JR max 1.164, EQ min 0.192) | no failure (108,252 nodes) | inside (144.8–288.8 °C) | shape checking off (default) ×3; secant-α re-referencing (7B) ×2; snippet mid-side-node reads (7B) ×14 | none | **VALID** |
| M02 | CONVERGED_VALID / True | PASS | PASS (44) | yes | 0 (JR max 1.245, EQ min 0.279) | no failure (108,252 nodes) | inside (155.6–289.9 °C) | shape checking off (default) ×3; elapsed > CPU (performance) ×1; secant-α re-referencing (7B) ×2; snippet mid-side-node reads (7B) ×14 | none | **VALID** |
| S3 | uses the P00 (Section 5B) CFD field / True | P00 mapping (identical) | PASS (22) | yes | mesh B (7B/8B) | no failure (108,252 nodes) | inside (150.7–289.4 °C) | shape checking off (default) ×2; S3 linear-perturbation-with-contact advisory (explained) ×1; out-of-core solver (performance) ×1; elapsed > CPU (performance) ×1; secant-α re-referencing (7B) ×1; snippet mid-side-node reads (7B) ×8 | none | **VALID** |

Warning categories were all seen and explained in 7B / 8A / 8B:

- the secant-α table re-referenced to T_ref 26.85 °C;
- shape checking off (Mechanical default);
- APDL snippet reads of mid-side-node stresses;
- out-of-core solver mode and elapsed > CPU time (performance only);
- S3 buckling only: MAPDL's advisory that a linear perturbation with contact usually needs NLGEOM,ON in the base analysis. The only contact pair is the bonded (KEYOPT(12) = 5) MPC force-distributed remote-point constraint, whose status cannot change; every buckling case of the project (S1, S2, S3 and the design cases) uses a small-deflection pre-stress by design; the same outlet block reproduced the clamped–pinned column in B03.

**S2 (8A solution, re-extracted).** Solved and audited in 8A. Its nodal table was re-extracted in 9B-2 without re-solving. Validation: the same MAPDL file applied to the 8A S1 result reproduces the 8A in-session table in every column (max difference 0.0e+00); S2 self-check: |u_θ| ≤ 1.2e-12 m at the 1202 U_θ-constrained end-face nodes, u_r uniform around the end-face rings. The first re-extraction run read both result files in one MAPDL session; see §6.

**No case failed, so no case was stopped. No value was fabricated or interpolated.** Runs that stopped at a gate *before* solving are recorded in §6.

## 2. Design-space validity (Part V)

| Condition | Finding |
|---|---|
| Material-property limits | every structural temperature lies inside the E(T) and S_y(T) tables (max 591.12 K = 318.0 °C < 400 °C). The secant-α table starts at 93.3 °C and every node is hotter (min 137.4 °C). No extrapolation |
| Invalid temperature range | none. The CFD air-property tables end at 600 K; the highest air-side temperatures (wall interface / fluid cell) are Q03 583.4 / 581.4 K, V01 580.4 / 578.6 K — F-049 (9B-1) |
| λ₁ < 1 (S1 supports) | **Q03 (0.9883), T01 (0.9450)** → LC2 static stress labelled as pre-buckling equilibrium (Part I) |
| Yield utilisation ≥ 1 | **none** (max 0.6446, Q03) |
| Excessive deformation | none: LC1 growth 1.625–2.064 mm on 600 mm; LC2 total ≤ 0.151 mm |
| Unexplained solver behaviour | none (§1). All reactions balance: LC2 end forces equal and opposite; LC1 reactions ≈ 0 |

## 3. Uncertainty — kept separate (Part X)

No combined percentage is formed, because the sources are of different kinds: discretisation, model form, assumption, idealisation. Values are for the baseline unless stated otherwise.

| # | Source | What it affects | Size (evidence) |
|---|---|---|---|
| 1 | CFD mesh | temperatures → LC2 stress, λ₁ | 6B GCI: temperature-driven LC2 stress −10.1 / +2.8 MPa; λ₁ +1.8 / −0.5 % (8B). T03 solid resolution (M03, 12 → 18 solid layers): node-field change ≤ 0.20 K, mid-span through-wall ΔT -0.0055 K, inlet-face through-wall ΔT +0.30 K (+1.8 %) |
| 2 | CFD property / model | wall temperatures, hence everything thermal | SST k-ω, constant-q″ idealisation, air tables to 600 K (highest air-side wall-interface temperature 583.4 K, 16.6 K below the limit, F-049). Not quantified by a model-form study |
| 3 | CFD → Mechanical mapping | local temperatures (LC1 inlet peak most) | (A) ≤ 0.154 K; numbering sensitivity (C00): LC2 peak 9.5e-06, λ₁ -4.2e-07, LC1 inlet peak -0.46 %; FV near-end limitation F-035 (LC1 inlet peak bound ±9.8 MPa, 8B) |
| 4 | Structural mesh | LC1 surface stresses; LC2 and λ₁ negligible | 8B: LC2 ≤ 10⁻⁴, λ₁ ≤ 6 × 10⁻⁶; LC1 bore σθ −2.1 % (sign known). T geometries (M01/M02): LC2 and λ₁ ≤ 1.4e-04; LC1 peak +1.39 % / -1.15 % |
| 5 | Material properties | E(T), α(T) → stress ∝ Eα; S_y(T) → utilisation | datasheet tables (VDM 4127 / Special Metals), about ±2 % in E and α (8B); S_y typical, not minimum-guaranteed — utilisation not a certified margin |
| 6 | Poisson ratio 0.294 [ASSUMED] | LC2 radial / hoop stresses, bending stiffness via shear | not varied (T-014 / F-011 open). λ₁ enters only through the shear correction (small) |
| 7 | Support / end condition | λ₁ (dominant), mechanism order | S1 1.108 → S3 2.232 → S2 4.300: a factor of about 4 on λ₁ from supports alone — **the largest single uncertainty for stability** (T-034) |
| 8 | Geometric imperfection / nonlinear buckling | λ₁ is an upper bound of the real collapse load | linear eigenvalue, perfect tube. Intermediate slenderness (KL/r ≈ 54 < C_c ≈ 60): Johnson inelastic 1.06 for S1 (8A). Not solved (T-035) |

## 4. Engineering synthesis — the ten questions (Part Y)

*No design is ranked or declared preferable. All statements hold for the idealised supports and the ±10 / ±20 % one-factor steps studied.*

**1. How does velocity affect flow and thermal response?** Δp rises with V (-13.3 / +14.1 % for −/+10 % V, a local exponent of about 1.37; see `PARAMETRIC_TRENDS.md` §4). A lower velocity removes the same heat with less mass flow, so all temperatures rise: V01 T_out +7.62 K, solid max +24.89 K, solid mean +21.48 K; V03 the reverse. Structurally, V acts only through the temperature: LC2 end force +9.72 / -8.00 %, λ₁ 1.0031 / 1.2109.

**2. How does heat flux affect thermal and structural response?** q″ is the load. ±10 % changes the heat input by ±10 % and the solid mean temperature by -24.41 / +24.82 K (the rise above the inlet by slightly more than ±10 %). The restrained end force follows (-11.02 / +11.23 %), λ₁ goes to 1.2546 / 0.9883, and the utilisation to 0.5129 / 0.6446.

**3. How does wall thickness affect stiffness and stability?** With Q held, the temperatures change by < 1 K, so the thermal stress level is nearly unchanged (LC2 VM -0.47 / +0.43 %). The section changes: A by -25.3 / +28.0 %, I by -36.7 / +49.5 %. The end force follows A (-25.6 / +28.5 %) and P_cr follows EI (-36.6 / +49.3 %), so λ₁ ∝ r_g² goes to 0.9450 (8 mm) and 1.2870 (12 mm). The LC1 free growth is almost unchanged (-0.44 / +0.42 %); the LC1 peak stress changes by -14.0 / +12.0 % with the through-wall temperature difference, and stays at about 2 % of S_y.

**4. How sensitive is the structural conclusion to support conditions?** Very. The static stress is almost unchanged, but λ₁ spans 1.108 (S1) – 2.232 (S3) – 4.300 (S2), and the governing mechanism switches: S1 buckles before first yield, while S2 and S3 would yield (or buckle inelastically) first. The real end restraint is undefined (T-034), so the choice between a stability-controlled and a yield-controlled conclusion cannot be made from this model.

**5. Which quantity is most sensitive to each parameter?** Normalised sensitivity S = (Δy/y)/(Δx/x) from the three solved points (`PARAMETRIC_TRENDS.md` §4). Velocity: Pressure drop Δp [Pa] (S +1.37), LC1 axial growth [mm] (S -0.95), λ₁ [-] (S +0.94). Heat flux: λ₁ [-] (S -1.20), LC1 axial growth [mm] (S +1.19), LC2 utilisation [-] (S +1.14). Thickness: P_cr [kN] (S +2.15), LC2 end reaction [kN] (S +1.35), λ₁ [-] (S +0.77).

**6. Which cases are stability-limited?** With the S1 supports: **7 of 7 design cases** — P00 (λ₁ 1.108 < 1.730), V01 (λ₁ 1.003 < 1.575), V03 (λ₁ 1.211 < 1.882), Q01 (λ₁ 1.255 < 1.950), Q03 (λ₁ 0.988 < 1.551), T01 (λ₁ 0.945 < 1.741), T03 (λ₁ 1.287 < 1.720). In each, λ₁ is below the first-yield factor. λ₁ < 1 in Q03, T01: for these, the LC2 static state is a pre-buckling equilibrium result only. V01 is marginal: λ₁ = 1.0031, 0.31 % above 1, well inside the uncertainties of §3.

**7. Which cases are yield-limited?** With the S1 supports: none. No case reaches first yield at the applied load (max utilisation 0.6446). The S2 and S3 *support* variants of P00 would be yield-limited in the idealised model (first-yield factor 1.73 < λ₁).

**8. Does the critical location move?** No, not with V, q″ or t: the LC2 maximum stays at the outer edge of the inlet face, and the LC1 maximum at the bore 6.5 mm from the inlet. Only the temperature there changes. For S2 and S3 see `SUPPORT_SENSITIVITY_RESULTS.md` §4.

**9. Does the buckling mode change?** Not with the design variables: the global guided-sway column mode (orthogonal pair, no local or shell mode) in every case. It changes with the support: guided sway (S1), fixed–pinned (S3) and clamped (S2).

**10. What uncertainties still dominate?** For stability, the **end-restraint definition** (a factor of about 4 on λ₁), then the **imperfection / inelastic-buckling gap** of the linear eigenvalue. For stresses and λ₁ within a support definition, the **CFD temperature field** (6B mesh; property / model form near the 600 K air limit). Mapping, structural mesh and ν are small by comparison. §3 keeps them separate.

## 5. Controls

- **C00** reproduces 7B/8A within 10⁻⁵ on LC2 VM, end force and λ₁. The remaining LC1 inlet-peak difference is the mapping-numbering effect (§3, #3).
- **M03** (T03 CFD solid layers 12 → 18): adequate, no remap (`Mesh_Checks/M03_MESH_ADEQUACY.md`).
- **M01 / M02**: the 4- and 6-division meshes of T01 / T03 are kept: LC2 mean stress and λ₁ change ≤ 4.2e-06, the LC2 peak ≤ 1.4e-04 (M01 above the 10⁻⁴ class-A tolerance at the single inlet-edge node, 34× below the T01 change of the LC2 peak), the LC1 peak by up to 1.4 % (`PARAMETRIC_STRUCTURAL_RESULTS.md` §2).
- **B03**: S3 implementation verified before the real S3 solve.

## 6. Run history (nothing deleted; archives in `Structural_Cases/Audits/`)

| Run | What happened | Action |
|---|---|---|
| C00 run 1 | Mechanical did not start: `current_case.json` contained .NET booleans (invalid JSON). Nothing solved | plain Python types + JSON validity check (`Run1_C00_FAIL_json`) |
| C00 run 2 | solved, bit-identical to 7B/8A, but — as T01 run 1 then showed — with the cached P00 source | kept for the record (`Run2_C00_before_setup_refresh`) |
| T01 run 1 | gate STOP: Mechanical source min/max = P00 values. The External Data change had not reached the analyses | refresh the Setup cells after the ED update (`Run1_T01_FAIL_stale_ED`) |
| C00 run 3 | gate STOP: bitwise temperature identity to 7B failed (max 0.081 K, re-numbered source) | criterion revised to 2 × the 7A mapping error (`Run3_C00_FAIL_bitwise_criterion`) |
| ALL run 4 | C00 and T01 solved; machine shut down during the T03 set-up (nothing solved for T03) | remaining cases re-run by `chain_rest.ps1` (`Run4_ALL_interrupted_by_shutdown`) |
| REST (chain_rest) | T03, V01, V03, Q01, Q03, M01, M02 solved, every gate PASS | results used |
| S3 deck runs 1–5 | Mechanical's `ImportLoad()` on the imported-temperature object raised NullReferenceException in the copied project (also for the LC2 re-import, before any new object). Nothing solved | a probe showed the group-level import works; `import_s3()` imports through the imported-load group (`Run1…Run5_S3_deck_FAIL_import`) |
| S3 deck run 6 | gate STOP: the check expected CONTA175, Mechanical wrote CONTA174 face elements | check changed to CONTA174/175 plus key-option and pilot-constraint checks (`Run6_S3_deck_FAIL_gate_CONTA174`) |
| S3 deck run 7 | deck written, gate PASS (22), not solved | deck copied into B03 |
| B03 run 1 / run 2 | run 1: two checks failed as first formulated (see `SUPPORT_SENSITIVITY_RESULTS.md` §2); reformulated, run 1 re-evaluated PASS; run 2 (structured mesh) PASS under the original limits too | real S3 solved afterwards |
| S3 solve | deck identical to run 7, static + buckling solved, gate PASS | results used |
| Integrity check (verification V7, first run) | 08_Structural_Analysis: 0 files changed, 0 missing, 1 added — a Python bytecode cache (`Buckling/__pycache__/mode_shapes.cpython-310.pyc`) written when post_9B2.py imported the unchanged 8A module | cache file moved (not deleted) to `Results/Verification_9B2/Moved_from_08/`; post_9B2.py now sets `sys.dont_write_bytecode`; post re-run with identical results; V7 PASS |
| S2 re-extraction run 1 | S2 and the S1 validation read in one MAPDL session: the S1 table inherited the S2 nodal rotations (u_r / u_θ wrong at 1,204 nodes; stresses, T, u_z exact). The S2 table itself was correct. A rotation-correction hypothesis (`fix_rotated`) was written and withdrawn; no reported number used it | run 2 with /CLEAR between the files: S1 validation exact, S2 table identical to run 1 (`S2_REEXTRACT/Run1_shared_session`) |

## 7. Independent verification

`Results/Verification_9B2/verify_9B2.py` recomputes the headline numbers from the raw solver tables with its own code; it does not import the post-processing scripts. It also checks the gates, the brief's rules and the 08_Structural_Analysis integrity: **45 / 46 PASS**.

Failed checks:

- V5 M01_T01_STRUCT_NR5: LC2 max vm, mean axial stress and lambda1 within 1e-4 of T01_THIN — {'LC2 max vm': 0.0001395, 'LC2 mean axial stress': -3.9e-06, 'lambda1': -4.2e-06}

The only failed check is the 10⁻⁴ class-A tolerance of the M01 structural-mesh check, exceeded by the LC2 peak (a single node at the inlet-face edge); the mean stress and λ₁ meet it by a factor of more than 20. Its effect is assessed in `PARAMETRIC_STRUCTURAL_RESULTS.md` §2 and carried as structural-mesh uncertainty (§3, #4). The tolerance was not relaxed after the result.

## 8. Readiness

All approved Mechanical and buckling cases are solved and audited. The design cases are P00, V01, V03, Q01, Q03, T01 and T03 (plus the C00 control, and M01 / M02). The S3 support case is solved after the B03 benchmark passed; S1 and S2 are reused. The results are ready for the final engineering synthesis / report. The report and presentation were **not** written (by instruction).
