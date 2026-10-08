# Section 9A: parametric study plan (for approval; nothing run yet)

> **RE-ANALYSIS 2026.** This plan is new work for the re-analysed project.
>
> - No parametric case has been solved. Every number marked "screening" is an analytical or anchored estimate from `Analytical_Screening/parametric_screening.py`, not CFD or Mechanical data.
> - Values marked "solved" are the existing baseline results (Sections 5B, 7B, 8A, 8B).
> - The baseline P00 is frozen and is the reference for every comparison.

**Two questions are kept separate. They are never combined into one matrix.**

- **Question A (design and operating parameters):** how do inlet velocity, heat flux and wall thickness change the thermal-fluid and structural response? Answered with the S1 support throughout.
- **Question B (support sensitivity):** how strongly does the structural conclusion depend on the end restraint? Answered at P00 only.

Detail documents:

- `VARIABLE_EVALUATION.md` (why these variables)
- `MESH_YPLUS_MATERIAL_POLICY.md` (rules)
- `OUTPUT_DEFINITIONS.md` (result definitions)
- `../Support_Sensitivity/SUPPORT_SCENARIOS.md`
- `../Analytical_Screening/SCREENING_RESULTS.md`
- `../Case_Matrix/PARAMETRIC_CASE_MATRIX.csv`
- `../Case_Matrix/CASE_NAMING.md`

## 1. Selected variables

| Variable | Role | Why selected |
|---|---|---|
| **V: inlet velocity** | operating (cooling) lever | the only variable that changes the heat-transfer coefficient and the flow-side outputs (Re, Δp, h, y⁺). It changes wall temperature without changing heat input |
| **Q: outer-wall heat flux q″** | thermal load | the prime driver of temperature, expansion and restrained stress; also scales the through-wall gradient (LC1) |
| **T: wall thickness t** (total heat input Q held constant) | geometric design lever | the only variable that changes the section (A, I) while leaving the thermal field essentially unchanged. It isolates the stability lever that Section 8 found governing |

**Rejected candidates:** length, bore diameter, inlet temperature, outlet pressure, material, ν. Reasons are given in `VARIABLE_EVALUATION.md` §2. None is varied only to produce plots.

## 2. Baseline values and selected ranges

| Variable | Low | **Baseline (P00)** | High | Change |
|---|---|---|---|---|
| Inlet velocity V | 21.15 m/s (V01) | **23.5 m/s** | 25.85 m/s (V03) | ±10 % |
| Outer-wall heat flux q″ | 7,200 W/m² (Q01) | **8,000 W/m²** | 8,800 W/m² (Q03) | ±10 % |
| Wall thickness t (D_o) | 8 mm, D_o 36 mm (T01; q″ 8,888.9 W/m²) | **10 mm, D_o 40 mm** | 12 mm, D_o 44 mm (T03; q″ 7,272.7 W/m²) | ±20 %, Q constant = 603.2 W (analytical) / 602.76 W (CFD, 48-gon) |

**Everything else is frozen at P00:**

- air at 300 K inlet; outlet 0 Pa gauge at 101,325 Pa;
- k-ω SST with a wall-resolved mesh;
- Inconel 718 with E(T), α(T), k(T), c_p(T) and S_y(T) from VDM 4127;
- ν = 0.294 [ASSUMED];
- T_ref = 300 K;
- L = 600 mm, D_i = 20 mm.

**One definitional follow-up:** in V cases the inlet turbulence intensity is recomputed with the baseline formula I = 0.16 Re^−1/8, giving 4.47 % at V01 and 4.36 % at V03 (4.41 % at P00). The definition is kept, not the number.

## 3. Engineering justification of the ranges

