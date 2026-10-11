# Calculation method

**Status: conceptual and educational. CONCEPTUAL — NOT APPROVED FOR CONSTRUCTION.** These are **preliminary screening calculations only**. They do not validate pressure-vessel or piping integrity, do not size or check any relief device, and do not demonstrate compliance with any code. Where the data are not sufficient for a number, the calculation is not done and the missing inputs are listed (`missing_inputs_register.csv`) instead of fabricating an answer.

`calculations.py` (standard library only, deterministic) implements everything below. `python calculations.py` regenerates every CSV; `validate_design.py` reruns it in a clean directory and requires byte-identical output.

## 1. Four kinds of number, kept apart

| Kind | Where it lives | Example |
|---|---|---|
| Verified property data | `verified_properties.csv`, `verified_constants.csv` (source URL, retrieval date) | Nitrogen density, enthalpy, viscosity; NIST fit coefficients |
| Equations | This file and `calculations.py` | Isothermal flow, radiation, free-molecular conduction |
| Illustrative assumptions and cases | `design_parameters.csv`, classes ASSUMED (AS-nn) and ILLUSTRATIVE (IL-nn), registered in `DESIGN_BASIS.md` section 5 | Source pressure 20 MPa(g), MLI emissivity 0.003 |
| Calculated results | The other CSVs; headline results are also in `design_parameters.csv` as CALCULATED rows | Heat leak, pressure loss |

A parameter that is UNRESOLVED has no value. `P(id)` in `calculations.py` raises `MissingInputError` for it, and the relief-sizing function exists only to raise that error (`relief_sizing`). Tables are interpolated linearly and **never extrapolated**: a request outside a table raises an error.

## 2. Verified property data

Nitrogen properties are computed with the open-source CoolProp library from the published reference equation of state (`generate_verified_properties.py` lists the query of every dataset; `DESIGN_BASIS.md` section 4 says why the NIST WebBook tables are not stored): the 300 K isotherm from 0 to 30 MPa gauge (1 MPa steps), isobars at 0, 1, 2, 5 and 10 MPa gauge, four saturation states, and three closed-volume isochores. Gauge pressure is absolute pressure minus 0.101325 MPa (M005). Compressibility is derived: `Z = p / (rho R_s T)` with `R_s = R_u / M` from the verified gas constant and molar mass. The 7-digit rounding of tabulated pressures is absorbed by an interpolation tolerance of 1e-6 of the table magnitude.

## 3. High-pressure GN2 (`HIGH_PRESSURE_SYSTEM.md`)

**3.1 Mass-flow basis.** The illustrative flow (IL-01) is the existing heated-duct air design flow, recomputed from the master-register inputs M002, M003, M005 and M023 and the air gas constant of `BASELINE_PARAMETERS.md`:

```
mdot = rho V A,   rho = p / (R T),   A = pi D^2 / 4
```

It is reused **only for its magnitude**. It is not a nitrogen requirement (UI-03). The volume at 300 K and 0.101325 MPa is `mdot / rho_N2` with `rho_N2` from the table.

**3.2 Pipe pressure loss (AS-01, AS-02, AS-05).** Isothermal compressible flow of a gas of near-constant `Z R T = p / rho`:

```
p1^2 - p2^2 = G^2 (Z R T) ( f L / D + 2 ln(p1 / p2) ),   G = mdot / A
Re = G D / mu,  f from Colebrook-White (turbulent) or 64/Re (laminar)
```

`p2` is found by bisection. If the flow exceeds the isothermal capacity of the segment the code stops with an error. `Z R T`, the density and `mu` are taken from the table at the segment inlet pressure. Roughness is 0.0015, 0.045 and 0.15 mm (low, nominal, high; AS-02). Route lengths and bends of each line are placeholders (AS-05), with a length factor 0.75, 1.0 and 1.5.

**3.3 Component losses (AS-03, AS-04).** Fittings, valves and the conditional check valve use `dp = K G^2 / (2 rho)` with generic K (AS-03). The filter and the flow element are **allocations**, a fraction of the local absolute pressure (AS-04), because no component data exist (UI-09). The regulators are **controlled drops** to the set pressures (IL-03, IL-04) and are not losses. The flow-control valve drop, the check-valve cracking pressure and the relief and vent back-pressure are unresolved rows, printed with no value (UI-04, UI-09, UI-07, UI-11).

