# Design basis

**Status: conceptual and educational.** This is a follow-on engineering exercise on top of the repository's existing heated-duct analysis. It is not a construction design, not a certified pressure-system design, and not a rocket-propulsion or launch-pad ground system. It was written after the February to May 2025 internship period and is not part of that internship.

The classes used in every document of this folder:

| Class | Meaning |
|---|---|
| **CFD** / **EXISTING** | A result or input already in this repository (register ID Mnnn in `05_Data/MASTER_PROJECT_DATA.csv`, or the cited file) |
| **CALC** | Derived here from verified inputs, by an equation that is written out |
| **ASSUMED** (AS-nn) | An assumption made here, registered in section 5 |
| **REQ** | A proposed engineering requirement (`REQUIREMENTS_TRACEABILITY.csv`) |
| **VENDOR / REVIEW** | Needs vendor data or review by a qualified engineer before it can be used |

## 1. Purpose and boundary

Design a conceptual air-supply, flow-control, instrumentation, heated-test-article and discharge system around the existing heated cylindrical duct, as a fluid-system design exercise relevant to test facilities.

In scope: a non-hazardous air rig fed by a low-pressure blower, discharging to atmosphere; flow and pressure-drop calculations; preliminary line sizing; generic component requirements; PFD and P&ID; schedules; operating states; a preliminary hazard review; validation.

Out of scope: compressed-gas storage, cryogenic fluids, propellants, combustion, hazardous gases; selection of commercial components, ratings, prices or availability; the heater and its controls (boundary only); construction drawings; any claim of code compliance.

## 2. Verified inputs and design reference conditions

The values stated in the task were checked against the repository's master data register (`05_Data/MASTER_PROJECT_DATA.csv`), the baseline parameter sheet and the CFD results. All match. `validate_design.py` repeats the register comparison on every run (check V-A01).

| Parameter | Stated value | Repository value | Source | Class |
|---|---:|---:|---|---|
| Inner diameter | 20 mm | 20 mm | M023 | EXISTING (re-analysis input) |
| Outer diameter | 40 mm | 40 mm | M024 | EXISTING |
| Length | 600 mm | 600 mm | M026 | EXISTING |
| Wall thickness | 10 mm | 10 mm | M025 | EXISTING |
| Air inlet temperature | 300 K | 300 K | M002 | EXISTING |
| Air inlet velocity | 23.5 m/s | 23.5 m/s | M003 | EXISTING |
| Reference absolute pressure | 101,325 Pa | 101,325 Pa (outlet 0 Pa gauge) | M005 | EXISTING |
| Baseline tube pressure drop | 438.13 Pa | 438.13 Pa, area-weighted static, inlet minus outlet, medium mesh | M036 | CFD |
| External wall heat flux | 8000 W/m2 | 8000 W/m2, uniform on the outer wall, end faces adiabatic | M006 | EXISTING |

Two points about what these values are:

- **Status of the inputs.** `BASELINE_PARAMETERS.md` classifies every one of the 17 baseline parameters as class B (re-analysed or assumed during the 2026 re-analysis) and none as class A (documented from surviving evidence). The original internship data were not retained. The new design inherits that status: no input here is measured data.
- **What the pressure drop is.** The CFD drop is the static pressure difference between the inlet and outlet faces of the tube model. The domain begins with a uniform velocity inlet at the tube entrance and ends with a pressure outlet at the exit plane, so it contains no entrance loss and no exit loss. It is the loss of the heated tube alone, not of the system. Its definition is `CFD_BASELINE_RESULTS.md` section 4.

Design reference conditions for the rig (AS-01): ambient air at 300 K and 101,325 Pa, the same as the CFD inlet, so that the design flow reproduces the CFD mass flow. The rig is a **mass-flow** machine: the CFD fixes the mass flow (and so the Reynolds number), not a volumetric flow, so the blower must deliver more volume on a warm day (AS-13).

## 3. Source-to-requirement table

Which existing results support the new system design, and which inputs still need an assumption or new data.