| Range | Physically meaningful because | Flow regime | Property validity (screening, anchored) | Structural validity | Geometry / licence |
|---|---|---|---|---|---|
| V ±10 % | a realistic operating band of the coolant supply. The low end is **set by the frozen air table**: −15 % gives near-wall air of 595 K (marginal) and −20 % gives 611 K (invalid). ±10 % keeps 20 K of margin | Re_out ≥ 22,600, fully turbulent; Mach ≤ 0.09; Δp ≤ 0.5 % of p_op | near-wall air 580 K (V01); solid 541.6–586.9 K | LC2 utilisation ≤ 0.64 (elastic); strain 0.39 % | same geometry; y⁺_max est. 0.53–0.64 ≤ 1 |
| q″ ±10 % | a heater-power / heating-load band. **The high end is set by the air table**: +12.5 % gives 591 K (marginal) and +18.75 % gives 608 K (invalid). 12,000 W/m² was already rejected in D-015 | Re unchanged at the inlet; ±1.4 % at the outlet | near-wall air 527.5–583.4 K; solid 533.9–590.7 K; solid minimum 409.8 K is inside the α(T) table | LC2 utilisation 0.51–0.65 | same geometry and mesh |
| t 8–12 mm, Q constant | a realistic design change of a thick-walled duct (D_o/D_i 1.8–2.2; D/t 4.5–3.7, still compact, no local or shell buckling). **The high end is set by the Student licence**: t = 12 mm at the baseline 2 mm radial element gives 127,080 nodes; t = 14 mm would need 145,908. The low end is symmetric | unchanged (D_i fixed, same bore heat flux) | temperatures change by ≤ 1 K | LC2 σ unchanged; end force −26 / +28 % | new CAD, CFD mesh and FE mesh (rule M-1); 89,424 and 127,080 nodes; CFD 155,520 and 168,480 cells |

**Why the operating ranges stop at ±10 %.** The limit is the frozen air property table (250–600 K), and the brief forbids unsupported extrapolation. Extending the table would change the frozen CFD material definition. That is not done in 9B.

**Signal against noise.** The ±10 % perturbations move the quantities of interest far above the known numerical uncertainties:

| Quantity | Change under the perturbations (screening) | Known uncertainty |
|---|---|---|
| Solid T_max | 21–29 K | CFD mesh −5 / +2 K |
| Δp | 14–15 % | about 1 % |
| λ₁ | 10–16 % | structural mesh 10⁻⁵ |
| LC2 stress | 8–12 % | structural mesh 10⁻⁴; CFD mesh −1.7 / +0.5 % |

## 4. Support scenarios (Question B, at P00 only)

| Case | Definition | Status | λ₁ |
|---|---|---|---|
| **S1_LC2_CURRENT** | both end faces U_z = 0 (rotation held, sway free) + 3 mid-span hoop nodes: guided column, K = 1 | solved (8A) | **1.108** |
| **S2_LC2_LATERALLY_GUIDED** | both end faces U_z = U_θ = 0 (clamped, no sway), K = 0.5 | solved (8A, "LC2NS") | **4.300** |
| **S3_LC2_INTERMEDIATE** | inlet face clamped (U_z = U_θ = 0); outlet pinned by a **deformable** remote point (U_x = U_y = U_z = 0, rotations free), K = 0.699 | proposed | about 2.2 (hand 2.22–2.29) |

**No support stiffness is invented.** Instead, beam-column theory calibrated to the solved FE gives the *required* relative lateral stiffness between the ends:

| Target λ₁ | Required stiffness |
|---|---|
| 1.5 | about 0.45 kN/mm |
| 1.73 (first-yield factor) | about 0.71 kN/mm |
| 4.30 (full no-sway) | about 3.9 kN/mm |

This is a design requirement for T-034, not a simulated support.

**The support alone changes the conclusion.**

- S1: elastic bifurcation (1.108) comes **before** first yield (≈ 1.73), so stability governs.
- S2 and S3: the bifurcation lies above first yield, so yield or inelastic behaviour governs (Johnson 1.58 / 1.41, conventional).
- S1 is also **not** a lower bound. It assumes perfectly rotation-fixed flanges; a rotation-free end with sway gives K = 2 and λ ≈ 0.28 (conceptual, hand only).

## 5. Number of CFD cases

| Group | Cases | Runs |
|---|---|---|
| Reference | P00_BASELINE (solved 5B, reused) | 0 |
| Pipeline control | C00_PIPELINE_CHECK | 1 |
| Velocity | V01_LOW, V03_HIGH (V02 = P00) | 2 |
| Heat flux | Q01_LOW, Q03_HIGH (Q02 = P00) | 2 |
| Thickness | T01_THIN, T03_THICK (T02 = P00) | 2 |
| Mesh adequacy | M03_T03_CFD_SOLID18 | 1 |
| **Total new Fluent runs** | | **8** |

## 6. Number of Mechanical cases

