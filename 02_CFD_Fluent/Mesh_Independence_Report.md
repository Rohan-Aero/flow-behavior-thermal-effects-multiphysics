# Mesh-Independence Study — Section 6B (coarse / medium / fine)

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems
**Date:** 2026-09-24 · ANSYS Fluent 2026 R1 (v261) · analysis script `Scripts/mesh_study.py` (ANSYS-bundled CPython 3.10)
**RE-ANALYSIS 2026 — newly generated results, not recovered originals. No measured data exists or is used.**

> **Bottom line.** All three meshes are converged, wall-resolved (y⁺ ≤ 0.66) and carry identical
> physics. Mass flow, heat input and outlet temperature change between meshes **only because the
> inscribed polygon changes**; corrected for that, they agree to round-off. The quantities that
> depend on resolution (Δp, wall and solid temperatures, Nu, f) converge monotonically at an
> apparent order of about 1.2–1.6 (Δp about 1.05, and only once its geometric part is removed), so
> they are **approximately convergent (status B), not proven
> mesh-independent**. The fine-mesh uncertainty is about ±3.4 K on the peak solid temperature,
> ±0.03 K on the through-wall ΔT, about ±1 % on Δp and about ±2 % on Nu and f. The **medium mesh is kept for
> downstream work**: it runs 4.4 K hotter than the extrapolated peak (conservative for thermal
> stress), and it costs a third of the fine mesh's run time. The fine mesh stays as the
> verification reference. F-029 is mainly a gas-heating effect, not a mesh effect.

Companion files: `MESH_INDEPENDENCE_RESULTS.csv` (master table, machine-readable) ·
`MESH_INDEPENDENCE_AUDIT.md` (how the study was done and checked) ·
`Geometry_Correction/GEOMETRY_CORRECTION.md` · `Uncertainty/UNCERTAINTY.md` ·
`Comparison_Tables/MASTER_TABLE.md`.

---

## 1. Purpose and scope

NR-02 requires evidence that the CFD answers used downstream do not depend materially on the
mesh. Three structured hexahedral meshes of the same geometry were solved with identical physics
(Sections 5B, 6A and 6B). This report:

1. separates what the meshes change geometrically from what they change numerically;
2. measures convergence with several metrics, not one;
3. investigates F-029 (friction factor) and the temperature gap to Section 2;
4. selects the mesh for the structural phase and states the uncertainty that goes with it.

Coarse and medium were **not rerun**. Their saved results were read only; their SHA-256 hashes
are identical before and after this section (`MESH_INDEPENDENCE_AUDIT.md` §5).

## 2. The three meshes

| | Coarse | Medium (5B baseline) | Fine |
|---|---|---|---|
| Cells (fluid + solid) | **51,840** (38,400 + 13,440) | **159,840** (116,640 + 43,200) | **500,580** (354,780 + 145,800) |
| Polygon sides N (circumferential cells) | 32 | 48 | 72 |
| O-grid core NC × NC | 8 × 8 | 12 × 12 | 18 × 18 |
| Fluid radial / solid radial cells | 18 / 7 | 24 / 10 | 32 / 15 |
| Axial slabs (Δz) | 60 (10.0 mm) | 90 (6.67 mm) | 135 (4.44 mm) |
| **First fluid layer** | **12.2 µm** | **12.2 µm** | **12.2 µm** |
| Min orthogonal quality / max aspect ratio | 0.448 / 974 | 0.446 / 654 | 0.314 / 438 |
| Solve wall clock (700 iterations, 4 cores) | 9.0 min | 13.0 min | 43.9 min |
| Case + data files | 5.8 MB | 13.5 MB | 55.6 MB |

**Refinement ratios.** The effective ratios from total cell count are r₃₂ = (159,840/51,840)^⅓ =
**1.4555** and r₂₁ = (500,580/159,840)^⅓ = **1.4631**, above the 1.3 recommended for Richardson
extrapolation. The refinement is **not** geometrically similar in every direction:

| Direction | Coarse → medium | Medium → fine |
|---|---|---|
| Circumferential (N) | 1.50 | 1.50 |
| Axial (slabs) | 1.50 | 1.50 |
| Fluid radial cells | 1.33 | 1.33 |
| Solid radial cells | 1.43 | 1.50 |
| **Wall-normal first-layer height** | **1.00 (held at 12.2 µm)** | **1.00** |

The first layer was held constant on purpose, so that every mesh is wall-resolved (y⁺ < 1). The
consequence is that the error from the first-cell height is **not refined**. The extrapolated values
below are the limit of *this* refinement path, not of a mesh refined in every direction (§6.4).

## 3. Same physics on every mesh

- Each additional mesh was placed under the medium case's settings with Fluent's own
  `mesh.replace`; the full settings tree differs from the medium case in **0** entries (D-032).
- Setup read back at three stages: coarse 130/130, fine 132/132. Every common item equals the
  medium run's own audit; the fine run writes the comparison machine-readably
  (`06_Fluent_CFD/Mesh_Independence/Fine/Audit/setup_comparison_vs_medium.csv`: 177 / 177 match).
- Fresh standard initialisation on every mesh; the medium data was never read.
- Same staged startup, one switch to second order at iteration 301, same convergence criteria.
  All three converged at 600 and were confirmed at 700.
- Same post-processing code; only the mesh constants differ.

