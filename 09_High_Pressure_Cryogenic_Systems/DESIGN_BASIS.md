# Design basis

**Status: conceptual and educational. CONCEPTUAL — NOT APPROVED FOR CONSTRUCTION.** This is a separate follow-on engineering study. It was written after the February to May 2025 internship period and is not part of that internship. It is not a construction-ready, certified or operationally approved pressure or cryogenic system. It runs no solver, and it does not claim compliance with any standard.

Drafted with AI assistance (Claude Code) for the repository owner. No qualified pressure-systems, cryogenic, piping, instrumentation or safety engineer has reviewed it.

The classes used in every document and CSV of this folder:

| Class | Meaning |
|---|---|
| **EXISTING** | A value already in this repository, with its master-register ID (Mnnn in `05_Data/MASTER_PROJECT_DATA.csv`) or file |
| **VERIFIED** | A value read from an authoritative public source, with the source recorded (`verified_constants.csv`, `verified_properties.csv`) |
| **ASSUMED** (AS-nn) | A modelling assumption made here, registered in section 5 |
| **ILLUSTRATIVE** (IL-nn) | A study case chosen to exercise the calculations. It is **not a requirement**, a specification or a recommendation |
| **UNRESOLVED** (UI-nn) | An input that is needed and that nobody has supplied. It has **no value**. A calculation that needs one stops with an error |
| **CALCULATED** | A result of an equation written out in `CALCULATION_METHOD.md` |

## 1. Purpose, scope and boundary

Study, at concept level, two ground-support fluid systems:

1. **High-pressure gaseous nitrogen (GN2) supply and pressure control.** Functional architecture, a boundary-condition register, a mass-flow and pressure-loss method, a regulator operating-envelope screening, a pressure-drop budget structure and its sensitivity. See `HIGH_PRESSURE_SYSTEM.md`.
2. **Liquid-nitrogen (LN2) transfer and conditioning.** Functional architecture, a heat-leak and boil-off model, thermal contraction, trapped-liquid pressure rise, relief and vent philosophy, and the operating states. See `CRYOGENIC_SYSTEM.md`.

**Out of scope.** Liquid oxygen, liquid hydrogen, propellants, combustion, hazardous operating trials, selection of components, ratings, sizes or prices, relief-device sizing, vessel or piping integrity, any claim of code compliance, and any change to the existing heated-duct air rig.

**Relationship to the existing rig.** `08_Fluid_Test_Rig_Design/` is a low-pressure air system (about 1.2 kPa gauge, blower-fed, discharging to atmosphere). It stays a low-pressure air system. Its design basis lists compressed-gas storage and cryogenic fluids as out of scope, and nothing in this folder changes that. No file of `08_Fluid_Test_Rig_Design/` is modified.

## 2. Source review and source-to-requirement mapping

The repository was reviewed on branch `claude/busy-faraday-82wzhp` (identical to `main` at commit `7f8527c` when the work started). Only the files below were read. The frozen master archive was not accessed. Fluent, Mechanical, LS-DYNA and the SQL import were not run.

| Need of this study | Existing source | What it provides | What is missing, or why it cannot be reused |
|---|---|---|---|
| Ambient state and gas reference temperature | M002 (300 K), M005 (101,325 Pa) | Reference ambient and gas temperature | Nothing missing |
| A repository-traceable magnitude for an illustrative flow | M002, M003, M005, M023 and the air gas constant in `01_Project_Documentation/BASELINE_PARAMETERS.md`; cross-check `08_Fluid_Test_Rig_Design/flow_basis.csv` | The existing air design flow, 8.686 g/s, recomputed here (IL-01) | It is an **air** flow of a different system, so it is **not** a nitrogen requirement (UI-03) |
| Existing rig boundary | `08_Fluid_Test_Rig_Design/DESIGN_BASIS.md` section 1 | Confirms that compressed-gas storage and cryogenic fluids were out of scope there | Nothing; this study is the separate follow-on |
| Existing standards review | `08_Fluid_Test_Rig_Design/PRELIMINARY_HAZARD_REVIEW.md` section 5 | ASME B31.3 Category D scope (design gauge pressure up to 1035 kPa) used for the air rig | The high-pressure case here is outside that scope by its pressure, so classification is open (UI-05) |
| CFD model limits | M001: air as an incompressible ideal gas, properties tabulated 250 to 600 K | Shows what the CFD covers | **Not valid** for nitrogen at high pressure or at cryogenic temperature; no CFD result is reused |
| Thermal and structural model limits | M007, M008, M009: Inconel 718, properties 293 to 673 K; M085: free axial growth 1.84 mm of the heated duct | Shows what the Mechanical model covers | **Not valid** at 77 K or for stainless steel or aluminium lines; cryogenic material data come from NIST instead |
| Publication and licensing caveats | `NOTICE.md`, `README.md`, `GITHUB_CONTENT_AUDIT.md`, `MANIFEST.csv` | The repository's own licence status and attribution rules | `NOTICE.md`, the audit and the manifest are deliberately **not edited**; this folder is not recorded in them. The repository's caveats apply unchanged |
| Format and validation precedent | `08_Fluid_Test_Rig_Design/` | Classes, assumptions register, stdlib-only deterministic Python, validation report | Reused as a pattern only |