| Design need | Existing source | What it provides | Still needs an assumption or new data |
| --- | --- | --- | --- |
| Test-article geometry | M023 to M026; BASELINE_PARAMETERS.md | Bore for flow area and spools; tube mass and stiffness | End flanges, heater envelope and insulation: not in the repository |
| Design flow | M002, M003, M005 | Inlet state and velocity give 8.686 g/s | Real ambient variation, humidity, blower heating of the inlet air (AS-13, AS-02, AS-14) |
| Flow range | Velocity cases V01_LOW and V03_HIGH (case matrix; M125 to M142) | CFD-supported 0.9 to 1.1 flow window: pressure drop, outlet temperature, wall temperature, deformation | Anything outside 0.9 to 1.1 needs new CFD; heat flux is fixed at 8000 W/m2 in those cases |
| Test-article pressure loss | M036; CFD_BASELINE_RESULTS.md s.4; Audit/fluent_si_p0_area.txt | Static drop of the CFD domain, its definition, and the area-weighted total pressures | Conversion to total pressure (done here, AS-10); real inlet profile differs from the uniform CFD inlet |
| Hot-air discharge | M037; CFD_BASELINE_RESULTS.md s.5 | Bulk outlet 368.93 K; maximum fluid temperature 553.41 K at the wall | Mixing length for the outlet thermocouple rake; heat loss in the line (AS-12) |
| Heat to the air | M006, M038 | 8000 W/m2 boundary; 602.755 W absorbed by the air | Heater electrical power, losses, construction and protection: out of scope, not inferred |
| Wall temperatures | M039, M154; Profiles/axial_profiles_cfd.csv | Axial outer-wall profile; peak 562.58 K; highest studied case 591.13 K | Trip setpoints and material, heater and insulation limits |
| Thermal growth and restraint | M085 (LC1), M155, M091 (LC2) | Free axial growth 1.84 mm; fully restrained bound 548.9 kN | Support and connection stiffness, flexible-joint data, piping loads: not evaluated. LC1 and LC2 do not qualify the new supports |
| Material properties | M008; BASELINE_PARAMETERS.md (E, alpha, specific heat) | Tube mass, axial stiffness, heating rate | Flange, bolting and piping materials |
| Pipe, fitting and component losses | none | - | Everything: AS-04 to AS-09, AS-15; vendor data required |
| Blower, filter, valves, sensors | none | - | Everything: generic requirements only; vendor data required |

## 4. Derived flow quantities

Calculated independently from the verified inputs (equations, units and the full cross-check are in `CALCULATION_METHOD.md` section 3 and `flow_basis.csv`).

| Quantity | Equation | Value | Unit | Class |
| --- | --- | ---: | --- | --- |
| Internal flow area | A = pi Di^2 / 4 | 314.159 | mm2 | CALC |
| Volumetric flow at 300 K, 101,325 Pa | Qv = V A | 7.383 | L/s | CALC |
| Air density at the inlet | rho = p / (R T) | 1.1766 | kg/m3 | CALC |
| Mass flow | mdot = rho V A | 8.686 | g/s | CALC |
| Mass flux | G = mdot / A | 27.65 | kg/(m2 s) | CALC |
| Dynamic viscosity at 300 K (Sutherland) | mu(T) | 1.8459e-05 | Pa s | CALC (AS-02) |
| Inlet Reynolds number | Re = 4 mdot / (pi Di mu) | 29,958 | - | CALC |
| Inlet dynamic pressure | q = 0.5 rho V^2 | 324.9 | Pa | CALC |
| Inlet Mach number | Ma = V / sqrt(gamma R T) | 0.0677 | - | CALC |
| Outlet density (CFD bulk outlet 368.93 K) | rho = p / (R T) | 0.9568 | kg/m3 | CALC from M037 |
| Outlet velocity (continuity) | V = mdot / (rho A) | 28.90 | m/s | CALC |
| Outlet Reynolds number | Re = 4 mdot / (pi Di mu) | 25,657 | - | CALC |
| Outlet dynamic pressure | q = 0.5 rho V^2 | 399.5 | Pa | CALC |
| Outlet Mach number | Ma = V / sqrt(gamma R T) | 0.0751 | - | CALC |
| Heating acceleration term | G^2 (1/rho_out - 1/rho_in) | 149.3 | Pa | CALC |

The flow implied by the existing inlet condition is **7.383 L/s**, matching the approximately 7.38 L/s quoted in the task, and the mass flow is **8.686 g/s** at 300 K and 101,325 Pa. The existing frozen baseline gives 7.383 L/s and 8.686 g/s, and the CFD flux is 8.662 g/s (0.28 % lower, because the CFD bore is a 48-sided polygon).

