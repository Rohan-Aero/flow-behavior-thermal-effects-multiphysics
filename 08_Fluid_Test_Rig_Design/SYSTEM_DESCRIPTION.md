# System description

Conceptual and educational design of an air supply, flow control, instrumentation, heated test article and discharge around the repository's existing heated duct. Not approved for construction. See `DESIGN_BASIS.md` for the inputs, classes and assumptions, `CALCULATION_METHOD.md` for the numbers, and `PRELIMINARY_HAZARD_REVIEW.md` for the hazards.

## 1. System boundary

**Inside the rig boundary:** the ambient intake (INL-101) to the discharge exit (STK-101), the blower and drive, the line and its components, the metering run, the adapters and instrument spools, the interface planes of the test article, the instrumentation, the rig control system and its hardwired safety logic.

**Outside:** the facility (building, ventilation, electrical supply, floor, noise limits); the design of the heater subsystem (HTR-101) beyond its boundary; the manufacture of the test article; any use of the rig for other fluids or pressures.

**Interfaces:** ambient air (station S1) and atmosphere (S14); interface planes IF-1 and IF-2 at the tube ends, which are the CFD inlet and outlet planes; the heater boundary (section 6); the electrical supply to the blower drive and heater (not designed here).

**Design case:** 8.69 g/s of air (7.38 L/s at 300 K) at 300 K and 101,325 Pa ambient; the line concept bore is 50 mm. Normal operation is the CFD condition; the CFD-supported window is 90 to 110 % of that flow.

## 2. Arrangement

![Process flow diagram](PFD.png)

*Process flow diagram (`PFD.mmd`, vector export `PFD.svg`). Stream values are rows of `stream_table.csv`.*

![Piping and instrumentation diagram](PID.png)

*P&ID (`PID.mmd`, vector export `PID.svg`). Conceptual, not approved for construction; no valve size, rating, material or model is specified.*

In flow order. Every selected component has a function; the right-hand column gives what was rejected.

| Tag | Component | Function | Alternative considered |
| --- | --- | --- | --- |
| INL-101 | Ambient air intake | Takes air from a clean, sheltered place away from STK-101. Defines the ambient reference for density compensation (PT-100, TT-100). | - |
| FLT-101 | Intake filter | Keeps particles out of the blower, the flow element and the 20 mm test-article bore. PDT-101 shows loading and intake blockage. | No filter: rejected, the 20 mm bore and the orifice are easily fouled. |
| BLW-101, VFD-101 | Speed-controlled blower and drive | The only source of flow. Flow is set by speed. | Compressed-gas supply: rejected, the duty is 1 to 2 kPa and a gas store brings the hazards the scope excludes. |
| FC-101 | Flexible connector | Isolates blower vibration from the metering run and the test article. | Rigid connection: transmits vibration to FE-101 and the thermocouples. |
| HV-101, ZSO-101 | Isolation valve, open-position switch | Isolates the blower for maintenance. Locked open in operation. Its open position is a blower start permissive. | Valve at the discharge: forbidden, a closed discharge blocks the heated tube. |
| PSV-101 (provisional) | Relief device | Limits blower-discharge pressure if the blower shut-off pressure exceeds the lowest component rating. Upstream of HV-101 so it still protects the blower when HV-101 is closed. | Kept only if vendor shut-off data show it is needed. |
| FE-101, FT-101 | Flow element and transmitter | Mass flow for FIC-101 and for the energy balance. | See section 4.4. |
| ADP-101 | Contraction adapter | Line bore to the 20 mm test-article bore. | Abrupt step: costs more pressure and disturbs the inlet profile. |
| L-105 and L-106 spools | Unheated 20 mm instrument spools | Hold the pressure and temperature taps clear of the heated tube. | Taps in the heated tube: they would change the tested geometry. |
| TA-101 (HTR-101 around it) | Heated duct test article | The existing model article. The heater subsystem is separate. | - |
| ADP-102 | Expansion adapter | 20 mm bore to the discharge line. | Conical diffuser: lower loss, longer; kept as an option. |
| FC-102 | Flexible connection | Absorbs the free thermal growth of TA-101 so the tube is not axially restrained. | Rigid connection: the restraint force would be of the order of 549 kN (section 7). |
| STK-101 | Discharge exit | Free-jet exit to a safe location. No valve or restriction. | Closed or throttled discharge: rejected. |
| SUP-101, SUP-102 | Fixed and guided supports | One axial fixed point at the cold inlet end; a guided sliding support at the hot outlet end. | Two fixed ends: the LC2 case, rejected. |
| CS-101, ES-101, HS-101 | Control system, hardwired safety logic, emergency stop | Closed-loop flow control and monitoring; trips that do not depend on software. | Software-only trips: rejected for the heater permissive. |