## 4. Raw three-mesh results (identical definitions)

Source: `Comparison_Tables/three_mesh_raw_table.csv`. Temperature changes are also given as a
percentage of the rise above the 300 K inlet, because a percentage of the absolute temperature
flatters them by a factor of about two.

| Quantity | Coarse | Medium | Fine | C→M | M→F | C→F |
|---|---|---|---|---|---|---|
| Cells | 51,840 | 159,840 | 500,580 | ×3.08 | ×3.13 | ×9.66 |
| ṁ [g/s] | 8.6312 | 8.6622 | 8.6759 | +0.0309 (+0.36 %) | +0.0138 (+0.16 %) | +0.0447 (+0.52 %) |
| Δp [Pa] | 437.09 | 438.13 | 439.12 | +1.03 (+0.24 %) | +0.99 (+0.23 %) | +2.03 (+0.46 %) |
| T_out [K] | 369.115 | 368.932 | 368.851 | −0.183 (−0.26 % of rise) | −0.081 (−0.12 %) | −0.264 (−0.38 %) |
| Q [W] | 602.217 | 602.755 | 602.994 | +0.538 (+0.09 %) | +0.239 (+0.04 %) | +0.777 (+0.13 %) |
| T_max, solid [K] | 565.40 | 562.58 | 560.83 | −2.83 (−1.07 % of rise) | −1.75 (−0.66 %) | −4.57 (−1.72 %) |
| ΔT_wall, mid-span z = 300 mm [K] | 7.554 | 7.581 | 7.597 | +0.027 (+0.35 %) | +0.016 (+0.21 %) | +0.043 (+0.57 %) |
| Nu_fd (x/D 18–29) | 53.38 | 54.17 | 54.66 | +0.79 (+1.48 %) | +0.49 (+0.91 %) | +1.28 (+2.40 %) |
| f_fd (x/D 18–29) | 0.02134 | 0.02163 | 0.02181 | +0.00029 (+1.35 %) | +0.00018 (+0.85 %) | +0.00047 (+2.20 %) |
| y⁺ area mean | 0.238 | 0.241 | 0.243 | +1.19 % | +0.71 % | +1.91 % |
| y⁺ max | 0.522 | 0.585 | 0.653 | +12.1 % | +11.7 % | +25.2 % |

Supporting quantities, same definitions: peak inner wall 558.12 / 555.27 / 553.50 K; mid-span
inner wall 534.24 / 531.67 / 530.17 K; volume-mean solid 527.66 / 525.48 / 524.18 K; minimum solid
425.41 / 423.97 / 423.09 K; mid-span h 79.69 / 80.69 / 81.29 W/m²K; ΔT_wall at z = 570 mm
7.334 / 7.361 / 7.378 K; mass imbalance 1.2e-13 / 7.0e-13 / 3.9e-12 %; energy imbalance
2.0e-11 / 3.1e-11 / 6.2e-11 %.

## 5. Geometry (polygon faceting) — what is *not* mesh error

Full derivation: `Geometry_Correction/GEOMETRY_CORRECTION.md`; numbers:
`faceting_ratios.csv`, `geometry_corrections.csv`.

Every mesh represents the Ø20/Ø40 circles as **inscribed regular N-gons**, so refining the mesh
also changes the geometry:

| Exact ratio to the circle | N = 32 | N = 48 | N = 72 |
|---|---|---|---|
| Flow area (N/2π)·sin(2π/N) | 0.993587 | 0.997147 | 0.998731 |
| Perimeter and heated area sin(π/N)/(π/N) | 0.998394 | 0.999286 | 0.999683 |
| D_h / D = cos(π/N) | 0.995185 | 0.997859 | 0.999048 |

**Exact consequences (fixed by conservation):**
- **ṁ = 23.5 m/s × ρ × polygon area.** ṁ divided by the planar ratio is **8.68694 g/s on all three
  meshes** (differences ~10⁻¹² %). The whole ṁ change is geometry.
- **Q = 8000 W/m² × polygon outer area.** Q divided by the lateral ratio is **603.186 W on all
  three**. The whole Q change is geometry.
- **T_out** follows from Q/ṁ, which the polygon raises by lateral/planar (+0.48 / +0.21 / +0.10 %).
  Removing that with the solver's own cₚ(T) gives **368.783 / 368.785 / 368.786 K**: the raw
  −0.183 and −0.081 K are **101 % geometric**.
- The bulk temperature at mid-span and at the exit shifts the same way; this exact bulk shift is
  removed from T_max and the wall temperatures (−0.33 / −0.15 / −0.07 K at the exit). It is only
  **7 % and 5 %** of the T_max changes, so **T_max changes are resolution, not geometry**.

**Estimated consequences (correlation scalings; shown, never used as headline values):**
- **Δp:** the 1-D acceleration term depends on T_out (exact part: −0.40 then −0.18 Pa), wall friction
  on 4τ_w/D_h with τ_w ∝ D_h^−0.2 at fixed G (estimate), and friction on mean density (estimate).
  The estimated geometric part is −1.24 Pa (C→M) and −0.55 Pa (M→F), **opposite** in sign to the
  raw changes. The polygon lowers Δp as N rises while resolution raises it.
- **Through-wall ΔT:** conduction across a polygonal annulus scales roughly with the apothem,
  cos(π/N). That estimate is +0.020 and +0.009 K, about 76 % and 56 % of the raw changes. The raw
  ΔT changes cannot therefore be attributed to resolution alone.