Cross-check against the existing CFD and frozen baseline (all within tolerance):

| Check | Calculated | Reference | Reference source | Difference | Result |
| --- | --- | --- | --- | --- | --- |
| volumetric flow | 0.00738274 | 0.007383 | BASELINE_PARAMETERS.md | -0.003 % | PASS |
| mass flow (circular tube) | 0.00868647 | 0.008686 | BASELINE_PARAMETERS.md | 0.005 % | PASS |
| mass flow vs CFD | 0.00868647 | 0.00866215 | CFD_BASELINE_RESULTS.md s4 | 0.281 % | PASS |
| inlet Reynolds number | 29957.9 | 29958 | M034 | -0.000 % | PASS |
| outlet Reynolds number | 25656.9 | 25545 | M035 | 0.438 % | PASS |
| inlet Mach number | 0.0676797 | 0.0677 | FLUID_CALCULATIONS.md | -0.030 % | PASS |
| inlet dynamic pressure | 324.886 | 324.9 | FLUID_CALCULATIONS.md | -0.004 % | PASS |
| outlet dynamic pressure | 399.534 | 399.5 | FLUID_CALCULATIONS.md | 0.009 % | PASS |
| outlet velocity (continuity) | 28.8995 | 28.894 | CFD_BASELINE_RESULTS.md s4 | 0.019 % | PASS |
| outlet temperature (energy balance) | 368.889 | 368.93 | M037 | -0.011 % | PASS |
| heating acceleration term | 149.296 | 149.31 | CFD_BASELINE_RESULTS.md s4 | -0.009 % | PASS |
| friction factor (smooth Colebrook vs Petukhov) | 0.0234907 | 0.0236471 | FLUID_CALCULATIONS.md (Petukhov) | -0.661 % | PASS |

## 5. Assumptions register

Every number in the calculations that is not an existing project value or a calculation from one is an assumption listed here. `validate_design.py` checks that each ID used in the code, the CSV files and the documents is registered here, and that each registered ID is used (check V-D11).

