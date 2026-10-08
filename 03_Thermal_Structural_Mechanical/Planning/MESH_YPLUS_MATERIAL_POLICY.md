# Section 9A: mesh, y⁺ and material-validity policy for the parametric cases

> **RE-ANALYSIS 2026.** These rules are fixed **before** any parametric run. The estimates quoted are screening values (`Analytical_Screening/`), not results. Every rule has a check that runs in Section 9B.

## 1. When must the mesh be rebuilt?

| Rule | Trigger | Action | Checks required |
|---|---|---|---|
| **M-1** | **Any geometry change** (D_i, D_o / t, L) | Rebuild the CAD, the CFD mesh and the structural mesh, and regenerate the temperature-mapping source (7A mesh-based procedure). **CFD mesh:** same generator (`05_Meshing/make_mesh.py`) and same fluid settings (NC 12, NR 24, NZ 90, first fluid cell 12.2 µm). Solid layers follow the solid rule: first layer 0.5 mm, growth ≤ 1.147 (baseline), smallest layer count that meets it. That gives t = 8 mm → 9 layers (g 1.139) and t = 12 mm → 12 layers (g 1.119). **Structural mesh:** baseline controls (36 circumferential, 130 axial, bias 4) with the **radial element size held at 2.0 mm** (t = 8 → 4 elements, t = 12 → 6 elements) | Mesh adequacy at **both extremes**: structural M01 (t = 8, radial refinement 4 → 5) and M02 (t = 12, coarsening 6 → 5, because refinement would exceed 128,000 nodes); CFD M03 (t = 12, solid layers 12 → 18). The 8B quality gates apply to every new mesh: quadratic hexes, 0 inverted elements, conformal, aspect ratio < 20 |
| **M-2** | **Operating change with unchanged geometry** (V, q″) | **Reuse** the medium CFD mesh and structural mesh B, **only if** (a) the y⁺ rule (§2) holds, (b) the property-table rule (§3) holds and (c) the flow stays turbulent and attached | y⁺ estimate before the run and measured y⁺ after it; re-map the temperature field with the unchanged 7A settings and check the mapping per case (as in 8B) |
| **M-3** | The structural node count would exceed 128,000 | Not allowed. Coarsen circumferentially and axially first, keeping the 2 mm radial size; document the change. T03 (127,080 nodes, 99.3 %) is permitted: the same topology solved in 8B (FR). **No extra nodes** (remote points, contact) may be added to T03 | node formula nc[(nr+1)(na+1)·2 + nr(na+1) + (nr+1)na] checked in the pre-solve gate |
| **M-4** | Support-scenario change (S1 / S2 / S3) | No re-mesh. Mesh B is kept. S3 adds one remote pilot node | the constraint set is read back from the written solver input (`SUPPORT_SCENARIOS.md` §6) |
| **M-5** | Any mesh change | Log the node/cell counts, element sizes and quality metrics in the case folder | — |

**Why operating changes may reuse the meshes.** 8B showed that the LC2 and buckling results on mesh B change by ≤ 10⁻⁴ under refinement. The parametric temperature fields are smooth rescalings of the baseline field (±5 % in temperature rise), so the same resolution applies.

**The one exception.** The known LC1 surface-stress bias of about −2 % (F-046) also applies to every case and is carried as a known bias.

## 2. y⁺ policy (wall-resolved k-ω SST, `correlation` wall treatment)

**Keeping the first-cell height does not keep y⁺.**

- y⁺ = u_τ y₁ / ν, with u_τ = V √(f/8).
- For fixed y₁, y⁺ ∝ V √f / ν ≈ V^0.9 (f falls slowly with Re).
- Heating raises ν at the wall downstream, which lowers y⁺ there.
- The baseline maximum (0.585) is at the inlet, where the boundary layer is thinnest and the air is at 300 K.