Left out on purpose, and why:

| Item | Reason |
| --- | --- |
| Throttling or control valve | A line-size valve has almost no control authority here (section 4.3). Speed control is simpler, wastes less energy and keeps the line free of moving restrictions. |
| Bypass or vent line | The test-article path has no way to close, so the blower is never deadheaded in normal operation. A bypass would add a second path to mis-set. |
| Check valve | No second pressure source and no stored gas, so reverse flow is not credible. |
| Silencers | A noise assessment has not been done. If silencers are needed they add pressure drop (+100 Pa each is a reasonable placeholder allowance, not data). |
| Cooler or dilution on the discharge | Not needed at 369 K for a free jet to a safe location; the hot-air and hot-surface review (H-10) decides. |
| Second flow meter | The energy balance with JT-120 and TT-103 is the independent check on mass flow. |

### Tag and identifier convention

| Kind | Form | Example and rule |
|---|---|---|
| Equipment | `AAA-nnn`, two to five letters and three digits | `BLW-101`. Letters are functional abbreviations. They follow the style of ISA-5.1 for instruments but no conformance to that standard is claimed |
| Instrument | ISA-style letters (first letter the measured variable, then function letters) and a three-digit loop number | `PT-101` pressure transmitter, `PDSL-102` differential-pressure switch low, `TSHH-120` temperature switch high-high. Loop 100 ambient, 101 supply and metering, 102 test article, 103 outlet, 111 to 113 wall, 120 heater subsystem |
| Line | `L-nnn` | `L-104`; bores, lengths and ratings are in `line_list.csv` |
| Interface plane | `IF-n` | `IF-1` is the CFD inlet plane |
| Station | `Sn` | `S10` is IF-1, in `stream_table.csv` |
| Budget row | `Bnn` | `B15` is the test article |
| Assumption, requirement, hazard, check | `AS-nn`, `REQ-xxx-nn`, `H-nn`, `V-xnn` | cross-referenced between files |

## 3. Design-case conditions

Static and total pressures are gauge, in Pa. The blower raises the total pressure by 1,278 Pa (nominal). At the design point the blower discharge static pressure is about 1,158 Pa(g) and the test-article inlet static pressure about 411 Pa(g). The static pressure falls to about -27 Pa(g) at the test-article outlet plane, which is below ambient.