## 3. Missing inputs

Nothing below was invented. Each item is registered as UNRESOLVED with no value in `design_parameters.csv`, and is described in full, with the calculation or decision it blocks and who must supply it, in `missing_inputs_register.csv`.

| ID | Missing input |
|---|---|
| UI-01 | Required downstream operating pressure and tolerance |
| UI-02 | Nitrogen source type, pressure range, temperature range and depletion profile |
| UI-03 | Required mass-flow range and duty cycle |
| UI-04 | Downstream minimum and maximum pressure limits |
| UI-05 | Pressure-system classification, governing design code and jurisdiction |
| UI-06 | Design pressure and design temperature of each pressure zone |
| UI-07 | Relief-device set pressures, required capacities and discharge locations |
| UI-08 | Regulator characteristics: supply-pressure effect, droop, lock-up, minimum differential, flow curves |
| UI-09 | Component specifications and ratings (valves, filter, flow element, check-valve cracking pressure, hoses) |
| UI-10 | Materials, seals, cleaning level and compatibility for the service temperature range |
| UI-11 | Vent routing, discharge location, stack height, noise and silencing |
| UI-12 | Room or area volume, ventilation rate and oxygen-deficiency classification |
| UI-13 | Power and instrument-air failure positions and electrical area classification |
| UI-20 | Source vessel capacity, maximum allowable working pressure, relief and vent capacity |
| UI-21 | Transfer-line length, routing, elevation and bore |
| UI-22 | Allowable pressures, relief set pressures, relief capacities and vent sizes |
| UI-23 | Insulation system data: vacuum level, MLI specification, vendor heat-leak figures |
| UI-24 | Support and spacer design, bellows or loop movement capacity |
| UI-25 | Material grades, low-temperature toughness requirements and allowable stresses |
| UI-26 | Receiving vessel or user, fill rate and pressure |
| UI-27 | Required transfer rate, duration and driving pressure difference |
| UI-28 | Cooldown time limit, valve and flange thermal masses |
| UI-29 | Phase separator and cold vent sizing, vent dispersion and ground-level cold-vapour behaviour |
| UI-30 | Installation environment: indoor or outdoor, drainage, spill containment, personnel exposure |
| UI-31 | Cryogenic-qualified instrument ranges and accuracy |
| UI-32 | Measured emissivity and MLI performance |
| UI-33 | Two-phase pressure drop, flow regime and hydraulic-transient data |

Because of these, **no operating pressure, source condition, flow, vessel capacity, allowable pressure, relief setting, vent size or component rating is established** by this study. The pressures and flows used in the calculations are illustrative study cases (IL-nn), chosen so that the equations can be exercised, and every output that depends on them says so.

## 4. Verified data and how it was obtained

All retrieval and comparison was on 2026-10-11. Verified data are kept apart from everything else in `verified_properties.csv` and `verified_constants.csv`.

**Nitrogen properties** (density, enthalpy, cp, cv, Joule-Thomson coefficient, viscosity, conductivity, saturation states and closed-volume isochores; 574 rows) are **computed with the open-source CoolProp library** (version 8.0.0, MIT licence) from the published reference equation of state for nitrogen (Span, Lemmon, Jacobsen, Wagner and Yokozeki, J. Phys. Chem. Ref. Data 29, 1361-1433, 2000) and the transport correlations of Lemmon and Jacobsen (Int. J. Thermophys. 25, 21-69, 2004). `generate_verified_properties.py` records the query of every dataset and re-creates the file (`pip install CoolProp==8.0.0`).

