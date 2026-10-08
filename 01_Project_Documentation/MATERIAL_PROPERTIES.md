# MATERIAL PROPERTY AUDIT — Section 2, Step 9

**Date:** 2026-09-18 · **RE-ANALYSIS (2026)**

Every externally obtained property is listed with its source. Values that are assumed
rather than sourced are marked **[ASSUMED]**. The audit produced **real findings**, listed
first.

---

## 🔴 Audit findings

### F1 — Yield strength was non-conservative by 3.4 % · **CORRECTED**

Section 1 used **S_y = 1060 MPa** at the operating temperature. The VDM Alloy 718 mill
datasheet gives, for solution-annealed and age-hardened material:

| Temperature | 0.2 % proof strength |
|---|---|
| 20 °C | 1030 MPa |
| 100 °C | 1060 MPa |
| 200 °C | 1040 MPa |
| 300 °C | 1020 MPa |
| 400 °C | 1000 MPa |

Interpolated to our mean solid temperature of **281.6 °C**: **1023.7 MPa**.

The Section 1 value of 1060 MPa is the *peak* of the curve (at 100 °C), not the value at
our operating temperature. **Using it overstated the margin.** Corrected to 1023.7 MPa.
Effect: LC2 utilisation 0.620 → **0.642**, margin of safety 0.61 → **0.56**. Still
comfortably elastic, but the corrected number is the honest one.

### F2 — Young's modulus and conductivity **independently confirmed to < 1 %**

| Property | Section 1 value | VDM datasheet at same temperature | Agreement |
|---|---|---|---|
| Young's modulus E | 188.5 GPa | **188.1 GPa** (interp. to 281.6 °C) | **0.2 %** |
| Thermal conductivity k_s | 15.3 W/m·K | **15.22 W/m·K** (interp. to 301 °C) | **0.5 %** |

Two independently chosen values matching a mill datasheet to under 1 % is meaningful
corroboration of the Section 1 property work.

### F3 — Specific heat was 10 % low · corrected, but **irrelevant**

Section 1 used 435 J/kg·K (a room-temperature value); VDM gives 460 J/kg·K at 20 °C rising
to 485 at 300 °C. Corrected to **481 J/kg·K**. **This changes nothing** — specific heat does
not appear anywhere in a steady-state solution. It is corrected for completeness and would
matter only in a future transient study.

### F4 — Two web extractions returned **wrong values** · caught before use

Worth recording as a process note, because it nearly contaminated the audit:

- A fetch of a standard air-property table returned rows for ~573 K while labelling them
  300 K (density 0.6158 kg/m³ — physically impossible for air at 300 K, 1 atm). Caught by
  checking ρ against p/(RT). **Re-fetched with an explicit row request.**
- A fetch of the VDM datasheet returned the CTE column as "7.73 × 10⁻⁶/K". Inconel 718's
  CTE near room temperature is ~13 × 10⁻⁶/K; 7.73 is the value in units of **10⁻⁶/°F**
  (7.73 × 1.8 = 13.9 × 10⁻⁶/°C). **The extraction mislabelled the units.** CTE was
  therefore taken from a source that states both unit systems explicitly.

**Lesson applied:** every fetched property was cross-checked against an independent
relation or a second source before being used. A value that cannot be sanity-checked does
not go in the model.

### F5 — Air property tables disagree by ~3 % · quantified, **not** changed

| Property at ~300 K | Incropera Table A.4 (**frozen, primary**) | Çengel Table A-15 (cross-check) | Δ |
|---|---|---|---|
| Specific heat cₚ | 1007 J/kg·K | 1007 J/kg·K | 0.0 % |
| Dynamic viscosity μ | 1.846 × 10⁻⁵ Pa·s | 1.849 × 10⁻⁵ Pa·s | 0.2 % |
| Thermal conductivity k | 0.02624 W/m·K | 0.02551 W/m·K | **2.9 %** |
| Prandtl number Pr | 0.707 | 0.7296 | **3.2 %** |

Both tables are internally consistent (Pr = μcₚ/k checks out in each); they simply draw on
different measurement compilations.

**Net effect on the result:** h ∝ Nu·k and Nu ∝ Pr^0.4, so the two effects partly cancel:

```
(0.7296/0.707)^0.4 = +1.3 %  on Nu ;  k lower by 2.9 %  ->  net  -1.7 % on h
```

**Under 2 % — an order of magnitude below the ~20 % property-variation correction and the
5–15 % turbulence-model uncertainty.** Section 1 froze Incropera, so Incropera is retained;
the spread is documented and folded into the acceptance band rather than acted on.

### F6 — Density must **not** be taken from the air table

Standard air-property tables list density at **100 kPa**, not 101.325 kPa (Incropera's
1.1614 kg/m³ at 300 K = 100 000/(287 × 300) exactly). Taking the tabulated value while
running at 1 atm would introduce a silent **1.3 % mass-flow error**.

**Density is therefore computed** as ρ = p_op/(R T) at the stated operating pressure, and
only cₚ, μ, k and Pr are read from the table. This keeps the model self-consistent.

---

## Solid — Inconel 718 (age-hardened)