| Station | Where | Line | T (K) | V (m/s) | Total p (Pa g) | Static p (Pa g) |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| S1 | Ambient air at intake | L-101 | 300.00 | 0.000 | 0.00 | 0.00 |
| S2 | Start of L-102: after filter and line entrance | L-102 | 300.00 | 3.760 | -104.16 | -112.48 |
| S3 | End of L-102: blower suction flange | L-102 | 300.00 | 3.760 | -111.80 | -120.11 |
| S4 | Start of L-103: blower discharge flange | L-103 | 300.00 | 3.760 | 1165.83 | 1157.52 |
| S5 | End of L-103: after HV-101, start of the metering run | L-103 | 300.00 | 3.760 | 1147.23 | 1138.91 |
| S6 | Flow element upstream (after 20 D straight run) | L-104 | 300.00 | 3.760 | 1142.09 | 1133.77 |
| S7 | Flow element downstream (after permanent loss) | L-104 | 300.00 | 3.760 | 926.73 | 918.41 |
| S8 | End of L-104: contraction adapter inlet | L-104 | 300.00 | 3.760 | 919.09 | 910.77 |
| S9 | Start of L-105: after contraction | L-105 | 300.00 | 23.500 | 782.64 | 457.75 |
| S10 | End of L-105: test-article inlet plane IF-1 | L-105 | 300.00 | 23.500 | 736.20 | 411.31 |
| S11 | Start of L-106: test-article outlet plane IF-2 | L-106 | 368.93 | 28.900 | 372.72 | -26.82 |
| S12 | End of L-106: before expansion | L-106 | 368.93 | 28.900 | 314.45 | -85.08 |
| S13 | Start of L-107: after expansion | L-107 | 368.93 | 4.624 | 32.54 | 22.31 |
| S14 | End of L-107: discharge exit plane, before exit loss | L-107 | 368.93 | 4.624 | 10.23 | 0.00 |

The air is at 300 K up to IF-1, apart from 2 to 5 K of blower heating (screening estimate, AS-14), and at the CFD bulk outlet temperature of 368.93 K downstream of IF-2. The mass flow is the same at every station.

## 4. Component selection rationale

### 4.1 Blower and operating point

The duty is small and low in pressure: 1,278 Pa at 7.38 L/s, a hydraulic power of 9.4 W. The specification for vendors is **at least 9.41 L/s at a fan total pressure of at least 2,722 Pa at full speed** (`CALCULATION_METHOD.md` section 8), so that the worst credible point (+10 % flow, warm day, all component losses at their high values) is reached at 90 % of full speed. Candidate types: a small centrifugal (radial) blower with speed control, or a regenerative (side-channel) blower with a drive. Both give a smoothly sloping characteristic at this pressure. A positive-displacement blower brings pulsation and needs a relief device, and an axial fan is not matched to this pressure at this flow. Cautions that a vendor must resolve: many catalogue blowers are larger than 8 L/s, so stable operation at the low end of the speed range must be shown; the **shut-off pressure** sets the overpressure case (H-01); the air heating and the noise are vendor data. The vendor curve basis (fan total or static pressure) must be stated and converted.

### 4.2 Line bore

Four bores were compared (`CALCULATION_METHOD.md` section 7). **50 mm is recommended**: the lowest nominal fan pressure of the candidates that pass screening (1,278 Pa), a line velocity of 3.8 m/s, and the smallest bore for which a standards-based orifice applies. 25 mm costs more than twice the pressure; 40 mm is within the uncertainty of 50 mm but cannot use a standard orifice; 80 mm gains nothing and slows the flow to 1.5 m/s. The result is a concept choice, not an optimisation: the loss corners of 40, 50 and 80 mm overlap.

### 4.3 Isolation and flow control

**Flow is controlled by blower speed** through FIC-101 and VFD-101. **There is no throttling or control valve.** The reason is control authority. At the design flow the line velocity pressure is only 8.3 Pa. A fully open full-bore valve (K about 0.1) takes under 1 Pa of a 1,278 Pa system, an authority below 0.1 %. To take 200 Pa out of the flow, a valve would have to reach K of about 24, more than 200 times its open value, far into a poorly controllable part of its range. A reduced-size valve would add permanent pressure drop. Speed control has none of these problems and saves energy.

**HV-101** is a manual full-bore isolation valve upstream of the metering run. It is locked open in operation, proven open by ZSO-101, and used only to isolate the blower for maintenance. **No valve is allowed in the discharge path**, because closing it would stop the flow through a heated tube.

### 4.4 Flow measurement

