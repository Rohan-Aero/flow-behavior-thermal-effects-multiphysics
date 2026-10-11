# Limitations and next steps

**CONCEPTUAL — NOT APPROVED FOR CONSTRUCTION.** Conceptual and educational study. It is not construction-ready, not certified for pressure or cryogenic service, and not operationally approved. The calculations are screening calculations: they do not validate vessel or piping integrity, relief-device sizing or code compliance.

## 1. What this study is and is not

It is a traceable concept for two ground-support fluid systems: functional architectures, a register of inputs separated into verified, illustrative, assumed and unresolved, screening calculations with their equations, two PFDs and two P&IDs with matching schedules and line lists, two preliminary hazard reviews, a requirements traceability matrix and a repeatable validation. It is **not** a design: no operating pressure, source, flow, vessel capacity, allowable pressure, relief setting, vent size, component, rating or size is established.

## 2. Principal limitations

1. **Every pressure and flow is illustrative.** The 20, 5 and 1 MPa(g) pressures and the <!--h:mdot_g_s-->8.686<!--/h--> g/s flow are study cases (IL-01 to IL-04). The flow is the heated-duct **air** flow reused for its magnitude. A different case gives different numbers.
2. **The loss budget rests on placeholders.** <!--h:vendor_share_del_pct-->44<!--/h--> percent of the nominal delivery-zone loss rests on generic loss coefficients and allocations, the rest on pipe friction on an assumed route; no row is supported by component data. The flow-control valve drop, the check-valve cracking pressure and the relief and vent back-pressure are unresolved, not zero.
3. **The cryogenic heat leak rests on placeholders and is a lower bound.** Emissivities, accommodation and vacuum levels are assumed (AS-10 to AS-13). Support conduction is **not calculated** (UI-24, UI-35), so every total covers radiation and residual-gas conduction only. In the one-at-a-time sensitivity the S1 heat leak swings by <!--h:unc_mli_pct-->246<!--/h--> percent of its nominal across the MLI emissivity range. Terminations, valves and flanges are excluded and the source vessel evaporation rate is not calculated.
4. **The degraded- and lost-vacuum cases are weaker than the design-vacuum case.** The degraded case is a bridged transitional-regime estimate; the lost-vacuum case is a conduction-only lower bound with convection ignored (Rayleigh number <!--h:Ra_S4-->3.64e+05<!--/h-->).
5. **Material data are absent.** The nitrogen table is computed with CoolProp from the published equation of state and was compared with the NIST WebBook (section 4 of `DESIGN_BASIS.md`); the few constants are derived from the SI defining constants or cited with their URLs and re-checked by `validate_design.py --online`. No thermal-expansion, modulus, conductivity or specific-heat data for any structural material are held, because the NIST cryogenic-material fits used in an earlier draft were removed (their redistribution terms were not cleared). The thermal contraction, movement, restraint stress, support conduction and metal cooldown heat are therefore **UNAVAILABLE** (UI-34, UI-35, `thermal_contraction.csv`). Nothing was substituted.
6. **Standards: partial reading only.** NASA-STD-5005D and NASA-STD-8719.17D were read in part; ASME B31.3 and Section VIII were **not read**; KSC-STD-Z-0009 could not be opened; CGA and NFPA documents named inside the NASA standards were not read. No compliance is claimed with any of them. See `DESIGN_BASIS.md` section 7.
7. **Steady, screening, single-point.** No transient, two-phase, hydraulic-surge, dispersion, stress-analysis or fire calculation is done. The trapped-liquid times ignore the thermal mass of the metal and the support conduction and are indicative only.
8. **The hazard reviews are preliminary.** They rank nothing and are not a HAZOP. They contain no failure-rate data.
9. **The diagrams are conceptual and laid out automatically** by the Mermaid renderer. Position on the drawing has no meaning; membership of a boundary is given by the box contents.
10. **The folder is not recorded** in `REPOSITORY_STRUCTURE.md`, `GITHUB_CONTENT_AUDIT.md` or `MANIFEST.csv`, which were deliberately left unchanged. The repository's publication and licensing caveats (`NOTICE.md`) are unchanged and not resolved by this folder.
11. **Authorship.** Drafted with AI assistance (Claude Code) at the repository owner's request. The owner should review every number and decision before relying on it.

