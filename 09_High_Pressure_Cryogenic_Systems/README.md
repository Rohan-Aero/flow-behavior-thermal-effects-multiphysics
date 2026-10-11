# 09 High-Pressure Gas and Cryogenic Fluid Systems for Aerospace Ground Support

A conceptual engineering study of two ground-support fluid systems: (1) a **high-pressure gaseous-nitrogen (GN2) supply and pressure-control system** and (2) a **liquid-nitrogen (LN2) transfer and conditioning system**.

**Status.** This is a separate follow-on educational study. It was written after the February to May 2025 internship period, after the LS-DYNA study, the SQL extension and the heated-duct fluid test rig design (`08_Fluid_Test_Rig_Design/`), and it is not part of the internship. It runs no solver and adds no new simulation result. **CONCEPTUAL — NOT APPROVED FOR CONSTRUCTION.** It is not a construction-ready, certified or operationally approved pressure or cryogenic system, it establishes no operating pressure, vessel capacity, relief setting, vent size or component rating, and it does not claim compliance with any standard. The existing heated-duct rig remains a **low-pressure air system**; nothing here changes it.

**Authorship and review.** Drafted with AI assistance (Claude Code) for the repository owner. No qualified pressure-systems, cryogenic, piping, instrumentation or safety engineer has reviewed it. Items that need that review are in `LIMITATIONS_AND_NEXT_STEPS.md`.

![GN2 process flow diagram](PFD_HIGH_PRESSURE.png)

![LN2 process flow diagram](PFD_CRYOGENIC.png)

## What it does

It builds a defensible, traceable concept without inventing the inputs that are not known. Verified data (nitrogen properties from the published reference equation of state, NIST material fits and constants), equations, illustrative study cases, assumptions and unresolved inputs are kept in separate classes. Where the data are insufficient for a number, the number is not produced and the missing input is registered. Every diagram carries the banner above.

## Headline results

All results are **screening values for illustrative cases and placeholder assumptions**, not predictions for a real system. Equations and limits: `CALCULATION_METHOD.md`.

| Quantity | Value | Basis |
| --- | --- | --- |
| Illustrative nitrogen mass flow (heated-duct air design flow reused for magnitude only) | <!--h:mdot_g_s-->8.686<!--/h--> g/s | IL-01 from M002, M003, M005, M023 |
| Compressibility factor at the illustrative 20 MPa(g) source | <!--h:Z_source-->1.058<!--/h--> | VERIFIED equation of state |
| Gas cooling across the two illustrative regulators | <!--h:dT_stage1-->-19.2<!--/h--> K and <!--h:dT_stage2-->-9.1<!--/h--> K (leaves at <!--h:T_out_stage2-->271.7<!--/h--> K) | Isenthalpic expansion, no heat gain |
| Choked mass flux per mm2 of flow area at the illustrative source pressure | <!--h:flux_source-->35.9<!--/h--> g/s (<!--h:flux_multiple_source-->4.1<!--/h--> times the illustrative flow) | Scale figure for the failed-regulator hazard, not a relief sizing |
| Nominal passive loss downstream of stage 2 (illustrative bore, assumed route) | <!--h:dp_del_nom_kPa-->16.64<!--/h--> kPa (<!--h:dp_del_pct-->1.66<!--/h--> percent of the delivery set pressure) | Generic K and allocations; <!--h:vendor_share_del_pct-->44<!--/h--> percent vendor-dependent |
| LN2 heat leak per metre, vacuum-jacketed with MLI, design vacuum (S1) | <!--h:Q_S1_nom-->0.185<!--/h--> W/m (range <!--h:Q_S1_low-->0.0678<!--/h--> to <!--h:Q_S1_high-->0.994<!--/h-->) | Radiation, residual gas and supports, assumed placeholders |
| Same with the vacuum lost (S4, lower bound) | <!--h:Q_S4_nom-->34.6<!--/h--> W/m, about <!--h:ratio_S4_S1-->187<!--/h--> times S1 | Conduction only |
| Held-cold boil-off of an illustrative 10 m line, S1 | <!--h:boil_S1_L_h_10m-->0.0416<!--/h--> L/h | Heat leak over the latent heat <!--h:hfg-->199.18<!--/h--> kJ/kg |
| 304 stainless contraction, 300 K to 77.355 K | <!--h:ss_strain_pct-->0.290<!--/h--> percent (<!--h:ss_dL_10m_mm-->29.0<!--/h--> mm per 10 m) | VERIFIED NIST fit |
| Pressure rise of liquid-full trapped LN2 | <!--h:dpdT_trap-->1.73<!--/h--> MPa per K | VERIFIED equation-of-state isochore |
| Time for trapped liquid to reach 1 MPa(g), S1 and S4 | <!--h:trap_t_S1_1MPa_min-->16<!--/h--> min and <!--h:trap_t_S4_1MPa_s-->5<!--/h--> s per metre of bore | Screening level, not an allowable pressure |
| LN2 vaporized into a well-mixed 10 m3 room to reach 19.5 percent oxygen | <!--h:odh_ln2_L_10m3-->1.01<!--/h--> L | VERIFIED densities and threshold |

