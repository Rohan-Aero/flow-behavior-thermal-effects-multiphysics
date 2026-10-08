# Section 9A: evaluation of candidate parametric variables

> **RE-ANALYSIS 2026.** This is a planning document.
>
> - The numbers are **screening estimates** from `Analytical_Screening/parametric_screening.py`: the Section 2 1-D model, anchored to the solved P00 baseline. They are not CFD or Mechanical results.
> - Percentages are changes from P00_BASELINE for the proposed ±10 % (velocity, heat flux) and ±2 mm (thickness) levels.

## 1. Candidates A–C

| Criterion | **A. Inlet velocity V** | **B. Outer-wall heat flux q″** | **C. Wall thickness t** (Q held constant) |
|---|---|---|---|
| Physical relevance | coolant flow rate: the designer's **cooling lever**, changing wall temperature without changing heat input | **thermal load** (heater power / external heating): the prime driver of temperature and restrained stress | the main **geometric design lever**: section A and I (stability) and the through-wall conduction path |
| Reynolds number | ∝ V: Re_in 26,961 / 29,957 / 32,952 (±10 %) | inlet unchanged; outlet ±1.4 % via μ(T) | unchanged (D_i fixed) |
| Heat transfer | h ∝ Re^0.8: mean h −9 / +9 % | h ±1–2 % (property correction only) | unchanged (same bore flux at constant Q) |
| Temperature | bulk rise ∝ 1/V, film ΔT ∝ 1/h: solid max +25 / −21 K, T_out +7.6 / −6.2 K | rise ∝ q″: solid max −28 / +29 K, T_out −6.8 / +6.9 K | ≤ 1 K change; through-wall ΔT ∝ ln(D_o/D_i): −15 / +14 % |
| Thermal expansion (LC1 ΔL) | +11 / −9 % | −12 / +13 % | ±0.2 % |
| Thermal stress | LC2 \|σ\| +10 / −8 % (via mean T); LC1 −4 / +2 % (through-wall ΔT hardly changes) | LC2 \|σ\| −12 / +12 %; LC1 −7 / +6 % | LC2 σ ±0.2 % but end force −26 / +28 % (∝ A); LC1 −17 / +16 % |
| Buckling λ₁ (S1) | −10 / +10 % (V01 ≈ 1.00) | +14 / −11.5 % (Q03 ≈ 0.98) | −15 / +16.5 % (T01 ≈ 0.94, T03 ≈ 1.29); P_cr −37 / +50 % |
| Computational cost | 1 CFD run per level on the **existing medium mesh** (about 13 min); FE on mesh B (about 8 min per set) | same as A | new CAD + new CFD mesh (scripted generator, fluid part unchanged) + new FE mesh and Workbench project + new mapping source per level; FE up to 127,080 nodes |
| Geometry / mesh regeneration | none, if the y⁺ policy holds (y⁺_max est. 0.53–0.64) | none | **yes** (geometry changes); mesh adequacy checks at both extremes |
| Limiting validity | low V: near-wall air must stay below the 600 K air table | high q″: same 600 K air limit | licence: t = 12 mm is the thickest at the baseline 2 mm radial element size |
| **Verdict** | **Approved** (±10 %) | **Approved** (±10 %) | **Approved** (8 / 10 / 12 mm, constant Q) |

**Why all three, and not only two.** A and B act on the structure mostly through the same mechanism, the temperature level. They are still both kept, for two reasons:

- They answer different operating questions: "more heat" against "less cooling".
- Only B scales the through-wall gradient (LC1). Only A changes the flow-side outputs Δp, h and y⁺.

C is the only variable that changes the *section* while leaving the thermal field essentially fixed. It therefore isolates the stability lever that Section 8 identified as governing.

**Why the thickness cases hold the total heat input Q constant** (q″·D_o constant, so q″ = 8,888.9 W/m² at t = 8 mm and 7,272.7 W/m² at t = 12 mm).

- With q″ held at 8,000 W/m², Q would change by ∓10 %. Temperatures and stresses would then move by ∓10–12 % (screening rows `cand_Tq_*`) and mask the geometric effect.
- Holding Q keeps the bore heat flux (16,000 W/m²) and the fluid-side thermal load identical, so only the conduction path and section change.
- This choice is recorded as decision D-060.

## 2. Candidates considered and rejected

| Candidate | Reason for rejection |
|---|---|
| Duct length L | λ₁ ∝ 1/L² makes it a strong stability lever, but it also changes the heat input, T_out and the developing-flow fraction at once. It confounds thermal and structural effects and overlaps the purpose of C. Needs a new mesh |
| Bore diameter D_i | changes Re, h, y⁺, Δp and the section together; hard to interpret; fluid re-mesh |
| Inlet temperature T_in | with T_ref = 300 K fixed, it shifts the whole thermal strain directly. Physically it is a change of reference state rather than a design variable |
| Outlet pressure | incompressible ideal gas; negligible effect (Δp/p ≈ 0.4 %) |
| Material | outside the re-analysis scope; would need a new verified property set |
| Poisson's ratio ν (T-014, [ASSUMED]) | a model-uncertainty parameter, not a design variable. Its effect on the global mode is small (shear term only). If required, handle it as a separate sensitivity, not in this matrix |
