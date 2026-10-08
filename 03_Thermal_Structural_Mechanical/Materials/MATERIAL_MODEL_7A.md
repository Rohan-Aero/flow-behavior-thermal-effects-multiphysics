# Section 7A - structural material model (Inconel_718_Re_analysis)

> RE-ANALYSIS 2026. Every value here was selected in 2026 from public datasheets during the rebuild
> (Section 2, `02_Engineering_Calculations/MATERIAL_PROPERTIES.md`). None of them is a recovered internship value.
> Poisson's ratio is **[ASSUMED]**.

## What the Mechanical model uses

| Property | Model definition | Source | Status |
|---|---|---|---|
| Density | 8190 kg/m³, constant | Special Metals / HTM | datasheet. No gravity load, so it has no effect on thermal stress |
| Young's modulus E(T) | table: 204 / 199 / 193 / 187 / 180 GPa at 20 / 100 / 200 / 300 / 400 °C | VDM Alloy 718 data sheet 4127 | datasheet |
| Poisson's ratio ν | 0.294, constant | literature range 0.284–0.294, upper end | **[ASSUMED]**: in neither datasheet (T-014, F-011) |
| Thermal expansion α(T) | **secant (mean) CTE from 70 °F**: 12.8 / 13.3 / 13.9 / 14.2 / 14.8 ×10⁻⁶ /K at 200 / 400 / 600 / 800 / 1000 °F (93.3 … 537.8 °C) | Special Metals / HTM | datasheet |
| Zero-thermal-strain reference of the α table | 294.26 K (70 °F = 21.11 °C), the datum of the published mean CTE | datasheet definition | — |
| Analysis reference temperature (stress-free state) | **T_ref = 300 K** (Mechanical environment temperature; `TREF,26.85` °C in the input file) | project decision since Section 1 | re-analysed choice |
| Tensile yield S_y | Engineering Data scalar **1020 MPa** = the VDM 300 °C point, a lower bound of S_y(T) over the mapped range 150.7–289.4 °C. The full table (1030 / 1060 / 1040 / 1020 / 1000 MPa at 20…400 °C) is kept in `materials_7A.csv` for Section 7B margins at the local temperature | VDM 4127, age-hardened | datasheet. Not used by the linear solve |
| Thermal conductivity k(T) | 11.5 / 12.1 / 13.5 / 15.2 / 17.1 W/m·K at 20…400 °C, the same table as the CFD | VDM 4127 | information only. Mechanical solves no thermal problem |

In the solver input file (`LC1_Free_Expansion_ds.dat`), Mechanical writes:

- `MPDATA,EX` and `MPDATA,NUXY` on the 20…400 °C points;
- `MPDATA,ALPX` on 93.33…537.78 °C;
- `MPAMOD,1,21.11` (converts the secant table from its 21.11 °C datum to TREF);
- `TREF,26.85`.

Mechanical also prints this message: "the reference temperature for the thermal expansion coefficient differs from the reference temperature of the body; data adjusted to zero thermal strain at the body reference temperature". It is **expected** here, because the datum is 21.11 °C and T_ref is 26.85 °C.

The adjustment only needs α at T_ref. That comes from MAPDL's constant extrapolation below the first point: α(26.85 °C) = α(93.3 °C) = 12.8×10⁻⁶ /K. All mapped temperatures (150.7–289.4 °C) lie inside the table, far from T_ref, so the correction is well conditioned.

## Decision D-036: temperature-dependent E and α, not the Section 2 constants

**What Section 2 used.** Single values evaluated at **281.6 °C**: E 188.1 GPa, α 13.72×10⁻⁶ /K, S_y 1023.7 MPa.

**Why they are not used here.** 281.6 °C is the Section 2 *analytical* mean-temperature basis. Brief item 10 forbids mixing that basis with the CFD field (F-027: the CFD volume mean is 525.48 K = 252.3 °C, about 30 K lower).

**What is used instead.** With the full 3-D CFD field, every point takes its properties at its own temperature. The model therefore uses the same datasheet points that Section 2 interpolated, now as tables.

**How big the difference is** (effective properties after re-referencing to 300 K; interpolation of the datasheet points, no stress computed):

| T | E(T) [GPa] | α(T) re-referenced to 300 K [10⁻⁶/K] |
|---|---|---|
| 423.8 K (source minimum) | 195.96 | 13.07 |
| 525.5 K (CFD volume mean) | 189.86 | 13.58 |
| 562.5 K (source maximum) | 187.64 | 13.78 |
| Section 2 constants (281.6 °C) | 188.1 | 13.72 |

The product E·α differs from the Section 2 constant product by less than about 1 % over the whole range. The choice is made for consistency of basis, not because it moves the answer much.

A constant-property run (Section 2 values) can be used in 7B as a sensitivity case if a like-for-like comparison with the analytical estimate is wanted.

## Open material items

- **T-014 / F-011:** Poisson's ratio is still [ASSUMED] (effect about 1.4 % on LC1 per Section 2; none on the axial LC2 stress).
- **Datum of the mean-CTE table.** The published table starts at 70 °F. Section 2 wrote "21 °C". The 0.11 K difference is immaterial.
- **Yield is temperature-dependent.** 7B must evaluate margins with S_y at the local temperature of the peak-stress location, not with the 1020 MPa scalar blindly.
  - The scalar is 0.2 % below S_y(T) at the hot end (1022.1 MPa at 289.4 °C).
  - It is 2.8 % below at the cold end (1049.9 MPa at 150.7 °C).