| ID | Assumption | Value used | Basis and rationale | Used in | Status |
| --- | --- | --- | --- | --- | --- |
| AS-01 | Rig ambient reference | 300 K, 101,325 Pa, dry air | Equal to the CFD inlet condition, so the design flow reproduces the CFD mass flow. Real ambient varies (AS-13). | calculations.py; INL-101; PT-100; TT-100 | Assumed |
| AS-02 | Air model | Ideal gas, R = 287.058 J/(kg K), gamma = 1.4. Viscosity by Sutherland's law, mu0 = 1.716e-5 Pa s at 273.15 K, S = 110.4 K | R and gamma are the project values (BASELINE_PARAMETERS.md). The Sutherland constants are a widely published set (checked against CFD-Wiki and the ANSYS Fluent manual). The result reproduces the CFD inlet Reynolds number to 0.001 % and the outlet value to 0.44 %. Humidity is ignored. | calculations.py | Assumed |
| AS-03 | Specific heat of air for the energy-balance cross-check | 1008 J/(kg K) | Mean of the 300 to 369 K range from standard tabulated values (about 1007 to 1009 J/(kg K)). Used only to cross-check the outlet temperature, never in the budget. | flow_basis.csv | Assumed |
| AS-04 | Pipe wall roughness | 0.0015 mm (low), 0.045 mm (nominal), 0.15 mm (high) | Commonly tabulated Moody-chart values for drawn tube, commercial steel and aged steel. No pipe material is selected. | pressure_drop_budget.csv (friction rows) | Assumed; material TBD |
| AS-05 | Conceptual routing | L-102: 1.0 m, 1 bend; L-103: 2.0 m, 2 bends; L-104: 0.5 m route, 1 bend, plus the metering run; L-107: 2.0 m, 2 bends. Friction length factors 0.75 / 1.0 / 1.5 | A plausible bench-scale layout with no drawing behind it. The factors cover a different layout. | line_list.csv; budget rows B03 to B20 | Assumed; layout TBD |
| AS-06 | Generic loss coefficients K (on line velocity pressure) | Bend 0.30 (0.15 to 0.90); open full-bore valve 0.10 (0.05 to 0.30); flexible connector 0.30 (0.10 to 1.0); line entrance 0.50 (0.05 to 1.0); free-jet exit 1.0 (1.0 to 1.1) | Handbook-typical magnitudes for long-radius bends, full-bore ball valves, corrugated connectors, sharp and bell-mouthed entrances. They are not vendor data and not read from a specific edition of a handbook. | budget rows B01, B04, B05, B07, B08, B12, B19, B20, B21 | Assumed; vendor data required |
| AS-07 | Intake filter pressure-drop allocation | 100 Pa nominal (50 Pa low, 250 Pa loaded), linear in flow | A design allocation that the filter vendor must meet, not a datasheet value. | budget row B02; FLT-101; PDT-101 | Allocation; vendor data required |
| AS-08 | Flow element model | Concentric orifice, discharge coefficient C = 0.60, expansibility 1, signal target 300 Pa, beta screening range 0.2 to 0.7. Low case 50 Pa (non-obstructive alternative), high case 1.25 x nominal | Generic sizing only. Expansibility is 1 because the signal is 0.3 % of the line pressure (error below 0.1 %). C and the beta limits are to be confirmed against ISO 5167-2 at detail design (the standard's text was not read). | budget row B10; FE-101; candidate_line_sizes.csv | Assumed; to be confirmed against ISO 5167-2 |
| AS-09 | Contraction and expansion loss forms | Contraction: K = 0.5 (1 - sigma) abrupt (nominal), K = 0.8 sin(15 deg) (1 - sigma) for a 30-degree cone (low), high = 1.25 x nominal. Expansion: Borda-Carnot K = (1 - sigma)^2 (nominal), K = 2.6 sin(7 deg) (1 - sigma)^2 for a 14-degree diffuser (low), high = 1.10 x nominal. sigma = small area / large area, K on small-end velocity pressure | The cone forms are the Crane-type small-angle expressions as given in public documentation (MathWorks); the abrupt contraction form is the same family. Borda-Carnot follows from a momentum balance. The nominal case is the simplest hardware. | budget rows B13, B17 | Assumed; to be confirmed against a handbook |
| AS-10 | Test-article uncertainty band | Low = 0.85 x nominal total-pressure loss. High = 1.15 x the unconverted static drop | +/-15 % is the project's own acceptance tolerance for the pressure drop (PR-05). A real adapter does not give the uniform velocity inlet of the CFD, so the entry-region friction can differ. The high case also gives no credit for the kinetic-energy change. | budget row B15 | Assumed |
| AS-11 | Instrument spools at the test article | Unheated, 20 mm bore, 5 diameters (100 mm) each, inlet and outlet | The CFD domain is exactly the heated tube; any real spool for taps and sensors is outside it and carries friction at the high bore velocity. | budget rows B14, B16; L-105; L-106 | Assumed |
| AS-12 | Discharge condition | Free jet to atmosphere (exit static pressure 0 Pa gauge). The discharge line carries air at the CFD outlet bulk temperature with no heat loss | No heat loss gives the higher velocity and loss, so it is conservative for the blower. A real line loses some heat. | budget rows B18 to B21; STK-101 | Assumed |
| AS-13 | Operating envelope and margins | Flow factor 0.9 to 1.1 (the CFD velocity cases); warm ambient 313 K; 10 % speed headroom at the upper point | The CFD supports only the 21.15 to 25.85 m/s cases. 313 K is a warm-day bound. Speed headroom lets the blower reach the upper point at 90 % speed and so stay controllable. | calculations.py; BLW-101; FIC-101 | Assumed |
| AS-14 | Blower overall efficiency, heating estimate only | 0.20 to 0.50 | All shaft power ends up in the air stream in this screening estimate. Not used for sizing. | thermal_structural_interface.csv; TT-102 | Assumed; vendor data required |
| AS-15 | Straight lengths of the metering run | 20 D upstream and 10 D downstream of FE-101 | Placeholders. ISO 5167-2 gives the required lengths as a function of beta and the upstream fitting; the standard's text was not read. | budget rows B09, B11; L-104 | Assumed; to be confirmed against ISO 5167-2 |
| AS-16 | Candidate line bores and screening | 25, 40, 50 and 80 mm internal diameter. Screening: line velocity at most 20 m/s, bore at least 50 mm and Reynolds number at least 5000 (the ISO 5167-2 scope) | Four sizes spanning a velocity range of 15 m/s down to 1.5 m/s. 20 m/s is a noise and vibration screening limit, not a code value. | candidate_line_sizes.csv | Assumed |
| AS-17 | Incompressible treatment outside the test article | Density at 101,325 Pa plus gauge pressure is not corrected | The largest gauge pressure is about 1.2 kPa, 1.1 % of the absolute pressure, so the density error is about 1 %, below the other uncertainties. | calculations.py | Assumed |
| AS-18 | Thermal and structural screening | Bare tube only (no heater, insulation, flanges); adiabatic heating on loss of flow; Euler-Bernoulli bending; Young's modulus at 555 K | A screening estimate for the size of effects, not an analysis. It bounds the real response from one side only. | thermal_structural_interface.csv | Assumed |

## 6. Proposed design requirements

The 34 requirements are in `REQUIREMENTS_TRACEABILITY.csv`, each with its source, where it is implemented, how it is verified and its status. The ones that shape the design most:

- **REQ-FLOW-01 / 02:** supply 8.69 g/s and keep the setpoint inside the CFD-supported 90 to 110 % window.
- **REQ-FLOW-03:** control flow by blower speed; no throttling valve in the line.
- **REQ-PRES-01:** the blower shall deliver at least 9.41 L/s at a fan total pressure of at least 2722 Pa at full speed.
- **REQ-PRES-02:** count the CFD test-article drop once, as a total-pressure loss, with the adapters and spools listed separately.
- **REQ-PRES-03:** no valve or restriction in the discharge path.
- **REQ-THERM-01 / 03:** do not restrain the test article axially; evaluate connection loads before construction.
- **REQ-SAFE-01 / 02:** heater power only with proven flow; an independent over-temperature trip.

Items whose status is `OPEN` need vendor data, a test or a qualified engineer. Nothing marked `MET IN CONCEPT` means more than that the concept satisfies it on paper.

## 7. External references used for numerical limits

These were checked through public catalogue listings and documentation pages while writing this design. The standards are paywalled and **their text was not read**; only scope statements from listings were used. Any real use needs the purchased text.

| Item | What was used | Source |
|---|---|---|
| ISO 5167-2:2022 (orifice plates) | Scope excludes pipes under 50 mm or over 1000 mm and pipe Reynolds numbers below 5000 | [ANSI webstore preview](https://webstore.ansi.org/preview-pages/ISO/preview_ISO+5167-2-2022.pdf); [AFNOR listing](https://www.boutique.afnor.org/en-gb/standard/iso-516722022/measurement-of-fluid-flow-by-means-of-pressure-differential-devices-inserte/xs139600/326524) |
| ISO 5167-4:2022 (Venturi tubes) | Uncalibrated use needs pipe size 50 to 1200 mm and pipe Reynolds number of at least 2e5, so it does not fit this rig (Re about 1.2e4 at 50 mm) | [AFNOR listing](https://www.boutique.afnor.org/en-gb/standard/iso-516742022/measurement-of-fluid-flow-by-means-of-pressure-differential-devices-inserte/xs141558/326489) |
| Sutherland constants for air | mu0 = 1.716e-5 Pa s, T0 = 273.15 K, S = 110.4 K | [CFD-Wiki](https://www.cfd-online.com/Wiki/Sutherland's_law); [ANSYS Fluent manual](https://www.afs.enea.it/project/neptunius/docs/fluent/html/ug/node294.htm) |
| Crane-type area-change loss forms | 0.5(1-sigma) abrupt contraction; 0.8 sin(theta/2)(1-sigma) and 2.6 sin(theta/2)(1-sigma)^2 for cones under 45 degrees | [MathWorks Area Change (IL)](https://www.mathworks.com/help/hydro/ref/areachangeil.html) (Crane TP-410 itself was not available) |
| Borda-Carnot loss | 0.5 rho (V1 - V2)^2 for a sudden expansion | [Wikipedia](https://en.wikipedia.org/wiki/Borda%E2%80%93Carnot_equation); the static rise rho V2 (V1 - V2) follows from the momentum balance and is checked in `validate_design.py` |
| Orifice permanent-loss form | The head-loss coefficient K = (sqrt(1 - beta^4 (1 - C^2)) / (C beta^2) - 1)^2 in the ISO 5167 family, as quoted by a public source; reproduced independently in `validate_design.py` | [fluids documentation](https://fluids.readthedocs.io/_modules/fluids/flow_meter.html) |

The standards that may apply to the facility, and why, are in `PRELIMINARY_HAZARD_REVIEW.md` section 5.