**3.3a Pressure-drop budget structure.** `pressure_budget.csv` runs a chain of rows from the source to the vent. Each included row gives a low, a nominal and a high loss, and the pressure after the row for the nominal chain. Zone totals (high-pressure, intermediate, delivery, all) are sums of the included rows. The delivery-zone total is compared with an illustrative limit (IL-09), which stands in for the unresolved downstream limit (UI-04).

**3.4 Sensitivity (IL-07, IL-08).** The chain is rerun for each line bore of the sweep and each multiplier applied to all component rows (the K rows and the allocations); pipe friction is not multiplied. `pressure_sensitivity.csv` reports the loss per zone, the loss as a percentage of the delivery set pressure, the peak velocity, an approximate Mach number (ideal-gas sound speed with the table `Z R T`) and the Reynolds number.

**3.5 Regulator operating envelope (AS-06, AS-07, AS-08).** For each stage and inlet pressure:

```
critical ratio  r* = (2/(g+1))^(g/(g-1))     (g = cp/cv at 300 K and 0.101325 MPa)
choked flux     G* = Cd sqrt(g rho0 p0) (2/(g+1))^((g+1)/(2(g-1)))
subsonic flux   G  = Cd sqrt( 2 rho0 p0 (g/(g-1)) ( r^(2/g) - r^((g+1)/g) ) ),   r = p1/p0
required area   A  = mdot / G
```

`rho0` is the real density at the stagnation state. The expansion is isenthalpic: the outlet temperature is the temperature on the outlet isobar with the enthalpy of the inlet state (AS-08). These figures show how capacity changes with the inlet pressure and how cold the gas gets. They are **scale figures**, not a relief-sizing calculation and not a regulator selection: the real seat area, discharge coefficient, real-gas exponent and supply-pressure effect are vendor data (UI-08).

**3.6 Oxygen deficiency (AS-20).** A well-mixed room of volume `V` that receives gas `V_add` while displaced mixture leaves reaches `x = x0 exp(-V_add / V)`. The added volume at which `x` falls to the 19.5 percent threshold (VC-05) from 20.95 percent (VC-04) is `V_add = V ln(x0 / x)`. One litre of liquid nitrogen gives `rho_liquid / rho_gas(300 K, 1 atm) / 1000` cubic metres of gas, and 1 L of gas at pressure gives its density ratio to ambient gas. Local concentrations can be far lower.

## 4. Verified values used for boundary conditions (`boundary_conditions.csv`)

Pressures are the illustrative set pressures (IL-02 to IL-04); temperatures after the regulators are the isenthalpic outlets (AS-08, no heat gain); the vent exit is at ambient pressure (AS-09); design pressures and relief settings are UNRESOLVED and blank (UI-06, UI-07, UI-22).

## 5. Liquid nitrogen (`CRYOGENIC_SYSTEM.md`)

**5.1 Geometry (IL-12 to IL-14).** Inner line outside diameter 25 mm, wall 2 mm, jacket inner diameter 50 mm. These are not pipe sizes.

**5.2 Radiation (AS-10, AS-11).** Bare concentric cylinders and a multilayer blanket:

```
Q'_bare = sigma pi D1 (Th^4 - Tc^4) / ( 1/e1 + (D1/D2)(1/e2 - 1) )        [W per metre]
Q'_MLI  = sigma pi D1 e_eff (Th^4 - Tc^4)                                  [W per metre]
```

`e_eff` is an equivalent emissivity on the cold-surface area; its values are placeholders (UI-23, UI-32).

**5.3 Residual-gas conduction (AS-12, AS-13).** Free-molecular regime (valid when the mean free path exceeds the gap):

```
Q'_fm = alpha (g+1)/(g-1) sqrt( Ru / (8 pi M Tm) ) p (Th - Tc) pi D1,   Tm = (Th + Tc)/2
```

Continuum conduction across the annulus (vacuum lost), a **lower bound** because convection is ignored:

```
Q'_c = 2 pi (integral of k(T) dT from Tc to Th) / ln(D2/D1)
```

with the nitrogen conductivity from the verified table. The Rayleigh number of the gap, `g (1/Tm) (Th - Tc) delta^3 / (nu a)`, is reported to show when convection matters. For the degraded vacuum the two limits are bridged as `1 / (1/Q'_fm + 1/Q'_c)`, a **low-confidence interpolation** (AS-13). Air in the annulus is represented by nitrogen.