| Group | Cases | Analyses |
|---|---|---|
| Pipeline control | C00 (LC1, LC2, BK-S1) | 3 |
| Design cases | V01, V03, Q01, Q03, T01, T03 × (LC1, LC2, BK-S1) | 18 |
| Mesh adequacy | M01_T01_STRUCT_NR5, M02_T03_STRUCT_NR5 × (LC1, LC2, BK-S1) | 6 |
| Support | S3_LC2_INTERMEDIATE (LC2 static + BK) | 2 |
| Support (reuse, no run) | S1, S2 from 8A | 0 |
| Method benchmark | B03_S3_TOY_BENCH (MAPDL toy tube, not a project result) | 1 |
| **Total** | | **29 Mechanical analyses + 1 MAPDL benchmark** |

**The pressure-included LC2P is not repeated.** Its effect was ≤ 1.3 × 10⁻⁷ on every mesh (8B). The maximum pressure rises only about 15 % at V03 (screening), so it stays negligible.

## 7. Mesh strategy

| Rule | Summary |
|---|---|
| M-1 geometry change | Rebuild CAD, CFD mesh and FE mesh. CFD: same fluid mesh; solid first layer 0.5 mm, growth ≤ 1.147, giving 9 layers at t = 8 and 12 layers at t = 12. FE: 36 × nr × 130, bias 4, **radial element 2.0 mm** (nr = 4 / 6). Adequacy at both extremes: M01 (refine 4 → 5), M02 (coarsen 6 → 5; refinement exceeds the licence), M03 (CFD solid 12 → 18 layers) |
| M-2 operating change | Reuse the medium CFD mesh and FE mesh B, provided the y⁺ and property rules hold. Re-map the temperature with the unchanged 7A mesh-based procedure; mapping check per case |
| M-3 licence | FE ≤ 128,000 nodes. T03 is at 127,080 (99.3 %), the same topology already solved in 8B; no extra nodes are allowed in T03 |
| M-4 supports | mesh B unchanged; S3 adds one pilot node |
| y⁺ | measured y⁺_max ≤ 1.0 and mean ≤ 0.5. Pre-run estimates: V01 0.53, V03 0.64, all others 0.585. Re-mesh the inflation layer if the estimate is > 1 or the measured value is > 1 |
| Frozen-physics gate | Every CFD case: a full settings-tree diff against the medium baseline case must show **only** the intended change (inlet velocity + turbulence intensity; or heat flux; or mesh + heat flux for T). Every FE case: the 8B-type pre-solve gate. Material identical to 7B; constraints re-located; mapping complete; sparse solver |

## 8. Expected physical trends (screening; to be tested by the runs)

| Output | V −10 % / +10 % | q″ −10 % / +10 % | t 8 / 12 mm (Q constant) |
|---|---|---|---|
| ṁ | −10 / +10 % | 0 | 0 |
| Re_in | 26,961 / 32,952 | 29,957 | 29,957 |
| Δp | −14 / +15 % | −4 / +4 % (thermal acceleration) | 0 |
| mean h | −9 / +9 % | +2 / −2 % | 0 |
| T_out | +7.6 / −6.2 K | −6.9 / +6.9 K | 0 |
| Q | 0 | −10 / +10 % | 0 (by definition) |
| Solid T_max | +25 / −21 K | −28 / +29 K | −1 / +1 K |
| LC1 ΔL | +11 / −9 % | −12 / +13 % | ±0.2 % |
| LC1 max VM | −4 / +2 % | −7 / +6 % | −17 / +16 % |
| LC2 \|mean axial stress\| | +10 / −8 % | −12 / +12 % | ±0.2 % |
| LC2 peak VM / utilisation | +10 / −8 %; 0.64 / 0.53 | −12 / +12 %; 0.51 / 0.65 | ±0.2 %; 0.58 |
| LC2 end force | +10 / −8 % | −12 / +12 % | −26 / +28 % |
| λ₁ (S1) | 1.00 / 1.22 (−10 / +10 %) | 1.26 / 0.98 (+14 / −11.5 %) | 0.94 / 1.29 (−15 / +16.5 %) |
| P_cr (S1) | ≈ 0 | ≈ 0 | −37 / +50 % |
| y⁺_max | 0.53 / 0.64 | ≈ 0.585 | 0.585 |

**Structural reading of the trends.**