| Option | Principle | Fit to this rig | Verdict |
| --- | --- | --- | --- |
| Orifice plate, ISO 5167-2 basis (baseline) | Differential pressure over a standard element | Scope needs a bore of at least 50 mm and Re at least 5000: met at 50 mm (Re 11,983). Permanent loss about 215 Pa, the third largest row of the budget. Standard-based, so no per-unit calibration is needed inside the standard's limits. Needs straight runs and a low-range transmitter (signal 300 Pa). | Baseline |
| Classical Venturi, ISO 5167-4 | Differential pressure with pressure recovery | Lower permanent loss, but uncalibrated use needs a pipe Reynolds number of at least 2e5; this rig runs at about 1.2e4. It would need calibration. | Not baseline |
| Thermal mass flow meter | Heat transfer to the flowing gas | Reads mass flow directly with almost no permanent loss. Accuracy, humidity and composition sensitivity, and installation limits are vendor data. A good alternative or second reading. | Alternative |
| Laminar flow element | Differential pressure over laminar passages | Very accurate for clean low flows, but a larger pressure drop and a filtration need (vendor data). | Not baseline |
| Vortex, turbine, rotameter | - | Vortex and turbine types typically need a higher velocity than 3.8 m/s; a rotameter only indicates. Confirm with a vendor. | Rejected |

The baseline is an orifice, with a thermal mass flow meter as the alternative or a cross-check. Whichever is chosen, the **mass flow** is what matters for the energy balance (the CFD heat input over 8.69 g/s gives a 69 K rise), so the uncertainty target is set from the energy balance: proposed at most +/-2 % of reading at the design flow (REQ-FLOW-04), to be shown by an uncertainty budget.

### 4.5 Pressure and temperature sensor locations

- **PT-100 and TT-100** (ambient): density compensation and a plausibility reference for the other temperatures and pressures.
- **PDT-101**: across the filter, for loading and intake blockage.
- **PT-101**: at the blower discharge, for blower protection and a trend of system resistance (the high-pressure trip input).
- **PT-102, TT-101 and FT-101** at FE-101: the compensation and the differential pressure of the flow calculation.
- **PT-103 and TT-102** at IF-1, and **PDT-102 and PDSL-102** across IF-1 and IF-2: taps on the end-face planes, so the measured drop is the CFD drop (M036) and excludes the spools. PDSL-102 is deliberately separate from FT-101, so the heater permissive does not rely on one measurement.
- **TE-111, TE-112, TE-113** on the outer wall at z = 50, 300 and 550 mm, for comparison with the CFD axial profile (expected 470.2, 539.2 and 561.2 K).
- **TE-103 and TT-103** after a mixing length in the discharge line. The CFD outlet temperature is far from uniform (bulk 368.93 K, fluid at the wall up to 553.41 K), so a single point would not give the bulk temperature. The element is a multi-point rake; the mixing length is a detail-design item.
- **TE-120, TSHH-120, JT-120** inside the heater boundary: the independent over-temperature trip and the electrical power for the energy balance. Not designed here.

### 4.6 Filter placement

The filter sits at the intake, upstream of the blower, so everything downstream sees clean air. It protects the 20 mm bore, the smallest passage, and the orifice. Its pressure drop is an allocation (100 Pa clean, 250 Pa loaded) and the largest single uncertainty in the budget; the filter grade, face velocity and housing are vendor data.

### 4.7 Flexible connections and expansion accommodation

Two flexible elements serve different purposes. **FC-101** isolates blower vibration. **FC-102** accommodates the free axial growth of the test article (1.84 mm, up to 2.07 mm across the studied cases) so the tube is never restrained. It sits downstream of the expansion, away from the hottest tube end, and must be rated for the hot discharge air. Movement capacity, stiffness and temperature rating are vendor data. Without it, full restraint would give a force of about 549 kN (a bound, not a case).

### 4.8 Supports

One **axial fixed point at the cold inlet end** (SUP-101) and a **guided sliding support at the hot outlet end** (SUP-102) give the LC1 free-expansion condition. The existing LC1 and LC2 results are for the bare tube and do not qualify these supports (section 7).