**Why the NIST WebBook tables are not stored.** NIST states that its Standard Reference Data are copyrighted and may not be reproduced, stored or transmitted without permission. The table here is computed from the published equation of state, not copied from any NIST table. The NIST WebBook was used as a **comparison**: all 574 rows were compared with a NIST WebBook fetch at authoring (the fetch was not kept). The largest relative differences were 5.4e-7 for density, 9.1e-7 for cp, 1.4e-7 for cv, 8.8e-7 for the Joule-Thomson coefficient and 9.1e-7 for viscosity; 1e-4 kJ/kg (absolute) for enthalpy; 3.9e-5 for the pressure of a closed-volume isochore at its steepest point; and 5.1e-4 for the conductivity of the saturated liquid at 1 atm, which comes from a 0.001 K difference in the boiling temperature. `validate_design.py --online` repeats a spot comparison with the live NIST WebBook (7 gas states and the 1 atm saturation states), and regenerates the table when CoolProp is installed.

| Data | Source | How it is stored |
|---|---|---|
| Molar mass of nitrogen (28.0134 g/mol) | NIST Chemistry WebBook nitrogen page | `verified_constants.csv` VC-02 |
| Molar gas constant, Stefan-Boltzmann constant | NIST CODATA 2022 pages (both exact) | VC-01, VC-03 |
| Oxygen volume fraction of dry air (20.95 percent) | NASA Earth Fact Sheet | VC-04 |
| Oxygen-deficient atmosphere threshold (19.5 percent by volume) | 29 CFR 1910.146(b), read as hosted by Cornell LII (the eCFR and OSHA hosts could not be reached) | VC-05 |
| Boiling temperature of oxygen at 0.101325 MPa (90.188 K) | NIST Chemistry WebBook oxygen fluid properties | VC-06; context only |
| 304 stainless steel: thermal conductivity, specific heat, Young's modulus, linear expansion | NIST cryogenic materials pages (curve-fit coefficients) | VC-10 to VC-46, coefficients transcribed verbatim |
| 6061-T6 aluminium: linear expansion, Young's modulus | NIST cryogenic materials pages | VC-50 to VC-64 |
| CoolProp version used | CoolProp 8.0.0 | VC-07 |

The NIST material pages state their own fit errors (1 to 5 percent), which are kept in the CSV. The 316 stainless page lists the same expansion coefficients as the 304 page; only 304 is used. The coefficients and constants are a few dozen cited numbers with their URLs; as `NOTICE.md` section 4 does for the main project's material data, the repository owner should confirm that publishing them with their citations is acceptable.

## 5. Assumptions and illustrative cases register

Every number that is not EXISTING or VERIFIED, or an equation result, is listed here. `validate_design.py` checks that each ID used in the code, the CSV files and the documents is registered here, and that each registered ID is used.