- **V and q″ act on stress and stability almost only through the temperature level.** λ₁ scales with 1/N and P_cr hardly changes.
- **Thickness leaves the stress and temperature almost unchanged** but moves λ₁ and P_cr strongly through the section.
- **Three proposed cases have screening λ₁(S1) ≤ 1:** V01 ≈ 1.00, Q03 ≈ 0.98 and T01 ≈ 0.94.
  - For the idealised S1 support, the ideal straight column would bifurcate before these LC2 states are reached.
  - Their static LC2 results will be labelled as ideal pre-buckling states.
- **In every proposed case, stability stays more limiting than first yield for S1** (first-yield factor ≥ 1.54).

**Interpreting λ₁ in every document.** Each document will keep these apart:

1. the **ideal linear eigenvalue** (straight, nominal geometry, elastic, perfect supports);
2. **real-world stability**: the load is displacement-controlled, so exceeding the critical state would appear as progressive bowing, not sudden collapse;
3. **end-restraint uncertainty** (S1–S3);
4. **geometric imperfections** and residual stress (not modelled; T-035);
5. **nonlinear behaviour**: plasticity, large deflection and tangent modulus (not modelled; F-044, F-045, T-036).

No λ₁ > 1 will be called "safe", and no λ₁ < 1 will be called "collapse".

## 9. Constraints and limitations

1. **One-factor-at-a-time.** Interactions are not measured.
   - The screening puts the V × q″ interaction at 8–11 % of the main effects (for example, near-wall temperature ±2–3 K on ±25 K effects; λ₁ ±0.011 on ±0.12).
   - It follows the known multiplicative physics (temperature rise ≈ q″ × a velocity factor).
   - The adverse corner (V −10 %, q″ +10 %) would exceed the air table (611 K), so a full factorial is not admissible within the frozen model.
2. **The ranges are narrow (±10 %)** because of the frozen air table. They show local sensitivities, not a design envelope.
3. **Support scenarios are evaluated at P00 only.** For design cases, λ₁ under S2 and S3 scales like S1 (the same E·I / N ratio). That is a screening statement, not a run.
4. **The screening model is approximate.** The 1-D model over-predicts the baseline T_max by 19 K. The anchoring removes that offset for the ratios, not every non-linearity. CFD and FE decide.
5. **Known biases carried:** LC1 surface stress about −2 % (F-046); ν assumed (T-014); linear-elastic material; no imperfections (F-044); no inelastic data (F-045).
6. **Constant-Q thickness definition.** A different installation (fixed q″) would add a ∓10 % heat-input effect. The screening shows its size (`cand_Tq_*`).
7. **The S3 remote-point pin is itself an idealisation.** It is validated against Euler on the toy tube (B03) before use.

## 10. Computational practicality

| Item | Basis (measured in earlier sections) | Estimate |
|---|---|---|
| Fluent run, medium mesh (159,840 cells) | P00: 12 min 58 s incl. audits and exports (700 iterations, 4 cores) | 8 runs × about 15–20 min incl. post and mapping export ≈ **2.5 h** (T03 168,480 cells, M03 ≈ 194,000 cells) |
| Mechanical set (LC1 + LC2 + BK), 108k–127k nodes | 8B: B 54 / 83 / 208 s; FR (127k) 86 / 92 / 266 s; plus gate, extraction and images | 9 sets × about 8–10 min ≈ **1.4 h**; S3 + benchmark about 0.3 h |
| New geometry / meshes / projects for T01, T03 | scripted CAD, Python CFD mesh generator, 7A mapping pipeline | about **1 h** incl. gates |
| **Total device time** | | **about 5 h**, in 4–5 separate batches |
| RAM (15.7 GB) | the fine CFD mesh (500,580 cells) and 127k-node FE both ran in 6B / 8B | adequate; the sparse solver may run out-of-core (performance only) |
| Student licence | Fluent: largest parametric mesh about 194,000 cells, far below the 500,580 cells already solved. Mechanical: 127,080 nodes (T03) = 99.3 % of 128,000, proven solvable in 8B | practical; T03 has no node headroom |
| Disk | about 130 MB per FE set, about 60 MB per CFD case with exports | about 2 GB |

**Execution order in 9B (recommended).**

1. C00 (proves the pipeline).
2. V01, V03, Q01, Q03 (same meshes).
3. T01, T03 with M01, M02, M03 (new geometry and meshes).
4. B03, then S3.
5. Post-processing against P00.

**Stop rule.** Any case failing its gate, convergence, property-table or y⁺ rule stops the batch. The case is repaired, archived and re-run, never reported.