## 5. Operating states and conditions

**Normal operating conditions:** the CFD condition (8.69 g/s, 300 K inlet, 101,325 Pa ambient, heat flux 8000 W/m2 on the outer wall) inside the CFD-supported window of 90 to 110 % flow. **Boundaries:** the rig is not qualified outside that window, below 300 K inlet or for any other fluid.

| State | What happens | Exit condition |
| --- | --- | --- |
| S0 Off / isolated | All power off and locked out. HV-101 locked open (operation) or closed (maintenance). | - |
| S1 Ready | Control power on. ZSO-101 shows open; sensors plausible; PDT-101 below its alarm; no active alarm. Heater locked out. | Checks pass |
| S2 Air on, heater off | Blower started by FIC-101 and ramped to the setpoint inside the CFD-supported window (7.82 to 9.56 g/s). FT-101, PDT-102 and the blower speed must agree. | Flow proven for a hold time TBD |
| S3 Heating and run | Heater enabled only with proven flow (FT-101 and PDSL-102 both healthy). The CFD condition: 8.69 g/s, 300 K inlet, outlet bulk 368.93 K, peak wall 562.58 K. The approach to steady state is not analysed. | Operator or program |
| S4 Cool-down | Heater off. Airflow continues until TE-111 to TE-113 fall below a limit set at detail design (REQ-SAFE-05). | Wall temperature below limit |
| S5 Shutdown | Blower stopped after cool-down. | - |
| S6 Trip | ES-101 acts on the cause: low differential pressure or over-temperature removes heater power and keeps the blower running for cooling; high blower pressure or an emergency stop stops the blower and removes heater power. | Reset only after the cause is cleared |
| S7 Maintenance | Lock-out of the blower, drive and heater supply; HV-101 closed and locked if the blower is to be opened; tube cooled before hands-on work. | Procedure |

**Trip and permissive summary** (concept level; the safety-rated architecture is for a qualified engineer):

| Initiator | Acts on | Action | Hazard |
| --- | --- | --- | --- |
| PT-101 high-high (PAHH) | ES-101 | Stop BLW-101, remove heater power | H-01 |
| ZSO-101 not open | ES-101 | Inhibit blower start; stop if lost in operation | H-01 |
| PDSL-102 low differential pressure | ES-101 | Remove heater power; blower keeps running | H-02 |
| TSHH-120 over-temperature (own sensor TE-120) | ES-101 | Remove heater power; blower keeps running | H-06 |
| HS-101 emergency stop | ES-101 | Stop BLW-101, remove heater power | H-09 |
| FT-101 low or high flow | CS-101 | Alarm; heater permissive withdrawn on low flow; setpoint clamps | H-03, H-04 |
| PDT-101 high, TT-103 high, TE-111 to TE-113 high | CS-101 | Alarm | H-05, H-06, H-14 |

**Credible off-normal conditions** are developed in `PRELIMINARY_HAZARD_REVIEW.md`: blocked or restricted discharge, blower failure, unexpected flow, incorrect settings, sensor failure, over-temperature, unexpected thermal expansion, leakage, vibration and support, filter blockage, hot-air discharge, and isolation for maintenance.

## 6. Heater subsystem boundary

The heater and its controls are a **separate subsystem**. The existing model gives a uniform external heat flux of 8000 W/m2 on the outer surface (M006), which delivers 602.755 W to the air in the CFD (M038) over an outer area of 0.0754 m2. That number is a model boundary condition and the heat absorbed by the air. **The heater electrical power, element construction, losses to the surroundings, wiring ratings and protection are not inferred from it**, because the heater's own losses, margins, start-up behaviour and safety design are not in the CFD. The interface this rig requires of the heater subsystem:

