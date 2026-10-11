# Calculation method

Conceptual and educational. Everything below is produced by `calculations.py` (Python standard library only, deterministic) and re-checked by `validate_design.py`. All pressures are Pa, gauge unless stated. Assumption IDs (AS-nn) are in `DESIGN_BASIS.md` section 5.

```
python calculations.py [--outdir DIR]     # writes the CSV and JSON outputs listed below
python validate_design.py                 # runs the checks and rewrites VALIDATION_REPORT.md
```

| Output | Content |
|---|---|
| `flow_basis.csv` | Flow quantities and the cross-check against the CFD and frozen baseline |
| `pressure_drop_budget.csv` | Row-by-row budget for each candidate bore (low, nominal, high) |
| `candidate_line_sizes.csv` | Comparison of the four candidate bores |
| `pressure_budget_sensitivity.csv` | One-at-a-time and global-multiplier sensitivity (50 mm) |
| `stream_table.csv` | Pressure, temperature and velocity at 14 stations (50 mm, design case) |
| `system_curve.csv` | Fan total pressure against flow, 0.8 to 1.3 of design |
| `thermal_structural_interface.csv` | Screening numbers for the test-article interfaces |
| `calculation_results.json` | Flat key/value results read by the validator |

## 1. Pressure bookkeeping

Every budget row is a **total-pressure loss** between two stations, so the blower duty is the **fan total pressure** (FTP), the sum of the rows:

```
FTP = P0(discharge) - P0(suction) = sum of the losses, including the velocity pressure dumped at the exit
```

where P0 = p + 0.5 rho V^2. Fan catalogues state either FTP or fan static pressure (FTP minus the velocity pressure at the fan outlet); the vendor curve basis must be confirmed (see `LIMITATIONS_AND_NEXT_STEPS.md`). The air starts at rest in the ambient (P0 = 0 gauge) and leaves as a free jet at ambient static pressure.

**The CFD pressure drop is used once.** The CFD gives a static difference, 438.13 Pa. A static difference is not what adds up along a line: it contains the change in velocity pressure along the tube (the heated air accelerates from 23.5 to 28.9 m/s, so the velocity pressure rises by 74.65 Pa), and total pressure is the quantity that sums along the line. The conversion subtracts that rise:

```
loss_TA = dp_static + q_in - q_out        q = 0.5 rho V^2, 1-D, at the CFD inlet and outlet bulk conditions
        = 438.13 + 324.89 - 399.53 = 363.48 Pa
```

The result is still larger than wall friction alone, because heating a gas in a constant-area tube also lowers its total pressure. The CFD's own momentum decomposition (`CFD_BASELINE_RESULTS.md` section 4) gives wall shear 242.87 Pa and momentum-profile development 46.15 Pa; adding the heating term q_out - q_in = 74.65 Pa gives 363.67 Pa, which agrees with the 363.48 Pa above to the 0.2 Pa by which the CFD's decomposition itself closes.

