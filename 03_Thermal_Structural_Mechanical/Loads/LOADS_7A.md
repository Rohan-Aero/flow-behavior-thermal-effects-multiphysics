# Section 7A: loads (prepared, NOT solved)

> RE-ANALYSIS 2026. Newly generated from the re-analysed CFD solution.

## 1. Thermal load (active in LC1 and LC2)

- **Source.** Imported Body Temperature from External Data `CFD solid T (baseline_medium_final)`. It is mesh-based: a CDB master (the Fluent solid mesh) plus Fluent node temperatures.
- **Mapping.** Mechanical, Bucket Volume + Shape Functions; outside option Nearest Node. Verification is in `07_Thermal_Analysis/THERMAL_MAPPING_NOTES.md`.
- **Field.** The full 3-D field, 423.84–562.56 K on the structural nodes. Volume mean 525.52 K (Fluent: 525.48 K).
- **Reference.** **T_ref = 300 K** (`TREF,26.85` °C). The thermal strain is α(T)·(T(x,y,z) − T_ref) with T_ref = 300 K.

  | Quantity | Range |
  |---|---|
  | ΔT(x,y,z) = T − 300 K | 123.8–262.6 K |
  | Volume-mean ΔT | 225.5 K |

- **Basis.** No Section 2 mean temperature (554.7 K, the length-averaged mid-wall temperature: F-027 as corrected in §12.7) and no CFD maximum is used anywhere. The load is the spatial field itself (brief item 10).

## 2. Internal pressure (prepared, SUPPRESSED in both load cases)

### Physical basis

- **Fluent pressures are gauge values** relative to the operating pressure of 101,325 Pa (read back: `operating pressure 101325`).
- **The outside of the duct is ambient.** So the differential pressure across the wall is the gauge static pressure on the inner wall itself.
- **No absolute pressure is used.** Applying 101 kPa absolute on the inside would be wrong, because the same atmosphere acts on the outside.

### Actual CFD field

Export: `07_Thermal_Analysis/Temperature_Source/fluent_interface_wall_pressure.csv`, 4,320 wall faces. Station averages are in `wall_pressure_profile_7A.csv`, 90 stations.

| Quantity | Value |
|---|---|
| Wall gauge pressure, first station (z = 3.3 mm) | **443.41 Pa** (maximum) |
| Second station (z = 10 mm) | 402.64 Pa. The entrance-region drop is 40.8 Pa in the first slab |
| Last station (z = 596.7 mm) | 2.55 Pa (the outlet is 0 Pa gauge) |
| Circumferential spread | ≤ 0.43 Pa |
| Area-weighted mean over the wall | 202.9 Pa |
| Reference quantity | cross-section area-weighted inlet-minus-outlet Δp = 438.13 Pa (Section 5B, D-031). The wall and section static pressures differ by ≤ 5.3 Pa |

### Objects prepared (suppressed) on SOLID_INNER_INTERFACE, in both LC1 and LC2

| Object | Definition | Use |
|---|---|---|
| `LCx_P_equivalent_uniform_443Pa_SUPPRESSED` | uniform 443.41 Pa normal to the bore | conservative bound: the CFD maximum applied everywhere |
| `LCx_P_CFD_linear_fit_SUPPRESSED` | p(z) = 407.36 − 681.55·z [Pa, z in m], formula read back from Mechanical | least-squares fit of the 90 CFD stations. Maximum deviation 38.3 Pa at the inlet station, mean 2.2 Pa |

**Recommendation for 7B.**

- The pressure is below 0.45 kPa: orders of magnitude below the thermal loading, which comes from a strain of order 10⁻³.
- Keep it suppressed in the primary LC1/LC2 solutions and show its negligibility with one superposition run: the uniform 443 Pa bound, the conservative choice.
- If a spatially resolved load is ever needed, the linear fit deviates from the CFD station values by at most 5.9 Pa (1.3 % of the inlet value) everywhere except the first station, where it is 38 Pa below.

### Other loads

- **None.** No gravity (irrelevant; the mass is 4.6 kg), no flange or bolt loads, no end-cap force. The duct is open-ended with through flow, so the internal pressure produces no axial end load.