- **Nu, h, f:** the D_h^−0.2 effect is −0.05 % and −0.02 %; negligible.
- **Re (D = 20 mm):** G = ṁ/A is unchanged by faceting; the outlet Re moves only through
  μ(T_out), i.e. geometrically.

**These differences are not called mesh error anywhere in this study.** A reassuring by-product:
Richardson extrapolation of the *raw* ṁ, Q and T_out, which converge at the polygon's own second
order (apparent p = 2.18–2.20), returns **8.68657 g/s, 603.179 W and 368.790 K**, within 0.004 %,
0.001 % and 0.004 K of the exact circle values. The extrapolation procedure recovers a known answer.

## 6. Convergence — method and metrics

### 6.1 Metrics used for every quantity (`Uncertainty/gci_analysis.csv`)

1. absolute change C→M and M→F;
2. percentage change (for temperatures, also as % of the rise above 300 K);
3. convergence ratio R = ε₂₁/ε₃₂ (0 < R < 1 monotonic convergence; R < 0 oscillatory; R ≥ 1 not converging);
4. apparent order p, by fixed-point iteration with the actual r₂₁ and r₃₂ (Celik et al. 2008, ASME J. Fluids Eng. 130, 078001);
5. Richardson-extrapolated value, only where p is credible (0.5–4);
6. GCI on the fine and medium meshes (Fs = 1.25; p capped at 2; Fs = 3 with p = 2 where p is not credible);
7. the geometric share of the change (§5).

### 6.2 Status rules

| Status | Rule |
|---|---|
| **A** clearly convergent | monotonic, R < 0.8, credible p, M→F < 0.5 % (of rise for temperatures), **and** no estimated geometric share ≥ 50 % and no estimated correction in the quantity itself |
| **B** approximately convergent | monotonic and M→F < 1 %, but one of the A conditions fails |
| **C** still changing materially | monotonic with M→F ≥ 1 %, or not converging with M→F ≥ 0.5 % |
| **D** affected by geometry | an **exact** geometric share ≥ 50 % of the C→M change (and outlet Re, which moves only through μ(T_out)) |
| **E** inconclusive | not a convergence metric, or not converging with a small change |

A small percentage change is **not** enough for A.

### 6.3 Results

| Quantity | R | p | Extrapolated | GCI fine | GCI medium | Status |
|---|---|---|---|---|---|---|
| ṁ, Q, T_out (raw) | 0.44 | 2.2 | → circle values (§5) | not quoted | not quoted | **D** |
| T_out, geometry-corrected | 0.55 | 1.61 | 368.787 K | 0.002 K | 0.003 K | **A** |
| Δp, raw | 0.96 | 0.13 (not credible) | — | 2.6 Pa (0.60 %, Fs 3) | 2.8 Pa | **B** |
| Δp, geometry-adjusted (estimate) | 0.68 | 1.05 | 441.8 Pa | 3.9 Pa (0.89 %) | 5.9 Pa (1.34 %) | **B** |
| — wall-shear term | 0.76 | 0.75 | 248.5 Pa | 5.3 Pa (2.2 %) | 7.1 Pa | B |
| T_max (raw) | 0.62 | 1.31 | 558.13 K | 3.37 K | 5.55 K | **B** |
| T_max, bulk-corrected | 0.63 | 1.26 | 558.06 K | 3.38 K (1.30 % of rise) | 5.46 K | **B** |
| Peak inner wall | 0.62 | 1.31 | 550.78 K | 3.40 K | 5.61 K | B |
| Volume-mean solid T | 0.60 | 1.40 | 522.34 K | 2.31 K | 3.93 K | B |
| **ΔT_wall, mid-span** | 0.60 | 1.37 | 7.620 K | 0.029 K (0.39 %) | 0.049 K | **B** |
| ΔT_wall, z = 570 mm | 0.65 | 1.18 | 7.407 K | 0.037 K | 0.058 K | B |
| h, mid-span | 0.60 | 1.40 | 82.14 W/m²K | 1.31 % | 2.24 % | B |
| **Nu_fd** | 0.62 | 1.30 | 55.43 | 1.76 % | 2.91 % | **B** |
| **f_fd** | 0.64 | 1.23 | 0.02212 | 1.77 % | 2.84 % | **B** |
| y⁺ mean / min | 0.60 | 1.37 | 0.245 / 0.210 | 1.3 % / 0.7 % | — | B / A |
| y⁺ max | 1.08 | — | — | — | — | **E** |
| Mass / energy imbalance | — | — | — | — | — | A (round-off) |

No quantity is **C**. The only one changing by ≥ 1 % between medium and fine is the y⁺ maximum (+12 %, R = 1.08), which is classed **E**: it is a sampling position in the first slab, not a convergence metric (§10).

### 6.4 Why the apparent order is below 2, and what that limits

The schemes are formally second order. The observed order is 1.2–1.6 for the temperatures, Nu and f, 1.05 for the
geometry-adjusted Δp and 0.75 for its wall-shear term; the raw Δp is not in the asymptotic range at all (p = 0.13). The
reasons:
- the refinement ratio differs by direction (1.5 / 1.5 / 1.33), and the first-layer height is not
  refined at all, so error components that shrink at different rates are mixed together;