| Property | Symbol | Value used | Units | Source |
|---|---|---|---|---|
| Density | ρ_s | 8190 | kg/m³ | [Special Metals / High Temp Metals](https://www.hightempmetals.com/techdata/hitempInconel718data.php) — VDM gives 8260, HTM 8220; **0.9 % spread, no effect on any steady-state result** |
| Young's modulus | E | **188.1** (at 281.6 °C) | GPa | [VDM Alloy 718 Data Sheet No. 4127](https://www.vdm-metals.com/fileadmin/user_upload/Downloads/Data_Sheets/Data_Sheet_VDM_Alloy_718.pdf) — 204/199/193/187/180 GPa at 20/100/200/300/400 °C |
| Poisson's ratio | ν | 0.294 | — | **[ASSUMED]** — *neither fetched datasheet lists it.* Literature range 0.284–0.294; upper end taken as conservative for LC1 (σ ∝ 1/(1−ν)). **1.4 % spread.** |
| Thermal conductivity | k_s | **15.22** (at 301 °C) | W/m·K | [VDM](https://www.vdm-metals.com/fileadmin/user_upload/Downloads/Data_Sheets/Data_Sheet_VDM_Alloy_718.pdf) — 11.5/12.1/13.5/15.2/17.1 at 20/100/200/300/400 °C |
| Specific heat | c_p,s | 481 (at 281.6 °C) | J/kg·K | [VDM](https://www.vdm-metals.com/fileadmin/user_upload/Downloads/Data_Sheets/Data_Sheet_VDM_Alloy_718.pdf) — 460/458/468/485/501. **Unused in steady state.** |
| Mean CTE from 21 °C | α | **13.72** (at 281.6 °C) | 10⁻⁶/K | [High Temp Metals / Special Metals](https://www.hightempmetals.com/techdata/hitempInconel718data.php) — 12.8/13.3/13.9/14.2/14.8 × 10⁻⁶/°C for means to 93/204/316/427/538 °C |
| 0.2 % yield strength | S_y | **1023.7** (at 281.6 °C) | MPa | [VDM](https://www.vdm-metals.com/fileadmin/user_upload/Downloads/Data_Sheets/Data_Sheet_VDM_Alloy_718.pdf) — age-hardened |

All temperature-dependent properties are **interpolated to the actual local temperature**
in `baseline_calculations.py`, not held at a single value.

## Fluid — Air at 1 atm

| Property | Symbol | 300 K | 368.9 K | Source |
|---|---|---|---|---|
| Density | ρ | 1.1766 | 0.9569 kg/m³ | **Computed** from p_op/(RT) — see F6 |
| Specific heat | cₚ | 1007 | 1011 J/kg·K | Incropera & DeWitt, *Fundamentals of Heat and Mass Transfer*, Table A.4 |
| Dynamic viscosity | μ | 1.846 × 10⁻⁵ | 2.176 × 10⁻⁵ Pa·s | Incropera Table A.4 |
| Thermal conductivity | k | 0.02624 | 0.03123 W/m·K | Incropera Table A.4 |
| Prandtl number | Pr | 0.707 | 0.696 | Incropera Table A.4 |
| Specific gas constant | R | 287.058 J/kg·K | | Standard dry air |
| Ratio of specific heats | γ | 1.4 | | Standard diatomic ideal gas — used only for Mach |

Cross-check source: [Çengel, Table A-15, hosted at me.psu.edu](https://www.me.psu.edu/cimbala/me433/Links/Table_A_9_CC_Properties_of_Air.pdf) — see F5.

---

## Property uncertainty, ranked by effect on the answer

| Rank | Property | Spread | Effect on final stress |
|---|---|---|---|
| 1 | **Correlation correction exponent n** | 0.4–0.575 | **±5 %** on LC2 (624–686 MPa) |
| 2 | Air k and Pr (source-to-source) | ~3 % | < 2 % on h → ~0.5 % on stress |
| 3 | Yield strength | 3.4 % (now corrected) | direct on margin of safety |
| 4 | Young's modulus | ~0.2 % confirmed | ~0.2 % on stress (linear) |
| 5 | Poisson's ratio **[ASSUMED]** | 0.284–0.294 | 1.4 % on LC1 only; **none** on LC2 |
| 6 | Solid conductivity | ~0.5 % confirmed | ~0.5 % on the 7.3 K through-wall ΔT |
| 7 | Density, specific heat (solid) | 0.9 %, 10 % | **zero** — neither appears in a steady-state result |

**The dominant uncertainty is not a material property at all** — it is the correlation
correction, which is a modelling choice. That is a useful thing to know before spending
effort chasing property data to three decimal places.

---

## Sources

- [VDM Metals, *VDM Alloy 718 Nicrofer 5219 Nb* Material Data Sheet No. 4127](https://www.vdm-metals.com/fileadmin/user_upload/Downloads/Data_Sheets/Data_Sheet_VDM_Alloy_718.pdf)
- [High Temp Metals, *Inconel 718 Technical Data*](https://www.hightempmetals.com/techdata/hitempInconel718data.php)
- [Çengel, *Properties of air at 1 atm*, Table A-15 (hosted at Penn State)](https://www.me.psu.edu/cimbala/me433/Links/Table_A_9_CC_Properties_of_Air.pdf)
- Incropera & DeWitt, *Fundamentals of Heat and Mass Transfer*, Table A.4 — primary air properties (textbook, frozen in Section 1)
- Kays & Crawford, *Convective Heat and Mass Transfer* — property-variation correction for turbulent gas flow
- Timoshenko & Goodier, *Theory of Elasticity* — thick-walled-cylinder thermal stress
- Gnielinski (1976); Dittus & Boelter (1930); Petukhov (1970) — correlations