| Interface | Requirement |
| --- | --- |
| Enable permissive | ES-101 to HTR-101: heater power only with proven flow and no trip. |
| Independent protection | TE-120 and TSHH-120 inside the boundary trip heater power through ES-101, independent of CS-101. |
| Power measurement | JT-120 reports heater electrical power to CS-101 for the energy balance. |
| Mounting | The heater mounts on the outer surface of TA-101; clearance and access for TE-111 to TE-113 are an interface item. |
| Insulation and touch temperature | Outer surface temperature of the insulated heater against hot-surface limits (H-10). |
| End conduction | The CFD ends are adiabatic; the real end connections are not modelled. |
| Isolation | Heater supply included in the lock-out scheme (S7). |

## 7. Thermal and structural interfaces

Connects this rig design to the existing thermal and Mechanical work. The existing LC1 and LC2 results do not qualify the proposed supports, piping, connections or heater.

| Interface | What the existing work gives | What is missing | New check needed |
| --- | --- | --- | --- |
| Heated ends IF-1 and IF-2 | CFD ends are adiabatic and the fluid domain is exactly the tube (M006, CFD results s.1). The CFD solid is about 424 K at the inlet end and 562 K at the outlet end. | Real end flanges conduct heat out of the tube into the adapters and supports; flange temperature and seals are unknown. | Thermal model of the end connections; thermal breaks; flange and seal temperature limits (vendor, qualified review). |
| Differential expansion | Free axial growth 1.84 mm (LC1, M085); up to 2.07 mm across the studied cases (M155). The simple estimate gives 1.86 mm. | Growth of the discharge line, adapters and supports; clearances; guide friction. | Piping flexibility analysis with the real layout (SUP-101, SUP-102, FC-102). |
| Support and connection loads | LC2, both ends restrained: 548,936.6 N (M091). LC1, one end free: reaction about zero (M088). | Joint axial and lateral stiffness, piping reaction loads, installation misalignment. The existing LC1 and LC2 results are for the bare tube and do not qualify the new supports, piping, connections or heater. | Joint and support load case with vendor stiffness data; FEA of the flange region if loads are not negligible. |
| Pressure on the tube | The existing LC2P check applied 443.41 Pa and found the effect negligible (M097). The test-article inlet static pressure here is about 411 Pa. | A blocked-outlet case at the blower shut-off pressure is not covered. | Re-check once the shut-off pressure is known. |
| Vibration | Bare-tube first bending frequency 83 to 530 Hz depending on the supports (screening). | Heater and insulation mass, real supports, blower excitation frequencies. | Modal check against the blower speed range. |
| Measurement locations | CFD axial wall temperature (Profiles/axial_profiles_cfd.csv), the outlet temperature spread (bulk 368.93 K, maximum fluid 553.41 K), the static drop definition (M036). | How to mount thermocouples under or through the heater; mixing length for TE-103. | Heater-subsystem interface drawing; a short CFD or test study of the mixing length. |

Existing results that are useful here: the CFD axial profiles and outlet profile, the pressure drop at the three flow cases (the CFD-supported window), the thermal field behind the Mechanical results, LC1 as the intended support concept (one end free, free expansion) and LC2 as a bounding case, the pressure-effect check (M097). Existing results that do not transfer: LC1 and LC2 as qualification of any real support, the buckling cases S1 to S3 (idealised end conditions), and the LS-DYNA elastic nonlinear buckling study.

New checks needed before physical construction: a flexibility analysis of the line with the real layout and joint data; a thermal model of the end connections; a modal check; a leak-tightness method and criterion; the blocked-outlet pressure case from the blower shut-off pressure; a heater-subsystem design and its protection; a mixing-length study for the outlet temperature; a noise assessment. The full list by discipline is in `LIMITATIONS_AND_NEXT_STEPS.md`.

## 8. Drawing consistency

Every tag on the PFD and P&ID is in `equipment_schedule.csv` or `instrument_index.csv`, every line is in `line_list.csv`, and every stream value on the PFD is a row of `stream_table.csv`. `validate_design.py` checks this in both directions (checks V-D01 to V-D12) and the result is in `VALIDATION_REPORT.md`.