**5.4 Supports (AS-14).** `Q'_s = n (A/L) integral of k_304(T) dT`, from Tc to the lower of Th and 300 K (the fit's upper limit), with the NIST fit for 304 stainless steel.

**5.5 Boil-off.** `mdot = Q / h_fg` with `h_fg` from the verified saturation rows at 0.101325 MPa; liquid volume rate with the saturated liquid density; vapour volume flows with the saturated vapour density and the 300 K gas density. Totals use the illustrative length (IL-15) and scale linearly (AS-17); terminations are excluded. The source vessel evaporation rate is **not** calculated (UI-20).

**5.6 Uncertainty.** `cryogenic_uncertainty.csv` varies one parameter at a time between its low and high value with the others at nominal, and reports the swing. `cryogenic_heat_leak.csv` carries low, nominal and high cases for each scenario (S1 to S4).

**5.7 Cooldown (AS-16, AS-21).** Energy to cool the metal `m' L integral of cp_304(T) dT` from 300 K to the boiling temperature with the NIST fit; liquid nitrogen is bounded between latent heat only (`h_fg`) and vapour leaving at 300 K (`h_gas(300 K) - h_liquid`).

**5.8 Thermal contraction (AS-19).** `(L(T) - L(T0)) / L(T0)` from the NIST fit of `(L - L293)/L293 x 1e5` (a polynomial above a lower limit temperature, a constant below it) between 300 K and the boiling temperature. The fully restrained thermal stress bound is `integral of E(T) alpha(T) dT` from the cold temperature to 293 K, with `alpha = dy/dT` of the same fit and `E(T)` from the NIST fit. No allowable stress is compared (UI-25).

**5.9 Trapped liquid (AS-18).** The pressure of a closed volume warmed at constant density is read from the verified isochore (806.0844 kg/m3 for a liquid-full volume at the 1 atm saturated density). Time to a pressure threshold `t = m cv dT / Q'` per metre of bore, with `m` the liquid mass per metre, `cv` the saturated-liquid value (VP-06) and `dT` the temperature rise from the isochore at the threshold (IL-16). The thermal mass of the metal and supports is ignored, so the time is the shortest. A partly filled volume is shown by the isochores at 760 and 700 kg/m3 (IL-18).

**5.10 Property screening.** `cryogenic_property_screening.csv` gives, for four saturation pressures, the boiling temperature, the latent heat, the densities and the volume ratios of liquid to saturated vapour and to ambient gas.

## 6. Limits of validity

- Everything depends on placeholders (AS-02 to AS-06, AS-10 to AS-16) and illustrative cases (IL-nn). A different case gives a different number; no number here is a prediction for a real system.
- The pressure budget assumes 300 K gas (AS-01) and no heat gain; the real cold gas is denser.
- Choked-flux figures use an ideal-gas exponent with a real density; at high pressure the real-gas behaviour differs and a relief calculation needs the real fluid model and a certified coefficient.
- The degraded-vacuum heat leak is an interpolation; the lost-vacuum value is a lower bound; MLI behaviour at degraded vacuum is not modelled.
- Free-molecular conduction uses an overall accommodation coefficient and an arithmetic mean temperature.
- Elastic stress bounds only; no plasticity, no allowable.
- No transient, two-phase, hydraulic-surge or stress-analysis calculation is done.

## 7. What is not calculated, and why

| Not calculated | Reason |
|---|---|
| Relief-device sizing, set pressures and vent sizes | Need UI-06, UI-07 and UI-22 and real component data |
| Vessel and piping integrity, wall thickness, test pressure | Need classification, code, materials and design pressures (UI-05, UI-06, UI-25) |
| Source vessel normal evaporation rate | Needs vessel data (UI-20) |
| Heat leak of terminations, valves, flanges and bayonets | Needs the real hardware (UI-21, UI-23, UI-24) |
| Two-phase pressure drop, flashing, hydraulic transients | Need geometry and transfer rate (UI-21, UI-27, UI-33) |
| Dispersion of cold vapour and vent plumes | Needs the site and the vent design (UI-11, UI-29) |
| Regulator droop, supply-pressure effect, lock-up | Need vendor data (UI-08) |
| Stress margin against an allowable | No allowable stress is available (UI-25) |