| Item | Requirement |
|---|---|
| Acceptance (measured in Fluent, conjugate interface) | **y⁺_max ≤ 1.0** and **area-weighted mean ≤ 0.5**, i.e. 100 % of the wall at y⁺ ≤ 1. Same as the baseline requirement (NR-01) |
| Pre-run estimate | y⁺_max,case = 0.585 × (u_τ/ν)_case / (u_τ/ν)_P00, at inlet conditions, with Petukhov f |
| Reuse threshold | reuse the medium mesh if the estimate is ≤ 0.8 (20 % margin); run and verify if 0.8–1.0; **re-mesh** the inflation layer (y₁ scaled by 0.8 / estimate) if > 1.0 |
| Estimates for the proposed cases | V01 0.533 · V03 0.636 · Q01 / Q03 / T01 / T03 0.585 (same inlet flow; downstream heating lowers y⁺ further). **All reuse the medium mesh** |
| Failure handling | a case whose measured y⁺_max exceeds 1.0 is **invalid**. It is re-meshed and re-run; it is not reported with a wall-function caveat |

## 3. Material and property validity

| Property table (frozen) | Valid range | Governing quantity | Worst proposed case (screening) | Status |
|---|---|---|---|---|
| Air c_p, μ, k, Pr (Incropera A.4, piecewise-linear in Fluent) | 250–600 K | near-wall air = interface temperature (P00: 555.27 K; fluid-cell maximum 553.41 K) | Q03: 583.4 K; V01: 580.3 K | inside, with ≥ 16 K margin |
| Inconel k, c_p (VDM 4127, Fluent) | 293–673 K | solid maximum (P00 562.6 K) and minimum (424.0 K) | Q03 max 590.7 K; Q01 min 409.8 K | inside |
| Inconel E(T), S_y(T) (VDM 4127, Mechanical and utilisation) | 20–400 °C (293–673 K) | as above | as above | inside |
| Inconel α(T), mean from 21 °C (Mechanical, MPAMOD) | 93–538 °C (366–811 K) | solid minimum | Q01 min 409.8 K (136.7 °C) | inside (no extrapolation below the table) |
| Poisson's ratio | constant 0.294 [ASSUMED] | — | — | unchanged (T-014) |

**Acceptance rules applied in 9B to every CFD case.**

1. No fluid or solid temperature leaves its property table at **any iteration**. The monitored minima and maxima are the same ones used in 5B.
2. The staged start of D-028 is used unchanged: flow and k-ω for 150 iterations with energy off, then energy on. The start-up overshoot of F-022 (761 K in an unstaged run) must not reappear at the higher heat flux.
3. A case violating either rule is rejected. It is not reported with extrapolated properties.

**Rejected operating points (screening).**

| Operating point | Why rejected |
|---|---|
| V ≤ −20 % | near-wall air ≥ 611 K (INVALID) |
| V −15 % | 595 K (MARGINAL) |
| q″ ≥ +18.75 % (≥ 9,500 W/m²) | ≥ 608 K (INVALID) |
| q″ +12.5 % | 591 K (MARGINAL) |
| q″ = 12,000 W/m² | also exceeds the Inconel tables (708 K) |
| Factorial corner V −10 % with q″ +10 % | 611 K (INVALID) |

## 4. Structural validity

- **Linear-elastic model.** LC2 utilisation stays ≤ 0.65 in every proposed case (screening), so there is no yielding in the static cases.
- **Small strain.** Mean thermal strain ≤ 0.40 %; flow-area change ≤ 0.7 %, so one-way coupling (D-013) remains valid.
- **Buckling results.** They are reported as ideal linear eigenvalues, with the interpretation rules in `PARAMETRIC_PLAN.md` §8.
- **Where λ₁(S1) < 1** (screening: V01 ≈ 1.00, Q03 ≈ 0.98, T01 ≈ 0.94), the static LC2 state is labelled "beyond the ideal bifurcation of the S1 idealisation".