Three CFD cases are available (the velocity cases of the project's parametric study), and the same conversion is applied to each:

| Flow factor | V_in (m/s) | CFD static dp (Pa) | CFD T_out (K) | q_in (Pa) | q_out (Pa) | Total-pressure loss (Pa) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.90 | 21.15 | 379.93 | 376.56 | 263.16 | 330.32 | 312.77 |
| 1.00 | 23.50 | 438.13 | 368.93 | 324.89 | 399.53 | 363.48 |
| 1.10 | 25.85 | 499.69 | 362.69 | 393.11 | 475.26 | 417.54 |

The loss rises as flow^1.44 over this window (the static drop as about flow^1.37). Cross-checks: the CFD area-weighted total-pressure difference (`Audit/fluent_si_p0_area.txt`) is **334.6 Pa**, which is lower than the 1-D value because the real outlet profile carries more kinetic energy. The budget keeps the larger 1-D value as nominal and brackets the range in the low and high cases. The repository states that the CFD total pressure is not to be substituted for the static drop; it is used here only as a bound on this conversion.

Everything outside the tube is added separately and is **not** in the CFD domain: the contraction into the 20 mm bore (B13), the inlet spool (B14), the outlet spool (B16) and the expansion (B17). Adding the 438.13 Pa as if it were a loss, and adding these again, would double count. The existing project figure of 1003.4 Pa for a "real installation" (`FLUID_CALCULATIONS.md`) adds its own sharp-entrance and sudden-exit factors to the CFD-comparable value, which is a different accounting from the total-pressure chain used here, and it is not used.

## 2. Air properties

Ideal gas, density rho = p/(R T) with R = 287.058 J/(kg K); viscosity by Sutherland's law, mu = mu0 (T/T0)^1.5 (T0 + S)/(T + S) with mu0 = 1.716e-5 Pa s, T0 = 273.15 K, S = 110.4 K (AS-02). At 300 K this gives rho = 1.1766 kg/m3 and mu = 1.8459e-5 Pa s.

## 3. Flow basis (Phase 4A)

```
A = pi Di^2 / 4          Qv = V A          mdot = rho V A          Re = 4 mdot / (pi D mu)
q = 0.5 rho V^2          Ma = V / sqrt(gamma R T)          V_out = mdot / (rho_out A)
dp_accel = G^2 (1/rho_out - 1/rho_in),  G = mdot/A
T_out ~ T_in + q'' (pi Do L) / (mdot cp)            (cross-check only, cp = 1008 J/(kg K), AS-03)
```

Results: A = 314.159 mm2, Qv = 7.383 L/s, mdot = 8.686 g/s, inlet Re = 29,958, Ma = 0.0677; outlet V = 28.90 m/s, Re = 25,657, Ma = 0.0751. The Reynolds number and velocity are in the turbulent, low-Mach range (continuity: the outlet velocity rises 23 % as the air heats at constant mass flux). Full table and cross-checks: `DESIGN_BASIS.md` section 4 and `flow_basis.csv`.

## 4. Friction (Darcy-Weisbach)

```
dp = f (L/D) q          1/sqrt(f) = -2 log10( eps/(3.7 D) + 2.51/(Re sqrt(f)) )        (Colebrook-White, fixed-point iteration)
```

Laminar flow (Re under 2300) would use f = 64/Re; every line here is turbulent, and the script labels the regime. Roughness eps is 0.0015 / 0.045 / 0.15 mm for the low, nominal and high cases (AS-04). The method reproduces the Petukhov value used by the project (smooth-tube f = 0.02349 against 0.02365 at the inlet Reynolds number, 0.7 % apart). The CFD fully developed friction factor in the strongly heated tube is 0.02163, about 8 % below the smooth-tube value; the project attributes part of that gap to the gas-heating reduction of f (finding F-029 in its CFD results). It does not enter the budget, because the tube row is the CFD drop itself. `validate_design.py` re-computes every friction row with the Haaland equation (different formulation) and requires agreement within 4 % in f.

## 5. Fitting and component forms

| Item | Form | Class |
|---|---|---|
| Bends, valves, flexible connectors, entrance, exit | dp = K q, K from AS-06 | ASSUMED generic |
| Filter | allocation, AS-07 | Allocation, vendor data |
| Flow element (generic orifice) | dp_signal = (mdot/(C A_d))^2 (1 - beta^4)/(2 rho); permanent loss = [(s - C beta^2)/(s + C beta^2)] dp_signal, s = sqrt(1 - beta^4 (1 - C^2)); C = 0.60 (AS-08) | ASSUMED generic |
| Contraction (line to 20 mm) | K = 0.5 (1 - sigma) on the 20 mm velocity pressure; cone: 0.8 sin(theta/2)(1 - sigma) | ASSUMED generic |
| Expansion (20 mm to line) | Borda-Carnot, loss = 0.5 rho (V1 - V2)^2; static rise rho V2 (V1 - V2); cone: 2.6 sin(theta/2)(1 - sigma)^2 | CALC (momentum balance) |
| Exit to atmosphere | K = 1 on the line velocity pressure | CALC |

The orifice is sized for a 300 Pa signal at design flow (beta from 80 bisection steps, clamped to 0.2 to 0.7). The candidate table shows a real design trade: because the signal depends on the throat diameter and not on the line size, a larger line needs a smaller beta, so the permanent loss of the element rises with line size (179, 215 and 263 Pa at 40, 50 and 80 mm). The independent check recomputes the mass flow from the sized throat and the permanent loss from the ISO loss-coefficient form.

## 6. Pressure budget, recommended 50 mm line, design case

Rows in flow order. Low and high are the corner cases for each row (AS-04 to AS-10). "Class": CALC = physics with verified inputs; CFD_DERIVED = the CFD drop; ASSUMED_GENERIC and ALLOCATION rest on generic or vendor-dependent data.

| ID | Tag | Item | Low (Pa) | Nominal (Pa) | High (Pa) | Class |
| --- | --- | --- | ---: | ---: | ---: | --- |
| B01 | FLT-101 | Line entrance from filter plenum to blower suction line | 0.42 | 4.16 | 8.32 | ASSUMED_GENERIC |
| B02 | FLT-101 | Intake filter, clean-to-loaded allocation (linear in flow) | 50.00 | 100.00 | 250.00 | ALLOCATION |
| B03 | L-102 | Straight pipe, filter to blower suction | 3.68 | 5.14 | 8.49 | CALC |
| B04 | L-102 | 90-degree bends x1, filter to blower suction | 1.25 | 2.50 | 7.49 | ASSUMED_GENERIC |
| B05 | FC-101 | Flexible connector at blower discharge | 0.83 | 2.50 | 8.32 | ASSUMED_GENERIC |
| B06 | L-103 | Straight pipe, blower discharge to metering run | 7.36 | 10.29 | 16.98 | CALC |
| B07 | L-103 | 90-degree bends x2, blower discharge | 2.50 | 4.99 | 14.97 | ASSUMED_GENERIC |
| B08 | HV-101 | Isolation valve, full-bore, fully open | 0.42 | 0.83 | 2.50 | ASSUMED_GENERIC |
| B09 | L-104 | Metering run, 20 D straight upstream of FE-101 | 3.68 | 5.14 | 8.49 | CALC |
| B10 | FE-101 | Orifice-type flow element, permanent pressure loss (signal 300 Pa at this flow) | 50.00 | 215.36 | 269.20 | ASSUMED_GENERIC |
| B11 | L-104 | Straight pipe: 10 D downstream of FE-101 plus route to the test-article adapter | 3.68 | 5.14 | 8.49 | CALC |
| B12 | L-104 | 90-degree bends x1, to test-article adapter | 1.25 | 2.50 | 7.49 | ASSUMED_GENERIC |
| B13 | ADP-101 | Contraction, line bore to 20 mm test-article bore (outside CFD) | 56.51 | 136.45 | 170.57 | ASSUMED_GENERIC |
| B14 | L-105 | Unheated 20 mm inlet instrument spool (outside CFD) | 28.87 | 46.44 | 89.54 | CALC |
| B15 | TA-101 | Heated duct, CFD static drop converted to total-pressure loss | 308.96 | 363.48 | 503.85 | CFD_DERIVED |
| B16 | L-106 | Unheated 20 mm outlet instrument spool (outside CFD) | 36.79 | 58.26 | 111.16 | CALC |
| B17 | ADP-102 | Expansion, 20 mm bore to line bore (outside CFD) | 89.33 | 281.91 | 310.10 | CALC |
| B18 | L-107 | Straight pipe, mixing section and discharge line (hot air) | 9.43 | 13.11 | 21.46 | CALC |
| B19 | FC-102 | Flexible connection (thermal-growth accommodation), hot | 1.02 | 3.07 | 10.23 | ASSUMED_GENERIC |
| B20 | L-107 | 90-degree bends x2, discharge line | 3.07 | 6.14 | 18.41 | ASSUMED_GENERIC |
| B21 | STK-101 | Free-jet discharge to atmosphere (velocity pressure dumped) | 10.23 | 10.23 | 11.25 | CALC |
|  |  | **Total (fan total pressure)** | **669.25** | **1277.63** | **1857.27** |  |

The fan total pressure at the design point is **1,278 Pa** (range 669 to 1,857 Pa across the loss corners). The test article is 28 % of it. Rows that rest on generic or vendor-dependent data make up 37 % of the nominal total; that share is the part of the budget that vendor data will change. The two adapters (contraction and expansion) and the two spools cost 523.07 Pa between them, more than the heated tube they serve, and the expansion alone (B17) is 281.91 Pa: a conical diffuser (low case, AS-09) would remove about 190 Pa.

### Station pressures

Cumulative result for the same case (`stream_table.csv`): the blower discharge static pressure is 1158 Pa and the test-article inlet static pressure is 411 Pa. The static difference across the tube is reproduced as 438.13 Pa, and the exit static pressure is 0, which closes the chain. The static pressure at the test-article outlet is **below ambient** (about -27 Pa, and -85 Pa at the end of the outlet spool) because the expansion into the larger line recovers pressure downstream of it. Leaks near the outlet draw in ambient air.

## 7. Candidate line bores

Four internal diameters are compared on the same routing assumptions (AS-05, AS-16). Pressures are fan total pressure in Pa. "Unsupported" is the share of the nominal total resting on generic or vendor-dependent data. "Screening" requires a bore of at least 50 mm and a Reynolds number of at least 5000 (the ISO 5167-2 scope) and a velocity of at most 20 m/s.

| Bore (mm) | V (m/s) | Re | beta | Signal (Pa) | ISO 5167-2 scope | Friction | Fittings | Flow element | Adapters | Low | Nominal | High | Unsupported (%) | Screening |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 25 | 15.040 | 23966 | 0.700 | 1169.9 | NO | 1030.82 | 413.43 | 603.25 | 214.96 | 1527.38 | 2902.90 | 5161.58 | 40.9 | NO |
| 40 | 5.875 | 14979 | 0.631 | 300.0 | NO | 109.66 | 63.08 | 179.32 | 451.27 | 724.54 | 1293.82 | 1981.62 | 36.0 | NO |
| 50 | 3.760 | 11983 | 0.517 | 300.0 | yes | 38.83 | 25.84 | 215.36 | 523.07 | 669.25 | 1277.63 | 1857.27 | 37.5 | yes |
| 80 | 1.469 | 7489 | 0.328 | 300.0 | yes | 4.58 | 3.94 | 263.43 | 608.15 | 655.51 | 1345.27 | 1881.24 | 38.6 | yes |

- **25 mm** has the highest velocity (15.0 m/s) and costs more than twice as much pressure (2,903 Pa nominal, 5,162 Pa in the high case): friction and bends scale with the velocity pressure. The orifice is clamped at the beta limit of 0.7 (a 1,170 Pa signal and 603 Pa permanent loss) and the bore is below the ISO 5167-2 scope.
- **40 mm** is close to the minimum (1,294 Pa) but is also below the ISO 5167-2 scope, so a standard orifice cannot be used.
- **50 mm** gives the lowest nominal fan pressure of the candidates that pass the screening (1,278 Pa). **Recommended** for the concept.
- **80 mm** is about 5 % above it (1,345 Pa) and gains nothing: the line losses are negligible, but the flow element and the expansion lose more, the velocity falls to 1.5 m/s (poorer mixing for the outlet temperature measurement), and the hardware is bulkier.

The choice is not sensitive to the generic coefficients: the ranking of 40, 50 and 80 mm moves by less than the uncertainty band, and only 25 mm is clearly worse. It is a concept choice, not an optimisation.

## 8. Sensitivity and blower duty

Largest one-at-a-time swings for the 50 mm line (`pressure_budget_sensitivity.csv`), sorted by the larger swing:

| Row | Tag | Item | Nominal (Pa) | Low delta (Pa) | High delta (Pa) |
| --- | --- | --- | ---: | ---: | ---: |
| B17 | ADP-102 | Expansion, 20 mm bore to line bore (outside CFD) | 281.91 | -192.58 | 28.19 |
| B10 | FE-101 | Orifice-type flow element, permanent pressure loss (signal 300 | 215.36 | -165.36 | 53.84 |
| B02 | FLT-101 | Intake filter, clean-to-loaded allocation (linear in flow) | 100.00 | -50.00 | 150.00 |
| B15 | TA-101 | Heated duct, CFD static drop converted to total-pressure loss | 363.48 | -54.52 | 140.37 |
| B13 | ADP-101 | Contraction, line bore to 20 mm test-article bore (outside CFD | 136.45 | -79.95 | 34.11 |
| B16 | L-106 | Unheated 20 mm outlet instrument spool (outside CFD) | 58.26 | -21.47 | 52.89 |
| B14 | L-105 | Unheated 20 mm inlet instrument spool (outside CFD) | 46.44 | -17.57 | 43.10 |
| B20 | L-107 | 90-degree bends x2, discharge line | 6.14 | -3.07 | 12.27 |

Scaling every generic-coefficient and allocation row by one factor (the global scan):

| Scale | Change in fan pressure (Pa) | Change (%) |
| --- | ---: | ---: |
| x0.50 | -239.24 | -18.73 % |
| x0.75 | -119.62 | -9.36 % |
| x1.00 | 0.00 | 0.00 % |
| x1.50 | 239.24 | 18.73 % |
| x2.00 | 478.48 | 37.45 % |
| x3.00 | 956.96 | 74.90 % |

If all generic and allocated component losses are twice the nominal values, the required pressure rises by about a third; if they are half, it falls by about a fifth. The filter allocation and the test-article band are the largest single swings.

Fan total pressure against flow for the 50 mm line (the system curve; the test-article row follows the CFD cases inside 0.9 to 1.1 and is extrapolated outside):

| Flow factor | mdot (g/s) | Suction flow (L/s) | Low (Pa) | Nominal (Pa) | High (Pa) | CFD-supported |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.80 | 6.949 | 5.906 | 470.9 | 879.1 | 1295.5 | EXTRAPOLATED |
| 0.90 | 7.818 | 6.644 | 566.8 | 1070.6 | 1566.0 | YES |
| 1.00 | 8.686 | 7.383 | 669.3 | 1277.6 | 1857.3 | YES |
| 1.10 | 9.555 | 8.121 | 779.6 | 1502.4 | 2172.2 | YES |
| 1.20 | 10.424 | 8.859 | 896.4 | 1742.3 | 2507.3 | EXTRAPOLATED |
| 1.30 | 11.292 | 9.598 | 1019.2 | 1996.8 | 2862.2 | EXTRAPOLATED |

Duty points (recommended bore). The warm-day case holds the mass flow and raises the suction volume flow by T/300; the test-article row is not corrected for the warmer inlet (the CFD is at 300 K only):

| Case | mdot (g/s) | Suction flow (L/s) | FTP low (Pa) | FTP nominal (Pa) | FTP high (Pa) | Hydraulic power at nominal (W) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Design | 8.69 | 7.38 | 669 | 1278 | 1857 | 9.4 |
| Upper flow, 300 K | 9.56 | 8.12 | 780 | 1502 | 2172 | 12.2 |
| Upper flow, 313 K | 9.56 | 8.47 | 786 | 1526 | 2205 | 12.9 |

**Conceptual blower-duty recommendation (REQ-PRES-01).** Choose a speed-controlled blower whose characteristic passes through the upper warm-ambient high-loss point (8.47 L/s, 2,205 Pa) at no more than 90 % of full speed. By the affinity laws this means the blower must deliver at least **9.41 L/s at a fan total pressure of at least 2,722 Pa at full speed** (the loss corners across the design flow span 669 to 1,857 Pa; the design point itself is 1,278 Pa). The hydraulic power at the design point is only 9.4 W, so the motor and drive are small; the shaft power depends on the blower efficiency (vendor data). This is a specification for asking vendors, not a blower selection: the type, the shut-off pressure, the efficiency, the noise and the temperature rise are all vendor data.

## 9. Thermal and structural interface screening (Phase 4D)

Screening numbers that size the interface problems. They are not analyses (AS-18).

| Quantity | Value | Unit | Class |
| --- | ---: | --- | --- |
| TA-101 tube mass (Inconel 718, no flanges/heater/insulation) | 4.631 | kg | DERIVED |
| TA-101 tube weight | 45.42 | N | DERIVED |
| Free axial growth, existing Mechanical LC1 | 1.8409 | mm | EXISTING_RESULT |
| Free axial growth, simple estimate alpha*L*(Tmean-Tref) | 1.8562 | mm | DERIVED |
| Difference, estimate vs LC1 | 0.83 | % | DERIVED |
| Largest LC1 maximum deformation in the existing parametric envelope | 2.0680 | mm | EXISTING_RESULT |
| Full-restraint axial force, existing LC2 end reaction | 548936.6 | N | EXISTING_RESULT |
| Full-restraint axial force, simple estimate E*A*alpha*dT | 548431.1 | N | DERIVED |
| Difference, estimate vs LC2 | -0.09 | % | DERIVED |
| Tube axial stiffness E*A/L | 2.955e+08 | N/m | DERIVED |
| Adiabatic heating rate of the bare tube if flow is lost with heat input on | 0.2706 | K/s | DERIVED |
| Time for +100 K at that rate | 370 | s | DERIVED |
| First bending frequency, cantilever bound | 83.3 | Hz | DERIVED |
| First bending frequency, pinned-pinned bound | 233.8 | Hz | DERIVED |
| First bending frequency, fixed-fixed bound | 530.0 | Hz | DERIVED |
| Test-article inlet static gauge pressure, design case | 411.31 | Pa | DERIVED |
| Existing peak outer-wall temperature, baseline | 562.58 | K | EXISTING_RESULT |
| Existing peak outer-wall temperature, highest of the studied cases | 591.13 | K | EXISTING_RESULT |
| Existing outlet bulk air temperature | 368.93 | K | EXISTING_RESULT |
| Blower heating of the air, low-efficiency bound | 5.39 | K | ASSUMED |
| Blower heating of the air, high-efficiency bound | 2.15 | K | ASSUMED |

Reading these: the simple estimates reproduce the existing Mechanical results (free growth within 1 %, full-restraint force within 0.1 %), which supports using them as screening numbers. A bare tube would heat at about 0.27 K/s if the flow were lost with the heat input on, so a 100 K rise takes about six minutes; the heater and insulation change that, in either direction. The tube's first bending frequency lies between about 83 Hz (cantilever) and 530 Hz (fixed-fixed), so the lower bound is close to the second harmonic (100 or 120 Hz) of a 2-pole motor at mains speed; a modal check with the real supports and heater mass is needed.

Illustrative end force if the free growth acts against a flexible joint of the stated placeholder stiffness (no vendor data; it shows the scale of the problem only):

| Joint axial stiffness | End force |
| --- | --- |
| 10 N/mm | 18.6 N |
| 100 N/mm | 185.6 N |
| 1000 N/mm | 1849.9 N |
| 10000 N/mm | 17953.9 N |

## 10. Limits of the method

- The test-article row uses the CFD drop at the CFD boundary conditions (uniform velocity inlet at 300 K, outlet at ambient). A real inlet adapter changes the entry-region friction; that is covered only by the +/-15 % band.
- Gauge pressures and heating are not fed back into the CFD result. The blower heats the inlet air by an estimated 2 to 5 K, which the CFD (300 K) does not include.
- Generic loss coefficients and allocations carry about a third of the nominal budget; the vendor values may be outside the ranges used.
- The flow element is a generic orifice model; the discharge coefficient, beta limits and straight lengths are to be confirmed against the standard.
- No transient behaviour (start-up, heater switch-on, cool-down) is analysed. The CFD is steady state.