## Files

| File | Content |
| --- | --- |
| README.md | This file |
| DESIGN_BASIS.md | Source-to-requirement mapping, missing inputs, verified data, assumptions register, standards verified |
| HIGH_PRESSURE_SYSTEM.md | GN2 architecture, boundary conditions, results, operating states and valve positions |
| CRYOGENIC_SYSTEM.md | LN2 architecture, heat leak and boil-off, contraction, trapped liquid, operating states |
| CALCULATION_METHOD.md | Equations, assumptions used, limits, what is not calculated |
| calculations.py | The calculation script (standard library only, deterministic) |
| validate_design.py | The validation script; writes `VALIDATION_REPORT.md` |
| generate_verified_properties.py | Re-creates or re-checks `verified_properties.csv` with the CoolProp library (MIT licence; `pip install CoolProp==8.0.0`) |
| verified_constants.csv, verified_properties.csv | Verified data with sources |
| design_parameters.csv | Register of every parameter: class, source, bounds, assumption ID; headline results |
| boundary_conditions.csv | Pressure and temperature boundary-condition register (both systems) |
| pressure_budget.csv, pressure_sensitivity.csv, regulator_envelope.csv | GN2 budget, sensitivity to bore and component losses, regulator envelope |
| cryogenic_heat_leak.csv, cryogenic_uncertainty.csv, cryogenic_cooldown.csv, thermal_contraction.csv, trapped_liquid.csv, cryogenic_property_screening.csv | LN2 screening calculations |
| oxygen_deficiency_screening.csv | Oxygen-deficiency screening for both systems |
| missing_inputs_register.csv | Every unresolved input, what it blocks, who must supply it |
| equipment_schedule.csv, instrument_index.csv, line_list_high_pressure.csv, line_list_cryogenic.csv | Schedules; every tag in the diagrams is here |
| PFD_HIGH_PRESSURE, PID_HIGH_PRESSURE, PFD_CRYOGENIC, PID_CRYOGENIC (.mmd, .svg, .png) | Mermaid sources and renders |
| mermaid-config.json | Renderer settings used for the exports |
| HAZARD_REVIEW_HIGH_PRESSURE.md, HAZARD_REVIEW_CRYOGENIC.md | Preliminary hazard reviews (not HAZOPs) |
| REQUIREMENTS_TRACEABILITY.csv | Requirements with source, implementation, verification and status |
| VALIDATION_REPORT.md | Result of every check and every mutation test (generated) |
| LIMITATIONS_AND_NEXT_STEPS.md | Limitations, open questions, review items, next steps |

## How to run

Written for Python 3.9 or later; developed and tested with Python 3.13. `calculations.py` and `validate_design.py` use the standard library only; nothing to install. CoolProp is needed only to regenerate or re-check the verified nitrogen table.

```
cd 09_High_Pressure_Cryogenic_Systems
python calculations.py                    # regenerate the CSV outputs
python calculations.py --outdir DIR       # write somewhere else, e.g. a temporary directory
python calculations.py --headlines        # print the headline values quoted in the documents
python validate_design.py                 # run all checks and the mutation tests; rewrites VALIDATION_REPORT.md; exit 1 on a failure
python validate_design.py --online        # also re-check the verified data against the live public pages and, if CoolProp is installed, regenerate the nitrogen table (needs network)
python generate_verified_properties.py --check   # regenerate the nitrogen table with CoolProp and compare (needs CoolProp)
```

`calculations.py` refuses to write inside the repository outside this folder. The validation reruns the calculation in a clean temporary directory and requires byte-identical output, checks formulas against independent re-computations, checks the tags of the diagrams against the schedules in both directions, checks that the numbers quoted in the documents and on the diagrams equal the calculated ones, and then corrupts a source value or an output on purpose in a temporary copy to prove that the checks fail. The diagrams are Mermaid sources; the exports were rendered with `@mermaid-js/mermaid-cli` 11.4.2:

```
mmdc -c mermaid-config.json -i PID_HIGH_PRESSURE.mmd -o PID_HIGH_PRESSURE.svg -b white
mmdc -c mermaid-config.json -i PID_HIGH_PRESSURE.mmd -o PID_HIGH_PRESSURE.png -b white -s 2
```

## Standards and public references actually verified

NASA-STD-5005D (with Change 2) and NASA-STD-8719.17D were read from their public releases in part; ASME B31.3 was verified only as a listing (edition 2024, scope, sold) and its text was **not read**; the 19.5 percent oxygen threshold of 29 CFR 1910.146(b) was read on a Cornell LII copy; the KSC cryogenic standard could not be opened. No standard is stored in this repository and no compliance is claimed. Details and limits: `DESIGN_BASIS.md` section 7.

## Read this with

`REPOSITORY_STRUCTURE.md`, `NOTICE.md` and `GITHUB_CONTENT_AUDIT.md` at the repository root: the repository's own publication and licensing caveats still apply, and this folder is **not yet recorded** in the structure and audit files or in `MANIFEST.csv`, which were deliberately left unchanged. `08_Fluid_Test_Rig_Design/` is the separate low-pressure air rig design that this study does not change.
