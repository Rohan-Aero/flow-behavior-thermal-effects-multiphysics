# Section 12A — Material-Data Check for an LS-DYNA Nonlinear Analysis

> **Sources checked:**
> - `08_Structural_Analysis/Materials/materials_7A.csv` and `MATERIAL_MODEL_7A.md`;
> - the MP block of the LC2 solver deck;
> - `11_Final_Audit/MASTER_PROJECT_DATA.csv` (M010–M013);
> - a project-wide keyword search (plastic, stress–strain, tangent, hardening, T-036, F-045).
>
> No data were added, estimated or taken from new sources. Full table: `material_availability_12A.csv`.

## 1. Availability

| Property | In project? | Values | Status |
|---|---|---|---|
| Young's modulus E(T) | yes | 204 / 199 / 193 / 187 / 180 GPa at 20 / 100 / 200 / 300 / 400 °C | datasheet, VDM 4127 [M010] |
| Poisson's ratio ν | yes, assumed | 0.294, constant | **[ASSUMED]** (T-014 / F-011) [M012] |
| CTE α(T) | yes, **secant** | 12.8 / 13.3 / 13.9 / 14.2 / 14.8 ×10⁻⁶ /K at 93.33 / 204.44 / 315.56 / 426.67 / 537.78 °C, mean from 21.11 °C (70 °F) | datasheet, Special Metals / HTM [M011]. Mechanical re-references it to T_ref = 300 K (`MPAMOD,1,21.11`, `TREF,26.85`) |
| 0.2 % yield S_y(T) | yes, typical | 1030 / 1060 / 1040 / 1020 / 1000 MPa at 20 / 100 / 200 / 300 / 400 °C | datasheet **typical** values, age-hardened, VDM 4127 [M013]. Not minimum or specification values |
| Post-yield stress–strain curve, hardening or tangent modulus, any temperature | **no** | — | **Missing** (F-045, T-036). The 8A Johnson values are conventional, not material data |
| Ultimate strength, elongation | no | — | not needed for the elastic study |
| Creep | no | — | outside scope (steady state, 150–290 °C) |
| Density | yes | 8190 kg/m³ | needed only as RO in LS-DYNA. Static implicit, no gravity |

## 2. Decision on material nonlinearity

**Material nonlinearity is marked UNAVAILABLE.**

- No temperature-dependent plastic stress–strain curve for Inconel 718 exists in the project, and none will be invented.
- That includes a bilinear or elastic–perfectly-plastic substitute. ETAN = 0 above S_y is itself a post-yield assumption.
  The S_y values are also typical, not minimum.
- The elastic–plastic path can only be added if authoritative data are supplied: lot data or specification-minimum curves
  at 150–290 °C, recorded with their source (T-036).

## 3. What is still possible: a thermo-elastic, geometrically nonlinear, imperfect-buckling study

| Requirement | Met by | Reference |
|---|---|---|
| Temperature-dependent elasticity without yield | `*MAT_ELASTIC_PLASTIC_THERMAL` (MAT_004) with T, E, PR given and **SIGY / ETAN not defined** | Vol II PDF p. 237–239: remark 2, *"If a thermo-elastic material is considered, do not define SIGY and ETAN"*. Up to 8 temperature points. *"The analysis will terminate if a material temperature falls outside the range specified"*. Remark 1: the stress rate includes Ċ·C⁻¹σ, so for small strain σ̇ = d(Cε_e)/dt, i.e. total-form elasticity like MAPDL. Confirmed by the G0 restrained-bar sub-test |
| Thermal strain with the project's α | `*MAT_ADD_THERMAL_EXPANSION` (LCID = α vs T curve), with ALPHA = 0 in MAT_004 | Vol II PDF p. 209–210. The stress update uses ε̇ − α(T) Ṫ δ, so **α is instantaneous**. MAT_004 remark 1 also defines α as instantaneous |
| Alternative elastic model | `*MAT_TEMPERATURE_DEPENDENT_ORTHOTROPIC` (MAT_023), set isotropic, up to 48 points | Vol II PDF p. 321 |

### Required CTE conversion (exact algebra on the same datasheet table; no new data)

Mechanical's total thermal strain from the 300 K stress-free state is:

ε_th(T) = α_s(T)·(T − T_d) − α_s(T_ref)·(T_ref − T_d)

where:

- T_d = 21.11 °C is the datum of the secant table;
- T_ref = 26.85 °C;
- α_s is linearly interpolated in the secant table, with constant extrapolation below 93.33 °C, as in MAPDL. That gives
  α_s(T_ref) = 12.8 × 10⁻⁶ /K (`MATERIAL_MODEL_7A.md`).

LS-DYNA needs α_inst(T) = dε_th/dT = α_s(T) + α_s′(T)·(T − T_d). This curve is **discontinuous at the five table
temperatures**, because α_s′ jumps there. So:

- An 8-point MAT_004 ALPHA table **cannot** represent it exactly.
- A dense `*DEFINE_CURVE` for `*MAT_ADD_THERMAL_EXPANSION` can.
- Acceptance check before any run: ∫ α_inst dT from 300 K must reproduce ε_th(T) at every node temperature, to a
  tolerance fixed in advance. Then LS-DYNA gates G2 (ΔL 1.8409 mm) and G3 (548,936.6 N) confirm it.

The conversion will be scripted and recorded in the build phase. **It has not been computed in 12A.**

### Temperature range

- The E table covers 20–400 °C (293–673 K).
- Scaling the field T = 300 K + λ·(T_i − 300 K) with T_i,max = 562.56 K keeps every node in range up to
  **λ = 1.42**. The study is capped there. The only extrapolation is the baseline's own: α_s held constant below 93.33 °C, as
  MAPDL does. No other property is extrapolated.

## 4. Limitations of the elastic study (to be stated with every result)

1. **No collapse load.** Elastic column post-buckling is not a collapse mechanism, and restrained thermal loading
   partly relieves itself by bowing. A limit point may not exist.
2. **Inelastic buckling not represented.**
   - The column is intermediate: KL/r 53.67 < C_c 60.2 (8A).
   - The elastic critical stress σ_E ≈ 650 MPa lies above the conventional proportional limit.
   - The 8A conventional Johnson estimate (1.058) indicates that inelastic effects would act below the elastic λ₁. It is
     an idealised S1 indicator, **not a capacity or margin**.
3. **Elastic validity ends at first yield.** Results are physically meaningful only up to the λ at which von Mises first
   reaches typical S_y(T) at the local temperature. Beyond that, stresses and deflections are elastic extrapolations.
4. ν is assumed; E and α carry about ±2 % uncertainty (MASTER_UNCERTAINTIES U5); S_y values are typical.
5. No residual stress, no strength scatter.