| ID | Assumption or illustrative case | Value or form | Basis, and what replaces it |
|---|---|---|---|
| AS-01 | Gas model for the pressure budget | Isothermal flow at 300 K; real-gas p/rho and viscosity from the verified table at each segment inlet; kinetic-energy change and heat gain neglected; gas cooled by regulators is **not** modelled in the budget | Colder gas is denser, so velocity-based losses would be slightly lower: the assumption is mildly conservative for losses. Replaced by a thermal model once routing exists |
| AS-02 | Pipe wall roughness | 0.0015 / 0.045 / 0.15 mm (low / nominal / high) | The same commonly tabulated values as `08_Fluid_Test_Rig_Design` AS-04; material TBD (UI-10) |
| AS-03 | Generic loss coefficients K on line velocity pressure | Bend 0.15 / 0.30 / 0.90; open full-bore valve 0.05 / 0.10 / 0.30; open check valve 1.0 / 2.0 / 5.0 | Handbook-magnitude placeholders, not vendor data (UI-09) |
| AS-04 | Pressure-drop allocations as a fraction of local absolute pressure | Filter 0.10 / 0.25 / 0.50 percent; flow element 0.20 / 0.50 / 1.00 percent | Design allocations that a vendor would have to meet, not datasheet values (UI-09) |
| AS-05 | Conceptual routing | L-301 2.0 m, 2 bends; L-302 0.5 m; L-303 3.0 m, 3 bends; L-304 2.0 m, 2 bends; L-305 6.0 m, 5 bends; length factor 0.75 / 1.0 / 1.5 | No layout exists (UI-21 for the cryogenic line, layout for the GN2 skid) |
| AS-06 | Discharge coefficient of the regulator seat | 0.8 | Screening placeholder; vendor flow-coefficient data replace it (UI-08) |
| AS-07 | Flux through a restriction | Ideal-gas isentropic relations with the real stagnation density; exponent cp/cv at 300 K and 0.101325 MPa | Screening only. Not a relief-sizing method |
| AS-08 | Joule-Thomson expansion | Isenthalpic, adiabatic, no heat gain, inlet at the source temperature or the previous stage outlet | Conservative for the minimum temperature |
| AS-09 | Vent exit | Ambient pressure at the exit; back-pressure neglected | Replaced when relief flows and vent routing are known (UI-07, UI-11) |
| AS-10 | Effective emissivity of the MLI blanket | 0.001 / 0.003 / 0.010 (equivalent value on the cold-surface area) | Placeholders; vendor or test data replace them (UI-23, UI-32) |
| AS-11 | Emissivity of bare metal surfaces, both surfaces | 0.05 / 0.10 / 0.30 | Surface finish unknown |
| AS-12 | Overall thermal accommodation coefficient | 0.7 / 0.9 / 1.0 | Placeholder range |
| AS-13 | Annulus gas pressure | 1e-3 Pa (design), 1 Pa (degraded), 101,325 Pa (lost) | Placeholders (UI-23) |
| AS-14 | Support conduction paths | A/L = 1e-5 / 2e-5 / 1e-4 m; 0.5 / 1 / 2 paths per metre | No support design exists (UI-24) |
| AS-15 | Warm-side temperature | 300 K; 313 K in the high case | 300 K is M002; 313 K is the warm-day bound used in `08_Fluid_Test_Rig_Design` AS-13 |
| AS-16 | Density of 304 stainless steel | 8000 kg/m3 | Typical handbook magnitude, not verified |
| AS-17 | Heat leak scales linearly with length | Terminations, valves, flanges and bayonets are excluded | Their heat leak is UI-21, UI-23 and UI-24 |
| AS-18 | Trapped liquid | Rigid closed volume, uniform temperature, no vapour space (806 kg/m3 case), thermal mass of metal and supports ignored | Shortest-time (conservative) screening |
| AS-19 | Thermal contraction and stress | NIST fits; installed at 300 K; elastic; fully restrained bound computed from 293 K because the modulus fit ends there | Bound only; no allowable stress is available (UI-25) |
| AS-20 | Oxygen-deficiency screening | Well-mixed room, displaced mixture leaves, release at ambient temperature | Local concentrations can be far lower than the room average |
| AS-21 | Cooldown | Inner-line metal only | Valves, flanges, supports, receiver and jacket are excluded (UI-28) |
| IL-01 | Illustrative nitrogen mass flow | Equal to the heated-duct air design flow, recomputed from M002, M003, M005, M023 and the air gas constant | A traceable magnitude, **not** a nitrogen flow requirement |
| IL-02 | Illustrative source pressure | 20 MPa(g) | Chosen to exercise the equations. Not a source specification |
| IL-03 | Illustrative intermediate set pressure | 5 MPa(g) | Study case |
| IL-04 | Illustrative delivery set pressure | 1 MPa(g) | Study case. Not a downstream requirement |
| IL-05 | Illustrative gas temperature at the source | 300 K | Equal to M002 |
| IL-06 | Illustrative uniform line inner diameter | 10 mm | Used in the reference budget only. Not a pipe or tube size |
| IL-07 | Line-diameter sweep | 6, 8, 10, 12, 16, 20 mm | Sensitivity study |
| IL-08 | Component-loss multiplier sweep | 0.5, 1, 2, 4 | Sensitivity study |
| IL-09 | Illustrative limit on passive loss downstream of stage 2 | 5 percent of the delivery set pressure | Stands in for UI-04 |
| IL-10 | Stage-1 inlet pressure sweep | 30, 25, 20, 15, 10, 7, 6 MPa(g) | Source depletion and over-supply |
| IL-11 | Stage-2 inlet pressure sweep | 20, 15, 10, 7, 5, 3, 2 MPa(g) | Includes stage 1 failed open |
| IL-12 | Illustrative inner line outside diameter | 25 mm | Heat-leak screening only. Not a pipe size |
| IL-13 | Illustrative inner line wall thickness | 2 mm | Not a pressure-design thickness |
| IL-14 | Illustrative vacuum-jacket inner diameter | 50 mm | Heat-leak screening only |
| IL-15 | Illustrative straight-run lengths | 5, 10, 20 m | Totals only. Not a routing |
| IL-16 | Trapped-liquid pressure thresholds | 0.5, 1, 5, 10 MPa(g) | Screening levels, **not** allowable pressures or relief settings |
| IL-17 | Illustrative well-mixed room volumes | 10, 100, 1000 m3 | Oxygen-deficiency screening |
| IL-18 | Closed-volume fill densities | 806.0844, 760, 700 kg/m3 | 806.0844 kg/m3 is the saturated liquid density at 0.101325 MPa |

## 6. Tag convention