## 3. Unresolved engineering questions

- What does the downstream user need: pressure, tolerance, flow range, duty cycle and the real limits (UI-01, UI-03, UI-04)?
- What is the source, and what is its pressure and temperature range during depletion (UI-02)?
- Which classification, code and jurisdiction apply to the GN2 system and to the LN2 system (UI-05)?
- What are the design pressures, relief set pressures and capacities, and the worst credible failed-open and trapped-liquid cases (UI-06, UI-07, UI-22)?
- Is a check valve needed at the delivery interface (HAZ-HP-09)?
- What are the regulator data: droop, supply-pressure effect, minimum differential, flow curves (UI-08)?
- What are the vacuum level, MLI performance and heat leak of a real vacuum-jacketed line and its terminations (UI-23, UI-32)?
- What movement capacity do the bellows or loops need, and how are the supports built (UI-24)? Which material data, from a source whose reuse terms are verified, give the contraction, restraint stress, support conduction and cooldown heat (UI-34, UI-35)?
- Where does the cold vent discharge, and how does the cold dense vapour disperse (UI-11, UI-29)?
- What failure position should each remote valve take on loss of power or air (UI-13)?

## 4. Items requiring review by a qualified engineer

| Discipline | Items |
|---|---|
| Pressure systems and piping | Classification, governing code and jurisdiction; design pressure and temperature of every zone; materials; flexibility and contraction analysis; relief philosophy and sizing; test requirements; whether the NASA documents or ASME B31.3 apply at all |
| Cryogenic | Insulation system and vacuum specification; supports and movement devices; trapped-liquid protection of every volume; two-phase and transient behaviour; cold vent design |
| Materials | Low-temperature toughness and allowable stresses; seals and elastomers at the cold-gas and liquid temperatures; cleaning level |
| Instrumentation and controls | Failure positions; independence and performance of the trips; sensor qualification at 77 K; alarm levels |
| Safety and industrial hygiene | Oxygen-deficiency classification, monitor placement and ventilation; vent exposure; cold-burn protection; procedures and training |
| Electrical | Area classification, power-failure behaviour (UI-13) |

## 5. Suggested next steps

1. Obtain the unresolved inputs in the order of `missing_inputs_register.csv`, starting with the downstream user (UI-01, UI-03, UI-04), the source (UI-02) and the classification and code (UI-05).
2. Replace each placeholder with vendor or measured data and rerun `calculations.py`; the budget and heat-leak rows flagged `VENDOR_DATA_REQUIRED` or `ALLOCATION` are the first to replace.
3. Add the real layout so that route lengths, bends, elevations and supports replace AS-05 and IL-15.
4. Carry out the relief and vent calculations (failed-open regulator, trapped liquid, boil-off, jacket failure) with qualified review; the scale figures here are not a substitute.
5. Hold a formal hazard study (for example a HAZOP) with the real design, procedures and site, and add failure-rate and consequence data.
6. Read the applicable standards in their purchased or public form and record clause-level compliance only after that reading.

## 6. Reuse

Reuse is subject to the repository's own terms (`NOTICE.md`, `README.md`): no open-source licence has been granted. **Third-party material.** `THIRD_PARTY_NOTICES.md` lists every third-party source, its licence or terms and the credit it requires. The nitrogen table is computed with the MIT-licensed CoolProp library, whose licence covers the CoolProp software only and **not** any material-property data. NIST Standard Reference Data (WebBook tables, CODATA values, the cryogenic material fits) are **not** stored: NIST states they may not be reproduced without permission. The NASA standards were read from their public releases and are not stored here.