- the geometry itself changes with N (§5).

**Limitations of the extrapolated values and GCI:**
- they assume monotonic convergence in the asymptotic range with a constant p, from only three points;
- the "asymptotic-range" check GCI₃₂/(r^p·GCI₂₁) ≈ 1.00 is **not** independent evidence, because p is computed from the same three solutions;
- they estimate the limit of this refinement path with a fixed 12.2 µm first layer. Any error tied to the first-cell height is outside them. At y⁺ ≈ 0.24 that part is expected to be small, but it is not measured;
- a GCI is an uncertainty band (≈ 95 % in Roache's sense), not a guaranteed bound.

## 7. Pressure drop

| Term (Pa) | Coarse | Medium | Fine | C→M | M→F |
|---|---|---|---|---|---|
| Wall shear, F_wall/A | 241.02 | 242.87 | 244.28 | +1.85 | +1.41 |
| 1-D acceleration, G²(1/ρ_out − 1/ρ_in) | 149.71 | 149.31 | 149.13 | −0.40 | −0.18 |
| Profile development (momentum-flux shape) | 46.42 | 46.15 | 45.97 | −0.27 | −0.18 |
| **Static Δp, inlet − outlet** | **437.09** | **438.13** | **439.12** | **+1.03** | **+0.99** |

(The momentum balance closes to −0.01 to −0.06 % on each mesh, so the terms do not sum exactly.)

- The **raw Δp** rises by almost the same amount at each step (R = 0.96). Its apparent order
  (0.13) is not credible, so no Richardson value is given for it.
- The reason is two opposing trends. Wall shear rises with resolution (+0.77 %, +0.58 %, the same
  trend as f). The acceleration term falls because T_out falls, which is **geometry** (§5).
- With the geometric part removed (exact acceleration part plus the estimated D_h and density
  parts), the sequence is 434.85 / 437.13 / 438.68 Pa: R = 0.68, p = 1.05, extrapolated
  **441.8 Pa**, GCI_fine 0.89 % (3.9 Pa). This series contains an estimate, so it cannot earn A.
- **Status B.** The fine Δp is about 0.6 % and the medium 0.8 % below the extrapolated
  (circle-referred) value. The mesh uncertainty on Δp is **about 1 % (≈ 4–6 Pa)**.
- The extrapolated 441.8 Pa is within 0.1 % of Section 2's 441.5 Pa. **This is not treated as
  validation**: Section 5B showed that the CFD wall-shear term is 7.7 % below Section 2's friction
  term while its profile-development term is 58 % above Section 2's entry term. The totals agree
  partly by compensation.

## 8. Thermal convergence

**Outlet temperature.** Raw T_out is status **D**: its change is 101 % geometric. Corrected, it
changes by 0.003 K over the three meshes. That is expected, since T_out is fixed by energy
conservation, which every mesh satisfies to 10⁻¹¹ %.

**Peak solid and wall temperatures.** T_max falls 2.83 K and then 1.75 K (R = 0.62, p ≈ 1.3).
Only 7 % and 5 % of those steps are the geometric bulk shift. The rest is the air film:
- fully developed Nu rises +1.48 % and +0.91 %; mid-span h rises +1.26 % and +0.74 %;
- the film carries about 97 % of the thermal resistance (F-010), so a 0.9 % rise in h across the
  ≈ 185 K inner-wall-to-bulk difference at the exit is ≈ 1.7 K, which is the observed −1.75 K.

The extrapolated T_max is **558.1 K**. GCI on the fine mesh is **3.4 K** (1.3 % of the 261 K rise).
The medium mesh is **4.4 K above** the extrapolated value, the coarse 7.3 K. Wall temperatures,
the minimum solid temperature and the volume-mean solid temperature all behave the same way
(p 1.3–1.5). **Status B.**

**Through-wall ΔT at matched location z = 300 mm (mandatory).** 7.554 → 7.581 → 7.597 K
(+0.35 %, +0.21 %; R = 0.60, p = 1.37). Extrapolated 7.620 K, GCI_fine **0.029 K (0.39 %)**. The
medium value is 0.040 K (0.52 %) below the extrapolated one. The metal conduction is therefore
almost mesh-insensitive: the three meshes span 0.043 K. It is rated **B, not A**, because the
polygonal wall is itself slightly thinner across the flats. The apothem estimate puts about ¾ of
the C→M change and about ½ of the M→F change on geometry; after that estimate the residual steps
are +0.006 and +0.007 K, too small to show a clean trend. The same holds at z = 570 mm (7.334 /
7.361 / 7.378 K).

### 8.1 F-027 and the 19 K gap to Section 2

| | Coarse | Medium | Fine | Extrapolated |
|---|---|---|---|---|
| T_max − Section 2 (581.71 K) | −16.3 K | −19.1 K | −20.9 K | −23.6 K |
| Fully developed Nu | 53.38 | 54.17 | 54.66 | 55.43 |
| ΔT_wall at z = 570 mm vs Section 2 (7.285 K) | +0.7 % | +1.0 % | +1.3 % | +1.7 % |
| Volume-mean solid T (Section 2 length-averaged mid-wall: 554.74 K) | 527.66 K | 525.48 K | 524.18 K | 522.34 K |

- **The fine mesh neither moves toward the analytical value nor stays at the medium value. It
  continues the coarse→medium trend away from Section 2, at a decreasing rate.** Refinement raises h,
  and a higher h makes the wall cooler. The 19 K gap is therefore **not a mesh artefact**; if
  anything, the medium mesh understates it by about 4 K.
- The gap sits in the film coefficient. Section 2 used Nu = 49.6 at the exit (Gnielinski with the
  n = 0.5 property correction, D-018). The CFD gives 54–55 in the developed region, which implies
  n ≈ 0.35 (fine) against the assumed 0.5. Section 5B attributed −15.0 K of the 19.1 K to h and
  −4.2 K to axial conduction toward the adiabatic outlet end. Neither is a mesh effect.
- The **through-wall ΔT** agrees with the 1-D analytical value within 2 % on every mesh, and the
  mesh moves it by only 0.6 %. The metal side of the problem is not in question.
- **F-027 proper: corrected in this section.** F-027 described Section 2's 554.7 K as an
  exit-station mid-wall value. The Section 2 profile (`02_Engineering_Calculations/axial_profiles.csv`)
  shows otherwise. It is the **length-averaged mid-wall temperature**: (T_wi + T_wo)/2 averaged
  over 0–600 mm is 554.74 K, while the exit-station value is 578.07 K.
  - The comparable CFD quantity, the length-averaged mid-wall temperature, is 524.60 K on the medium
    mesh (volume mean 525.48 K). The ≈ 30 K difference is therefore **a real model difference, not a
    difference of basis**.
  - At mid-span, Section 2's inner wall is at 550.5 K against the CFD's 531.7 K. That is the film
    coefficient, as for the peak.
  - At the inlet, Section 2's local 1-D model already puts the wall at 529.6 K, whereas the CFD wall
    is at 423 K. The CFD has a thermal entrance region and axial conduction toward the cold end;
    the 1-D model has neither.
  - The mesh moves the volume mean by only 1–2 K per level, so this is not a mesh question either.
  - **Consequence for the structural phase (recorded, not acted on):** Section 2's free growth
    (2.096 mm) and LC2 stress (−657 MPa) both use its 254.7 K mean rise. A CFD-based mean rise is
    ≈ 225.5 K, about 11 % lower. The structural phase must decide the basis explicitly (T-025).

## 9. Friction factor (F-029) — evidence, not assumption

Evidence: the three heated meshes, plus a dedicated **isothermal diagnostic** (same medium case and
mesh with the energy equation off;
`06_Fluent_CFD/Diagnostics/F029_Isothermal/F029_ISOTHERMAL_DIAGNOSTIC.md`), and Figure MI11.

| Evidence | Value |
|---|---|
| f_fd (window x/D 18–29), coarse / medium / fine | 0.02134 / 0.02163 / 0.02181; extrapolated 0.02212 (GCI_fine 1.8 %) |
| vs Section 2 (0.02413) | −11.6 / −10.4 / −9.6 %; extrapolated −8.4 % |
| vs Petukhov at the heated window Re (0.02440), fine | −10.6 % |
| vs Petukhov × (T_w/T_b)^−0.1 (0.02337), fine / extrapolated | −6.7 % / −5.3 % |
| **Isothermal CFD, medium mesh**, window | **0.02304**: −2.6 % vs Petukhov (0.02365), −4.1 % vs Blasius (Re 29 958) |
| Isothermal local f, x/D 18 → 29 | 0.02274 → 0.02340 (+2.9 % at constant Re) |
| **Heating effect in the CFD** (heated / isothermal, Re change removed) | **× 0.910 (−9.0 %)**; (T_w/T_b)^−0.1 predicts × 0.957 (−4.3 %); implied exponent m ≈ −0.22 |

Each candidate cause, judged on that evidence:

1. **Mesh resolution: real, but a minor part.** f rises 1.35 % and then 0.85 % with refinement.
   The medium value is 2.2 % below its extrapolated limit and the fine 1.4 %. Refinement recovers
   about 2 of the 10.4 points; the extrapolated f is still 8.4 % below Section 2.
2. **Turbulence model: no material deficit in isothermal flow.** SST on the medium mesh is 2.6 %
   below Petukhov, and about 0.4 % below after the mesh factor. Under heating, however, the CFD's
   friction falls about twice as much as the standard (T_w/T_b)^−0.1 correction. That residual of
   about 5 points is either SST's response to strong near-wall property variation or a limitation
   of the correlation's exponent. **It cannot be settled without measurements** and is recorded as
   a model uncertainty.
3. **Polygon geometry: negligible.** The D_h effect on f is +0.10 / +0.04 / +0.02 % and G is unchanged.
4. **Entrance / developing flow: contributes 1–2 points.** At constant Re the isothermal f still
   rises 2.9 % across x/D 18–29 and is still rising at the outlet. The window mean is 1.6 % below
   its own x/D 29 value. The window is not fully developed, and Section 2's 17.9 D entry length
   was optimistic for the wall shear. This is part of the isothermal factor above.
5. **Correlation limits: the main issue.** Section 2's 0.02413 is a duct-averaged, constant-property
   Petukhov value with no heating correction, applied at T_w/T_b ≈ 1.55. At the window's lower Re
   the same correlation gives 0.02440 (+1.1 %). Petukhov and Blasius differ by 1.6 % at this Re.

**Exact multiplicative decomposition of the medium-mesh gap** (`Comparison_Tables/f029_decomposition.csv`):
Re basis × 1.011 · isothermal SST (incl. mesh and development) × 0.974 · heating × 0.910 =
**× 0.896 (−10.4 %)**. As shares of the log-gap: heating ≈ 86 %, isothermal factor ≈ 24 %, Re
basis ≈ −10 %.

**Finding:** F-029 is **mainly a variable-property (gas-heating) effect** that the constant-property
Section 2 value does not contain. Mesh accounts for about 2 points, flow development for 1–2, SST in
isothermal flow for about 0 ± 2. About 5 points remain as a model-versus-correlation uncertainty
under strong heating. PR-04's recorded status on the medium production mesh (−10.4 %) is **not
re-interpreted here**. For information, the fine and extrapolated values are −9.6 % and −8.4 %.

## 10. y⁺ on the conjugate wall

| | Coarse | Medium | Fine |
|---|---|---|---|
| y⁺ min / mean / median | 0.207 / 0.238 / 0.233 | 0.208 / 0.241 / 0.236 | 0.209 / 0.243 / 0.238 |
| y⁺ 95th / 99th percentile / max | 0.286 / 0.477 / 0.522 | 0.288 / 0.499 / 0.585 | 0.291 / 0.391 / 0.653 |
| Wall area with y⁺ ≤ 1 / ≤ 0.5 | 100 % / 99.2 % | 100 % / 99.1 % | 100 % / 99.3 % |
| First-cell-centre distance, mid-span | 5.23–6.02 µm | 5.19–6.06 µm | 5.17–6.08 µm |
| Circumferential peak-to-peak: y⁺ / τ_w | 14.2 % / 0.15 % | 15.5 % / 0.08 % | 16.1 % / 0.13 % |
| Maximum located at | first slab, z = 5.0 mm | z = 3.3 mm | z = 2.2 mm |

- **Wall-normal spacing is the same on every mesh.** The first layer is 12.2 µm by design; the
  measured first-cell-centre distances differ by about 1 %. The study refines everything
  except this dimension.
- **O-grid structure.** The super-ellipse core bends the radial grid lines, so the first layer is
  about 15 % thinner at the four diagonals (≈ 10.4 µm) than on the axes (≈ 12.1 µm) (F-028). Each
  mesh shows the same four-fold y⁺ pattern (Figure MI08b), while the wall shear varies only
  0.1 % around the circumference. The y⁺ variation is spacing, not flow.
- **Circumferential resolution.** With 32 / 48 / 72 cells around the wall, the finer meshes sample
  the thin diagonal cells more closely, so the peak-to-peak y⁺ rises from 14.2 to 16.1 %.
- **Mean y⁺ rises 1.2 % and 0.7 %** because the *solution* changes (higher τ_w as f rises, slightly
  cooler wall so lower ν), not because the grid does.
- **Maximum y⁺ is a sampling position (status E).** It is always in the first slab, whose centre
  moves toward the inlet leading edge (5.0 → 3.3 → 2.2 mm), where the shear is highest.
- **SST compatibility:** all three meshes are wall-resolved (y⁺ ≤ 0.66), which suits the
  `correlation` ω wall treatment. The isothermal diagnostic reaches y⁺ 0.85 because the near-wall
  air is colder, which shows the margin to 1 shrinks when the wall is cooler or the flow faster.
  Recheck it for any parametric case at higher velocity.

## 11. Master table

Machine-readable, with extrapolated values, GCI and the reason for each status:
`MESH_INDEPENDENCE_RESULTS.csv`. Temperature percentages are of the rise above 300 K.

| Quantity | Coarse | Medium | Fine | Coarse→Medium | Medium→Fine | Geometry effect | Status |
|---|---|---|---|---|---|---|---|
| Cells | 51,840 | 159,840 | 500,580 | ×3.08 | ×3.13 | N = 32 / 48 / 72 | — |
| ṁ [g/s] | 8.631 | 8.662 | 8.676 | +0.36 % | +0.16 % | 100 % (planar ratio); corrected 8.687 on all | **D** |
| Δp [Pa] | 437.1 | 438.1 | 439.1 | +0.24 % | +0.23 % | est. −1.24 / −0.55 Pa, opposing | **B** |
| Δp, geometry-adjusted (est.) [Pa] | 434.9 | 437.1 | 438.7 | +0.52 % | +0.35 % | removed (estimate) | **B** (ext. 441.8) |
| T_out [K] | 369.12 | 368.93 | 368.85 | −0.18 K (−0.26 %) | −0.08 K (−0.12 %) | 101 % (Q/ṁ); corrected 368.783 / 368.785 / 368.786 | **D** |
| Q [W] | 602.22 | 602.76 | 602.99 | +0.09 % | +0.04 % | 100 % (lateral ratio); corrected 603.19 on all | **D** |
| T_max, solid [K] | 565.4 | 562.6 | 560.8 | −2.8 K (−1.07 %) | −1.7 K (−0.66 %) | bulk shift 7 % / 5 % | **B** (ext. 558.1 ± 3.4) |
| ΔT_wall, mid-span [K] | 7.554 | 7.581 | 7.597 | +0.35 % | +0.21 % | est. ≈ 76 % / 56 % (apothem) | **B** (ext. 7.620 ± 0.03) |
| Nu_fd | 53.4 | 54.2 | 54.7 | +1.48 % | +0.91 % | est. −0.05 % / −0.02 % | **B** (ext. 55.4) |
| f_fd | 0.02134 | 0.02163 | 0.02181 | +1.35 % | +0.85 % | est. −0.05 % / −0.02 % | **B** (ext. 0.0221) |
| Volume-mean solid T [K] | 527.7 | 525.5 | 524.2 | −0.95 % | −0.58 % | bulk shift | B (ext. 522.3) |
| y⁺ mean | 0.238 | 0.241 | 0.243 | +1.2 % | +0.7 % | none (first layer fixed) | B |
| y⁺ max | 0.52 | 0.58 | 0.65 | +12 % | +12 % | sampling position (first slab) | **E** |
| Mass imbalance [%] | 1.2e-13 | 7.0e-13 | 3.9e-12 | — | — | — | A (round-off) |
| Energy imbalance [%] | 2.0e-11 | 3.1e-11 | 6.2e-11 | — | — | — | A (round-off) |

## 12. Mesh decision — medium for downstream work, fine as the reference

The choice was made on six criteria. Neither the fine nor the medium mesh was assumed.

| Criterion | Coarse | **Medium** | Fine |
|---|---|---|---|
| **Sensitivity** (distance from the extrapolated value) | T_max +7.3 K; Nu −3.7 %; f −3.5 % | **T_max +4.4 K; ΔT_wall −0.04 K; Nu −2.3 %; f −2.2 %; Δp −0.8 %** | T_max +2.7 K; Nu −1.4 %; f −1.4 %; Δp −0.6 % |
| **Physics** (wall-resolved, same flow structure, MI09) | yes | yes | yes |
| **Cost** (wall clock / files) | 9 min / 6 MB | **13 min / 14 MB** | 44 min (3.4×) / 56 MB (4.1×); fluid-cell export 143 MB |
| **Structural coupling** (solid cells to map to Mechanical) | 13,440 | **43,200** (≈ 48 k nodes, inside the typical 128 k Student structural limit, to be confirmed in Section 7) | 145,800 (≈ 157 k nodes, 72 × 16 × 136): about 1.2× that limit for a 1:1 structural mesh |
| **Thermal sensitivity vs other uncertainties** | mesh bias 7 K | **mesh bias 4.4 K vs 19 K model–analytical gap and ~5 % friction/heating model uncertainty** | mesh bias 2.7 K |
| **Student licence / laptop** | trivial | **comfortable** (4 cores) | runs (T-008 closed: no restriction at 500,580 cells), but 44 min per case |

**Decision (D-034): use the MEDIUM mesh (159,840 cells) for all downstream work.** Keep the fine
mesh as the verification reference and quote the extrapolated values when validating against
correlations. Reasons, in order:
1. **Its error is known, small and conservative where it matters.** Medium runs 4.4 K hotter at the
   peak and 3.1 K hotter on the volume mean than the extrapolated field. That overstates restrained
   thermal stress and free growth by 1.4–1.7 %, which is on the safe side. The through-wall ΔT that
   drives LC1 is 0.5 % low (0.04 K), which is negligible.
2. **Mesh error is not the dominant uncertainty.** The 19 K difference from Section 2 and the ≈ 5-point
   heating-friction uncertainty are model and correlation effects (§8.1, §9). A finer mesh does not
   reduce them.
3. **Cost.** The fine mesh gains ≈ 1.7 K and ≈ 0.9 % in Nu for 3.4× the run time and 4× the storage,
   a cost that would repeat in every later case.
4. **Coupling.** The medium solid mesh can be mapped 1:1 into a Student structural model; the fine
   one probably cannot.

The coarse mesh is **not** recommended: its peak temperature bias (7.3 K) is the largest and the
saving over medium is only 4 minutes.

**What would change this decision:** if Section 7 shows the structural answer depends on the local
peak temperature to better than ≈ 1.7 %, or if a later case moves y⁺ or the thermal gradients
materially. In that case, rerun that case on the fine mesh.

## 13. Downstream impact (thermal expansion, stress, deformation)

Sensitivities from the frozen Section 2 closed forms: E·α = 188.1 GPa × 13.72 × 10⁻⁶ /K =
**2.58 MPa/K** (restrained, LC2); α·L = 8.23 µm/K (free growth); LC1 stress ∝ through-wall ΔT.
Source: `Uncertainty/downstream_impact.csv`; details in `Uncertainty/UNCERTAINTY.md`.

| CFD input to Mechanical | Medium | Best estimate (extrapolated) | Medium − best | Structural effect of using medium |
|---|---|---|---|---|
| Peak solid temperature | 562.58 K | 558.13 K (GCI_fine 3.4 K) | **+4.4 K** | LC2 local axial stress **+11.5 MPa** on 657 MPa (**+1.7 %**), conservative |
| Volume-mean solid temperature | 525.48 K | 522.34 K | **+3.1 K** | free axial growth **+0.026 mm** (+1.4 % of the CFD mean rise), conservative |
| Through-wall ΔT, mid-span | 7.581 K | 7.620 K (GCI_fine 0.03 K) | **−0.040 K (−0.5 %)** | LC1 peak stress **−0.09 MPa** on 16.3 MPa, negligible |
| Heat input | 602.76 W | 603.19 W (circle) | −0.07 % | geometric; bulk-temperature effect < 0.15 K |
| For comparison: CFD vs Section 2 peak temperature | 562.58 K | 581.71 K (analytical) | −19.1 K | ≈ 49 MPa (7.5 %) on LC2: **model difference, 4× the mesh effect** |

Mesh-related deformation changes are a few hundredths of a millimetre axially and below a micron
radially. The mesh uncertainty that Mechanical inherits is small compared with the modelling
choices still ahead: the temperature-mapping basis (F-027), the end restraint, and the correlation
uncertainty in h.

## 14. Engineering conclusion — nine questions

1. **Is the fine solution converged and conservative?** Yes. It converged at 600 and was confirmed
   at 700 iterations. Residuals are ≤ 2 × 10⁻¹⁰; mass imbalance is 3.9 × 10⁻¹² % and energy
   imbalance 6.2 × 10⁻¹¹ %. The physics is identical to the medium case (0-entry settings diff,
   177/177 audit items).
2. **Which differences are geometry, not mesh error?** Mass flow, heat input and outlet temperature
   (and outlet Re) change only because the polygon changes. Corrected, they agree to round-off.
   About ¾ of the small through-wall ΔT change is probably geometry too (estimate).
3. **Is Δp mesh-converged?** Approximately (B). Raw Δp changes 0.24 % and 0.23 % per level, and its
   geometric and resolution parts oppose each other. The geometry-adjusted series gives 441.8 Pa
   with about 1 % uncertainty.
4. **Is the thermal field mesh-converged?** Approximately (B). It converges monotonically at
   p ≈ 1.3. The fine-mesh uncertainty is ±3.4 K on T_max and ±0.03 K on the through-wall ΔT.
   It is not "mesh-independent" in a strict sense, and it is not called that here.
5. **Does refinement explain F-029?** Only about 2 of the 10.4 points. The gap is mainly gas heating
   that the constant-property Section 2 value omits. SST is 2.6 % below Petukhov in
   isothermal flow on the medium mesh (about 0.4 % after the mesh correction), and the averaging window is not fully developed.
6. **Does refinement close the 19 K gap to Section 2?** No. It widens it to about 21 K (fine) and
   about 24 K (extrapolated). The gap is in h (correlation versus CFD), not in the mesh.
7. **Is the near-wall resolution adequate for SST?** Yes, on all three meshes: y⁺ ≤ 0.66 and 100 %
   ≤ 1. The first layer is identical by design, so the study does not test first-cell height.
8. **Which mesh goes downstream?** The medium mesh, with the fine mesh as reference (§12).
9. **How much mesh uncertainty goes to Mechanical?** About +4.4 K on the peak and +3.1 K on the mean
   solid temperature (both conservative), and −0.04 K on the through-wall ΔT. In stress terms that
   is ≈ 1.7 % on LC2, ≈ 0.5 % on LC1 and ≈ 0.03 mm of axial growth.

## 15. Limitations and remaining concerns

- **Three points and non-uniform refinement.** The apparent order (1.2–1.6; Δp only after the geometric adjustment) is below the formal 2,
  the first-layer height is not refined, and the extrapolated values carry the assumptions in §6.4.
- **Estimated geometric corrections.** The Δp adjustment and the through-wall ΔT split rely on
  correlation scalings. They are shown beside the raw values, never instead of them.
- **Heating-friction uncertainty (≈ 5 points)** between the CFD and the (T_w/T_b)^−0.1 correction
  cannot be resolved without measured data. Nu shows the opposite tendency: the CFD's property
  effect is weaker (n ≈ 0.35) than the n = 0.5 assumed in Section 2.
- **Fully developed window.** x/D 18–29 is still developing in the CFD. Nu_fd and f_fd are window
  means, not asymptotic values.
- **Fine-mesh core quality.** Minimum orthogonal quality is 0.31 and 540 cells have skewness above
  0.8 at the O-grid corners (F-017, F-018). The solution showed no local anomaly, so T-018 needs no
  action.
- **Structural node limit.** The 128 k figure for the Student structural licence is an assumption
  carried from Section 3 and has not been tested yet.

## 16. Files

| Path (under `09_Mesh_Independence/`) | Content |
|---|---|
| `Mesh_Independence_Report.md` | this report |
| `MESH_INDEPENDENCE_RESULTS.csv` | master table with extrapolated values, GCI, status and basis |
| `MESH_INDEPENDENCE_AUDIT.md` | method, checks, frozen-file hashes, reproducibility |
| `mesh_study_results.json`, `mesh_study_log.txt` | complete machine-readable results; run log |
| `Raw_Data/` | copies of the three results JSONs and axial profiles; `three_mesh_values.json` |
| `Geometry_Correction/` | `GEOMETRY_CORRECTION.md`, `faceting_ratios.csv`, `geometry_corrections.csv` |
| `Comparison_Tables/` | `MASTER_TABLE.md`, `three_mesh_raw_table.csv`, `f029_decomposition.csv` |
| `Uncertainty/` | `UNCERTAINTY.md`, `gci_analysis.csv`, `downstream_impact.csv` |
| `Plots/` | MI01–MI07 (cells vs Δp, T_out, Q, T_max, mid-span ΔT, Nu, f; raw and corrected together), MI08 y⁺, MI09 profiles, MI10 geometry vs resolution, MI11 F-029 evidence |
| `Scripts/mesh_study.py` | the whole analysis; reads only saved results; rerunnable |