Tags have the form `<letters>-<three digits>`. Area 3xx is the high-pressure GN2 system; area 4xx is the liquid-nitrogen system. The 08 rig uses area 1xx, so no tag is repeated across the repository. Lines are `L-3nn` and `L-4nn`; stations are `SB-3nn` (GN2) and `SC-4nn` (LN2). Every tag in a diagram, schedule, line list or document is checked against `equipment_schedule.csv` and `instrument_index.csv`. Instrument letters follow the ISA style of 08 (P pressure, T temperature, F flow, L level, A analysis, Z position; I indicate, T transmit, S switch, H high, HH high-high, C control, DT differential transmitter) with no claim of conformance to any symbol standard.

## 7. Standards and public references: what was actually verified

**No standard text is stored or reproduced in this repository.** The two NASA standards below are public releases; their PDFs were downloaded to a temporary scratch area outside the repository, read, and deleted. Nothing is quoted beyond short paraphrase. **No compliance is claimed with any of them.**

| Reference | What was verified, and how | What was not verified | How it is used here |
|---|---|---|---|
| **NASA-STD-5005D with Change 2** (Standard for the Design and Fabrication of Ground Support Equipment; approved 2013-06-14, revalidated 2024-09-30; listed Active) | The NASA Technical Standards System record (public release, scope statement) and the full PDF text of the Foreword, 1.2, 4.2.3, 5.2.1, 5.2.2, 5.2.6, 5.2.11 and the references. It applies to NASA space flight programs at the program's discretion. 5.2.1 names ASME Section VIII and B31.3 for pneumatic servicing (excluding shop air below 1.14 MPa) and asks for restraints on flex hose of 1.14 MPa or more. 5.2.2 names Section VIII and B31.3 (for Severe Cyclic Conditions) for cryogenic servicing. 5.2.6(b) and (c) give a precedent for two valves in series with a vent between for GN2 into ECS ducting, and oxygen monitoring. 5.2.11 requires pressurized systems to comply with NASA-STD-8719.17. 4.2.3.2 states the single-failure philosophy | The remaining sections were not read in full. The referenced KSC standards (for example KSC-STD-Z-0009, cryogenic GSE) were **not reviewed**: the NASA record could not be opened (HTTP 403) | A reference framework for architecture choices only. It does not apply to this educational study. It is cited where a concept feature has a precedent |
| **NASA-STD-8719.17D** (NASA Standard for Ground-Based Pressure Vessels and Pressurized Systems (PVS); approved 2022-04-26) | The full PDF text of 1.1, 1.2, 4.2.3.3 (inert-gas piping exclusion up to 150 psig and NPS 2), 4.2.3.23, 4.10.1.10 to 4.10.1.13, 4.10.2 and 4.10.3. A regulator is not overpressure protection (4.10.1.10). Pressure systems downstream of a regulator are certified for the source pressure or protected by relief devices that accommodate a full-open regulator failure (4.10.3.2). Safety-related pressure indicators are controlled (4.10.2) | Sections 4.3 to 4.9, 4.11 to 4.13 and the appendices were not read in full | Reference practice for the regulator, relief and indicator architecture. Not applied formally |
| **ASME B31.3** (Process Piping), edition listed: 2024 | The ASME catalogue page lists B31.3 - 2024, describes its scope (materials and components, design, fabrication, assembly, erection, examination, inspection and testing of piping, including cryogenic plants) and shows that the text is sold | **The code text was not read.** Whether it applies, which fluid service category applies, and which edition governs depend on jurisdiction and owner (UI-05) | Listed only as an item for review. NASA-STD-5005D 5.2.1 and 5.2.2 name it for pneumatic and cryogenic GSE |
| ASME Boiler and Pressure Vessel Code, Section VIII | Named by NASA-STD-5005D 5.2.1, 5.2.2 and 5.2.11 | **Not read and not independently verified** | For review (UI-05, UI-20) |
| 29 CFR 1910.146(b) | The definition of an oxygen-deficient atmosphere (less than 19.5 percent oxygen by volume), read on a Cornell LII copy | Applicability of the permit-required confined spaces rule to any installation | The 19.5 percent figure is the screening threshold (VC-05) |
| CGA E-4, CGA P-1, NFPA 55 and NFPA 59A | Named inside the NASA documents only | **Not read, not verified** | None |

Publicly accessible NASA ground-systems development guidance **actually used** is the two NASA standards above. Other NASA ground-systems documents (for example the KSC design requirements) were not reviewed.

## 8. Requirements

The requirements are in `REQUIREMENTS_TRACEABILITY.csv`, each with its source, where it is implemented, how it is verified and its status. `MET IN CONCEPT` means only that the concept satisfies it on paper. `OPEN` items need vendor data, a calculation that is blocked by an unresolved input, or review by a qualified engineer.
